"""V6.24-P1B step 2 | Probe SSD objects carrying actual-vs-forecast semantics.

Targets come from the owner's AX4 dashboard: scenario "SSD Phoenix Low Vol. w/
Efficiency", keys NAMPRD04..NAMPRD11, actuals through August 2026.

All target tables are small (<= 55k rows per sys.partitions), so these aggregates
are cheap. Read-only.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")
rep = {}

# --- A. Accuracy metrics tables named exactly after the dashboard scenarios ---
for tbl in ["forecast_substrateBE_ssd_phx_lvwe_metrics",
            "forecast_substrateBE_ssd_phx_lvne_metrics"]:
    print(f"\n=== {tbl} ===")
    r = S.run(
        f"SELECT COUNT(*), COUNT(DISTINCT [Key]), MIN(Start_Date), MAX(End_Date), "
        f"MIN(Forecast_Version), MAX(Forecast_Version), MIN(Count), MAX(Count) "
        f"FROM dbo.[{tbl}]",
        metric="SSD", obj=tbl, purpose="Coverage of the accuracy metrics table",
        qtype="aggregate",
    )
    if r:
        x = r[0]
        print(f"   rows={x[0]:,} distinct_keys={x[1]} window={x[2]}..{x[3]}")
        print(f"   forecast_version={x[4]}..{x[5]}  obs_count_per_row={x[6]}..{x[7]}")
        rep[f"{tbl}_coverage"] = [str(v) for v in x]

    k = S.run(
        f"SELECT TOP 15 [Key], COUNT(*) AS n, MAX(Count) AS max_obs, MAX(End_Date) AS last_end "
        f"FROM dbo.[{tbl}] GROUP BY [Key] ORDER BY 2 DESC",
        metric="SSD", obj=tbl, purpose="Key vocabulary with observation counts",
        qtype="vocabulary",
    )
    for x in k:
        print(f"     {str(x[0]):<16} rows={x[1]:>5} max_obs={x[2]} last_end={x[3]}")
    rep[f"{tbl}_keys"] = [[str(x[0]), int(x[1]), int(x[2] or 0), str(x[3])] for x in k]

# --- B. Row-level staging table ---
print("\n=== forecast_staging_agent_SSD (1,000 rows) ===")
r = S.run(
    "SELECT type, COUNT(*), MIN(datadate), MAX(datadate), COUNT(DISTINCT [key]) "
    "FROM dbo.[forecast_staging_agent_SSD] GROUP BY type ORDER BY 2 DESC",
    metric="SSD", obj="forecast_staging_agent_SSD",
    purpose="type vocabulary: hunting a row-level actual marker", qtype="vocabulary",
)
for x in r[:20]:
    print(f"   {str(x[0]).strip():<28} rows={x[1]:>6,} {x[2]}..{x[3]} keys={x[4]}")
rep["staging_agent_ssd_type"] = [[str(x[0]), int(x[1]), str(x[2]), str(x[3]), int(x[4])] for x in r]

# --- C. SSD demand history table ---
print("\n=== SubstrateBE_SSD_Demand_History ===")
c = S.run(
    "SELECT COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
    "WHERE TABLE_NAME = 'SubstrateBE_SSD_Demand_History' ORDER BY ORDINAL_POSITION",
    metric="SSD", obj="SubstrateBE_SSD_Demand_History", purpose="Column signature",
)
print(f"   cols: {[x[0] for x in c]}")
rep["ssd_demand_history_cols"] = [[x[0], x[1]] for x in c]

(OUT / "_p1b_probe.json").write_text(json.dumps(rep, indent=1, default=str), encoding="utf-8")
S.save_ledger()
