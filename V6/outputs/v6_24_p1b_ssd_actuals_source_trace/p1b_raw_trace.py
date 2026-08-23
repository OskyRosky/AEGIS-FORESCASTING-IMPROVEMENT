"""V6.24-P1B step 2 | Raw daily source trace and series continuity.

Q13 asks whether a raw daily SSD source exists behind the LVWE/LVNE metrics, or
whether Mean_Actual must be treated as the official observed series.

sys.sql_modules lineage returned 0 hits, so the tables are populated by an
external pipeline. This measures the standalone raw candidates directly.

Read-only.
"""

from __future__ import annotations

import atexit
import json
from pathlib import Path

import _p1b_sql as S

OUT = Path(__file__).resolve().parent
S.load_ledger()
R = json.loads((OUT / "_p1b_evidence.json").read_text(encoding="utf-8"))
atexit.register(lambda: (
    (OUT / "_p1b_evidence.json").write_text(json.dumps(R, indent=1, default=str), encoding="utf-8"),
    S.save_ledger(),
))

LVWE = "forecast_substrateBE_ssd_phx_lvwe_metrics"

# --- Q13a. Is LVWE a continuous daily series? ---
r = S.run(
    f"SELECT COUNT(DISTINCT End_Date), COUNT(DISTINCT Start_Date), "
    f"DATEDIFF(day, MIN(End_Date), MAX(End_Date)) + 1 FROM dbo.[{LVWE}]",
    obj=LVWE, purpose="Q13: distinct window end dates versus calendar span, to test daily continuity",
    qtype="aggregate",
)
x = r[0]
print(f"LVWE distinct_End_Date={x[0]} distinct_Start_Date={x[1]} calendar_days={x[2]}")
R["lvwe_continuity"] = [int(v) for v in x]

# --- Q13b. forecast_staging_agent_SSD: catalogue says ~1000 rows ---
r = S.run(
    "SELECT COUNT(*), COUNT(DISTINCT [key]), MIN(datadate), MAX(datadate), "
    "COUNT(DISTINCT type) FROM dbo.[forecast_staging_agent_SSD]",
    obj="forecast_staging_agent_SSD",
    purpose="Q13: staging table coverage as a raw daily candidate", qtype="aggregate",
)
x = r[0]
print(f"staging_agent_SSD rows={x[0]} keys={x[1]} {x[2]}..{x[3]} types={x[4]}")
R["staging_agent_ssd"] = [str(v) for v in x]

# --- Q13c/d. The two standalone raw daily candidates ---
for tbl, dcol, vcol, kcol in [
    ("Greenland_SSD_HDD_Forest_Daily_Raw", "DataDate", "SSDDemandTB", "Forest"),
    ("SubstrateBE_SSD_Demand_History", "DataDate", "SubstrateSSDDemandTB", "Forest"),
]:
    r = S.run(
        f"""
        SELECT COUNT(*) AS combos,
               SUM(CASE WHEN obs > 50 THEN 1 ELSE 0 END) AS over_50,
               MIN(obs), MAX(obs), MIN(d0), MAX(d1)
        FROM (SELECT [{kcol}], COUNT(*) AS obs, MIN([{dcol}]) d0, MAX([{dcol}]) d1
              FROM dbo.[{tbl}] WHERE [{vcol}] IS NOT NULL GROUP BY [{kcol}]) t
        """,
        obj=tbl, purpose="Q13: raw daily candidate coverage and keys over 50 observations",
        qtype="aggregate",
    )
    x = r[0]
    print(f"{tbl}: keys={x[0]} over_50={x[1]} obs={x[2]}..{x[3]} {str(x[4])[:10]}..{str(x[5])[:10]}")
    R[f"raw_{tbl}"] = [str(v) for v in x]

# --- Q13e. Do the raw sources share keys with LVWE? ---
r = S.run(
    f"""
    SELECT COUNT(DISTINCT g.Forest)
    FROM dbo.[Greenland_SSD_HDD_Forest_Daily_Raw] g
    WHERE g.Forest IN (SELECT DISTINCT [Key] FROM dbo.[{LVWE}])
    """,
    obj="Greenland_SSD_HDD_Forest_Daily_Raw",
    purpose="Q13: overlap between the raw daily forests and the LVWE key space",
    qtype="aggregate",
)
print(f"Greenland forests also present in LVWE: {r[0][0]}")
R["greenland_lvwe_key_overlap"] = int(r[0][0])
print("step 2 complete")
