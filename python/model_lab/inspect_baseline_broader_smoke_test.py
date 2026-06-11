"""Inspect and validate Stage 5.9B broader baseline smoke-test outputs."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_baseline_broader_smoke_test")

SMOKE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "smoke_test_broader"
SMOKE_FORECASTS = SMOKE_DIR / "broader_smoke_forecasts.csv"
SMOKE_STATUS = SMOKE_DIR / "broader_smoke_execution_status.csv"
SMOKE_SUMMARY = SMOKE_DIR / "broader_smoke_summary.csv"
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
    """Validate that a required broader smoke-test output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required broader smoke-test output missing: {path}")


def inspect_baseline_broader_smoke_test() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Inspect broader smoke outputs and validate execution-only success criteria."""

    for path in (SMOKE_FORECASTS, SMOKE_STATUS, SMOKE_SUMMARY, EXECUTION_CONFIG):
        _require_file(path)

    forecasts = pd.read_csv(SMOKE_FORECASTS, parse_dates=["forecast_date"])
    statuses = pd.read_csv(SMOKE_STATUS)
    summary = pd.read_csv(SMOKE_SUMMARY)

    missing_forecast_columns = sorted(FORECAST_COLUMNS - set(forecasts.columns))
    if missing_forecast_columns:
        raise ValueError(
            f"broader_smoke_forecasts.csv missing columns: {missing_forecast_columns}"
        )
    missing_summary_columns = sorted(SUMMARY_COLUMNS - set(summary.columns))
    if missing_summary_columns:
        raise ValueError(
            f"broader_smoke_summary.csv missing columns: {missing_summary_columns}"
        )

    models = set(statuses["model_name"])
    if models != BASELINE_MODELS:
        raise ValueError(f"Broader smoke model mismatch: {sorted(models)}")
    if len(statuses) != 21:
        raise ValueError(f"Expected 21 broader smoke jobs, found {len(statuses)}")
    if statuses["entity_key"].nunique() != 3:
        raise ValueError("Expected exactly 3 entities in broader smoke status.")
    if statuses[["entity_key", "window_id"]].drop_duplicates().shape[0] != 3:
        raise ValueError("Expected exactly 1 window per entity.")
    if (statuses["status"] == "failed").any():
        failed = statuses[statuses["status"] == "failed"]
        raise ValueError(
            f"Broader smoke failures detected: {failed.to_dict('records')}"
        )
    if len(forecasts) != 630:
        raise ValueError(f"Expected 630 forecast rows, found {len(forecasts)}.")
    if not pd.to_numeric(forecasts["forecast_value"], errors="coerce").notna().all():
        raise ValueError("Broader smoke forecasts contain non-numeric values.")
    if forecasts["horizon_day"].min() != 1 or forecasts["horizon_day"].max() != 30:
        raise ValueError("Broader smoke horizon must span horizon_day 1 through 30.")
    if forecasts.groupby("job_id")["horizon_day"].nunique().min() != 30:
        raise ValueError("Each broader smoke job must produce 30 horizon days.")

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
    logger.info("Stage 5.9B broader baseline smoke test inspection passed")
    return forecasts, statuses, summary


if __name__ == "__main__":
    inspect_baseline_broader_smoke_test()
