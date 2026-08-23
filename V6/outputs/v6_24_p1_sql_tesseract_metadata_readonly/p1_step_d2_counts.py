"""V6.24-P1 Step D2 | Row counts and ValueType vocabulary for candidate sources.

Step D's catalogue-count query failed (recorded in the ledger), so counts are
measured here with sys.partitions first and a direct COUNT(*) fallback.

Read-only. Aggregates only, no row extraction.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

# The four *_region tables share the identical 12-column contract that V6
# already consumes for HDD, so they are the primary actuals candidates.
PRIMARY = [
    ("HDD", "forecast_substrateBE_hdd_region"),
    ("CPU", "forecast_substrateBE_cpu_region"),
    ("CPU", "forecast_substrateBE_cpu_actual_region"),
    ("IOPS", "forecast_substrateBE_iops_region"),
    ("IOPS", "forecast_substrateBE_iops_actual_region"),
    ("SSD", "forecast_substrateBE_ssd_region"),
    ("SSD", "forecast_substrateBE_SSD_Phoenix_Organic"),
]

part = S.run(
    """
    SELECT t.name, SUM(p.rows)
    FROM sys.partitions p
    JOIN sys.tables t ON t.object_id = p.object_id
    WHERE p.index_id IN (0, 1)
    GROUP BY t.name
    """,
    metric="ALL", obj="sys.partitions",
    purpose="Catalogue row counts via sys.partitions (fallback after Q019 failed)",
)
counts = {r[0]: int(r[1]) for r in part}
print(f"CATALOGUE_COUNTS={len(counts)}")

report = {}
for metric, tbl in PRIMARY:
    n = counts.get(tbl)
    print(f"\n=== {metric} | {tbl} | catalogue_rows={n} ===")
    entry = {"metric": metric, "catalogue_rows": n, "value_types": [],
             "scenario_types": [], "date_range": None}

    if n is None or n == 0:
        print("    SKIP: no catalogue count available or table empty")
        report[tbl] = entry
        continue

    vt = S.run(
        f"SELECT ValueType, COUNT(*) AS n, MIN(DateTime), MAX(DateTime), "
        f"COUNT(DISTINCT [Key]) FROM dbo.[{tbl}] GROUP BY ValueType",
        metric=metric, obj=tbl,
        purpose="ValueType split with date range and distinct key count",
        qtype="aggregate",
    )
    entry["value_types"] = [
        {"value_type": str(r[0]), "rows": int(r[1]), "min_date": str(r[2]),
         "max_date": str(r[3]), "distinct_keys": int(r[4])} for r in vt
    ]
    for e in entry["value_types"]:
        print(f"    ValueType={e['value_type']:<12} rows={e['rows']:>10,} "
              f"{e['min_date']}..{e['max_date']} keys={e['distinct_keys']}")
    report[tbl] = entry

(OUT / "_stepD2_counts.json").write_text(json.dumps(report, indent=1, default=str),
                                         encoding="utf-8")
S.save_ledger()
