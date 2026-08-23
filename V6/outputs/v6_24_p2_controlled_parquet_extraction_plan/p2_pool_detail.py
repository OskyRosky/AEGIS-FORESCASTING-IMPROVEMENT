"""V6.24-P2 | Per-key sanity detail for the SSD, CPU and IOPS candidate pools.

P1/P1B measured these pools in aggregate. Selecting a representative cohort needs
per-key observation counts and date ranges, so three grouped-count queries are
issued here. No time-series rows are returned.

Budget: 10 queries. This uses 3. Read-only.
"""

from __future__ import annotations

import atexit
import json
from pathlib import Path

import _p2_sql as S

OUT = Path(__file__).resolve().parent
S.load_ledger()
R = {}
atexit.register(lambda: (
    (OUT / "_p2_pools.json").write_text(json.dumps(R, indent=1, default=str), encoding="utf-8"),
    S.save_ledger(),
))

# --- SSD: 137 forest keys from the LVWE metrics table ---
# Mean_Actual is stored as varchar (P2Q001 failed on AVG). TRY_CAST both measures
# the values and counts any row that does not parse as a number, which is a real
# extraction risk for P3.
R["ssd"] = [
    {"key": str(r[0]), "obs": int(r[1]), "non_numeric": int(r[2]),
     "min_date": str(r[3])[:10], "max_date": str(r[4])[:10],
     "mean_actual_avg": round(float(r[5]), 2) if r[5] is not None else None}
    for r in S.run(
        """
        SELECT [Key], COUNT(*) AS obs,
               SUM(CASE WHEN TRY_CAST(Mean_Actual AS FLOAT) IS NULL THEN 1 ELSE 0 END) AS non_numeric,
               MIN(Start_Date), MAX(End_Date), AVG(TRY_CAST(Mean_Actual AS FLOAT))
        FROM dbo.[forecast_substrateBE_ssd_phx_lvwe_metrics]
        WHERE Mean_Actual IS NOT NULL
        GROUP BY [Key]
        ORDER BY [Key]
        """,
        obj="forecast_substrateBE_ssd_phx_lvwe_metrics",
        purpose="Per-key observation counts, date ranges and non-numeric Mean_Actual detection",
        qtype="aggregate",
    )
]
bad = sum(x["non_numeric"] for x in R["ssd"])
print(f"SSD_POOL={len(R['ssd'])} over50={sum(1 for x in R['ssd'] if x['obs'] > 50)} "
      f"non_numeric_Mean_Actual_rows={bad}")

# --- CPU: Scenario x Key from the confirmed actuals table ---
R["cpu"] = [
    {"scenario": str(r[0]), "key": str(r[1]), "obs": int(r[2]),
     "min_date": str(r[3])[:10], "max_date": str(r[4])[:10]}
    for r in S.run(
        """
        SELECT Scenario, [Key], COUNT(*) AS obs, MIN(DateTime), MAX(DateTime)
        FROM dbo.[forecast_substrateBE_cpu_actual_region]
        WHERE ModelVersion = 'Actual' AND Value IS NOT NULL
        GROUP BY Scenario, [Key]
        ORDER BY Scenario, [Key]
        """,
        obj="forecast_substrateBE_cpu_actual_region",
        purpose="Per-scenario-per-key observation counts for the CPU candidate pool",
        qtype="aggregate",
    )
]
print(f"CPU_POOL={len(R['cpu'])} over50={sum(1 for x in R['cpu'] if x['obs'] > 50)}")

# --- IOPS: Scenario x Key from the confirmed actuals table ---
R["iops"] = [
    {"scenario": str(r[0]), "key": str(r[1]), "obs": int(r[2]),
     "min_date": str(r[3])[:10], "max_date": str(r[4])[:10]}
    for r in S.run(
        """
        SELECT Scenario, [Key], COUNT(*) AS obs, MIN(DateTime), MAX(DateTime)
        FROM dbo.[forecast_substrateBE_iops_actual_region]
        WHERE ModelVersion = 'Actual' AND Value IS NOT NULL
        GROUP BY Scenario, [Key]
        ORDER BY Scenario, [Key]
        """,
        obj="forecast_substrateBE_iops_actual_region",
        purpose="Per-scenario-per-key observation counts for the IOPS candidate pool",
        qtype="aggregate",
    )
]
print(f"IOPS_POOL={len(R['iops'])} over50={sum(1 for x in R['iops'] if x['obs'] > 50)}")

print(f"\nSSD keys sample: {[x['key'] for x in R['ssd'][:8]]}")
print(f"CPU keys sample: {sorted({x['key'] for x in R['cpu']})[:12]}")
print(f"IOPS keys sample: {sorted({x['key'] for x in R['iops']})[:12]}")
print(f"CPU scenarios: {sorted({x['scenario'] for x in R['cpu']})}")
print(f"IOPS scenarios: {sorted({x['scenario'] for x in R['iops']})}")
