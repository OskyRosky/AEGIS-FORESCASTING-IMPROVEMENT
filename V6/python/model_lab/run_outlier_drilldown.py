"""Run metrics outlier drilldown diagnostics.

This Stage 5.12A script investigates baseline metric outliers. It does not
create rankings, composite scores, tournament outputs, winners, rerun models,
modify forecasts, modify metrics, or run challengers.
"""

from __future__ import annotations

from collections import Counter

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_outlier_drilldown")

METRICS_INPUT = PROJECT_ROOT / "outputs" / "model_lab" / "metrics" / "baseline_metrics.csv"
FLAGS_INPUT = (
    PROJECT_ROOT / "outputs" / "model_lab" / "metrics_sanity" / "metrics_sanity_flags.csv"
)
FORECASTS_INPUT = (
    PROJECT_ROOT / "outputs" / "model_lab" / "full_baseline" / "full_baseline_forecasts.csv"
)
ACTUALS_INPUT = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
DRILLDOWN_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "outlier_drilldown"

TOP_METRIC_OUTLIERS_OUTPUT = DRILLDOWN_DIR / "top_metric_outliers.csv"
OUTLIER_BY_MODEL_OUTPUT = DRILLDOWN_DIR / "outlier_by_model.csv"
OUTLIER_BY_ENTITY_OUTPUT = DRILLDOWN_DIR / "outlier_by_entity.csv"
OUTLIER_WINDOW_DIAGNOSTICS_OUTPUT = DRILLDOWN_DIR / "outlier_window_diagnostics.csv"
OUTLIER_ROOT_CAUSES_OUTPUT = DRILLDOWN_DIR / "outlier_root_causes.csv"
RANKING_RISK_ASSESSMENT_OUTPUT = DRILLDOWN_DIR / "ranking_risk_assessment.csv"
OUTLIER_DRILLDOWN_SUMMARY_OUTPUT = DRILLDOWN_DIR / "outlier_drilldown_summary.csv"

METRICS_TO_DRILL = ["wmape", "mape", "rmse", "abs_bias"]
PERCENTAGE_METRICS = {"wmape", "mape"}


def _require_file(path) -> None:
    """Validate that a required drilldown input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required outlier drilldown input missing: {path}")


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load metrics, flags, forecasts, and actuals."""

    for path in (METRICS_INPUT, FLAGS_INPUT, FORECASTS_INPUT, ACTUALS_INPUT):
        _require_file(path)

    metrics = pd.read_csv(METRICS_INPUT)
    for column in ["wmape", "mape", "rmse", "smape", "bias"]:
        metrics[column] = pd.to_numeric(metrics[column], errors="coerce")
    metrics["abs_bias"] = metrics["bias"].abs()

    flags = pd.read_csv(FLAGS_INPUT)
    forecasts = pd.read_csv(FORECASTS_INPUT, parse_dates=["forecast_date"])
    forecasts["forecast_value"] = pd.to_numeric(
        forecasts["forecast_value"], errors="coerce"
    )
    actuals = pd.read_csv(ACTUALS_INPUT, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["actual_value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals[["entity_key", "date", "actual_value"]]
    return metrics, flags, forecasts, actuals


def _outlier_thresholds(metrics: pd.DataFrame) -> dict[str, float]:
    """Build 10x-median thresholds for drilldown metrics."""

    thresholds = {}
    for metric in METRICS_TO_DRILL:
        median = float(metrics[metric].median())
        thresholds[metric] = 10 * median if median > 0 else np.inf
    return thresholds


def _is_outlier(row: pd.Series, thresholds: dict[str, float]) -> bool:
    """Return whether a metric row is flagged by any drilldown rule."""

    for metric in METRICS_TO_DRILL:
        if row[metric] > thresholds[metric]:
            return True
    return any(row[metric] > 1.0 for metric in PERCENTAGE_METRICS)


def _top_metric_outliers(metrics: pd.DataFrame) -> pd.DataFrame:
    """Extract top 50 rows for each required metric."""

    rows = []
    for metric in METRICS_TO_DRILL:
        top = metrics.sort_values(metric, ascending=False).head(50)
        for _, row in top.iterrows():
            rows.append(
                {
                    "metric_name": metric,
                    "entity_key": row["entity_key"],
                    "window_id": int(row["window_id"]),
                    "model_name": row["model_name"],
                    "metric_value": float(row[metric]),
                    "wmape": float(row["wmape"]),
                    "mape": float(row["mape"]),
                    "rmse": float(row["rmse"]),
                    "bias": float(row["bias"]),
                    "abs_bias": float(row["abs_bias"]),
                }
            )
    return pd.DataFrame(rows)


def _flagged_rows(metrics: pd.DataFrame, thresholds: dict[str, float]) -> pd.DataFrame:
    """Return metric rows hit by any outlier rule."""

    mask = metrics.apply(lambda row: _is_outlier(row, thresholds), axis=1)
    flagged = metrics.loc[mask].copy()
    flagged["outlier_severity"] = flagged.apply(
        lambda row: max(
            [
                row[metric] / thresholds[metric]
                for metric in METRICS_TO_DRILL
                if np.isfinite(thresholds[metric]) and thresholds[metric] > 0
            ]
            + [row[metric] for metric in PERCENTAGE_METRICS]
        ),
        axis=1,
    )
    return flagged


def _outlier_by_model(flagged: pd.DataFrame, total_rows: int) -> pd.DataFrame:
    """Build model-level outlier contribution diagnostics."""

    if flagged.empty:
        return pd.DataFrame(
            columns=[
                "model_name",
                "outlier_count",
                "outlier_percentage",
                "average_severity",
            ]
        )
    rows = (
        flagged.groupby("model_name", as_index=False)
        .agg(
            outlier_count=("model_name", "size"),
            average_severity=("outlier_severity", "mean"),
        )
        .sort_values("model_name")
    )
    rows["outlier_percentage"] = rows["outlier_count"] / total_rows
    return rows[["model_name", "outlier_count", "outlier_percentage", "average_severity"]]


def _outlier_by_entity(flagged: pd.DataFrame, total_rows: int) -> pd.DataFrame:
    """Build entity-level outlier contribution diagnostics."""

    if flagged.empty:
        return pd.DataFrame(
            columns=["entity_key", "outlier_count", "outlier_percentage"]
        )
    rows = (
        flagged.groupby("entity_key", as_index=False)
        .agg(outlier_count=("entity_key", "size"))
        .sort_values("entity_key")
    )
    rows["outlier_percentage"] = rows["outlier_count"] / total_rows
    return rows[["entity_key", "outlier_count", "outlier_percentage"]]


def _window_diagnostics(
    flagged: pd.DataFrame, forecasts: pd.DataFrame, actuals: pd.DataFrame
) -> pd.DataFrame:
    """Inspect forecast/actual paths for top outlier windows."""

    top_windows = (
        flagged.sort_values("outlier_severity", ascending=False)
        .drop_duplicates(["entity_key", "window_id", "model_name"])
        .head(100)
    )
    rows = []
    for _, outlier in top_windows.iterrows():
        forecast_path = forecasts[
            (forecasts["entity_key"] == outlier["entity_key"])
            & (forecasts["window_id"] == outlier["window_id"])
            & (forecasts["model_name"] == outlier["model_name"])
        ].copy()
        merged = forecast_path.merge(
            actuals,
            how="left",
            left_on=["entity_key", "forecast_date"],
            right_on=["entity_key", "date"],
        )
        if merged.empty:
            continue
        error = merged["forecast_value"] - merged["actual_value"]
        start_error = float(error.iloc[0])
        end_error = float(error.iloc[-1])
        wrong_direction = bool(np.sign(start_error) != np.sign(end_error))
        forecast_range = float(
            merged["forecast_value"].max() - merged["forecast_value"].min()
        )
        actual_range = float(merged["actual_value"].max() - merged["actual_value"].min())
        collapsed = bool(forecast_range <= 1e-9 and actual_range > 0)
        overshoot = bool(
            merged["forecast_value"].max() > 2 * max(merged["actual_value"].max(), 1e-9)
        )
        lagged_trend = bool(abs(end_error) > abs(start_error) and actual_range > 0)
        rows.append(
            {
                "entity_key": outlier["entity_key"],
                "window_id": int(outlier["window_id"]),
                "model_name": outlier["model_name"],
                "wmape": float(outlier["wmape"]),
                "mape": float(outlier["mape"]),
                "rmse": float(outlier["rmse"]),
                "bias": float(outlier["bias"]),
                "max_forecast_deviation": float(error.abs().max()),
                "avg_forecast_deviation": float(error.abs().mean()),
                "forecast_min": float(merged["forecast_value"].min()),
                "forecast_max": float(merged["forecast_value"].max()),
                "actual_min": float(merged["actual_value"].min()),
                "actual_max": float(merged["actual_value"].max()),
                "wrong_direction": wrong_direction,
                "forecast_collapse": collapsed,
                "forecast_overshoot": overshoot,
                "lagged_trend_change": lagged_trend,
            }
        )
    return pd.DataFrame(rows)


def _classify_root_cause(row: pd.Series) -> str:
    """Assign a heuristic root-cause class to one outlier diagnostic row."""

    actual_min = float(row["actual_min"])
    actual_max = float(row["actual_max"])
    actual_range = actual_max - actual_min
    actual_scale = max(abs(actual_max), abs(actual_min), 1e-9)
    volatility_ratio = actual_range / actual_scale

    if row["forecast_collapse"]:
        return "POSSIBLE_IMPLEMENTATION_ISSUE"
    if row["forecast_overshoot"]:
        return "BASELINE_MODEL_LIMITATION"
    if volatility_ratio > 0.5:
        return "EXPECTED_VOLATILITY"
    if row["lagged_trend_change"]:
        return "STRUCTURAL_BREAK"
    if actual_scale < 1.0:
        return "ENTITY_DATA_ANOMALY"
    return "BASELINE_MODEL_LIMITATION"


def _root_causes(diagnostics: pd.DataFrame) -> pd.DataFrame:
    """Classify root causes for diagnosed outlier windows."""

    if diagnostics.empty:
        return pd.DataFrame(
            columns=[
                "entity_key",
                "window_id",
                "model_name",
                "root_cause",
                "evidence",
            ]
        )
    rows = []
    for _, row in diagnostics.iterrows():
        root_cause = _classify_root_cause(row)
        evidence = (
            f"wmape={row['wmape']:.4f}; rmse={row['rmse']:.4f}; "
            f"actual_range={row['actual_min']:.4f}-{row['actual_max']:.4f}; "
            f"forecast_range={row['forecast_min']:.4f}-{row['forecast_max']:.4f}"
        )
        rows.append(
            {
                "entity_key": row["entity_key"],
                "window_id": int(row["window_id"]),
                "model_name": row["model_name"],
                "root_cause": root_cause,
                "evidence": evidence,
            }
        )
    return pd.DataFrame(rows)


def _ranking_risk(flagged: pd.DataFrame, root_causes: pd.DataFrame) -> pd.DataFrame:
    """Assess which models/entities could distort future rankings."""

    rows = []
    model_counts = Counter(flagged["model_name"]) if not flagged.empty else Counter()
    entity_counts = Counter(flagged["entity_key"]) if not flagged.empty else Counter()
    root_counts = Counter(root_causes["root_cause"]) if not root_causes.empty else Counter()
    for model_name, count in sorted(model_counts.items()):
        rows.append(
            {
                "risk_type": "model_penalty_risk",
                "subject": model_name,
                "risk_count": count,
                "risk_message": "Model has metric outliers that could dominate ranking penalties.",
            }
        )
    for entity_key, count in sorted(entity_counts.items()):
        rows.append(
            {
                "risk_type": "entity_distortion_risk",
                "subject": entity_key,
                "risk_count": count,
                "risk_message": "Entity has metric outliers that could distort aggregate rankings.",
            }
        )
    for root_cause, count in sorted(root_counts.items()):
        rows.append(
            {
                "risk_type": "root_cause_mix",
                "subject": root_cause,
                "risk_count": count,
                "risk_message": "Root-cause category observed in diagnosed outlier windows.",
            }
        )
    return pd.DataFrame(rows)


def run_outlier_drilldown() -> dict[str, pd.DataFrame]:
    """Run full outlier drilldown and write diagnostic outputs."""

    logger.info("Stage 5.12A outlier drilldown started")
    DRILLDOWN_DIR.mkdir(parents=True, exist_ok=True)
    metrics, flags, forecasts, actuals = _load_inputs()
    thresholds = _outlier_thresholds(metrics)
    top_outliers = _top_metric_outliers(metrics)
    flagged = _flagged_rows(metrics, thresholds)
    by_model = _outlier_by_model(flagged, len(metrics))
    by_entity = _outlier_by_entity(flagged, len(metrics))
    diagnostics = _window_diagnostics(flagged, forecasts, actuals)
    root_causes = _root_causes(diagnostics)
    ranking_risk = _ranking_risk(flagged, root_causes)
    recommendation = (
        "KEEP_RANKING_BLOCKED" if not flagged.empty else "APPROVE_BASELINE_RANKING_STAGE"
    )
    summary = pd.DataFrame(
        [
            {
                "metric_rows_reviewed": len(metrics),
                "sanity_flag_rows_reviewed": len(flags),
                "top_outlier_rows": len(top_outliers),
                "flagged_metric_rows": len(flagged),
                "models_with_outliers": by_model["model_name"].nunique()
                if not by_model.empty
                else 0,
                "entities_with_outliers": by_entity["entity_key"].nunique()
                if not by_entity.empty
                else 0,
                "diagnosed_windows": len(diagnostics),
                "root_cause_rows": len(root_causes),
                "ranking_risk_rows": len(ranking_risk),
                "recommendation": recommendation,
            }
        ]
    )

    top_outliers.to_csv(TOP_METRIC_OUTLIERS_OUTPUT, index=False)
    by_model.to_csv(OUTLIER_BY_MODEL_OUTPUT, index=False)
    by_entity.to_csv(OUTLIER_BY_ENTITY_OUTPUT, index=False)
    diagnostics.to_csv(OUTLIER_WINDOW_DIAGNOSTICS_OUTPUT, index=False)
    root_causes.to_csv(OUTLIER_ROOT_CAUSES_OUTPUT, index=False)
    ranking_risk.to_csv(RANKING_RISK_ASSESSMENT_OUTPUT, index=False)
    summary.to_csv(OUTLIER_DRILLDOWN_SUMMARY_OUTPUT, index=False)

    logger.info("Created %s with %s rows", TOP_METRIC_OUTLIERS_OUTPUT, len(top_outliers))
    logger.info("Created %s with %s rows", OUTLIER_BY_MODEL_OUTPUT, len(by_model))
    logger.info("Created %s with %s rows", OUTLIER_BY_ENTITY_OUTPUT, len(by_entity))
    logger.info(
        "Created %s with %s rows", OUTLIER_WINDOW_DIAGNOSTICS_OUTPUT, len(diagnostics)
    )
    logger.info("Created %s with %s rows", OUTLIER_ROOT_CAUSES_OUTPUT, len(root_causes))
    logger.info(
        "Created %s with %s rows", RANKING_RISK_ASSESSMENT_OUTPUT, len(ranking_risk)
    )
    logger.info("Created %s with %s rows", OUTLIER_DRILLDOWN_SUMMARY_OUTPUT, len(summary))
    logger.info("Stage 5.12A outlier drilldown completed")
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
    run_outlier_drilldown()
