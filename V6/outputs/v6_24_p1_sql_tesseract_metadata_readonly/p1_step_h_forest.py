"""V6.24-P1 Step H | Forest-granularity actuals probe.

Region granularity is already confirmed. This checks whether Forest-level actuals
also exist, which would widen the extractable cohort.

Read-only. Vocabulary and aggregate queries only.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

report = {}

# HDD forest: V6 already extracts from this table via TRIM(data_type).
rows = S.run(
    "SELECT data_type, type, COUNT(*), MIN(target_date), MAX(target_date), "
    "COUNT(DISTINCT forest_name) FROM dbo.[forecast_substrateBE_hdd] "
    "GROUP BY data_type, type ORDER BY 3 DESC",
    metric="HDD", obj="forecast_substrateBE_hdd",
    purpose="data_type/type vocabulary to locate Forest-level actuals",
    qtype="vocabulary",
)
print("=== HDD | forecast_substrateBE_hdd (Forest) ===")
hdd = []
for r in rows[:25]:
    e = {"data_type": str(r[0]).strip(), "type": str(r[1]).strip(), "rows": int(r[2]),
         "min_date": str(r[3]), "max_date": str(r[4]), "forests": int(r[5])}
    hdd.append(e)
    print(f"  data_type={e['data_type']:<14} type={e['type']:<14} rows={e['rows']:>9,} "
          f"{e['min_date'][:10]}..{e['max_date'][:10]} forests={e['forests']}")
report["forecast_substrateBE_hdd"] = hdd

# CPU / IOPS forest-shaped tables.
for metric, tbl, tcol, dcol, kcol in [
    ("CPU", "forecast_substrateBE_cpu", "type", "datadate", "Forest_SKU"),
    ("IOPS", "forecast_substrateBE_iops", "type", "datadate", "Forest_SKU"),
]:
    rows = S.run(
        f"SELECT [{tcol}], COUNT(*), MIN([{dcol}]), MAX([{dcol}]), COUNT(DISTINCT [{kcol}]) "
        f"FROM dbo.[{tbl}] GROUP BY [{tcol}] ORDER BY 2 DESC",
        metric=metric, obj=tbl, purpose=f"{tcol} vocabulary to locate Forest-level actuals",
        qtype="vocabulary",
    )
    print(f"\n=== {metric} | {tbl} (Forest) ===")
    vals = []
    for r in rows[:20]:
        e = {"type": str(r[0]).strip(), "rows": int(r[1]), "min_date": str(r[2]),
             "max_date": str(r[3]), "keys": int(r[4])}
        vals.append(e)
        print(f"  type={e['type']:<20} rows={e['rows']:>9,} "
              f"{e['min_date']}..{e['max_date']} keys={e['keys']}")
    report[tbl] = vals

(OUT / "_stepH_forest.json").write_text(json.dumps(report, indent=1, default=str),
                                        encoding="utf-8")
S.save_ledger()
