"""Inspect and validate the Stage 5.13 baseline ranking policy."""

from __future__ import annotations

import pandas as pd

from model_lab.load_configs import load_yaml_config
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_ranking_policy")

CONFIG_INPUT = PROJECT_ROOT / "config" / "ranking_policy.yaml"
POLICY_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "ranking_policy"
POLICY_DEFINITION = POLICY_DIR / "ranking_policy_definition.csv"
METRIC_WEIGHTS = POLICY_DIR / "ranking_metric_weights.csv"
NORMALIZATION_RULES = POLICY_DIR / "ranking_normalization_rules.csv"
OUTLIER_RULES = POLICY_DIR / "ranking_outlier_rules.csv"
TIEBREAK_RULES = POLICY_DIR / "ranking_tiebreak_rules.csv"
AGGREGATION_RULES = POLICY_DIR / "ranking_aggregation_rules.csv"
POLICY_SUMMARY = POLICY_DIR / "ranking_policy_summary.csv"

EXPECTED_METRICS = {"wmape", "mape", "rmse", "smape", "abs_bias"}


def _require_file(path) -> None:
    """Validate that a required policy file exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required ranking policy file missing: {path}")


def inspect_ranking_policy() -> dict[str, pd.DataFrame]:
    """Inspect ranking policy files and validate required coverage."""

    for path in (
        CONFIG_INPUT,
        POLICY_DEFINITION,
        METRIC_WEIGHTS,
        NORMALIZATION_RULES,
        OUTLIER_RULES,
        TIEBREAK_RULES,
        AGGREGATION_RULES,
        POLICY_SUMMARY,
    ):
        _require_file(path)

    config = load_yaml_config(CONFIG_INPUT)
    policy_definition = pd.read_csv(POLICY_DEFINITION)
    metric_weights = pd.read_csv(METRIC_WEIGHTS)
    normalization_rules = pd.read_csv(NORMALIZATION_RULES)
    outlier_rules = pd.read_csv(OUTLIER_RULES)
    tiebreak_rules = pd.read_csv(TIEBREAK_RULES)
    aggregation_rules = pd.read_csv(AGGREGATION_RULES)
    policy_summary = pd.read_csv(POLICY_SUMMARY)

    if set(config["allowed_metrics"]) != EXPECTED_METRICS:
        raise ValueError("ranking_policy.yaml does not cover all expected metrics.")
    if set(metric_weights["metric_name"]) != EXPECTED_METRICS:
        raise ValueError("Metric weights do not cover all expected metrics.")
    if abs(float(metric_weights["weight"].sum()) - 1.0) > 1e-9:
        raise ValueError("Metric weights must sum to 1.0.")
    if set(normalization_rules["metric_name"]) != EXPECTED_METRICS:
        raise ValueError("Normalization rules do not cover all expected metrics.")
    if len(outlier_rules) < 3:
        raise ValueError("Outlier handling rules are incomplete.")
    if len(aggregation_rules) < 4:
        raise ValueError("Aggregation rules are incomplete.")
    if len(tiebreak_rules) < 5:
        raise ValueError("Tie-break rules are incomplete.")
    if bool(policy_summary["winners_selected"].iloc[0]):
        raise ValueError("Policy stage must not select winners.")
    if bool(policy_summary["tournament_outputs_created"].iloc[0]):
        raise ValueError("Policy stage must not create tournament outputs.")

    logger.info("Policy config loaded: %s", config["policy_name"])
    logger.info("Metrics covered: %s", sorted(EXPECTED_METRICS))
    logger.info("Metric weights sum: %.6f", float(metric_weights["weight"].sum()))
    logger.info("Normalization rules: %s", len(normalization_rules))
    logger.info("Outlier rules: %s", len(outlier_rules))
    logger.info("Aggregation rules: %s", len(aggregation_rules))
    logger.info("Tie-break rules: %s", len(tiebreak_rules))
    logger.info("Stage 5.13 baseline ranking policy inspection passed")
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
    inspect_ranking_policy()
