"""Build dashboard-ready evaluation CSV exports.

This Stage 4.5 script reshapes existing baseline metrics and ranking outputs
into lightweight CSVs for future Shiny consumption. It does not modify Shiny,
raw data, processed data, models, forecasts, or metric definitions.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("build_dashboard_exports")

METRICS_DIR = PROJECT_ROOT / "outputs" / "metrics"
DASHBOARD_DIR = PROJECT_ROOT / "outputs" / "dashboard"

BASELINE_METRICS_INPUT = METRICS_DIR / "baseline_metrics.csv"
BASELINE_RANKINGS_INPUT = METRICS_DIR / "baseline_rankings.csv"

METRIC_SUMMARY_OUTPUT = DASHBOARD_DIR / "metric_summary.csv"
HORIZON_SUMMARY_OUTPUT = DASHBOARD_DIR / "horizon_summary.csv"
TOP_ENTITIES_OUTPUT = DASHBOARD_DIR / "top_entities.csv"
EXECUTIVE_SUMMARY_OUTPUT = DASHBOARD_DIR / "executive_summary.csv"
DASHBOARD_METADATA_OUTPUT = DASHBOARD_DIR / "dashboard_metadata.csv"

AGG_COLUMNS = {
    "MAPE": "avg_mape",
    "SMAPE": "avg_smape",
    "RMSE": "avg_rmse",
    "Accuracy": "avg_accuracy",
}


def _require_input_file(path) -> None:
    """Fail fast when an expected baseline output is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required dashboard input missing: {path}")


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load baseline metrics and rankings."""

    _require_input_file(BASELINE_METRICS_INPUT)
    _require_input_file(BASELINE_RANKINGS_INPUT)
    return pd.read_csv(BASELINE_METRICS_INPUT), pd.read_csv(BASELINE_RANKINGS_INPUT)


def _aggregate_summary(frame: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Aggregate official baseline metrics for dashboard summaries."""

    summary = (
        frame.groupby(group_column, as_index=False)
        .agg(
            row_count=("Key", "size"),
            avg_mape=("MAPE", "mean"),
            avg_smape=("SMAPE", "mean"),
            avg_rmse=("RMSE", "mean"),
            avg_accuracy=("Accuracy", "mean"),
        )
        .sort_values(group_column)
    )
    return summary


def _build_top_entities(rankings: pd.DataFrame) -> pd.DataFrame:
    """Select the top 50 existing ranked entities by MAPE rank."""

    columns = [
        "Key",
        "Forecast_Version",
        "avg_mape",
        "avg_smape",
        "avg_rmse",
        "avg_accuracy",
        "model_rank_mape",
        "model_rank_accuracy",
    ]
    return rankings.sort_values("model_rank_mape", ascending=True)[columns].head(50)


def _build_executive_summary(
    baseline_metrics: pd.DataFrame, baseline_rankings: pd.DataFrame
) -> pd.DataFrame:
    """Build a one-row dashboard overview from existing baseline outputs."""

    top_entity = baseline_rankings.sort_values("model_rank_mape").iloc[0]
    return pd.DataFrame(
        [
            {
                "total_metric_rows": len(baseline_metrics),
                "total_rank_rows": len(baseline_rankings),
                "total_entities": baseline_metrics["Key"].nunique(),
                "total_forecast_versions": baseline_metrics[
                    "Forecast_Version"
                ].nunique(),
                "avg_mape": baseline_metrics["MAPE"].mean(),
                "avg_accuracy": baseline_metrics["Accuracy"].mean(),
                "best_entity": top_entity["Key"],
                "best_entity_mape": top_entity["avg_mape"],
            }
        ]
    )


def _build_metadata(
    baseline_metrics: pd.DataFrame, baseline_rankings: pd.DataFrame
) -> pd.DataFrame:
    """Build metadata for dashboard export freshness and coverage."""

    return pd.DataFrame(
        [
            {
                "build_timestamp": datetime.now().isoformat(timespec="seconds"),
                "baseline_metrics_rows": len(baseline_metrics),
                "baseline_rankings_rows": len(baseline_rankings),
                "entity_count": baseline_metrics["Key"].nunique(),
                "forecast_version_count": baseline_metrics[
                    "Forecast_Version"
                ].nunique(),
            }
        ]
    )


def _write_csv(frame: pd.DataFrame, path) -> None:
    """Write a dashboard CSV and log its row count."""

    frame.to_csv(path, index=False)
    logger.info("Created %s with %s rows", path, len(frame))


def build_dashboard_exports() -> None:
    """Create all Stage 4.5 dashboard-ready CSV outputs."""

    logger.info("Stage 4.5 dashboard export build started")
    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)

    baseline_metrics, baseline_rankings = _load_inputs()

    metric_summary = _aggregate_summary(baseline_metrics, "source_file")
    horizon_summary = _aggregate_summary(baseline_metrics, "horizon_bucket")
    top_entities = _build_top_entities(baseline_rankings)
    executive_summary = _build_executive_summary(baseline_metrics, baseline_rankings)
    dashboard_metadata = _build_metadata(baseline_metrics, baseline_rankings)

    _write_csv(metric_summary, METRIC_SUMMARY_OUTPUT)
    _write_csv(horizon_summary, HORIZON_SUMMARY_OUTPUT)
    _write_csv(top_entities, TOP_ENTITIES_OUTPUT)
    _write_csv(executive_summary, EXECUTIVE_SUMMARY_OUTPUT)
    _write_csv(dashboard_metadata, DASHBOARD_METADATA_OUTPUT)

    logger.info("Unique entities: %s", baseline_metrics["Key"].nunique())
    logger.info(
        "Unique forecast versions: %s",
        baseline_metrics["Forecast_Version"].nunique(),
    )
    logger.info("Stage 4.5 dashboard export build completed")


if __name__ == "__main__":
    build_dashboard_exports()
