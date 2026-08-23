"""V6.24-P1 Step E | Axis vocabularies: Type, Scenario, ModelVersion.

ValueType proved useless (always 'Forecast-Mean'), so the actual-vs-forecast
marker must live in another axis column. This measures all three across the four
*_region tables that share the V6 contract.

Read-only. GROUP BY aggregates only.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

TABLES = [
    ("HDD", "forecast_substrateBE_hdd_region"),
    ("CPU", "forecast_substrateBE_cpu_region"),
    ("CPU", "forecast_substrateBE_cpu_actual_region"),
    ("IOPS", "forecast_substrateBE_iops_region"),
    ("IOPS", "forecast_substrateBE_iops_actual_region"),
    ("SSD", "forecast_substrateBE_ssd_region"),
]

report = {}
for metric, tbl in TABLES:
    print(f"\n=== {metric} | {tbl} ===")
    entry = {"metric": metric}
    for col in ("Type", "Scenario", "ModelVersion"):
        rows = S.run(
            f"SELECT [{col}], COUNT(*) AS n, MIN(DateTime), MAX(DateTime) "
            f"FROM dbo.[{tbl}] GROUP BY [{col}] ORDER BY n DESC",
            metric=metric, obj=tbl, purpose=f"{col} vocabulary with row count and date range",
            qtype="vocabulary",
        )
        vals = [{"value": str(r[0]), "rows": int(r[1]),
                 "min_date": str(r[2]), "max_date": str(r[3])} for r in rows]
        entry[col] = vals
        print(f"  {col}:")
        for v in vals[:25]:
            print(f"     {v['value']:<30} rows={v['rows']:>10,}  "
                  f"{v['min_date']}..{v['max_date']}")
        if len(vals) > 25:
            print(f"     ... (+{len(vals) - 25} more)")
    report[tbl] = entry

(OUT / "_stepE_vocab.json").write_text(json.dumps(report, indent=1, default=str),
                                       encoding="utf-8")
S.save_ledger()
