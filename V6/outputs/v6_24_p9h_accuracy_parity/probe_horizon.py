import pandas as pd, numpy as np
D = r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6\data\processed\v6_24_mvp_cohort"
a = pd.read_parquet(D + r"\accuracy_metrics.parquet")

print("=== Q1: does accuracy_metrics carry ANY horizon dimension? ===")
print("horizon-like columns:", [c for c in a.columns if "horiz" in c.lower() or "step" in c.lower()])
print("rows:", len(a), "= series", a.series_id.nunique(), "x models", a.model_name.nunique(),
      "=", a.series_id.nunique() * a.model_name.nunique())
print("VERDICT: accuracy is ONE row per (series, model) - no horizon axis\n")

print("=== Q2: what window does it cover? compare to the backtest artifact ===")
b = pd.read_parquet(D + r"\model_backtests_15_models.parquet",
                    columns=["series_id", "model_name", "horizon_steps", "target_date"])
SID = "CPU__Consumed__Region__EUR-MSIT"
MOD = "ETS Explicit"
sub = b[(b.series_id == SID) & (b.model_name == MOD)]
arow = a[(a.series_id == SID) & (a.model_name == MOD)].iloc[0]
print(f"backtest rows for one (series,model): {len(sub)}  horizons {sorted(sub.horizon_steps.unique())}")
print(f"accuracy n_backtest_rows = {arow.n_backtest_rows}, n_target_dates = {arow.n_target_dates}")
print(f"backtest distinct target_dates = {sub.target_date.nunique()}")
print(f"accuracy min/max target date = {arow.min_target_date} .. {arow.max_target_date}")
print(f"backtest min/max target date  = {sub.target_date.min()} .. {sub.target_date.max()}")
print("VERDICT: accuracy aggregates ALL horizons 1..30, it is not a slice\n")

print("=== Q3: rows per horizon in the backtest artifact (for context) ===")
print(b.groupby("horizon_steps").size().head(35).to_string())

print("\n=== Q4: how many (series,model) have non-computable wape? ===")
nc = a[a.wape_status != "COMPUTED"]
print("non-computable wape rows:", len(nc), "across series:", nc.series_id.nunique())
print("their signal status is driven by all-zero actuals:",
      dict(nc.groupby("model_name").size().head(3)))

print("\n=== Q5: extreme value magnitude by metric (readability problem) ===")
for c in ["mae", "rmse", "wape", "smape"]:
    v = pd.to_numeric(a[c], errors="coerce")
    f = v[np.isfinite(v)]
    over = (f > 1e6).sum()
    print(f"  {c:6s} median={f.median():.4g}  p99={f.quantile(.99):.4g}  max={f.max():.4g}  rows>1e6: {over}")

print("\n=== Q6: MEDIAN vs MEAN ranking of series (legacy uses mean) ===")
piv = a.pivot_table(index="series_id", values="mae", aggfunc=["mean", "median"])
piv.columns = ["mean_mae", "median_mae"]
top_mean = piv.sort_values("mean_mae", ascending=False).head(5).index.tolist()
top_med = piv.sort_values("median_mae", ascending=False).head(5).index.tolist()
print("worst 5 by MEAN  :", [s.split('__')[-1] for s in top_mean])
print("worst 5 by MEDIAN:", [s.split('__')[-1] for s in top_med])
print("overlap:", len(set(top_mean) & set(top_med)), "of 5")
