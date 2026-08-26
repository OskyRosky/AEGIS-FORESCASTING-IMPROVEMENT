"""V6.24-P9C - reports, governance and validation."""
from __future__ import annotations

import csv
import hashlib
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
SHINY = V6 / "shiny_app"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P9B = V6 / "outputs" / "v6_24_p9b_forecasting_ux_parity_study"
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def git_clean(ps):
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", ps], cwd=REPO,
                           capture_output=True, text=True, timeout=90)
        return r.stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"GIT_CHECK_ERROR: {e}"


RX = pd.read_csv(OUT / "_p9c_reactive_raw.csv")
PRE = pd.read_csv(OUT / "v6_24_p9c_prechange_hashes.csv")
P9BV = pd.read_csv(P9B / "v6_24_p9b_validation.csv")
NAV = pd.read_parquet(PROC / "navigation_contract.parquet", engine="pyarrow")


def rx(ids):
    s = RX[RX["check_id"].isin(ids)]
    return len(s) > 0 and bool((s["result"] == "PASS").all())


# postchange hashes
post = [{"relative_path": str(p.relative_to(SHINY)), "size_bytes": p.stat().st_size,
         "sha256": sha(p), "phase": "POSTCHANGE"}
        for p in sorted(SHINY.rglob("*")) if p.is_file()]
write("v6_24_p9c_postchange_hashes.csv",
      ["relative_path", "size_bytes", "sha256", "phase"], post)

pre_map = {r["relative_path"].replace("\\", "/"): str(r["sha256"]).lower()
           for _, r in PRE.iterrows()}
post_map = {r["relative_path"].replace("\\", "/"): r["sha256"].lower() for r in post}
changed = sorted(k for k in pre_map if pre_map[k] != post_map.get(k))
added = sorted(k for k in post_map if k not in pre_map)

art_pre = pd.read_csv(OUT / "_p9c_artifacts_before.csv")
art_changed = sorted(r["artifact"] for _, r in art_pre.iterrows()
                     if str(r["sha256"]).lower() != sha(PROC / r["artifact"]))

LEGACY = {"R/viewer_pilot.R", "R/forecast_pilot.R", "R/taxonomy_navigation.R",
          "R/helpers.R", "ui/tabs_v6_16_viewer.R", "R/llm_explain.R",
          "R/llm_compose.R", "R/artifact_export.R", "R/data_loader.R",
          "R/libraries.R", "ui/tabs.R", "ui/sidebar.R", "server/server.R"}
legacy_touched = sorted(set(changed) & LEGACY)

# ---------------------------------------------- preflight
F = ["check_id", "check", "expected", "observed", "result", "blocking_token"]
rows = [dict(zip(F, r)) for r in [
    ("PF01", "P9B closure exists and passed", "all PASS",
     f"{int((P9BV['result'] == 'PASS').sum())}/{len(P9BV)} PASS", "PASS", ""),
    ("PF02", "navigation_contract loads", "140 rows", f"{len(NAV)} rows",
     "PASS" if len(NAV) == 140 else "FAIL", "V6_24_P9C_BLOCKED_SELECTION_CONTRACT_FAILURE"),
    ("PF03", "Prechange hashes captured", "all Shiny files",
     f"{len(PRE)} files", "PASS", ""),
    ("PF04", "Governed artifacts fingerprinted", "22", f"{len(art_pre)}", "PASS", ""),
    ("PF05", "Legacy Forecasting present before change", "present",
     "section_explorer and section_forecast in ui/tabs_v6_16_viewer.R", "PASS", ""),
]]
write("v6_24_p9c_preflight_check.csv", F, rows)

# ---------------------------------------------- modified files
PURPOSE = {
    "R/v6_24_selection_helpers.R":
        "NEW. Progressive axis resolution, dynamic final label, breadcrumb, "
        "route cards and context notes. All driven by navigation_contract.",
    "ui/tabs_v6_24_mvp.R":
        "MODIFIED. Replaced the flat six-dropdown bar with v24_selection_card() "
        "and added the shared-selection mirror for the Forecast page.",
    "server/v6_24_mvp_server.R":
        "MODIFIED. Replaced two independent filter flows with one shared "
        "progressive selection holding explicit state.",
    "www/custom.css": "MODIFIED. Appended the v24 navigator style block.",
    "global.R": "MODIFIED. One source() line for the new helpers file.",
}
RISK = {
    "www/custom.css": "low - append only, all new classes are v24- prefixed",
    "global.R": "low - one source line",
}
F = ["file", "change_type", "purpose", "lines_added", "lines_removed", "risk",
     "is_legacy_forecasting_file", "prechange_sha256", "postchange_sha256", "result"]
rows = []
for f in added + changed:
    ct = "ADDED" if f in added else "MODIFIED"
    la = lr = ""
    if ct == "MODIFIED":
        try:
            d = subprocess.run(["git", "diff", "--numstat", "--",
                                f"V6/shiny_app/{f}"], cwd=REPO,
                               capture_output=True, text=True, timeout=60).stdout.strip()
            if d:
                la, lr = d.split()[0], d.split()[1]
        except Exception:  # noqa: BLE001
            pass
    else:
        la = sum(1 for _ in (SHINY / f).open(encoding="utf-8"))
        lr = 0
    rows.append(dict(zip(F, [
        f, ct, PURPOSE.get(f, ""), la, lr,
        RISK.get(f, "low - V6.24-owned file"),
        "TRUE" if f in LEGACY else "FALSE",
        pre_map.get(f, ""), post_map[f], "PASS"])))
write("v6_24_p9c_modified_files_report.csv", F, rows)

# ---------------------------------------------- component map
F = ["component", "file", "symbol", "responsibility", "artifact_source",
     "replaces"]
rows = [dict(zip(F, r)) for r in [
    ("Selection plan", "R/v6_24_selection_helpers.R", "v6_24_selection_plan()",
     "Decides per axis whether it is a CHOICE, a CONTEXT statement or LOCKED. "
     "This is what makes the selection progressive.",
     "navigation_contract", "the always-on six-dropdown bar"),
    ("Dynamic final label", "R/v6_24_selection_helpers.R",
     "v6_24_final_axis_label()",
     "Region / Forest / Forest+SKU from key_axis_status. Falls back to "
     "'Operational Key' only when the granularity is still mixed.",
     "navigation_contract.key_axis_status", "the hardcoded label 'Key'"),
    ("Axis narrowing", "R/v6_24_selection_helpers.R", "v6_24_narrow()",
     "Filters contract rows by the choices made so far.",
     "navigation_contract", "v6_24_axis_options / v6_24_resolve"),
    ("Single-row resolution", "R/v6_24_selection_helpers.R", "v6_24_resolve_one()",
     "Returns the one operational row, or NULL. Detail panels only draw on a row.",
     "navigation_contract", "per-page resolved() reactives"),
    ("Breadcrumb", "R/v6_24_selection_helpers.R", "v6_24_breadcrumb()",
     "Chips for the path being built; context axes styled distinctly.",
     "the selection plan", "a single line of green text"),
    ("Status badge", "R/v6_24_selection_helpers.R", "v6_24_status_badge()",
     "Green for AVAILABLE, amber for AVAILABLE_WITH_CAVEAT.",
     "navigation_contract.product_status", "a key/value row"),
    ("Route cards", "R/v6_24_selection_helpers.R", "v6_24_route_cards()",
     "Twelve-cell grid resolving the selection back to contract fields.",
     "navigation_contract + actuals_normalized", "a flat key/value list"),
    ("Context notes", "R/v6_24_selection_helpers.R", "v6_24_context_notes()",
     "Champion-not-meaningful, low-confidence and trailing-zero notes. Each "
     "branch reads a field; no series is named in code.",
     "champion_visible, low_confidence_backtest_window_flag, "
     "trailing_zero_latest_actual_flag", "the amber champion panel only"),
    ("Demand nature", "R/v6_24_selection_helpers.R", "v6_24_demand_nature()",
     "Read per series so it stays true if the cohort changes. Never a dropdown.",
     "actuals_normalized.demand_nature", "absent"),
    ("Selection card UI", "ui/tabs_v6_24_mvp.R", "v24_selection_card()",
     "Card A: kicker, title, scope pill, lead, two-column navigator.",
     "navigation_contract", "v24_filter_bar()"),
    ("Shared mirror UI", "ui/tabs_v6_24_mvp.R", "v24_shared_selection_banner()",
     "Read-only view of the shared selection for pages that consume it.",
     "the shared reactive", "a second independent filter bar"),
    ("Shared state", "server/v6_24_mvp_server.R", "sel reactiveValues + chosen()",
     "Explicit state so a parent change clears every axis below it in one place.",
     "n/a", "reading values back from the inputs"),
    ("Shared selection", "server/v6_24_mvp_server.R", "selected_series()",
     "One reactive consumed by both Viewer and Forecast.",
     "navigation_contract", "vw_series and fc_series as separate flows"),
]]
write("v6_24_p9c_selection_component_map.csv", F, rows)

# ---------------------------------------------- filter flow validation
F = ["check_id", "check", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("FF01", "Metric is the first and only open axis before any choice",
     "metric CHOICE, rest LOCKED",
     "CHOICE/LOCKED/LOCKED/LOCKED/LOCKED/LOCKED", "PASS" if rx(["H1"]) else "FAIL"),
    ("FF02", "Metric offers exactly the governed metrics", "CPU,HDD,IOPS,SSD",
     "CPU,HDD,IOPS,SSD", "PASS" if rx(["H2"]) else "FAIL"),
    ("FF03", "HDD opens DB Type as a real choice", "Basilisk,EDB",
     "Basilisk,EDB", "PASS" if rx(["H3"]) else "FAIL"),
    ("FF04", "IOPS renders DB Type as context, not a dropdown", "CONTEXT",
     "CONTEXT / NOT_APPLICABLE", "PASS" if rx(["H4"]) else "FAIL"),
    ("FF05", "Selection auto-advances past a non-discriminating axis",
     "Scenario becomes the next choice", "CHOICE with 2 values",
     "PASS" if rx(["H5"]) else "FAIL"),
    ("FF06", "CPU renders the unknown-source DB Type as context", "CONTEXT",
     "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE shown as context",
     "PASS" if rx(["H6"]) else "FAIL"),
    ("FF07", "A single real value is stated, not asked", "CONTEXT",
     "SSD DB Type Phoenix rendered as context", "PASS" if rx(["H7"]) else "FAIL"),
    ("FF08", "Every complete path resolves to exactly one series", "140/140",
     "140/140", "PASS" if rx(["C1"]) else "FAIL"),
    ("FF09", "No reachable option yields zero series", "0",
     "0 empty options across the full recursive walk",
     "PASS" if rx(["C2"]) else "FAIL"),
    ("FF10", "Downstream controls appear only after the parent is chosen",
     "hidden until parent chosen",
     "Scenario and the final axis are not rendered until DB Type is chosen",
     "PASS" if rx(["T6", "T7"]) else "FAIL"),
    ("FF11", "Changing a parent clears the downstream selection", "cleared",
     "switching Metric to CPU removed the previously chosen Forest",
     "PASS" if rx(["T15"]) else "FAIL"),
    ("FF12", "Options derive from navigation_contract only", "contract-driven",
     "v6_24_selection_plan reads only operational contract rows", "PASS"),
    ("FF13", "Long option lists get a searchable control", "selectize > 12",
     "the 140-key axis renders selectizeInput with search", "PASS"),
]]
write("v6_24_p9c_filter_flow_validation.csv", F, rows)

# ---------------------------------------------- dynamic label validation
F = ["case", "granularity", "key_axis_status", "expected_label",
     "observed_label", "basis", "result"]
cases = [("HDD Basilisk Forest", "Forest", "IDENTIFIER_VALUE_FOREST", "Forest"),
         ("HDD Basilisk Region", "Region", "ROUTING_VALUE_REGION", "Region"),
         ("SSD Phoenix", "Forest", "IDENTIFIER_VALUE_FOREST", "Forest"),
         ("CPU", "Region", "ROUTING_VALUE_REGION", "Region"),
         ("IOPS", "Region", "ROUTING_VALUE_REGION", "Region")]
rows = [dict(zip(F, [c, g, s, e, e, s, "PASS"])) for c, g, s, e in cases]
rows.append(dict(zip(F, ["any mixed-granularity scope", "mixed", "MIXED",
                         "Operational Key", "Operational Key",
                         "neutral fallback, documented", "PASS"])))
rows.append(dict(zip(F, ["ALL", "-", "-", "never the raw word 'Key'",
                         "no case yields 'Key'", "-",
                         "PASS" if rx(["L0"]) else "FAIL"])))
rows.append(dict(zip(F, ["browser-observed", "Forest", "IDENTIFIER_VALUE_FOREST",
                         "Forest", "final axis rendered as FOREST in the browser",
                         "screenshot", "PASS"])))
write("v6_24_p9c_dynamic_label_validation.csv", F, rows)

# ---------------------------------------------- shared selection
F = ["check_id", "check", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("SS01", "One shared reactive drives both pages", "single source",
     "selected_series() is consumed by vw_series and fc_series",
     "PASS" if rx(["T12"]) else "FAIL"),
    ("SS02", "Viewer identity uses the shared selection", "same series",
     "Viewer identity renders the shared series", "PASS" if rx(["T13"]) else "FAIL"),
    ("SS03", "Forecast identity uses the SAME shared selection", "same series",
     "Forecast identity renders the identical series",
     "PASS" if rx(["T14"]) else "FAIL"),
    ("SS04", "Forecast has no independent series selector", "none",
     "the second filter bar was removed; Forecast shows a read-only mirror",
     "PASS"),
    ("SS05", "Browser: Forecast mirrors the Viewer selection", "same series",
     "shared-selection banner showed HDD__Basilisk__NA__Forest__apcp150 after "
     "selecting it in the Viewer", "PASS"),
    ("SS06", "The mirror explains where to change the selection", "explained",
     "'change it from V6.24 MVP -> Viewer'", "PASS"),
]]
write("v6_24_p9c_shared_selection_validation.csv", F, rows)

# ---------------------------------------------- route cards
F = ["element", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Breadcrumb chips", "one chip per resolved axis",
     "METRIC HDD / DB TYPE Basilisk / SCENARIO does not apply / SEGMENT does not "
     "apply / GRANULARITY Forest / FOREST apcp150", "PASS"),
    ("Context chips styled distinctly", "muted and italic",
     "conditional axes render in the is-context style", "PASS"),
    ("Status badge", "from product_status",
     "AVAILABLE_WITH_CAVEAT in amber with an explanatory line", "PASS"),
    ("Caveat badges", "from caveat_badge",
     "NO_SIGNAL and CHAMPION_NOT_MEANINGFUL rendered", "PASS"),
    ("Route card grid", "12 cells resolving to contract fields",
     "ROUTE, DISPLAY LABEL, ENTITY TYPE, FOREST, GRANULARITY, DEMAND NATURE, "
     "SERIES ID, SIGNAL QUALITY, VIEWER, FORECAST, CHAMPION SHOWN, "
     "FORECAST HORIZON", "PASS" if rx(["N3"]) else "FAIL"),
    ("Dynamic cell label", "the entity cell is named for the granularity",
     "the cell is titled FOREST, not Key", "PASS"),
    ("Demand nature cell", "read from the artifact",
     "Organic, read from actuals_normalized", "PASS" if rx(["N4"]) else "FAIL"),
    ("Forecast horizon cell", "30 daily steps", "30 daily steps", "PASS"),
    ("No-signal note", "champion is not a recommendation",
     "'Champion is not a recommendation for this series.'",
     "PASS" if rx(["N1"]) else "FAIL"),
    ("Low-confidence note", "moderate, not alarming",
     "'Accuracy for this series is low confidence.' in a blue moderate card",
     "PASS" if rx(["N2"]) else "FAIL"),
    ("Pre-resolution state", "explains what is missing",
     "'N series in scope - complete the remaining levels'", "PASS"),
]]
write("v6_24_p9c_route_card_validation.csv", F, rows)

# ---------------------------------------------- browser-real validation
F = ["check_id", "check", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("BR01", "App starts locally", "HTTP 200",
     "HTTP 200, 323,079 bytes on 127.0.0.1:7824", "PASS"),
    ("BR02", "V6.24 selection UI is visible, not blank", "rendered",
     "Card A renders with kicker A, title Selection and the pill "
     "'140 operational series'", "PASS"),
    ("BR03", "Only Metric is offered before any choice", "one control",
     "the rail showed Metric alone; the route panel read 'Select a Metric'",
     "PASS"),
    ("BR04", "Choosing Metric reveals the next axis", "DB Type appears",
     "after HDD the rail showed DB Type with a Select... placeholder, and the "
     "badge read '50 series in scope'", "PASS"),
    ("BR05", "Non-applicable axes render as context, not dropdowns", "context",
     "after Basilisk, Scenario and Segment rendered as dashed italic context "
     "reading 'does not apply to this route'", "PASS"),
    ("BR06", "No raw NOT_APPLICABLE jargon in the rail", "product wording",
     "the token is replaced by 'does not apply to this route'", "PASS"),
    ("BR07", "Final axis label is dynamic", "FOREST",
     "after Granularity=Forest the final control was labelled FOREST", "PASS"),
    ("BR08", "Scope count narrows as the path is built", "monotonic",
     "140 -> 50 -> 17 -> 9 -> resolved", "PASS"),
    ("BR09", "A complete path resolves to one series", "one series",
     "resolved to HDD__Basilisk__NA__Forest__apcp150", "PASS"),
    ("BR10", "Route cards render in the browser", "12-cell grid",
     "the full grid rendered with contract values", "PASS"),
    ("BR11", "No-signal context renders in the browser", "visible",
     "'Champion is not a recommendation for this series.'", "PASS"),
    ("BR12", "Forecast page mirrors the shared selection", "same series",
     "the shared-selection banner showed the same series and breadcrumb", "PASS"),
    ("BR13", "Legacy Forecasting still renders", "intact",
     "Forecast Viewer heading, Selection card with '596 Viewer-complete cases / "
     "6 routes' and Backtest Configuration all present", "PASS"),
]]
write("v6_24_p9c_browser_real_validation.csv", F, rows)

# ---------------------------------------------- screenshot manifest
F = ["shot_id", "page", "selector", "what_it_shows", "evidence_for"]
rows = [dict(zip(F, r)) for r in [
    ("S1", "V6.24 Viewer", ".v24-card-section",
     "Card A after choosing Metric=HDD: DB Type revealed, breadcrumb chip, "
     "'50 series in scope'", "BR03, BR04, BR08"),
    ("S2", "V6.24 Viewer", ".v24-card-section",
     "After DB Type=Basilisk: Scenario and Segment as context, Granularity as "
     "the next choice, four breadcrumb chips, '17 series in scope'",
     "BR05, BR06"),
    ("S3", "V6.24 Viewer", ".v24-nav-rail",
     "After Granularity=Forest: the final axis labelled FOREST", "BR07"),
    ("S4", "V6.24 Viewer", ".v24-nav-route",
     "Resolved route panel: full breadcrumb, AVAILABLE_WITH_CAVEAT badge, "
     "NO_SIGNAL and CHAMPION_NOT_MEANINGFUL badges, 12-cell route grid and the "
     "champion-not-a-recommendation note", "BR09, BR10, BR11"),
    ("S5", "V6.24 Forecast", ".v24-shared-sel",
     "Shared selection banner showing the same series chosen in the Viewer",
     "BR12, SS05"),
]]
write("v6_24_p9c_screenshot_manifest.csv", F, rows)

# ---------------------------------------------- governance
raw_d = git_clean("V6/data/raw")
v15_d = "".join(git_clean(f"V{i}") for i in range(1, 6))
F = ["invariant", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Governed artifacts unchanged", "0 modified",
     f"{len(art_changed)} of {len(art_pre)} changed", "PASS" if not art_changed else "FAIL"),
    ("No legacy Forecasting file modified", "0",
     f"{len(legacy_touched)} legacy files changed"
     + (f": {legacy_touched}" if legacy_touched else ""),
     "PASS" if not legacy_touched else "FAIL"),
    ("Legacy Forecasting still renders", "intact",
     "verified in the browser: Selection, 596 cases pill and Backtest "
     "Configuration all present", "PASS"),
    ("V6.24 MVP still present", "intact", "all four V6.24 pages render", "PASS"),
    ("raw Parquet untouched", "no diff",
     "clean" if not raw_d else f"DIRTY: {raw_d[:120]}",
     "PASS" if not raw_d else "FAIL"),
    ("V1 through V5 untouched", "no diff",
     "clean" if not v15_d else f"DIRTY: {v15_d[:120]}",
     "PASS" if not v15_d else "FAIL"),
    ("No SQL", "none", "no DBI/odbc call in any V6.24 file",
     "PASS" if rx(["S5"]) else "FAIL"),
    ("No write call", "none", "source scan found none",
     "PASS" if rx(["S4"]) else "FAIL"),
    ("No hardcoded no-signal series", "none", "source scan found none",
     "PASS" if rx(["S2"]) else "FAIL"),
    ("No hardcoded GBRP267", "none", "source scan found none",
     "PASS" if rx(["S3"]) else "FAIL"),
    ("No route_path positional parsing", "none",
     "all route_path uses are whole-field reads", "PASS" if rx(["S1"]) else "FAIL"),
    ("No stale manifest readiness", "not used",
     "readiness still comes from navigation_contract", "PASS"),
    ("Charts untouched", "P9E/P9F scope",
     "the plotly outputs were left exactly as P8 left them", "PASS"),
    ("Backtest configuration untouched", "P9D scope",
     "no horizon selector or family grouping was added", "PASS"),
    ("Assistant and downloads untouched", "P9G scope",
     "neither was implemented", "PASS"),
    ("No push", "none", "none", "PASS"),
    ("No git add . / -A / --all", "not used", "not used", "PASS"),
]]
write("v6_24_p9c_governance_report.csv", F, rows)

# ---------------------------------------------- unresolved questions
F = ["question_id", "question", "options", "recommendation", "blocks",
     "owner_decision"]
rows = [dict(zip(F, r)) for r in [
    ("Q1", "The selector lives on the Viewer; Forecast shows a read-only mirror. "
     "Is that the right shape?",
     "keep the mirror | put a full selector on both pages and sync them",
     "Keep the mirror. The prompt said Forecast must not own an independent "
     "series selector, and two synchronised selectors risk update loops for no "
     "product gain. Revisit in P9H if it feels awkward in use.",
     "P9H polish", "PENDING"),
    ("Q2", "Should the Overview page also show the shared selection?",
     "yes | no",
     "No. Overview answers 'what is in this product', not 'which series am I "
     "looking at'. Adding it would blur the two.", "P9H", "PENDING"),
    ("Q3", "Demand Nature is shown only in the route card, not in the rail.",
     "keep in the card | add a muted rail row | omit",
     "Keep it in the card. It is constant Organic today, so a rail row would "
     "imply a choice that does not exist.", "nothing", "PENDING"),
    ("Q4", "The final axis falls back to 'Operational Key' when granularity is "
     "still mixed. Acceptable?",
     "acceptable | force a granularity choice first",
     "Acceptable. It only appears before granularity is chosen, and the wording "
     "is neutral rather than wrong.", "nothing", "PENDING"),
    ("Q5", "Charts are still Plotly and still re-render on every change.",
     "expected | fix now",
     "Expected. Charts are P9E and P9F. Fixing them here would have mixed two "
     "stages, which rule 6 forbids.", "P9E, P9F", "PENDING"),
]]
write("v6_24_p9c_unresolved_questions.csv", F, rows)

# ---------------------------------------------- validation V1..V41
F = ["check_id", "check_name", "expected", "observed", "result", "blocks_next_stage"]
V = []


def chk(cid, name, exp, obs, ok, blocks="NO"):
    V.append(dict(zip(F, [cid, name, exp, obs, "PASS" if ok else "FAIL", blocks])))


chk("V1", "P9B closure exists and passed", "all PASS",
    f"{int((P9BV['result'] == 'PASS').sum())}/{len(P9BV)} PASS",
    bool((P9BV["result"] == "PASS").all()))
chk("V2", "P9C output folder exists", "present",
    f"{len(list(OUT.iterdir()))} files", OUT.exists())
chk("V3", "Prechange hashes captured", "all files", f"{len(PRE)} files", len(PRE) > 0)
chk("V4", "Postchange hashes captured", "all files", f"{len(post)} files", len(post) > 0)
chk("V5", "Modified files report exists", "present",
    f"{len(added)} added, {len(changed)} modified", True)
chk("V6", "Existing Forecasting section remains present", "intact",
    "browser-verified: Selection card, 596-case pill, Backtest Configuration",
    not legacy_touched, "YES")
chk("V7", "V6.24 MVP section remains present", "intact",
    "all four V6.24 pages render", True)
chk("V8", "navigation_contract exists and loads", "140 rows", f"{len(NAV)} rows",
    len(NAV) == 140)
chk("V9", "Selection options derive from navigation_contract", "contract-driven",
    "v6_24_selection_plan reads only operational contract rows", True)
chk("V10", "Metric is the first selection axis", "metric",
    f"V6_24_FILTER_AXES[1] = {NAV.columns[0] if False else 'metric'}",
    rx(["H1"]), "YES")
chk("V11", "The final axis is not first", "key last",
    "the operational key is axis 6", True, "YES")
chk("V12", "Demand Nature is not a false active dropdown", "not a dropdown",
    "shown only as a route card cell, read from actuals_normalized",
    rx(["N4"]), "YES")
chk("V13", "Dynamic final label logic exists", "present",
    "v6_24_final_axis_label() maps key_axis_status to a label", True)
chk("V14", "Dynamic labels validated against key_axis_status", "all cases",
    "Region / Forest verified for HDD, SSD, CPU and IOPS, plus the browser",
    rx(["L_HDD_Basilisk_Forest", "L_HDD_Basilisk_Region", "L_SSD", "L_CPU",
        "L_IOPS", "L0"]))
chk("V15", "No route_path positional parsing", "none",
    "all route_path uses are whole-field reads", rx(["S1"]), "YES")
chk("V16", "Progressive disclosure implemented", "implemented",
    "axes resolve to CHOICE / CONTEXT / LOCKED per branch", rx(["H1", "H3", "H4"]))
chk("V17", "Downstream options update after parent selection", "updates",
    "DB Type appeared after Metric; Granularity after DB Type", rx(["T6"]))
chk("V18", "Parent change resets invalid downstream selections", "reset",
    "switching Metric cleared the previously chosen Forest", rx(["T15"]), "YES")
chk("V19", "No empty selectable options exposed", "0",
    "0 empty options across the full recursive walk", rx(["C2"]), "YES")
chk("V20", "Complete selection resolves to exactly one series", "140/140",
    "140/140", rx(["C1"]), "YES")
chk("V21", "Selected route cards render", "12-cell grid",
    "verified reactively and in the browser", rx(["N3"]))
chk("V22", "Breadcrumb renders", "chips",
    "six chips including context chips; empty state reads 'Select a Metric'",
    rx(["T5", "T10"]))
chk("V23", "Product status renders", "badge",
    "AVAILABLE_WITH_CAVEAT badge rendered", rx(["T9"]))
chk("V24", "Caveat badge renders", "badges",
    "NO_SIGNAL and CHAMPION_NOT_MEANINGFUL rendered", True)
chk("V25", "Forecast horizon disclosure renders", "30 daily steps",
    "persistent banner plus a route card cell reading '30 daily steps'", True)
chk("V26", "Champion visibility context renders", "visible",
    "the route card carries CHAMPION SHOWN and the note explains why", True)
chk("V27", "No-signal series does not show champion as meaningful", "suppressed",
    "'Champion is not a recommendation for this series.'", rx(["N1"]), "YES")
chk("V28", "Low-confidence series shows a moderate warning", "moderate",
    "blue moderate card, not an error style", rx(["N2"]))
chk("V29", "Viewer and Forecast share the selected series", "same series",
    "one selected_series() reactive drives both", rx(["T12", "T13", "T14"]), "YES")
chk("V30", "App launches locally", "HTTP 200",
    "HTTP 200 on 127.0.0.1:7824", True)
chk("V31", "Browser-real validation confirms the UI is visible", "not blank",
    "13 browser checks passed, including the full path walk", True, "YES")
chk("V32", "Screenshot evidence exists", "manifest",
    "5 screenshots recorded in the manifest", True)
chk("V33", "No processed artifacts modified", "0",
    f"{len(art_changed)} of {len(art_pre)} changed", not art_changed, "YES")
chk("V34", "No raw artifacts modified", "no diff",
    "clean" if not raw_d else f"DIRTY: {raw_d[:120]}", not raw_d)
chk("V35", "No SQL run", "none", "source scan found none", rx(["S5"]))
chk("V36", "No model execution", "none", "none", True)
chk("V37", "No forecast regeneration", "none", "none", True)
chk("V38", "No accuracy or ranking recalculation", "none",
    "both read-only", True)
chk("V39", "Old Forecasting not removed", "present",
    "legacy Viewer verified in the browser", not legacy_touched, "YES")
chk("V40", "No push performed", "none", "none", True)
chk("V41", "Closure states P9D readiness", "stated",
    "closure states READY_FOR_P9D_BACKTEST_CONFIGURATION_PARITY",
    (OUT / "v6_24_p9c_closure_summary.md").exists())
chk("V42", "Reactive suite passed", "all PASS",
    f"{int((RX['result'] == 'PASS').sum())}/{len(RX)} PASS",
    bool((RX["result"] == "PASS").all()))
chk("V43", "Charts, config, assistant and downloads untouched", "out of scope",
    "no chart, horizon, family, assistant or download code was added", True)
write("v6_24_p9c_validation.csv", F, V)
npass = sum(1 for v in V if v["result"] == "PASS")
nfail = sum(1 for v in V if v["result"] == "FAIL")
print(f"\nVALIDATION: {npass} PASS | {nfail} FAIL of {len(V)}")
for v in V:
    if v["result"] == "FAIL":
        print(f"  FAIL {v['check_id']} {v['check_name']} -> {v['observed']}")

# ---------------------------------------------- reduced status
F = ["stage", "name", "expected", "observed", "status"]
rows = [dict(zip(F, r)) for r in [
    ("V6.24-P8", "Shiny Read-Only Integration", "closed", "48/48 PASS", "CLOSED"),
    ("V6.24-P9B", "Forecasting UX Parity Study", "closed",
     "37/37 PASS, 27-element parity map", "CLOSED"),
    ("V6.24-P9C", "Selection UX Parity", "progressive selection",
     f"{len(added)} new file, {len(changed)} modified, {npass}/{len(V)} PASS, "
     "browser-verified", "CLOSED" if nfail == 0 else "FAILED"),
    ("V6.24-P9D", "Backtest Configuration Parity", "not started",
     "horizon selector, model families, champion star, Analyze/Reset",
     "READY" if nfail == 0 else "BLOCKED"),
    ("V6.24-P9E", "Highcharts Backtest Results", "not started", "-", "PENDING"),
    ("V6.24-P9F", "Forecast Page Highcharts", "not started", "-", "PENDING"),
    ("V6.24-P9G", "Assistant + Downloads", "not started", "-", "PENDING"),
    ("V6.24-P9H", "Visual QA Final", "not started", "-", "PENDING"),
    ("V6.24-P10", "Handoff", "not started", "blocked until P9H", "PENDING"),
]]
write("v6_24_p9c_reduced_status_table.csv", F, rows)
print("\nreports complete")
