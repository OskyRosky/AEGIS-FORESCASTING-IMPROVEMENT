"""V6.24-P1B | SSD actuals source trace. Fresh verification, nothing from memory.

Answers Q1-Q13 of the P1B brief with live SQL. Budget: 25 queries.

Read-only.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1b_sql as S

OUT = Path(__file__).resolve().parent
S.load_ledger()
R = {}

LVWE = "forecast_substrateBE_ssd_phx_lvwe_metrics"
LVNE = "forecast_substrateBE_ssd_phx_lvne_metrics"

import atexit


def _persist():
    """Persist evidence and ledger even if a query raises.

    P1's ledger was lost because a crash skipped the save step.
    """
    (OUT / "_p1b_evidence.json").write_text(json.dumps(R, indent=1, default=str),
                                            encoding="utf-8")
    S.save_ledger()


atexit.register(_persist)

# ---------------------------------------------------------------- 1. Sweep
# Row-count estimates for every SSD-related object, from the catalogue only.
R["sweep_counts"] = [
    [r[0], r[1], int(r[2])] for r in S.run(
        """
        SELECT s.name, t.name, SUM(p.rows)
        FROM sys.partitions p
        JOIN sys.tables t ON t.object_id = p.object_id
        JOIN sys.schemas s ON s.schema_id = t.schema_id
        WHERE p.index_id IN (0,1)
          AND (t.name LIKE '%ssd%' OR t.name LIKE '%phoenix%' OR t.name LIKE '%phx%')
        GROUP BY s.name, t.name
        """,
        obj="sys.partitions", purpose="Row-count estimates for all SSD-related tables",
    )
]
print(f"SSD_TABLES_WITH_COUNTS={len(R['sweep_counts'])}")

# Every SSD-related object including views, with type.
R["sweep_objects"] = [
    [r[0], r[1], r[2]] for r in S.run(
        """
        SELECT s.name, o.name, o.type_desc
        FROM sys.objects o JOIN sys.schemas s ON s.schema_id = o.schema_id
        WHERE o.type IN ('U','V')
          AND (o.name LIKE '%ssd%' OR o.name LIKE '%phoenix%' OR o.name LIKE '%phx%')
        ORDER BY o.name
        """,
        obj="sys.objects", purpose="Enumerate all SSD-related tables and views",
    )
]
print(f"SSD_OBJECTS={len(R['sweep_objects'])}")

# Column signatures for every SSD-related object.
R["sweep_columns"] = {}
for r in S.run(
    """
    SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME LIKE '%ssd%' OR TABLE_NAME LIKE '%phoenix%' OR TABLE_NAME LIKE '%phx%'
    ORDER BY TABLE_NAME, ORDINAL_POSITION
    """,
    obj="INFORMATION_SCHEMA.COLUMNS", purpose="Column signatures for all SSD-related objects",
):
    R["sweep_columns"].setdefault(r[0], []).append([r[1], r[2], r[3]])
print(f"SSD_OBJECTS_WITH_COLUMNS={len(R['sweep_columns'])}")

# ------------------------------------------- 2. Q13: is there a raw daily source?
# Search every programmable object for references to the LVWE/LVNE tables. If a
# procedure or view builds them, its body names the upstream raw table.
R["lineage"] = [
    [r[0], r[1], r[2][:400]] for r in S.run(
        """
        SELECT o.name, o.type_desc, m.definition
        FROM sys.sql_modules m JOIN sys.objects o ON o.object_id = m.object_id
        WHERE m.definition LIKE '%lvwe%' OR m.definition LIKE '%lvne%'
        """,
        obj="sys.sql_modules",
        purpose="Q13 lineage: find any procedure or view that builds the LVWE/LVNE tables",
    )
]
print(f"LINEAGE_HITS={len(R['lineage'])}")
for x in R["lineage"]:
    print(f"   {x[0]} ({x[1]})")

# ---------------------------------------------- 3. Q2-Q7: LVWE and LVNE measured
for tag, tbl in [("LVWE", LVWE), ("LVNE", LVNE)]:
    cov = S.run(
        f"""
        SELECT COUNT(*) AS total_rows,
               SUM(CASE WHEN Mean_Actual IS NULL THEN 1 ELSE 0 END) AS null_actual,
               COUNT(DISTINCT [Key]) AS distinct_keys,
               MIN(Start_Date), MAX(Start_Date), MIN(End_Date), MAX(End_Date),
               COUNT(DISTINCT Forecast_Version) AS versions,
               MIN(Count), MAX(Count), AVG(CAST(Count AS FLOAT))
        FROM dbo.[{tbl}]
        """,
        obj=tbl, purpose=f"{tag} coverage: rows, null actuals, keys, window, version, window size",
        qtype="aggregate",
    )
    x = cov[0]
    print(f"\n=== {tag} coverage ===")
    print(f"   rows={x[0]:,} null_Mean_Actual={x[1]} keys={x[2]}")
    print(f"   Start_Date {x[3]}..{x[4]}  End_Date {x[5]}..{x[6]}")
    print(f"   forecast_versions={x[7]}  window_Count min/max/avg={x[8]}/{x[9]}/{round(x[10], 2)}")
    R[f"{tag}_coverage"] = [str(v) for v in x]

    thr = S.run(
        f"""
        SELECT COUNT(*) AS keys_total,
               SUM(CASE WHEN obs > 50 THEN 1 ELSE 0 END) AS keys_over_50,
               MIN(obs), MAX(obs), AVG(CAST(obs AS FLOAT))
        FROM (SELECT [Key], COUNT(*) AS obs FROM dbo.[{tbl}]
              WHERE Mean_Actual IS NOT NULL GROUP BY [Key]) t
        """,
        obj=tbl, purpose=f"{tag} Q5/Q6: keys with more than 50 non-null Mean_Actual observations",
        qtype="aggregate",
    )
    x = thr[0]
    print(f"   keys={x[0]} over_50={x[1]} obs_per_key {x[2]}..{x[3]} avg={round(x[4], 1)}")
    R[f"{tag}_threshold"] = [str(v) for v in x]

# ------------------------------------- 4. Q9: AX4 dashboard reconciliation
for tag, tbl in [("LVWE", LVWE), ("LVNE", LVNE)]:
    rows = S.run(
        f"SELECT TOP 6 [Key], Start_Date, End_Date, Count, Mean_Actual, Mean_Forecast, "
        f"Accuracy, MAPE, Bias_Pct, Forecast_Version FROM dbo.[{tbl}] "
        f"WHERE [Key] IN ('NAMPRD07','NAMPRD08') AND End_Date = "
        f"(SELECT MAX(End_Date) FROM dbo.[{tbl}]) ORDER BY [Key]",
        obj=tbl, purpose=f"{tag} Q9: reconcile NAMPRD07 and NAMPRD08 against the AX4 dashboard",
        qtype="sample",
    )
    print(f"\n=== {tag} | AX4 reconciliation ===")
    for x in rows:
        print(f"   {x[0]} {str(x[1])[:10]}..{str(x[2])[:10]} n={x[3]} "
              f"actual={x[4]} forecast={x[5]} acc={x[6]} mape={x[7]}")
    R[f"{tag}_ax4"] = [[str(v) for v in x] for x in rows]

# ------------------------------- 5. Q8: are the keys forest-level?
keys = S.run(
    f"SELECT DISTINCT [Key] FROM dbo.[{LVWE}] ORDER BY [Key]",
    obj=LVWE, purpose="Q8: full distinct key list to confirm forest-level identity",
    qtype="vocabulary",
)
R["lvwe_keys"] = [str(k[0]) for k in keys]
print(f"\nLVWE_DISTINCT_KEYS={len(R['lvwe_keys'])}")
print(f"   first 20: {R['lvwe_keys'][:20]}")

# ------------------- 6. Are LVWE and LVNE distinct series or one series twice?
# EXCEPT is cheaper and safer than a self-join: it returns rows present in one
# table but not the other, so a count of 0 proves the columns are identical.
diff_actual = S.run(
    f"""
    SELECT COUNT(*) FROM (
        SELECT [Key], End_Date, Mean_Actual FROM dbo.[{LVWE}]
        EXCEPT
        SELECT [Key], End_Date, Mean_Actual FROM dbo.[{LVNE}]
    ) t
    """,
    obj=f"{LVWE} EXCEPT {LVNE}",
    purpose="Q11: rows where LVWE Mean_Actual differs from LVNE for the same key and window",
    qtype="aggregate",
)
diff_forecast = S.run(
    f"""
    SELECT COUNT(*) FROM (
        SELECT [Key], End_Date, Mean_Forecast FROM dbo.[{LVWE}]
        EXCEPT
        SELECT [Key], End_Date, Mean_Forecast FROM dbo.[{LVNE}]
    ) t
    """,
    obj=f"{LVWE} EXCEPT {LVNE}",
    purpose="Q11: rows where LVWE Mean_Forecast differs from LVNE for the same key and window",
    qtype="aggregate",
)
da = int(diff_actual[0][0]) if diff_actual else -1
df = int(diff_forecast[0][0]) if diff_forecast else -1
print(f"\nLVWE vs LVNE | rows with differing Mean_Actual={da} | differing Mean_Forecast={df}")
print("   interpretation: 0 differing actuals means one shared observed series; "
      "many differing forecasts means two forecast variants, not two scenarios")
R["lvwe_vs_lvne"] = {"differing_actual_rows": da, "differing_forecast_rows": df}

(OUT / "_p1b_evidence.json").write_text(json.dumps(R, indent=1, default=str), encoding="utf-8")
print("investigation complete")
