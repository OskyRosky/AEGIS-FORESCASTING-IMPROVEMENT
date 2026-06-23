"""
Audit #4 — Independent spot-check verification (read-only).
Does NOT modify, rerun, or regenerate any model outputs.
Independently recomputes row counts, schema checks, denominator policy,
non-negative adjustment, aggregation hierarchy, and significance inputs
to validate the challenger official results before 5.30 Tournament Engine.
"""
import os
import numpy as np
import pandas as pd

ROOT = r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT"
ML = os.path.join(ROOT, "outputs", "model_lab")

FINAL = ["AutoARIMA", "Theta", "ETS Explicit", "LightGBM", "XGBoost", "FastNeuralAR_MLP"]

def line(t): print("\n" + "=" * 70 + f"\n{t}\n" + "=" * 70)

# ---------------------------------------------------------------- B: forecasts
line("B. OFFICIAL FORECAST INTEGRITY")
fc = pd.read_csv(os.path.join(ML, "challenger_official_execution", "challenger_official_forecasts.csv"))
print("columns:", list(fc.columns))
print("total rows:", len(fc))
print("models present:", sorted(fc["model_name"].unique()))
print("NBEATS rows:", (fc["model_name"] == "NBEATS").sum())
print("NHITS rows:", (fc["model_name"] == "NHITS").sum())
print("rows per model:\n", fc["model_name"].value_counts())
if "execution_mode" in fc.columns:
    print("execution_mode values:", fc["execution_mode"].unique())
print("horizon_day min/max:", fc["horizon_day"].min(), fc["horizon_day"].max())
print("horizon_day distinct count:", fc["horizon_day"].nunique())
print("forecast_value nulls:", fc["forecast_value"].isna().sum())
print("forecast_value inf:", np.isinf(fc["forecast_value"]).sum())
dup_keys = ["model_name", "entity_key", "window_id", "horizon_day"]
if "run_id" in fc.columns:
    dup_keys = ["run_id"] + dup_keys
print("duplicate rows by keys:", fc.duplicated(subset=dup_keys).sum())
print("distinct entity_key:", fc["entity_key"].nunique())
print("distinct window_id:", sorted(fc["window_id"].unique()))
print("entity-windows:", fc.groupby(["entity_key", "window_id"]).ngroups)
neg_raw = (fc["forecast_value"] < 0).sum()
print("raw negative forecast_value rows:", neg_raw)

# ---------------------------------------------------------------- C: join/metrics
line("C. ACTUAL JOIN + METRICS")
join = pd.read_csv(os.path.join(ML, "challenger_metrics", "challenger_actual_forecast_join.csv"))
print("join rows:", len(join))
print("join columns:", list(join.columns))
actual_cols = [c for c in join.columns if "actual" in c.lower()]
print("actual-like columns:", actual_cols)
for c in actual_cols:
    print(f"  {c} nulls:", join[c].isna().sum())
mw = pd.read_csv(os.path.join(ML, "challenger_metrics", "challenger_metrics_entity_window.csv"))
print("metric rows:", len(mw))
print("metric columns:", list(mw.columns))
print("metric models:", sorted(mw["model_name"].unique()))
print("metric rows per model:\n", mw["model_name"].value_counts())
for m in ["mase", "rmsse", "wmape", "mape", "smape", "rmse", "bias"]:
    col = [c for c in mw.columns if c.lower() == m or c.lower().startswith(m)]
    if col:
        c = col[0]
        print(f"  {c}: nan={mw[c].isna().sum()} inf={np.isinf(mw[c]).sum()}")

# ---------------------------------------------------------------- E: non-negative
line("E. NON-NEGATIVE SCORING POLICY")
sc = pd.read_csv(os.path.join(ML, "challenger_metrics", "challenger_scoring_forecasts.csv"))
print("scoring rows:", len(sc))
print("scoring columns:", list(sc.columns))
raw_col = "forecast_value" if "forecast_value" in sc.columns else None
adj_col = next((c for c in sc.columns if "adjust" in c.lower() and "value" in c.lower()), None)
flag_col = next((c for c in sc.columns if "negative" in c.lower() and "flag" in c.lower()), None)
print("raw_col:", raw_col, "adj_col:", adj_col, "flag_col:", flag_col)
if raw_col and adj_col:
    expected_adj = sc[raw_col].clip(lower=0)
    mismatch = (~np.isclose(sc[adj_col], expected_adj)).sum()
    print("rows where adjusted != max(raw,0):", mismatch)
    print("raw negatives in scoring:", (sc[raw_col] < 0).sum())
    print("adjusted negatives (should be 0):", (sc[adj_col] < 0).sum())
if flag_col:
    print("negative_forecast_flag true count:", sc[flag_col].sum())
    if raw_col:
        print("flag matches raw<0:", (sc[flag_col].astype(bool) == (sc[raw_col] < 0)).all())

# ---------------------------------------------------------------- D: denominators
line("D. DENOMINATOR POLICY")
den = pd.read_csv(os.path.join(ML, "denominator_reconciliation", "training_only_denominators.csv"))
print("denominator rows:", len(den))
print("denominator columns:", list(den.columns))
print("entity-windows in denominators:", den.groupby(["entity_key", "window_id"]).ngroups)
# Spot-check MASE recomputation for a few entity-windows
line("D2. INDEPENDENT MASE/RMSSE SPOT-CHECK (5 random entity-windows)")
mw_keys = [c for c in mw.columns]
# Identify metric + join columns
ew_actual = next((c for c in join.columns if c.lower() in ("actual", "actual_value", "y_true")), None)
ew_pred = next((c for c in join.columns if "adjust" in c.lower() and "value" in c.lower()), None)
if ew_pred is None:
    ew_pred = next((c for c in join.columns if c.lower() in ("forecast_value", "adjusted_forecast_value")), None)
print("join actual col:", ew_actual, "join pred col used:", ew_pred)
den_idx = den.set_index(["entity_key", "window_id"])
rng = np.random.default_rng(7)
sample = mw.sample(5, random_state=7)
for _, r in sample.iterrows():
    ek, wid, mdl = r["entity_key"], r["window_id"], r["model_name"]
    sub = join[(join["entity_key"] == ek) & (join["window_id"] == wid) & (join["model_name"] == mdl)]
    if ew_actual and ew_pred and len(sub):
        mae = (sub[ew_pred] - sub[ew_actual]).abs().mean()
        mse = ((sub[ew_pred] - sub[ew_actual]) ** 2).mean()
        try:
            dmae = den_idx.loc[(ek, wid), "mase_denominator_mae"]
            dmse = den_idx.loc[(ek, wid), "rmsse_denominator_mse"]
            mase_calc = mae / dmae
            rmsse_calc = np.sqrt(mse / dmse)
            mase_col = next((c for c in mw.columns if c.lower() == "mase"), None)
            rmsse_col = next((c for c in mw.columns if c.lower() == "rmsse"), None)
            print(f"{mdl[:14]:14} {ek[:16]:16} w{wid}: MASE calc={mase_calc:.4f} stored={r.get(mase_col,'?'):.4f} | "
                  f"RMSSE calc={rmsse_calc:.4f} stored={r.get(rmsse_col,'?'):.4f}")
        except KeyError:
            print(f"{mdl} {ek} w{wid}: denominator missing")

# ---------------------------------------------------------------- F: aggregation
line("F. AGGREGATION HIERARCHY (equal entity weighting)")
canon = pd.read_csv(os.path.join(ML, "challenger_aggregation_significance", "challenger_canonical_entity_window_scores.csv"))
print("canonical rows:", len(canon))
ent_mod = pd.read_csv(os.path.join(ML, "challenger_aggregation_significance", "challenger_aggregation_by_entity_model.csv"))
print("entity_model rows:", len(ent_mod), "| distinct entities:", ent_mod["entity_key"].nunique())
by_model = pd.read_csv(os.path.join(ML, "challenger_aggregation_significance", "challenger_aggregation_by_model.csv"))
print("by_model rows:", len(by_model))
# Recompute two-stage median for one model
mase_c = next((c for c in canon.columns if c.lower() == "mase"), None)
print("canonical mase col:", mase_c)
if mase_c:
    for m in FINAL:
        cm = canon[canon["model_name"] == m]
        stage1 = cm.groupby("entity_key")[mase_c].median()
        stage2 = stage1.median()
        stored = by_model.loc[by_model["model_name"] == m, "official_median_mase"].values
        print(f"  {m[:16]:16} two-stage median MASE={stage2:.5f} stored={stored[0] if len(stored) else '?':.5f} "
              f"entities={cm['entity_key'].nunique()}")

# ---------------------------------------------------------------- G: significance
line("G. SIGNIFICANCE")
pw = pd.read_csv(os.path.join(ML, "challenger_aggregation_significance", "challenger_pairwise_significance.csv"))
print("pairwise comparisons:", len(pw))
print("paired_entity_count unique:", pw["paired_entity_count"].unique())
print("comparison_status counts:\n", pw["comparison_status"].value_counts())
print("supported:", (pw["comparison_status"] == "supported_difference").sum())
print("inconclusive:", (pw["comparison_status"] == "inconclusive").sum())
print("practical_threshold values:", pw["practical_threshold"].unique())
# BH monotonicity check
print("BH adj p >= raw p for all:", (pw["bh_adjusted_p_value"] >= pw["sign_test_p_value"] - 1e-12).all())

line("J. SCOPE / SAFETY — ranking/tournament/champion columns scan")
for name, df in [("forecasts", fc), ("metrics", mw), ("by_model", by_model), ("pairwise", pw)]:
    bad = [c for c in df.columns if any(k in c.lower() for k in ("rank", "winner", "champion", "tournament_score"))]
    print(f"  {name}: suspicious columns = {bad if bad else 'none'}")

print("\nDONE.")
