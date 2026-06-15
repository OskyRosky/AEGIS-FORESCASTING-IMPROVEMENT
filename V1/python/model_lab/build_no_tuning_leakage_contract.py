"""Build the Stage 5.26 no-tuning-leakage contract artifacts.

This script creates policy, checklist, preregistration, and audit readiness
artifacts only. It does not run models, register challengers for execution,
create forecasts, calculate metrics, create rankings, or write tournament
outputs.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("build_no_tuning_leakage_contract")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "no_tuning_leakage_contract"

WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
AGGREGATION_POLICY = MODEL_LAB_DIR / "aggregation_hierarchy" / "aggregation_policy.md"
SIGNIFICANCE_POLICY = (
    MODEL_LAB_DIR / "statistical_significance" / "significance_policy.md"
)
OPTIONAL_CONFIGS = [
    PROJECT_ROOT / "config" / "model_registry.yaml",
    PROJECT_ROOT / "config" / "training_job_plan.yaml",
    PROJECT_ROOT / "config" / "execution.yaml",
]

CONTRACT_OUTPUT = OUTPUT_DIR / "no_tuning_leakage_contract.md"
PREREG_OUTPUT = OUTPUT_DIR / "challenger_preregistration_template.csv"
CHECKLIST_OUTPUT = OUTPUT_DIR / "leakage_control_checklist.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "no_tuning_leakage_summary.csv"
MANIFEST_OUTPUT = OUTPUT_DIR / "audit_readiness_manifest.csv"

RUN_ID_PREFIX = "no_tuning_leakage_contract"
PLANNED_CHALLENGERS = [
    ("AutoARIMA", "ClassicalStatistical"),
    ("Theta", "ClassicalStatistical"),
    ("ETS Explicit", "ClassicalStatistical"),
    ("LightGBM", "GradientBoosting"),
    ("XGBoost", "GradientBoosting"),
    ("NBEATS", "DeepLearning"),
    ("NHITS", "DeepLearning"),
]

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


def _require_file(path) -> None:
    """Validate required policy/input file exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required contract input missing: {path}")


def _inspect_inputs() -> dict[str, bool]:
    """Inspect required and optional inputs without modifying them."""

    _require_file(WINDOWS_INPUT)
    _require_file(AGGREGATION_POLICY)
    _require_file(SIGNIFICANCE_POLICY)
    return {str(path.relative_to(PROJECT_ROOT)): path.exists() for path in OPTIONAL_CONFIGS}


def _contract_markdown(timestamp: str, optional_configs: dict[str, bool]) -> str:
    """Create no-tuning-leakage contract text."""

    optional_lines = "\n".join(
        f"- `{name}`: {'present' if exists else 'missing informational'}"
        for name, exists in optional_configs.items()
    )
    challengers = "\n".join(f"- {name}" for name, _ in PLANNED_CHALLENGERS)
    return f"""# No-Tuning-Leakage Contract - Stage 5.26

Created timestamp: {timestamp}

## Purpose

This contract governs all future challenger models for TESSERACT v2 / AEGIS Forecast Improvement Platform. Its purpose is to prevent tuning leakage from test windows, future actuals, benchmark results, MASE/RMSSE outcomes, statistical significance outputs, tournament outputs, and champion-selection feedback.

## Scope

The contract applies to all future challenger onboarding, sandbox execution, official execution, feature generation, hyperparameter tuning, metadata capture, and audit review. It does not register or execute challengers in this block.

## Allowed Future Challenger Families

{challengers}

These challengers are planned only. They are not ready for official execution until preregistration, leakage controls, and audit checks pass.

## Temporal Isolation Rules

- For every backtesting window, training data must end at `train_end_date`.
- Test data must not be used for fitting.
- Future actuals must not be used for features.
- Future actuals must not be used for hyperparameter tuning.
- Forecast horizon actuals may only be used after forecasts are generated and only for evaluation.
- Models must not use data from future windows to tune earlier windows.

## Feature Leakage Rules

- No future timestamps may be used in features.
- No target leakage is allowed.
- Rolling windows must not include test-period actuals.
- Lag features must not be created from future values.
- Global transformations must not be fitted on full history including test rows.
- Normalization must not be fitted using future or test rows.
- Imputation must not use future or test rows.

## Tuning Rules

- Official MASE must not be used for hyperparameter tuning.
- Official RMSSE must not be used for hyperparameter tuning.
- Statistical significance outputs must not be used for tuning.
- Tournament rank must not be used for tuning.
- Champion selection feedback must not be used for tuning.
- If tuning is needed, it must occur only inside an explicitly defined inner-validation process using training-only data.

## Sandbox Mode

`sandbox_mode` is exploratory and may be used for code stability checks. Sandbox results are not eligible for champion decisions, cannot be promoted to official tournament results, and cannot be used as official benchmark evidence.

## Official Mode

`official_mode` requires locked configuration, locked windows, locked features, locked seeds, no post-hoc tuning, and formal metadata capture. Official mode is used for formal comparison only.

## Challenger Preregistration Requirements

Before official challenger execution, each challenger must declare:

- `model_name`
- `model_family`
- `allowed_features`
- `hyperparameter_space`
- `tuning_budget`
- `training_window_policy`
- `random_seed_policy`
- `dependency_requirements`
- `expected_runtime_class`
- `leakage_risk_level`

## Cross-Entity and Entity/Window Isolation

Cross-entity learning is allowed only when the model design explicitly declares it, the training data remains temporally valid, and no test-window outcomes leak across entities. Entity/window isolation must be preserved for every official backtesting window.

## Reproducibility Requirements

Every official challenger run must record:

- `run_id`
- git status
- config snapshot
- input data hashes if available
- random seeds
- dependency versions if available
- model registry snapshot
- execution timestamp

## Audit Requirements

Every challenger must produce enough metadata for Claude Code and future reviewers to inspect what data was used, what features were used, what hyperparameters were used, whether tuning occurred, and whether the run was sandbox or official.

## Blocking Conditions

Official challenger execution is blocked if any required leakage control fails, preregistration is incomplete, official mode is not declared, tuning uses official results, future actuals are used before forecast generation, metadata is insufficient for audit, or the run cannot be reproduced.

## Prohibited Practices

- Using test-window actuals for fitting.
- Using future actuals for features or tuning.
- Tuning from official MASE/RMSSE outcomes.
- Tuning from significance outcomes.
- Tuning from tournament or champion feedback.
- Promoting sandbox outputs to official tournament evidence.
- Creating challenger official outputs without preregistration and audit controls.

## Input Configuration Findings

Missing optional config files are informational in this block and do not block contract creation:

{optional_lines}
"""


def _preregistration() -> pd.DataFrame:
    """Create planned challenger preregistration template."""

    rows = []
    for model_name, model_family in PLANNED_CHALLENGERS:
        rows.append(
            {
                "model_name": model_name,
                "model_family": model_family,
                "status": "planned",
                "allowed_features": "TBD_before_official_execution",
                "hyperparameter_space_declared": False,
                "tuning_budget_declared": False,
                "training_window_policy_declared": False,
                "random_seed_policy_declared": False,
                "dependency_requirements_declared": False,
                "leakage_risk_level": "TBD",
                "ready_for_official_execution": False,
            }
        )
    return pd.DataFrame(rows, columns=PREREG_COLUMNS)


def _checklist() -> pd.DataFrame:
    """Create leakage control checklist."""

    controls = [
        ("LC-001", "temporal cutoff", "Training data ends at train_end_date for each window."),
        ("LC-002", "feature lag safety", "Lag features are created only from historical values available before forecast generation."),
        ("LC-003", "rolling window safety", "Rolling windows exclude test-period and future actual values."),
        ("LC-004", "normalization safety", "Normalizers are fitted on training-only rows within each window."),
        ("LC-005", "imputation safety", "Imputation uses training-only information and no future/test rows."),
        ("LC-006", "hyperparameter tuning isolation", "Tuning occurs only through inner validation using training-only data."),
        ("LC-007", "sandbox/official separation", "Sandbox outputs cannot be promoted to official tournament evidence."),
        ("LC-008", "random seed reproducibility", "Official runs record locked seeds or deterministic policy."),
        ("LC-009", "dependency recording", "Official runs record dependency versions when available."),
        ("LC-010", "metadata recording", "Official runs record data, features, hyperparameters, tuning status, and mode."),
        ("LC-011", "no post-hoc tuning", "No tuning after official evaluation on benchmark windows."),
        ("LC-012", "no tournament-feedback tuning", "No tuning from tournament rank, champion feedback, significance, MASE, or RMSSE outcomes."),
    ]
    return pd.DataFrame(
        [
            {
                "control_id": control_id,
                "control_area": area,
                "control_description": description,
                "required_for_challenger_onboarding": True,
                "required_for_official_execution": True,
                "blocking_if_failed": True,
            }
            for control_id, area, description in controls
        ],
        columns=CHECKLIST_COLUMNS,
    )


def _manifest(run_id: str, timestamp: str) -> pd.DataFrame:
    """Create audit readiness manifest."""

    artifacts = [
        ("no_tuning_leakage_contract.md", CONTRACT_OUTPUT, "contract", True),
        ("challenger_preregistration_template.csv", PREREG_OUTPUT, "template", True),
        ("leakage_control_checklist.csv", CHECKLIST_OUTPUT, "checklist", True),
        ("no_tuning_leakage_summary.csv", SUMMARY_OUTPUT, "summary", True),
        ("aggregation_policy.md", AGGREGATION_POLICY, "upstream_policy", True),
        ("significance_policy.md", SIGNIFICANCE_POLICY, "upstream_policy", True),
    ]
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "artifact_name": name,
                "artifact_path": str(path.relative_to(PROJECT_ROOT)),
                "artifact_type": artifact_type,
                "required_for_audit_3": required,
                "exists": path.exists(),
                "created_timestamp": timestamp,
            }
            for name, path, artifact_type, required in artifacts
        ],
        columns=MANIFEST_COLUMNS,
    )


def _summary(
    run_id: str,
    prereg: pd.DataFrame,
    checklist: pd.DataFrame,
    audit_ready: bool,
    timestamp: str,
) -> pd.DataFrame:
    """Create contract summary."""

    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "planned_challengers": len(prereg),
                "contract_controls": len(checklist),
                "blocking_controls": int(checklist["blocking_if_failed"].sum()),
                "sandbox_mode_defined": True,
                "official_mode_defined": True,
                "challengers_ready_for_official_execution": int(
                    prereg["ready_for_official_execution"].sum()
                ),
                "audit_ready": audit_ready,
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _write_initial_outputs(
    contract_text: str,
    prereg: pd.DataFrame,
    checklist: pd.DataFrame,
    timestamp: str,
) -> tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Write contract, preregistration, and checklist before summary/manifest."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    CONTRACT_OUTPUT.write_text(contract_text, encoding="utf-8")
    prereg.to_csv(PREREG_OUTPUT, index=False)
    checklist.to_csv(CHECKLIST_OUTPUT, index=False)
    logger.info("Created %s", CONTRACT_OUTPUT)
    logger.info("Created %s with %s rows", PREREG_OUTPUT, len(prereg))
    logger.info("Created %s with %s rows", CHECKLIST_OUTPUT, len(checklist))
    return contract_text, prereg, checklist, _manifest("", timestamp)


def build_no_tuning_leakage_contract() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build no-tuning-leakage contract artifacts."""

    logger.info("Stage 5.26 no-tuning-leakage contract build started")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")
    optional_configs = _inspect_inputs()

    contract_text = _contract_markdown(timestamp, optional_configs)
    prereg = _preregistration()
    checklist = _checklist()
    _write_initial_outputs(contract_text, prereg, checklist, timestamp)

    no_ready_challengers = int(prereg["ready_for_official_execution"].sum()) == 0
    summary = _summary(run_id, prereg, checklist, False, timestamp)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    manifest = _manifest(run_id, timestamp)
    required_exists = bool(manifest[manifest["required_for_audit_3"]]["exists"].all())
    audit_ready = required_exists and no_ready_challengers
    summary = _summary(run_id, prereg, checklist, audit_ready, timestamp)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    manifest = _manifest(run_id, timestamp)
    manifest.to_csv(MANIFEST_OUTPUT, index=False)

    logger.info("Created %s with %s rows", SUMMARY_OUTPUT, len(summary))
    logger.info("Created %s with %s rows", MANIFEST_OUTPUT, len(manifest))
    logger.info("Planned challengers: %s", len(prereg))
    logger.info("Contract controls: %s", len(checklist))
    logger.info("Blocking controls: %s", int(checklist["blocking_if_failed"].sum()))
    logger.info(
        "Challengers ready for official execution: %s",
        int(prereg["ready_for_official_execution"].sum()),
    )
    logger.info("Audit ready: %s", audit_ready)
    logger.info("No models, rankings, champions, or tournament outputs created.")
    logger.info("Stage 5.26 no-tuning-leakage contract build completed")
    return prereg, checklist, summary


if __name__ == "__main__":
    build_no_tuning_leakage_contract()
