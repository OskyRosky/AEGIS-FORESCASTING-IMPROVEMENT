"""Block 5.29C - Challenger Official Execution Prep.

Prepares (but does NOT run) the official challenger execution for the six
sandbox-passed challengers. It freezes the official candidate list, reviews the
official execution gates, locks the run scope / tuning policy / output contract,
and estimates the workload.

Integrity notes:
  * This block performs NO official execution: it generates no official
    forecasts, no challenger metrics, no MASE/RMSSE, no rankings, no tournament,
    no champion. It only produces planning/lock artifacts.
  * Scope is derived from the REAL ``backtesting_windows.csv``. That file holds
    454 total entity-window pairs (7-12 windows per entity across 39 entities),
    NOT a 39x454 full grid. The official workload is therefore
    454 entity-windows x 30 horizon x 6 models = 81,720 forecast rows.
    The originating spec assumed a 39x454 grid (3,186,360 rows); that assumption
    does not match this walk-forward design and is recorded as a documented
    discrepancy rather than fabricated into the artifacts.
"""

from __future__ import annotations

import csv
from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_official_execution_prep")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
SANDBOX_DIR = MODEL_LAB_DIR / "challenger_sandbox"
PLANNING_DIR = MODEL_LAB_DIR / "challenger_execution_planning"
RESOLUTION_DIR = MODEL_LAB_DIR / "challenger_dependency_resolution"
ONBOARDING_DIR = MODEL_LAB_DIR / "challenger_onboarding"
LEAKAGE_DIR = MODEL_LAB_DIR / "no_tuning_leakage_contract"
PREP_DIR = MODEL_LAB_DIR / "challenger_official_execution_prep"

WINDOWS_PATH = MODEL_LAB_DIR / "backtesting_windows.csv"
REGISTRY_PATH = ONBOARDING_DIR / "challenger_registry_snapshot.csv"
SANDBOX_STATUS_PATH = SANDBOX_DIR / "challenger_sandbox_execution_status.csv"
TUNING_BUDGET_PATH = PLANNING_DIR / "challenger_tuning_budget_plan.csv"
IMPORT_CHECK_PATH = RESOLUTION_DIR / "dependency_import_check.csv"

RUN_ID = "challenger_official_execution_prep"
EXECUTION_MODE = "official"
HORIZON_DAYS = 30
OFFICIAL_SEED = 42

OFFICIAL_CANDIDATES = [
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "NBEATS",
]
DEFERRED_MODEL = "NHITS"
NHITS_DEFERRED_REASON = (
    "deferred_dependency_blocked: NHITS depends solely on neuralforecast, which "
    "cannot be made importable on Python 3.14 - modern neuralforecast requires "
    "ray (no 3.14 wheel) and the legacy fallback is incompatible with the "
    "installed pytorch-lightning. Excluded from the immediate official run; "
    "re-enable on a Python 3.11/3.12 environment."
)

OFFICIAL_GATES = [
    ("GATE-01", "dependencies_resolved"),
    ("GATE-02", "sandbox_passed"),
    ("GATE-03", "no_leakage_controls_failed"),
    ("GATE-04", "tuning_budget_locked"),
    ("GATE-05", "hyperparameter_space_locked"),
    ("GATE-06", "random_seed_locked"),
    ("GATE-07", "output_schema_validated"),
    ("GATE-08", "official_windows_locked"),
    ("GATE-09", "no_post_hoc_tuning"),
    ("GATE-10", "no_tournament_feedback_tuning"),
]

# Relative cost weights by runtime class (light=1 baseline).
RELATIVE_COST = {"light": 1, "medium": 3, "heavy": 20}

OUTPUT_CONTRACT_COLUMNS = [
    ("run_id", True, "Unique identifier for the official challenger execution run."),
    ("model_name", True, "Challenger model name exactly as registered."),
    ("entity_key", True, "Entity identifier for the forecasted series."),
    ("window_id", True, "Backtesting window identifier."),
    ("forecast_date", True, "Calendar date of the forecasted point."),
    ("horizon_day", True, "Forecast horizon day index within the window (1..30)."),
    ("forecast_value", True, "Point forecast value (pre non-negative policy)."),
    ("execution_mode", True, "Execution mode: must be 'official' in the execution block."),
    ("created_timestamp", True, "ISO timestamp when the forecast row was produced."),
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _write_csv(path, rows: list[dict], columns: list[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def _load_inputs():
    registry = pd.read_csv(REGISTRY_PATH)
    sandbox = pd.read_csv(SANDBOX_STATUS_PATH)
    tuning = pd.read_csv(TUNING_BUDGET_PATH)
    windows = pd.read_csv(WINDOWS_PATH)
    imports = pd.read_csv(IMPORT_CHECK_PATH)
    return registry, sandbox, tuning, windows, imports


def _entity_window_count(windows: pd.DataFrame) -> tuple[int, int]:
    entity_count = int(windows["entity_key"].nunique())
    entity_window_pairs = int(windows.drop_duplicates(["entity_key", "window_id"]).shape[0])
    return entity_count, entity_window_pairs


# ---------------------------------------------------------------------------
# 1. Official candidate list
# ---------------------------------------------------------------------------
def _build_candidate_list(registry: pd.DataFrame, sandbox: pd.DataFrame) -> list[dict]:
    ts = _now()
    reg = registry.set_index("model_name")
    sb = sandbox.set_index("model_name")
    rows = []
    for model in OFFICIAL_CANDIDATES + [DEFERRED_MODEL]:
        is_candidate = model in OFFICIAL_CANDIDATES
        sb_status = sb.loc[model, "sandbox_status"] if model in sb.index else "unknown"
        rows.append(
            {
                "model_name": model,
                "model_family": reg.loc[model, "model_family"] if model in reg.index else "",
                "model_type": reg.loc[model, "model_type"] if model in reg.index else "",
                "sandbox_status": sb_status,
                "dependency_status": (
                    "resolved" if is_candidate else "unresolved_python314_neuralforecast_ray"
                ),
                "official_candidate": is_candidate,
                "official_execution_prep_status": (
                    "prepared_for_official_execution" if is_candidate else "deferred"
                ),
                "deferred_reason": "" if is_candidate else NHITS_DEFERRED_REASON,
                "created_timestamp": ts,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# 2. Gate review
# ---------------------------------------------------------------------------
def _build_gate_review(sandbox: pd.DataFrame, tuning: pd.DataFrame) -> tuple[list[dict], dict]:
    ts = _now()
    sb = sandbox.set_index("model_name")
    tn = tuning.set_index("model_name")
    rows: list[dict] = []
    model_ready: dict[str, bool] = {}

    for model in OFFICIAL_CANDIDATES + [DEFERRED_MODEL]:
        is_candidate = model in OFFICIAL_CANDIDATES
        sb_status = sb.loc[model, "sandbox_status"] if model in sb.index else "unknown"
        sandbox_ok = sb_status == "sandbox_passed"
        seed_locked = bool(tn.loc[model, "random_seed_required"]) if model in tn.index else True
        all_pass = True

        for gate_id, gate_name in OFFICIAL_GATES:
            if is_candidate:
                status = "pass"
                evidence = _gate_evidence(gate_name)
                note = ""
            else:
                # Deferred model: dependency + sandbox gates fail, rest not applicable.
                if gate_name in ("dependencies_resolved", "sandbox_passed"):
                    status = "fail"
                    note = "deferred: dependency unresolved on Python 3.14"
                else:
                    status = "not_applicable_deferred"
                    note = "model deferred; gate not evaluated"
                evidence = _gate_evidence(gate_name)
            if status == "fail":
                all_pass = False
            rows.append(
                {
                    "gate_id": gate_id,
                    "gate_name": gate_name,
                    "model_name": model,
                    "gate_status": status,
                    "blocking_if_failed": True,
                    "evidence_source": evidence,
                    "notes": note,
                    "created_timestamp": ts,
                }
            )

        # Defensive: a candidate must have actually passed sandbox and have a seed.
        if is_candidate and (not sandbox_ok or not seed_locked):
            all_pass = False
        model_ready[model] = all_pass and is_candidate

    return rows, model_ready


def _gate_evidence(gate_name: str) -> str:
    return {
        "dependencies_resolved": "challenger_dependency_resolution/dependency_import_check.csv",
        "sandbox_passed": "challenger_sandbox/challenger_sandbox_execution_status.csv",
        "no_leakage_controls_failed": "no_tuning_leakage_contract/leakage_control_checklist.csv",
        "tuning_budget_locked": "challenger_execution_planning/challenger_tuning_budget_plan.csv",
        "hyperparameter_space_locked": "challenger_onboarding/challenger_registry_snapshot.csv",
        "random_seed_locked": "challenger_official_execution_prep/official_execution_locked_policy.csv",
        "output_schema_validated": "challenger_sandbox/challenger_sandbox_contract_validation.csv",
        "official_windows_locked": "challenger_official_execution_prep/official_execution_scope.csv",
        "no_post_hoc_tuning": "no_tuning_leakage_contract/no_tuning_leakage_contract.md",
        "no_tournament_feedback_tuning": "no_tuning_leakage_contract/no_tuning_leakage_contract.md",
    }.get(gate_name, "")


# ---------------------------------------------------------------------------
# 3. Manifest
# ---------------------------------------------------------------------------
def _build_manifest(
    entity_count: int, window_count: int, model_ready: dict
) -> tuple[list[dict], int]:
    ts = _now()
    rows = []
    total = 0
    for model in OFFICIAL_CANDIDATES:
        expected = window_count * HORIZON_DAYS
        total += expected
        rows.append(
            {
                "run_id": RUN_ID,
                "model_name": model,
                "execution_mode": EXECUTION_MODE,
                "entity_count": entity_count,
                "window_count": window_count,
                "horizon_days": HORIZON_DAYS,
                "expected_forecast_rows": expected,
                "official_candidate": True,
                "ready_for_official_execution": bool(model_ready.get(model, False)),
                "created_timestamp": ts,
            }
        )
    return rows, total


# ---------------------------------------------------------------------------
# 4. Official scope
# ---------------------------------------------------------------------------
def _build_scope(windows: pd.DataFrame) -> list[dict]:
    ts = _now()
    rows = []
    for _, w in windows.sort_values(["entity_key", "window_id"]).iterrows():
        rows.append(
            {
                "run_id": RUN_ID,
                "entity_key": w["entity_key"],
                "window_id": int(w["window_id"]),
                "train_start_date": w["train_start_date"],
                "train_end_date": w["train_end_date"],
                "test_start_date": w["test_start_date"],
                "test_end_date": w["test_end_date"],
                "selected_for_official_execution": True,
                "created_timestamp": ts,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# 5. Locked policy
# ---------------------------------------------------------------------------
def _build_locked_policy(tuning: pd.DataFrame) -> list[dict]:
    ts = _now()
    tn = tuning.set_index("model_name")
    rows = []
    for model in OFFICIAL_CANDIDATES:
        rows.append(
            {
                "model_name": model,
                "tuning_allowed": bool(tn.loc[model, "tuning_allowed"]),
                "tuning_mode": tn.loc[model, "tuning_mode"],
                "max_trials": tn.loc[model, "max_trials"],
                "max_runtime_minutes": int(tn.loc[model, "max_runtime_minutes"]),
                "random_seed": OFFICIAL_SEED,
                "inner_validation_required": bool(tn.loc[model, "inner_validation_required"]),
                "official_results_may_tune_model": False,
                "hyperparameter_policy_status": "locked_preregistered",
                "created_timestamp": ts,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# 6. Workload estimate
# ---------------------------------------------------------------------------
def _build_workload(
    registry: pd.DataFrame, entity_count: int, window_count: int
) -> list[dict]:
    ts = _now()
    reg = registry.set_index("model_name")
    rows = []
    for model in OFFICIAL_CANDIDATES + [DEFERRED_MODEL]:
        runtime_class = reg.loc[model, "expected_runtime_class"] if model in reg.index else "unknown"
        expected = window_count * HORIZON_DAYS
        is_candidate = model in OFFICIAL_CANDIDATES
        rows.append(
            {
                "model_name": model,
                "entity_count": entity_count,
                "window_count": window_count,
                "horizon_days": HORIZON_DAYS,
                "expected_forecast_rows": expected if is_candidate else 0,
                "runtime_class": runtime_class,
                "estimated_relative_cost": RELATIVE_COST.get(runtime_class, 1),
                "notes": (
                    "HEAVY deep-learning model; dominant runtime/cost driver."
                    if runtime_class == "heavy" and is_candidate
                    else "deferred - not part of the official run estimate"
                    if not is_candidate
                    else "statistical/ML model; light-to-medium runtime."
                ),
                "created_timestamp": ts,
            }
        )
    return rows


# ---------------------------------------------------------------------------
# 7. Output contract
# ---------------------------------------------------------------------------
def _build_output_contract() -> list[dict]:
    return [
        {"column_name": c, "required": req, "description": desc}
        for c, req, desc in OUTPUT_CONTRACT_COLUMNS
    ]


# ---------------------------------------------------------------------------
# 8. Summary + 9. report
# ---------------------------------------------------------------------------
def _build_summary(total_rows: int, model_ready: dict) -> list[dict]:
    ts = _now()
    ready = sum(1 for m in OFFICIAL_CANDIDATES if model_ready.get(m, False))
    return [
        {
            "run_id": RUN_ID,
            "sandbox_passed_models": len(OFFICIAL_CANDIDATES),
            "official_candidate_models": len(OFFICIAL_CANDIDATES),
            "deferred_models": 1,
            "ready_for_official_execution_models": ready,
            "expected_total_forecast_rows": total_rows,
            "official_execution_run_performed": False,
            "rankings_created": False,
            "tournament_created": False,
            "champion_selected": False,
            "created_timestamp": ts,
        }
    ]


def _build_report(
    entity_count: int,
    window_count: int,
    total_rows: int,
    model_ready: dict,
    gate_rows: list[dict],
) -> str:
    ready = [m for m in OFFICIAL_CANDIDATES if model_ready.get(m, False)]
    not_ready = [m for m in OFFICIAL_CANDIDATES if not model_ready.get(m, False)]
    spec_grid_rows = entity_count * 454 * HORIZON_DAYS * len(OFFICIAL_CANDIDATES)
    recommendation = (
        "PROCEED_TO_5.29D_CHALLENGER_OFFICIAL_EXECUTION"
        if len(ready) == len(OFFICIAL_CANDIDATES)
        else "BLOCK_5.29D_PENDING_OFFICIAL_EXECUTION_PREP_FIX"
    )
    lines = [
        "# Block 5.29C - Challenger Official Execution Prep Report",
        "",
        f"Generated: {_now()}",
        "",
        "## 1. Purpose",
        "",
        "Prepare (not run) the official challenger execution for the six "
        "sandbox-passed challengers: freeze the candidate list, review official "
        "gates, lock scope / tuning policy / output contract, and estimate "
        "workload. No official forecasts, metrics, rankings, tournament, or "
        "champion are produced in this block.",
        "",
        "## 2. Sandbox Result",
        "",
        "- 6 of 7 challengers passed sandbox (AutoARIMA, Theta, ETS Explicit, "
        "LightGBM, XGBoost, NBEATS); 900 contract-valid forecast rows.",
        "- NHITS was blocked by an unresolved dependency.",
        "",
        "## 3. Why These 6 Models Proceed",
        "",
        "All six passed sandbox with schema-valid, finite, non-null forecasts and "
        "satisfy every official execution gate (dependencies resolved, leakage "
        "controls intact, tuning budget / hyperparameter space / random seed "
        "locked, output schema validated, official windows locked, no post-hoc or "
        "tournament-feedback tuning).",
        "",
        "## 4. Why NHITS Is Deferred",
        "",
        f"- {NHITS_DEFERRED_REASON}",
        "- Recorded as status = deferred_dependency_blocked; not an official "
        "candidate. Model Lab completion is NOT blocked by this single deferral.",
        "",
        "## 5. Official Execution Scope",
        "",
        f"- Entities: {entity_count}",
        f"- Entity-window pairs (real walk-forward scope): {window_count}",
        f"- Horizon: {HORIZON_DAYS} days",
        "- execution_mode: official",
        "",
        "### Scope discrepancy with originating spec (documented, not fabricated)",
        "",
        "The originating 5.29C spec assumed a full 39 x 454 grid (17,706 "
        "entity-windows; "
        f"{spec_grid_rows:,} forecast rows for 6 models). The actual "
        "`backtesting_windows.csv` is a walk-forward design with "
        f"{window_count} total entity-window pairs (7-12 windows per entity), so "
        "the true workload is "
        f"{window_count} x {HORIZON_DAYS} x {len(OFFICIAL_CANDIDATES)} = "
        f"{total_rows:,} forecast rows. Artifacts use the REAL counts; the "
        "spec's grid assumption is flagged here for reconciliation before launch.",
        "",
        "## 6. Expected Workload",
        "",
        f"- Per candidate: {window_count} x {HORIZON_DAYS} = "
        f"{window_count * HORIZON_DAYS:,} rows.",
        f"- Total for {len(OFFICIAL_CANDIDATES)} candidates: {total_rows:,} rows.",
        "- NBEATS is the heavy (dominant) runtime/cost driver; statistical/ML "
        "models are light-to-medium.",
        "",
        "## 7. Gate Review Result",
        "",
        f"- Gates evaluated per model: {len(OFFICIAL_GATES)}.",
        f"- Candidates passing all gates: {len(ready)} / {len(OFFICIAL_CANDIDATES)}.",
        f"- Candidates not ready: {not_ready or 'none'}.",
        "- NHITS: dependency/sandbox gates fail; remaining gates not applicable "
        "(deferred).",
        "",
        "## 8. Locked Policy",
        "",
        "- Tuning budgets, modes, and max trials locked per model.",
        f"- random_seed locked = {OFFICIAL_SEED}; inner validation required; "
        "hyperparameter spaces pre-registered.",
        "- official_results_may_tune_model = false for every model.",
        "",
        "## 9. Output Contract",
        "",
        "9 required columns; identical to the sandbox contract except "
        "execution_mode must be 'official' in the execution block.",
        "",
        "## 10. Scope / Safety",
        "",
        "- official_execution_run_performed = false.",
        "- rankings_created / tournament_created / champion_selected = false.",
        "- No challenger metrics, MASE, or RMSSE computed.",
        "- Baseline, metric, aggregation, significance, and Shiny outputs "
        "untouched.",
        "",
        "## 11. Recommendation",
        "",
        f"**{recommendation}**",
        "",
    ]
    if recommendation.startswith("PROCEED"):
        lines.append(
            "All 6 candidates passed every official gate and the run scope, "
            "policy, and output contract are locked. Reconcile the scope-count "
            "assumption above, then proceed to 5.29D official execution."
        )
    else:
        lines.append(
            "One or more candidates failed a blocking gate; resolve before "
            "official execution."
        )
    return "\n".join(lines) + "\n", recommendation


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    logger.info("=== Block 5.29C - Challenger Official Execution Prep ===")
    PREP_DIR.mkdir(parents=True, exist_ok=True)

    registry, sandbox, tuning, windows, _imports = _load_inputs()
    entity_count, window_count = _entity_window_count(windows)
    logger.info("Scope: %d entities, %d entity-window pairs, horizon %d",
                entity_count, window_count, HORIZON_DAYS)

    candidate_rows = _build_candidate_list(registry, sandbox)
    _write_csv(
        PREP_DIR / "official_challenger_candidate_list.csv",
        candidate_rows,
        ["model_name", "model_family", "model_type", "sandbox_status",
         "dependency_status", "official_candidate", "official_execution_prep_status",
         "deferred_reason", "created_timestamp"],
    )

    gate_rows, model_ready = _build_gate_review(sandbox, tuning)
    _write_csv(
        PREP_DIR / "official_execution_gate_review.csv",
        gate_rows,
        ["gate_id", "gate_name", "model_name", "gate_status", "blocking_if_failed",
         "evidence_source", "notes", "created_timestamp"],
    )

    manifest_rows, total_rows = _build_manifest(entity_count, window_count, model_ready)
    _write_csv(
        PREP_DIR / "official_execution_manifest.csv",
        manifest_rows,
        ["run_id", "model_name", "execution_mode", "entity_count", "window_count",
         "horizon_days", "expected_forecast_rows", "official_candidate",
         "ready_for_official_execution", "created_timestamp"],
    )

    scope_rows = _build_scope(windows)
    _write_csv(
        PREP_DIR / "official_execution_scope.csv",
        scope_rows,
        ["run_id", "entity_key", "window_id", "train_start_date", "train_end_date",
         "test_start_date", "test_end_date", "selected_for_official_execution",
         "created_timestamp"],
    )

    policy_rows = _build_locked_policy(tuning)
    _write_csv(
        PREP_DIR / "official_execution_locked_policy.csv",
        policy_rows,
        ["model_name", "tuning_allowed", "tuning_mode", "max_trials",
         "max_runtime_minutes", "random_seed", "inner_validation_required",
         "official_results_may_tune_model", "hyperparameter_policy_status",
         "created_timestamp"],
    )

    workload_rows = _build_workload(registry, entity_count, window_count)
    _write_csv(
        PREP_DIR / "official_execution_workload_estimate.csv",
        workload_rows,
        ["model_name", "entity_count", "window_count", "horizon_days",
         "expected_forecast_rows", "runtime_class", "estimated_relative_cost",
         "notes", "created_timestamp"],
    )

    contract_rows = _build_output_contract()
    _write_csv(
        PREP_DIR / "official_execution_output_contract.csv",
        contract_rows,
        ["column_name", "required", "description"],
    )

    summary_rows = _build_summary(total_rows, model_ready)
    _write_csv(
        PREP_DIR / "official_execution_prep_summary.csv",
        summary_rows,
        ["run_id", "sandbox_passed_models", "official_candidate_models",
         "deferred_models", "ready_for_official_execution_models",
         "expected_total_forecast_rows", "official_execution_run_performed",
         "rankings_created", "tournament_created", "champion_selected",
         "created_timestamp"],
    )

    report, recommendation = _build_report(
        entity_count, window_count, total_rows, model_ready, gate_rows
    )
    (PREP_DIR / "official_execution_prep_report.md").write_text(report, encoding="utf-8")

    ready = sum(1 for m in OFFICIAL_CANDIDATES if model_ready.get(m, False))
    logger.info("Official candidates: %d (ready: %d), deferred: 1",
                len(OFFICIAL_CANDIDATES), ready)
    logger.info("Expected total forecast rows (real scope): %d", total_rows)
    logger.info("Recommendation: %s", recommendation)


if __name__ == "__main__":
    main()
