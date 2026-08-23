"""V6.24-P2A | Independent SQL verification of the 50 selected SSD keys.

Pre-P3 gate. The P2 closure reported an SSD observation range of 24-131, which
was the eligible POOL range rather than the SELECTED range. This re-measures the
50 selected keys directly, from SQL, without trusting the P2 plan file.

Budget: 8 queries. Read-only. No time-series rows are returned.
"""

from __future__ import annotations

import atexit
import csv
import json
from pathlib import Path

import _p2a_sql as S

OUT = Path(__file__).resolve().parent
P2 = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan"

S.load_ledger()
R = {}
atexit.register(lambda: (
    (OUT / "_p2a_evidence.json").write_text(json.dumps(R, indent=1, default=str),
                                            encoding="utf-8"),
    S.save_ledger(),
))

LVWE = "forecast_substrateBE_ssd_phx_lvwe_metrics"
LVNE = "forecast_substrateBE_ssd_phx_lvne_metrics"

plan = list(csv.DictReader((P2 / "v6_24_p2_ssd_50_extraction_plan.csv").open(encoding="utf-8")))
keys = [r["key"] for r in plan]
R["p2_keys"] = keys
print(f"P2_SELECTED_KEYS={len(keys)} unique={len(set(keys))}")

ph = ",".join("?" for _ in keys)

# --- 1. Per-key verification against LVWE, the canonical observed source ---
R["lvwe"] = [
    {"key": str(r[0]), "total_rows": int(r[1]), "parseable": int(r[2]),
     "non_parseable": int(r[3]), "null_actual": int(r[4]),
     "min_date": str(r[5])[:10], "max_date": str(r[6])[:10],
     "distinct_dates": int(r[7])}
    for r in S.run(
        f"""
        SELECT [Key],
               COUNT(*)                                                              AS total_rows,
               SUM(CASE WHEN TRY_CAST(Mean_Actual AS FLOAT) IS NOT NULL THEN 1 ELSE 0 END) AS parseable,
               SUM(CASE WHEN Mean_Actual IS NOT NULL
                         AND TRY_CAST(Mean_Actual AS FLOAT) IS NULL THEN 1 ELSE 0 END)     AS non_parseable,
               SUM(CASE WHEN Mean_Actual IS NULL THEN 1 ELSE 0 END)                  AS null_actual,
               MIN(End_Date), MAX(End_Date),
               COUNT(DISTINCT End_Date)                                              AS distinct_dates
        FROM dbo.[{LVWE}]
        WHERE [Key] IN ({ph})
        GROUP BY [Key]
        ORDER BY [Key]
        """,
        obj=LVWE,
        purpose="Per-key parseable/non-parseable actual counts and date coverage for the 50 selected keys",
        qtype="aggregate", params=tuple(keys),
    )
]
p = [x["parseable"] for x in R["lvwe"]]
print(f"LVWE verified keys={len(R['lvwe'])} parseable min={min(p)} max={max(p)} "
      f"non_parseable_total={sum(x['non_parseable'] for x in R['lvwe'])} "
      f"null_total={sum(x['null_actual'] for x in R['lvwe'])}")
print(f"keys_over_50={sum(1 for x in p if x > 50)} of {len(p)}")

# --- 2. Confirm LVNE carries an identical Mean_Actual for these 50 keys ---
diff = S.run(
    f"""
    SELECT COUNT(*) FROM (
        SELECT [Key], End_Date, Mean_Actual FROM dbo.[{LVWE}] WHERE [Key] IN ({ph})
        EXCEPT
        SELECT [Key], End_Date, Mean_Actual FROM dbo.[{LVNE}] WHERE [Key] IN ({ph})
    ) t
    """,
    obj=f"{LVWE} EXCEPT {LVNE}",
    purpose="Confirm LVNE Mean_Actual is identical to LVWE for the 50 selected keys",
    qtype="aggregate", params=tuple(keys) + tuple(keys),
)
R["lvne_differing_actual_rows"] = int(diff[0][0]) if diff else -1
print(f"LVNE differing Mean_Actual rows for selected keys = {R['lvne_differing_actual_rows']}")

# --- 3. Eligible replacement pool, in case any key fails ---
R["pool"] = [
    {"key": str(r[0]), "parseable": int(r[1]), "non_parseable": int(r[2]),
     "min_date": str(r[3])[:10], "max_date": str(r[4])[:10]}
    for r in S.run(
        f"""
        SELECT [Key],
               SUM(CASE WHEN TRY_CAST(Mean_Actual AS FLOAT) IS NOT NULL THEN 1 ELSE 0 END) AS parseable,
               SUM(CASE WHEN Mean_Actual IS NOT NULL
                         AND TRY_CAST(Mean_Actual AS FLOAT) IS NULL THEN 1 ELSE 0 END)     AS non_parseable,
               MIN(End_Date), MAX(End_Date)
        FROM dbo.[{LVWE}]
        GROUP BY [Key]
        HAVING SUM(CASE WHEN TRY_CAST(Mean_Actual AS FLOAT) IS NOT NULL THEN 1 ELSE 0 END) > 50
        ORDER BY [Key]
        """,
        obj=LVWE,
        purpose="Full eligible replacement pool: keys with more than 50 parseable actuals",
        qtype="aggregate",
    )
]
print(f"ELIGIBLE_POOL={len(R['pool'])} (selected {len(keys)}, "
      f"spare {len(R['pool']) - len(keys)})")
print("verification queries complete")
