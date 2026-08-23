"""V6.24-P2 | Deterministic representative selection for the 140-series MVP cohort.

No SQL. Operates on the pools already measured:
  - HDD  : local artifact v6_24_p0_product_complete_candidates.csv (596 rows)
  - SSD  : _p2_pools.json ssd  (137 forest keys, 136 over 50)
  - CPU  : _p2_pools.json cpu  (60 scenario x key, all over 50)
  - IOPS : _p2_pools.json iops (58 scenario x key, all over 50)

Selection is reproducible: every step uses a stable sort and an explicit
tie-breaker, and no step depends on input file ordering.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
P0 = OUT.parent / "v6_24_p0_combination_inventory_reality_check"

pools = json.loads((OUT / "_p2_pools.json").read_text(encoding="utf-8"))

NA = "NOT_APPLICABLE"
NPS = "NOT_PRESENT_IN_SOURCE"
NF = "NOT_FILTERED"

FIELDS = [
    "cohort_id", "extraction_id", "selected_for_mvp", "selected_for_p3_extraction",
    "extraction_status", "metric", "db_type", "variant", "scenario", "segment",
    "demand_nature", "granularity", "key", "route_path",
    "source_object_or_artifact", "date_column", "value_column", "actual_column",
    "forecast_column", "additional_columns_to_extract", "min_date", "max_date",
    "observation_count", "passes_50_actuals", "freshness_status", "caveat",
    "selection_reason",
]


def spread(items, n, sort_key):
    """Pick n items evenly spaced across a stably sorted list.

    Sampling by stride rather than taking the head guarantees coverage of the
    whole range of the sort key (observation count), instead of clustering at
    one extreme.
    """
    ordered = sorted(items, key=sort_key)
    if n >= len(ordered):
        return ordered
    step = len(ordered) / n
    return [ordered[min(int(i * step), len(ordered) - 1)] for i in range(n)]


def round_robin_by_prefix(items, n, prefix_of, rank_key):
    """Take one item per prefix group in rotation until n are chosen.

    Guarantees geographic spread: no prefix can dominate the selection while
    other prefixes remain unrepresented.
    """
    groups: dict[str, list] = {}
    for it in items:
        groups.setdefault(prefix_of(it), []).append(it)
    for g in groups.values():
        g.sort(key=rank_key)
    chosen, ring = [], sorted(groups)
    while len(chosen) < n and any(groups[p] for p in ring):
        for p in ring:
            if groups[p] and len(chosen) < n:
                chosen.append(groups[p].pop(0))
    return chosen


rows: list[dict] = []

# ============================================================ HDD : 50 local
hdd_all = list(csv.DictReader((P0 / "v6_24_p0_product_complete_candidates.csv")
                              .open(encoding="utf-8")))
by_route: dict[str, list] = {}
for r in hdd_all:
    by_route.setdefault(r["route_id"], []).append(r)

# Equal base allocation across all six routes, remainder to the largest pools.
routes = sorted(by_route)
base, rem = divmod(50, len(routes))
alloc = {rt: base for rt in routes}
for rt in sorted(routes, key=lambda x: (-len(by_route[x]), x))[:rem]:
    alloc[rt] += 1
HDD_ALLOC = dict(alloc)

for rt in routes:
    picked = spread(by_route[rt], alloc[rt],
                    lambda r: (int(r["actual_observation_count"]), r["key_entity"]))
    for r in picked:
        seg = r["segment"] or NA
        rows.append(dict(zip(FIELDS, [
            "", "", "TRUE", "FALSE", "ALREADY_LOCAL", "HDD",
            r["db_type"], NA, NA, seg, r["demand_nature"] or "Organic",
            r["granularity"], r["key_entity"], rt,
            "LOCAL:forecast_viewer_model_outputs_v2_full.parquet|forecast_forward_outputs_v6_17_full.parquet",
            "date", "value", "actual", "15 governed model columns",
            "actuals + 15 governed backtests + forecast already present locally",
            r["first_actual_date"], r["last_actual_date"],
            int(r["actual_observation_count"]), "TRUE",
            "CURRENT (last actual 2026-08-17 fleet-wide)", NA,
            f"Route {rt}: allocated {alloc[rt]} of 50; evenly spread across the route's "
            f"observation-count range, tie-broken by key",
        ])))

# ============================================================ SSD : 50 to extract
ssd_pool = [x for x in pools["ssd"] if x["obs"] > 50]
DASH = ["NAMPRD07", "NAMPRD08"]
forced = [x for x in ssd_pool if x["key"] in DASH]
rest = [x for x in ssd_pool if x["key"] not in DASH]
ssd_pick = forced + round_robin_by_prefix(
    rest, 50 - len(forced),
    prefix_of=lambda x: x["key"][:3].upper(),
    rank_key=lambda x: (-x["obs"], x["key"]),
)
for x in ssd_pick:
    why = ("AX4 dashboard reference key, force-included" if x["key"] in DASH
           else f"Geographic round-robin on prefix {x['key'][:3].upper()}, "
                f"highest observation count first")
    rows.append(dict(zip(FIELDS, [
        "", "", "TRUE", "TRUE", "TO_EXTRACT_IN_P3", "SSD",
        "Phoenix", "LVWE+LVNE", NA, NA, "Organic", "Forest", x["key"],
        "SSD|Phoenix|LowVolume|Forest",
        "forecast_substrateBE_ssd_phx_lvwe_metrics + forecast_substrateBE_ssd_phx_lvne_metrics",
        "End_Date", "Mean_Actual", "Mean_Actual", "Mean_Forecast",
        "Start_Date,Count,MAE,RMSE,Bias,Bias_Pct,MAPE,SMAPE,Accuracy,Forecast_Version",
        x["min_date"], x["max_date"], x["obs"], "TRUE",
        "CURRENT (to 2026-08-22)",
        "AGGREGATED_WINDOW_ACTUALS (window 1-7 days, mean 5.22); "
        "Mean_Actual stored as varchar, must be CAST in P3; single Forecast_Version 2026-03-12; "
        "15 governed model backtests DO NOT exist yet and must be generated in P5",
        why,
    ])))

# ============================================================ CPU / IOPS : 20 each
for metric, pool, src, stale in [
    ("CPU", pools["cpu"], "forecast_substrateBE_cpu_actual_region", "2023-07-20"),
    ("IOPS", pools["iops"], "forecast_substrateBE_iops_actual_region", "2023-07-20"),
]:
    elig = [x for x in pool if x["obs"] > 50]
    for scen in sorted({x["scenario"] for x in elig}):
        subset = [x for x in elig if x["scenario"] == scen]
        pick = round_robin_by_prefix(
            subset, 10,
            prefix_of=lambda x: x["key"].split("-")[0],
            rank_key=lambda x: (-x["obs"], x["key"]),
        )
        for x in pick:
            dbt = ("UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE" if metric == "CPU" else NA)
            rows.append(dict(zip(FIELDS, [
                "", "", "TRUE", "TRUE", "TO_EXTRACT_IN_P3", metric,
                dbt, NA, scen, NA, "Organic", "Region", x["key"],
                f"{metric}|Organic|{scen}|Region", src,
                "DateTime", "Value", "Value", NPS,
                "ValueRef,ModelVersion,ForecastVersion,Fleet,Workload,Resource,Unit,Type,Scenario",
                x["min_date"], x["max_date"], x["obs"], "TRUE",
                f"STALE (last actual {stale})",
                f"STALE_ACTUALS_SOURCE, latest date {stale}; Region granularity only; "
                f"no forecast column in the actuals table; 15 governed model backtests "
                f"DO NOT exist yet and must be generated in P5",
                f"Scenario {scen}: 10 of 20; geographic round-robin on region prefix "
                f"{x['key'].split('-')[0]}, highest observation count first",
            ])))

# ---------------------------------------------------------------- identifiers
order = {"HDD": 0, "SSD": 1, "CPU": 2, "IOPS": 3}
rows.sort(key=lambda r: (order[r["metric"]], r["route_path"], r["key"]))
ext = 0
for i, r in enumerate(rows, start=1):
    r["cohort_id"] = f"MVP{i:03d}"
    if r["selected_for_p3_extraction"] == "TRUE":
        ext += 1
        r["extraction_id"] = f"EXT{ext:03d}"
    else:
        r["extraction_id"] = NA

(OUT / "_p2_selection.json").write_text(json.dumps(
    {"rows": rows, "hdd_alloc": HDD_ALLOC}, indent=1), encoding="utf-8")

from collections import Counter
print("SELECTED:", Counter(r["metric"] for r in rows))
print("TOTAL:", len(rows), "| P3 extraction:", ext)
print("HDD allocation:", HDD_ALLOC)
print("SSD unique keys:", len({r["key"] for r in rows if r["metric"] == "SSD"}))
print("SSD prefixes:", sorted({r["key"][:3] for r in rows if r["metric"] == "SSD"}))
for m in ("CPU", "IOPS"):
    print(f"{m} scenarios:", Counter(r["scenario"] for r in rows if r["metric"] == m))
