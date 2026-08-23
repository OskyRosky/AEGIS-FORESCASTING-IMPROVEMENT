"""V6.24-P1B step 2 | Probe the SSD objects that carry actual-vs-forecast semantics.

Targets chosen from the owner's AX4 dashboard evidence: scenario
"SSD Phoenix Low Vol. w/ Efficiency", keys NAMPRD04..NAMPRD11, actuals to Aug 2026.

Read-only.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")
rep = {}

# --- A. Row-level staging table: same shape as forecast_staging_agent_HDD ---
r = S.run(
    "SELECT type, COUNT(*), MIN(datadate), MAX(datadate), COUNT(DISTINCT [key]) "
    "FROM dbo.[forecast_staging_agent_SSD] GROUP BY type ORDER BY 2 DESC",
    metric="SSD", obj="forecast_staging_agent_SSD",
    purpose="type vocabulary: hunting a row-level actual marker", qtype="vocabulary",
)
print("=== forecast_staging_agent_SSD | type vocabulary ===")
for x in r[:30]:
    print(f"   {str(x[0]).strip():<30} rows={x[1]:>9,} {x[2]}..{x[3]} keys={x[4]}")
rep["staging_agent_ssd_type"] = [[str(x[0]), int(x[1]), str(x[2]), str(x[3]), int(x[4])] for x in r]

r = S.run(
    "SELECT TOP 20 [key], COUNT(*) FROM dbo.[forecast_staging_agent_SSD] "
    "GROUP BY [key] ORDER BY 2 DESC",
    metric="SSD", obj="forecast_staging_agent_SSD",
    purpose="Key vocabulary: check for NAMPRD forest keys", qtype="vocabulary",
)
print(f"   keys sample: {[str(x[0]) for x in r]}")
rep["staging_agent_ssd_keys"] = [[str(x[0]), int(x[1])] for x in r]

# --- B. Accuracy metrics tables named after the dashboard scenarios ---
for tbl in ["forecast_substrateBE_ssd_phx_lvwe_metrics",
            "forecast_substrateBE_ssd_phx_lvne_metrics"]:
    r = S.run(
        f"SELECT COUNT(*), COUNT(DISTINCT [Key]), MIN(Start_Date), MAX(End_Date), "
        f"MIN(Forecast_Version), MAX(Forecast_Version) FROM dbo.[{tbl}]",
        metric="SSD", obj=tbl, purpose="Coverage of the accuracy metrics table",
        qtype="aggregate",
    )
    if r:
        x = r[0]
        print(f"\n=== {tbl} ===")
        print(f"   rows={x[0]:,} keys={x[1]} {x[2]}..{x[3]} fv={x[4]}..{x[5]}")
        rep[f"{tbl}_coverage"] = [str(v) for v in x]
    k = S.run(
        f"SELECT TOP 20 [Key], COUNT(*), SUM(Count) FROM dbo.[{tbl}] GROUP BY [Key] ORDER BY 2 DESC",
        metric="SSD", obj=tbl, purpose="Key vocabulary and observation counts", qtype="vocabulary",
    )
    print(f"   keys: {[(str(x[0]), int(x[1]), int(x[2]) if x[2] else 0) for x in k][:12]}")
    rep[f"{tbl}_keys"] = [[str(x[0]), int(x[1]), int(x[2]) if x[2] else 0] for x in k]

# --- C. Accuracy views that expose Actual/Demand directly ---
for tbl, dcol, acol, kcol in [
    ("vw_SubstrateBE_SSD_Region_Env_Forecast_Accuracy", "DateTime", "Demand", "Env_Region"),
    ("vw_SubstrateBE_SSD_Region_Env_Forecast_Accuracy_for_HotBuffer", "SnapshotDate", "Actual", "Region"),
]:
    r = S.run(
        f"SELECT COUNT(*), MIN([{dcol}]), MAX([{dcol}]), COUNT(DISTINCT [{kcol}]) "
        f"FROM dbo.[{tbl}] WHERE [{acol}] IS NOT NULL",
        metric="SSD", obj=tbl, purpose=f"Coverage of non-null {acol}", qtype="aggregate",
    )
    if r:
        x = r[0]
        print(f"\n=== {tbl} ===")
        print(f"   rows_with_{acol}={x[0]:,} {x[1]}..{x[2]} keys={x[3]}")
        rep[f"{tbl}_coverage"] = [str(v) for v in x]

(OUT / "_p1b_probe.json").write_text(json.dumps(rep, indent=1, default=str), encoding="utf-8")
S.save_ledger()
