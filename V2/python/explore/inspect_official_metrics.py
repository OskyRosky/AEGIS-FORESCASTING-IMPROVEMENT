"""Inspect official TESSERACT metrics CSV exports.

This script reads the four raw official metrics exports and prints inventory
details only. It does not calculate metrics, rankings, or model outputs.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import RAW_DIR


logger = get_logger("inspect_official_metrics")

METRICS_FILES = {
    "hdd_region_metrics": RAW_DIR / "hdd_region_metrics.csv",
    "hdd_forest_metrics": RAW_DIR / "hdd_forest_metrics.csv",
    "ssd_phx_lvwe_metrics": RAW_DIR / "ssd_phx_lvwe_metrics.csv",
    "ssd_phx_lvne_metrics": RAW_DIR / "ssd_phx_lvne_metrics.csv",
}

METRIC_COLUMNS = ("MAPE", "SMAPE", "RMSE", "MAE", "Bias", "Bias_Pct", "Accuracy")


def _forecast_version_column(frame: pd.DataFrame) -> str | None:
    """Return the forecast-version column name present in a metrics CSV."""

    for column in ("ForecastVersion", "Forecast_Version"):
        if column in frame.columns:
            return column
    return None


def _date_range(frame: pd.DataFrame, column: str) -> str:
    """Return a readable min/max range for a date-like column."""

    if column not in frame.columns:
        return "column not present"

    values = pd.to_datetime(frame[column], errors="coerce")
    return f"{values.min()} to {values.max()}"


def _inspect_metrics_file(label: str, path) -> None:
    """Log required inventory details for one raw metrics CSV."""

    if not path.exists():
        logger.error("%s file not found: %s", label, path)
        return

    frame = pd.read_csv(path)
    logger.info("%s file: %s", label, path)
    logger.info("%s rows: %s", label, len(frame))
    logger.info("%s columns: %s", label, list(frame.columns))

    version_column = _forecast_version_column(frame)
    if version_column:
        versions = sorted(frame[version_column].dropna().astype(str).unique().tolist())
        logger.info("%s available forecast versions: %s", label, versions)
    else:
        logger.info("%s available forecast versions: no version column found", label)

    if "Key" in frame.columns:
        logger.info("%s unique Keys: %s", label, frame["Key"].nunique())
    else:
        logger.info("%s unique Keys: Key column not present", label)

    logger.info("%s Start_Date range: %s", label, _date_range(frame, "Start_Date"))
    logger.info("%s End_Date range: %s", label, _date_range(frame, "End_Date"))

    present_metric_columns = [column for column in METRIC_COLUMNS if column in frame.columns]
    logger.info("%s metric columns present: %s", label, present_metric_columns)


def inspect_official_metrics() -> None:
    """Inspect all official metrics raw CSV exports."""

    for label, path in METRICS_FILES.items():
        _inspect_metrics_file(label, path)


if __name__ == "__main__":
    inspect_official_metrics()
