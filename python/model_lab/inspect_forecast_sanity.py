"""Inspect Stage 5.9D forecast sanity review outputs."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_forecast_sanity")

SANITY_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "sanity_review"
SANITY_SUMMARY = SANITY_DIR / "forecast_sanity_summary.csv"
SANITY_BY_MODEL = SANITY_DIR / "forecast_sanity_by_model.csv"
SANITY_BY_ENTITY = SANITY_DIR / "forecast_sanity_by_entity.csv"
SANITY_FLAGS = SANITY_DIR / "forecast_sanity_flags.csv"


def _require_file(path) -> None:
    """Validate that a required sanity output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required forecast sanity output missing: {path}")


def inspect_forecast_sanity() -> dict[str, pd.DataFrame]:
    """Inspect sanity outputs and validate expected review coverage."""

    for path in (SANITY_SUMMARY, SANITY_BY_MODEL, SANITY_BY_ENTITY, SANITY_FLAGS):
        _require_file(path)

    summary = pd.read_csv(SANITY_SUMMARY)
    by_model = pd.read_csv(SANITY_BY_MODEL)
    by_entity = pd.read_csv(SANITY_BY_ENTITY)
    flags = pd.read_csv(SANITY_FLAGS)

    row = summary.iloc[0]
    if int(row["forecast_rows_reviewed"]) != 2100:
        raise ValueError("Forecast sanity review did not cover all 2100 rows.")
    if len(by_model) != 7:
        raise ValueError(f"Expected 7 model summary rows, found {len(by_model)}.")
    if len(by_entity) != 10:
        raise ValueError(f"Expected 10 entity summary rows, found {len(by_entity)}.")
    if int(row["null_forecast_count"]) != 0:
        raise ValueError("Forecast sanity review found null forecasts.")
    if int(row["nan_forecast_count"]) != 0:
        raise ValueError("Forecast sanity review found NaN forecasts.")
    if int(row["positive_inf_forecast_count"]) != 0:
        raise ValueError("Forecast sanity review found positive infinity forecasts.")
    if int(row["negative_inf_forecast_count"]) != 0:
        raise ValueError("Forecast sanity review found negative infinity forecasts.")

    logger.info("Forecast rows reviewed: %s", int(row["forecast_rows_reviewed"]))
    logger.info("Models reviewed: %s", int(row["model_count"]))
    logger.info("Entities reviewed: %s", int(row["entity_count"]))
    logger.info("Null forecasts: %s", int(row["null_forecast_count"]))
    logger.info("NaN forecasts: %s", int(row["nan_forecast_count"]))
    logger.info("Inf forecasts: %s", int(row["positive_inf_forecast_count"]))
    logger.info("-Inf forecasts: %s", int(row["negative_inf_forecast_count"]))
    logger.info("Negative forecasts: %s", int(row["negative_forecast_count"]))
    logger.info("Flags: %s", len(flags))
    logger.info("Recommendation: %s", row["recommendation"])
    logger.info("Model summary rows: %s", len(by_model))
    logger.info("Entity summary rows: %s", len(by_entity))
    logger.info("Stage 5.9D forecast sanity inspection passed")
    return {
        "summary": summary,
        "by_model": by_model,
        "by_entity": by_entity,
        "flags": flags,
    }


if __name__ == "__main__":
    inspect_forecast_sanity()
