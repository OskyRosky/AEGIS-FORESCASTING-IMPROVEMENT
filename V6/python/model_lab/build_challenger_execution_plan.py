"""Build the Stage 5.29A challenger execution plan.

This script creates the official execution plan for the seven onboarded
challenger models. It is planning only: it does not train models, generate
forecasts, calculate MASE/RMSSE, create rankings, build tournament outputs, or
select champions. Official execution remains blocked for every challenger.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("build_challenger_execution_plan")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
ONBOARDING_DIR = MODEL_LAB_DIR / "challenger_onboarding"
REGISTRY_INPUT = ONBOARDING_DIR / "challenger_registry_snapshot.csv"
DEPENDENCY_INPUT = ONBOARDING_DIR / "challenger_dependency_matrix.csv"
READINESS_INPUT = ONBOARDING_DIR / "challenger_readiness_matrix.csv"
LEAKAGE_MAPPING_INPUT = ONBOARDING_DIR / "challenger_leakage_control_mapping.csv"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"

OUTPUT_DIR = MODEL_LAB_DIR / "challenger_execution_planning"
EXECUTION_PLAN_OUTPUT = OUTPUT_DIR / "challenger_execution_plan.csv"
DEPENDENCY_RESOLUTION_OUTPUT = OUTPUT_DIR / "challenger_dependency_resolution_plan.csv"
TUNING_BUDGET_OUTPUT = OUTPUT_DIR / "challenger_tuning_budget_plan.csv"
SANDBOX_PLAN_OUTPUT = OUTPUT_DIR / "challenger_sandbox_plan.csv"
OFFICIAL_GATE_OUTPUT = OUTPUT_DIR / "challenger_official_execution_gate.csv"
FORECAST_CONTRACT_OUTPUT = OUTPUT_DIR / "challenger_forecast_output_contract.csv"
PLANNING_SUMMARY_OUTPUT = OUTPUT_DIR / "challenger_execution_planning_summary.csv"
PLANNING_REPORT_OUTPUT = OUTPUT_DIR / "challenger_execution_planning_report.md"

RUN_ID_PREFIX = "challenger_execution_planning"

# Planning-only constants. No challenger may be official-execution-allowed here.
OFFICIAL_EXECUTION_ALLOWED = False
EXECUTION_PHASE = "planned"
RECOMMENDED_FIRST_MODE = "sandbox"

# Execution order follows planning principle: statistical -> ML -> deep learning.
EXECUTION_ORDER = [
    {"model_name": "AutoARIMA", "execution_phase_group": "statistical", "priority_level": "high"},
    {"model_name": "Theta", "execution_phase_group": "statistical", "priority_level": "high"},
    {"model_name": "ETS Explicit", "execution_phase_group": "statistical", "priority_level": "high"},
    {"model_name": "LightGBM", "execution_phase_group": "machine_learning", "priority_level": "medium"},
    {"model_name": "XGBoost", "execution_phase_group": "machine_learning", "priority_level": "medium"},
    {"model_name": "NBEATS", "execution_phase_group": "deep_learning", "priority_level": "low"},
    {"model_name": "NHITS", "execution_phase_group": "deep_learning", "priority_level": "low"},
]

# Conservative, pre-registered tuning budgets per the planning brief.
TUNING_BUDGETS = {
    "AutoARIMA": {
        "tuning_allowed": True,
        "tuning_mode": "library_auto_search_bounded",
        "max_trials": "limited_by_library_auto_search",
        "max_runtime_minutes": 20,
        "notes": "AutoARIMA internal stepwise search; bounded by library auto-search.",
    },
    "Theta": {
        "tuning_allowed": False,
        "tuning_mode": "fixed_default",
        "max_trials": 1,
        "max_runtime_minutes": 10,
        "notes": "Minimal/no tuning; use library default theta configuration.",
    },
    "ETS Explicit": {
        "tuning_allowed": True,
        "tuning_mode": "bounded_grid",
        "max_trials": 10,
        "max_runtime_minutes": 20,
        "notes": "Bounded ETS component selection via inner validation only.",
    },
    "LightGBM": {
        "tuning_allowed": True,
        "tuning_mode": "bounded_random_search",
        "max_trials": 20,
        "max_runtime_minutes": 45,
        "notes": "Bounded random search over training-only inner validation folds.",
    },
    "XGBoost": {
        "tuning_allowed": True,
        "tuning_mode": "bounded_random_search",
        "max_trials": 20,
        "max_runtime_minutes": 45,
        "notes": "Bounded random search over training-only inner validation folds.",
    },
    "NBEATS": {
        "tuning_allowed": True,
        "tuning_mode": "bounded_config_search",
        "max_trials": 5,
        "max_runtime_minutes": 90,
        "notes": "Very limited config search; heavy runtime, fixed deterministic seed.",
    },
    "NHITS": {
        "tuning_allowed": True,
        "tuning_mode": "bounded_config_search",
        "max_trials": 5,
        "max_runtime_minutes": 90,
        "notes": "Very limited config search; heavy runtime, fixed deterministic seed.",
    },
}

# Recommended dependency resolution guidance (planning only, no installs).
RESOLUTION_GUIDANCE = {
    "statsforecast": "Plan to install statsforecast in a controlled environment before sandbox.",
    "pmdarima": "Optional AutoARIMA fallback; plan install only if statsforecast unavailable.",
    "darts": "Optional fallback for Theta/NBEATS; plan install only if primary backend unavailable.",
    "statsmodels": "Plan to install statsmodels for explicit ETS state-space estimation.",
    "lightgbm": "Plan to install lightgbm before ML sandbox.",
    "xgboost": "Plan to install xgboost before ML sandbox.",
    "neuralforecast": "Plan to install neuralforecast (with torch) before deep-learning sandbox.",
    "torch": "Plan to install a CPU/GPU-appropriate torch build before deep-learning sandbox.",
}

# Official execution gates (all required before any official challenger run).
OFFICIAL_GATES = [
    ("GATE-01", "dependencies_resolved", "All required dependencies for the model are installed and recorded."),
    ("GATE-02", "sandbox_passed", "Model passed sandbox execution on the controlled subset."),
    ("GATE-03", "no_leakage_controls_failed", "All mapped leakage controls verified and none failed."),
    ("GATE-04", "tuning_budget_locked", "Tuning mode, max trials, and runtime budget are locked."),
    ("GATE-05", "hyperparameter_space_locked", "Hyperparameter search space is locked and pre-registered."),
    ("GATE-06", "random_seed_locked", "Random seed or deterministic policy is locked and recorded."),
    ("GATE-07", "output_schema_validated", "Forecast output schema matches the challenger forecast output contract."),
    ("GATE-08", "official_windows_locked", "Official backtesting windows are locked for the official run."),
    ("GATE-09", "no_post_hoc_tuning", "No tuning occurs after official evaluation on benchmark windows."),
    ("GATE-10", "no_tournament_feedback_tuning", "No tuning from tournament rank, champion, significance, MASE, or RMSSE outcomes."),
]

# Future challenger forecast output contract (compatible with Model Lab schema).
FORECAST_CONTRACT = [
    ("run_id", True, "Unique identifier for the challenger execution run."),
    ("model_name", True, "Challenger model name exactly as registered."),
    ("entity_key", True, "Entity identifier for the forecasted series."),
    ("window_id", True, "Backtesting window identifier."),
    ("forecast_date", True, "Calendar date of the forecasted point."),
    ("horizon_day", True, "Forecast horizon day index within the window (1..30)."),
    ("forecast_value", True, "Point forecast value (pre non-negative policy)."),
    ("execution_mode", True, "Execution mode: sandbox or official."),
    ("created_timestamp", True, "ISO timestamp when the forecast row was produced."),
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

# Sandbox scope recommendation: latest 1 window, 3-5 representative entities.
SANDBOX_WINDOW_SCOPE = "latest_1_window"
SANDBOX_ENTITY_COUNT = 5


def _require_file(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required execution-planning input missing: {path}")


def _load_registry() -> pd.DataFrame:
    """Load the challenger registry snapshot from onboarding."""

    _require_file(REGISTRY_INPUT)
    registry = pd.read_csv(REGISTRY_INPUT)
    required = {"model_name", "model_family", "model_type", "expected_runtime_class"}
    missing = required.difference(registry.columns)
    if missing:
        raise ValueError(f"challenger_registry_snapshot.csv missing columns: {sorted(missing)}")
    return registry


def _load_dependency_matrix() -> pd.DataFrame:
    """Load the onboarding dependency matrix."""

    _require_file(DEPENDENCY_INPUT)
    matrix = pd.read_csv(DEPENDENCY_INPUT)
    required = {"model_name", "dependency_name", "dependency_role", "available", "availability_status"}
    missing = required.difference(matrix.columns)
    if missing:
        raise ValueError(f"challenger_dependency_matrix.csv missing columns: {sorted(missing)}")
    return matrix


def _sandbox_entities(window_scope_available: bool) -> str:
    """Build a representative entity scope label for sandbox planning."""

    if not window_scope_available:
        return "representative_subset_pending_window_inventory"
    return f"{SANDBOX_ENTITY_COUNT}_representative_entities"


def _build_dependency_resolution(matrix: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    """Plan dependency resolution per model (no installs performed)."""

    fallback_by_model = (
        matrix[matrix["dependency_role"] == "fallback"]
        .groupby("model_name")["available"]
        .apply(lambda s: bool(s.astype(str).str.lower().isin(["true", "1"]).any()))
        .to_dict()
    )
    rows = []
    for _, dep in matrix.iterrows():
        model_name = dep["model_name"]
        available = str(dep["available"]).lower() in {"true", "1"}
        availability_status = dep["availability_status"]
        resolution_required = not available
        fallback_available = bool(fallback_by_model.get(model_name, False))
        recommended = (
            "no_action_dependency_available"
            if available
            else RESOLUTION_GUIDANCE.get(
                dep["dependency_name"], "Plan controlled install before sandbox."
            )
        )
        # A dependency blocks sandbox only if it is required and unavailable and no
        # fallback exists for the model. Official execution is blocked by any
        # unresolved required dependency until resolved.
        blocks_sandbox = bool(resolution_required and not fallback_available)
        blocks_official = bool(resolution_required)
        rows.append(
            {
                "model_name": model_name,
                "required_dependency": dep["dependency_name"],
                "dependency_role": dep["dependency_role"],
                "current_availability_status": availability_status,
                "resolution_required": bool(resolution_required),
                "recommended_resolution": recommended,
                "fallback_available": fallback_available,
                "blocks_sandbox": blocks_sandbox,
                "blocks_official": blocks_official,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=DEPENDENCY_RESOLUTION_COLUMNS)


def _model_blocked_by_dependencies(resolution: pd.DataFrame) -> dict[str, bool]:
    """Return whether each model is blocked from sandbox by dependencies."""

    blocked: dict[str, bool] = {}
    for model_name, group in resolution.groupby("model_name"):
        any_available = (
            group["current_availability_status"].astype(str).str.lower() == "available"
        ).any()
        blocked[model_name] = not bool(any_available)
    return blocked


def _build_execution_plan(
    registry: pd.DataFrame, blocked_by_deps: dict[str, bool], timestamp: str
) -> pd.DataFrame:
    """Build the ordered challenger execution plan."""

    registry_by_name = registry.set_index("model_name")
    rows = []
    for order, entry in enumerate(EXECUTION_ORDER, start=1):
        model_name = entry["model_name"]
        meta = registry_by_name.loc[model_name]
        dependency_status = (
            "blocked_dependency_missing" if blocked_by_deps.get(model_name, True) else "available"
        )
        sandbox_entry_gate = (
            "dependencies_resolved_and_schema_validated"
            if blocked_by_deps.get(model_name, True)
            else "schema_validated"
        )
        rows.append(
            {
                "execution_order": order,
                "model_name": model_name,
                "model_family": meta["model_family"],
                "model_type": meta["model_type"],
                "execution_phase": EXECUTION_PHASE,
                "recommended_first_mode": RECOMMENDED_FIRST_MODE,
                "official_execution_allowed": OFFICIAL_EXECUTION_ALLOWED,
                "dependency_status": dependency_status,
                "sandbox_entry_gate": sandbox_entry_gate,
                "official_entry_gate": "all_official_gates_passed",
                "expected_runtime_class": meta["expected_runtime_class"],
                "priority_level": entry["priority_level"],
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=EXECUTION_PLAN_COLUMNS)


def _build_tuning_budget(registry: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    """Build the conservative, pre-registered tuning budget plan."""

    rows = []
    for entry in EXECUTION_ORDER:
        model_name = entry["model_name"]
        budget = TUNING_BUDGETS[model_name]
        rows.append(
            {
                "model_name": model_name,
                "tuning_allowed": bool(budget["tuning_allowed"]),
                "tuning_mode": budget["tuning_mode"],
                "max_trials": budget["max_trials"],
                "max_runtime_minutes": budget["max_runtime_minutes"],
                "random_seed_required": True,
                "inner_validation_required": True,
                "official_results_may_tune_model": False,
                "notes": budget["notes"],
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=TUNING_BUDGET_COLUMNS)


def _build_sandbox_plan(
    blocked_by_deps: dict[str, bool], window_scope_available: bool, timestamp: str
) -> pd.DataFrame:
    """Build the controlled sandbox execution plan."""

    entities_label = _sandbox_entities(window_scope_available)
    rows = []
    for entry in EXECUTION_ORDER:
        model_name = entry["model_name"]
        blocked = blocked_by_deps.get(model_name, True)
        promote = (
            "false_dependency_unresolved"
            if blocked
            else "eligible_after_sandbox_pass_and_gate_review"
        )
        rows.append(
            {
                "model_name": model_name,
                "sandbox_scope": "controlled_subset_not_full_454_windows",
                "sandbox_entities": entities_label,
                "sandbox_windows": SANDBOX_WINDOW_SCOPE,
                "sandbox_success_criteria": (
                    "model fits and produces 30-day forecasts for all sandbox "
                    "entities without error and output matches forecast contract schema"
                ),
                "sandbox_failure_criteria": (
                    "fit/predict error, schema mismatch, NaN/inf forecasts, or runtime "
                    "exceeds sandbox runtime budget"
                ),
                "promote_to_official_if_passed": promote,
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=SANDBOX_PLAN_COLUMNS)


def _build_official_gates(timestamp: str) -> pd.DataFrame:
    """Build the official execution gate table."""

    rows = [
        {
            "gate_id": gate_id,
            "gate_name": gate_name,
            "gate_description": description,
            "required_before_official_execution": True,
            "blocking_if_failed": True,
            "created_timestamp": timestamp,
        }
        for gate_id, gate_name, description in OFFICIAL_GATES
    ]
    return pd.DataFrame(rows, columns=OFFICIAL_GATE_COLUMNS)


def _build_forecast_contract() -> pd.DataFrame:
    """Build the future challenger forecast output contract."""

    rows = [
        {"column_name": name, "required": bool(required), "description": description}
        for name, required, description in FORECAST_CONTRACT
    ]
    return pd.DataFrame(rows, columns=FORECAST_CONTRACT_COLUMNS)


def _build_summary(
    registry: pd.DataFrame,
    blocked_by_deps: dict[str, bool],
    run_id: str,
    timestamp: str,
) -> pd.DataFrame:
    """Build the single-row execution planning summary."""

    statistical = int((registry["model_family"] == "statistical").sum())
    ml = int((registry["model_family"] == "machine_learning").sum())
    deep_learning = int((registry["model_family"] == "deep_learning").sum())
    blocked_count = int(sum(1 for blocked in blocked_by_deps.values() if blocked))
    ready_for_sandbox = int(sum(1 for blocked in blocked_by_deps.values() if not blocked))
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "planned_challengers": len(EXECUTION_ORDER),
                "statistical_challengers": statistical,
                "ml_challengers": ml,
                "deep_learning_challengers": deep_learning,
                "models_ready_for_sandbox": ready_for_sandbox,
                "models_blocked_by_dependencies": blocked_count,
                "models_ready_for_official_execution": 0,
                "official_execution_allowed": OFFICIAL_EXECUTION_ALLOWED,
                "created_timestamp": timestamp,
            }
        ],
        columns=PLANNING_SUMMARY_COLUMNS,
    )


def _write_report(
    execution_plan: pd.DataFrame,
    dependency_resolution: pd.DataFrame,
    tuning_budget: pd.DataFrame,
    sandbox_plan: pd.DataFrame,
    official_gates: pd.DataFrame,
    summary: pd.DataFrame,
    timestamp: str,
) -> None:
    """Write the execution planning report."""

    row = summary.iloc[0]
    ready_for_sandbox = int(row["models_ready_for_sandbox"])
    blocked = int(row["models_blocked_by_dependencies"])
    recommendation = (
        "PROCEED_TO_5.29B_CHALLENGER_SANDBOX_EXECUTION"
        if int(row["models_ready_for_official_execution"]) == 0
        and not bool(row["official_execution_allowed"])
        else "BLOCK_5.29B_PENDING_FIX"
    )
    order_lines = "\n".join(
        f"| {r['execution_order']} | {r['model_name']} | {r['model_family']} | "
        f"{r['priority_level']} | {r['expected_runtime_class']} | {r['dependency_status']} |"
        for _, r in execution_plan.iterrows()
    )
    missing_deps = sorted(
        dependency_resolution.loc[
            dependency_resolution["resolution_required"], "required_dependency"
        ].unique()
    )
    gate_lines = "\n".join(
        f"- {r['gate_id']} {r['gate_name']}: {r['gate_description']}"
        for _, r in official_gates.iterrows()
    )
    budget_lines = "\n".join(
        f"| {r['model_name']} | {r['tuning_allowed']} | {r['tuning_mode']} | "
        f"{r['max_trials']} | {r['max_runtime_minutes']} |"
        for _, r in tuning_budget.iterrows()
    )

    content = f"""# Challenger Execution Planning Report - Stage 5.29A

Created timestamp: {timestamp}
Run id: {row['run_id']}

## Purpose of 5.29A

Block 5.29A defines the official execution plan for the seven onboarded
challenger models. It is planning only: no model is trained, no forecast is
generated, no metric is calculated, and no ranking, tournament, or champion
output is created. Official execution remains blocked for every challenger. The
plan is designed to make Block 5.29B (Challenger Sandbox Execution)
straightforward and safe.

## Execution Order

Statistical challengers run first, then machine learning, then deep learning.

| order | model_name | model_family | priority | runtime_class | dependency_status |
| --- | --- | --- | --- | --- | --- |
{order_lines}

## Dependency Gaps

Dependency availability is inherited from Stage 5.28 onboarding. No packages were
installed in this block. Required dependencies currently unavailable:
{", ".join(missing_deps) if missing_deps else "none"}.

- Models ready for sandbox now (a usable backend present): {ready_for_sandbox}
- Models blocked by missing dependencies: {blocked}

Each missing dependency has a recommended (planned) resolution recorded in
`challenger_dependency_resolution_plan.csv`. Resolution is a prerequisite for
sandbox (where no fallback exists) and for all official execution.

## Sandbox Plan

Sandbox execution uses a controlled subset, not all 454 windows. The recommended
first sandbox scope is the latest 1 window across {SANDBOX_ENTITY_COUNT}
representative entities, for any challenger whose dependencies allow it. Success
requires error-free fit/predict, schema-compliant 30-day forecasts, and no
NaN/inf values within the sandbox runtime budget. See
`challenger_sandbox_plan.csv`.

## Official Execution Gates

All gates must pass before any official challenger run; each is blocking:

{gate_lines}

## Tuning Budget Plan

Tuning is conservative and pre-registered. Statistical challengers have smaller
budgets; ML and deep-learning challengers have explicitly bounded budgets. For
every model, `official_results_may_tune_model = false`, inner validation is
required, and a random seed is required.

| model_name | tuning_allowed | tuning_mode | max_trials | max_runtime_minutes |
| --- | --- | --- | --- | --- |
{budget_lines}

## Leakage Controls

All leakage controls from the Stage 5.26 No-Tuning-Leakage Contract remain in
force and are mapped to every challenger. No model may use official MASE, RMSSE,
statistical significance, tournament rank, or champion feedback for tuning.
Tuning is restricted to inner validation on training-only data. Gates GATE-03,
GATE-09, and GATE-10 enforce these constraints before official execution.

## Dashboard-Readiness Note

All planning artifacts are emitted as flat, tabular CSVs with explicit columns
and a single-row summary, so they can be loaded directly by the Shiny
presentation layer without transformation. The forecast output contract fixes
the schema future challenger forecasts must satisfy, keeping downstream MASE,
RMSSE, non-negative policy, and aggregation steps compatible.

## Recommendation

{recommendation}
"""
    PLANNING_REPORT_OUTPUT.write_text(content, encoding="utf-8")


def _write_outputs(
    execution_plan: pd.DataFrame,
    dependency_resolution: pd.DataFrame,
    tuning_budget: pd.DataFrame,
    sandbox_plan: pd.DataFrame,
    official_gates: pd.DataFrame,
    forecast_contract: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Write all execution planning outputs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    execution_plan.to_csv(EXECUTION_PLAN_OUTPUT, index=False)
    dependency_resolution.to_csv(DEPENDENCY_RESOLUTION_OUTPUT, index=False)
    tuning_budget.to_csv(TUNING_BUDGET_OUTPUT, index=False)
    sandbox_plan.to_csv(SANDBOX_PLAN_OUTPUT, index=False)
    official_gates.to_csv(OFFICIAL_GATE_OUTPUT, index=False)
    forecast_contract.to_csv(FORECAST_CONTRACT_OUTPUT, index=False)
    summary.to_csv(PLANNING_SUMMARY_OUTPUT, index=False)


def build_challenger_execution_plan() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    """Create the Stage 5.29A challenger execution plan."""

    logger.info("Stage 5.29A challenger execution planning started (planning only)")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    registry = _load_registry()
    dependency_matrix = _load_dependency_matrix()
    window_scope_available = WINDOWS_INPUT.exists()
    if not window_scope_available:
        logger.info("Backtesting windows not found (informational): %s", WINDOWS_INPUT)

    dependency_resolution = _build_dependency_resolution(dependency_matrix, timestamp)
    blocked_by_deps = _model_blocked_by_dependencies(dependency_resolution)
    execution_plan = _build_execution_plan(registry, blocked_by_deps, timestamp)
    tuning_budget = _build_tuning_budget(registry, timestamp)
    sandbox_plan = _build_sandbox_plan(blocked_by_deps, window_scope_available, timestamp)
    official_gates = _build_official_gates(timestamp)
    forecast_contract = _build_forecast_contract()
    summary = _build_summary(registry, blocked_by_deps, run_id, timestamp)

    _write_outputs(
        execution_plan,
        dependency_resolution,
        tuning_budget,
        sandbox_plan,
        official_gates,
        forecast_contract,
        summary,
    )
    _write_report(
        execution_plan,
        dependency_resolution,
        tuning_budget,
        sandbox_plan,
        official_gates,
        summary,
        timestamp,
    )

    row = summary.iloc[0]
    logger.info("Planned challengers: %s", int(row["planned_challengers"]))
    logger.info("Models ready for sandbox: %s", int(row["models_ready_for_sandbox"]))
    logger.info("Models blocked by dependencies: %s", int(row["models_blocked_by_dependencies"]))
    logger.info(
        "Models ready for official execution: %s",
        int(row["models_ready_for_official_execution"]),
    )
    logger.info("Official execution allowed: %s", bool(row["official_execution_allowed"]))
    logger.info("Stage 5.29A challenger execution planning completed")
    return (
        execution_plan,
        dependency_resolution,
        tuning_budget,
        sandbox_plan,
        official_gates,
        forecast_contract,
        summary,
    )


if __name__ == "__main__":
    build_challenger_execution_plan()
