"""Inspect Stage 5.12A outlier drilldown outputs."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_outlier_drilldown")

DRILLDOWN_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "outlier_drilldown"
TOP_METRIC_OUTLIERS = DRILLDOWN_DIR / "top_metric_outliers.csv"
OUTLIER_BY_MODEL = DRILLDOWN_DIR / "outlier_by_model.csv"
OUTLIER_BY_ENTITY = DRILLDOWN_DIR / "outlier_by_entity.csv"
OUTLIER_WINDOW_DIAGNOSTICS = DRILLDOWN_DIR / "outlier_window_diagnostics.csv"
OUTLIER_ROOT_CAUSES = DRILLDOWN_DIR / "outlier_root_causes.csv"
RANKING_RISK_ASSESSMENT = DRILLDOWN_DIR / "ranking_risk_assessment.csv"
OUTLIER_DRILLDOWN_SUMMARY = DRILLDOWN_DIR / "outlier_drilldown_summary.csv"


def _require_file(path) -> None:
    """Validate that a required outlier drilldown output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required outlier drilldown output missing: {path}")


def inspect_outlier_drilldown() -> dict[str, pd.DataFrame]:
    """Inspect outlier drilldown outputs and validate coverage."""

    for path in (
        TOP_METRIC_OUTLIERS,
        OUTLIER_BY_MODEL,
        OUTLIER_BY_ENTITY,
        OUTLIER_WINDOW_DIAGNOSTICS,
        OUTLIER_ROOT_CAUSES,
        RANKING_RISK_ASSESSMENT,
        OUTLIER_DRILLDOWN_SUMMARY,
    ):
        _require_file(path)

    top_outliers = pd.read_csv(TOP_METRIC_OUTLIERS)
    by_model = pd.read_csv(OUTLIER_BY_MODEL)
    by_entity = pd.read_csv(OUTLIER_BY_ENTITY)
    diagnostics = pd.read_csv(OUTLIER_WINDOW_DIAGNOSTICS)
    root_causes = pd.read_csv(OUTLIER_ROOT_CAUSES)
    ranking_risk = pd.read_csv(RANKING_RISK_ASSESSMENT)
    summary = pd.read_csv(OUTLIER_DRILLDOWN_SUMMARY)
    row = summary.iloc[0]

    if int(row["metric_rows_reviewed"]) != 3178:
        raise ValueError("Outlier drilldown did not review all 3178 metric rows.")
    if len(top_outliers) != 200:
        raise ValueError(f"Expected 200 top outlier rows, found {len(top_outliers)}.")
    if int(row["flagged_metric_rows"]) <= 0:
        raise ValueError("Expected flagged metric rows for drilldown.")
    if diagnostics.empty:
        raise ValueError("Expected diagnosed outlier windows.")
    if root_causes.empty:
        raise ValueError("Expected root-cause classifications.")
    if ranking_risk.empty:
        raise ValueError("Expected ranking risk assessment rows.")

    logger.info("Metric rows reviewed: %s", int(row["metric_rows_reviewed"]))
    logger.info("Sanity flag rows reviewed: %s", int(row["sanity_flag_rows_reviewed"]))
    logger.info("Top outlier rows: %s", len(top_outliers))
    logger.info("Flagged metric rows: %s", int(row["flagged_metric_rows"]))
    logger.info("Models with outliers: %s", int(row["models_with_outliers"]))
    logger.info("Entities with outliers: %s", int(row["entities_with_outliers"]))
    logger.info("Diagnosed windows: %s", len(diagnostics))
    logger.info("Root-cause rows: %s", len(root_causes))
    logger.info("Ranking risk rows: %s", len(ranking_risk))
    logger.info("Recommendation: %s", row["recommendation"])
    logger.info("Stage 5.12A outlier drilldown inspection passed")
    return {
        "top_outliers": top_outliers,
        "by_model": by_model,
        "by_entity": by_entity,
        "diagnostics": diagnostics,
        "root_causes": root_causes,
        "ranking_risk": ranking_risk,
        "summary": summary,
    }


if __name__ == "__main__":
    inspect_outlier_drilldown()
