"""Inspect raw HDD Region CSV extracts from Stage 3 ingestion.

This script prints basic shape and coverage diagnostics for the raw forecast and
actuals extracts. It is console-only and does not modify source files.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import RAW_DIR


logger = get_logger("inspect_raw_csv")

FORECASTS_INPUT_PATH = RAW_DIR / "hdd_region_forecasts.csv"
ACTUALS_INPUT_PATH = RAW_DIR / "hdd_region_actuals.csv"


def _inspect_csv(label: str, path) -> None:
    """Read one raw CSV and log high-level extract diagnostics."""

    if not path.exists():
        logger.error("%s file not found: %s", label, path)
        return

    frame = pd.read_csv(path, parse_dates=["DateTime"])

    logger.info("%s file: %s", label, path)
    logger.info("%s row count: %s", label, len(frame))
    logger.info("%s unique entities: %s", label, frame["Key"].nunique())
    logger.info(
        "%s unique ModelVersions: %s",
        label,
        sorted(frame["ModelVersion"].dropna().unique().tolist()),
    )
    logger.info(
        "%s ForecastVersion values: %s",
        label,
        sorted(frame["ForecastVersion"].dropna().unique().tolist()),
    )
    logger.info("%s min DateTime: %s", label, frame["DateTime"].min())
    logger.info("%s max DateTime: %s", label, frame["DateTime"].max())


def inspect_raw_csv() -> None:
    """Inspect the raw HDD Region forecast and actuals CSV files."""

    _inspect_csv("Forecasts", FORECASTS_INPUT_PATH)
    _inspect_csv("Actuals", ACTUALS_INPUT_PATH)


if __name__ == "__main__":
    inspect_raw_csv()
