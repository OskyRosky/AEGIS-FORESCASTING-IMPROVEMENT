"""Run the Stage 5.14 baseline ranking dry run.

This script applies the Stage 5.13 ranking policy to baseline metrics for
diagnostic validation only. It does not select production winners, eliminate
models, run challengers, create tournament outputs, rerun forecasts, or
recompute metrics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from model_lab.load_configs import load_yaml_config
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_baseline_ranking_dry_run")

METRICS_INPUT = PROJECT_ROOT / "outputs" / "model_lab" / "metrics" / "baseline_metrics.csv"
POLICY_CONFIG = PROJECT_ROOT / "config" / "ranking_policy.yaml"
WEIGHTS_INPUT = (
    PROJECT_ROOT / "outputs" / "model_lab" / "ranking_policy" / "ranking_metric_weights.csv"
)
DRY_RUN_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "ranking_dry_run"

SCORES_OUTPUT = DRY_RUN_DIR / "baseline_ranking_scores.csv"
BY_ENTITY_OUTPUT = DRY_RUN_DIR / "baseline_ranking_by_entity.csv"
BY_MODEL_OUTPUT = DRY_RUN_DIR / "baseline_ranking_by_model.csv"
DISTRIBUTION_OUTPUT = DRY_RUN_DIR / "baseline_ranking_distribution.csv"
SUMMARY_OUTPUT = DRY_RUN_DIR / "baseline_ranking_summary.csv"
FLAGS_OUTPUT = DRY_RUN_DIR / "baseline_ranking_flags.csv"

METRICS = ["wmape", "mape", "rmse", "smape", "abs_bias"]
NORMALIZED_COLUMNS = [f"normalized_{metric}" for metric in METRICS]
BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}


def _require_file(path) -> None:
    """Validate that a required dry-run input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required ranking dry-run input missing: {path}")


def _load_inputs() -> tuple[pd.DataFrame, dict[str, float], dict]:
    """Load metrics and policy inputs."""

    for path in (METRICS_INPUT, POLICY_CONFIG, WEIGHTS_INPUT):
        _require_file(path)

    metrics = pd.read_csv(METRICS_INPUT)
    for column in ["wmape", "mape", "rmse", "smape", "bias"]:
        metrics[column] = pd.to_numeric(metrics[column], errors="coerce")
    metrics["abs_bias"] = metrics["bias"].abs()

    weights_frame = pd.read_csv(WEIGHTS_INPUT)
    weights = {
        row["metric_name"]: float(row["weight"]) for _, row in weights_frame.iterrows()
    }
    policy = load_yaml_config(POLICY_CONFIG)
    return metrics, weights, policy


def _clip_outliers(metrics: pd.DataFrame) -> pd.DataFrame:
    """Apply p99 winsorization by entity and metric."""

    scored = metrics.copy()
    for metric in METRICS:
        clipped_column = f"clipped_{metric}"
        scored[clipped_column] = scored[metric]
        p99_by_entity = scored.groupby("entity_key")[metric].transform(
            lambda series: series.quantile(0.99)
        )
        scored[clipped_column] = scored[clipped_column].clip(upper=p99_by_entity)
    return scored


def _normalize_within_entity_window(scored: pd.DataFrame) -> pd.DataFrame:
    """Convert lower-is-better clipped metrics to 0-100 normalized scores."""

    result = scored.copy()
    group_columns = ["entity_key", "window_id"]
    for metric in METRICS:
        clipped_column = f"clipped_{metric}"
        normalized_column = f"normalized_{metric}"

        def normalize_group(series: pd.Series) -> pd.Series:
            if len(series) <= 1:
                return pd.Series(100.0, index=series.index)
            ranks = series.rank(method="average", ascending=True)
            percentile = (ranks - 1) / (len(series) - 1)
            return 100 * (1 - percentile)

        result[normalized_column] = result.groupby(group_columns)[clipped_column].transform(
            normalize_group
        )
    return result


def _score(metrics: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Apply clipping, normalization, weights, and diagnostic positions."""

    scored = _normalize_within_entity_window(_clip_outliers(metrics))
    for metric in METRICS:
        scored[f"weighted_{metric}"] = scored[f"normalized_{metric}"] * weights[metric]
    scored["diagnostic_composite_score"] = scored[
        [f"weighted_{metric}" for metric in METRICS]
    ].sum(axis=1)
    scored["diagnostic_position_within_entity_window"] = scored.groupby(
        ["entity_key", "window_id"]
    )["diagnostic_composite_score"].rank(method="min", ascending=False)
    return scored


def _aggregate_by_entity(scored: pd.DataFrame) -> pd.DataFrame:
    """Aggregate diagnostic scores to entity/model level."""

    rows = (
        scored.groupby(["entity_key", "model_name"], as_index=False)
        .agg(
            window_count=("window_id", "nunique"),
            entity_model_score=("diagnostic_composite_score", "median"),
            median_normalized_wmape=("normalized_wmape", "median"),
            median_normalized_smape=("normalized_smape", "median"),
            median_normalized_rmse=("normalized_rmse", "median"),
            median_normalized_abs_bias=("normalized_abs_bias", "median"),
        )
        .sort_values(["entity_key", "model_name"])
    )
    rows["diagnostic_position_within_entity"] = rows.groupby("entity_key")[
        "entity_model_score"
    ].rank(method="min", ascending=False)
    return rows


def _aggregate_by_model(by_entity: pd.DataFrame) -> pd.DataFrame:
    """Aggregate entity-balanced diagnostic scores to model level."""

    rows = (
        by_entity.groupby("model_name", as_index=False)
        .agg(
            entity_count=("entity_key", "nunique"),
            global_score=("entity_model_score", "mean"),
            median_entity_score=("entity_model_score", "median"),
            min_entity_score=("entity_model_score", "min"),
            max_entity_score=("entity_model_score", "max"),
            avg_normalized_wmape=("median_normalized_wmape", "mean"),
            avg_normalized_smape=("median_normalized_smape", "mean"),
            avg_normalized_rmse=("median_normalized_rmse", "mean"),
            avg_normalized_abs_bias=("median_normalized_abs_bias", "mean"),
        )
        .sort_values("model_name")
    )
    rows["diagnostic_global_position"] = rows["global_score"].rank(
        method="min", ascending=False
    )
    return rows


def _distribution(scored: pd.DataFrame, by_model: pd.DataFrame) -> pd.DataFrame:
    """Build score distribution diagnostics."""

    rows = []
    for name, values in {
        "entity_window_composite": scored["diagnostic_composite_score"],
        "global_model_score": by_model["global_score"],
    }.items():
        rows.append(
            {
                "score_level": name,
                "row_count": len(values),
                "min": float(values.min()),
                "p25": float(values.quantile(0.25)),
                "median": float(values.median()),
                "p75": float(values.quantile(0.75)),
                "p90": float(values.quantile(0.90)),
                "p95": float(values.quantile(0.95)),
                "max": float(values.max()),
                "spread": float(values.max() - values.min()),
            }
        )
    return pd.DataFrame(rows)


def _unclipped_score(metrics: pd.DataFrame, weights: dict[str, float]) -> pd.DataFrame:
    """Calculate a no-clipping comparison score for outlier sensitivity diagnostics."""

    comparison = metrics.copy()
    for metric in METRICS:
        comparison[f"clipped_{metric}"] = comparison[metric]
    comparison = _normalize_within_entity_window(comparison)
    comparison["unclipped_composite_score"] = sum(
        comparison[f"normalized_{metric}"] * weights[metric] for metric in METRICS
    )
    return comparison[
        ["entity_key", "window_id", "model_name", "unclipped_composite_score"]
    ]


def _flags(
    scored: pd.DataFrame,
    by_entity: pd.DataFrame,
    by_model: pd.DataFrame,
    distribution: pd.DataFrame,
    metrics: pd.DataFrame,
    weights: dict[str, float],
) -> pd.DataFrame:
    """Generate ranking dry-run diagnostic flags."""

    flags: list[dict] = []

    global_spread = float(by_model["global_score"].max() - by_model["global_score"].min())
    if global_spread < 1.0:
        flags.append(
            {
                "flag_type": "score_spread_too_small",
                "level": "global_model_score",
                "value": global_spread,
                "threshold": 1.0,
                "message": "Global model scores are tightly clustered.",
            }
        )
    if global_spread > 80.0:
        flags.append(
            {
                "flag_type": "score_spread_too_large",
                "level": "global_model_score",
                "value": global_spread,
                "threshold": 80.0,
                "message": "Global model scores are excessively dispersed.",
            }
        )

    contribution_columns = [f"weighted_{metric}" for metric in METRICS]
    contribution_share = scored[contribution_columns].mean()
    total_contribution = float(contribution_share.sum())
    if total_contribution > 0:
        for metric in METRICS:
            share = float(contribution_share[f"weighted_{metric}"] / total_contribution)
            if share > 0.45:
                flags.append(
                    {
                        "flag_type": "metric_dominance_detected",
                        "level": "metric",
                        "value": share,
                        "threshold": 0.45,
                        "message": f"{metric} contributes more than 45% of average score.",
                    }
                )

    entity_score = by_entity.groupby("entity_key")["entity_model_score"].mean()
    if not entity_score.empty:
        max_entity_share = float(entity_score.max() / entity_score.sum())
        if max_entity_share > 0.10:
            flags.append(
                {
                    "flag_type": "entity_dominance_detected",
                    "level": "entity",
                    "value": max_entity_share,
                    "threshold": 0.10,
                    "message": "One entity contributes unusually large score share.",
                }
            )

    ordered_scores = by_model.sort_values("global_score", ascending=False)[
        "global_score"
    ].to_numpy()
    if len(ordered_scores) > 1:
        min_gap = float(np.min(np.abs(np.diff(ordered_scores))))
        if min_gap < 0.25:
            flags.append(
                {
                    "flag_type": "ranking_instability_detected",
                    "level": "global_model_score",
                    "value": min_gap,
                    "threshold": 0.25,
                    "message": "At least two diagnostic global scores are nearly tied.",
                }
            )

    unclipped = _unclipped_score(metrics, weights)
    sensitivity = scored.merge(
        unclipped, on=["entity_key", "window_id", "model_name"], how="left"
    )
    sensitivity["score_delta_from_outlier_control"] = (
        sensitivity["diagnostic_composite_score"]
        - sensitivity["unclipped_composite_score"]
    ).abs()
    max_delta = float(sensitivity["score_delta_from_outlier_control"].max())
    if max_delta > 15.0:
        flags.append(
            {
                "flag_type": "outlier_dominance_detected",
                "level": "entity_window_model",
                "value": max_delta,
                "threshold": 15.0,
                "message": "Outlier controls materially changed at least one row score.",
            }
        )

    return pd.DataFrame(
        flags,
        columns=["flag_type", "level", "value", "threshold", "message"],
    )


def run_baseline_ranking_dry_run() -> dict[str, pd.DataFrame]:
    """Execute baseline ranking dry-run diagnostics."""

    logger.info("Stage 5.14 baseline ranking dry run started")
    DRY_RUN_DIR.mkdir(parents=True, exist_ok=True)
    metrics, weights, policy = _load_inputs()

    if set(metrics["model_name"]) != BASELINE_MODELS:
        raise ValueError("Metrics input does not contain exactly the baseline models.")
    if set(policy["allowed_metrics"]) != set(METRICS):
        raise ValueError("Policy metrics do not match dry-run metrics.")

    scored = _score(metrics, weights)
    by_entity = _aggregate_by_entity(scored)
    by_model = _aggregate_by_model(by_entity)
    distribution = _distribution(scored, by_model)
    flags = _flags(scored, by_entity, by_model, distribution, metrics, weights)
    summary = pd.DataFrame(
        [
            {
                "metric_rows_processed": len(metrics),
                "score_rows_created": len(scored),
                "entity_score_rows": len(by_entity),
                "model_score_rows": len(by_model),
                "models": scored["model_name"].nunique(),
                "entities": scored["entity_key"].nunique(),
                "windows": scored[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "normalization_method": policy["normalization"]["method"],
                "outlier_control": policy["outlier_handling"]["extreme_outlier_control"],
                "weights_sum": sum(weights.values()),
                "flag_count": len(flags),
                "winner_selected": False,
                "tournament_created": False,
            }
        ]
    )

    scored.to_csv(SCORES_OUTPUT, index=False)
    by_entity.to_csv(BY_ENTITY_OUTPUT, index=False)
    by_model.to_csv(BY_MODEL_OUTPUT, index=False)
    distribution.to_csv(DISTRIBUTION_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    flags.to_csv(FLAGS_OUTPUT, index=False)

    logger.info("Created %s with %s rows", SCORES_OUTPUT, len(scored))
    logger.info("Created %s with %s rows", BY_ENTITY_OUTPUT, len(by_entity))
    logger.info("Created %s with %s rows", BY_MODEL_OUTPUT, len(by_model))
    logger.info("Created %s with %s rows", DISTRIBUTION_OUTPUT, len(distribution))
    logger.info("Created %s with %s rows", SUMMARY_OUTPUT, len(summary))
    logger.info("Created %s with %s rows", FLAGS_OUTPUT, len(flags))
    logger.info("Stage 5.14 baseline ranking dry run completed")
    return {
        "scores": scored,
        "by_entity": by_entity,
        "by_model": by_model,
        "distribution": distribution,
        "summary": summary,
        "flags": flags,
    }


if __name__ == "__main__":
    run_baseline_ranking_dry_run()
