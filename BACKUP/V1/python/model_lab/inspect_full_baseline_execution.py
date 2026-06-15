"""Inspect and validate Stage 5.10 full baseline execution outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_full_baseline_execution")

FULL_BASELINE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "full_baseline"
FULL_BASELINE_FORECASTS = FULL_BASELINE_DIR / "full_baseline_forecasts.csv"
FULL_BASELINE_STATUS = FULL_BASELINE_DIR / "full_baseline_execution_status.csv"
FULL_BASELINE_SUMMARY = FULL_BASELINE_DIR / "full_baseline_summary.csv"
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
    "windows_executed",
    "entities_executed",
    "models_executed",
    "jobs_planned",
    "jobs_executed",
    "jobs_failed",
    "forecast_rows",
    "created_timestamp",
}


def _require_file(path) -> None:
    """Validate that a required full-baseline output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required full-baseline output missing: {path}")


def inspect_full_baseline_execution() -> dict[str, object]:
    """Inspect full baseline outputs and issue metrics-stage recommendation."""

    for path in (
        FULL_BASELINE_FORECASTS,
        FULL_BASELINE_STATUS,
        FULL_BASELINE_SUMMARY,
        EXECUTION_CONFIG,
    ):
        _require_file(path)

    forecasts = pd.read_csv(FULL_BASELINE_FORECASTS, parse_dates=["forecast_date"])
    statuses = pd.read_csv(FULL_BASELINE_STATUS)
    summary = pd.read_csv(FULL_BASELINE_SUMMARY)

    missing_forecast_columns = sorted(FORECAST_COLUMNS - set(forecasts.columns))
    if missing_forecast_columns:
        raise ValueError(
            f"full_baseline_forecasts.csv missing columns: {missing_forecast_columns}"
        )
    missing_summary_columns = sorted(SUMMARY_COLUMNS - set(summary.columns))
    if missing_summary_columns:
        raise ValueError(
            f"full_baseline_summary.csv missing columns: {missing_summary_columns}"
        )

    models = set(statuses["model_name"])
    if models != BASELINE_MODELS:
        raise ValueError(f"Full baseline model mismatch: {sorted(models)}")
    if len(statuses) != 3178:
        raise ValueError(f"Expected 3178 baseline jobs, found {len(statuses)}")
    if set(forecasts["model_name"]) - BASELINE_MODELS:
        raise ValueError("Forecast output contains challenger models.")

    jobs_executed = int((statuses["status"] == "completed").sum())
    jobs_failed = int((statuses["status"] == "failed").sum())
    expected_forecast_rows = jobs_executed * 30
    if len(forecasts) != expected_forecast_rows:
        raise ValueError(
            f"Forecast rows {len(forecasts)} != completed jobs x 30 "
            f"({expected_forecast_rows})."
        )
    if not forecasts.empty:
        numeric_forecasts = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
        if not numeric_forecasts.notna().all():
            raise ValueError("Full baseline forecasts contain non-numeric values.")
        if not np.isfinite(numeric_forecasts.to_numpy(dtype=float)).all():
            raise ValueError("Full baseline forecasts contain non-finite values.")
        if forecasts["horizon_day"].min() != 1 or forecasts["horizon_day"].max() != 30:
            raise ValueError("Full baseline horizon must span horizon_day 1 through 30.")
        if forecasts.groupby("job_id")["horizon_day"].nunique().min() != 30:
            raise ValueError("Each completed full baseline job must produce 30 days.")

    execution_text = EXECUTION_CONFIG.read_text(encoding="utf-8")
    if "training_enabled: false" not in execution_text or "dry_run: true" not in execution_text:
        raise ValueError("execution.yaml safety flags changed unexpectedly.")

    failure_rate = jobs_failed / len(statuses)
    recommendation = (
        "BLOCK METRICS STAGE" if failure_rate > 0.05 else "APPROVE METRICS STAGE"
    )
    entities_executed = statuses[statuses["status"] == "completed"][
        "entity_key"
    ].nunique()
    windows_executed = (
        statuses[statuses["status"] == "completed"][["entity_key", "window_id"]]
        .drop_duplicates()
        .shape[0]
    )

    logger.info("Jobs planned: %s", len(statuses))
    logger.info("Jobs executed: %s", jobs_executed)
    logger.info("Jobs failed: %s", jobs_failed)
    logger.info("Failure rate: %.4f", failure_rate)
    logger.info("Forecast rows: %s", len(forecasts))
    logger.info("Entities executed: %s", entities_executed)
    logger.info("Windows executed: %s", windows_executed)
    logger.info("Models executed: %s", sorted(models))
    logger.info("Recommendation: %s", recommendation)
    logger.info("Stage 5.10 full baseline inspection passed")
    return {
        "forecasts": forecasts,
        "statuses": statuses,
        "summary": summary,
        "recommendation": recommendation,
        "failure_rate": failure_rate,
    }


if __name__ == "__main__":
    inspect_full_baseline_execution()
