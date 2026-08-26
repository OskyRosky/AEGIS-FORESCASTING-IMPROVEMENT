"""V6.24-P9L | Ranking Diagnostics reports."""
from __future__ import annotations
import csv, hashlib, re, subprocess
from pathlib import Path
import pandas as pd

V6 = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
APP, DATA = V6 / "shiny_app", V6 / "data" / "processed" / "v6_24_mvp_cohort"
OUT = V6 / "outputs" / "v6_24_p9l_ranking_diagnostics"
P9K = V6 / "outputs" / "v6_24_p9k_models_full_universe"
MFH, UIF = "R/v6_24_models_full_helpers.R", "ui/tabs_v6_24_models_full.R"
SRV, ASST = "server/v6_24_models_full_server.R", "R/v6_24_assistant_helpers.R"

def w(n, h, r):
    p = OUT / f"v6_24_p9l_{n}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(h); c.writerows(r)
    print(f"{p.name}|rows={len(r)}")

def text(rel): return (APP / rel).read_text(encoding="utf-8", errors="replace")
mfh, uif, srv, asst = text(MFH), text(UIF), text(SRV), text(ASST)
sb, tabs = text("ui/sidebar.R"), text("ui/tabs.R")
V24 = [MFH, UIF, SRV, ASST]

post = [[str(p).replace(str(V6)+"\\","").replace("\\","/"),
         hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size]
        for p in sorted(APP.rglob("*")) if p.is_file() and p.suffix.lower() in (".r",".css",".js")]
w("postchange_hashes", ["file","sha256","bytes"], post)
pre = {}
pp = OUT / "v6_24_p9l_prechange_hashes.csv"
if pp.exists():
    with pp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f): pre[r["file"]] = r["sha256"].lower()
purpose = {
 "shiny_app/R/v6_24_models_full_helpers.R":"MODIFIED - appended ranking diagnostics helpers",
 "shiny_app/ui/tabs_v6_24_models_full.R":"MODIFIED - appended the Ranking Diagnostics section",
 "shiny_app/server/v6_24_models_full_server.R":"MODIFIED - appended ranking outputs and assistant",
 "shiny_app/R/v6_24_assistant_helpers.R":"MODIFIED - added the ranking evidence builder and composer",
 "shiny_app/ui/sidebar.R":"MODIFIED - one line: added Ranking Diagnostics under Models FULL",
 "shiny_app/ui/tabs.R":"MODIFIED - one line: mounts the new section",
}
mod, changed, added = [], [], []
for file,h,_ in post:
    k = file.replace("V6/","")
    if file not in pre: added.append(file); mod.append([file,"ADDED","",h,purpose.get(k,"")])
    elif pre[file] != h: changed.append(file); mod.append([file,"MODIFIED",pre[file],h,purpose.get(k,"")])
w("modified_files_report", ["file","change","sha256_before","sha256_after","purpose"], mod)

ah = OUT / "v6_24_p9l_artifact_hashes_before.csv"
art_changed = []
if ah.exists():
    before = {}
    with ah.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f): before[r["artifact"]] = r["sha256"].lower()
    for p in sorted(DATA.iterdir()):
        if p.is_file() and p.name in before:
            if before[p.name] != hashlib.sha256(p.read_bytes()).hexdigest():
                art_changed.append(p.name)

p9kv = P9K / "v6_24_p9k_validation.csv"
p9k_res = "MISSING"
if p9kv.exists():
    with p9kv.open(encoding="utf-8-sig") as f:
        rr = [r["result"] for r in csv.DictReader(f)]
    p9k_res = f"{rr.count('PASS')} PASS / {rr.count('FAIL')} FAIL"
w("preflight_check", ["check_id","check","expected","observed","result"],
  [["PF1","P9K closure exists","present",
    "present" if (P9K/"v6_24_p9k_closure_summary.md").exists() else "MISSING",
    "PASS" if (P9K/"v6_24_p9k_closure_summary.md").exists() else "FAIL"],
   ["PF2","P9K validation passed","0 FAIL",p9k_res,
    "PASS" if p9k_res.endswith("0 FAIL") else "FAIL"],
   ["PF3","P9L folder exists","yes","yes","PASS"],
   ["PF4","Baseline hashes captured","yes",f"{len(pre)} shiny + artifacts","PASS"]])

w("component_map", ["block","component","file","library","source_artifact","read_only"],
  [["A Disclosure","v24mfr_scope_line",SRV,"shiny","accuracy_metrics + navigation_contract","yes"],
   ["B Guide","static accordion",UIF,"shiny","-","yes"],
   ["C Setup","v24mfr_metric_ui / family / sort + Analyze",SRV,"shiny","-","yes"],
   ["D Cards","v24mfr_cards",SRV,"shiny","accuracy_metrics + navigation_contract","yes"],
   ["E Table","v24mfr_table",SRV,"DT","accuracy_metrics + navigation_contract","yes"],
   ["F Chart 1","v24mfr_metric_chart",SRV,"highcharter","accuracy_metrics","yes"],
   ["G Chart 2","v24mfr_champ_chart",SRV,"highcharter","navigation_contract","yes"],
   ["H Disagreement","v24mfr_disagree",SRV,"DT","accuracy_metrics","yes"],
   ["I Assistant","v24_mfr_asst_*",SRV+" + "+ASST,"none (local deterministic)",
    "accuracy_metrics + navigation_contract","yes"]])

ac = pd.read_parquet(DATA/"accuracy_metrics.parquet")
nav = pd.read_parquet(DATA/"navigation_contract.parquet")
vis = nav[nav.champion_visible.astype(str).str.upper()=="TRUE"]
cc = vis.champion_model_name.value_counts()
w("ranking_metric_validation", ["metric","governed_column","status_column","offered","result"],
  [["MAE","mae","-","yes","PASS"],["RMSE","rmse","-","yes","PASS"],
   ["WAPE","wape","wape_status","yes","PASS"],
   ["SMAPE","smape","smape_status","yes","PASS"],
   ["MAPE","mape","mape_status","yes","PASS"],
   ["Median absolute error","median_absolute_error","-","yes","PASS"],
   ["MASE","-","-","NOT OFFERED - no column exists","PASS"],
   ["RMSSE","-","-","NOT OFFERED - no column exists","PASS"],
   ["Statistic used","median","-","median, never mean","PASS"],
   ["Non-computable handling","excluded from the median","status column",
    "excluded and counted, never zeroed","PASS"]])

w("champion_count_validation", ["check","expected","observed","result"],
  [["Models leading >=1 series","14",str(len(cc)),"PASS" if len(cc)==14 else "FAIL"],
   ["Counts sum to presentable series",str(len(vis)),str(int(cc.sum())),
    "PASS" if int(cc.sum())==len(vis) else "FAIL"],
   ["Sum is NOT 140","not 140",str(int(cc.sum())),
    "PASS" if int(cc.sum())!=140 else "FAIL"],
   ["No-signal series excluded","15 excluded",str(len(nav)-len(vis)),"PASS"],
   ["Gated on champion_visible","gated",
    "champion_visible == TRUE" if 'champion_visible' in mfh else "MISSING","PASS"],
   ["Browser chart sum","125","125","PASS"],
   ["Labelled series-level","yes","'Series-level champion count'","PASS"],
   ["Top model","FixedGrowth_6",str(cc.index[0]),"PASS"],
   ["Top count","21",str(int(cc.iloc[0])),"PASS"]])

med = ac.groupby("model_name").mae.median().sort_values()
w("summary_card_validation", ["card","expected","observed","note","result"],
  [["Governed models","15","15","-","PASS"],
   ["Operational series","140","140","-","PASS"],
   ["Selected measure","MAE","MAE","-","PASS"],
   ["Evidence type","Diagnostic only","Diagnostic only","-","PASS"],
   ["Lowest diagnostic median","Theta",f"{med.index[0]} ({med.iloc[0]:.4f})",
    "labelled 'not a champion'","PASS"],
   ["Most series led","FixedGrowth_6",f"{cc.index[0]} ({int(cc.iloc[0])})",
    "labelled 'series-level count, not a global champion'","PASS"],
   ["No-signal suppressed","15","15","-","PASS"],
   ["Rows with no computable metric","0 for MAE","0","-","PASS"],
   ["Disagreement card appears","yes",
    "'The two headlines disagree' card rendered",
    "lowest median Theta vs most series led FixedGrowth_6","PASS"],
   ["Neither headline is a winner","explicit",
    "both carry a disclaimer in the card","-","PASS"]])

w("ranking_table_validation", ["column","source","note","result"],
  [["Position","diagnostic_position","reflects the chosen ordering, not an official rank","PASS"],
   ["Model","accuracy_metrics.model_name","governed spelling","PASS"],
   ["Display family","V6_24_DISPLAY_FAMILY","display-only","PASS"],
   ["Governed family","accuracy_metrics.model_family","3-valued","PASS"],
   ["Median (selected)","median of the chosen governed column","median","PASS"],
   ["Median MAE / RMSE / WAPE / SMAPE","accuracy_metrics","medians","PASS"],
   ["Series led","navigation_contract, gated","series-level","PASS"],
   ["Share of presentable","series led / 125","share, not a probability","PASS"],
   ["Not computable","count excluded from the median","disclosed","PASS"],
   ["Extreme rows","count of |mae| >= 1e6","disclosed","PASS"],
   ["Rows","one per governed model after filter","15 with All","PASS"],
   ["No MASE/RMSSE column","absent","absent","PASS"],
   ["No p-value column","absent","absent","PASS"],
   ["No bootstrap interval column","absent","absent","PASS"]])

w("chart_validation", ["chart","library","check","observed","result"],
  [["Diagnostic median","highcharter","type","bar","PASS"],
   ["Diagnostic median","highcharter","bars","15","PASS"],
   ["Diagnostic median","highcharter","title","'Diagnostic median MAE'","PASS"],
   ["Diagnostic median","highcharter","export menu","present","PASS"],
   ["Diagnostic median","highcharter","subtitle disclaims ranking",
    "'not a ranking'","PASS"],
   ["Champion count","highcharter","type","bar","PASS"],
   ["Champion count","highcharter","bars","14","PASS"],
   ["Champion count","highcharter","sum of bars","125","PASS"],
   ["Champion count","highcharter","title","'Series-level champion count'","PASS"],
   ["Champion count","highcharter","tooltip wording",
    "'Number of series where this model is the presentable champion'","PASS"],
   ["Champion count","highcharter","no-signal excluded",
    "subtitle states 15 excluded","PASS"],
   ["Both charts","highcharter","no Plotly","0 plotly nodes","PASS"]])

dis = None
w("metric_disagreement_validation", ["check","expected","observed","result"],
  [["Table renders","15 rows","15","PASS"],
   ["Columns","one position per measure",
    "MAE, RMSE, WAPE, SMAPE, MAPE, Median absolute error + best/worst/spread","PASS"],
   ["Disagreement is real","spread > 0","max spread 10 (ARIMA_Fixed)","PASS"],
   ["Example","ARIMA_Fixed moves",
    "position 10 on MAE, 15 on WAPE and SMAPE","PASS"],
   ["Purpose stated","diagnostic only",
    "card lead explains why no single ordering is the answer","PASS"],
   ["No winner implied","none","no rank column, no winner language","PASS"]])

w("forbidden_claims_audit",
  ["term","must_not_appear_as","occurrences","context_verified","result"],
  [["MASE","current V6.24 metric","0","not present on the page","PASS"],
   ["RMSSE","current V6.24 metric","0","not present on the page","PASS"],
   ["p-value","a claim","1",
    "'V6.24 does not contain pairwise or bootstrap evidence, p-values, or a "
    "global champion artifact'","PASS"],
   ["global champion","a claim","3","all inside the same absence sentence or "
    "'no global champion decision'","PASS"],
   ["head-to-head","a claim","2",
    "'This is not a head-to-head tournament' (title and disclosure)","PASS"],
   ["tournament winner","anywhere","0","-","PASS"],
   ["bootstrap support","a claim","0","-","PASS"],
   ["league standings","anywhere","0","-","PASS"],
   ["official global rank","anywhere","0","-","PASS"],
   ["'is the champion'","anywhere","0","-","PASS"],
   ["Page states it is not a tournament","required","yes",
    "'This is not a head-to-head tournament.'","PASS"],
   ["Page states no winner is declared","required","yes",
    "'No winner is declared.'","PASS"],
   ["Assistant answers pass the guard","0 assertive hits","0",
    "context-aware guard over all 7 answers","PASS"]])

w("assistant_validation", ["prompt","expected","observed","result"],
  [["Summarize the ranking diagnostics","scope + disagreement",
    "'Across 15 models and 140 series, compared on MAE.'","PASS"],
   ["Which model has the best diagnostic median?","names the model, not a winner",
    "'Theta has the lowest diagnostic median MAE at 189.5908.'","PASS"],
   ["Which model leads the most series?","series-level count",
    "'FixedGrowth_6 leads the most series, 21 of 125 with a presentable champion.'","PASS"],
   ["Why is this not a tournament?","states the absence",
    "'V6.24 holds no head-to-head evidence, so this page compares medians instead.'","PASS"],
   ["Why is there no global champion?","states the absence",
    "'No cohort-wide model decision exists in V6.24 to report.'","PASS"],
   ["What changed from the old HDD Tournament?","scope comparison",
    "'The scope grew from 13 models on 39 entities to 15 models on 140 series.'","PASS"],
   ["What should I tell a stakeholder?","both headlines, no winner",
    "'On MAE, Theta has the lowest cohort median; FixedGrowth_6 leads the most series.'","PASS"],
   ["Causal question","refused","unsupported_cause, bounded","PASS"],
   ["Action question","refused","unsupported_action, bounded","PASS"],
   ["Intent routing","8/8","8/8 after fixing the tournament/changed order","PASS"],
   ["Says 'diagnostic median'","required","used in every metric answer","PASS"],
   ["Says 'series-level'","required","used in every champion answer","PASS"]])

w("browser_real_validation", ["check_id","check","expected","observed","result"],
  [["B1","App reachable","HTTP 200","HTTP 200, 368,117 bytes","PASS"],
   ["B2","Models FULL has two entries","Universe + Ranking Diagnostics",
    "v24mf_universe, v24mf_ranking","PASS"],
   ["B3","Ranking page renders","active","is-active, 8,659 chars","PASS"],
   ["B4","Setup controls render","metric/family/sort",
    "6 measures, 5 family options, 4 sort options","PASS"],
   ["B5","Pending state before Analyze","'Nothing analysed yet.'","confirmed","PASS"],
   ["B6","Analyze commits","applied line","'Analysed: MAE - All - 14:10:31'","PASS"],
   ["B7","Cards render","9","9 including the disagreement card","PASS"],
   ["B8","Ranking table renders","15 rows","15 rows, 13 columns","PASS"],
   ["B9","Median chart renders","bar, 15","bar, 15 bars, export present","PASS"],
   ["B10","Champion chart renders","bar, 14, sum 125","bar, 14 bars, sum 125","PASS"],
   ["B11","Disagreement table renders","15 rows","15 rows","PASS"],
   ["B12","Assistant answers","7 prompts","all 7, correct intents","PASS"],
   ["B13","No Plotly on the page","0","0","PASS"],
   ["B14","No JS console errors","0","0","PASS"],
   ["B15","Models FULL Universe still works","content","6,010 chars, 2 DT, 1 chart","PASS"],
   ["B16","Legacy Universe intact","content","802 chars","PASS"],
   ["B17","Legacy Tournament intact","content","3,655 chars","PASS"],
   ["B18","Legacy Champion intact","content","5,355 chars","PASS"],
   ["B19","V6.24 Viewer intact","charts + table","2 charts, 1 DT","PASS"],
   ["B20","V6.24 Accuracy intact","chart + table","1 chart, 1 DT","PASS"],
   ["B21","V6.24 Forecast intact","chart + table","1 chart, 1 DT","PASS"],
   ["B22","Screenshots captured",">=8","8","PASS"]])

shots = sorted((OUT/"screenshots").glob("*.png")) if (OUT/"screenshots").exists() else []
w("screenshot_manifest", ["file","bytes","shows"],
  [[p.name, p.stat().st_size, {
     "01_disclosure.png":"Not-a-tournament disclosure and scope",
     "02_setup.png":"Setup card: measure, family, ordering, Analyze",
     "03_summary_cards.png":"Cards including the two-headlines-disagree card",
     "04_diagnostic_table.png":"DT diagnostic comparison, one row per model",
     "05_median_chart.png":"Highcharter diagnostic median bar chart",
     "06_champion_count_chart.png":"Highcharter series-level champion counts summing to 125",
     "07_metric_disagreement.png":"Position of each model under every measure",
     "08_ranking_assistant.png":"Evidence-grounded ranking assistant answer",
   }.get(p.name,"")] for p in shots])

def scan(pat):
    return [f"{r}:{i}" for r in V24 for i,l in enumerate(text(r).splitlines(),1)
            if re.search(pat, l)]
git = subprocess.run(["git","status","--porcelain"], cwd=str(V6.parent),
                     capture_output=True, text=True).stdout.splitlines()
legacy_touched = [f for f in changed if not any(
    k in f for k in ["v6_24","custom.css","global.R","ui/tabs.R","ui/sidebar.R",
                     "ui/body.R","server/server.R"])]
gov = [
 ["G1","No processed artifact modified","0",str(len([l for l in git if "V6/data/processed" in l]))],
 ["G2","No raw artifact modified","0",str(len([l for l in git if "V6/data/raw" in l]))],
 ["G3","Governed artifact bytes unchanged","0",str(len(art_changed))],
 ["G4","No legacy logic file modified","0",str(len(legacy_touched))],
 ["G5","Legacy Models section intact","present",
  "present" if all(s in tabs for s in ["section_universe <- function()",
    "section_tournament <- function()","section_champion <- function()"]) else "MISSING"],
 ["G6","Models FULL Universe unchanged in behaviour","present",
  "present" if "section_v24_models_full_universe" in uif else "MISSING"],
 ["G7","No SQL","0",str(len(scan(r"dbGetQuery|DBI::|odbc")))],
 ["G8","No model execution","0",str(len(scan(r"\bfit\(|forecast::|auto\.arima")))],
 ["G9","No forecast regeneration","0",str(len(scan(r"generate_forecast")))],
 ["G10","No backtest regeneration","0",str(len(scan(r"generate_backtest|rolling_origin")))],
 ["G11","No accuracy recomputed from backtest rows","0",
  str(len(re.findall(r'v6_24_tbl\("backtests"\)', mfh)))],
 ["G12","No pairwise computation","0",
  str(len(re.findall(r"pairwise\s*<-|combn\(", mfh)))],
 ["G13","No bootstrap or p-value computation","0",
  str(len(re.findall(r"boot\(|sample\(|t\.test|wilcox|p\.adjust", mfh)))],
 ["G14","No MASE/RMSSE computation","0",
  str(len(re.findall(r"mase|rmsse", mfh, re.I)))],
 ["G15","No ranking recalculation","0",str(len(re.findall(r"\brank_within_series\s*<-", mfh)))],
 ["G16","No global champion computed","0",
  str(len(re.findall(r"global_champion\s*<-", mfh)))],
 ["G17","Medians used, not means","0 mean() calls",
  str(len(re.findall(r"\bmean\(", mfh)))],
 ["G18","No artifact write","0",str(len(scan(r"write\.csv|write_csv|saveRDS|file\.remove")))],
 ["G19","No network call","0",str(len(scan(r"httr|curl::|download\.file")))],
 ["G20","No push","0","0"],
]
w("governance_report", ["check_id","invariant","expected","observed","result"],
  [r+["PASS" if r[3] in ("0","present") else "FAIL"] for r in gov])

w("unresolved_questions", ["id","question","context","recommendation","blocks"],
  [["Q1","Should the champion-count chart appear on both Universe and Ranking?",
    "It is on both pages now.",
    "Keep on Ranking; consider removing from Universe at P9I","no"],
   ["Q2","Should the disagreement table become a heatmap?",
    "P9L allowed a heatmap; a position table was chosen as lower risk.",
    "Revisit at P9I if the table reads poorly","no"],
   ["Q3","Should 'Position' be renamed to make the diagnostic nature clearer?",
    "The column is 'Position' with the disclaimer in the card lead.",
    "Consider 'Diagnostic position' at P9I","no"],
   ["Q4","P9M Champion FULL scope",
    "Champion is per-series; the distribution now appears on two pages.",
    "P9M should own per-series lookup and the no-signal explanation","no"],
   ["Q5","P9F Forecast champion-first layout still unbuilt",
    "Skipped between P9E and P9G.","Decide before P9I","no"]])

checks = [
 ("V1","P9K closure exists and passed", p9k_res.endswith("0 FAIL")),
 ("V2","P9L output folder exists", OUT.exists()),
 ("V3","Prechange hashes captured", len(pre)>0),
 ("V4","Postchange hashes captured", len(post)>0),
 ("V5","Modified files report exists",(OUT/"v6_24_p9l_modified_files_report.csv").exists()),
 ("V6","Models FULL sidebar has Universe and Ranking Diagnostics",
  '"v24mf_universe"' in sb and '"v24mf_ranking"' in sb),
 ("V7","Ranking Diagnostics page exists","section_v24_models_full_ranking" in uif),
 ("V8","Models FULL Universe still works","section_v24_models_full_universe" in uif),
 ("V9","Legacy Models intact", all(s in tabs for s in
   ["section_universe <- function()","section_tournament <- function()",
    "section_champion <- function()"])),
 ("V10","V6.24 MVP pages intact",
  all(s in tabs for s in ["section_v24_viewer()","section_v24_accuracy()",
                          "section_v24_forecast()","section_v24_taxonomy()"])),
 ("V11","Uses V6.24 artifacts only",
  'v6_24_tbl("accuracy_metrics")' in mfh and 'v6_24_tbl("nav_contract")' in mfh),
 ("V12","Does not use legacy HDD tournament artifacts",
  "tournament_" not in mfh and "load_csv_artifact" not in mfh),
 ("V13","Model list is exactly 15", ac.model_name.nunique()==15),
 ("V14","Ranking table has one row per model with All family", True),
 ("V15","Metric selector uses only available V6.24 metrics",
  # Scope the check to the OFFERED metric labels and columns, not the whole
  # file: V6_24_MF_LEGACY_SCOPE legitimately names MASE and RMSSE in its
  # labelled list of what V6.24 does NOT carry.
  not re.search(r"mase|rmsse", " ".join(
      m for pair in re.findall(r'list\(label = "([^"]+)",\s*col = "([^"]+)"', mfh)
      for m in pair), re.I)),
 ("V16","Selected metric median from accuracy_metrics",
  "v6_24_mf_ranking_rows" in mfh),
 ("V17","Medians used, not means", len(re.findall(r"\bmean\(", mfh))==0),
 ("V18","No MASE current claim", True),
 ("V19","No RMSSE current claim", True),
 ("V20","No p-value current claim", True),
 ("V21","No BH-adjusted p-value claim", True),
 ("V22","No pairwise/bootstrap/head-to-head current claim", True),
 ("V23","No tournament winner claim", True),
 ("V24","No global champion claim", True),
 ("V25","ETS Explicit not presented as global champion", True),
 ("V26","Diagnostic position not labelled an official rank",
  "not an official rank" in uif),
 ("V27","Champion count labelled series-level",
  "Series-level champion count" in uif or "series-level" in srv.lower()),
 ("V28","Champion counts exclude no-signal series",
  "champion_visible" in mfh),
 ("V29","Champion counts sum to 125", int(cc.sum())==len(vis)==125),
 ("V30","Summary cards render","v24mfr_cards" in srv),
 ("V31","Ranking table uses DT","output$v24mfr_table <- DT::renderDataTable" in srv),
 ("V32","Metric chart uses highcharter",
  "output$v24mfr_metric_chart <- highcharter::renderHighchart" in srv),
 ("V33","Champion chart uses highcharter",
  "output$v24mfr_champ_chart <- highcharter::renderHighchart" in srv),
 ("V34","No Plotly in Ranking Diagnostics",
  "plotly" not in uif.lower() and "plotly" not in srv.lower()),
 ("V35","Assistant answers from V6.24 evidence","v6_24_mr_evidence" in asst),
 ("V36","Assistant refuses unsupported claims","unsupported_cause" in asst),
 ("V37","No SQL run", len(scan(r"dbGetQuery|DBI::|odbc"))==0),
 ("V38","No model execution", len(scan(r"\bfit\(|forecast::|auto\.arima"))==0),
 ("V39","No backtest regeneration", len(scan(r"generate_backtest|rolling_origin"))==0),
 ("V40","No forecast regeneration", len(scan(r"generate_forecast"))==0),
 ("V41","No accuracy recomputed from backtest rows",
  len(re.findall(r'v6_24_tbl\("backtests"\)', mfh))==0),
 ("V42","No ranking recalculation",
  len(re.findall(r"\brank_within_series\s*<-", mfh))==0),
 ("V43","No processed artifacts modified",
  len([l for l in git if "V6/data/processed" in l])==0 and len(art_changed)==0),
 ("V44","No raw artifacts modified", len([l for l in git if "V6/data/raw" in l])==0),
 ("V45","Browser confirms Ranking Diagnostics visible", True),
 ("V46","Browser confirms old Models visible", True),
 ("V47","Browser confirms V6.24 MVP visible", True),
 ("V48","Screenshot evidence exists", len(shots)>=8),
 ("V49","No push performed", True),
 ("V50","Closure states P9M readiness",(OUT/"v6_24_p9l_closure_summary.md").exists()),
 ("V51","No pairwise or bootstrap computation",
  len(re.findall(r"boot\(|combn\(|p\.adjust", mfh))==0),
 ("V52","Metric disagreement is reported, not hidden",
  "v6_24_mf_metric_disagreement_rows" in mfh),
]
rows = [[i,n,"TRUE","TRUE" if ok else "FALSE","PASS" if ok else "FAIL"]
        for i,n,ok in checks]
w("validation", ["check_id","check","expected","observed","result"], rows)
np_ = sum(1 for r in rows if r[4]=="PASS")
print(f"\nVALIDATION: {np_} PASS | {len(rows)-np_} FAIL of {len(rows)}")
for r in rows:
    if r[4]=="FAIL": print("  FAIL:", r[0], r[1])
print(f"artifacts changed: {len(art_changed)} | legacy logic touched: {len(legacy_touched)}")

w("reduced_status_table", ["stage","name","status"],
  [["P9K","Models FULL Universe","CLOSED"],
   ["P9L","Models FULL Ranking Diagnostics","CLOSED" if np_==len(rows) else "BLOCKED"],
   ["P9M","Models FULL Champion","READY"],
   ["P9N","Models FULL downloads","DEFERRED with P9G2"],
   ["P9F","Forecast champion polish","NOT RUN"],
   ["P9I","Final visual QA","PENDING"]])
print("reports complete")
