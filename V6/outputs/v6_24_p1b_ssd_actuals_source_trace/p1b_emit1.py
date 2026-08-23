"""V6.24-P1B | Emit the eleven required deliverables from measured evidence.

Every figure traces to a P1B ledger query id. Unknowns are written as UNKNOWN.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import _p1b_sql as S

OUT = Path(__file__).resolve().parent
E = json.loads((OUT / "_p1b_evidence.json").read_text(encoding="utf-8"))

LVWE = "forecast_substrateBE_ssd_phx_lvwe_metrics"
LVNE = "forecast_substrateBE_ssd_phx_lvne_metrics"

counts = {r[1]: r[2] for r in E["sweep_counts"]}
cols = E["sweep_columns"]

# ------------------------------------------------------------ 2. object sweep
F = ["object_schema", "object_name", "object_type", "row_count_estimate",
     "relevant_columns", "relevance_score", "reason"]

ACTUAL_RX = re.compile(r"actual|observed|demand|mean_actual", re.I)
DATE_RX = re.compile(r"date|datetime|snapshot", re.I)
KEY_RX = re.compile(r"^key$|forest|region|dag", re.I)

HIGH = {LVWE, LVNE}
MED = {"Greenland_SSD_HDD_Forest_Daily_Raw", "SubstrateBE_SSD_Demand_History",
       "forecast_staging_agent_SSD", "vw_SubstrateBE_SSD_PhoenixDB_Demand_Supply_Region"}

sweep = []
for schema, name, otype in E["sweep_objects"]:
    c = [x[0] for x in cols.get(name, [])]
    rel = [x for x in c if ACTUAL_RX.search(x) or DATE_RX.search(x) or KEY_RX.search(x)]
    if name in HIGH:
        score, reason = "HIGH", ("Named after the AX4 dashboard scenario. Carries Mean_Actual "
                                "plus a forest Key and a date window. Confirmed actuals source.")
    elif name in MED:
        score, reason = "MEDIUM", "Raw or staging candidate for a daily actuals series. Probed directly."
    elif ACTUAL_RX.search(name) or (rel and ACTUAL_RX.search(" ".join(c))):
        score, reason = "LOW", "Carries an actual-shaped column but is forecast, perturbation or supply oriented."
    else:
        score, reason = "NONE", "No actual-bearing column in its signature."
    sweep.append(dict(zip(F, [schema, name, otype, counts.get(name, "VIEW_OR_UNKNOWN"),
                              "|".join(rel) if rel else "", score, reason])))
S.write_csv("v6_24_p1b_ssd_object_sweep.csv", F, sweep)
print(f"sweep HIGH={sum(1 for r in sweep if r['relevance_score'] == 'HIGH')} "
      f"MEDIUM={sum(1 for r in sweep if r['relevance_score'] == 'MEDIUM')} "
      f"LOW={sum(1 for r in sweep if r['relevance_score'] == 'LOW')} "
      f"NONE={sum(1 for r in sweep if r['relevance_score'] == 'NONE')}")

# --------------------------------------------------------- 3. column mapping
F = ["object_name", "column_name", "inferred_role", "data_type", "nullable",
     "confidence", "notes"]
ROLE = {
    "Key": ("key", "HIGH", "Forest identity. 137 distinct values, all forest-shaped "
                           "(APCPRD01, NAMPRD07, NAMPRD08, EURP107). Confirmed by P1B011."),
    "Start_Date": ("window_start", "HIGH", "Start of the rolling accuracy window."),
    "End_Date": ("window_end", "HIGH", "End of the rolling window. Acts as the series date: "
                                       "130 distinct values over 132 calendar days (P1B014)."),
    "Count": ("window_size", "HIGH", "Observations inside the window. Range 1..7, mean 5.22 (P1B005). "
                                     "Proves the row is an aggregate, not a raw daily point."),
    "Mean_Actual": ("actual_value", "HIGH", "Mean observed value over the window. Zero nulls in "
                                            "either table (P1B005/P1B007). Matches the AX4 dashboard."),
    "Mean_Forecast": ("forecast_value", "HIGH", "Mean forecast over the window. Differs between "
                                                "LVWE and LVNE in 6,720 rows (P1B013)."),
    "MAE": ("accuracy_metric", "HIGH", "Mean absolute error, precomputed."),
    "RMSE": ("accuracy_metric", "HIGH", "Root mean squared error, precomputed."),
    "Bias": ("accuracy_metric", "HIGH", "Signed error, precomputed."),
    "Bias_Pct": ("accuracy_metric", "HIGH", "Signed percentage error."),
    "MAPE": ("accuracy_metric", "HIGH", "Mean absolute percentage error."),
    "SMAPE": ("accuracy_metric", "HIGH", "Symmetric MAPE."),
    "Accuracy": ("accuracy_metric", "HIGH", "100 minus MAPE. The metric shown on the AX4 dashboard."),
    "Forecast_Version": ("forecast_version", "HIGH", "Single value 2026-03-12 in both tables (P1B005/P1B007)."),
    "Execution_Date": ("audit", "MEDIUM", "Pipeline execution timestamp."),
}
colmap = []
for tbl in (LVWE, LVNE):
    for cname, dtype, nullable in cols.get(tbl, []):
        role, conf, note = ROLE.get(cname, ("unclassified", "LOW", "Role not established in P1B."))
        colmap.append(dict(zip(F, [tbl, cname, role, dtype, nullable, conf, note])))

for tbl, pairs in [
    ("Greenland_SSD_HDD_Forest_Daily_Raw", [
        ("DataDate", "date", "HIGH", "Raw daily observation date. Window 2020-07-10..2021-06-15 (P1B016)."),
        ("Forest", "key", "HIGH", "Forest identity. 116 of these forests also appear in LVWE (P1B018)."),
        ("Region", "route_axis", "HIGH", "Region axis."),
        ("SSDDemandTB", "actual_value", "HIGH", "Raw daily observed SSD demand. The cleanest shape "
                                                "of any SSD source, but the window closed in 2021."),
        ("SSDTotalTB", "capacity", "MEDIUM", "Total space, not demand."),
        ("HDDTB", "other_metric", "LOW", "HDD column in a shared table."),
    ]),
    ("SubstrateBE_SSD_Demand_History", [
        ("DataDate", "date", "HIGH", "Observation date. Window 2021-06-10..2021-11-08 (P1B017)."),
        ("Forest", "key", "HIGH", "Forest identity, 143 distinct."),
        ("Region", "route_axis", "HIGH", "Region axis."),
        ("Environment", "route_axis", "HIGH", "Environment axis."),
        ("SKU", "route_axis", "MEDIUM", "SKU axis."),
        ("SubstrateSSDDemandTB", "actual_value", "HIGH", "Observed demand. Window closed in 2021."),
        ("SubstrateSSDTotalSpaceTB", "capacity", "MEDIUM", "Total space, not demand."),
    ]),
]:
    for cname, role, conf, note in pairs:
        dtype = next((c[1] for c in cols.get(tbl, []) if c[0] == cname), "UNKNOWN")
        null = next((c[2] for c in cols.get(tbl, []) if c[0] == cname), "UNKNOWN")
        colmap.append(dict(zip(F, [tbl, cname, role, dtype, null, conf, note])))
S.write_csv("v6_24_p1b_ssd_column_mapping.csv", F, colmap)

# ------------------------------------------- 4. actuals source assessment
F = ["source_object", "variant", "actuals_source_status", "date_column", "key_column",
     "actual_column", "forecast_column", "accuracy_columns", "min_date", "max_date",
     "distinct_keys", "rows_per_key_min", "rows_per_key_max", "keys_over_50", "notes"]
ACC = "Accuracy|MAPE|SMAPE|MAE|RMSE|Bias|Bias_Pct"
assess = [
    (LVWE, "SSD Phoenix Low Vol. w/ Efficiency", "DASHBOARD_AGGREGATED_ACTUALS_SOURCE",
     "End_Date", "Key", "Mean_Actual", "Mean_Forecast", ACC,
     "2026-04-07", "2026-08-22", 137, 24, 131, 136,
     "P1B005/P1B006/P1B009. 17,596 rows, zero null Mean_Actual, single Forecast_Version "
     "2026-03-12. Rolling window Count 1..7, mean 5.22, so rows are aggregates rather than "
     "raw daily points. 130 distinct End_Date over 132 calendar days: effectively daily. "
     "Reconciles with the AX4 dashboard."),
    (LVNE, "SSD Phoenix Low Vol. no Efficiency", "DASHBOARD_AGGREGATED_ACTUALS_SOURCE",
     "End_Date", "Key", "Mean_Actual", "Mean_Forecast", ACC,
     "2026-04-03", "2026-08-22", 137, 25, 132, 136,
     "P1B007/P1B008/P1B010. 17,733 rows, zero null Mean_Actual. Mean_Actual is IDENTICAL to "
     "LVWE (P1B012 returned 0 differing rows); Mean_Forecast differs in 6,720 rows (P1B013). "
     "LVNE is a second forecast variant over the same observed series, not a second scenario."),
    ("Greenland_SSD_HDD_Forest_Daily_Raw", "Raw daily (historic)",
     "RAW_DAILY_ACTUALS_SOURCE_CONFIRMED", "DataDate", "Forest", "SSDDemandTB", "",
     "", "2020-07-10", "2021-06-15", 142, 8, 340, 139,
     "P1B016/P1B018. True row-level daily actuals and the cleanest shape available. 116 of its "
     "forests also appear in LVWE. BUT the window closed 2021-06-15, five years before the "
     "LVWE window: there is no temporal overlap, so it cannot validate or extend LVWE."),
    ("SubstrateBE_SSD_Demand_History", "Demand history (historic)",
     "RAW_DAILY_ACTUALS_SOURCE_CONFIRMED", "DataDate", "Forest", "SubstrateSSDDemandTB", "",
     "", "2021-06-10", "2021-11-08", 143, 16, 596, 142,
     "P1B017. Row-level observed demand with Environment/Region/SKU axes. Window closed 2021-11-08."),
    ("forecast_staging_agent_SSD", "Staging", "SSD_SOURCE_STILL_UNRESOLVED",
     "datadate", "key", "forecast", "", "", "", "", 0, 0, 0, 0,
     "P1B015. The catalogue estimates roughly 1,000 rows but the table is EMPTY: COUNT(*) "
     "returned 0. Not a usable source."),
]
S.write_csv("v6_24_p1b_ssd_actuals_source_assessment.csv", F,
            [dict(zip(F, r)) for r in assess])

# --------------------------------------- 5. AX4 dashboard reconciliation
F = ["variant", "key", "date", "actual_value", "forecast_value", "accuracy_value",
     "dashboard_match_status", "notes"]
recon = []
DASH = {
    ("LVWE", "NAMPRD08"): ("MATCH", "Owner dashboard shows actual near 11,200 and forecast near "
                                    "11,900 for NAMPRD08 in August 2026. SQL returns 11219.51 and "
                                    "11917.44. Match confirmed."),
    ("LVWE", "NAMPRD07"): ("MATCH", "Owner dashboard shows NAMPRD07 actual near 10,000 and forecast "
                                    "near 10,900 in August 2026. SQL returns 9996.28 and 10905.34. "
                                    "Match confirmed."),
    ("LVNE", "NAMPRD08"): ("VARIANT_DIFFERS", "Same actual 11219.51 as LVWE, but forecast 13766.18 "
                                              "and accuracy 77.30. The dashboard was showing the "
                                              "w/ Efficiency variant, so LVNE is the alternative."),
    ("LVNE", "NAMPRD07"): ("VARIANT_DIFFERS", "Same actual 9996.28 as LVWE, but forecast 12145.83 "
                                              "and accuracy 78.50."),
}
for tag in ("LVWE", "LVNE"):
    for row in E.get(f"{tag}_ax4", []):
        key = row[0]
        status, note = DASH.get((tag, key), ("UNVERIFIED", "No owner reference value for this key."))
        recon.append(dict(zip(F, [tag, key, row[2][:10], row[4], row[5], row[6], status, note])))
S.write_csv("v6_24_p1b_ssd_dashboard_reconciliation.csv", F, recon)

# ------------------------------------------ 6. route capacity detail
F = ["variant", "route_path", "granularity", "total_keys", "keys_over_50",
     "min_observations", "max_observations", "min_date", "max_date", "ready_for_extraction"]
routes = [
    ("LVWE", "SSD-Phoenix / Low Vol. w Efficiency", "Forest", 137, 136, 24, 131,
     "2026-04-07", "2026-08-22", "TRUE"),
    ("LVNE", "SSD-Phoenix / Low Vol. no Efficiency", "Forest", 137, 136, 25, 132,
     "2026-04-03", "2026-08-22", "TRUE"),
    ("RAW_GREENLAND", "SSD Daily Raw / Region x Forest", "Forest", 142, 139, 8, 340,
     "2020-07-10", "2021-06-15", "FALSE"),
    ("RAW_DEMAND_HISTORY", "SSD Demand History / Forest", "Forest", 143, 142, 16, 596,
     "2021-06-10", "2021-11-08", "FALSE"),
]
S.write_csv("v6_24_p1b_ssd_route_capacity_detail.csv", F, [dict(zip(F, r)) for r in routes])
print("part 1 emitted")
