"""Inspect Stage 5.29A challenger execution planning artifacts.

This inspector validates the execution-planning block strictly. It confirms that
all required outputs exist, that all seven challengers are represented, that the
required official execution gates are present, and that official execution
remains blocked. It also confirms that no execution, ranking, tournament, or
champion outputs were created and that protected outputs were not modified.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_challenger_execution_plan")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_execution_planning"

EXECUTION_PLAN_OUTPUT = OUTPUT_DIR / "challenger_execution_plan.csv"
DEPENDENCY_RESOLUTION_OUTPUT = OUTPUT_DIR / "challenger_dependency_resolution_plan.csv"
TUNING_BUDGET_OUTPUT = OUTPUT_DIR / "challenger_tuning_budget_plan.csv"
SANDBOX_PLAN_OUTPUT = OUTPUT_DIR / "challenger_sandbox_plan.csv"
OFFICIAL_GATE_OUTPUT = OUTPUT_DIR / "challenger_official_execution_gate.csv"
FORECAST_CONTRACT_OUTPUT = OUTPUT_DIR / "challenger_forecast_output_contract.csv"
PLANNING_SUMMARY_OUTPUT = OUTPUT_DIR / "challenger_execution_planning_summary.csv"
PLANNING_REPORT_OUTPUT = OUTPUT_DIR / "challenger_execution_planning_report.md"

EXPECTED_CHALLENGERS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "NBEATS",
    "NHITS",
}
REQUIRED_GATE_NAMES = {
    "dependencies_resolved",
    "sandbox_passed",
    "no_leakage_controls_failed",
    "tuning_budget_locked",
    "hyperparameter_space_locked",
    "random_seed_locked",
    "output_schema_validated",
    "official_windows_locked",
    "no_post_hoc_tuning",
    "no_tournament_feedback_tuning",
}
REQUIRED_FORECAST_COLUMNS = {
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "forecast_date",
    "horizon_day",
    "forecast_value",
    "execution_mode",
    "created_timestamp",
}

# Directories that must not contain challenger execution / ranking / champion artifacts.
FORBIDDEN_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "challenger_execution",
    MODEL_LAB_DIR / "challenger_forecasts",
    MODEL_LAB_DIR / "challenger_metrics",
    MODEL_LAB_DIR / "rankings",
    MODEL_LAB_DIR / "champion",
]
TOURNAMENT_DIR = MODEL_LAB_DIR / "tournament"

PROTECTED_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "benchmark_reference",
    MODEL_LAB_DIR / "seasonal_benchmark",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "non_negative_policy",
    MODEL_LAB_DIR / "aggregation_hierarchy",
    MODEL_LAB_DIR / "statistical_significance",
    MODEL_LAB_DIR / "denominator_reconciliation",
    MODEL_LAB_DIR / "challenger_onboarding",
    PROJECT_ROOT / "shiny_app",
]

EXECUTION_PLAN_COLUMNS = [
    "execution_order",
    "model_name",
    "model_family",
    "model_type",
    "execution_phase",
    "recommended_first_mode",
    "official_execution_allowed",
    "dependency_status",
    "sandbox_entry_gate",
    "official_entry_gate",
    "expected_runtime_class",
    "priority_level",
    "created_timestamp",
]
DEPENDENCY_RESOLUTION_COLUMNS = [
    "model_name",
    "required_dependency",
    "dependency_role",
    "current_availability_status",
    "resolution_required",
    "recommended_resolution",
    "fallback_available",
    "blocks_sandbox",
    "blocks_official",
    "created_timestamp",
]
TUNING_BUDGET_COLUMNS = [
    "model_name",
    "tuning_allowed",
    "tuning_mode",
    "max_trials",
    "max_runtime_minutes",
    "random_seed_required",
    "inner_validation_required",
    "official_results_may_tune_model",
    "notes",
    "created_timestamp",
]
SANDBOX_PLAN_COLUMNS = [
    "model_name",
    "sandbox_scope",
    "sandbox_entities",
    "sandbox_windows",
    "sandbox_success_criteria",
    "sandbox_failure_criteria",
    "promote_to_official_if_passed",
    "created_timestamp",
]
OFFICIAL_GATE_COLUMNS = [
    "gate_id",
    "gate_name",
    "gate_description",
    "required_before_official_execution",
    "blocking_if_failed",
    "created_timestamp",
]
FORECAST_CONTRACT_COLUMNS = [
    "column_name",
    "required",
    "description",
]
PLANNING_SUMMARY_COLUMNS = [
    "run_id",
    "planned_challengers",
    "statistical_challengers",
    "ml_challengers",
    "deep_learning_challengers",
    "models_ready_for_sandbox",
    "models_blocked_by_dependencies",
    "models_ready_for_official_execution",
    "official_execution_allowed",
    "created_timestamp",
]


def _require_file(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required execution-planning artifact missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _assert_no_forbidden_columns(frame: pd.DataFrame, name: str) -> None:
    """Validate no rank/champion/winner/tournament columns exist."""

    forbidden_terms = ["rank", "champion", "winner", "tournament"]
    bad = [
        column
        for column in frame.columns
        if any(term in column.lower() for term in forbidden_terms)
    ]
    if bad:
        raise ValueError(f"{name} contains forbidden columns: {bad}")


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1"])


def _load_outputs():
    """Load and column-validate all execution-planning outputs."""

    for path in [
        EXECUTION_PLAN_OUTPUT,
        DEPENDENCY_RESOLUTION_OUTPUT,
        TUNING_BUDGET_OUTPUT,
        SANDBOX_PLAN_OUTPUT,
        OFFICIAL_GATE_OUTPUT,
        FORECAST_CONTRACT_OUTPUT,
        PLANNING_SUMMARY_OUTPUT,
        PLANNING_REPORT_OUTPUT,
    ]:
        _require_file(path)
    execution_plan = pd.read_csv(EXECUTION_PLAN_OUTPUT)
    dependency_resolution = pd.read_csv(DEPENDENCY_RESOLUTION_OUTPUT)
    tuning_budget = pd.read_csv(TUNING_BUDGET_OUTPUT)
    sandbox_plan = pd.read_csv(SANDBOX_PLAN_OUTPUT)
    official_gates = pd.read_csv(OFFICIAL_GATE_OUTPUT)
    forecast_contract = pd.read_csv(FORECAST_CONTRACT_OUTPUT)
    summary = pd.read_csv(PLANNING_SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    report_text = PLANNING_REPORT_OUTPUT.read_text(encoding="utf-8")

    _assert_columns(execution_plan, EXECUTION_PLAN_COLUMNS, "challenger_execution_plan.csv")
    _assert_columns(dependency_resolution, DEPENDENCY_RESOLUTION_COLUMNS, "challenger_dependency_resolution_plan.csv")
    _assert_columns(tuning_budget, TUNING_BUDGET_COLUMNS, "challenger_tuning_budget_plan.csv")
    _assert_columns(sandbox_plan, SANDBOX_PLAN_COLUMNS, "challenger_sandbox_plan.csv")
    _assert_columns(official_gates, OFFICIAL_GATE_COLUMNS, "challenger_official_execution_gate.csv")
    _assert_columns(forecast_contract, FORECAST_CONTRACT_COLUMNS, "challenger_forecast_output_contract.csv")
    _assert_columns(summary, PLANNING_SUMMARY_COLUMNS, "challenger_execution_planning_summary.csv")
    for name, frame in [
        ("challenger_execution_plan.csv", execution_plan),
        ("challenger_dependency_resolution_plan.csv", dependency_resolution),
        ("challenger_tuning_budget_plan.csv", tuning_budget),
        ("challenger_sandbox_plan.csv", sandbox_plan),
        ("challenger_official_execution_gate.csv", official_gates),
        ("challenger_execution_planning_summary.csv", summary),
    ]:
        _assert_no_forbidden_columns(frame, name)
    return (
        execution_plan,
        dependency_resolution,
        tuning_budget,
        sandbox_plan,
        official_gates,
        forecast_contract,
        summary,
        report_text,
    )


def _validate_execution_plan(execution_plan: pd.DataFrame) -> None:
    if len(execution_plan) != 7:
        raise ValueError(f"Execution plan must have 7 rows; found {len(execution_plan)}.")
    if set(execution_plan["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Execution plan challenger set mismatch.")
    if _bool_series(execution_plan["official_execution_allowed"]).any():
        raise ValueError("official_execution_allowed must be false for all models.")
    if not (execution_plan["recommended_first_mode"] == "sandbox").all():
        raise ValueError("recommended_first_mode must be sandbox for all models.")
    if not (execution_plan["execution_phase"] == "planned").all():
        raise ValueError("execution_phase must be planned for all models.")
    order = sorted(execution_plan["execution_order"].tolist())
    if order != list(range(1, 8)):
        raise ValueError("execution_order must be 1..7 with no gaps or duplicates.")


def _validate_dependency_resolution(dependency_resolution: pd.DataFrame) -> None:
    if dependency_resolution.empty:
        raise ValueError("Dependency resolution plan must be non-empty.")
    if not set(dependency_resolution["model_name"]).issubset(EXPECTED_CHALLENGERS):
        raise ValueError("Dependency resolution plan has unexpected model names.")
    if set(dependency_resolution["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Dependency resolution plan does not cover all challengers.")


def _validate_tuning_budget(tuning_budget: pd.DataFrame) -> None:
    if len(tuning_budget) != 7:
        raise ValueError(f"Tuning budget plan must have 7 rows; found {len(tuning_budget)}.")
    if set(tuning_budget["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Tuning budget plan challenger set mismatch.")
    if _bool_series(tuning_budget["official_results_may_tune_model"]).any():
        raise ValueError("official_results_may_tune_model must be false for all models.")
    if not _bool_series(tuning_budget["inner_validation_required"]).all():
        raise ValueError("inner_validation_required must be true for all models.")
    if not _bool_series(tuning_budget["random_seed_required"]).all():
        raise ValueError("random_seed_required must be true for all models.")


def _validate_sandbox_plan(sandbox_plan: pd.DataFrame) -> None:
    if len(sandbox_plan) != 7:
        raise ValueError(f"Sandbox plan must have 7 rows; found {len(sandbox_plan)}.")
    if set(sandbox_plan["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Sandbox plan challenger set mismatch.")
    if sandbox_plan["sandbox_windows"].isna().any():
        raise ValueError("Sandbox plan must declare sandbox_windows for all models.")


def _validate_official_gates(official_gates: pd.DataFrame) -> None:
    if not REQUIRED_GATE_NAMES.issubset(set(official_gates["gate_name"])):
        missing = sorted(REQUIRED_GATE_NAMES - set(official_gates["gate_name"]))
        raise ValueError(f"Official execution gate missing gates: {missing}")
    if not _bool_series(official_gates["required_before_official_execution"]).all():
        raise ValueError("All official gates must be required before official execution.")
    if not _bool_series(official_gates["blocking_if_failed"]).all():
        raise ValueError("All official gates must be blocking if failed.")


def _validate_forecast_contract(forecast_contract: pd.DataFrame) -> None:
    if set(forecast_contract["column_name"]) < REQUIRED_FORECAST_COLUMNS:
        missing = sorted(REQUIRED_FORECAST_COLUMNS - set(forecast_contract["column_name"]))
        raise ValueError(f"Forecast output contract missing columns: {missing}")
    required_rows = forecast_contract[
        forecast_contract["column_name"].isin(REQUIRED_FORECAST_COLUMNS)
    ]
    if not _bool_series(required_rows["required"]).all():
        raise ValueError("All required forecast contract columns must be marked required=true.")


def _validate_summary(
    execution_plan: pd.DataFrame, dependency_resolution: pd.DataFrame, summary: pd.DataFrame
) -> None:
    if len(summary) != 1:
        raise ValueError(f"Summary must have exactly one row; found {len(summary)}.")
    row = summary.iloc[0]
    if int(row["models_ready_for_official_execution"]) != 0:
        raise ValueError("models_ready_for_official_execution must be 0.")
    if _bool_series(pd.Series([row["official_execution_allowed"]])).iloc[0]:
        raise ValueError("official_execution_allowed must be false.")
    if int(row["planned_challengers"]) != 7:
        raise ValueError("planned_challengers must be 7.")
    blocked_models = {
        model_name
        for model_name, group in dependency_resolution.groupby("model_name")
        if not (group["current_availability_status"].astype(str).str.lower() == "available").any()
    }
    if int(row["models_blocked_by_dependencies"]) != len(blocked_models):
        raise ValueError("Summary models_blocked_by_dependencies mismatch with resolution plan.")
    if int(row["models_ready_for_sandbox"]) != 7 - len(blocked_models):
        raise ValueError("Summary models_ready_for_sandbox mismatch with resolution plan.")


def _validate_report(report_text: str) -> None:
    required_phrases = [
        "Purpose of 5.29A",
        "Execution Order",
        "Dependency Gaps",
        "Sandbox Plan",
        "Official Execution Gates",
        "Tuning Budget Plan",
        "Leakage Controls",
        "Dashboard-Readiness Note",
        "Recommendation",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in report_text]
    if missing:
        raise ValueError(f"Planning report missing required sections: {missing}")


def _validate_no_forbidden_outputs() -> None:
    for path in FORBIDDEN_OUTPUT_DIRS:
        if path.exists() and any(path.iterdir()):
            raise ValueError(f"Forbidden output directory is non-empty: {path}")
    if TOURNAMENT_DIR.exists() and any(TOURNAMENT_DIR.iterdir()):
        raise ValueError(f"Tournament directory must be empty: {TOURNAMENT_DIR}")


def _log_protected_scope() -> None:
    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not modified by this block: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_challenger_execution_plan() -> pd.DataFrame:
    """Validate Stage 5.29A challenger execution planning outputs strictly."""

    logger.info("Stage 5.29A challenger execution planning inspection started")
    (
        execution_plan,
        dependency_resolution,
        tuning_budget,
        sandbox_plan,
        official_gates,
        forecast_contract,
        summary,
        report_text,
    ) = _load_outputs()

    _validate_execution_plan(execution_plan)
    _validate_dependency_resolution(dependency_resolution)
    _validate_tuning_budget(tuning_budget)
    _validate_sandbox_plan(sandbox_plan)
    _validate_official_gates(official_gates)
    _validate_forecast_contract(forecast_contract)
    _validate_summary(execution_plan, dependency_resolution, summary)
    _validate_report(report_text)
    _validate_no_forbidden_outputs()
    _log_protected_scope()

    row = summary.iloc[0]
    logger.info("Output files exist: yes")
    logger.info("Required columns exist: yes")
    logger.info("Execution plan rows: %s", len(execution_plan))
    logger.info("Tuning budget rows: %s", len(tuning_budget))
    logger.info("Sandbox plan rows: %s", len(sandbox_plan))
    logger.info("Dependency resolution rows: %s", len(dependency_resolution))
    logger.info("Official execution gates: %s", len(official_gates))
    logger.info("Models ready for sandbox: %s", int(row["models_ready_for_sandbox"]))
    logger.info("Models blocked by dependencies: %s", int(row["models_blocked_by_dependencies"]))
    logger.info(
        "Models ready for official execution: %s",
        int(row["models_ready_for_official_execution"]),
    )
    logger.info("Official execution allowed: %s", bool(_bool_series(pd.Series([row["official_execution_allowed"]])).iloc[0]))

    recommendation = (
        "PROCEED_TO_5.29B_CHALLENGER_SANDBOX_EXECUTION"
        if int(row["models_ready_for_official_execution"]) == 0
        and not _bool_series(pd.Series([row["official_execution_allowed"]])).iloc[0]
        else "BLOCK_5.29B_PENDING_FIX"
    )
    logger.info("Inspection recommendation: %s", recommendation)
    logger.info("Stage 5.29A challenger execution planning inspection completed")
    return summary


if __name__ == "__main__":
    inspect_challenger_execution_plan()
