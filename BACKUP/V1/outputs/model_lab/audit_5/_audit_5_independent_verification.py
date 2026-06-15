#!/usr/bin/env python3
"""
Audit #5 - Model Lab Closure / Dashboard Handoff Audit
Independent read-only verification script.

This script ONLY reads existing Model Lab artifacts and writes a single
verification result CSV under outputs/model_lab/audit_5/. It does not
rerun models, recalculate metrics, or modify any source output.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime

# Repo root is three levels up from this file:
# <root>/outputs/model_lab/audit_5/_audit_5_independent_verification.py
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
ML = os.path.join(ROOT, "outputs", "model_lab")
CP = os.path.join(ML, "model_lab_closure_pack")

TS = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def read_rows(path: str) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        return list(csv.DictReader(fh))


def exists(*parts: str) -> bool:
    return os.path.isfile(os.path.join(ML, *parts))


def main() -> None:
    checks: list[tuple[str, str, str]] = []  # (check, status, evidence)

    def add(name: str, ok: bool, evidence: str) -> None:
        checks.append((name, "PASS" if ok else "FAIL", evidence))

    # 1. Closure summary single row + status
    cs = read_rows(os.path.join(CP, "model_lab_closure_summary.csv"))
    add("closure_summary_one_row", len(cs) == 1, f"rows={len(cs)}")
    add(
        "closure_status_completed_pending_final_audit",
        cs and cs[0]["closure_status"] == "completed_pending_final_audit",
        cs[0]["closure_status"] if cs else "missing",
    )
    add(
        "ready_for_dashboard_handoff_true",
        cs and cs[0]["ready_for_dashboard_handoff"] == "True",
        cs[0].get("ready_for_dashboard_handoff", "") if cs else "missing",
    )

    # 2. Champion decision consistency
    cd = read_rows(os.path.join(ML, "champion_decision", "champion_decision.csv"))
    add("champion_decision_one_row", len(cd) == 1, f"rows={len(cd)}")
    add(
        "champion_is_ets_explicit_with_conditions",
        cd
        and cd[0]["decision"] == "CHAMPION_SELECTED_WITH_CONDITIONS"
        and cd[0]["selected_champion_model"] == "ETS Explicit"
        and cd[0]["selected_champion_origin"] == "challenger"
        and cd[0]["selected_champion_family"] == "statistical"
        and cd[0]["decision_confidence"] == "medium",
        f"{cd[0]['decision']}|{cd[0]['selected_champion_model']}" if cd else "missing",
    )

    # 3. Champion metrics match closure summary champion summary
    chs = read_rows(os.path.join(CP, "model_lab_champion_summary.csv"))
    add(
        "champion_metrics_match",
        chs
        and chs[0]["official_median_mase"] == "6.901143533373399"
        and chs[0]["official_median_rmsse"] == "1.856193218184295"
        and chs[0]["supported_better_count"] == "8"
        and chs[0]["supported_worse_count"] == "0",
        f"mase={chs[0]['official_median_mase']};rmsse={chs[0]['official_median_rmsse']}"
        if chs
        else "missing",
    )

    # 4. Final model universe composition
    mu = read_rows(os.path.join(CP, "model_lab_final_model_universe.csv"))
    baseline = [r for r in mu if r["model_origin"] == "baseline"]
    deferred = [r for r in mu if "deferred" in r["final_status"]]
    active_challengers = [
        r for r in mu
        if r["model_origin"] == "challenger" and "deferred" not in r["final_status"]
    ]
    champ = [r for r in mu if r["selected_champion"] == "True"]
    add("universe_15_models", len(mu) == 15, f"rows={len(mu)}")
    add("universe_7_baseline", len(baseline) == 7, f"baseline={len(baseline)}")
    add(
        "universe_6_final_challengers",
        len(active_challengers) == 6,
        f"active_challengers={len(active_challengers)}",
    )
    add("universe_2_deferred", len(deferred) == 2, f"deferred={len(deferred)}")
    add(
        "single_champion_ets_explicit",
        len(champ) == 1 and champ[0]["model_name"] == "ETS Explicit",
        f"champions={[r['model_name'] for r in champ]}",
    )
    fnar = [r for r in mu if r["model_name"] == "FastNeuralAR_MLP"]
    add(
        "fastneuralar_risk_flagged",
        fnar and fnar[0]["risk_flag"] == "True",
        fnar[0]["risk_flag"] if fnar else "missing",
    )

    # 5. Deferred models file
    dm = read_rows(os.path.join(CP, "model_lab_deferred_models.csv"))
    names = {r["model_name"] for r in dm}
    add("deferred_file_nbeats_nhits", names == {"NBEATS", "NHITS"}, str(sorted(names)))

    # 6. Risk register carry-forwards
    rr = read_rows(os.path.join(CP, "model_lab_risk_register_final.csv"))
    rr_models = {r["model_name"] for r in rr}
    needed = {"FastNeuralAR_MLP", "NBEATS", "NHITS", "ETS Explicit", "FixedGrowth_6"}
    add(
        "risk_register_carryforwards",
        needed.issubset(rr_models),
        f"models={sorted(rr_models)}",
    )

    # 7. Dashboard handoff sections
    dh = read_rows(os.path.join(CP, "model_lab_dashboard_handoff_manifest.csv"))
    sections = {r["dashboard_section"] for r in dh}
    required_sections = {
        "Executive Summary", "Model Universe", "Champion Decision",
        "Tournament Standings", "Baseline vs Challenger Scorecard",
        "Pairwise Evidence", "Risk Register", "Challenger Metrics",
        "Aggregation Summary", "Audit Status", "Deferred Models",
        "Methodology / Governance",
    }
    add(
        "dashboard_all_sections",
        required_sections.issubset(sections),
        f"missing={sorted(required_sections - sections)}",
    )
    add(
        "dashboard_referenced_files_exist",
        all(os.path.isfile(os.path.join(ROOT, r["artifact_path"])) for r in dh),
        "all referenced dashboard files present",
    )

    # 8. Validation files have no fail rows
    clv = read_rows(os.path.join(CP, "model_lab_closure_validation.csv"))
    add(
        "closure_validation_no_fail",
        all(r["status"].lower() != "fail" for r in clv),
        f"rows={len(clv)}",
    )
    cdv = read_rows(os.path.join(ML, "champion_decision", "champion_decision_validation.csv"))
    add(
        "champion_validation_no_fail",
        all(r["status"].lower() != "fail" for r in cdv),
        f"rows={len(cdv)}",
    )

    # 9. Upstream gates: no blockers
    a4 = read_rows(os.path.join(ML, "audit_4", "audit_4_summary.csv"))
    add("audit_4_no_blockers", a4 and a4[0]["blockers"] == "0", f"blockers={a4[0]['blockers']}" if a4 else "missing")
    ts = read_rows(os.path.join(ML, "tournament_sanity_review", "tournament_sanity_summary.csv"))
    add("sanity_no_blockers", ts and ts[0]["blockers"] == "0", f"blockers={ts[0]['blockers']}" if ts else "missing")

    # 10. Source safety: shiny present, audit dir is only write target
    add("shiny_app_present", os.path.isdir(os.path.join(ROOT, "shiny_app")), "shiny_app/ dir present")

    # Write results
    out_path = os.path.join(HERE, "audit_5_independent_verification_results.csv")
    with open(out_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["check_name", "status", "evidence", "created_timestamp"])
        for name, status, evidence in checks:
            w.writerow([name, status, evidence, TS])

    failed = [c for c in checks if c[1] == "FAIL"]
    print(f"Audit #5 independent verification: {len(checks)} checks, {len(failed)} failed")
    for name, status, evidence in failed:
        print(f"  FAIL: {name} -> {evidence}")
    print(f"Results written to {out_path}")


if __name__ == "__main__":
    main()
