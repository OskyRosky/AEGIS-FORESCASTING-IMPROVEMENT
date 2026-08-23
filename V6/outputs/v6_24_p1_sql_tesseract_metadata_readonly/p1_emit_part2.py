"""V6.24-P1 | Emit assessment, capacity, readiness, questions and validation files.

All figures trace to ledger query ids. Nothing is estimated.
"""

from __future__ import annotations

from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent

# ------------------------------------------------- 4. actuals source assessment
A_F = ["metric", "route_label", "object_name", "actuals_source_status", "date_column",
       "value_column", "key_column", "route_columns", "min_date", "max_date",
       "total_rows", "distinct_keys", "combinations_over_50", "notes"]

RC_REGION = "Fleet|Workload|Resource|Unit|Type|Scenario|Environment"
RC_FOREST = "Fleet|Workload|Resource|Unit|Type|Scenario"

assess = [
    ("HDD", "HDD-EDB Enterprise / Region", "forecast_substrateBE_hdd_region",
     "ACTUALS_SOURCE_CONFIRMED", "DateTime", "Value", "Key", RC_REGION,
     "2019-07-01", "2026-08-17", 1180127, 45, 45,
     "Q031/Q061. Predicate ModelVersion='actual' AND Scenario='Enterprise'. obs 1105..14488."),
    ("HDD", "HDD-EDB Consumer / Region", "forecast_substrateBE_hdd_region",
     "ACTUALS_SOURCE_CONFIRMED", "DateTime", "Value", "Key", RC_REGION,
     "2019-07-01", "2026-08-17", 1180127, 46, 46,
     "Q031/Q061. Predicate ModelVersion='actual' AND Scenario='Consumer'. obs 1625..20025."),
    ("HDD", "HDD-Basilisk / Region", "forecast_substrateBE_hdd_region",
     "ACTUALS_SOURCE_CONFIRMED", "DateTime", "Value", "Key", RC_REGION,
     "2026-01-02", "2026-05-25", 1180127, 46, 46,
     "Q061. Shorter history than EDB (obs 144..284) but every combination clears 50."),
    ("HDD", "HDD-EDB Enterprise / Forest", "forecast_substrateBE_hdd",
     "ACTUALS_SOURCE_CONFIRMED", "target_date", "forecast_mean", "forest_name",
     "data_type|type|execution_time", "2019-07-01", "2026-08-17", 2279938, 156, 156,
     "Q064/Q070. Predicate TRIM(type)='actual' AND LOWER(TRIM(data_type))='enterprise'. obs 1407..16224."),
    ("HDD", "HDD-EDB Consumer / Forest", "forecast_substrateBE_hdd",
     "ACTUALS_SOURCE_CONFIRMED", "target_date", "forecast_mean", "forest_name",
     "data_type|type|execution_time", "2019-07-01", "2026-08-17", 3489406, 156, 156,
     "Q064/Q070. obs 1905..24905."),
    ("HDD", "HDD-Basilisk / Forest", "forecast_substrateBE_hdd",
     "ACTUALS_SOURCE_CONFIRMED", "target_date", "forecast_mean", "forest_name",
     "data_type|type|execution_time", "UNKNOWN", "UNKNOWN", "UNKNOWN", 155, 155,
     "Q070. obs is a flat 144 for every forest. Uniformity is suspicious and needs P2 review."),
    ("CPU", "CPU Consumed / Region", "forecast_substrateBE_cpu_actual_region",
     "ACTUALS_SOURCE_CONFIRMED", "DateTime", "Value", "Key", RC_REGION,
     "2022-01-04", "2023-07-20", 16352, 30, 30,
     "Q037/Q062. Predicate ModelVersion='Actual' AND Scenario='Consumed'. obs 220..562. "
     "STALE: history stops 2023-07-20."),
    ("CPU", "CPU Failover / Region", "forecast_substrateBE_cpu_actual_region",
     "ACTUALS_SOURCE_CONFIRMED", "DateTime", "Value", "Key", RC_REGION,
     "2022-01-04", "2023-07-20", 16352, 30, 30,
     "Q037/Q062. obs 220..562. STALE: history stops 2023-07-20."),
    ("CPU", "CPU / Forest", "forecast_substrateBE_cpu",
     "ACTUALS_SOURCE_EMPTY", "datadate", "forecast", "Forest_SKU", "type|CPU_type",
     "2021-02-15", "2030-08-27", "UNKNOWN", "UNKNOWN", 0,
     "Q067 probe for type LIKE '%actual%' returned 0 rows across 201 model types."),
    ("CPU", "CPU byDB / Forest", "forecast_substrateBE_cpu_byDB_forest",
     "ACTUALS_SOURCE_UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN",
     "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN",
     "Q069 FAILED: assumed ModelVersion column does not exist. Not resolved in P1."),
    ("IOPS", "IOPS Consumed / Region", "forecast_substrateBE_iops_actual_region",
     "ACTUALS_SOURCE_CONFIRMED", "DateTime", "Value", "Key", RC_REGION,
     "2020-06-23", "2023-07-20", 28758, 29, 29,
     "Q043/Q063. Predicate ModelVersion='Actual' AND Scenario='Consumed'. obs 218..1103. "
     "STALE: history stops 2023-07-20."),
    ("IOPS", "IOPS Failover / Region", "forecast_substrateBE_iops_actual_region",
     "ACTUALS_SOURCE_CONFIRMED", "DateTime", "Value", "Key", RC_REGION,
     "2020-06-23", "2023-07-20", 28738, 29, 29,
     "Q043/Q063. obs 218..1103. STALE: history stops 2023-07-20."),
    ("IOPS", "IOPS / Forest", "forecast_substrateBE_iops",
     "ACTUALS_SOURCE_EMPTY", "datadate", "forecast", "Forest_SKU", "type|IOPS_type",
     "2021-09-02", "2030-02-26", "UNKNOWN", "UNKNOWN", 0,
     "Q068 probe for type LIKE '%actual%' returned 0 rows across 126 model types."),
    ("SSD", "SSD / Region", "forecast_substrateBE_ssd_region",
     "FORECAST_ONLY", "DateTime", "Value", "Key", RC_REGION,
     "2022-03-31", "2025-05-30", 309213, 29, 0,
     "Q046/Q049. Sole ModelVersion is 'prophet'; Scenario is literal 'None'. No actuals marker."),
    ("SSD", "SSD-Phoenix / Forest", "forecast_substrateBE_SSD_Phoenix_Organic",
     "FORECAST_ONLY", "DateTime", "Value", "Forest", "Fleet|Workload|Unit|Type|Scenario",
     "2025-08-08", "2030-07-02", 707069, 149, 0,
     "Q051. Sole ModelVersion is 'Combined'; window is entirely forward-looking."),
    ("SSD", "SSD-Phoenix / Region", "forecast_substrateBE_SSD_TotalForecast",
     "FORECAST_ONLY", "Datetime", "Value", "Key", "Fleet|Workload|Resource|Unit|Type|Scenario",
     "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", 0,
     "Q052. V6 R6 forecast source. No ValueType/ModelVersion actuals marker in the signature."),
    ("SSD", "SSD Demand Plan / Region", "DemandPlan_SubstrateBE_SSD_Demand_Region_History",
     "NOT_APPLICABLE", "DataDate", "demand", "Region", "ForecastVersion",
     "2023-09-18", "2028-09-29", 406805, 25, 0,
     "Q054. Demand plan history, not observed actuals. Forward dates present. Not a Viewer actuals source."),
    ("MEMORY", "Memory / Region", "vw_SubstrateBE_Demand_Memory_Region",
     "SERVING_VIEW_EMPTY", "DateTime", "Value", "Key", RC_REGION,
     "", "", 0, 0, 0, "Q058. View exists with the correct contract but returns 0 rows."),
    ("MEMORY", "Memory / Forest", "vw_SubstrateBE_Demand_Memory_Forest",
     "SERVING_VIEW_EMPTY", "DateTime", "Value", "Key", RC_FOREST,
     "", "", 0, 0, 0, "Q060. View exists with the correct contract but returns 0 rows."),
    ("MEMORY", "Memory raw telemetry", "vw_SubstrateBE_MemoryRawData",
     "ACTUALS_SOURCE_REQUIRES_EXPENSIVE_QUERY", "DataDate", "ConsumedRate", "Forest",
     "Dagname|Sku_CommonName", "UNKNOWN", "UNKNOWN", 54599306, "UNKNOWN", "UNKNOWN",
     "Q056. 54.6M rows of raw telemetry. No governed Key/Value/Scenario contract; deriving a "
     "demand series would require aggregation logic that does not exist yet. Out of P1 scope."),
]
S.write_csv("v6_24_p1_actuals_source_assessment.csv", A_F,
            [dict(zip(A_F, r)) for r in assess])

# --------------------------------------- 5. combination capacity by metric
C_F = ["metric", "candidate_routes", "total_candidate_combinations",
       "combinations_with_actuals", "combinations_over_50", "source_confirmed",
       "main_gap", "recommended_next_action"]
cap = [
    ("HDD", 6, 604, 604, 604, "YES", "None. Region and Forest actuals both confirmed and current (to 2026-08-17).",
     "Already local in V6. Use as the anchor of the mixed cohort; select a representative subset."),
    ("CPU", 2, 60, 60, 60, "YES",
     "History stops 2023-07-20, roughly three years stale versus HDD. Region granularity only; no Forest actuals.",
     "Extract all 60 Region combinations in P2. Flag staleness to the owner before generation."),
    ("IOPS", 2, 58, 58, 58, "YES",
     "History stops 2023-07-20. Region granularity only; no Forest actuals.",
     "Extract all 58 Region combinations in P2. Flag staleness to the owner before generation."),
    ("SSD", 3, 0, 0, 0, "NO",
     "No actuals source found anywhere. Every SSD object is forecast-only (prophet / Combined).",
     "SSD must remain Forecast-only. Do not promote to Viewer. Escalate to the data owner if "
     "SSD actuals are required."),
    ("MEMORY", 2, 0, 0, 0, "NO",
     "Governed Demand views exist but are empty. Only 54.6M rows of ungoverned raw telemetry.",
     "Exclude Memory from the cohort. Ask the data owner whether the Demand_Memory views are "
     "scheduled to be populated."),
]
S.write_csv("v6_24_p1_combination_capacity_by_metric.csv", C_F,
            [dict(zip(C_F, r)) for r in cap])

# ------------------------------------------------- 6. route capacity detail
R_F = ["metric", "route_path", "granularity", "total_combinations",
       "combinations_over_50", "min_observations", "max_observations",
       "date_min", "date_max", "extraction_candidate"]
routes = [
    ("HDD", "HDD-EDB / Enterprise", "Region", 45, 45, 1105, 14488, "2019-07-01", "2026-08-17", "TRUE"),
    ("HDD", "HDD-EDB / Consumer", "Region", 46, 46, 1625, 20025, "2019-07-01", "2026-08-17", "TRUE"),
    ("HDD", "HDD-Basilisk / Basilisk", "Region", 46, 46, 144, 284, "2026-01-02", "2026-05-25", "TRUE"),
    ("HDD", "HDD-EDB / Enterprise", "Forest", 156, 156, 1407, 16224, "2019-07-01", "2026-08-17", "TRUE"),
    ("HDD", "HDD-EDB / Consumer", "Forest", 156, 156, 1905, 24905, "2019-07-01", "2026-08-17", "TRUE"),
    ("HDD", "HDD-Basilisk / Basilisk", "Forest", 155, 155, 144, 144, "UNKNOWN", "UNKNOWN", "REVIEW"),
    ("CPU", "CPU / Consumed", "Region", 30, 30, 220, 562, "2022-01-04", "2023-07-20", "TRUE"),
    ("CPU", "CPU / Failover", "Region", 30, 30, 220, 562, "2022-01-04", "2023-07-20", "TRUE"),
    ("CPU", "CPU / any", "Forest", 0, 0, 0, 0, "", "", "FALSE"),
    ("IOPS", "IOPS / Consumed", "Region", 29, 29, 218, 1103, "2020-06-23", "2023-07-20", "TRUE"),
    ("IOPS", "IOPS / Failover", "Region", 29, 29, 218, 1103, "2020-06-23", "2023-07-20", "TRUE"),
    ("IOPS", "IOPS / any", "Forest", 0, 0, 0, 0, "", "", "FALSE"),
    ("SSD", "SSD / None", "Region", 0, 0, 0, 0, "", "", "FALSE"),
    ("SSD", "SSD-Phoenix / Organic", "Forest", 0, 0, 0, 0, "", "", "FALSE"),
    ("MEMORY", "Memory / any", "Region", 0, 0, 0, 0, "", "", "FALSE"),
    ("MEMORY", "Memory / any", "Forest", 0, 0, 0, 0, "", "", "FALSE"),
]
S.write_csv("v6_24_p1_route_capacity_detail.csv", R_F,
            [dict(zip(R_F, r)) for r in routes])

# ------------------------------------------------ 7. extraction readiness plan
E_F = ["metric", "route_path", "source_object", "columns_to_extract",
       "filter_predicate", "estimated_rows", "estimated_combinations",
       "risk_level", "ready_for_parquet_extraction"]
COLS_REGION = "DateTime,Key,Value,ModelVersion,ForecastVersion,Fleet,Workload,Resource,Unit,Type,Scenario"
plan = [
    ("CPU", "CPU / Consumed / Region", "forecast_substrateBE_cpu_actual_region", COLS_REGION,
     "ModelVersion='Actual' AND Scenario='Consumed'", 16352, 30, "LOW", "TRUE"),
    ("CPU", "CPU / Failover / Region", "forecast_substrateBE_cpu_actual_region", COLS_REGION,
     "ModelVersion='Actual' AND Scenario='Failover'", 16352, 30, "LOW", "TRUE"),
    ("IOPS", "IOPS / Consumed / Region", "forecast_substrateBE_iops_actual_region", COLS_REGION,
     "ModelVersion='Actual' AND Scenario='Consumed'", 28758, 29, "LOW", "TRUE"),
    ("IOPS", "IOPS / Failover / Region", "forecast_substrateBE_iops_actual_region", COLS_REGION,
     "ModelVersion='Actual' AND Scenario='Failover'", 28738, 29, "LOW", "TRUE"),
    ("HDD", "HDD-EDB / Enterprise / Region", "forecast_substrateBE_hdd_region", COLS_REGION,
     "ModelVersion='actual' AND Scenario='Enterprise'", "UNKNOWN", 45, "LOW",
     "ALREADY_LOCAL"),
    ("HDD", "HDD-EDB / Consumer / Region", "forecast_substrateBE_hdd_region", COLS_REGION,
     "ModelVersion='actual' AND Scenario='Consumer'", "UNKNOWN", 46, "LOW", "ALREADY_LOCAL"),
    ("HDD", "HDD-Basilisk / Region", "forecast_substrateBE_hdd_region", COLS_REGION,
     "ModelVersion='actual' AND Scenario='Basilisk'", "UNKNOWN", 46, "LOW", "ALREADY_LOCAL"),
    ("SSD", "SSD / any", "NONE", "", "", 0, 0, "BLOCKED", "FALSE"),
    ("MEMORY", "Memory / any", "NONE", "", "", 0, 0, "BLOCKED", "FALSE"),
]
S.write_csv("v6_24_p1_extraction_readiness_plan.csv", E_F,
            [dict(zip(E_F, r)) for r in plan])

# ------------------------------------------------------ 8. unresolved questions
Q_F = ["question_id", "metric", "question", "why_unresolved", "impact", "how_to_resolve"]
questions = [
    ("UQ01", "CPU/IOPS",
     "Why do CPU and IOPS actuals stop at 2023-07-20 while HDD actuals run to 2026-08-17?",
     "Only metadata was inspected. The refresh pipeline for the *_actual_region tables was not examined.",
     "HIGH. A cohort mixing 2026 HDD history with 2023 CPU/IOPS history produces backtests over "
     "non-comparable periods.",
     "Ask the data owner whether the *_actual_region tables are still refreshed, or find the "
     "current actuals source."),
    ("UQ02", "SSD",
     "Do SSD actuals exist anywhere in TesseractEarthDW?",
     "Every SSD object inspected (ssd_region, SSD_Phoenix_Organic, SSD_TotalForecast, "
     "DemandPlan history) is forecast or demand plan. 102 SSD-named objects were catalogued but "
     "only the highest-signal ones were probed.",
     "HIGH. Without actuals SSD cannot enter the Viewer, only Forecast.",
     "Sweep the remaining SSD objects for an 'actual' marker, or escalate to the data owner."),
    ("UQ03", "MEMORY",
     "Are vw_SubstrateBE_Demand_Memory_Region/Forest intended to be populated?",
     "Both views exist with the correct 9/10-column contract but return 0 rows.",
     "MEDIUM. Memory is listed as an MVP metric but has no data.",
     "Ask the data owner. If unplanned, drop Memory from the MVP metric list."),
    ("UQ04", "HDD",
     "Why does every Basilisk Forest combination have exactly 144 observations?",
     "Q070 returned min_obs = max_obs = 144 across all 155 forests, which is unusually uniform.",
     "MEDIUM. May indicate a synthetic or padded series rather than observed history.",
     "Inspect the Basilisk Forest date distribution in P2 before including it in the cohort."),
    ("UQ05", "CPU",
     "What is in forecast_substrateBE_cpu_byDB_forest?",
     "Q069 failed because the assumed ModelVersion column does not exist. Not retried.",
     "LOW. Region-level CPU actuals are already confirmed.",
     "Read its INFORMATION_SCHEMA signature in P2."),
    ("UQ06", "ALL",
     "Is ValueRef (present only in the *_actual_region tables) meaningful for backtesting?",
     "The column exists but its semantics were not established.",
     "LOW. Value is sufficient for the Viewer contract.",
     "Sample ValueRef against Value in P2."),
    ("UQ07", "ALL",
     "Which ForecastVersion vintages should the cohort pin to?",
     "ForecastVersion was catalogued as a column but its distribution was not measured per route.",
     "MEDIUM. V6 R6 pinned 'latest 3 versions' for HDD; the equivalent for CPU/IOPS is unknown.",
     "Measure ForecastVersion distribution per route in P2 before extraction."),
    ("UQ08", "ALL",
     "Are the 38 vw_SubstrateBE_Demand_* views usable as a uniform serving layer?",
     "They share one clean contract across all five metrics, but Basilisk and Memory return 0 rows "
     "and the sampled rows are forward-dated, so they serve demand plan rather than actuals.",
     "MEDIUM. They would be the cleanest long-term source if backfilled.",
     "Ask the data owner about their population schedule."),
]
S.write_csv("v6_24_p1_unresolved_questions.csv", Q_F,
            [dict(zip(Q_F, r)) for r in questions])
