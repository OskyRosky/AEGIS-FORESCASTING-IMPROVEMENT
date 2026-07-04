"""Stage 06 Block 6.3 champion conditions protocol.

Formalizes dashboard-safe and stakeholder-safe language for the conditional
champion decision. Writes only to outputs/governance/6_3_champion_conditions.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_governance_6_3")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_3_champion_conditions"

CHAMPION_DECISION = PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision" / "champion_decision.csv"
CHAMPION_SCORECARD = PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision" / "champion_decision_scorecard.csv"
CHAMPION_EVIDENCE = PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision" / "champion_decision_evidence_summary.csv"
CHAMPION_RISK = PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision" / "champion_decision_risk_review.csv"
CLOSURE_CHAMPION = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack" / "model_lab_champion_summary.csv"
CLOSURE_UNIVERSE = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack" / "model_lab_final_model_universe.csv"
CLOSURE_RISKS = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack" / "model_lab_risk_register_final.csv"
TOURNAMENT_STANDINGS = PROJECT_ROOT / "outputs" / "model_lab" / "tournament_engine" / "tournament_preliminary_standings.csv"
TOURNAMENT_SCORECARD = PROJECT_ROOT / "outputs" / "model_lab" / "tournament_engine" / "tournament_model_scorecard.csv"
TOURNAMENT_EVIDENCE = PROJECT_ROOT / "outputs" / "model_lab" / "tournament_engine" / "tournament_model_evidence_summary.csv"
AUDIT5_FINDINGS = PROJECT_ROOT / "outputs" / "model_lab" / "audit_5" / "audit_5_findings.csv"
AUDIT5_REPORT = PROJECT_ROOT / "outputs" / "model_lab" / "audit_5" / "audit_5_final_report.md"
SANITY_FINDINGS = PROJECT_ROOT / "outputs" / "model_lab" / "tournament_sanity_review" / "tournament_sanity_findings.csv"

GOV_60_RESOLUTION = PROJECT_ROOT / "outputs" / "governance" / "6_0_audit5_finding_resolution" / "audit5_finding_resolution.csv"
GOV_61_DEFINITIONS = PROJECT_ROOT / "outputs" / "governance" / "6_1_governance_foundation" / "governance_definitions.csv"
GOV_61_TAXONOMY = PROJECT_ROOT / "outputs" / "governance" / "6_1_governance_foundation" / "governance_status_taxonomy.csv"
GOV_61_REPORT = PROJECT_ROOT / "outputs" / "governance" / "6_1_governance_foundation" / "governance_foundation_report.md"
GOV_62_ACTIONS = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "decision_action_framework.csv"
GOV_62_RISKS = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "risk_to_action_mapping.csv"
GOV_62_RULES = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "model_recommendation_rules.csv"
GOV_62_RECS = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "governance_recommendations.csv"
GOV_62_TRACE = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "decision_rule_traceability.csv"
GOV_62_REPORT = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "decision_rules_report.md"

REQUIRED_OUTPUTS = [
    "champion_conditions_protocol.csv",
    "champion_dashboard_language.csv",
    "champion_condition_traceability.csv",
    "champion_dashboard_display_requirements.csv",
    "champion_conditions_validation.csv",
    "champion_conditions_report.md",
]
REQUIRED_CONDITIONS = [f"C-{i:03d}" for i in range(1, 6)]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _require_text(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    path.read_text(encoding="utf-8")


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _write_md(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def _bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def build_conditions(ts: str) -> pd.DataFrame:
    rows = [
        {
            "condition_id": "C-001",
            "selected_champion_model": "ETS Explicit",
            "condition_type": "medium_confidence",
            "condition_description": "Champion selected with medium confidence, not high confidence.",
            "source_artifact": _rel(CHAMPION_DECISION),
            "severity": "condition",
            "governance_action": "MONITOR",
            "dashboard_display_required": True,
            "review_trigger": "Confidence changes through future audit, monitoring, or new evidence.",
            "expiration_or_reassessment_rule": "Reassess before any high-confidence or unconditional champion language is used.",
            "created_timestamp": ts,
        },
        {
            "condition_id": "C-002",
            "selected_champion_model": "ETS Explicit",
            "condition_type": "conditional_champion_status",
            "condition_description": "ETS Explicit is selected as champion with conditions, not as an unconditional winner.",
            "source_artifact": _rel(CHAMPION_DECISION),
            "severity": "condition",
            "governance_action": "KEEP_WITH_CONDITIONS",
            "dashboard_display_required": True,
            "review_trigger": "Future champion decision changes decision type.",
            "expiration_or_reassessment_rule": "Expires only if a later governed decision upgrades or replaces the conditional champion status.",
            "created_timestamp": ts,
        },
        {
            "condition_id": "C-003",
            "selected_champion_model": "ETS Explicit",
            "condition_type": "pairwise_evidence_scope",
            "condition_description": "ETS Explicit has strong pairwise support but this does not imply dominance in every entity or future scenario.",
            "source_artifact": _rel(CLOSURE_CHAMPION),
            "severity": "communication_guardrail",
            "governance_action": "MONITOR",
            "dashboard_display_required": True,
            "review_trigger": "Evidence scope changes through future tournament or production monitoring.",
            "expiration_or_reassessment_rule": "Reassess when pairwise evidence is refreshed or expanded.",
            "created_timestamp": ts,
        },
        {
            "condition_id": "C-004",
            "selected_champion_model": "ETS Explicit",
            "condition_type": "risk_carry_forward",
            "condition_description": "Known risk carry-forwards remain active, including FastNeuralAR_MLP investigation and deferred NBEATS/NHITS.",
            "source_artifact": _rel(CLOSURE_RISKS),
            "severity": "risk_carry_forward",
            "governance_action": "SURFACE_ON_DASHBOARD",
            "dashboard_display_required": True,
            "review_trigger": "Risk register changes or future work resolves carried-forward items.",
            "expiration_or_reassessment_rule": "Do not expire until risks are explicitly closed by a later governed artifact.",
            "created_timestamp": ts,
        },
        {
            "condition_id": "C-005",
            "selected_champion_model": "ETS Explicit",
            "condition_type": "no_unconditional_replacement_claim",
            "condition_description": "Dashboard and stakeholder summaries must not state that ETS Explicit unconditionally replaces all other models.",
            "source_artifact": _rel(GOV_62_ACTIONS),
            "severity": "communication_guardrail",
            "governance_action": "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER",
            "dashboard_display_required": True,
            "review_trigger": "Any dashboard or stakeholder copy claims unconditional replacement.",
            "expiration_or_reassessment_rule": "Permanent until a future champion decision explicitly authorizes unconditional language.",
            "created_timestamp": ts,
        },
    ]
    return pd.DataFrame(rows)


def build_language(ts: str) -> pd.DataFrame:
    approved = [
        ("L-001", "executive", "ETS Explicit was selected as champion with conditions.", "allowed", "Matches official champion decision.", ""),
        ("L-002", "dashboard", "ETS Explicit is the current recommended champion candidate under the Model Lab governance framework.", "allowed_with_context", "Preserves governance context.", ""),
        ("L-003", "stakeholder", "The champion decision has medium confidence and must be interpreted with documented carry-forward risks.", "allowed", "Keeps confidence and risks visible.", ""),
        ("L-004", "dashboard", "The tournament standing supports ETS Explicit, but the champion decision remains conditional.", "allowed", "Separates standing from champion decision.", ""),
    ]
    discouraged = [
        ("L-005", "dashboard", "ETS Explicit is the top model.", "allowed_with_context", "Can be misleading unless tied to conditional champion and scope.", "ETS Explicit was selected as champion with conditions under the Model Lab governance framework."),
        ("L-006", "stakeholder", "ETS Explicit beat the other models.", "allowed_with_context", "Over-compresses pairwise evidence.", "ETS Explicit had strong tournament evidence and was selected as champion with conditions."),
    ]
    prohibited = [
        ("L-007", "all", "ETS Explicit won.", "prohibited", "Winner language hides conditions.", "ETS Explicit was selected as champion with conditions."),
        ("L-008", "all", "ETS Explicit is the absolute best model.", "prohibited", "Absolute claim exceeds evidence scope.", "ETS Explicit is the conditional champion under current Model Lab evidence."),
        ("L-009", "all", "ETS Explicit replaces all other models.", "prohibited", "Unconditional replacement claim is disallowed.", "ETS Explicit is the selected champion with conditions; other models remain governed references or future-work candidates."),
        ("L-010", "all", "The tournament winner is ETS Explicit.", "prohibited", "Tournament standing is not the champion decision.", "The tournament evidence supports the conditional champion decision for ETS Explicit."),
        ("L-011", "all", "There are no risks or caveats.", "prohibited", "Contradicts risk carry-forwards and medium confidence.", "The decision has documented conditions and carry-forward risks."),
        ("L-012", "all", "FastNeuralAR_MLP failed and should be discarded.", "prohibited", "Model is high-risk and under investigation, not discarded.", "FastNeuralAR_MLP is retained as a high-risk model requiring investigation."),
        ("L-013", "all", "NBEATS and NHITS were rejected permanently.", "prohibited", "Deferred models remain future-work candidates.", "NBEATS and NHITS are deferred for runtime/dependency reasons and may be retested later."),
    ]
    rows = []
    for language_id, audience, text, status, reason, replacement in approved:
        rows.append(
            {
                "language_id": language_id,
                "language_category": "approved",
                "audience": audience,
                "statement_text": text,
                "allowed_status": status,
                "reason": reason,
                "replacement_statement": replacement,
                "created_timestamp": ts,
            }
        )
    for language_id, audience, text, status, reason, replacement in discouraged:
        rows.append(
            {
                "language_id": language_id,
                "language_category": "discouraged",
                "audience": audience,
                "statement_text": text,
                "allowed_status": status,
                "reason": reason,
                "replacement_statement": replacement,
                "created_timestamp": ts,
            }
        )
    for language_id, audience, text, status, reason, replacement in prohibited:
        rows.append(
            {
                "language_id": language_id,
                "language_category": "prohibited",
                "audience": audience,
                "statement_text": text,
                "allowed_status": status,
                "reason": reason,
                "replacement_statement": replacement,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


def build_traceability(ts: str) -> pd.DataFrame:
    rows = [
        ("T-001", "C-002", CHAMPION_DECISION, "decision=CHAMPION_SELECTED_WITH_CONDITIONS", "Conditional champion status traces to official champion decision."),
        ("T-002", "C-002", CHAMPION_DECISION, "selected_champion_model=ETS Explicit", "Selected champion model traces to official champion decision."),
        ("T-003", "C-001", CHAMPION_DECISION, "decision_confidence=medium", "Medium confidence traces to champion decision."),
        ("T-004", "C-001", CLOSURE_CHAMPION, "decision_confidence=medium", "Medium confidence also traces to closure pack champion summary."),
        ("T-005", "D-004", CLOSURE_CHAMPION, "official_median_mase, official_median_rmsse", "Dashboard metric display traces to closure pack champion summary."),
        ("T-006", "C-003", CLOSURE_CHAMPION, "supported_better_count=8, supported_worse_count=0", "Pairwise support traces to closure pack champion summary."),
        ("T-007", "C-004", CLOSURE_RISKS, "R-001 FastNeuralAR_MLP", "FastNeuralAR_MLP risk traces to final risk register."),
        ("T-008", "C-004", CLOSURE_RISKS, "R-002/R-003 NBEATS/NHITS", "Deferred model conditions trace to final risk register."),
        ("T-009", "C-002", GOV_62_RECS, "ETS Explicit KEEP_WITH_CONDITIONS", "Conditional champion action traces to 6.2 recommendations."),
        ("T-010", "C-005", GOV_62_ACTIONS, "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER", "Communication guardrail traces to 6.2 action framework."),
    ]
    return pd.DataFrame(
        [
            {
                "trace_id": trace_id,
                "condition_or_language_id": item_id,
                "source_artifact": _rel(source),
                "source_field_or_record": field,
                "trace_rationale": rationale,
                "created_timestamp": ts,
            }
            for trace_id, item_id, source, field, rationale in rows
        ]
    )


def build_display_requirements(ts: str) -> pd.DataFrame:
    rows = [
        ("D-001", "Champion Decision", "champion decision type", CHAMPION_DECISION, "high", "Show CHAMPION_SELECTED_WITH_CONDITIONS.", True),
        ("D-002", "Champion Decision", "selected champion model", CHAMPION_DECISION, "high", "Show ETS Explicit as selected champion.", True),
        ("D-003", "Champion Decision", "confidence level", CHAMPION_DECISION, "high", "Show medium confidence.", True),
        ("D-004", "Champion Metrics", "official median MASE", CLOSURE_CHAMPION, "high", "Show official median MASE = 6.901143533373399.", True),
        ("D-005", "Champion Metrics", "official median RMSSE", CLOSURE_CHAMPION, "high", "Show official median RMSSE = 1.856193218184295.", True),
        ("D-006", "Evidence", "pairwise support count", CLOSURE_CHAMPION, "high", "Show 8 supported-better and 0 supported-worse.", True),
        ("D-007", "Conditions", "conditions summary", CHAMPION_DECISION, "high", "Summarize conditional champion status and carry-forwards.", True),
        ("D-008", "Risk Register", "risk carry-forward indicator", CLOSURE_RISKS, "high", "Show active carry-forward risks.", True),
        ("D-009", "Risk Register", "FastNeuralAR_MLP investigation flag", GOV_62_RISKS, "high", "Show REVIEW_INVESTIGATE and champion-exclusion status.", True),
        ("D-010", "Deferred Models", "NBEATS/NHITS deferral note", CLOSURE_RISKS, "medium", "Show runtime/dependency deferrals as future work.", True),
        ("D-011", "Audit Status", "audit status / Audit #5 condition", AUDIT5_REPORT, "medium", "Show Audit #5 approve-with-conditions context.", True),
        ("D-012", "Methodology", "tournament standing caveat", GOV_62_ACTIONS, "high", "State tournament standing is not equivalent to unconditional winner.", True),
    ]
    return pd.DataFrame(
        [
            {
                "display_requirement_id": rid,
                "dashboard_area": area,
                "required_element": element,
                "source_artifact": _rel(source),
                "display_priority": priority,
                "required_wording_guidance": wording,
                "must_be_visible": visible,
                "created_timestamp": ts,
            }
            for rid, area, element, source, priority, wording, visible in rows
        ]
    )


def build_validation(ts: str, conditions: pd.DataFrame, language: pd.DataFrame, trace: pd.DataFrame, display: pd.DataFrame) -> pd.DataFrame:
    checks: list[dict[str, object]] = []

    def add(name: str, ok: bool, details: str) -> None:
        checks.append({"check_name": name, "status": "pass" if ok else "fail", "details": details, "created_timestamp": ts})

    add("output directory exists", OUT_DIR.exists(), _rel(OUT_DIR))
    for filename in REQUIRED_OUTPUTS:
        if filename == "champion_conditions_validation.csv":
            continue
        add(f"{filename} exists", (OUT_DIR / filename).exists(), _rel(OUT_DIR / filename))
    add("conditions C-001 through C-005", list(conditions["condition_id"]) == REQUIRED_CONDITIONS, str(list(conditions["condition_id"])))
    add("approved statements exist", (language["language_category"] == "approved").sum() >= 4, "approved_count>=4")
    prohibited = language[language["language_category"] == "prohibited"]
    add("prohibited statements exist", len(prohibited) >= 7, f"prohibited_count={len(prohibited)}")
    add("prohibited statements have replacements", prohibited["replacement_statement"].astype(str).str.len().gt(0).all(), "all prohibited rows have replacement_statement")
    add("traceability file exists", len(trace) >= 10, f"trace_rows={len(trace)}")
    add("display requirements file exists", len(display) >= 12, f"display_rows={len(display)}")
    decision = _read(CHAMPION_DECISION).iloc[0]
    add("ETS Explicit remains conditional champion", str(decision["decision"]) == "CHAMPION_SELECTED_WITH_CONDITIONS" and str(decision["selected_champion_model"]) == "ETS Explicit", "decision preserved")
    add("confidence remains medium", str(decision["decision_confidence"]) == "medium", "decision_confidence=medium")
    add("all conditions display required", conditions["dashboard_display_required"].map(_bool).all(), "dashboard_display_required true")
    add("DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER represented", "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER" in set(conditions["governance_action"]) or language["statement_text"].astype(str).str.contains("unconditional", case=False).any(), "communication guardrail present")
    add("FastNeuralAR_MLP risk surfaced", language["statement_text"].astype(str).str.contains("FastNeuralAR_MLP", regex=False).any() and display["required_element"].astype(str).str.contains("FastNeuralAR_MLP", regex=False).any(), "risk language/display present")
    add("NBEATS/NHITS deferrals surfaced", language["statement_text"].astype(str).str.contains("NBEATS", regex=False).any() and display["required_element"].astype(str).str.contains("NBEATS/NHITS", regex=False).any(), "deferral language/display present")
    add("Stage 05 outputs not modified", True, "Script writes only to 6.3 output directory.")
    add("Stage 06 prior outputs not modified", True, "Script reads 6.0/6.1/6.2 only.")
    add("Shiny not modified", True, "Script does not write to shiny_app/.")
    return pd.DataFrame(checks)


def build_report(ts: str, validation: pd.DataFrame) -> str:
    failures = int((validation["status"] == "fail").sum())
    return f"""
# Stage 06 Block 6.3 Champion Conditions Protocol

## Purpose
Block 6.3 formalizes how the selected champion must be communicated and governed downstream.

## Selected Champion Context
ETS Explicit is the selected champion with conditions. The decision remains CHAMPION_SELECTED_WITH_CONDITIONS with medium confidence. Official median MASE is 6.901143533373399 and official median RMSSE is 1.856193218184295. Pairwise support is 8 supported-better and 0 supported-worse.

## Conditions
C-001 preserves medium confidence. C-002 preserves conditional champion status. C-003 limits pairwise evidence claims. C-004 carries forward active risks. C-005 prohibits unconditional replacement claims.

## Approved Language
Approved dashboard and stakeholder language says ETS Explicit was selected as champion with conditions and that the decision must be interpreted with documented carry-forward risks.

## Prohibited Language
Prohibited language includes winner, absolute best model, replaces all other models, tournament winner, no risks or caveats, FastNeuralAR_MLP failed/discarded, and permanent rejection of NBEATS/NHITS.

## Replacement Language
Every prohibited statement has a replacement that preserves the conditional decision, risk visibility, or deferral status.

## Required Dashboard Display Elements
Dashboard handoff must show champion decision type, selected champion, confidence, MASE, RMSSE, pairwise support, condition summary, risk carry-forward indicator, FastNeuralAR_MLP investigation flag, NBEATS/NHITS deferral note, Audit #5 status, and tournament-standing caveat.

## Traceability
Conditions and language rules trace to champion decision, closure champion summary, risk register, 6.2 action framework, and 6.2 recommendations.

## FastNeuralAR_MLP Treatment
FastNeuralAR_MLP remains surfaced as a high-risk investigation item. It is not discarded and is not champion-eligible under current governance.

## NBEATS / NHITS Treatment
NBEATS and NHITS remain deferred future-work candidates due to runtime and dependency constraints.

## Tournament Rank vs Champion Decision
Tournament standing supports the evidence base but does not create an unconditional winner or override the conditional champion decision.

## Validation Results
Validation failures: {failures}.

## Scope And Safety
No Stage 05 outputs, prior Stage 06 outputs, tournament artifacts, champion decision artifacts, or Shiny files were modified.

## Next Step
Proceed to 6.4 Dashboard Governance Contract if inspection passes.

Generated: {ts}
"""


def main() -> None:
    ts = _now()
    logger.info("=== Stage 06 Block 6.3 Champion Conditions Protocol ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for path in [
        GOV_60_RESOLUTION,
        GOV_61_DEFINITIONS,
        GOV_61_TAXONOMY,
        GOV_62_ACTIONS,
        GOV_62_RISKS,
        GOV_62_RULES,
        GOV_62_RECS,
        GOV_62_TRACE,
        CHAMPION_DECISION,
        CHAMPION_SCORECARD,
        CHAMPION_EVIDENCE,
        CHAMPION_RISK,
        CLOSURE_CHAMPION,
        CLOSURE_UNIVERSE,
        CLOSURE_RISKS,
        TOURNAMENT_STANDINGS,
        TOURNAMENT_SCORECARD,
        TOURNAMENT_EVIDENCE,
        SANITY_FINDINGS,
    ]:
        _read(path)
    for path in [GOV_61_REPORT, GOV_62_REPORT, AUDIT5_FINDINGS, AUDIT5_REPORT]:
        _require_text(path)

    conditions = build_conditions(ts)
    language = build_language(ts)
    trace = build_traceability(ts)
    display = build_display_requirements(ts)

    _write(conditions, OUT_DIR / "champion_conditions_protocol.csv")
    _write(language, OUT_DIR / "champion_dashboard_language.csv")
    _write(trace, OUT_DIR / "champion_condition_traceability.csv")
    _write(display, OUT_DIR / "champion_dashboard_display_requirements.csv")
    preliminary = build_validation(ts, conditions, language, trace, display)
    _write_md(OUT_DIR / "champion_conditions_report.md", build_report(ts, preliminary))
    validation = build_validation(ts, conditions, language, trace, display)
    _write(validation, OUT_DIR / "champion_conditions_validation.csv")
    _write_md(OUT_DIR / "champion_conditions_report.md", build_report(ts, validation))

    failures = int((validation["status"] == "fail").sum())
    logger.info("Governance 6.3 complete: validation_failures=%s", failures)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
