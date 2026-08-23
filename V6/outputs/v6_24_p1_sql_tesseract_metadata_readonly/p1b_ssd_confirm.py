"""V6.24-P1B step 3 | Confirm SSD actuals semantics and measure the >50 threshold.

The lvwe/lvne metrics tables match the owner's AX4 dashboard exactly (137 forest
keys, window 2026-04-07..2026-08-22). This confirms Mean_Actual is a real observed
series and counts how many keys clear 50 observations.

Also checks SubstrateBE_SSD_Demand_History as a second, row-level actuals source.

Read-only.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")
rep = {}

# --- A. Sample lvwe for a dashboard key to verify Mean_Actual is real ---
r = S.run(
    "SELECT TOP 8 [Key], Start_Date, End_Date, Count, Mean_Actual, Mean_Forecast, "
    "Accuracy, MAPE, Forecast_Version FROM dbo.[forecast_substrateBE_ssd_phx_lvwe_metrics] "
    "WHERE [Key] = 'NAMPRD08' ORDER BY End_Date DESC",
    metric="SSD", obj="forecast_substrateBE_ssd_phx_lvwe_metrics",
    purpose="Sample NAMPRD08 to verify Mean_Actual against the owner's dashboard",
    qtype="sample",
)
print("=== lvwe | NAMPRD08 (dashboard key) ===")
for x in r:
    print(f"   {x[1]}..{x[2]} n={x[3]} actual={x[4]} forecast={x[5]} acc={x[6]}")
rep["lvwe_sample_NAMPRD08"] = [[str(v) for v in x] for x in r]

# --- B. Combinations over 50 observations, per scenario table ---
for tbl, scen in [("forecast_substrateBE_ssd_phx_lvwe_metrics", "SSD Phoenix Low Vol. w/ Efficiency"),
                  ("forecast_substrateBE_ssd_phx_lvne_metrics", "SSD Phoenix Low Vol. no Efficiency")]:
    r = S.run(
        f"""
        SELECT COUNT(*) AS keys_total,
               SUM(CASE WHEN obs > 50 THEN 1 ELSE 0 END) AS keys_over_50,
               MIN(obs) AS min_obs, MAX(obs) AS max_obs,
               MIN(d0) AS date_min, MAX(d1) AS date_max
        FROM (
            SELECT [Key], COUNT(*) AS obs, MIN(Start_Date) AS d0, MAX(End_Date) AS d1
            FROM dbo.[{tbl}]
            WHERE Mean_Actual IS NOT NULL
            GROUP BY [Key]
        ) t
        """,
        metric="SSD", obj=tbl,
        purpose="Keys with more than 50 non-null Mean_Actual observations",
        qtype="aggregate",
    )
    if r:
        x = r[0]
        print(f"\n=== {scen} ===")
        print(f"   keys={x[0]} over_50={x[1]} obs={x[2]}..{x[3]} {x[4]}..{x[5]}")
        rep[f"{tbl}_over50"] = [str(v) for v in x]

# --- C. SubstrateBE_SSD_Demand_History as a row-level actuals source ---
r = S.run(
    "SELECT COUNT(*), MIN(DataDate), MAX(DataDate), COUNT(DISTINCT Forest), "
    "COUNT(DISTINCT Region), COUNT(DISTINCT Environment) "
    "FROM dbo.[SubstrateBE_SSD_Demand_History]",
    metric="SSD", obj="SubstrateBE_SSD_Demand_History",
    purpose="Coverage of the SSD demand history table", qtype="aggregate",
)
if r:
    x = r[0]
    print(f"\n=== SubstrateBE_SSD_Demand_History ===")
    print(f"   rows={x[0]:,} {x[1]}..{x[2]} forests={x[3]} regions={x[4]} envs={x[5]}")
    rep["ssd_demand_history_coverage"] = [str(v) for v in x]

r = S.run(
    """
    SELECT COUNT(*) AS combos, SUM(CASE WHEN obs > 50 THEN 1 ELSE 0 END) AS over_50,
           MIN(obs), MAX(obs)
    FROM (SELECT Forest, COUNT(*) AS obs FROM dbo.[SubstrateBE_SSD_Demand_History]
          WHERE SubstrateSSDDemandTB IS NOT NULL GROUP BY Forest) t
    """,
    metric="SSD", obj="SubstrateBE_SSD_Demand_History",
    purpose="Forest combinations with more than 50 demand observations", qtype="aggregate",
)
if r:
    x = r[0]
    print(f"   forests={x[0]} over_50={x[1]} obs={x[2]}..{x[3]}")
    rep["ssd_demand_history_over50"] = [str(v) for v in x]

(OUT / "_p1b_confirm.json").write_text(json.dumps(rep, indent=1, default=str), encoding="utf-8")
S.save_ledger()
