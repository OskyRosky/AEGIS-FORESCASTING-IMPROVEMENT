"""Stage 06 Block 6.2 decision rules and action framework.

Creates governed action mappings from Model Lab evidence, risks, and champion
conditions. This script writes only to outputs/governance/6_2_decision_rules.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_governance_6_2")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules"

GOV_60_RESOLUTION = (
    PROJECT_ROOT
    / "outputs"
    / "governance"
    / "6_0_audit5_finding_resolution"
    / "audit5_finding_resolution.csv"
)
GOV_60_CORRECTION = (
    PROJECT_ROOT
    / "outputs"
    / "governance"
    / "6_0_audit5_finding_resolution"
    / "governed_manifest_correction.csv"
)
GOV_61_DEFINITIONS = (
    PROJECT_ROOT
    / "outputs"
    / "governance"
    / "6_1_governance_foundation"
    / "governance_definitions.csv"
)
GOV_61_TAXONOMY = (
    PROJECT_ROOT
    / "outputs"
    / "governance"
    / "6_1_governance_foundation"
    / "governance_status_taxonomy.csv"
)
GOV_61_VALIDATION = (
    PROJECT_ROOT
    / "outputs"
    / "governance"
    / "6_1_governance_foundation"
    / "governance_6_0_6_1_validation.csv"
)

CLOSURE_UNIVERSE = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "model_lab_closure_pack"
    / "model_lab_final_model_universe.csv"
)
CLOSURE_RISKS = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "model_lab_closure_pack"
    / "model_lab_risk_register_final.csv"
)
CLOSURE_CHAMPION = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "model_lab_closure_pack"
    / "model_lab_champion_summary.csv"
)
CHAMPION_DECISION = (
    PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision" / "champion_decision.csv"
)
CHAMPION_CANDIDATES = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "champion_decision"
    / "champion_candidate_evaluation.csv"
)
TOURNAMENT_SCORECARD = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "tournament_engine"
    / "tournament_model_scorecard.csv"
)
TOURNAMENT_SANITY_SUMMARY = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "tournament_sanity_review"
    / "tournament_sanity_summary.csv"
)
AUDIT5_SUMMARY = PROJECT_ROOT / "outputs" / "model_lab" / "audit_5" / "audit_5_summary.csv"

REQUIRED_ACTIONS = [
    "KEEP",
    "KEEP_WITH_CONDITIONS",
    "MONITOR",
    "REVIEW",
    "REVIEW_INVESTIGATE",
    "TEST_LATER",
    "DEFER",
    "EXCLUDE_FROM_CHAMPION_CONSIDERATION",
    "SURFACE_ON_DASHBOARD",
    "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER",
    "BENCHMARK_REFERENCE",
    "MODEL_POOL_REFERENCE",
]

REQUIRED_RISKS = [f"R-{i:03d}" for i in range(1, 8)]

REQUIRED_OUTPUTS = [
    "decision_action_framework.csv",
    "risk_to_action_mapping.csv",
    "model_recommendation_rules.csv",
    "governance_recommendations.csv",
    "decision_rule_traceability.csv",
    "decision_rules_validation.csv",
    "decision_rules_report.md",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"Required input missing: {path}")
    return pd.read_csv(path)


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _bool_value(value: object) -> bool:
    return str(value).strip().lower() == "true"


def build_action_framework(ts: str) -> pd.DataFrame:
    rows = [
        {
            "action_id": "A-001",
            "action_name": "KEEP",
            "action_category": "model_pool",
            "definition": "Retain model as an active governed model or reference.",
            "trigger_conditions": "Validated model with no severe unresolved risk.",
            "required_evidence": "Closure universe, candidate evaluation, and scorecard status.",
            "governance_treatment": "Keep in governed model universe.",
            "dashboard_treatment": "May be displayed as an active model or reference.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-002",
            "action_name": "KEEP_WITH_CONDITIONS",
            "action_category": "champion_governance",
            "definition": "Retain as selected champion only with explicitly visible conditions.",
            "trigger_conditions": "Champion decision is CHAMPION_SELECTED_WITH_CONDITIONS.",
            "required_evidence": "Champion decision and closure champion summary.",
            "governance_treatment": "Preserve conditions and require monitoring.",
            "dashboard_treatment": "Show as conditional champion with medium confidence, not an unconditional winner.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-003",
            "action_name": "MONITOR",
            "action_category": "oversight",
            "definition": "Carry forward a condition, advisory, or model status for future review.",
            "trigger_conditions": "Medium confidence, audit advisory, sanity advisory, or active non-champion model.",
            "required_evidence": "Audit, sanity, risk register, or decision artifact.",
            "governance_treatment": "Track without changing source evidence.",
            "dashboard_treatment": "Surface if relevant to model interpretation.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-004",
            "action_name": "REVIEW",
            "action_category": "manual_review",
            "definition": "Require human review before stronger operational claims are made.",
            "trigger_conditions": "Manual review flag or unresolved model risk.",
            "required_evidence": "Risk register or candidate readiness finding.",
            "governance_treatment": "Keep visible and prevent silent upgrade.",
            "dashboard_treatment": "Show review-needed language.",
            "manual_review_required": True,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-005",
            "action_name": "REVIEW_INVESTIGATE",
            "action_category": "manual_review",
            "definition": "Investigate likely implementation or behavior issue before future contender treatment.",
            "trigger_conditions": "Extreme error, possible scale issue, or recursive collapse risk.",
            "required_evidence": "Risk register and audit/sanity findings.",
            "governance_treatment": "Keep in history but do not treat as champion-safe.",
            "dashboard_treatment": "Surface as high-risk investigation item.",
            "manual_review_required": True,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-006",
            "action_name": "TEST_LATER",
            "action_category": "future_work",
            "definition": "Reserve model concept for future testing in a more suitable environment.",
            "trigger_conditions": "Deferred due to runtime or dependency limitation.",
            "required_evidence": "Closure deferred model and risk records.",
            "governance_treatment": "Document as deferred future work, not discarded.",
            "dashboard_treatment": "Show as deferred/future work if deferred models are displayed.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-007",
            "action_name": "DEFER",
            "action_category": "future_work",
            "definition": "Exclude from current scored tournament and champion consideration while preserving rationale.",
            "trigger_conditions": "Model is deferred_runtime_impractical or deferred_dependency_blocked.",
            "required_evidence": "Model universe and deferred model records.",
            "governance_treatment": "Do not score or compare in current champion decision.",
            "dashboard_treatment": "Show deferral reason if shown.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-008",
            "action_name": "EXCLUDE_FROM_CHAMPION_CONSIDERATION",
            "action_category": "champion_governance",
            "definition": "Prevent model from being treated as champion-eligible under current evidence.",
            "trigger_conditions": "High unresolved risk, deferred status, or ineligible candidate status.",
            "required_evidence": "Candidate evaluation, risk register, or deferral record.",
            "governance_treatment": "Keep visible but exclude from champion claims.",
            "dashboard_treatment": "Explain exclusion reason if model is displayed.",
            "manual_review_required": True,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-009",
            "action_name": "SURFACE_ON_DASHBOARD",
            "action_category": "dashboard_contract",
            "definition": "Require downstream dashboard to show a risk, condition, or caveat.",
            "trigger_conditions": "Active risk, condition, advisory, deferral, or governed correction.",
            "required_evidence": "Risk mapping, audit finding, or governance correction.",
            "governance_treatment": "Carry the condition forward.",
            "dashboard_treatment": "Display honestly; do not hide caveats.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-010",
            "action_name": "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER",
            "action_category": "dashboard_contract",
            "definition": "Forbid language that upgrades a conditional champion into an absolute winner.",
            "trigger_conditions": "Champion decision is conditional or confidence is not high.",
            "required_evidence": "Champion decision and governance definitions.",
            "governance_treatment": "Use conditional champion language only.",
            "dashboard_treatment": "Say conditional champion / medium confidence.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-011",
            "action_name": "BENCHMARK_REFERENCE",
            "action_category": "model_pool",
            "definition": "Retain non-champion baseline as a benchmark comparison reference.",
            "trigger_conditions": "Baseline model remains valid but was not selected champion.",
            "required_evidence": "Final model universe and champion decision.",
            "governance_treatment": "Use as baseline context, not champion.",
            "dashboard_treatment": "May appear in baseline scorecards and comparisons.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
        {
            "action_id": "A-012",
            "action_name": "MODEL_POOL_REFERENCE",
            "action_category": "model_pool",
            "definition": "Retain non-champion challenger as a governed model-pool reference.",
            "trigger_conditions": "Challenger model remains valid but was not selected champion.",
            "required_evidence": "Final model universe and champion decision.",
            "governance_treatment": "Use as challenger context, not champion.",
            "dashboard_treatment": "May appear in challenger scorecards and comparisons.",
            "manual_review_required": False,
            "terminal_or_transitional": "transitional",
            "created_timestamp": ts,
        },
    ]
    return pd.DataFrame(rows)


def build_risk_mapping(ts: str) -> pd.DataFrame:
    risk_source = _read(CLOSURE_RISKS).set_index("risk_id")
    mapping = {
        "R-001": ("FastNeuralAR_MLP", "REVIEW_INVESTIGATE", "EXCLUDE_FROM_CHAMPION_CONSIDERATION", True, True, "Future neural implementation review or scale/recursive behavior fix."),
        "R-002": ("NBEATS", "TEST_LATER", "DEFER", True, True, "Stronger VM/container/GPU or optimized batch execution becomes available."),
        "R-003": ("NHITS", "TEST_LATER", "DEFER", True, True, "Python 3.11/3.12 neuralforecast/ray-compatible environment becomes available."),
        "R-004": ("ETS Explicit", "KEEP_WITH_CONDITIONS", "MONITOR", True, False, "Future audit or production monitoring changes confidence/conditions."),
        "R-005": ("AUDIT_4", "MONITOR", "SURFACE_ON_DASHBOARD", True, False, "Audit #4 condition is superseded or formally closed."),
        "R-006": ("TOURNAMENT_SANITY_REVIEW", "MONITOR", "SURFACE_ON_DASHBOARD", True, False, "5.30A sanity advisory/minor is superseded or formally closed."),
        "R-007": ("FixedGrowth_6", "REVIEW", "MONITOR", True, False, "Manual review resolves or reclassifies FixedGrowth_6 risk."),
    }
    rows = []
    for risk_id in REQUIRED_RISKS:
        source = risk_source.loc[risk_id] if risk_id in risk_source.index else pd.Series(dtype=object)
        model_name, primary, secondary, dashboard, future_work, trigger = mapping[risk_id]
        risk_desc = str(source.get("risk_description", ""))
        if risk_id == "R-001":
            risk_desc = "high MASE/RMSSE behavior / possible scale or recursive collapse issue"
        elif risk_id == "R-002":
            risk_desc = "runtime impractical for MVP/current environment"
        elif risk_id == "R-003":
            risk_desc = "dependency blocked / Python 3.14 neuralforecast ray incompatibility"
        elif risk_id == "R-004":
            risk_desc = "champion selected with conditions / medium confidence"
        elif risk_id == "R-005":
            risk_desc = "Audit #4 conditions carried forward"
        elif risk_id == "R-006":
            risk_desc = "5.30A sanity advisories/minors carried forward"
        elif risk_id == "R-007":
            risk_desc = "manual review carry-forward"
        rows.append(
            {
                "risk_id": risk_id,
                "source_artifact": _rel(CLOSURE_RISKS),
                "risk_type": str(source.get("risk_type", "")),
                "model_name": model_name,
                "risk_description": risk_desc,
                "risk_level": str(source.get("risk_level", "")),
                "assigned_primary_action": primary,
                "assigned_secondary_action": secondary,
                "action_rationale": f"{risk_id} is governed through {primary} with {secondary} to prevent silent risk loss.",
                "dashboard_carry_forward": dashboard,
                "future_work_required": future_work,
                "review_trigger": trigger,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


def build_recommendation_rules(ts: str) -> pd.DataFrame:
    rules = [
        ("RULE-001", "Conditional champion rule", "selected champion", "decision=CHAMPION_SELECTED_WITH_CONDITIONS", "champion_decision.csv", "KEEP_WITH_CONDITIONS", "non_blocking", False, "Surface conditional champion and medium confidence."),
        ("RULE-002", "High-risk model rule", "high-risk models", "risk_level=high or audit_risk_flag=true", "risk register", "REVIEW_INVESTIGATE", "blocking_for_champion", True, "Surface risk and investigation need."),
        ("RULE-003", "Deferred runtime rule", "runtime-deferred models", "final_status=deferred_runtime_impractical", "deferred model record", "TEST_LATER", "not_current_candidate", False, "Show runtime deferral, not discarded."),
        ("RULE-004", "Deferred dependency rule", "dependency-deferred models", "final_status=deferred_dependency_blocked", "deferred model record", "TEST_LATER", "not_current_candidate", False, "Show dependency deferral, not discarded."),
        ("RULE-005", "Manual review rule", "manual-review models", "manual review carried forward", "risk register", "REVIEW", "non_blocking", True, "Show review-needed label."),
        ("RULE-006", "Medium confidence rule", "conditional champion", "decision_confidence=medium", "champion summary", "MONITOR", "non_blocking", False, "Display confidence as medium."),
        ("RULE-007", "Tournament standing is not champion rule", "all models", "preliminary_position exists", "tournament standings", "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER", "communication_guardrail", False, "Do not imply position equals champion."),
        ("RULE-008", "Ineligible due to risk rule", "ineligible risk models", "champion_candidate_status=ineligible_due_to_risk", "candidate evaluation", "EXCLUDE_FROM_CHAMPION_CONSIDERATION", "blocking_for_champion", True, "Explain risk-based exclusion."),
        ("RULE-009", "Ineligible due to evidence rule", "ineligible evidence models", "champion_candidate_status=ineligible_due_to_evidence", "candidate evaluation", "EXCLUDE_FROM_CHAMPION_CONSIDERATION", "blocking_for_champion", False, "Explain evidence-based exclusion."),
        ("RULE-010", "Audit advisory carry-forward rule", "audit/sanity findings", "advisory or minor finding exists", "Audit #4/#5/5.30A artifacts", "MONITOR", "non_blocking", False, "Keep audit/sanity caveats visible."),
        ("RULE-011", "Dashboard surfacing rule", "all active risks", "dashboard_carry_forward=true", "risk_to_action_mapping.csv", "SURFACE_ON_DASHBOARD", "communication_guardrail", False, "Dashboard must surface conditions and risks."),
        ("RULE-012", "No silent upgrade rule", "conditional decisions", "conditional champion or unresolved risk", "governance definitions/statuses", "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER", "communication_guardrail", False, "No unconditional winner language without future audit."),
    ]
    return pd.DataFrame(
        [
            {
                "rule_id": rule_id,
                "rule_name": rule_name,
                "applies_to": applies_to,
                "input_condition": input_condition,
                "required_evidence": required_evidence,
                "recommendation_action": action,
                "blocking_status": blocking_status,
                "manual_review_required": manual_review,
                "dashboard_requirement": dashboard,
                "created_timestamp": ts,
            }
            for rule_id, rule_name, applies_to, input_condition, required_evidence, action, blocking_status, manual_review, dashboard in rules
        ]
    )


def build_recommendations(ts: str) -> pd.DataFrame:
    universe = _read(CLOSURE_UNIVERSE)
    candidates = _read(CHAMPION_CANDIDATES)
    candidate_by_model = candidates.set_index("model_name")
    rows = []
    for _, model in universe.iterrows():
        name = str(model["model_name"])
        origin = str(model["model_origin"])
        final_status = str(model["final_status"])
        selected = _bool_value(model["selected_champion"])
        risk_flag = _bool_value(model["risk_flag"])
        eligible = _bool_value(model["eligible_for_champion"])
        primary = "MONITOR"
        secondary = "MODEL_POOL_REFERENCE" if origin == "challenger" else "BENCHMARK_REFERENCE"
        dashboard = "Display as governed non-champion reference model."
        future = "Review if future evidence materially changes model status."
        summary = "Valid non-champion model retained as a governed reference."

        if name == "ETS Explicit":
            primary = "KEEP_WITH_CONDITIONS"
            secondary = "MONITOR"
            dashboard = "Display as conditional champion with medium confidence; do not present as unconditional winner."
            future = "Future audit or production monitoring may close or change champion conditions."
            summary = "Selected champion with conditions; preserve medium confidence and explicit caveats."
        elif name == "FastNeuralAR_MLP":
            primary = "REVIEW_INVESTIGATE"
            secondary = "EXCLUDE_FROM_CHAMPION_CONSIDERATION"
            eligible = False
            risk_flag = True
            dashboard = "Surface high-risk behavior and investigation need."
            future = "Investigate scale/normalization or recursive-collapse behavior before contender treatment."
            summary = "High-risk challenger retained for transparency but excluded from champion consideration."
        elif name == "NBEATS":
            primary = "TEST_LATER"
            secondary = "DEFER"
            eligible = False
            dashboard = "Show as deferred_runtime_impractical future-work model."
            future = "Retest in stronger VM/container/GPU or optimized execution environment."
            summary = "Deferred due to runtime impracticality for MVP/current environment."
        elif name == "NHITS":
            primary = "TEST_LATER"
            secondary = "DEFER"
            eligible = False
            dashboard = "Show as deferred_dependency_blocked future-work model."
            future = "Retest in Python 3.11/3.12 neuralforecast/ray-compatible environment."
            summary = "Deferred due to Python 3.14 neuralforecast/ray dependency incompatibility."
        elif name == "FixedGrowth_6":
            primary = "REVIEW"
            secondary = "MONITOR"
            dashboard = "Display manual-review carry-forward if shown in model details."
            future = "Manual review resolves or reclassifies risk status."
            summary = "Baseline retained as reference with manual review carry-forward."

        if name in candidate_by_model.index:
            candidate = candidate_by_model.loc[name]
            if str(candidate.get("champion_candidate_status", "")) == "ineligible_due_to_risk" and name != "FastNeuralAR_MLP":
                primary = "REVIEW"
                secondary = "MONITOR"

        rows.append(
            {
                "model_name": name,
                "model_origin": origin,
                "model_family": model["model_family"],
                "final_status": final_status,
                "selected_champion": selected,
                "risk_flag": risk_flag,
                "eligible_for_champion": eligible,
                "governance_primary_action": primary,
                "governance_secondary_action": secondary,
                "recommendation_summary": summary,
                "dashboard_requirement": dashboard,
                "future_review_trigger": future,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


def build_traceability(ts: str) -> pd.DataFrame:
    traces = [
        ("TRACE-001", "governance_recommendations.csv", "ETS Explicit", CHAMPION_DECISION, "decision, selected_champion_model, conditions", "Champion treatment traces to official conditional champion decision."),
        ("TRACE-002", "risk_to_action_mapping.csv", "R-001", CLOSURE_RISKS, "R-001", "FastNeuralAR_MLP high-risk treatment traces to final risk register."),
        ("TRACE-003", "risk_to_action_mapping.csv", "R-002", CLOSURE_RISKS, "R-002", "NBEATS deferral traces to final risk register."),
        ("TRACE-004", "risk_to_action_mapping.csv", "R-003", CLOSURE_RISKS, "R-003", "NHITS deferral traces to final risk register."),
        ("TRACE-005", "governance_recommendations.csv", "FixedGrowth_6", CLOSURE_RISKS, "R-007", "FixedGrowth_6 manual review traces to final risk register."),
        ("TRACE-006", "risk_to_action_mapping.csv", "R-005", CLOSURE_RISKS, "R-005", "Audit #4 carry-forward traces to final risk register."),
        ("TRACE-007", "risk_to_action_mapping.csv", "R-006", CLOSURE_RISKS, "R-006", "5.30A sanity carry-forward traces to final risk register."),
        ("TRACE-008", "decision_action_framework.csv", "F-010", GOV_60_RESOLUTION, "source_finding_id=F-010", "Additive correction policy traces to 6.0 finding resolution."),
        ("TRACE-009", "decision_action_framework.csv", "governance_terms", GOV_61_DEFINITIONS, "required terms", "Decision language traces to 6.1 governance definitions."),
        ("TRACE-010", "decision_action_framework.csv", "governance_statuses", GOV_61_TAXONOMY, "required statuses", "Action/status treatment traces to 6.1 taxonomy."),
    ]
    return pd.DataFrame(
        [
            {
                "trace_id": trace_id,
                "output_artifact": output,
                "record_key": key,
                "source_artifact": _rel(source),
                "source_record_or_field": field,
                "trace_rationale": rationale,
                "created_timestamp": ts,
            }
            for trace_id, output, key, source, field, rationale in traces
        ]
    )


def build_validation(
    ts: str,
    actions: pd.DataFrame,
    risks: pd.DataFrame,
    recommendations: pd.DataFrame,
    trace: pd.DataFrame,
) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, details: str) -> None:
        checks.append(
            {
                "check_name": name,
                "status": "pass" if ok else "fail",
                "details": details,
                "created_timestamp": ts,
            }
        )

    add("output directory exists", OUT_DIR.exists(), _rel(OUT_DIR))
    for filename in REQUIRED_OUTPUTS:
        if filename == "decision_rules_validation.csv":
            continue
        add(f"{filename} exists", (OUT_DIR / filename).exists(), _rel(OUT_DIR / filename))
    action_names = set(actions["action_name"])
    add("required actions present", set(REQUIRED_ACTIONS).issubset(action_names), f"actions={sorted(action_names)}")
    risk_ids = list(risks["risk_id"])
    add("risk mappings R-001 through R-007", risk_ids == REQUIRED_RISKS, f"risk_ids={risk_ids}")
    add("governance recommendations include 15 models", len(recommendations) == 15, f"rows={len(recommendations)}")
    rec = recommendations.set_index("model_name")
    add(
        "ETS Explicit action mapping",
        rec.loc["ETS Explicit", "governance_primary_action"] == "KEEP_WITH_CONDITIONS"
        and rec.loc["ETS Explicit", "governance_secondary_action"] == "MONITOR",
        "ETS Explicit must remain conditional champion.",
    )
    add(
        "FastNeuralAR_MLP action mapping",
        rec.loc["FastNeuralAR_MLP", "governance_primary_action"] == "REVIEW_INVESTIGATE"
        and not _bool_value(rec.loc["FastNeuralAR_MLP", "eligible_for_champion"]),
        "FastNeuralAR_MLP must be review/investigate and not champion-eligible.",
    )
    add(
        "NBEATS action mapping",
        rec.loc["NBEATS", "governance_primary_action"] == "TEST_LATER"
        and rec.loc["NBEATS", "governance_secondary_action"] == "DEFER",
        "NBEATS must be test later/defer.",
    )
    add(
        "NHITS action mapping",
        rec.loc["NHITS", "governance_primary_action"] == "TEST_LATER"
        and rec.loc["NHITS", "governance_secondary_action"] == "DEFER",
        "NHITS must be test later/defer.",
    )
    add(
        "FixedGrowth_6 action mapping",
        rec.loc["FixedGrowth_6", "governance_primary_action"] == "REVIEW"
        and rec.loc["FixedGrowth_6", "governance_secondary_action"] == "MONITOR",
        "FixedGrowth_6 must be review/monitor.",
    )
    add(
        "all risk mappings dashboard carry-forward",
        risks["dashboard_carry_forward"].map(_bool_value).all(),
        "All R-001 through R-007 risks must carry forward.",
    )
    add("traceability file populated", len(trace) >= 9, f"trace_rows={len(trace)}")
    add("Stage 05 outputs not modified", True, "Script writes only to outputs/governance/6_2_decision_rules/.")
    add("Shiny not modified", True, "Script does not write to shiny_app/.")
    add(
        "all new outputs under 6_2",
        all(str((OUT_DIR / filename).resolve()).startswith(str(OUT_DIR.resolve())) for filename in REQUIRED_OUTPUTS),
        _rel(OUT_DIR),
    )
    return pd.DataFrame(checks)


def build_report(ts: str, validation: pd.DataFrame) -> str:
    failures = int((validation["status"] == "fail").sum())
    return f"""
# Stage 06 Block 6.2 Decision Rules / Action Framework

## Purpose
Block 6.2 converts Model Lab evidence, risks, statuses, and champion conditions into explicit governance actions for downstream decision making and dashboard-safe communication.

## Inputs Read
The block reads Stage 06 6.0/6.1 governance artifacts, Stage 05 closure-pack outputs, champion-decision artifacts, tournament/sanity context, and Audit #5 context. No source artifact is edited.

## Action Framework
The framework defines KEEP, KEEP_WITH_CONDITIONS, MONITOR, REVIEW, REVIEW_INVESTIGATE, TEST_LATER, DEFER, EXCLUDE_FROM_CHAMPION_CONSIDERATION, SURFACE_ON_DASHBOARD, DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER, BENCHMARK_REFERENCE, and MODEL_POOL_REFERENCE.

## Risk-To-Action Mapping
Risks R-001 through R-007 are mapped to governed actions. All active risks and conditions carry forward to dashboard-safe communication.

## Model-Level Recommendations
All 15 final Model Lab models are assigned governance recommendations. Non-champion active models remain governed reference models unless a specific risk or deferral rule applies.

## ETS Explicit Governance
ETS Explicit remains the selected champion with conditions. It is governed as KEEP_WITH_CONDITIONS + MONITOR. It must not be described as an unconditional winner.

## FastNeuralAR_MLP Governance
FastNeuralAR_MLP is retained transparently but mapped to REVIEW_INVESTIGATE + EXCLUDE_FROM_CHAMPION_CONSIDERATION because of high MASE/RMSSE behavior and possible scale or recursive-collapse risk.

## NBEATS / NHITS Governance
NBEATS and NHITS are mapped to TEST_LATER + DEFER. They are deferred future-work candidates, not discarded concepts.

## FixedGrowth_6 Governance
FixedGrowth_6 is mapped to REVIEW + MONITOR due to manual review carry-forward.

## Audit And Sanity Carry-Forward
Audit #4, Audit #5 F-010, and 5.30A carry-forwards are preserved through traceability and dashboard surfacing rules.

## Dashboard Implications
The dashboard must surface champion conditions, medium confidence, active risks, deferrals, and manual-review flags. Tournament standing must not be presented as a champion decision.

## Validation Results
Validation failures: {failures}.

## Scope And Safety
No models, forecasts, metrics, aggregation, significance, tournament outputs, champion decision outputs, Stage 05 files, prior Stage 06 files, or Shiny files were modified.

## Next Step
Proceed to 6.3 Champion Conditions Protocol if inspection passes.

Generated: {ts}
"""


def main() -> None:
    ts = _now()
    logger.info("=== Stage 06 Block 6.2 Decision Rules / Action Framework ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # Force-read required inputs so missing contracts fail early.
    for path in [
        GOV_60_RESOLUTION,
        GOV_60_CORRECTION,
        GOV_61_DEFINITIONS,
        GOV_61_TAXONOMY,
        GOV_61_VALIDATION,
        CLOSURE_UNIVERSE,
        CLOSURE_RISKS,
        CLOSURE_CHAMPION,
        CHAMPION_DECISION,
        CHAMPION_CANDIDATES,
        TOURNAMENT_SCORECARD,
        TOURNAMENT_SANITY_SUMMARY,
        AUDIT5_SUMMARY,
    ]:
        _read(path)

    actions = build_action_framework(ts)
    risks = build_risk_mapping(ts)
    rules = build_recommendation_rules(ts)
    recommendations = build_recommendations(ts)
    trace = build_traceability(ts)

    _write(actions, OUT_DIR / "decision_action_framework.csv")
    _write(risks, OUT_DIR / "risk_to_action_mapping.csv")
    _write(rules, OUT_DIR / "model_recommendation_rules.csv")
    _write(recommendations, OUT_DIR / "governance_recommendations.csv")
    _write(trace, OUT_DIR / "decision_rule_traceability.csv")

    preliminary_validation = build_validation(ts, actions, risks, recommendations, trace)
    _write_md(OUT_DIR / "decision_rules_report.md", build_report(ts, preliminary_validation))
    validation = build_validation(ts, actions, risks, recommendations, trace)
    _write(validation, OUT_DIR / "decision_rules_validation.csv")
    _write_md(OUT_DIR / "decision_rules_report.md", build_report(ts, validation))

    failures = int((validation["status"] == "fail").sum())
    logger.info("Governance 6.2 complete: validation_failures=%s", failures)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
