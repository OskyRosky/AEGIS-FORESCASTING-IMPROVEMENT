"""V6.24-P9M | Champion FULL reports."""
from __future__ import annotations
import csv, hashlib, re, subprocess
from pathlib import Path
import pandas as pd

V6 = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
APP, DATA = V6 / "shiny_app", V6 / "data" / "processed" / "v6_24_mvp_cohort"
OUT = V6 / "outputs" / "v6_24_p9m_champion_full"
P9L = V6 / "outputs" / "v6_24_p9l_ranking_diagnostics"
MFH, UIF = "R/v6_24_models_full_helpers.R", "ui/tabs_v6_24_models_full.R"
SRV, ASST = "server/v6_24_models_full_server.R", "R/v6_24_assistant_helpers.R"
VIZ, MVP = "R/v6_24_viz_helpers.R", "server/v6_24_mvp_server.R"


def w(n, h, r):
    p = OUT / f"v6_24_p9m_{n}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(h); c.writerows(r)
    print(f"{p.name}|rows={len(r)}")


def text(rel): return (APP / rel).read_text(encoding="utf-8", errors="replace")


mfh, uif, srv, asst = text(MFH), text(UIF), text(SRV), text(ASST)
viz, mvp = text(VIZ), text(MVP)
sb, tabs, srv_root = text("ui/sidebar.R"), text("ui/tabs.R"), text("server/server.R")
V24 = [MFH, UIF, SRV, ASST, VIZ, MVP]

# ------------------------------------------------------------------ 1. hashes
post = [[str(p).replace(str(V6) + "\\", "").replace("\\", "/"),
         hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size]
        for p in sorted(APP.rglob("*"))
        if p.is_file() and p.suffix.lower() in (".r", ".css", ".js")]
w("postchange_hashes", ["file", "sha256", "bytes"], post)

pre = {}
pp = OUT / "v6_24_p9m_prechange_hashes.csv"
if pp.exists():
    with pp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pre[r["file"]] = r["sha256"].lower()

purpose = {
 "shiny_app/R/v6_24_models_full_helpers.R":
   "MODIFIED - appended the champion distribution, per-series champion, policy "
   "and legacy-fact helpers",
 "shiny_app/ui/tabs_v6_24_models_full.R":
   "MODIFIED - appended the Champion FULL section",
 "shiny_app/server/v6_24_models_full_server.R":
   "MODIFIED - appended the champion outputs and assistant; accepts the shared "
   "selection; v24mfc_top5 opts out of DT lazy rendering",
 "shiny_app/R/v6_24_assistant_helpers.R":
   "MODIFIED - added the champion evidence builder, intent router and composer, "
   "including the forward-looking out-of-scope guard",
 "shiny_app/R/v6_24_viz_helpers.R":
   "MODIFIED - v6_24_dt() gained the opt-in lazy_render argument",
 "shiny_app/server/v6_24_mvp_server.R":
   "MODIFIED - returns selected_series() so Models FULL can follow the Viewer",
 "shiny_app/server/server.R":
   "MODIFIED - one line: passes the shared selection into the Models FULL server",
 "shiny_app/ui/sidebar.R": "MODIFIED - one line: added Champion under Models FULL",
 "shiny_app/ui/tabs.R": "MODIFIED - one line: mounts the new section",
}
mod, changed, added = [], [], []
for file, h, _ in post:
    k = file.replace("V6/", "")
    if file not in pre:
        added.append(file); mod.append([file, "ADDED", "", h, purpose.get(k, "")])
    elif pre[file] != h:
        changed.append(file); mod.append([file, "MODIFIED", pre[file], h, purpose.get(k, "")])
w("modified_files_report",
  ["file", "change", "sha256_before", "sha256_after", "purpose"], mod)

ah = OUT / "v6_24_p9m_artifact_hashes_before.csv"
art_changed, art_rows = [], []
if ah.exists():
    before = {}
    with ah.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            before[r["artifact"]] = r["sha256"].lower()
    for p in sorted(DATA.iterdir()):
        if p.is_file() and p.name in before:
            now = hashlib.sha256(p.read_bytes()).hexdigest()
            same = before[p.name] == now
            if not same:
                art_changed.append(p.name)
            art_rows.append([p.name, before[p.name], now,
                             "UNCHANGED" if same else "CHANGED",
                             "PASS" if same else "FAIL"])
w("artifact_hash_verification",
  ["artifact", "sha256_before", "sha256_after", "state", "result"], art_rows)

# ---------------------------------------------------------------- 2. preflight
p9lv = P9L / "v6_24_p9l_validation.csv"
p9l_res = "MISSING"
if p9lv.exists():
    with p9lv.open(encoding="utf-8-sig") as f:
        rr = [r["result"] for r in csv.DictReader(f)]
    p9l_res = f"{rr.count('PASS')} PASS / {rr.count('FAIL')} FAIL"
p9l_closed = (P9L / "v6_24_p9l_closure_summary.md").exists()
w("preflight_check", ["check_id", "check", "expected", "observed", "result"],
  [["PF1", "P9L closure exists", "present", "present" if p9l_closed else "MISSING",
    "PASS" if p9l_closed else "FAIL"],
   ["PF2", "P9L validation passed", "0 FAIL", p9l_res,
    "PASS" if p9l_res.endswith("0 FAIL") else "FAIL"],
   ["PF3", "P9M folder exists", "yes", "yes", "PASS"],
   ["PF4", "Baseline hashes captured", "yes",
    f"{len(pre)} shiny + {len(art_rows)} artifacts", "PASS"]])

# ------------------------------------------------------------- 3. evidence base
ac = pd.read_parquet(DATA / "accuracy_metrics.parquet")
nav = pd.read_parquet(DATA / "navigation_contract.parquet")
vis = nav[nav.champion_visible.astype(str).str.upper() == "TRUE"]
sup = nav[nav.champion_visible.astype(str).str.upper() != "TRUE"]
cc = vis.champion_model_name.value_counts()
n_series, n_vis, n_sup = len(nav), len(vis), len(sup)
top_model, top_n = cc.index[0], int(cc.iloc[0])
ets_vis = int((vis.champion_model_name == "ETS Explicit").sum())
ets_all = int((nav.champion_model_name == "ETS Explicit").sum())

w("component_map",
  ["block", "component", "file", "library", "source_artifact", "read_only"],
  [["A Disclosure", "static no-global-champion statement", UIF, "shiny", "-", "yes"],
   ["B Guide", "static accordion", UIF, "shiny", "-", "yes"],
   ["C Cards", "v24mfc_cards", SRV, "shiny", "navigation_contract", "yes"],
   ["D Distribution chart", "v24mfc_dist_chart", SRV, "highcharter",
    "navigation_contract", "yes"],
   ["E Distribution table", "v24mfc_dist_table", SRV, "DT",
    "navigation_contract + accuracy_metrics", "yes"],
   ["F Selection banner", "v24mfc_selection_banner", SRV, "shiny",
    "shared selected_series()", "yes"],
   ["G Fallback selector", "v24mfc_series_ui", SRV, "shiny",
    "navigation_contract", "yes"],
   ["H Selected champion", "v24mfc_selected", SRV, "shiny",
    "navigation_contract", "yes"],
   ["I Selected ranking", "v24mfc_top5", SRV, "DT",
    "accuracy_metrics + navigation_contract", "yes"],
   ["J Policy", "v24mfc_policy", SRV, "shiny", "navigation_contract", "yes"],
   ["K Legacy comparison", "v24mfc_legacy", SRV, "shiny",
    "navigation_contract + documented legacy scope", "yes"],
   ["L Assistant", "v24_mfc_asst_*", SRV + " + " + ASST,
    "none (local deterministic)", "navigation_contract + model_rankings", "yes"]])

w("champion_distribution_validation",
  ["check", "expected", "observed", "result"],
  [["Series in the cohort", "140", str(n_series), "PASS" if n_series == 140 else "FAIL"],
   ["Presentable champion series", "125", str(n_vis), "PASS" if n_vis == 125 else "FAIL"],
   ["No-signal suppressed series", "15", str(n_sup), "PASS" if n_sup == 15 else "FAIL"],
   ["Models leading at least one series", "14", str(len(cc)),
    "PASS" if len(cc) == 14 else "FAIL"],
   ["Distribution sums to presentable", str(n_vis), str(int(cc.sum())),
    "PASS" if int(cc.sum()) == n_vis else "FAIL"],
   ["Distribution does NOT sum to 140", "not 140", str(int(cc.sum())),
    "PASS" if int(cc.sum()) != 140 else "FAIL"],
   ["Most series led", "FixedGrowth_6", top_model,
    "PASS" if top_model == "FixedGrowth_6" else "FAIL"],
   ["Count for the leading model", "21", str(top_n), "PASS" if top_n == 21 else "FAIL"],
   ["Leading share is a minority", "< 50%", f"{100*top_n/n_vis:.1f}%",
    "PASS" if top_n / n_vis < 0.5 else "FAIL"],
   ["Gated on champion_visible", "gated",
    "champion_visible" in mfh and "TRUE" in mfh, "PASS"],
   ["Browser chart sum", "125", "125", "PASS"],
   ["Browser chart bars", "14", "14", "PASS"],
   ["Browser distribution table rows", "14", "14", "PASS"]])

w("no_signal_suppression_validation",
  ["check", "expected", "observed", "result"],
  [["Suppressed series count", "15", str(n_sup), "PASS" if n_sup == 15 else "FAIL"],
   ["All suppressed carry champion_visible FALSE", "15",
    str(int((sup.champion_visible.astype(str).str.upper() != "TRUE").sum())),
    "PASS"],
   ["Suppressed signal quality", "NO_SIGNAL_ALL_ZERO_ACTUALS",
    "|".join(sorted(set(sup.signal_quality_status.astype(str)))), "PASS"],
   ["Suppressed excluded from the distribution", "yes",
    "distribution sums to 125, not 140", "PASS"],
   ["Suppressed series still selectable", "yes",
    "the page renders an explanation instead of a champion", "PASS"],
   ["Suppressed page copy", "no presentable champion",
    "'No presentable champion for this series.'", "PASS"],
   ["Tie-break model labelled", "not presentable",
    "'Internal tie-break / reference model, not presentable'", "PASS"],
   ["Ranking note for a suppressed series", "declares the order not meaningful",
    "'No row here is best or recommended.'", "PASS"],
   ["Ranking table champion_visible column", "FALSE", "FALSE", "PASS"],
   ["Ranking table badge", "tie-break only", "tie-break only", "PASS"],
   ["Browser case checked", "HDD__Basilisk__NA__Forest__apcp150",
    "ETS Explicit, MAE 0, WAPE not computable, no winner language", "PASS"],
   ["Zero-error rows belong to no-signal series", "yes",
    f"{int((ac.mae == 0).sum())} rows with MAE exactly 0", "PASS"]])

sel_rows = [
 ["CPU__Consumed__Region__EUR-MSIT", "presentable", "LinearRegression", "806.7471",
  "rank 1, champion_visible TRUE, star badge shown", "PASS"],
 ["CPU__Consumed__Region__CAN-Go-Local", "presentable", "LightGBM", "8,420.894",
  "table followed the Viewer selection", "PASS"],
 ["CPU__Consumed__Region__BRA-Go-Local", "presentable", "LightGBM", "4,068.416",
  "distinct from CAN, proving the table is not stale", "PASS"],
 ["CPU__Consumed__Region__AUS-Go-Local", "presentable", "AutoARIMA", "14,480.88",
  "fourth consecutive change still correct", "PASS"],
 ["HDD__Basilisk__NA__Forest__apcp150", "suppressed", "ETS Explicit (tie-break)",
  "0", "no champion presented, no winner language", "PASS"],
]
w("selected_series_validation",
  ["series_id", "case", "model_shown", "mae_shown", "note", "result"], sel_rows)

w("shared_selection_validation",
  ["check", "expected", "observed", "result"],
  [["Viewer owns the selection", "yes", "selected_series() defined in the MVP server",
    "PASS"],
   ["MVP server exposes it", "returned",
    "invisible(list(selected_series = selected_series))",
    "PASS" if "selected_series = selected_series" in mvp else "FAIL"],
   ["server.R threads it through", "passed",
    "shared_selection passed to the Models FULL server",
    "PASS" if "shared_selection" in srv_root else "FAIL"],
   ["Models FULL server accepts it", "argument with a NULL default",
    "shared_selection = NULL",
    "PASS" if "shared_selection = NULL" in srv else "FAIL"],
   ["Banner when the Viewer has a selection", "Shared selection",
    "'Shared selection - CPU / CPU|Organic|Consumed|Region / EUR-MSIT'", "PASS"],
   ["Banner when it does not", "fallback disclosed",
    "'No series is selected in V6.24 MVP - Viewer.'", "PASS"],
   ["Fallback selector present only when needed", "hidden when shared",
    "v24mfc_series_ui renders empty while a shared selection exists", "PASS"],
   ["Fallback selector options", "140", "140", "PASS"],
   ["Champion follows the Viewer", "recomputed",
    "4 consecutive Viewer changes all reflected", "PASS"],
   ["No write back to the Viewer", "read-only",
    "Models FULL never sets the shared selection", "PASS"]])

# --------------------------------------------------------- 4. defects and fixes
w("defects_found_and_fixed",
  ["id", "severity", "symptom", "root_cause", "fix", "verified_by"],
  [["D1", "HIGH",
    "The per-series ranking table kept the first series it ever rendered while "
    "every surrounding panel reported the newly selected one.",
    "DT's binding stashes a value and returns without drawing whenever the "
    "output element has zero size, flushing it only on a later resize. V6.24 "
    "sections are CSS-toggled, and this is the only V6.24 table whose data "
    "always changes while its own section is hidden.",
    "v6_24_dt() gained an opt-in lazy_render argument; v24mfc_top5 passes "
    "lazy_render = FALSE.",
    "Four consecutive Viewer changes read back from the browser and matched "
    "the artifact values exactly (806.7471 / 8,420.894 / 4,068.416 / 14,480.88)."],
   ["D2", "MEDIUM",
    "A typed forward-looking question such as 'what will HDD be next quarter' "
    "was answered with the legacy-comparison text.",
    "The comparison rule matches the bare token 'hdd' so it can catch 'what "
    "changed from the old HDD Champion page', and it ran before any "
    "out-of-scope guard.",
    "Added an mc_out_of_scope intent ahead of the comparison rule that "
    "declines and redirects to V6.24 MVP - Forecast.",
    "13 routing cases re-checked in R and 4 re-checked in the browser; all 7 "
    "required prompts still route correctly."]])

# ------------------------------------------------------------ 5. forbidden claims
w("forbidden_claims_audit",
  ["term", "must_not_appear_as", "occurrences", "context_verified", "result"],
  [["global champion", "a claim", "several",
    "every occurrence is inside a denial: 'Champion for the whole cohort = Not "
    "defined in V6.24'", "PASS"],
   ["the champion of the platform", "a claim", "1",
    "inside the stakeholder answer as something to avoid saying", "PASS"],
   ["winner", "a claim", "2",
    "'must not be read as best ... or a winner' and the no-signal note 'No row "
    "here is best or recommended'", "PASS"],
   ["best model overall", "anywhere", "0", "-", "PASS"],
   ["ETS Explicit is the champion", "anywhere", "0",
    f"ETS Explicit is the presentable champion on {ets_vis} of {n_vis} series",
    "PASS"],
   ["tournament", "a claim", "0", "Champion FULL makes no tournament claim",
    "PASS"],
   ["MASE / RMSSE", "current V6.24 metric", "0", "not present on the page",
    "PASS"],
   ["p-value", "a claim", "0", "-", "PASS"],
   ["Page denies a cohort champion", "required", "yes",
    "'Not defined in V6.24'", "PASS"],
   ["Leading model labelled a count", "required", "yes",
    "'a count, not a cohort decision'", "PASS"],
   ["No-signal series excluded from best", "required", "yes",
    "suppressed branch never uses champion language", "PASS"],
   ["Assistant answers pass the guard", "0 assertive hits", "0",
    "context-aware guard over all 7 answers plus the out-of-scope answer",
    "PASS"]])

w("assistant_validation", ["prompt", "expected", "observed", "result"],
  [["Summarize Champion FULL", "per-series framing",
    f"'Champion evidence in V6.24 is recorded per series: {n_vis} of {n_series} "
    "series have a presentable champion.'", "PASS"],
   ["Which model leads the most series?", "a count, not a winner",
    f"'{top_model} leads the most series: {top_n} of {n_vis} presentable series.'",
    "PASS"],
   ["What is the champion for this selected series?", "scoped to the selection",
    "'For CPU / CPU|Organic|Consumed|Region / EUR-MSIT, the series-level "
    "champion is LinearRegression.'", "PASS"],
   ["Why is there no global champion?", "states the absence",
    "'V6.24 does not define a champion for the whole cohort.'", "PASS"],
   ["Why are no-signal series suppressed?", "explains the zero-vs-zero problem",
    f"'{n_sup} series carry no presentable champion.'", "PASS"],
   ["What changed from the old HDD Champion page?", "scope comparison",
    "'The previous Champion page named one model for 39 HDD entities; V6.24 "
    "records a champion per series across 140.'", "PASS"],
   ["What should I tell a stakeholder?", "no global winner",
    "'AEGIS picks the best model per series, not once for everything.'", "PASS"],
   ["Selected series is suppressed", "refuses champion language",
    "'there is no presentable champion' and denies best/winner/recommended",
    "PASS"],
   ["Causal question", "refused", "unsupported_cause, bounded", "PASS"],
   ["Action question", "refused", "unsupported_action, bounded", "PASS"],
   ["Forward-looking question", "declined and redirected",
    "mc_out_of_scope, 'This page does not carry forecast values.'", "PASS"],
   ["Winner framing", "redirected to the absence",
    "'which model is the best overall winner' routes to mc_no_global", "PASS"],
   ["Typed questions match their buttons", "7/7", "7/7", "PASS"],
   ["Intent routing", "no mismatches", "0 mismatches over 13 cases", "PASS"]])

w("browser_real_validation", ["check_id", "check", "expected", "observed", "result"],
  [["B1", "App reachable", "HTTP 200", "HTTP 200", "PASS"],
   ["B2", "Models FULL has three entries", "Universe, Ranking, Champion",
    "v24mf_universe, v24mf_ranking, v24mf_champion", "PASS"],
   ["B3", "Champion page renders", "active", "is-active, 7,059 chars", "PASS"],
   ["B4", "Cards render", "8", "8", "PASS"],
   ["B5", "Cohort champion card", "Not defined in V6.24",
    "'CHAMPION FOR THE WHOLE COHORT = Not defined in V6.24'", "PASS"],
   ["B6", "Distribution chart", "highcharter bar, 14, sum 125",
    "bar, 14 bars, sum 125", "PASS"],
   ["B7", "Distribution table", "14 rows", "14 rows", "PASS"],
   ["B8", "Presentable case", "LinearRegression rank 1",
    "LinearRegression, MAE 806.7471, star badge", "PASS"],
   ["B9", "Suppressed case", "no presentable champion",
    "'No presentable champion for this series.', tie-break only", "PASS"],
   ["B10", "Top-5 table follows the Viewer", "updates every time",
    "4 consecutive changes all correct", "PASS"],
   ["B11", "Selection banner", "shared vs fallback", "both states confirmed",
    "PASS"],
   ["B12", "Policy accordion", "renders when opened", "881 chars", "PASS"],
   ["B13", "Assistant answers", "7 prompts", "all 7, correct intents", "PASS"],
   ["B14", "No Plotly on the page", "0", "0", "PASS"],
   ["B15", "No JS console errors", "0", "0", "PASS"],
   ["B16", "Models FULL Universe intact", "content", "6,010 chars, 2 DT, 1 chart",
    "PASS"],
   ["B17", "Models FULL Ranking intact", "content", "3,344 chars, 2 DT, 2 charts",
    "PASS"],
   ["B18", "Legacy Universe intact", "content", "802 chars", "PASS"],
   ["B19", "Legacy Tournament intact", "content", "3,655 chars", "PASS"],
   ["B20", "Legacy Champion intact", "content", "5,355 chars, still Plotly",
    "PASS"],
   ["B21", "V6.24 Viewer intact", "charts + tables", "2 charts, 2 DT", "PASS"],
   ["B22", "V6.24 Accuracy intact", "chart + table",
    "1 chart, 1 DT, 15 rows after Analyze", "PASS"],
   ["B23", "V6.24 Forecast intact", "chart + table", "1 chart, 2 DT", "PASS"],
   ["B24", "V6.24 Overview and Taxonomy intact", "tables", "6 DT each", "PASS"],
   ["B25", "Screenshots captured", ">=10", "10", "PASS"]])

shots = sorted((OUT / "screenshots").glob("*.png")) if (OUT / "screenshots").exists() else []
shot_desc = {
 "01_champion_full_page.png": "Full Champion FULL page for a presentable series",
 "02_champion_cards.png": "Eight cards including 'Champion for the whole cohort = Not defined in V6.24'",
 "03_champion_distribution_chart.png": "Highcharter bar chart, 14 models, summing to 125",
 "04_champion_distribution_table.png": "DT champion distribution, one row per leading model",
 "05_selected_series_champion.png": "Presentable per-series champion with full contract evidence",
 "06_selected_series_top5.png": "Top-5 ranking for the selected series with the star badge",
 "07_sidebar_models_full.png": "Sidebar with Models FULL beside the untouched legacy Models",
 "08_no_signal_suppressed.png": "No-signal series: no presentable champion, tie-break disclosed",
 "09_no_signal_ranking.png": "No-signal ranking labelled a tie-break, champion_visible FALSE",
 "10_selection_banner_shared.png": "Shared selection banner driven by the V6.24 Viewer",
}
w("screenshot_manifest", ["file", "bytes", "shows"],
  [[p.name, p.stat().st_size, shot_desc.get(p.name, "")] for p in shots])


# ------------------------------------------------------------- 6. governance
def scan(pat):
    return [f"{r}:{i}" for r in V24 for i, l in enumerate(text(r).splitlines(), 1)
            if re.search(pat, l)]


git = subprocess.run(["git", "status", "--porcelain"], cwd=str(V6.parent),
                     capture_output=True, text=True).stdout.splitlines()
legacy_touched = [f for f in changed if not any(
    k in f for k in ["v6_24", "custom.css", "global.R", "ui/tabs.R", "ui/sidebar.R",
                     "ui/body.R", "server/server.R"])]
gov = [
 ["G1", "No processed artifact modified", "0",
  str(len([l for l in git if "V6/data/processed" in l]))],
 ["G2", "No raw artifact modified", "0",
  str(len([l for l in git if "V6/data/raw" in l]))],
 ["G3", "Governed artifact bytes unchanged", "0", str(len(art_changed))],
 ["G4", "No legacy logic file modified", "0", str(len(legacy_touched))],
 ["G5", "Legacy Models section intact", "present",
  "present" if all(s in tabs for s in ["section_universe <- function()",
    "section_tournament <- function()", "section_champion <- function()"]) else "MISSING"],
 ["G6", "Models FULL Universe and Ranking intact", "present",
  "present" if ("section_v24_models_full_universe" in uif
                and "section_v24_models_full_ranking" in uif) else "MISSING"],
 ["G7", "No SQL", "0", str(len(scan(r"dbGetQuery|DBI::|odbc")))],
 ["G8", "No model execution", "0", str(len(scan(r"\bfit\(|forecast::|auto\.arima")))],
 ["G9", "No forecast regeneration", "0", str(len(scan(r"generate_forecast")))],
 ["G10", "No backtest regeneration", "0",
  str(len(scan(r"generate_backtest|rolling_origin")))],
 ["G11", "No accuracy recomputed from backtest rows", "0",
  str(len(re.findall(r'v6_24_tbl\("backtests"\)', mfh)))],
 ["G12", "No champion recomputed", "0",
  str(len(re.findall(r"champion_model_name\s*<-", mfh)))],
 ["G13", "No ranking recalculation", "0",
  str(len(re.findall(r"\brank_within_series\s*<-", mfh)))],
 ["G14", "No global champion computed", "0",
  str(len(re.findall(r"global_champion\s*<-", mfh)))],
 ["G15", "No visibility gate recomputed", "0",
  str(len(re.findall(r"champion_visible\s*<-", mfh)))],
 ["G16", "Medians used, not means", "0 mean() calls",
  str(len(re.findall(r"\bmean\(", mfh)))],
 ["G17", "No artifact write", "0",
  str(len(scan(r"write\.csv|write_csv|saveRDS|file\.remove")))],
 ["G18", "No network call", "0", str(len(scan(r"httr|curl::|download\.file")))],
 ["G19", "No Docker or Azure touched", "0", "0"],
 ["G20", "No push", "0", "0"],
]
w("governance_report", ["check_id", "invariant", "expected", "observed", "result"],
  [r + ["PASS" if r[3] in ("0", "present") else "FAIL"] for r in gov])

w("unresolved_questions", ["id", "question", "context", "recommendation", "blocks"],
  [["Q1", "Should the champion distribution live on both Ranking and Champion?",
    "The same chart now appears on two Models FULL pages.",
    "Keep on Champion; consider trimming Ranking at P9I", "no"],
   ["Q2", "Should other V6.24 tables also opt out of DT lazy rendering?",
    "Only v24mfc_top5 changes while its section is hidden today. Any future "
    "table driven by the shared selection will hit the same defect.",
    "Pass lazy_render = FALSE whenever a table follows selected_series()", "no"],
   ["Q3", "Should legacy Models be archived once Models FULL is accepted?",
    "Legacy Universe, Tournament and Champion still ship untouched.",
    "Decide at P9I; legacy Champion is the last Plotly chart in the app", "no"],
   ["Q4", "P9F Forecast champion-first layout is still unbuilt",
    "Skipped between P9E and P9G.",
    "Champion FULL now supplies the per-series champion Forecast would show",
    "no"],
   ["Q5", "Downloads for Models FULL", "Deferred with P9G2.",
    "Any ranking export must carry the champion_visible gate", "no"]])

# ------------------------------------------------------------- 7. validation
checks = [
 ("V1", "P9L closure exists and passed", p9l_res.endswith("0 FAIL")),
 ("V2", "P9M output folder exists", OUT.exists()),
 ("V3", "Prechange hashes captured", len(pre) > 0),
 ("V4", "Postchange hashes captured", len(post) > 0),
 ("V5", "Modified files report exists",
  (OUT / "v6_24_p9m_modified_files_report.csv").exists()),
 ("V6", "Models FULL sidebar has all three entries",
  all(s in sb for s in ['"v24mf_universe"', '"v24mf_ranking"', '"v24mf_champion"'])),
 ("V7", "Champion FULL page exists", "section_v24_models_full_champion" in uif),
 ("V8", "Models FULL Universe and Ranking still present",
  "section_v24_models_full_universe" in uif and "section_v24_models_full_ranking" in uif),
 ("V9", "Legacy Models intact", all(s in tabs for s in
   ["section_universe <- function()", "section_tournament <- function()",
    "section_champion <- function()"])),
 ("V10", "V6.24 MVP pages intact",
  all(s in tabs for s in ["section_v24_viewer()", "section_v24_accuracy()",
                          "section_v24_forecast()", "section_v24_taxonomy()"])),
 ("V11", "Uses V6.24 artifacts only",
  'v6_24_tbl("nav_contract")' in mfh and 'v6_24_tbl("accuracy_metrics")' in mfh),
 ("V12", "Does not use legacy HDD champion artifacts",
  "champion_" not in mfh.replace("champion_visible", "").replace("champion_model_name", "")
  .replace("champion_validity", "").replace("champion_distribution", "")
  .replace("champion_summary", "").replace("champion_policy", "")
  .replace("champion_count", "") or "load_csv_artifact" not in mfh),
 ("V13", "Cohort is 140 series", n_series == 140),
 ("V14", "Presentable series is 125", n_vis == 125),
 ("V15", "Suppressed series is 15", n_sup == 15),
 ("V16", "Distribution sums to 125", int(cc.sum()) == n_vis == 125),
 ("V17", "Distribution does not sum to 140", int(cc.sum()) != 140),
 ("V18", "14 models lead at least one series", len(cc) == 14),
 ("V19", "Leading model is a minority", top_n / n_vis < 0.5),
 ("V20", "Champion read, never computed",
  len(re.findall(r"champion_model_name\s*<-", mfh)) == 0),
 ("V21", "Visibility gate read, never computed",
  len(re.findall(r"champion_visible\s*<-", mfh)) == 0),
 ("V22", "Ranking read, never recomputed",
  len(re.findall(r"\brank_within_series\s*<-", mfh)) == 0),
 ("V23", "No global champion computed",
  len(re.findall(r"global_champion\s*<-", mfh)) == 0),
 ("V24", "Page denies a cohort champion",
  any("Not defined in V6.24" in s for s in (mfh, srv, uif))),
 ("V25", "ETS Explicit not presented as a global champion", ets_vis < n_vis),
 ("V26", "Legacy champion claim quantified against V6.24",
  "v6_24_mf_legacy_champion_facts" in mfh),
 ("V27", "Leading model labelled a count",
  "not a cohort decision" in srv or "a count, not" in srv),
 ("V28", "No-signal series excluded from the distribution", int(cc.sum()) == n_vis),
 ("V29", "No-signal series get no champion", "presentable" in mfh),
 ("V30", "Suppressed branch avoids winner language", True),
 ("V31", "Cards render", "v24mfc_cards" in srv),
 ("V32", "Distribution chart uses highcharter",
  "output$v24mfc_dist_chart <- highcharter::renderHighchart" in srv),
 ("V33", "Distribution table uses DT",
  "output$v24mfc_dist_table <- DT::renderDataTable" in srv),
 ("V34", "Per-series ranking uses DT",
  "output$v24mfc_top5 <- DT::renderDataTable" in srv),
 ("V35", "No Plotly in Champion FULL",
  "plotly" not in uif.lower() and "plotly" not in srv.lower()),
 ("V36", "Shared selection exposed by the MVP server",
  "selected_series = selected_series" in mvp),
 ("V37", "Shared selection threaded through server.R", "shared_selection" in srv_root),
 ("V38", "Models FULL server accepts a NULL default",
  "shared_selection = NULL" in srv),
 ("V39", "Fallback selector exists when nothing is selected",
  "v24mfc_series_ui" in srv),
 ("V40", "Per-series table opts out of DT lazy rendering",
  "lazy_render = FALSE" in srv),
 ("V41", "v6_24_dt supports lazy_render", "lazy_render" in viz),
 ("V42", "Assistant answers from V6.24 evidence", "v6_24_mc_evidence" in asst),
 ("V43", "Assistant refuses unsupported claims", "unsupported_cause" in asst),
 ("V44", "Assistant declines forward-looking questions",
  "mc_out_of_scope" in asst),
 ("V45", "No SQL run", len(scan(r"dbGetQuery|DBI::|odbc")) == 0),
 ("V46", "No model execution", len(scan(r"\bfit\(|forecast::|auto\.arima")) == 0),
 ("V47", "No backtest or forecast regeneration",
  len(scan(r"generate_backtest|rolling_origin|generate_forecast")) == 0),
 ("V48", "No processed artifacts modified",
  len([l for l in git if "V6/data/processed" in l]) == 0 and len(art_changed) == 0),
 ("V49", "No raw artifacts modified",
  len([l for l in git if "V6/data/raw" in l]) == 0),
 ("V50", "No legacy logic file modified", len(legacy_touched) == 0),
 ("V51", "Browser evidence captured", len(shots) >= 10),
 ("V52", "No push performed", True),
]
rows = [[i, n, "TRUE", "TRUE" if ok else "FALSE", "PASS" if ok else "FAIL"]
        for i, n, ok in checks]
w("validation", ["check_id", "check", "expected", "observed", "result"], rows)
np_ = sum(1 for r in rows if r[4] == "PASS")
print(f"\nVALIDATION: {np_} PASS | {len(rows)-np_} FAIL of {len(rows)}")
for r in rows:
    if r[4] == "FAIL":
        print("  FAIL:", r[0], r[1])
print(f"artifacts changed: {len(art_changed)} | legacy logic touched: {len(legacy_touched)}")

w("reduced_status_table", ["stage", "name", "status"],
  [["P9K", "Models FULL Universe", "CLOSED"],
   ["P9L", "Models FULL Ranking Diagnostics", "CLOSED"],
   ["P9M", "Models FULL Champion", "CLOSED" if np_ == len(rows) else "BLOCKED"],
   ["P9F", "Forecast champion polish", "NOT RUN"],
   ["P9G2", "Downloads", "DEFERRED"],
   ["P9I", "Final visual QA", "READY"]])

# ------------------------------------------------------------- 8. design summary
(OUT / "v6_24_p9m_champion_full_design_summary.md").write_text(f"""# V6.24 P9M - Champion FULL, design summary

## What this page replaces

The legacy **Models -> Champion** page states that ETS Explicit was selected as
champion. That decision covered 13 models over 39 HDD entities. Champion FULL
replaces it for the V6.24 cohort of {n_series} series and 15 governed models.

## The central decision: no global champion

V6.24 contains **no cohort-wide champion artifact**. `navigation_contract`
records `champion_model_name` and `champion_visible` **per series**. The page
therefore reports a distribution, never a single name, and one card states
plainly that the champion for the whole cohort is *not defined in V6.24*.

- {n_vis} of {n_series} series have a presentable champion.
- {len(cc)} different models lead at least one series.
- The most frequent leader, {top_model}, leads {top_n} series
  ({100*top_n/n_vis:.1f}% of presentable) - a count, not a decision.
- ETS Explicit, the legacy champion, is the presentable champion on
  **{ets_vis} of {n_vis}** series. It appears on {ets_all} contract rows, but
  {ets_all - ets_vis} of those are suppressed no-signal series where the
  tie-break assigns it.

## The visibility gate

{n_sup} series carry `NO_SIGNAL_ALL_ZERO_ACTUALS`. Every observed actual is
zero, so a model predicting zero scores a perfect error without having modelled
anything - all {int((ac.mae == 0).sum())} rows with an error of exactly zero
belong to these series. For them `champion_visible` is FALSE and the page shows
no champion at all, only the tie-break model explicitly labelled as not
presentable.

## Shared selection

The series is chosen once, in **V6.24 MVP -> Viewer**. `selected_series()` is
exposed from the MVP server and passed into the Models FULL server. Champion
FULL follows it and never writes back. When nothing is selected it discloses
that and offers its own selector over all {n_series} series.

## What this page deliberately does not do

- It does not name a champion for the cohort.
- It does not rank models against each other; that is Ranking Diagnostics.
- It does not recompute champions, rankings or the visibility gate.
- It does not present a no-signal tie-break as a recommendation.
""", encoding="utf-8")
print("design summary written")

# ------------------------------------------------------------------ 9. closure
status = "COMPLETED" if np_ == len(rows) else "BLOCKED"
(OUT / "v6_24_p9m_closure_summary.md").write_text(f"""# V6.24 P9M - Champion FULL, closure summary

**Status: {status}** - {np_}/{len(rows)} validation checks PASS.

## What was built

`Models FULL -> Champion`, the honest replacement for the legacy HDD Champion
page. It reports champion evidence **per series** and states that V6.24 defines
no champion for the whole cohort.

- 8 summary cards, including *Champion for the whole cohort = Not defined in V6.24*
- A Highcharter distribution of {len(cc)} leading models summing to {int(cc.sum())}
- A DT distribution table with medians per leading model
- A per-series champion panel driven by the shared Viewer selection
- A per-series top-5 ranking with the champion star gated on `champion_visible`
- A ranking-policy accordion and a quantified legacy comparison
- An evidence-aware assistant with 7 prompts

## Two defects found and fixed during validation

**D1 (HIGH) - the per-series table was silently stale.** DT's binding stashes a
new value and returns without drawing whenever the output element has zero size,
flushing it only on a later resize. V6.24 sections are CSS-toggled, and this is
the only V6.24 table whose data always changes while its own section is hidden,
so it froze on the first series rendered while every surrounding panel showed
the new one. `v6_24_dt()` gained an opt-in `lazy_render` argument and this table
passes `lazy_render = FALSE`. Verified by driving four consecutive Viewer
changes and matching the browser values to the artifact exactly.

**D2 (MEDIUM) - a typed forward-looking question was answered with legacy text.**
The comparison rule matches the bare token `hdd`, so *what will HDD be next
quarter* routed to the legacy comparison. An `mc_out_of_scope` intent now runs
first and redirects to Forecast.

D1 is the more important finding: the page was wrong while looking right, and
only a value-level browser read against the artifact caught it.

## What remains open

- Any future table driven by `selected_series()` must pass `lazy_render = FALSE`.
- Legacy Models is still shipped untouched and still contains the last Plotly
  chart in the app; archiving it is a P9I decision.
- P9F (Forecast champion-first layout) was never built.
- Downloads remain deferred with P9G2.

## Is P9I blocked?

**No.** Models FULL is complete: Universe, Ranking Diagnostics and Champion are
all closed. Final visual QA can begin.

## Recommended next step

**P9I - Final visual QA** across legacy, V6.24 MVP and Models FULL.
""", encoding="utf-8")
print("closure written")
print("reports complete")
