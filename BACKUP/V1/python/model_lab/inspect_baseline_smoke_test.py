"""Inspect and validate Stage 5.9A baseline smoke-test outputs."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_baseline_smoke_test")

SMOKE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "smoke_test"
SMOKE_FORECASTS = SMOKE_DIR / "smoke_forecasts.csv"
SMOKE_STATUS = SMOKE_DIR / "smoke_execution_status.csv"
SMOKE_SUMMARY = SMOKE_DIR / "smoke_summary.csv"
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


def _require_file(path) -> None:
    """Validate that a required smoke-test output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required smoke-test output missing: {path}")


def inspect_baseline_smoke_test() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Inspect smoke-test outputs and validate execution-only success criteria."""

    for path in (SMOKE_FORECASTS, SMOKE_STATUS, SMOKE_SUMMARY, EXECUTION_CONFIG):
        _require_file(path)

    forecasts = pd.read_csv(SMOKE_FORECASTS, parse_dates=["forecast_date"])
    statuses = pd.read_csv(SMOKE_STATUS)
    summary = pd.read_csv(SMOKE_SUMMARY)

    missing_columns = sorted(FORECAST_COLUMNS - set(forecasts.columns))
    if missing_columns:
        raise ValueError(f"smoke_forecasts.csv missing columns: {missing_columns}")

    models = set(statuses["model_name"])
    if models != BASELINE_MODELS:
        raise ValueError(f"Smoke test model mismatch: {sorted(models)}")
    if len(statuses) != 7:
        raise ValueError(f"Expected 7 smoke jobs, found {len(statuses)}")
    if (statuses["status"] == "failed").any():
        failed = statuses[statuses["status"] == "failed"]
        raise ValueError(f"Smoke test failures detected: {failed.to_dict('records')}")
    if forecasts.empty:
        raise ValueError("Smoke test produced no forecast rows.")
    if not pd.to_numeric(forecasts["forecast_value"], errors="coerce").notna().all():
        raise ValueError("Smoke forecasts contain non-numeric values.")
    if forecasts["horizon_day"].min() != 1 or forecasts["horizon_day"].max() != 30:
        raise ValueError("Smoke forecast horizon must span horizon_day 1 through 30.")
    if forecasts.groupby("model_name")["horizon_day"].nunique().min() != 30:
        raise ValueError("Each smoke-test model must produce 30 horizon days.")

    execution_text = EXECUTION_CONFIG.read_text(encoding="utf-8")
    if "training_enabled: false" not in execution_text or "dry_run: true" not in execution_text:
        raise ValueError("execution.yaml safety flags changed unexpectedly.")

    jobs_executed = int((statuses["status"] == "completed").sum())
    jobs_failed = int((statuses["status"] == "failed").sum())
    logger.info("Jobs planned: %s", len(statuses))
    logger.info("Jobs executed: %s", jobs_executed)
    logger.info("Jobs failed: %s", jobs_failed)
    logger.info("Forecast rows: %s", len(forecasts))
    logger.info("Entity tested: %s", summary["entity_key"].iloc[0])
    logger.info("Window tested: %s", int(summary["window_id"].iloc[0]))
    logger.info("Models executed: %s", sorted(models))
    logger.info(
        "Forecast date range: %s to %s",
        forecasts["forecast_date"].min().date(),
        forecasts["forecast_date"].max().date(),
    )
    logger.info("Stage 5.9A baseline smoke test inspection passed")
    return forecasts, statuses, summary


if __name__ == "__main__":
    inspect_baseline_smoke_test()
