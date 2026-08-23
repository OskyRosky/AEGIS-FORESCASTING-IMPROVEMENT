"""V6.24-P4 | Cohort normalization and manifest freeze.

SCHEMA normalization only. No scaling, standardizing, smoothing, interpolation,
date filling, or value recomputation. Values are carried through unchanged; the
only permitted transformations are:
  - varchar -> float cast for SSD Mean_Actual (audited, original text retained)
  - removal of EXACT duplicate rows (audited row by row)

HDD lineage note
----------------
forecast_viewer_model_outputs_v2_full.parquet mixes two extraction lineages:
  R6P1-20260812T100822            -> 44 of the 50 selected series
  LEGACY_STAGE05H_VERIFIED_R8FIX0 -> the remaining 6 (EDB Enterprise Region)
The two are DISJOINT over the selected set (0 grain groups appear in both), so
the union is unambiguous. Within LEGACY a grain can repeat across run_ids, but
the values agree to float representation noise: measured absolute spread is
0.000000 across all 808 such groups. The audit records that spread.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P2 = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan"
V617 = OUT.parent / "v6_17_full_multimetric_productive_artifact_generation"

NA, NPS = "NOT_APPLICABLE", "NOT_PRESENT_IN_SOURCE"
UNK_DB = "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE"
LOCAL = "ALREADY_LOCAL_NOT_EXTRACTED"
STALE = "STALE_ACTUALS_SOURCE, latest date 2023-07-20"
NO15 = "15 governed model backtests DO NOT exist yet; must be generated in P5"
AUDIT = {}


def slug(s):
    return re.sub(r"[^A-Za-z0-9]+", "-", str(s)).strip("-")


def read_plan(p):
    with Path(p).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# ============================================================ HDD
hdd_plan = read_plan(P2 / "v6_24_p2_hdd_50_local_reference_plan.csv")
MET = {"Basilisk": "HDD - Basilisk", "EDB": "HDD - EDB"}
hdd_sel = {}
for r in hdd_plan:
    scen = "Basilisk" if r["db_type"] == "Basilisk" else r["segment"]
    hdd_sel[(MET[r["db_type"]], scen, r["granularity"], r["key"])] = r

hv = pd.read_parquet(
    V617 / "forecast_viewer_model_outputs_v2_full.parquet", engine="pyarrow",
    columns=["metric", "scenario", "granularity", "series_key", "date", "actual_value",
             "extraction_run_id", "run_id"])
hv["k"] = list(zip(hv["metric"], hv["scenario"], hv["granularity"], hv["series_key"]))
hs = hv[hv["k"].isin(hdd_sel)].copy()
print(f"HDD selected rows in artifact: {len(hs):,} over {hs['k'].nunique()} series")

GR = ["metric", "scenario", "granularity", "series_key", "date"]
spread = hs.groupby(GR)["actual_value"].agg(["min", "max"])
AUDIT["hdd_max_value_spread_within_grain"] = float((spread["max"] - spread["min"]).max())
AUDIT["hdd_lineages"] = {k: int(v) for k, v in
                         hs.drop_duplicates(["k", "extraction_run_id"])
                         .groupby("extraction_run_id")["k"].size().items()}
print(f"HDD max value spread within a grain group: {AUDIT['hdd_max_value_spread_within_grain']:.10f}")
print(f"HDD lineages: {AUDIT['hdd_lineages']}")

hs = hs.sort_values(GR + ["extraction_run_id", "run_id"])
hdd_rows_before = len(hs)
hdd = hs.drop_duplicates(GR, keep="first").copy()
AUDIT["hdd_duplicate_rows_removed"] = hdd_rows_before - len(hdd)
print(f"HDD actuals: {hdd_rows_before:,} -> {len(hdd):,} "
      f"(removed {AUDIT['hdd_duplicate_rows_removed']:,} model/run repetitions of the same "
      f"series-date observation)")

# ============================================================ SSD / CPU / IOPS
lvwe = pd.read_parquet(RAW / "ssd" / "ssd_lvwe_raw.parquet", engine="pyarrow")
lvne = pd.read_parquet(RAW / "ssd" / "ssd_lvne_raw.parquet", engine="pyarrow")
cpu = pd.read_parquet(RAW / "cpu" / "cpu_actuals_raw.parquet", engine="pyarrow")
iops = pd.read_parquet(RAW / "iops" / "iops_actuals_raw.parquet", engine="pyarrow")

bad = int((lvwe["actual_value_source_text"].notna() & lvwe["actual_value"].isna()).sum())
if bad:
    raise SystemExit(f"V6_24_P4_BLOCKED_VALUE_PRESERVATION_FAILURE: {bad} unparseable Mean_Actual")
AUDIT["ssd_unparseable"] = bad

SG = ["series_key", "series_date"]
dup_mask = lvwe.duplicated(subset=SG, keep=False)
dups = lvwe[dup_mask].copy()
conflict = int((dups.groupby(SG)["actual_value"].nunique() > 1).sum())
if conflict:
    raise SystemExit(f"V6_24_P4_BLOCKED_CONFLICTING_DUPLICATES: {conflict} conflicting groups")
ssd_before = len(lvwe)
ssd = lvwe.sort_values(SG).drop_duplicates(SG, keep="first").copy()
AUDIT["ssd_duplicate_rows_removed"] = ssd_before - len(ssd)
AUDIT["ssd_duplicate_conflicts"] = conflict
print(f"SSD actuals: {ssd_before:,} -> {len(ssd):,} "
      f"(removed {AUDIT['ssd_duplicate_rows_removed']} EXACT duplicates, 0 conflicts)")

dedup_rows = []
for (k, dt), g in dups.groupby(SG):
    dedup_rows.append({
        "metric": "SSD", "series_key": k, "series_date": str(dt)[:10],
        "rows_in_raw": int(len(g)), "rows_kept": 1,
        "rows_removed": int(len(g) - 1),
        "distinct_actual_values": int(g["actual_value"].nunique()),
        "distinct_forecast_values": int(g["forecast_value"].nunique()),
        "distinct_window_start": int(g["window_start"].nunique()),
        "actual_value": float(g["actual_value"].iloc[0]),
        "removal_basis": "EXACT_DUPLICATE",
        "notes": "All value-bearing columns identical. Keep-first is lossless.",
    })
AUDIT["dedup_rows"] = dedup_rows

# ============================================================ series identity
def hdd_ids(r):
    seg = r["segment"] if r["segment"] != NA else "NA"
    return f"HDD__{r['db_type']}__{seg}__{r['granularity']}__{slug(r['key'])}"


manifest, rows_map = [], {}
for r in hdd_plan:
    scen = "Basilisk" if r["db_type"] == "Basilisk" else r["segment"]
    rows_map[("HDD", hdd_ids(r))] = (MET[r["db_type"]], scen, r["granularity"], r["key"])
    manifest.append({
        "metric": "HDD", "series_id": hdd_ids(r), "db_type": r["db_type"],
        "variant_contract": NA, "scenario": NA, "segment": r["segment"],
        "demand_nature": r["demand_nature"], "granularity": r["granularity"],
        "key": r["key"], "route_path": r["route_path"],
        "ui_filter_path": (f"Metric=HDD > DBType={r['db_type']} > Segment={r['segment']} > "
                           f"Granularity={r['granularity']} > Key={r['key']}"),
        "source_status": LOCAL,
        "source_object_or_artifact": "forecast_viewer_model_outputs_v2_full.parquet",
        "raw_or_local_source_path":
            "V6/outputs/v6_17_full_multimetric_productive_artifact_generation/"
            "forecast_viewer_model_outputs_v2_full.parquet",
        "date_column_source": "date", "actual_column_source": "actual_value",
        "freshness_status": "CURRENT",
        "caveat": "None. Actuals, all 15 governed backtests and forecast already local.",
        "has_15_model_backtests": "TRUE", "has_forecast_outputs": "TRUE",
        "has_accuracy_metrics": "TRUE", "viewer_visible_now": "TRUE",
        "p5_required": "FALSE", "p6_required": "FALSE",
        "notes": "Not extracted in P3. Folded into the cohort from local artifacts so Viewer "
                 "and Forecast share one manifest.",
    })
for key in sorted(ssd["series_key"].unique()):
    manifest.append({
        "metric": "SSD", "series_id": f"SSD__Phoenix__Forest__{slug(key)}",
        "db_type": "Phoenix", "variant_contract": "LVWE+LVNE (forecast variants)",
        "scenario": NA, "segment": NA, "demand_nature": "Organic",
        "granularity": "Forest", "key": key,
        "route_path": "SSD|Phoenix|LowVolume|Forest",
        "ui_filter_path": f"Metric=SSD > DBType=Phoenix > Variant=LVWE|LVNE > "
                          f"Granularity=Forest > Key={key}",
        "source_status": "EXTRACTED_IN_P3",
        "source_object_or_artifact": "forecast_substrateBE_ssd_phx_lvwe_metrics",
        "raw_or_local_source_path": "V6/data/raw/v6_24_mvp_cohort/ssd/ssd_lvwe_raw.parquet",
        "date_column_source": "End_Date", "actual_column_source": "Mean_Actual",
        "freshness_status": "CURRENT (to 2026-08-22)",
        "caveat": f"AGGREGATED_WINDOW_ACTUALS (rolling window 1-7 days); {NO15}",
        "has_15_model_backtests": "FALSE", "has_forecast_outputs": "FALSE",
        "has_accuracy_metrics": "FALSE", "viewer_visible_now": "FALSE",
        "p5_required": "TRUE", "p6_required": "TRUE",
        "notes": "Actuals taken from LVWE only. LVNE contributes a second source forecast "
                 "baseline and must never be loaded as a second actual series.",
    })
for metric, df, dbt, src, path in (
    ("CPU", cpu, UNK_DB, "forecast_substrateBE_cpu_actual_region",
     "V6/data/raw/v6_24_mvp_cohort/cpu/cpu_actuals_raw.parquet"),
    ("IOPS", iops, NA, "forecast_substrateBE_iops_actual_region",
     "V6/data/raw/v6_24_mvp_cohort/iops/iops_actuals_raw.parquet"),
):
    for (scen, key) in sorted(map(tuple, df[["scenario", "series_key"]].drop_duplicates().values)):
        manifest.append({
            "metric": metric, "series_id": f"{metric}__{scen}__Region__{slug(key)}",
            "db_type": dbt, "variant_contract": NA, "scenario": scen, "segment": NA,
            "demand_nature": str(df[df["series_key"] == key]["demand_nature"].iloc[0]),
            "granularity": "Region", "key": key,
            "route_path": f"{metric}|Organic|{scen}|Region",
            "ui_filter_path": f"Metric={metric} > Scenario={scen} > Granularity=Region > Key={key}",
            "source_status": "EXTRACTED_IN_P3", "source_object_or_artifact": src,
            "raw_or_local_source_path": path,
            "date_column_source": "DateTime", "actual_column_source": "Value",
            "freshness_status": "STALE (to 2023-07-20)",
            "caveat": f"{STALE}; {NO15}",
            "has_15_model_backtests": "FALSE", "has_forecast_outputs": "FALSE",
            "has_accuracy_metrics": "FALSE", "viewer_visible_now": "FALSE",
            "p5_required": "TRUE", "p6_required": "TRUE",
            "notes": f"No source forecast baseline exists for {metric}.",
        })

ORDER = {"HDD": 0, "SSD": 1, "CPU": 2, "IOPS": 3}
manifest.sort(key=lambda r: (ORDER[r["metric"]], r["route_path"], r["key"]))
for i, r in enumerate(manifest, 1):
    r["cohort_id"] = f"V6_24_MVP_{i:04d}"
    r["value_transformation"] = ("CAST_VARCHAR_TO_FLOAT" if r["metric"] == "SSD"
                                 else "NONE")
    r["selected_for_mvp"] = "TRUE"
    r["selected_for_modeling"] = "TRUE"
    r["has_actuals"] = "TRUE"
    r["viewer_visible_after_p7"] = "TRUE"
    r["p7_required"] = "TRUE"
print(f"MANIFEST: {len(manifest)} series")

json.dump({"manifest": manifest, "audit": AUDIT, "rows_map":
           {f"{k[0]}|{k[1]}": list(v) for k, v in rows_map.items()}},
          (OUT / "_p4_manifest.json").open("w", encoding="utf-8"), indent=1, default=str)

# stash the prepared frames for the writer step
hdd.to_pickle(OUT / "_p4_hdd.pkl")
ssd.to_pickle(OUT / "_p4_ssd.pkl")
print("normalization prepared")
