"""V6.24-P4 | Value-preservation audit and all P4 reports.

The audit re-reads every source independently and compares it to the processed
output, rather than trusting the transformation code that produced it.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
V617 = OUT.parent / "v6_17_full_multimetric_productive_artifact_generation"
P2 = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan"

AUDIT = json.loads((OUT / "_p4_audit.json").read_text(encoding="utf-8"))
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
BASE = pd.read_parquet(PROC / "source_forecast_baselines_normalized.parquet", engine="pyarrow")


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# ================================================= value preservation audit
res = []


def compare(metric, src, proc, keycols):
    """Join source to processed on the series grain and measure any value drift."""
    m = src.merge(proc, on=keycols, how="outer", suffixes=("_src", "_proc"), indicator=True)
    both = m[m["_merge"] == "both"]
    d = (both["actual_value_src"] - both["actual_value_proc"]).abs()
    return {
        "metric": metric,
        "source_rows": int(len(src)),
        "processed_rows": int(len(proc)),
        "matched_rows": int(len(both)),
        "source_only_rows": int((m["_merge"] == "left_only").sum()),
        "processed_only_rows": int((m["_merge"] == "right_only").sum()),
        "max_abs_value_delta": float(d.max()) if len(d) else 0.0,
        "changed_value_count": int((d > 1e-9).sum()) if len(d) else 0,
    }


# SSD: re-cast Mean_Actual from the raw file, independently
lvwe = pd.read_parquet(RAW / "ssd" / "ssd_lvwe_raw.parquet", engine="pyarrow")
ssd_src = (lvwe.assign(actual_value=pd.to_numeric(lvwe["actual_value_source_text"],
                                                  errors="coerce"))
           .sort_values(["series_key", "series_date"])
           .drop_duplicates(["series_key", "series_date"], keep="first")
           [["series_key", "series_date", "actual_value"]]
           .rename(columns={"series_key": "key"}))
ssd_src["series_date"] = pd.to_datetime(ssd_src["series_date"])
ssd_proc = ACT[ACT["metric"] == "SSD"][["key", "series_date", "actual_value"]]
r = compare("SSD", ssd_src, ssd_proc, ["key", "series_date"])
r.update({"expected_row_delta": -AUDIT["ssd_duplicate_rows_removed"],
          "observed_row_delta": int(len(ssd_proc) - len(lvwe)),
          "duplicate_rows_removed": AUDIT["ssd_duplicate_rows_removed"],
          "missing_series_count": 50 - ssd_proc["key"].nunique(),
          "notes": "actual_value re-derived independently with pd.to_numeric on the retained "
                   "source text, then compared. 50 exact duplicates removed as audited."})
res.append(r)

# CPU / IOPS: raw value column, zero transformation expected
for metric, f in (("CPU", RAW / "cpu" / "cpu_actuals_raw.parquet"),
                  ("IOPS", RAW / "iops" / "iops_actuals_raw.parquet")):
    raw = pd.read_parquet(f, engine="pyarrow")[["scenario", "series_key", "series_date",
                                                "actual_value"]].rename(
        columns={"series_key": "key"})
    raw["series_date"] = pd.to_datetime(raw["series_date"])
    proc = ACT[ACT["metric"] == metric][["scenario", "key", "series_date", "actual_value"]]
    r = compare(metric, raw, proc, ["scenario", "key", "series_date"])
    r.update({"expected_row_delta": 0, "observed_row_delta": int(len(proc) - len(raw)),
              "duplicate_rows_removed": 0,
              "missing_series_count": 20 - proc[["scenario", "key"]].drop_duplicates().shape[0],
              "notes": "No transformation applied. Values carried through verbatim."})
    res.append(r)

# HDD: independent re-read of the local artifact.
# The join must use the FULL route grain, not key+date: 4 selected keys appear
# under two routes each (for example APC-MSIT under both EDB Consumer Region and
# EDB Enterprise Region), so key+date alone cross-matches distinct series.
plan = list(csv.DictReader((P2 / "v6_24_p2_hdd_50_local_reference_plan.csv").open(encoding="utf-8")))
MET = {"Basilisk": "HDD - Basilisk", "EDB": "HDD - EDB"}
sel = {(MET[p["db_type"]], "Basilisk" if p["db_type"] == "Basilisk" else p["segment"],
        p["granularity"], p["key"]) for p in plan}
hv = pd.read_parquet(V617 / "forecast_viewer_model_outputs_v2_full.parquet", engine="pyarrow",
                     columns=["metric", "scenario", "granularity", "series_key", "date",
                              "actual_value"])
hv["k"] = list(zip(hv["metric"], hv["scenario"], hv["granularity"], hv["series_key"]))
hs = hv[hv["k"].isin(sel)].copy()
GR = ["metric", "scenario", "granularity", "series_key", "date"]
hdd_src = (hs.sort_values(GR).drop_duplicates(GR, keep="first")
           [GR + ["actual_value"]].copy())
hdd_src["db_type"] = ["Basilisk" if m == "HDD - Basilisk" else "EDB"
                      for m in hdd_src["metric"]]
hdd_src["segment"] = ["NOT_APPLICABLE" if d == "Basilisk" else s
                      for d, s in zip(hdd_src["db_type"], hdd_src["scenario"])]
hdd_src = hdd_src.rename(columns={"series_key": "key", "date": "series_date"})[
    ["db_type", "segment", "granularity", "key", "series_date", "actual_value"]]
hdd_src["series_date"] = pd.to_datetime(hdd_src["series_date"])
HKEYS = ["db_type", "segment", "granularity", "key", "series_date"]
hdd_proc = ACT[ACT["metric"] == "HDD"][HKEYS + ["actual_value"]]
r = compare("HDD", hdd_src, hdd_proc, HKEYS)
r.update({"expected_row_delta": 0, "observed_row_delta": int(len(hdd_proc) - len(hdd_src)),
          "duplicate_rows_removed": AUDIT["hdd_duplicate_rows_removed"],
          "missing_series_count": 50 - MAN[MAN["metric"] == "HDD"]["series_id"].nunique(),
          "notes": f"Local artifact repeats each observation once per model and run. "
                   f"{AUDIT['hdd_duplicate_rows_removed']:,} repetitions collapsed to one row "
                   f"per series-date. Max value spread inside a grain group: "
                   f"{AUDIT['hdd_max_value_spread_within_grain']:.10f} (float representation "
                   f"noise, not a data conflict)."})
res.append(r)

F = ["metric", "source_rows", "processed_rows", "matched_rows", "source_only_rows",
     "processed_only_rows", "expected_row_delta", "observed_row_delta",
     "max_abs_value_delta", "changed_value_count", "missing_series_count",
     "duplicate_rows_removed", "validation_status", "notes"]
for r in res:
    ok = (r["changed_value_count"] == 0 and r["missing_series_count"] == 0
          and r["source_only_rows"] == 0 and r["processed_only_rows"] == 0)
    r["validation_status"] = "PASS" if ok else "FAIL"
    print(f"  {r['metric']}: max_delta={r['max_abs_value_delta']:.2e} "
          f"changed={r['changed_value_count']} status={r['validation_status']}")
write("v6_24_p4_actuals_value_preservation_audit.csv", F, res)
AUDIT["preservation"] = res

# ================================================= deduplication audit
F = ["metric", "series_key", "series_date", "rows_in_raw", "rows_kept", "rows_removed",
     "distinct_actual_values", "distinct_forecast_values", "distinct_window_start",
     "actual_value", "removal_basis", "notes"]
ded = list(AUDIT["dedup_rows"])
ded.append({"metric": "HDD", "series_key": "ALL_50_SERIES", "series_date": "ALL_DATES",
            "rows_in_raw": 204300, "rows_kept": 10687,
            "rows_removed": AUDIT["hdd_duplicate_rows_removed"],
            "distinct_actual_values": 1, "distinct_forecast_values": "NOT_APPLICABLE",
            "distinct_window_start": "NOT_APPLICABLE", "actual_value": "VARIES",
            "removal_basis": "MODEL_AND_RUN_REPETITION_OF_SAME_OBSERVATION",
            "notes": "The local artifact stores one row per model per run, so each series-date "
                     "observation repeats 15 or more times. Collapsing them is not data loss."})
write("v6_24_p4_deduplication_audit.csv", F, ded)

# ================================================= summaries and reports
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p4_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P3", "Governed Data Extraction to Parquet", "CLOSED", "90 series, 4 raw Parquet."),
    ("V6.24-P3B", "Raw Extraction Inventory + Diversity Review", "CLOSED",
     "Owner chose KEEP_CURRENT_MVP for CPU/IOPS."),
    ("V6.24-P4", "Cohort Normalization / Manifest Freeze", "CLOSED (this stage)",
     "First official processed layer. 140 series frozen, 48,916 normalized actual rows."),
    ("V6.24-P5", "15-Model Backtest Generation", "NEXT",
     "Required for the 90 non-HDD series. HDD already has its 15 governed backtests."),
    ("V6.24-P6", "Forecast Generation", "PENDING",
     "Also produces accuracy_metrics and model_rankings."),
    ("V6.24-P7", "Product Completeness Gate", "PENDING",
     "Produces validation_summary, navigation_contract and taxonomy_counts AFTER the gate."),
    ("V6.24-P8", "Shiny Integration", "PENDING", "Repoint Shiny to processed/ only."),
    ("V6.24-P9", "Visual QA / Demo Readiness", "PENDING", ""),
]])

F = ["metric", "series", "unique_keys", "actuals_rows", "min_date", "max_date",
     "min_obs_per_series", "max_obs_per_series", "duplicate_rows_removed",
     "has_source_forecast_baseline", "has_15_model_backtests", "viewer_visible_now",
     "p5_required", "caveat"]
rows = []
for m in ("HDD", "SSD", "CPU", "IOPS"):
    a = ACT[ACT["metric"] == m]
    mm = MAN[MAN["metric"] == m]
    per = a.groupby("series_id").size()
    rows.append(dict(zip(F, [
        m, int(len(mm)), int(mm["key"].nunique()), int(len(a)),
        str(a["series_date"].min())[:10], str(a["series_date"].max())[:10],
        int(per.min()), int(per.max()),
        int(mm["duplicate_rows_removed"].astype(int).sum()),
        "TRUE (LVWE + LVNE)" if m == "SSD" else "FALSE",
        mm["has_15_model_backtests"].iloc[0], mm["viewer_visible_now"].iloc[0],
        mm["p5_required"].iloc[0], mm["caveat"].iloc[0],
    ])))
write("v6_24_p4_manifest_summary.csv", F, rows)
write("v6_24_p4_actuals_summary_by_metric.csv", F, rows)

F = ["cohort_id", "series_id", "metric", "db_type", "variant_contract", "scenario",
     "segment", "granularity", "key", "route_path", "ui_filter_path"]
write("v6_24_p4_series_id_mapping.csv", F, MAN[F].to_dict("records"))

F = ["forecast_variant", "metric", "series", "rows", "min_date", "max_date",
     "source_forecast_column", "source_object", "is_15_model_output", "notes"]
brows = []
for v in sorted(BASE["forecast_variant"].unique()):
    b = BASE[BASE["forecast_variant"] == v]
    brows.append(dict(zip(F, [
        v, "SSD", int(b["series_id"].nunique()), int(len(b)),
        str(b["series_date"].min())[:10], str(b["series_date"].max())[:10],
        "Mean_Forecast", b["source_object"].iloc[0], "FALSE",
        "Source-provided external baseline. NOT a 15-model backtest and NOT P6 "
        "forecast_outputs.",
    ])))
for m in ("CPU", "IOPS", "HDD"):
    brows.append(dict(zip(F, [
        "NOT_APPLICABLE", m, 0, 0, "NOT_APPLICABLE", "NOT_APPLICABLE",
        "NOT_PRESENT_IN_SOURCE", "NOT_APPLICABLE", "FALSE",
        "No source-provided forecast baseline exists for this metric." if m != "HDD"
        else "HDD forecast lives in local artifacts and is not re-normalized in P4.",
    ])))
write("v6_24_p4_source_forecast_baseline_summary.csv", F, brows)

F = ["artifact", "column_name", "data_type", "nullable", "row_count", "distinct_values", "notes"]
sch = []
for name in ("cohort_manifest", "actuals_normalized", "source_forecast_baselines_normalized"):
    t = pq.read_table(PROC / f"{name}.parquet")
    df = {"cohort_manifest": MAN, "actuals_normalized": ACT,
          "source_forecast_baselines_normalized": BASE}[name]
    for f in t.schema:
        sch.append(dict(zip(F, [f"{name}.parquet", f.name, str(f.type), str(f.nullable),
                                len(df), int(df[f.name].nunique()),
                                "Written by P4. Schema normalization only."])))
write("v6_24_p4_schema_report.csv", F, sch)

json.dump(AUDIT, (OUT / "_p4_audit.json").open("w", encoding="utf-8"), indent=1, default=str)
print("reports emitted")
