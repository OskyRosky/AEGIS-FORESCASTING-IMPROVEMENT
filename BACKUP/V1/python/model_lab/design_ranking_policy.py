"""Design the Stage 5.13 baseline ranking policy.

This script documents ranking methodology only. It does not rank models, select
winners, create tournaments, rerun forecasts, or recalculate metrics.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("design_ranking_policy")

CONFIG_OUTPUT = PROJECT_ROOT / "config" / "ranking_policy.yaml"
METRICS_INPUT = PROJECT_ROOT / "outputs" / "model_lab" / "metrics" / "baseline_metrics.csv"
POLICY_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "ranking_policy"

POLICY_DEFINITION_OUTPUT = POLICY_DIR / "ranking_policy_definition.csv"
METRIC_WEIGHTS_OUTPUT = POLICY_DIR / "ranking_metric_weights.csv"
NORMALIZATION_RULES_OUTPUT = POLICY_DIR / "ranking_normalization_rules.csv"
OUTLIER_RULES_OUTPUT = POLICY_DIR / "ranking_outlier_rules.csv"
TIEBREAK_RULES_OUTPUT = POLICY_DIR / "ranking_tiebreak_rules.csv"
AGGREGATION_RULES_OUTPUT = POLICY_DIR / "ranking_aggregation_rules.csv"
POLICY_SUMMARY_OUTPUT = POLICY_DIR / "ranking_policy_summary.csv"

METRICS = ["wmape", "mape", "rmse", "smape", "abs_bias"]


def _require_file(path) -> None:
    """Validate that a required policy input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required ranking policy input missing: {path}")


def _write_csv(path, rows: list[dict]) -> pd.DataFrame:
    """Write policy rows to CSV and return the frame."""

    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    logger.info("Created %s with %s rows", path, len(frame))
    return frame


def _write_yaml() -> None:
    """Write the ranking policy YAML config."""

    CONFIG_OUTPUT.write_text(
        """policy_name: baseline_ranking_policy
policy_stage: Stage 5.13
policy_scope: baseline_models_only
policy_status: design_only
allowed_metrics:
  - wmape
  - mape
  - rmse
  - smape
  - abs_bias
normalization:
  method: percentile_rank_within_entity_window
  raw_rmse_allowed: false
  direction: lower_metric_is_better
  normalized_score_range: 0_to_100
  normalized_score_direction: higher_is_better
outlier_handling:
  p95_control: diagnostic_threshold
  p99_control: winsorization_threshold
  extreme_outlier_control: clip_to_p99
  exclusions_allowed: false
  silent_removal_allowed: false
aggregation:
  entity_window_score: weighted_mean_of_normalized_metrics
  entity_score: median_across_windows
  cross_entity_score: equal_weighted_mean_across_entities
  global_score: equal_weighted_mean_of_entity_scores
tie_breaking:
  - normalized_wmape
  - normalized_smape
  - normalized_rmse
  - normalized_abs_bias
  - model_name_ascending
prohibitions:
  rank_models: true
  select_winners: true
  create_tournament_outputs: true
  evaluate_challengers: true
  rerun_forecasts: true
  recalculate_metrics: true
""",
        encoding="utf-8",
    )
    logger.info("Created %s", CONFIG_OUTPUT)


def _policy_definition() -> list[dict]:
    """Define high-level ranking policy constraints."""

    return [
        {
            "policy_area": "scope",
            "rule": "Policy applies to baseline production models only.",
            "rationale": "Challenger evaluation is not active in Stage 5.13.",
        },
        {
            "policy_area": "methodology",
            "rule": "Use normalized metric scores; raw RMSE must not be used directly.",
            "rationale": "Prevents scale and entity-size dominance.",
        },
        {
            "policy_area": "methodology",
            "rule": "All metrics are lower-is-better before normalization and higher-is-better after normalization.",
            "rationale": "Provides a consistent score direction.",
        },
        {
            "policy_area": "prohibition",
            "rule": "Do not select winners or produce model rankings in this stage.",
            "rationale": "Stage 5.13 is policy design only.",
        },
    ]


def _metric_weights() -> list[dict]:
    """Define metric weights for future ranking use."""

    weights = {
        "wmape": 0.30,
        "mape": 0.15,
        "rmse": 0.20,
        "smape": 0.20,
        "abs_bias": 0.15,
    }
    return [
        {
            "metric_name": metric,
            "weight": weight,
            "direction_before_normalization": "lower_is_better",
            "normalized_score_direction": "higher_is_better",
        }
        for metric, weight in weights.items()
    ]


def _normalization_rules() -> list[dict]:
    """Define robust normalization for each metric."""

    return [
        {
            "metric_name": metric,
            "normalization_method": "percentile_rank_within_entity_window",
            "formula": "100 * (1 - percentile_rank(metric_value_after_outlier_control))",
            "score_range": "0_to_100",
            "raw_metric_allowed_in_score": False,
            "rationale": "Controls scale, range, and entity-size dominance.",
        }
        for metric in METRICS
    ]


def _outlier_rules() -> list[dict]:
    """Define explicit outlier handling decisions."""

    return [
        {
            "rule_name": "p95_control",
            "applies_to": "all_metrics",
            "action": "diagnostic_flag_only",
            "silent_removal": False,
            "description": "Values above p95 are retained but flagged for review.",
        },
        {
            "rule_name": "p99_control",
            "applies_to": "all_metrics",
            "action": "winsorize_to_entity_metric_p99_before_normalization",
            "silent_removal": False,
            "description": "Values above p99 are capped for scoring but retained in diagnostics.",
        },
        {
            "rule_name": "extreme_outlier_control",
            "applies_to": "all_metrics",
            "action": "clip_to_p99_no_exclusion",
            "silent_removal": False,
            "description": "No rows are excluded; extreme values are clipped only in normalized scoring input.",
        },
    ]


def _aggregation_rules() -> list[dict]:
    """Define future aggregation levels."""

    return [
        {
            "aggregation_level": "entity_window_model",
            "input": "normalized metric scores for one entity/window/model",
            "method": "weighted_mean",
            "output": "model_score_within_entity_window",
        },
        {
            "aggregation_level": "entity_model",
            "input": "model_score_within_entity_window across windows",
            "method": "median",
            "output": "model_score_within_entity",
        },
        {
            "aggregation_level": "cross_entity_model",
            "input": "model_score_within_entity across entities",
            "method": "equal_weighted_mean",
            "output": "model_score_across_entities",
        },
        {
            "aggregation_level": "global_model",
            "input": "model_score_across_entities",
            "method": "identity",
            "output": "global_model_score",
        },
    ]


def _tiebreak_rules() -> list[dict]:
    """Define deterministic tie-breaking hierarchy."""

    tiebreakers = [
        ("normalized_wmape", "higher_is_better"),
        ("normalized_smape", "higher_is_better"),
        ("normalized_rmse", "higher_is_better"),
        ("normalized_abs_bias", "higher_is_better"),
        ("model_name_ascending", "lexicographic_ascending"),
    ]
    return [
        {
            "priority": priority,
            "tiebreak_field": field,
            "direction": direction,
            "description": "Applied only when prior score fields are tied.",
        }
        for priority, (field, direction) in enumerate(tiebreakers, start=1)
    ]


def design_ranking_policy() -> dict[str, pd.DataFrame]:
    """Create all baseline ranking policy documents."""

    logger.info("Stage 5.13 baseline ranking policy design started")
    _require_file(METRICS_INPUT)
    POLICY_DIR.mkdir(parents=True, exist_ok=True)
    _write_yaml()

    policy_definition = _write_csv(POLICY_DEFINITION_OUTPUT, _policy_definition())
    metric_weights = _write_csv(METRIC_WEIGHTS_OUTPUT, _metric_weights())
    normalization_rules = _write_csv(NORMALIZATION_RULES_OUTPUT, _normalization_rules())
    outlier_rules = _write_csv(OUTLIER_RULES_OUTPUT, _outlier_rules())
    tiebreak_rules = _write_csv(TIEBREAK_RULES_OUTPUT, _tiebreak_rules())
    aggregation_rules = _write_csv(AGGREGATION_RULES_OUTPUT, _aggregation_rules())
    policy_summary = _write_csv(
        POLICY_SUMMARY_OUTPUT,
        [
            {
                "policy_name": "baseline_ranking_policy",
                "metrics_covered": len(METRICS),
                "weights_sum": sum(row["weight"] for row in _metric_weights()),
                "normalization_defined": True,
                "outlier_handling_defined": True,
                "aggregation_defined": True,
                "tiebreaking_defined": True,
                "winners_selected": False,
                "tournament_outputs_created": False,
            }
        ],
    )

    logger.info("Stage 5.13 baseline ranking policy design completed")
    return {
        "policy_definition": policy_definition,
        "metric_weights": metric_weights,
        "normalization_rules": normalization_rules,
        "outlier_rules": outlier_rules,
        "tiebreak_rules": tiebreak_rules,
        "aggregation_rules": aggregation_rules,
        "policy_summary": policy_summary,
    }


if __name__ == "__main__":
    design_ranking_policy()
