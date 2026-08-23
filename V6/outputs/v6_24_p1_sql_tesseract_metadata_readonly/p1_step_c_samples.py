"""V6.24-P1 Step C | Small TOP samples to establish column semantics.

Read-only. TOP 5 rows per view plus the distinct DemandType vocabulary, which is
what determines whether these views serve actuals or forecast.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

VIEWS = {
    "CPU": ["vw_SubstrateBE_Demand_Cpu_Region", "vw_SubstrateBE_Demand_CpuPhoenix_Region"],
    "HDD": ["vw_SubstrateBE_Demand_HddEdbEnterprise_Region", "vw_SubstrateBE_Demand_HddBasilisk_Region"],
    "IOPS": ["vw_SubstrateBE_Demand_Iops_Region"],
    "MEMORY": ["vw_SubstrateBE_Demand_Memory_Region"],
    "SSD": ["vw_SubstrateBE_Demand_Ssd_Region", "vw_SubstrateBE_Demand_SsdPhoenix_Region"],
}

result = {}
for metric, views in VIEWS.items():
    for v in views:
        sample = S.run(
            f"SELECT TOP 5 * FROM dbo.[{v}]",
            metric=metric, obj=v, purpose="TOP 5 sample to infer column semantics",
            qtype="sample",
        )
        print(f"\n--- {metric} | {v} ---")
        for row in sample:
            print("   ", " | ".join(str(x) for x in row))

        vocab = S.run(
            f"SELECT DISTINCT DemandType FROM dbo.[{v}]",
            metric=metric, obj=v, purpose="Distinct DemandType vocabulary",
            qtype="vocabulary",
        )
        dt = [r[0] for r in vocab]
        print(f"    DemandType values: {dt}")
        result[v] = {"metric": metric, "demand_types": dt,
                     "sample": [[str(x) for x in r] for r in sample]}

(OUT / "_stepC_samples.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
S.save_ledger()
