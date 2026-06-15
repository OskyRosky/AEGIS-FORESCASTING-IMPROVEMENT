#!/usr/bin/env python3
"""
Audit #6 - Governance Pre-Shiny Audit
Independent read-only verification script.

Reads Stage 06 governance artifacts (and a few Stage 05 references) and writes a
single verification result CSV under outputs/governance/audit_6/. It does not
modify any Stage 05, Stage 06, or Shiny artifact.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime

# <root>/outputs/governance/audit_6/_audit_6_independent_verification.py
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
GOV = os.path.join(ROOT, "outputs", "governance")
ML = os.path.join(ROOT, "outputs", "model_lab")

TS = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def read_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def main() -> None:
    checks: list[tuple[str, str, str]] = []

    def add(name: str, ok: bool, evidence: str) -> None:
        checks.append((name, "PASS" if ok else "FAIL", evidence))

    # --- Block existence (6.0 - 6.5) ---
    block_dirs = {
        "6_0": "6_0_audit5_finding_resolution",
        "6_1": "6_1_governance_foundation",
        "6_2": "6_2_decision_rules",
        "6_3": "6_3_champion_conditions",
        "6_4": "6_4_dashboard_contract",
        "6_5": "6_5_governance_closure_pack",
    }
    for block, d in block_dirs.items():
        add(f"{block}_directory_exists", os.path.isdir(os.path.join(GOV, d)), d)

    # --- A. F-010 governed correction ---
    gmc = read_rows(os.path.join(GOV, block_dirs["6_0"], "governed_manifest_correction.csv"))
    add(
        "f010_authoritative_value_true",
        bool(gmc) and gmc[0]["authoritative_governed_value"].strip().lower() == "true",
        gmc[0].get("authoritative_governed_value", "") if gmc else "missing",
    )
    add(
        "f010_applied_to_original_false",
        bool(gmc) and gmc[0]["applied_to_original_file"].strip().lower() == "false",
        gmc[0].get("applied_to_original_file", "") if gmc else "missing",
    )

    # --- B. Champion status preserved in 6.2 / 6.3 ---
    gr = read_rows(os.path.join(GOV, block_dirs["6_2"], "governance_recommendations.csv"))
    ets = [r for r in gr if r["model_name"] == "ETS Explicit"]
    add(
        "ets_explicit_keep_with_conditions",
        bool(ets)
        and ets[0]["selected_champion"] == "True"
        and ets[0]["governance_primary_action"] == "KEEP_WITH_CONDITIONS",
        ets[0]["governance_primary_action"] if ets else "missing",
    )

    cc = read_rows(os.path.join(GOV, block_dirs["6_3"], "champion_conditions_protocol.csv"))
    cond_ids = {r["condition_id"] for r in cc}
    add(
        "champion_conditions_c001_c005_present",
        {"C-001", "C-002", "C-003", "C-004", "C-005"}.issubset(cond_ids),
        str(sorted(cond_ids)),
    )

    lang = read_rows(os.path.join(GOV, block_dirs["6_3"], "champion_dashboard_language.csv"))
    prohibited = [r for r in lang if r["allowed_status"] == "prohibited"]
    won_prohibited = any("won" in r["statement_text"].lower() for r in prohibited)
    add("unconditional_winner_language_prohibited", won_prohibited and len(prohibited) >= 5,
        f"prohibited_count={len(prohibited)}")

    # --- C. Risk-to-action mapping R-001..R-007 ---
    rmap = read_rows(os.path.join(GOV, block_dirs["6_2"], "risk_to_action_mapping.csv"))
    by_risk = {r["risk_id"]: r for r in rmap}
    add("risk_ids_r001_r007_present",
        {"R-001", "R-002", "R-003", "R-004", "R-005", "R-006", "R-007"}.issubset(by_risk.keys()),
        str(sorted(by_risk.keys())))
    add("fastneural_review_investigate",
        "R-001" in by_risk and by_risk["R-001"]["assigned_primary_action"] == "REVIEW_INVESTIGATE",
        by_risk.get("R-001", {}).get("assigned_primary_action", "missing"))
    add("nbeats_test_later",
        "R-002" in by_risk and by_risk["R-002"]["assigned_primary_action"] == "TEST_LATER",
        by_risk.get("R-002", {}).get("assigned_primary_action", "missing"))
    add("nhits_test_later",
        "R-003" in by_risk and by_risk["R-003"]["assigned_primary_action"] == "TEST_LATER",
        by_risk.get("R-003", {}).get("assigned_primary_action", "missing"))
    add("fixedgrowth6_review",
        "R-007" in by_risk and by_risk["R-007"]["assigned_primary_action"] == "REVIEW",
        by_risk.get("R-007", {}).get("assigned_primary_action", "missing"))
    add("all_risks_dashboard_carry_forward",
        all(r["dashboard_carry_forward"].strip().lower() == "true" for r in rmap),
        f"rows={len(rmap)}")

    # --- D. Dashboard contract read-only + no-recompute + no unconditional winner ---
    dc = read_rows(os.path.join(GOV, block_dirs["6_4"], "dashboard_governance_contract.csv"))
    areas = {r["contract_area"] for r in dc}
    add("dashboard_read_only_rule", "read_only_behavior" in areas, str("read_only_behavior" in areas))
    add("dashboard_no_recompute_rule", "no_metric_recalculation" in areas, str("no_metric_recalculation" in areas))
    add("dashboard_no_unconditional_winner_rule", "no_unconditional_winner_language" in areas,
        str("no_unconditional_winner_language" in areas))
    add("dashboard_tournament_vs_champion_rule", "tournament_vs_champion_distinction" in areas,
        str("tournament_vs_champion_distinction" in areas))

    # --- E. Closure pack status ---
    cs = read_rows(os.path.join(GOV, block_dirs["6_5"], "governance_closure_summary.csv"))
    add("closure_status_completed_pending_audit_6",
        bool(cs) and cs[0]["closure_status"] == "completed_pending_audit_6",
        cs[0].get("closure_status", "") if cs else "missing")
    add("ready_for_audit_6_true",
        bool(cs) and cs[0]["ready_for_audit_6"].strip().lower() == "true",
        cs[0].get("ready_for_audit_6", "") if cs else "missing")

    ssm = read_rows(os.path.join(GOV, block_dirs["6_5"], "governance_stage_status_manifest.csv"))
    add("all_blocks_completed",
        bool(ssm) and all(r["status"] == "completed" for r in ssm) and len(ssm) == 6,
        f"rows={len(ssm)}; statuses={sorted({r['status'] for r in ssm})}")

    # Handoff manifest sections complete
    hand = read_rows(os.path.join(GOV, block_dirs["6_5"], "governance_dashboard_handoff_manifest.csv"))
    required_sections = {
        "Executive Summary", "Champion Decision", "Champion Conditions", "Model Universe",
        "Tournament Standings", "Baseline vs Challenger Scorecard", "Pairwise Evidence",
        "Risk Register", "Deferred Models", "Audit Status", "Governance Actions",
        "Methodology / Metric Policy",
    }
    sections = {r["dashboard_section"] for r in hand}
    add("handoff_sections_complete", required_sections.issubset(sections),
        f"missing={sorted(required_sections - sections)}")

    # Artifact manifest: every listed artifact exists on disk
    am = read_rows(os.path.join(GOV, block_dirs["6_5"], "governance_artifact_manifest.csv"))
    missing = [r["artifact_path"] for r in am if not os.path.isfile(os.path.join(ROOT, r["artifact_path"]))]
    add("artifact_manifest_files_exist", not missing, f"missing={missing[:3]} (n={len(missing)})")

    # --- F. Safety: Stage 05 champion decision unchanged + Shiny present ---
    cd_ml = read_rows(os.path.join(ML, "champion_decision", "champion_decision.csv"))
    add("stage05_champion_decision_intact",
        bool(cd_ml)
        and cd_ml[0]["decision"] == "CHAMPION_SELECTED_WITH_CONDITIONS"
        and cd_ml[0]["selected_champion_model"] == "ETS Explicit"
        and cd_ml[0]["decision_confidence"] == "medium",
        cd_ml[0]["decision"] if cd_ml else "missing")
    add("shiny_app_present", os.path.isdir(os.path.join(ROOT, "shiny_app")), "shiny_app/ dir present")

    # Dashboard binding source columns actually exist in referenced Stage 05 files
    pe = read_rows(os.path.join(ML, "tournament_engine", "tournament_pairwise_evidence.csv"))
    pe_cols = set(pe[0].keys()) if pe else set()
    add("pairwise_binding_columns_exist",
        {"model_a", "model_b", "median_delta_mase", "bh_adjusted_p_value", "comparison_status"}.issubset(pe_cols),
        f"has_cols={ {'model_a','model_b','median_delta_mase','bh_adjusted_p_value','comparison_status'} & pe_cols }")

    # --- Write results ---
    out_path = os.path.join(HERE, "audit_6_independent_verification_results.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["check_name", "status", "evidence", "created_timestamp"])
        for name, status, evidence in checks:
            w.writerow([name, status, evidence, TS])

    failed = [c for c in checks if c[1] == "FAIL"]
    print(f"Audit #6 independent verification: {len(checks)} checks, {len(failed)} failed")
    for name, status, evidence in failed:
        print(f"  FAIL: {name} -> {evidence}")
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()
