"""Build the Stage 5.28 challenger onboarding layer.

This script formally registers and prepares the seven planned challenger models
for future execution. It is an onboarding-only block: it does not train models,
generate forecasts, calculate MASE/RMSSE, create rankings, build tournament
outputs, or select champions. Every challenger remains
``official_execution_ready = false`` because execution belongs to a later block.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("build_challenger_onboarding")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_onboarding"
LEAKAGE_CONTRACT_DIR = MODEL_LAB_DIR / "no_tuning_leakage_contract"
PREREGISTRATION_INPUT = LEAKAGE_CONTRACT_DIR / "challenger_preregistration_template.csv"
LEAKAGE_CHECKLIST_INPUT = LEAKAGE_CONTRACT_DIR / "leakage_control_checklist.csv"
CHALLENGER_REGISTRY_CONFIG = PROJECT_ROOT / "config" / "challenger_registry.yaml"

REGISTRY_SNAPSHOT_OUTPUT = OUTPUT_DIR / "challenger_registry_snapshot.csv"
DEPENDENCY_MATRIX_OUTPUT = OUTPUT_DIR / "challenger_dependency_matrix.csv"
READINESS_MATRIX_OUTPUT = OUTPUT_DIR / "challenger_readiness_matrix.csv"
LEAKAGE_MAPPING_OUTPUT = OUTPUT_DIR / "challenger_leakage_control_mapping.csv"
EXECUTION_MODE_POLICY_OUTPUT = OUTPUT_DIR / "challenger_execution_mode_policy.md"
ONBOARDING_SUMMARY_OUTPUT = OUTPUT_DIR / "challenger_onboarding_summary.csv"
ONBOARDING_REPORT_OUTPUT = OUTPUT_DIR / "challenger_onboarding_report.md"

RUN_ID_PREFIX = "challenger_onboarding"

# Onboarding-only constants. No challenger may become official-ready here.
OFFICIAL_EXECUTION_READY = False
IMPLEMENTATION_STATUS = "registered_placeholder"
HYPERPARAMETER_SPACE_STATUS = "declared_search_space_metadata_only"
TUNING_POLICY = "inner_validation_training_only_no_official_metric_feedback"
ALLOWED_EXECUTION_MODE = "sandbox_pending_official_lock"
CONTROL_STATUS = "mapped_pending_official_verification"

# Directories that, if populated with challenger artifacts, would indicate that
# execution / ranking / tournament / champion selection has already happened.
FORBIDDEN_CHALLENGER_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "challenger_execution",
    MODEL_LAB_DIR / "challenger_forecasts",
    MODEL_LAB_DIR / "challenger_metrics",
    MODEL_LAB_DIR / "rankings",
    MODEL_LAB_DIR / "champion",
]
TOURNAMENT_DIR = MODEL_LAB_DIR / "tournament"

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

# Planned challenger definitions (metadata only, no fitted or learned values).
CHALLENGERS = [
    {
        "challenger_id": "CH-01",
        "model_name": "AutoARIMA",
        "model_family": "statistical",
        "model_type": "auto_arima",
        "preferred_dependencies": ["statsforecast", "pmdarima"],
        "fallback_dependencies": ["pmdarima"],
        "feature_requirements": "univariate_target_series_training_only",
        "leakage_risk_level": "low",
        "expected_runtime_class": "medium",
    },
    {
        "challenger_id": "CH-02",
        "model_name": "Theta",
        "model_family": "statistical",
        "model_type": "theta",
        "preferred_dependencies": ["statsforecast", "darts"],
        "fallback_dependencies": ["darts"],
        "feature_requirements": "univariate_target_series_training_only",
        "leakage_risk_level": "low",
        "expected_runtime_class": "light",
    },
    {
        "challenger_id": "CH-03",
        "model_name": "ETS Explicit",
        "model_family": "statistical",
        "model_type": "ets_explicit",
        "preferred_dependencies": ["statsmodels", "statsforecast"],
        "fallback_dependencies": ["statsforecast"],
        "feature_requirements": "univariate_target_series_training_only",
        "leakage_risk_level": "low",
        "expected_runtime_class": "light",
    },
    {
        "challenger_id": "CH-04",
        "model_name": "LightGBM",
        "model_family": "machine_learning",
        "model_type": "gradient_boosting",
        "preferred_dependencies": ["lightgbm"],
        "fallback_dependencies": [],
        "feature_requirements": "engineered_lag_and_calendar_features_training_only",
        "leakage_risk_level": "medium",
        "expected_runtime_class": "medium",
    },
    {
        "challenger_id": "CH-05",
        "model_name": "XGBoost",
        "model_family": "machine_learning",
        "model_type": "gradient_boosting",
        "preferred_dependencies": ["xgboost"],
        "fallback_dependencies": [],
        "feature_requirements": "engineered_lag_and_calendar_features_training_only",
        "leakage_risk_level": "medium",
        "expected_runtime_class": "medium",
    },
    {
        "challenger_id": "CH-06",
        "model_name": "NBEATS",
        "model_family": "deep_learning",
        "model_type": "neural_basis_expansion",
        "preferred_dependencies": ["neuralforecast", "torch"],
        "fallback_dependencies": ["darts"],
        "feature_requirements": "windowed_sequence_inputs_training_only",
        "leakage_risk_level": "high",
        "expected_runtime_class": "heavy",
    },
    {
        "challenger_id": "CH-07",
        "model_name": "NHITS",
        "model_family": "deep_learning",
        "model_type": "neural_hierarchical_interpolation",
        "preferred_dependencies": ["neuralforecast", "torch"],
        "fallback_dependencies": [],
        "feature_requirements": "windowed_sequence_inputs_training_only",
        "leakage_risk_level": "high",
        "expected_runtime_class": "heavy",
    },
]

PLANNED_CHALLENGER_NAMES = [challenger["model_name"] for challenger in CHALLENGERS]


def _check_dependency_available(dependency_name: str) -> tuple[bool, str, str]:
    """Safely check whether a dependency can be imported without importing it."""

    try:
        spec = importlib.util.find_spec(dependency_name)
    except (ModuleNotFoundError, ValueError, ImportError) as exc:
        return False, "error", f"{type(exc).__name__}: {exc}"
    if spec is None:
        return False, "missing", "module not found in environment"
    return True, "available", "module spec located (not imported)"


def _load_preregistration_template() -> pd.DataFrame | None:
    """Load existing leakage-contract preregistration template if present."""

    if not PREREGISTRATION_INPUT.exists():
        logger.info("Preregistration template not found (informational): %s", PREREGISTRATION_INPUT)
        return None
    prereg = pd.read_csv(PREREGISTRATION_INPUT)
    logger.info("Loaded preregistration template with %s planned challengers.", len(prereg))
    return prereg


def _load_leakage_controls() -> pd.DataFrame:
    """Load the leakage-control checklist from the no-tuning-leakage contract."""

    if not LEAKAGE_CHECKLIST_INPUT.exists():
        raise FileNotFoundError(
            f"Required leakage-control checklist missing: {LEAKAGE_CHECKLIST_INPUT}"
        )
    checklist = pd.read_csv(LEAKAGE_CHECKLIST_INPUT)
    required = {
        "control_id",
        "control_area",
        "required_for_challenger_onboarding",
        "blocking_if_failed",
    }
    missing = required.difference(checklist.columns)
    if missing:
        raise ValueError(f"leakage_control_checklist.csv missing columns: {sorted(missing)}")
    return checklist


def _build_dependency_matrix(timestamp: str) -> tuple[pd.DataFrame, dict[str, bool]]:
    """Check dependency availability for every challenger."""

    rows = []
    dependency_missing_by_model: dict[str, bool] = {}
    for challenger in CHALLENGERS:
        model_name = challenger["model_name"]
        any_available = False
        seen: set[str] = set()
        ordered = [
            (dependency, "preferred") for dependency in challenger["preferred_dependencies"]
        ] + [
            (dependency, "fallback") for dependency in challenger["fallback_dependencies"]
        ]
        for dependency_name, role in ordered:
            if dependency_name in seen:
                continue
            seen.add(dependency_name)
            available, availability_status, notes = _check_dependency_available(dependency_name)
            any_available = any_available or available
            rows.append(
                {
                    "model_name": model_name,
                    "dependency_name": dependency_name,
                    "dependency_role": role,
                    "available": bool(available),
                    "availability_status": availability_status,
                    "notes": notes,
                    "created_timestamp": timestamp,
                }
            )
        dependency_missing_by_model[model_name] = not any_available
    matrix = pd.DataFrame(rows, columns=DEPENDENCY_MATRIX_COLUMNS)
    return matrix, dependency_missing_by_model


def _build_leakage_mapping(checklist: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    """Map every leakage control to every challenger."""

    rows = []
    for challenger in CHALLENGERS:
        model_name = challenger["model_name"]
        for _, control in checklist.iterrows():
            rows.append(
                {
                    "model_name": model_name,
                    "control_id": control["control_id"],
                    "control_area": control["control_area"],
                    "control_required": bool(
                        str(control["required_for_challenger_onboarding"]).lower()
                        in {"true", "1"}
                    ),
                    "control_status": CONTROL_STATUS,
                    "blocking_if_failed": bool(
                        str(control["blocking_if_failed"]).lower() in {"true", "1"}
                    ),
                    "created_timestamp": timestamp,
                }
            )
    return pd.DataFrame(rows, columns=LEAKAGE_MAPPING_COLUMNS)


def _build_registry_snapshot(
    dependency_missing_by_model: dict[str, bool], timestamp: str
) -> pd.DataFrame:
    """Build the challenger registry snapshot (metadata only)."""

    rows = []
    for challenger in CHALLENGERS:
        model_name = challenger["model_name"]
        dependency_missing = dependency_missing_by_model[model_name]
        # Sandbox readiness requires at least one backend dependency to be present.
        # Official execution readiness is always false in this onboarding block.
        sandbox_ready = not dependency_missing
        rows.append(
            {
                "challenger_id": challenger["challenger_id"],
                "model_name": model_name,
                "model_family": challenger["model_family"],
                "model_type": challenger["model_type"],
                "implementation_status": IMPLEMENTATION_STATUS,
                "preferred_dependencies": ";".join(challenger["preferred_dependencies"]),
                "fallback_dependencies": ";".join(challenger["fallback_dependencies"]),
                "feature_requirements": challenger["feature_requirements"],
                "hyperparameter_space_status": HYPERPARAMETER_SPACE_STATUS,
                "tuning_policy": TUNING_POLICY,
                "allowed_execution_mode": ALLOWED_EXECUTION_MODE,
                "leakage_risk_level": challenger["leakage_risk_level"],
                "expected_runtime_class": challenger["expected_runtime_class"],
                "sandbox_ready": bool(sandbox_ready),
                "official_execution_ready": OFFICIAL_EXECUTION_READY,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=REGISTRY_SNAPSHOT_COLUMNS)


def _build_readiness_matrix(
    registry: pd.DataFrame, dependency_missing_by_model: dict[str, bool], timestamp: str
) -> pd.DataFrame:
    """Build the challenger readiness matrix."""

    rows = []
    for challenger in CHALLENGERS:
        model_name = challenger["model_name"]
        dependency_missing = dependency_missing_by_model[model_name]
        sandbox_ready = bool(
            registry.loc[registry["model_name"] == model_name, "sandbox_ready"].iloc[0]
        )
        # Onboarding-level blocking reasons only. A missing dependency blocks
        # sandbox execution but does not block onboarding completion.
        reasons = []
        if dependency_missing:
            reasons.append("dependency_missing_for_sandbox")
        blocking_reasons = ";".join(reasons) if reasons else "none"
        rows.append(
            {
                "model_name": model_name,
                "registered": True,
                "dependencies_checked": True,
                "leakage_controls_mapped": True,
                "tuning_policy_declared": True,
                "hyperparameter_space_declared": True,
                "sandbox_ready": sandbox_ready,
                "official_execution_ready": OFFICIAL_EXECUTION_READY,
                "blocking_reasons": blocking_reasons,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=READINESS_MATRIX_COLUMNS)


def _no_forbidden_outputs_exist() -> bool:
    """Confirm no execution/ranking/champion outputs exist and tournament is empty."""

    for path in FORBIDDEN_CHALLENGER_OUTPUT_DIRS:
        if path.exists() and any(path.iterdir()):
            logger.info("Forbidden challenger output directory is non-empty: %s", path)
            return False
    if TOURNAMENT_DIR.exists() and any(TOURNAMENT_DIR.iterdir()):
        logger.info("Tournament directory is non-empty: %s", TOURNAMENT_DIR)
        return False
    return True


def _build_summary(
    registry: pd.DataFrame,
    readiness: pd.DataFrame,
    dependency_matrix: pd.DataFrame,
    leakage_mapping: pd.DataFrame,
    dependency_missing_by_model: dict[str, bool],
    run_id: str,
    timestamp: str,
) -> pd.DataFrame:
    """Build the single-row challenger onboarding summary."""

    registered = len(registry)
    statistical = int((registry["model_family"] == "statistical").sum())
    ml = int((registry["model_family"] == "machine_learning").sum())
    deep_learning = int((registry["model_family"] == "deep_learning").sum())
    sandbox_ready_count = int(registry["sandbox_ready"].sum())
    official_ready_count = int(registry["official_execution_ready"].sum())
    dependency_missing_count = int(sum(dependency_missing_by_model.values()))
    # Onboarding-level blockers only: a model is blocked if it is not registered or
    # lacks mapped leakage controls, a declared tuning policy, or a declared
    # hyperparameter space. Missing dependencies are a sandbox-only note and do not
    # block onboarding completion.
    onboarding_gates = (
        readiness["registered"].astype(bool)
        & readiness["leakage_controls_mapped"].astype(bool)
        & readiness["tuning_policy_declared"].astype(bool)
        & readiness["hyperparameter_space_declared"].astype(bool)
    )
    blocking_models_count = int((~onboarding_gates).sum())

    every_challenger_has_control = (
        leakage_mapping.groupby("model_name")["control_id"].nunique().min() >= 1
    )
    ready_for_execution_block = bool(
        registered == len(CHALLENGERS)
        and set(registry["model_name"]) == set(PLANNED_CHALLENGER_NAMES)
        and bool(readiness["leakage_controls_mapped"].all())
        and bool(every_challenger_has_control)
        and bool(readiness["dependencies_checked"].all())
        and not dependency_matrix.empty
        and official_ready_count == 0
        and _no_forbidden_outputs_exist()
    )
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "planned_challengers": len(CHALLENGERS),
                "registered_challengers": registered,
                "statistical_challengers": statistical,
                "ml_challengers": ml,
                "deep_learning_challengers": deep_learning,
                "sandbox_ready_count": sandbox_ready_count,
                "official_execution_ready_count": official_ready_count,
                "dependency_missing_count": dependency_missing_count,
                "blocking_models_count": blocking_models_count,
                "ready_for_challenger_execution_block": ready_for_execution_block,
                "created_timestamp": timestamp,
            }
        ],
        columns=ONBOARDING_SUMMARY_COLUMNS,
    )


def _write_execution_mode_policy(timestamp: str) -> None:
    """Write the sandbox vs official execution-mode policy document."""

    content = f"""# Challenger Execution Mode Policy - Stage 5.28

Created timestamp: {timestamp}

## Purpose

This policy governs how the seven onboarded challengers may be executed in
future blocks. Block 5.28 is onboarding only. No challenger is trained, no
forecast is generated, no metric is calculated, and no challenger is promoted to
official execution in this block.

## Sandbox Mode Definition

`sandbox_mode` is an exploratory mode used to verify code stability, data
plumbing, and dependency wiring for a challenger. Sandbox runs:

- are not eligible for champion decisions;
- cannot be promoted to official tournament evidence;
- cannot be used as official benchmark evidence;
- require at least one usable backend dependency to be present.

## Official Mode Definition

`official_mode` is the formal comparison mode. It requires locked configuration,
locked backtesting windows, locked features, locked random seeds, no post-hoc
tuning, and full metadata capture for audit. Official mode is used only for
formal benchmark comparison against the baseline cohort.

## Why Official Execution Remains False

Every onboarded challenger has `official_execution_ready = false` in this block
because official execution belongs to a later block (5.29 and beyond).
Onboarding only registers the challengers, checks dependency availability, maps
leakage controls, and declares tuning and hyperparameter-space policy. No model
has been run, locked, or audited for official comparison.

## No-Tuning-Leakage Requirement

All challenger tuning must obey the Stage 5.26 No-Tuning-Leakage Contract.
Tuning may occur only through an inner-validation process using training-only
data. Official MASE, official RMSSE, statistical significance outputs, tournament
rank, and champion-selection feedback must never be used for tuning.

## Model Preregistration Requirement

Before official execution, each challenger must complete preregistration:
`model_name`, `model_family`, `allowed_features`, `hyperparameter_space`,
`tuning_budget`, `training_window_policy`, `random_seed_policy`,
`dependency_requirements`, `expected_runtime_class`, and `leakage_risk_level`.

## Dependency Requirement

A challenger may not enter sandbox or official execution unless its required
dependencies are available and recorded. Dependency availability is checked in
this block via safe import-spec inspection only; no packages are installed.

## Reproducibility Requirement

Every official challenger run must record `run_id`, git status, config snapshot,
input data hashes if available, random seeds, dependency versions if available,
a model registry snapshot, and the execution timestamp.

## Denominator Note

MASE and RMSSE use the official training-only lag-1 naive denominators:

- MASE denominator: training-only lag-1 naive MAE,
  `mean(abs(y_train[t] - y_train[t-1]))`.
- RMSSE denominator: training-only lag-1 naive MSE,
  `mean((y_train[t] - y_train[t-1])^2)`.

The denominator is computed per entity and window using only actuals with date
`<= train_end_date`. It is never computed on the test horizon.

## Interpretation Note

The corrected MASE scale may be high because the denominator is an
in-sample one-step lag-1 naive error rather than an out-of-sample flat naive.
A 30-day horizon model error divided by a small in-sample one-step error can
yield MASE values well above 1. This is expected and methodologically standard;
it is not a defect. The same logic applies to the RMSSE guardrail scale.

## Scope Boundary

This block creates no champion, no tournament output, and no ranking. Challenger
execution, metric calculation, ranking, and champion selection are explicitly
deferred to later blocks.
"""
    EXECUTION_MODE_POLICY_OUTPUT.write_text(content, encoding="utf-8")


def _write_onboarding_report(
    registry: pd.DataFrame,
    readiness: pd.DataFrame,
    dependency_matrix: pd.DataFrame,
    leakage_mapping: pd.DataFrame,
    summary: pd.DataFrame,
    timestamp: str,
) -> None:
    """Write the challenger onboarding report."""

    row = summary.iloc[0]
    ready_flag = bool(row["ready_for_challenger_execution_block"])
    recommendation = (
        "PROCEED_TO_5.29_CHALLENGER_EXECUTION_PLANNING"
        if ready_flag and int(row["official_execution_ready_count"]) == 0
        else "BLOCK_5.29_PENDING_FIX"
    )

    registry_lines = "\n".join(
        f"| {r['challenger_id']} | {r['model_name']} | {r['model_family']} | "
        f"{r['model_type']} | {r['leakage_risk_level']} | {r['expected_runtime_class']} | "
        f"{r['sandbox_ready']} | {r['official_execution_ready']} |"
        for _, r in registry.iterrows()
    )
    available_deps = dependency_matrix[dependency_matrix["available"]]["dependency_name"].nunique()
    total_deps = dependency_matrix["dependency_name"].nunique()
    missing_models = sorted(
        readiness.loc[
            readiness["blocking_reasons"].str.contains("dependency_missing"), "model_name"
        ]
    )

    content = f"""# Challenger Onboarding Report - Stage 5.28

Created timestamp: {timestamp}
Run id: {row['run_id']}

## Purpose of the Block

Block 5.28 formally registers and prepares the seven planned challenger models
for future execution. It is onboarding only: no challenger is trained, no
forecast is generated, no MASE/RMSSE is calculated, no ranking is built, no
tournament output is produced, and no champion is selected. Every challenger
remains `official_execution_ready = false` because execution belongs to a later
block.

## Models Onboarded

| challenger_id | model_name | model_family | model_type | leakage_risk_level | runtime_class | sandbox_ready | official_ready |
| --- | --- | --- | --- | --- | --- | --- | --- |
{registry_lines}

- Statistical challengers: {int(row['statistical_challengers'])} (AutoARIMA, Theta, ETS Explicit)
- Machine learning challengers: {int(row['ml_challengers'])} (LightGBM, XGBoost)
- Deep learning challengers: {int(row['deep_learning_challengers'])} (NBEATS, NHITS)

## Dependency Findings

- Distinct dependencies inspected: {total_deps}
- Distinct dependencies available in current environment: {available_deps}
- Challengers with no available backend dependency: {int(row['dependency_missing_count'])}
- Models missing a sandbox dependency: {", ".join(missing_models) if missing_models else "none"}

Dependency availability was checked using safe import-spec inspection only. No
packages were installed. Missing dependencies are recorded as informational and
do not block onboarding; they keep `sandbox_ready = false` for the affected
challenger and have no effect on `official_execution_ready`, which is false for
all challengers in this block.

## Readiness Findings

- Planned challengers: {int(row['planned_challengers'])}
- Registered challengers: {int(row['registered_challengers'])}
- Sandbox-ready challengers: {int(row['sandbox_ready_count'])}
- Official-execution-ready challengers: {int(row['official_execution_ready_count'])} (must be 0)
- Onboarding-blocking models: {int(row['blocking_models_count'])}

Every challenger is registered, has dependencies checked, has leakage controls
mapped, has its tuning policy declared, and has its hyperparameter-space status
declared (metadata only).

## Leakage-Control Mapping

All leakage controls from the Stage 5.26 No-Tuning-Leakage Contract are mapped to
every challenger. Total control mappings: {len(leakage_mapping)} rows across
{leakage_mapping['model_name'].nunique()} challengers and
{leakage_mapping['control_id'].nunique()} distinct controls. Each control is
recorded with status `{CONTROL_STATUS}` because verification occurs at execution
time, not during onboarding.

## Sandbox vs Official Execution Policy

See `challenger_execution_mode_policy.md`. Sandbox mode is exploratory and cannot
be promoted to official evidence. Official mode requires locked configuration,
windows, features, and seeds, no post-hoc tuning, and full audit metadata.

## Why Official Execution Remains False

Official execution requires completed preregistration, verified leakage controls,
recorded dependencies, locked reproducibility metadata, and audit review. None of
these execution-time gates are performed in an onboarding block, so all
challengers remain `official_execution_ready = false`.

## What Remains for 5.29

- Lock per-challenger hyperparameter spaces and tuning budgets.
- Resolve or record any missing dependencies required for execution.
- Define the challenger execution plan (sandbox first, then official).
- Verify leakage controls at execution time against locked windows.
- Capture full reproducibility metadata for official runs.

## Recommendation

{recommendation}
"""
    ONBOARDING_REPORT_OUTPUT.write_text(content, encoding="utf-8")


def _write_challenger_registry_config(registry: pd.DataFrame, timestamp: str) -> None:
    """Write the optional metadata-only challenger registry config (YAML)."""

    lines = [
        "# Challenger registry (Stage 5.28 onboarding metadata only).",
        "# No fitted parameters, learned values, or post-hoc tuning results.",
        "# No challenger is official-execution-ready in this block.",
        "challenger_registry:",
        "  policy_stage: Stage 5.28",
        "  policy_scope: challenger_onboarding_metadata_only",
        f"  created_timestamp: {timestamp}",
        "  official_execution_ready_any: false",
        "  challengers:",
    ]
    for _, r in registry.iterrows():
        preferred = ", ".join(
            f'"{dep}"' for dep in str(r["preferred_dependencies"]).split(";") if dep
        )
        fallback = ", ".join(
            f'"{dep}"' for dep in str(r["fallback_dependencies"]).split(";") if dep
        )
        lines.extend(
            [
                f"    - challenger_id: {r['challenger_id']}",
                f"      model_name: \"{r['model_name']}\"",
                f"      model_family: {r['model_family']}",
                f"      model_type: {r['model_type']}",
                f"      implementation_status: {r['implementation_status']}",
                f"      preferred_dependencies: [{preferred}]",
                f"      fallback_dependencies: [{fallback}]",
                f"      feature_requirements: {r['feature_requirements']}",
                f"      hyperparameter_space_status: {r['hyperparameter_space_status']}",
                f"      tuning_policy: {r['tuning_policy']}",
                f"      allowed_execution_mode: {r['allowed_execution_mode']}",
                f"      leakage_risk_level: {r['leakage_risk_level']}",
                f"      expected_runtime_class: {r['expected_runtime_class']}",
                "      status: registered_planned",
                "      official_execution_ready: false",
            ]
        )
    CHALLENGER_REGISTRY_CONFIG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_outputs(
    registry: pd.DataFrame,
    dependency_matrix: pd.DataFrame,
    readiness: pd.DataFrame,
    leakage_mapping: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Write all challenger onboarding CSV outputs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    registry.to_csv(REGISTRY_SNAPSHOT_OUTPUT, index=False)
    dependency_matrix.to_csv(DEPENDENCY_MATRIX_OUTPUT, index=False)
    readiness.to_csv(READINESS_MATRIX_OUTPUT, index=False)
    leakage_mapping.to_csv(LEAKAGE_MAPPING_OUTPUT, index=False)
    summary.to_csv(ONBOARDING_SUMMARY_OUTPUT, index=False)


def build_challenger_onboarding() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    """Create the Stage 5.28 challenger onboarding layer."""

    logger.info("Stage 5.28 challenger onboarding started (onboarding only)")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    prereg = _load_preregistration_template()
    if prereg is not None and set(prereg["model_name"]) != set(PLANNED_CHALLENGER_NAMES):
        logger.info(
            "Preregistration template challenger set differs from planned set; "
            "using the Stage 5.28 planned challenger definitions."
        )
    checklist = _load_leakage_controls()

    dependency_matrix, dependency_missing_by_model = _build_dependency_matrix(timestamp)
    leakage_mapping = _build_leakage_mapping(checklist, timestamp)
    registry = _build_registry_snapshot(dependency_missing_by_model, timestamp)
    readiness = _build_readiness_matrix(registry, dependency_missing_by_model, timestamp)
    summary = _build_summary(
        registry,
        readiness,
        dependency_matrix,
        leakage_mapping,
        dependency_missing_by_model,
        run_id,
        timestamp,
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    _write_outputs(registry, dependency_matrix, readiness, leakage_mapping, summary)
    _write_execution_mode_policy(timestamp)
    _write_onboarding_report(
        registry, readiness, dependency_matrix, leakage_mapping, summary, timestamp
    )
    _write_challenger_registry_config(registry, timestamp)

    row = summary.iloc[0]
    logger.info("Registered challengers: %s", int(row["registered_challengers"]))
    logger.info("Sandbox-ready challengers: %s", int(row["sandbox_ready_count"]))
    logger.info(
        "Official-execution-ready challengers: %s",
        int(row["official_execution_ready_count"]),
    )
    logger.info("Dependency-missing challengers: %s", int(row["dependency_missing_count"]))
    logger.info(
        "Ready for challenger execution block: %s",
        bool(row["ready_for_challenger_execution_block"]),
    )
    logger.info("Stage 5.28 challenger onboarding completed")
    return registry, dependency_matrix, readiness, leakage_mapping, summary


if __name__ == "__main__":
    build_challenger_onboarding()
