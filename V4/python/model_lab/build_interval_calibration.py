"""Stage 07 Etapa 2B-v1 - Empirical backtest-calibrated prediction interval builder.

Reproducible, NON-Shiny pipeline step. Produces an ADDITIVE interval-enhanced
forecast artifact (data/processed/forecasts_with_intervals.csv) plus governed
diagnostic outputs under outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_ARTIFACT_ETAPA2B_V1/.

Method: empirical residual-quantile intervals.
  residual = actual_value - forecast_value  (from backtest evidence)
  offsets  = quantiles of residuals per (calibration grain x horizon bucket)
  band     = forecast_value + residual_quantile, lower capped at 0.
Horizon scope: 1-30 days ONLY (backtest evidence limit). No extrapolation.
Calibration grain fallback: entity_key x bucket -> resource x bucket -> global x bucket.

Does NOT touch Shiny, models, SQL, or champion. Does NOT overwrite forecasts.csv.
"""
from __future__ import annotations

import os
import numpy as np
import pandas as pd

ROOT = r"c:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V2"
PROC = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "outputs", "shiny_mvp", "7_V2_FORECAST_INTERVAL_ARTIFACT_ETAPA2B_V1")
os.makedirs(OUT, exist_ok=True)

BACKTEST = os.path.join(PROC, "forecast_viewer_model_outputs.csv")
FORECASTS = os.path.join(PROC, "forecasts.csv")
ARTIFACT = os.path.join(PROC, "forecasts_with_intervals.csv")

MIN_N_KEY = 20      # preferred grain (entity_key x bucket)
MIN_N_FALLBACK = 30  # resource/global grain
INTERVAL_METHOD = "empirical_backtest_residual_quantile"
INTERVAL_SOURCE = "forecast_viewer_model_outputs.csv"

BUCKETS = [("1_7", 1, 7), ("8_14", 8, 14), ("15_30", 15, 30)]


def bucket_of(h: int) -> str | None:
    for name, lo, hi in BUCKETS:
        if lo <= h <= hi:
            return name
    return None


def q(series: pd.Series, p: float) -> float:
    return float(np.quantile(series.to_numpy(), p))


# ---------------------------------------------------------------- calibration
bt = pd.read_csv(BACKTEST)
bt = bt[(bt["horizon_days"] >= 1) & (bt["horizon_days"] <= 30)].copy()
bt = bt.dropna(subset=["actual_value", "forecast_value"])
bt["residual"] = bt["actual_value"] - bt["forecast_value"]
bt["horizon_bucket"] = bt["horizon_days"].apply(bucket_of)
bt["resource"] = "HDD"  # entire upstream table is HDD (Etapa 1 confirmed)

cal_rows = []


def build_cal(df, grain_name, group_cols):
    out = {}
    for keys, g in df.groupby(group_cols):
        if not isinstance(keys, tuple):
            keys = (keys,)
        n = len(g)
        rec = {
            "grain": grain_name,
            "n": n,
            "q025": q(g["residual"], 0.025),
            "q10": q(g["residual"], 0.10),
            "q90": q(g["residual"], 0.90),
            "q975": q(g["residual"], 0.975),
        }
        out[keys] = rec
        cal_rows.append({
            "calibration_grain": grain_name,
            **{c: v for c, v in zip(group_cols, keys)},
            "horizon_bucket": keys[-1],
            "n_residuals": n,
            "q025": rec["q025"], "q10": rec["q10"],
            "q90": rec["q90"], "q975": rec["q975"],
        })
    return out


cal_key = build_cal(bt, "entity_key_x_horizon_bucket", ["series_key", "horizon_bucket"])
cal_res = build_cal(bt, "resource_x_horizon_bucket", ["resource", "horizon_bucket"])
cal_glob = build_cal(bt.assign(_g="ALL"), "global_x_horizon_bucket", ["_g", "horizon_bucket"])

cal_df = pd.DataFrame(cal_rows)
cal_df.to_csv(os.path.join(OUT, "stage07_v2_forecast_interval_artifact_etapa2b_v1_calibration_table.csv"), index=False)


def lookup(entity_key, resource, bucket):
    rec = cal_key.get((entity_key, bucket))
    if rec is not None and rec["n"] >= MIN_N_KEY:
        return rec
    rec = cal_res.get((resource, bucket))
    if rec is not None and rec["n"] >= MIN_N_FALLBACK:
        return rec
    rec = cal_glob.get(("ALL", bucket))
    if rec is not None and rec["n"] >= MIN_N_FALLBACK:
        return rec
    return None


# ---------------------------------------------------------------- production
fc = pd.read_csv(FORECASTS)
orig_cols = list(fc.columns)
orig_rows = len(fc)
fc["date"] = pd.to_datetime(fc["date"])
forecast_start = fc["date"].min()
fc["forecast_horizon_day"] = (fc["date"] - forecast_start).dt.days + 1

new_cols = [
    "forecast_lower_80", "forecast_upper_80", "forecast_lower_95", "forecast_upper_95",
    "interval_available", "interval_method", "interval_source", "interval_level_available",
    "interval_calibration_grain", "interval_calibration_sample_size", "interval_horizon_bucket",
    "interval_extrapolated", "interval_unavailable_reason",
]
for c in new_cols:
    fc[c] = pd.NA

mono_violations = 0
reason_counts = {}


def add_reason(r):
    reason_counts[r] = reason_counts.get(r, 0) + 1


for i, row in fc.iterrows():
    h = int(row["forecast_horizon_day"])
    fc.at[i, "interval_extrapolated"] = False
    bucket = bucket_of(h)
    if h > 30 or bucket is None:
        fc.at[i, "interval_available"] = False
        fc.at[i, "interval_unavailable_reason"] = "outside_calibrated_horizon_1_30"
        add_reason("outside_calibrated_horizon_1_30")
        continue
    rec = lookup(row["entity_key"], row["resource"], bucket)
    fc.at[i, "interval_horizon_bucket"] = bucket
    if rec is None:
        fc.at[i, "interval_available"] = False
        fc.at[i, "interval_unavailable_reason"] = "insufficient_calibration_sample"
        add_reason("insufficient_calibration_sample")
        continue
    v = float(row["forecast_value"])
    l80 = max(0.0, v + rec["q10"])
    u80 = v + rec["q90"]
    l95 = max(0.0, v + rec["q025"])
    u95 = v + rec["q975"]
    # contract monotonicity: band must bracket the point forecast
    if not (l95 <= l80 <= v <= u80 <= u95):
        fc.at[i, "interval_available"] = False
        fc.at[i, "interval_unavailable_reason"] = "monotonicity_violation_residual_bias"
        add_reason("monotonicity_violation_residual_bias")
        mono_violations += 1
        continue
    fc.at[i, "forecast_lower_80"] = round(l80, 6)
    fc.at[i, "forecast_upper_80"] = round(u80, 6)
    fc.at[i, "forecast_lower_95"] = round(l95, 6)
    fc.at[i, "forecast_upper_95"] = round(u95, 6)
    fc.at[i, "interval_available"] = True
    fc.at[i, "interval_method"] = INTERVAL_METHOD
    fc.at[i, "interval_source"] = INTERVAL_SOURCE
    fc.at[i, "interval_level_available"] = "80,95"
    fc.at[i, "interval_calibration_grain"] = rec["grain"]
    fc.at[i, "interval_calibration_sample_size"] = rec["n"]

# restore date as ISO string to match original formatting
fc["date"] = fc["date"].dt.strftime("%Y-%m-%d")
fc.to_csv(ARTIFACT, index=False)

# ---------------------------------------------------------------- diagnostics
avail = int((fc["interval_available"] == True).sum())
unavail = int((fc["interval_available"] == False).sum())
h1_30 = int((fc["forecast_horizon_day"] <= 30).sum())
print("ARTIFACT_ROWS", len(fc), "ORIG_ROWS", orig_rows, "COLS_PRESERVED", orig_cols == list(fc.columns)[:len(orig_cols)])
print("FORECAST_START", forecast_start.date())
print("HORIZON_1_30_ROWS", h1_30)
print("AVAILABLE", avail, "UNAVAILABLE", unavail, "MONO_VIOL", mono_violations)
print("REASONS", reason_counts)

# unavailable summary
us = pd.DataFrame([{"reason": k, "rows": v} for k, v in reason_counts.items()])
us.to_csv(os.path.join(OUT, "stage07_v2_forecast_interval_artifact_etapa2b_v1_unavailable_summary.csv"), index=False)

# sample rows: available within horizon, and a few > 30
samp_avail = fc[fc["interval_available"] == True].head(15)
samp_over = fc[fc["forecast_horizon_day"] > 30].head(5)
sample = pd.concat([samp_avail, samp_over])
keep = ["entity_key", "date", "forecast_value", "model_version", "forecast_horizon_day",
        "forecast_lower_80", "forecast_upper_80", "forecast_lower_95", "forecast_upper_95",
        "interval_available", "interval_calibration_grain", "interval_calibration_sample_size",
        "interval_horizon_bucket", "interval_unavailable_reason"]
sample[keep].to_csv(os.path.join(OUT, "stage07_v2_forecast_interval_artifact_etapa2b_v1_sample_rows.csv"), index=False)

# coverage (in-sample diagnostic): fraction of backtest residuals within each band per key x bucket
cov_rows = []
for (sk, bk), g in bt.groupby(["series_key", "horizon_bucket"]):
    r = g["residual"]
    q025, q10, q90, q975 = q(r, 0.025), q(r, 0.10), q(r, 0.90), q(r, 0.975)
    cov80 = float(((r >= q10) & (r <= q90)).mean())
    cov95 = float(((r >= q025) & (r <= q975)).mean())
    cov_rows.append({"calibration_grain": "entity_key_x_horizon_bucket", "entity_key": sk,
                     "horizon_bucket": bk, "n": len(g), "coverage_80": round(cov80, 4),
                     "coverage_95": round(cov95, 4)})
# global per bucket
for bk in [b[0] for b in BUCKETS]:
    g = bt[bt["horizon_bucket"] == bk]
    r = g["residual"]
    q025, q10, q90, q975 = q(r, 0.025), q(r, 0.10), q(r, 0.90), q(r, 0.975)
    cov_rows.append({"calibration_grain": "global_x_horizon_bucket", "entity_key": "ALL",
                     "horizon_bucket": bk, "n": len(g),
                     "coverage_80": round(float(((r >= q10) & (r <= q90)).mean()), 4),
                     "coverage_95": round(float(((r >= q025) & (r <= q975)).mean()), 4)})
cov_df = pd.DataFrame(cov_rows)
cov_df.to_csv(os.path.join(OUT, "stage07_v2_forecast_interval_artifact_etapa2b_v1_coverage_report.csv"), index=False)
print("COVERAGE_80_RANGE", round(cov_df["coverage_80"].min(), 3), round(cov_df["coverage_80"].max(), 3))
print("COVERAGE_95_RANGE", round(cov_df["coverage_95"].min(), 3), round(cov_df["coverage_95"].max(), 3))

# contract summary
contract = pd.DataFrame([{"column": c, "status": "preserved"} for c in orig_cols] +
                        [{"column": c, "status": "added"} for c in ["forecast_horizon_day"] + new_cols])
contract.to_csv(os.path.join(OUT, "stage07_v2_forecast_interval_artifact_etapa2b_v1_contract_summary.csv"), index=False)
print("DONE")
