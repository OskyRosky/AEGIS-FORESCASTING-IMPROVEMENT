"""V6.24-P1B | Correct the P1 deliverables with the SSD actuals found in the sweep.

P1 concluded SSD had no actuals after probing only 3 of 102 SSD objects. Owner
evidence (AX4 Security dashboard) prompted an exhaustive sweep which found four
SSD actuals sources, two of them current to 2026-08-22.

Rewrites the affected rows; leaves HDD/CPU/IOPS/Memory findings intact.
"""

from __future__ import annotations

import csv
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent


def load(name):
    with (OUT / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh)), csv.DictReader((OUT / name).open(encoding="utf-8")).fieldnames


# ---------------------------------------------- 1. actuals source assessment
rows, fields = load("v6_24_p1_actuals_source_assessment.csv")
rows = [r for r in rows if r["metric"] != "SSD"]

RC = "Fleet|Workload|Resource|Unit|Type|Scenario"
ssd_new = [
    ("SSD", "SSD-Phoenix Low Vol. w/ Efficiency / Forest",
     "forecast_substrateBE_ssd_phx_lvwe_metrics", "ACTUALS_SOURCE_CONFIRMED",
     "Start_Date|End_Date", "Mean_Actual", "Key", "Forecast_Version",
     "2026-04-07", "2026-08-22", 17596, 137, 136,
     "P1B Q008/Q009. Matches the owner AX4 dashboard exactly: NAMPRD08 last window "
     "actual=11219.51 forecast=11917.44 accuracy=93.78. Rolling window aggregate "
     "(Count 6-7 per row), one row per key per day. obs 24..131."),
    ("SSD", "SSD-Phoenix Low Vol. no Efficiency / Forest",
     "forecast_substrateBE_ssd_phx_lvne_metrics", "ACTUALS_SOURCE_CONFIRMED",
     "Start_Date|End_Date", "Mean_Actual", "Key", "Forecast_Version",
     "2026-04-03", "2026-08-22", 17733, 137, 136,
     "P1B Q010. Twin of lvwe without the efficiency adjustment. obs 25..132."),
    ("SSD", "SSD Demand / Forest", "SubstrateBE_SSD_Demand_History",
     "ACTUALS_SOURCE_CONFIRMED", "DataDate", "SubstrateSSDDemandTB", "Forest",
     "Environment|Region|SKU", "2021-06-10", "2021-11-08", 54757, 143, 142,
     "P1B Q011/Q012. Real observed demand but the window closed in 2021, roughly "
     "five years stale. obs 16..596."),
    ("SSD", "SSD Daily Raw / Region x Forest", "Greenland_SSD_HDD_Forest_Daily_Raw",
     "ACTUALS_SOURCE_CONFIRMED", "DataDate", "SSDDemandTB", "Forest", "Region",
     "2020-07-10", "2021-06-15", 46704, 142, 139,
     "P1B Q016. Raw daily observations, the cleanest shape of any SSD source, but the "
     "window closed in 2021. obs 8..340."),
    ("SSD", "SSD-PhoenixDB Demand/Supply / Region x Env",
     "vw_SubstrateBE_SSD_PhoenixDB_Demand_Supply_Region", "NOT_APPLICABLE",
     "datadate", "demand", "region", "environment",
     "2024-08-01", "2028-09-29", "UNKNOWN", 36, 36,
     "P1B Q017. 36 combinations clear 50, but the window runs to 2028 so this is a "
     "demand plan rather than pure observed history. Not a Viewer actuals source."),
    ("SSD", "SSD / Region", "forecast_substrateBE_ssd_region", "FORECAST_ONLY",
     "DateTime", "Value", "Key", RC, "2022-03-31", "2025-05-30", 309213, 29, 0,
     "P1 Q046/Q049. ModelVersion='prophet' only. Confirmed forecast-only."),
    ("SSD", "SSD-Phoenix / Forest", "forecast_substrateBE_SSD_Phoenix_Organic",
     "FORECAST_ONLY", "DateTime", "Value", "Forest", RC,
     "2025-08-08", "2030-07-02", 707069, 149, 0,
     "P1 Q051. ModelVersion='Combined' only, wholly forward window."),
    ("SSD", "SSD-Phoenix / Region", "forecast_substrateBE_SSD_TotalForecast",
     "FORECAST_ONLY", "Datetime", "Value", "Key", RC,
     "UNKNOWN", "UNKNOWN", "UNKNOWN", "UNKNOWN", 0,
     "P1 Q052. V6 R6 forecast source. No actuals marker."),
    ("SSD", "SSD Demand Plan / Region",
     "DemandPlan_SubstrateBE_SSD_Demand_Region_History", "NOT_APPLICABLE",
     "DataDate", "demand", "Region", "ForecastVersion",
     "2023-09-18", "2028-09-29", 406805, 25, 0,
     "P1 Q054. Demand plan with forward dates. Not observed actuals."),
]
rows.extend(dict(zip(fields, r)) for r in ssd_new)
rows.sort(key=lambda r: (r["metric"], r["object_name"]))
S.write_csv("v6_24_p1_actuals_source_assessment.csv", fields, rows)

# --------------------------------------------- 2. capacity by metric
rows, fields = load("v6_24_p1_combination_capacity_by_metric.csv")
for r in rows:
    if r["metric"] == "SSD":
        r.update({
            "candidate_routes": 4, "total_candidate_combinations": 559,
            "combinations_with_actuals": 559, "combinations_over_50": 272,
            "source_confirmed": "YES",
            "main_gap": "Current actuals (2026-08-22) exist only as rolling-window aggregates in "
                        "the lvwe/lvne metrics tables. The raw daily sources closed in 2021.",
            "recommended_next_action": "Extract the 272 lvwe+lvne Forest combinations in P2. "
                                       "Confirm with the owner that Mean_Actual over a 6-7 day "
                                       "window is an acceptable observed series.",
        })
S.write_csv("v6_24_p1_combination_capacity_by_metric.csv", fields, rows)

# --------------------------------------------- 3. route capacity detail
rows, fields = load("v6_24_p1_route_capacity_detail.csv")
rows = [r for r in rows if r["metric"] != "SSD"]
ssd_routes = [
    ("SSD", "SSD-Phoenix / Low Vol. w Efficiency", "Forest", 137, 136, 24, 131,
     "2026-04-07", "2026-08-22", "TRUE"),
    ("SSD", "SSD-Phoenix / Low Vol. no Efficiency", "Forest", 137, 136, 25, 132,
     "2026-04-03", "2026-08-22", "TRUE"),
    ("SSD", "SSD Demand History / Forest", "Forest", 143, 142, 16, 596,
     "2021-06-10", "2021-11-08", "REVIEW"),
    ("SSD", "SSD Daily Raw / Region x Forest", "Forest", 142, 139, 8, 340,
     "2020-07-10", "2021-06-15", "REVIEW"),
    ("SSD", "SSD / None", "Region", 0, 0, 0, 0, "", "", "FALSE"),
]
rows.extend(dict(zip(fields, r)) for r in ssd_routes)
rows.sort(key=lambda r: (r["metric"], r["route_path"]))
S.write_csv("v6_24_p1_route_capacity_detail.csv", fields, rows)

# --------------------------------------------- 4. extraction readiness plan
rows, fields = load("v6_24_p1_extraction_readiness_plan.csv")
rows = [r for r in rows if r["metric"] != "SSD"]
COLS = "Key,Start_Date,End_Date,Count,Mean_Actual,Mean_Forecast,MAE,RMSE,Bias,MAPE,Accuracy,Forecast_Version"
rows.extend(dict(zip(fields, r)) for r in [
    ("SSD", "SSD-Phoenix / Low Vol. w Efficiency / Forest",
     "forecast_substrateBE_ssd_phx_lvwe_metrics", COLS,
     "Mean_Actual IS NOT NULL", 17596, 136, "LOW", "TRUE"),
    ("SSD", "SSD-Phoenix / Low Vol. no Efficiency / Forest",
     "forecast_substrateBE_ssd_phx_lvne_metrics", COLS,
     "Mean_Actual IS NOT NULL", 17733, 136, "LOW", "TRUE"),
    ("SSD", "SSD Daily Raw / Region x Forest", "Greenland_SSD_HDD_Forest_Daily_Raw",
     "DataDate,Region,Forest,SSDDemandTB,SSDTotalTB", "SSDDemandTB IS NOT NULL",
     46704, 139, "MEDIUM", "REVIEW"),
])
rows.sort(key=lambda r: (r["metric"], r["route_path"]))
S.write_csv("v6_24_p1_extraction_readiness_plan.csv", fields, rows)

# --------------------------------------------- 5. unresolved questions
rows, fields = load("v6_24_p1_unresolved_questions.csv")
for r in rows:
    if r["question_id"] == "UQ02":
        r.update({
            "question": "RESOLVED IN P1B. SSD actuals do exist. Four sources found; two current "
                        "to 2026-08-22 (lvwe/lvne metrics tables, Forest granularity).",
            "why_unresolved": "RESOLVED. P1 probed only 3 of 102 SSD objects and searched by "
                              "Key=region; SSD actuals are keyed by forest and live in accuracy "
                              "metrics tables.",
            "impact": "RESOLVED. 272 SSD combinations clear the 50-observation threshold.",
            "how_to_resolve": "Done. See v6_24_p1b_ssd_correction.md.",
        })
rows.extend(dict(zip(fields, r)) for r in [
    ("UQ09", "SSD",
     "Is Mean_Actual over a rolling 6-7 day window an acceptable observed series for backtesting?",
     "The lvwe/lvne tables store window aggregates, not raw daily points. The raw daily "
     "sources (Greenland, SSD_Demand_History) closed in 2021.",
     "HIGH. It is the only current SSD actuals shape. If windowed means are unacceptable, "
     "SSD loses its current history.",
     "Owner decision. Alternatively locate the upstream raw table that feeds lvwe/lvne."),
    ("UQ10", "SSD",
     "Why do the current SSD actuals only start in April 2026?",
     "The lvwe/lvne tables carry a single Forecast_Version (2026-03-12) and start shortly after it.",
     "MEDIUM. 131 observations clears 50 but is a much shorter history than HDD.",
     "Ask whether earlier forecast versions are retained, or whether history can be rebuilt."),
    ("UQ11", "SSD",
     "Do lvwe and lvne represent two distinct scenarios or one series with two adjustments?",
     "Both carry the same 137 keys over nearly the same window.",
     "MEDIUM. Determines whether SSD contributes 272 or 136 distinct Viewer combinations.",
     "Compare Mean_Actual between the two tables for a shared key in P2."),
])
S.write_csv("v6_24_p1_unresolved_questions.csv", fields, rows)
print("P1B corrections applied")
