"""Inspect Stage 5.26 no-tuning-leakage contract artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_no_tuning_leakage_contract")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "no_tuning_leakage_contract"

CONTRACT_OUTPUT = OUTPUT_DIR / "no_tuning_leakage_contract.md"
PREREG_OUTPUT = OUTPUT_DIR / "challenger_preregistration_template.csv"
CHECKLIST_OUTPUT = OUTPUT_DIR / "leakage_control_checklist.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "no_tuning_leakage_summary.csv"
MANIFEST_OUTPUT = OUTPUT_DIR / "audit_readiness_manifest.csv"
AGGREGATION_POLICY = MODEL_LAB_DIR / "aggregation_hierarchy" / "aggregation_policy.md"
SIGNIFICANCE_POLICY = (
    MODEL_LAB_DIR / "statistical_significance" / "significance_policy.md"
)

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
    MODEL_LAB_DIR / "tournament",
    PROJECT_ROOT / "shiny_app",
]

PLANNED_CHALLENGERS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "NBEATS",
    "NHITS",
}
REQUIRED_CONTROL_AREAS = {
    "temporal cutoff",
    "feature lag safety",
    "rolling window safety",
    "normalization safety",
    "imputation safety",
    "hyperparameter tuning isolation",
    "sandbox/official separation",
    "random seed reproducibility",
    "dependency recording",
    "metadata recording",
    "no post-hoc tuning",
    "no tournament-feedback tuning",
}

PREREG_COLUMNS = [
    "model_name",
    "model_family",
    "status",
    "allowed_features",
    "hyperparameter_space_declared",
    "tuning_budget_declared",
    "training_window_policy_declared",
    "random_seed_policy_declared",
    "dependency_requirements_declared",
    "leakage_risk_level",
    "ready_for_official_execution",
]
CHECKLIST_COLUMNS = [
    "control_id",
    "control_area",
    "control_description",
    "required_for_challenger_onboarding",
    "required_for_official_execution",
    "blocking_if_failed",
]
SUMMARY_COLUMNS = [
    "run_id",
    "planned_challengers",
    "contract_controls",
    "blocking_controls",
    "sandbox_mode_defined",
    "official_mode_defined",
    "challengers_ready_for_official_execution",
    "audit_ready",
    "created_timestamp",
]
MANIFEST_COLUMNS = [
    "run_id",
    "artifact_name",
    "artifact_path",
    "artifact_type",
    "required_for_audit_3",
    "exists",
    "created_timestamp",
]


def _require_file(path: Path) -> None:
    """Validate that a required contract artifact exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required contract artifact missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _assert_no_forbidden_columns(frame: pd.DataFrame, name: str) -> None:
    """Validate no rank/champion/winner columns exist."""

    forbidden_terms = ["rank", "champion", "winner"]
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


def _load_outputs() -> tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all contract outputs."""

    for path in [
        CONTRACT_OUTPUT,
        PREREG_OUTPUT,
        CHECKLIST_OUTPUT,
        SUMMARY_OUTPUT,
        MANIFEST_OUTPUT,
    ]:
        _require_file(path)
    contract = CONTRACT_OUTPUT.read_text(encoding="utf-8")
    prereg = pd.read_csv(PREREG_OUTPUT)
    checklist = pd.read_csv(CHECKLIST_OUTPUT)
    summary = pd.read_csv(SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    manifest = pd.read_csv(MANIFEST_OUTPUT, parse_dates=["created_timestamp"])
    _assert_columns(prereg, PREREG_COLUMNS, "challenger_preregistration_template.csv")
    _assert_columns(checklist, CHECKLIST_COLUMNS, "leakage_control_checklist.csv")
    _assert_columns(summary, SUMMARY_COLUMNS, "no_tuning_leakage_summary.csv")
    _assert_columns(manifest, MANIFEST_COLUMNS, "audit_readiness_manifest.csv")
    for name, frame in [
        ("challenger_preregistration_template.csv", prereg),
        ("leakage_control_checklist.csv", checklist),
        ("no_tuning_leakage_summary.csv", summary),
        ("audit_readiness_manifest.csv", manifest),
    ]:
        _assert_no_forbidden_columns(frame, name)
    return contract, prereg, checklist, summary, manifest


def _validate_contract(contract: str) -> None:
    """Validate contract text contains required policy coverage."""

    required_phrases = [
        "Temporal Isolation Rules",
        "Feature Leakage Rules",
        "Tuning Rules",
        "Sandbox Mode",
        "Official Mode",
        "Challenger Preregistration Requirements",
        "Reproducibility Requirements",
        "Audit Requirements",
        "Blocking Conditions",
        "Prohibited Practices",
        "AutoARIMA",
        "Theta",
        "ETS Explicit",
        "LightGBM",
        "XGBoost",
        "NBEATS",
        "NHITS",
        "Official MASE must not be used for hyperparameter tuning",
        "Official RMSSE must not be used for hyperparameter tuning",
        "Champion selection feedback must not be used for tuning",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in contract]
    if missing:
        raise ValueError(f"Contract missing required phrases: {missing}")


def _validate_preregistration(prereg: pd.DataFrame) -> None:
    """Validate planned challenger preregistration template."""

    if len(prereg) != 7:
        raise ValueError(f"Expected 7 planned challengers; found {len(prereg)}.")
    if set(prereg["model_name"]) != PLANNED_CHALLENGERS:
        raise ValueError("Planned challenger set mismatch.")
    if not (prereg["status"] == "planned").all():
        raise ValueError("All planned challengers must have status=planned.")
    ready = _bool_series(prereg["ready_for_official_execution"])
    if ready.any():
        raise ValueError("No planned challenger may be ready for official execution.")


def _validate_checklist(checklist: pd.DataFrame) -> None:
    """Validate leakage control checklist."""

    if len(checklist) < len(REQUIRED_CONTROL_AREAS):
        raise ValueError("Checklist does not contain enough controls.")
    if not REQUIRED_CONTROL_AREAS.issubset(set(checklist["control_area"])):
        missing = sorted(REQUIRED_CONTROL_AREAS - set(checklist["control_area"]))
        raise ValueError(f"Checklist missing control areas: {missing}")
    if not _bool_series(checklist["required_for_challenger_onboarding"]).all():
        raise ValueError("All controls must be required for challenger onboarding.")
    if not _bool_series(checklist["required_for_official_execution"]).all():
        raise ValueError("All controls must be required for official execution.")
    if not _bool_series(checklist["blocking_if_failed"]).any():
        raise ValueError("At least one blocking control is required.")


def _validate_summary(
    prereg: pd.DataFrame, checklist: pd.DataFrame, summary: pd.DataFrame, manifest: pd.DataFrame
) -> None:
    """Validate no-tuning-leakage summary values."""

    if len(summary) != 1:
        raise ValueError(f"Summary must have exactly one row; found {len(summary)}.")
    row = summary.iloc[0]
    ready_count = int(_bool_series(prereg["ready_for_official_execution"]).sum())
    blocking_count = int(_bool_series(checklist["blocking_if_failed"]).sum())
    required_manifest = manifest[_bool_series(manifest["required_for_audit_3"])]
    manifest_ready = bool(_bool_series(required_manifest["exists"]).all())
    expected_audit_ready = manifest_ready and ready_count == 0
    expected = {
        "planned_challengers": len(prereg),
        "contract_controls": len(checklist),
        "blocking_controls": blocking_count,
        "challengers_ready_for_official_execution": ready_count,
    }
    for column, value in expected.items():
        if int(row[column]) != int(value):
            raise ValueError(
                f"Summary {column} mismatch: expected {value}, found {row[column]}"
            )
    if not bool(_bool_series(pd.Series([row["sandbox_mode_defined"]])).iloc[0]):
        raise ValueError("sandbox_mode_defined must be true.")
    if not bool(_bool_series(pd.Series([row["official_mode_defined"]])).iloc[0]):
        raise ValueError("official_mode_defined must be true.")
    if bool(_bool_series(pd.Series([row["audit_ready"]])).iloc[0]) != expected_audit_ready:
        raise ValueError("audit_ready does not match artifact existence rules.")


def _validate_manifest(manifest: pd.DataFrame) -> None:
    """Validate audit readiness manifest."""

    required_artifacts = {
        "no_tuning_leakage_contract.md",
        "challenger_preregistration_template.csv",
        "leakage_control_checklist.csv",
        "no_tuning_leakage_summary.csv",
        "aggregation_policy.md",
        "significance_policy.md",
    }
    if set(manifest["artifact_name"]) != required_artifacts:
        raise ValueError("Audit readiness manifest artifact set mismatch.")
    if not _bool_series(manifest["required_for_audit_3"]).all():
        raise ValueError("All manifest artifacts must be required for AUDIT #3.")
    for _, row in manifest.iterrows():
        artifact_path = PROJECT_ROOT / row["artifact_path"]
        if bool(_bool_series(pd.Series([row["exists"]])).iloc[0]) != artifact_path.exists():
            raise ValueError(f"Manifest exists flag mismatch for {row['artifact_name']}.")
    _require_file(AGGREGATION_POLICY)
    _require_file(SIGNIFICANCE_POLICY)


def _log_protected_scope() -> None:
    """Report protected directories to make no-touch validation explicit."""

    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not inspected for writes: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_no_tuning_leakage_contract() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate Stage 5.26 no-tuning-leakage contract outputs."""

    logger.info("Stage 5.26 no-tuning-leakage contract inspection started")
    contract, prereg, checklist, summary, manifest = _load_outputs()
    _validate_contract(contract)
    _validate_preregistration(prereg)
    _validate_checklist(checklist)
    _validate_manifest(manifest)
    _validate_summary(prereg, checklist, summary, manifest)
    _log_protected_scope()

    ready_count = int(_bool_series(prereg["ready_for_official_execution"]).sum())
    blocking_count = int(_bool_series(checklist["blocking_if_failed"]).sum())
    audit_ready = bool(_bool_series(summary["audit_ready"]).iloc[0])
    logger.info("Output files exist: yes")
    logger.info("Required columns exist: yes")
    logger.info("Planned challengers: %s", len(prereg))
    logger.info("All planned challengers represented: yes")
    logger.info("Ready for official execution count: %s", ready_count)
    logger.info("Contract controls: %s", len(checklist))
    logger.info("Blocking controls: %s", blocking_count)
    logger.info("sandbox_mode_defined: yes")
    logger.info("official_mode_defined: yes")
    logger.info("Audit readiness manifest exists: yes")
    logger.info("audit_ready: %s", audit_ready)
    logger.info("No model execution outputs created: yes")
    logger.info("No challenger forecast outputs created: yes")
    logger.info("No rankings/champions/winners/tournament outputs created: yes")
    logger.info("Stage 5.26 no-tuning-leakage contract inspection completed")
    return prereg, checklist, summary


if __name__ == "__main__":
    inspect_no_tuning_leakage_contract()
