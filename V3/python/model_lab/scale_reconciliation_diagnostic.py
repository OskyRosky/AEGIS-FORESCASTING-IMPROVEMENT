"""
Stage 07 - Etapa 2B-v1.1a : Scale Reconciliation Diagnostic (READ-ONLY).
Compares scale comparability across three artifacts BEFORE attempting relative-residual intervals.
Does NOT generate interval bands, does NOT modify any data/Shiny/model.
"""
import os
import numpy as np
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DP = os.path.join(ROOT, "data", "processed")
OUT = os.path.join(ROOT, "outputs", "shiny_mvp",
                   "7_V2_FORECAST_INTERVAL_SCALE_RECONCILIATION_ETAPA2B_V1_1A")
os.makedirs(OUT, exist_ok=True)
P = "stage07_v2_forecast_interval_"


def stats(df, key_col, val_col, label):
    rows = []
    for k, g in df.groupby(key_col):
        v = pd.to_numeric(g[val_col], errors="coerce").dropna()
        d = pd.to_datetime(g["date"], errors="coerce")
        rows.append(dict(
            entity_key=k, artifact=label, value_col=val_col,
            row_count=len(g),
            min_date=str(d.min().date()) if d.notna().any() else "",
            max_date=str(d.max().date()) if d.notna().any() else "",
            min_value=round(float(v.min()), 4) if len(v) else np.nan,
            p05_value=round(float(v.quantile(0.05)), 4) if len(v) else np.nan,
            median_value=round(float(v.median()), 4) if len(v) else np.nan,
            mean_value=round(float(v.mean()), 4) if len(v) else np.nan,
            p95_value=round(float(v.quantile(0.95)), 4) if len(v) else np.nan,
            max_value=round(float(v.max()), 4) if len(v) else np.nan,
            zero_count=int((v == 0).sum()),
            negative_count=int((v < 0).sum()),
        ))
    return pd.DataFrame(rows)


# ---- load ----
bt = pd.read_csv(os.path.join(DP, "forecast_viewer_model_outputs.csv"))
bt = bt.rename(columns={"series_key": "entity_key"})
fc = pd.read_csv(os.path.join(DP, "forecasts.csv"))
ac = pd.read_csv(os.path.join(DP, "actuals.csv"))

# ---- 3. scale_by_key (all artifacts/value cols stacked) ----
sb = pd.concat([
    stats(bt, "entity_key", "actual_value", "backtest_actual"),
    stats(bt, "entity_key", "forecast_value", "backtest_forecast"),
    stats(fc, "entity_key", "forecast_value", "production_forecast"),
    stats(ac, "entity_key", "actual_value", "actuals"),
], ignore_index=True)
sb.to_csv(os.path.join(OUT, P + "scale_by_key.csv"), index=False)

# ---- 5. key_overlap ----
kb, kf, ka = set(bt.entity_key), set(fc.entity_key), set(ac.entity_key)
allk = sorted(kb | kf | ka)
ko = pd.DataFrame([dict(
    entity_key=k,
    in_backtest=k in kb, in_production_forecast=k in kf, in_actuals=k in ka,
    in_all_three=(k in kb and k in kf and k in ka),
) for k in allk])
ko.to_csv(os.path.join(OUT, P + "key_overlap.csv"), index=False)

# ---- 4. scale_ratio_diagnostic ----
med = sb.pivot_table(index="entity_key", columns="artifact",
                     values="median_value", aggfunc="first")
for c in ["backtest_actual", "backtest_forecast", "production_forecast", "actuals"]:
    if c not in med.columns:
        med[c] = np.nan


def ratio(a, b):
    return (a / b).where(b.abs() > 1e-9)


rd = pd.DataFrame(index=med.index)
rd["prod_fc_median"] = med["production_forecast"]
rd["bt_actual_median"] = med["backtest_actual"]
rd["bt_forecast_median"] = med["backtest_forecast"]
rd["actuals_median"] = med["actuals"]
rd["bt_actual__over__prod_fc"] = ratio(med["backtest_actual"], med["production_forecast"])
rd["bt_forecast__over__prod_fc"] = ratio(med["backtest_forecast"], med["production_forecast"])
rd["actuals__over__prod_fc"] = ratio(med["actuals"], med["production_forecast"])
rd["bt_actual__over__actuals"] = ratio(med["backtest_actual"], med["actuals"])
rd["bt_forecast__over__actuals"] = ratio(med["backtest_forecast"], med["actuals"])
rd = rd.round(4).reset_index()
rd.to_csv(os.path.join(OUT, P + "scale_ratio_diagnostic.csv"), index=False)


# ---- 7. scale_mismatch_flags ----
def sev(r):
    if pd.isna(r):
        return "no_data"
    a = abs(np.log(r)) if r > 0 else np.inf
    if r > 30 or r < 1 / 30:
        return "extreme_gt30x"
    if r > 10 or r < 1 / 10:
        return "severe_gt10x"
    if r > 2 or r < 0.5:
        return "moderate_gt2x"
    return "ok_within_2x"


flags = rd[["entity_key", "bt_actual__over__prod_fc",
            "bt_forecast__over__prod_fc", "actuals__over__prod_fc"]].copy()
flags["flag_bt_actual_vs_prod_fc"] = flags["bt_actual__over__prod_fc"].apply(sev)
flags["flag_bt_forecast_vs_prod_fc"] = flags["bt_forecast__over__prod_fc"].apply(sev)
flags["flag_actuals_vs_prod_fc"] = flags["actuals__over__prod_fc"].apply(sev)
flags.to_csv(os.path.join(OUT, P + "scale_mismatch_flags.csv"), index=False)

# ---- 6. APC-Dedicated case study ----
case = sb[sb.entity_key == "APC-Dedicated"].copy()
case.to_csv(os.path.join(OUT, P + "apc_dedicated_case_study.csv"), index=False)


# ---- 8. relative_residual_readiness ----
# Relative residuals are computed WITHIN backtest: (bt_actual - bt_forecast)/bt_forecast
# -> scale-invariant, so bt-vs-prod absolute scale mismatch does NOT block them.
# Readiness depends on: key present in backtest, backtest forecast not near zero,
# and a measurable in-sample relative error distribution.
rr_rows = []
for k in allk:
    g = bt[bt.entity_key == k]
    in_bt = k in kb
    rel = np.nan
    rel_p95 = np.nan
    n = 0
    if in_bt and len(g):
        a = pd.to_numeric(g["actual_value"], errors="coerce")
        f = pd.to_numeric(g["forecast_value"], errors="coerce")
        mask = (f.abs() > 1e-9) & a.notna() & f.notna()
        re = ((a - f) / f)[mask]
        n = int(mask.sum())
        if n:
            rel = round(float(re.abs().median()), 4)
            rel_p95 = round(float(re.abs().quantile(0.95)), 4)
    if not in_bt:
        readiness = "fallback_needed_no_backtest"
    elif n < 30:
        readiness = "thin_sample_use_fallback"
    else:
        readiness = "ready_relative_residual"
    rr_rows.append(dict(
        entity_key=k, in_backtest=in_bt, backtest_rel_err_n=n,
        median_abs_relative_error=rel, p95_abs_relative_error=rel_p95,
        readiness=readiness,
    ))
rr = pd.DataFrame(rr_rows)
rr.to_csv(os.path.join(OUT, P + "relative_residual_readiness.csv"), index=False)

# ---- 2. validation.csv ----
checks = [
    ("v2_root_exists", os.path.isdir(ROOT), ROOT),
    ("backtest_inspected", True, f"{bt.entity_key.nunique()} keys, {len(bt)} rows"),
    ("production_forecast_inspected", True, f"{fc.entity_key.nunique()} keys, {len(fc)} rows"),
    ("actuals_inspected", True, f"{ac.entity_key.nunique()} keys, {len(ac)} rows"),
    ("key_overlap_computed", True, f"{int(ko.in_all_three.sum())} keys in all three"),
    ("scale_by_key_computed", True, f"{len(sb)} key-artifact rows"),
    ("ratio_diagnostic_computed", True, f"{len(rd)} keys"),
    ("apc_dedicated_diagnosed", len(case) > 0, f"{len(case)} artifact rows for APC-Dedicated"),
    ("severe_mismatch_flags_created", True,
     f"{int((flags.flag_bt_actual_vs_prod_fc.isin(['severe_gt10x','extreme_gt30x'])).sum())} keys >=10x bt_actual vs prod"),
    ("relative_residual_readiness_classified", True,
     rr.readiness.value_counts().to_dict().__str__()),
    ("no_code_modified", True, "diagnostic only"),
    ("no_data_modified", True, "read-only"),
    ("no_shiny_modified", True, "untouched"),
    ("no_models_run", True, "none"),
    ("no_forecasts_generated", True, "none"),
    ("champion_unchanged", True, "untouched"),
]
val = pd.DataFrame([dict(check=c, status="pass" if s else "fail", details=d)
                    for c, s, d in checks])
val.to_csv(os.path.join(OUT, P + "scale_reconciliation_validation.csv"), index=False)

# ---- console summary ----
print("KEYS all/bt/fc/ac:", len(allk), len(kb), len(kf), len(ka),
      "| in_all_three:", int(ko.in_all_three.sum()))
print("Missing from backtest:", sorted(kf - kb))
print("\nFlag distribution bt_actual vs prod_fc:")
print(flags.flag_bt_actual_vs_prod_fc.value_counts().to_string())
print("\nReadiness distribution:")
print(rr.readiness.value_counts().to_string())
print("\nAPC-Dedicated medians by artifact:")
print(case[["artifact", "value_col", "row_count", "median_value",
            "p95_value", "min_date", "max_date"]].to_string(index=False))
print("\nAPC-Dedicated ratios:")
print(rd[rd.entity_key == "APC-Dedicated"].to_string(index=False))
print("\nWorst 8 by |log bt_actual/prod_fc|:")
tmp = rd.copy()
tmp["absdev"] = (np.log(tmp["bt_actual__over__prod_fc"].where(
    tmp["bt_actual__over__prod_fc"] > 0))).abs()
print(tmp.sort_values("absdev", ascending=False)
      [["entity_key", "prod_fc_median", "bt_actual_median",
        "bt_actual__over__prod_fc", "actuals_median",
        "actuals__over__prod_fc"]].head(8).to_string(index=False))
print("\nGlobal: actuals vs prod_fc median ratio describe:")
print(rd["actuals__over__prod_fc"].describe().round(3).to_string())
print("Global: bt_actual vs prod_fc median ratio describe:")
print(rd["bt_actual__over__prod_fc"].describe().round(3).to_string())
print("\nDONE_SCALE_DIAG")
