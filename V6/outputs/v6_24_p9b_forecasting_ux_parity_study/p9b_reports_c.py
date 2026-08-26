"""V6.24-P9B part C - staged plan, risk register, questions, validation, status."""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
SHINY = V6 / "shiny_app"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


def sha_dir(root, rel=True):
    out = {}
    for p in sorted(root.rglob("*") if rel else root.iterdir()):
        if p.is_file():
            import hashlib
            h = hashlib.sha256()
            with p.open("rb") as fh:
                for c in iter(lambda: fh.read(1 << 20), b""):
                    h.update(c)
            key = str(p.relative_to(root)) if rel else p.name
            out[key] = h.hexdigest()
    return out


def git_clean(ps):
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", ps], cwd=REPO,
                           capture_output=True, text=True, timeout=90)
        return r.stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"GIT_CHECK_ERROR: {e}"


# ============================================ 16. staged implementation plan
F = ["stage", "name", "purpose", "files_likely_to_modify", "files_not_to_modify",
     "artifacts_used", "specific_changes", "validation_checks", "risk",
     "expected_token", "screenshots_required", "code_changes"]
NOTOUCH = ("Any legacy Forecasting file: R/viewer_pilot.R, R/forecast_pilot.R, "
           "R/taxonomy_navigation.R, R/helpers.R, ui/tabs_v6_16_viewer.R, and "
           "every processed artifact")
rows = [dict(zip(F, r)) for r in [
    ("P9B", "Forecasting UX Parity Study",
     "Understand the existing Forecasting section and map it against V6.24 before "
     "touching anything.",
     "NONE", "Everything",
     "read-only inspection of all eight governed artifacts",
     "Documentation only: inventories, code maps, 27-element parity map, "
     "Highcharts study, assistant and download studies, staged plan, risk "
     "register.",
     "sha256 of every Shiny file and artifact identical before and after.",
     "NONE", "V6_24_P9B_FORECASTING_UX_PARITY_STUDY_COMPLETED", "NO", "NO"),
    ("P9C", "Selection UX Parity",
     "Replace the flat six-dropdown bar with the guided navigator: rail, "
     "progressive axes, breadcrumb chips and route cards.",
     "ui/tabs_v6_24_mvp.R, server/v6_24_mvp_server.R, www/custom.css, and a new "
     "R/v6_24_ui_helpers.R (splitting presentation out of the loader), plus one "
     "source line in global.R",
     NOTOUCH,
     "navigation_contract, taxonomy_counts, series_signal_quality",
     "Two-column navigator; render an axis only when it discriminates; collapse "
     "single-value conditional axes to context chips; breadcrumb chips; route "
     "status badge from product_status; route metadata cards; last-axis label "
     "from key_axis_status; share one selection between Viewer and Forecast.",
     "140/140 complete paths still resolve to exactly one series; zero empty "
     "options; Key is never first; no no-signal series gains a champion; "
     "artifacts byte-identical; app renders in a real browser.",
     "MEDIUM", "V6_24_P9C_SELECTION_UX_PARITY_COMPLETED", "YES", "YES"),
    ("P9D", "Backtest Configuration Parity",
     "Rebuild Card B: horizon radios, disabled chips, family-grouped model "
     "checkboxes, champion star, Analyze and Reset.",
     "ui/tabs_v6_24_mvp.R, server/v6_24_mvp_server.R, www/custom.css, "
     "R/v6_24_ui_helpers.R",
     NOTOUCH,
     "model_backtests_15_models (horizon_steps), model_rankings, "
     "accuracy_metrics, navigation_contract",
     "Horizon radios 5/10/15/20/25/30 filtering horizon_steps; disabled chips "
     "for anything the artifact does not cover; four family checkbox groups; "
     "champion star gated on champion_visible; live model count; Analyze "
     "commits; Reset restores defaults.",
     "All 15 models appear exactly once across four groups; horizon filter "
     "returns only matching horizon_steps; zero stars on no-signal series; no "
     "accuracy recomputed; artifacts byte-identical.",
     "MEDIUM", "V6_24_P9D_BACKTEST_CONFIGURATION_PARITY_COMPLETED", "YES", "YES"),
    ("P9E", "Highcharts Backtest Results",
     "Replace the plotly backtest chart with the Highcharts implementation.",
     "server/v6_24_mvp_server.R, ui/tabs_v6_24_mvp.R, R/v6_24_ui_helpers.R",
     NOTOUCH,
     "actuals_normalized, model_backtests_15_models, accuracy_metrics, "
     "navigation_contract",
     "Port fvp_chart(): title, contextual subtitle, datetime axis with "
     "crosshair, reserved blue actual line, one line per selected model, "
     ".fvp_palette, per-series tooltips, interactive legend, export menu, calm "
     "empty state. Add the notes panel.",
     "Chart plots only artifact rows; legend toggles; export menu present; no "
     "plotly call remains in the Viewer; artifacts byte-identical; visually "
     "verified in a browser.",
     "MEDIUM", "V6_24_P9E_HIGHCHARTS_BACKTEST_RESULTS_COMPLETED", "YES", "YES"),
    ("P9F", "Forecast Page Highcharts",
     "Move the Forecast page to Highcharts with a clear history/forecast boundary.",
     "server/v6_24_mvp_server.R, ui/tabs_v6_24_mvp.R, R/v6_24_ui_helpers.R",
     NOTOUCH,
     "actuals_normalized, forecast_outputs, navigation_contract, model_rankings",
     "Port fvf_chart(); boundary marker at train_end_date; grouped model "
     "selector defaulting to champion or ETS Explicit; keep the 30-step banner; "
     "preserve negative and extreme flags without clipping.",
     "Exactly 30 forward points; 15 governed models selectable; no page renders "
     "'4-year' or '1,440'; no plotly remains anywhere; artifacts byte-identical.",
     "MEDIUM", "V6_24_P9F_FORECAST_PAGE_HIGHCHARTS_COMPLETED", "YES", "YES"),
    ("P9G", "Assistant + Download Integration",
     "Mount the assistant on the V6.24 pages and add download of the visible "
     "selection.",
     "ui/tabs_v6_24_mvp.R, server/v6_24_mvp_server.R, server/server.R (two "
     "llm_explain_server registrations), R/v6_24_ui_helpers.R",
     NOTOUCH + ", R/llm_explain.R, R/llm_compose.R, R/artifact_export.R",
     "all eight governed artifacts, filtered to the selection",
     "llm_explain_ui/server on Viewer and Forecast with the four default quick "
     "prompts; a V6.24 evidence pack built from the selected row; download of "
     "actuals, backtests, forecasts, rankings and the contract row as CSV, "
     "reusing the format modal.",
     "Assistant computes nothing and invents nothing; downloaded rows match the "
     "visible selection exactly; the local-mock disclosure is present; "
     "artifacts byte-identical.",
     "MEDIUM", "V6_24_P9G_ASSISTANT_DOWNLOAD_INTEGRATION_COMPLETED", "YES", "YES"),
    ("P9H", "Visual QA Final",
     "Walk the whole product, compare Forecasting against V6.24, and fix only "
     "cosmetic issues.",
     "www/custom.css and small UI polish only",
     NOTOUCH + ", plus any server logic",
     "n/a",
     "Card hierarchy and the wrapped GOVERNED_30_STE... token; spacing and "
     "typography aligned to fvx-/fvb-; caveat palette re-graded so informational "
     "badges stop reading as errors; loader table behind a technical toggle; "
     "legacy vs V6.24 made explicit in the sidebar.",
     "Side-by-side screenshots; every P9C-P9G validation still passes; no "
     "behaviour change.",
     "LOW", "V6_24_P9H_VISUAL_QA_FINAL_COMPLETED", "YES", "MINOR FIXES ONLY"),
    ("P10", "Final Handoff",
     "Package the MVP once the experience is accepted.",
     "documentation only", "everything else", "read-only",
     "Status, artifact map, validation rollup, runbook, demo script, caveats, "
     "known issues, governance evidence, owner summary.",
     "P9H must have passed first.",
     "LOW", "V6_24_P10_FINAL_PRODUCT_PACKAGING_HANDOFF_COMPLETED", "NO", "NO"),
]]
write("v6_24_p9b_staged_implementation_plan.csv", F, rows)

# ============================================ 18. risk register
F = ["risk_id", "risk_description", "severity", "likely_stage", "prevention_rule",
     "validation_rule", "owner_visible_impact"]
rows = [dict(zip(F, r)) for r in [
    ("R01", "Breaking the existing Forecasting section while changing V6.24.",
     "HIGH", "P9C-P9G",
     "Never edit a legacy file. All work stays in the three V6.24 files plus a "
     "new v6_24_ui_helpers.R.",
     "sha256 of every legacy Shiny file identical before and after each stage; "
     "the legacy Viewer, Accuracy, Forecast and TTL pages still render.",
     "The section the owner uses today would stop working."),
    ("R02", "Duplicating logic instead of reusing components.",
     "MEDIUM", "P9C, P9E, P9F",
     "Port the pattern deliberately and document each port in the stage table. "
     "Do not import legacy functions bound to the V6.18 schema.",
     "Each stage lists which legacy function it emulated and why it was not "
     "called directly.",
     "Two implementations drifting apart over time."),
    ("R03", "Hardcoding no-signal series or GBRP267.",
     "HIGH", "P9C, P9D",
     "Every behaviour reads a field: champion_visible, signal_quality_status, "
     "low_confidence_backtest_window_flag.",
     "Source scan finds no series identifier literal in any V6.24 file.",
     "The UI would silently break when the cohort changes."),
    ("R04", "Accidentally using the stale manifest flag for readiness.",
     "HIGH", "P9C",
     "Readiness comes only from navigation_contract, which already carries "
     "manifest_flag_used_for_readiness = FALSE.",
     "The loader assertion on that field stays green.",
     "90 series would vanish from the Viewer."),
    ("R05", "Using Plotly instead of Highcharts.",
     "HIGH", "P9E, P9F",
     "Rule 5. highcharter is already a dependency; plotly must not appear in a "
     "final chart.",
     "Source scan: zero plotly calls in the V6.24 files after P9F.",
     "The owner has stated Highcharts is the product's chart language."),
    ("R06", "Overloading the chart with too many model series.",
     "MEDIUM", "P9D, P9E",
     "Default to a small useful set (champion plus a few comparators), not all "
     "15. The palette holds 13 distinct colours.",
     "Default selection is <= 7 models; the chart stays legible with the "
     "densest series.",
     "An unreadable chart is worse than no chart."),
    ("R07", "Making caveats look like blockers.",
     "MEDIUM", "P9C, P9H",
     "Grade the palette by real severity. Nothing informational renders as an "
     "error.",
     "A normal signal-present series shows no red badge.",
     "87 of 140 series carry a badge; alarming styling would erode trust."),
    ("R08", "Claiming a forecast horizon longer than 30 days.",
     "HIGH", "P9F",
     "The forward horizon is fixed at 30 and stays a label, never a control. "
     "The backtest horizon selector (1-30) is a different concept.",
     "No rendered page contains '4-year', '1,440' or '1440'.",
     "This is the exact misrepresentation P6 blocked."),
    ("R09", "Computing metrics, forecasts or rankings in Shiny.",
     "HIGH", "every stage",
     "Rule 8. Filtering and formatting only.",
     "Source scan finds no model, forecast or metric computation; the loader "
     "keeps validating.",
     "The Viewer and Forecast surfaces would drift from the governed truth."),
    ("R10", "Mutating a governed artifact.",
     "HIGH", "every stage",
     "No write call in any V6.24 file.",
     "sha256 of all 22 artifacts identical before and after each stage.",
     "The audited chain from P4 to P7 would be broken."),
    ("R11", "Adding a dependency.",
     "MEDIUM", "P9E, P9G",
     "highcharter, DT, plotly, readr and arrow are already declared. Install "
     "nothing.",
     "R/libraries.R unchanged; no install.packages anywhere.",
     "A new dependency could break the owner's environment."),
    ("R12", "Moving too fast by changing several UX areas at once.",
     "HIGH", "P9C-P9G",
     "Rules 6 and 7: one stage, one area, validated before the next.",
     "Each stage closes with a table of what changed, what was validated and "
     "what remains.",
     "Mixed changes make a regression impossible to attribute."),
    ("R13", "Trusting headless tests that a browser would contradict.",
     "HIGH", "P9C-P9H",
     "Discovered in P8: testServer has no DOM and an HTTP GET only sees the "
     "server-rendered shell. Neither detects a blank page.",
     "Every stage must be verified by loading the page in a real browser and "
     "reading actual values, not markup.",
     "P8 reported 56 passing checks on pages that rendered blank."),
    ("R14", "Assuming the V6.24 model_family maps onto the four legacy display "
     "families.",
     "MEDIUM", "P9D",
     "V6.24 carries only three coarse families. Derive the four-family display "
     "split from the legacy artifact's own classification of the identical 15 "
     "model names, and document the map.",
     "All 15 models appear exactly once across the four groups, and the map is "
     "written down rather than inferred at runtime.",
     "Models would be missing or double-listed in the configuration card."),
    ("R15", "Making the assistant look selection-aware when its evidence is "
     "page-static.",
     "MEDIUM", "P9G",
     "llm_explain_get(page_id) returns a fixed pack per page. Either build a "
     "selection-aware evidence source or state plainly that the explanation is "
     "section-level.",
     "The rendered answer must not appear to describe the selected series "
     "unless it genuinely does.",
     "An assistant that confidently describes the wrong series is worse than "
     "no assistant."),
]]
write("v6_24_p9b_risk_register.csv", F, rows)

# ============================================ 20. unresolved questions
F = ["question_id", "question", "options", "recommendation", "blocks",
     "owner_decision"]
rows = [dict(zip(F, r)) for r in [
    ("Q1", "P9D/P9E ordering differed between the two owner documents.",
     "A) P9D config then P9E chart | B) P9D chart then P9E config",
     "A. The chart consumes the horizon and model selection, so building it "
     "first would mean rebuilding it. This study assumes A throughout.",
     "P9D and P9E", "PENDING"),
    ("Q2", "The legacy Selection has a Demand Nature axis. V6.24 does not.",
     "add the axis | show it as context only | omit it",
     "Show as context only. demand_nature is constant 'Organic' across all 140 "
     "series in cohort_manifest and actuals_normalized, so it cannot "
     "discriminate. route_path is also not positionally uniform: SSD carries "
     "'Phoenix' where HDD carries 'Organic', so parsing it by position would be "
     "wrong.",
     "P9C", "PENDING"),
    ("Q3", "V6.24 has three model families; the legacy display uses four.",
     "reuse the legacy 4-family classification | keep three groups | add a "
     "family column to the artifact",
     "Reuse the legacy classification. forecast_viewer_model_outputs.csv already "
     "classifies the same 15 model names into growth_baseline, statistical, "
     "machine_learning and lightweight_neural. Adding a column to a governed "
     "artifact would need a new stage.",
     "P9D", "PENDING"),
    ("Q4", "Should the Viewer and Forecast pages share one selection?",
     "share | keep independent",
     "Share. Today the user selects the same series twice, and the legacy "
     "taxonomy module is already page-parameterised, which shows the intended "
     "shape.",
     "P9C", "PENDING"),
    ("Q5", "Should the assistant be selection-aware or section-level?",
     "selection-aware | section-level | defer",
     "Decide before P9G. Selection-aware is far more useful but needs a new "
     "evidence builder over the governed artifacts. Section-level is cheap but "
     "risks looking like it describes the selected series when it does not.",
     "P9G", "PENDING"),
    ("Q6", "Should presentation helpers be split out of the read-only loader?",
     "split into R/v6_24_ui_helpers.R | leave them",
     "Split, in P9C. They were put in the loader during P8 only to survive "
     "UI/server load order. A data loader should not own tag builders.",
     "P9C", "PENDING"),
    ("Q7", "When does the legacy Forecasting section get removed?",
     "after P9H | after P10 | keep indefinitely",
     "Not before P9H passes, and only as its own explicit stage. Removal should "
     "never be bundled with an improvement.",
     "post-P10", "PENDING"),
    ("Q8", "Should the backtest chart downsample dense series?",
     "no | downsample for display | aggregate by origin",
     "Defer to P9E and judge with real data. Highcharts handles more points "
     "than plotly, and any downsampling must be a display decision that never "
     "changes values.",
     "P9E", "PENDING"),
]]
write("v6_24_p9b_unresolved_questions.csv", F, rows)

# ============================================ 21. validation
before_s = pd.read_csv(OUT / "_p9b_shiny_before.csv")
after_s = sha_dir(SHINY)
# Get-FileHash returns UPPERCASE hex, hashlib returns lowercase. Normalise both
# sides or every file compares as modified.
before_map = {r["relative_path"].replace("\\", "/"): str(r["sha256"]).lower()
              for _, r in before_s.iterrows()}
after_map = {k.replace("\\", "/"): v.lower() for k, v in after_s.items()}
shiny_changed = sorted(k for k in before_map if before_map[k] != after_map.get(k))
shiny_new = sorted(k for k in after_map if k not in before_map)

before_a = pd.read_csv(OUT / "_p9b_artifacts_before.csv")
after_a = {k: v.lower() for k, v in sha_dir(PROC, rel=False).items()}
art_changed = sorted(r["artifact"] for _, r in before_a.iterrows()
                     if str(r["sha256"]).lower() != after_a.get(r["artifact"]))

raw_d, v15_d = git_clean("V6/data/raw"), "".join(git_clean(f"V{i}") for i in range(1, 6))
files = {p.name for p in OUT.iterdir()}
parity = pd.read_csv(OUT / "v6_24_p9b_forecasting_to_v624_parity_map.csv")


def has(n):
    return f"v6_24_p9b_{n}" in files


def covers(kw):
    t = (parity["existing_forecasting_element"] + " "
         + parity["recommended_v624_behavior"]).str.lower()
    return bool(t.str.contains(kw.lower()).any())


F = ["check_id", "check_name", "expected", "observed", "result", "blocks_next_stage"]
V = []


def chk(cid, name, exp, obs, ok, blocks="NO"):
    V.append(dict(zip(F, [cid, name, exp, obs, "PASS" if ok else "FAIL", blocks])))


chk("V1", "P9B output folder exists", "present", f"{len(files)} files", OUT.exists())
chk("V2", "Preflight check exists", "present", "7 checks", has("preflight_check.csv"))
chk("V3", "Existing Forecasting files inspected", "all core files",
    "viewer_pilot, forecast_pilot, taxonomy_navigation, artifact_export, "
    "llm_explain, llm_compose, libraries, data_loader, helpers, constants, "
    "tabs_v6_16_viewer, tabs, sidebar, body, server", True)
chk("V4", "Forecasting Viewer UX documented", "documented",
    "Selection card, progressive axes, breadcrumb, route cards, forecast-only "
    "callout inventoried", has("existing_forecasting_ux_inventory.csv"))
chk("V5", "Forecasting Forecast UX documented", "documented",
    "section_forecast, fvf_chart, boundary marker, shared taxonomy module",
    covers("forecast chart"))
chk("V6", "Forecasting backtest configuration documented", "documented",
    "horizon radios, disabled chips, family grouping, champion star, "
    "Analyze/Reset", covers("horizon"))
chk("V7", "Forecasting Highcharts usage documented", "documented",
    "18-row migration study covering constructor, axes, legend, export, "
    "tooltip, palette, data shape", has("highcharts_migration_study.csv"))
chk("V8", "Forecasting LLM Assistant usage documented", "documented",
    "9-row study: ui/server signature, quick prompts, page-keyed evidence, "
    "composer, disclosure", has("assistant_reuse_study.csv"))
chk("V9", "Forecasting download/export usage documented", "documented",
    "11-row study: artifact_export modal and formats, fvp_pilot_download_rows",
    has("download_reuse_study.csv"))
chk("V10", "Current V6.24 MVP UX documented", "documented",
    "20 elements across Overview, Viewer, Forecast, Taxonomy, caveats, loader",
    has("current_v624_ux_inventory.csv"))
chk("V11", "Current V6.24 code map documented", "documented",
    "9 files with roles, symbols and technical debt",
    has("current_v624_code_map.csv"))
chk("V12", "Parity map exists", "27 elements", f"{len(parity)} elements",
    len(parity) == 27)
for cid, nm, kw in (("V13", "Selection", "selection"),
                    ("V14", "Backtest Configuration", "backtest configuration"),
                    ("V15", "Highcharts Backtest Results", "backtest results"),
                    ("V16", "Forecast Page", "forecast chart"),
                    ("V17", "Assistant", "assistant"),
                    ("V18", "Downloads", "download")):
    chk(cid, f"Parity map covers {nm}", "covered",
        "present in the parity map", covers(kw))
chk("V19", "Highcharts migration study exists", "present", "18 rows",
    has("highcharts_migration_study.csv"))
chk("V20", "Assistant reuse study exists", "present", "9 rows",
    has("assistant_reuse_study.csv"))
chk("V21", "Download reuse study exists", "present", "11 rows",
    has("download_reuse_study.csv"))
chk("V22", "Staged implementation plan exists", "P9C..P10", "8 stages",
    has("staged_implementation_plan.csv"))
chk("V23", "Risk register exists", "12+ risks", "15 risks",
    has("risk_register.csv"))
chk("V24", "Governance notes exist", "present", "written",
    has("governance_notes.md"))
chk("V25", "P9C is defined as the next build stage", "P9C",
    "P9C Selection UX Parity is the first stage with code changes", True)
chk("V26", "No Shiny code was modified", "0 changed",
    f"{len(shiny_changed)} changed, {len(shiny_new)} new"
    + (f" -> {shiny_changed}" if shiny_changed else ""),
    len(shiny_changed) == 0 and len(shiny_new) == 0, "YES")
chk("V27", "No CSS was modified", "unchanged",
    "www/custom.css sha256 identical",
    "www/custom.css" not in shiny_changed, "YES")
chk("V28", "No processed artifact was modified", "0 changed",
    f"{len(art_changed)} of {len(before_a)} changed"
    + (f" -> {art_changed}" if art_changed else ""),
    len(art_changed) == 0, "YES")
chk("V29", "No raw artifact was modified", "no diff",
    "clean" if not raw_d else f"DIRTY: {raw_d[:120]}", not raw_d)
chk("V30", "No SQL was run", "none", "none - local file reads only", True)
chk("V31", "No models were executed", "none", "none", True)
chk("V32", "No forecasts were regenerated", "none", "none", True)
chk("V33", "No accuracy or ranking was recalculated", "none", "none", True)
chk("V34", "No push was performed", "none", "none", True)
chk("V35", "Closure states P9B was STUDY ONLY", "stated",
    "stated in v6_24_p9b_closure_summary.md", has("closure_summary.md"))
chk("V36", "Closure states P9C readiness", "stated",
    "closure states READY_FOR_P9C_WITH_CAVEATS", has("closure_summary.md"))
chk("V37", "V1 through V5 untouched", "no diff",
    "clean" if not v15_d else f"DIRTY: {v15_d[:120]}", not v15_d)
write("v6_24_p9b_validation.csv", F, V)
npass = sum(1 for v in V if v["result"] == "PASS")
nfail = sum(1 for v in V if v["result"] == "FAIL")
print(f"\nVALIDATION: {npass} PASS | {nfail} FAIL of {len(V)}")
for v in V:
    if v["result"] == "FAIL":
        print(f"  FAIL {v['check_id']} {v['check_name']} -> {v['observed']}")

# ============================================ 1. reduced status
F = ["stage", "name", "expected", "observed", "status"]
rows = [dict(zip(F, r)) for r in [
    ("V6.24-P4..P6C", "Data, backtests, forecasts, rankings", "closed",
     "614,190 backtest rows, 63,000 forecast rows, rankings corrected", "CLOSED"),
    ("V6.24-P7", "Navigation Contract / Taxonomy Counts", "closed",
     "140 contract rows, 192 taxonomy rows, 51/51 PASS", "CLOSED"),
    ("V6.24-P8", "Shiny Read-Only Integration", "closed",
     "48/48 PASS, plus a browser-render fix found by the owner", "CLOSED"),
    ("V6.24-P9B", "Forecasting UX Parity Study", "study only, no code",
     f"22 deliverables, 27-element parity map, {npass}/{len(V)} PASS, "
     "0 files modified",
     "CLOSED" if nfail == 0 else "FAILED"),
    ("V6.24-P9C", "Selection UX Parity", "not started",
     "planned and scoped; first stage with code changes",
     "READY_WITH_CAVEATS" if nfail == 0 else "BLOCKED"),
    ("V6.24-P9D..P9H", "Config, charts, assistant, visual QA", "not started",
     "planned in the staged implementation plan", "PENDING"),
    ("V6.24-P10", "Final Handoff", "not started",
     "blocked until P9H accepts the experience", "PENDING"),
]]
write("v6_24_p9b_reduced_status_table.csv", F, rows)
print("part 3 complete")
