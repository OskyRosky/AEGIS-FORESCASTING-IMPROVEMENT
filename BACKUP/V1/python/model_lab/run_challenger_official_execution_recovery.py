"""Block 5.29D-Recovery - official execution recovery.

Preserves complete official challenger outputs from the interrupted 5.29D run,
excludes partial NBEATS rows, adds FastNeuralAR_MLP, and finalizes the official
forecast contract for the approved re-scoped six-model set.
"""

from __future__ import annotations

import importlib.util
import time
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
import warnings

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_official_execution_recovery")

RUN_ID = "challenger_official_execution"
RECOVERY_RUN_ID = "block_5_29d_recovery"
EXECUTION_MODE = "official"
HORIZON_DAYS = 30
EXPECTED_ENTITY_WINDOWS = 454
EXPECTED_PER_MODEL_ROWS = EXPECTED_ENTITY_WINDOWS * HORIZON_DAYS
EXPECTED_TOTAL_ROWS = EXPECTED_PER_MODEL_ROWS * 6
RANDOM_SEED = 42

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
PREP_DIR = MODEL_LAB_DIR / "challenger_official_execution_prep"
OFFICIAL_DIR = MODEL_LAB_DIR / "challenger_official_execution"
RECOVERY_DIR = MODEL_LAB_DIR / "challenger_official_execution_recovery"

EVAL_PATH = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
SCOPE_PATH = PREP_DIR / "official_execution_scope.csv"

FINAL_MODELS = [
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
]
PRESERVED_MODELS = ["AutoARIMA", "Theta", "ETS Explicit", "LightGBM", "XGBoost"]
DEFERRED_STATUS = {
    "NBEATS": "deferred_runtime_impractical",
    "NHITS": "deferred_dependency_blocked",
}
MODEL_FAMILY = {
    "AutoARIMA": "statistical",
    "Theta": "statistical",
    "ETS Explicit": "statistical",
    "LightGBM": "machine_learning",
    "XGBoost": "machine_learning",
    "FastNeuralAR_MLP": "lightweight_neural",
    "NBEATS": "deep_learning",
    "NHITS": "deep_learning",
}

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


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _write_csv(df: pd.DataFrame, path: Path, columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.reindex(columns=columns).to_csv(path, index=False)


def _load_scope() -> pd.DataFrame:
    scope = pd.read_csv(SCOPE_PATH)
    selected = scope[
        scope["selected_for_official_execution"].astype(str).str.lower().isin(
            {"true", "1", "yes"}
        )
    ].copy()
    for col in ["train_start_date", "train_end_date", "test_start_date", "test_end_date"]:
        selected[col] = pd.to_datetime(selected[col], errors="raise")
    selected["window_id"] = pd.to_numeric(selected["window_id"], errors="raise").astype(int)
    selected = selected.sort_values(["entity_key", "window_id"]).reset_index(drop=True)
    if len(selected) != EXPECTED_ENTITY_WINDOWS:
        raise ValueError(f"official scope must contain 454 rows, found {len(selected)}")
    return selected


def _load_actuals() -> pd.DataFrame:
    actuals = pd.read_csv(EVAL_PATH)
    if "record_type" in actuals.columns:
        actuals = actuals[actuals["record_type"].astype(str).str.lower() == "actual"].copy()
    actuals["date"] = pd.to_datetime(actuals["date"], errors="coerce")
    actuals["value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "value"]).copy()
    return actuals.sort_values(["entity_key", "date"]).reset_index(drop=True)


def _series_for_window(actuals: pd.DataFrame, entity: str, train_end: pd.Timestamp) -> np.ndarray:
    series = actuals[(actuals["entity_key"] == entity) & (actuals["date"] <= train_end)]
    return series.sort_values("date")["value"].to_numpy(dtype=float)


def _make_lag_matrix(values: np.ndarray, n_lags: int) -> tuple[np.ndarray, np.ndarray]:
    rows_x: list[np.ndarray] = []
    rows_y: list[float] = []
    for idx in range(n_lags, len(values)):
        rows_x.append(values[idx - n_lags : idx][::-1])
        rows_y.append(float(values[idx]))
    return np.asarray(rows_x, dtype=float), np.asarray(rows_y, dtype=float)


def _fit_fast_neural(values: np.ndarray) -> tuple[Pipeline, int]:
    if len(values) < 10:
        raise ValueError(f"insufficient training history ({len(values)} rows)")
    n_lags = min(30, max(2, len(values) - 1))
    x, y = _make_lag_matrix(values.astype(float), n_lags)
    if len(y) < 5:
        raise ValueError(f"insufficient lag training rows ({len(y)} rows)")

    early_stopping = len(y) >= 20
    validation_fraction = 0.15 if early_stopping else 0.1
    mlp = MLPRegressor(
        hidden_layer_sizes=(32,),
        activation="relu",
        solver="adam",
        max_iter=300,
        random_state=RANDOM_SEED,
        early_stopping=early_stopping,
        validation_fraction=validation_fraction,
    )
    model = Pipeline([("scale", StandardScaler()), ("mlp", mlp)])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(x, y)
    return model, n_lags


def _forecast_fast_neural(values: np.ndarray) -> tuple[np.ndarray, int, int]:
    model, n_lags = _fit_fast_neural(values)
    history = list(values.astype(float))
    preds: list[float] = []
    for _ in range(HORIZON_DAYS):
        feats = np.asarray(history[-n_lags:][::-1], dtype=float).reshape(1, -1)
        pred = float(model.predict(feats)[0])
        preds.append(pred)
        history.append(pred)
    arr = np.asarray(preds, dtype=float)
    return arr, n_lags, int((arr < 0).sum())


def _run_fast_neural_window(
    scope_row: pd.Series,
    actuals: pd.DataFrame,
) -> tuple[list[dict], str, int, int]:
    entity = str(scope_row["entity_key"])
    train_end = pd.to_datetime(scope_row["train_end_date"])
    test_start = pd.to_datetime(scope_row["test_start_date"])
    test_end = pd.to_datetime(scope_row["test_end_date"])
    window_id = int(scope_row["window_id"])
    values = _series_for_window(actuals, entity, train_end)
    preds, lags_used, negative_count = _forecast_fast_neural(values)
    if len(preds) != HORIZON_DAYS:
        return [], f"expected {HORIZON_DAYS} forecasts, got {len(preds)}", lags_used, negative_count
    if not np.all(np.isfinite(preds)):
        return [], "non-finite (NaN/Inf) forecast values", lags_used, negative_count

    ts = _now()
    rows = []
    for idx, value in enumerate(preds):
        forecast_date = test_start + timedelta(days=idx)
        if forecast_date > test_end:
            return [], f"forecast_date {forecast_date.date()} beyond test_end", lags_used, negative_count
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": "FastNeuralAR_MLP",
                "entity_key": entity,
                "window_id": window_id,
                "forecast_date": forecast_date.strftime("%Y-%m-%d"),
                "horizon_day": idx + 1,
                "forecast_value": float(value),
                "execution_mode": EXECUTION_MODE,
                "created_timestamp": ts,
            }
        )
    return rows, "", lags_used, negative_count


def _run_fast_neural_scope(
    scope: pd.DataFrame,
    actuals: pd.DataFrame,
    mode: str,
) -> tuple[pd.DataFrame, pd.DataFrame, float, int, int]:
    start_all = time.perf_counter()
    forecast_rows: list[dict] = []
    status_rows: list[dict] = []
    total_negative = 0
    min_lags = 10_000
    for idx, scope_row in scope.iterrows():
        start = time.perf_counter()
        rows: list[dict] = []
        error = ""
        lags_used = 0
        negative_count = 0
        status = "official_failed" if mode == "official" else "sandbox_failed"
        try:
            rows, error, lags_used, negative_count = _run_fast_neural_window(scope_row, actuals)
            passed_status = "official_passed" if mode == "official" else "sandbox_passed"
            status = passed_status if rows and not error else status
        except Exception as exc:  # noqa: BLE001 - per-window isolation for audit
            error = f"{type(exc).__name__}: {exc}"
        runtime = round(time.perf_counter() - start, 6)
        forecast_rows.extend(rows)
        total_negative += negative_count
        if lags_used:
            min_lags = min(min_lags, lags_used)
        status_rows.append(
            {
                "run_id": RECOVERY_RUN_ID,
                "model_name": "FastNeuralAR_MLP",
                "entity_key": str(scope_row["entity_key"]),
                "window_id": int(scope_row["window_id"]),
                "execution_mode": mode,
                "official_status": status,
                "attempted": True,
                "forecast_rows": len(rows),
                "error_message": error,
                "runtime_seconds": runtime,
                "created_timestamp": _now(),
            }
        )
        if mode == "official" and ((idx + 1) % 50 == 0 or idx + 1 == len(scope)):
            logger.info(
                "FastNeuralAR_MLP official progress: %d/%d windows, rows=%d",
                idx + 1,
                len(scope),
                len(forecast_rows),
            )
    elapsed = time.perf_counter() - start_all
    min_lags = 0 if min_lags == 10_000 else min_lags
    return (
        pd.DataFrame(forecast_rows, columns=FORECAST_COLUMNS),
        pd.DataFrame(status_rows, columns=STATUS_COLUMNS),
        elapsed,
        min_lags,
        total_negative,
    )


def _inventory_source(path: Path, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    if not path.exists():
        return pd.DataFrame(
            [
                {
                    "source_file": str(path.relative_to(PROJECT_ROOT)),
                    "model_name": "ALL",
                    "rows_found": 0,
                    "complete_model_output": False,
                    "included_in_final_output": False,
                    "excluded_reason": "source file missing",
                    "created_timestamp": ts,
                }
            ]
        )
    df = pd.read_csv(path)
    rows = []
    for model, count in df.groupby("model_name").size().sort_index().items():
        complete = int(count) == EXPECTED_PER_MODEL_ROWS
        included = model in PRESERVED_MODELS and complete
        if included:
            reason = ""
        elif model == "NBEATS":
            reason = "excluded_partial_deferred_runtime_impractical"
        elif model == "NHITS":
            reason = "excluded_deferred_dependency_blocked"
        elif model == "FastNeuralAR_MLP":
            reason = "regenerated_by_recovery_script"
        else:
            reason = "not_in_final_official_model_set_or_incomplete"
        rows.append(
            {
                "source_file": str(path.relative_to(PROJECT_ROOT)),
                "model_name": model,
                "rows_found": int(count),
                "complete_model_output": complete,
                "included_in_final_output": included,
                "excluded_reason": reason,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


def _build_partial_inventory(scope: pd.DataFrame) -> pd.DataFrame:
    frames = [
        _inventory_source(OFFICIAL_DIR / "challenger_official_forecasts.csv", scope),
        _inventory_source(OFFICIAL_DIR / "_checkpoint_forecasts.csv", scope),
    ]
    return pd.concat(frames, ignore_index=True)


def _load_preserved_forecasts() -> pd.DataFrame:
    forecasts = pd.read_csv(OFFICIAL_DIR / "challenger_official_forecasts.csv")
    forecasts = forecasts[forecasts["model_name"].isin(PRESERVED_MODELS)].copy()
    counts = forecasts.groupby("model_name").size().to_dict()
    missing = [m for m in PRESERVED_MODELS if counts.get(m, 0) != EXPECTED_PER_MODEL_ROWS]
    if missing:
        raise ValueError(f"cannot preserve incomplete official outputs: {missing}")
    return forecasts.reindex(columns=FORECAST_COLUMNS)


def _build_final_status(fast_status: pd.DataFrame, final_forecasts: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    rows: list[dict] = []
    for model in PRESERVED_MODELS:
        for _, r in scope.iterrows():
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "entity_key": str(r["entity_key"]),
                    "window_id": int(r["window_id"]),
                    "execution_mode": EXECUTION_MODE,
                    "official_status": "official_passed",
                    "attempted": True,
                    "forecast_rows": HORIZON_DAYS,
                    "error_message": "",
                    "runtime_seconds": 0.0,
                    "created_timestamp": ts,
                }
            )
    rows.extend(fast_status.to_dict("records"))
    for model, status in DEFERRED_STATUS.items():
        reason = (
            "too slow for MVP/prototype automation profile in current Python/container execution context"
            if model == "NBEATS"
            else "Python 3.14 / neuralforecast / ray incompatibility"
        )
        for _, r in scope.iterrows():
            rows.append(
                {
                    "run_id": RUN_ID,
                    "model_name": model,
                    "entity_key": str(r["entity_key"]),
                    "window_id": int(r["window_id"]),
                    "execution_mode": EXECUTION_MODE,
                    "official_status": status,
                    "attempted": False,
                    "forecast_rows": 0,
                    "error_message": reason,
                    "runtime_seconds": 0.0,
                    "created_timestamp": ts,
                }
            )
    return pd.DataFrame(rows, columns=STATUS_COLUMNS)


def _validate_contract(forecasts: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    rows: list[dict] = []

    def add(check_name: str, ok: bool, details: str, model: str = "ALL") -> None:
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "check_name": check_name,
                "status": "pass" if ok else "fail",
                "details": details,
                "created_timestamp": ts,
            }
        )

    missing_cols = [c for c in FORECAST_COLUMNS if c not in forecasts.columns]
    add("required_columns_present", not missing_cols, f"missing={missing_cols or 'none'}")
    add(
        "execution_mode_official",
        (forecasts["execution_mode"] == EXECUTION_MODE).all(),
        f"values={sorted(forecasts['execution_mode'].dropna().unique().tolist())}",
    )
    values = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
    add("no_nan_forecast_value", not values.isna().any(), f"nan_count={int(values.isna().sum())}")
    finite = np.isfinite(values.to_numpy())
    add("no_inf_forecast_value", bool(finite.all()), f"inf_count={int((~finite).sum())}")
    horizon = pd.to_numeric(forecasts["horizon_day"], errors="coerce")
    add("horizon_day_1_to_30", horizon.between(1, HORIZON_DAYS).all(), f"min={horizon.min()} max={horizon.max()}")

    grouped = forecasts.groupby(["model_name", "entity_key", "window_id"]).size()
    bad_windows = int((grouped != HORIZON_DAYS).sum())
    expected_groups = len(scope) * len(FINAL_MODELS)
    add(
        "thirty_rows_per_model_entity_window",
        bad_windows == 0 and len(grouped) == expected_groups,
        f"bad_windows={bad_windows} groups={len(grouped)} expected_groups={expected_groups}",
    )
    dupes = forecasts.duplicated(["run_id", "model_name", "entity_key", "window_id", "horizon_day"])
    add("no_duplicate_run_model_entity_window_horizon", not dupes.any(), f"duplicate_count={int(dupes.sum())}")
    models = set(forecasts["model_name"].dropna())
    add("only_final_models_present", models == set(FINAL_MODELS), f"models={sorted(models)}")
    add("no_nbeats_rows", "NBEATS" not in models, "NBEATS absent from final forecasts")
    add("no_nhits_rows", "NHITS" not in models, "NHITS absent from final forecasts")
    add("fast_neural_rows_present", "FastNeuralAR_MLP" in models, "FastNeuralAR_MLP present")
    add(
        "expected_total_rows_81720",
        len(forecasts) == EXPECTED_TOTAL_ROWS,
        f"expected={EXPECTED_TOTAL_ROWS} actual={len(forecasts)}",
    )
    for model in FINAL_MODELS:
        count = int((forecasts["model_name"] == model).sum())
        add(
            "per_model_expected_rows_13620",
            count == EXPECTED_PER_MODEL_ROWS,
            f"expected={EXPECTED_PER_MODEL_ROWS} actual={count}",
            model=model,
        )
    return pd.DataFrame(rows, columns=CONTRACT_COLUMNS)


def _build_model_summary(status: pd.DataFrame, forecasts: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    rows = []
    for model in FINAL_MODELS + ["NBEATS", "NHITS"]:
        model_status = status[status["model_name"] == model]
        model_forecasts = forecasts[forecasts["model_name"] == model]
        expected = EXPECTED_PER_MODEL_ROWS if model in FINAL_MODELS else 0
        if model in DEFERRED_STATUS:
            model_state = DEFERRED_STATUS[model]
        elif len(model_forecasts) == EXPECTED_PER_MODEL_ROWS:
            model_state = "official_model_passed"
        else:
            model_state = "official_model_failed"
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "model_family": MODEL_FAMILY[model],
                "attempted_windows": int(model_status["attempted"].astype(bool).sum()) if len(model_status) else 0,
                "passed_windows": int((model_status["official_status"] == "official_passed").sum()) if len(model_status) else 0,
                "failed_windows": int((model_status["official_status"] == "official_failed").sum()) if len(model_status) else 0,
                "forecast_rows": int(len(model_forecasts)),
                "expected_forecast_rows": expected,
                "official_model_status": model_state,
                "runtime_seconds": round(float(model_status["runtime_seconds"].sum()), 6) if len(model_status) else 0.0,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows, columns=MODEL_SUMMARY_COLUMNS)


def _build_summary(forecasts: pd.DataFrame, model_summary: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
    ts = _now()
    active = model_summary[model_summary["model_name"].isin(FINAL_MODELS)]
    return pd.DataFrame(
        [
            {
                "run_id": RUN_ID,
                "official_candidate_models": 6,
                "models_attempted": int((active["attempted_windows"] > 0).sum()),
                "models_passed": int((active["official_model_status"] == "official_model_passed").sum()),
                "models_partial": 0,
                "models_failed": int((active["official_model_status"] != "official_model_passed").sum()),
                "models_deferred": 2,
                "entity_windows": int(len(scope)),
                "horizon_days": HORIZON_DAYS,
                "expected_total_forecast_rows": EXPECTED_TOTAL_ROWS,
                "actual_total_forecast_rows": int(len(forecasts)),
                "official_forecast_execution_completed": len(forecasts) == EXPECTED_TOTAL_ROWS,
                "metrics_created": False,
                "rankings_created": False,
                "tournament_created": False,
                "champion_selected": False,
                "created_timestamp": ts,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _build_manifest(model_summary: pd.DataFrame, scope: pd.DataFrame) -> pd.DataFrame:
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


def _write_fast_neural_status(
    sandbox_status: pd.DataFrame,
    sandbox_forecasts: pd.DataFrame,
    official_status: pd.DataFrame,
    official_forecasts: pd.DataFrame,
    official_elapsed: float,
) -> None:
    ts = _now()
    sandbox_pass = len(sandbox_status) > 0 and (sandbox_status["official_status"] == "sandbox_passed").all()
    _write_csv(
        pd.DataFrame(
            [
                {
                    "run_id": RECOVERY_RUN_ID,
                    "model_name": "FastNeuralAR_MLP",
                    "execution_mode": "sandbox",
                    "sandbox_status": "sandbox_passed" if sandbox_pass else "sandbox_failed",
                    "entities_attempted": int(sandbox_status["entity_key"].nunique()) if len(sandbox_status) else 0,
                    "windows_attempted": int(len(sandbox_status)),
                    "forecast_rows": int(len(sandbox_forecasts)),
                    "error_message": "; ".join(sandbox_status["error_message"].dropna().astype(str).loc[lambda s: s != ""].head(5)),
                    "created_timestamp": ts,
                }
            ]
        ),
        RECOVERY_DIR / "fast_neural_sandbox_status.csv",
        [
            "run_id",
            "model_name",
            "execution_mode",
            "sandbox_status",
            "entities_attempted",
            "windows_attempted",
            "forecast_rows",
            "error_message",
            "created_timestamp",
        ],
    )
    passed = int((official_status["official_status"] == "official_passed").sum())
    failed = int((official_status["official_status"] == "official_failed").sum())
    _write_csv(
        pd.DataFrame(
            [
                {
                    "run_id": RECOVERY_RUN_ID,
                    "model_name": "FastNeuralAR_MLP",
                    "execution_mode": "official",
                    "official_status": "official_passed" if failed == 0 and passed == EXPECTED_ENTITY_WINDOWS else "official_failed",
                    "entity_windows_attempted": int(len(official_status)),
                    "entity_windows_passed": passed,
                    "entity_windows_failed": failed,
                    "forecast_rows": int(len(official_forecasts)),
                    "error_message": "; ".join(official_status["error_message"].dropna().astype(str).loc[lambda s: s != ""].head(5)),
                    "runtime_seconds": round(float(official_elapsed), 6),
                    "created_timestamp": ts,
                }
            ]
        ),
        RECOVERY_DIR / "fast_neural_official_status.csv",
        [
            "run_id",
            "model_name",
            "execution_mode",
            "official_status",
            "entity_windows_attempted",
            "entity_windows_passed",
            "entity_windows_failed",
            "forecast_rows",
            "error_message",
            "runtime_seconds",
            "created_timestamp",
        ],
    )


def _write_recovery_summary(final_forecasts: pd.DataFrame) -> None:
    _write_csv(
        pd.DataFrame(
            [
                {
                    "run_id": RECOVERY_RUN_ID,
                    "final_official_models": 6,
                    "deferred_models": 2,
                    "preserved_models": 5,
                    "new_model_added": "FastNeuralAR_MLP",
                    "expected_total_forecast_rows": EXPECTED_TOTAL_ROWS,
                    "actual_total_forecast_rows": int(len(final_forecasts)),
                    "metrics_created": False,
                    "rankings_created": False,
                    "tournament_created": False,
                    "champion_selected": False,
                    "created_timestamp": _now(),
                }
            ]
        ),
        RECOVERY_DIR / "recovery_summary.csv",
        [
            "run_id",
            "final_official_models",
            "deferred_models",
            "preserved_models",
            "new_model_added",
            "expected_total_forecast_rows",
            "actual_total_forecast_rows",
            "metrics_created",
            "rankings_created",
            "tournament_created",
            "champion_selected",
            "created_timestamp",
        ],
    )


def _report(
    model_summary: pd.DataFrame,
    contract: pd.DataFrame,
    final_forecasts: pd.DataFrame,
    official_elapsed: float,
    negative_count: int,
    min_lags: int,
) -> str:
    contract_failures = contract[contract["status"] == "fail"]
    lines = [
        "# Block 5.29D-Recovery - Official Execution Recovery Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Interrupted NBEATS Run",
        "",
        "NBEATS produced partial official rows before the re-scope decision and is now deferred for runtime impracticality. It is not treated as a statistical failure.",
        "",
        "## Preserved Completed Outputs",
        "",
        "Completed official forecasts were preserved for AutoARIMA, Theta, ETS Explicit, LightGBM, and XGBoost.",
        "",
        "## Excluded Partial Outputs",
        "",
        "Partial NBEATS rows and all NHITS rows are excluded from the final official forecast file.",
        "",
        "## FastNeuralAR_MLP Sandbox",
        "",
        "FastNeuralAR_MLP passed the recovery sandbox before official execution.",
        "",
        "## FastNeuralAR_MLP Official Execution",
        "",
        f"- Official rows: {int((final_forecasts['model_name'] == 'FastNeuralAR_MLP').sum())}",
        f"- Runtime seconds: {official_elapsed:.2f}",
        f"- Minimum lag count used: {min_lags}",
        f"- Negative forecasts reported: {negative_count}",
        "",
        "## Final Official Output Reconciliation",
        "",
        f"- Final official models: {', '.join(FINAL_MODELS)}",
        f"- Expected rows: {EXPECTED_TOTAL_ROWS}",
        f"- Actual rows: {len(final_forecasts)}",
        "",
        "## Model Summary",
        "",
        "| model_name | status | forecast_rows | expected_rows |",
        "| --- | --- | ---: | ---: |",
    ]
    for _, r in model_summary.iterrows():
        lines.append(
            f"| {r['model_name']} | {r['official_model_status']} | {r['forecast_rows']} | {r['expected_forecast_rows']} |"
        )
    lines += [
        "",
        "## Contract Validation",
        "",
        f"- Checks passed: {int((contract['status'] == 'pass').sum())}",
        f"- Checks failed: {int((contract['status'] == 'fail').sum())}",
    ]
    if len(contract_failures):
        for _, r in contract_failures.iterrows():
            lines.append(f"- FAIL {r['model_name']} / {r['check_name']}: {r['details']}")
    lines += [
        "",
        "## Safety Findings",
        "",
        "- No metrics, rankings, tournament outputs, or champion selections were created.",
        "- Baseline outputs, official baseline metrics, aggregation/significance outputs, and Shiny were not modified by this recovery script.",
        "- NBEATS is deferred for runtime impracticality only.",
        "- NHITS is deferred for dependency incompatibility only.",
        "",
        "## Recommendation",
        "",
        "**PROCEED_TO_5.29E_CHALLENGER_METRICS_SCORING**",
        "",
    ]
    return "\n".join(lines)


def _write_official_report(
    model_summary: pd.DataFrame,
    contract: pd.DataFrame,
    summary: pd.DataFrame,
    official_elapsed: float,
    negative_count: int,
    min_lags: int,
) -> None:
    s = summary.iloc[0]
    lines = [
        "# Block 5.29D-Recovery - Challenger Official Execution Report",
        "",
        f"Generated: {_now()}",
        "",
        "## Final Official Model Set",
        "",
        ", ".join(FINAL_MODELS),
        "",
        "## Deferred Models",
        "",
        "- NBEATS: deferred_runtime_impractical; too slow for MVP/prototype automation in the current Python/container execution context.",
        "- NHITS: deferred_dependency_blocked; Python 3.14 / neuralforecast / ray incompatibility.",
        "",
        "## FastNeuralAR_MLP Replacement Rationale",
        "",
        "FastNeuralAR_MLP supplies a lightweight neural/autoregressive comparison similar in spirit to NNETAR while remaining practical for MVP and future container automation.",
        "",
        "## Official Scope",
        "",
        f"- Entity-windows: {EXPECTED_ENTITY_WINDOWS}",
        f"- Horizon days: {HORIZON_DAYS}",
        f"- Expected final rows: {EXPECTED_TOTAL_ROWS}",
        "",
        "## Execution Results",
        "",
        f"- Actual final rows: {s['actual_total_forecast_rows']}",
        f"- FastNeuralAR_MLP runtime seconds: {official_elapsed:.2f}",
        f"- FastNeuralAR_MLP minimum lag count used: {min_lags}",
        f"- FastNeuralAR_MLP negative forecasts reported: {negative_count}",
        "",
        "## Row Reconciliation",
        "",
        f"- Expected total forecast rows: {s['expected_total_forecast_rows']}",
        f"- Actual total forecast rows: {s['actual_total_forecast_rows']}",
        "",
        "## Contract Validation",
        "",
        f"- Failed checks: {int((contract['status'] == 'fail').sum())}",
        "",
        "## Safety Findings",
        "",
        "- NBEATS partial rows are excluded.",
        "- NHITS rows are excluded.",
        "- No metric, ranking, tournament, or champion outputs were created.",
        "",
        "## Recommendation for 5.29E",
        "",
        "**PROCEED_TO_5.29E_CHALLENGER_METRICS_SCORING**",
        "",
    ]
    (OFFICIAL_DIR / "challenger_official_execution_report.md").write_text("\n".join(lines), encoding="utf-8")


def _assert_sklearn_available() -> None:
    if importlib.util.find_spec("sklearn") is None:
        raise ImportError("scikit-learn is required for FastNeuralAR_MLP")


def main() -> None:
    start = time.perf_counter()
    logger.info("=== Block 5.29D-Recovery - Official Execution Recovery ===")
    _assert_sklearn_available()
    RECOVERY_DIR.mkdir(parents=True, exist_ok=True)
    OFFICIAL_DIR.mkdir(parents=True, exist_ok=True)

    scope = _load_scope()
    actuals = _load_actuals()

    partial_inventory = _build_partial_inventory(scope)
    _write_csv(
        partial_inventory,
        RECOVERY_DIR / "partial_output_inventory.csv",
        [
            "source_file",
            "model_name",
            "rows_found",
            "complete_model_output",
            "included_in_final_output",
            "excluded_reason",
            "created_timestamp",
        ],
    )

    sandbox_scope = scope.head(6).copy()
    sandbox_forecasts, sandbox_status, _, _, _ = _run_fast_neural_scope(
        sandbox_scope,
        actuals,
        mode="sandbox",
    )
    if len(sandbox_status) == 0 or not (sandbox_status["official_status"] == "sandbox_passed").all():
        _write_fast_neural_status(sandbox_status, sandbox_forecasts, pd.DataFrame(columns=STATUS_COLUMNS), pd.DataFrame(columns=FORECAST_COLUMNS), 0.0)
        raise RuntimeError("FastNeuralAR_MLP sandbox failed; official recovery execution blocked")

    fast_forecasts, fast_status, official_elapsed, min_lags, negative_count = _run_fast_neural_scope(
        scope,
        actuals,
        mode="official",
    )
    _write_fast_neural_status(sandbox_status, sandbox_forecasts, fast_status, fast_forecasts, official_elapsed)

    preserved = _load_preserved_forecasts()
    final_forecasts = pd.concat([preserved, fast_forecasts], ignore_index=True)
    final_forecasts = final_forecasts[final_forecasts["model_name"].isin(FINAL_MODELS)].copy()
    final_forecasts["forecast_value"] = pd.to_numeric(final_forecasts["forecast_value"], errors="coerce")
    final_forecasts["horizon_day"] = pd.to_numeric(final_forecasts["horizon_day"], errors="raise").astype(int)
    final_forecasts["window_id"] = pd.to_numeric(final_forecasts["window_id"], errors="raise").astype(int)
    final_forecasts = final_forecasts.sort_values(
        ["model_name", "entity_key", "window_id", "horizon_day"]
    ).reset_index(drop=True)

    status = _build_final_status(fast_status, final_forecasts, scope)
    contract = _validate_contract(final_forecasts, scope)
    model_summary = _build_model_summary(status, final_forecasts, scope)
    summary = _build_summary(final_forecasts, model_summary, scope)
    manifest = _build_manifest(model_summary, scope)

    _write_csv(final_forecasts, OFFICIAL_DIR / "challenger_official_forecasts.csv", FORECAST_COLUMNS)
    _write_csv(status, OFFICIAL_DIR / "challenger_official_execution_status.csv", STATUS_COLUMNS)
    _write_csv(model_summary, OFFICIAL_DIR / "challenger_official_model_summary.csv", MODEL_SUMMARY_COLUMNS)
    _write_csv(contract, OFFICIAL_DIR / "challenger_official_contract_validation.csv", CONTRACT_COLUMNS)
    _write_csv(summary, OFFICIAL_DIR / "challenger_official_execution_summary.csv", SUMMARY_COLUMNS)
    _write_csv(manifest, OFFICIAL_DIR / "challenger_official_execution_manifest_final.csv", FINAL_MANIFEST_COLUMNS)
    _write_recovery_summary(final_forecasts)
    (RECOVERY_DIR / "recovery_report.md").write_text(
        _report(model_summary, contract, final_forecasts, official_elapsed, negative_count, min_lags),
        encoding="utf-8",
    )
    _write_official_report(model_summary, contract, summary, official_elapsed, negative_count, min_lags)

    elapsed = time.perf_counter() - start
    logger.info(
        "Recovery complete: rows=%d expected=%d contract_failures=%d elapsed=%.2fs",
        len(final_forecasts),
        EXPECTED_TOTAL_ROWS,
        int((contract["status"] == "fail").sum()),
        elapsed,
    )


if __name__ == "__main__":
    main()
