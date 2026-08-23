"""V6.24-P1 Step G | Combinations over the 50-observation threshold.

Only sources with a confirmed actuals marker are measured. The route axis is
Scenario and the series axis is Key, matching the contract V6 already consumes
for HDD.

Read-only. GROUP BY / HAVING aggregates only, no row extraction.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

# (metric, table, actuals predicate)
CONFIRMED = [
    ("HDD", "forecast_substrateBE_hdd_region", "ModelVersion = 'actual'"),
    ("CPU", "forecast_substrateBE_cpu_actual_region", "ModelVersion = 'Actual'"),
    ("IOPS", "forecast_substrateBE_iops_actual_region", "ModelVersion = 'Actual'"),
]

report = {}
for metric, tbl, pred in CONFIRMED:
    print(f"\n=== {metric} | {tbl} | WHERE {pred} ===")

    rows = S.run(
        f"""
        SELECT Scenario,
               COUNT(*)                                   AS combinations,
               SUM(CASE WHEN obs > 50 THEN 1 ELSE 0 END)  AS combinations_over_50,
               MIN(obs) AS min_obs, MAX(obs) AS max_obs,
               MIN(d0)  AS date_min, MAX(d1) AS date_max
        FROM (
            SELECT Scenario, [Key], COUNT(*) AS obs,
                   MIN(DateTime) AS d0, MAX(DateTime) AS d1
            FROM dbo.[{tbl}]
            WHERE {pred}
            GROUP BY Scenario, [Key]
        ) t
        GROUP BY Scenario
        ORDER BY Scenario
        """,
        metric=metric, obj=tbl,
        purpose="Route x key combinations and how many exceed 50 real observations",
        qtype="aggregate",
    )
    detail = [{
        "scenario": str(r[0]), "combinations": int(r[1]),
        "combinations_over_50": int(r[2]), "min_obs": int(r[3]), "max_obs": int(r[4]),
        "date_min": str(r[5]), "date_max": str(r[6]),
    } for r in rows]
    for d in detail:
        print(f"  {d['scenario']:<14} combos={d['combinations']:>4} "
              f">50={d['combinations_over_50']:>4} obs={d['min_obs']}..{d['max_obs']} "
              f"{d['date_min']}..{d['date_max']}")
    report[tbl] = {"metric": metric, "predicate": pred, "by_scenario": detail}

(OUT / "_stepG_combinations.json").write_text(json.dumps(report, indent=1, default=str),
                                              encoding="utf-8")
S.save_ledger()
