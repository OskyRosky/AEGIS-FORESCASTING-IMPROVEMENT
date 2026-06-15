"""Inspect generated Model Lab backtesting windows.

This Stage 5.2 helper reports window coverage and validity diagnostics. It does
not train models, generate forecasts, calculate metrics, or create rankings.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_backtesting_windows")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
SUMMARY_INPUT = MODEL_LAB_DIR / "backtesting_window_summary.csv"


def _require_input_file(path) -> None:
    """Fail fast when an expected window output is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required window output missing: {path}")


def inspect_backtesting_windows() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Inspect generated walk-forward windows and summaries."""

    _require_input_file(WINDOWS_INPUT)
    _require_input_file(SUMMARY_INPUT)

    windows = pd.read_csv(WINDOWS_INPUT, parse_dates=["test_start_date", "test_end_date"])
    summary = pd.read_csv(SUMMARY_INPUT)

    windows_per_entity = windows.groupby("entity_key")["window_id"].count()

    logger.info("Total windows: %s", len(windows))
    logger.info("Unique entities: %s", windows["entity_key"].nunique())
    logger.info("Windows per entity min: %s", int(windows_per_entity.min()))
    logger.info("Windows per entity max: %s", int(windows_per_entity.max()))
    logger.info(
        "Test date range: %s to %s",
        windows["test_start_date"].min(),
        windows["test_end_date"].max(),
    )
    logger.info("Train observation min: %s", int(windows["train_observations"].min()))
    logger.info("Train observation max: %s", int(windows["train_observations"].max()))
    logger.info("Test observation min: %s", int(windows["test_observations"].min()))
    logger.info("Test observation max: %s", int(windows["test_observations"].max()))
    logger.info("Summary rows: %s", len(summary))
    logger.info("Skipped entities: not tracked in output; generator logged any skips")

    return windows, summary


if __name__ == "__main__":
    inspect_backtesting_windows()
