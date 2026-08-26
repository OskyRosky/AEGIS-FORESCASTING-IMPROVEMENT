import pandas as pd, numpy as np
D = r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6\data\processed\v6_24_mvp_cohort"
a = pd.read_parquet(D + r"\accuracy_metrics.parquet")
print("rows", len(a), "series", a.series_id.nunique(), "models", a.model_name.nunique())
print("\ncolumns:", sorted(a.columns.tolist()))
print("\nstatus cols:")
for c in ["wape_status", "smape_status", "mape_status"]:
    print(" ", c, dict(a[c].value_counts()))
print("\nnumeric ranges (finite only):")
for c in ["mae", "rmse", "wape", "smape", "mape", "bias", "mean_error",
          "median_absolute_error", "n_backtest_rows", "n_target_dates"]:
    v = pd.to_numeric(a[c], errors="coerce")
    f = v[np.isfinite(v)]
    print(f"  {c:24s} finite={len(f):5d} nan={int(v.isna().sum()):4d} "
          f"min={f.min():.4g} med={f.median():.4g} max={f.max():.4g}")
print("\n-- is accuracy per-horizon or aggregated? --")
print("unique (series,model) pairs:", len(a.groupby(['series_id','model_name']).size()))
print("rows per (series,model):", a.groupby(['series_id','model_name']).size().unique())
print("\n-- mean vs median of MAE per model (why mean is unusable) --")
g = a.groupby("model_name")["mae"].agg(["mean", "median", "max"])
print(g.sort_values("median").to_string())
