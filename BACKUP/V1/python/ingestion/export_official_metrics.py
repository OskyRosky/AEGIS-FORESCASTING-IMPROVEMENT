"""Export official TESSERACT accuracy metrics tables to raw CSV files.

These exports capture the baseline metrics currently used by the dashboard.
The script does not calculate new metrics, create rankings, or modify processed
datasets.
"""

from __future__ import annotations

import pandas as pd
import pyodbc

from ingestion.config import build_connection_string
from utils.logger import get_logger
from utils.paths import RAW_DIR


logger = get_logger("export_official_metrics")

TABLE_EXPORTS = [
    {
        "table": "[TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region_metrics]",
        "output": RAW_DIR / "hdd_region_metrics.csv",
    },
    {
        "table": "[TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_forest_metrics]",
        "output": RAW_DIR / "hdd_forest_metrics.csv",
    },
    {
        "table": "[TesseractEarthDW].[dbo].[forecast_substrateBE_ssd_phx_lvwe_metrics]",
        "output": RAW_DIR / "ssd_phx_lvwe_metrics.csv",
    },
    {
        "table": "[TesseractEarthDW].[dbo].[forecast_substrateBE_ssd_phx_lvne_metrics]",
        "output": RAW_DIR / "ssd_phx_lvne_metrics.csv",
    },
]


def _forecast_version_column(frame: pd.DataFrame) -> str | None:
    """Return the forecast-version column name used by a metrics table."""

    for column in ("ForecastVersion", "Forecast_Version"):
        if column in frame.columns:
            return column
    return None


def _metric_date_summary(frame: pd.DataFrame, column: str) -> tuple[object, object]:
    """Return min/max date-like values without changing source data."""

    values = pd.to_datetime(frame[column], errors="coerce")
    return values.min(), values.max()


def _log_export_summary(table: str, output_path, frame: pd.DataFrame) -> None:
    """Log required discovery details for one exported metrics table."""

    logger.info("Table: %s", table)
    logger.info("Output CSV: %s", output_path)
    logger.info("Row count: %s", len(frame))
    logger.info("Column count: %s", len(frame.columns))

    version_column = _forecast_version_column(frame)
    if version_column:
        versions = sorted(frame[version_column].dropna().astype(str).unique().tolist())
        logger.info("%s values: %s", version_column, versions)
    else:
        logger.info("ForecastVersion/Forecast_Version values: column not present")

    for date_column in ("Start_Date", "End_Date"):
        if date_column in frame.columns:
            minimum, maximum = _metric_date_summary(frame, date_column)
            logger.info("%s min: %s", date_column, minimum)
            logger.info("%s max: %s", date_column, maximum)
        else:
            logger.info("%s min/max: column not present", date_column)


def export_official_metrics() -> None:
    """Export the official metrics tables to data/raw."""

    logger.info("Official metrics export started")
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    try:
        with pyodbc.connect(build_connection_string()) as connection:
            for export in TABLE_EXPORTS:
                table = export["table"]
                output_path = export["output"]
                logger.info("Exporting %s", table)

                frame = pd.read_sql(f"SELECT * FROM {table};", connection)
                frame.to_csv(output_path, index=False)
                _log_export_summary(table, output_path, frame)

        logger.info("Official metrics export completed")
    except pyodbc.Error as exc:
        logger.error("Official metrics export failed with pyodbc error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Official metrics export failed with unexpected error: %s", exc)
        raise


if __name__ == "__main__":
    export_official_metrics()
