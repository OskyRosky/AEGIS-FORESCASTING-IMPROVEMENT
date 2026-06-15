"""Inspect Stage 5.20 30-day seasonal naive benchmark outputs.

This inspector validates output contracts and leakage controls. It does not
run models, calculate metrics, create rankings, or write tournament outputs.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_seasonal_naive")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "seasonal_benchmark"
FORECASTS_OUTPUT = OUTPUT_DIR / "seasonal_naive_forecasts.csv"
STATUS_OUTPUT = OUTPUT_DIR / "seasonal_naive_status.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "seasonal_naive_summary.csv"

PROTECTED_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "benchmark_reference",
    PROJECT_ROOT / "shiny_app",
]

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


def _require_file(path: Path) -> None:
    """Validate that a required file exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required seasonal naive output missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _load_valid_windows() -> pd.DataFrame:
    """Load the planned 30-day benchmark windows."""

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
    required = {
        "entity_key",
        "window_id",
        "train_end_date",
        "test_start_date",
        "test_end_date",
        "forecast_horizon_days",
    }
    missing = required.difference(windows.columns)
    if missing:
        raise ValueError(f"backtesting_windows.csv missing columns: {sorted(missing)}")
    return windows[windows["forecast_horizon_days"] == FORECAST_HORIZON_DAYS].copy()


def _load_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load generated seasonal naive outputs."""

    for path in [FORECASTS_OUTPUT, STATUS_OUTPUT, SUMMARY_OUTPUT]:
        _require_file(path)

    forecasts = pd.read_csv(
        FORECASTS_OUTPUT,
        parse_dates=["forecast_date", "reference_actual_date", "created_timestamp"],
    )
    statuses = pd.read_csv(STATUS_OUTPUT, parse_dates=["created_timestamp"])
    summary = pd.read_csv(SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    _assert_columns(forecasts, FORECAST_COLUMNS, "seasonal_naive_forecasts.csv")
    _assert_columns(statuses, STATUS_COLUMNS, "seasonal_naive_status.csv")
    _assert_columns(summary, SUMMARY_COLUMNS, "seasonal_naive_summary.csv")
    return forecasts, statuses, summary


def _validate_window_representation(windows: pd.DataFrame, statuses: pd.DataFrame) -> None:
    """Validate that every valid window was attempted exactly once."""

    planned = set(zip(windows["entity_key"], windows["window_id"].astype(int)))
    attempted = set(zip(statuses["entity_key"], statuses["window_id"].astype(int)))
    if planned != attempted:
        missing = sorted(planned - attempted)[:10]
        unexpected = sorted(attempted - planned)[:10]
        raise ValueError(
            "Status rows do not match valid windows. "
            f"Missing sample: {missing}; unexpected sample: {unexpected}"
        )
    duplicate_attempts = statuses.duplicated(["entity_key", "window_id"]).sum()
    if duplicate_attempts:
        raise ValueError(f"Duplicate status rows found: {duplicate_attempts}")


def _validate_completed_forecasts(
    windows: pd.DataFrame, forecasts: pd.DataFrame, statuses: pd.DataFrame
) -> None:
    """Validate forecast rows for completed windows."""

    completed = statuses[statuses["status"] == "completed"][
        ["entity_key", "window_id"]
    ].copy()
    completed["window_id"] = completed["window_id"].astype(int)

    if completed.empty:
        if not forecasts.empty:
            raise ValueError("Forecast rows exist but no windows are completed.")
        return

    forecast_keys = forecasts[["entity_key", "window_id"]].copy()
    forecast_keys["window_id"] = forecast_keys["window_id"].astype(int)
    row_counts = forecast_keys.value_counts().rename("rows").reset_index()
    counts = completed.merge(row_counts, on=["entity_key", "window_id"], how="left")
    counts["rows"] = counts["rows"].fillna(0).astype(int)
    bad_counts = counts[counts["rows"] != FORECAST_HORIZON_DAYS]
    if not bad_counts.empty:
        raise ValueError(
            "Completed windows without exactly 30 forecast rows: "
            f"{bad_counts.head(10).to_dict(orient='records')}"
        )

    if int(forecasts["horizon_day"].min()) != 1:
        raise ValueError("horizon_day minimum is not 1.")
    if int(forecasts["horizon_day"].max()) != FORECAST_HORIZON_DAYS:
        raise ValueError("horizon_day maximum is not 30.")
    if forecasts["seasonal_naive_forecast_value"].isna().any():
        raise ValueError("Null seasonal naive forecast values found.")
    finite_mask = forecasts["seasonal_naive_forecast_value"].map(math.isfinite)
    if not finite_mask.all():
        raise ValueError("Non-finite seasonal naive forecast values found.")
    if forecasts["reference_actual_date"].isna().any():
        raise ValueError("Null reference_actual_date values found.")

    expected_reference_dates = forecasts["forecast_date"] - pd.Timedelta(
        days=SEASON_LENGTH_DAYS
    )
    bad_references = forecasts["reference_actual_date"] != expected_reference_dates
    if bad_references.any():
        raise ValueError("reference_actual_date is not forecast_date - 30 days.")

    windows_lookup = windows[
        ["entity_key", "window_id", "train_end_date", "test_start_date", "test_end_date"]
    ].copy()
    windows_lookup["window_id"] = windows_lookup["window_id"].astype(int)
    merged = forecasts.merge(windows_lookup, on=["entity_key", "window_id"], how="left")
    if merged[["test_start_date", "test_end_date"]].isna().any().any():
        raise ValueError("Forecast rows include windows not present in valid inputs.")
    outside_test = (
        (merged["forecast_date"] < merged["test_start_date"])
        | (merged["forecast_date"] > merged["test_end_date"])
    )
    if outside_test.any():
        raise ValueError("Forecast dates outside test window found.")
    leakage = merged["reference_actual_date"] > merged["train_end_date"]
    if leakage.any():
        raise ValueError("Future leakage detected in reference_actual_date.")
    if (merged["reference_actual_date"] >= merged["forecast_date"]).any():
        raise ValueError("Reference actual date is not historical.")


def _validate_reference_actual_source(forecasts: pd.DataFrame) -> None:
    """Validate seasonal references exist as actual rows and values match."""

    _require_file(EVALUATION_DATASET)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "value"])
    actuals["date"] = actuals["date"].dt.normalize()
    actuals = actuals.sort_values(["entity_key", "date"])
    if actuals.duplicated(["entity_key", "date"]).any():
        raise ValueError("Duplicate actual rows found for entity/date.")

    actual_lookup = {
        (str(row.entity_key), row.date): float(row.value)
        for row in actuals.itertuples(index=False)
    }
    unique_refs = forecasts[
        [
            "entity_key",
            "window_id",
            "forecast_date",
            "reference_actual_date",
            "seasonal_naive_forecast_value",
        ]
    ].drop_duplicates()
    for _, row in unique_refs.iterrows():
        lookup_key = (str(row["entity_key"]), row["reference_actual_date"])
        if lookup_key not in actual_lookup:
            raise ValueError(
                "reference_actual_date not found as actual row for "
                f"{row['entity_key']}/{row['window_id']}/{row['forecast_date'].date()}"
            )
        if actual_lookup[lookup_key] != float(row["seasonal_naive_forecast_value"]):
            raise ValueError(
                "seasonal_naive_forecast_value does not match reference actual for "
                f"{row['entity_key']}/{row['window_id']}/{row['forecast_date'].date()}"
            )


def _validate_summary(
    windows: pd.DataFrame,
    forecasts: pd.DataFrame,
    statuses: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Validate summary values against detailed outputs."""

    if len(summary) != 1:
        raise ValueError(f"Summary must contain exactly one row; found {len(summary)}.")
    row = summary.iloc[0]
    completed = int((statuses["status"] == "completed").sum())
    failed = int((statuses["status"] == "failed").sum())
    expected = {
        "windows_planned": len(windows),
        "windows_completed": completed,
        "windows_failed": failed,
        "entities": windows["entity_key"].nunique(),
        "forecast_rows": len(forecasts),
        "season_length_days": SEASON_LENGTH_DAYS,
    }
    for column, value in expected.items():
        if int(row[column]) != int(value):
            raise ValueError(
                f"Summary {column} mismatch: expected {value}, found {row[column]}"
            )


def _log_protected_scope() -> None:
    """Report protected directories to make no-touch validation explicit."""

    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not inspected for writes: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_seasonal_naive() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate the Stage 5.20 seasonal naive outputs."""

    logger.info("Stage 5.20 seasonal naive inspection started")
    windows = _load_valid_windows()
    forecasts, statuses, summary = _load_outputs()

    _validate_window_representation(windows, statuses)
    _validate_completed_forecasts(windows, forecasts, statuses)
    if not forecasts.empty:
        _validate_reference_actual_source(forecasts)
    _validate_summary(windows, forecasts, statuses, summary)
    _log_protected_scope()

    logger.info("Output files exist: yes")
    logger.info("Expected columns exist: yes")
    logger.info("Valid windows represented: %s", len(windows))
    logger.info("Completed windows: %s", int((statuses["status"] == "completed").sum()))
    logger.info("Failed windows: %s", int((statuses["status"] == "failed").sum()))
    logger.info("Forecast rows: %s", len(forecasts))
    logger.info("Season length days: %s", SEASON_LENGTH_DAYS)
    logger.info(
        "Forecast date range: %s to %s",
        forecasts["forecast_date"].min().date() if not forecasts.empty else "n/a",
        forecasts["forecast_date"].max().date() if not forecasts.empty else "n/a",
    )
    logger.info("No baseline models executed: yes")
    logger.info("No challenger models executed: yes")
    logger.info("No metrics calculated: yes")
    logger.info("No rankings created: yes")
    logger.info("No tournament outputs created: yes")
    logger.info("Stage 5.20 seasonal naive inspection completed")
    return forecasts, statuses, summary


if __name__ == "__main__":
    inspect_seasonal_naive()
