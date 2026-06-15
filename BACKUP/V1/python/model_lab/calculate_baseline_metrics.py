"""Calculate baseline model forecast metrics.

This Stage 5.11 script evaluates completed baseline forecasts against actuals.
It calculates metric rows and summaries only. It does not calculate composite
scores, rank models, build tournament outputs, rerun models, or modify
execution controls.
"""

from __future__ import annotations

from datetime import datetime

import numpy as np
import pandas as pd

from model_lab.load_configs import load_yaml_config
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("calculate_baseline_metrics")

SCORING_DEFINITIONS = PROJECT_ROOT / "config" / "scoring_definitions.yaml"
FULL_BASELINE_FORECASTS = (
    PROJECT_ROOT / "outputs" / "model_lab" / "full_baseline" / "full_baseline_forecasts.csv"
)
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
METRICS_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "metrics"
BASELINE_METRICS_OUTPUT = METRICS_DIR / "baseline_metrics.csv"
BASELINE_METRICS_SUMMARY_OUTPUT = METRICS_DIR / "baseline_metrics_summary.csv"
BASELINE_METRICS_BY_MODEL_OUTPUT = METRICS_DIR / "baseline_metrics_by_model.csv"
BASELINE_METRICS_BY_ENTITY_OUTPUT = METRICS_DIR / "baseline_metrics_by_entity.csv"

BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}
METRIC_COLUMNS = [
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
]


def _require_file(path) -> None:
    """Validate that a required metrics input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required baseline metrics input missing: {path}")


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load forecasts, actuals, and scoring definitions."""

    for path in (FULL_BASELINE_FORECASTS, EVALUATION_DATASET, SCORING_DEFINITIONS):
        _require_file(path)

    forecasts = pd.read_csv(FULL_BASELINE_FORECASTS, parse_dates=["forecast_date"])
    forecasts["forecast_value"] = pd.to_numeric(
        forecasts["forecast_value"], errors="coerce"
    )
    forecasts = forecasts[forecasts["model_name"].isin(BASELINE_MODELS)].copy()
    if forecasts.empty:
        raise ValueError("No baseline forecast rows found.")

    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["actual_value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals[["entity_key", "date", "actual_value"]]
    if actuals.empty:
        raise ValueError("No actual rows found.")

    scoring_config = load_yaml_config(SCORING_DEFINITIONS)
    return forecasts, actuals, scoring_config


def _merge_forecasts_actuals(
    forecasts: pd.DataFrame, actuals: pd.DataFrame
) -> pd.DataFrame:
    """Join forecasts to actuals by entity and forecast date."""

    merged = forecasts.merge(
        actuals,
        how="left",
        left_on=["entity_key", "forecast_date"],
        right_on=["entity_key", "date"],
    )
    if merged["actual_value"].isna().any():
        missing = merged[merged["actual_value"].isna()][
            ["entity_key", "forecast_date", "job_id"]
        ].head(10)
        raise ValueError(
            "Forecast rows without actuals detected: "
            f"{missing.to_dict('records')}"
        )
    return merged


def _percentage_mask(actual: pd.Series, scoring_config: dict) -> pd.Series:
    """Return rows allowed for percentage metrics under zero-actual policy."""

    zero_policy = scoring_config["zero_actual_handling"]
    threshold = float(zero_policy["minimum_actual_threshold"])
    if zero_policy.get("exclude_zero_actuals_from_percentage_metrics") is True:
        return actual.abs() > threshold
    return pd.Series(True, index=actual.index)


def _calculate_group_metrics(group: pd.DataFrame, scoring_config: dict) -> dict:
    """Calculate metrics for one entity/window/model group."""

    actual = group["actual_value"].astype(float)
    forecast = group["forecast_value"].astype(float)
    error = forecast - actual
    abs_error = error.abs()

    percentage_rows = _percentage_mask(actual, scoring_config)
    percentage_actual = actual[percentage_rows]
    percentage_abs_error = abs_error[percentage_rows]
    percentage_forecast = forecast[percentage_rows]

    denominator = percentage_actual.abs().sum()
    if denominator == 0:
        wmape = 0.0
    else:
        wmape = float(percentage_abs_error.sum() / denominator)

    if len(percentage_actual) == 0:
        mape = 0.0
        smape = 0.0
    else:
        mape = float((percentage_abs_error / percentage_actual.abs()).mean())
        smape_denominator = percentage_actual.abs() + percentage_forecast.abs()
        smape_terms = np.where(
            smape_denominator.to_numpy(dtype=float) == 0,
            0.0,
            2.0
            * percentage_abs_error.to_numpy(dtype=float)
            / smape_denominator.to_numpy(dtype=float),
        )
        smape = float(np.mean(smape_terms))

    rmse = float(np.sqrt(np.mean(np.square(error.to_numpy(dtype=float)))))
    bias = float(error.mean())

    return {
        "run_id": group["run_id"].iloc[0],
        "entity_key": group["entity_key"].iloc[0],
        "window_id": int(group["window_id"].iloc[0]),
        "model_name": group["model_name"].iloc[0],
        "forecast_rows": len(group),
        "wmape": wmape,
        "mape": mape,
        "rmse": rmse,
        "smape": smape,
        "bias": bias,
    }


def _build_summary(metrics: pd.DataFrame, created_timestamp: str) -> pd.DataFrame:
    """Build one-row metrics summary."""

    return pd.DataFrame(
        [
            {
                "run_id": metrics["run_id"].iloc[0],
                "metric_rows": len(metrics),
                "entities": metrics["entity_key"].nunique(),
                "windows": metrics[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "models": metrics["model_name"].nunique(),
                "avg_wmape": float(metrics["wmape"].mean()),
                "avg_mape": float(metrics["mape"].mean()),
                "avg_rmse": float(metrics["rmse"].mean()),
                "avg_smape": float(metrics["smape"].mean()),
                "avg_bias": float(metrics["bias"].mean()),
                "created_timestamp": created_timestamp,
            }
        ]
    )


def _build_group_summary(metrics: pd.DataFrame, group_column: str) -> pd.DataFrame:
    """Build model/entity average metric summaries."""

    return (
        metrics.groupby(group_column, as_index=False)
        .agg(
            metric_rows=("model_name", "size"),
            avg_wmape=("wmape", "mean"),
            avg_mape=("mape", "mean"),
            avg_rmse=("rmse", "mean"),
            avg_smape=("smape", "mean"),
            avg_bias=("bias", "mean"),
        )
        .sort_values(group_column)
    )


def calculate_baseline_metrics() -> dict[str, pd.DataFrame]:
    """Calculate and write baseline metrics outputs."""

    logger.info("Stage 5.11 baseline metrics calculation started")
    METRICS_DIR.mkdir(parents=True, exist_ok=True)

    forecasts, actuals, scoring_config = _load_inputs()
    merged = _merge_forecasts_actuals(forecasts, actuals)
    created_timestamp = datetime.now().isoformat(timespec="seconds")

    rows = [
        _calculate_group_metrics(group, scoring_config)
        for _, group in merged.groupby(["entity_key", "window_id", "model_name"])
    ]
    metrics = pd.DataFrame(rows, columns=METRIC_COLUMNS[:-1])
    metrics["created_timestamp"] = created_timestamp
    metrics = metrics[METRIC_COLUMNS]

    summary = _build_summary(metrics, created_timestamp)
    by_model = _build_group_summary(metrics, "model_name")
    by_entity = _build_group_summary(metrics, "entity_key")

    metrics.to_csv(BASELINE_METRICS_OUTPUT, index=False)
    summary.to_csv(BASELINE_METRICS_SUMMARY_OUTPUT, index=False)
    by_model.to_csv(BASELINE_METRICS_BY_MODEL_OUTPUT, index=False)
    by_entity.to_csv(BASELINE_METRICS_BY_ENTITY_OUTPUT, index=False)

    logger.info("Created %s with %s rows", BASELINE_METRICS_OUTPUT, len(metrics))
    logger.info(
        "Created %s with %s rows", BASELINE_METRICS_SUMMARY_OUTPUT, len(summary)
    )
    logger.info(
        "Created %s with %s rows", BASELINE_METRICS_BY_MODEL_OUTPUT, len(by_model)
    )
    logger.info(
        "Created %s with %s rows", BASELINE_METRICS_BY_ENTITY_OUTPUT, len(by_entity)
    )
    logger.info("Stage 5.11 baseline metrics calculation completed")
    return {
        "metrics": metrics,
        "summary": summary,
        "by_model": by_model,
        "by_entity": by_entity,
    }


if __name__ == "__main__":
    calculate_baseline_metrics()
