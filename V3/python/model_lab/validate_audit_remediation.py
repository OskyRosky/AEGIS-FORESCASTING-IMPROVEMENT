"""Validate Stage 5.8A audit remediation controls.

This validation checks design remediation only. It does not call fit(), call
predict(), train models, generate forecasts, calculate metrics, or create
rankings.
"""

from __future__ import annotations

import pandas as pd

from model_lab.load_configs import load_yaml_config
from model_lab.models.model_registry import list_models
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("validate_audit_remediation")

CONFIG_DIR = PROJECT_ROOT / "config"
SCORING_DEFINITIONS = CONFIG_DIR / "scoring_definitions.yaml"
MULTISTEP_FORECASTING = CONFIG_DIR / "multistep_forecasting.yaml"
EXECUTION_CONFIG = CONFIG_DIR / "execution.yaml"

RUNS_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "runs"
RUN_MANIFEST_HISTORY = RUNS_DIR / "run_manifest_history.csv"
RUN_METADATA_HISTORY = RUNS_DIR / "run_metadata_history.csv"
EXECUTION_AUDIT_HISTORY = RUNS_DIR / "execution_audit_history.csv"

REQUIRED_SCORING_SECTIONS = {
    "metric_normalization",
    "composite_score",
    "rmse_normalization",
    "bias_handling",
    "zero_actual_handling",
    "stability_score",
    "horizon_score",
}
REQUIRED_NORMALIZED_METRICS = {
    "wmape",
    "mape",
    "rmse",
    "bias",
    "stability",
    "horizon",
}


def _require_file(path) -> None:
    """Validate that a required file exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required remediation file missing: {path}")
    logger.info("Found file: %s", path)


def _validate_scoring_definitions(scoring_config: dict) -> None:
    """Validate scoring design remediation coverage."""

    missing_sections = sorted(REQUIRED_SCORING_SECTIONS - set(scoring_config))
    if missing_sections:
        raise ValueError(f"Missing scoring definition sections: {missing_sections}")

    metric_normalization = scoring_config["metric_normalization"]
    missing_metrics = sorted(
        REQUIRED_NORMALIZED_METRICS - set(metric_normalization.keys())
    )
    if missing_metrics:
        raise ValueError(f"Missing metric normalization definitions: {missing_metrics}")

    composite_score = scoring_config["composite_score"]
    if composite_score.get("method") != "weighted_normalized_score":
        raise ValueError("Composite score must use weighted_normalized_score.")
    if composite_score.get("higher_is_better") is not True:
        raise ValueError("Composite score must define higher_is_better: true.")

    rmse_normalization = scoring_config["rmse_normalization"]
    if rmse_normalization.get("method") != "divide_by_entity_mean_actual":
        raise ValueError("RMSE normalization must divide by entity mean actual.")

    bias_handling = scoring_config["bias_handling"]
    if bias_handling.get("use_absolute_bias") is not True:
        raise ValueError("Bias handling must use absolute bias.")

    zero_actual_handling = scoring_config["zero_actual_handling"]
    if zero_actual_handling.get("exclude_zero_actuals_from_percentage_metrics") is not True:
        raise ValueError("Zero actual handling must exclude zero actual percentage rows.")

    if scoring_config["stability_score"].get("definition") != "variance_of_window_level_wmape":
        raise ValueError("stability_score definition is not set correctly.")
    if scoring_config["horizon_score"].get("definition") != "late_horizon_error_degradation":
        raise ValueError("horizon_score definition is not set correctly.")

    logger.info("Scoring definitions validated")


def _collect_multistep_models(multistep_config: dict) -> set[str]:
    """Collect all model names covered by multistep strategy groups."""

    strategies = multistep_config.get("strategies")
    if not isinstance(strategies, dict):
        raise ValueError("multistep_forecasting.yaml must define strategies.")

    covered_models: set[str] = set()
    for strategy_name, strategy_config in strategies.items():
        applies_to = strategy_config.get("applies_to")
        if not isinstance(applies_to, list) or not applies_to:
            raise ValueError(f"{strategy_name} must define non-empty applies_to list.")
        covered_models.update(applies_to)
        logger.info("%s covers models: %s", strategy_name, applies_to)

    return covered_models


def _validate_multistep_strategy(multistep_config: dict) -> None:
    """Validate multistep strategy coverage and leakage controls."""

    if multistep_config.get("default_strategy") != "recursive":
        raise ValueError("Default multistep strategy must be recursive.")

    registered_models = set(list_models())
    covered_models = _collect_multistep_models(multistep_config)
    missing_models = sorted(registered_models - covered_models)
    unexpected_models = sorted(covered_models - registered_models)
    if missing_models or unexpected_models:
        raise ValueError(
            "Multistep model coverage mismatch. "
            f"missing={missing_models}, unexpected={unexpected_models}"
        )

    leakage_rules = multistep_config.get("leakage_rules", {})
    if leakage_rules.get("train_data_cutoff") != "train_end_date":
        raise ValueError("train_data_cutoff must be train_end_date.")
    if leakage_rules.get("test_actuals_allowed_only_for_evaluation") is not True:
        raise ValueError("Test actuals must be allowed only for evaluation.")
    if leakage_rules.get("no_actual_values_allowed_during_prediction_horizon") is not True:
        raise ValueError("Actual values must be blocked during prediction horizon.")

    logger.info("Multistep strategy covers all %s registered models", len(registered_models))


def _validate_history_file(path, required_columns: set[str]) -> None:
    """Validate that an append-only history file exists and has rows."""

    _require_file(path)
    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"History file is empty: {path}")

    missing_columns = sorted(required_columns - set(frame.columns))
    if missing_columns:
        raise ValueError(f"{path.name} missing columns: {missing_columns}")

    logger.info("%s rows: %s", path.name, len(frame))


def _validate_history_files() -> None:
    """Validate append-only history files created by manifest and audit scripts."""

    _validate_history_file(
        RUN_MANIFEST_HISTORY,
        {"run_id", "run_timestamp", "training_enabled", "dry_run", "planned_jobs"},
    )
    _validate_history_file(
        RUN_METADATA_HISTORY,
        {"run_id", "created_at", "platform_stage", "platform_block", "notes"},
    )
    _validate_history_file(
        EXECUTION_AUDIT_HISTORY,
        {
            "run_id",
            "execution_timestamp",
            "training_enabled",
            "dry_run",
            "planned_jobs",
            "executed_jobs",
            "skipped_jobs",
            "status",
            "message",
        },
    )


def _validate_execution_controls() -> None:
    """Validate that execution controls remain unchanged and safe."""

    execution_config = load_yaml_config(EXECUTION_CONFIG)
    if execution_config.get("training_enabled") is not False:
        raise ValueError("training_enabled must remain false.")
    if execution_config.get("dry_run") is not True:
        raise ValueError("dry_run must remain true.")

    logger.info("training_enabled remains false")
    logger.info("dry_run remains true")


def validate_audit_remediation() -> None:
    """Run all Stage 5.8A remediation validation checks."""

    logger.info("Stage 5.8A audit remediation validation started")

    for path in (SCORING_DEFINITIONS, MULTISTEP_FORECASTING, EXECUTION_CONFIG):
        _require_file(path)

    scoring_config = load_yaml_config(SCORING_DEFINITIONS)
    multistep_config = load_yaml_config(MULTISTEP_FORECASTING)

    _validate_scoring_definitions(scoring_config)
    _validate_multistep_strategy(multistep_config)
    _validate_history_files()
    _validate_execution_controls()

    logger.info("Stage 5.8A audit remediation validation passed")


if __name__ == "__main__":
    validate_audit_remediation()
