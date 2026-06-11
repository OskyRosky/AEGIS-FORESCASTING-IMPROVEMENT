"""Inspect Stage 5.12 metrics sanity review outputs."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_metrics_sanity")

METRICS_SANITY_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "metrics_sanity"
METRICS_SANITY_SUMMARY = METRICS_SANITY_DIR / "metrics_sanity_summary.csv"
METRICS_SANITY_BY_MODEL = METRICS_SANITY_DIR / "metrics_sanity_by_model.csv"
METRICS_SANITY_BY_ENTITY = METRICS_SANITY_DIR / "metrics_sanity_by_entity.csv"
METRICS_SANITY_FLAGS = METRICS_SANITY_DIR / "metrics_sanity_flags.csv"


def _require_file(path) -> None:
    """Validate that a required metrics sanity output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required metrics sanity output missing: {path}")


def inspect_metrics_sanity() -> dict[str, pd.DataFrame]:
    """Inspect metrics sanity outputs and validate coverage."""

    for path in (
        METRICS_SANITY_SUMMARY,
        METRICS_SANITY_BY_MODEL,
        METRICS_SANITY_BY_ENTITY,
        METRICS_SANITY_FLAGS,
    ):
        _require_file(path)

    summary = pd.read_csv(METRICS_SANITY_SUMMARY)
    by_model = pd.read_csv(METRICS_SANITY_BY_MODEL)
    by_entity = pd.read_csv(METRICS_SANITY_BY_ENTITY)
    flags = pd.read_csv(METRICS_SANITY_FLAGS)

    row = summary.iloc[0]
    if int(row["metric_rows_reviewed"]) != 3178:
        raise ValueError("Metrics sanity review did not cover all 3178 rows.")
    if int(row["models"]) != 7 or len(by_model) != 7:
        raise ValueError("Metrics sanity model coverage mismatch.")
    if int(row["entities"]) != 39 or len(by_entity) != 39:
        raise ValueError("Metrics sanity entity coverage mismatch.")
    if int(row["invalid_metric_flag_count"]) > 0:
        raise ValueError("Invalid metric values were found.")

    logger.info("Metric rows reviewed: %s", int(row["metric_rows_reviewed"]))
    logger.info("Entities reviewed: %s", int(row["entities"]))
    logger.info("Windows reviewed: %s", int(row["windows"]))
    logger.info("Models reviewed: %s", int(row["models"]))
    logger.info("Invalid metric flags: %s", int(row["invalid_metric_flag_count"]))
    logger.info("Total flags: %s", len(flags))
    logger.info("Recommendation: %s", row["recommendation"])
    logger.info("Model sanity rows: %s", len(by_model))
    logger.info("Entity sanity rows: %s", len(by_entity))
    logger.info("Stage 5.12 metrics sanity inspection passed")
    return {
        "summary": summary,
        "by_model": by_model,
        "by_entity": by_entity,
        "flags": flags,
    }


if __name__ == "__main__":
    inspect_metrics_sanity()
