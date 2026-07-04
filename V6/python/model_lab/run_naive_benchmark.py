"""Generate lag-1 naive benchmark forecasts for every valid backtesting window.

This Stage 5.19 implementation creates reference forecasts only. It does not
run baseline or challenger models, calculate metrics, create rankings, or write
tournament outputs.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_naive_benchmark")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "benchmark_reference"
FORECASTS_OUTPUT = OUTPUT_DIR / "naive_benchmark_forecasts.csv"
STATUS_OUTPUT = OUTPUT_DIR / "naive_benchmark_status.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "naive_benchmark_summary.csv"

RUN_ID_PREFIX = "naive_benchmark"
FORECAST_HORIZON_DAYS = 30

FORECAST_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "forecast_date",
    "horizon_day",
    "naive_forecast_value",
    "train_end_date",
    "last_training_actual_value",
    "created_timestamp",
]
STATUS_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "status",
    "message",
    "created_timestamp",
]
SUMMARY_COLUMNS = [
    "run_id",
    "windows_planned",
    "windows_completed",
    "windows_failed",
    "entities",
    "forecast_rows",
    "min_forecast_date",
    "max_forecast_date",
    "created_timestamp",
]


def _require_file(path) -> None:
    """Validate that a required input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required naive benchmark input missing: {path}")


def _load_windows() -> pd.DataFrame:
    """Load valid 30-day backtesting windows."""

    _require_file(WINDOWS_INPUT)
    windows = pd.read_csv(
        WINDOWS_INPUT,
        parse_dates=[
            "train_start_date",
            "train_end_date",
            "test_start_date",
            "test_end_date",
        ],
    )
    required_columns = {
        "entity_key",
        "window_id",
        "train_end_date",
        "test_start_date",
        "test_end_date",
        "forecast_horizon_days",
    }
    missing = required_columns.difference(windows.columns)
    if missing:
        raise ValueError(f"backtesting_windows.csv missing columns: {sorted(missing)}")

    valid_windows = windows[windows["forecast_horizon_days"] == FORECAST_HORIZON_DAYS]
    valid_windows = valid_windows.copy().sort_values(["entity_key", "window_id"])
    if valid_windows.empty:
        raise ValueError("No valid 30-day backtesting windows found.")
    return valid_windows


def _load_actuals() -> pd.DataFrame:
    """Load actual values only from the evaluation dataset."""

    _require_file(EVALUATION_DATASET)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    required_columns = {"entity_key", "date", "value", "record_type"}
    missing = required_columns.difference(actuals.columns)
    if missing:
        raise ValueError(f"evaluation_dataset.csv missing columns: {sorted(missing)}")

    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "value"])
    actuals = actuals.sort_values(["entity_key", "date"])
    if actuals.empty:
        raise ValueError("No valid actual rows found in evaluation_dataset.csv.")
    return actuals


def _last_training_actual(actuals_by_entity: dict[str, pd.DataFrame], window: pd.Series) -> float:
    """Return the last actual value at or before the window train_end_date."""

    entity_actuals = actuals_by_entity.get(str(window["entity_key"]))
    if entity_actuals is None or entity_actuals.empty:
        raise ValueError("No actual rows found for entity.")

    training_actuals = entity_actuals[entity_actuals["date"] <= window["train_end_date"]]
    if training_actuals.empty:
        raise ValueError("No training actual at or before train_end_date.")
    if training_actuals["date"].max() > window["train_end_date"]:
        raise ValueError("Training leakage detected.")
    return float(training_actuals.iloc[-1]["value"])


def _forecast_dates(window: pd.Series) -> pd.DatetimeIndex:
    """Build and validate the 30-day forecast horizon for a window."""

    dates = pd.date_range(window["test_start_date"], window["test_end_date"], freq="D")
    if len(dates) != FORECAST_HORIZON_DAYS:
        raise ValueError(
            "Forecast horizon must be exactly "
            f"{FORECAST_HORIZON_DAYS} days; found {len(dates)}."
        )
    return dates


def _write_outputs(
    forecasts: pd.DataFrame, statuses: pd.DataFrame, summary: pd.DataFrame
) -> None:
    """Write all naive benchmark outputs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(FORECASTS_OUTPUT, index=False)
    statuses.to_csv(STATUS_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    logger.info("Created %s with %s rows", FORECASTS_OUTPUT, len(forecasts))
    logger.info("Created %s with %s rows", STATUS_OUTPUT, len(statuses))
    logger.info("Created %s with %s rows", SUMMARY_OUTPUT, len(summary))


def run_naive_benchmark() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create lag-1 naive benchmark forecasts for every valid window."""

    logger.info("Stage 5.19 naive benchmark generation started")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    windows = _load_windows()
    actuals = _load_actuals()
    actuals_by_entity = {
        entity_key: group.sort_values("date").reset_index(drop=True)
        for entity_key, group in actuals.groupby("entity_key", sort=False)
    }

    forecast_rows = []
    status_rows = []

    for _, window in windows.iterrows():
        try:
            last_value = _last_training_actual(actuals_by_entity, window)
            dates = _forecast_dates(window)

            for horizon_day, forecast_date in enumerate(dates, start=1):
                forecast_rows.append(
                    {
                        "run_id": run_id,
                        "entity_key": window["entity_key"],
                        "window_id": int(window["window_id"]),
                        "forecast_date": forecast_date.date(),
                        "horizon_day": horizon_day,
                        "naive_forecast_value": last_value,
                        "train_end_date": window["train_end_date"].date(),
                        "last_training_actual_value": last_value,
                        "created_timestamp": timestamp,
                    }
                )
            status = "completed"
            message = "Naive benchmark forecast completed."
        except Exception as exc:  # pragma: no cover - operational status path
            status = "failed"
            message = f"{type(exc).__name__}: {exc}"

        status_rows.append(
            {
                "run_id": run_id,
                "entity_key": window["entity_key"],
                "window_id": int(window["window_id"]),
                "status": status,
                "message": message,
                "created_timestamp": timestamp,
            }
        )

    forecasts = pd.DataFrame(forecast_rows, columns=FORECAST_COLUMNS)
    statuses = pd.DataFrame(status_rows, columns=STATUS_COLUMNS)
    completed = int((statuses["status"] == "completed").sum())
    failed = int((statuses["status"] == "failed").sum())
    summary = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "windows_planned": len(windows),
                "windows_completed": completed,
                "windows_failed": failed,
                "entities": windows["entity_key"].nunique(),
                "forecast_rows": len(forecasts),
                "min_forecast_date": (
                    forecasts["forecast_date"].min() if not forecasts.empty else ""
                ),
                "max_forecast_date": (
                    forecasts["forecast_date"].max() if not forecasts.empty else ""
                ),
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )

    _write_outputs(forecasts, statuses, summary)
    logger.info(
        "Stage 5.19 naive benchmark generation completed: %s completed, %s failed",
        completed,
        failed,
    )
    return forecasts, statuses, summary


if __name__ == "__main__":
    run_naive_benchmark()
