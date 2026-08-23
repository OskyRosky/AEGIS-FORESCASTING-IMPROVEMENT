"""V6.24-P1 Step F | Resolve the remaining actuals questions.

1. Do the large *_region tables carry ModelVersion='actual' (hidden in the tail
   of the vocabulary listings)?
2. Where do SSD actuals live, if anywhere?
3. Does Memory have any populated source?

Read-only. Targeted aggregates only.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

report = {}

# --- 1. Direct probe for an 'actual' ModelVersion in the big region tables ---
for metric, tbl in [("CPU", "forecast_substrateBE_cpu_region"),
                    ("IOPS", "forecast_substrateBE_iops_region"),
                    ("SSD", "forecast_substrateBE_ssd_region")]:
    rows = S.run(
        f"SELECT ModelVersion, COUNT(*), MIN(DateTime), MAX(DateTime), COUNT(DISTINCT [Key]) "
        f"FROM dbo.[{tbl}] WHERE ModelVersion LIKE '%actual%' GROUP BY ModelVersion",
        metric=metric, obj=tbl,
        purpose="Probe for an 'actual' ModelVersion marker", qtype="aggregate",
    )
    hit = [{"value": str(r[0]), "rows": int(r[1]), "min_date": str(r[2]),
            "max_date": str(r[3]), "keys": int(r[4])} for r in rows]
    print(f"{metric}|{tbl}|actual_marker={hit if hit else 'NONE'}")
    report[f"{tbl}::actual_probe"] = hit

# --- 2. SSD actuals hunt across every remaining SSD-shaped source ---
SSD_SOURCES = [
    ("forecast_substrateBE_SSD_Phoenix_Organic", "ModelVersion", "DateTime", "Forest"),
    ("forecast_substrateBE_SSD_TotalForecast", None, None, None),
    ("DemandPlan_SubstrateBE_SSD_Demand_Region_History", None, "DataDate", "Region"),
]
for tbl, mv, dt, key in SSD_SOURCES:
    cols = S.run(
        "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
        metric="SSD", obj=tbl, purpose="Column signature", params=(tbl,),
    )
    colnames = [c[0] for c in cols]
    print(f"\nSSD|{tbl}|columns={colnames}")
    report[f"{tbl}::columns"] = [[c[0], c[1]] for c in cols]

    if mv and mv in colnames:
        rows = S.run(
            f"SELECT [{mv}], COUNT(*), MIN([{dt}]), MAX([{dt}]), COUNT(DISTINCT [{key}]) "
            f"FROM dbo.[{tbl}] GROUP BY [{mv}] ORDER BY 2 DESC",
            metric="SSD", obj=tbl, purpose=f"{mv} vocabulary", qtype="vocabulary",
        )
        vals = [{"value": str(r[0]), "rows": int(r[1]), "min_date": str(r[2]),
                 "max_date": str(r[3]), "keys": int(r[4])} for r in rows]
        for v in vals[:15]:
            print(f"    {v['value']:<25} rows={v['rows']:>10,} "
                  f"{v['min_date']}..{v['max_date']} keys={v['keys']}")
        report[f"{tbl}::{mv}"] = vals
    elif dt and dt in colnames:
        rows = S.run(
            f"SELECT COUNT(*), MIN([{dt}]), MAX([{dt}]), COUNT(DISTINCT [{key}]) "
            f"FROM dbo.[{tbl}]",
            metric="SSD", obj=tbl, purpose="Row count and date range", qtype="aggregate",
        )
        if rows:
            r = rows[0]
            print(f"    rows={r[0]:,} {r[1]}..{r[2]} keys={r[3]}")
            report[f"{tbl}::range"] = [int(r[0]), str(r[1]), str(r[2]), int(r[3])]

# --- 3. Memory sources ---
for tbl in ["vw_SubstrateBE_MemoryRawData", "vw_SubstrateBE_Demand_Memory_Region",
            "vw_SubstrateBE_Demand_Memory_Forest"]:
    cols = S.run(
        "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_NAME = ? ORDER BY ORDINAL_POSITION",
        metric="MEMORY", obj=tbl, purpose="Column signature", params=(tbl,),
    )
    print(f"\nMEMORY|{tbl}|columns={[c[0] for c in cols]}")
    n = S.run(f"SELECT COUNT(*) FROM dbo.[{tbl}]", metric="MEMORY", obj=tbl,
              purpose="Row count", qtype="aggregate")
    total = int(n[0][0]) if n else -1
    print(f"    rows={total:,}")
    report[f"{tbl}::count"] = total

(OUT / "_stepF_resolve.json").write_text(json.dumps(report, indent=1, default=str),
                                         encoding="utf-8")
S.save_ledger()
