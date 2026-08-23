"""V6.24-P5 | HDD reuse mapping and final artifact assembly.

HDD is NOT re-run. Its existing backtest rows are read from the v6_17 artifact
that P4 already reconciled, mapped into the P5 schema, and marked
REUSED_HDD_EXISTING_ARTIFACT.

The join uses the FULL route grain, never key alone: four HDD keys appear under
two routes each, so a key-only join would cross-match distinct series. That was
the exact defect caught in P4.

The final artifact is written only if every promotion condition holds.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work"
V617 = OUT.parent / "v6_17_full_multimetric_productive_artifact_generation"

RUN = json.loads((OUT / "_p5_run.json").read_text(encoding="utf-8"))
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])

SCHEMA = ["cohort_id", "series_id", "metric", "db_type", "scenario", "segment",
          "granularity", "key", "route_path", "model_name", "model_family",
          "target_date", "prediction_date", "train_start_date", "train_end_date",
          "horizon_steps", "actual_value", "predicted_value", "backtest_type",
          "burn_in_count", "source_actuals_artifact", "model_run_id",
          "source_generation_status", "model_status", "runtime_seconds", "caveat"]

# ------------------------------------------------- reassemble generated rows
cks = sorted((WORK / "checkpoints").glob("*.parquet"))
GEN = pd.concat([pd.read_parquet(c, engine="pyarrow") for c in cks], ignore_index=True)
print(f"GENERATED: {len(GEN):,} rows from {len(cks)} checkpoints | "
      f"{GEN['series_id'].nunique()} series | {GEN['model_name'].nunique()} models")
assert len(GEN) == RUN["rows"], f"checkpoint total {len(GEN)} != ledger {RUN['rows']}"

# ------------------------------------------------- HDD reuse
hdd_man = MAN[MAN["metric"] == "HDD"].copy()
MET = {"Basilisk": "HDD - Basilisk", "EDB": "HDD - EDB"}
hdd_man["_art_metric"] = hdd_man["db_type"].map(MET)
hdd_man["_art_scenario"] = [("Basilisk" if d == "Basilisk" else s)
                            for d, s in zip(hdd_man["db_type"], hdd_man["segment"])]
route_to_series = {(r["_art_metric"], r["_art_scenario"], r["granularity"], r["key"]): r
                   for _, r in hdd_man.iterrows()}
print(f"HDD cohort: {len(hdd_man)} series over {hdd_man['key'].nunique()} unique keys "
      f"(4 keys appear under two routes, so the join must use the full route grain)")

HV = pd.read_parquet(V617 / "forecast_viewer_model_outputs_v2_full.parquet", engine="pyarrow",
                     columns=["metric", "scenario", "granularity", "series_key", "date",
                              "actual_value", "model_name", "forecast_value",
                              "forecast_start_date", "horizon_days", "extraction_run_id",
                              "run_id", "forecast_type"])
HV["_k"] = list(zip(HV["metric"], HV["scenario"], HV["granularity"], HV["series_key"]))
HS = HV[HV["_k"].isin(route_to_series)].copy()
print(f"HDD source rows for the 50 cohort series: {len(HS):,}")

GRAIN = ["_k", "model_name", "forecast_start_date", "date"]
before = len(HS)
HS = HS.sort_values(GRAIN + ["extraction_run_id", "run_id"]).drop_duplicates(GRAIN, keep="first")
print(f"HDD deduped on (route, model, origin, target): {before:,} -> {len(HS):,} "
      f"(removed {before - len(HS):,} run-level repetitions)")

meta = pd.DataFrame([route_to_series[k] for k in HS["_k"]]).reset_index(drop=True)
FAM = {**{m: "Baseline" for m in
          ("FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
           "ARIMA_Fixed", "ETS_Current", "LinearRegression")},
       **{m: "Challenger" for m in
          ("AutoARIMA", "ETS Explicit", "Theta", "LightGBM", "XGBoost")},
       **{m: "Neural" for m in ("FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN")}}

HDD = pd.DataFrame({
    "cohort_id": meta["cohort_id"].values, "series_id": meta["series_id"].values,
    "metric": "HDD", "db_type": meta["db_type"].values, "scenario": "NOT_APPLICABLE",
    "segment": meta["segment"].values, "granularity": meta["granularity"].values,
    "key": meta["key"].values, "route_path": meta["route_path"].values,
    "model_name": HS["model_name"].values,
    "model_family": [FAM.get(m, "UNKNOWN") for m in HS["model_name"]],
    "target_date": pd.to_datetime(HS["date"]).values,
    "prediction_date": pd.to_datetime(HS["date"]).values,
    "train_start_date": pd.NaT,
    "train_end_date": pd.to_datetime(HS["forecast_start_date"]).values,
    "horizon_steps": HS["horizon_days"].astype(int).values,
    "actual_value": HS["actual_value"].values,
    "predicted_value": HS["forecast_value"].values,
    "backtest_type": "REUSED_LEGACY_BACKTEST",
    "burn_in_count": -1,
    "source_actuals_artifact":
        "outputs/v6_17_full_multimetric_productive_artifact_generation/"
        "forecast_viewer_model_outputs_v2_full.parquet",
    "model_run_id": HS["run_id"].values,
    "source_generation_status": "REUSED_HDD_EXISTING_ARTIFACT",
    "model_status": "OK", "runtime_seconds": 0.0,
    "caveat": [f"Reused from the local v6_17 artifact, not recomputed in P5. Lineage: {e}. "
               f"train_start_date and burn_in_count are NOT_PRESENT_IN_SOURCE."
               for e in HS["extraction_run_id"]],
})
# train_end_date is the origin, so horizon_steps must reconcile with the dates.
calc = (pd.to_datetime(HDD["target_date"]) - pd.to_datetime(HDD["train_end_date"])).dt.days
mismatch = int((calc != HDD["horizon_steps"]).sum())
print(f"HDD horizon reconciliation: {mismatch} rows where "
      f"target_date - train_end_date != horizon_days")
if mismatch:
    HDD["horizon_steps"] = calc.astype(int)
    print("  -> horizon_steps recomputed from the dates so the invariant holds")

print(f"HDD MAPPED: {len(HDD):,} rows | {HDD['series_id'].nunique()} series | "
      f"{HDD['model_name'].nunique()} models")

# ------------------------------------------------- assemble
FINAL = pd.concat([HDD[SCHEMA], GEN[SCHEMA]], ignore_index=True)
FINAL = FINAL.sort_values(["metric", "series_id", "model_name", "train_end_date",
                           "target_date"]).reset_index(drop=True)
print(f"\nFINAL: {len(FINAL):,} rows | {FINAL['series_id'].nunique()} series | "
      f"{FINAL['model_name'].nunique()} models")
print(FINAL.groupby(["metric", "source_generation_status"]).agg(
    rows=("target_date", "size"), series=("series_id", "nunique"),
    models=("model_name", "nunique")).to_string())

# ------------------------------------------------- promotion gate
gates = []


def gate(name, expected, observed, ok):
    gates.append({"condition": name, "expected": expected, "observed": observed,
                  "result": "PASS" if ok else "FAIL"})
    return ok


nh = FINAL[FINAL["metric"] != "HDD"]
per = nh.groupby(["metric", "series_id"])["model_name"].nunique()
gate("90 non-HDD series completed", "90", f"{nh['series_id'].nunique()}",
     nh["series_id"].nunique() == 90)
gate("1,350 non-HDD model-series runs completed", "1350",
     f"{RUN['done_ms']} in the execution ledger; "
     f"{nh.groupby(['series_id', 'model_name']).ngroups} distinct pairs in the artifact",
     RUN["done_ms"] == 1350 and nh.groupby(["series_id", "model_name"]).ngroups == 1350)
gate("All 15 models present for every non-HDD series", "15 per series",
     f"min {int(per.min())}, max {int(per.max())}", int(per.min()) == 15)
gate("HDD reuse mapped safely", "50 series, 15 models, no re-run",
     f"{HDD['series_id'].nunique()} series, {HDD['model_name'].nunique()} models, "
     f"{len(HDD):,} rows reused",
     HDD["series_id"].nunique() == 50 and HDD["model_name"].nunique() == 15)
gate("Final artifact covers 140 MVP series", "140", f"{FINAL['series_id'].nunique()}",
     FINAL["series_id"].nunique() == 140)
allper = FINAL.groupby("series_id")["model_name"].nunique()
gate("15 models per series across the whole artifact", "15",
     f"min {int(allper.min())}, max {int(allper.max())}", int(allper.min()) == 15)
off = int((FINAL["prediction_date"] != FINAL["target_date"]).sum())
gate("prediction_date equals target_date", "0 offsets", f"{off}", off == 0)
leak = int((pd.to_datetime(FINAL["train_end_date"])
            >= pd.to_datetime(FINAL["target_date"])).sum())
gate("train_end_date < target_date", "0 violations", f"{leak}", leak == 0)

truth = ACT[["series_id", "series_date", "actual_value"]].rename(
    columns={"series_date": "target_date", "actual_value": "truth"})
J = nh.merge(truth, on=["series_id", "target_date"], how="left", indicator=True)
orphan = int((J["_merge"] == "left_only").sum())
both = J[J["_merge"] == "both"]
delta = (both["actual_value"] - both["truth"]).abs()
mism = int((delta > 1e-9).sum())
gate("Every non-HDD target_date exists in actuals_normalized", "0 orphans", f"{orphan}",
     orphan == 0)
gate("actual_value matches actuals_normalized", "0 mismatches",
     f"{mism}, max delta {float(delta.max()) if len(delta) else 0:.2e}", mism == 0)
nan = int(FINAL["predicted_value"].isna().sum())
gate("No NaN predicted_value", "0", f"{nan}", nan == 0)
dup = int(FINAL.duplicated(["series_id", "model_name", "target_date",
                            "train_end_date"]).sum())
gate("No duplicate series/model/target/origin rows", "0", f"{dup}", dup == 0)
gate("No unresolved model failures", "0", f"{RUN['failures']}", RUN["failures"] == 0)
gate("Budget respected", "< 120 minutes",
     f"{RUN['minutes']}m, about {RUN['minutes'] / 120:.1%} of the hard budget",
     RUN["minutes"] < 120)

PROMOTE = all(g["result"] == "PASS" for g in gates)
print("\n=== PROMOTION GATE ===")
for g in gates:
    print(f"  {g['result']:<5} {g['condition']:<52} {g['observed']}")
print(f"\nPROMOTE = {PROMOTE}")

if PROMOTE:
    FINAL.to_parquet(PROC / "model_backtests_15_models.parquet", index=False,
                     engine="pyarrow", compression="snappy")
    FINAL.to_csv(PROC / "model_backtests_15_models.csv", index=False)
    back = pd.read_parquet(PROC / "model_backtests_15_models.parquet", engine="pyarrow")
    assert len(back) == len(FINAL)
    print(f"PROMOTED: model_backtests_15_models.parquet ({len(back):,} rows, re-read OK)")
else:
    print("NOT PROMOTED. Checkpoints retained in work/.")

with (OUT / "v6_24_p5_promotion_gate.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=["condition", "expected", "observed", "result"])
    w.writeheader()
    w.writerows(gates)

FINAL.to_pickle(OUT / "_p5_final.pkl")
HDD.to_pickle(OUT / "_p5_hdd.pkl")
json.dump({"promoted": PROMOTE, "final_rows": len(FINAL), "hdd_rows": len(HDD),
           "gen_rows": len(GEN), "orphan": orphan, "mismatch": mism, "offset": off,
           "leak": leak, "nan": nan, "dup": dup,
           "hdd_dedup_removed": before - len(HS),
           "hdd_horizon_recomputed": mismatch},
          (OUT / "_p5_assembly.json").open("w", encoding="utf-8"), indent=1)
