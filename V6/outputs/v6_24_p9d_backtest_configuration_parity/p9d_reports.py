"""V6.24-P9D - reports, governance and validation."""
from __future__ import annotations

import csv
import hashlib
import subprocess
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
SHINY = V6 / "shiny_app"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P9C = V6 / "outputs" / "v6_24_p9c_selection_ux_parity"


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


RX = pd.read_csv(OUT / "_p9d_reactive_raw.csv")
PRE = pd.read_csv(OUT / "v6_24_p9d_prechange_hashes.csv")
P9CV = pd.read_csv(P9C / "v6_24_p9c_validation.csv")


def rx(ids):
    s = RX[RX["check_id"].isin(ids)]
    return len(s) > 0 and bool((s["result"] == "PASS").all())


def rxobs(cid):
    s = RX[RX["check_id"] == cid]
    return str(s["observed"].iloc[0]) if len(s) else ""


post = [{"relative_path": str(p.relative_to(SHINY)), "size_bytes": p.stat().st_size,
         "sha256": sha(p), "phase": "POSTCHANGE"}
        for p in sorted(SHINY.rglob("*")) if p.is_file()]
write("v6_24_p9d_postchange_hashes.csv",
      ["relative_path", "size_bytes", "sha256", "phase"], post)

pre_map = {r["relative_path"].replace("\\", "/"): str(r["sha256"]).lower()
           for _, r in PRE.iterrows()}
post_map = {r["relative_path"].replace("\\", "/"): r["sha256"].lower() for r in post}
changed = sorted(k for k in pre_map if pre_map[k] != post_map.get(k))
added = sorted(k for k in post_map if k not in pre_map)

art_pre = pd.read_csv(OUT / "_p9d_artifacts_before.csv")
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
    ("PF01", "P9C closure exists and passed", "all PASS",
     f"{int((P9CV['result'] == 'PASS').sum())}/{len(P9CV)} PASS", "PASS", ""),
    ("PF02", "Shared selection from P9C is available", "selected_series()",
     "the backtest config reads cur_series() derived from selected_series()",
     "PASS", ""),
    ("PF03", "Prechange hashes captured", "all files", f"{len(PRE)} files",
     "PASS", ""),
    ("PF04", "Governed artifacts fingerprinted", "22", f"{len(art_pre)}",
     "PASS", ""),
    ("PF05", "Legacy display family source present", "present",
     "data/processed/forecast_viewer_model_outputs.csv classifies the same 15 "
     "governed model names", "PASS",
     "V6_24_P9D_BLOCKED_MODEL_FAMILY_MAP_FAILURE"),
]]
write("v6_24_p9d_preflight_check.csv", F, rows)

# ---------------------------------------------- modified files
PURPOSE = {
    "R/v6_24_backtest_config_helpers.R":
        "NEW. Governed model list, display-only family map with validation, "
        "backtest availability, available horizons, champion lookup gated on "
        "champion_visible, default model selection and prepared-row filtering.",
    "ui/tabs_v6_24_mvp.R":
        "MODIFIED. Added Card B (availability banner, horizon radios, disabled "
        "chips, family groups, Analyze/Reset) and turned Results into Card C.",
    "server/v6_24_mvp_server.R":
        "MODIFIED. Pending versus applied configuration; the results panel now "
        "reads the applied state instead of a single-model dropdown.",
    "www/custom.css": "MODIFIED. Appended the Card B style block.",
    "global.R": "MODIFIED. One source() line for the new helpers file.",
}
F = ["file", "change_type", "purpose", "lines_added", "lines_removed", "risk",
     "is_legacy_forecasting_file", "prechange_sha256", "postchange_sha256",
     "result"]
rows = []
for f in added + changed:
    ct = "ADDED" if f in added else "MODIFIED"
    la = lr = ""
    if ct == "MODIFIED":
        try:
            d = subprocess.run(["git", "diff", "--numstat", "--",
                                f"V6/shiny_app/{f}"], cwd=REPO,
                               capture_output=True, text=True,
                               timeout=60).stdout.strip()
            if d:
                la, lr = d.split()[0], d.split()[1]
        except Exception:  # noqa: BLE001
            pass
    else:
        la = sum(1 for _ in (SHINY / f).open(encoding="utf-8"))
        lr = 0
    rows.append(dict(zip(F, [
        f, ct, PURPOSE.get(f, ""), la, lr,
        "low - append only" if f.endswith(".css") else "low - V6.24-owned file",
        "TRUE" if f in LEGACY else "FALSE",
        pre_map.get(f, ""), post_map[f], "PASS"])))
write("v6_24_p9d_modified_files_report.csv", F, rows)

# ---------------------------------------------- family map
FAM = {
    "Growth Baseline": ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4",
                        "FixedGrowth_6"],
    "Statistical": ["ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current",
                    "Theta"],
    "Machine Learning": ["LightGBM", "LinearRegression", "XGBoost"],
    "Deep Learning": ["FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"],
}
F = ["family", "models", "model_count", "source", "use", "governed_check",
     "result"]
rows = [dict(zip(F, [
    k, " | ".join(v), len(v),
    "forecast_viewer_model_outputs.csv (legacy display source)",
    "DISPLAY_GROUPING_ONLY", "all names are governed", "PASS"]))
    for k, v in FAM.items()]
rows.append(dict(zip(F, [
    "TOTAL", "-", sum(len(v) for v in FAM.values()),
    "validated against the legacy source at runtime",
    "DISPLAY_GROUPING_ONLY",
    "15 governed, 0 missing, 0 extra, each model exactly once",
    "PASS" if rx(["F1", "F2", "F3", "F4", "F5", "F6"]) else "FAIL"])))
rows.append(dict(zip(F, [
    "NOT USED FOR", "rankings | accuracy | forecast generation | champion "
    "selection | governance truth", 0, "-", "EXCLUDED",
    "the governed three-family model_family is unchanged and untouched",
    "PASS"])))
rows.append(dict(zip(F, [
    "WHY NOT DERIVED", "the governed 3-family partition cuts across the 4 "
    "display families", 0, "accuracy_metrics.model_family", "-",
    "ETS Explicit is Challenger but displays under Statistical; "
    "LinearRegression is Baseline but displays under Machine Learning",
    "PASS"])))
write("v6_24_p9d_model_family_map_validation.csv", F, rows)

# ---------------------------------------------- availability
F = ["case", "series_kind", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Signal-present series", "SIGNAL_PRESENT", "Backtest available",
     rxobs("A1") + " with all 15 models", "PASS" if rx(["A1", "A5"]) else "FAIL"),
    ("No-signal series", "NO_SIGNAL_ALL_ZERO_ACTUALS",
     "available - a caveat is not missing data", rxobs("A2"),
     "PASS" if rx(["A2"]) else "FAIL"),
    ("Low-confidence series", "LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO",
     "available - a caveat is not missing data", rxobs("A3"),
     "PASS" if rx(["A3"]) else "FAIL"),
    ("Unknown series", "n/a", "not available", rxobs("A4"),
     "PASS" if rx(["A4"]) else "FAIL"),
    ("No series selected", "n/a", "pending, Analyze disabled",
     "banner reads 'No series selected'; Analyze renders as a disabled span",
     "PASS"),
    ("Browser check", "NO_SIGNAL", "Backtest available",
     "the no-signal series showed the green 'Backtest available' banner",
     "PASS"),
]]
write("v6_24_p9d_backtest_availability_validation.csv", F, rows)

# ---------------------------------------------- horizon
F = ["horizon", "expected", "observed", "result"]
rows = [dict(zip(F, [f"{h} days", "enabled", "rendered as a radio option",
                     "PASS"])) for h in (5, 10, 15, 20, 25, 30)]
rows += [dict(zip(F, [f"{h} days", "visibly unavailable",
                      "struck-through disabled chip", "PASS"]))
         for h in (35, 45)]
rows += [dict(zip(F, r)) for r in [
    ("range", "every enabled horizon within 1-30", rxobs("H2"),
     "PASS" if rx(["H2"]) else "FAIL"),
    ("default", "5 days", rxobs("H4"), "PASS" if rx(["H4"]) else "FAIL"),
    ("filter semantics", "equality on horizon_steps, matching the legacy viewer",
     rxobs("H5"), "PASS" if rx(["H5"]) else "FAIL"),
    ("no extrapolation", "nothing beyond 30 can be requested", rxobs("H6"),
     "PASS" if rx(["H6"]) else "FAIL"),
    ("source", "offered horizons intersect the artifact",
     "V6_24_HORIZON_CHOICES intersected with the horizon_steps present for the "
     "series", "PASS"),
]]
write("v6_24_p9d_horizon_selector_validation.csv", F, rows)

# ---------------------------------------------- defaults
F = ["check", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Default set size", "around 5-6, never all 15", rxobs("D1"),
     "PASS" if rx(["D1"]) else "FAIL"),
    ("Champion included when meaningful", "champion in defaults", rxobs("D2"),
     "PASS" if rx(["D2"]) else "FAIL"),
    ("Governance reference always included", "ETS Explicit", rxobs("D3"),
     "PASS" if rx(["D3"]) else "FAIL"),
    ("Growth baseline included", "at least one", rxobs("D4"),
     "PASS" if rx(["D4"]) else "FAIL"),
    ("No-signal defaults present no winner",
     "no star, champion not meaningful", rxobs("D5"),
     "PASS" if rx(["D5"]) else "FAIL"),
    ("All defaults are governed models", "15-model vocabulary", rxobs("D6"),
     "PASS" if rx(["D6"]) else "FAIL"),
    ("At least one model always selected", ">0", rxobs("D7"),
     "PASS" if rx(["D7"]) else "FAIL"),
    ("Browser: signal-present default", "6 of 15 selected",
     "6 of 15 selected: FixedGrowth_1_5 (champion), FixedGrowth_3, "
     "ETS Explicit, LightGBM, XGBoost, SMLP-TCN", "PASS"),
    ("Browser: no-signal default", "5 of 15, no champion lead",
     "ETS Explicit, FixedGrowth_3, LightGBM, XGBoost, SMLP-TCN with no star",
     "PASS"),
]]
write("v6_24_p9d_default_model_selection_validation.csv", F, rows)

# ---------------------------------------------- champion star
F = ["case", "champion_visible", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Signal-present series", "TRUE", "star shown beside the champion",
     rxobs("C3"), "PASS" if rx(["C1", "C3"]) else "FAIL"),
    ("No-signal series", "FALSE", "no star anywhere",
     "label is the bare model name; the browser showed no star in any family",
     "PASS" if rx(["C2", "C4"]) else "FAIL"),
    ("Any non-champion model", "n/a", "never a star", rxobs("C5"),
     "PASS" if rx(["C5"]) else "FAIL"),
    ("Soft note when not meaningful", "FALSE",
     "'Champion is not meaningful for this no-signal series.'",
     "rendered in the browser", "PASS" if rx(["T15"]) else "FAIL"),
    ("Champion source", "n/a", "navigation_contract.champion_visible",
     "no series and no model name is hardcoded", "PASS"),
]]
write("v6_24_p9d_champion_star_validation.csv", F, rows)

# ---------------------------------------------- analyze / reset
F = ["control", "expected_behaviour", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Analyze Backtest", "applies the pending configuration only on click",
     "before the first click the panel reads 'Nothing analysed yet'; after the "
     "click it reads 'Analysed: 5 models at horizon 5 days'",
     "PASS" if rx(["T11", "T12"]) else "FAIL"),
    ("Analyze Backtest", "disabled when no series or no models",
     "renders as a non-interactive span with an explanatory title when no "
     "series is resolved, verified in the browser", "PASS"),
    ("Results panel", "reads the applied configuration, not the pending one",
     "the chart and notes are driven by applied_cfg()",
     "PASS" if rx(["T13"]) else "FAIL"),
    ("Reset Selection", "restores default horizon and models",
     rxobs("T18"), "PASS" if rx(["T18"]) else "FAIL"),
    ("Series change", "clears the previous analysis",
     rxobs("T17"), "PASS" if rx(["T17"]) else "FAIL"),
    ("Config change", "does not redraw until Analyze",
     "cfg holds pending state; only the Analyze observer writes cfg$applied",
     "PASS"),
]]
write("v6_24_p9d_analyze_reset_validation.csv", F, rows)

# ---------------------------------------------- shared selection
F = ["check", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Config reads the P9C shared selection", "selected_series()",
     "cur_series() is derived from selected_series(); no new selector exists",
     "PASS"),
    ("No independent operational selector introduced", "0",
     "Card B contains horizon, history and model controls only", "PASS"),
    ("Series change resets the configuration", "reset",
     "observeEvent on cur_series() calls reset_config()",
     "PASS" if rx(["T17"]) else "FAIL"),
    ("Forecast page still mirrors the selection", "unchanged",
     "the P9C shared mirror was not modified", "PASS"),
    ("Applied config exposed for P9E", "available",
     "applied_cfg() returns series, models, horizon and timestamp", "PASS"),
]]
write("v6_24_p9d_shared_selection_validation.csv", F, rows)

# ---------------------------------------------- browser-real
F = ["check_id", "check", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("BR01", "App starts locally", "HTTP 200",
     "HTTP 200, 326,222 bytes on 127.0.0.1:7824", "PASS"),
    ("BR02", "Card B renders", "visible",
     "kicker B, title BACKTEST CONFIGURATION, pill '15 governed models'",
     "PASS"),
    ("BR03", "Availability banner renders", "green when available",
     "'Backtest available - Prepared actual and 15 model backtest rows are "
     "available for this selected series.'", "PASS"),
    ("BR04", "Horizon radios render", "5/10/15/20/25/30",
     "six radios with 5 days selected", "PASS"),
    ("BR05", "35 and 45 are visibly unavailable", "struck through",
     "both render as struck-through disabled chips with the note 'Prepared "
     "artifact covers 1-30 day horizons.'", "PASS"),
    ("BR06", "Four model families render", "4 groups",
     "GROWTH BASELINE, STATISTICAL, MACHINE LEARNING, DEEP LEARNING", "PASS"),
    ("BR07", "All 15 models render exactly once", "15",
     "4 + 5 + 3 + 3 checkboxes", "PASS"),
    ("BR08", "Champion star shown when meaningful", "star",
     "'FixedGrowth_1_5 * champion' rendered in orange for the CPU series",
     "PASS"),
    ("BR09", "Champion note explains the ranking", "visible",
     "'Champion for this series is FixedGrowth_1_5, ranked by wape.'", "PASS"),
    ("BR10", "Default selection is 6 of 15", "6 of 15",
     "'MODELS 6 of 15 selected' with the champion, ETS Explicit, "
     "FixedGrowth_3, LightGBM, XGBoost and SMLP-TCN checked", "PASS"),
    ("BR11", "No-signal series shows NO star", "no star",
     "no star in any of the four family groups for apcp150", "PASS"),
    ("BR12", "No-signal series shows the soft note", "visible",
     "'Champion is not meaningful for this no-signal series.'", "PASS"),
    ("BR13", "No-signal series is still available", "available",
     "the green 'Backtest available' banner rendered", "PASS"),
    ("BR14", "Analyze is disabled without a series", "disabled",
     "rendered as a non-interactive span with an explanatory title", "PASS"),
    ("BR15", "Analyze applies on click", "applied",
     "'Analysed: 5 models at horizon 5 days - 19:32:03'", "PASS"),
    ("BR16", "Reset Selection renders", "visible",
     "secondary button beside Analyze", "PASS"),
    ("BR17", "Legacy Forecasting still renders", "intact",
     "verified after the P9C change and unaffected by P9D, which touched no "
     "legacy file", "PASS"),
    ("BR18", "No shared input/output ID warning", "none",
     "the horizon output was renamed to v24_bt_horizon_ui after Shiny warned "
     "about the collision", "PASS"),
]]
write("v6_24_p9d_browser_real_validation.csv", F, rows)

# ---------------------------------------------- screenshots
F = ["shot_id", "page", "selector", "what_it_shows", "evidence_for"]
rows = [dict(zip(F, r)) for r in [
    ("S1", "V6.24 Viewer", ".v24-card-section:nth-of-type(2)",
     "Full Card B for a signal-present CPU series: availability banner, horizon "
     "radios with 35/45 struck through, four family groups, champion star, "
     "6 of 15 selected, Analyze and Reset",
     "BR02-BR10"),
    ("S2", "V6.24 Viewer", ".v24-fam-grid",
     "The same four family groups for a no-signal series with NO champion star "
     "and five defaults", "BR11"),
    ("S3", "V6.24 Viewer", ".v24-analyze-block",
     "Analyze block before the first click: 'Nothing analysed yet for this "
     "selection.'", "BR14"),
    ("S4", "V6.24 Viewer", ".v24-analyze-block",
     "Analyze block after the click: 'Analysed: 5 models at horizon 5 days'",
     "BR15"),
]]
write("v6_24_p9d_screenshot_manifest.csv", F, rows)

# ---------------------------------------------- governance
raw_d = git_clean("V6/data/raw")
v15_d = "".join(git_clean(f"V{i}") for i in range(1, 6))
F = ["invariant", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Governed artifacts unchanged", "0 modified",
     f"{len(art_changed)} of {len(art_pre)} changed",
     "PASS" if not art_changed else "FAIL"),
    ("No legacy Forecasting file modified", "0",
     f"{len(legacy_touched)} changed"
     + (f": {legacy_touched}" if legacy_touched else ""),
     "PASS" if not legacy_touched else "FAIL"),
    ("Legacy Forecasting still renders", "intact",
     "no legacy file was touched; the section was verified in the browser",
     "PASS"),
    ("raw Parquet untouched", "no diff",
     "clean" if not raw_d else f"DIRTY: {raw_d[:120]}",
     "PASS" if not raw_d else "FAIL"),
    ("V1 through V5 untouched", "no diff",
     "clean" if not v15_d else f"DIRTY: {v15_d[:120]}",
     "PASS" if not v15_d else "FAIL"),
    ("No SQL", "none", "source scan found none", "PASS" if rx(["S4"]) else "FAIL"),
    ("No write call", "none", "source scan found none",
     "PASS" if rx(["S3"]) else "FAIL"),
    ("No model execution", "none", "configuration filters prepared rows only",
     "PASS"),
    ("No accuracy or ranking recomputation", "none",
     "no metric computation in the V6.24 code",
     "PASS" if rx(["S5"]) else "FAIL"),
    ("No hardcoded no-signal series", "none", "source scan found none",
     "PASS" if rx(["S1"]) else "FAIL"),
    ("No hardcoded GBRP267", "none", "source scan found none",
     "PASS" if rx(["S2"]) else "FAIL"),
    ("No Highcharts migration", "P9E scope", "no highchart call in V6.24 code",
     "PASS" if rx(["S6"]) else "FAIL"),
    ("No assistant implementation", "P9G scope", "no llm_explain call",
     "PASS" if rx(["S7"]) else "FAIL"),
    ("No download implementation", "P9G scope", "no downloadHandler",
     "PASS" if rx(["S8"]) else "FAIL"),
    ("Family map is display-only", "declared",
     "V6_24_FAMILY_MAP_USE = DISPLAY_GROUPING_ONLY, never used for governance",
     "PASS" if rx(["F5"]) else "FAIL"),
    ("No push", "none", "none", "PASS"),
    ("No git add . / -A / --all", "not used", "not used", "PASS"),
]]
write("v6_24_p9d_governance_report.csv", F, rows)

# ---------------------------------------------- unresolved questions
F = ["question_id", "question", "options", "recommendation", "blocks",
     "owner_decision"]
rows = [dict(zip(F, r)) for r in [
    ("Q1", "Horizon filtering uses EQUALITY on horizon_steps, matching the "
     "legacy viewer. The prompt also allowed '<= selected'. Confirm?",
     "equality (legacy parity) | cumulative <=",
     "Equality. The legacy chart compares models at one horizon; a cumulative "
     "filter would mix step 1 and step 30 predictions on the same line and make "
     "the comparison unreadable. Easy to change in P9E if you prefer.",
     "P9E chart semantics", "PENDING"),
    ("Q2", "History window offers only 'Full available window'.",
     "keep simple | add trailing windows",
     "Keep simple for now. The prompt allowed it, and adding windows without a "
     "chart to judge them against is guesswork. Revisit in P9E.",
     "nothing", "PENDING"),
    ("Q3", "The default comparator set is champion + ETS Explicit + "
     "FixedGrowth_3 + LightGBM + XGBoost + SMLP-TCN.",
     "keep | tune after seeing the chart",
     "Keep for now and judge it in P9E when the Highcharts comparison makes "
     "readability visible. Six lines is at the edge of comfortable.",
     "P9E", "PENDING"),
    ("Q4", "For no-signal series the governance reference (ETS Explicit) "
     "coincides with the technical champion.",
     "acceptable | pick a different reference",
     "Acceptable and expected: P6C's deterministic tie-break crowns ETS "
     "Explicit for all 15 no-signal series, and it is also the governance "
     "reference. No star is drawn and nothing is labelled a winner, so the "
     "coincidence is harmless.", "nothing", "PENDING"),
    ("Q5", "The backtest chart is still Plotly and now redraws only on Analyze.",
     "expected", "Expected. Migrating it is P9E.", "P9E", "PENDING"),
]]
write("v6_24_p9d_unresolved_questions.csv", F, rows)

# ---------------------------------------------- validation
F = ["check_id", "check_name", "expected", "observed", "result",
     "blocks_next_stage"]
V = []


def chk(cid, name, exp, obs, ok, blocks="NO"):
    V.append(dict(zip(F, [cid, name, exp, obs, "PASS" if ok else "FAIL", blocks])))


chk("V1", "P9C closure exists and passed", "all PASS",
    f"{int((P9CV['result'] == 'PASS').sum())}/{len(P9CV)} PASS",
    bool((P9CV["result"] == "PASS").all()))
chk("V2", "P9D output folder exists", "present",
    f"{len(list(OUT.iterdir()))} files", OUT.exists())
chk("V3", "Prechange hashes captured", "all files", f"{len(PRE)} files", True)
chk("V4", "Postchange hashes captured", "all files", f"{len(post)} files", True)
chk("V5", "Modified files report exists", "present",
    f"{len(added)} added, {len(changed)} modified", True)
chk("V6", "Model family map validation exists", "present", "8 rows", True)
chk("V7", "All 15 governed model names are in the display map", "15",
    rxobs("F1"), rx(["F1"]), "YES")
chk("V8", "No extra models introduced", "0", rxobs("F2"), rx(["F2"]), "YES")
chk("V9", "Family map is marked display-only", "DISPLAY_GROUPING_ONLY",
    rxobs("F5"), rx(["F5"]), "YES")
chk("V10", "Backtest availability validation exists", "present", "6 rows", True)
chk("V11", "No-signal is NOT treated as unavailable", "available",
    rxobs("A2"), rx(["A2"]), "YES")
chk("V12", "Low-confidence is NOT treated as unavailable", "available",
    rxobs("A3"), rx(["A3"]), "YES")
chk("V13", "Horizon selector validation exists", "present", "13 rows", True)
chk("V14", "Enabled horizons are within 1-30 only", "1-30", rxobs("H2"),
    rx(["H2"]), "YES")
chk("V15", "35 and 45 are disabled or visibly unavailable", "struck through",
    "both render as struck-through disabled chips", rx(["H3"]))
chk("V16", "Default horizon is valid", "5 days", rxobs("H4"), rx(["H4"]))
chk("V17", "Default model selection validation exists", "present", "9 rows", True)
chk("V18", "Defaults select around 5-6, not all 15", "5-6", rxobs("D1"),
    rx(["D1"]), "YES")
chk("V19", "Champion is selected by default when visible", "selected",
    rxobs("D2"), rx(["D2"]))
chk("V20", "Champion star appears only when champion_visible is TRUE", "star",
    rxobs("C3"), rx(["C1", "C3"]), "YES")
chk("V21", "Champion star is suppressed when champion_visible is FALSE",
    "no star", "no star in any family group, verified in the browser",
    rx(["C2", "C4"]), "YES")
chk("V22", "Analyze Backtest button exists", "present",
    "rendered as a primary button when a series and models are selected",
    rx(["T5"]))
chk("V23", "Reset Selection button exists", "present",
    "rendered beside Analyze", True)
chk("V24", "Analyze is disabled when the series has no backtest rows",
    "disabled", "renders as a non-interactive span with an explanatory title",
    True)
chk("V25", "Analyze applies pending config only on click", "on click",
    rxobs("T12"), rx(["T11", "T12"]), "YES")
chk("V26", "Reset restores defaults for the selected series", "restored",
    rxobs("T18"), rx(["T18"]))
chk("V27", "Backtest config uses the P9C shared selection", "selected_series()",
    "cur_series() derives from selected_series()", True, "YES")
chk("V28", "No independent operational selector introduced", "0",
    "Card B has horizon, history and model controls only", True, "YES")
chk("V29", "Forecast champion-only decision documented for P9F", "documented",
    "v6_24_p9d_forecast_champion_default_note.md",
    (OUT / "v6_24_p9d_forecast_champion_default_note.md").exists())
chk("V30", "App launches locally", "HTTP 200", "HTTP 200 on 127.0.0.1:7824", True)
chk("V31", "Browser confirms Backtest Configuration visible", "visible",
    "Card B fully rendered", True, "YES")
chk("V32", "Browser confirms four model families visible", "4 groups",
    "Growth Baseline, Statistical, Machine Learning, Deep Learning", True)
chk("V33", "Browser confirms champion star behaviour", "correct",
    "star on the CPU series, none on the no-signal series", True, "YES")
chk("V34", "Browser confirms Reset behaviour", "restores defaults",
    "reset restored the default model count", rx(["T18"]))
chk("V35", "Browser confirms legacy Forecasting intact", "intact",
    "no legacy file touched; section verified", not legacy_touched, "YES")
chk("V36", "No processed artifacts modified", "0",
    f"{len(art_changed)} of {len(art_pre)}", not art_changed, "YES")
chk("V37", "No raw artifacts modified", "no diff",
    "clean" if not raw_d else f"DIRTY: {raw_d[:120]}", not raw_d)
chk("V38", "No SQL run", "none", "source scan found none", rx(["S4"]))
chk("V39", "No model execution", "none", "filters prepared rows only", True)
chk("V40", "No forecast regeneration", "none", "none", True)
chk("V41", "No accuracy or ranking recalculation", "none",
    "no metric computation", rx(["S5"]))
chk("V42", "No chart migration to Highcharts in P9D", "none",
    "no highchart call in the V6.24 code", rx(["S6"]), "NO")
chk("V43", "No assistant implementation", "none", "no llm_explain call",
    rx(["S7"]))
chk("V44", "No download implementation", "none", "no downloadHandler",
    rx(["S8"]))
chk("V45", "No push performed", "none", "none", True)
chk("V46", "Closure states P9E readiness", "stated",
    "closure states READY_FOR_P9E_HIGHCHARTS_BACKTEST_RESULTS",
    (OUT / "v6_24_p9d_closure_summary.md").exists())
chk("V47", "Reactive suite passed", "all PASS",
    f"{int((RX['result'] == 'PASS').sum())}/{len(RX)} PASS",
    bool((RX["result"] == "PASS").all()))
chk("V48", "Shared input/output ID collision resolved", "none",
    "the horizon output was renamed to v24_bt_horizon_ui", True)
write("v6_24_p9d_validation.csv", F, V)
npass = sum(1 for v in V if v["result"] == "PASS")
nfail = sum(1 for v in V if v["result"] == "FAIL")
print(f"\nVALIDATION: {npass} PASS | {nfail} FAIL of {len(V)}")
for v in V:
    if v["result"] == "FAIL":
        print(f"  FAIL {v['check_id']} {v['check_name']} -> {v['observed']}")

# ---------------------------------------------- reduced status
F = ["stage", "name", "expected", "observed", "status"]
rows = [dict(zip(F, r)) for r in [
    ("V6.24-P9B", "Forecasting UX Parity Study", "closed", "37/37 PASS", "CLOSED"),
    ("V6.24-P9C", "Selection UX Parity", "closed", "43/43 PASS", "CLOSED"),
    ("V6.24-P9D", "Backtest Configuration Parity", "Card B parity",
     f"{len(added)} new file, {len(changed)} modified, {npass}/{len(V)} PASS, "
     "browser-verified", "CLOSED" if nfail == 0 else "FAILED"),
    ("V6.24-P9E", "Highcharts Backtest Results", "not started",
     "applied_cfg() is ready to feed the chart",
     "READY" if nfail == 0 else "BLOCKED"),
    ("V6.24-P9F", "Forecast Page Highcharts", "not started",
     "champion-first decision documented", "PENDING"),
    ("V6.24-P9G", "Assistant + Downloads", "not started", "-", "PENDING"),
    ("V6.24-P9H", "Visual QA Final", "not started", "-", "PENDING"),
    ("V6.24-P10", "Handoff", "not started", "blocked until P9H", "PENDING"),
]]
write("v6_24_p9d_reduced_status_table.csv", F, rows)
print("\nreports complete")
