"""V6.24-P4 | Write the processed cohort artifacts and the value-preservation audit."""

from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
V617 = OUT.parent / "v6_17_full_multimetric_productive_artifact_generation"

S = json.loads((OUT / "_p4_manifest.json").read_text(encoding="utf-8"))
manifest, AUDIT = S["manifest"], S["audit"]
rows_map = {tuple(k.split("|", 1)): tuple(v) for k, v in S["rows_map"].items()}

hdd = pd.read_pickle(OUT / "_p4_hdd.pkl")
ssd = pd.read_pickle(OUT / "_p4_ssd.pkl")
lvne = pd.read_parquet(RAW / "ssd" / "ssd_lvne_raw.parquet", engine="pyarrow")
cpu = pd.read_parquet(RAW / "cpu" / "cpu_actuals_raw.parquet", engine="pyarrow")
iops = pd.read_parquet(RAW / "iops" / "iops_actuals_raw.parquet", engine="pyarrow")

MAN = pd.DataFrame(manifest)
by_key = {(r["metric"], r["scenario"], r["key"]): r for r in manifest}
hdd_by_route = {rows_map[("HDD", r["series_id"])]: r for r in manifest if r["metric"] == "HDD"}

ACT_COLS = ["cohort_id", "series_id", "metric", "db_type", "variant_contract", "scenario",
            "segment", "demand_nature", "granularity", "key", "route_path", "series_date",
            "actual_value", "actual_value_source_text", "source_object_or_artifact",
            "source_file", "source_row_hash_if_available", "raw_row_count_contribution",
            "duplicate_handling", "freshness_status", "caveat"]


def rowhash(*parts):
    return hashlib.sha1("|".join(str(p) for p in parts).encode()).hexdigest()[:16]


frames = []

# ---------------------------------------------------------------- HDD
hdd = hdd.copy()
hdd["_r"] = list(zip(hdd["metric"], hdd["scenario"], hdd["granularity"], hdd["series_key"]))
h = pd.DataFrame({
    "cohort_id": [hdd_by_route[r]["cohort_id"] for r in hdd["_r"]],
    "series_id": [hdd_by_route[r]["series_id"] for r in hdd["_r"]],
    "metric": "HDD",
    "db_type": [hdd_by_route[r]["db_type"] for r in hdd["_r"]],
    "variant_contract": "NOT_APPLICABLE", "scenario": "NOT_APPLICABLE",
    "segment": [hdd_by_route[r]["segment"] for r in hdd["_r"]],
    "demand_nature": [hdd_by_route[r]["demand_nature"] for r in hdd["_r"]],
    "granularity": [hdd_by_route[r]["granularity"] for r in hdd["_r"]],
    "key": hdd["series_key"].values,
    "route_path": [hdd_by_route[r]["route_path"] for r in hdd["_r"]],
    "series_date": pd.to_datetime(hdd["date"]).values,
    "actual_value": hdd["actual_value"].values,
    "actual_value_source_text": "NOT_PRESENT_IN_SOURCE",
    "source_object_or_artifact": "forecast_viewer_model_outputs_v2_full.parquet",
    "source_file": "outputs/v6_17_full_multimetric_productive_artifact_generation/"
                   "forecast_viewer_model_outputs_v2_full.parquet",
    "source_row_hash_if_available": [rowhash(*r, d) for r, d in zip(hdd["_r"], hdd["date"])],
    "raw_row_count_contribution": 1,
    "duplicate_handling": "DEDUPED_MODEL_AND_RUN_REPETITIONS_OF_SAME_OBSERVATION",
    "freshness_status": "CURRENT",
    "caveat": "None. Actuals, all 15 governed backtests and forecast already local.",
})
frames.append(h)

# ---------------------------------------------------------------- SSD
sm = {k[2]: v for k, v in by_key.items() if k[0] == "SSD"}
s = pd.DataFrame({
    "cohort_id": [sm[k]["cohort_id"] for k in ssd["series_key"]],
    "series_id": [sm[k]["series_id"] for k in ssd["series_key"]],
    "metric": "SSD", "db_type": "Phoenix",
    "variant_contract": "LVWE+LVNE (forecast variants)",
    "scenario": "NOT_APPLICABLE", "segment": "NOT_APPLICABLE",
    "demand_nature": ssd["demand_nature"].values, "granularity": "Forest",
    "key": ssd["series_key"].values,
    "route_path": "SSD|Phoenix|LowVolume|Forest",
    "series_date": pd.to_datetime(ssd["series_date"]).values,
    "actual_value": ssd["actual_value"].values,
    "actual_value_source_text": ssd["actual_value_source_text"].values,
    "source_object_or_artifact": "forecast_substrateBE_ssd_phx_lvwe_metrics",
    "source_file": "data/raw/v6_24_mvp_cohort/ssd/ssd_lvwe_raw.parquet",
    "source_row_hash_if_available": [rowhash("SSD", k, d) for k, d in
                                     zip(ssd["series_key"], ssd["series_date"])],
    "raw_row_count_contribution": 1,
    "duplicate_handling": "EXACT_DUPLICATE_REMOVED_KEEP_FIRST",
    "freshness_status": "CURRENT (to 2026-08-22)",
    "caveat": "AGGREGATED_WINDOW_ACTUALS (rolling window 1-7 days); Mean_Actual CAST from "
              "varchar; 15 governed model backtests DO NOT exist yet; must be generated in P5",
})
frames.append(s)

# ---------------------------------------------------------------- CPU / IOPS
for metric, df, src, path in (
    ("CPU", cpu, "forecast_substrateBE_cpu_actual_region",
     "data/raw/v6_24_mvp_cohort/cpu/cpu_actuals_raw.parquet"),
    ("IOPS", iops, "forecast_substrateBE_iops_actual_region",
     "data/raw/v6_24_mvp_cohort/iops/iops_actuals_raw.parquet"),
):
    mm = {(k[1], k[2]): v for k, v in by_key.items() if k[0] == metric}
    pair = list(zip(df["scenario"], df["series_key"]))
    frames.append(pd.DataFrame({
        "cohort_id": [mm[p]["cohort_id"] for p in pair],
        "series_id": [mm[p]["series_id"] for p in pair],
        "metric": metric, "db_type": df["db_type"].values,
        "variant_contract": "NOT_APPLICABLE", "scenario": df["scenario"].values,
        "segment": "NOT_APPLICABLE", "demand_nature": df["demand_nature"].values,
        "granularity": "Region", "key": df["series_key"].values,
        "route_path": [f"{metric}|Organic|{s}|Region" for s in df["scenario"]],
        "series_date": pd.to_datetime(df["series_date"]).values,
        "actual_value": df["actual_value"].values,
        "actual_value_source_text": "NOT_PRESENT_IN_SOURCE",
        "source_object_or_artifact": src, "source_file": path,
        "source_row_hash_if_available": [rowhash(metric, sc, k, d) for sc, k, d in
                                         zip(df["scenario"], df["series_key"], df["series_date"])],
        "raw_row_count_contribution": 1, "duplicate_handling": "NONE_REQUIRED",
        "freshness_status": "STALE (to 2023-07-20)",
        "caveat": "STALE_ACTUALS_SOURCE, latest date 2023-07-20; 15 governed model backtests "
                  "DO NOT exist yet; must be generated in P5",
    }))

ACT = pd.concat(frames, ignore_index=True)[ACT_COLS]
ACT = ACT.sort_values(["metric", "series_id", "series_date"]).reset_index(drop=True)
print(f"ACTUALS_NORMALIZED: {len(ACT):,} rows over {ACT['series_id'].nunique()} series")
print(ACT.groupby("metric").agg(rows=("series_date", "size"),
                                series=("series_id", "nunique")).to_string())

dupes = int(ACT.duplicated(["series_id", "series_date"]).sum())
if dupes:
    raise SystemExit(f"V6_24_P4_BLOCKED_SERIES_COUNT_MISMATCH: {dupes} duplicate series/date")
print(f"duplicate series_id+series_date: {dupes}")

# --------------------------------------- source forecast baselines
BASE_COLS = ["cohort_id", "series_id", "metric", "db_type", "forecast_variant", "scenario",
             "granularity", "key", "series_date", "source_forecast_value",
             "source_forecast_column", "source_object", "source_file", "caveat"]
bframes = []
for variant, df, obj, path in (
    ("LVWE", ssd, "forecast_substrateBE_ssd_phx_lvwe_metrics",
     "data/raw/v6_24_mvp_cohort/ssd/ssd_lvwe_raw.parquet"),
    ("LVNE", lvne.sort_values(["series_key", "series_date"])
                 .drop_duplicates(["series_key", "series_date"], keep="first"),
     "forecast_substrateBE_ssd_phx_lvne_metrics",
     "data/raw/v6_24_mvp_cohort/ssd/ssd_lvne_raw.parquet"),
):
    bframes.append(pd.DataFrame({
        "cohort_id": [sm[k]["cohort_id"] for k in df["series_key"]],
        "series_id": [sm[k]["series_id"] for k in df["series_key"]],
        "metric": "SSD", "db_type": "Phoenix", "forecast_variant": variant,
        "scenario": "NOT_APPLICABLE", "granularity": "Forest",
        "key": df["series_key"].values,
        "series_date": pd.to_datetime(df["series_date"]).values,
        "source_forecast_value": df["forecast_value"].values,
        "source_forecast_column": "Mean_Forecast",
        "source_object": obj, "source_file": path,
        "caveat": "SOURCE-PROVIDED EXTERNAL BASELINE. This is NOT a 15-model backtest and NOT "
                  "P6 forecast_outputs. Single Forecast_Version 2026-03-12.",
    }))
BASE = pd.concat(bframes, ignore_index=True)[BASE_COLS]
BASE = BASE.sort_values(["series_id", "forecast_variant", "series_date"]).reset_index(drop=True)
print(f"\nSOURCE_FORECAST_BASELINES: {len(BASE):,} rows")
print(BASE.groupby("forecast_variant").agg(rows=("series_date", "size"),
                                           series=("series_id", "nunique")).to_string())

# ------------------------------------------------------ write processed
PROC.mkdir(parents=True, exist_ok=True)
MAN_COLS = ["cohort_id", "series_id", "metric", "db_type", "variant_contract", "scenario",
            "segment", "demand_nature", "granularity", "key", "route_path", "ui_filter_path",
            "source_status", "source_object_or_artifact", "raw_or_local_source_path",
            "date_column_source", "actual_column_source", "value_transformation",
            "min_date", "max_date", "observation_count", "distinct_date_count",
            "duplicate_rows_removed", "freshness_status", "caveat", "selected_for_mvp",
            "selected_for_modeling", "has_actuals", "has_15_model_backtests",
            "has_forecast_outputs", "has_accuracy_metrics", "viewer_visible_now",
            "viewer_visible_after_p7", "p5_required", "p6_required", "p7_required", "notes"]

agg = ACT.groupby("series_id").agg(min_date=("series_date", "min"),
                                   max_date=("series_date", "max"),
                                   observation_count=("series_date", "size"),
                                   distinct_date_count=("series_date", "nunique"))
dupmap = {r["series_key"]: r["rows_removed"] for r in AUDIT["dedup_rows"]}
for r in manifest:
    a = agg.loc[r["series_id"]]
    r["min_date"] = str(a["min_date"])[:10]
    r["max_date"] = str(a["max_date"])[:10]
    r["observation_count"] = int(a["observation_count"])
    r["distinct_date_count"] = int(a["distinct_date_count"])
    r["duplicate_rows_removed"] = int(dupmap.get(r["key"], 0)) if r["metric"] == "SSD" else 0
MAN = pd.DataFrame(manifest)[MAN_COLS]

for name, df in (("cohort_manifest", MAN), ("actuals_normalized", ACT),
                 ("source_forecast_baselines_normalized", BASE)):
    df.to_parquet(PROC / f"{name}.parquet", index=False, engine="pyarrow", compression="snappy")
    df.to_csv(PROC / f"{name}.csv", index=False)
    back = pd.read_parquet(PROC / f"{name}.parquet", engine="pyarrow")
    assert len(back) == len(df), f"{name} round-trip row mismatch"
    print(f"WROTE {name}: {len(df):,} rows x {len(df.columns)} cols (re-read OK)")

AUDIT["actuals_rows"] = int(len(ACT))
AUDIT["baseline_rows"] = int(len(BASE))
json.dump(AUDIT, (OUT / "_p4_audit.json").open("w", encoding="utf-8"), indent=1, default=str)
ACT.to_pickle(OUT / "_p4_act.pkl")
print("\nprocessed artifacts written")
