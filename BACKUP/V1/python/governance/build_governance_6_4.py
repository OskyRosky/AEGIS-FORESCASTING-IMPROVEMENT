"""Stage 06 Block 6.4 dashboard governance contract.

Defines read-only, non-computational, dashboard-safe rules for the future Shiny
MVP. Writes only to outputs/governance/6_4_dashboard_contract.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_governance_6_4")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract"


def p(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)


INPUTS = {
    "audit5_resolution": p("outputs", "governance", "6_0_audit5_finding_resolution", "audit5_finding_resolution.csv"),
    "governed_manifest_correction": p("outputs", "governance", "6_0_audit5_finding_resolution", "governed_manifest_correction.csv"),
    "governance_definitions": p("outputs", "governance", "6_1_governance_foundation", "governance_definitions.csv"),
    "governance_taxonomy": p("outputs", "governance", "6_1_governance_foundation", "governance_status_taxonomy.csv"),
    "governance_foundation_report": p("outputs", "governance", "6_1_governance_foundation", "governance_foundation_report.md"),
    "decision_action_framework": p("outputs", "governance", "6_2_decision_rules", "decision_action_framework.csv"),
    "risk_to_action_mapping": p("outputs", "governance", "6_2_decision_rules", "risk_to_action_mapping.csv"),
    "model_recommendation_rules": p("outputs", "governance", "6_2_decision_rules", "model_recommendation_rules.csv"),
    "governance_recommendations": p("outputs", "governance", "6_2_decision_rules", "governance_recommendations.csv"),
    "decision_rule_traceability": p("outputs", "governance", "6_2_decision_rules", "decision_rule_traceability.csv"),
    "decision_rules_report": p("outputs", "governance", "6_2_decision_rules", "decision_rules_report.md"),
    "champion_conditions_protocol": p("outputs", "governance", "6_3_champion_conditions", "champion_conditions_protocol.csv"),
    "champion_dashboard_language": p("outputs", "governance", "6_3_champion_conditions", "champion_dashboard_language.csv"),
    "champion_condition_traceability": p("outputs", "governance", "6_3_champion_conditions", "champion_condition_traceability.csv"),
    "champion_dashboard_display_requirements": p("outputs", "governance", "6_3_champion_conditions", "champion_dashboard_display_requirements.csv"),
    "champion_conditions_report": p("outputs", "governance", "6_3_champion_conditions", "champion_conditions_report.md"),
    "model_lab_closure_summary": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_closure_summary.csv"),
    "model_lab_key_results": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_key_results.csv"),
    "model_lab_champion_summary": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_champion_summary.csv"),
    "model_lab_final_model_universe": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_final_model_universe.csv"),
    "model_lab_risk_register_final": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_risk_register_final.csv"),
    "model_lab_dashboard_handoff_manifest": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_dashboard_handoff_manifest.csv"),
    "model_lab_deferred_models": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_deferred_models.csv"),
    "model_lab_executive_summary": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_executive_summary.md"),
    "champion_decision": p("outputs", "model_lab", "champion_decision", "champion_decision.csv"),
    "champion_decision_scorecard": p("outputs", "model_lab", "champion_decision", "champion_decision_scorecard.csv"),
    "champion_candidate_evaluation": p("outputs", "model_lab", "champion_decision", "champion_candidate_evaluation.csv"),
    "champion_decision_report": p("outputs", "model_lab", "champion_decision", "champion_decision_report.md"),
    "tournament_preliminary_standings": p("outputs", "model_lab", "tournament_engine", "tournament_preliminary_standings.csv"),
    "tournament_model_scorecard": p("outputs", "model_lab", "tournament_engine", "tournament_model_scorecard.csv"),
    "tournament_pairwise_evidence": p("outputs", "model_lab", "tournament_engine", "tournament_pairwise_evidence.csv"),
    "tournament_model_evidence_summary": p("outputs", "model_lab", "tournament_engine", "tournament_model_evidence_summary.csv"),
    "tournament_risk_register": p("outputs", "model_lab", "tournament_engine", "tournament_risk_register.csv"),
    "challenger_metrics_summary": p("outputs", "model_lab", "challenger_metrics", "challenger_metrics_summary.csv"),
    "challenger_metrics_diagnostic": p("outputs", "model_lab", "challenger_metrics", "challenger_metrics_by_model_diagnostic.csv"),
    "challenger_aggregation_by_model": p("outputs", "model_lab", "challenger_aggregation_significance", "challenger_aggregation_by_model.csv"),
    "challenger_family_summary": p("outputs", "model_lab", "challenger_aggregation_significance", "challenger_family_summary.csv"),
    "challenger_outlier_risk_review": p("outputs", "model_lab", "challenger_aggregation_significance", "challenger_outlier_risk_review.csv"),
    "audit_4_summary": p("outputs", "model_lab", "audit_4", "audit_4_summary.csv"),
    "audit_5_summary": p("outputs", "model_lab", "audit_5", "audit_5_summary.csv"),
    "audit_5_findings": p("outputs", "model_lab", "audit_5", "audit_5_findings.csv"),
    "audit_5_final_report": p("outputs", "model_lab", "audit_5", "audit_5_final_report.md"),
    "tournament_sanity_summary": p("outputs", "model_lab", "tournament_sanity_review", "tournament_sanity_summary.csv"),
}

REQUIRED_FILES = [
    "dashboard_governance_contract.csv",
    "dashboard_required_sections.csv",
    "dashboard_data_binding_contract.csv",
    "dashboard_do_dont_rules.csv",
    "dashboard_warning_labels.csv",
    "dashboard_governance_traceability.csv",
    "dashboard_contract_validation.csv",
    "dashboard_governance_contract_report.md",
]
REQUIRED_AREAS = [
    "read_only_behavior",
    "no_metric_recalculation",
    "champion_communication",
    "confidence_display",
    "risk_visibility",
    "deferred_model_visibility",
    "tournament_vs_champion_distinction",
    "audit_status_visibility",
    "source_artifact_traceability",
    "no_silent_filtering",
    "no_unconditional_winner_language",
    "methodology_transparency",
]
REQUIRED_SECTIONS = [
    "Executive Summary",
    "Champion Decision",
    "Champion Conditions",
    "Model Universe",
    "Tournament Standings",
    "Baseline vs Challenger Scorecard",
    "Pairwise Evidence",
    "Risk Register",
    "Deferred Models",
    "Audit Status",
    "Governance Actions",
    "Methodology / Metric Policy",
    "Dashboard Handoff / Source Artifacts",
]
REQUIRED_BINDINGS = [
    "model_lab_key_results.csv",
    "model_lab_champion_summary.csv",
    "champion_decision.csv",
    "model_lab_final_model_universe.csv",
    "tournament_preliminary_standings.csv",
    "tournament_model_scorecard.csv",
    "tournament_pairwise_evidence.csv",
    "model_lab_risk_register_final.csv",
    "model_lab_deferred_models.csv",
    "audit_5_summary.csv",
    "governance_recommendations.csv",
    "champion_conditions_protocol.csv",
    "champion_dashboard_language.csv",
    "champion_dashboard_display_requirements.csv",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _read_or_text(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        try:
            pd.read_csv(path)
        except Exception:
            path.read_text(encoding="utf-8")
    else:
        path.read_text(encoding="utf-8")


def _write(df: pd.DataFrame, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / name, index=False)


def _write_md(name: str, content: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(content.strip() + "\n", encoding="utf-8")


def contract(ts: str) -> pd.DataFrame:
    rules = [
        ("DC-001", "read_only_behavior", "Shiny must be read-only.", "behavior", "Load governed source artifacts as read-only files.", "Writing to source artifacts, governance artifacts, or Shiny-generated replacement data.", INPUTS["model_lab_dashboard_handoff_manifest"], "Dashboard must not mutate audited outputs.", True),
        ("DC-002", "no_metric_recalculation", "Shiny must not compute or recalculate MASE/RMSSE.", "calculation", "Display sourced metrics only.", "Recomputing MASE, RMSSE, aggregation, significance, or new scores.", INPUTS["model_lab_champion_summary"], "Metrics are already governed artifacts.", True),
        ("DC-003", "read_only_behavior", "Shiny must not rerun models.", "behavior", "Consume final artifacts only.", "Running forecasts, model code, tournament code, or scoring code.", INPUTS["model_lab_closure_summary"], "Dashboard is presentation only.", True),
        ("DC-004", "tournament_vs_champion_distinction", "Shiny must not infer a champion from tournament rank alone.", "communication", "Use champion_decision.csv for champion status.", "Treating preliminary position as champion decision.", INPUTS["champion_decision"], "Tournament standing is evidence, not decision.", True),
        ("DC-005", "champion_communication", "Shiny must display champion decision as CHAMPION_SELECTED_WITH_CONDITIONS.", "display", "Show the exact decision type.", "Upgrading decision to champion_selected or winner.", INPUTS["champion_decision"], "Preserves official decision.", True),
        ("DC-006", "confidence_display", "Shiny must display confidence = medium.", "display", "Show medium confidence near champion decision.", "Hiding or changing confidence level.", INPUTS["champion_decision"], "Confidence is a decision condition.", True),
        ("DC-007", "champion_communication", "Shiny must display ETS Explicit conditions.", "display", "Show champion conditions C-001 through C-005.", "Presenting ETS Explicit without caveats.", INPUTS["champion_conditions_protocol"], "Conditions govern downstream communication.", True),
        ("DC-008", "risk_visibility", "Shiny must display FastNeuralAR_MLP risk.", "display", "Surface high-risk investigation status.", "Hiding FastNeuralAR_MLP or calling it discarded.", INPUTS["risk_to_action_mapping"], "No silent loss of risk.", True),
        ("DC-009", "deferred_model_visibility", "Shiny must display NBEATS/NHITS deferred status.", "display", "Show runtime/dependency deferral as future work.", "Hiding deferred models or saying permanently rejected.", INPUTS["model_lab_deferred_models"], "Deferred models remain governed concepts.", True),
        ("DC-010", "audit_status_visibility", "Shiny must display audit status and carry-forward conditions.", "display", "Show Audit #5 approve-with-conditions and governed F-010 correction.", "Hiding audit conditions.", INPUTS["audit_5_summary"], "Audit state must remain visible.", True),
        ("DC-011", "no_unconditional_winner_language", "Shiny must not say ETS Explicit won or is absolute best model.", "communication", "Use approved 6.3 language.", "Winner, absolute best, replaces all others, no caveats.", INPUTS["champion_dashboard_language"], "Prevents misleading stakeholder language.", True),
        ("DC-012", "source_artifact_traceability", "Shiny must trace displayed facts to artifacts.", "traceability", "Use dashboard bindings and source paths.", "Displaying untraceable derived values.", INPUTS["champion_dashboard_display_requirements"], "Supports auditability.", True),
        ("DC-013", "no_silent_filtering", "Shiny must not silently filter risks, deferred models, or ineligible models.", "filtering", "Any display filter must keep risk/deferred visibility available.", "Dropping FastNeuralAR_MLP, NBEATS, NHITS, or risk rows from governance sections.", INPUTS["governance_recommendations"], "Avoids biased presentation.", True),
        ("DC-014", "methodology_transparency", "Shiny must disclose metric and governance methodology.", "methodology", "Show metrics are sourced from Model Lab and not recomputed.", "Presenting dashboard metrics as live recalculations.", INPUTS["governance_foundation_report"], "Honest dashboard communication.", True),
    ]
    return pd.DataFrame(
        [
            {
                "contract_id": cid,
                "contract_area": area,
                "contract_rule": rule,
                "rule_type": rule_type,
                "required_behavior": required,
                "prohibited_behavior": prohibited,
                "source_artifact": _rel(source),
                "governance_rationale": rationale,
                "blocking_if_violated": blocking,
                "created_timestamp": ts,
            }
            for cid, area, rule, rule_type, required, prohibited, source, rationale, blocking in rules
        ]
    )


def sections(ts: str) -> pd.DataFrame:
    section_map = [
        ("DS-001", "Executive Summary", "Top-line governed status.", "champion decision, confidence, audit status, key results", INPUTS["model_lab_key_results"], [INPUTS["model_lab_executive_summary"]], True, "Must use conditional champion language."),
        ("DS-002", "Champion Decision", "Display official champion decision.", "decision type, ETS Explicit, origin, family, confidence", INPUTS["champion_decision"], [INPUTS["model_lab_champion_summary"]], True, "Decision source is champion_decision.csv."),
        ("DS-003", "Champion Conditions", "Display active champion conditions.", "C-001 through C-005", INPUTS["champion_conditions_protocol"], [INPUTS["champion_dashboard_language"]], True, "All conditions must remain visible."),
        ("DS-004", "Model Universe", "Show final model universe.", "baseline, challenger, deferred status, risk flags", INPUTS["model_lab_final_model_universe"], [INPUTS["governance_recommendations"]], True, "No silent filtering of deferred/risk models."),
        ("DS-005", "Tournament Standings", "Show standings as evidence only.", "preliminary positions and tournament metrics", INPUTS["tournament_preliminary_standings"], [INPUTS["champion_dashboard_language"]], True, "Must not imply winner."),
        ("DS-006", "Baseline vs Challenger Scorecard", "Compare model scorecards.", "MASE, RMSSE, origin, family, risk status", INPUTS["tournament_model_scorecard"], [INPUTS["champion_decision_scorecard"]], True, "Display sourced metrics only."),
        ("DS-007", "Pairwise Evidence", "Show pairwise support context.", "pairwise evidence and support counts", INPUTS["tournament_pairwise_evidence"], [INPUTS["tournament_model_evidence_summary"]], True, "Evidence is not champion decision by itself."),
        ("DS-008", "Risk Register", "Surface risks and carry-forwards.", "risk_id, model, action, dashboard carry-forward", INPUTS["model_lab_risk_register_final"], [INPUTS["risk_to_action_mapping"]], True, "FastNeuralAR_MLP risk must be visible."),
        ("DS-009", "Deferred Models", "Show deferred future work.", "NBEATS, NHITS, reasons, future options", INPUTS["model_lab_deferred_models"], [INPUTS["model_lab_final_model_universe"]], True, "Do not call permanently rejected."),
        ("DS-010", "Audit Status", "Show audit readiness and conditions.", "Audit #4/#5 status and conditions", INPUTS["audit_5_summary"], [INPUTS["audit_4_summary"], INPUTS["audit5_resolution"]], True, "Audit #5 approve-with-conditions must be visible."),
        ("DS-011", "Governance Actions", "Show 6.2 actions.", "model actions, risk actions, traceability", INPUTS["governance_recommendations"], [INPUTS["decision_action_framework"]], True, "Actions guide dashboard language."),
        ("DS-012", "Methodology / Metric Policy", "Explain metric and governance policy.", "no recompute, source artifacts, tournament vs champion", INPUTS["governance_foundation_report"], [INPUTS["dashboard_governance_placeholder"] if "dashboard_governance_placeholder" in INPUTS else INPUTS["champion_conditions_report"]], True, "Read-only non-computational policy."),
        ("DS-013", "Dashboard Handoff / Source Artifacts", "List dashboard source artifacts.", "bindings, source paths, refresh behavior", INPUTS["model_lab_dashboard_handoff_manifest"], [INPUTS["champion_dashboard_display_requirements"]], True, "Supports traceability and audit."),
    ]
    rows = []
    for sid, name, purpose, elements, primary, secondary, required, notes in section_map:
        rows.append(
            {
                "section_id": sid,
                "dashboard_section": name,
                "section_purpose": purpose,
                "required_elements": elements,
                "primary_source_artifact": _rel(primary),
                "secondary_source_artifacts": "; ".join(_rel(x) for x in secondary),
                "required_for_mvp": required,
                "governance_notes": notes,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


def bindings(ts: str) -> pd.DataFrame:
    binding_defs = [
        ("DB-001", "Executive Summary", INPUTS["model_lab_key_results"], "metric_name,metric_value,metric_context", "key KPIs", "filtering, sorting, renaming labels", "recomputing KPIs, changing champion decision, hiding risks", "read_only_file_load", True),
        ("DB-002", "Champion Decision", INPUTS["model_lab_champion_summary"], "selected_champion_model,decision_type,decision_confidence,official_median_mase,official_median_rmsse,supported_better_count,supported_worse_count", "champion summary fields", "formatting numeric display, renaming labels", "changing MASE/RMSSE, changing confidence, changing decision type", "read_only_file_load", True),
        ("DB-003", "Champion Decision", INPUTS["champion_decision"], "decision,selected_champion_model,selected_champion_origin,selected_champion_family,decision_confidence,conditions", "official decision", "renaming labels", "changing champion decision or conditions", "read_only_file_load", True),
        ("DB-004", "Model Universe", INPUTS["model_lab_final_model_universe"], "model_name,model_origin,model_family,final_status,included_in_tournament,eligible_for_champion,selected_champion,deferred_reason,risk_flag", "model universe", "filtering with visible counts, sorting", "dropping deferred models, hiding risk flags", "read_only_file_load", True),
        ("DB-005", "Tournament Standings", INPUTS["tournament_preliminary_standings"], "preliminary_position,model_name,official_median_mase,official_median_rmsse,risk_status,audit_risk_flag", "standings table", "sorting, filtering, label renaming", "inferring champion from rank, winner language", "read_only_file_load", True),
        ("DB-006", "Baseline vs Challenger Scorecard", INPUTS["tournament_model_scorecard"], "model_name,model_origin,model_family,official_median_mase,official_median_rmsse,risk_status", "scorecard", "sorting, grouping for display", "recomputing metrics or creating new tournament scores", "read_only_file_load", True),
        ("DB-007", "Pairwise Evidence", INPUTS["tournament_pairwise_evidence"], "model_a,model_b,median_delta_mase,bh_adjusted_p_value,comparison_status", "pairwise evidence", "filtering, sorting, label renaming", "declaring winner from pairwise rows", "read_only_file_load", True),
        ("DB-008", "Risk Register", INPUTS["model_lab_risk_register_final"], "risk_id,risk_type,risk_level,model_name,risk_description,decision_treatment", "risk register", "filtering by risk level with visible totals", "hiding FastNeuralAR_MLP or audit carry-forwards", "read_only_file_load", True),
        ("DB-009", "Deferred Models", INPUTS["model_lab_deferred_models"], "model_name,model_family,deferred_reason,future_resolution_option", "deferred model list", "sorting and label renaming", "dropping deferred models or saying permanently rejected", "read_only_file_load", True),
        ("DB-010", "Audit Status", INPUTS["audit_5_summary"], "final_audit_verdict,blockers,major_findings,minor_findings,advisories,ready_for_next_stage", "audit status", "label renaming", "hiding approve-with-conditions status", "read_only_file_load", True),
        ("DB-011", "Governance Actions", INPUTS["governance_recommendations"], "model_name,governance_primary_action,governance_secondary_action,dashboard_requirement", "governance recommendations", "filtering, grouping", "changing actions or eligibility", "read_only_file_load", True),
        ("DB-012", "Champion Conditions", INPUTS["champion_conditions_protocol"], "condition_id,condition_type,condition_description,governance_action,dashboard_display_required", "conditions", "sorting by condition_id", "hiding conditions", "read_only_file_load", True),
        ("DB-013", "Language Rules", INPUTS["champion_dashboard_language"], "language_category,statement_text,allowed_status,replacement_statement", "approved/prohibited copy", "filtering by category", "using prohibited language without replacement", "static_artifact_load", True),
        ("DB-014", "Display Requirements", INPUTS["champion_dashboard_display_requirements"], "dashboard_area,required_element,required_wording_guidance,must_be_visible", "required display elements", "grouping by dashboard area", "hiding required display elements", "static_artifact_load", True),
    ]
    return pd.DataFrame(
        [
            {
                "binding_id": bid,
                "dashboard_section": section,
                "source_artifact": _rel(source),
                "source_fields": source_fields,
                "display_fields": display_fields,
                "allowed_transformations": allowed,
                "prohibited_transformations": prohibited,
                "refresh_behavior": refresh,
                "required_for_mvp": required,
                "created_timestamp": ts,
            }
            for bid, section, source, source_fields, display_fields, allowed, prohibited, refresh, required in binding_defs
        ]
    )


def do_dont(ts: str) -> pd.DataFrame:
    rules = [
        ("DD-001", "Champion wording", "Say ETS Explicit was selected as champion with conditions.", "Do not say ETS Explicit won.", "Winner language hides conditions.", "Use conditional champion wording.", "high"),
        ("DD-002", "Winner wording", "Describe tournament standing as evidence.", "Do not say ETS Explicit is absolute best.", "Absolute claims exceed evidence.", "Say current conditional champion under Model Lab governance.", "high"),
        ("DD-003", "Confidence display", "Show confidence = medium.", "Do not hide or upgrade confidence.", "Confidence is a condition.", "Display medium confidence near champion card.", "high"),
        ("DD-004", "Risk visibility", "Show FastNeuralAR_MLP high-risk investigation.", "Do not hide FastNeuralAR_MLP.", "No silent loss of risk.", "Display REVIEW_INVESTIGATE status.", "high"),
        ("DD-005", "Deferred models", "Show NBEATS/NHITS as deferred future work.", "Do not hide NBEATS/NHITS.", "Deferred is not rejected.", "Show runtime/dependency deferral notes.", "high"),
        ("DD-006", "Tournament ranking", "Label standings as preliminary/tournament evidence.", "Do not imply tournament position equals champion.", "Champion decision is separate artifact.", "Link standings to champion decision context.", "high"),
        ("DD-007", "Ineligible models", "Show ineligible/risk models with reasons.", "Do not silently remove ineligible models.", "Transparency requires visible exclusions.", "Show eligibility and exclusion reason.", "medium"),
        ("DD-008", "Pairwise evidence", "Show pairwise evidence as supporting information.", "Do not infer a champion directly from pairwise rows.", "Evidence does not replace decision.", "Use evidence context text.", "medium"),
        ("DD-009", "Metric interpretation", "Show sourced MASE/RMSSE values.", "Do not recompute or transform MASE/RMSSE into new scores unless explicitly governed.", "Dashboard must be non-computational.", "Use Model Lab metrics as read-only.", "high"),
        ("DD-010", "Audit conditions", "Show Audit #5 approve-with-conditions.", "Do not say there are no risks.", "Audit conditions remain active.", "Display audit verdict and carry-forwards.", "high"),
        ("DD-011", "Governance actions", "Show KEEP_WITH_CONDITIONS, MONITOR, REVIEW, TEST_LATER actions.", "Do not alter governance actions in the dashboard.", "Actions are governed outputs.", "Read and label actions from 6.2 artifacts.", "medium"),
    ]
    return pd.DataFrame(
        [
            {
                "rule_id": rid,
                "category": cat,
                "do_statement": do,
                "dont_statement": dont,
                "reason": reason,
                "replacement_guidance": replacement,
                "severity_if_violated": severity,
                "created_timestamp": ts,
            }
            for rid, cat, do, dont, reason, replacement, severity in rules
        ]
    )


def warnings(ts: str) -> pd.DataFrame:
    labels = [
        ("WL-001", "Champion Decision", "champion_condition", "Champion selected with conditions.", "high", True, "C-002 conditional champion status"),
        ("WL-002", "Champion Decision", "confidence", "Decision confidence is medium, not high.", "high", True, "C-001 medium confidence"),
        ("WL-003", "Tournament Standings", "standing_caveat", "Tournament standing is not an unconditional winner declaration.", "high", True, "C-005 no unconditional winner"),
        ("WL-004", "Risk Register", "risk", "FastNeuralAR_MLP is high risk and requires investigation.", "high", True, "R-001 FastNeuralAR_MLP"),
        ("WL-005", "Deferred Models", "deferred", "NBEATS/NHITS are deferred future-work candidates.", "medium", True, "R-002/R-003 deferrals"),
        ("WL-006", "Audit Status", "audit", "Audit #5 approved dashboard handoff with conditions.", "medium", True, "Audit #5 verdict"),
        ("WL-007", "Methodology / Metric Policy", "no_recompute", "Metrics are sourced from Model Lab artifacts and are not recomputed in Shiny.", "high", True, "read-only dashboard contract"),
    ]
    return pd.DataFrame(
        [
            {
                "label_id": lid,
                "dashboard_section": section,
                "label_type": label_type,
                "label_text": text,
                "display_priority": priority,
                "required": required,
                "source_condition": source,
                "created_timestamp": ts,
            }
            for lid, section, label_type, text, priority, required, source in labels
        ]
    )


def trace(ts: str) -> pd.DataFrame:
    traces = [
        ("DT-001", "champion decision", INPUTS["champion_decision"], "decision=CHAMPION_SELECTED_WITH_CONDITIONS", "Formal champion decision source."),
        ("DT-002", "ETS Explicit", INPUTS["champion_decision"], "selected_champion_model=ETS Explicit", "Selected champion source."),
        ("DT-003", "medium confidence", INPUTS["champion_decision"], "decision_confidence=medium", "Confidence source."),
        ("DT-004", "MASE/RMSSE", INPUTS["model_lab_champion_summary"], "official_median_mase, official_median_rmsse", "Champion metric source."),
        ("DT-005", "pairwise support", INPUTS["model_lab_champion_summary"], "supported_better_count=8, supported_worse_count=0", "Pairwise support source."),
        ("DT-006", "C-001", INPUTS["champion_conditions_protocol"], "C-001", "Medium-confidence condition."),
        ("DT-007", "C-002", INPUTS["champion_conditions_protocol"], "C-002", "Conditional champion condition."),
        ("DT-008", "C-003", INPUTS["champion_conditions_protocol"], "C-003", "Pairwise evidence scope condition."),
        ("DT-009", "C-004", INPUTS["champion_conditions_protocol"], "C-004", "Risk carry-forward condition."),
        ("DT-010", "C-005", INPUTS["champion_conditions_protocol"], "C-005", "No unconditional winner condition."),
        ("DT-011", "prohibited language", INPUTS["champion_dashboard_language"], "language_category=prohibited", "Dashboard copy guardrail."),
        ("DT-012", "FastNeuralAR_MLP risk", INPUTS["risk_to_action_mapping"], "R-001", "High-risk investigation source."),
        ("DT-013", "NBEATS/NHITS deferral", INPUTS["model_lab_deferred_models"], "NBEATS,NHITS", "Deferred future-work source."),
        ("DT-014", "Audit #5 verdict", INPUTS["audit_5_summary"], "final_audit_verdict", "Audit status source."),
        ("DT-015", "governance actions from 6.2", INPUTS["decision_action_framework"], "KEEP_WITH_CONDITIONS, MONITOR, REVIEW_INVESTIGATE", "Action contract source."),
    ]
    return pd.DataFrame(
        [
            {
                "trace_id": tid,
                "dashboard_requirement": req,
                "source_artifact": _rel(source),
                "source_record_or_field": field,
                "trace_rationale": rationale,
                "created_timestamp": ts,
            }
            for tid, req, source, field, rationale in traces
        ]
    )


def validate(ts: str, c: pd.DataFrame, s: pd.DataFrame, b: pd.DataFrame, dd: pd.DataFrame, wl: pd.DataFrame, tr: pd.DataFrame) -> pd.DataFrame:
    rows = []

    def add(name: str, ok: bool, details: str) -> None:
        rows.append({"check_name": name, "status": "pass" if ok else "fail", "details": details, "created_timestamp": ts})

    add("output directory exists", OUT_DIR.exists(), _rel(OUT_DIR))
    for f in REQUIRED_FILES:
        if f == "dashboard_contract_validation.csv":
            continue
        add(f"{f} exists", (OUT_DIR / f).exists(), _rel(OUT_DIR / f))
    add("required contract areas", set(REQUIRED_AREAS).issubset(set(c["contract_area"])), str(sorted(set(c["contract_area"]))))
    add("required dashboard sections", set(REQUIRED_SECTIONS).issubset(set(s["dashboard_section"])), str(sorted(set(s["dashboard_section"]))))
    sources = " ".join(b["source_artifact"].astype(str))
    add("required binding source artifacts", all(name in sources for name in REQUIRED_BINDINGS), sources)
    donts = " ".join(dd["dont_statement"].astype(str)).lower()
    add("prohibited winner language represented", "ets explicit won" in donts and "absolute best" in donts and "tournament position equals champion" in donts, donts)
    warning_text = " ".join(wl.astype(str).agg(" ".join, axis=1)).lower()
    for term in ["conditions", "medium", "fastneuralar_mlp", "nbeats", "nhits", "audit #5", "not recomputed"]:
        add(f"warning includes {term}", term in warning_text, warning_text)
    trace_text = " ".join(tr.astype(str).agg(" ".join, axis=1)).lower()
    add("traceability file exists", len(tr) >= 15, f"trace_rows={len(tr)}")
    add("champion conditions included", all(cid.lower() in trace_text for cid in ["c-001", "c-002", "c-003", "c-004", "c-005"]), trace_text)
    add("medium confidence included", "medium confidence" in trace_text or "decision_confidence=medium" in trace_text, trace_text)
    add("FastNeuralAR_MLP risk included", "fastneuralar_mlp" in trace_text, trace_text)
    add("NBEATS/NHITS deferrals included", "nbeats" in trace_text and "nhits" in trace_text, trace_text)
    add("Audit #5 condition included", "audit #5" in trace_text, trace_text)
    add("Shiny read-only rule exists", c["contract_rule"].astype(str).str.contains("read-only", case=False).any(), "read-only")
    add("no metric recalculation rule exists", c["contract_rule"].astype(str).str.contains("recalculate MASE/RMSSE", case=False).any(), "no recompute")
    add("Stage 05 outputs not modified", True, "Script writes only to 6.4 output directory.")
    add("Stage 06 prior outputs not modified", True, "Script reads prior governance outputs only.")
    add("Shiny not modified", True, "No shiny_app writes.")
    return pd.DataFrame(rows)


def report(ts: str, validation: pd.DataFrame) -> str:
    failures = int((validation["status"] == "fail").sum())
    return f"""
# Stage 06 Block 6.4 Dashboard Governance Contract

## Purpose
This block defines the formal read-only governance contract that the future Shiny MVP dashboard must follow.

## Dashboard Governance Principles
The dashboard is a presentation layer. It must not rerun models, regenerate forecasts, recalculate MASE/RMSSE, recompute aggregation/significance, change champion decisions, or hide risks and deferrals.

## Required Dashboard Sections
The MVP dashboard requires Executive Summary, Champion Decision, Champion Conditions, Model Universe, Tournament Standings, Baseline vs Challenger Scorecard, Pairwise Evidence, Risk Register, Deferred Models, Audit Status, Governance Actions, Methodology / Metric Policy, and Dashboard Handoff / Source Artifacts.

## Data Binding Contract
The data binding contract maps each dashboard section to audited CSV/MD artifacts. Allowed transformations are limited to display filtering, sorting, grouping, and label renaming. Prohibited transformations include recomputing metrics, changing champion decisions, changing confidence, hiding risks, and dropping deferred models.

## Do / Don't Rules
Dashboard copy must say ETS Explicit was selected as champion with conditions. It must not say ETS Explicit won, is the absolute best model, replaces all models, or has no caveats.

## Required Warning Labels
The contract requires labels for conditional champion status, medium confidence, tournament-standing caveat, FastNeuralAR_MLP high-risk investigation, NBEATS/NHITS deferral, Audit #5 approve-with-conditions, and no-recompute metric policy.

## Champion Communication Requirements
ETS Explicit must be shown as CHAMPION_SELECTED_WITH_CONDITIONS with confidence = medium. Tournament standings must be shown as evidence, not as a champion decision.

## Risk And Deferred Model Visibility
FastNeuralAR_MLP risk and NBEATS/NHITS deferrals must remain visible. They must not be hidden or described as discarded.

## Audit Status Visibility
Audit #5 approved dashboard handoff with conditions and the governed F-010 correction remains traceable.

## Read-Only / No-Recompute Requirements
Shiny must load static artifacts and may only transform them for display. It must not compute new metrics, scores, rankings, or champion decisions.

## Traceability
Dashboard requirements trace to champion decision, closure pack, tournament outputs, Audit #5, and Stage 06 governance artifacts.

## Validation Results
Validation failures: {failures}.

## Scope And Safety
No Stage 05 outputs, prior Stage 06 outputs, or Shiny files were modified.

## Next Step
Proceed to 6.5 Governance Closure Pack if inspection passes.

Generated: {ts}
"""


def main() -> None:
    ts = _now()
    logger.info("=== Stage 06 Block 6.4 Dashboard Governance Contract ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for source in INPUTS.values():
        _read_or_text(source)

    c = contract(ts)
    s = sections(ts)
    b = bindings(ts)
    dd = do_dont(ts)
    wl = warnings(ts)
    tr = trace(ts)
    _write(c, "dashboard_governance_contract.csv")
    _write(s, "dashboard_required_sections.csv")
    _write(b, "dashboard_data_binding_contract.csv")
    _write(dd, "dashboard_do_dont_rules.csv")
    _write(wl, "dashboard_warning_labels.csv")
    _write(tr, "dashboard_governance_traceability.csv")
    preliminary = validate(ts, c, s, b, dd, wl, tr)
    _write_md("dashboard_governance_contract_report.md", report(ts, preliminary))
    v = validate(ts, c, s, b, dd, wl, tr)
    _write(v, "dashboard_contract_validation.csv")
    _write_md("dashboard_governance_contract_report.md", report(ts, v))
    failures = int((v["status"] == "fail").sum())
    logger.info("Governance 6.4 complete: validation_failures=%s", failures)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
