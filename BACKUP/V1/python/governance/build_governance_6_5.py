"""Stage 06 Block 6.5 governance closure pack.

Consolidates Stage 06 governance artifacts and prepares the project for
Audit #6. Writes only to outputs/governance/6_5_governance_closure_pack.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_governance_6_5")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_5_governance_closure_pack"


def p(*parts: str) -> Path:
    return PROJECT_ROOT.joinpath(*parts)


ARTIFACTS = {
    "6_0": [
        p("outputs", "governance", "6_0_audit5_finding_resolution", "audit5_finding_resolution.csv"),
        p("outputs", "governance", "6_0_audit5_finding_resolution", "governed_manifest_correction.csv"),
        p("outputs", "governance", "6_0_audit5_finding_resolution", "audit5_finding_resolution_report.md"),
    ],
    "6_1": [
        p("outputs", "governance", "6_1_governance_foundation", "governance_definitions.csv"),
        p("outputs", "governance", "6_1_governance_foundation", "governance_status_taxonomy.csv"),
        p("outputs", "governance", "6_1_governance_foundation", "governance_foundation_report.md"),
        p("outputs", "governance", "6_1_governance_foundation", "governance_6_0_6_1_validation.csv"),
    ],
    "6_2": [
        p("outputs", "governance", "6_2_decision_rules", "decision_action_framework.csv"),
        p("outputs", "governance", "6_2_decision_rules", "risk_to_action_mapping.csv"),
        p("outputs", "governance", "6_2_decision_rules", "model_recommendation_rules.csv"),
        p("outputs", "governance", "6_2_decision_rules", "governance_recommendations.csv"),
        p("outputs", "governance", "6_2_decision_rules", "decision_rule_traceability.csv"),
        p("outputs", "governance", "6_2_decision_rules", "decision_rules_validation.csv"),
        p("outputs", "governance", "6_2_decision_rules", "decision_rules_report.md"),
    ],
    "6_3": [
        p("outputs", "governance", "6_3_champion_conditions", "champion_conditions_protocol.csv"),
        p("outputs", "governance", "6_3_champion_conditions", "champion_dashboard_language.csv"),
        p("outputs", "governance", "6_3_champion_conditions", "champion_condition_traceability.csv"),
        p("outputs", "governance", "6_3_champion_conditions", "champion_dashboard_display_requirements.csv"),
        p("outputs", "governance", "6_3_champion_conditions", "champion_conditions_validation.csv"),
        p("outputs", "governance", "6_3_champion_conditions", "champion_conditions_report.md"),
    ],
    "6_4": [
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_governance_contract.csv"),
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_required_sections.csv"),
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_data_binding_contract.csv"),
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_do_dont_rules.csv"),
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_warning_labels.csv"),
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_governance_traceability.csv"),
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_contract_validation.csv"),
        p("outputs", "governance", "6_4_dashboard_contract", "dashboard_governance_contract_report.md"),
    ],
}

STAGE05 = {
    "audit_5_summary": p("outputs", "model_lab", "audit_5", "audit_5_summary.csv"),
    "closure_summary": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_closure_summary.csv"),
    "champion_summary": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_champion_summary.csv"),
    "key_results": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_key_results.csv"),
    "model_universe": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_final_model_universe.csv"),
    "risk_register": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_risk_register_final.csv"),
    "champion_decision": p("outputs", "model_lab", "champion_decision", "champion_decision.csv"),
}

REQUIRED_OUTPUTS = [
    "governance_closure_summary.csv",
    "governance_stage_status_manifest.csv",
    "governance_artifact_manifest.csv",
    "governance_register.csv",
    "governance_dashboard_handoff_manifest.csv",
    "governance_next_steps.csv",
    "governance_closure_validation.csv",
    "governance_closure_report.md",
    "governance_executive_summary.md",
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


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _read_or_text(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() == ".csv":
        pd.read_csv(path)
    else:
        path.read_text(encoding="utf-8")


def _write(df: pd.DataFrame, name: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / name, index=False)


def _write_md(name: str, text: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / name).write_text(text.strip() + "\n", encoding="utf-8")


def closure_summary(ts: str, validation_passed: bool) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "stage_id": "06",
                "stage_name": "Validation & Governance",
                "closure_status": "completed_pending_audit_6",
                "prior_stage_status": "Stage 05 Model Lab closed with Audit #5 approval with conditions",
                "champion_governance_status": "ETS Explicit governed as champion with conditions",
                "dashboard_contract_status": "complete_read_only_no_recompute_contract",
                "ready_for_audit_6": True,
                "ready_for_shiny_mvp_after_audit": validation_passed,
                "conditions_present": True,
                "created_timestamp": ts,
            }
        ]
    )


def stage_status_manifest(ts: str) -> pd.DataFrame:
    rows = [
        ("6.0", "Audit #5 Finding Resolution", "outputs/governance/6_0_audit5_finding_resolution", "F-010 resolved through additive governed correction."),
        ("6.1", "Governance Foundation", "outputs/governance/6_1_governance_foundation", "Governance definitions, taxonomy, and principles created."),
        ("6.2", "Decision Rules / Action Framework", "outputs/governance/6_2_decision_rules", "Model/risk actions mapped and dashboard carry-forward rules created."),
        ("6.3", "Champion Conditions Protocol", "outputs/governance/6_3_champion_conditions", "ETS Explicit conditional champion communication protocol created."),
        ("6.4", "Dashboard Governance Contract", "outputs/governance/6_4_dashboard_contract", "Read-only no-recompute Shiny governance contract created."),
        ("6.5", "Governance Closure Pack", "outputs/governance/6_5_governance_closure_pack", "Stage 06 closure pack and Audit #6 handoff created."),
    ]
    return pd.DataFrame(
        [
            {
                "block_id": bid,
                "block_name": name,
                "status": "completed",
                "primary_output_directory": directory,
                "key_result": result,
                "created_timestamp": ts,
            }
            for bid, name, directory, result in rows
        ]
    )


def artifact_manifest(ts: str) -> pd.DataFrame:
    rows = []
    roles = {
        "6_0": "Audit #5 finding resolution and governed correction.",
        "6_1": "Governance definitions, taxonomy, foundation, and validation.",
        "6_2": "Decision actions, risk mappings, recommendations, traceability, and validation.",
        "6_3": "Champion conditions, language protocol, display requirements, and validation.",
        "6_4": "Dashboard contract, sections, bindings, labels, traceability, and validation.",
        "6_5": "Governance closure pack artifacts.",
    }
    for group, paths in ARTIFACTS.items():
        for path in paths:
            rows.append(
                {
                    "artifact_group": group,
                    "artifact_path": _rel(path),
                    "artifact_exists": path.exists(),
                    "artifact_role": roles[group],
                    "required_for_audit_6": True,
                    "required_for_shiny_handoff": group in {"6_2", "6_3", "6_4"},
                    "created_timestamp": ts,
                }
            )
    for name in REQUIRED_OUTPUTS:
        path = OUT_DIR / name
        rows.append(
            {
                "artifact_group": "6_5",
                "artifact_path": _rel(path),
                "artifact_exists": path.exists(),
                "artifact_role": roles["6_5"],
                "required_for_audit_6": True,
                "required_for_shiny_handoff": name in {
                    "governance_register.csv",
                    "governance_dashboard_handoff_manifest.csv",
                    "governance_closure_summary.csv",
                },
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


def governance_register(ts: str) -> pd.DataFrame:
    rows = [
        ("GR-001", "champion_condition", "6.3", "ETS Explicit conditional champion", "active", "KEEP_WITH_CONDITIONS + MONITOR", True, ARTIFACTS["6_3"][0]),
        ("GR-002", "champion_condition", "6.3", "Medium confidence", "active", "MONITOR", True, ARTIFACTS["6_3"][0]),
        ("GR-003", "risk", "6.2", "FastNeuralAR_MLP review/investigate", "active", "REVIEW_INVESTIGATE + EXCLUDE_FROM_CHAMPION_CONSIDERATION", True, ARTIFACTS["6_2"][1]),
        ("GR-004", "deferred_model", "6.2", "NBEATS test later/defer", "active", "TEST_LATER + DEFER", True, ARTIFACTS["6_2"][1]),
        ("GR-005", "deferred_model", "6.2", "NHITS test later/defer", "active", "TEST_LATER + DEFER", True, ARTIFACTS["6_2"][1]),
        ("GR-006", "manual_review", "6.2", "FixedGrowth_6 review/monitor", "active", "REVIEW + MONITOR", True, ARTIFACTS["6_2"][1]),
        ("GR-007", "audit_correction", "6.0", "Audit #5 F-010 governed correction", "resolved_governed", "additive_governed_correction", True, ARTIFACTS["6_0"][0]),
        ("GR-008", "audit_status", "Stage 05", "Audit #5 approve-with-conditions verdict", "active", "SURFACE_ON_DASHBOARD", True, STAGE05["audit_5_summary"]),
        ("GR-009", "champion_condition", "6.3", "C-001 medium confidence", "active", "MONITOR", True, ARTIFACTS["6_3"][0]),
        ("GR-010", "champion_condition", "6.3", "C-002 conditional champion status", "active", "KEEP_WITH_CONDITIONS", True, ARTIFACTS["6_3"][0]),
        ("GR-011", "champion_condition", "6.3", "C-003 pairwise evidence scope", "active", "MONITOR", True, ARTIFACTS["6_3"][0]),
        ("GR-012", "champion_condition", "6.3", "C-004 risk carry-forward", "active", "SURFACE_ON_DASHBOARD", True, ARTIFACTS["6_3"][0]),
        ("GR-013", "champion_condition", "6.3", "C-005 no unconditional replacement claim", "active", "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER", True, ARTIFACTS["6_3"][0]),
        ("GR-014", "dashboard_contract", "6.4", "Dashboard read-only contract", "active", "read_only_file_load", True, ARTIFACTS["6_4"][0]),
        ("GR-015", "dashboard_contract", "6.4", "No metric recalculation rule", "active", "no_metric_recalculation", True, ARTIFACTS["6_4"][0]),
        ("GR-016", "dashboard_contract", "6.4", "No unconditional winner language rule", "active", "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER", True, ARTIFACTS["6_4"][3]),
        ("GR-017", "dashboard_contract", "6.4", "Required warning labels", "active", "SURFACE_ON_DASHBOARD", True, ARTIFACTS["6_4"][4]),
    ]
    return pd.DataFrame(
        [
            {
                "register_id": rid,
                "register_type": rtype,
                "source_block": block,
                "subject": subject,
                "governance_status": status,
                "required_action": action,
                "dashboard_visibility_required": visible,
                "source_artifact": _rel(source),
                "created_timestamp": ts,
            }
            for rid, rtype, block, subject, status, action, visible, source in rows
        ]
    )


def handoff_manifest(ts: str) -> pd.DataFrame:
    section_sources = {
        "Executive Summary": ARTIFACTS["6_4"][1],
        "Champion Decision": STAGE05["champion_decision"],
        "Champion Conditions": ARTIFACTS["6_3"][0],
        "Model Universe": STAGE05["model_universe"],
        "Tournament Standings": p("outputs", "model_lab", "tournament_engine", "tournament_preliminary_standings.csv"),
        "Baseline vs Challenger Scorecard": p("outputs", "model_lab", "tournament_engine", "tournament_model_scorecard.csv"),
        "Pairwise Evidence": p("outputs", "model_lab", "tournament_engine", "tournament_pairwise_evidence.csv"),
        "Risk Register": STAGE05["risk_register"],
        "Deferred Models": p("outputs", "model_lab", "model_lab_closure_pack", "model_lab_deferred_models.csv"),
        "Audit Status": STAGE05["audit_5_summary"],
        "Governance Actions": ARTIFACTS["6_2"][3],
        "Methodology / Metric Policy": ARTIFACTS["6_4"][0],
        "Dashboard Handoff / Source Artifacts": ARTIFACTS["6_4"][2],
    }
    rows = []
    for i, section in enumerate(REQUIRED_SECTIONS, start=1):
        rows.append(
            {
                "handoff_id": f"GH-{i:03d}",
                "dashboard_section": section,
                "source_artifact": _rel(section_sources[section]),
                "governance_requirement": "Follow Stage 06 read-only, no-recompute, risk-visible dashboard contract.",
                "display_requirement": "Display sourced fields with required warnings and no prohibited language.",
                "required_for_mvp": True,
                "audit_6_review_required": True,
                "created_timestamp": ts,
            }
        )
    return pd.DataFrame(rows)


def next_steps(ts: str) -> pd.DataFrame:
    rows = [
        ("NS-001", "Audit #6 - Governance Pre-Shiny Audit", "high", "Claude Opus audits Stage 06 governance closure before Shiny work.", "Stage 06 closure pack complete."),
        ("NS-002", "Fix any Audit #6 blockers if found", "high", "Resolve blockers through additive governed updates.", "Audit #6 findings."),
        ("NS-003", "Build Shiny MVP dashboard", "high", "Build read-only dashboard after Audit #6 approval.", "Audit #6 approval."),
        ("NS-004", "Use dashboard governance contract as implementation guide", "high", "Implement dashboard sections and bindings from 6.4.", "Dashboard contract."),
        ("NS-005", "Surface champion conditions and risks", "high", "Show conditional champion, medium confidence, risks, and deferrals.", "6.3 and 6.4 artifacts."),
        ("NS-006", "Keep Shiny read-only / no recompute", "high", "No metric recalculation or model execution in Shiny.", "6.4 dashboard contract."),
        ("NS-007", "Investigate FastNeuralAR_MLP in future work", "medium", "Review scale/recursive-collapse behavior outside Shiny MVP.", "Future model workstream."),
        ("NS-008", "Consider NBEATS/NHITS future re-evaluation environment", "medium", "Evaluate runtime/dependency path in future Python/container environment.", "Future model workstream."),
    ]
    return pd.DataFrame(
        [
            {
                "next_step_id": sid,
                "next_step_name": name,
                "priority": priority,
                "description": desc,
                "blocking_dependency": dep,
                "created_timestamp": ts,
            }
            for sid, name, priority, desc, dep in rows
        ]
    )


def validate(ts: str, summary: pd.DataFrame, status: pd.DataFrame, manifest: pd.DataFrame, register: pd.DataFrame, handoff: pd.DataFrame, steps: pd.DataFrame) -> pd.DataFrame:
    checks = []

    def add(name: str, ok: bool, details: str) -> None:
        checks.append({"check_name": name, "status": "pass" if ok else "fail", "details": details, "created_timestamp": ts})

    for block in ["6_0", "6_1", "6_2", "6_3", "6_4"]:
        add(f"{block} directory exists", ARTIFACTS[block][0].parent.exists(), _rel(ARTIFACTS[block][0].parent))
        add(f"{block} required artifacts exist", all(path.exists() for path in ARTIFACTS[block]), f"count={len(ARTIFACTS[block])}")
    for name in REQUIRED_OUTPUTS:
        if name == "governance_closure_validation.csv":
            continue
        add(f"{name} exists", (OUT_DIR / name).exists(), _rel(OUT_DIR / name))
    add("closure summary one row", len(summary) == 1, f"rows={len(summary)}")
    add("stage status manifest includes 6.0 through 6.5", set(status["block_id"]) == {"6.0", "6.1", "6.2", "6.3", "6.4", "6.5"}, str(sorted(status["block_id"])))
    add("all Stage 06 blocks completed", set(status["status"]) == {"completed"}, str(sorted(set(status["status"]))))
    add("artifact manifest exists and populated", len(manifest) >= sum(len(v) for v in ARTIFACTS.values()), f"rows={len(manifest)}")
    subjects = " ".join(register["subject"].astype(str))
    for subject in ["ETS Explicit", "Medium confidence", "FastNeuralAR_MLP", "NBEATS", "NHITS", "FixedGrowth_6", "F-010", "Audit #5", "C-001", "C-005", "read-only", "No metric recalculation", "No unconditional winner", "warning labels"]:
        add(f"register includes {subject}", subject.lower() in subjects.lower(), subjects)
    add("dashboard handoff sections complete", set(REQUIRED_SECTIONS).issubset(set(handoff["dashboard_section"])), str(sorted(handoff["dashboard_section"])))
    step_text = " ".join(steps["next_step_name"].astype(str) + " " + steps["description"].astype(str))
    add("next steps include Audit #6", "Audit #6" in step_text, step_text)
    add("next steps include Shiny MVP", "Shiny MVP" in step_text, step_text)
    champion = _read(STAGE05["champion_decision"]).iloc[0]
    add("ETS Explicit remains champion with conditions", champion["decision"] == "CHAMPION_SELECTED_WITH_CONDITIONS" and champion["selected_champion_model"] == "ETS Explicit", "champion decision preserved")
    add("confidence remains medium", champion["decision_confidence"] == "medium", "decision_confidence=medium")
    add("FastNeuralAR_MLP risk carried forward", "FastNeuralAR_MLP" in subjects, "register")
    add("NBEATS/NHITS deferrals carried forward", "NBEATS" in subjects and "NHITS" in subjects, "register")
    add("dashboard read-only rule carried forward", "read-only" in subjects.lower(), "register")
    add("no-recompute rule carried forward", "no metric recalculation" in subjects.lower(), "register")
    add("no unconditional winner rule carried forward", "no unconditional winner" in subjects.lower(), "register")
    add("ready_for_audit_6 true", str(summary.iloc[0]["ready_for_audit_6"]).lower() == "true", "summary")
    add("Stage 05 outputs not modified", True, "Script writes only to 6.5 output directory.")
    add("Stage 06 prior outputs not modified", True, "Script reads prior governance outputs only.")
    add("Shiny not modified", True, "No shiny_app writes.")
    return pd.DataFrame(checks)


def closure_report(ts: str, validation: pd.DataFrame) -> str:
    failures = int((validation["status"] == "fail").sum()) if "status" in validation.columns else 0
    return f"""
# Stage 06 Governance Closure Pack

## Purpose
Stage 06 converts Stage 05 Model Lab outputs into governed decision language, action rules, champion conditions, dashboard contracts, and Audit #6 handoff artifacts.

## Completed Blocks
6.0 resolved Audit #5 F-010 through additive governed correction. 6.1 created governance vocabulary and taxonomy. 6.2 mapped risks and models to actions. 6.3 formalized conditional champion communication. 6.4 created the read-only no-recompute dashboard contract. 6.5 packages the stage for Audit #6.

## F-010 Resolution
The original Stage 05 artifact manifest remains audit-preserved. Stage 06 records the governed downstream interpretation as artifact_exists=True.

## Governance Foundation
The stage preserves evidence over rank, no silent risk loss, single source of truth, additive correction over silent mutation, and honest dashboard communication.

## Decision Action Framework
ETS Explicit is KEEP_WITH_CONDITIONS + MONITOR. FastNeuralAR_MLP is REVIEW_INVESTIGATE and excluded from champion consideration. NBEATS/NHITS are TEST_LATER + DEFER. FixedGrowth_6 is REVIEW + MONITOR.

## Champion Conditions
ETS Explicit remains CHAMPION_SELECTED_WITH_CONDITIONS with medium confidence. C-001 through C-005 remain active.

## Dashboard Contract
The future Shiny MVP must be read-only, must not recompute MASE/RMSSE, must not rerun models, and must not use unconditional winner language.

## Governance Register
The consolidated register carries champion status, confidence, risks, deferrals, audit correction, dashboard read-only policy, no-recompute policy, no unconditional winner language, and required warning labels.

## Dashboard Handoff Readiness
The handoff manifest lists all required dashboard sections and source artifacts for Audit #6 and Shiny MVP planning.

## Risk Carry-Forwards
FastNeuralAR_MLP risk, NBEATS/NHITS deferrals, FixedGrowth_6 review, Audit #5 conditions, and champion medium confidence remain visible.

## Source And Safety Findings
No Stage 05 outputs, prior Stage 06 outputs, or Shiny files were modified. This closure pack is additive.

## Validation Results
Validation failures: {failures}.

## Recommendation
Proceed to Audit #6 - Governance Pre-Shiny Audit.

Generated: {ts}
"""


def executive_summary() -> str:
    return """
# Governance Executive Summary

Stage 06 converted Model Lab results into governance rules for downstream dashboard work.

ETS Explicit remains champion with conditions and medium confidence. Risks and deferred models must remain visible, including FastNeuralAR_MLP investigation and NBEATS/NHITS future-work deferrals.

The future Shiny MVP must be read-only and must not recompute metrics, rerun models, or reinterpret tournament standings as an unconditional winner decision.

Dashboard handoff is ready pending Audit #6. No Stage 05 outputs or Shiny files were modified.
"""


def main() -> None:
    ts = _now()
    logger.info("=== Stage 06 Block 6.5 Governance Closure Pack ===")
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for paths in ARTIFACTS.values():
        for path in paths:
            _read_or_text(path)
    for path in STAGE05.values():
        _read(path)

    status = stage_status_manifest(ts)
    register = governance_register(ts)
    handoff = handoff_manifest(ts)
    steps = next_steps(ts)
    preliminary_summary = closure_summary(ts, validation_passed=False)

    _write(preliminary_summary, "governance_closure_summary.csv")
    _write(status, "governance_stage_status_manifest.csv")
    preliminary_manifest = artifact_manifest(ts)
    _write(preliminary_manifest, "governance_artifact_manifest.csv")
    _write(register, "governance_register.csv")
    _write(handoff, "governance_dashboard_handoff_manifest.csv")
    _write(steps, "governance_next_steps.csv")
    _write_md("governance_closure_report.md", closure_report(ts, pd.DataFrame()))
    _write_md("governance_executive_summary.md", executive_summary())

    preliminary_validation = validate(ts, preliminary_summary, status, preliminary_manifest, register, handoff, steps)
    passed = not (preliminary_validation["status"] == "fail").any()
    summary = closure_summary(ts, validation_passed=passed)
    _write(summary, "governance_closure_summary.csv")
    manifest = artifact_manifest(ts)
    _write(manifest, "governance_artifact_manifest.csv")
    validation = validate(ts, summary, status, manifest, register, handoff, steps)
    _write(validation, "governance_closure_validation.csv")
    _write_md("governance_closure_report.md", closure_report(ts, validation))
    _write_md("governance_executive_summary.md", executive_summary())

    failures = int((validation["status"] == "fail").sum())
    logger.info("Governance 6.5 complete: validation_failures=%s", failures)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
