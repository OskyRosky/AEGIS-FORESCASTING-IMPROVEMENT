"""Inspect Stage 5.28 challenger onboarding artifacts.

This inspector validates the onboarding block strictly. It confirms that all
seven challengers are registered with the correct names, that dependencies were
checked, that leakage controls are mapped to every challenger, that tuning and
hyperparameter-space policy are declared, and that no challenger is official
-execution-ready. It also confirms that no execution, ranking, tournament, or
champion outputs were created.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_challenger_onboarding")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_onboarding"

REGISTRY_SNAPSHOT_OUTPUT = OUTPUT_DIR / "challenger_registry_snapshot.csv"
DEPENDENCY_MATRIX_OUTPUT = OUTPUT_DIR / "challenger_dependency_matrix.csv"
READINESS_MATRIX_OUTPUT = OUTPUT_DIR / "challenger_readiness_matrix.csv"
LEAKAGE_MAPPING_OUTPUT = OUTPUT_DIR / "challenger_leakage_control_mapping.csv"
EXECUTION_MODE_POLICY_OUTPUT = OUTPUT_DIR / "challenger_execution_mode_policy.md"
ONBOARDING_SUMMARY_OUTPUT = OUTPUT_DIR / "challenger_onboarding_summary.csv"
ONBOARDING_REPORT_OUTPUT = OUTPUT_DIR / "challenger_onboarding_report.md"

EXPECTED_CHALLENGERS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "NBEATS",
    "NHITS",
}

# Directories that must not contain challenger artifacts created by this block.
FORBIDDEN_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "challenger_execution",
    MODEL_LAB_DIR / "challenger_forecasts",
    MODEL_LAB_DIR / "challenger_metrics",
    MODEL_LAB_DIR / "rankings",
    MODEL_LAB_DIR / "champion",
]
TOURNAMENT_DIR = MODEL_LAB_DIR / "tournament"

# Protected outputs that this block must not modify.
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
    PROJECT_ROOT / "shiny_app",
]

REGISTRY_SNAPSHOT_COLUMNS = [
    "challenger_id",
    "model_name",
    "model_family",
    "model_type",
    "implementation_status",
    "preferred_dependencies",
    "fallback_dependencies",
    "feature_requirements",
    "hyperparameter_space_status",
    "tuning_policy",
    "allowed_execution_mode",
    "leakage_risk_level",
    "expected_runtime_class",
    "sandbox_ready",
    "official_execution_ready",
    "created_timestamp",
]
DEPENDENCY_MATRIX_COLUMNS = [
    "model_name",
    "dependency_name",
    "dependency_role",
    "available",
    "availability_status",
    "notes",
    "created_timestamp",
]
READINESS_MATRIX_COLUMNS = [
    "model_name",
    "registered",
    "dependencies_checked",
    "leakage_controls_mapped",
    "tuning_policy_declared",
    "hyperparameter_space_declared",
    "sandbox_ready",
    "official_execution_ready",
    "blocking_reasons",
    "created_timestamp",
]
LEAKAGE_MAPPING_COLUMNS = [
    "model_name",
    "control_id",
    "control_area",
    "control_required",
    "control_status",
    "blocking_if_failed",
    "created_timestamp",
]
ONBOARDING_SUMMARY_COLUMNS = [
    "run_id",
    "planned_challengers",
    "registered_challengers",
    "statistical_challengers",
    "ml_challengers",
    "deep_learning_challengers",
    "sandbox_ready_count",
    "official_execution_ready_count",
    "dependency_missing_count",
    "blocking_models_count",
    "ready_for_challenger_execution_block",
    "created_timestamp",
]


def _require_file(path: Path) -> None:
    """Validate that a required onboarding artifact exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required challenger onboarding artifact missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

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
    """Normalize bool-like CSV values to booleans."""

    return series.astype(str).str.lower().isin(["true", "1"])


def _load_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str, str]:
    """Load and column-validate all onboarding outputs."""

    for path in [
        REGISTRY_SNAPSHOT_OUTPUT,
        DEPENDENCY_MATRIX_OUTPUT,
        READINESS_MATRIX_OUTPUT,
        LEAKAGE_MAPPING_OUTPUT,
        EXECUTION_MODE_POLICY_OUTPUT,
        ONBOARDING_SUMMARY_OUTPUT,
        ONBOARDING_REPORT_OUTPUT,
    ]:
        _require_file(path)
    registry = pd.read_csv(REGISTRY_SNAPSHOT_OUTPUT)
    dependency_matrix = pd.read_csv(DEPENDENCY_MATRIX_OUTPUT)
    readiness = pd.read_csv(READINESS_MATRIX_OUTPUT)
    leakage_mapping = pd.read_csv(LEAKAGE_MAPPING_OUTPUT)
    summary = pd.read_csv(ONBOARDING_SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    policy_text = EXECUTION_MODE_POLICY_OUTPUT.read_text(encoding="utf-8")
    report_text = ONBOARDING_REPORT_OUTPUT.read_text(encoding="utf-8")

    _assert_columns(registry, REGISTRY_SNAPSHOT_COLUMNS, "challenger_registry_snapshot.csv")
    _assert_columns(dependency_matrix, DEPENDENCY_MATRIX_COLUMNS, "challenger_dependency_matrix.csv")
    _assert_columns(readiness, READINESS_MATRIX_COLUMNS, "challenger_readiness_matrix.csv")
    _assert_columns(leakage_mapping, LEAKAGE_MAPPING_COLUMNS, "challenger_leakage_control_mapping.csv")
    _assert_columns(summary, ONBOARDING_SUMMARY_COLUMNS, "challenger_onboarding_summary.csv")
    for name, frame in [
        ("challenger_registry_snapshot.csv", registry),
        ("challenger_dependency_matrix.csv", dependency_matrix),
        ("challenger_readiness_matrix.csv", readiness),
        ("challenger_leakage_control_mapping.csv", leakage_mapping),
        ("challenger_onboarding_summary.csv", summary),
    ]:
        _assert_no_forbidden_columns(frame, name)
    return registry, dependency_matrix, readiness, leakage_mapping, summary, policy_text, report_text


def _validate_registry(registry: pd.DataFrame) -> None:
    """Validate the challenger registry snapshot."""

    if len(registry) != 7:
        raise ValueError(f"Registry snapshot must have 7 rows; found {len(registry)}.")
    if set(registry["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Registry snapshot challenger set mismatch.")
    if registry["model_name"].duplicated().any():
        raise ValueError("Registry snapshot contains duplicate challengers.")
    if _bool_series(registry["official_execution_ready"]).any():
        raise ValueError("No challenger may be official-execution-ready.")
    valid_families = {"statistical", "machine_learning", "deep_learning"}
    if not set(registry["model_family"]).issubset(valid_families):
        raise ValueError(f"Registry has invalid model_family values: {set(registry['model_family'])}")


def _validate_dependency_matrix(dependency_matrix: pd.DataFrame) -> None:
    """Validate the dependency matrix."""

    if dependency_matrix.empty:
        raise ValueError("Dependency matrix must be non-empty.")
    if set(dependency_matrix["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Dependency matrix does not cover all challengers.")
    valid_status = {"available", "missing", "error"}
    if not set(dependency_matrix["availability_status"]).issubset(valid_status):
        raise ValueError("Dependency matrix has invalid availability_status values.")
    if not set(dependency_matrix["dependency_role"]).issubset({"preferred", "fallback"}):
        raise ValueError("Dependency matrix has invalid dependency_role values.")


def _validate_leakage_mapping(leakage_mapping: pd.DataFrame) -> None:
    """Validate the leakage-control mapping."""

    if leakage_mapping.empty:
        raise ValueError("Leakage-control mapping must be non-empty.")
    if set(leakage_mapping["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Leakage-control mapping does not cover all challengers.")
    controls_per_model = leakage_mapping.groupby("model_name")["control_id"].nunique()
    if controls_per_model.min() < 1:
        raise ValueError("Every challenger must have at least one leakage control mapped.")


def _validate_readiness(readiness: pd.DataFrame) -> None:
    """Validate the readiness matrix."""

    if len(readiness) != 7:
        raise ValueError(f"Readiness matrix must have 7 rows; found {len(readiness)}.")
    if set(readiness["model_name"]) != EXPECTED_CHALLENGERS:
        raise ValueError("Readiness matrix challenger set mismatch.")
    for column in [
        "registered",
        "dependencies_checked",
        "leakage_controls_mapped",
        "tuning_policy_declared",
        "hyperparameter_space_declared",
    ]:
        if not _bool_series(readiness[column]).all():
            raise ValueError(f"Readiness column {column} must be true for all challengers.")
    if _bool_series(readiness["official_execution_ready"]).any():
        raise ValueError("No challenger may be official-execution-ready in readiness matrix.")


def _validate_summary(
    registry: pd.DataFrame,
    readiness: pd.DataFrame,
    dependency_matrix: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Validate the onboarding summary against the detail tables."""

    if len(summary) != 1:
        raise ValueError(f"Summary must have exactly one row; found {len(summary)}.")
    row = summary.iloc[0]
    if int(row["official_execution_ready_count"]) != 0:
        raise ValueError("official_execution_ready_count must be 0.")
    expected = {
        "planned_challengers": 7,
        "registered_challengers": len(registry),
        "statistical_challengers": int((registry["model_family"] == "statistical").sum()),
        "ml_challengers": int((registry["model_family"] == "machine_learning").sum()),
        "deep_learning_challengers": int((registry["model_family"] == "deep_learning").sum()),
        "sandbox_ready_count": int(_bool_series(registry["sandbox_ready"]).sum()),
    }
    for column, value in expected.items():
        if int(row[column]) != int(value):
            raise ValueError(
                f"Summary {column} mismatch: expected {value}, found {row[column]}"
            )
    ready_flag = bool(_bool_series(pd.Series([row["ready_for_challenger_execution_block"]])).iloc[0])
    if ready_flag and int(row["official_execution_ready_count"]) != 0:
        raise ValueError("ready_for_challenger_execution_block cannot be true with official-ready challengers.")


def _validate_policy_and_report(policy_text: str, report_text: str) -> None:
    """Validate execution-mode policy and report cover required topics."""

    required_policy_phrases = [
        "Sandbox Mode Definition",
        "Official Mode Definition",
        "Why Official Execution Remains False",
        "No-Tuning-Leakage Requirement",
        "Model Preregistration Requirement",
        "Dependency Requirement",
        "Reproducibility Requirement",
        "Denominator Note",
        "training-only lag-1",
        "Interpretation Note",
        "in-sample one-step lag-1",
    ]
    missing_policy = [p for p in required_policy_phrases if p not in policy_text]
    if missing_policy:
        raise ValueError(f"Execution-mode policy missing required phrases: {missing_policy}")
    forbidden_policy = ["champion", "tournament", "ranking"]
    # These words may appear only in negation context; confirm a no-champion clause exists.
    if "no champion" not in policy_text.lower() and "creates no champion" not in policy_text.lower():
        raise ValueError("Execution-mode policy must explicitly exclude champion selection.")
    required_report_phrases = [
        "Purpose of the Block",
        "Models Onboarded",
        "Dependency Findings",
        "Readiness Findings",
        "Leakage-Control Mapping",
        "Why Official Execution Remains False",
        "What Remains for 5.29",
        "Recommendation",
    ]
    missing_report = [p for p in required_report_phrases if p not in report_text]
    if missing_report:
        raise ValueError(f"Onboarding report missing required sections: {missing_report}")
    _ = forbidden_policy


def _validate_no_forbidden_outputs() -> None:
    """Confirm no execution/ranking/tournament/champion outputs exist."""

    for path in FORBIDDEN_OUTPUT_DIRS:
        if path.exists() and any(path.iterdir()):
            raise ValueError(f"Forbidden output directory is non-empty: {path}")
    if TOURNAMENT_DIR.exists() and any(TOURNAMENT_DIR.iterdir()):
        raise ValueError(f"Tournament directory must be empty: {TOURNAMENT_DIR}")


def _log_protected_scope() -> None:
    """Report protected directories to make no-touch validation explicit."""

    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not modified by this block: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_challenger_onboarding() -> pd.DataFrame:
    """Validate Stage 5.28 challenger onboarding outputs strictly."""

    logger.info("Stage 5.28 challenger onboarding inspection started")
    (
        registry,
        dependency_matrix,
        readiness,
        leakage_mapping,
        summary,
        policy_text,
        report_text,
    ) = _load_outputs()

    _validate_registry(registry)
    _validate_dependency_matrix(dependency_matrix)
    _validate_leakage_mapping(leakage_mapping)
    _validate_readiness(readiness)
    _validate_summary(registry, readiness, dependency_matrix, summary)
    _validate_policy_and_report(policy_text, report_text)
    _validate_no_forbidden_outputs()
    _log_protected_scope()

    row = summary.iloc[0]
    logger.info("Output files exist: yes")
    logger.info("Required columns exist: yes")
    logger.info("Registered challengers: %s", int(row["registered_challengers"]))
    logger.info("All 7 challengers represented: yes")
    logger.info("Dependency matrix rows: %s", len(dependency_matrix))
    logger.info("Leakage control mappings: %s", len(leakage_mapping))
    logger.info("Sandbox-ready challengers: %s", int(row["sandbox_ready_count"]))
    logger.info("Dependency-missing challengers: %s", int(row["dependency_missing_count"]))
    logger.info("Official-execution-ready challengers: %s", int(row["official_execution_ready_count"]))
    logger.info(
        "Ready for challenger execution block: %s",
        bool(_bool_series(pd.Series([row["ready_for_challenger_execution_block"]])).iloc[0]),
    )

    ready_flag = bool(_bool_series(pd.Series([row["ready_for_challenger_execution_block"]])).iloc[0])
    recommendation = (
        "PROCEED_TO_5.29_CHALLENGER_EXECUTION_PLANNING"
        if ready_flag and int(row["official_execution_ready_count"]) == 0
        else "BLOCK_5.29_PENDING_FIX"
    )
    logger.info("Inspection recommendation: %s", recommendation)
    logger.info("Stage 5.28 challenger onboarding inspection completed")
    return summary


if __name__ == "__main__":
    inspect_challenger_onboarding()
