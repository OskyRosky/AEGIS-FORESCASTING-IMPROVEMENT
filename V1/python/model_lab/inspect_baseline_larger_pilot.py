"""Inspect and validate Stage 5.9C larger baseline pilot outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_baseline_larger_pilot")

PILOT_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "baseline_pilot"
PILOT_FORECASTS = PILOT_DIR / "baseline_pilot_forecasts.csv"
PILOT_STATUS = PILOT_DIR / "baseline_pilot_execution_status.csv"
PILOT_SUMMARY = PILOT_DIR / "baseline_pilot_summary.csv"
EXECUTION_CONFIG = PROJECT_ROOT / "config" / "execution.yaml"

BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}
FORECAST_COLUMNS = {
    "run_id",
    "job_id",
    "entity_key",
    "window_id",
    "model_name",
    "model_family",
    "forecast_date",
    "horizon_day",
    "forecast_value",
    "created_timestamp",
}
SUMMARY_COLUMNS = {
    "run_id",
    "entities_tested",
    "windows_tested",
    "models_tested",
    "jobs_planned",
    "jobs_executed",
    "jobs_failed",
    "forecast_rows",
    "created_timestamp",
}


def _require_file(path) -> None:
    """Validate that a required larger pilot output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required larger pilot output missing: {path}")


def inspect_baseline_larger_pilot() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Inspect larger pilot outputs and validate execution-only success criteria."""

    for path in (PILOT_FORECASTS, PILOT_STATUS, PILOT_SUMMARY, EXECUTION_CONFIG):
        _require_file(path)

    forecasts = pd.read_csv(PILOT_FORECASTS, parse_dates=["forecast_date"])
    statuses = pd.read_csv(PILOT_STATUS)
    summary = pd.read_csv(PILOT_SUMMARY)

    missing_forecast_columns = sorted(FORECAST_COLUMNS - set(forecasts.columns))
    if missing_forecast_columns:
        raise ValueError(
            f"baseline_pilot_forecasts.csv missing columns: {missing_forecast_columns}"
        )
    missing_summary_columns = sorted(SUMMARY_COLUMNS - set(summary.columns))
    if missing_summary_columns:
        raise ValueError(
            f"baseline_pilot_summary.csv missing columns: {missing_summary_columns}"
        )

    models = set(statuses["model_name"])
    if models != BASELINE_MODELS:
        raise ValueError(f"Larger pilot model mismatch: {sorted(models)}")
    if len(statuses) != 70:
        raise ValueError(f"Expected 70 pilot jobs, found {len(statuses)}")
    if statuses["entity_key"].nunique() != 10:
        raise ValueError("Expected exactly 10 entities in larger pilot status.")
    if statuses[["entity_key", "window_id"]].drop_duplicates().shape[0] != 10:
        raise ValueError("Expected exactly 1 window per entity.")
    if (statuses["status"] == "failed").any():
        failed = statuses[statuses["status"] == "failed"]
        raise ValueError(f"Larger pilot failures detected: {failed.to_dict('records')}")
    if len(forecasts) != 2100:
        raise ValueError(f"Expected 2100 forecast rows, found {len(forecasts)}.")

    numeric_forecasts = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
    if not numeric_forecasts.notna().all():
        raise ValueError("Larger pilot forecasts contain non-numeric values.")
    if not np.isfinite(numeric_forecasts.to_numpy(dtype=float)).all():
        raise ValueError("Larger pilot forecasts contain non-finite values.")
    if forecasts["horizon_day"].min() != 1 or forecasts["horizon_day"].max() != 30:
        raise ValueError("Larger pilot horizon must span horizon_day 1 through 30.")
    if forecasts.groupby("job_id")["horizon_day"].nunique().min() != 30:
        raise ValueError("Each larger pilot job must produce 30 horizon days.")

    execution_text = EXECUTION_CONFIG.read_text(encoding="utf-8")
    if "training_enabled: false" not in execution_text or "dry_run: true" not in execution_text:
        raise ValueError("execution.yaml safety flags changed unexpectedly.")

    jobs_executed = int((statuses["status"] == "completed").sum())
    jobs_failed = int((statuses["status"] == "failed").sum())
    entities = sorted(statuses["entity_key"].unique())
    windows = (
        statuses[["entity_key", "window_id"]]
        .drop_duplicates()
        .sort_values(["entity_key", "window_id"])
        .to_dict("records")
    )

    logger.info("Jobs planned: %s", len(statuses))
    logger.info("Jobs executed: %s", jobs_executed)
    logger.info("Jobs failed: %s", jobs_failed)
    logger.info("Forecast rows: %s", len(forecasts))
    logger.info("Entities tested: %s", entities)
    logger.info("Windows tested: %s", windows)
    logger.info("Models executed: %s", sorted(models))
    logger.info(
        "Forecast date range: %s to %s",
        forecasts["forecast_date"].min().date(),
        forecasts["forecast_date"].max().date(),
    )
    logger.info("Stage 5.9C larger baseline pilot inspection passed")
    return forecasts, statuses, summary


if __name__ == "__main__":
    inspect_baseline_larger_pilot()
