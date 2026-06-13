"""Block 5.29D - Challenger Official Execution.

Runs the locked official challenger forecast scope for the six approved
challenger models only. This block produces forecasts and execution audit
artifacts only; it does not calculate metrics, rankings, tournaments, or
champions.
"""

from __future__ import annotations

import importlib
import importlib.util
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_official_execution")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
PREP_DIR = MODEL_LAB_DIR / "challenger_official_execution_prep"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_official_execution"
CHECKPOINT_STATUS_PATH = OUTPUT_DIR / "_checkpoint_execution_status.csv"
CHECKPOINT_FORECASTS_PATH = OUTPUT_DIR / "_checkpoint_forecasts.csv"

EVAL_PATH = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
SCOPE_PATH = PREP_DIR / "official_execution_scope.csv"
CANDIDATE_PATH = PREP_DIR / "official_challenger_candidate_list.csv"
MANIFEST_PATH = PREP_DIR / "official_execution_manifest.csv"
POLICY_PATH = PREP_DIR / "official_execution_locked_policy.csv"

RUN_ID = "challenger_official_execution"
EXECUTION_MODE = "official"
HORIZON_DAYS = 30
RANDOM_SEED = 42

APPROVED_MODELS = [
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "NBEATS",
]
DEFERRED_MODEL = "NHITS"

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

STATUS_COLUMNS = [
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "execution_mode",
    "official_status",
    "attempted",
    "forecast_rows",
    "error_message",
    "runtime_seconds",
    "created_timestamp",
]

MODEL_SUMMARY_COLUMNS = [
    "run_id",
    "model_name",
    "model_family",
    "attempted_windows",
    "passed_windows",
    "failed_windows",
    "forecast_rows",
    "expected_forecast_rows",
    "official_model_status",
    "runtime_seconds",
    "created_timestamp",
]

CONTRACT_COLUMNS = [
    "run_id",
    "model_name",
    "check_name",
    "status",
    "details",
    "created_timestamp",
]

SUMMARY_COLUMNS = [
    "run_id",
    "official_candidate_models",
    "models_attempted",
    "models_passed",
    "models_partial",
    "models_failed",
    "models_deferred",
    "entity_windows",
    "horizon_days",
    "expected_total_forecast_rows",
    "actual_total_forecast_rows",
    "official_forecast_execution_completed",
    "metrics_created",
    "rankings_created",
    "tournament_created",
    "champion_selected",
    "created_timestamp",
]

FINAL_MANIFEST_COLUMNS = [
    "run_id",
    "model_name",
    "execution_mode",
    "entity_window_count",
    "horizon_days",
    "expected_forecast_rows",
    "actual_forecast_rows",
    "official_execution_status",
    "created_timestamp",
]

DEPENDENCY_OPTIONS: dict[str, list[list[str]]] = {
    "AutoARIMA": [["pmdarima"]],
    "Theta": [["darts"]],
    "ETS Explicit": [["statsmodels"]],
    "LightGBM": [["lightgbm"]],
    "XGBoost": [["xgboost"]],
    "NBEATS": [["darts", "torch"]],
}

MODEL_FAMILY = {
    "AutoARIMA": "statistical",
    "Theta": "statistical",
    "ETS Explicit": "statistical",
    "LightGBM": "machine_learning",
    "XGBoost": "machine_learning",
    "NBEATS": "deep_learning",
    "NHITS": "deep_learning",
}


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _write_csv(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df = df.reindex(columns=columns)
    df.to_csv(path, index=False)


_IMPORT_CACHE: dict[str, bool] = {}


def _module_available(name: str) -> bool:
    if name in _IMPORT_CACHE:
        return _IMPORT_CACHE[name]
    available = False
    if importlib.util.find_spec(name) is not None:
        try:
            importlib.import_module(name)
            available = True
        except Exception:  # noqa: BLE001 - broken install means unavailable
            available = False
    _IMPORT_CACHE[name] = available
    return available


def _first_available_option(model_name: str) -> list[str] | None:
    for option in DEPENDENCY_OPTIONS.get(model_name, []):
        if all(_module_available(mod) for mod in option):
            return option
    return None


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
    import pmdarima as pm

    model = pm.auto_arima(
        values.astype(float),
        seasonal=False,
        start_p=0,
        start_q=0,
        max_p=2,
        max_q=2,
        max_order=4,
        stepwise=True,
        error_action="ignore",
        suppress_warnings=True,
        random_state=RANDOM_SEED,
    )
    return np.asarray(model.predict(HORIZON_DAYS), dtype=float)


def _forecast_theta(values: np.ndarray, option: list[str]) -> np.ndarray:
    from darts import TimeSeries
    from darts.models import Theta as DartsTheta

    ts = TimeSeries.from_values(values.astype(float))
    model = DartsTheta()
    model.fit(ts)
    return model.predict(HORIZON_DAYS).values().flatten().astype(float)


def _forecast_ets(values: np.ndarray, option: list[str]) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    model = ExponentialSmoothing(
        values.astype(float), trend="add", seasonal=None
    ).fit(optimized=True)
    return np.asarray(model.forecast(HORIZON_DAYS), dtype=float)


def _forecast_lightgbm(values: np.ndarray, option: list[str]) -> np.ndarray:
    import lightgbm as lgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = lgb.LGBMRegressor(
        n_estimators=100,
        random_state=RANDOM_SEED,
        verbosity=-1,
        deterministic=True,
        n_jobs=1,
    )
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags)


def _forecast_xgboost(values: np.ndarray, option: list[str]) -> np.ndarray:
    import xgboost as xgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = xgb.XGBRegressor(
        n_estimators=100,
        random_state=RANDOM_SEED,
        verbosity=0,
        n_jobs=1,
    )
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags)


def _forecast_nbeats(values: np.ndarray, option: list[str]) -> np.ndarray:
    import torch
    from darts import TimeSeries
    from darts.models import NBEATSModel

    torch.manual_seed(RANDOM_SEED)
    ts = TimeSeries.from_values(values.astype(float))
    model = NBEATSModel(
        input_chunk_length=min(30, max(2, len(values) // 2)),
        output_chunk_length=HORIZON_DAYS,
        n_epochs=5,
        random_state=RANDOM_SEED,
        pl_trainer_kwargs={
            "enable_checkpointing": False,
            "logger": False,
            "enable_progress_bar": False,
        },
    )
    model.fit(ts, verbose=False)
    return model.predict(HORIZON_DAYS, verbose=False).values().flatten().astype(float)


FORECASTERS: dict[str, Callable[[np.ndarray, list[str]], np.ndarray]] = {
    "AutoARIMA": _forecast_autoarima,
    "Theta": _forecast_theta,
    "ETS Explicit": _forecast_ets,
    "LightGBM": _forecast_lightgbm,
    "XGBoost": _forecast_xgboost,
    "NBEATS": _forecast_nbeats,
}


def _load_actuals() -> pd.DataFrame:
    df = pd.read_csv(EVAL_PATH)
    if "record_type" in df.columns:
        df = df[df["record_type"].astype(str).str.lower() == "actual"].copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["entity_key", "date", "value"]).copy()
    logger.info("Loaded actuals: %d rows / %d entities", len(df), df["entity_key"].nunique())
    return df


def _load_scope() -> pd.DataFrame:
    scope = pd.read_csv(SCOPE_PATH)
    selected = scope[
        scope["selected_for_official_execution"].astype(str).str.lower().isin(
            {"true", "1", "yes"}
        )
    ].copy()
    for col in ["train_start_date", "train_end_date", "test_start_date", "test_end_date"]:
        selected[col] = pd.to_datetime(selected[col], errors="coerce")
    selected["window_id"] = pd.to_numeric(selected["window_id"], errors="raise").astype(int)
    selected = selected.sort_values(["model_sort_key", "entity_key", "window_id"] if "model_sort_key" in selected.columns else ["entity_key", "window_id"])
    logger.info("Loaded official scope: %d entity-window rows", len(selected))
    return selected


def _load_candidates() -> tuple[pd.DataFrame, list[str]]:
    candidates = pd.read_csv(CANDIDATE_PATH)
    active = candidates[
        candidates["official_candidate"].astype(str).str.lower().isin({"true", "1", "yes"})
    ]["model_name"].tolist()
    if active != APPROVED_MODELS:
        raise ValueError(f"official candidate list mismatch: {active} != {APPROVED_MODELS}")
    return candidates, active


def _validate_inputs(scope: pd.DataFrame, models: list[str]) -> None:
    required_files = [SCOPE_PATH, CANDIDATE_PATH, MANIFEST_PATH, POLICY_PATH, EVAL_PATH]
    missing = [str(p) for p in required_files if not p.exists()]
    if missing:
        raise FileNotFoundError(f"missing required inputs: {missing}")
    if len(scope) != 454:
        raise ValueError(f"official scope must contain 454 rows, found {len(scope)}")
    if scope[["entity_key", "window_id"]].duplicated().any():
        raise ValueError("official scope contains duplicate entity_key/window_id pairs")
    if models != APPROVED_MODELS:
        raise ValueError("approved model list changed unexpectedly")
    if DEFERRED_MODEL in models:
        raise ValueError("NHITS must not be in the active official execution list")


def _series_for_window(actuals: pd.DataFrame, entity: str, train_end: pd.Timestamp) -> np.ndarray:
    return (
        actuals[(actuals["entity_key"] == entity) & (actuals["date"] <= train_end)]
        .sort_values("date")["value"]
        .to_numpy(dtype=float)
    )


def _run_one_window(
    model_name: str,
    option: list[str],
    scope_row: pd.Series,
    actuals: pd.DataFrame,
) -> tuple[list[dict], str]:
    entity = str(scope_row["entity_key"])
    train_end = pd.to_datetime(scope_row["train_end_date"])
    test_start = pd.to_datetime(scope_row["test_start_date"])
    test_end = pd.to_datetime(scope_row["test_end_date"])
    window_id = int(scope_row["window_id"])
    series = _series_for_window(actuals, entity, train_end)
    if len(series) < 10:
        return [], f"insufficient training history ({len(series)} rows)"

    preds = np.asarray(FORECASTERS[model_name](series, option), dtype=float)
    if len(preds) != HORIZON_DAYS:
        return [], f"expected {HORIZON_DAYS} forecasts, got {len(preds)}"
    if not np.all(np.isfinite(preds)):
        return [], "non-finite (NaN/Inf) forecast values"

    ts = _now()
    rows: list[dict] = []
    for i, value in enumerate(preds):
        forecast_date = test_start + timedelta(days=i)
        if forecast_date > test_end:
            return [], f"forecast_date {forecast_date.date()} beyond test_end {test_end.date()}"
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model_name,
                "entity_key": entity,
                "window_id": window_id,
                "forecast_date": forecast_date.strftime("%Y-%m-%d"),
                "horizon_day": i + 1,
                "forecast_value": float(value),
                "execution_mode": EXECUTION_MODE,
                "created_timestamp": ts,
            }
        )
    return rows, ""


def _execute_models(
    models: list[str], scope: pd.DataFrame, actuals: pd.DataFrame
) -> tuple[pd.DataFrame, pd.DataFrame]:
    if CHECKPOINT_STATUS_PATH.exists():
        status_df = pd.read_csv(CHECKPOINT_STATUS_PATH)
        logger.info("Loaded status checkpoint: %d rows", len(status_df))
    else:
        status_df = pd.DataFrame(columns=STATUS_COLUMNS)
    if CHECKPOINT_FORECASTS_PATH.exists():
        forecasts_df = pd.read_csv(CHECKPOINT_FORECASTS_PATH)
        logger.info("Loaded forecast checkpoint: %d rows", len(forecasts_df))
    else:
        forecasts_df = pd.DataFrame(columns=FORECAST_COLUMNS)

    completed_keys = set(
        tuple(x)
        for x in status_df[["model_name", "entity_key", "window_id"]].itertuples(
            index=False, name=None
        )
    ) if len(status_df) else set()
    total_jobs = len(models) * len(scope)
    completed_jobs = len(completed_keys)

    for model_name in models:
        option = _first_available_option(model_name)
        if option is None:
            logger.warning("%s: dependency option unavailable; marking all windows failed", model_name)
        else:
            logger.info("%s: running official execution with backend %s", model_name, option)

        for _, scope_row in scope.iterrows():
            start = time.perf_counter()
            entity = str(scope_row["entity_key"])
            window_id = int(scope_row["window_id"])
            key = (model_name, entity, window_id)
            if key in completed_keys:
                continue
            completed_jobs += 1
            rows: list[dict] = []
            error = ""
            attempted = option is not None
            status = "official_failed"

            if option is None:
                error = "required official forecasting dependency not importable"
            else:
                try:
                    rows, error = _run_one_window(model_name, option, scope_row, actuals)
                    status = "official_passed" if rows and not error else "official_failed"
                except Exception as exc:  # noqa: BLE001 - isolate model/window failures
                    error = f"{type(exc).__name__}: {exc}"
                    rows = []
                    status = "official_failed"

            runtime = round(time.perf_counter() - start, 6)
            if rows:
                forecasts_df = pd.concat(
                    [forecasts_df, pd.DataFrame(rows, columns=FORECAST_COLUMNS)],
                    ignore_index=True,
                )
            status_df = pd.concat(
                [
                    status_df,
                    pd.DataFrame(
                        [
                            {
                                "run_id": RUN_ID,
                                "model_name": model_name,
                                "entity_key": entity,
                                "window_id": window_id,
                                "execution_mode": EXECUTION_MODE,
                                "official_status": status,
                                "attempted": attempted,
                                "forecast_rows": len(rows),
                                "error_message": error,
                                "runtime_seconds": runtime,
                                "created_timestamp": _now(),
                            }
                        ],
                        columns=STATUS_COLUMNS,
                    ),
                ],
                ignore_index=True,
            )
            completed_keys.add(key)
            _write_csv(status_df, CHECKPOINT_STATUS_PATH, STATUS_COLUMNS)
            _write_csv(forecasts_df, CHECKPOINT_FORECASTS_PATH, FORECAST_COLUMNS)

            if completed_jobs % 25 == 0 or completed_jobs == total_jobs:
                logger.info(
                    "Progress: %d/%d model-window jobs complete; forecasts=%d",
                    completed_jobs,
                    total_jobs,
                    len(forecasts_df),
                )
                _materialize_outputs(status_df, forecasts_df, scope, partial=True)

    return status_df, forecasts_df


def _complete_status_grid(status_df: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    rows = []
    existing = set(
        tuple(x)
        for x in status_df[["model_name", "entity_key", "window_id"]].itertuples(
            index=False, name=None
        )
    ) if len(status_df) else set()
    for model in APPROVED_MODELS:
        for _, r in scope.iterrows():
            key = (model, str(r["entity_key"]), int(r["window_id"]))
            if key in existing:
                continue
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "entity_key": key[1],
                    "window_id": key[2],
                    "execution_mode": EXECUTION_MODE,
                    "official_status": "official_not_attempted",
                    "attempted": False,
                    "forecast_rows": 0,
                    "error_message": "not attempted yet; official execution incomplete",
                    "runtime_seconds": 0.0,
                    "created_timestamp": ts,
                }
            )
    nhits_rows = [
        {
            "run_id": RUN_ID,
            "model_name": DEFERRED_MODEL,
            "entity_key": str(r["entity_key"]),
            "window_id": int(r["window_id"]),
            "execution_mode": EXECUTION_MODE,
            "official_status": "official_skipped_deferred",
            "attempted": False,
            "forecast_rows": 0,
            "error_message": (
                "deferred_dependency_blocked: neuralforecast is not importable on "
                "Python 3.14 and ray has no compatible wheel; NHITS not run"
            ),
            "runtime_seconds": 0.0,
            "created_timestamp": ts,
        }
        for _, r in scope.iterrows()
    ]
    return pd.concat(
        [status_df, pd.DataFrame(rows), pd.DataFrame(nhits_rows)], ignore_index=True
    ).reindex(columns=STATUS_COLUMNS)


def _validate_contract(
    forecasts_df: pd.DataFrame, status_df: pd.DataFrame, scope: pd.DataFrame
) -> pd.DataFrame:
    ts = _now()
    rows: list[dict] = []
    expected_total = len(scope) * HORIZON_DAYS * len(APPROVED_MODELS)
    scope_dates = scope[["entity_key", "window_id", "test_start_date", "test_end_date"]].copy()
    scope_dates["window_id"] = scope_dates["window_id"].astype(int)

    def add(model: str, check: str, ok: bool, details: str) -> None:
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "check_name": check,
                "status": "pass" if ok else "fail",
                "details": details,
                "created_timestamp": ts,
            }
        )

    missing = [c for c in FORECAST_COLUMNS if c not in forecasts_df.columns]
    add("ALL", "required_columns_present", not missing, f"missing={missing or 'none'}")
    add(
        "ALL",
        "execution_mode_is_official",
        len(forecasts_df) == 0 or (forecasts_df["execution_mode"] == EXECUTION_MODE).all(),
        f"values={sorted(forecasts_df['execution_mode'].dropna().unique().tolist()) if 'execution_mode' in forecasts_df else []}",
    )
    vals = pd.to_numeric(forecasts_df.get("forecast_value", pd.Series(dtype=float)), errors="coerce")
    add("ALL", "no_nan_forecast_value", not vals.isna().any(), f"nan_count={int(vals.isna().sum())}")
    finite = np.isfinite(vals.to_numpy()) if len(vals) else np.asarray([], dtype=bool)
    add("ALL", "no_inf_forecast_value", bool(finite.all()), f"inf_count={int((~finite).sum())}")
    hd = pd.to_numeric(forecasts_df.get("horizon_day", pd.Series(dtype=float)), errors="coerce")
    add(
        "ALL",
        "horizon_day_1_to_30",
        len(hd) == 0 or hd.between(1, HORIZON_DAYS).all(),
        f"min={hd.min() if len(hd) else 'NA'} max={hd.max() if len(hd) else 'NA'}",
    )
    bad_models = sorted(set(forecasts_df.get("model_name", pd.Series(dtype=str))) - set(APPROVED_MODELS))
    add("ALL", "only_approved_models_forecasted", not bad_models, f"bad_models={bad_models or 'none'}")
    add(
        "ALL",
        "no_nhits_forecasts",
        DEFERRED_MODEL not in set(forecasts_df.get("model_name", pd.Series(dtype=str))),
        "NHITS absent from forecast rows",
    )

    merged = forecasts_df.merge(scope_dates, on=["entity_key", "window_id"], how="left")
    fdates = pd.to_datetime(merged.get("forecast_date", pd.Series(dtype=str)), errors="coerce")
    in_window = (
        fdates.notna()
        & merged["test_start_date"].notna()
        & merged["test_end_date"].notna()
        & (fdates >= merged["test_start_date"])
        & (fdates <= merged["test_end_date"])
    )
    add(
        "ALL",
        "forecast_date_within_official_test_window",
        len(merged) == 0 or bool(in_window.all()),
        f"out_of_window_count={int((~in_window).sum()) if len(merged) else 0}",
    )

    passed_status = status_df[status_df["official_status"] == "official_passed"]
    if len(passed_status):
        counts = forecasts_df.groupby(["model_name", "entity_key", "window_id"]).size()
        passed_index = pd.MultiIndex.from_frame(
            passed_status[["model_name", "entity_key", "window_id"]]
        )
        passed_counts = counts.reindex(passed_index, fill_value=0)
        ok = bool((passed_counts == HORIZON_DAYS).all())
        detail = f"bad_successful_windows={int((passed_counts != HORIZON_DAYS).sum())}"
    else:
        ok = True
        detail = "no passed windows"
    add("ALL", "thirty_rows_per_successful_model_entity_window", ok, detail)

    add(
        "ALL",
        "expected_total_rows_reconciled",
        len(forecasts_df) == expected_total,
        f"expected={expected_total} actual={len(forecasts_df)}",
    )

    for model in APPROVED_MODELS:
        fc = forecasts_df[forecasts_df["model_name"] == model]
        expected = len(scope) * HORIZON_DAYS
        add(
            model,
            "per_model_expected_rows_reconciled",
            len(fc) == expected,
            f"expected={expected} actual={len(fc)}",
        )

    return pd.DataFrame(rows, columns=CONTRACT_COLUMNS)


def _build_model_summary(status_df: pd.DataFrame, forecasts_df: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    rows: list[dict] = []
    for model in APPROVED_MODELS + [DEFERRED_MODEL]:
        model_status = status_df[status_df["model_name"] == model]
        model_forecasts = forecasts_df[forecasts_df["model_name"] == model]
        attempted = int(model_status["attempted"].astype(bool).sum())
        passed = int((model_status["official_status"] == "official_passed").sum())
        failed = int((model_status["official_status"] == "official_failed").sum())
        expected = 0 if model == DEFERRED_MODEL else len(scope) * HORIZON_DAYS
        if model == DEFERRED_MODEL:
            official_model_status = "official_model_deferred"
        elif passed == len(scope) and len(model_forecasts) == expected:
            official_model_status = "official_model_passed"
        elif passed > 0:
            official_model_status = "official_model_partial"
        else:
            official_model_status = "official_model_failed"
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_family": MODEL_FAMILY[model],
                "attempted_windows": attempted,
                "passed_windows": passed,
                "failed_windows": failed,
                "forecast_rows": int(len(model_forecasts)),
                "expected_forecast_rows": expected,
                "official_model_status": official_model_status,
                "runtime_seconds": round(float(model_status["runtime_seconds"].sum()), 6)
                if len(model_status)
                else 0.0,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows, columns=MODEL_SUMMARY_COLUMNS)


def _build_summary(model_summary: pd.DataFrame, forecasts_df: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    active = model_summary[model_summary["model_name"].isin(APPROVED_MODELS)]
    expected_total = len(scope) * HORIZON_DAYS * len(APPROVED_MODELS)
    all_passed = bool((active["official_model_status"] == "official_model_passed").all())
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "official_candidate_models": len(APPROVED_MODELS),
                "models_attempted": int((active["attempted_windows"] > 0).sum()),
                "models_passed": int((active["official_model_status"] == "official_model_passed").sum()),
                "models_partial": int((active["official_model_status"] == "official_model_partial").sum()),
                "models_failed": int((active["official_model_status"] == "official_model_failed").sum()),
                "models_deferred": int((model_summary["official_model_status"] == "official_model_deferred").sum()),
                "entity_windows": int(len(scope)),
                "horizon_days": HORIZON_DAYS,
                "expected_total_forecast_rows": expected_total,
                "actual_total_forecast_rows": int(len(forecasts_df)),
                "official_forecast_execution_completed": all_passed,
                "metrics_created": False,
                "rankings_created": False,
                "tournament_created": False,
                "champion_selected": False,
                "created_timestamp": ts,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _build_final_manifest(model_summary: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    rows = []
    for _, r in model_summary.iterrows():
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": r["model_name"],
                "execution_mode": EXECUTION_MODE,
                "entity_window_count": int(len(scope)),
                "horizon_days": HORIZON_DAYS,
                "expected_forecast_rows": int(r["expected_forecast_rows"]),
                "actual_forecast_rows": int(r["forecast_rows"]),
                "official_execution_status": r["official_model_status"],
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows, columns=FINAL_MANIFEST_COLUMNS)


def _recommendation(summary: pd.DataFrame, contract_df: pd.DataFrame, model_summary: pd.DataFrame) -> str:
    completed = bool(summary.iloc[0]["official_forecast_execution_completed"])
    contract_ok = not (contract_df["status"] == "fail").any()
    partial = (model_summary["official_model_status"] == "official_model_partial").any()
    if completed and contract_ok:
        return "PROCEED_TO_5.29E_CHALLENGER_METRICS_SCORING"
    if partial:
        return "BLOCK_5.29E_PENDING_OFFICIAL_EXECUTION_COMPLETION"
    return "BLOCK_5.29E_PENDING_OFFICIAL_EXECUTION_FIX"


def _load_candidates_for_report() -> pd.DataFrame:
    return pd.read_csv(CANDIDATE_PATH)


def _build_report(
    candidates: pd.DataFrame,
    scope: pd.DataFrame,
    model_summary: pd.DataFrame,
    contract_df: pd.DataFrame,
    summary: pd.DataFrame,
    recommendation: str,
    elapsed_seconds: float,
) -> str:
    s = summary.iloc[0]
    failures = model_summary[
        model_summary["official_model_status"].isin(
            ["official_model_partial", "official_model_failed"]
        )
    ]
    active = candidates[candidates["model_name"].isin(APPROVED_MODELS)]
    nhits = candidates[candidates["model_name"] == DEFERRED_MODEL]
    lines = [
        "# Block 5.29D - Challenger Official Execution Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Purpose",
        "",
        "Execute official challenger forecasts for the six approved candidates over the locked 5.29C official scope. This block creates forecast and execution audit artifacts only.",
        "",
        "## Official Candidate List",
        "",
        "| model_name | model_family | official_candidate |",
        "| --- | --- | --- |",
    ]
    for _, r in active.iterrows():
        lines.append(f"| {r['model_name']} | {r['model_family']} | {r['official_candidate']} |")
    lines += [
        "",
        "## NHITS Deferred Status",
        "",
        f"- NHITS was not run and produced zero forecast rows.",
        f"- Deferred reason: {nhits.iloc[0]['deferred_reason'] if len(nhits) else 'deferred_dependency_blocked'}",
        "",
        "## Official Scope",
        "",
        f"- Entity-window rows: {len(scope)}",
        f"- Horizon days: {HORIZON_DAYS}",
        f"- Expected rows per active model: {len(scope) * HORIZON_DAYS}",
        f"- Expected total rows: {s['expected_total_forecast_rows']}",
        "",
        "## Model Execution Results",
        "",
        "| model_name | status | attempted_windows | passed_windows | failed_windows | forecast_rows | expected_rows | runtime_seconds |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for _, r in model_summary.iterrows():
        lines.append(
            f"| {r['model_name']} | {r['official_model_status']} | {r['attempted_windows']} | "
            f"{r['passed_windows']} | {r['failed_windows']} | {r['forecast_rows']} | "
            f"{r['expected_forecast_rows']} | {r['runtime_seconds']} |"
        )
    contract_failures = contract_df[contract_df["status"] == "fail"]
    lines += [
        "",
        "## Forecast Row Reconciliation",
        "",
        f"- Expected total forecast rows: {s['expected_total_forecast_rows']}",
        f"- Actual total forecast rows: {s['actual_total_forecast_rows']}",
        "",
        "## Contract Validation",
        "",
        f"- Checks passed: {int((contract_df['status'] == 'pass').sum())}",
        f"- Checks failed: {int((contract_df['status'] == 'fail').sum())}",
    ]
    if len(contract_failures):
        for _, r in contract_failures.iterrows():
            lines.append(f"- FAIL {r['model_name']} / {r['check_name']}: {r['details']}")
    lines += [
        "",
        "## Failures",
        "",
    ]
    if len(failures):
        for _, r in failures.iterrows():
            lines.append(
                f"- {r['model_name']}: {r['official_model_status']} "
                f"({r['failed_windows']} failed windows, {r['forecast_rows']} rows)."
            )
    else:
        lines.append("- None.")
    lines += [
        "",
        "## Scope and Safety Findings",
        "",
        "- Used only the locked official_execution_scope.csv rows selected for official execution.",
        "- NHITS remained deferred_dependency_blocked and has no forecast rows.",
        "- Metrics, rankings, tournament outputs, champion selection, baseline outputs, aggregation/significance outputs, and Shiny were not modified by this script.",
        "",
        "## Recommendation for 5.29E",
        "",
        f"**{recommendation}**",
        "",
        "## Runtime",
        "",
        f"- Total execution time: {elapsed_seconds:.2f} seconds",
        "",
    ]
    return "\n".join(lines)


def _materialize_outputs(
    active_status_df: pd.DataFrame,
    forecasts_df: pd.DataFrame,
    scope: pd.DataFrame,
    partial: bool,
    elapsed_seconds: float = 0.0,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    status_df = _complete_status_grid(active_status_df, scope)
    contract_df = _validate_contract(forecasts_df, status_df, scope)
    model_summary = _build_model_summary(status_df, forecasts_df, scope)
    summary = _build_summary(model_summary, forecasts_df, scope)
    final_manifest = _build_final_manifest(model_summary, scope)
    recommendation = _recommendation(summary, contract_df, model_summary)
    report = _build_report(
        _load_candidates_for_report(),
        scope,
        model_summary,
        contract_df,
        summary,
        recommendation,
        elapsed_seconds,
    )
    _write_csv(forecasts_df, OUTPUT_DIR / "challenger_official_forecasts.csv", FORECAST_COLUMNS)
    _write_csv(status_df, OUTPUT_DIR / "challenger_official_execution_status.csv", STATUS_COLUMNS)
    _write_csv(model_summary, OUTPUT_DIR / "challenger_official_model_summary.csv", MODEL_SUMMARY_COLUMNS)
    _write_csv(contract_df, OUTPUT_DIR / "challenger_official_contract_validation.csv", CONTRACT_COLUMNS)
    _write_csv(summary, OUTPUT_DIR / "challenger_official_execution_summary.csv", SUMMARY_COLUMNS)
    _write_csv(final_manifest, OUTPUT_DIR / "challenger_official_execution_manifest_final.csv", FINAL_MANIFEST_COLUMNS)
    (OUTPUT_DIR / "challenger_official_execution_report.md").write_text(report, encoding="utf-8")
    if partial:
        logger.info("Materialized partial official artifacts for resume/audit.")
    return status_df, contract_df, model_summary, summary


def main() -> None:
    start = time.perf_counter()
    logger.info("=== Block 5.29D - Challenger Official Execution ===")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    candidates, models = _load_candidates()
    scope = _load_scope()
    _validate_inputs(scope, models)
    actuals = _load_actuals()

    status_df, forecasts_df = _execute_models(models, scope, actuals)
    elapsed = time.perf_counter() - start
    status_df, contract_df, model_summary, summary = _materialize_outputs(
        status_df,
        forecasts_df,
        scope,
        partial=False,
        elapsed_seconds=elapsed,
    )
    recommendation = _recommendation(summary, contract_df, model_summary)

    logger.info(
        "Official execution complete: models_passed=%d rows=%d expected=%d recommendation=%s",
        int(summary.iloc[0]["models_passed"]),
        len(forecasts_df),
        int(summary.iloc[0]["expected_total_forecast_rows"]),
        recommendation,
    )


if __name__ == "__main__":
    main()
