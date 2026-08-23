"""V6.24-P1 Step D | Actuals source assessment for the forecast_substrateBE_* family.

Row counts come from sys.dm_db_partition_stats (catalogue metadata, no scan).
ValueType vocabulary and date ranges are measured per candidate table.

Read-only. No extraction.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

CANDIDATES = {
    "HDD": ["forecast_substrateBE_hdd_region", "forecast_substrateBE_hdd"],
    "CPU": ["forecast_substrateBE_cpu_actual_region", "forecast_substrateBE_cpu_region",
            "forecast_substrateBE_cpu"],
    "IOPS": ["forecast_substrateBE_iops_actual_region", "forecast_substrateBE_iops_region",
             "forecast_substrateBE_iops"],
    "SSD": ["forecast_substrateBE_ssd_region", "forecast_substrateBE_ssd",
            "forecast_substrateBE_SSD_Phoenix_Organic"],
    "MEMORY": [],
}

# 1. Cheap catalogue row counts for every user table at once.
counts = {
    r[0]: int(r[1]) for r in S.run(
        """
        SELECT t.name, SUM(p.row_count)
        FROM sys.dm_db_partition_stats p
        JOIN sys.tables t ON t.object_id = p.object_id
        WHERE p.index_id IN (0, 1)
        GROUP BY t.name
        """,
        metric="ALL", obj="sys.dm_db_partition_stats",
        purpose="Catalogue row counts for all user tables (no table scan)",
    )
}
print(f"TABLES_WITH_COUNTS={len(counts)}")

# 2. Column signatures for the candidate tables.
cols = {}
for r in S.run(
    """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME LIKE 'forecast[_]substrateBE[_]%'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """,
    metric="ALL", obj="INFORMATION_SCHEMA.COLUMNS",
    purpose="Column signatures for forecast_substrateBE_* candidate tables",
):
    cols.setdefault(r[0], []).append((r[1], r[2]))

report = {}
for metric, tables in CANDIDATES.items():
    for tbl in tables:
        n = counts.get(tbl, 0)
        sig = cols.get(tbl, [])
        colnames = [c[0] for c in sig]
        print(f"\n=== {metric} | {tbl} | catalogue_rows={n:,} ===")
        print(f"    columns: {', '.join(f'{c}:{t}' for c, t in sig)}")
        entry = {"metric": metric, "catalogue_rows": n, "columns": sig,
                 "value_types": [], "date_range": None}

        if n > 0:
            vt_col = next((c for c in colnames if c.lower() in ("valuetype", "value_type")), None)
            if vt_col:
                vt = S.run(
                    f"SELECT [{vt_col}], COUNT(*) FROM dbo.[{tbl}] GROUP BY [{vt_col}]",
                    metric=metric, obj=tbl, purpose=f"{vt_col} vocabulary and row split",
                    qtype="vocabulary",
                )
                entry["value_types"] = [[str(r[0]), int(r[1])] for r in vt]
                print(f"    {vt_col}: {entry['value_types']}")
        report[tbl] = entry

(OUT / "_stepD_candidates.json").write_text(json.dumps(report, indent=1, default=str),
                                            encoding="utf-8")
S.save_ledger()
