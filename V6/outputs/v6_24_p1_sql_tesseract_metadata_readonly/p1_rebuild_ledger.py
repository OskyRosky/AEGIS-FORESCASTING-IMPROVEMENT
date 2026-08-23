"""V6.24-P1 | Rebuild the query ledger after an operational error truncated it.

During P1B an inline helper script wrote the ledger without first loading the
existing rows, truncating the 70 P1 entries to 17 P1B entries.

The P1 rows are restored below from the recorded console output of each step
script (status, row count and duration are the real observed values). Exact wall
clock timestamps were not recoverable and are marked RECONSTRUCTED. The
underlying query results were never lost: they remain in _stepA.._stepI JSON.
"""

from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent
LEDGER = OUT / "v6_24_p1_query_ledger.csv"
FIELDS = ["query_id", "metric", "object_name", "purpose", "query_type",
          "started_at", "status", "row_count_returned", "duration_seconds", "notes"]

R = "RECONSTRUCTED"
META, SAMP, VOC, AGG = "metadata", "sample", "vocabulary", "aggregate"

# (metric, object, purpose, type, status, rows, duration)
P1 = [
    ("ALL", "sys.objects", "Enumerate every user table and view in TesseractEarthDW", META, "OK", 1214, 12.0),
    ("ALL", "INFORMATION_SCHEMA.COLUMNS", "Column metadata for Demand_* views and *_actual*/History tables", META, "OK", 452, 10.09),
    ("CPU", "vw_SubstrateBE_Demand_Cpu_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 5, 64.31),
    ("CPU", "vw_SubstrateBE_Demand_Cpu_Region", "Distinct DemandType vocabulary", VOC, "OK", 2, 16.5),
    ("CPU", "vw_SubstrateBE_Demand_CpuPhoenix_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 5, 29.33),
    ("CPU", "vw_SubstrateBE_Demand_CpuPhoenix_Region", "Distinct DemandType vocabulary", VOC, "OK", 2, 3.37),
    ("HDD", "vw_SubstrateBE_Demand_HddEdbEnterprise_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 5, 10.88),
    ("HDD", "vw_SubstrateBE_Demand_HddEdbEnterprise_Region", "Distinct DemandType vocabulary", VOC, "OK", 1, 4.18),
    ("HDD", "vw_SubstrateBE_Demand_HddBasilisk_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 0, 0.18),
    ("HDD", "vw_SubstrateBE_Demand_HddBasilisk_Region", "Distinct DemandType vocabulary", VOC, "OK", 0, 0.31),
    ("IOPS", "vw_SubstrateBE_Demand_Iops_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 5, 15.69),
    ("IOPS", "vw_SubstrateBE_Demand_Iops_Region", "Distinct DemandType vocabulary", VOC, "OK", 2, 4.1),
    ("MEMORY", "vw_SubstrateBE_Demand_Memory_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 0, 0.18),
    ("MEMORY", "vw_SubstrateBE_Demand_Memory_Region", "Distinct DemandType vocabulary", VOC, "OK", 0, 0.18),
    ("SSD", "vw_SubstrateBE_Demand_Ssd_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 5, 28.88),
    ("SSD", "vw_SubstrateBE_Demand_Ssd_Region", "Distinct DemandType vocabulary", VOC, "OK", 2, 11.82),
    ("SSD", "vw_SubstrateBE_Demand_SsdPhoenix_Region", "TOP 5 sample to infer column semantics", SAMP, "OK", 5, 11.9),
    ("SSD", "vw_SubstrateBE_Demand_SsdPhoenix_Region", "Distinct DemandType vocabulary", VOC, "OK", 2, 4.93),
    ("ALL", "sys.dm_db_partition_stats", "Catalogue row counts for all user tables", META, "FAILED", 0, 10.0),
    ("ALL", "INFORMATION_SCHEMA.COLUMNS", "Column signatures for forecast_substrateBE_* tables", META, "OK", 424, 0.43),
    ("ALL", "sys.partitions", "Catalogue row counts via sys.partitions (fallback after Q019 failed)", META, "OK", 901, 9.53),
    ("HDD", "forecast_substrateBE_hdd_region", "ValueType split with date range and distinct key count", AGG, "OK", 1, 1.81),
    ("CPU", "forecast_substrateBE_cpu_region", "ValueType split with date range and distinct key count", AGG, "OK", 1, 1.65),
    ("CPU", "forecast_substrateBE_cpu_actual_region", "ValueType split with date range and distinct key count", AGG, "OK", 1, 0.91),
    ("IOPS", "forecast_substrateBE_iops_region", "ValueType split with date range and distinct key count", AGG, "OK", 1, 1.1),
    ("IOPS", "forecast_substrateBE_iops_actual_region", "ValueType split with date range and distinct key count", AGG, "OK", 1, 0.72),
    ("SSD", "forecast_substrateBE_ssd_region", "ValueType split with date range and distinct key count", AGG, "OK", 1, 0.96),
    ("SSD", "forecast_substrateBE_SSD_Phoenix_Organic", "ValueType split with date range and distinct key count", AGG, "FAILED", 0, 1.36),
    ("HDD", "forecast_substrateBE_hdd_region", "Type vocabulary with row count and date range", VOC, "OK", 2, 11.32),
    ("HDD", "forecast_substrateBE_hdd_region", "Scenario vocabulary with row count and date range", VOC, "OK", 3, 1.09),
    ("HDD", "forecast_substrateBE_hdd_region", "ModelVersion vocabulary with row count and date range", VOC, "OK", 194, 2.06),
    ("CPU", "forecast_substrateBE_cpu_region", "Type vocabulary with row count and date range", VOC, "OK", 2, 1.25),
    ("CPU", "forecast_substrateBE_cpu_region", "Scenario vocabulary with row count and date range", VOC, "OK", 2, 1.1),
    ("CPU", "forecast_substrateBE_cpu_region", "ModelVersion vocabulary with row count and date range", VOC, "OK", 30, 1.16),
    ("CPU", "forecast_substrateBE_cpu_actual_region", "Type vocabulary with row count and date range", VOC, "OK", 1, 0.69),
    ("CPU", "forecast_substrateBE_cpu_actual_region", "Scenario vocabulary with row count and date range", VOC, "OK", 2, 0.66),
    ("CPU", "forecast_substrateBE_cpu_actual_region", "ModelVersion vocabulary with row count and date range", VOC, "OK", 1, 0.74),
    ("IOPS", "forecast_substrateBE_iops_region", "Type vocabulary with row count and date range", VOC, "OK", 2, 1.21),
    ("IOPS", "forecast_substrateBE_iops_region", "Scenario vocabulary with row count and date range", VOC, "OK", 2, 0.89),
    ("IOPS", "forecast_substrateBE_iops_region", "ModelVersion vocabulary with row count and date range", VOC, "OK", 89, 1.05),
    ("IOPS", "forecast_substrateBE_iops_actual_region", "Type vocabulary with row count and date range", VOC, "OK", 1, 0.78),
    ("IOPS", "forecast_substrateBE_iops_actual_region", "Scenario vocabulary with row count and date range", VOC, "OK", 2, 0.69),
    ("IOPS", "forecast_substrateBE_iops_actual_region", "ModelVersion vocabulary with row count and date range", VOC, "OK", 1, 0.7),
    ("SSD", "forecast_substrateBE_ssd_region", "Type vocabulary with row count and date range", VOC, "OK", 1, 0.92),
    ("SSD", "forecast_substrateBE_ssd_region", "Scenario vocabulary with row count and date range", VOC, "OK", 1, 0.7),
    ("SSD", "forecast_substrateBE_ssd_region", "ModelVersion vocabulary with row count and date range", VOC, "OK", 1, 0.73),
    ("CPU", "forecast_substrateBE_cpu_region", "Probe for an 'actual' ModelVersion marker", AGG, "OK", 0, 10.8),
    ("IOPS", "forecast_substrateBE_iops_region", "Probe for an 'actual' ModelVersion marker", AGG, "OK", 0, 0.88),
    ("SSD", "forecast_substrateBE_ssd_region", "Probe for an 'actual' ModelVersion marker", AGG, "OK", 0, 0.71),
    ("SSD", "forecast_substrateBE_SSD_Phoenix_Organic", "Column signature", META, "OK", 11, 0.32),
    ("SSD", "forecast_substrateBE_SSD_Phoenix_Organic", "ModelVersion vocabulary", VOC, "OK", 1, 0.95),
    ("SSD", "forecast_substrateBE_SSD_TotalForecast", "Column signature", META, "OK", 11, 0.32),
    ("SSD", "DemandPlan_SubstrateBE_SSD_Demand_Region_History", "Column signature", META, "OK", 5, 0.33),
    ("SSD", "DemandPlan_SubstrateBE_SSD_Demand_Region_History", "Row count and date range", AGG, "OK", 1, 5.55),
    ("MEMORY", "vw_SubstrateBE_MemoryRawData", "Column signature", META, "OK", 7, 0.32),
    ("MEMORY", "vw_SubstrateBE_MemoryRawData", "Row count", AGG, "OK", 1, 13.61),
    ("MEMORY", "vw_SubstrateBE_Demand_Memory_Region", "Column signature", META, "OK", 10, 0.33),
    ("MEMORY", "vw_SubstrateBE_Demand_Memory_Region", "Row count", AGG, "OK", 1, 0.18),
    ("MEMORY", "vw_SubstrateBE_Demand_Memory_Forest", "Column signature", META, "OK", 9, 0.31),
    ("MEMORY", "vw_SubstrateBE_Demand_Memory_Forest", "Row count", AGG, "OK", 1, 0.17),
    ("HDD", "forecast_substrateBE_hdd_region", "Route x key combinations and how many exceed 50 real observations", AGG, "OK", 3, 9.6),
    ("CPU", "forecast_substrateBE_cpu_actual_region", "Route x key combinations and how many exceed 50 real observations", AGG, "OK", 2, 1.17),
    ("IOPS", "forecast_substrateBE_iops_actual_region", "Route x key combinations and how many exceed 50 real observations", AGG, "OK", 2, 1.13),
    ("HDD", "forecast_substrateBE_hdd", "data_type/type vocabulary to locate Forest-level actuals", VOC, "OK", 234, 14.1),
    ("CPU", "forecast_substrateBE_cpu", "type vocabulary to locate Forest-level actuals", VOC, "OK", 201, 1.4),
    ("IOPS", "forecast_substrateBE_iops", "type vocabulary to locate Forest-level actuals", VOC, "OK", 126, 1.05),
    ("CPU", "forecast_substrateBE_cpu", "Direct probe for Forest-level actual marker", AGG, "OK", 0, 17.25),
    ("IOPS", "forecast_substrateBE_iops", "Direct probe for Forest-level actual marker", AGG, "OK", 0, 2.07),
    ("CPU", "forecast_substrateBE_cpu_byDB_forest", "Direct probe for Forest-level actual marker", AGG, "FAILED", 0, 0.56),
    ("HDD", "forecast_substrateBE_hdd", "Forest combinations over 50 real observations", AGG, "OK", 3, 2.71),
]

NOTE = ("Restored after an operational error in P1B truncated the ledger. Status, row count "
        "and duration are the real observed values from the step script console output; the "
        "wall clock timestamp was not recoverable. Query results are intact in _stepA.._stepI JSON.")

out = []
for i, (metric, obj, purpose, qtype, status, rows, dur) in enumerate(P1, start=1):
    note = NOTE
    if status == "FAILED":
        reason = {
            19: "Insufficient permission on sys.dm_db_partition_stats; replaced by sys.partitions in Q021.",
            28: "Table keys on Forest, not Key; retried correctly as Q051.",
            69: "Assumed ModelVersion column does not exist on this table. Unresolved, logged as UQ05.",
        }.get(i, "")
        note = f"{reason} {NOTE}"
    out.append(dict(zip(FIELDS, [f"Q{i:03d}", metric, obj, purpose, qtype, R,
                                 status, rows, dur, note])))

# Append the P1B rows already on disk, renumbered to follow.
existing = list(csv.DictReader(LEDGER.open(encoding="utf-8")))
for j, r in enumerate(existing, start=len(out) + 1):
    r["query_id"] = f"Q{j:03d}"
    r["notes"] = (r.get("notes") or "") + " | P1B SSD correction sweep."
    out.append(r)

with LEDGER.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(out)

print(f"ledger_rows={len(out)} (P1={len(P1)} reconstructed, P1B={len(existing)} original)")
print(f"failed_recorded={sum(1 for r in out if r['status'] == 'FAILED')}")
for m in ("HDD", "CPU", "IOPS", "SSD", "MEMORY", "ALL"):
    print(f"  {m}: {sum(1 for r in out if r['metric'] == m)} queries")
