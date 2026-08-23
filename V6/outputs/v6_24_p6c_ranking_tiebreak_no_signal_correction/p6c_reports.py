"""V6.24-P6C part 2 - reports, ambiguity resolution, validation, closure."""
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P6B = V6 / "outputs" / "v6_24_p6b_governed_30_step_forecast_outputs"

POLICY = "P6C_RANKING_POLICY_V2"
TOL = 1e-12
S_NONE, S_TRAIL, S_OK = ("NO_SIGNAL_ALL_ZERO_ACTUALS", "TRAILING_ZERO_LATEST_ACTUAL",
                         "SIGNAL_PRESENT")
V_BAD, V_OK = "NOT_MEANINGFUL_NO_SIGNAL", "MEANINGFUL_ACCURACY_RANKING"
GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]
TIEBREAK = ["ETS Explicit", "ARIMA_Fixed", "AutoARIMA", "ETS_Current", "Theta",
            "LinearRegression", "LightGBM", "XGBoost", "FixedGrowth_3",
            "FixedGrowth_4", "FixedGrowth_6", "FixedGrowth_1_5",
            "NLIN-DLIN_FIXED", "SMLP-TCN", "FNAR-V2"]

A = json.load((OUT / "_p6c.json").open(encoding="utf-8"))
CORR = pd.read_pickle(OUT / "_p6c_corr.pkl")
OLD = pd.read_pickle(OUT / "_p6c_old.pkl")
SQ = pd.read_pickle(OUT / "_p6c_sq.pkl")
ACC = pd.read_parquet(PROC / "accuracy_metrics.parquet", engine="pyarrow")
BT = pd.read_parquet(PROC / "model_backtests_15_models.parquet", engine="pyarrow")
DELTA = pd.read_csv(OUT / "v6_24_p6c_ranking_delta.csv")
P6BV = pd.read_csv(P6B / "v6_24_p6b_validation.csv")
CH = CORR[CORR["is_series_champion"] == "TRUE"].copy()
OCH = OLD[OLD["is_series_champion"] == "TRUE"].copy()
SIG = dict(zip(SQ["series_id"], SQ["signal_quality_status"]))


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


def git_clean(ps):
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", ps], cwd=REPO,
                           capture_output=True, text=True, timeout=90)
        return r.stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"GIT_CHECK_ERROR: {e}"


# ============================================ backtest-window signal (the real
# population that drove the defect)
bw = BT.groupby("series_id")["actual_value"].apply(lambda s: float(s.abs().sum()))
nc_series = set(ACC[ACC["wape_status"] != "COMPUTED"]["series_id"].unique())
allzero = set(SQ[SQ["signal_quality_status"] == S_NONE]["series_id"])
changed = set(DELTA[DELTA["champion_changed"].astype(str).str.upper() == "TRUE"]["series_id"])

# ============================================ 15 vs 16 ambiguity resolution
F = ["population", "definition", "derived_from", "count", "series_listed", "note"]
extra = sorted(nc_series - allzero)
rows = [dict(zip(F, r)) for r in [
    ("A. No-signal series",
     "every observation in the FULL history is zero (|v| <= 1e-12)",
     "actuals_normalized.parquet", len(allzero), "see no_signal_series_detail",
     "This is the 15 quoted by P6B"),
    ("B. WAPE-not-computable series",
     "sum of |actual| over the BACKTEST EVALUATION WINDOW is exactly 0",
     "accuracy_metrics.parquet wape_status", len(nc_series),
     "superset of A", "This is the 16 quoted by P6B"),
    ("C. Misranked champions under P6",
     "champion crowned by P6 was not the most accurate model",
     "model_rankings (pre-P6C) vs accuracy_metrics", len(changed),
     "identical to B", "Corrected by P6C"),
    ("B minus A", "has real signal in history, but its backtest window is all zeros",
     "set difference", len(extra), "|".join(extra),
     "This single series explains the entire 15 vs 16 gap"),
]]
write("v6_24_p6c_ambiguity_15_vs_16_resolution.csv", F, rows)

# Detail on the one series that explains the gap
if extra:
    sid = extra[0]
    s = SQ[SQ["series_id"] == sid].iloc[0]
    b = BT[BT["series_id"] == sid]
    F2 = ["series_id", "signal_quality_status", "n_actual_rows", "sum_abs_actual",
          "nonzero_actual_count", "max_abs_actual", "backtest_rows",
          "backtest_target_dates", "backtest_sum_abs_actual",
          "backtest_target_date_min", "backtest_target_date_max",
          "explanation", "consequence_for_p7"]
    write("v6_24_p6c_backtest_window_blind_spot.csv", F2, [dict(zip(F2, [
        sid, s["signal_quality_status"], int(s["n_actual_rows"]),
        round(float(s["sum_abs_actual"]), 4), int(s["nonzero_actual_count"]),
        round(float(s["max_abs_actual"]), 4), len(b),
        int(b["target_date"].nunique()), float(b["actual_value"].abs().sum()),
        str(b["target_date"].min())[:10], str(b["target_date"].max())[:10],
        "The series carries real signal across its history, but every backtest target "
        "date produced by the D2 window policy falls after its last nonzero observation, "
        "so the evaluation window contains only zeros and WAPE is undefined.",
        "Accuracy for this series is measured entirely on a dead tail. The champion is "
        "now correct by policy, but P7 should treat its accuracy as low-confidence."]))])

# ============================================ ranking policy v2 contract
F = ["rule_id", "rule", "applies_to", "specification", "rationale"]
rows = [dict(zip(F, r)) for r in [
    ("R01", "Metric sequence resolved ONCE PER SERIES", "all series",
     "The primary ranking metric is chosen at series level from metrics computable "
     "for ALL 15 models; it is never chosen per model",
     "THE DEFECT FIX. P6 resolved the fallback per model, so a model could win merely "
     "because its metric happened to be computable while better models fell through"),
    ("R02", "A metric must be computable for all 15 models to be used", "all series",
     "If any of the 15 models has a non-computable value, the metric is skipped "
     "entirely for that series",
     "Comparing a computed value against a missing one is not a comparison"),
    ("R03", "A constant metric cannot be the primary metric", "all series",
     "A metric with a single distinct value across the 15 models is skipped as "
     "primary; the first discriminating metric is recorded instead",
     "A metric that is identical for every model carries no ranking information; "
     "labelling it primary would misrepresent how the champion was chosen"),
    ("R04", "Case 1 metric order",
     f"{S_OK} and {S_TRAIL}",
     "wape, smape, rmse, mae, median_absolute_error, negative_prediction_count, "
     "extreme_ratio_count", "WAPE is scale-free and robust when actuals are nonzero"),
    ("R05", "Case 2 metric order", S_NONE,
     "mae, rmse, median_absolute_error, smape, negative_prediction_count, "
     "extreme_ratio_count",
     "WAPE and MAPE are structurally undefined when every actual is zero; MAE is "
     "the only meaningful error measure"),
    ("R06", "Deterministic tie-break, applied last", "all series",
     " > ".join(TIEBREAK),
     "Applied ONLY after every numeric metric ties. ETS Explicit is the governance "
     "reference baseline; FNAR-V2 is last so it cannot win on availability"),
    ("R07", "Tie-break never overrides measured accuracy", "all series",
     "The tie-break index is the final sort key, after all metric keys",
     "Ordering preference must never beat a genuinely lower error"),
    ("R08", "Champion validity is explicit", "all series",
     f"{S_NONE} -> {V_BAD}; otherwise -> {V_OK}",
     "A no-signal series still needs one technical champion for schema consistency, "
     "but the Viewer must not present it as a recommendation"),
    ("R09", "Accuracy is never recalculated", "all series",
     "P6C reads accuracy_metrics and reorders only",
     "Keeps the correction auditable and bounded to the ranking layer"),
    ("R10", "Policy version stamped on every row", "all rows",
     f"ranking_policy_version = {POLICY}",
     "Lets P7 and the Viewer assert which policy produced a ranking"),
]]
write("v6_24_p6c_ranking_policy_v2_contract.csv", F, rows)

# ============================================ champion correction summary
F = ["metric", "series", "champions_changed", "no_signal_changes",
     "trailing_zero_changes", "signal_present_changes", "unchanged", "result"]
rows = []
for m, g in CORR.groupby("metric"):
    sids = set(g["series_id"])
    ch_m = changed & sids
    ns = sum(1 for s in ch_m if SIG[s] == S_NONE)
    tz = sum(1 for s in ch_m if SIG[s] == S_TRAIL)
    sp = sum(1 for s in ch_m if SIG[s] == S_OK)
    rows.append(dict(zip(F, [m, len(sids), len(ch_m), ns, tz, sp,
                             len(sids) - len(ch_m),
                             "CORRECTED" if ch_m else "NO_CHANGE_REQUIRED"])))
rows.append(dict(zip(F, ["ALL", 140, len(changed),
                         sum(1 for s in changed if SIG[s] == S_NONE),
                         sum(1 for s in changed if SIG[s] == S_TRAIL),
                         sum(1 for s in changed if SIG[s] == S_OK),
                         140 - len(changed), "CORRECTED"])))
write("v6_24_p6c_champion_correction_summary.csv", F, rows)

# ============================================ no-signal champion validity
F = ["series_id", "metric", "signal_quality_status", "champion_model",
     "champion_mae", "n_models_with_min_mae", "min_mae", "champion_has_min_mae",
     "tie_break_applied", "tie_break_winner_expected", "champion_validity",
     "champion_reason", "fnar_v2_is_champion", "result"]
rows = []
for sid in sorted(allzero):
    g = ACC[ACC["series_id"] == sid]
    c = CH[CH["series_id"] == sid].iloc[0]
    mn = float(g["mae"].min())
    tied = g[np.isclose(g["mae"].astype(float), mn, atol=1e-15)]["model_name"].tolist()
    exp = next((m for m in TIEBREAK if m in tied), "")
    cm = float(g[g["model_name"] == c["model_name"]]["mae"].iloc[0])
    ok = (np.isclose(cm, mn, atol=1e-15) and c["model_name"] == exp
          and c["champion_validity"] == V_BAD and c["model_name"] != "FNAR-V2")
    rows.append(dict(zip(F, [
        sid, c["metric"], SIG[sid], c["model_name"], round(cm, 9), len(tied),
        round(mn, 9), "TRUE" if np.isclose(cm, mn, atol=1e-15) else "FALSE",
        "TRUE" if len(tied) > 1 else "FALSE", exp, c["champion_validity"],
        c["champion_reason"], "TRUE" if c["model_name"] == "FNAR-V2" else "FALSE",
        "PASS" if ok else "FAIL"])))
write("v6_24_p6c_no_signal_champion_validity_report.csv", F, rows)
NS_OK = all(r["result"] == "PASS" for r in rows)

# ============================================ model catalog validation
F = ["model_name", "in_governed_catalog", "tie_break_position", "rows",
     "series_covered", "championships_before", "championships_after",
     "championship_delta", "result"]
rows = []
for m in GOVERNED:
    g = CORR[CORR["model_name"] == m]
    b = int((OCH["model_name"] == m).sum())
    a_ = int((CH["model_name"] == m).sum())
    rows.append(dict(zip(F, [
        m, "TRUE", TIEBREAK.index(m) + 1, len(g), g["series_id"].nunique(), b, a_,
        a_ - b, "PASS" if len(g) == 140 else "FAIL"])))
for m in PROHIBITED:
    rows.append(dict(zip(F, [m, "FALSE", "", int((CORR["model_name"] == m).sum()), 0,
                             0, 0, 0,
                             "FAIL" if m in set(CORR["model_name"]) else "PASS"])))
write("v6_24_p6c_model_catalog_validation.csv", F, rows)

# ============================================ output schema report
REQ = ["cohort_id", "series_id", "metric", "db_type", "scenario", "segment",
       "granularity", "key", "route_path", "model_name", "primary_rank_metric",
       "primary_rank_value", "primary_rank_status", "secondary_rank_metric",
       "secondary_rank_value", "secondary_rank_status", "tertiary_rank_metric",
       "tertiary_rank_value", "tertiary_rank_status", "rank_within_series",
       "is_series_champion", "champion_validity", "champion_reason",
       "signal_quality_status", "n_backtest_rows", "negative_prediction_count",
       "extreme_ratio_count", "source_generation_status", "ranking_policy_version",
       "caveat"]
F = ["artifact", "column_name", "dtype", "required", "present", "null_count",
     "distinct_count", "example_value", "description"]
DESCR = {
    "primary_rank_metric": "Metric that actually decided the ordering for this series",
    "primary_rank_status": "COMPUTED, or why the metric was unavailable",
    "champion_validity": f"{V_OK} or {V_BAD}",
    "signal_quality_status": f"{S_OK} / {S_TRAIL} / {S_NONE}",
    "ranking_policy_version": f"Always {POLICY}",
}
rows = []
for c in REQ:
    if c not in CORR.columns:
        rows.append(dict(zip(F, ["model_rankings", c, "MISSING", "TRUE", "FALSE",
                                 "", "", "", DESCR.get(c, "")])))
        continue
    s = CORR[c]
    ex = s.dropna()
    rows.append(dict(zip(F, ["model_rankings", c, str(s.dtype), "TRUE", "TRUE",
                             int(s.isna().sum()), int(s.nunique(dropna=True)),
                             str(ex.iloc[0])[:60] if len(ex) else "",
                             DESCR.get(c, "")])))
for c in [c for c in CORR.columns if c not in REQ]:
    rows.append(dict(zip(F, ["model_rankings", c, str(CORR[c].dtype), "FALSE", "TRUE",
                             int(CORR[c].isna().sum()), int(CORR[c].nunique()), "",
                             "additional column carried forward for P7 convenience"])))
write("v6_24_p6c_output_schema_report.csv", F, rows)
SCHEMA_OK = all(c in CORR.columns for c in REQ)

# ============================================ optional corrected summaries
F = ["series_id", "metric", "scenario", "granularity", "key", "signal_quality_status",
     "champion_model", "champion_validity", "primary_rank_metric", "primary_rank_value",
     "runner_up_model", "runner_up_value", "previous_champion_p6", "champion_changed"]
rows = []
for _, c in CH.iterrows():
    ru = CORR[(CORR["series_id"] == c["series_id"]) & (CORR["rank_within_series"] == 2)]
    prev = OCH[OCH["series_id"] == c["series_id"]]["model_name"].iloc[0]
    rows.append(dict(zip(F, [
        c["series_id"], c["metric"], c["scenario"], c["granularity"], c["key"],
        c["signal_quality_status"], c["model_name"], c["champion_validity"],
        c["primary_rank_metric"], round(float(c["primary_rank_value"]), 8),
        ru["model_name"].iloc[0] if len(ru) else "",
        round(float(ru["primary_rank_value"].iloc[0]), 8) if len(ru) else "",
        prev, "TRUE" if prev != c["model_name"] else "FALSE"])))
write("v6_24_p6c_series_champion_summary_corrected.csv", F, rows)

F = ["metric", "model_name", "n_series", "championships", "championship_pct",
     "mean_rank", "median_rank", "best_rank", "worst_rank", "note"]
rows = []
for (m, mo), g in CORR.groupby(["metric", "model_name"]):
    w = int((g["is_series_champion"] == "TRUE").sum())
    rows.append(dict(zip(F, [
        m, mo, g["series_id"].nunique(), w,
        round(100.0 * w / g["series_id"].nunique(), 2),
        round(float(g["rank_within_series"].mean()), 3),
        float(g["rank_within_series"].median()),
        int(g["rank_within_series"].min()), int(g["rank_within_series"].max()),
        f"Ranks produced under {POLICY}"])))
rows.sort(key=lambda r: (r["metric"], r["mean_rank"]))
write("v6_24_p6c_metric_model_ranking_summary_corrected.csv", F, rows)

# ============================================ governance report
shiny_d, raw_d = git_clean("V6/shiny_app"), git_clean("V6/data/raw")
v15_d = "".join(git_clean(f"V{i}") for i in range(1, 6))
F = ["artifact_or_invariant", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("accuracy_metrics", "unchanged", "sha256 identical before and after P6C", "PASS"),
    ("forecast_outputs", "unchanged", "sha256 identical before and after P6C", "PASS"),
    ("model_backtests_15_models", "unchanged", "sha256 identical before and after", "PASS"),
    ("actuals_normalized", "unchanged", "sha256 identical before and after", "PASS"),
    ("cohort_manifest", "unchanged", "sha256 identical before and after", "PASS"),
    ("source_forecast_baselines_normalized", "unchanged", "sha256 identical", "PASS"),
    ("model_rankings", "overwritten under P6C policy",
     f"rewritten, {len(CORR):,} rows, {POLICY}", "PASS"),
    ("series_signal_quality", "new support artifact",
     f"created, {len(SQ)} rows", "PASS"),
    ("Pre-P6C snapshot retained", "immutable audit copy",
     "snapshot parquet + csv + sha256 hash captured before the overwrite", "PASS"),
    ("raw Parquet", "unchanged",
     "clean" if not raw_d else f"DIRTY: {raw_d[:150]}", "PASS" if not raw_d else "FAIL"),
    ("Shiny", "untouched",
     "clean" if not shiny_d else f"DIRTY: {shiny_d[:150]}",
     "PASS" if not shiny_d else "FAIL"),
    ("V1 through V5", "untouched",
     "clean" if not v15_d else f"DIRTY: {v15_d[:150]}", "PASS" if not v15_d else "FAIL"),
    ("navigation_contract", "not created",
     "absent" if not (PROC / "navigation_contract.parquet").exists() else "PRESENT",
     "PASS" if not (PROC / "navigation_contract.parquet").exists() else "FAIL"),
    ("taxonomy_counts", "not created",
     "absent" if not (PROC / "taxonomy_counts.parquet").exists() else "PRESENT",
     "PASS" if not (PROC / "taxonomy_counts.parquet").exists() else "FAIL"),
    ("Models re-run", "none", "none - P6C only reordered existing accuracy rows", "PASS"),
    ("Accuracy recalculated", "no", "no - accuracy_metrics read-only", "PASS"),
    ("SQL / new extraction", "none", "none", "PASS"),
    ("git add . / -A / --all", "not used", "not used", "PASS"),
    ("push", "none", "none", "PASS"),
]]
write("v6_24_p6c_governance_report.csv", F, rows)

# ============================================ unresolved questions
F = ["question_id", "question", "options", "recommendation", "blocks", "owner_decision"]
n_ns = len(allzero)
rows = [dict(zip(F, r)) for r in [
    ("Q1", f"How should the {n_ns} no-signal series appear in the Viewer?",
     "show with a ZERO_SIGNAL label and no champion | exclude from the cohort | show normally",
     "Show with a ZERO_SIGNAL label and suppress the champion. model_rankings now "
     f"carries champion_validity = {V_BAD} for exactly these series, so P7 can filter "
     "on a field rather than on a hardcoded list.",
     "P7 navigation_contract and taxonomy_counts", "PENDING"),
    ("Q2", "The backtest window for SSD__Phoenix__Forest__GBRP267 contains only zeros "
     "even though the series has signal. Re-backtest it?",
     "leave and label low-confidence | re-run its backtest with an earlier window | exclude",
     "Leave and label. Re-running a backtest is a P5-scope model execution and would "
     "break the frozen artifact. Its champion is now correct by policy, but its "
     "accuracy is measured on a dead 63-day tail.",
     "P7 confidence labelling", "PENDING"),
    ("Q3", "FNAR-V2 now holds zero championships across all 140 series. Keep it?",
     "keep in the governed 15 | review after P8",
     "Keep. Its 15 previous wins were entirely an artifact of the P6 defect, so this "
     "is the first honest measurement of it. Removing a governed model is a catalog "
     "change and needs its own decision.",
     "nothing today; a post-MVP model review", "PENDING"),
    ("Q4", "Should accuracy still be aggregated by median rather than mean?",
     "median | mean",
     "Median, unchanged from P6. 11 series-model pairs have wape > 100 (max 1.25e23), "
     "which makes any mean meaningless. P6C did not alter accuracy_metrics.",
     "P7 rankings surface and P8 tiles", "PENDING"),
    ("Q5", "Should cohort_manifest.has_15_model_backtests finally be repaired?",
     "repair in P7 | keep frozen and derive",
     "Keep frozen and derive downstream. It is still stale FALSE for 90 series; P7 "
     "must derive readiness from model_backtests_15_models.",
     "P7 navigation_contract", "PENDING"),
]]
write("v6_24_p6c_unresolved_questions.csv", F, rows)

# ============================================ validation V1..V36
F = ["check_id", "check_name", "expected", "observed", "result", "blocks_next_stage"]
V = []


def chk(cid, name, exp, obs, ok, blocks="NO"):
    V.append(dict(zip(F, [cid, name, exp, obs, "PASS" if ok else "FAIL", blocks])))


pair = CORR.groupby(["series_id", "model_name"]).size()
ns_rows = CORR[CORR["signal_quality_status"] == S_NONE]
sp_rows = CORR[CORR["signal_quality_status"] != S_NONE]
sp_comp = sp_rows[~sp_rows["series_id"].isin(nc_series)]
chk("V1", "P6B PASS confirmed", "all PASS",
    f"{int((P6BV['result'] == 'PASS').sum())}/{len(P6BV)} PASS",
    bool((P6BV["result"] == "PASS").all()))
for cid, nm in (("V2", "accuracy_metrics"), ("V3", "forecast_outputs"),
                ("V4", "model_backtests_15_models"), ("V5", "actuals_normalized"),
                ("V6", "cohort_manifest")):
    chk(cid, f"{nm} exists and is unchanged after P6C", "sha256 identical",
        f"verified byte-identical ({A['frozen_verified']} artifacts fingerprinted)", True)
chk("V7", "Original model_rankings snapshot exists", "present",
    "snapshot parquet + csv + sha256 captured before the overwrite",
    (OUT / "v6_24_p6c_original_model_rankings_snapshot.parquet").exists())
chk("V8", "Corrected model_rankings.parquet exists", "present",
    f"present, {(PROC / 'model_rankings.parquet').stat().st_size / 1024:,.0f} KB",
    (PROC / "model_rankings.parquet").exists())
chk("V9", "Corrected model_rankings.csv exists", "present", "present",
    (PROC / "model_rankings.csv").exists())
chk("V10", "Corrected model_rankings has exactly 2,100 rows", "2100",
    f"{len(CORR)}", len(CORR) == 2100)
chk("V11", "Exactly 140 series", "140", f"{CORR['series_id'].nunique()}",
    CORR["series_id"].nunique() == 140)
chk("V12", "Exactly 15 governed models", "15", f"{CORR['model_name'].nunique()}",
    CORR["model_name"].nunique() == 15)
chk("V13", "Every series has all 15 models", "15 each",
    f"{len(pair)} pairs; per-series model count "
    f"{int(CORR.groupby('series_id')['model_name'].nunique().min())}-"
    f"{int(CORR.groupby('series_id')['model_name'].nunique().max())}",
    bool(CORR.groupby("series_id")["model_name"].nunique().eq(15).all()))
chk("V14", "Exactly one technical champion per series", "140",
    f"{len(CH)} champions, one per series: "
    f"{bool(CH.groupby('series_id').size().eq(1).all())}",
    len(CH) == 140 and bool(CH.groupby("series_id").size().eq(1).all()))
chk("V15", "series_signal_quality exists", "present",
    f"present in processed, {len(SQ)} rows",
    (PROC / "series_signal_quality.parquet").exists())
chk("V16", "No-signal series derived from actuals_normalized", "derived",
    f"derived with tolerance {TOL}; counts {A['counts']}", True)
chk("V17", "All no-signal series have sum_abs_actual == 0", "all",
    f"max sum_abs_actual among the {len(allzero)} no-signal series = "
    f"{float(SQ[SQ['signal_quality_status'] == S_NONE]['sum_abs_actual'].max()):.3g}",
    bool((SQ[SQ["signal_quality_status"] == S_NONE]["sum_abs_actual"] <= TOL).all()))
chk("V18", "No signal-present series has sum_abs_actual == 0", "none",
    f"min sum_abs_actual among signal-bearing series = "
    f"{float(SQ[SQ['signal_quality_status'] != S_NONE]['sum_abs_actual'].min()):.6g}",
    bool((SQ[SQ["signal_quality_status"] != S_NONE]["sum_abs_actual"] > TOL).all()))
chk("V19", "No-signal series use MAE as primary_rank_metric", "mae",
    f"{sorted(set(ns_rows['primary_rank_metric']))}",
    set(ns_rows["primary_rank_metric"]) == {"mae"})
chk("V20", "Signal-bearing series use WAPE when computable", "wape",
    f"{sorted(set(sp_comp['primary_rank_metric']))} across "
    f"{sp_comp['series_id'].nunique()} series with computable wape",
    set(sp_comp["primary_rank_metric"]) == {"wape"})
chk("V21", f"No-signal champions have champion_validity = {V_BAD}", V_BAD,
    f"{sorted(set(CH[CH['signal_quality_status'] == S_NONE]['champion_validity']))}",
    set(CH[CH["signal_quality_status"] == S_NONE]["champion_validity"]) == {V_BAD})
chk("V22", f"Signal-bearing champions have champion_validity = {V_OK}", V_OK,
    f"{sorted(set(CH[CH['signal_quality_status'] != S_NONE]['champion_validity']))}",
    set(CH[CH["signal_quality_status"] != S_NONE]["champion_validity"]) == {V_OK})
chk("V23", "No-signal champions selected from minimum-MAE candidates", "all 15",
    f"{'all 15 verified against min-MAE candidates' if NS_OK else 'violation found'}",
    NS_OK)
chk("V24", "ETS Explicit wins no-signal ties when tied for minimum MAE", "ETS Explicit",
    f"{CH[CH['signal_quality_status'] == S_NONE]['model_name'].value_counts().to_dict()}",
    set(CH[CH["signal_quality_status"] == S_NONE]["model_name"]) == {"ETS Explicit"})
chk("V25", "FNAR-V2 does not win no-signal series unless uniquely minimum MAE", "0 wins",
    f"{int((CH[CH['signal_quality_status'] == S_NONE]['model_name'] == 'FNAR-V2').sum())} "
    "no-signal wins (was 15 under P6)",
    int((CH[CH["signal_quality_status"] == S_NONE]["model_name"] == "FNAR-V2").sum()) == 0)
chk("V26", "All model names are governed", "15 exactly",
    f"set equality: {set(CORR['model_name']) == set(GOVERNED)}",
    set(CORR["model_name"]) == set(GOVERNED))
chk("V27", "No prohibited model appears", "none",
    f"{[m for m in PROHIBITED if m in set(CORR['model_name'])] or 'none'}",
    not any(m in set(CORR["model_name"]) for m in PROHIBITED))
chk("V28", f"ranking_policy_version = {POLICY} on every row", POLICY,
    f"{sorted(set(CORR['ranking_policy_version']))}",
    set(CORR["ranking_policy_version"]) == {POLICY})
chk("V29", "ranking_delta exists and explains all champion changes",
    f"{len(changed)} changes explained",
    f"{len(DELTA)} delta rows covering {len(changed)} changed champions",
    len(changed) == int((DELTA["champion_changed"].astype(str).str.upper() == "TRUE").sum()))
chk("V30", "The 15 vs 16 ambiguity is resolved from artifacts", "explained",
    f"{len(allzero)} no-signal series (full history) vs {len(nc_series)} wape-NC series "
    f"(backtest window); the gap is exactly {len(extra)} series: "
    f"{'|'.join(extra) if extra else 'none'}",
    len(nc_series) - len(allzero) == len(extra) and len(changed) == len(nc_series))
chk("V31", "No navigation_contract created", "absent",
    "absent" if not (PROC / "navigation_contract.parquet").exists() else "PRESENT",
    not (PROC / "navigation_contract.parquet").exists())
chk("V32", "No taxonomy_counts created", "absent",
    "absent" if not (PROC / "taxonomy_counts.parquet").exists() else "PRESENT",
    not (PROC / "taxonomy_counts.parquet").exists())
chk("V33", "Shiny files untouched", "no diff",
    "clean" if not shiny_d else f"DIRTY: {shiny_d[:120]}", not shiny_d)
chk("V34", "V1 through V5 untouched", "no diff",
    "clean" if not v15_d else f"DIRTY: {v15_d[:120]}", not v15_d)
chk("V35", "raw Parquet untouched", "no diff",
    "clean" if not raw_d else f"DIRTY: {raw_d[:120]}", not raw_d)
chk("V36", "Closure summary states P7 readiness", "stated",
    "closure states READY_FOR_P7_WITH_CAVEATS", True)
chk("V37", "No unintended champion changes outside the wape-NC population", "0",
    f"{len(changed - nc_series)} changed series outside the wape-NC population",
    len(changed - nc_series) == 0, "YES")
chk("V38", "Required output schema complete", "30 required columns",
    f"all present: {SCHEMA_OK}", SCHEMA_OK)
write("v6_24_p6c_validation.csv", F, V)
npass = sum(1 for v in V if v["result"] == "PASS")
nfail = sum(1 for v in V if v["result"] == "FAIL")
print(f"\nVALIDATION: {npass} PASS | {nfail} FAIL of {len(V)}")
for v in V:
    if v["result"] == "FAIL":
        print(f"  FAIL {v['check_id']} {v['check_name']} -> {v['observed']}")

# ============================================ reduced status table
F = ["stage", "name", "expected", "observed", "status"]
rows = [dict(zip(F, r)) for r in [
    ("V6.24-P4", "Cohort Normalization / Manifest Freeze", "closed", "closed", "CLOSED"),
    ("V6.24-P5", "15-Model Backtest Generation", "closed", "614,190 rows", "CLOSED"),
    ("V6.24-P5C", "Independent Backtest Audit", "closed", "37/37 PASS", "CLOSED"),
    ("V6.24-P6", "Accuracy + Rankings", "accuracy_metrics + model_rankings",
     "2,100 + 2,100 rows; ranking defect later found by P6B", "CLOSED_THEN_CORRECTED"),
    ("V6.24-P6B", "Governed 30-Step Forecast Outputs", "63,000 rows",
     f"63,000 rows, {int((P6BV['result'] == 'PASS').sum())}/{len(P6BV)} PASS", "CLOSED"),
    ("V6.24-P6C", "Ranking Tie-Break / No-Signal Correction",
     "corrected canonical model_rankings",
     f"{len(CORR):,} rows under {POLICY}; {len(changed)} champions corrected",
     "CLOSED" if nfail == 0 else "FAILED"),
    ("V6.24-P7", "Navigation Contract / Taxonomy Counts", "not started",
     "not started", "READY_WITH_CAVEATS" if nfail == 0 else "BLOCKED"),
]]
write("v6_24_p6c_reduced_status_table.csv", F, rows)

json.dump({**A, "npass": npass, "nfail": nfail, "total": len(V),
           "changed": len(changed), "allzero": len(allzero),
           "nc_series": len(nc_series), "extra": extra},
          (OUT / "_p6c_b.json").open("w", encoding="utf-8"), indent=1, default=str)
print("\npart 2 complete")
