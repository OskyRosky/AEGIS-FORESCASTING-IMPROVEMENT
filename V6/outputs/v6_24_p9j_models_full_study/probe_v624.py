"""P9J | Does V6.24 carry global ranking / pairwise / global champion / MASE?
Read-only. Answers the questions that decide whether Tournament FULL and
Champion FULL are buildable at all.
"""
import pandas as pd
from pathlib import Path

ROOT = Path(r"C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V6")
D = ROOT / "data" / "processed" / "v6_24_mvp_cohort"

print("=== 1. V6.24 canonical artifacts present ===")
for p in sorted(D.glob("*.parquet")):
    print("  ", p.name)

nav = pd.read_parquet(D / "navigation_contract.parquet")
rk = pd.read_parquet(D / "model_rankings.parquet")
ac = pd.read_parquet(D / "accuracy_metrics.parquet")

print("\n=== 2. Governed model list ===")
V15 = sorted(ac.model_name.unique())
print("  count:", len(V15))
for m in V15: print("   -", m)

print("\n=== 3. Legacy tournament model list vs V6.24 ===")
ts = pd.read_csv(ROOT/"outputs/model_lab/tournament_engine/tournament_preliminary_standings.csv")
L = sorted(ts.model_name.unique())
print("  legacy tournament models:", len(L))
print("  in BOTH:", sorted(set(L) & set(V15)), "=", len(set(L) & set(V15)))
print("  legacy ONLY (absent from V6.24):", sorted(set(L) - set(V15)))
print("  V6.24 ONLY (never in the tournament):", sorted(set(V15) - set(L)))

print("\n=== 4. Legacy scope: how many entities? ===")
sc = pd.read_csv(ROOT/"outputs/model_lab/tournament_engine/tournament_model_scorecard.csv")
print("  scorecard entity_count:", sorted(sc.entity_count.unique()))
print("  V6.24 series:", nav.series_id.nunique())
print("  V6.24 metrics covered:", sorted(nav.metric.unique()))

print("\n=== 5. Does V6.24 carry MASE or RMSSE? ===")
print("  accuracy_metrics columns:", sorted(ac.columns.tolist()))
has = [c for c in ac.columns if "mase" in c.lower() or "rmsse" in c.lower()]
print("  MASE/RMSSE columns ->", has if has else "NONE")

print("\n=== 6. Is model_rankings global or per-series? ===")
print("  rows:", len(rk), " series:", rk.series_id.nunique(), " models:", rk.model_name.nunique())
print("  columns:", sorted(rk.columns.tolist()))
print("  rows per series:", sorted(rk.groupby('series_id').size().unique()))
gl = [c for c in rk.columns if "global" in c.lower() or "overall" in c.lower()]
print("  any GLOBAL rank column ->", gl if gl else "NONE - ranking is per-series only")

print("\n=== 7. Is there a pairwise artifact anywhere in V6.24? ===")
pw = [p.name for p in D.glob("*") if "pair" in p.name.lower() or "tournam" in p.name.lower()]
print("  in the cohort folder ->", pw if pw else "NONE")
v24_out = ROOT / "outputs"
hits = [str(p.relative_to(ROOT)) for p in v24_out.rglob("*")
        if p.is_file() and "v6_24" in str(p).lower()
        and ("pairwise" in p.name.lower() or "tournament" in p.name.lower())]
print("  in V6.24 outputs ->", hits if hits else "NONE")

print("\n=== 8. Is there a GLOBAL champion decision in V6.24? ===")
champ_cols = [c for c in nav.columns if "champion" in c.lower()]
print("  navigation_contract champion columns:", champ_cols)
print("  distinct champion_model_name values across the 140 series:")
vc = nav.champion_model_name.value_counts()
for m, n in vc.items(): print(f"    {m:20s} {n:3d} series")
print("  champion_visible:", dict(nav.champion_visible.astype(str).value_counts()))
print("  champion_validity:", dict(nav.champion_validity.value_counts()))
gc = [p for p in D.glob("*champion*")]
print("  a dedicated global-champion artifact ->", gc if gc else "NONE")

print("\n=== 9. What a Universe FULL page could show ===")
fam = ac.groupby("model_family").model_name.nunique()
print("  governed model_family (3-valued):", dict(fam))
print("  per-model coverage (series each model was scored on):")
cov = ac.groupby("model_name").series_id.nunique()
print("   all equal 140?", bool((cov == 140).all()), "->", sorted(cov.unique()))

print("\n=== 10. Per-model median accuracy across the cohort (medians, not means) ===")
med = ac.groupby("model_name")[["mae", "rmse"]].median().sort_values("mae")
wape_ok = ac[ac.wape_status == "COMPUTED"]
medw = wape_ok.groupby("model_name").wape.median()
med["median_wape"] = medw
print(med.to_string())

print("\n=== 11. Championship counts per model (per-series, visible only) ===")
vis = nav[nav.champion_visible.astype(str).str.upper() == "TRUE"]
print("  series with a presentable champion:", len(vis))
print(dict(vis.champion_model_name.value_counts()))
