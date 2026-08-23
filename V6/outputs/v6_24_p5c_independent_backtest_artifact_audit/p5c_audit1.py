"""V6.24-P5C | Independent audit of the promoted P5 backtest artifact, part 1.

Every figure is recomputed from the artifacts themselves. P5's own summary
reports are read ONLY to compare claim against measurement, never as evidence.

Audit only. Nothing is modified, no model is run.
"""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work"

GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]
EXPECT = {"rows": 614190, "series": 140, "models": 15, "pairs": 2100,
          "gen_rows": 409890, "hdd_rows": 204300,
          "SSD": (50, 225000), "CPU": (20, 89910), "IOPS": (20, 94980),
          "HDD": (50, 204300)}
A = {}


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# ============================================================ inputs
BTP = PROC / "model_backtests_15_models.parquet"
BTC = PROC / "model_backtests_15_models.csv"
print(f"artifact exists: parquet={BTP.exists()} csv={BTC.exists()}")
BT = pd.read_parquet(BTP, engine="pyarrow")
for c in ("target_date", "train_end_date", "prediction_date"):
    BT[c] = pd.to_datetime(BT[c])
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
GEN = BT[BT["source_generation_status"] == "GENERATED_P5"]
HDD = BT[BT["source_generation_status"] == "REUSED_HDD_EXISTING_ARTIFACT"]
print(f"loaded artifact: {len(BT):,} rows | {BT['series_id'].nunique()} series | "
      f"{BT['model_name'].nunique()} models")

# ============================================================ 2. inventory
F = ["artifact", "path", "exists", "size_bytes", "rows", "columns", "sha256_prefix", "notes"]
csv_rows = sum(1 for _ in BTC.open(encoding="utf-8")) - 1
inv = [
    dict(zip(F, ["final backtests (parquet)", "data/processed/v6_24_mvp_cohort/"
                 "model_backtests_15_models.parquet", BTP.exists(), BTP.stat().st_size,
                 len(BT), len(BT.columns),
                 hashlib.sha256(BTP.read_bytes()).hexdigest()[:16], "The promoted artifact"])),
    dict(zip(F, ["final backtests (csv)", "data/processed/v6_24_mvp_cohort/"
                 "model_backtests_15_models.csv", BTC.exists(), BTC.stat().st_size,
                 csv_rows, len(BT.columns),
                 hashlib.sha256(BTC.read_bytes()).hexdigest()[:16],
                 "Row count must match the parquet"])),
    dict(zip(F, ["actuals_normalized", "data/processed/v6_24_mvp_cohort/"
                 "actuals_normalized.parquet", True,
                 (PROC / "actuals_normalized.parquet").stat().st_size, len(ACT),
                 len(ACT.columns),
                 hashlib.sha256((PROC / "actuals_normalized.parquet").read_bytes()
                                ).hexdigest()[:16], "Reference truth for reconciliation"])),
    dict(zip(F, ["cohort_manifest", "data/processed/v6_24_mvp_cohort/cohort_manifest.parquet",
                 True, (PROC / "cohort_manifest.parquet").stat().st_size, len(MAN),
                 len(MAN.columns),
                 hashlib.sha256((PROC / "cohort_manifest.parquet").read_bytes()
                                ).hexdigest()[:16], "Cohort definition"])),
]
cks = sorted((WORK / "checkpoints").glob("*.parquet"))
inv.append(dict(zip(F, ["P5 checkpoints", "data/model_runs/v6_24_p5_work/checkpoints",
                        len(cks) > 0, sum(p.stat().st_size for p in cks),
                        "see ledger audit", "-", "-", f"{len(cks)} checkpoint files"])))
write("v6_24_p5c_artifact_inventory.csv", F, inv)
A["csv_rows"] = csv_rows

# ============================================================ 3. row counts
F = ["dimension", "value", "series", "models", "series_model_pairs", "rows",
     "expected_rows", "delta", "result"]
rc = []
for st, exp in (("GENERATED_P5", EXPECT["gen_rows"]),
                ("REUSED_HDD_EXISTING_ARTIFACT", EXPECT["hdd_rows"])):
    g = BT[BT["source_generation_status"] == st]
    rc.append(dict(zip(F, ["source_generation_status", st, g["series_id"].nunique(),
                           g["model_name"].nunique(),
                           g.groupby(["series_id", "model_name"]).ngroups, len(g), exp,
                           len(g) - exp, "PASS" if len(g) == exp else "FAIL"])))
for m in ("HDD", "SSD", "CPU", "IOPS"):
    g = BT[BT["metric"] == m]
    es, er = EXPECT[m]
    ok = len(g) == er and g["series_id"].nunique() == es
    rc.append(dict(zip(F, ["metric", m, g["series_id"].nunique(), g["model_name"].nunique(),
                           g.groupby(["series_id", "model_name"]).ngroups, len(g), er,
                           len(g) - er, "PASS" if ok else "FAIL"])))
for (m, st), g in BT.groupby(["metric", "source_generation_status"]):
    rc.append(dict(zip(F, ["metric+status", f"{m} | {st}", g["series_id"].nunique(),
                           g["model_name"].nunique(),
                           g.groupby(["series_id", "model_name"]).ngroups, len(g),
                           EXPECT[m][1], len(g) - EXPECT[m][1],
                           "PASS" if len(g) == EXPECT[m][1] else "FAIL"])))
for (m, mo), g in BT.groupby(["metric", "model_name"]):
    rc.append(dict(zip(F, ["metric+model", f"{m} | {mo}", g["series_id"].nunique(), 1,
                           g["series_id"].nunique(), len(g), "", "",
                           "PASS" if g["series_id"].nunique() == EXPECT[m][0] else "FAIL"])))
rc.append(dict(zip(F, ["TOTAL", "ALL", BT["series_id"].nunique(), BT["model_name"].nunique(),
                       BT.groupby(["series_id", "model_name"]).ngroups, len(BT),
                       EXPECT["rows"], len(BT) - EXPECT["rows"],
                       "PASS" if len(BT) == EXPECT["rows"] else "FAIL"])))
write("v6_24_p5c_row_count_reconciliation.csv", F, rc)
A["row_fail"] = sum(1 for r in rc if r["result"] == "FAIL")

# ============================================================ 4. model catalog
F = ["model_number", "model_name", "present", "exact_spelling_match", "series_covered",
     "rows", "hdd_rows", "generated_rows", "distinct_origins", "result"]
mc = []
for i, m in enumerate(GOVERNED, 1):
    g = BT[BT["model_name"] == m]
    mc.append(dict(zip(F, [i, m, "TRUE" if len(g) else "FALSE",
                           "TRUE" if m in set(BT["model_name"]) else "FALSE",
                           int(g["series_id"].nunique()), len(g),
                           int((g["metric"] == "HDD").sum()),
                           int((g["metric"] != "HDD").sum()),
                           int(g["train_end_date"].nunique()),
                           "PASS" if g["series_id"].nunique() == 140 else "FAIL"])))
for p in PROHIBITED:
    hit = int((BT["model_name"] == p).sum())
    mc.append(dict(zip(F, ["-", f"PROHIBITED: {p}", "TRUE" if hit else "FALSE", "-", 0, hit,
                           0, 0, 0, "FAIL" if hit else "PASS"])))
extra = sorted(set(BT["model_name"]) - set(GOVERNED))
if extra:
    mc.append(dict(zip(F, ["-", f"UNEXPECTED: {extra}", "TRUE", "-", 0, 0, 0, 0, 0, "FAIL"])))
write("v6_24_p5c_model_catalog_audit.csv", F, mc)
A["catalog_fail"] = sum(1 for r in mc if r["result"] == "FAIL")
A["extra_models"] = extra

# ============================================================ 5. series completion
F = ["series_id", "metric", "source_generation_status", "models_present", "expected_models",
     "rows", "distinct_origins", "distinct_target_dates", "min_target", "max_target", "result"]
sc = []
for sid, g in BT.groupby("series_id"):
    sc.append(dict(zip(F, [sid, g["metric"].iloc[0],
                           "|".join(sorted(g["source_generation_status"].unique())),
                           int(g["model_name"].nunique()), 15, len(g),
                           int(g["train_end_date"].nunique()),
                           int(g["target_date"].nunique()),
                           str(g["target_date"].min())[:10], str(g["target_date"].max())[:10],
                           "PASS" if g["model_name"].nunique() == 15 else "FAIL"])))
write("v6_24_p5c_series_model_completion_audit.csv", F, sc)
A["series_fail"] = sum(1 for r in sc if r["result"] == "FAIL")
A["series_count"] = len(sc)

# ============================================================ 6. D2 date audit
off = int((BT["prediction_date"] != BT["target_date"]).sum())
leak_all = int((BT["train_end_date"] >= BT["target_date"]).sum())
leak_gen = int((GEN["train_end_date"] >= GEN["target_date"]).sum())
hz = (BT["target_date"] - BT["train_end_date"]).dt.days
hzm = int((hz != BT["horizon_steps"]).sum())
hzr = int(((BT["horizon_steps"] < 1) | (BT["horizon_steps"] > 30)).sum())
obs_map = ACT.groupby("series_id")["series_date"].apply(set).to_dict()
gen_bad = sum(len(set(g["target_date"]) - obs_map.get(sid, set()))
              for sid, g in GEN.groupby("series_id"))
bts = sorted(GEN["backtest_type"].unique())
F = ["check", "expected", "observed", "severity", "result"]
da = [dict(zip(F, r)) for r in [
    ("prediction_date equals target_date on every row", "0 offsets",
     f"{off} of {len(BT):,}", "CRITICAL", "PASS" if off == 0 else "FAIL"),
    ("train_end_date < target_date on every GENERATED_P5 row", "0 violations",
     f"{leak_gen} of {len(GEN):,}", "CRITICAL", "PASS" if leak_gen == 0 else "FAIL"),
    ("train_end_date < target_date across the whole artifact", "0 violations",
     f"{leak_all} of {len(BT):,}", "CRITICAL", "PASS" if leak_all == 0 else "FAIL"),
    ("horizon_steps equals target_date minus train_end_date", "0 mismatches", f"{hzm}",
     "HIGH", "PASS" if hzm == 0 else "FAIL"),
    ("horizon_steps within 1..30", "0 out of range", f"{hzr}", "HIGH",
     "PASS" if hzr == 0 else "FAIL"),
    ("No invented GENERATED_P5 target dates", "0 outside actuals_normalized", f"{gen_bad}",
     "CRITICAL", "PASS" if gen_bad == 0 else "FAIL"),
    ("No filled dates", "targets are a subset of observed dates", f"{gen_bad} outside",
     "CRITICAL", "PASS" if gen_bad == 0 else "FAIL"),
    ("No resampled dates", "targets are a subset of observed dates", f"{gen_bad} outside",
     "CRITICAL", "PASS" if gen_bad == 0 else "FAIL"),
    ("No interpolated dates", "targets are a subset of observed dates", f"{gen_bad} outside",
     "CRITICAL", "PASS" if gen_bad == 0 else "FAIL"),
    ("D2 policy tagged on generated rows", "D2_SPARSE_OBSERVED_BACKTEST", f"{bts}",
     "HIGH", "PASS" if bts == ["D2_SPARSE_OBSERVED_BACKTEST"] else "FAIL"),
]]
write("v6_24_p5c_d2_date_alignment_audit.csv", F, da)
A["date_fail"] = sum(1 for r in da if r["result"] == "FAIL")
A.update({"off": off, "leak": leak_all, "invented": gen_bad, "hzm": hzm})

# ============================================================ 7. actual reconciliation
truth = ACT[["series_id", "series_date", "actual_value"]].rename(
    columns={"series_date": "target_date", "actual_value": "truth"})
J = GEN.merge(truth, on=["series_id", "target_date"], how="left", indicator=True)
orphan = int((J["_merge"] == "left_only").sum())
both = J[J["_merge"] == "both"]
d = (both["actual_value"] - both["truth"]).abs()
F = ["metric", "checked_rows", "joined_rows", "orphan_rows", "mismatches", "max_abs_delta",
     "result", "notes"]
ar = []
for m in ("SSD", "CPU", "IOPS"):
    s = J[J["metric"] == m]
    sb = s[s["_merge"] == "both"]
    sd = (sb["actual_value"] - sb["truth"]).abs()
    o, mm = int((s["_merge"] == "left_only").sum()), int((sd > 1e-9).sum())
    ar.append(dict(zip(F, [m, len(s), len(sb), o, mm,
                           f"{float(sd.max()) if len(sd) else 0:.3e}",
                           "PASS" if o == 0 and mm == 0 else "FAIL",
                           "Independently re-joined to actuals_normalized."])))
hj = HDD.merge(truth, on=["series_id", "target_date"], how="inner")
hd = (hj["actual_value"] - hj["truth"]).abs()
ar.append(dict(zip(F, ["HDD (overlap only)", len(HDD), len(hj), "NOT_APPLICABLE",
                       int((hd > 1e-6).sum()),
                       f"{float(hd.max()) if len(hd) else 0:.3e}",
                       "PASS" if int((hd > 1e-6).sum()) == 0 else "REVIEW",
                       "Reused rows carry their own actual_value from the v6_17 artifact and "
                       "span a different origin grid, so a full join is not expected. Where "
                       "dates DO overlap actuals_normalized the values are compared."])))
mism = int((d > 1e-9).sum())
ar.append(dict(zip(F, ["ALL GENERATED_P5", len(J), len(both), orphan, mism,
                       f"{float(d.max()) if len(d) else 0:.3e}",
                       "PASS" if orphan == 0 and mism == 0 else "FAIL", ""])))
write("v6_24_p5c_actual_value_reconciliation_audit.csv", F, ar)
A.update({"orphan": orphan, "mismatch": mism,
          "maxdelta": float(d.max()) if len(d) else 0.0,
          "hdd_overlap_rows": len(hj), "hdd_overlap_mismatch": int((hd > 1e-6).sum()),
          "hdd_overlap_maxdelta": float(hd.max()) if len(hd) else 0.0})
print(f"HDD rows overlapping actuals dates: {len(hj):,} | mismatches "
      f"{A['hdd_overlap_mismatch']} | max delta {A['hdd_overlap_maxdelta']:.3e}")

# ============================================================ 8. newest observation
F = ["series_id", "metric", "max_observed_date", "max_backtest_target", "reached",
     "origins", "target_dates", "result"]
no = []
for sid, g in GEN.groupby("series_id"):
    mo, mt = max(obs_map[sid]), g["target_date"].max()
    no.append(dict(zip(F, [sid, g["metric"].iloc[0], str(mo)[:10], str(mt)[:10],
                           "TRUE" if mt == mo else "FALSE",
                           int(g["train_end_date"].nunique()),
                           int(g["target_date"].nunique()),
                           "PASS" if mt == mo else "FAIL"])))
write("v6_24_p5c_newest_observation_preservation_audit.csv", F, no)
A["newest_ok"] = sum(1 for r in no if r["result"] == "PASS")
A["newest_total"] = len(no)

# ============================================================ 9. grain duplicates
GRAIN = ["series_id", "model_name", "target_date", "train_end_date"]
FULL = GRAIN + ["source_generation_status"]
kr = int((BT.groupby(["key", "route_path"])["series_id"].nunique() > 1).sum())
km = int((BT.groupby("key")["series_id"].nunique() > 1).sum())
F = ["check", "grain", "expected", "observed", "result"]
gd = [dict(zip(F, r)) for r in [
    ("No duplicate rows at the full grain", "+".join(FULL), "0",
     f"{int(BT.duplicated(FULL).sum())}", "PASS" if not BT.duplicated(FULL).any() else "FAIL"),
    ("No duplicate rows at the natural grain", "+".join(GRAIN), "0",
     f"{int(BT.duplicated(GRAIN).sum())}", "PASS" if not BT.duplicated(GRAIN).any() else "FAIL"),
    ("No duplicate GENERATED_P5 rows", "+".join(GRAIN), "0",
     f"{int(GEN.duplicated(GRAIN).sum())}",
     "PASS" if not GEN.duplicated(GRAIN).any() else "FAIL"),
    ("No duplicate reused HDD rows after mapping", "+".join(GRAIN), "0",
     f"{int(HDD.duplicated(GRAIN).sum())}",
     "PASS" if not HDD.duplicated(GRAIN).any() else "FAIL"),
    ("No accidental duplication from mixed HDD lineage", "+".join(GRAIN), "0",
     f"{int(HDD.duplicated(GRAIN).sum())} duplicates across "
     f"{HDD['model_run_id'].nunique()} distinct run_id values",
     "PASS" if not HDD.duplicated(GRAIN).any() else "FAIL"),
    ("No key-only join implied", "key+route_path maps to exactly one series_id", "0",
     f"{kr} key+route combinations mapping to more than one series_id; {km} keys spanning "
     f"multiple series_id (expected: 4 HDD keys appear under two routes each)",
     "PASS" if kr == 0 else "FAIL"),
]]
write("v6_24_p5c_grain_duplicate_audit.csv", F, gd)
A["dup_fail"] = sum(1 for r in gd if r["result"] == "FAIL")
A["keys_multi_series"] = km

# ============================================================ 10. numeric sanity
pv = pd.to_numeric(BT["predicted_value"], errors="coerce")
av = pd.to_numeric(BT["actual_value"], errors="coerce")
nan_p = int(pv.isna().sum())
inf_p = int(np.isinf(pv.to_numpy(dtype=float, na_value=0.0)).sum())
F = ["check", "scope", "observed", "severity", "result", "notes"]
ns = [dict(zip(F, r)) for r in [
    ("NaN predicted_value", "all rows", f"{nan_p}", "CRITICAL",
     "PASS" if nan_p == 0 else "FAIL", ""),
    ("Infinite predicted_value", "all rows", f"{inf_p}", "CRITICAL",
     "PASS" if inf_p == 0 else "FAIL", ""),
    ("Non-numeric predicted_value", "all rows",
     f"{int(pv.isna().sum() - BT['predicted_value'].isna().sum())}", "CRITICAL",
     "PASS" if pv.isna().sum() == BT["predicted_value"].isna().sum() else "FAIL", ""),
    ("Negative predicted_value", "all rows", f"{int((pv < 0).sum())}", "MEDIUM", "REVIEW",
     "Demand metrics should not be negative. Baselines clip at zero; some challengers do not."),
    ("Zero predicted_value where actual is non-zero", "all rows",
     f"{int(((pv == 0) & (av != 0)).sum())}", "MEDIUM", "REVIEW",
     "Reported for P6 accuracy review, not a failure condition."),
    ("All-zero model output", "per metric+model",
     f"{int(BT.groupby(['metric', 'model_name'])['predicted_value'].max().eq(0).sum())} "
     f"metric-model combinations predict zero everywhere", "HIGH",
     "PASS" if not BT.groupby(["metric", "model_name"])["predicted_value"].max().eq(0).any()
     else "FAIL", ""),
]]
for (m, mo), g in BT.groupby(["metric", "model_name"]):
    p = pd.to_numeric(g["predicted_value"], errors="coerce")
    const = int(g.groupby("series_id")["predicted_value"].nunique().eq(1).sum())
    ns.append(dict(zip(F, ["prediction distribution", f"{m} | {mo}",
                           f"min={p.min():.4g} median={p.median():.4g} max={p.max():.4g}",
                           "INFO", "INFO",
                           f"{const} of {g['series_id'].nunique()} series where this model "
                           f"predicts a single constant value"])))
for m, g in BT.groupby("metric"):
    a = pd.to_numeric(g["actual_value"], errors="coerce")
    ns.append(dict(zip(F, ["actual distribution", m,
                           f"min={a.min():.4g} median={a.median():.4g} max={a.max():.4g}",
                           "INFO", "INFO", ""])))
write("v6_24_p5c_numeric_sanity_audit.csv", F, ns)
A.update({"nan_p": nan_p, "inf_p": inf_p, "neg_p": int((pv < 0).sum()),
          "numeric_fail": sum(1 for r in ns if r["result"] == "FAIL")})

# ============================================================ 11. extreme predictions
nz = BT[av != 0].copy()
nz["ratio"] = (pd.to_numeric(nz["predicted_value"], errors="coerce")
               / pd.to_numeric(nz["actual_value"], errors="coerce")).abs()
ext = nz[(nz["ratio"] > 100) | (nz["ratio"] < 0.01)]
F = ["metric", "model_name", "series_id", "extreme_rows", "share_of_series_model_rows",
     "min_ratio", "max_ratio", "severity", "notes"]
er = []
for (m, mo, sid), g in ext.groupby(["metric", "model_name", "series_id"]):
    tot = len(BT[(BT["metric"] == m) & (BT["model_name"] == mo) & (BT["series_id"] == sid)])
    er.append(dict(zip(F, [m, mo, sid, len(g), f"{len(g) / tot:.1%}",
                           f"{g['ratio'].min():.3g}", f"{g['ratio'].max():.3g}",
                           "REVIEW_IN_P6",
                           "Ratio outside 0.01..100. Reported, not a failure."])))
er.append(dict(zip(F, ["ALL", "ALL", "ALL", len(ext), f"{len(ext) / len(BT):.4%}",
                       f"{ext['ratio'].min():.3g}" if len(ext) else "-",
                       f"{ext['ratio'].max():.3g}" if len(ext) else "-", "SUMMARY",
                       f"{len(ext):,} of {len(BT):,} rows have |predicted/actual| outside "
                       f"0.01..100."])))
write("v6_24_p5c_extreme_prediction_review.csv", F, er)
A["extreme"] = len(ext)
A["extreme_share"] = len(ext) / len(BT)

json.dump(A, (OUT / "_p5c_a.json").open("w", encoding="utf-8"), indent=1, default=str)
print(f"\nextreme rows: {len(ext):,} ({len(ext) / len(BT):.4%}) | negatives: {A['neg_p']:,}")
print("part 1 complete")
