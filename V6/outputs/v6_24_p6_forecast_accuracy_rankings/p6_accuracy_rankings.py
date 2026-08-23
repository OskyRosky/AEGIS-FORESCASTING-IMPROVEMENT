"""V6.24-P6 | Accuracy metrics, model rankings, and the forecast horizon contract.

Readiness is derived from model_backtests_15_models.parquet, NEVER from the stale
cohort_manifest.has_15_model_backtests flag that P5C flagged.

Accuracy is computed PER (series_id, model_name) first and only then aggregated,
so that denser series cannot silently dominate the ranking.

Predictions are never clipped. Negative and extreme values are counted and
reported, because accuracy must evaluate what the models actually produced.
"""

from __future__ import annotations

import csv
import json
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P5C = OUT.parent / "v6_24_p5c_independent_backtest_artifact_audit"
P5 = OUT.parent / "v6_24_p5_15_model_backtest_generation"

GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
NC = "STRUCTURALLY_NOT_COMPUTABLE"
RUN_ID = f"P6_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
A = {}


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# ==================================================== PHASE 0: preflight
P5CV = pd.read_csv(P5C / "v6_24_p5c_validation.csv")
p5c_pass = (P5CV["result"] == "PASS").all()
BT = pd.read_parquet(PROC / "model_backtests_15_models.parquet", engine="pyarrow")
BT["target_date"] = pd.to_datetime(BT["target_date"])
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")

# P6 owns exactly these names in processed/. Re-running P6 may overwrite its own
# outputs, but must never touch a P4/P5 artifact. Anything else carrying a P6 name
# is unexpected and blocks the run.
P6_OWNED = {"accuracy_metrics.parquet", "accuracy_metrics.csv",
            "model_rankings.parquet", "model_rankings.csv"}
P45_FROZEN = {"cohort_manifest", "actuals_normalized", "model_backtests_15_models",
              "source_forecast_baselines_normalized"}
existing = [p.name for p in PROC.iterdir()
            if any(k in p.name for k in ("forecast_outputs", "accuracy_metrics",
                                         "model_rankings"))]
unexpected = [n for n in existing if n not in P6_OWNED]
frozen_before = {p.name: p.stat().st_mtime for p in PROC.iterdir()
                 if any(p.name.startswith(k) for k in P45_FROZEN)}

F = ["check", "expected", "observed", "result"]
pf = [dict(zip(F, r)) for r in [
    ("P5C audit PASS", "all checks PASS",
     f"{int((P5CV['result'] == 'PASS').sum())}/{len(P5CV)} PASS",
     "PASS" if p5c_pass else "FAIL"),
    ("model_backtests_15_models.parquet exists", "present",
     f"{len(BT):,} rows", "PASS"),
    ("Backtests contain 140 series", "140", f"{BT['series_id'].nunique()}",
     "PASS" if BT["series_id"].nunique() == 140 else "FAIL"),
    ("Backtests contain 15 models", "15", f"{BT['model_name'].nunique()}",
     "PASS" if BT["model_name"].nunique() == 15 else "FAIL"),
    ("Backtests contain 2,100 series-model pairs", "2100",
     f"{BT.groupby(['series_id', 'model_name']).ngroups}",
     "PASS" if BT.groupby(["series_id", "model_name"]).ngroups == 2100 else "FAIL"),
    ("actuals_normalized exists", "present", f"{len(ACT):,} rows", "PASS"),
    ("cohort_manifest exists", "present", f"{len(MAN)} rows", "PASS"),
    ("Pre-existing P6-named artifacts are all P6-owned (re-run is idempotent)",
     "0 unexpected",
     f"{len(unexpected)} unexpected; {len(existing)} P6-owned present: {sorted(existing)}",
     "PASS" if not unexpected else "FAIL"),
    ("forecast_outputs absent (P6 forecast is blocked)", "absent",
     "absent" if not any("forecast_outputs" in n for n in existing) else "PRESENT",
     "PASS" if not any("forecast_outputs" in n for n in existing) else "FAIL"),
]]
write("v6_24_p6_preflight_check.csv", F, pf)
if not p5c_pass or unexpected:
    raise SystemExit("PREFLIGHT FAILED")
print(f"preflight OK | P5C {int((P5CV['result'] == 'PASS').sum())}/{len(P5CV)} PASS")

# ==================================================== derived readiness
F = ["cohort_id", "series_id", "metric", "models_present", "expected_models",
     "backtest_rows", "generated_or_reused_status",
     "manifest_has_15_model_backtests_original", "derived_has_15_model_backtests",
     "readiness_result", "notes"]
man_flag = dict(zip(MAN["series_id"], MAN["has_15_model_backtests"]))
rows = []
for sid, g in BT.groupby("series_id"):
    present = int(g["model_name"].nunique())
    per_model_ok = g.groupby("model_name").size().min() >= 1
    derived = present == 15 and per_model_ok
    orig = str(man_flag.get(sid, "MISSING"))
    is_stale = orig.upper() == "FALSE" and derived
    rows.append(dict(zip(F, [
        g["cohort_id"].iloc[0], sid, g["metric"].iloc[0], present, 15, len(g),
        "|".join(sorted(g["source_generation_status"].unique())), orig,
        "TRUE" if derived else "FALSE", "PASS" if derived else "FAIL",
        ("STALE MANIFEST FLAG CORRECTED: the manifest reads FALSE but the artifact holds "
         f"{present} models across {len(g):,} backtest rows. Readiness derived from "
         "model_backtests_15_models, never from the flag."
         if is_stale else
         "Derived from model_backtests_15_models; the manifest flag agrees.")])))
write("v6_24_p6_derived_backtest_readiness.csv", F, rows)
ready = sum(1 for r in rows if r["derived_has_15_model_backtests"] == "TRUE")
# Case-insensitive: the manifest stores "FALSE"/"TRUE" in upper case.
stale = sum(1 for r in rows
            if str(r["manifest_has_15_model_backtests_original"]).upper() == "FALSE"
            and r["derived_has_15_model_backtests"] == "TRUE")
A["ready"], A["stale_corrected"] = ready, stale
print(f"derived readiness: {ready}/140 ready | {stale} series where the stale manifest flag "
      f"said FALSE but the artifact proves TRUE")

# ==================================================== accuracy metrics
print("\ncomputing per-series/model accuracy...")
BT["error"] = BT["predicted_value"] - BT["actual_value"]
BT["abs_error"] = BT["error"].abs()
BT["sq_error"] = BT["error"] ** 2
nz = BT["actual_value"] != 0
BT["ape"] = np.where(nz, (BT["error"] / BT["actual_value"].where(nz)).abs(), np.nan)
den = BT["actual_value"].abs() + BT["predicted_value"].abs()
BT["sape"] = np.where(den != 0, 2 * BT["abs_error"] / den.where(den != 0), np.nan)
BT["ratio"] = np.where(nz, (BT["predicted_value"] / BT["actual_value"].where(nz)).abs(), np.nan)
BT["is_extreme"] = (BT["ratio"] > 100) | (BT["ratio"] < 0.01)

META = ["cohort_id", "metric", "db_type", "scenario", "segment", "granularity", "key",
        "route_path", "model_family", "source_generation_status", "caveat"]
acc = []
for (sid, mo), g in BT.groupby(["series_id", "model_name"]):
    sa = g["actual_value"].abs().sum()
    m0 = g.iloc[0]
    # Numeric columns stay numeric. Computability is carried in a separate status
    # column rather than as a sentinel string, so the parquet schema stays clean
    # and downstream consumers cannot accidentally compare a string to a float.
    mape = float(g["ape"].mean()) if g["ape"].notna().any() else np.nan
    smape = float(g["sape"].mean()) if g["sape"].notna().any() else np.nan
    wape = float(g["abs_error"].sum() / sa) if sa != 0 else np.nan
    acc.append({
        "cohort_id": m0["cohort_id"], "series_id": sid, "model_name": mo,
        **{c: m0[c] for c in ("metric", "db_type", "scenario", "segment", "granularity",
                              "key", "route_path", "model_family")},
        "n_backtest_rows": int(len(g)),
        "n_target_dates": int(g["target_date"].nunique()),
        "min_target_date": str(g["target_date"].min())[:10],
        "max_target_date": str(g["target_date"].max())[:10],
        "mae": float(g["abs_error"].mean()),
        "rmse": float(np.sqrt(g["sq_error"].mean())),
        "mape": mape, "smape": smape, "wape": wape,
        "mape_status": "COMPUTED" if not np.isnan(mape) else NC,
        "smape_status": "COMPUTED" if not np.isnan(smape) else NC,
        "wape_status": "COMPUTED" if not np.isnan(wape) else NC,
        "bias": float(g["error"].mean()),
        "mean_error": float(g["error"].mean()),
        "mean_actual": float(g["actual_value"].mean()),
        "mean_predicted": float(g["predicted_value"].mean()),
        "median_absolute_error": float(g["abs_error"].median()),
        "negative_prediction_count": int((g["predicted_value"] < 0).sum()),
        "extreme_ratio_count": int(g["is_extreme"].sum()),
        "zero_actual_count": int((g["actual_value"] == 0).sum()),
        "nonzero_actual_count": int((g["actual_value"] != 0).sum()),
        "source_generation_status": m0["source_generation_status"],
        "mape_units": "decimal fraction (0.05 = 5 percent)",
        "smape_units": "decimal fraction",
        "wape_units": "decimal fraction",
        "caveat": m0["caveat"],
    })
ACC = pd.DataFrame(acc)
print(f"accuracy_metrics: {len(ACC)} series-model rows | {ACC['series_id'].nunique()} series "
      f"| {ACC['model_name'].nunique()} models")
ACC.to_parquet(PROC / "accuracy_metrics.parquet", index=False, engine="pyarrow",
               compression="snappy")
ACC.to_csv(PROC / "accuracy_metrics.csv", index=False)
assert len(pd.read_parquet(PROC / "accuracy_metrics.parquet")) == len(ACC)
print("PROMOTED accuracy_metrics.parquet / .csv")

# ==================================================== model rankings
print("\nranking models within each series...")
rk = []
for sid, g in ACC.groupby("series_id"):
    g = g.copy()
    # Rank by wape; fall back to smape then mae where wape is not computable.
    # No model is ever dropped: a fallback is used and the reason is recorded.
    def sortkey(r):
        if r["wape_status"] == "COMPUTED":
            return (0, float(r["wape"]))
        if r["smape_status"] == "COMPUTED":
            return (1, float(r["smape"]))
        return (2, float(r["mae"]))
    g["_k"] = g.apply(sortkey, axis=1)
    g = g.sort_values(["_k", "model_name"]).reset_index(drop=True)
    for i, r in g.iterrows():
        used = ("wape" if r["wape_status"] == "COMPUTED"
                else "smape" if r["smape_status"] == "COMPUTED" else "mae")
        rk.append({
            "cohort_id": r["cohort_id"], "series_id": sid, "metric": r["metric"],
            "db_type": r["db_type"], "scenario": r["scenario"], "segment": r["segment"],
            "granularity": r["granularity"], "key": r["key"],
            "route_path": r["route_path"], "model_name": r["model_name"],
            "model_family": r["model_family"],
            "primary_rank_metric": used,
            "primary_rank_value": r[used],
            "secondary_rank_metric": "smape", "secondary_rank_value": r["smape"],
            "tertiary_rank_metric": "rmse", "tertiary_rank_value": r["rmse"],
            "tie_breaker_metric": "mae", "tie_breaker_value": r["mae"],
            "rank_within_series": i + 1,
            "is_series_champion": "TRUE" if i == 0 else "FALSE",
            "champion_reason": (f"Lowest {used} among all 15 governed models for this series"
                                if i == 0 else "NOT_CHAMPION"),
            "n_backtest_rows": r["n_backtest_rows"],
            "negative_prediction_count": r["negative_prediction_count"],
            "extreme_ratio_count": r["extreme_ratio_count"],
            "source_generation_status": r["source_generation_status"],
            "caveat": r["caveat"],
        })
RK = pd.DataFrame(rk)
champs = RK[RK["is_series_champion"] == "TRUE"]
print(f"model_rankings: {len(RK)} rows | {champs['series_id'].nunique()} champions | "
      f"exactly one per series: {champs.groupby('series_id').size().eq(1).all()}")
RK.to_parquet(PROC / "model_rankings.parquet", index=False, engine="pyarrow",
              compression="snappy")
RK.to_csv(PROC / "model_rankings.csv", index=False)
print("PROMOTED model_rankings.parquet / .csv")

ACC.to_pickle(OUT / "_p6_acc.pkl")
RK.to_pickle(OUT / "_p6_rk.pkl")

# Governance: prove P6 did not touch any frozen P4/P5 artifact.
frozen_after = {p.name: p.stat().st_mtime for p in PROC.iterdir()
                if any(p.name.startswith(k) for k in P45_FROZEN)}
touched = sorted(n for n in frozen_before
                 if frozen_before[n] != frozen_after.get(n))
if touched:
    raise SystemExit(f"GOVERNANCE VIOLATION: P6 modified frozen artifacts: {touched}")
print(f"governance OK | {len(frozen_before)} frozen P4/P5 artifacts unmodified")

A.update({"acc_rows": len(ACC), "rk_rows": len(RK),
          "champ_series": int(champs["series_id"].nunique()),
          "one_per_series": bool(champs.groupby("series_id").size().eq(1).all()),
          "frozen_unmodified": len(frozen_before), "run_id": RUN_ID})
json.dump(A, (OUT / "_p6_a.json").open("w", encoding="utf-8"), indent=1, default=str)
print("\npart 1 complete")
