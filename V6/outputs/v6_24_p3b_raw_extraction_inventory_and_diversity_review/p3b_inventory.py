"""V6.24-P3B | Exact raw extraction inventory and CPU/IOPS diversity review.

Documentation only. Reads the raw Parquet written by P3 and the P2/P2A plan files.
No SQL, no Parquet writes, no normalization, no deduplication.

Produces two deliberately distinct views:
  A. observed-series view     ->  90 rows (product/UI truth)
  B. raw-extraction-unit view -> 140 rows (physical truth)
The gap between them is entirely SSD: 50 observed series stored as 100 physical
units, because LVWE and LVNE are two forecast variants over one observed series.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
P2 = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan"

FILES = {"LVWE": RAW / "ssd" / "ssd_lvwe_raw.parquet",
         "LVNE": RAW / "ssd" / "ssd_lvne_raw.parquet",
         "CPU": RAW / "cpu" / "cpu_actuals_raw.parquet",
         "IOPS": RAW / "iops" / "iops_actuals_raw.parquet"}
DF = {k: pd.read_parquet(v, engine="pyarrow") for k, v in FILES.items()}
REL = {k: str(v.relative_to(V6)).replace("\\", "/") for k, v in FILES.items()}

NA, NPS = "NOT_APPLICABLE", "NOT_PRESENT_IN_SOURCE"
UNK_DB = "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE"
LOCAL = "ALREADY_LOCAL_NOT_EXTRACTED"
STALE = "STALE_ACTUALS_SOURCE, latest date 2023-07-20"
NO15 = "15 governed model backtests DO NOT exist yet; must be generated in P5"
SSD_CAV = (f"AGGREGATED_WINDOW_ACTUALS (rolling window 1-7 days); Mean_Actual is varchar in "
           f"source and was CAST; 1 exact-duplicate row per key on 2026-04-22; {NO15}")


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


def stats(g, metric):
    grain = (["series_key", "series_date"] if metric == "SSD"
             else ["scenario", "series_key", "series_date"])
    return {
        "row_count": int(len(g)),
        "distinct_date_count": int(g["series_date"].nunique()),
        "duplicate_row_count": int(len(g) - g[grain].drop_duplicates().shape[0]),
        "min_date": str(g["series_date"].min())[:10],
        "max_date": str(g["series_date"].max())[:10],
        "parseable_actual_count": int(g["actual_value"].notna().sum()),
        "non_parseable_actual_count": (
            int((g["actual_value_source_text"].notna() & g["actual_value"].isna()).sum())
            if "actual_value_source_text" in g.columns else 0),
    }


FIELDS = ["inventory_row_id", "observed_series_id", "raw_extraction_unit_id", "metric",
          "db_type", "variant", "scenario", "segment", "demand_nature", "granularity",
          "key", "route_path", "ui_filter_path", "source_object", "raw_parquet_file",
          "raw_parquet_relative_path", "date_column", "actual_column", "forecast_column",
          "min_date", "max_date", "row_count", "distinct_date_count", "duplicate_row_count",
          "parseable_actual_count", "non_parseable_actual_count", "freshness_status",
          "caveat", "is_observed_series", "is_forecast_variant",
          "is_duplicate_physical_variant", "ui_visible_now", "ui_visible_after_p5_p6_p7",
          "notes"]


def row(metric, variant, scen, key, g, unit, obs_id, unit_id, rid, *,
        is_obs, is_var, is_dupvar, note):
    s = stats(g, metric)
    ssd = metric == "SSD"
    return dict(zip(FIELDS, [
        rid, obs_id, unit_id, metric,
        "Phoenix" if ssd else (UNK_DB if metric == "CPU" else NA),
        variant, scen, NA, str(g["demand_nature"].iloc[0]),
        "Forest" if ssd else "Region", key,
        "SSD|Phoenix|LowVolume|Forest" if ssd else f"{metric}|Organic|{scen}|Region",
        (f"Metric=SSD > DBType=Phoenix > Variant={variant} > Granularity=Forest > Key={key}"
         if ssd else
         f"Metric={metric} > Scenario={scen} > Granularity=Region > Key={key}"),
        str(g["source_object"].iloc[0]), FILES[unit].name, REL[unit],
        "End_Date" if ssd else "DateTime",
        "Mean_Actual" if ssd else "Value",
        "Mean_Forecast" if ssd else NPS,
        s["min_date"], s["max_date"], s["row_count"], s["distinct_date_count"],
        s["duplicate_row_count"], s["parseable_actual_count"], s["non_parseable_actual_count"],
        "CURRENT (to 2026-08-22)" if ssd else "STALE (to 2023-07-20)",
        SSD_CAV if ssd else f"{STALE}; {NO15}",
        is_obs, is_var, is_dupvar, "FALSE", "TRUE", note,
    ]))


# =============================================== A. observed-series view (90)
obs, rid = [], 0
for key, g in DF["LVWE"].groupby("series_key"):
    rid += 1
    obs.append(row("SSD", "LVWE+LVNE", NA, key, g, "LVWE",
                   f"OBS-SSD-{key}", "SEE_RAW_UNIT_INVENTORY", f"INV{rid:03d}",
                   is_obs="TRUE", is_var="FALSE", is_dupvar="FALSE",
                   note="One observed series. Its actual series is measured from LVWE; LVNE "
                        "carries an identical Mean_Actual and contributes only a second "
                        "forecast variant."))
for metric in ("CPU", "IOPS"):
    for (scen, key), g in DF[metric].groupby(["scenario", "series_key"]):
        rid += 1
        obs.append(row(metric, NA, scen, key, g, metric,
                       f"OBS-{metric}-{scen}-{key}", f"RAW-{metric}-{scen}-{key}",
                       f"INV{rid:03d}", is_obs="TRUE", is_var="FALSE", is_dupvar="FALSE",
                       note="Observed series is the (scenario, key) pair. This key also appears "
                            "under the other scenario as a separate series."))
write("v6_24_p3b_observed_series_inventory_90.csv", FIELDS, obs)

# ============================================ B. raw-extraction-unit view (140)
units, rid = [], 0
for unit in ("LVWE", "LVNE"):
    for key, g in DF[unit].groupby("series_key"):
        rid += 1
        units.append(row("SSD", unit, NA, key, g, unit,
                         f"OBS-SSD-{key}", f"RAW-SSD-{unit}-{key}", f"RAW{rid:03d}",
                         is_obs="TRUE" if unit == "LVWE" else "FALSE",
                         is_var="TRUE",
                         is_dupvar="FALSE" if unit == "LVWE" else "TRUE",
                         note=("Physical unit that CARRIES the observed actual series."
                               if unit == "LVWE" else
                               "Physical unit only. Its Mean_Actual duplicates LVWE exactly and "
                               "must NOT be loaded as actuals. Contributes Mean_Forecast only.")))
for metric in ("CPU", "IOPS"):
    for (scen, key), g in DF[metric].groupby(["scenario", "series_key"]):
        rid += 1
        units.append(row(metric, NA, scen, key, g, metric,
                         f"OBS-{metric}-{scen}-{key}", f"RAW-{metric}-{scen}-{key}",
                         f"RAW{rid:03d}", is_obs="TRUE", is_var="FALSE", is_dupvar="FALSE",
                         note="Physical unit maps one-to-one to an observed series."))
write("v6_24_p3b_raw_extraction_unit_inventory.csv", FIELDS, units)

# ======================================================= 4. UI filter tree
cpu_keys = int(DF["CPU"]["series_key"].nunique())
iops_keys = int(DF["IOPS"]["series_key"].nunique())
F = ["metric", "in_p3_extraction", "db_type_axis", "variant_axis", "scenario_axis",
     "segment_axis", "granularity_axis", "key_axis", "key_count", "observed_series",
     "ui_filter_path_template", "ui_visible_now", "ui_visible_after_p5_p6_p7", "caveat", "notes"]
write("v6_24_p3b_ui_filter_tree_preview.csv", F, [dict(zip(F, r)) for r in [
    ("SSD", "YES", "Phoenix (single value)", "LVWE | LVNE",
     f"{NA} (no scenario axis exists in source)", NA, "Forest (single value)",
     "50 forest keys", 50, 50,
     "Metric > DB Type > Variant > Granularity > Key", "FALSE", "TRUE", SSD_CAV,
     "Variant is a FORECAST variant. Selecting LVWE or LVNE must change the forecast line "
     "shown, never the actual line. The actual line is identical under both."),
    ("CPU", "YES", f"{UNK_DB} (do not render this axis)", NA, "Consumed | Failover", NA,
     "Region (single value)", "region-environment keys", cpu_keys, 20,
     "Metric > Scenario > Granularity > Key", "FALSE", "TRUE", f"{STALE}; {NO15}",
     f"All {cpu_keys} keys exist under BOTH scenarios, so the Key list does not change when the "
     f"Scenario changes. This enables a Consumed-vs-Failover comparison on the same region."),
    ("IOPS", "YES", f"{NA} (IOPS has no DB Type axis)", NA, "Consumed | Failover", NA,
     "Region (single value)", "region-environment keys", iops_keys, 20,
     "Metric > Scenario > Granularity > Key", "FALSE", "TRUE", f"{STALE}; {NO15}",
     f"Same structure as CPU: {iops_keys} keys under both scenarios."),
    ("HDD", f"NO ({LOCAL})", "EDB | Basilisk", NA, NA,
     "Consumer | Enterprise (EDB only; NOT_APPLICABLE under Basilisk)",
     "Forest | Region", "forest or region keys", 50, 50,
     "Metric > DB Type > Segment > Granularity > Key", "TRUE", "TRUE",
     "None. Actuals, all 15 governed backtests and forecast already local.",
     "The only metric with a CONDITIONAL segment axis: it applies under EDB and not under "
     "Basilisk. Context only in P3B; HDD raw data was neither read nor modified."),
    ("Memory", "NO (not selected)", NA, NA, NA, NA, NA, "none", 0, 0,
     "NOT_RENDERED", "FALSE", "FALSE", "BLOCKED_NO_USEFUL_ACTUALS_SOURCE",
     "Awareness gap only. Governed Demand_Memory views exist but return 0 rows."),
]])

# ================================================ 5. metric axis value inventory
F = ["metric", "axis_name", "axis_value", "applies_to_ui", "source", "count", "notes"]
axv = []
for metric, unit in (("SSD", "LVWE"), ("CPU", "CPU"), ("IOPS", "IOPS")):
    d = DF[unit]
    axv.append(dict(zip(F, [metric, "db_type", str(d["db_type"].iloc[0]),
                            "YES" if metric == "SSD" else "NO", "raw column db_type",
                            int(d["series_key"].nunique()),
                            "Rendered only for SSD. CPU and IOPS carry an explicit placeholder "
                            "that must never become a selectable filter option."])))
    for v in sorted(d["variant"].astype(str).unique()):
        axv.append(dict(zip(F, [metric, "variant", v, "YES" if metric == "SSD" else "NO",
                                "raw column variant", int((d["variant"].astype(str) == v).sum()),
                                "Forecast variant." if metric == "SSD"
                                else "No variant axis for this metric."])))
    for v in sorted(d["scenario"].astype(str).unique()):
        n = int(d[d["scenario"].astype(str) == v]["series_key"].nunique())
        axv.append(dict(zip(F, [metric, "scenario", v, "NO" if metric == "SSD" else "YES",
                                "raw column scenario", n,
                                "SSD has no scenario axis in source." if metric == "SSD"
                                else f"{n} keys available under this scenario."])))
    axv.append(dict(zip(F, [metric, "segment", NA, "NO", "constant", 0,
                            "No segment axis for any extracted metric. Only HDD has one."])))
    axv.append(dict(zip(F, [metric, "granularity", str(d["granularity"].iloc[0]), "YES",
                            "raw column granularity", 1,
                            "Single value, so informational rather than selectable."])))
    axv.append(dict(zip(F, [metric, "key", f"{d['series_key'].nunique()} distinct keys", "YES",
                            "raw column series_key", int(d["series_key"].nunique()),
                            "The only high-cardinality axis."])))
    for v in sorted(d["demand_nature"].astype(str).unique()):
        axv.append(dict(zip(F, [metric, "demand_nature", v, "NO", "raw column demand_nature",
                                int((d["demand_nature"].astype(str) == v).sum()),
                                "Informational. Not a product filter."])))
axv.append(dict(zip(F, ["SSD", "variant", "LVNE", "YES", "raw file ssd_lvne_raw.parquet",
                        int(DF["LVNE"]["series_key"].nunique()),
                        "Second forecast variant over the same 50 observed series."])))
write("v6_24_p3b_metric_axis_value_inventory.csv", F, axv)

# ==================================================== 6. SSD variant inventory
F = ["key", "observed_series_id", "lvwe_rows", "lvne_rows", "lvwe_distinct_dates",
     "lvne_distinct_dates", "actual_series_count", "forecast_variant_count",
     "duplicate_date_count", "actual_identical_across_variants", "notes"]
w, n = DF["LVWE"].groupby("series_key"), DF["LVNE"].groupby("series_key")
mg = DF["LVWE"][["series_key", "series_date", "actual_value"]].merge(
    DF["LVNE"][["series_key", "series_date", "actual_value"]],
    on=["series_key", "series_date"], suffixes=("_w", "_n"))
diff_by_key = mg.assign(d=mg["actual_value_w"] != mg["actual_value_n"]) \
                .groupby("series_key")["d"].sum()
var = []
for key in sorted(DF["LVWE"]["series_key"].unique()):
    gw, gn = w.get_group(key), n.get_group(key)
    dup = int(len(gw) - gw[["series_date"]].drop_duplicates().shape[0])
    var.append(dict(zip(F, [
        key, f"OBS-SSD-{key}", int(len(gw)), int(len(gn)),
        int(gw["series_date"].nunique()), int(gn["series_date"].nunique()), 1, 2, dup,
        "TRUE" if int(diff_by_key.get(key, 0)) == 0 else "FALSE",
        f"One observed series, two forecast variants. {dup} duplicate date row(s) on 2026-04-22 "
        f"remain in the raw file; P4 must dedupe. Counts 1 toward the 90-series cohort, not 2.",
    ])))
write("v6_24_p3b_ssd_variant_inventory.csv", F, var)

# ============================================= 7/8. scenario x key matrices
for metric in ("CPU", "IOPS"):
    d = DF[metric]
    scen = sorted(d["scenario"].astype(str).unique())
    F = (["key"] + [f"in_{s}" for s in scen] + [f"rows_{s}" for s in scen]
         + ["scenarios_present", "shared_by_both_scenarios", "series_contributed", "notes"])
    rows = []
    for key in sorted(d["series_key"].unique()):
        g = d[d["series_key"] == key]
        present = {s: bool((g["scenario"].astype(str) == s).any()) for s in scen}
        counts = {s: int((g["scenario"].astype(str) == s).sum()) for s in scen}
        nsc = sum(present.values())
        rows.append(dict(zip(F, [key] + [str(present[s]).upper() for s in scen]
                             + [counts[s] for s in scen]
                             + [nsc, "TRUE" if nsc == 2 else "FALSE", nsc,
                                "Contributes 2 of the 20 series: selected under both scenarios."
                                if nsc == 2 else "Contributes 1 series."])))
    write(f"v6_24_p3b_{metric.lower()}_scenario_key_matrix.csv", F, rows)

# ================================================= 9. diversity decision table
pools = json.loads((P2 / "_p2_pools.json").read_text(encoding="utf-8"))
pool_keys = {m: len({x["key"] for x in pools[m.lower()]}) for m in ("CPU", "IOPS")}
pool_per_scen = {m: {s: len({x["key"] for x in pools[m.lower()] if x["scenario"] == s})
                     for s in sorted({x["scenario"] for x in pools[m.lower()]})}
                 for m in ("CPU", "IOPS")}
print(f"POOL unique keys={pool_keys} per_scenario={pool_per_scen}")

F = ["option_id", "option_name", "meaning", "cpu_result", "iops_result", "pros", "cons",
     "extraction_work_required", "recommended", "rationale"]
write("v6_24_p3b_cpu_iops_diversity_decision_table.csv", F, [dict(zip(F, r)) for r in [
    ("A", "KEEP_CURRENT_MVP",
     "Keep 20 CPU series over 10 keys x 2 scenarios and 20 IOPS series over 10 keys x "
     "2 scenarios, exactly as extracted in P3.",
     f"20 series over {cpu_keys} keys", f"20 series over {iops_keys} keys",
     "No re-extraction. Fastest path to P4. Already validated 33/33. PRESERVES a real "
     "analytical capability: because every key exists under BOTH scenarios, the Viewer can "
     "compare Consumed against Failover for the SAME region, which is an actual demand-planning "
     "question.",
     f"Geographic coverage is {cpu_keys} regions rather than 20. The Key list does not change "
     f"when the Scenario filter changes, which may read as a thin cohort in a demo.",
     "NONE", "YES",
     "The data is valid, the series count is exactly as planned, and the owner is prioritising "
     "MVP speed. The scenario-pair structure is arguably better for analysis than 20 unrelated "
     "keys because it supports a like-for-like comparison."),
    ("B", "PATCH_DIVERSITY_BEFORE_P4",
     "Reselect CPU and IOPS to use 20 DISTINCT keys, for example 10 keys under Consumed and 10 "
     "different keys under Failover.",
     f"achievable: pool holds {pool_keys['CPU']} distinct keys, per scenario "
     f"{pool_per_scen['CPU']}",
     f"achievable: pool holds {pool_keys['IOPS']} distinct keys, per scenario "
     f"{pool_per_scen['IOPS']}",
     "Doubles geographic coverage to 20 regions per metric. The Key list would change with the "
     "Scenario filter, demonstrating conditional filtering more convincingly.",
     "Requires a small extraction patch (about 10 new scenario-key pairs per metric). LOSES the "
     "Consumed-vs-Failover comparison on the same region, because no region would appear under "
     "both.",
     "SMALL: one extra filtered SELECT per metric, roughly 20 new series", "NO",
     "Defer. This is a presentation preference, not a data-validity issue, and it trades away a "
     "real analytical capability. Revisit after the demo if geographic breadth matters more."),
]])
print("part 1 emitted")
