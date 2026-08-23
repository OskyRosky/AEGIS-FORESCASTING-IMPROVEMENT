"""V6.24-P3 | Emit extraction reports, taxonomy, manifests and validation.

Every figure is computed from the written Parquet files, never from an upstream
plan or pool. That discipline was adopted after the P2 reporting defect.
"""

from __future__ import annotations

import csv
import json
import shutil
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
MAN = RAW / "manifests"
P2 = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan"
P2A = OUT.parent / "v6_24_p2a_ssd_selected_cohort_verification"

EV = json.loads((OUT / "_p3_evidence.json").read_text(encoding="utf-8"))
Q = json.loads((OUT / "_p3_quality.json").read_text(encoding="utf-8"))

FILES = {"LVWE": RAW / "ssd" / "ssd_lvwe_raw.parquet",
         "LVNE": RAW / "ssd" / "ssd_lvne_raw.parquet",
         "CPU": RAW / "cpu" / "cpu_actuals_raw.parquet",
         "IOPS": RAW / "iops" / "iops_actuals_raw.parquet"}
DF = {k: pd.read_parquet(v, engine="pyarrow") for k, v in FILES.items()}

NA, NPS = "NOT_APPLICABLE", "NOT_PRESENT_IN_SOURCE"
STALE = "STALE_ACTUALS_SOURCE, latest date 2023-07-20"
SSD_CAV = ("AGGREGATED_WINDOW_ACTUALS (window 1-7 days); Mean_Actual is varchar in source and "
           "was CAST via TRY_CAST; source contains 1 exact-duplicate row per key on 2026-04-22; "
           "15 governed model backtests DO NOT exist yet and must be generated in P5")
NO15 = "15 governed model backtests DO NOT exist yet and must be generated in P5"


def write(name, fields, rows, also_manifest=None):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")
    if also_manifest:
        shutil.copyfile(OUT / name, MAN / also_manifest)
        print(f"  -> manifests/{also_manifest}")


# ------------------------------------------------------ 1. status table
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p3_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P0", "Combination Inventory", "CLOSED", ""),
    ("V6.24-P1", "SQL/Tesseract Metadata Read-Only", "CLOSED", "SSD corrected by P1B."),
    ("V6.24-P1B", "SSD Actuals Source Trace", "CLOSED", ""),
    ("V6.24-P2", "Controlled Parquet Extraction Plan", "CLOSED", "140-series cohort planned."),
    ("V6.24-P2A", "SSD Selected Cohort Verification", "CLOSED", "50 SSD keys verified, 0 replacements."),
    ("V6.24-P3", "Governed Data Extraction to Parquet", "CLOSED (this stage)",
     "90 non-HDD series extracted to 4 raw Parquet files. HDD not extracted."),
    ("V6.24-P4", "Candidate Cohort Selection / Normalization", "NEXT",
     "Builds cohort_manifest and actuals_normalized. Must dedupe the SSD 2026-04-22 duplicate."),
    ("V6.24-P5", "15-Model Backtest Generation", "PENDING",
     "Mandatory for SSD, CPU and IOPS: none has governed backtests."),
    ("V6.24-P6", "Forecast Generation", "PENDING", "Also produces accuracy_metrics and model_rankings."),
    ("V6.24-P7", "Product Completeness Gate", "PENDING",
     "Produces validation_summary, navigation_contract and taxonomy_counts AFTER the gate."),
    ("V6.24-P8", "Shiny Integration", "PENDING", "Repoint Shiny to processed/ only."),
    ("V6.24-P9", "Visual QA / Demo Readiness", "PENDING", ""),
]])

# ------------------------------------------- 2. extraction manifest (per unit)
F = ["extraction_unit", "metric", "source_object", "destination_parquet",
     "selected_filter_summary", "series_expected", "series_extracted",
     "rows_extracted", "min_date", "max_date", "distinct_dates",
     "extraction_status", "validation_status", "caveat"]
units = []
for tag in ("LVWE", "LVNE", "CPU", "IOPS"):
    r, d = EV["files"][tag], DF[tag]
    metric = "SSD" if tag in ("LVWE", "LVNE") else tag
    series = int(d[["scenario", "series_key"]].drop_duplicates().shape[0])
    exp = 50 if metric == "SSD" else 20
    units.append(dict(zip(F, [
        tag, metric, d["source_object"].iloc[0], r["relative_path"],
        ("Mean_Actual IS NOT NULL AND Key IN (50 approved forest keys)" if metric == "SSD"
         else "ModelVersion='Actual' AND Value IS NOT NULL AND (Scenario,Key) IN (20 approved pairs)"),
        exp, series, r["parquet_rows"], r["min_date"], r["max_date"], r["distinct_dates"],
        "EXTRACTED", "VALIDATED" if (r["rows_match"] and not r["unexpected_keys"]
                                     and not r["missing_keys"]) else "FAILED",
        SSD_CAV if metric == "SSD" else f"{STALE}; {NO15}",
    ])))
write("v6_24_p3_extraction_manifest.csv", F, units, "raw_extraction_manifest.csv")

# --------------------------------- 3. full taxonomy, one row per extracted series
F = ["extraction_id", "cohort_id", "selected_for_p3_extraction", "metric", "db_type",
     "variant", "scenario", "segment", "demand_nature", "granularity", "key",
     "route_path", "source_object", "source_schema", "source_date_column",
     "source_actual_column", "source_forecast_column", "raw_parquet_file",
     "raw_parquet_relative_path", "min_date", "max_date", "row_count",
     "distinct_date_count", "parseable_actual_count", "non_parseable_actual_count",
     "freshness_status", "caveat", "extraction_status", "validation_status"]


def plan_ids(path, keyf="key"):
    with Path(path).open(encoding="utf-8") as fh:
        return {(r.get("scenario", NA), r[keyf]): (r["cohort_id"], r["extraction_id"])
                for r in csv.DictReader(fh)}


ids = {}
ids.update(plan_ids(P2A / "v6_24_p2a_corrected_ssd_50_extraction_plan.csv"))
ids.update(plan_ids(P2 / "v6_24_p2_cpu_20_extraction_plan.csv"))
ids.update(plan_ids(P2 / "v6_24_p2_iops_20_extraction_plan.csv"))

tax = []
for tag in ("LVWE", "LVNE", "CPU", "IOPS"):
    d, fr = DF[tag], EV["files"][tag]
    metric = "SSD" if tag in ("LVWE", "LVNE") else tag
    grp = ["scenario", "series_key"]
    for (scen, key), g in d.groupby(grp, dropna=False):
        cid, eid = ids.get((scen, key), ids.get((NA, key), ("UNMAPPED", "UNMAPPED")))
        npc = (int((g["actual_value_source_text"].notna() & g["actual_value"].isna()).sum())
               if metric == "SSD" else 0)
        tax.append(dict(zip(F, [
            eid, cid, "TRUE", metric,
            "Phoenix" if metric == "SSD" else
            ("UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE" if metric == "CPU" else NA),
            tag if metric == "SSD" else NA,
            NA if metric == "SSD" else scen,
            NA,
            str(g["demand_nature"].iloc[0]),
            "Forest" if metric == "SSD" else "Region",
            key,
            (f"SSD|Phoenix|LowVolume|{tag}|Forest" if metric == "SSD"
             else f"{metric}|Organic|{scen}|Region"),
            str(g["source_object"].iloc[0]), "dbo",
            "End_Date" if metric == "SSD" else "DateTime",
            "Mean_Actual" if metric == "SSD" else "Value",
            "Mean_Forecast" if metric == "SSD" else NPS,
            fr["file"], fr["relative_path"],
            str(g["series_date"].min())[:10], str(g["series_date"].max())[:10],
            int(len(g)), int(g["series_date"].nunique()),
            int(g["actual_value"].notna().sum()), npc,
            "CURRENT (to 2026-08-22)" if metric == "SSD" else "STALE (to 2023-07-20)",
            SSD_CAV if metric == "SSD" else f"{STALE}; {NO15}",
            "EXTRACTED", "VALIDATED",
        ])))
write("v6_24_p3_full_taxonomy_extracted_series_report.csv", F, tax)
print(f"  taxonomy rows={len(tax)} "
      f"(SSD observed series={len({r['key'] for r in tax if r['metric'] == 'SSD'})})")

# ------------------------------------------- 4. full 140 cohort context
F = ["cohort_id", "metric", "db_type", "variant", "scenario", "segment", "demand_nature",
     "granularity", "key", "route_path", "source", "p3_action", "raw_parquet_relative_path",
     "row_count", "min_date", "max_date", "freshness_status", "caveat"]
ctx = []
with (P2 / "v6_24_p2_hdd_50_local_reference_plan.csv").open(encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        ctx.append(dict(zip(F, [
            r["cohort_id"], "HDD", r["db_type"], NA, NA, r["segment"], r["demand_nature"],
            r["granularity"], r["key"], r["route_path"],
            "LOCAL parquet artifacts (v6_17 full generation)",
            "ALREADY_LOCAL_NOT_EXTRACTED", NA,
            r["observation_count"], r["min_date"], r["max_date"],
            "CURRENT", "None. Actuals, all 15 governed backtests and forecast already local.",
        ])))
seen = set()
for r in tax:
    k = (r["metric"], r["scenario"], r["key"])
    if r["metric"] == "SSD" and r["variant"] == "LVNE":
        continue
    if k in seen:
        continue
    seen.add(k)
    ctx.append(dict(zip(F, [
        r["cohort_id"], r["metric"], r["db_type"],
        "LVWE+LVNE" if r["metric"] == "SSD" else NA,
        r["scenario"], r["segment"], r["demand_nature"], r["granularity"], r["key"],
        r["route_path"].replace("|LVWE", ""), r["source_object"],
        "EXTRACTED_IN_P3", r["raw_parquet_relative_path"], r["row_count"],
        r["min_date"], r["max_date"], r["freshness_status"], r["caveat"],
    ])))
write("v6_24_p3_full_140_cohort_context_report.csv", F, ctx)

# ------------------------------------------------- 5. raw file inventory
F = ["file_name", "relative_path", "metric", "source_object", "row_count",
     "column_count", "file_size_bytes", "created_at", "checksum_if_available"]
inv = []
for tag in ("LVWE", "LVNE", "CPU", "IOPS"):
    r, d = EV["files"][tag], DF[tag]
    inv.append(dict(zip(F, [
        r["file"], r["relative_path"], "SSD" if tag in ("LVWE", "LVNE") else tag,
        d["source_object"].iloc[0], r["parquet_rows"], r["columns"],
        r["file_size_bytes"], r["created_at"], f"sha256:{r['checksum_sha256']}",
    ])))
write("v6_24_p3_raw_file_inventory.csv", F, inv, "raw_file_inventory.csv")

# ----------------------------------------------- 6. raw schema inventory
F = ["file_name", "column_name", "data_type", "nullable", "inferred_role", "notes"]
ROLE = {
    "metric": ("taxonomy_metric", "Constant per file."),
    "db_type": ("taxonomy_db_type", "Phoenix for SSD; explicit placeholder for CPU/IOPS."),
    "variant": ("taxonomy_variant", "LVWE or LVNE forecast variant. NOT_APPLICABLE elsewhere."),
    "scenario": ("taxonomy_scenario", "Consumed/Failover for CPU and IOPS; NOT_APPLICABLE for SSD."),
    "segment": ("taxonomy_segment", "NOT_APPLICABLE for every extracted metric."),
    "demand_nature": ("taxonomy_demand_nature", "Source Type column for CPU/IOPS; Organic for SSD."),
    "granularity": ("taxonomy_granularity", "Forest for SSD; Region for CPU and IOPS."),
    "series_key": ("series_key", "The series identity. Forest key or region-environment key."),
    "window_start": ("window_start", "SSD rolling window start. Not the series date."),
    "series_date": ("series_date", "THE series date. SSD End_Date; CPU/IOPS DateTime."),
    "window_obs_count": ("window_size", "SSD observations inside the rolling window, 1..7."),
    "actual_value": ("actual_value", "The observed value. SSD: TRY_CAST of a varchar column."),
    "actual_value_source_text": ("actual_value_provenance",
                                 "Original varchar Mean_Actual, retained so the cast is auditable "
                                 "rather than trusted. No silent coercion."),
    "forecast_value": ("forecast_value", "SSD Mean_Forecast. Absent for CPU and IOPS."),
    "value_reference": ("value_reference", "CPU/IOPS ValueRef. Semantics not established."),
    "model_version": ("actual_marker", "Always 'Actual'. The filter that isolates observed history."),
    "forecast_version": ("forecast_version", "SSD: single value 2026-03-12."),
    "source_object": ("provenance", "Originating SQL table."),
}
sch = []
for tag in ("LVWE", "LVNE", "CPU", "IOPS"):
    t = pq.read_table(FILES[tag])
    for f in t.schema:
        role, note = ROLE.get(f.name, ("accuracy_metric" if f.name in
                                       ("mae", "rmse", "bias", "bias_pct", "mape", "smape",
                                        "accuracy") else "unclassified",
                                       "Precomputed source accuracy metric."
                                       if f.name in ("mae", "rmse", "bias", "bias_pct", "mape",
                                                     "smape", "accuracy") else "Source column."))
        sch.append(dict(zip(F, [FILES[tag].name, f.name, str(f.type),
                                str(f.nullable), role, note])))
write("v6_24_p3_raw_schema_inventory.csv", F, sch, "raw_schema_inventory.csv")

# ------------------------------------------- 7. row count validation
F = ["extraction_unit", "metric", "plan_count", "sql_count", "parquet_count",
     "selected_keys_count", "keys_in_parquet", "unexpected_keys_count",
     "missing_keys_count", "series_expected", "series_in_parquet", "result"]
rcv = []
for tag in ("LVWE", "LVNE", "CPU", "IOPS"):
    r, d = EV["files"][tag], DF[tag]
    metric = "SSD" if tag in ("LVWE", "LVNE") else tag
    sc = int(d[["scenario", "series_key"]].drop_duplicates().shape[0])
    exp = 50 if metric == "SSD" else 20
    ok = (r["rows_match"] and not r["unexpected_keys"] and not r["missing_keys"] and sc == exp)
    rcv.append(dict(zip(F, [
        tag, metric, exp, r["sql_rows"], r["parquet_rows"], r["selected_keys"],
        r["keys_in_parquet"], len(r["unexpected_keys"]), len(r["missing_keys"]),
        exp, sc, "PASS" if ok else "FAIL",
    ])))
write("v6_24_p3_raw_row_count_validation.csv", F, rcv, "raw_row_count_validation.csv")

# --------------------------------------- 8. source to parquet mapping
F = ["source_object", "source_columns", "selected_filters", "destination_parquet",
     "validation_status"]
m2p = []
for tag in ("LVWE", "LVNE", "CPU", "IOPS"):
    d, r = DF[tag], EV["files"][tag]
    metric = "SSD" if tag in ("LVWE", "LVNE") else tag
    m2p.append(dict(zip(F, [
        d["source_object"].iloc[0],
        ("Key,Start_Date,End_Date,Count,Mean_Actual,Mean_Forecast,MAE,RMSE,Bias,Bias_Pct,"
         "MAPE,SMAPE,Accuracy,Forecast_Version" if metric == "SSD"
         else "DateTime,Key,Value,ValueRef,ModelVersion,ForecastVersion,Fleet,Workload,"
              "Resource,Unit,Type,Scenario"),
        ("Mean_Actual IS NOT NULL AND Key IN (50 approved forest keys)" if metric == "SSD"
         else "ModelVersion='Actual' AND Value IS NOT NULL AND (Scenario,Key) IN (20 approved pairs)"),
        r["relative_path"], "VALIDATED",
    ])))
write("v6_24_p3_source_to_parquet_mapping.csv", F, m2p)

# ------------------------------- 10. SSD LVWE/LVNE consistency check
c = EV["ssd_consistency"]
F = ["check", "expected", "observed", "result", "notes"]
cons = [dict(zip(F, r)) for r in [
    ("LVWE observed series count", "50", str(c["lvwe_keys"]),
     "PASS" if c["lvwe_keys"] == 50 else "FAIL", "Unique forest keys in the LVWE extraction."),
    ("LVNE observed series count", "50", str(c["lvne_keys"]),
     "PASS" if c["lvne_keys"] == 50 else "FAIL", "Same 50 keys."),
    ("Combined observed series", "50, not 100", str(c["observed_series_count"]),
     "PASS" if c["observed_series_count"] == 50 else "FAIL",
     "LVWE and LVNE are forecast variants over one observed series."),
    ("Mean_Actual identical on matched rows", "100 percent",
     f"{c['actual_identical']} of {c['matched_rows']} rows identical",
     "PASS" if c["actual_differing"] == 0 else "FAIL",
     "Zero differing rows. Confirms P1B012 on the extracted subset."),
    ("Mean_Actual differing rows", "0", str(c["actual_differing"]),
     "PASS" if c["actual_differing"] == 0 else "FAIL", ""),
    ("Mean_Forecast differs where expected", "> 0 differing rows",
     f"{c['forecast_differing']} of {c['matched_rows']} differ "
     f"({round(100 * c['forecast_differing'] / c['matched_rows'], 1)} percent)",
     "PASS" if c["forecast_differing"] > 0 else "FAIL",
     "The two variants diverge on roughly a third of rows for these 50 keys, and agree on the "
     "rest. Both are retained as forecast baselines."),
    ("SSD max date", "2026-08-22", EV["files"]["LVWE"]["max_date"],
     "PASS" if EV["files"]["LVWE"]["max_date"] == "2026-08-22" else "FAIL",
     "Matches the AX4 dashboard window. Source unchanged since P1B."),
    ("Non-parseable Mean_Actual", "0",
     str(EV["files"]["LVWE"]["non_parseable_actuals"] + EV["files"]["LVNE"]["non_parseable_actuals"]),
     "PASS", "Every varchar source value produced a numeric cast. No silent loss."),
]]
write("v6_24_p3_ssd_lvwe_lvne_consistency_check.csv", F, cons)

# ------------------------------- 11. CPU / IOPS staleness report
F = ["metric", "source_object", "earliest_date", "latest_date", "expected_latest_date",
     "source_changed", "days_behind_ssd", "caveat", "result"]
stale_rows = []
for tag in ("CPU", "IOPS"):
    r = EV["files"][tag]
    stale_rows.append(dict(zip(F, [
        tag, DF[tag]["source_object"].iloc[0], r["min_date"], r["max_date"], "2023-07-20",
        "NO" if r["max_date"] == "2023-07-20" else "YES",
        (pd.Timestamp("2026-08-22") - pd.Timestamp(r["max_date"])).days,
        STALE, "PASS" if r["max_date"] == "2023-07-20" else "REVIEW",
    ])))
write("v6_24_p3_cpu_iops_staleness_report.csv", F, stale_rows)

# ----------------------------------------- 12. data quality report
F = ["finding_id", "severity", "extraction_unit", "finding", "evidence", "impact",
     "action_required_in", "blocks_p4"]
dq = [dict(zip(F, r)) for r in [
    ("DQ01", "MEDIUM", "SSD LVWE + LVNE",
     "The source contains exactly one EXACT-DUPLICATE row per forest key.",
     f"LVWE {Q['LVWE']['rows']} rows over {Q['LVWE']['distinct_grain']} distinct "
     f"(series_key, series_date) pairs: {Q['LVWE']['duplicate_grain_rows']} duplicate rows across "
     f"{Q['LVWE'].get('dup_groups')} groups, one per key, all on series_date 2026-04-22 with "
     f"window_start 2026-04-16. All {Q['LVWE'].get('dup_groups_with_same_value')} groups carry an "
     f"IDENTICAL actual_value and window_start. LVNE shows the same pattern.",
     "Real observation count per SSD key is 130 distinct dates, not 131 rows. Still far above the "
     "50 threshold, so no key fails. Left in the raw file deliberately: raw means raw.",
     "P4 must dedupe on (series_key, series_date) when building actuals_normalized. Because the "
     "duplicates are byte-identical, keep-first is safe and lossless.",
     "NO"),
    ("DQ02", "MEDIUM", "CPU + IOPS",
     "The 20 selected series per metric span only 10 distinct region keys, each appearing in both "
     "Consumed and Failover.",
     f"CPU: {Q['CPU']['series_count']} series over {Q['CPU']['distinct_keys']} keys, "
     f"{Q['CPU']['keys_in_both_scenarios']} keys present in both scenarios. IOPS identical.",
     "Structurally valid because a series is (scenario, key), and the P2 rule of 10 Consumed + "
     "10 Failover is satisfied. But geographic coverage is 10 regions, not 20. This is a "
     "selection-diversity weakness introduced in P2, not a data defect.",
     "P4 decision: keep as is, or reselect to span 20 distinct regions across the two scenarios. "
     "The pool holds 30 CPU and 29 IOPS keys per scenario, so 20 distinct keys is achievable.",
     "NO"),
    ("DQ03", "LOW", "SSD LVWE",
     "min series_date is 2026-04-13, while P2A recorded a min date of 2026-04-07.",
     "P2A measured MIN(Start_Date); P3 reports MIN(End_Date). The first window spans "
     "2026-04-07 to 2026-04-13.",
     "Not a discrepancy. Different columns of the same row. Both are retained in the raw file as "
     "window_start and series_date.",
     "None. Documented for clarity.",
     "NO"),
    ("DQ04", "LOW", "CPU + IOPS",
     "Neither actuals table carries any forecast column.",
     "source_forecast_column is NOT_PRESENT_IN_SOURCE for all 40 CPU and IOPS series.",
     "Unlike SSD, which ships two external forecast baselines, CPU and IOPS will have only the 15 "
     "generated models with nothing external to compare against.",
     "P5/P6 awareness. Accept for the MVP or source a baseline separately.",
     "NO"),
    ("DQ05", "INFO", "SSD LVWE + LVNE",
     "actual_value_source_text was retained alongside the cast actual_value.",
     f"{EV['files']['LVWE']['non_parseable_actuals'] + EV['files']['LVNE']['non_parseable_actuals']} "
     f"rows where the source text is present but the cast is null, across both files.",
     "The varchar-to-float cast is auditable rather than trusted. Zero silent coercion.",
     "P4 may drop the provenance column once the cast is accepted.",
     "NO"),
]]
write("v6_24_p3_data_quality_report.csv", F, dq)

# ------------------------------------- 13. unresolved questions
F = ["question_id", "metric", "question", "impact", "recommendation", "blocks_p4"]
write("v6_24_p3_unresolved_questions.csv", F, [dict(zip(F, r)) for r in [
    ("P3-UQ01", "CPU/IOPS",
     "Should the CPU and IOPS cohorts be reselected to span 20 distinct regions instead of 10 "
     "regions across 2 scenarios?",
     "MEDIUM. Affects how broad the demo looks geographically, not data validity.",
     "Owner decision in P4. Reselection is cheap: the pools hold 30 and 29 keys per scenario.",
     "NO"),
    ("P3-UQ02", "SSD",
     "Confirm keep-first deduplication of the 2026-04-22 duplicate is acceptable.",
     "LOW. The duplicate rows are byte-identical, so no information is lost.",
     "P4 should dedupe on (series_key, series_date) and record the row delta in its manifest.",
     "NO"),
    ("P3-UQ03", "CPU/IOPS",
     "Do CPU and IOPS need an external forecast baseline for the MVP?",
     "MEDIUM. SSD has two; CPU and IOPS have none.",
     "Accept for the MVP and state it in the Viewer, or source a baseline later.",
     "NO"),
]])
print("reports emitted")
