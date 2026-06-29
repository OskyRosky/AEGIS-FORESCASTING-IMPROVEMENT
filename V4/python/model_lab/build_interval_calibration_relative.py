"""
Stage 07 - Etapa 2B-v1.1b : Relative-residual empirical prediction-interval artifact.
Reproducible, NON-Shiny. Reads backtest + production forecasts; writes a CANDIDATE artifact
data/processed/forecasts_with_intervals_relative.csv (does NOT overwrite forecasts.csv).
Method: relative residuals computed WITHIN backtest (scale-invariant), applied to production point.
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DP = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "outputs", "shiny_mvp",
                   "7_V2_FORECAST_INTERVAL_RELATIVE_ARTIFACT_ETAPA2B_V1_1B")
os.makedirs(OUT, exist_ok=True)
P = "stage07_v2_forecast_interval_relative_"

# ---- guardrail constants ----
CLIP_LOW = -0.95            # relative-error lower clip
NEAR_ZERO_KEY_FRAC = 0.01   # exclude |bt_forecast| < 1% of key median |forecast|
MIN_N_KEY = 20             # min obs for key x bucket grain
MIN_N_FALLBACK = 30        # min obs for resource/global fallback
N_HOLDOUT_CUTOFFS = 3      # last N backtest cutoffs held out for coverage validation
METHOD = "empirical_backtest_relative_residual_quantile"
SOURCE = "forecast_viewer_model_outputs.csv"


def bucket_of(h):
    if 1 <= h <= 7:
        return "1_7"
    if 8 <= h <= 14:
        return "8_14"
    if 15 <= h <= 30:
        return "15_30"
    return None


# ================= load backtest =================
bt = pd.read_csv(os.path.join(DP, SOURCE)).rename(columns={"series_key": "entity_key"})
bt["f"] = pd.to_numeric(bt["forecast_value"], errors="coerce")
bt["a"] = pd.to_numeric(bt["actual_value"], errors="coerce")
bt["horizon_bucket"] = bt["horizon_days"].apply(bucket_of)
n_total = len(bt)

# ---- near-zero / invalid denominator handling ----
key_med_abs = bt.groupby("entity_key")["f"].transform(lambda s: s.abs().median())
floor = NEAR_ZERO_KEY_FRAC * key_med_abs
excl_nonpos = (bt["f"] <= 0)
excl_small = (bt["f"] > 0) & (bt["f"].abs() < floor)
valid = bt[~(excl_nonpos | excl_small) & bt["a"].notna() & bt["f"].notna()
           & bt["horizon_bucket"].notna()].copy()
NEAR_ZERO_EXCLUDED = int(excl_nonpos.sum() + excl_small.sum())

# ---- relative error + winsorize ----
valid["re_raw"] = (valid["a"] - valid["f"]) / valid["f"]
CLIP_HIGH = round(float(valid["re_raw"].quantile(0.99)), 4)
valid["re"] = valid["re_raw"].clip(CLIP_LOW, CLIP_HIGH)

# ---- temporal holdout split by forecast_start_date ----
cutoffs = sorted(valid["forecast_start_date"].dropna().unique())
holdout_cuts = set(cutoffs[-N_HOLDOUT_CUTOFFS:]) if len(cutoffs) > N_HOLDOUT_CUTOFFS else set()
train = valid[~valid["forecast_start_date"].isin(holdout_cuts)].copy()
hold = valid[valid["forecast_start_date"].isin(holdout_cuts)].copy()

QS = {"q025": 0.025, "q10": 0.10, "q90": 0.90, "q975": 0.975}


def build_grains(df):
    """Return dicts for key x bucket, resource x bucket (single HDD), global x bucket."""
    keyg, resg, glog = {}, {}, {}
    for (k, b), g in df.groupby(["entity_key", "horizon_bucket"]):
        if len(g) >= MIN_N_KEY:
            keyg[(k, b)] = {q: float(g["re"].quantile(p)) for q, p in QS.items()} | {"n": len(g)}
    for b, g in df.groupby("horizon_bucket"):
        if len(g) >= MIN_N_FALLBACK:
            resg[("HDD", b)] = {q: float(g["re"].quantile(p)) for q, p in QS.items()} | {"n": len(g)}
            glog[("GLOBAL", b)] = resg[("HDD", b)]
    return keyg, resg, glog


def lookup(keyg, resg, glog, key, b):
    if (key, b) in keyg:
        return keyg[(key, b)], "entity_key_x_horizon_bucket"
    if ("HDD", b) in resg:
        return resg[("HDD", b)], "resource_x_horizon_bucket"
    if ("GLOBAL", b) in glog:
        return glog[("GLOBAL", b)], "global_x_horizon_bucket"
    return None, None


train_key, train_res, train_glo = build_grains(train)
full_key, full_res, full_glo = build_grains(valid)   # final calibration uses ALL evidence

# ================= holdout coverage (out-of-sample) =================
def covered(df, kg, rg, gg):
    in80 = in95 = tot = 0
    by_bucket = {}
    for _, r in df.iterrows():
        q, _grain = lookup(kg, rg, gg, r["entity_key"], r["horizon_bucket"])
        if q is None:
            continue
        f, a = r["f"], r["a"]
        lo80 = max(0.0, f * (1 + q["q10"])); up80 = f * (1 + q["q90"])
        lo95 = max(0.0, f * (1 + q["q025"])); up95 = f * (1 + q["q975"])
        lo80, up80 = min(lo80, f), max(up80, f)
        lo95, up95 = min(lo95, lo80), max(up95, up80)
        c80 = lo80 <= a <= up80; c95 = lo95 <= a <= up95
        in80 += c80; in95 += c95; tot += 1
        bb = by_bucket.setdefault(r["horizon_bucket"], [0, 0, 0])
        bb[0] += c80; bb[1] += c95; bb[2] += 1
    return in80, in95, tot, by_bucket


h80, h95, htot, hbb = covered(hold, train_key, train_res, train_glo)
COV80 = round(h80 / htot, 4) if htot else np.nan
COV95 = round(h95 / htot, 4) if htot else np.nan

# ================= production point forecasts =================
fc = pd.read_csv(os.path.join(DP, "forecasts.csv"))
orig_cols = list(fc.columns)
fc["_d"] = pd.to_datetime(fc["date"], errors="coerce")
start = fc["_d"].min()
fc["forecast_horizon_day"] = (fc["_d"] - start).dt.days + 1

# ---- forecast_point_scale_anomaly (from backtest actual vs production forecast median) ----
bt_actual_med = bt.groupby("entity_key")["a"].median()
prod_fc_med = fc.groupby("entity_key")["forecast_value"].median()
anomaly_keys = set()
for k in prod_fc_med.index:
    ba = bt_actual_med.get(k, np.nan)
    pf = prod_fc_med.get(k, np.nan)
    if pd.notna(ba) and pd.notna(pf) and pf > 0 and ba > 0:
        ratio = ba / pf
        if ratio > 10 or ratio < 0.1:
            anomaly_keys.add(k)

# ---- compute bands ----
new = {c: [] for c in [
    "forecast_lower_80", "forecast_upper_80", "forecast_lower_95", "forecast_upper_95",
    "interval_available", "interval_method", "interval_source", "interval_level_available",
    "interval_calibration_grain", "interval_calibration_sample_size", "interval_horizon_bucket",
    "interval_extrapolated", "interval_unavailable_reason", "forecast_point_scale_anomaly"]}
mono_clamped = 0
for _, r in fc.iterrows():
    h = r["forecast_horizon_day"]
    f = r["forecast_value"]
    key = r["entity_key"]
    anom = key in anomaly_keys
    b = bucket_of(h) if pd.notna(h) else None
    if b is None or h < 1 or h > 30:
        new["forecast_lower_80"].append(np.nan); new["forecast_upper_80"].append(np.nan)
        new["forecast_lower_95"].append(np.nan); new["forecast_upper_95"].append(np.nan)
        new["interval_available"].append(False)
        new["interval_method"].append(METHOD); new["interval_source"].append(SOURCE)
        new["interval_level_available"].append(np.nan)
        new["interval_calibration_grain"].append(np.nan)
        new["interval_calibration_sample_size"].append(np.nan)
        new["interval_horizon_bucket"].append(np.nan)
        new["interval_extrapolated"].append(False)
        new["interval_unavailable_reason"].append("outside_calibrated_horizon_1_30")
        new["forecast_point_scale_anomaly"].append(anom)
        continue
    q, grain = lookup(full_key, full_res, full_glo, key, b)
    if q is None:
        new["forecast_lower_80"].append(np.nan); new["forecast_upper_80"].append(np.nan)
        new["forecast_lower_95"].append(np.nan); new["forecast_upper_95"].append(np.nan)
        new["interval_available"].append(False)
        new["interval_method"].append(METHOD); new["interval_source"].append(SOURCE)
        new["interval_level_available"].append(np.nan)
        new["interval_calibration_grain"].append(np.nan)
        new["interval_calibration_sample_size"].append(np.nan)
        new["interval_horizon_bucket"].append(b)
        new["interval_extrapolated"].append(False)
        new["interval_unavailable_reason"].append("no_calibration_evidence")
        new["forecast_point_scale_anomaly"].append(anom)
        continue
    lo80 = max(0.0, f * (1 + q["q10"])); up80 = f * (1 + q["q90"])
    lo95 = max(0.0, f * (1 + q["q025"])); up95 = f * (1 + q["q975"])
    rlo80, rup80, rlo95, rup95 = lo80, up80, lo95, up95
    lo80 = min(lo80, f); up80 = max(up80, f)
    lo95 = min(lo95, lo80); up95 = max(up95, up80)
    if (rlo80, rup80, rlo95, rup95) != (lo80, up80, lo95, up95):
        mono_clamped += 1
    new["forecast_lower_80"].append(round(lo80, 4)); new["forecast_upper_80"].append(round(up80, 4))
    new["forecast_lower_95"].append(round(lo95, 4)); new["forecast_upper_95"].append(round(up95, 4))
    new["interval_available"].append(True)
    new["interval_method"].append(METHOD); new["interval_source"].append(SOURCE)
    new["interval_level_available"].append("80,95")
    new["interval_calibration_grain"].append(grain)
    new["interval_calibration_sample_size"].append(int(q["n"]))
    new["interval_horizon_bucket"].append(b)
    new["interval_extrapolated"].append(False)
    new["interval_unavailable_reason"].append(np.nan)
    new["forecast_point_scale_anomaly"].append(anom)

for c, v in new.items():
    fc[c] = v
# global scalar metadata columns
fc["interval_relative_error_clip_lower"] = CLIP_LOW
fc["interval_relative_error_clip_upper"] = CLIP_HIGH
fc["interval_near_zero_excluded_count"] = NEAR_ZERO_EXCLUDED
fc["interval_holdout_coverage_80"] = COV80
fc["interval_holdout_coverage_95"] = COV95

out_cols = orig_cols + [
    "forecast_horizon_day", "forecast_lower_80", "forecast_upper_80",
    "forecast_lower_95", "forecast_upper_95", "interval_available", "interval_method",
    "interval_source", "interval_level_available", "interval_calibration_grain",
    "interval_calibration_sample_size", "interval_horizon_bucket", "interval_extrapolated",
    "interval_unavailable_reason", "interval_relative_error_clip_lower",
    "interval_relative_error_clip_upper", "interval_near_zero_excluded_count",
    "interval_holdout_coverage_80", "interval_holdout_coverage_95", "forecast_point_scale_anomaly"]
art = fc[out_cols].copy()
art.to_csv(os.path.join(DP, "forecasts_with_intervals_relative.csv"), index=False)

# ================= diagnostics / output files =================
av = art[art["interval_available"] == True].copy()
av["band95_width_ratio"] = (av["forecast_upper_95"] - av["forecast_lower_95"]) / av["forecast_value"]
av["band80_width_ratio"] = (av["forecast_upper_80"] - av["forecast_lower_80"]) / av["forecast_value"]

# 4. calibration table (final, full-evidence)
cal_rows = []
for (k, b), q in full_key.items():
    cal_rows.append(dict(grain="entity_key_x_horizon_bucket", entity_key=k, horizon_bucket=b,
                         n=q["n"], q025=round(q["q025"], 4), q10=round(q["q10"], 4),
                         q90=round(q["q90"], 4), q975=round(q["q975"], 4)))
for (k, b), q in full_res.items():
    cal_rows.append(dict(grain="resource_x_horizon_bucket", entity_key=k, horizon_bucket=b,
                         n=q["n"], q025=round(q["q025"], 4), q10=round(q["q10"], 4),
                         q90=round(q["q90"], 4), q975=round(q["q975"], 4)))
pd.DataFrame(cal_rows).to_csv(os.path.join(OUT, P + "calibration_table.csv"), index=False)

# 5. holdout coverage report
cov_rows = [dict(scope="overall", level="80", coverage=COV80, n=htot),
            dict(scope="overall", level="95", coverage=COV95, n=htot)]
for bk, (c8, c9, t) in hbb.items():
    cov_rows.append(dict(scope=f"bucket_{bk}", level="80",
                         coverage=round(c8 / t, 4) if t else np.nan, n=t))
    cov_rows.append(dict(scope=f"bucket_{bk}", level="95",
                         coverage=round(c9 / t, 4) if t else np.nan, n=t))
pd.DataFrame(cov_rows).to_csv(os.path.join(OUT, P + "holdout_coverage_report.csv"), index=False)

# 6. unavailable summary
un = art[art["interval_available"] == False]
us = un.groupby("interval_unavailable_reason").size().reset_index(name="rows")
us.to_csv(os.path.join(OUT, P + "unavailable_summary.csv"), index=False)

# 7. band width diagnostic
gt2 = int((av["band95_width_ratio"] > 2).sum()); gt5 = int((av["band95_width_ratio"] > 5).sum())
bw = pd.DataFrame([
    dict(metric="available_rows", value=len(av)),
    dict(metric="median_band95_width_ratio", value=round(float(av["band95_width_ratio"].median()), 4)),
    dict(metric="p95_band95_width_ratio", value=round(float(av["band95_width_ratio"].quantile(0.95)), 4)),
    dict(metric="median_band80_width_ratio", value=round(float(av["band80_width_ratio"].median()), 4)),
    dict(metric="rows_band95_gt_2x", value=gt2),
    dict(metric="pct_band95_gt_2x", value=round(gt2 / len(av) * 100, 2)),
    dict(metric="rows_band95_gt_5x", value=gt5),
    dict(metric="pct_band95_gt_5x", value=round(gt5 / len(av) * 100, 2)),
    dict(metric="monotonicity_clamped_rows", value=mono_clamped),
])
bw.to_csv(os.path.join(OUT, P + "band_width_diagnostic.csv"), index=False)

# 8. APC-Dedicated sample
apc = art[(art["entity_key"] == "APC-Dedicated") & (art["interval_available"] == True)].head(10)
apc.to_csv(os.path.join(OUT, P + "apc_dedicated_sample.csv"), index=False)

# 9. top widest rows
top = av.sort_values("band95_width_ratio", ascending=False).head(20)[
    ["entity_key", "date", "forecast_horizon_day", "forecast_value",
     "forecast_lower_95", "forecast_upper_95", "band95_width_ratio",
     "interval_calibration_grain", "forecast_point_scale_anomaly"]]
top.to_csv(os.path.join(OUT, P + "top_widest_rows.csv"), index=False)

# 3. contract summary
cs = pd.DataFrame([
    dict(item="rows_in", value=len(fc)), dict(item="rows_out", value=len(art)),
    dict(item="original_columns", value=len(orig_cols)),
    dict(item="columns_added", value=len(out_cols) - len(orig_cols)),
    dict(item="forecast_start", value=str(start.date())),
    dict(item="rows_horizon_1_30", value=int(((art.forecast_horizon_day >= 1) & (art.forecast_horizon_day <= 30)).sum())),
    dict(item="interval_available_true", value=int(av.shape[0])),
    dict(item="interval_available_false", value=int(un.shape[0])),
    dict(item="grain_key", value=int((av.interval_calibration_grain == "entity_key_x_horizon_bucket").sum())),
    dict(item="grain_resource_fallback", value=int((av.interval_calibration_grain == "resource_x_horizon_bucket").sum())),
    dict(item="grain_global_fallback", value=int((av.interval_calibration_grain == "global_x_horizon_bucket").sum())),
    dict(item="near_zero_excluded", value=NEAR_ZERO_EXCLUDED),
    dict(item="clip_lower", value=CLIP_LOW), dict(item="clip_upper", value=CLIP_HIGH),
    dict(item="holdout_cutoffs", value=len(holdout_cuts)),
    dict(item="holdout_coverage_80", value=COV80), dict(item="holdout_coverage_95", value=COV95),
    dict(item="anomaly_keys", value=";".join(sorted(anomaly_keys))),
    dict(item="mono_clamped_rows", value=mono_clamped),
])
cs.to_csv(os.path.join(OUT, P + "artifact_contract_summary.csv"), index=False)

# console
print("ROWS_IN", len(fc), "ROWS_OUT", len(art), "COLS_PRESERVED",
      orig_cols == list(art.columns)[:len(orig_cols)])
print("AVAILABLE", len(av), "UNAVAILABLE", len(un))
print("GRAINS key/res/global:",
      int((av.interval_calibration_grain == "entity_key_x_horizon_bucket").sum()),
      int((av.interval_calibration_grain == "resource_x_horizon_bucket").sum()),
      int((av.interval_calibration_grain == "global_x_horizon_bucket").sum()))
print("NEAR_ZERO_EXCLUDED", NEAR_ZERO_EXCLUDED, "CLIP", CLIP_LOW, CLIP_HIGH)
print("HOLDOUT cutoffs", sorted(holdout_cuts), "COV80", COV80, "COV95", COV95)
print("BAND95 width ratio median", round(float(av.band95_width_ratio.median()), 3),
      "p95", round(float(av.band95_width_ratio.quantile(0.95)), 3),
      "| >2x", gt2, "(", round(gt2/len(av)*100, 1), "% )",
      "| >5x", gt5, "(", round(gt5/len(av)*100, 1), "% )")
print("BAND80 width ratio median", round(float(av.band80_width_ratio.median()), 3))
print("ANOMALY_KEYS", sorted(anomaly_keys))
print("MONO_CLAMPED", mono_clamped)
neg = int((av[["forecast_lower_80", "forecast_lower_95"]] < 0).any(axis=1).sum())
mono_ok = bool((av.forecast_lower_95 <= av.forecast_lower_80).all()
               and (av.forecast_lower_80 <= av.forecast_value).all()
               and (av.forecast_value <= av.forecast_upper_80).all()
               and (av.forecast_upper_80 <= av.forecast_upper_95).all())
print("NEG_LOWER", neg, "MONO_OK", mono_ok)
print("APC sample:")
print(apc[["date", "forecast_horizon_day", "forecast_value", "forecast_lower_95",
           "forecast_upper_95", "forecast_point_scale_anomaly"]].head(4).to_string(index=False))
print("DONE_RELATIVE_BUILD")
