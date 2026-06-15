"""Export baseline HDD Region production data for Stage 3 ingestion.

The workflow connects to TesseractEarthDW, dynamically resolves the latest valid
Enterprise Forecast-Mean ForecastVersion, and writes raw CSV extracts for
forecasts and actuals. Nothing executes on import.
"""

from __future__ import annotations

import pandas as pd
import pyodbc

from config import build_connection_string
from queries import (
    HDD_REGION_ACTUALS_QUERY,
    HDD_REGION_FORECASTS_QUERY,
    LATEST_ENTERPRISE_FORECAST_VERSION_QUERY,
)
from utils.logger import get_logger
from utils.paths import RAW_DIR


logger = get_logger("export_hdd_region")

FORECASTS_OUTPUT_PATH = RAW_DIR / "hdd_region_forecasts.csv"
ACTUALS_OUTPUT_PATH = RAW_DIR / "hdd_region_actuals.csv"


def _summarize_frame(name: str, frame: pd.DataFrame) -> None:
    """Log basic extract diagnostics without creating metrics or rankings."""

    logger.info("%s row count: %s", name, len(frame))
    logger.info("%s unique entities: %s", name, frame["Key"].nunique())
    logger.info("%s unique models: %s", name, frame["ModelVersion"].nunique())
    logger.info("%s min DateTime: %s", name, frame["DateTime"].min())
    logger.info("%s max DateTime: %s", name, frame["DateTime"].max())


def _resolve_latest_enterprise_forecast_version(connection: pyodbc.Connection):
    """Resolve the latest valid Enterprise Forecast-Mean run dynamically."""

    cursor = connection.cursor()
    cursor.execute(LATEST_ENTERPRISE_FORECAST_VERSION_QUERY)
    row = cursor.fetchone()
    forecast_version = row[0] if row else None

    if forecast_version is None:
        raise RuntimeError("No Enterprise Forecast-Mean ForecastVersion was found.")

    return forecast_version


def export_hdd_region() -> None:
    """Export raw HDD Region forecasts and actuals to data/raw."""

    logger.info("Export started")

    try:
        with pyodbc.connect(build_connection_string()) as connection:
            forecast_version = _resolve_latest_enterprise_forecast_version(connection)
            logger.info("ForecastVersion used: %s", forecast_version)

            # pandas handles typed tabular extraction from the pyodbc connection.
            forecasts = pd.read_sql(HDD_REGION_FORECASTS_QUERY, connection)
            actuals = pd.read_sql(HDD_REGION_ACTUALS_QUERY, connection)

        forecasts.to_csv(FORECASTS_OUTPUT_PATH, index=False)
        actuals.to_csv(ACTUALS_OUTPUT_PATH, index=False)

        logger.info("Forecasts exported to %s", FORECASTS_OUTPUT_PATH)
        _summarize_frame("Forecasts", forecasts)

        logger.info("Actuals exported to %s", ACTUALS_OUTPUT_PATH)
        _summarize_frame("Actuals", actuals)

        logger.info("Export completed")
    except pyodbc.Error as exc:
        logger.error("Export failed with pyodbc error: %s", exc)
        raise
    except Exception as exc:
        logger.error("Export failed with unexpected error: %s", exc)
        raise


if __name__ == "__main__":
    export_hdd_region()
