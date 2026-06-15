"""Inspect Stage 5.9 baseline forecast and execution status outputs."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_baseline_forecasts")

FORECASTS_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "forecasts"
BASELINE_FORECASTS = FORECASTS_DIR / "baseline_forecasts.csv"
BASELINE_STATUS = FORECASTS_DIR / "baseline_execution_status.csv"


def _require_file(path) -> None:
    """Validate that a required output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required baseline output missing: {path}")


def inspect_baseline_forecasts() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Report baseline forecast and status output coverage."""

    _require_file(BASELINE_FORECASTS)
    _require_file(BASELINE_STATUS)

    forecasts = pd.read_csv(BASELINE_FORECASTS)
    statuses = pd.read_csv(BASELINE_STATUS)

    executed_jobs = int((statuses["status"] == "completed").sum())
    skipped_jobs = int(
        statuses["status"]
        .isin(["blocked_by_config", "dry_run_only", "skipped"])
        .sum()
    )
    failed_jobs = int((statuses["status"] == "failed").sum())

    logger.info("Forecast rows: %s", len(forecasts))
    logger.info("Executed jobs: %s", executed_jobs)
    logger.info("Skipped jobs: %s", skipped_jobs)
    logger.info("Failed jobs: %s", failed_jobs)
    logger.info("Models included: %s", sorted(statuses["model_name"].unique()))
    logger.info("Entities included: %s", statuses["entity_key"].nunique())

    if forecasts.empty:
        logger.info("Date range: no forecast rows")
        logger.info("Horizon day min/max: no forecast rows")
    else:
        forecasts["forecast_date"] = pd.to_datetime(forecasts["forecast_date"])
        logger.info(
            "Date range: %s to %s",
            forecasts["forecast_date"].min().date(),
            forecasts["forecast_date"].max().date(),
        )
        logger.info(
            "Horizon day min/max: %s/%s",
            int(forecasts["horizon_day"].min()),
            int(forecasts["horizon_day"].max()),
        )

    return forecasts, statuses


if __name__ == "__main__":
    inspect_baseline_forecasts()
