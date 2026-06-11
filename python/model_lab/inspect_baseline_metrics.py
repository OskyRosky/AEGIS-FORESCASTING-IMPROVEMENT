"""Inspect and validate Stage 5.11 baseline metrics outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_baseline_metrics")

METRICS_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "metrics"
BASELINE_METRICS = METRICS_DIR / "baseline_metrics.csv"
BASELINE_METRICS_SUMMARY = METRICS_DIR / "baseline_metrics_summary.csv"
BASELINE_METRICS_BY_MODEL = METRICS_DIR / "baseline_metrics_by_model.csv"
BASELINE_METRICS_BY_ENTITY = METRICS_DIR / "baseline_metrics_by_entity.csv"

BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}
METRIC_COLUMNS = {
    "run_id",
    "entity_key",
    "window_id",
    "model_name",
    "forecast_rows",
    "wmape",
    "mape",
    "rmse",
    "smape",
    "bias",
    "created_timestamp",
}
METRIC_VALUE_COLUMNS = ["wmape", "mape", "rmse", "smape", "bias"]


def _require_file(path) -> None:
    """Validate that a required metrics output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required baseline metrics output missing: {path}")


def _validate_metric_values(metrics: pd.DataFrame) -> None:
    """Validate metric values are present and finite."""

    for column in METRIC_VALUE_COLUMNS:
        values = pd.to_numeric(metrics[column], errors="coerce")
        if values.isna().any():
            raise ValueError(f"{column} contains NaN values.")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{column} contains non-finite values.")


def inspect_baseline_metrics() -> dict[str, pd.DataFrame]:
    """Inspect baseline metrics and validate dataset coverage."""

    for path in (
        BASELINE_METRICS,
        BASELINE_METRICS_SUMMARY,
        BASELINE_METRICS_BY_MODEL,
        BASELINE_METRICS_BY_ENTITY,
    ):
        _require_file(path)

    metrics = pd.read_csv(BASELINE_METRICS)
    summary = pd.read_csv(BASELINE_METRICS_SUMMARY)
    by_model = pd.read_csv(BASELINE_METRICS_BY_MODEL)
    by_entity = pd.read_csv(BASELINE_METRICS_BY_ENTITY)

    missing_columns = sorted(METRIC_COLUMNS - set(metrics.columns))
    if missing_columns:
        raise ValueError(f"baseline_metrics.csv missing columns: {missing_columns}")
    if metrics.duplicated(["entity_key", "window_id", "model_name"]).any():
        raise ValueError("Duplicate metric rows detected.")
    if not (metrics["forecast_rows"] == 30).all():
        raise ValueError("Every metric row must have forecast_rows = 30.")
    if set(metrics["model_name"]) != BASELINE_MODELS:
        raise ValueError(f"Model coverage mismatch: {sorted(metrics['model_name'].unique())}")
    if len(metrics) != 3178:
        raise ValueError(f"Expected 3178 metric rows, found {len(metrics)}.")

    _validate_metric_values(metrics)

    logger.info("Metric rows: %s", len(metrics))
    logger.info("Entities: %s", metrics["entity_key"].nunique())
    logger.info(
        "Windows: %s",
        metrics[["entity_key", "window_id"]].drop_duplicates().shape[0],
    )
    logger.info("Models: %s", metrics["model_name"].nunique())
    logger.info("Average wMAPE: %.6f", float(metrics["wmape"].mean()))
    logger.info("Average MAPE: %.6f", float(metrics["mape"].mean()))
    logger.info("Average RMSE: %.6f", float(metrics["rmse"].mean()))
    logger.info("Average SMAPE: %.6f", float(metrics["smape"].mean()))
    logger.info("Average Bias: %.6f", float(metrics["bias"].mean()))
    logger.info("Model summary rows: %s", len(by_model))
    logger.info("Entity summary rows: %s", len(by_entity))
    logger.info("Stage 5.11 baseline metrics inspection passed")
    return {
        "metrics": metrics,
        "summary": summary,
        "by_model": by_model,
        "by_entity": by_entity,
    }


if __name__ == "__main__":
    inspect_baseline_metrics()
