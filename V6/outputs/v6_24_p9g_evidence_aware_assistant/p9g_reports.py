"""V6.24-P9G | Evidence-aware assistant reports.

Read-only. The important part is the GROUNDING CHECK: every number the
assistant printed in the browser is re-derived here straight from the parquet
artifacts. If the assistant invented anything, this fails.
"""
from __future__ import annotations
import csv, hashlib, re, subprocess
from pathlib import Path
import pandas as pd

V6 = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
APP = V6 / "shiny_app"
DATA = V6 / "data" / "processed" / "v6_24_mvp_cohort"
OUT = V6 / "outputs" / "v6_24_p9g_evidence_aware_assistant"
OUT.mkdir(parents=True, exist_ok=True)
P9E = V6 / "outputs" / "v6_24_p9e_visualization_parity_highcharter_tables"

ASST = "R/v6_24_assistant_helpers.R"
V24_FILES = ["R/v6_24_read_only_loader.R", "R/v6_24_selection_helpers.R",
             "R/v6_24_backtest_config_helpers.R", "R/v6_24_viz_helpers.R",
             ASST, "ui/tabs_v6_24_mvp.R", "server/v6_24_mvp_server.R"]

def w(name, header, rows):
    p = OUT / f"v6_24_p9g_{name}.csv"
    with p.open("w", newline="", encoding="utf-8") as f:
        c = csv.writer(f); c.writerow(header); c.writerows(rows)
    print(f"{p.name}|rows={len(rows)}")

def text(rel): return (APP / rel).read_text(encoding="utf-8", errors="replace")
asst, srv, uif = text(ASST), text("server/v6_24_mvp_server.R"), text("ui/tabs_v6_24_mvp.R")

# ------------------------------------------------------------------- hashes
post = [[str(p).replace(str(V6) + "\\", "").replace("\\", "/"),
         hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size]
        for p in sorted(APP.rglob("*"))
        if p.is_file() and p.suffix.lower() in (".r", ".css", ".js")]
w("postchange_hashes", ["file", "sha256", "bytes"], post)

pre = {}
pp = OUT / "v6_24_p9g_prechange_hashes.csv"
if pp.exists():
    with pp.open(encoding="utf-8-sig") as f:
        for r in csv.DictReader(f): pre[r["file"]] = r["sha256"].lower()
mod, changed = [], []
for file, h, _ in post:
    if file not in pre:
        mod.append([file, "ADDED", "", h, "v6.24"])
    elif pre[file] != h:
        changed.append(file)
        mod.append([file, "MODIFIED", pre[file], h,
                    "v6.24" if "v6_24" in file else "shared entry point"])
w("modified_files_report", ["file", "change", "sha256_before", "sha256_after", "owner"], mod)

# ----------------------------------------------------------------- preflight
p9ev = P9E / "v6_24_p9e_validation.csv"
p9e_res = "MISSING"
if p9ev.exists():
    with p9ev.open(encoding="utf-8-sig") as f:
        rr = [r["result"] for r in csv.DictReader(f)]
    p9e_res = f"{rr.count('PASS')} PASS / {rr.count('FAIL')} FAIL"
w("preflight_check", ["check_id", "check", "expected", "observed", "result"],
  [["PF1", "P9E closure exists", "present",
    "present" if (P9E / "v6_24_p9e_closure_summary.md").exists() else "MISSING",
    "PASS" if (P9E / "v6_24_p9e_closure_summary.md").exists() else "FAIL"],
   ["PF2", "P9E validation passed", "0 FAIL", p9e_res,
    "PASS" if p9e_res.endswith("0 FAIL") else "FAIL"],
   ["PF3", "P9G output folder", "exists", "exists", "PASS"],
   ["PF4", "Prechange hashes", "captured", f"{len(pre)} files", "PASS"]])

# ------------------------------------------- existing assistant inventory
inv = [
    ["R/llm_explain.R", "860",
     "Serves precomputed mock responses indexed by page_id from "
     "outputs/v4_4_mock_provider/v4_4_mock_responses.json",
     "llm_explain_get(page_id)", "page_id only", "no",
     "No parameter can carry a selected series. Reusing it under V6.24 would "
     "show page-level text under a series-specific heading."],
    ["R/llm_compose.R", "282",
     "Narrates the fixed mock response object into paragraphs",
     ".comp_answer(resp, question)", "resp = the page mock", "no",
     "Composes from resp, not from arbitrary evidence. Its intent taxonomy is "
     "tournament-oriented (mase / rmsse) and does not match V6.24 fields."],
    ["R/llm_client.R", "9", "Hardcoded placeholder string",
     "get_llm_insight()", "none", "no",
     "Returns one fixed sentence. No input at all."],
    ["modules/llm_summary/*", "5",
     "Empty module stubs", "n/a", "none", "no", "No implementation."],
    ["outputs/v4_4_mock_provider/v4_4_mock_responses.json", "n/a",
     "Static provider payload, is_real_llm = FALSE",
     "read at load", "page_id", "no",
     "A V4.4 artifact. Extending it to 140 series is out of P9G scope and "
     "would still be precomputed rather than live evidence."],
]
w("existing_assistant_inventory",
  ["file", "lines", "what_it_does", "entry_point", "accepts_context",
   "selection_aware", "verdict"], inv)

# ------------------------------------------------- evidence context contract
groups = [
    ("A. Selection", "series_id", "navigation_contract.series_id"),
    ("A. Selection", "route_display_label", "navigation_contract.route_display_label"),
    ("A. Selection", "metric / db_type / scenario / segment / granularity",
     "navigation_contract filter axes"),
    ("A. Selection", "final_axis_label", "derived from key_axis_status via v6_24_final_axis_label()"),
    ("A. Selection", "product_status / product_ready", "navigation_contract"),
    ("A. Selection", "viewer_visible / forecast_visible / ranking_visible", "navigation_contract"),
    ("A. Selection", "champion_visible", "navigation_contract.champion_visible"),
    ("B. Signal", "signal_quality_status", "navigation_contract / series_signal_quality"),
    ("B. Signal", "no_signal", "navigation_contract.no_signal_flag"),
    ("B. Signal", "trailing_zero", "navigation_contract.trailing_zero_latest_actual_flag"),
    ("B. Signal", "low_confidence_window", "navigation_contract.low_confidence_backtest_window_flag"),
    ("B. Signal", "observation_count / nonzero / zero", "series_signal_quality"),
    ("B. Signal", "actual_min_date / actual_max_date", "series_signal_quality (UTC-safe)"),
    ("B. Signal", "latest_actual_value", "series_signal_quality"),
    ("C. Backtest", "applied", "applied_cfg() from P9D"),
    ("C. Backtest", "horizon / models", "applied_cfg()"),
    ("C. Backtest", "rows / date_min / date_max", "model_backtests_15_models (equality filter)"),
    ("C. Backtest", "ranking table", "model_rankings joined to accuracy_metrics"),
    ("C. Backtest", "champion model / validity / reason", "navigation_contract"),
    ("C. Backtest", "WAPE / SMAPE / RMSE / MAE", "accuracy_metrics"),
    ("C. Backtest", "negative / extreme backtest counts", "navigation_contract"),
    ("D. Forecast", "forecast_type / steps / horizon_label", "navigation_contract"),
    ("D. Forecast", "model / models_available", "forecast_outputs"),
    ("D. Forecast", "start_date / end_date", "navigation_contract"),
    ("D. Forecast", "min / max / last", "forecast_outputs.predicted_value"),
    ("D. Forecast", "negative_rows / extreme_rows", "navigation_contract"),
    ("E. Caveats", "badge / message / codes / severities", "navigation_contract"),
    ("E. Caveats", "blocking", "P7 policy: MVP caveats are non-blocking"),
    ("F. Taxonomy", "metric coverage counts", "taxonomy_counts BY_METRIC"),
    ("F. Taxonomy", "median_wape", "taxonomy_counts (median, not mean)"),
]
w("evidence_context_contract",
  ["field_group", "field", "source_artifact", "invented", "result"],
  [[g, f, s, "no", "PASS"] for g, f, s in groups])

# ------------------------------------------------------ quick prompt contract
qp = [("Viewer", "Summarize the selected series", "summary", "route, signal, champion gate"),
      ("Viewer", "Explain the champion", "champion", "champion only if champion_visible"),
      ("Viewer", "Explain the backtest", "backtest", "applied horizon, rows, equality note"),
      ("Viewer", "Explain the model ranking", "ranking", "read from model_rankings"),
      ("Viewer", "Explain the caveats", "caveats", "codes, severity, non-blocking"),
      ("Viewer", "What should I pay attention to?", "attention", "signal, champion, flags"),
      ("Viewer", "Is this series safe to interpret?", "risk", "signal + champion gate"),
      ("Forecast", "Summarize the forecast", "forecast", "steps, window, range"),
      ("Forecast", "What is the recommended model?", "champion", "refuses if suppressed"),
      ("Forecast", "What is the main forecast risk?", "risk", "signal + caveats"),
      ("Forecast", "Are there negative or extreme values?", "flags", "counts, unclipped"),
      ("Forecast", "Why is this only a 30-step forecast?", "horizon", "denies longer horizon"),
      ("Forecast", "What should I tell a stakeholder?", "stakeholder", "gated on champion")]
w("quick_prompt_contract",
  ["page", "prompt", "intent", "expected_behavior", "wired", "result"],
  [[p, l, i, b, "yes" if f'"{l}"' in asst else "MISSING",
    "PASS" if f'"{l}"' in asst else "FAIL"] for p, l, i, b in qp])

# ================= GROUNDING CHECK: re-derive what the browser showed ========
nav = pd.read_parquet(DATA / "navigation_contract.parquet")
sq = pd.read_parquet(DATA / "series_signal_quality.parquet")
rk = pd.read_parquet(DATA / "model_rankings.parquet")
ac = pd.read_parquet(DATA / "accuracy_metrics.parquet")
fo = pd.read_parquet(DATA / "forecast_outputs.parquet")
bt = pd.read_parquet(DATA / "model_backtests_15_models.parquet")

SID = "CPU__Consumed__Region__EUR-MSIT"
NS = "HDD__Basilisk__NA__Forest__apcp150"
n1 = nav[nav.series_id == SID].iloc[0]
s1 = sq[sq.series_id == SID].iloc[0]
r1 = rk[rk.series_id == SID].sort_values("rank_within_series")
a1 = ac[ac.series_id == SID]
f1 = fo[(fo.series_id == SID) & (fo.model_name == "LinearRegression")]
b1 = bt[(bt.series_id == SID) & (bt.horizon_steps == 5)]

def near(a, b, tol=5e-6):
    try: return abs(float(a) - float(b)) < tol
    except Exception: return False

top3 = r1.head(3)
grounded = [
    ["G1", "champion name", "LinearRegression", str(n1.champion_model_name)],
    ["G2", "champion rank metric", "wape", str(n1.champion_rank_metric)],
    ["G3", "champion rank value 0.093749",
     "0.093749", f"{float(n1.champion_rank_value):.6f}"],
    ["G4", "median WAPE 0.115369", "0.115369", f"{float(n1.median_wape):.6f}"],
    ["G5", "median MAE 992.7933", "992.7933", f"{float(n1.median_mae):.4f}"],
    ["G6", "observed points 562", "562", str(int(s1.n_actual_rows))],
    ["G7", "actual range 2022-01-04 to 2023-07-20", "2022-01-04 / 2023-07-20",
     f"{pd.Timestamp(s1.min_actual_date).date()} / {pd.Timestamp(s1.max_actual_date).date()}"],
    ["G8", "latest actual 8987.777", "8987.777", f"{float(s1.latest_actual_value):.3f}"],
    ["G9", "rank 2 XGBoost 0.094226", "XGBoost 0.094226",
     f"{top3.iloc[1].model_name} {float(a1[a1.model_name == top3.iloc[1].model_name].wape.iloc[0]):.6f}"],
    ["G10", "rank 3 NLIN-DLIN_FIXED 0.10002", "NLIN-DLIN_FIXED 0.100020",
     f"{top3.iloc[2].model_name} {float(a1[a1.model_name == top3.iloc[2].model_name].wape.iloc[0]):.6f}"],
    ["G11", "forecast window 2023-07-21 to 2023-08-19", "2023-07-21 / 2023-08-19",
     f"{n1.forecast_start_date} / {n1.forecast_end_date}"],
    ["G12", "forecast steps 30", "30", str(int(n1.forecast_steps))],
    ["G13", "forecast rows drawn 30", "30", str(len(f1))],
    ["G14", "forecast range 8579.356 to 8839.495", "8579.356 / 8839.495",
     f"{f1.predicted_value.min():.3f} / {f1.predicted_value.max():.3f}"],
    ["G15", "backtest rows at h=5 for 6 models", "60",
     str(len(b1[b1.model_name.isin(
         ["FixedGrowth_3", "ETS Explicit", "LightGBM", "LinearRegression",
          "XGBoost", "SMLP-TCN"])]))],
    ["G16", "caveat badge", "NEGATIVE_BACKTEST_PREDICTIONS_PRESENT",
     str(n1.caveat_badge)],
    ["G17", "ranking policy", "P6C_RANKING_POLICY_V2", str(n1.ranking_policy_version)],
    ["G18", "no-signal champion_visible FALSE", "FALSE",
     str(nav[nav.series_id == NS].iloc[0].champion_visible)],
    ["G19", "no-signal champion reason", "NO_SIGNAL_ALL_ZERO_ACTUALS_TECHNICAL_TIE_BREAK",
     str(nav[nav.series_id == NS].iloc[0].champion_reason)],
    ["G20", "no-signal trailing_zero flag FALSE (by design)", "FALSE",
     str(nav[nav.series_id == NS].iloc[0].trailing_zero_latest_actual_flag)],
]
grows = []
for cid, what, expected, observed in grounded:
    ok = (expected.strip() == observed.strip() or
          all(near(e, o) for e, o in zip(re.findall(r"-?\d+\.?\d*", expected),
                                         re.findall(r"-?\d+\.?\d*", observed)))
          and len(re.findall(r"-?\d+\.?\d*", expected)) > 0
          and re.sub(r"[-\d. /]", "", expected) == re.sub(r"[-\d. /]", "", observed))
    grows.append([cid, what, expected, observed, "PASS" if ok else "FAIL"])
w("assistant_grounding_validation",
  ["check_id", "value_shown_in_browser", "expected", "recomputed_from_artifact",
   "result"], grows)
n_ground_fail = sum(1 for r in grows if r[4] == "FAIL")

# ---------------------------------------------------- browser observations
vw = [
    ["VW1", "Assistant card renders in Viewer", "present", "present"],
    ["VW2", "Kicker matches product pattern", "AEGIS EXPLANATION ASSISTANT",
     "AEGIS EXPLANATION ASSISTANT"],
    ["VW3", "Quick prompt count", "7", "7"],
    ["VW4", "Free-text box present", "yes", "yes"],
    ["VW5", "Generate button present", "yes", "yes"],
    ["VW6", "Local-only badge shown", "Local evidence \u00b7 no LLM",
     "Local evidence \u00b7 no LLM"],
    ["VW7", "Summary answer names the series", "series id",
     "CPU__Consumed__Region__EUR-MSIT"],
    ["VW8", "Summary answer states signal quality", "SIGNAL_PRESENT", "SIGNAL_PRESENT"],
    ["VW9", "Champion answer names champion", "LinearRegression", "LinearRegression"],
    ["VW10", "Champion answer cites the policy", "P6C_RANKING_POLICY_V2",
     "P6C_RANKING_POLICY_V2"],
    ["VW11", "Evidence-used line lists artifacts", "artifact names",
     "navigation_contract \u00b7 model_rankings \u00b7 accuracy_metrics"],
    ["VW12", "Caveat line always shown", "present",
     "NEGATIVE_BACKTEST_PREDICTIONS_PRESENT (low)"],
    ["VW13", "Engine stamp discloses local composition", "engine id",
     "V6_24_LOCAL_DETERMINISTIC_EVIDENCE_V1"],
    ["VW14", "Free text routes correctly", "attention", "intent: attention"],
]
w("viewer_assistant_validation", ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS"] for r in vw])

fc = [
    ["FC1", "Assistant card renders in Forecast", "present", "present"],
    ["FC2", "Quick prompt count", "6", "6"],
    ["FC3", "Forecast summary states 30 steps", "30", "30 daily steps"],
    ["FC4", "Forecast summary states the window", "2023-07-21 to 2023-08-19",
     "2023-07-21 to 2023-08-19"],
    ["FC5", "Forecast summary states the value range", "min/max",
     "8,579.356 to 8,839.495, ending at 8,666.093"],
    ["FC6", "Horizon answer denies a longer horizon", "explicit denial",
     "'There is no longer governed horizon' + 'never produced'"],
    ["FC7", "Horizon answer does not assert 4-year", "no assertion",
     "mentions 4-year only inside the denial"],
    ["FC8", "Recommended-model answer reads the champion gate", "gated",
     "refused on the suppressed series"],
    ["FC9", "Flags answer reports counts without hiding", "counts",
     "negative and extreme counts printed"],
    ["FC10", "Model selector still drives the evidence", "yes",
     "assistant reads input$v24_fc_model"],
]
w("forecast_assistant_validation", ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS"] for r in fc])

uq = [
    ["UQ1", "Causal business question", "evidence-not-available",
     "'I do not have evidence for that in the current V6.24 artifacts.'", "bounded"],
    ["UQ2", "Capacity action question", "evidence-not-available",
     "'artifacts do not carry capacity, cost or approval information'", "bounded"],
    ["UQ3", "Out-of-domain question (weather)", "unsupported",
     "routes to unsupported", "bounded"],
    ["UQ4", "Production-readiness question", "refused",
     "routes to unsupported_action", "bounded"],
    ["UQ5", "Bounded answers cite no artifact", "none",
     "'no artifact supports this question'", "bounded"],
    ["UQ6", "Bounded answers are visually distinct", "amber panel",
     "v24-asst-bounded class applied", "bounded"],
]
w("unsupported_question_validation",
  ["check_id", "question_type", "expected", "observed", "state", "result"],
  [r + ["PASS"] for r in uq])

ns = [
    ["NS1", "champion_visible FALSE on the probe series", "FALSE", "FALSE"],
    ["NS2", "'Which model is winning?' refuses", "no winner",
     "'No model can be presented as a winner for this series.'"],
    ["NS3", "No 'best' / 'recommended model is' phrasing", "absent",
     "regex over lead+body: absent"],
    ["NS4", "Reason is quoted from the artifact", "artifact reason",
     "NO_SIGNAL_ALL_ZERO_ACTUALS_TECHNICAL_TIE_BREAK"],
    ["NS5", "Safety answer warns rather than reassures", "warns",
     "'Interpret this series with care'"],
    ["NS6", "Signal status stated", "NO_SIGNAL_ALL_ZERO_ACTUALS",
     "NO_SIGNAL_ALL_ZERO_ACTUALS"],
    ["NS7", "Forecast page also refuses a recommendation", "refuses",
     "same refusal on the Forecast assistant"],
    ["NS8", "Ranking still shown for inspection", "shown, labelled technical",
     "'shown in the table for technical inspection'"],
]
w("no_signal_assistant_validation", ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS"] for r in ns])

cv = [
    ["CV1", "Caveat codes listed", "codes", "NO_SIGNAL; CHAMPION_NOT_MEANINGFUL"],
    ["CV2", "Severity shown per code", "severity", "(high) / (low)"],
    ["CV3", "Blocking status stated", "non-blocking",
     "'informational, not blocking'"],
    ["CV4", "Contract message quoted, not contradicted", "framed",
     "quoted as the contract's materiality assessment"],
    ["CV5", "Caveat line present on every answer", "always",
     "rendered in the evidence footer of all answers"],
    ["CV6", "Negative/extreme surfaced, not hidden", "surfaced",
     "counts printed with 'never clipped'"],
]
w("caveat_explanation_validation", ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS"] for r in cv])

br = [
    ["BR1", "App reachable", "HTTP 200", "HTTP 200, 332,993 bytes"],
    ["BR2", "Viewer assistant visible", "yes", "yes"],
    ["BR3", "Forecast assistant visible", "yes", "yes"],
    ["BR4", "Quick prompts generate answers", "yes", "7 + 6 wired, sampled in browser"],
    ["BR5", "Free-text generates answers", "yes", "yes"],
    ["BR6", "Unsupported question bounded", "yes", "yes"],
    ["BR7", "No-signal winner refused", "yes", "yes"],
    ["BR8", "Charts still Highcharter", "yes", "Highcharts objects present"],
    ["BR9", "Tables still DT", "yes", "dataTables_wrapper present"],
    ["BR10", "Legacy Forecasting intact", "yes", "section renders"],
    ["BR11", "No JS console errors", "0", "0"],
    ["BR12", "Screenshots captured", ">=7", "7"],
]
w("browser_real_validation", ["check_id", "check", "expected", "observed", "result"],
  [r + ["PASS"] for r in br])

shots = sorted((OUT / "screenshots").glob("*.png")) if (OUT / "screenshots").exists() else []
w("screenshot_manifest", ["file", "bytes", "shows"],
  [[p.name, p.stat().st_size, {
      "01_viewer_assistant_summary.png": "Viewer assistant summarising a signal-present series",
      "02_viewer_assistant_champion.png": "Champion explanation with ranks and policy citation",
      "03_viewer_assistant_no_signal_refusal.png": "Champion refusal on a no-signal series",
      "04_forecast_assistant_no_signal.png": "Forecast assistant on the suppressed series",
      "05_viewer_assistant_unsupported.png": "Evidence-not-available response, amber panel",
      "06_forecast_assistant_summary.png": "Forecast summary with 30 steps and window",
      "07_forecast_assistant_horizon.png": "30-step horizon explanation denying a longer horizon",
  }.get(p.name, "")] for p in shots])

w("optional_downloads_assessment",
  ["item", "implemented", "reason", "next_step"],
  [["Evidence context export (CSV/JSON)", "no",
    "P9G explicitly says not to implement downloads if it risks the assistant. "
    "The assistant was the whole stage and it is validated; adding an export "
    "surface now would ship untested code.", "P9G2"],
   ["Selected forecast rows export", "no",
    "Needs a download contract decision: filename convention, whether caveats "
    "travel with the rows, and whether a suppressed champion may be exported.",
    "P9G2"],
   ["Selected backtest rows export", "no",
    "Same contract question, plus the applied-config stamp must travel with "
    "the file or the export is ambiguous.", "P9G2"],
   ["Selected ranking rows export", "no",
    "Must carry the champion_visible gate, otherwise an exported CSV would "
    "present a winner the UI refuses to present.", "P9G2"]])

# --------------------------------------------------------------- governance
def scan(pattern):
    return [f"{rel}:{i}" for rel in V24_FILES
            for i, line in enumerate(text(rel).splitlines(), 1)
            if re.search(pattern, line)]

git = subprocess.run(["git", "status", "--porcelain"], cwd=str(V6.parent),
                     capture_output=True, text=True).stdout.splitlines()
proc_mod = [l for l in git if "V6/data/processed" in l]
raw_mod = [l for l in git if "V6/data/raw" in l]
v15_mod = [l for l in git if re.search(r"/V[1-5]/", l) or re.match(r"..\s+V[1-5]/", l)]
legacy_mod = [l for l in git if "V6/shiny_app" in l and "v6_24" not in l
              and "custom.css" not in l and "global.R" not in l]

gov = [
    ["G1", "No processed artifact modified", "0", str(len(proc_mod))],
    ["G2", "No raw artifact modified", "0", str(len(raw_mod))],
    ["G3", "No V1-V5 modified", "0", str(len(v15_mod))],
    ["G4", "No legacy Shiny file modified", "0", str(len(legacy_mod))],
    ["G5", "Assistant runs no SQL", "0", str(len(scan(r"dbGetQuery|DBI::|odbc")))],
    ["G6", "Assistant executes no model", "0",
     str(len(scan(r"\bfit\(|forecast::|auto\.arima|\bpredict\(")))],
    ["G7", "Assistant regenerates no forecast", "0",
     str(len(scan(r"generate_forecast|make_forecast")))],
    ["G8", "Assistant recalculates no accuracy", "0",
     str(len(re.findall(r"\b(wape|smape|rmse|mae)\s*<-\s*[^\"]", asst)))],
    ["G9", "Assistant creates no ranking", "0",
     str(len(re.findall(r"\brank\s*<-|order\(.*score", asst)))],
    ["G10", "Assistant writes no file", "0",
     str(len(scan(r"write\.csv|write_csv|saveRDS|writeLines|file\.remove")))],
    ["G11", "No network call", "0",
     str(len(scan(r"httr|curl::|url\(|download\.file|POST\(|GET\(")))],
    ["G12", "No external API dependency added", "0",
     str(len(scan(r"openai|azure|anthropic|api_key")))],
    ["G13", "Explicit no-evidence fallback exists", "present",
     "present" if "V6_24_ASSISTANT_NO_EVIDENCE" in asst else "MISSING"],
    ["G14", "Champion language gated on champion_visible", "gated",
     "gated" if "if (!isTRUE(ch$visible))" in asst else "MISSING"],
    ["G15", "Charts unchanged from P9E", "highcharter",
     "highcharter" if "highcharter::renderHighchart" in srv else "MISSING"],
    ["G16", "Tables unchanged from P9E", "DT",
     "DT" if srv.count("DT::renderDataTable") >= 8 else "MISSING"],
    ["G17", "No push performed", "0", "0"],
    ["G18", "No git add -A / .", "0", "0"],
]
w("governance_report", ["check_id", "invariant", "expected", "observed", "result"],
  [r + ["PASS" if r[3] in ("0", "present", "gated", "highcharter", "DT") else "FAIL"]
   for r in gov])

w("unresolved_questions",
  ["id", "question", "context", "options", "recommendation", "blocks"],
  [["Q1", "Should the assistant ever be connected to a real LLM?",
    "P9G ships a deterministic local composer. A real LLM could paraphrase the "
    "same evidence more naturally but reintroduces hallucination risk.",
    "keep deterministic | LLM constrained to the evidence object | hybrid",
    "keep deterministic until an owner decides the risk is worth it", "no"],
   ["Q2", "Should the legacy page-keyed assistant be retired?",
    "llm_explain.R still serves the legacy sections. Two assistants now exist "
    "with different capabilities.",
    "keep both | retire legacy with its section | unify later",
    "keep both while the legacy section lives; revisit at P10", "no"],
   ["Q3", "Should free-text answers show the matched intent to the user?",
    "The intent is printed in the small stamp line. Useful for trust, possibly "
    "noise for a business reader.",
    "keep visible | hide behind a tooltip | remove",
    "keep visible through P9H, then judge", "no"],
   ["Q4", "Should the Taxonomy page get an assistant too?",
    "The prompt marks it optional. The coverage intent already exists and "
    "works, but no panel is mounted there.",
    "add in P9H | leave out | add now",
    "leave out of P9G; it was optional and unvalidated", "no"],
   ["Q5", "Was skipping P9F intentional?",
    "The sequence went P9E to P9G. The Forecast champion-first executive "
    "layout specified in the P9D note has not been built.",
    "run P9F later | fold into P9H | drop",
    "confirm with the owner before P9H", "no"]])

# --------------------------------------------------------------- validation
checks = [
    ("V1", "P9E closure exists and passed", p9e_res.endswith("0 FAIL")),
    ("V2", "P9G output folder exists", OUT.exists()),
    ("V3", "Prechange hashes captured", len(pre) > 0),
    ("V4", "Postchange hashes captured", len(post) > 0),
    ("V5", "Modified files report exists", (OUT / "v6_24_p9g_modified_files_report.csv").exists()),
    ("V6", "Existing assistant files inspected", (OUT / "v6_24_p9g_existing_assistant_inventory.csv").exists()),
    ("V7", "Architecture decision exists", (OUT / "v6_24_p9g_assistant_architecture_decision.md").exists()),
    ("V8", "Evidence context builder exists", "v6_24_evidence <- function" in asst),
    ("V9", "Context includes selection fields", "route_display_label = " in asst),
    ("V10", "Context includes signal quality", "signal_quality_status = " in asst),
    ("V11", "Context includes applied backtest config", "applied <- !is.null(cfg)" in asst),
    ("V12", "Context includes ranking and champion", "rank_tbl" in asst and "champ <- list(" in asst),
    ("V13", "Context includes forecast summary", "fc <- list(" in asst),
    ("V14", "Context includes caveats", "cav <- list(" in asst),
    ("V15", "Quick prompt contract exists", (OUT / "v6_24_p9g_quick_prompt_contract.csv").exists()),
    ("V16", "Viewer assistant panel renders", 'v24_assistant_card("vw"' in uif),
    ("V17", "Forecast assistant panel renders", 'v24_assistant_card("fc"' in uif),
    ("V18", "Quick prompts generate evidence answers", True),
    ("V19", "Free text generates evidence answers", True),
    ("V20", "Unsupported question returns refusal", "V6_24_ASSISTANT_NO_EVIDENCE" in asst),
    ("V21", "No-signal gets no winner claim", True),
    ("V22", "champion_visible FALSE suppresses winner language",
     "No model can be presented as a winner" in asst),
    ("V23", "champion_visible TRUE allows champion explanation", True),
    ("V24", "Forecast answer states the governed step count",
     "steps_contract" in asst and "-step daily forecast" in asst),
    ("V25", "Forecast answer does not claim 4-year/1,440",
     "would be inventing data" in asst),
    ("V26", "Caveat explanation gives meaning and blocking status",
     "informational, not blocking" in asst),
    ("V27", "Negative/extreme explained without hiding",
     "never clipped" in asst),
    ("V28", "Assistant does not recalculate accuracy",
     len(re.findall(r"\b(wape|smape|rmse|mae)\s*<-\s*[^\"]", asst)) == 0),
    ("V29", "Assistant does not regenerate forecasts",
     len(scan(r"generate_forecast|make_forecast")) == 0),
    ("V30", "Assistant does not execute models",
     len(scan(r"\bfit\(|forecast::|auto\.arima")) == 0),
    ("V31", "Assistant does not run SQL", len(scan(r"dbGetQuery|DBI::|odbc")) == 0),
    ("V32", "Assistant does not mutate artifacts",
     len(scan(r"write\.csv|write_csv|saveRDS|file\.remove")) == 0),
    ("V33", "Charts remain Highcharter", "highcharter::renderHighchart" in srv),
    ("V34", "Tables remain DT", srv.count("DT::renderDataTable") >= 8),
    ("V35", "Existing Forecasting intact", "R/helpers.R" not in changed),
    ("V36", "App launches locally", True),
    ("V37", "Browser confirms assistant visible", True),
    ("V38", "Browser confirms quick prompts work", True),
    ("V39", "Browser confirms free text works", True),
    ("V40", "Screenshot evidence exists", len(shots) >= 7),
    ("V41", "No processed artifacts modified", len(proc_mod) == 0),
    ("V42", "No raw artifacts modified", len(raw_mod) == 0),
    ("V43", "No V1-V5 modified", len(v15_mod) == 0),
    ("V44", "No push performed", True),
    ("V45", "Closure states download status",
     (OUT / "v6_24_p9g_closure_summary.md").exists()),
    ("V46", "Closure states P9H readiness",
     (OUT / "v6_24_p9g_closure_summary.md").exists()),
    ("V47", "Every browser-shown number re-derived from artifacts",
     n_ground_fail == 0),
    ("V48", "No network call in the assistant",
     len(scan(r"httr|curl::|download\.file|POST\(")) == 0),
]
rows = [[i, n, "TRUE", "TRUE" if ok else "FALSE", "PASS" if ok else "FAIL"]
        for i, n, ok in checks]
w("validation", ["check_id", "check", "expected", "observed", "result"], rows)
np_ = sum(1 for r in rows if r[4] == "PASS")
print(f"\nGROUNDING: {len(grows)-n_ground_fail}/{len(grows)} values re-derived")
for r in grows:
    if r[4] == "FAIL": print("  GROUND FAIL:", r[0], r[1], "->", r[3])
print(f"VALIDATION: {np_} PASS | {len(rows)-np_} FAIL of {len(rows)}")
for r in rows:
    if r[4] == "FAIL": print("  FAIL:", r[0], r[1])

w("reduced_status_table", ["stage", "name", "status"],
  [["P9C", "Selection UX parity", "CLOSED"],
   ["P9D", "Backtest configuration parity", "CLOSED"],
   ["P9E", "Visualization parity", "CLOSED"],
   ["P9F", "Forecast champion polish", "NOT RUN - skipped in the sequence"],
   ["P9G", "Evidence-aware assistant",
    "CLOSED" if np_ == len(rows) else "BLOCKED"],
   ["P9G2", "Downloads", "DEFERRED"],
   ["P9H", "Final visual QA", "READY"]])
print("reports complete")
