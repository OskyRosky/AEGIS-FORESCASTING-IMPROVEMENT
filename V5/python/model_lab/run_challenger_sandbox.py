"""Block 5.29B - Challenger Sandbox Execution.

This script runs a *small, controlled* sandbox execution ONLY for challenger
models whose forecasting dependencies are actually installed in the current
environment. It then validates any produced forecasts against the challenger
forecast output contract and decides which challengers are eligible to become
official-execution candidates.

Hard rules enforced here:
  * Real libraries only. If a challenger's dependency is missing, that
    challenger is marked ``sandbox_blocked_dependency_missing`` and NO forecast
    is produced for it. We never fabricate forecasts or relabel a baseline as a
    challenger.
  * Sandbox scope only: a controlled subset (5 representative entities, the
    latest window each) - never the full 454-window backtest.
  * ``official_execution_allowed`` is always ``False`` in this block. Passing the
    sandbox only makes a model an *eligible candidate*; it never sets
    ``official_execution_ready``.
  * No rankings / tournaments / champions are produced.
"""

from __future__ import annotations

import importlib
import importlib.util
from datetime import datetime, timedelta
from typing import Callable

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_sandbox")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
PLANNING_DIR = MODEL_LAB_DIR / "challenger_execution_planning"
SANDBOX_DIR = MODEL_LAB_DIR / "challenger_sandbox"

WINDOWS_PATH = MODEL_LAB_DIR / "backtesting_windows.csv"
EVAL_PATH = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
REGISTRY_PATH = (
    MODEL_LAB_DIR / "challenger_onboarding" / "challenger_registry_snapshot.csv"
)

HORIZON_DAYS = 30
SANDBOX_ENTITY_COUNT = 5
RUN_ID = "challenger_sandbox"
EXECUTION_MODE = "sandbox"

FORECAST_COLUMNS = [
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "forecast_date",
    "horizon_day",
    "forecast_value",
    "execution_mode",
    "created_timestamp",
]

# ---------------------------------------------------------------------------
# Dependency model: each model can run if ANY one of its option-sets is fully
# importable. An option-set is a list of modules that must ALL be present.
# ---------------------------------------------------------------------------
DEPENDENCY_OPTIONS: dict[str, list[list[str]]] = {
    "AutoARIMA": [["statsforecast"], ["pmdarima"]],
    "Theta": [["statsforecast"], ["darts"]],
    "ETS Explicit": [["statsmodels"], ["statsforecast"]],
    "LightGBM": [["lightgbm"]],
    "XGBoost": [["xgboost"]],
    "NBEATS": [["neuralforecast", "torch"], ["darts", "torch"]],
    "NHITS": [["neuralforecast", "torch"]],
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


_IMPORT_CACHE: dict[str, bool] = {}


def _module_available(name: str) -> bool:
    """Return True only if the module can actually be *imported*.

    A package that is installed but broken/incompatible (e.g. an outdated
    neuralforecast that fails against the current pytorch-lightning) must count
    as unavailable so the dependent challenger is correctly blocked rather than
    attempted-and-failed.
    """
    if name in _IMPORT_CACHE:
        return _IMPORT_CACHE[name]
    available = False
    if importlib.util.find_spec(name) is not None:
        try:
            importlib.import_module(name)
            available = True
        except Exception:  # noqa: BLE001 - broken install => unavailable
            available = False
    _IMPORT_CACHE[name] = available
    return available


def _first_available_option(model_name: str) -> list[str] | None:
    """Return the first fully-available option-set for a model, else None."""
    for option in DEPENDENCY_OPTIONS.get(model_name, []):
        if all(_module_available(mod) for mod in option):
            return option
    return None


# ---------------------------------------------------------------------------
# Real, dependency-guarded model adapters. Each returns a length-HORIZON numpy
# array of point forecasts or raises. They are ONLY invoked when the required
# library is importable, so in a backend-less environment they never execute.
# ---------------------------------------------------------------------------
def _make_lag_matrix(values: np.ndarray, n_lags: int) -> tuple[np.ndarray, np.ndarray]:
    rows_x, rows_y = [], []
    for i in range(n_lags, len(values)):
        rows_x.append(values[i - n_lags : i][::-1])
        rows_y.append(values[i])
    return np.asarray(rows_x, dtype=float), np.asarray(rows_y, dtype=float)


def _recursive_tree_forecast(model, values: np.ndarray, n_lags: int) -> np.ndarray:
    history = list(values.astype(float))
    preds: list[float] = []
    for _ in range(HORIZON_DAYS):
        feats = np.asarray(history[-n_lags:][::-1], dtype=float).reshape(1, -1)
        yhat = float(model.predict(feats)[0])
        preds.append(yhat)
        history.append(yhat)
    return np.asarray(preds, dtype=float)


def _forecast_autoarima(values: np.ndarray, option: list[str]) -> np.ndarray:
    if option == ["statsforecast"]:
        from statsforecast import StatsForecast
        from statsforecast.models import AutoARIMA

        df = pd.DataFrame(
            {
                "unique_id": "s",
                "ds": pd.RangeIndex(len(values)),
                "y": values.astype(float),
            }
        )
        sf = StatsForecast(models=[AutoARIMA()], freq=1, n_jobs=1)
        fc = sf.forecast(df=df, h=HORIZON_DAYS)
        return fc["AutoARIMA"].to_numpy(dtype=float)
    import pmdarima as pm

    model = pm.auto_arima(values.astype(float), seasonal=False, error_action="ignore")
    return np.asarray(model.predict(HORIZON_DAYS), dtype=float)


def _forecast_theta(values: np.ndarray, option: list[str]) -> np.ndarray:
    if option == ["statsforecast"]:
        from statsforecast import StatsForecast
        from statsforecast.models import Theta

        df = pd.DataFrame(
            {
                "unique_id": "s",
                "ds": pd.RangeIndex(len(values)),
                "y": values.astype(float),
            }
        )
        sf = StatsForecast(models=[Theta()], freq=1, n_jobs=1)
        fc = sf.forecast(df=df, h=HORIZON_DAYS)
        return fc["Theta"].to_numpy(dtype=float)
    from darts import TimeSeries
    from darts.models import Theta as DartsTheta

    ts = TimeSeries.from_values(values.astype(float))
    model = DartsTheta()
    model.fit(ts)
    return model.predict(HORIZON_DAYS).values().flatten().astype(float)


def _forecast_ets(values: np.ndarray, option: list[str]) -> np.ndarray:
    if option == ["statsmodels"]:
        from statsmodels.tsa.holtwinters import ExponentialSmoothing

        model = ExponentialSmoothing(
            values.astype(float), trend="add", seasonal=None
        ).fit()
        return np.asarray(model.forecast(HORIZON_DAYS), dtype=float)
    from statsforecast import StatsForecast
    from statsforecast.models import AutoETS

    df = pd.DataFrame(
        {
            "unique_id": "s",
            "ds": pd.RangeIndex(len(values)),
            "y": values.astype(float),
        }
    )
    sf = StatsForecast(models=[AutoETS()], freq=1, n_jobs=1)
    fc = sf.forecast(df=df, h=HORIZON_DAYS)
    return fc["AutoETS"].to_numpy(dtype=float)


def _forecast_lightgbm(values: np.ndarray, option: list[str]) -> np.ndarray:
    import lightgbm as lgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = lgb.LGBMRegressor(n_estimators=100, random_state=0, verbosity=-1)
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags)


def _forecast_xgboost(values: np.ndarray, option: list[str]) -> np.ndarray:
    import xgboost as xgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = xgb.XGBRegressor(n_estimators=100, random_state=0, verbosity=0)
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags)


def _forecast_nbeats(values: np.ndarray, option: list[str]) -> np.ndarray:
    from darts import TimeSeries
    from darts.models import NBEATSModel

    ts = TimeSeries.from_values(values.astype(float))
    model = NBEATSModel(
        input_chunk_length=min(30, max(2, len(values) // 2)),
        output_chunk_length=HORIZON_DAYS,
        n_epochs=5,
        random_state=0,
    )
    model.fit(ts)
    return model.predict(HORIZON_DAYS).values().flatten().astype(float)


def _forecast_nhits(values: np.ndarray, option: list[str]) -> np.ndarray:
    from neuralforecast import NeuralForecast
    from neuralforecast.models import NHITS

    df = pd.DataFrame(
        {
            "unique_id": "s",
            "ds": pd.RangeIndex(len(values)),
            "y": values.astype(float),
        }
    )
    nf = NeuralForecast(models=[NHITS(h=HORIZON_DAYS, input_size=30, max_steps=20)], freq=1)
    nf.fit(df=df)
    fc = nf.predict()
    return fc["NHITS"].to_numpy(dtype=float)


FORECASTERS: dict[str, Callable[[np.ndarray, list[str]], np.ndarray]] = {
    "AutoARIMA": _forecast_autoarima,
    "Theta": _forecast_theta,
    "ETS Explicit": _forecast_ets,
    "LightGBM": _forecast_lightgbm,
    "XGBoost": _forecast_xgboost,
    "NBEATS": _forecast_nbeats,
    "NHITS": _forecast_nhits,
}


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def _load_registry() -> pd.DataFrame:
    df = pd.read_csv(REGISTRY_PATH)
    logger.info("Loaded challenger registry: %d models", len(df))
    return df


def _load_windows() -> pd.DataFrame:
    df = pd.read_csv(WINDOWS_PATH)
    logger.info("Loaded backtesting windows: %d rows", len(df))
    return df


def _load_actuals() -> pd.DataFrame:
    df = pd.read_csv(EVAL_PATH)
    if "record_type" in df.columns:
        df = df[df["record_type"].astype(str).str.lower() == "actual"].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["date", "value"])
    logger.info("Loaded actuals: %d rows / %d entities", len(df), df["entity_key"].nunique())
    return df


# ---------------------------------------------------------------------------
# Sandbox scope: latest window per entity, 5 entities chosen for volume diversity
# ---------------------------------------------------------------------------
def _select_sandbox_entities(actuals: pd.DataFrame, windows: pd.DataFrame) -> list[str]:
    entities = sorted(set(windows["entity_key"]).intersection(actuals["entity_key"]))
    if not entities:
        return []
    volume = (
        actuals[actuals["entity_key"].isin(entities)]
        .groupby("entity_key")["value"].sum().sort_values()
    )
    ordered = list(volume.index)
    n = len(ordered)
    k = min(SANDBOX_ENTITY_COUNT, n)
    idx = np.unique(np.linspace(0, n - 1, k).round().astype(int))
    selected = [ordered[i] for i in idx]
    logger.info("Selected %d sandbox entities (volume diversity): %s", len(selected), selected)
    return selected


def _build_scope(windows: pd.DataFrame, selected: list[str]) -> pd.DataFrame:
    ts = _now()
    latest = (
        windows.sort_values(["entity_key", "window_id"])
        .groupby("entity_key", as_index=False)
        .tail(1)
        .copy()
    )
    rows = []
    for _, w in latest.iterrows():
        is_sel = w["entity_key"] in selected
        rows.append(
            {
                "run_id": RUN_ID,
                "entity_key": w["entity_key"],
                "window_id": int(w["window_id"]),
                "train_start_date": w["train_start_date"],
                "train_end_date": w["train_end_date"],
                "test_start_date": w["test_start_date"],
                "test_end_date": w["test_end_date"],
                "selected_for_sandbox": is_sel,
                "selection_reason": (
                    "selected_latest_window_volume_diversity"
                    if is_sel
                    else "not_selected"
                ),
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Dependency check artifact
# ---------------------------------------------------------------------------
def _build_dependency_check(models: list[str]) -> pd.DataFrame:
    ts = _now()
    rows = []
    for model in models:
        options = DEPENDENCY_OPTIONS.get(model, [])
        seen: set[str] = set()
        usable_option = _first_available_option(model)
        for option in options:
            for mod in option:
                if mod in seen:
                    continue
                seen.add(mod)
                avail = _module_available(mod)
                rows.append(
                    {
                        "model_name": model,
                        "dependency_name": mod,
                        "required_for_sandbox": True,
                        "available": avail,
                        "status": "available" if avail else "missing",
                        "notes": (
                            "satisfies sandbox backend (any one option-set suffices)"
                            if usable_option is not None
                            else "no complete option-set available for this model"
                        ),
                        "created_timestamp": ts,
                    }
                )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Sandbox execution
# ---------------------------------------------------------------------------
def _run_model(
    model_name: str,
    option: list[str],
    scope_rows: pd.DataFrame,
    actuals: pd.DataFrame,
) -> tuple[list[dict], str, str]:
    """Run one challenger across the sandbox scope. Returns (forecast_rows,
    status, error_message)."""
    ts = _now()
    forecaster = FORECASTERS[model_name]
    forecast_rows: list[dict] = []
    for _, w in scope_rows.iterrows():
        entity = w["entity_key"]
        train_end = pd.to_datetime(w["train_end_date"])
        test_start = pd.to_datetime(w["test_start_date"])
        series = (
            actuals[(actuals["entity_key"] == entity) & (actuals["date"] <= train_end)]
            .sort_values("date")["value"].to_numpy(dtype=float)
        )
        if len(series) < 10:
            return [], "sandbox_failed", f"insufficient training history for {entity}"
        try:
            preds = np.asarray(forecaster(series, option), dtype=float)
        except Exception as exc:  # noqa: BLE001 - sandbox isolates model failures
            return [], "sandbox_failed", f"{type(exc).__name__}: {exc}"
        if len(preds) != HORIZON_DAYS:
            return [], "sandbox_failed", (
                f"expected {HORIZON_DAYS} forecasts, got {len(preds)}"
            )
        if not np.all(np.isfinite(preds)):
            return [], "sandbox_failed", "non-finite (NaN/inf) forecast values"
        for h in range(HORIZON_DAYS):
            forecast_rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model_name,
                    "entity_key": entity,
                    "window_id": int(w["window_id"]),
                    "forecast_date": (test_start + timedelta(days=h)).strftime("%Y-%m-%d"),
                    "horizon_day": h + 1,
                    "forecast_value": float(preds[h]),
                    "execution_mode": EXECUTION_MODE,
                    "created_timestamp": ts,
                }
            )
    return forecast_rows, "sandbox_passed", ""


def _build_execution(
    models: list[str],
    scope_rows: pd.DataFrame,
    actuals: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    ts = _now()
    n_entities = int(scope_rows["entity_key"].nunique())
    n_windows = int(scope_rows["window_id"].nunique())
    status_rows: list[dict] = []
    all_forecasts: list[dict] = []

    for model in models:
        option = _first_available_option(model)
        if option is None:
            status_rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "execution_mode": EXECUTION_MODE,
                    "sandbox_status": "sandbox_blocked_dependency_missing",
                    "attempted": False,
                    "forecast_rows": 0,
                    "entities_attempted": 0,
                    "windows_attempted": 0,
                    "error_message": "required forecasting dependency not installed",
                    "eligible_for_official_candidate": False,
                    "created_timestamp": ts,
                }
            )
            logger.info("%s: blocked - dependency missing", model)
            continue

        logger.info("%s: running sandbox using backend %s", model, option)
        forecasts, status, error = _run_model(model, option, scope_rows, actuals)
        all_forecasts.extend(forecasts)
        status_rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "execution_mode": EXECUTION_MODE,
                "sandbox_status": status,
                "attempted": True,
                "forecast_rows": len(forecasts),
                "entities_attempted": n_entities,
                "windows_attempted": n_windows,
                "error_message": error,
                "eligible_for_official_candidate": status == "sandbox_passed",
                "created_timestamp": ts,
            }
        )

    forecasts_df = (
        pd.DataFrame(all_forecasts, columns=FORECAST_COLUMNS)
        if all_forecasts
        else pd.DataFrame(columns=FORECAST_COLUMNS)
    )
    return pd.DataFrame(status_rows), forecasts_df


# ---------------------------------------------------------------------------
# Contract validation
# ---------------------------------------------------------------------------
def _validate_contract(
    status_df: pd.DataFrame, forecasts_df: pd.DataFrame
) -> pd.DataFrame:
    ts = _now()
    rows: list[dict] = []

    def add(model: str, check: str, status: str, details: str) -> None:
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "check_name": check,
                "status": status,
                "details": details,
                "created_timestamp": ts,
            }
        )

    for _, s in status_df.iterrows():
        model = s["model_name"]
        if s["sandbox_status"] != "sandbox_passed":
            add(
                model,
                "forecast_presence",
                "not_applicable_blocked",
                f"no sandbox forecasts to validate (status={s['sandbox_status']})",
            )
            continue

        fc = forecasts_df[forecasts_df["model_name"] == model]
        missing = [c for c in FORECAST_COLUMNS if c not in fc.columns]
        add(
            model,
            "required_columns_present",
            "pass" if not missing else "fail",
            "all contract columns present" if not missing else f"missing: {missing}",
        )
        add(
            model,
            "execution_mode_is_sandbox",
            "pass" if (fc["execution_mode"] == EXECUTION_MODE).all() else "fail",
            f"execution_mode values: {sorted(fc['execution_mode'].unique())}",
        )
        vals = pd.to_numeric(fc["forecast_value"], errors="coerce")
        add(
            model,
            "no_nan_values",
            "pass" if not vals.isna().any() else "fail",
            f"nan_count={int(vals.isna().sum())}",
        )
        add(
            model,
            "no_inf_values",
            "pass" if np.isfinite(vals.to_numpy()).all() else "fail",
            f"inf_count={int((~np.isfinite(vals.to_numpy())).sum())}",
        )
        hd = pd.to_numeric(fc["horizon_day"], errors="coerce")
        add(
            model,
            "horizon_day_in_range",
            "pass" if hd.between(1, HORIZON_DAYS).all() else "fail",
            f"min={hd.min()} max={hd.max()}",
        )
        grp = fc.groupby(["entity_key", "window_id"]).size()
        add(
            model,
            "rows_per_entity_window_equal_horizon",
            "pass" if (grp == HORIZON_DAYS).all() else "fail",
            f"counts={sorted(grp.unique().tolist())}",
        )
        neg = int((vals < 0).sum())
        add(
            model,
            "negative_value_policy_reported_not_corrected",
            "pass",
            f"negative_count={neg} (reported only; not corrected in sandbox)",
        )

    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Summary + report + recommendation
# ---------------------------------------------------------------------------
def _decide_recommendation(status_df: pd.DataFrame) -> str:
    attempted = int(status_df["attempted"].sum())
    passed = int((status_df["sandbox_status"] == "sandbox_passed").sum())
    failed = int((status_df["sandbox_status"] == "sandbox_failed").sum())
    blocked = int(
        (status_df["sandbox_status"] == "sandbox_blocked_dependency_missing").sum()
    )
    if attempted == 0 and blocked == len(status_df):
        return "BLOCK_5.29C_PENDING_DEPENDENCY_RESOLUTION"
    if failed > 0 and passed == 0:
        return "BLOCK_5.29C_PENDING_SANDBOX_FIX"
    if passed > 0 and failed == 0:
        return "PROCEED_TO_5.29C_CHALLENGER_OFFICIAL_EXECUTION_PREP"
    return "BLOCK_5.29C_PENDING_SANDBOX_FIX"


def _build_summary(
    status_df: pd.DataFrame, forecasts_df: pd.DataFrame, scope_rows: pd.DataFrame
) -> pd.DataFrame:
    ts = _now()
    selected = scope_rows[scope_rows["selected_for_sandbox"]]
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "planned_challengers": len(status_df),
                "models_attempted": int(status_df["attempted"].sum()),
                "models_passed": int(
                    (status_df["sandbox_status"] == "sandbox_passed").sum()
                ),
                "models_failed": int(
                    (status_df["sandbox_status"] == "sandbox_failed").sum()
                ),
                "models_blocked_dependency_missing": int(
                    (
                        status_df["sandbox_status"]
                        == "sandbox_blocked_dependency_missing"
                    ).sum()
                ),
                "sandbox_forecast_rows": int(len(forecasts_df)),
                "entities": int(selected["entity_key"].nunique()),
                "windows": int(selected["window_id"].nunique()),
                "official_execution_allowed": False,
                "created_timestamp": ts,
            }
        ]
    )


def _build_report(
    dep_df: pd.DataFrame,
    scope_rows: pd.DataFrame,
    status_df: pd.DataFrame,
    contract_df: pd.DataFrame,
    summary: pd.DataFrame,
    recommendation: str,
) -> str:
    s = summary.iloc[0]
    selected = scope_rows[scope_rows["selected_for_sandbox"]]
    avail = dep_df[dep_df["available"]]["dependency_name"].unique().tolist()
    missing = sorted(dep_df[~dep_df["available"]]["dependency_name"].unique().tolist())
    candidates = status_df[status_df["eligible_for_official_candidate"]][
        "model_name"
    ].tolist()

    lines = [
        "# Block 5.29B - Challenger Sandbox Execution Report",
        "",
        f"Generated: {_now()}",
        "",
        "## 1. Dependency State",
        "",
        f"- Available forecasting backends: {avail or 'none'}",
        f"- Missing forecasting backends: {missing or 'none'}",
        "",
        "## 2. Sandbox Scope",
        "",
        "- Scope: controlled subset (NOT the full 454-window backtest).",
        f"- Entities selected: {s['entities']} (volume-diversity selection).",
        f"- Windows per entity: {s['windows']} (latest window).",
        "",
        "| entity_key | window_id | train_end_date | test_start_date | test_end_date |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, r in selected.iterrows():
        lines.append(
            f"| {r['entity_key']} | {r['window_id']} | {r['train_end_date']} | "
            f"{r['test_start_date']} | {r['test_end_date']} |"
        )

    lines += [
        "",
        "## 3. Execution Status",
        "",
        "| model_name | sandbox_status | attempted | forecast_rows | eligible_candidate |",
        "| --- | --- | --- | --- | --- |",
    ]
    for _, r in status_df.iterrows():
        lines.append(
            f"| {r['model_name']} | {r['sandbox_status']} | {r['attempted']} | "
            f"{r['forecast_rows']} | {r['eligible_for_official_candidate']} |"
        )

    n_pass = int((contract_df["status"] == "pass").sum()) if len(contract_df) else 0
    n_fail = int((contract_df["status"] == "fail").sum()) if len(contract_df) else 0
    lines += [
        "",
        "## 4. Forecast Contract Validation",
        "",
        f"- Checks passed: {n_pass}",
        f"- Checks failed: {n_fail}",
        f"- Models with no forecasts (blocked/not-attempted): "
        f"{int((status_df['forecast_rows'] == 0).sum())}",
        "",
        "## 5. Official-Execution Candidate Assessment",
        "",
        f"- Eligible candidate models: {candidates or 'none'}",
        f"- official_execution_allowed: {s['official_execution_allowed']}",
        "  (Sandbox eligibility never sets official_execution_ready.)",
        "",
        "## 6. Remaining Blockers",
        "",
    ]
    if missing:
        lines.append(
            "- Forecasting dependencies are not installed. No challenger could run; "
            "all challengers are blocked pending dependency resolution."
        )
        lines.append(f"- Missing packages: {missing}")
    else:
        lines.append("- None related to dependencies.")

    lines += [
        "",
        "## 7. Recommendation",
        "",
        f"**{recommendation}**",
        "",
    ]
    if recommendation == "BLOCK_5.29C_PENDING_DEPENDENCY_RESOLUTION":
        lines.append(
            "All challenger forecasting backends are missing, so the sandbox could not "
            "execute any model. All planning/status artifacts were produced cleanly and "
            "no forecasts were fabricated. Resolve dependencies (with explicit approval) "
            "before re-running 5.29B."
        )
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    logger.info("=== Block 5.29B - Challenger Sandbox Execution ===")
    SANDBOX_DIR.mkdir(parents=True, exist_ok=True)

    registry = _load_registry()
    models = registry["model_name"].tolist()
    windows = _load_windows()
    actuals = _load_actuals()

    dep_df = _build_dependency_check(models)
    dep_df.to_csv(SANDBOX_DIR / "challenger_sandbox_dependency_check.csv", index=False)

    selected = _select_sandbox_entities(actuals, windows)
    scope_rows = _build_scope(windows, selected)
    scope_rows.to_csv(SANDBOX_DIR / "challenger_sandbox_scope.csv", index=False)

    sandbox_scope = scope_rows[scope_rows["selected_for_sandbox"]].copy()
    status_df, forecasts_df = _build_execution(models, sandbox_scope, actuals)
    status_df.to_csv(
        SANDBOX_DIR / "challenger_sandbox_execution_status.csv", index=False
    )
    forecasts_df.to_csv(
        SANDBOX_DIR / "challenger_sandbox_forecasts.csv", index=False
    )

    contract_df = _validate_contract(status_df, forecasts_df)
    contract_df.to_csv(
        SANDBOX_DIR / "challenger_sandbox_contract_validation.csv", index=False
    )

    summary = _build_summary(status_df, forecasts_df, scope_rows)
    summary.to_csv(SANDBOX_DIR / "challenger_sandbox_summary.csv", index=False)

    recommendation = _decide_recommendation(status_df)
    report = _build_report(
        dep_df, scope_rows, status_df, contract_df, summary, recommendation
    )
    (SANDBOX_DIR / "challenger_sandbox_report.md").write_text(report, encoding="utf-8")

    logger.info(
        "Sandbox complete: attempted=%d passed=%d failed=%d blocked=%d forecasts=%d",
        int(status_df["attempted"].sum()),
        int((status_df["sandbox_status"] == "sandbox_passed").sum()),
        int((status_df["sandbox_status"] == "sandbox_failed").sum()),
        int((status_df["sandbox_status"] == "sandbox_blocked_dependency_missing").sum()),
        len(forecasts_df),
    )
    logger.info("Recommendation: %s", recommendation)


if __name__ == "__main__":
    main()
