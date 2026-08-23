"""V6.24-P1 | Emit the ten required deliverables from measured SQL metadata.

Every value written here comes from a query recorded in v6_24_p1_query_ledger.csv.
Nothing is inferred or invented; unknowns are written as UNKNOWN.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent

stepD2 = json.loads((OUT / "_stepD2_counts.json").read_text(encoding="utf-8"))
stepE = json.loads((OUT / "_stepE_vocab.json").read_text(encoding="utf-8"))
stepG = json.loads((OUT / "_stepG_combinations.json").read_text(encoding="utf-8"))
stepI = json.loads((OUT / "_stepI_forest_actuals.json").read_text(encoding="utf-8"))
stepB = json.loads((OUT / "_stepB_columns.json").read_text(encoding="utf-8"))
stepA = json.loads((OUT / "_stepA_catalogue.json").read_text(encoding="utf-8"))

# ---------------------------------------------------------------- 2. inventory
INV_F = ["metric", "object_schema", "object_name", "object_type", "exists",
         "is_empty", "estimated_or_actual_row_count", "evidence_source", "notes"]

inv = [
    ("HDD", "dbo", "forecast_substrateBE_hdd_region", "USER_TABLE", "TRUE", "FALSE",
     4411852, "sys.partitions Q021 + Q031",
     "V6 proven source. ModelVersion='actual' isolates 1,180,127 actual rows 2019-07-01..2026-08-17."),
    ("HDD", "dbo", "forecast_substrateBE_hdd", "USER_TABLE", "TRUE", "FALSE",
     "UNKNOWN", "Q064 + Q070",
     "Forest granularity. TRIM(type)='actual' isolates actuals across 156 forests."),
    ("CPU", "dbo", "forecast_substrateBE_cpu_actual_region", "USER_TABLE", "TRUE", "FALSE",
     32704, "sys.partitions Q021 + Q037",
     "ACTUALS CONFIRMED. ModelVersion='Actual'. Stale: max date 2023-07-20."),
    ("CPU", "dbo", "forecast_substrateBE_cpu_region", "USER_TABLE", "TRUE", "FALSE",
     2654280, "sys.partitions Q021 + Q047",
     "Model forecasts only across 30 ModelVersions. No 'actual' marker (Q047 returned 0 rows)."),
    ("CPU", "dbo", "forecast_substrateBE_cpu", "USER_TABLE", "TRUE", "FALSE",
     "UNKNOWN", "Q065 + Q067",
     "Forest granularity, 201 model types. No 'actual' marker (Q067 returned 0 rows)."),
    ("CPU", "dbo", "forecast_substrateBE_cpu_byDB_forest", "USER_TABLE", "TRUE", "UNKNOWN",
     "UNKNOWN", "Q069 FAILED",
     "Probe failed: expected ModelVersion column absent. Unresolved."),
    ("IOPS", "dbo", "forecast_substrateBE_iops_actual_region", "USER_TABLE", "TRUE", "FALSE",
     57496, "sys.partitions Q021 + Q043",
     "ACTUALS CONFIRMED. ModelVersion='Actual'. Stale: max date 2023-07-20."),
    ("IOPS", "dbo", "forecast_substrateBE_iops_region", "USER_TABLE", "TRUE", "FALSE",
     6451852, "sys.partitions Q021 + Q048",
     "Model forecasts only across 89 ModelVersions. No 'actual' marker (Q048 returned 0 rows)."),
    ("IOPS", "dbo", "forecast_substrateBE_iops", "USER_TABLE", "TRUE", "FALSE",
     "UNKNOWN", "Q066 + Q068",
     "Forest granularity, 126 model types. No 'actual' marker (Q068 returned 0 rows)."),
    ("SSD", "dbo", "forecast_substrateBE_ssd_region", "USER_TABLE", "TRUE", "FALSE",
     309213, "sys.partitions Q021 + Q046",
     "ModelVersion='prophet' only, Scenario='None'. FORECAST_ONLY. No actuals."),
    ("SSD", "dbo", "forecast_substrateBE_SSD_Phoenix_Organic", "USER_TABLE", "TRUE", "FALSE",
     707069, "sys.partitions Q021 + Q051",
     "ModelVersion='Combined' only, 2025-08-08..2030-07-02, 149 forests. FORECAST_ONLY."),
    ("SSD", "dbo", "forecast_substrateBE_SSD_TotalForecast", "USER_TABLE", "TRUE", "UNKNOWN",
     "UNKNOWN", "Q052",
     "Forecast serving table (V6 R6 source for SSD-Phoenix). No ValueType/ModelVersion actuals marker."),
    ("SSD", "dbo", "DemandPlan_SubstrateBE_SSD_Demand_Region_History", "USER_TABLE", "TRUE", "FALSE",
     406805, "Q054",
     "Demand plan history 2023-09-18..2028-09-29, 25 regions. Demand plan, not observed actuals."),
    ("MEMORY", "dbo", "vw_SubstrateBE_Demand_Memory_Region", "VIEW", "TRUE", "TRUE",
     0, "Q058", "SERVING_VIEW_EMPTY. Returns 0 rows."),
    ("MEMORY", "dbo", "vw_SubstrateBE_Demand_Memory_Forest", "VIEW", "TRUE", "TRUE",
     0, "Q060", "SERVING_VIEW_EMPTY. Returns 0 rows."),
    ("MEMORY", "dbo", "vw_SubstrateBE_MemoryRawData", "VIEW", "TRUE", "FALSE",
     54599306, "Q056",
     "Raw telemetry only (DataDate/Dagname/Forest/ConsumedRate/InstalledMemoryGBPerServer). "
     "No governed Key/Value/Scenario contract. Would require derivation, out of P1 scope."),
    ("HDD", "dbo", "vw_SubstrateBE_Demand_HddBasilisk_Region", "VIEW", "TRUE", "TRUE",
     0, "Q009/Q010", "SERVING_VIEW_EMPTY. Basilisk demand view returns 0 rows."),
]
S.write_csv("v6_24_p1_candidate_object_inventory.csv", INV_F,
            [dict(zip(INV_F, r)) for r in inv])

# ------------------------------------------------------------ 3. column mapping
COL_F = ["metric", "object_name", "column_name", "inferred_role", "data_type",
         "nullable", "confidence", "notes"]

ROLE = {
    "DateTime": ("date", "HIGH", "Observation date. Confirmed by MIN/MAX aggregates."),
    "Datetime": ("date", "HIGH", "Observation date (lower-case variant)."),
    "Key": ("key", "HIGH", "Series identity. Region code at Region granularity."),
    "Value": ("value", "HIGH", "Numeric measure."),
    "ValueRef": ("value_reference", "MEDIUM", "Secondary value, semantics not established in P1."),
    "ModelVersion": ("actual_forecast_marker", "HIGH",
                     "Decisive column: 'actual'/'Actual' marks observed history."),
    "ForecastVersion": ("forecast_version", "HIGH", "Vintage of the forecast run."),
    "Scenario": ("route_axis", "HIGH", "Route axis: HDD Enterprise/Consumer/Basilisk; CPU+IOPS Consumed/Failover."),
    "Type": ("route_axis", "MEDIUM", "Organic / Organic_adjust / Organic (Without SubstrateBlobShard)."),
    "Fleet": ("route_axis", "HIGH", "Constant 'SubstrateBE' in all samples."),
    "Workload": ("route_axis", "HIGH", "Constant 'Backend' in all samples."),
    "Resource": ("route_axis", "HIGH", "Metric label, e.g. 'HDD - EDB Enterprise', 'CPU', 'IOPS'."),
    "Unit": ("unit", "HIGH", "TB / GCYCLES / IOPS."),
    "Environment": ("route_axis", "HIGH", "Region-granularity only. e.g. GO LOCAL, Dedicated, Gallatin."),
    "DemandType": ("route_axis", "HIGH", "Organic / Perturbation. Demand views only."),
}

colmap = []
TRACKED = {
    "forecast_substrateBE_hdd_region": "HDD",
    "forecast_substrateBE_cpu_actual_region": "CPU",
    "forecast_substrateBE_cpu_region": "CPU",
    "forecast_substrateBE_iops_actual_region": "IOPS",
    "forecast_substrateBE_iops_region": "IOPS",
    "forecast_substrateBE_ssd_region": "SSD",
    "forecast_substrateBE_SSD_Phoenix_Organic": "SSD",
}
sigs = json.loads((OUT / "_stepD_candidates.json").read_text(encoding="utf-8"))
for tbl, metric in TRACKED.items():
    for cname, ctype in sigs.get(tbl, {}).get("columns", []):
        role, conf, note = ROLE.get(cname, ("unclassified", "LOW", "Role not established in P1."))
        colmap.append(dict(zip(COL_F, [metric, tbl, cname, role, ctype, "UNKNOWN", conf, note])))

# Forest-granularity tables use a different vocabulary.
for metric, tbl, pairs in [
    ("HDD", "forecast_substrateBE_hdd", [
        ("forest_name", "key", "char", "HIGH", "Forest identity."),
        ("target_date", "date", "datetime", "HIGH", "Observation date."),
        ("forecast_mean", "value", "float", "HIGH", "Measure; carries actuals when type='actual'."),
        ("forecast_p90", "value_band", "float", "MEDIUM", "Upper band."),
        ("forecast_p95", "value_band", "float", "MEDIUM", "Upper band."),
        ("type", "actual_forecast_marker", "nchar", "HIGH", "TRIM(type)='actual' marks observed history."),
        ("data_type", "route_axis", "varchar", "HIGH", "enterprise/consumer/basilisk. Case-inconsistent, needs TRIM+LOWER."),
        ("execution_time", "run_id", "datetime", "HIGH", "Extraction run discriminator used by V6 R6."),
        ("write_time", "audit", "datetime", "LOW", "Audit timestamp."),
    ]),
    ("MEMORY", "vw_SubstrateBE_MemoryRawData", [
        ("DataDate", "date", "UNKNOWN", "MEDIUM", "Telemetry date."),
        ("Forest", "key", "UNKNOWN", "MEDIUM", "Candidate key, unverified."),
        ("ConsumedRate", "value", "UNKNOWN", "LOW", "Rate, not a governed demand measure."),
        ("InstalledMemoryGBPerServer", "capacity", "UNKNOWN", "LOW", "Capacity, not demand."),
        ("Dagname", "route_axis", "UNKNOWN", "LOW", "DAG identity, no route mapping established."),
    ]),
]:
    for cname, role, dtype, conf, note in pairs:
        colmap.append(dict(zip(COL_F, [metric, tbl, cname, role, dtype, "UNKNOWN", conf, note])))

S.write_csv("v6_24_p1_column_mapping.csv", COL_F, colmap)
print(f"colmap_rows={len(colmap)}")
