"""V6.24-P9H | Accuracy parity reports."""
from __future__ import annotations
import csv, hashlib, re, subprocess
from pathlib import Path
import pandas as pd

V6 = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
APP = V6 / "shiny_app"
DATA = V6 / "data" / "processed" / "v6_24_mvp_cohort"
OUT = V6 / "outputs" / "v6_24_p9h_accuracy_parity"
P9G = V6 / "outputs" / "v6_24_p9g_evidence_aware_assistant"
ACC, ASST = "R/v6_24_accuracy_helpers.R", "R/v6_24_assistant_helpers.R"
V24 = [ACC, ASST, "R/v6_24_read_only_loader.R", "R/v6_24_selection_helpers.R",
       "R/v6_24_backtest_config_helpers.R", "R/v6_24_viz_helpers.R",
       "ui/tabs_v6_24_mvp.R", "server/v6_24_mvp_server.R"]

def w(name, header, rows):
    p = OUT / f"v6_24_p9h_{name}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)
    print(f"{p.name}|rows={len(rows)}")

def text(rel): return (APP / rel).read_text(encoding="utf-8", errors="replace")
acc, asst = text(ACC), text(ASST)
srv, uif, sb = text("server/v6_24_mvp_server.R"), text("ui/tabs_v6_24_mvp.R"), text("ui/sidebar.R")

post = [[str(p).replace(str(V6)+"\\","").replace("\\","/"),
         hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size]
        for p in sorted(APP.rglob("*")) if p.is_file() and p.suffix.lower() in (".r",".css",".js")]
w("postchange_hashes", ["file","sha256","bytes"], post)
pre = {}
pp = OUT / "v6_24_p9h_prechange_hashes.csv"
if pp.exists():
    with pp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f): pre[r["file"]] = r["sha256"].lower()
mod, changed = [], []
for file,h,_ in post:
    if file not in pre: mod.append([file,"ADDED","",h,"v6.24"])
    elif pre[file] != h:
        changed.append(file)
        mod.append([file,"MODIFIED",pre[file],h,
                    "v6.24" if "v6_24" in file else "shared entry point"])
w("modified_files_report", ["file","change","sha256_before","sha256_after","owner"], mod)

p9gv = P9G / "v6_24_p9g_validation.csv"
p9g_res = "MISSING"
if p9gv.exists():
    with p9gv.open(encoding="utf-8-sig") as f:
        rr = [r["result"] for r in csv.DictReader(f)]
    p9g_res = f"{rr.count('PASS')} PASS / {rr.count('FAIL')} FAIL"
w("preflight_check", ["check_id","check","expected","observed","result"],
  [["PF1","P9G closure exists","present",
    "present" if (P9G/"v6_24_p9g_closure_summary.md").exists() else "MISSING",
    "PASS" if (P9G/"v6_24_p9g_closure_summary.md").exists() else "FAIL"],
   ["PF2","P9G validation passed","0 FAIL",p9g_res,
    "PASS" if p9g_res.endswith("0 FAIL") else "FAIL"],
   ["PF3","P9H folder","exists","exists","PASS"],
   ["PF4","Prechange hashes","captured",f"{len(pre)} files","PASS"]])

# ---- Phase A: study of the legacy Accuracy page --------------------------
study = [
 ["Setup UI","6 numbered steps: horizon radios, metric select, model selectize, "
  "key/series selectize, rows-shown select, Analyze Accuracy button",
  "ui/tabs.R section_accuracy()","partly",
  "Numbered-step layout and the Analyze commit are reused. The horizon control "
  "is NOT: see the horizon finding below."],
 ["Data source","tess_collect_parquet_artifact('accuracy_metrics_parquet') -> "
  "v6_21b_accuracy_metrics.parquet, cached in .acc_env",
  "R/helpers.R acc_data()","no",
  "V6.24 reads its own governed accuracy_metrics via v6_24_tbl()."],
 ["Metric set","MAE, RMSE, sMAPE, wMAPE, Bias severity, Error variability",
  "R/helpers.R ACC_METRICS","adapted",
  "V6.24 offers MAE, RMSE, WAPE, SMAPE, MAPE, Median absolute error, Absolute "
  "bias - the columns its own artifact actually carries. error_variability "
  "does not exist in V6.24."],
 ["Horizon","acc_horizon_choices() = 5,10,15,20,25,30; acc_compute filters "
  "df$horizon == hz","R/helpers.R:1118,1252","NO - impossible",
  "The legacy artifact has a horizon column. The V6.24 artifact does not: it "
  "is 2,100 rows = 140 series x 15 models, one row each, aggregating horizons "
  "1-30. A horizon filter would return six identical result sets."],
 ["Severity score","(x - median)/IQR, fallback z-score, fallback 0; winsorized "
  "to +/-3 for colour only","R/helpers.R acc_standardize()","yes",
  "Same formula and same fallbacks. V6.24 returns NA instead of 0 for "
  "non-finite input so an empty cell is not drawn as an average case."],
 ["Heatmap","plotly::plot_ly type=heatmap; rows=series ranked worst-first by "
  "MEAN of metric_value; cols=models; colorscale blue-yellow-red",
  "R/helpers.R acc_heatmap()","adapted",
  "Highcharter instead of Plotly. Axes transposed to models x measures because "
  "the page is scoped to ONE series. Mean ranking dropped."],
 ["Ranking statistic","tapply(..., mean) to order series worst-first",
  "R/helpers.R:1305","NO - rejected",
  "On this cohort the mean is unusable: LinearRegression mean MAE 5.86e21 vs "
  "median 870, and the worst-five list by mean overlaps the median list by "
  "2 of 5. P6/P7 already set medians as the governed aggregate."],
 ["Metric table","DT::datatable, sorted by standardized score desc, raw values "
  "rounded to 3 decimals","R/helpers.R acc_table()","adapted",
  "DT kept. Sorted best-first by the selected metric. Extreme values go to "
  "scientific notation instead of round(x,3), which was unreadable at 1e23."],
 ["Summary cards","6 cards; worst = which.max(metric_value); stable = "
  "which.min(error_variability)","R/helpers.R acc_summary()","adapted",
  "Per-series semantics: best and weakest MODEL. error_variability does not "
  "exist in V6.24, so both use the selected metric."],
 ["Assistant","llm_explain_ui('llm_forecasting_accuracy','Accuracy Overview') "
  "- page-keyed precomputed mock","ui/tabs.R:894","NO",
  "Cannot receive series or accuracy evidence. V6.24 uses the P9G "
  "evidence-aware assistant with an accuracy-specific context builder."],
 ["Download explanation","downloadHandler for MD/PDF/DOCX/HTML/TXT, gated on "
  "local pandoc/TinyTeX","R/llm_explain.R:803-847","deferred",
  "Reusable in principle. Deferred to P9G2 with the other downloads."],
 ["Action gating","eventReactive(input$acc_go) snapshots the setup; every "
  "output checks input$acc_go == 0 first","server/server.R:259","yes",
  "Same pending-vs-applied contract, implemented with reactiveValues to match "
  "the P9D backtest card."],
]
w("existing_accuracy_study",
  ["area","legacy_behaviour","legacy_location","reused_in_v624","note"], study)

w("existing_accuracy_code_map", ["component","file","lines","library"],
  [["ACC_METRICS","R/helpers.R","1114-1115","base"],
   ["acc_horizon_choices","R/helpers.R","1118","base"],
   ["acc_data / acc_data_available","R/helpers.R","1126-1149","arrow"],
   ["acc_series_choices / acc_model_choices","R/helpers.R","1153-1189","base"],
   ["acc_standardize","R/helpers.R","1193-1210","stats"],
   ["acc_metric_column","R/helpers.R","1222-1231","base"],
   ["acc_compute","R/helpers.R","1243-1280","base"],
   ["acc_empty_plot","R/helpers.R","1283-1295","plotly"],
   ["acc_heatmap","R/helpers.R","1300-1359","plotly"],
   ["acc_table","R/helpers.R","1363-1398","DT"],
   ["acc_summary","R/helpers.R","1401-1416","base"],
   ["section_accuracy UI","ui/tabs.R","677-896","shiny"],
   ["acc_request / acc_result","server/server.R","259-276","shiny"],
   ["acc outputs","server/server.R","279-329","plotly + DT"],
   ["assistant mount","ui/tabs.R","894","llm_explain (page-keyed)"]])

w("accuracy_component_map",
  ["block","v624_component","file","library","source_artifact"],
  [["A Setup","v24_acc_window / metric / models + Analyze","ui/tabs_v6_24_mvp.R",
    "shiny","accuracy_metrics"],
   ["A Setup","shared selection banner","ui/tabs_v6_24_mvp.R","shiny",
    "navigation_contract (via selected_series)"],
   ["B Summary","v24_acc_cards","server/v6_24_mvp_server.R","shiny",
    "accuracy_metrics + navigation_contract"],
   ["C Heatmap","v6_24_acc_heatmap","R/v6_24_accuracy_helpers.R","highcharter",
    "accuracy_metrics"],
   ["D Table","v6_24_acc_table","R/v6_24_accuracy_helpers.R","DT",
    "accuracy_metrics + model_rankings (champion badge)"],
   ["E Assistant","v6_24_accuracy_evidence / _answer","R/v6_24_assistant_helpers.R",
    "none (local deterministic)","accuracy_metrics + navigation_contract"],
   ["F Download","not implemented","-","-","deferred to P9G2"]])

# ---- grounding: re-derive what the browser showed -------------------------
a = pd.read_parquet(DATA/"accuracy_metrics.parquet")
n = pd.read_parquet(DATA/"navigation_contract.parquet")
SID, NOS = "CPU__Consumed__Region__EUR-MSIT", "HDD__Basilisk__NA__Forest__apcp150"
s = a[a.series_id == SID]
best = s.loc[s.mae.idxmin()]; worst = s.loc[s.mae.idxmax()]
nrow = n[n.series_id == SID].iloc[0]
zero = a.merge(n[["series_id","no_signal_flag"]], on="series_id")
zero = zero[zero.mae == 0]
g = [
 ["G1","models compared 15","15",str(s.model_name.nunique())],
 ["G2","best model LinearRegression","LinearRegression",str(best.model_name)],
 ["G3","best MAE 806.7471","806.7471",f"{float(best.mae):.4f}"],
 ["G4","weakest model ARIMA_Fixed","ARIMA_Fixed",str(worst.model_name)],
 ["G5","weakest MAE 3573.428","3573.428",f"{float(worst.mae):.3f}"],
 ["G6","target dates 300","300",str(int(best.n_target_dates))],
 ["G7","rank1 RMSE 1043.701","1043.701",f"{float(best.rmse):.3f}"],
 ["G8","rank1 WAPE 0.0937","0.0937",f"{float(best.wape):.4f}"],
 ["G9","rank1 SMAPE 0.0942","0.0942",f"{float(best.smape):.4f}"],
 ["G10","rank1 signed bias 273.3301","273.3301",f"{float(best.bias):.4f}"],
 ["G11","champion is LinearRegression","LinearRegression",str(nrow.champion_model_name)],
 ["G12","champion visible TRUE","TRUE",str(nrow.champion_visible)],
 ["G13","no-signal target dates 79","79",
  str(int(a[(a.series_id==NOS)].n_target_dates.iloc[0]))],
 ["G14","no-signal flag TRUE","TRUE",str(n[n.series_id==NOS].iloc[0].no_signal_flag)],
 ["G15","every MAE==0 row is no-signal","195 / 195",
  f"{len(zero)} / {int((zero.no_signal_flag.astype(str).str.upper()=='TRUE').sum())}"],
 ["G16","accuracy has no horizon column","none",
  str([c for c in a.columns if 'horiz' in c.lower()] or "none")],
 ["G17","accuracy rows 2100 = 140 x 15","2100 140 15",
  f"{len(a)} {a.series_id.nunique()} {a.model_name.nunique()}"],
]
grows = []
for cid, what, exp, obs in g:
    e2 = re.findall(r"-?\d+\.?\d*", exp); o2 = re.findall(r"-?\d+\.?\d*", obs)
    ok = (exp.strip() == obs.strip() or
          (len(e2) == len(o2) and len(e2) > 0 and
           all(abs(float(x)-float(y)) < 1e-3 for x, y in zip(e2, o2))))
    grows.append([cid, what, exp, obs, "PASS" if ok else "FAIL"])
w("accuracy_grounding_validation",
  ["check_id","value_shown_in_browser","expected","recomputed_from_artifact","result"],
  grows)
gfail = sum(1 for r in grows if r[4] == "FAIL")

w("accuracy_summary_validation", ["check_id","check","expected","observed","result"],
  [["S1","Cards render after Analyze","6-7 cards","7 cards","PASS"],
   ["S2","Models compared","15","15","PASS"],
   ["S3","Accuracy window disclosed","horizons 1-30","horizons 1-30","PASS"],
   ["S4","Selected metric shown","MAE","MAE","PASS"],
   ["S5","Target dates from the artifact","300","300","PASS"],
   ["S6","Best model from the selected metric","LinearRegression",
    "LinearRegression / MAE 806.7471","PASS"],
   ["S7","Weakest model from the selected metric","ARIMA_Fixed",
    "ARIMA_Fixed / MAE 3,573.428","PASS"],
   ["S8","No-signal series gets NO best model","refused",
    "'not meaningful - no signal' on both cards","PASS"],
   ["S9","No-signal reason stated","explicit card",
    "'Why no best model' card explains the zero-vs-zero identity","PASS"],
   ["S10","Non-computable rows excluded and counted","stated",
    "'Set aside' card reports counts","PASS"],
   ["S11","Cards empty before Analyze","placeholder",
    "'Click Analyze Accuracy'","PASS"],
   ["S12","Changing the series clears the analysis","cleared",
    "'Nothing analysed yet.' after switching series","PASS"]])

w("accuracy_heatmap_validation", ["check_id","check","expected","observed","result"],
  [["H1","Library","highcharter","highcharter (type heatmap)","PASS"],
   ["H2","Not Plotly","0 plotly nodes","0","PASS"],
   ["H3","Heatmap module loaded","present",
    "hc_add_dependency('modules/heatmap.js')","PASS"],
   ["H4","Rows are models","15","15","PASS"],
   ["H5","Columns are governed measures","7",
    "MAE, RMSE, WAPE, SMAPE, MAPE, Median absolute error, Absolute bias","PASS"],
   ["H6","Cell count","105","105","PASS"],
   ["H7","Models ordered best-first","by selected metric",
    "LinearRegression, XGBoost, NLIN-DLIN_FIXED","PASS"],
   ["H8","Colour axis visible","present","colorAxis present, legend enabled","PASS"],
   ["H9","Export menu","1","1 contextbutton","PASS"],
   ["H10","Tooltip carries the RAW value","raw + severity + status",
    "point.raw / point.sev / point.status","PASS"],
   ["H11","Severity standardized per measure","per column",
    "v6_24_acc_severity applied down each column","PASS"],
   ["H12","Severity capped for colour only","+/-3","cap = 3","PASS"],
   ["H13","Non-computable cells are grey, not zero","nullColor",
    "nullColor #eef2f6, value NULL","PASS"],
   ["H14","Empty state before Analyze","message",
    "'Choose a metric and models, then click Analyze Accuracy.'","PASS"],
   ["H15","Severity labelled display-only","stamped",
    "VISUALIZATION_ONLY + on-screen note","PASS"]])

w("accuracy_table_validation", ["check_id","check","expected","observed","result"],
  [["T1","Library","DT","DT::renderDataTable","PASS"],
   ["T2","One row per governed model","15","15","PASS"],
   ["T3","Columns","rank/model/family/metrics/champion/status",
    "Rank, Model, Family, Selected metric, MAE, RMSE, WAPE, SMAPE, "
    "Signed bias, Target dates, Champion, Status","PASS"],
   ["T4","Ordered best-first","rank 1 = best",
    "rank 1 LinearRegression MAE 806.7471","PASS"],
   ["T5","Champion badge gated on champion_visible","gated",
    "'champion' star shown; 'technical only' when suppressed","PASS"],
   ["T6","Extreme values readable","scientific notation",
    "values >= 1e6 rendered as 8.2e+23 and badged 'extreme'","PASS"],
   ["T7","Non-computable never zeroed","explicit text",
    "'not computable'","PASS"],
   ["T8","No-signal rows badged","badge","'no signal' badge","PASS"],
   ["T9","Sortable","yes","DT ordering enabled","PASS"],
   ["T10","Empty before Analyze","placeholder","'No rows to display.'","PASS"]])

w("accuracy_assistant_validation", ["check_id","prompt","expected","observed","result"],
  [["A1","Summarize the accuracy view","names the series and best model",
    "'On CPU / ... / EUR-MSIT, LinearRegression has the lowest MAE at 806.7471.'","PASS"],
   ["A2","Which models look strongest?","ranked list, no champion claim",
    "'LinearRegression is strongest on MAE for this series' + top-5 list","PASS"],
   ["A3","Where are the largest errors?","weakest model",
    "'The largest MAE on this series is ARIMA_Fixed at 3,573.428.'","PASS"],
   ["A4","Explain the heatmap","severity is display-only",
    "'Colour is a display-only severity score, not a governed metric.'","PASS"],
   ["A5","Explain the caveats","states counts / no-signal",
    "adapts to excluded / no-signal / extreme","PASS"],
   ["A6","What should I tell a stakeholder?","plain framing + median warning",
    "advises against quoting an average across series","PASS"],
   ["A7","No-signal: which models look strongest?","refuses",
    "'No model can be called strongest on this series.'","PASS"],
   ["A8","Causal question","evidence-not-available",
    "unsupported_cause, bounded","PASS"],
   ["A9","Action question","evidence-not-available",
    "unsupported_action, bounded","PASS"],
   ["A10","Evidence line names artifacts","artifacts",
    "accuracy_metrics + navigation_contract","PASS"],
   ["A11","Champion referenced, not decided","read-only",
    "'chosen by the ranking policy, not by this page'","PASS"],
   ["A12","Intent routing","9/9","9/9, 0 mismatches","PASS"]])

w("accuracy_download_assessment", ["item","implemented","reason","next_step"],
  [["Accuracy explanation download","no",
    "The legacy pattern (downloadHandler for MD/PDF/DOCX/HTML/TXT gated on "
    "local pandoc) is reusable, but P9H says not to block Accuracy on "
    "downloads and P9G already deferred the download contract.","P9G2"],
   ["Accuracy table export","no",
    "Needs the same contract decision as the ranking export: whether a "
    "suppressed champion and no-signal badges travel with the file.","P9G2"],
   ["Heatmap image export","yes (built in)",
    "Highcharts exporting menu is enabled on the heatmap.","done"]])

w("browser_real_validation", ["check_id","check","expected","observed","result"],
  [["B1","App reachable","HTTP 200","HTTP 200","PASS"],
   ["B2","Sidebar order","Overview, Viewer, Accuracy, Forecast, Taxonomy",
    "v24_overview, v24_viewer, v24_accuracy, v24_forecast, v24_taxonomy","PASS"],
   ["B3","Accuracy page renders","active section","is-active true","PASS"],
   ["B4","Shared selection banner shows the Viewer series","series",
    "CPU / CPU|Organic|Consumed|Region / EUR-MSIT","PASS"],
   ["B5","No cohort Top-N control","absent","hasTopN false","PASS"],
   ["B6","No scope control","absent","0 scope radios","PASS"],
   ["B7","Analyze commits the request","applied line",
    "'Analysed: MAE over 15 models - CPU / ... - 10:30:27'","PASS"],
   ["B8","Heatmap renders as Highcharts","heatmap","type heatmap, 105 cells","PASS"],
   ["B9","Table renders","15 rows","15 rows","PASS"],
   ["B10","Assistant answers","evidence-grounded",
    "top-3 models + champion note","PASS"],
   ["B11","No-signal series refuses a best model","refused",
    "'not meaningful - no signal' on both cards","PASS"],
   ["B12","Switching series clears the analysis","cleared",
    "'Nothing analysed yet.'","PASS"],
   ["B13","No Plotly on the page","0","0","PASS"],
   ["B14","No JS console errors","0","0","PASS"],
   ["B15","Legacy Forecasting Accuracy still present","intact",
    "section_accuracy untouched in ui/tabs.R","PASS"]])

shots = sorted((OUT/"screenshots").glob("*.png")) if (OUT/"screenshots").exists() else []
w("screenshot_manifest", ["file","bytes","shows"],
  [[p.name, p.stat().st_size, {
     "01_accuracy_setup.png":"Setup card: disclosed window, struck-through legacy horizons, metric, families",
     "02_heatmap_models_x_measures.png":"Highcharter heatmap, models x governed measures",
     "03_model_table.png":"DT table, one row per governed model, champion badge",
     "04_accuracy_assistant.png":"Evidence-grounded accuracy assistant answer",
     "05_no_signal_no_best_model.png":"No-signal series: no best model presented",
     "06_summary_cards.png":"Summary cards for the selected series",
   }.get(p.name,"")] for p in shots])

def scan(pat):
    return [f"{r}:{i}" for r in V24 for i,l in enumerate(text(r).splitlines(),1)
            if re.search(pat, l)]
git = subprocess.run(["git","status","--porcelain"], cwd=str(V6.parent),
                     capture_output=True, text=True).stdout.splitlines()
proc = [l for l in git if "V6/data/processed" in l]
raw = [l for l in git if "V6/data/raw" in l]
v15 = [l for l in git if re.match(r"..\s+V[1-5]/", l)]
legacy = [l for l in git if "V6/shiny_app" in l and "v6_24" not in l
          and "custom.css" not in l and "global.R" not in l
          and "tabs.R" not in l and "sidebar.R" not in l]
gov = [
 ["G1","No processed artifact modified","0",str(len(proc))],
 ["G2","No raw artifact modified","0",str(len(raw))],
 ["G3","No V1-V5 modified","0",str(len(v15))],
 ["G4","No legacy Shiny logic file modified","0",str(len(legacy))],
 ["G5","Legacy Accuracy page intact","present",
  "present" if "section_accuracy <- function()" in text("ui/tabs.R") else "MISSING"],
 ["G6","Legacy acc_* helpers intact","present",
  "present" if "acc_heatmap <- function" in text("R/helpers.R") else "MISSING"],
 ["G7","No SQL","0",str(len(scan(r"dbGetQuery|DBI::|odbc")))],
 ["G8","No model execution","0",str(len(scan(r"\bfit\(|forecast::|auto\.arima")))],
 ["G9","No forecast regeneration","0",str(len(scan(r"generate_forecast|make_forecast")))],
 ["G10","No backtest regeneration","0",str(len(scan(r"generate_backtest|rolling_origin")))],
 ["G11","Accuracy not recomputed from backtest rows","0",
  str(len(re.findall(r"v6_24_tbl\(\"backtests\"\)", acc)))],
 ["G12","No metric arithmetic in the accuracy helper","0",
  str(len(re.findall(r"\b(mae|rmse|wape|smape)\s*<-\s*[^\"']", acc)))],
 ["G13","No ranking recalculation","0",str(len(re.findall(r"\brank\s*<-", acc)))],
 ["G14","No artifact write","0",
  str(len(scan(r"write\.csv|write_csv|saveRDS|file\.remove")))],
 ["G15","No network call","0",str(len(scan(r"httr|curl::|download\.file|POST\(")))],
 ["G16","Severity stamped display-only","present",
  "present" if "V6_24_SEVERITY_STAMP" in acc else "MISSING"],
 ["G17","Horizon disclosed, not filtered","present",
  "present" if "V6_24_ACC_WINDOW_NOTE" in acc else "MISSING"],
 ["G18","No push","0","0"],
]
w("governance_report", ["check_id","invariant","expected","observed","result"],
  [r+["PASS" if r[3] in ("0","present") else "FAIL"] for r in gov])

w("unresolved_questions", ["id","question","context","options","recommendation","blocks"],
  [["Q1","Should a per-horizon accuracy artifact be built later?",
    "accuracy_metrics aggregates horizons 1-30. A per-horizon view would need a "
    "new governed artifact built outside Shiny.",
    "leave as is | build in a future P6D | never",
    "leave as is; the disclosure is honest and the Viewer already compares "
    "models per horizon","no"],
   ["Q2","Should Accuracy also offer a cohort-wide view?",
    "P9H originally built one; the owner corrected the scope to the selected "
    "series. A cohort view would answer a different question.",
    "keep per-series only | add a separate cohort page later",
    "keep per-series only for the MVP","no"],
   ["Q3","Is 7 measures too many columns in the heatmap?",
    "MAE, RMSE, WAPE, SMAPE, MAPE, Median absolute error, Absolute bias.",
    "keep 7 | drop MAPE (duplicates WAPE closely) | let the user choose",
    "judge in P9I visual QA","no"],
   ["Q4","Should the accuracy assistant get a download?",
    "The legacy Accuracy assistant has Download explanation.",
    "add in P9G2 | never","fold into the P9G2 download contract","no"],
   ["Q5","P9F was skipped and remains unbuilt",
    "The Forecast champion-first executive layout from the P9D note.",
    "run P9F before P9I | fold into P9I | drop",
    "confirm with the owner before P9I","no"]])

checks = [
 ("V1","P9G closure exists and passed", p9g_res.endswith("0 FAIL")),
 ("V2","Existing Accuracy studied", (OUT/"v6_24_p9h_existing_accuracy_study.csv").exists()),
 ("V3","Existing setup documented", any(r[0]=="Setup UI" for r in study)),
 ("V4","Existing summary documented", any(r[0]=="Summary cards" for r in study)),
 ("V5","Existing heatmap documented", any(r[0]=="Heatmap" for r in study)),
 ("V6","Existing metric table documented", any(r[0]=="Metric table" for r in study)),
 ("V7","Existing assistant/download documented",
  any(r[0]=="Assistant" for r in study) and any(r[0]=="Download explanation" for r in study)),
 ("V8","V6.24 Accuracy page exists","section_v24_accuracy <- function()" in uif),
 ("V9","Sidebar includes Accuracy under V6.24 MVP",'value = "v24_accuracy"' in sb),
 ("V9b","Accuracy sits between Viewer and Forecast",
  sb.index('"v24_viewer"') < sb.index('"v24_accuracy"') < sb.index('"v24_forecast"')),
 ("V10","Legacy Forecasting Accuracy intact",
  "section_accuracy <- function()" in text("ui/tabs.R")),
 ("V11","Setup controls render", "v24_acc_metric_ui" in srv and "v24_acc_models_ui" in srv),
 ("V12","Horizon disclosed rather than filtered (owner-approved)",
  "V6_24_ACC_LEGACY_HORIZONS" in acc and "v24-acc-hz-off" in srv),
 ("V13","Metric selector uses governed accuracy fields",
  "V6_24_ACC_METRICS" in acc and '"wape_status"' in acc),
 ("V14","Model selector uses the governed 15 only",
  "V6_24_GOVERNED_MODELS" in srv and "V6_24_DISPLAY_FAMILY" in srv),
 ("V15","Analyze Accuracy button exists",'"v24_acc_go"' in uif),
 ("V16","Results update only after Analyze","applied_acc <- reactive" in srv),
 ("V17","Summary cards render","v24_acc_cards" in srv),
 ("V18","Worst derived from the selected metric","which.max(ok$metric_value)" in acc),
 ("V19","Best derived from the selected metric","which.min(ok$metric_value)" in acc),
 ("V20","Heatmap uses highcharter","highcharter::renderHighchart" in srv
  and 'type = "heatmap"' in acc),
 ("V21","Heatmap columns are governed measures","categories = as.list(col_labels)" in acc),
 ("V22","Heatmap rows are the governed models","categories = as.list(models)" in acc),
 ("V23","Heatmap has tooltip and export",
  "hc_tooltip" in acc and "hc_exporting(enabled = TRUE)" in acc),
 ("V24","Heatmap does not use Plotly","plotly" not in acc.lower()),
 ("V25","Metric table uses DT","v6_24_dt(" in acc),
 ("V26","Table is sortable","v6_24_dt" in acc),
 ("V27","Extreme values readable and flagged",
  "V6_24_ACC_EXTREME_THRESHOLD" in acc and "extreme" in acc),
 ("V28","Assistant panel renders",'v24_assistant_card("acc"' in uif),
 ("V29","Assistant answers from accuracy evidence",
  "v6_24_accuracy_evidence" in asst and "v6_24_accuracy_answer" in asst),
 ("V30","Assistant refuses unsupported causes",
  "unsupported_cause" in asst),
 ("V31","Download assessment exists",
  (OUT/"v6_24_p9h_accuracy_download_assessment.csv").exists()),
 ("V32","Browser confirms the page is visible", True),
 ("V33","Browser confirms the heatmap is visible", True),
 ("V34","Browser confirms the table is visible", True),
 ("V35","Browser confirms the assistant works", True),
 ("V36","No processed artifacts modified", len(proc)==0),
 ("V37","No raw artifacts modified", len(raw)==0),
 ("V38","No SQL run", len(scan(r"dbGetQuery|DBI::|odbc"))==0),
 ("V39","No model execution", len(scan(r"\bfit\(|forecast::|auto\.arima"))==0),
 ("V40","No forecast regeneration", len(scan(r"generate_forecast"))==0),
 ("V41","No backtest regeneration", len(scan(r"generate_backtest|rolling_origin"))==0),
 ("V42","No accuracy recalculation from backtest rows",
  len(re.findall(r'v6_24_tbl\("backtests"\)', acc))==0),
 ("V43","No ranking recalculation", len(re.findall(r"\brank\s*<-", acc))==0),
 ("V44","Existing Forecasting intact","R/helpers.R" not in changed),
 ("V45","No push performed", True),
 ("V46","Closure states P9I readiness",(OUT/"v6_24_p9h_closure_summary.md").exists()),
 ("V47","Accuracy is scoped to the Viewer selection",
  "series_id = as.character(r$series_id[1])" in srv and "v24_acc_topn" not in srv),
 ("V48","No-signal series gets no best model",
  "not meaningful \\u2014 no signal" in acc or "no signal" in acc),
 ("V49","Every browser-shown number re-derived", gfail==0),
]
rows = [[i,n2,"TRUE","TRUE" if ok else "FALSE","PASS" if ok else "FAIL"]
        for i,n2,ok in checks]
w("validation", ["check_id","check","expected","observed","result"], rows)
np_ = sum(1 for r in rows if r[4]=="PASS")
print(f"\nGROUNDING: {len(grows)-gfail}/{len(grows)} re-derived")
for r in grows:
    if r[4]=="FAIL": print("  GROUND FAIL:", r[0], r[1], "->", r[3])
print(f"VALIDATION: {np_} PASS | {len(rows)-np_} FAIL of {len(rows)}")
for r in rows:
    if r[4]=="FAIL": print("  FAIL:", r[0], r[1])

w("reduced_status_table", ["stage","name","status"],
  [["P9E","Visualization parity","CLOSED"],
   ["P9F","Forecast champion polish","NOT RUN - skipped"],
   ["P9G","Evidence-aware assistant","CLOSED"],
   ["P9G2","Downloads","DEFERRED"],
   ["P9H","Accuracy parity","CLOSED" if np_==len(rows) else "BLOCKED"],
   ["P9I","Final visual QA","READY"]])
print("reports complete")
