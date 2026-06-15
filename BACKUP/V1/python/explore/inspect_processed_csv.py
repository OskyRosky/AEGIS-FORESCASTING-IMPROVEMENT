"""Inspect Stage 4.1 processed data contract CSVs.

This script prints shape and coverage diagnostics for processed outputs only.
It does not calculate forecast metrics, rankings, or processed derivatives.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROCESSED_DIR


logger = get_logger("inspect_processed_csv")

PROCESSED_FILES = {
    "actuals": PROCESSED_DIR / "actuals.csv",
    "forecasts": PROCESSED_DIR / "forecasts.csv",
    "forecast_comparison": PROCESSED_DIR / "forecast_comparison.csv",
    "entities": PROCESSED_DIR / "entities.csv",
    "run_metadata": PROCESSED_DIR / "run_metadata.csv",
}


def _date_range(frame: pd.DataFrame, column: str = "date") -> str:
    """Return a readable min/max date range for a column if present."""

    if column not in frame.columns or frame.empty:
        return "not available"

    dates = pd.to_datetime(frame[column], errors="coerce")
    return f"{dates.min()} to {dates.max()}"


def _inspect_file(label: str, path) -> None:
    """Print basic diagnostics for one processed CSV."""

    if not path.exists():
        logger.error("%s file not found: %s", label, path)
        return

    frame = pd.read_csv(path)
    logger.info("%s file: %s", label, path)
    logger.info("%s rows: %s", label, len(frame))
    logger.info("%s columns: %s", label, list(frame.columns))

    if "entity_key" in frame.columns:
        logger.info("%s unique entities: %s", label, frame["entity_key"].nunique())

    if "model_version" in frame.columns:
        logger.info("%s unique models: %s", label, frame["model_version"].nunique())

    if "date" in frame.columns:
        logger.info("%s date range: %s", label, _date_range(frame))

    if label == "forecast_comparison":
        logger.info("%s is empty: %s", label, frame.empty)


def inspect_processed_csv() -> None:
    """Inspect all Stage 4.1 processed contract files."""

    for label, path in PROCESSED_FILES.items():
        _inspect_file(label, path)


if __name__ == "__main__":
    inspect_processed_csv()
