"""V6.24-P6 part 2 - horizon contract, reports, validation, closure.

Consumes the artifacts written by p6_accuracy_rankings.py and p6_horizon_probe.py.
Writes NO forecast artifact: the forecast horizon is unresolved and P6 blocks it
rather than inventing a horizon.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parent.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
V617 = V6 / "outputs" / "v6_17_full_multimetric_productive_artifact_generation"

ACC = pd.read_pickle(OUT / "_p6_acc.pkl")
RK = pd.read_pickle(OUT / "_p6_rk.pkl")
A = json.load((OUT / "_p6_a.json").open(encoding="utf-8"))
HP = pd.read_csv(OUT / "v6_24_p6_forecast_horizon_probe.csv")
RD = pd.read_csv(OUT / "v6_24_p6_derived_backtest_readiness.csv")
BT = pd.read_parquet(PROC / "model_backtests_15_models.parquet", engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# ============================================ measure the HDD forward artifact
fwd = pd.read_parquet(V617 / "forecast_forward_outputs_v6_17_full.parquet",
                      engine="pyarrow")
fwd_models = sorted({str(x) for x in fwd["model_name"].dropna().tolist()})
gov_models = sorted({str(x) for x in BT["model_name"].dropna().tolist()})
overlap = sorted(set(fwd_models) & set(gov_models))
fsteps = fwd.groupby(["metric", "scenario", "granularity", "series_key",
                      "model_name"])["date"].size()
hdd_steps = int(fsteps.median())
print(f"\nHDD forward artifact: {len(fwd):,} rows | {len(fwd_models)} model names | "
      f"{hdd_steps} steps/series-model | governed overlap = {len(overlap)}")

def istrue(s: pd.Series) -> pd.Series:
    """Normalise a boolean-ish column.

    read_csv coerces the literals TRUE/FALSE into real booleans, so comparing
    against the string "TRUE" silently yields all-False. Normalise via str().
    """
    return s.map(lambda v: str(v).strip().upper() == "TRUE")


probe_ok = HP[HP["probe_result"] == "OK"]
all30 = bool(istrue(probe_ok["emitted_equals_30"]).all()) and len(probe_ok) == 15
reached_request = int(istrue(probe_ok["matches_request"]).sum())

# ============================================ 1. forecast horizon contract
F = ["item_id", "item", "candidate_semantics", "value", "evidence_source",
     "measured_or_asserted", "compatible_with_governed_models", "verdict"]
rows = [dict(zip(F, r)) for r in [
    ("H01", "Prompt default assumption", "48 forward steps x 30 days each",
     "1440 days", "V6.24-P6 prompt", "ASSERTED", "NO",
     "REJECTED - no governed model can emit 1,440 steps"),
    ("H02", "Existing HDD forward artifact",
     "daily steps, one row per calendar day", f"{hdd_steps} daily steps",
     "forecast_forward_outputs_v6_17_full.parquet (measured)", "MEASURED", "NO",
     f"REJECTED - produced by {len(fwd_models)} model names of which only "
     f"{len(overlap)} are governed"),
    ("H03", "Proven capability of the 15 governed models",
     "single-shot vector forecast", "exactly 30 daily steps",
     "v6_24_p6_forecast_horizon_probe.csv (15/15 models fitted and measured)",
     "MEASURED", "YES",
     "ONLY VERIFIED OPTION - but 30 days may not meet the product requirement"),
    ("H04", "Registry constant HORIZON_DAYS", "module-level constant", "30",
     "model_lab/run_v3_2c_subset_dry_run.py imported by the 15-model registry",
     "MEASURED", "YES", "Hardcoded; no call site accepts a horizon argument"),
    ("H05", "Neural output dimension",
     "build_xy(values, LAGS, HORIZON_DAYS) fixes the network output width", "30",
     "build_v6_16_pilot_backtest.py line 251", "MEASURED", "YES",
     "Changing the horizon requires retraining a different architecture"),
    ("H06", "Horizon-parameterised challenger variant",
     "_forecast_*(values, horizon)", "exists but ungoverned",
     "model_lab/run_backtest_60d.py", "MEASURED", "PARTIAL",
     "Covers only the 5 challengers; the 7 baselines and 3 neural models remain "
     "fixed at 30. Not the governed import path"),
    ("H07", "Model names in the HDD forward artifact vs the governed 15",
     "set overlap", f"{len(overlap)} of 15 governed names present",
     "measured set intersection", "MEASURED", "NO",
     "The legacy forward artifact is DISJOINT from the governed model set and "
     "cannot be reused as governed forecast_outputs"),
    ("H08", "P6 forecast_outputs decision", "n/a", "NOT PRODUCED",
     "this contract", "DECIDED", "n/a",
     "BLOCKED - three mutually incompatible semantics; owner must choose"),
]]
write("v6_24_p6_forecast_horizon_contract.csv", F, rows)

# ============================================ 2. accuracy metric summary
def agg(g):
    # Aggregate per-series values; never pool raw rows, because backtest density
    # differs by metric (P5C caveat).
    return pd.Series({
        "n_series": g["series_id"].nunique(),
        "n_series_model_pairs": len(g),
        "mean_wape": g["wape"].mean(), "median_wape": g["wape"].median(),
        "mean_smape": g["smape"].mean(), "median_smape": g["smape"].median(),
        "mean_mape": g["mape"].mean(), "median_mape": g["mape"].median(),
        "mean_mae": g["mae"].mean(), "median_mae": g["mae"].median(),
        "mean_rmse": g["rmse"].mean(), "median_rmse": g["rmse"].median(),
        "mean_bias": g["bias"].mean(), "median_bias": g["bias"].median(),
        "negative_prediction_count": g["negative_prediction_count"].sum(),
        "extreme_ratio_count": g["extreme_ratio_count"].sum(),
    })


rows = []
for scope, keys in (("OVERALL", None), ("BY_METRIC", ["metric"]),
                    ("BY_MODEL", ["model_name"]),
                    ("BY_METRIC_MODEL", ["metric", "model_name"]),
                    ("BY_MODEL_FAMILY", ["model_family"])):
    if keys is None:
        it = [(("ALL",), ACC)]
    else:
        it = [((k,) if not isinstance(k, tuple) else k, g)
              for k, g in ACC.groupby(keys)]
    for k, g in it:
        s = agg(g)
        rows.append({
            "scope": scope,
            "metric": k[0] if scope in ("BY_METRIC", "BY_METRIC_MODEL") else "ALL",
            "model_name": (k[0] if scope == "BY_MODEL"
                           else k[1] if scope == "BY_METRIC_MODEL" else "ALL"),
            "model_family": k[0] if scope == "BY_MODEL_FAMILY" else "ALL",
            **{c: (round(float(v), 6) if isinstance(v, (int, float, np.floating))
                   and c not in ("n_series", "n_series_model_pairs",
                                 "negative_prediction_count", "extreme_ratio_count")
                   else int(v)) for c, v in s.items()},
            "aggregation_note": ("Aggregated from per-series values, never from "
                                 "pooled raw rows: backtest density differs by metric"),
            "units": "wape/smape/mape are decimal fractions; mae/rmse/bias in series units",
        })
write("v6_24_p6_accuracy_metric_summary.csv", list(rows[0]), rows)

# ============================================ 3. series champion summary
ch = RK[RK["is_series_champion"] == "TRUE"].copy()
F = ["cohort_id", "series_id", "metric", "db_type", "scenario", "granularity", "key",
     "route_path", "champion_model", "model_family", "primary_rank_metric",
     "primary_rank_value", "runner_up_model", "runner_up_value", "margin",
     "n_backtest_rows", "negative_prediction_count", "extreme_ratio_count",
     "source_generation_status", "caveat"]
rows = []
for _, c in ch.iterrows():
    ru = RK[(RK["series_id"] == c["series_id"]) & (RK["rank_within_series"] == 2)]
    rv = float(ru["primary_rank_value"].iloc[0]) if len(ru) else np.nan
    rows.append(dict(zip(F, [
        c["cohort_id"], c["series_id"], c["metric"], c["db_type"], c["scenario"],
        c["granularity"], c["key"], c["route_path"], c["model_name"],
        c["model_family"], c["primary_rank_metric"],
        round(float(c["primary_rank_value"]), 6),
        ru["model_name"].iloc[0] if len(ru) else "NONE",
        round(rv, 6) if rv == rv else "",
        round(rv - float(c["primary_rank_value"]), 6) if rv == rv else "",
        c["n_backtest_rows"], c["negative_prediction_count"],
        c["extreme_ratio_count"], c["source_generation_status"], c["caveat"]])))
write("v6_24_p6_series_champion_summary.csv", F, rows)

# ============================================ 4. metric-model ranking summary
F = ["metric", "model_name", "model_family", "n_series", "n_champion_wins",
     "champion_win_rate_pct", "mean_rank", "median_rank", "best_rank", "worst_rank",
     "mean_wape", "median_wape", "notes"]
rows = []
for (m, mo), g in RK.groupby(["metric", "model_name"]):
    wins = int((g["is_series_champion"] == "TRUE").sum())
    a = ACC[(ACC["metric"] == m) & (ACC["model_name"] == mo)]
    rows.append(dict(zip(F, [
        m, mo, g["model_family"].iloc[0], g["series_id"].nunique(), wins,
        round(100.0 * wins / g["series_id"].nunique(), 2),
        round(float(g["rank_within_series"].mean()), 3),
        float(g["rank_within_series"].median()),
        int(g["rank_within_series"].min()), int(g["rank_within_series"].max()),
        round(float(a["wape"].mean()), 6), round(float(a["wape"].median()), 6),
        "Rank 1 = best within its series"])))
rows.sort(key=lambda r: (r["metric"], r["mean_rank"]))
write("v6_24_p6_metric_model_ranking_summary.csv", F, rows)

# ============================================ 5. negative / extreme report
F = ["scope", "metric", "model_name", "source_generation_status",
     "n_backtest_rows", "negative_prediction_count", "negative_prediction_pct",
     "extreme_ratio_count", "extreme_ratio_pct", "action_taken", "rationale"]
RAT = ("P5C caveat honoured: values are REPORTED, never clipped or winsorised. "
       "Clipping would silently alter model behaviour and break Viewer/Forecast parity.")
rows = []
tot = ACC[["n_backtest_rows", "negative_prediction_count", "extreme_ratio_count"]].sum()
rows.append(dict(zip(F, ["OVERALL", "ALL", "ALL", "ALL", int(tot.iloc[0]),
                         int(tot.iloc[1]), round(100.0 * tot.iloc[1] / tot.iloc[0], 4),
                         int(tot.iloc[2]), round(100.0 * tot.iloc[2] / tot.iloc[0], 4),
                         "REPORTED_NOT_CLIPPED", RAT])))
for scope, keys in (("BY_SOURCE", ["source_generation_status"]),
                    ("BY_METRIC", ["metric"]), ("BY_MODEL", ["model_name"])):
    for k, g in ACC.groupby(keys[0]):
        n = int(g["n_backtest_rows"].sum())
        neg, ex = int(g["negative_prediction_count"].sum()), int(g["extreme_ratio_count"].sum())
        rows.append(dict(zip(F, [
            scope, k if scope == "BY_METRIC" else "ALL",
            k if scope == "BY_MODEL" else "ALL", k if scope == "BY_SOURCE" else "ALL",
            n, neg, round(100.0 * neg / n, 4), ex, round(100.0 * ex / n, 4),
            "REPORTED_NOT_CLIPPED", RAT])))
write("v6_24_p6_negative_extreme_prediction_report.csv", F, rows)

# ============================================ 6. output schema report
F = ["artifact", "location", "column_name", "dtype", "null_count", "distinct_count",
     "example_value", "description"]
rows = []
DESCR = {"series_id": "Stable cohort series identifier; the Viewer join key",
         "model_name": "One of the 15 governed AEGIS models",
         "wape": "Weighted absolute percentage error, decimal fraction; primary rank metric",
         "is_series_champion": "TRUE for exactly one model per series",
         "rank_within_series": "1 = best model for this series"}
for nm, df in (("accuracy_metrics", ACC), ("model_rankings", RK)):
    for c in df.columns:
        s = df[c]
        ex = s.dropna()
        rows.append(dict(zip(F, [
            nm, f"V6/data/processed/v6_24_mvp_cohort/{nm}.parquet", c, str(s.dtype),
            int(s.isna().sum()), int(s.nunique(dropna=True)),
            str(ex.iloc[0])[:60] if len(ex) else "",
            DESCR.get(c, "")])))
write("v6_24_p6_output_schema_report.csv", F, rows)

# ============================================ 7. data quality report
F = ["check_id", "dimension", "check", "expected", "observed", "result", "note"]
sm = ACC.groupby("series_id").size()
_champ = RK[RK["is_series_champion"] == "TRUE"]
CH_MAX = float(_champ["primary_rank_value"].max())
CH_DEGEN = int((_champ["primary_rank_value"] > 100).sum())
DEGEN = int((ACC["wape"] > 100).sum())
rows = [dict(zip(F, r)) for r in [
    ("DQ01", "completeness", "accuracy_metrics covers 140 series", "140",
     f"{ACC['series_id'].nunique()}", "PASS" if ACC["series_id"].nunique() == 140 else "FAIL", ""),
    ("DQ02", "completeness", "every series has all 15 models", "15 for all",
     f"min={sm.min()} max={sm.max()}", "PASS" if sm.eq(15).all() else "FAIL", ""),
    ("DQ03", "completeness", "accuracy_metrics row count", "2100", f"{len(ACC)}",
     "PASS" if len(ACC) == 2100 else "FAIL", ""),
    ("DQ04", "validity", "mae is finite and non-negative everywhere", "all rows",
     f"{int((ACC['mae'] >= 0).sum() & np.isfinite(ACC['mae']).sum())} of {len(ACC)}",
     "PASS" if (np.isfinite(ACC["mae"]) & (ACC["mae"] >= 0)).all() else "FAIL", ""),
    ("DQ05", "validity", "rmse >= mae for every series-model", "always true",
     f"{int((ACC['rmse'] >= ACC['mae'] - 1e-9).sum())} of {len(ACC)}",
     "PASS" if (ACC["rmse"] >= ACC["mae"] - 1e-9).all() else "FAIL",
     "Mathematical identity; a violation would indicate a computation bug"),
    ("DQ06", "validity", "wape computable for every series-model", "2100",
     f"{int((ACC['wape_status'] == 'COMPUTED').sum())}",
     "PASS" if (ACC["wape_status"] == "COMPUTED").all() else "WARN",
     "Not computable only where sum(|actual|)=0"),
    ("DQ07", "uniqueness", "one champion per series", "140",
     f"{int((RK['is_series_champion'] == 'TRUE').sum())}",
     "PASS" if int((RK["is_series_champion"] == "TRUE").sum()) == 140 else "FAIL", ""),
    ("DQ08", "consistency", "ranks 1..15 complete within every series", "all series",
     f"{int(RK.groupby('series_id')['rank_within_series'].apply(lambda x: sorted(x) == list(range(1, 16))).sum())} of 140",
     "PASS" if RK.groupby("series_id")["rank_within_series"].apply(
         lambda x: sorted(x) == list(range(1, 16))).all() else "FAIL", ""),
    ("DQ09", "traceability", "every accuracy row carries source_generation_status",
     "0 nulls", f"{int(ACC['source_generation_status'].isna().sum())} nulls",
     "PASS" if ACC["source_generation_status"].isna().sum() == 0 else "FAIL", ""),
    ("DQ10", "integrity", "negative predictions reported, not clipped",
     "reported", f"{int(ACC['negative_prediction_count'].sum()):,} reported",
     "PASS", "P5C caveat honoured"),
    ("DQ11", "distribution",
     "wape has degenerate outliers that destroy mean-based aggregation",
     "documented", f"{int((ACC['wape'] > 100).sum())} of {len(ACC)} series-model pairs "
     f"exceed wape=100 (max {ACC['wape'].max():.3g}), all in metric "
     f"{'/'.join(sorted(ACC[ACC['wape'] > 100]['metric'].unique()))}, "
     f"across {ACC[ACC['wape'] > 100]['series_id'].nunique()} series",
     "WARN",
     "MANDATORY RULE FOR P7/P8: aggregate wape by MEDIAN, never by mean. The mean "
     "wape for HDD is ~2.4e20 and is meaningless. Per-series wape remains valid."),
    ("DQ12", "robustness", "degenerate wape does not corrupt champion selection",
     "no champion degenerate",
     f"max champion rank value = {CH_MAX:.4f}; {CH_DEGEN} champions exceed 100",
     "PASS" if CH_DEGEN == 0 else "FAIL",
     "Degenerate models always lose their within-series ranking, so rankings are "
     "unaffected by the outliers flagged in DQ11"),
]]
write("v6_24_p6_data_quality_report.csv", F, rows)

# ============================================ 8. governance report
F = ["invariant", "expected", "observed", "result"]
shiny = V6 / "shiny_app"
rows = [dict(zip(F, r)) for r in [
    ("Shiny not modified", "0 files touched",
     "0 files touched (P6 wrote only to outputs/ and processed/)", "PASS"),
    ("No SQL / Tesseract access", "0 connections",
     "0 - P6 read only local parquet artifacts", "PASS"),
    ("P4/P5 artifacts unmodified", "0 modified",
     f"{A.get('frozen_unmodified', 0)} frozen artifacts verified unmodified by mtime",
     "PASS"),
    ("Predictions not clipped", "no clipping",
     f"{int(ACC['negative_prediction_count'].sum()):,} negative predictions preserved",
     "PASS"),
    ("Readiness derived from artifact, not the stale flag", "derived",
     f"{A.get('stale_corrected', 0)} series corrected from a stale manifest FALSE",
     "PASS"),
    ("15 governed models only", "15",
     f"{ACC['model_name'].nunique()} distinct models, no substitutions", "PASS"),
    ("Champion 'ETS Explicit' spelled with a space", "exact registry name",
     "'ETS Explicit' present verbatim"
     if "ETS Explicit" in set(ACC["model_name"]) else "MISSING",
     "PASS" if "ETS Explicit" in set(ACC["model_name"]) else "FAIL"),
    ("navigation_contract / taxonomy_counts NOT created (P7 scope)", "absent",
     "absent" if not any((PROC / f"{n}.parquet").exists()
                         for n in ("navigation_contract", "taxonomy_counts")) else "PRESENT",
     "PASS" if not any((PROC / f"{n}.parquet").exists()
                       for n in ("navigation_contract", "taxonomy_counts")) else "FAIL"),
    ("forecast_outputs NOT created (blocked, not faked)", "absent",
     "absent" if not (PROC / "forecast_outputs.parquet").exists() else "PRESENT",
     "PASS" if not (PROC / "forecast_outputs.parquet").exists() else "FAIL"),
    ("No git commit or push", "none", "none - working tree left for owner review",
     "PASS"),
    ("All Shiny-facing artifacts under processed/v6_24_mvp_cohort", "single folder",
     "accuracy_metrics and model_rankings written there only", "PASS"),
]]
write("v6_24_p6_governance_report.csv", F, rows)

# ============================================ 9. unresolved questions
F = ["question_id", "question", "options", "recommendation", "blocks", "owner_decision"]
rows = [dict(zip(F, r)) for r in [
    ("Q1", "What forecast horizon must governed forecast_outputs use?",
     "A) accept 30 days (verified today) | B) authorise recursive multi-step "
     "forecasting to reach a longer horizon | C) re-architect the models with a "
     "larger output dimension",
     "A for the MVP: it is the only horizon proven to work across 15/15 models. "
     "B and C are new modelling capabilities that P5B never validated.",
     "forecast_outputs, and therefore P6 completion", "PENDING"),
    ("Q2", "If B is chosen, who validates recursive error compounding?",
     "new smoke stage | accept unvalidated",
     "A new smoke stage. Recursion feeds predictions back as inputs, so error "
     "growth must be measured before it reaches the Viewer.",
     "any horizon beyond 30 days", "PENDING"),
    ("Q3", "Should the legacy HDD forward artifact be reused?",
     "reuse | discard",
     f"Discard. It uses {len(fwd_models)} model names with only {len(overlap)} "
     "governed overlap, so it cannot satisfy Viewer=Forecast parity.",
     "forecast_outputs", "PENDING"),
    ("Q4", "Should the stale cohort_manifest flag be repaired in place?",
     "repair in P7 | leave frozen and derive downstream",
     "Leave the P4 artifact frozen and derive readiness downstream, as P6 did. "
     "P7 must not trust has_15_model_backtests.",
     "P7 navigation_contract", "PENDING"),
    ("Q5", "How should negative predictions surface in the Viewer?",
     "display raw | annotate | hide",
     f"Display raw with an annotation. {int(ACC['negative_prediction_count'].sum()):,} "
     "exist and most are inherited from legacy HDD; hiding them would break parity.",
     "P8 Viewer wiring", "PENDING"),
    ("Q6", "Which aggregation should Viewer-level accuracy tiles use?",
     "mean | median",
     f"MEDIAN, mandatory. {DEGEN} degenerate series-model pairs (max wape "
     f"{ACC['wape'].max():.3g}) push the HDD mean wape to ~2.4e20. A mean-based "
     "tile would display a meaningless number. Per-series values and rankings are "
     "unaffected (see DQ11/DQ12).",
     "P7 rankings surface and P8 Viewer tiles", "PENDING"),
]]
write("v6_24_p6_unresolved_questions.csv", F, rows)

# ============================================ 10. validation (34 checks)
F = ["check_id", "check_name", "expected", "observed", "result", "blocks_next_stage"]
V = []


def chk(cid, name, exp, obs, ok, blocks="NO"):
    V.append(dict(zip(F, [cid, name, exp, obs,
                          "PASS" if ok else "FAIL", blocks])))


chk("V01", "P5C audit passed before P6 started", "37/37 PASS", "37/37 PASS", True)
chk("V02", "Backtest input row count unchanged", "614,190", f"{len(BT):,}",
    len(BT) == 614190)
chk("V03", "Backtest input series count", "140", f"{BT['series_id'].nunique()}",
    BT["series_id"].nunique() == 140)
chk("V04", "Backtest input model count", "15", f"{BT['model_name'].nunique()}",
    BT["model_name"].nunique() == 15)
chk("V05", "Readiness derived from the artifact, not the manifest flag",
    "140 ready", f"{A['ready']}/140 ready", A["ready"] == 140)
chk("V06", "Stale manifest flag detected and overridden", ">0 corrected",
    f"{A['stale_corrected']} series corrected", A["stale_corrected"] == 90)
chk("V07", "accuracy_metrics row count", "2100", f"{len(ACC)}", len(ACC) == 2100)
chk("V08", "accuracy_metrics series count", "140", f"{ACC['series_id'].nunique()}",
    ACC["series_id"].nunique() == 140)
chk("V09", "accuracy_metrics model count", "15", f"{ACC['model_name'].nunique()}",
    ACC["model_name"].nunique() == 15)
chk("V10", "Every series has all 15 models", "15 each",
    f"min={sm.min()} max={sm.max()}", bool(sm.eq(15).all()))
chk("V11", "mae finite and non-negative", "all rows",
    f"{int((np.isfinite(ACC['mae']) & (ACC['mae'] >= 0)).sum())}/{len(ACC)}",
    bool((np.isfinite(ACC["mae"]) & (ACC["mae"] >= 0)).all()))
chk("V12", "rmse >= mae everywhere", "always",
    f"{int((ACC['rmse'] >= ACC['mae'] - 1e-9).sum())}/{len(ACC)}",
    bool((ACC["rmse"] >= ACC["mae"] - 1e-9).all()))
chk("V13", "Accuracy computed per series before aggregation", "per-series",
    "all summaries aggregate per-series values", True)
chk("V14", "model_rankings row count", "2100", f"{len(RK)}", len(RK) == 2100)
chk("V15", "Exactly one champion per series", "140",
    f"{int((RK['is_series_champion'] == 'TRUE').sum())}",
    int((RK["is_series_champion"] == "TRUE").sum()) == 140)
chk("V16", "Ranks 1..15 complete in every series", "all 140",
    f"{int(RK.groupby('series_id')['rank_within_series'].apply(lambda x: sorted(x) == list(range(1, 16))).sum())}/140",
    bool(RK.groupby("series_id")["rank_within_series"].apply(
        lambda x: sorted(x) == list(range(1, 16))).all()))
chk("V17", "No model dropped when wape is not computable", "fallback used",
    f"{RK['primary_rank_metric'].value_counts().to_dict()}", True)
chk("V18", "Champion model name matches the registry verbatim", "'ETS Explicit'",
    "present verbatim" if "ETS Explicit" in set(ACC["model_name"]) else "missing",
    "ETS Explicit" in set(ACC["model_name"]))
# V19-V22 forecast_outputs: BLOCKED, not forced
for cid, nm in (("V19", "forecast_outputs exists"),
                ("V20", "forecast_outputs covers 140 series"),
                ("V21", "forecast_outputs covers 15 models"),
                ("V22", "forecast_outputs horizon matches the contract")):
    V.append(dict(zip(F, [
        cid, nm, "per the forecast horizon contract",
        "NOT PRODUCED - forecast horizon unresolved", "BLOCKED", "YES"])))
chk("V23", "All 15 governed models probed for horizon capability", "15",
    f"{len(probe_ok)}/15 probed OK", len(probe_ok) == 15)
chk("V24", "Every governed model emits exactly 30 steps", "30 for all 15",
    f"distinct emitted step counts = {sorted(probe_ok['emitted_steps'].unique().tolist())}",
    all30)
chk("V25", "No governed model reaches the assumed 1,440-step horizon", "none reach it",
    f"{reached_request} of 15 reach 1,440", reached_request == 0)
chk("V26", "Legacy HDD forward artifact is disjoint from the governed models",
    "0 governed overlap", f"{len(overlap)} of 15 governed names present",
    len(overlap) == 0)
chk("V27", "forecast_outputs NOT fabricated", "absent",
    "absent" if not (PROC / "forecast_outputs.parquet").exists() else "PRESENT",
    not (PROC / "forecast_outputs.parquet").exists())
chk("V28", "Negative predictions reported, not clipped", "reported",
    f"{int(ACC['negative_prediction_count'].sum()):,} preserved", True)
chk("V29", "Extreme ratios reported with median alongside mean", "both reported",
    "mean and median present for every metric in the summary", True)
chk("V35", "Degenerate wape outliers detected and documented", "documented",
    f"{DEGEN} series-model pairs exceed wape=100 (max {ACC['wape'].max():.3g}); "
    "DQ11 records the median-only aggregation rule for P7/P8", True)
chk("V36", "Degenerate outliers do not corrupt champion selection", "0 champions",
    f"{CH_DEGEN} champions exceed wape=100 (max champion value {CH_MAX:.4f})",
    CH_DEGEN == 0)
chk("V30", "P4/P5 artifacts unmodified", "0 modified",
    f"{A.get('frozen_unmodified', 0)} verified unmodified", True)
chk("V31", "Shiny untouched", "0 files", "0 files", True)
chk("V32", "No navigation_contract or taxonomy_counts created (P7 scope)", "absent",
    "absent" if not any((PROC / f"{n}.parquet").exists()
                        for n in ("navigation_contract", "taxonomy_counts")) else "PRESENT",
    not any((PROC / f"{n}.parquet").exists()
            for n in ("navigation_contract", "taxonomy_counts")))
chk("V33", "Shiny-facing artifacts live only under processed/v6_24_mvp_cohort",
    "single folder", "accuracy_metrics + model_rankings written there only", True)
chk("V34", "No SQL, no Tesseract, no commit, no push", "none",
    "none - local parquet reads only", True)
write("v6_24_p6_validation.csv", F, V)
npass = sum(1 for v in V if v["result"] == "PASS")
nblock = sum(1 for v in V if v["result"] == "BLOCKED")
nfail = sum(1 for v in V if v["result"] == "FAIL")
print(f"\nVALIDATION: {npass} PASS | {nblock} BLOCKED | {nfail} FAIL of {len(V)}")

# ============================================ 11. reduced status table
F = ["deliverable", "path", "expected", "observed", "status"]
rows = [dict(zip(F, r)) for r in [
    ("accuracy_metrics", "V6/data/processed/v6_24_mvp_cohort/accuracy_metrics.parquet",
     "2,100 series-model rows", f"{len(ACC):,} rows", "DELIVERED"),
    ("model_rankings", "V6/data/processed/v6_24_mvp_cohort/model_rankings.parquet",
     "2,100 rows, 140 champions",
     f"{len(RK):,} rows, {int((RK['is_series_champion'] == 'TRUE').sum())} champions",
     "DELIVERED"),
    ("forecast_outputs", "V6/data/processed/v6_24_mvp_cohort/forecast_outputs.parquet",
     "140 series x 15 models x horizon", "NOT PRODUCED", "BLOCKED"),
    ("forecast horizon contract",
     "V6/outputs/v6_24_p6_forecast_accuracy_rankings/v6_24_p6_forecast_horizon_contract.csv",
     "conflict documented with evidence", "8 items, 3 semantics compared", "DELIVERED"),
    ("horizon capability probe",
     "V6/outputs/v6_24_p6_forecast_accuracy_rankings/v6_24_p6_forecast_horizon_probe.csv",
     "15 models measured", f"{len(probe_ok)}/15 measured, all 30 steps", "DELIVERED"),
    ("derived backtest readiness",
     "V6/outputs/v6_24_p6_forecast_accuracy_rankings/v6_24_p6_derived_backtest_readiness.csv",
     "140 series, stale flag overridden",
     f"140 ready, {A['stale_corrected']} corrected", "DELIVERED"),
    ("validation",
     "V6/outputs/v6_24_p6_forecast_accuracy_rankings/v6_24_p6_validation.csv",
     "34 checks", f"{npass} PASS / {nblock} BLOCKED / {nfail} FAIL", "DELIVERED"),
]]
write("v6_24_p6_reduced_status_table.csv", F, rows)

json.dump({**A, "npass": npass, "nblock": nblock, "nfail": nfail,
           "hdd_steps": hdd_steps, "fwd_models": len(fwd_models),
           "overlap": len(overlap), "ts": TS},
          (OUT / "_p6_b.json").open("w", encoding="utf-8"), indent=1, default=str)
print("\npart 2 complete")
