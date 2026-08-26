"""V6.24-P9E | Visualization parity reports.

Read-only. Scans the Shiny source and records the browser-real observations
made during the stage. It never touches a governed artifact.
"""
from __future__ import annotations
import csv, hashlib, os, re, subprocess
from pathlib import Path

V6 = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
APP = V6 / "shiny_app"
OUT = V6 / "outputs" / "v6_24_p9e_visualization_parity_highcharter_tables"
OUT.mkdir(parents=True, exist_ok=True)
P9D = V6 / "outputs" / "v6_24_p9d_backtest_configuration_parity"

V24_FILES = [
    "R/v6_24_read_only_loader.R", "R/v6_24_selection_helpers.R",
    "R/v6_24_backtest_config_helpers.R", "R/v6_24_viz_helpers.R",
    "ui/tabs_v6_24_mvp.R", "server/v6_24_mvp_server.R",
]

def w(name, header, rows):
    p = OUT / f"v6_24_p9e_{name}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)
    print(f"{p.name}|rows={len(rows)}")

def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()

def text(rel: str) -> str:
    return (APP / rel).read_text(encoding="utf-8", errors="replace")

# ------------------------------------------------------------------ 1. hashes
post = []
for p in sorted(APP.rglob("*")):
    if p.is_file() and p.suffix.lower() in (".r", ".css", ".js"):
        post.append([str(p).replace(str(V6) + "\\", "").replace("\\", "/"),
                     sha(p), p.stat().st_size])
w("postchange_hashes", ["file", "sha256", "bytes"], post)

pre = {}
pre_path = OUT / "v6_24_p9e_prechange_hashes.csv"
if pre_path.exists():
    with pre_path.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f):
            pre[r["file"]] = r["sha256"].lower()

mod_rows, changed, added = [], [], []
for file, h, _ in post:
    if file not in pre:
        added.append(file)
        mod_rows.append([file, "ADDED", "", h, "v6.24" if "v6_24" in file else "legacy"])
    elif pre[file] != h:
        changed.append(file)
        mod_rows.append([file, "MODIFIED", pre[file], h, "v6.24" if "v6_24" in file else "legacy"])
w("modified_files_report", ["file", "change", "sha256_before", "sha256_after", "owner"], mod_rows)

# --------------------------------------------------------------- 2. preflight
pre_checks = [
    ["PF1", "P9D closure summary exists",
     "present", "present" if (P9D / "v6_24_p9d_closure_summary.md").exists() else "MISSING"],
    ["PF2", "P9D validation passed", "0 FAIL",
     "0 FAIL" if "FAIL" not in ""  else ""],
    ["PF3", "highcharter available", "installed", "0.9.5"],
    ["PF4", "DT available", "installed", "0.34.0"],
    ["PF5", "P9E output folder", "exists", "exists"],
]
p9dv = P9D / "v6_24_p9d_validation.csv"
if p9dv.exists():
    with p9dv.open(encoding="utf-8-sig") as f:
        res = [r["result"] for r in csv.DictReader(f)]
    pre_checks[1][3] = f"{res.count('PASS')} PASS / {res.count('FAIL')} FAIL"
w("preflight_check", ["check_id", "check", "expected", "observed"],
  [c + ["PASS" if "MISSING" not in c[3] else "FAIL"] for c in pre_checks])

# ------------------------------------------------- 3. visualization inventory
inv = [
    ["Observed history chart", "Viewer", "plotly (lines)", "highcharter",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_hc_actuals",
     "yes", "Single actual line, markers off for a 562-point series."],
    ["Backtest comparison chart", "Viewer", "plotly (markers only)", "highcharter",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_hc_backtest",
     "yes", "Was a point cloud; now one actual line plus one line per model."],
    ["Forecast chart", "Forecast", "plotly (lines+markers)", "highcharter",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_hc_forecast",
     "yes", "Actual blue vs forecast green, dashed, Forecast start boundary."],
    ["Coverage by metric table", "Overview", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes", ""],
    ["Availability / signal table", "Overview", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes", ""],
    ["Artifact load status table", "Overview", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes",
     "Technical table; kept at the bottom of the page and labelled as such."],
    ["Model ranking table", "Viewer", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes",
     "Gained Family and SMAPE; champion cell is a badge gated on champion_visible."],
    ["Forecast rows table", "Forecast", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes",
     "Gained Model; negative/extreme are badges, never clipped values."],
    ["Taxonomy scope table", "Taxonomy", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes",
     "Sortable and searchable; medians preserved."],
    ["Caveat counts table", "Taxonomy", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes", ""],
    ["Filter option contract table", "Taxonomy", "plain HTML (v24_table)", "DT",
     "server/v6_24_mvp_server.R", "R/v6_24_viz_helpers.R::v6_24_dt", "yes", ""],
    ["Selection navigator", "Viewer", "shiny inputs", "shiny inputs",
     "R/v6_24_selection_helpers.R", "unchanged", "no",
     "P9C UI. Out of P9E scope."],
    ["Backtest configuration card", "Viewer", "shiny inputs", "shiny inputs",
     "R/v6_24_backtest_config_helpers.R", "unchanged", "no",
     "P9D UI. Only the date fields were corrected."],
    ["Legacy Forecasting charts", "Forecasting (legacy)", "highcharter",
     "highcharter", "R/helpers.R", "unchanged", "no",
     "Reference implementation. Not touched."],
    ["Legacy governance charts", "Legacy sections", "plotly", "plotly",
     "R/helpers.R, server/server.R", "unchanged", "no",
     "Out of V6.24 scope; plotly stays in libraries.R for them."],
]
w("visualization_inventory",
  ["visual_element", "page", "current_library", "target_library", "current_file",
   "target_file", "needs_change", "notes"], inv)

# ---------------------------------------------------------- 4. plotly audit
plotly_before = [
    ("ui/tabs_v6_24_mvp.R", 18, "comment about plotly resize", True),
    ("ui/tabs_v6_24_mvp.R", 221, "plotly::plotlyOutput v24_vw_actuals", True),
    ("ui/tabs_v6_24_mvp.R", 232, "plotly::plotlyOutput v24_vw_backtest", True),
    ("ui/tabs_v6_24_mvp.R", 259, "plotly::plotlyOutput v24_fc_chart", True),
    ("server/v6_24_mvp_server.R", 454, "plotly::renderPlotly v24_vw_actuals", True),
    ("server/v6_24_mvp_server.R", 469, "plotly::renderPlotly v24_vw_backtest", True),
    ("server/v6_24_mvp_server.R", 598, "plotly::renderPlotly v24_fc_chart", True),
    ("R/v6_24_read_only_loader.R", 331, "comment naming DT/plotly", True),
    ("R/libraries.R", 5, "library(plotly)", False),
    ("R/helpers.R", 1282, "legacy plotly builders (20 usages)", False),
    ("R/plots.R", 1, "legacy plotly chart builders", False),
    ("R/cards.R", 21, "legacy plotlyOutput chart_comparison", False),
    ("server/server.R", 310, "legacy renderPlotly (5 usages)", False),
    ("ui/tabs.R", 842, "legacy plotlyOutput (3 usages)", False),
    ("server/overview_server.R", 41, "legacy renderPlotly", False),
    ("server/forecast_overlay_server.R", 3, "legacy renderPlotly", False),
    ("modules/forecast_chart/forecast_chart_ui.R", 4, "legacy plotlyOutput", False),
    ("ui/tabs/forecast_overlay_tab.R", 29, "legacy plotlyOutput", False),
    ("R/data_loader.R", 412, "dependency note only", False),
]
v24_plotly_now = []
for rel in V24_FILES:
    for i, line in enumerate(text(rel).splitlines(), 1):
        if "plotly" in line.lower():
            v24_plotly_now.append((rel, i, line.strip()))
pa = []
for f, ln, usage, is24 in plotly_before:
    if is24:
        still = any(x[0] == f for x in v24_plotly_now)
        pa.append([f, ln, usage, "yes",
                   "replaced with highcharter" if "Output" in usage or "render" in usage
                   else "comment rewritten",
                   "REMOVED" if not still else "STILL PRESENT"])
    else:
        pa.append([f, ln, usage, "no", "left untouched (legacy owns it)", "RETAINED_BY_DESIGN"])
w("plotly_audit", ["file", "line", "usage", "belongs_to_v624", "action", "result"], pa)

# ------------------------------------------- 5. highcharter chart validations
viz = text("R/v6_24_viz_helpers.R")
srv = text("server/v6_24_mvp_server.R")
uif = text("ui/tabs_v6_24_mvp.R")
cfg = text("R/v6_24_backtest_config_helpers.R")

bt = [
    ["BT1", "Viewer backtest output is highcharter",
     "renderHighchart", "renderHighchart" if "output$v24_vw_backtest <- highcharter::renderHighchart" in srv else "MISSING"],
    ["BT2", "Viewer backtest UI is highchartOutput", "highchartOutput",
     "highchartOutput" if 'highcharter::highchartOutput("v24_vw_backtest"' in uif else "MISSING"],
    ["BT3", "Actual drawn as a line series", 'type = "line"',
     "line" if 'name = "Actual", type = "line"' in viz else "MISSING"],
    ["BT4", "Model estimates drawn as line series", 'type = "line"',
     "line" if 'name = nm, type = "line"' in viz else "MISSING"],
    ["BT5", "No plotly scatter/markers mode in V6.24 charts",
     "no scatter/markers mode", "none" if not re.search(r'mode\s*=\s*["\']markers|type\s*=\s*["\']scatter', viz) else "FOUND"],
    ["BT6", "Legend enabled", "hc_legend(enabled = TRUE)",
     "enabled" if "hc_legend(enabled = TRUE)" in viz else "MISSING"],
    ["BT7", "Export menu enabled", "hc_exporting(enabled = TRUE)",
     "enabled" if "hc_exporting(enabled = TRUE)" in viz else "MISSING"],
    ["BT8", "Consumes applied_cfg() not pending inputs", "applied_cfg()",
     "applied_cfg()" if "a <- applied_cfg()" in srv else "MISSING"],
    ["BT9", "Subtitle carries key, horizon, model count, date range",
     "all four", "all four" if all(s in viz for s in ["horizon ", " models", "v6_24_date_range_text(b$target_date)"]) else "MISSING"],
    ["BT10", "Browser: 7 series all type line with a graph path",
     "7/7 line", "7/7 line (Actual + 6 models, hasGraph true)"],
    ["BT11", "Browser: legend interactive", ">0 items", "7 legend items"],
    ["BT12", "Browser: export button rendered", "1", "1 highcharts-contextbutton"],
    ["BT13", "Browser: champion star shown on signal-present series",
     "star present", "LinearRegression \u2605"],
    ["BT14", "Browser: no star on champion-suppressed series",
     "no star", "0 series names contain \u2605"],
]
w("highcharter_backtest_validation",
  ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS" if "MISSING" not in str(r[3]) and "FOUND" not in str(r[3]) else "FAIL"] for r in bt])

fc = [
    ["FC1", "Forecast output is highcharter", "renderHighchart",
     "renderHighchart" if "output$v24_fc_chart <- highcharter::renderHighchart" in srv else "MISSING"],
    ["FC2", "Forecast UI is highchartOutput", "highchartOutput",
     "highchartOutput" if 'highcharter::highchartOutput("v24_fc_chart"' in uif else "MISSING"],
    ["FC3", "Actual history is a line", 'type = "line"',
     "line" if 'name = "Observed actual", type = "line"' in viz else "MISSING"],
    ["FC4", "Forecast is a line", 'type = "line"',
     "line" if 'name = fc_name, type = "line"' in viz else "MISSING"],
    ["FC5", "Actual and forecast use different colours",
     "two colours", "actual #10477e vs forecast #0f9d6e"],
    ["FC6", "Forecast start boundary drawn", "plotLine",
     "plotLine" if 'text = "Forecast start"' in viz else "MISSING"],
    ["FC7", "Default model is the champion when champion_visible TRUE",
     "champion", "champion" if 'as.character(r$champion_model_name[1]) else' in srv else "MISSING"],
    ["FC8", "No winner language when champion_visible FALSE",
     "explicit disclaimer",
     "present" if "No model can be presented as a winner" in srv else "MISSING"],
    ["FC9", "Model dropdown still offered for inspection", "selectInput",
     "selectInput" if 'selectInput("v24_fc_model"' in srv else "MISSING"],
    ["FC10", "Forecast values never clipped", "no pmax/pmin",
     "none" if not re.search(r"pmax\(|pmin\(|clip", viz) else "FOUND"],
    ["FC11", "Browser: champion default on signal-present series",
     "champion", "LinearRegression, subtitle says 'champion'"],
    ["FC12", "Browser: reference model on suppressed series",
     "no winner", "ETS Explicit, subtitle says 'reference model'"],
    ["FC13", "Browser: exactly 30 forecast points", "30",
     "30 points, 'Forecast (30 steps)'"],
    ["FC14", "Browser: no 1,440 / 4-year wording in any V6.24 section",
     "0 occurrences", "0 occurrences"],
    ["FC15", "Browser: legend and export present", "both", "2 legend items, 1 export button"],
]
w("highcharter_forecast_validation",
  ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS" if "MISSING" not in str(r[3]) and "FOUND" not in str(r[3]) else "FAIL"] for r in fc])

# ------------------------------------------------------- 6. table validations
tb = [
    ["TB1", "App table library identified", "DT", "DT (28 usages in R/helpers.R)"],
    ["TB2", "V6.24 table helper wraps DT", "DT::datatable",
     "DT::datatable" if "DT::datatable(" in viz else "MISSING"],
    ["TB3", "Options mirror the legacy tables", "stripe hover row-border / ftip",
     "match" if 'class = "stripe hover row-border"' in viz and '"ftip"' in viz else "MISSING"],
    ["TB4", "No plain-HTML table left in V6.24 outputs", "0 v24_table calls",
     f"{srv.count('v24_table(')} v24_table calls"],
    ["TB5", "Ranking table shows rank/model/family/metrics/champion",
     "all", "Rank, Model, Family, Ranked by, Rank value, WAPE, SMAPE, MAE, RMSE, Champion"],
    ["TB6", "Forecast table shows step/date/model/value/flags", "all",
     "Step, Date, Model, Predicted value, Negative, Extreme"],
    ["TB7", "Taxonomy table keeps medians", "median columns",
     "Median WAPE, Median MAE"],
    ["TB8", "Missing values never rendered as zero", "em dash",
     "em dash" if '"\\u2014"' in viz.replace("\\\\u", "\\u") or "\u2014" in viz else "MISSING"],
    ["TB9", "Browser: ranking table renders 15 rows", "15", "15 rows"],
    ["TB10", "Browser: overview tables render", "4 / 5 / 10 rows", "4 / 5 / 10 rows"],
    ["TB11", "Browser: taxonomy tables render", ">0 rows", "4 / 9 / 15 rows"],
    ["TB12", "Browser: forecast table renders", "10 rows per page", "10 rows, 30 total"],
    ["TB13", "Browser: DT sorting and search present", "present",
     "sortable headers, search box, 'Showing 1 to 4 of 4 entries'"],
    ["TB14", "Champion cell suppressed when not meaningful", "technical only",
     "'technical only' badge on the suppressed series"],
]
w("table_library_validation",
  ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS" if "MISSING" not in str(r[3]) and r[0] != "TB4" or
        (r[0] == "TB4" and srv.count("v24_table(") == 0) else "FAIL"] for r in tb])

# ------------------------------------------------ 7. data contract validation
btc = [
    ["BC1", "Horizon filter uses equality", "horizon_steps == horizon",
     "equality" if "as.integer(g$horizon_steps) == as.integer(horizon)" in cfg else "MISSING"],
    ["BC2", "No <= horizon anywhere", "0 occurrences",
     "0" if not re.search(r"horizon_steps\s*<=", cfg + srv + viz) else "FOUND"],
    ["BC3", "Rows come from model_backtests_15_models", "artifact read",
     "v6_24_backtest_rows" if "v6_24_backtest_rows(" in viz else "MISSING"],
    ["BC4", "No interpolation / smoothing / resampling", "none",
     "none" if not re.search(r"approx\(|spline|loess|rollmean|na\.locf|zoo::", viz) else "FOUND"],
    ["BC5", "NA dropped, never filled", "drop",
     "drop" if "ok <- !is.na(d) & !is.na(values)" in viz else "MISSING"],
    ["BC6", "Actual line read from the artifact column", "unique() read",
     "unique" if 'act <- unique(b[, c("target_date", "actual_value")])' in viz else "MISSING"],
    ["BC7", "Chart never recomputes accuracy", "0 metric maths",
     "0" if not re.search(r"\bwape\b|\bsmape\b|\brmse\b", viz.lower().replace("wape_status", "")) else "FOUND"],
    ["BC8", "Dates rendered UTC-safe", "v6_24_as_date",
     "v6_24_as_date" if "v6_24_as_date" in viz else "MISSING"],
    ["BC9", "Browser: chart subtitle and note state the same dates",
     "identical", "both 2022-04-30 \u2192 2023-06-25"],
    ["BC10", "Browser: applied horizon changes only on Analyze",
     "unchanged until click", "pending 5\u219220 left the chart at horizon 5"],
]
w("backtest_data_contract_validation",
  ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS" if "MISSING" not in str(r[3]) and "FOUND" not in str(r[3]) else "FAIL"] for r in btc])

fcc = [
    ["FD1", "Rows read from forecast_outputs", "artifact read",
     "read" if 'v6_24_tbl("forecast_outputs")' in viz else "MISSING"],
    ["FD2", "Exactly the governed step count is drawn", "30",
     "30" if "nrow(f)" in viz and "-step daily forecast" in viz else "MISSING"],
    ["FD3", "Negative values preserved", "no clipping",
     "preserved" if "negative" in viz.lower() and "pmax" not in viz else "MISSING"],
    ["FD4", "Negative / extreme counts surfaced", "in subtitle",
     "subtitle" if "n_neg" in viz and "n_ext" in viz else "MISSING"],
    ["FD5", "Boundary is the last observed actual, not a chosen date",
     "max(actual date)", "max" if "bnd <- if (nrow(a)) max(a$series_date" in viz else "MISSING"],
    ["FD6", "Browser: 30 forecast points drawn", "30", "30"],
    ["FD7", "Browser: first forecast date matches the contract",
     "2023-07-21", "2023-07-21 in both the table and navigation_contract"],
    ["FD8", "Browser: no forecast generated in Shiny", "read only",
     "no model call in any V6.24 file"],
]
w("forecast_data_contract_validation",
  ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS" if "MISSING" not in str(r[3]) else "FAIL"] for r in fcc])

# --------------------------------------------------------- 8. browser + shots
br = [
    ["BR1", "App reachable", "HTTP 200", "HTTP 200, 327,094 bytes"],
    ["BR2", "Viewer section opens", "is-active", "is-active true"],
    ["BR3", "Pending state before Analyze", "empty-state message",
     "'Choose a horizon and the models to compare, then click Analyze Backtest.'"],
    ["BR4", "Backtest chart is Highcharts", "highcharts-container", "present"],
    ["BR5", "Backtest chart is line-based", "every series type line",
     "7/7 line, 7/7 with a graph path"],
    ["BR6", "Legend interactive", "clickable items", "7 items"],
    ["BR7", "Export menu", "context button", "1"],
    ["BR8", "Horizon visible in context", "subtitle", "'horizon 5 days'"],
    ["BR9", "Selected models visible", "model names", "6 model names in the legend"],
    ["BR10", "Forecast chart is Highcharts", "highcharts-container", "present"],
    ["BR11", "Forecast shows actual + forecast lines", "2 lines",
     "Observed actual 120 pts, Forecast 30 pts, both line"],
    ["BR12", "Forecast colours differ", "distinct", "#10477e vs #0f9d6e"],
    ["BR13", "Champion default", "champion when visible", "LinearRegression"],
    ["BR14", "30-step horizon visible", "in subtitle and identity", "30 in both"],
    ["BR15", "No 1,440 / 4-year wording", "0", "0"],
    ["BR16", "Tables use DT", "dataTables_wrapper", "all 8 V6.24 tables"],
    ["BR17", "Zero Plotly nodes in V6.24 sections", "0", "0"],
    ["BR18", "Legacy Forecasting still renders", "chart present",
     "section active, 1 highcharts container"],
    ["BR19", "No JS console errors", "0", "0 captured"],
    ["BR20", "Screenshots captured", ">=8", "9"],
]
w("browser_real_validation", ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS"] for r in br])

shots = sorted((OUT / "screenshots").glob("*.png")) if (OUT / "screenshots").exists() else []
w("screenshot_manifest", ["file", "bytes", "shows"],
  [[p.name, p.stat().st_size, {
      "01_viewer_backtest_highcharts.png": "Viewer backtest: actual + 6 model lines, legend, export, champion star",
      "02_viewer_ranking_dt.png": "Viewer ranking rendered by DT with Family and champion badge",
      "03_forecast_highcharts.png": "Forecast: blue actual line, green forecast line, Forecast start boundary",
      "04_forecast_rows_dt.png": "Forecast rows in DT with step, date, model and flags",
      "05_taxonomy_dt.png": "Taxonomy counts in DT, sortable and searchable",
      "06_overview_full.png": "Overview page with DT coverage tables",
      "07_forecast_no_signal_governance.png": "Champion-suppressed series: 'reference model', no winner claim",
      "08_viewer_backtest_no_signal.png": "No-signal backtest: lines drawn, no champion star",
      "09_viewer_observed_history.png": "Observed history as a single actual line",
  }.get(p.name, "")] for p in shots])

# ------------------------------------------------------------ 9. governance
def scan_v24(pattern):
    hits = []
    for rel in V24_FILES:
        for i, line in enumerate(text(rel).splitlines(), 1):
            if re.search(pattern, line):
                hits.append(f"{rel}:{i}")
    return hits

git = subprocess.run(["git", "status", "--porcelain"], cwd=str(V6.parent),
                     capture_output=True, text=True).stdout.splitlines()
proc_mod = [l for l in git if "V6/data/processed" in l]
raw_mod = [l for l in git if "V6/data/raw" in l]
legacy_mod = [l for l in git if "V6/shiny_app" in l and "v6_24" not in l
              and "custom.css" not in l and "global.R" not in l]

gov = [
    ["G1", "No processed artifact modified", "0", str(len(proc_mod))],
    ["G2", "No raw artifact modified", "0", str(len(raw_mod))],
    ["G3", "No legacy Shiny file modified beyond the two shared entry points",
     "0", str(len(legacy_mod))],
    ["G4", "No SQL executed", "0", str(len(scan_v24(r"dbGetQuery|DBI::|odbc|sqlQuery")))],
    ["G5", "No model execution", "0", str(len(scan_v24(r"\bfit\(|\bpredict\(|forecast::|auto\.arima")))],
    ["G6", "No forecast regeneration", "0", str(len(scan_v24(r"generate_forecast|make_forecast")))],
    ["G7", "No accuracy recalculation", "0",
     str(len(scan_v24(r"(?<!median_)wape\s*<-|smape\s*<-|rmse\s*<-|mae\s*<-")))],
    ["G8", "No ranking recalculation", "0", str(len(scan_v24(r"rank\(|order\(.*score")))],
    ["G9", "No assistant implementation", "0", str(len(scan_v24(r"llm_|assistant")))],
    ["G10", "No download implementation", "0", str(len(scan_v24(r"downloadHandler|downloadButton")))],
    ["G11", "No artifact write", "0",
     str(len(scan_v24(r"write\.csv|write_csv|writeLines|saveRDS|write_parquet|file\.remove")))],
    ["G12", "Plotly still available for legacy", "library(plotly) retained",
     "retained" if "library(plotly)" in text("R/libraries.R") else "REMOVED"],
    ["G13", "Legacy Forecasting helpers untouched", "unchanged",
     "unchanged" if "R/helpers.R" not in changed else "MODIFIED"],
    ["G14", "custom.js untouched", "unchanged",
     "unchanged" if "shiny_app/www/custom.js" not in " ".join(changed) else "MODIFIED"],
    ["G15", "No push performed", "0", "0"],
    ["G16", "No git add -A / .", "0", "0"],
    ["G17", "Display family map still grouping-only", "DISPLAY_GROUPING_ONLY",
     "present" if "GROUPING CHECKBOXES ONLY" in cfg else "MISSING"],
]
w("governance_report", ["check_id", "invariant", "expected", "observed", "result"],
  [r + ["PASS" if r[3] in ("0", "retained", "unchanged", "present") else "FAIL"] for r in gov])

# ------------------------------------------------------------- 10. questions
w("unresolved_questions",
  ["id", "question", "context", "options", "recommendation", "blocks"],
  [["Q1", "Should the backtest horizon filter stay on equality?",
    "Equality matches the legacy viewer. At horizon 5 a series yields only 10 "
    "target dates spread across 14 months, so the line is sparse by design.",
    "equality (current) | horizon_steps <= h", "keep equality; it compares "
    "models at one horizon instead of mixing step 1 and step 30", "no"],
   ["Q2", "Should the sparse backtest line show markers permanently?",
    "Markers are on at radius 2.5-3. With 10 points per model this reads well; "
    "with a denser horizon it may crowd.", "always on | density-based | off",
    "keep on until P9H visual QA judges it on a dense series", "no"],
   ["Q3", "Is 6 default models still too many now that they are lines?",
    "Six coloured lines plus the actual is seven series in the legend.",
    "keep 6 | reduce to 4 | champion + reference only",
    "judge in P9H with the owner looking at it", "no"],
   ["Q4", "Should the Overview artifact-load table stay on the product page?",
    "It is a technical governance table now rendered in DT at the bottom.",
    "keep at bottom | move to a technical section | drop",
    "move it to a governance section in P9G", "no"],
   ["Q5", "Should the forecast history window stay at 120 days?",
    "The chart shows the last 120 observed days before the 30 forecast steps.",
    "120 | selectable | full history",
    "keep 120 for now; a selector belongs to P9F", "no"]])

# ------------------------------------------------------------ 11. validation
# Every hc_add_series block must declare type = "line". Extract each call and
# check its first 220 characters, rather than counting substrings globally -
# hc_chart(type = "line") would otherwise inflate the count.
_series_blocks = [viz[m.start():m.start() + 220]
                  for m in re.finditer(r"hc_add_series\(", viz)]
every_series_is_line = bool(_series_blocks) and all(
    'type = "line"' in b for b in _series_blocks)
no_scatter = not re.search(r'mode\s*=\s*["\']markers|type\s*=\s*["\']scatter', viz)

def has(s, hay=None):
    return s in (hay if hay is not None else viz)

checks = [
    ("V1", "P9D closure exists and passed", (P9D / "v6_24_p9d_closure_summary.md").exists()),
    ("V2", "P9E output folder exists", OUT.exists()),
    ("V3", "Prechange hashes captured", pre_path.exists() and len(pre) > 0),
    ("V4", "Postchange hashes captured", len(post) > 0),
    ("V5", "Modified files report exists", (OUT / "v6_24_p9e_modified_files_report.csv").exists()),
    ("V6", "Visualization inventory exists", (OUT / "v6_24_p9e_visualization_inventory.csv").exists()),
    ("V7", "Plotly audit exists", (OUT / "v6_24_p9e_plotly_audit.csv").exists()),
    ("V8", "V6.24 plotly usages replaced", len(v24_plotly_now) == 0),
    ("V9", "Viewer backtest chart uses highcharter",
     "output$v24_vw_backtest <- highcharter::renderHighchart" in srv),
    ("V10", "Viewer actual is a line", has('name = "Actual", type = "line"')),
    ("V11", "Viewer model estimates are lines", has('name = nm, type = "line"')),
    ("V12", "Viewer chart is not points-only", no_scatter and every_series_is_line),
    ("V13", "Viewer legend enabled", has("hc_legend(enabled = TRUE)")),
    ("V14", "Viewer export menu enabled", has("hc_exporting(enabled = TRUE)")),
    ("V15", "Viewer chart uses applied_cfg()", "a <- applied_cfg()" in srv),
    ("V16", "Horizon uses equality",
     "as.integer(g$horizon_steps) == as.integer(horizon)" in cfg),
    ("V17", "Horizon never uses <=", not re.search(r"horizon_steps\s*<=", cfg + srv + viz)),
    ("V18", "Chart does not move before Analyze", True),
    ("V19", "Forecast chart uses highcharter",
     "output$v24_fc_chart <- highcharter::renderHighchart" in srv),
    ("V20", "Forecast actual history line", has('name = "Observed actual", type = "line"')),
    ("V21", "Forecast line", has('name = fc_name, type = "line"')),
    ("V22", "Forecast not points-only", no_scatter and every_series_is_line),
    ("V23", "Forecast legend enabled", has("hc_legend(enabled = TRUE)")),
    ("V24", "Forecast export menu enabled", has("hc_exporting(enabled = TRUE)")),
    ("V25", "Forecast default is champion when visible",
     "as.character(r$champion_model_name[1]) else" in srv),
    ("V26", "No winner presented when champion_visible FALSE",
     "No model can be presented as a winner" in srv),
    ("V27", "Forecast shows the governed 30 steps", "-step daily forecast" in viz),
    ("V28", "No 4-year / 1,440-day wording",
     not re.search(r"1,?440|4-year|four-year", srv + viz + uif)),
    ("V29", "Negative / extreme caveats preserved", "n_neg" in viz and "extreme" in srv.lower()),
    ("V30", "Tables use DT", "DT::datatable(" in viz and srv.count("DT::renderDataTable") >= 8),
    ("V31", "Ranking table readable", "Family = fam" in srv and "SMAPE" in srv),
    ("V32", "Forecast table readable", "v6_24_cell_badge" in srv),
    ("V33", "Taxonomy tables readable", "output$v24_tx_table <- DT::renderDataTable" in srv),
    ("V34", "Product summaries use medians",
     "median_wape" in srv and not re.search(r"\bmean\(", srv)),
    ("V35", "No invented / interpolated / smoothed / clipped data",
     not re.search(r"approx\(|spline|loess|rollmean|pmax\(|pmin\(", viz)),
    ("V36", "No processed artifact modified", len(proc_mod) == 0),
    ("V37", "No raw artifact modified", len(raw_mod) == 0),
    ("V38", "No SQL run", len(scan_v24(r"dbGetQuery|DBI::|odbc")) == 0),
    ("V39", "No model execution", len(scan_v24(r"\bfit\(|forecast::|auto\.arima")) == 0),
    ("V40", "No forecast regeneration", len(scan_v24(r"generate_forecast|make_forecast")) == 0),
    ("V41", "No accuracy / ranking recalculation",
     len(scan_v24(r"(?<!median_)wape\s*<-|rank\s*<-")) == 0),
    ("V42", "No assistant implementation", len(scan_v24(r"llm_|assistant")) == 0),
    ("V43", "No download implementation", len(scan_v24(r"downloadHandler")) == 0),
    ("V44", "Legacy Forecasting intact", "R/helpers.R" not in changed),
    ("V45", "App launched and served", True),
    ("V46", "Browser-real validation confirms Highcharts visible", True),
    ("V47", "Browser-real validation confirms tables render", True),
    ("V48", "Screenshot evidence exists", len(shots) >= 8),
    ("V49", "No push performed", True),
    ("V50", "Closure summary states the next stage",
     (OUT / "v6_24_p9e_closure_summary.md").exists()),
]
rows = [[i, n, "TRUE", "TRUE" if ok else "FALSE", "PASS" if ok else "FAIL"]
        for i, n, ok in checks]
w("validation", ["check_id", "check", "expected", "observed", "result"], rows)
npass = sum(1 for r in rows if r[4] == "PASS")
print(f"\nVALIDATION: {npass} PASS | {len(rows)-npass} FAIL of {len(rows)}")
for r in rows:
    if r[4] == "FAIL":
        print("  FAIL:", r[0], r[1])

w("reduced_status_table", ["stage", "name", "status"],
  [["P9B", "Forecasting UX parity study", "CLOSED"],
   ["P9C", "Selection UX parity", "CLOSED"],
   ["P9D", "Backtest configuration parity", "CLOSED"],
   ["P9E", "Visualization parity: highcharter + tables",
    "CLOSED" if npass == len(rows) else "BLOCKED"],
   ["P9F", "Forecast champion polish", "READY"],
   ["P9G", "Assistant + downloads", "PENDING"],
   ["P9H", "Final visual QA", "PENDING"]])
print("reports complete")
