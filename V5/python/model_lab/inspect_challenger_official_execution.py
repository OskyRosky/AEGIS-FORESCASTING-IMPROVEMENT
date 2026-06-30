"""Block 5.29D - Challenger Official Execution Inspector.

Read-only validation for the official challenger forecast artifacts. The
inspector verifies contract, scope, and safety constraints and does not mutate
outputs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_official_execution_inspector")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_official_execution"
PREP_DIR = MODEL_LAB_DIR / "challenger_official_execution_prep"
SCOPE_PATH = PREP_DIR / "official_execution_scope.csv"

APPROVED_MODELS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "NBEATS",
}
DEFERRED_MODEL = "NHITS"
HORIZON_DAYS = 30
EXPECTED_ENTITY_WINDOWS = 454
EXPECTED_TOTAL_ROWS = 81720
EXPECTED_PER_MODEL_ROWS = 13620

REQUIRED_FILES = [
    "challenger_official_forecasts.csv",
    "challenger_official_execution_status.csv",
    "challenger_official_model_summary.csv",
    "challenger_official_contract_validation.csv",
    "challenger_official_execution_summary.csv",
    "challenger_official_execution_manifest_final.csv",
    "challenger_official_execution_report.md",
]

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

FORBIDDEN_OUTPUT_PATHS = [
    MODEL_LAB_DIR / "challenger_metrics",
    MODEL_LAB_DIR / "challenger_rankings",
    MODEL_LAB_DIR / "challenger_tournament",
    MODEL_LAB_DIR / "challenger_champion",
    MODEL_LAB_DIR / "rankings",
    MODEL_LAB_DIR / "tournament",
    MODEL_LAB_DIR / "champion",
]

PROTECTED_PATHS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "aggregation_hierarchy",
    MODEL_LAB_DIR / "statistical_significance",
    PROJECT_ROOT / "outputs" / "metrics",
    PROJECT_ROOT / "shiny_app",
]

_failures: list[str] = []
_checks = 0


def _check(condition: bool, message: str) -> None:
    global _checks
    _checks += 1
    if condition:
        logger.info("PASS: %s", message)
    else:
        logger.error("FAIL: %s", message)
        _failures.append(message)


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def _assert_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    _check(not missing, f"{name}: required columns present ({missing or 'all'})")


def _path_has_files(path: Path) -> bool:
    return path.exists() and any(path.iterdir()) if path.is_dir() else path.exists()


def main() -> int:
    logger.info("=== Block 5.29D - Challenger Official Execution Inspection ===")

    for fname in REQUIRED_FILES:
        _check((OUTPUT_DIR / fname).exists(), f"required file exists: {fname}")
    if _failures:
        return _finish()

    forecasts = pd.read_csv(OUTPUT_DIR / "challenger_official_forecasts.csv")
    status = pd.read_csv(OUTPUT_DIR / "challenger_official_execution_status.csv")
    model_summary = pd.read_csv(OUTPUT_DIR / "challenger_official_model_summary.csv")
    contract = pd.read_csv(OUTPUT_DIR / "challenger_official_contract_validation.csv")
    summary = pd.read_csv(OUTPUT_DIR / "challenger_official_execution_summary.csv")
    manifest = pd.read_csv(OUTPUT_DIR / "challenger_official_execution_manifest_final.csv")
    scope = pd.read_csv(SCOPE_PATH)

    _assert_columns(forecasts, FORECAST_COLUMNS, "forecasts")
    _assert_columns(status, STATUS_COLUMNS, "execution_status")
    _assert_columns(model_summary, MODEL_SUMMARY_COLUMNS, "model_summary")
    _assert_columns(summary, SUMMARY_COLUMNS, "summary")
    _assert_columns(manifest, [
        "run_id",
        "model_name",
        "execution_mode",
        "entity_window_count",
        "horizon_days",
        "expected_forecast_rows",
        "actual_forecast_rows",
        "official_execution_status",
        "created_timestamp",
    ], "final_manifest")

    selected_scope = scope[
        scope["selected_for_official_execution"].astype(str).str.lower().isin(
            {"true", "1", "yes"}
        )
    ].copy()
    selected_scope["window_id"] = pd.to_numeric(selected_scope["window_id"]).astype(int)
    for c in ["test_start_date", "test_end_date"]:
        selected_scope[c] = pd.to_datetime(selected_scope[c], errors="coerce")

    _check(len(selected_scope) == EXPECTED_ENTITY_WINDOWS, "locked scope has 454 entity-window rows")
    _check(len(forecasts) == EXPECTED_TOTAL_ROWS, "forecast row count equals 81,720")
    _check(set(forecasts["model_name"]).issubset(APPROVED_MODELS), "only six approved models appear in forecasts")
    _check(DEFERRED_MODEL not in set(forecasts["model_name"]), "NHITS does not appear in forecasts")
    _check((forecasts["execution_mode"] == "official").all(), "execution_mode is official for all forecasts")

    vals = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
    _check(not vals.isna().any(), "no NaN forecast_value")
    _check(np.isfinite(vals.to_numpy()).all(), "no Inf forecast_value")
    hd = pd.to_numeric(forecasts["horizon_day"], errors="coerce")
    _check(hd.between(1, HORIZON_DAYS).all(), "horizon_day only 1..30")

    dupes = forecasts.duplicated(["run_id", "model_name", "entity_key", "window_id", "horizon_day"])
    _check(not dupes.any(), "no duplicate run/model/entity/window/horizon forecast rows")

    merged = forecasts.merge(
        selected_scope[["entity_key", "window_id", "test_start_date", "test_end_date"]],
        on=["entity_key", "window_id"],
        how="left",
    )
    fdates = pd.to_datetime(merged["forecast_date"], errors="coerce")
    in_window = (
        fdates.notna()
        & merged["test_start_date"].notna()
        & merged["test_end_date"].notna()
        & (fdates >= merged["test_start_date"])
        & (fdates <= merged["test_end_date"])
    )
    _check(in_window.all(), "forecast_date aligns with locked official scope")

    per_model = forecasts.groupby("model_name").size().to_dict()
    bad_model_counts = {
        model: count
        for model, count in per_model.items()
        if count != EXPECTED_PER_MODEL_ROWS
    }
    missing_models = sorted(APPROVED_MODELS - set(per_model))
    _check(not bad_model_counts and not missing_models, "per-model row count equals 13,620 for all six models")

    valid_status = {
        "official_passed",
        "official_failed",
        "official_skipped_deferred",
        "official_not_attempted",
    }
    _check(set(status["official_status"]).issubset(valid_status), "official_status values are valid")
    active_status = status[status["model_name"].isin(APPROVED_MODELS)]
    _check(len(active_status) == EXPECTED_ENTITY_WINDOWS * len(APPROVED_MODELS), "status covers all active model-window combinations")
    _check(active_status["attempted"].astype(bool).all(), "all six candidates attempted for every official entity-window")
    nhits_status = status[status["model_name"] == DEFERRED_MODEL]
    _check(
        len(nhits_status) == EXPECTED_ENTITY_WINDOWS
        and (nhits_status["official_status"] == "official_skipped_deferred").all()
        and not nhits_status["attempted"].astype(bool).any(),
        "NHITS is documented only as official_skipped_deferred",
    )

    _check(not (contract["status"] == "fail").any(), "contract validation has no failed checks")

    summary_row = summary.iloc[0]
    _check(int(summary_row["expected_total_forecast_rows"]) == EXPECTED_TOTAL_ROWS, "summary expected rows = 81,720")
    _check(int(summary_row["actual_total_forecast_rows"]) == len(forecasts), "summary actual rows reconciles")
    _check(not _bool_series(summary["metrics_created"]).any(), "metrics_created = false")
    _check(not _bool_series(summary["rankings_created"]).any(), "rankings_created = false")
    _check(not _bool_series(summary["tournament_created"]).any(), "tournament_created = false")
    _check(not _bool_series(summary["champion_selected"]).any(), "champion_selected = false")

    for path in FORBIDDEN_OUTPUT_PATHS:
        _check(not _path_has_files(path), f"forbidden metrics/ranking/tournament/champion path absent or empty: {path.name}")
    for path in PROTECTED_PATHS:
        _check(path.exists(), f"protected path still present: {path}")

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for failure in _failures:
            logger.error("  - %s", failure)
        return 1
    logger.info("INSPECTION PASSED: official execution artifacts satisfy Block 5.29D.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
