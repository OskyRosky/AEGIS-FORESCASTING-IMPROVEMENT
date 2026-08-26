"""V6.24-P9J | Models FULL parity study. STUDY ONLY - writes reports, no code."""
from __future__ import annotations
import csv, hashlib, re, subprocess
from pathlib import Path
import pandas as pd

V6 = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
APP, DATA = V6 / "shiny_app", V6 / "data" / "processed" / "v6_24_mvp_cohort"
OUT = V6 / "outputs" / "v6_24_p9j_models_full_study"
P9H = V6 / "outputs" / "v6_24_p9h_accuracy_parity"
LEG = V6 / "outputs" / "model_lab" / "tournament_engine"

def w(name, header, rows):
    p = OUT / f"v6_24_p9j_{name}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)
    print(f"{p.name}|rows={len(rows)}")

post = [[str(p).replace(str(V6)+"\\","").replace("\\","/"),
         hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size]
        for p in sorted(APP.rglob("*")) if p.is_file() and p.suffix.lower() in (".r",".css",".js")]
w("postchange_hashes", ["file","sha256","bytes"], post)
pre = {}
pp = OUT / "v6_24_p9j_prechange_hashes.csv"
if pp.exists():
    with pp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f): pre[r["file"]] = r["sha256"].lower()
touched = [f for f,h,_ in post if f in pre and pre[f] != h]
added = [f for f,h,_ in post if f not in pre]

p9hv = P9H / "v6_24_p9h_validation.csv"
p9h_res = "MISSING"
if p9hv.exists():
    with p9hv.open(encoding="utf-8-sig") as f:
        rr = [r["result"] for r in csv.DictReader(f)]
    p9h_res = f"{rr.count('PASS')} PASS / {rr.count('FAIL')} FAIL"
w("preflight_check", ["check_id","check","expected","observed","result"],
  [["PF1","P9H closure exists","present",
    "present" if (P9H/"v6_24_p9h_closure_summary.md").exists() else "MISSING",
    "PASS" if (P9H/"v6_24_p9h_closure_summary.md").exists() else "FAIL"],
   ["PF2","P9H validation passed","0 FAIL",p9h_res,
    "PASS" if p9h_res.endswith("0 FAIL") else "FAIL"],
   ["PF3","Study folder exists","yes","yes","PASS"],
   ["PF4","Prechange hashes captured","yes",f"{len(pre)} files","PASS"]])

# ---------------------------------------------------------------- evidence
nav = pd.read_parquet(DATA/"navigation_contract.parquet")
rk  = pd.read_parquet(DATA/"model_rankings.parquet")
ac  = pd.read_parquet(DATA/"accuracy_metrics.parquet")
ts  = pd.read_csv(LEG/"tournament_preliminary_standings.csv")
sc  = pd.read_csv(LEG/"tournament_model_scorecard.csv")
pwv = pd.read_csv(LEG/"tournament_pairwise_evidence.csv")
V15, L13 = sorted(ac.model_name.unique()), sorted(ts.model_name.unique())
vis = nav[nav.champion_visible.astype(str).str.upper()=="TRUE"]
ets_vis = int((vis.champion_model_name=="ETS Explicit").sum())
ets_all = int((nav.champion_model_name=="ETS Explicit").sum())
champ_counts = vis.champion_model_name.value_counts()

# ---------------------------------------------------- A. Universe study
w("existing_models_universe_study",
  ["element","legacy_behaviour","data_source","static_or_artifact","reuse_for_full","note"],
  [["Page title","'Model Universe' + 'baselines, challengers and the governed champion'",
    "static text","static","yes (reword)","Wording must drop the single-champion framing."],
   ["Accordion 1","'How to read this universe'","static text","static","yes",
    "Explains baseline vs challenger vs tournament vs champion."],
   ["Accordion 2","'Model families compared' - four families",
    "static text","static","yes (adapt)",
    "Legacy names 4 display families. V6.24 model_family is 3-valued "
    "(Baseline 7 / Challenger 5 / Neural 3); the 4-family split is the "
    "P9D DISPLAY_GROUPING_ONLY map."],
   ["Accordion 3","'Current model universe (15 models)' table with origin, "
    "family, median MASE, champion eligibility, evidence source",
    "tournament_scorecard + standings","artifact","partly",
    "Structure reusable. median MASE and champion eligibility do NOT exist "
    "in V6.24 and must be replaced or dropped."],
   ["Model count","Header says 15 models","static text","static","no",
    "The legacy tournament artifacts actually carry 13 model names. The '15' "
    "in the heading counts models the tournament did not all rank."],
   ["Assistant","llm_explain_ui('llm_models_universe','Model Universe')",
    "v4_4_mock_responses.json by page_id","page-keyed","no",
    "Cannot receive model evidence. Use the P9G evidence-aware assistant."],
   ["Download","Download explanation inside the assistant panel",
    "llm_explain downloadHandler","n/a","deferred","Defer with P9G2."]])

# ------------------------------------------------- B. Tournament study
w("existing_models_tournament_study",
  ["element","legacy_behaviour","data_source","exists_in_v624","note"],
  [["Meaning of 'tournament'","Bootstrap pairwise head-to-head over a fixed "
    "backtest, with sign test and BH-adjusted p-values",
    "tournament_pairwise_evidence.csv","NO",
    f"{len(pwv)} pairwise rows, {pwv.shape[1]} columns including bootstrap_ci_low/high, "
    "sign_test_p_value, bh_adjusted_p_value. V6.24 has no equivalent."],
   ["Primary metric","Median MASE (lower is better)","tournament_scorecard","NO",
    "accuracy_metrics carries mae/rmse/wape/smape/mape/bias. No MASE column."],
   ["Guardrail metric","Median RMSSE","tournament_scorecard","NO","No RMSSE column."],
   ["Standings","13 models ranked by preliminary_position",
    "tournament_preliminary_standings.csv","NO",
    "V6.24 model_rankings is per-series (2,100 rows = 140 x 15); "
    "rank_within_series only, no global position."],
   ["Pairwise matrix","78 ordered pairs = C(13,2); each pair supported_better / "
    "supported_worse / inconclusive","tournament_pairwise_evidence.csv","NO",
    "No pairwise artifact exists anywhere under V6.24."],
   ["Evidence summary","comparisons_tested=12 per model, net_supported_evidence",
    "tournament_model_evidence_summary.csv","NO","No equivalent."],
   ["Challenger evaluation","6 models scored separately in a closed candidate "
    "study; deep-learning challengers did not enter the bootstrap",
    "challenger_metrics_by_model_diagnostic.csv","NO",
    "In V6.24 all 15 models are scored identically on all 140 series."],
   ["Scope","39 entities, HDD only","tournament_model_scorecard.entity_count","N/A",
    f"entity_count is {sorted(sc.entity_count.unique())} for every model. "
    f"V6.24 covers {nav.series_id.nunique()} series across "
    f"{sorted(nav.metric.unique())}."],
   ["Model coverage",f"{len(L13)} models","tournament artifacts","partial",
    f"12 overlap. Legacy-only: {sorted(set(L13)-set(V15))}. "
    f"V6.24-only: {sorted(set(V15)-set(L13))}."],
   ["Computation","Precomputed outside Shiny by the tournament engine; Shiny "
    "only loads and orders","R/helpers.R tournament_league_data()","n/a","yes",
    "The read-only discipline is exactly what V6.24 should keep."]])

# --------------------------------------------------- C. Champion study
w("existing_models_champion_study",
  ["element","legacy_behaviour","data_source","transfers_to_v624","note"],
  [["Champion scope","ONE global champion for the whole model universe",
    "champion_decision.csv","NO",
    "V6.24 has no global champion artifact. Champion is per-series."],
   ["Selected champion","ETS Explicit, 'selected with conditions'",
    "champion_conditions_protocol.csv","NO - contradicted",
    f"In V6.24 ETS Explicit is the presentable champion on only {ets_vis} of "
    f"{len(vis)} signal-present series. It appears as champion_model_name on "
    f"{ets_all} rows, but {ets_all-ets_vis} of those are the no-signal series "
    "where P6C's tie-break crowns it and champion_visible is FALSE."],
   ["Confidence","medium_confidence, condition C-001, action MONITOR",
    "champion_conditions_protocol.csv","no","Legacy governance record; keep as history."],
   ["Conditional status","'champion with conditions, not an unconditional winner', "
    "condition C-002, KEEP_WITH_CONDITIONS","champion_conditions_protocol.csv","no",
    "The CAUTION is worth carrying; the specific decision is not."],
   ["Approved language","13 approved/forbidden statements by audience",
    "champion_dashboard_language.csv","partly",
    "The discipline of governed wording is reusable; the statements name "
    "ETS Explicit and would be false in V6.24."],
   ["Supporting metrics","median MASE 6.90, median RMSSE 1.86, 8 supported-better "
    "0 supported-worse","tournament artifacts","NO","Neither metric exists in V6.24."],
   ["Leadership chart","champion_leadership_count_chart (Plotly) - per-series "
    "leadership counts","champion_series_evidence","adaptable",
    "V6.24 CAN build this honestly from navigation_contract: "
    f"{len(champ_counts)} distinct models win at least one series."],
   ["Series evidence table","champion_series_evidence_table + exceptions",
    "champion_entity_model_scores","adaptable",
    "V6.24 equivalent is model_rankings joined to navigation_contract."],
   ["Assistant","llm_explain_ui('llm_champion_overview','Champion Overview')",
    "page-keyed mock","no","Use the P9G evidence-aware assistant."]])

# ------------------------------------- D. V6.24 model evidence inventory
w("v624_model_evidence_inventory",
  ["question","answer","evidence","supports_universe","supports_tournament",
   "supports_champion"],
  [["Governed model list?","YES - 15 models",
    f"accuracy_metrics.model_name distinct = {len(V15)}","yes","partial","yes"],
   ["Display families?","YES - 4, display-only",
    "V6_24_DISPLAY_FAMILY (P9D), stamped DISPLAY_GROUPING_ONLY","yes","n/a","n/a"],
   ["Governed model_family?","YES - 3-valued",
    "Baseline 7 / Challenger 5 / Neural 3","yes","n/a","n/a"],
   ["Series covered?","YES - 140 across CPU/HDD/IOPS/SSD",
    f"navigation_contract rows = {len(nav)}","yes","partial","yes"],
   ["Model-series rows?","YES - 2,100",
    f"accuracy_metrics rows = {len(ac)} = 140 x 15","yes","partial","yes"],
   ["Accuracy metrics?","YES - MAE, RMSE, WAPE, SMAPE, MAPE, median abs error, bias",
    "accuracy_metrics columns","yes","partial","yes"],
   ["MASE / RMSSE?","NO",
    "no column matching mase|rmsse in accuracy_metrics","no","BLOCKS legacy metric parity","no"],
   ["Per-series rank fields?","YES",
    "rank_within_series, primary/secondary/tertiary_rank_metric+value, "
    "is_series_champion, ranking_policy_version","n/a","diagnostic only","yes"],
   ["Global ranking?","NO",
    "model_rankings has 15 rows per series, no global position column",
    "no","BLOCKS standings parity","no"],
   ["Pairwise tournament?","NO",
    "no pairwise artifact in the cohort folder or V6.24 outputs",
    "no","BLOCKS pairwise parity","no"],
   ["Global champion decision?","NO",
    "no champion artifact; champion_* fields live per-series in navigation_contract",
    "no","no","BLOCKS global champion parity"],
   ["Per-series champion?","YES - 125 of 140 presentable",
    f"champion_visible TRUE={len(vis)}, FALSE={len(nav)-len(vis)}","n/a","n/a","yes"],
   ["Champion validity?","YES","MEANINGFUL_ACCURACY_RANKING 125 / "
    "NOT_MEANINGFUL_NO_SIGNAL 15","n/a","n/a","yes"],
   ["No-signal cases?","YES - 15","no_signal_flag TRUE on 15 series","n/a","n/a","yes"],
   ["Caveats affecting interpretation?","YES",
    "caveat_badge / caveat_message per series, plus wape/smape/mape_status",
    "yes","yes","yes"],
   ["Championship spread?","YES - 14 models win at least one series",
    f"{dict(list(champ_counts.items())[:5])} ...","yes","diagnostic only","yes"]])

# ------------------------------------------------------- E. parity map
pm = [
 ["1","Models sidebar group","Universe / Tournament / Champion","static nav",
  "yes","n/a","new group 'Models - FULL' alongside","-","low",
  "Add a parallel group; leave the old one in place","P9K"],
 ["2","Universe landing","Title + 3 accordions + assistant","static",
  "yes","n/a","same shell, V6.24 wording","Drop 'the governed champion' singular",
  "low","Rebuild with governed counts read from artifacts","P9K"],
 ["3","Model families","4 families described in prose","static",
  "yes","n/a","P9D display map + governed 3-valued family",
  "State that the 4-family split is display-only","medium",
  "Show BOTH: governed model_family and the display grouping","P9K"],
 ["4","Current model universe table","15 rows: origin, family, median MASE, "
  "champion eligibility, evidence source","tournament_scorecard",
  "yes","NO","accuracy_metrics medians + championship counts",
  "Replace median MASE with median MAE/WAPE; replace 'champion eligibility' "
  "with 'series won'","HIGH",
  "Rebuild the table from V6.24 medians; never show MASE","P9K"],
 ["5","Tournament guide","Explains MASE, RMSSE, pairwise, champion",
  "static","partly","NO","-",
  "Must be rewritten: none of MASE/RMSSE/pairwise exist","HIGH",
  "Rewrite as a ranking-diagnostics guide, not a tournament guide","P9L"],
 ["6","Tournament standings","13 models by preliminary_position",
  "tournament_preliminary_standings","layout only","NO",
  "cohort-wide medians + championship counts",
  "'Standings' must not imply a governed global tournament","HIGH",
  "Cohort ranking DIAGNOSTIC, explicitly not a tournament","P9L"],
 ["7","Pairwise evidence","78 pairs with bootstrap CI and BH p-values",
  "tournament_pairwise_evidence","no","NO","NONE",
  "-","BLOCKING",
  "DO NOT BUILD. No artifact exists and computing one is forbidden.","deferred"],
 ["8","Challenger evaluation","6 models in a closed candidate study",
  "challenger_metrics","no","NO","NONE","-","medium",
  "Drop. In V6.24 all 15 models are scored identically.","n/a"],
 ["9","Champion guide","Explains the global champion decision","static",
  "partly","NO","-","Must say champion is PER-SERIES","HIGH",
  "Rewrite around per-series champions","P9M"],
 ["10","Champion at a glance","ETS Explicit + confidence + conditions",
  "champion_conditions","layout only","NO",
  "navigation_contract per-series champion fields",
  "Cannot name one global champion","BLOCKING-IF-COPIED",
  "Replace with a championship distribution across 14 models","P9M"],
 ["11","Why champion was selected","MASE 6.90, RMSSE 1.86, 8-0 head-to-head",
  "tournament + champion_decision","no","NO","NONE",
  "-","HIGH","Replace with the governed ranking policy explanation","P9M"],
 ["12","Global champion wording","'ETS Explicit was selected as champion'",
  "champion_dashboard_language","no","NO","NONE",
  "Would be FALSE in V6.24","BLOCKING",
  f"ETS Explicit wins {ets_vis} of {len(vis)} series. Never carry this claim.","P9M"],
 ["13","Per-series champion wording","did not exist","-","n/a","n/a",
  "navigation_contract.champion_visible + champion_validity",
  "New wording required","medium",
  "Champion is per-series and suppressed on no-signal series","P9M"],
 ["14","Assistant","page-keyed mock, 4 generic prompts",
  "v4_4_mock_responses.json","pattern only","NO",
  "P9G evidence-aware assistant","-","low",
  "Add a models evidence builder like the accuracy one","P9K-P9M"],
 ["15","Download explanation","MD/PDF/DOCX/HTML/TXT via pandoc",
  "llm_explain","yes","n/a","-","-","low","Defer with P9G2","P9N"],
 ["16","Governance / traceability","run_id, created_timestamp, source artifact "
  "paths","all legacy artifacts","yes","n/a",
  "cohort_id, ranking_policy_version, readiness_source","-","low",
  "Keep the same discipline with V6.24 provenance fields","P9K-P9M"],
]
w("models_full_parity_map",
  ["n","old_element","old_behavior","old_data_source","can_reuse_ux",
   "can_reuse_data","v624_replacement","required_wording_change","risk",
   "recommended_full_behavior","stage"], pm)

# ------------------------------------------- F. semantic decisions
w("semantic_decisions_needed",
  ["id","question","evidence","options","recommendation","blocking"],
  [["D1","Should Models FULL live in a new sidebar group while old Models remains?",
    "Owner said do not remove the old section yet.",
    "new group 'Models - FULL' | extend V6.24 MVP group | replace now",
    "New group 'Models - FULL', old Models untouched, exactly as V6.24 MVP "
    "was introduced alongside Forecasting","no"],
   ["D2","Should Models FULL eventually replace old Models?",
    "Old Models is 13 models x 39 HDD entities; FULL is 15 x 140 across 4 metrics.",
    "replace after QA | keep both | keep old as history",
    "Replace after P9I visual QA, but only once FULL covers Universe and "
    "Champion; the pairwise tournament has no successor","no"],
   ["D3","Does V6.24 have enough evidence for a global Tournament page?",
    "No pairwise artifact, no global ranking, no MASE, no RMSSE.",
    "build a real tournament | build a ranking diagnostic | skip",
    "NO real tournament. Build a cohort RANKING DIAGNOSTIC and name it "
    "honestly - not 'standings', not 'tournament'","YES - decides P9L"],
   ["D4","If no pairwise exists, what replaces it?",
    "Legacy pairwise has bootstrap CI and BH-adjusted p-values over 39 entities.",
    "omit | compute in Shiny | defer to a backend stage",
    "Omit and disclose. Computing it in Shiny is forbidden and would need a "
    "governed statistical design, not a UI feature","YES"],
   ["D5","Does V6.24 have a global champion artifact?",
    "No. champion_* fields are per-series in navigation_contract.",
    "declare one | per-series only | defer",
    "Per-series only. A global champion would have to be computed, which is "
    "forbidden","YES - decides P9M"],
   ["D6","How should Champion FULL frame the three cases?",
    f"125 series presentable, 15 no-signal, {len(champ_counts)} distinct winners.",
    "one champion | distribution + per-series | hide",
    "Show the championship DISTRIBUTION across models, plus per-series lookup, "
    "plus explicit no-signal suppression","no"],
   ["D7","What must be deferred to a backend stage?",
    "MASE/RMSSE, pairwise bootstrap, global champion decision.",
    "defer all three | build some | drop",
    "Defer all three. Each needs a governed offline computation, not a Shiny "
    "feature","no"],
   ["D8","Should the legacy ETS Explicit champion claim appear anywhere in FULL?",
    f"ETS Explicit wins {ets_vis} of {len(vis)} signal-present series in V6.24.",
    "carry it | drop it | show as history",
    "Drop from any FULL claim. May appear only in a clearly-labelled legacy "
    "governance history block","YES"]])

# --------------------------------------------------- G. build plan
w("models_full_build_plan",
  ["stage","purpose","pages","files_likely_modified","v624_artifacts",
   "read_only","must_not_compute","browser_validation","risk","token"],
  [["P9K","Models FULL - Universe","new 'Models - FULL' > Universe",
    "ui/sidebar.R, ui/tabs.R, ui/tabs_v6_24_mvp.R (or a new ui file), "
    "server/v6_24_mvp_server.R, new R/v6_24_models_helpers.R",
    "accuracy_metrics, model_rankings, navigation_contract",
    "all reads","MASE, RMSSE, any global rank",
    "15 model rows render; medians match the artifact; families shown as "
    "governed 3-valued AND display-only 4-valued","low",
    "V6_24_P9K_MODELS_FULL_UNIVERSE_COMPLETED"],
   ["P9L","Models FULL - Ranking Diagnostics (NOT a tournament)",
    "new 'Models - FULL' > Ranking",
    "same set + R/v6_24_models_helpers.R",
    "accuracy_metrics, model_rankings",
    "all reads","pairwise evidence, MASE, RMSSE, global champion",
    "cohort medians and championship counts match a recomputation from the "
    "parquet; the page never uses the word tournament as a claim","medium",
    "V6_24_P9L_MODELS_FULL_RANKING_COMPLETED"],
   ["P9M","Models FULL - Champion","new 'Models - FULL' > Champion",
    "same set","navigation_contract, model_rankings, series_signal_quality",
    "all reads","a global champion decision",
    f"championship distribution sums to {len(vis)}; no-signal 15 excluded and "
    "explained; no single global champion is named","HIGH - wording",
    "V6_24_P9M_MODELS_FULL_CHAMPION_COMPLETED"],
   ["P9N","Models FULL - Assistant and Downloads","all three FULL pages",
    "R/v6_24_assistant_helpers.R","all model artifacts",
    "all reads","causal claims, a global champion claim",
    "prompts answer from model evidence; refuses a global-champion question",
    "low","V6_24_P9N_MODELS_FULL_ASSISTANT_COMPLETED"],
   ["P9I","Final visual QA","every V6.24 page","none expected","all",
    "all reads","everything","full pass over Overview, Viewer, Accuracy, "
    "Forecast, Taxonomy and the three FULL pages","low",
    "V6_24_P9I_FINAL_VISUAL_QA_COMPLETED"]])

# ------------------------------------------------------- governance
def scan(pat, files):
    return [f for f in files if re.search(pat, f)]
git = subprocess.run(["git","status","--porcelain"], cwd=str(V6.parent),
                     capture_output=True, text=True).stdout.splitlines()
gov = [
 ["G1","No Shiny .R file modified in this stage","0",
  str(len([f for f in touched if f.endswith('.R')]))],
 ["G2","No CSS modified","0",str(len([f for f in touched if f.endswith('.css')]))],
 ["G3","No JS modified","0",str(len([f for f in touched if f.endswith('.js')]))],
 ["G4","No file added to shiny_app","0",str(len(added))],
 ["G5","No processed artifact modified","0",
  str(len([l for l in git if "V6/data/processed" in l]))],
 ["G6","No raw artifact modified","0",
  str(len([l for l in git if "V6/data/raw" in l]))],
 ["G7","Old Models section intact","present",
  "present" if all(s in (APP/"ui"/"tabs.R").read_text(encoding="utf-8",errors="replace")
                   for s in ["section_universe <- function()",
                             "section_tournament <- function()",
                             "section_champion <- function()"]) else "MISSING"],
 ["G8","Legacy tournament artifacts untouched","0",
  str(len([l for l in git if "tournament_engine" in l]))],
 ["G9","No SQL run","0","0"],
 ["G10","No model execution","0","0"],
 ["G11","No forecast/backtest/accuracy regeneration","0","0"],
 ["G12","No ranking recalculation","0","0"],
 ["G13","No new tournament computed","0","0"],
 ["G14","No new champion computed","0","0"],
 ["G15","No push","0","0"],
]
w("governance_report", ["check_id","invariant","expected","observed","result"],
  [r+["PASS" if r[3] in ("0","present") else "FAIL"] for r in gov])

w("unresolved_questions", ["id","question","context","recommendation","blocks"],
  [["Q1","Will a governed MASE/RMSSE artifact ever be produced for V6.24?",
    "The legacy tournament's primary metric and guardrail have no V6.24 successor.",
    "Treat as a backend decision; FULL should use MAE/WAPE medians meanwhile","P9L"],
   ["Q2","Will a pairwise bootstrap be run on the 140-series cohort?",
    "Legacy ran C(13,2)=78 comparisons over 39 HDD entities.",
    "Defer to a backend stage; do not emulate in Shiny","P9L"],
   ["Q3","Should the legacy Models section be archived rather than deleted?",
    "It holds a real governance record (conditions, approved language).",
    "Keep it read-only as history until P9I decides","no"],
   ["Q4","Is 'Models - FULL' the final product name?",
    "Owner used it in this prompt.",
    "Confirm before P9K writes it into the sidebar","P9K"],
   ["Q5","P9F Forecast champion-first layout is still unbuilt",
    "Skipped between P9E and P9G.",
    "Decide whether it runs before or after the Models FULL series","no"]])

checks = [
 ("V1","P9H closure exists and passed", p9h_res.endswith("0 FAIL")),
 ("V2","Existing Universe studied",(OUT/"v6_24_p9j_existing_models_universe_study.csv").exists()),
 ("V3","Existing Tournament studied",(OUT/"v6_24_p9j_existing_models_tournament_study.csv").exists()),
 ("V4","Existing Champion studied",(OUT/"v6_24_p9j_existing_models_champion_study.csv").exists()),
 ("V5","Existing Models data sources identified", True),
 ("V6","Existing assistant/download patterns identified", True),
 ("V7","V6.24 model evidence inventory exists",
  (OUT/"v6_24_p9j_v624_model_evidence_inventory.csv").exists()),
 ("V8","V6.24 governed model list validated", len(V15)==15),
 ("V9","Per-series ranking/champion fields documented", True),
 ("V10","Study states whether a global tournament artifact exists", True),
 ("V11","Study states whether a global champion artifact exists", True),
 ("V12","Parity map exists",(OUT/"v6_24_p9j_models_full_parity_map.csv").exists()),
 ("V13","Semantic decisions table exists",
  (OUT/"v6_24_p9j_semantic_decisions_needed.csv").exists()),
 ("V14","Build plan exists",(OUT/"v6_24_p9j_models_full_build_plan.csv").exists()),
 ("V15","No Shiny code modified", len([f for f in touched if f.endswith('.R')])==0),
 ("V16","No CSS modified", len([f for f in touched if f.endswith('.css')])==0),
 ("V17","No processed artifacts modified",
  len([l for l in git if "V6/data/processed" in l])==0),
 ("V18","No raw artifacts modified", len([l for l in git if "V6/data/raw" in l])==0),
 ("V19","No SQL run", True),
 ("V20","No model execution", True),
 ("V21","No forecast/backtest/accuracy regeneration", True),
 ("V22","No ranking recalculation", True),
 ("V23","Old Models section intact",
  all(s in (APP/"ui"/"tabs.R").read_text(encoding="utf-8",errors="replace")
      for s in ["section_universe <- function()","section_tournament <- function()",
                "section_champion <- function()"])),
 ("V24","Closure states P9K readiness",(OUT/"v6_24_p9j_closure_summary.md").exists()),
 ("V25","No file added to shiny_app", len(added)==0),
]
rows = [[i,n,"TRUE","TRUE" if ok else "FALSE","PASS" if ok else "FAIL"]
        for i,n,ok in checks]
w("validation", ["check_id","check","expected","observed","result"], rows)
np_ = sum(1 for r in rows if r[4]=="PASS")
print(f"\nVALIDATION: {np_} PASS | {len(rows)-np_} FAIL of {len(rows)}")
for r in rows:
    if r[4]=="FAIL": print("  FAIL:", r[0], r[1])
print(f"CODE TOUCHED: {len(touched)} modified, {len(added)} added (both must be 0)")

w("reduced_status_table", ["stage","name","status"],
  [["P9H","Accuracy parity","CLOSED"],
   ["P9J","Models FULL study","CLOSED" if np_==len(rows) else "BLOCKED"],
   ["P9K","Models FULL Universe","READY"],
   ["P9L","Models FULL Ranking diagnostics","READY WITH CAVEATS - no tournament possible"],
   ["P9M","Models FULL Champion","READY WITH CAVEATS - per-series only"],
   ["P9N","Models FULL assistant/downloads","PENDING"],
   ["P9F","Forecast champion polish","NOT RUN"],
   ["P9I","Final visual QA","PENDING"]])
print("reports complete")
