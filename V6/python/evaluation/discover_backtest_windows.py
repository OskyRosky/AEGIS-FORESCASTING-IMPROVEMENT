"""Discover historical ForecastVersions that can be evaluated against actuals.

This Stage 4.2 script profiles Enterprise Forecast-Mean runs in the source HDD
Region table. It creates an inventory only; it does not calculate forecast
errors, metrics, rankings, processed datasets, or model outputs.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyodbc

from ingestion.config import build_connection_string
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("discover_backtest_windows")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "evaluation"
OUTPUT_PATH = OUTPUT_DIR / "backtest_window_inventory.csv"

SOURCE_TABLE = "[TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]"

WINDOW_INVENTORY_QUERY = f"""
WITH enterprise_rows AS (
    SELECT
        CAST([ForecastVersion] AS varchar(64)) AS forecast_version,
        [DateTime],
        [Key],
        [ModelVersion]
    FROM {SOURCE_TABLE}
    WHERE [Scenario] = 'Enterprise'
      AND [ValueType] = 'Forecast-Mean'
),
forecast_summary AS (
    SELECT
        forecast_version,
        COUNT(*) AS row_count,
        COUNT(DISTINCT [Key]) AS unique_keys,
        COUNT(DISTINCT CASE WHEN [ModelVersion] <> 'actual' THEN [ModelVersion] END)
            AS unique_model_versions,
        MIN(CASE WHEN [ModelVersion] <> 'actual' THEN [DateTime] END)
            AS forecast_min_datetime,
        MAX(CASE WHEN [ModelVersion] <> 'actual' THEN [DateTime] END)
            AS forecast_max_datetime
    FROM enterprise_rows
    GROUP BY forecast_version
),
actual_summary AS (
    SELECT
        forecast_version,
        MIN(CASE WHEN [ModelVersion] = 'actual' THEN [DateTime] END)
            AS actual_min_datetime,
        MAX(CASE WHEN [ModelVersion] = 'actual' THEN [DateTime] END)
            AS actual_max_datetime
    FROM enterprise_rows
    GROUP BY forecast_version
),
overlap_dates AS (
    SELECT
        forecasts.forecast_version,
        COUNT(DISTINCT forecasts.[DateTime]) AS overlapping_forecast_dates
    FROM enterprise_rows AS forecasts
    INNER JOIN enterprise_rows AS actuals
        ON forecasts.forecast_version = actuals.forecast_version
       AND forecasts.[DateTime] = actuals.[DateTime]
    WHERE forecasts.[ModelVersion] <> 'actual'
      AND actuals.[ModelVersion] = 'actual'
    GROUP BY forecasts.forecast_version
),
overlap_keys AS (
    SELECT
        forecasts.forecast_version,
        COUNT(DISTINCT forecasts.[Key]) AS overlapping_keys
    FROM enterprise_rows AS forecasts
    INNER JOIN enterprise_rows AS actuals
        ON forecasts.forecast_version = actuals.forecast_version
       AND forecasts.[DateTime] = actuals.[DateTime]
       AND forecasts.[Key] = actuals.[Key]
    WHERE forecasts.[ModelVersion] <> 'actual'
      AND actuals.[ModelVersion] = 'actual'
    GROUP BY forecasts.forecast_version
)
SELECT
    forecast_summary.forecast_version,
    forecast_summary.row_count,
    forecast_summary.unique_keys,
    forecast_summary.unique_model_versions,
    forecast_summary.forecast_min_datetime,
    forecast_summary.forecast_max_datetime,
    actual_summary.actual_min_datetime,
    actual_summary.actual_max_datetime,
    CASE
        WHEN COALESCE(overlap_dates.overlapping_forecast_dates, 0) > 0
        THEN CAST(1 AS bit)
        ELSE CAST(0 AS bit)
    END AS dates_overlap_actuals,
    COALESCE(overlap_dates.overlapping_forecast_dates, 0)
        AS overlapping_forecast_dates,
    COALESCE(overlap_keys.overlapping_keys, 0) AS overlapping_keys
FROM forecast_summary
LEFT JOIN actual_summary
    ON forecast_summary.forecast_version = actual_summary.forecast_version
LEFT JOIN overlap_dates
    ON forecast_summary.forecast_version = overlap_dates.forecast_version
LEFT JOIN overlap_keys
    ON forecast_summary.forecast_version = overlap_keys.forecast_version
ORDER BY forecast_summary.forecast_version;
"""


def _normalize_inventory(inventory: pd.DataFrame) -> pd.DataFrame:
    """Normalize dates and boolean fields for a stable CSV inventory."""

    datetime_columns = [
        "forecast_min_datetime",
        "forecast_max_datetime",
        "actual_min_datetime",
        "actual_max_datetime",
    ]
    for column in datetime_columns:
        inventory[column] = pd.to_datetime(inventory[column], errors="coerce").dt.date

    inventory["dates_overlap_actuals"] = inventory["dates_overlap_actuals"].astype(bool)
    return inventory


def _best_candidates(inventory: pd.DataFrame, limit: int = 5) -> pd.DataFrame:
    """Select candidate runs with overlap, ordered by newest version and coverage."""

    evaluable = inventory[inventory["dates_overlap_actuals"]].copy()
    if evaluable.empty:
        return evaluable

    evaluable["_forecast_version_sort"] = pd.to_datetime(
        evaluable["forecast_version"], errors="coerce"
    )
    candidates = evaluable.sort_values(
        [
            "_forecast_version_sort",
            "overlapping_forecast_dates",
            "overlapping_keys",
            "unique_model_versions",
        ],
        ascending=[False, False, False, False],
    ).head(limit)

    return candidates.drop(columns=["_forecast_version_sort"])


def _log_summary(inventory: pd.DataFrame) -> None:
    """Print a concise discovery summary for backtest planning."""

    total_versions = len(inventory)
    evaluable = inventory[inventory["dates_overlap_actuals"]].copy()
    evaluable_count = len(evaluable)

    logger.info("Total ForecastVersions found: %s", total_versions)
    logger.info("Evaluable ForecastVersions: %s", evaluable_count)

    if evaluable.empty:
        logger.warning("No evaluable ForecastVersions found with same-date actual overlap.")
        return

    evaluable["_forecast_version_sort"] = pd.to_datetime(
        evaluable["forecast_version"], errors="coerce"
    )
    newest = evaluable.sort_values("_forecast_version_sort").iloc[-1]
    oldest = evaluable.sort_values("_forecast_version_sort").iloc[0]

    logger.info("Newest evaluable ForecastVersion: %s", newest["forecast_version"])
    logger.info("Oldest evaluable ForecastVersion: %s", oldest["forecast_version"])

    candidates = _best_candidates(inventory)
    logger.info("Best candidate ForecastVersions for backtesting:")
    for _, row in candidates.iterrows():
        logger.info(
            "ForecastVersion=%s, overlap_dates=%s, overlap_keys=%s, models=%s",
            row["forecast_version"],
            row["overlapping_forecast_dates"],
            row["overlapping_keys"],
            row["unique_model_versions"],
        )


def discover_backtest_windows() -> pd.DataFrame:
    """Query TesseractEarthDW and save historical backtest window inventory."""

    logger.info("Stage 4.2 historical evaluation discovery started")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with pyodbc.connect(build_connection_string()) as connection:
            inventory = pd.read_sql(WINDOW_INVENTORY_QUERY, connection)
    except pyodbc.Error as exc:
        logger.error("Discovery failed with pyodbc error: %s", exc)
        raise

    inventory = _normalize_inventory(inventory)
    inventory.to_csv(OUTPUT_PATH, index=False)

    logger.info("Created %s with %s rows", OUTPUT_PATH, len(inventory))
    _log_summary(inventory)
    logger.info("Stage 4.2 historical evaluation discovery completed")

    return inventory


if __name__ == "__main__":
    discover_backtest_windows()
