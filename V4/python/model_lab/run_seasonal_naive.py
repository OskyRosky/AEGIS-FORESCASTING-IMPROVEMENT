"""Generate 30-day seasonal naive benchmark forecasts for valid windows.

This Stage 5.20 implementation creates an additional reference benchmark only.
It does not run baseline or challenger models, calculate metrics, create
rankings, modify the lag-1 benchmark reference outputs, or write tournament
outputs.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_seasonal_naive")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "seasonal_benchmark"
FORECASTS_OUTPUT = OUTPUT_DIR / "seasonal_naive_forecasts.csv"
STATUS_OUTPUT = OUTPUT_DIR / "seasonal_naive_status.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "seasonal_naive_summary.csv"

RUN_ID_PREFIX = "seasonal_naive"
FORECAST_HORIZON_DAYS = 30
SEASON_LENGTH_DAYS = 30

FORECAST_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "forecast_date",
    "horizon_day",
    "seasonal_naive_forecast_value",
    "reference_actual_date",
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
    "season_length_days",
    "min_forecast_date",
    "max_forecast_date",
    "created_timestamp",
]


def _require_file(path) -> None:
    """Validate that a required input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required seasonal naive input missing: {path}")


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


def _load_actual_lookup() -> dict[tuple[str, pd.Timestamp], float]:
    """Load actual observations into an exact entity/date lookup."""

    _require_file(EVALUATION_DATASET)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    required_columns = {"entity_key", "date", "value", "record_type"}
    missing = required_columns.difference(actuals.columns)
    if missing:
        raise ValueError(f"evaluation_dataset.csv missing columns: {sorted(missing)}")

    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "value"])
    actuals["date"] = actuals["date"].dt.normalize()
    actuals = actuals.sort_values(["entity_key", "date"])
    if actuals.empty:
        raise ValueError("No valid actual rows found in evaluation_dataset.csv.")
    if actuals.duplicated(["entity_key", "date"]).any():
        duplicates = actuals[actuals.duplicated(["entity_key", "date"], keep=False)]
        sample = duplicates[["entity_key", "date"]].head(10).to_dict(orient="records")
        raise ValueError(f"Duplicate actual rows found for entity/date: {sample}")

    return {
        (str(row.entity_key), row.date): float(row.value)
        for row in actuals.itertuples(index=False)
    }


def _forecast_dates(window: pd.Series) -> pd.DatetimeIndex:
    """Build and validate the 30-day forecast horizon for a window."""

    dates = pd.date_range(window["test_start_date"], window["test_end_date"], freq="D")
    if len(dates) != FORECAST_HORIZON_DAYS:
        raise ValueError(
            "Forecast horizon must be exactly "
            f"{FORECAST_HORIZON_DAYS} days; found {len(dates)}."
        )
    return dates


def _window_forecasts(
    run_id: str,
    timestamp: str,
    window: pd.Series,
    actual_lookup: dict[tuple[str, pd.Timestamp], float],
) -> list[dict[str, object]]:
    """Create all 30 seasonal naive rows for one window or fail the window."""

    rows = []
    entity_key = str(window["entity_key"])
    for horizon_day, forecast_date in enumerate(_forecast_dates(window), start=1):
        reference_actual_date = forecast_date.normalize() - pd.Timedelta(
            days=SEASON_LENGTH_DAYS
        )
        if reference_actual_date > window["train_end_date"].normalize():
            raise ValueError(
                "Reference actual date is beyond train_end_date; leakage risk."
            )
        lookup_key = (entity_key, reference_actual_date)
        if lookup_key not in actual_lookup:
            raise ValueError(
                "Missing seasonal reference actual for "
                f"{entity_key} on {reference_actual_date.date()}."
            )
        rows.append(
            {
                "run_id": run_id,
                "entity_key": entity_key,
                "window_id": int(window["window_id"]),
                "forecast_date": forecast_date.date(),
                "horizon_day": horizon_day,
                "seasonal_naive_forecast_value": actual_lookup[lookup_key],
                "reference_actual_date": reference_actual_date.date(),
                "created_timestamp": timestamp,
            }
        )
    return rows


def _write_outputs(
    forecasts: pd.DataFrame, statuses: pd.DataFrame, summary: pd.DataFrame
) -> None:
    """Write all seasonal naive benchmark outputs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(FORECASTS_OUTPUT, index=False)
    statuses.to_csv(STATUS_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    logger.info("Created %s with %s rows", FORECASTS_OUTPUT, len(forecasts))
    logger.info("Created %s with %s rows", STATUS_OUTPUT, len(statuses))
    logger.info("Created %s with %s rows", SUMMARY_OUTPUT, len(summary))


def run_seasonal_naive() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Create 30-day seasonal naive forecasts for every valid window."""

    logger.info("Stage 5.20 seasonal naive generation started")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    windows = _load_windows()
    actual_lookup = _load_actual_lookup()
    forecast_rows = []
    status_rows = []

    for _, window in windows.iterrows():
        try:
            window_rows = _window_forecasts(run_id, timestamp, window, actual_lookup)
            forecast_rows.extend(window_rows)
            status = "completed"
            message = "Seasonal naive benchmark forecast completed."
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
                "season_length_days": SEASON_LENGTH_DAYS,
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
        "Stage 5.20 seasonal naive generation completed: %s completed, %s failed",
        completed,
        failed,
    )
    return forecasts, statuses, summary


if __name__ == "__main__":
    run_seasonal_naive()
