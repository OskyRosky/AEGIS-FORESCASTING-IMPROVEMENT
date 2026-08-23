"""V6.24-P2 | Emit the plan deliverables from the deterministic selection.

No SQL. No Parquet. Plan artifacts only.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
sel = json.loads((OUT / "_p2_selection.json").read_text(encoding="utf-8"))
rows = sel["rows"]
FIELDS = list(rows[0].keys())


def write(name, fields, data):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(data)
    print(f"{name}|rows={len(data)}")


# 1. reduced status table
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p2_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P0", "Combination Inventory / Artifact Reality Check", "CLOSED",
     "596 HDD product-complete measured locally."),
    ("V6.24-P1", "SQL/Tesseract Metadata Read-Only", "CLOSED",
     "HDD/CPU/IOPS/Memory confirmed. SSD conclusion was wrong and was corrected by P1B."),
    ("V6.24-P1B", "SSD Actuals Source Trace / AX4 Reconciliation", "CLOSED",
     "SSD actuals confirmed in LVWE/LVNE, 136 keys over 50, reconciled with AX4."),
    ("V6.24-P2", "Controlled Parquet Extraction Plan", "CLOSED (this stage)",
     "140-series cohort planned; 90 series scheduled for P3. No data extracted."),
    ("V6.24-P3", "Governed Data Extraction to Parquet", "NEXT",
     "THE EXTRACTION STAGE. Executes the templates produced here."),
    ("V6.24-P4", "Candidate Cohort Selection 130-150", "PENDING", ""),
    ("V6.24-P5", "15-Model Backtest Generation", "PENDING",
     "Mandatory for SSD, CPU and IOPS: none of them has governed backtests yet."),
    ("V6.24-P6", "Forecast Generation", "PENDING", ""),
    ("V6.24-P7", "Product Completeness Gate", "PENDING", "Enforces Viewer = Forecast parity."),
    ("V6.24-P8", "Shiny Integration", "PENDING", "Shiny must read processed cohort artifacts only."),
    ("V6.24-P9", "Visual QA / Demo Readiness", "PENDING", ""),
]])

# 2-7. cohort and per-metric plans
write("v6_24_p2_full_140_mvp_cohort_plan.csv", FIELDS, rows)
write("v6_24_p2_p3_90_series_extraction_plan.csv", FIELDS,
      [r for r in rows if r["selected_for_p3_extraction"] == "TRUE"])
write("v6_24_p2_hdd_50_local_reference_plan.csv", FIELDS,
      [r for r in rows if r["metric"] == "HDD"])
write("v6_24_p2_ssd_50_extraction_plan.csv", FIELDS,
      [r for r in rows if r["metric"] == "SSD"])
write("v6_24_p2_cpu_20_extraction_plan.csv", FIELDS,
      [r for r in rows if r["metric"] == "CPU"])
write("v6_24_p2_iops_20_extraction_plan.csv", FIELDS,
      [r for r in rows if r["metric"] == "IOPS"])

# 8. conditional axis contract
F = ["metric", "in_mvp_cohort", "db_type", "variant", "scenario", "segment",
     "demand_nature", "granularity", "key_type", "route_path_pattern",
     "source", "extraction_stage", "axis_notes"]
write("v6_24_p2_metric_axis_contract.csv", F, [dict(zip(F, r)) for r in [
    ("HDD", "YES (50)", "EDB | Basilisk", "NOT_APPLICABLE", "NOT_APPLICABLE",
     "Consumer | Enterprise for EDB; NOT_APPLICABLE for Basilisk", "Organic",
     "Forest | Region", "forest name or region code",
     "HDD|Organic|{db_type}[|{segment}]|{granularity}",
     "LOCAL parquet artifacts", "ALREADY_LOCAL",
     "Segment applies only under EDB. Basilisk has no segment split, so it is written "
     "NOT_APPLICABLE rather than left blank."),
    ("SSD", "YES (50)", "Phoenix", "LVWE | LVNE (forecast variant)", "NOT_APPLICABLE",
     "NOT_APPLICABLE", "Organic", "Forest", "forest key",
     "SSD|Phoenix|LowVolume|Forest",
     "forecast_substrateBE_ssd_phx_lvwe_metrics + _lvne_metrics", "P3",
     "Scenario is NOT_APPLICABLE: no scenario axis is physically present in the source. "
     "Variant is a FORECAST variant, not an observed-series axis; LVWE and LVNE share one "
     "identical Mean_Actual."),
    ("CPU", "YES (20)", "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE", "NOT_APPLICABLE",
     "Consumed | Failover", "NOT_APPLICABLE", "Organic", "Region",
     "composite region-environment key, e.g. CHN-Gallatin",
     "CPU|Organic|{scenario}|Region",
     "forecast_substrateBE_cpu_actual_region", "P3",
     "The actuals table carries no DB Type column. Not invented; recorded explicitly as "
     "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE. No Forest granularity exists for CPU actuals."),
    ("IOPS", "YES (20)", "NOT_APPLICABLE", "NOT_APPLICABLE", "Consumed | Failover",
     "NOT_APPLICABLE", "Organic", "Region",
     "composite region-environment key, e.g. CHN-Gallatin",
     "IOPS|Organic|{scenario}|Region",
     "forecast_substrateBE_iops_actual_region", "P3",
     "IOPS has no DB Type axis by design. No Forest granularity exists for IOPS actuals."),
    ("Memory", "NO (0)", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE",
     "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE",
     "NOT_APPLICABLE", "NONE", "BLOCKED_NO_USEFUL_ACTUALS_SOURCE",
     "Governed Demand_Memory views exist with the correct contract but return 0 rows. "
     "Only 54.6M rows of ungoverned raw telemetry. Awareness and gap only."),
]])

# 9. parquet destination plan
F = ["stage", "path", "artifact", "format", "written_by", "contents", "status"]
write("v6_24_p2_parquet_destination_plan.csv", F, [dict(zip(F, r)) for r in [
    ("P3", "V6/data/raw/v6_24_mvp_cohort/ssd/", "ssd_lvwe_actuals_raw.parquet", "parquet",
     "P3", "Raw LVWE rows for the 50 selected forest keys, untransformed", "PLANNED"),
    ("P3", "V6/data/raw/v6_24_mvp_cohort/ssd/", "ssd_lvne_actuals_raw.parquet", "parquet",
     "P3", "Raw LVNE rows for the same 50 keys, for the second forecast variant", "PLANNED"),
    ("P3", "V6/data/raw/v6_24_mvp_cohort/cpu/", "cpu_actuals_raw.parquet", "parquet",
     "P3", "Raw CPU actuals for the 20 selected scenario-key series", "PLANNED"),
    ("P3", "V6/data/raw/v6_24_mvp_cohort/iops/", "iops_actuals_raw.parquet", "parquet",
     "P3", "Raw IOPS actuals for the 20 selected scenario-key series", "PLANNED"),
    ("P3", "V6/data/raw/v6_24_mvp_cohort/manifests/", "extraction_manifest.csv", "csv",
     "P3", "Per-query row counts, filters, timestamps and checksums", "PLANNED"),
    ("P4", "V6/data/processed/v6_24_mvp_cohort/", "cohort_manifest.parquet", "parquet",
     "P4", "The frozen 140-series cohort, all four metrics unified", "PLANNED"),
    ("P4", "V6/data/processed/v6_24_mvp_cohort/", "actuals_normalized.parquet", "parquet",
     "P4", "Long format: metric, route, granularity, key, date, actual_value", "PLANNED"),
    ("P5", "V6/data/processed/v6_24_mvp_cohort/", "model_backtests_15_models.parquet", "parquet",
     "P5", "15 governed model backtests for all 140 series", "PLANNED"),
    ("P6", "V6/data/processed/v6_24_mvp_cohort/", "forecast_outputs.parquet", "parquet",
     "P6", "Forward forecast for all 140 series", "PLANNED"),
    ("P6", "V6/data/processed/v6_24_mvp_cohort/", "accuracy_metrics.parquet", "parquet",
     "P6", "Accuracy per series per model per horizon", "PLANNED"),
    ("P4", "V6/data/processed/v6_24_mvp_cohort/", "data_dictionary.csv", "csv",
     "P4", "Column contract for every processed artifact", "PLANNED"),
    ("P7", "V6/data/processed/v6_24_mvp_cohort/", "validation_summary.csv", "csv",
     "P7", "Completeness gate results enforcing Viewer = Forecast parity", "PLANNED"),
    ("P2", "V6/outputs/v6_24_p2_controlled_parquet_extraction_plan/", "plan CSV/MD/SQL", "csv/md/sql",
     "P2", "This stage. Plan artifacts only, zero data files", "CREATED"),
]])

# optional. unresolved questions
F = ["question_id", "metric", "question", "impact", "recommendation", "blocks_p3"]
write("v6_24_p2_unresolved_questions.csv", F, [dict(zip(F, r)) for r in [
    ("P2-UQ01", "SSD",
     "Mean_Actual is stored as varchar while Mean_Forecast is float. Is the varchar typing "
     "intentional or a pipeline defect?",
     "MEDIUM. P2Q004 confirmed all 17,596 values parse cleanly via TRY_CAST, so extraction is "
     "safe today, but the typing could silently admit junk in a later refresh.",
     "P3 must CAST explicitly and fail loudly on any TRY_CAST null rather than dropping rows.",
     "NO"),
    ("P2-UQ02", "CPU/IOPS",
     "Actuals stop at 2023-07-20 while HDD and SSD run to August 2026.",
     "HIGH. The cohort backtests over non-contemporaneous periods.",
     "Owner has accepted this for the MVP with a visible STALE_ACTUALS_SOURCE caveat. Carry the "
     "caveat into the Viewer, do not hide it.",
     "NO"),
    ("P2-UQ03", "CPU",
     "The CPU actuals table carries no DB Type column.",
     "LOW. Recorded as UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE rather than invented.",
     "Leave as is. Revisit only if a DB-Type-bearing CPU actuals source is found.",
     "NO"),
    ("P2-UQ04", "SSD",
     "Do the 50 selected forest keys intersect the 300 SSD rows already in the V6 navigation "
     "contract?",
     "MEDIUM. Determines how much of the Viewer/Forecast parity gap actually closes.",
     "Local join in P4. No SQL needed.",
     "NO"),
    ("P2-UQ05", "ALL",
     "CPU and IOPS actuals tables contain no forecast column at all.",
     "MEDIUM. Unlike SSD, which ships one Mean_Forecast baseline, CPU and IOPS will have only "
     "the 15 generated models with no external baseline to compare against.",
     "Accept for the MVP, or source a CPU/IOPS forecast baseline separately in a later stage.",
     "NO"),
]])
print("plan CSVs emitted")
