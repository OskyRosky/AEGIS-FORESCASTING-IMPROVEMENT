"""V6.24-P1 Step B | Column metadata for the Demand_* serving family.

Read-only. INFORMATION_SCHEMA only, no data pages touched.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

rows = S.run(
    """
    SELECT TABLE_SCHEMA, TABLE_NAME, ORDINAL_POSITION, COLUMN_NAME,
           DATA_TYPE, IS_NULLABLE, CHARACTER_MAXIMUM_LENGTH
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME LIKE 'vw_SubstrateBE_Demand[_]%'
       OR TABLE_NAME LIKE 'forecast_substrateBE_%actual%'
       OR TABLE_NAME LIKE 'DemandPlan_SubstrateBE_%History'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """,
    metric="ALL", obj="INFORMATION_SCHEMA.COLUMNS",
    purpose="Column metadata for Demand_* serving views and *_actual*/History tables",
)

by_obj: dict[str, list[dict]] = {}
for r in rows:
    by_obj.setdefault(r[1], []).append({
        "ordinal": r[2], "column_name": r[3], "data_type": r[4],
        "is_nullable": r[5], "max_len": r[6],
    })

print(f"OBJECTS_WITH_COLUMNS={len(by_obj)}")
for obj, cols in sorted(by_obj.items()):
    sig = ", ".join(f"{c['column_name']}:{c['data_type']}" for c in cols)
    print(f"{obj} || {sig}")

(OUT / "_stepB_columns.json").write_text(json.dumps(by_obj, indent=1), encoding="utf-8")
S.save_ledger()
