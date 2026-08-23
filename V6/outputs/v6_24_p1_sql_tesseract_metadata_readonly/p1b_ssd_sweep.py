"""V6.24-P1B | Exhaustive SSD actuals sweep.

P1 probed only the highest-signal SSD objects and wrongly concluded SSD has no
actuals. Owner evidence (AX4 Security dashboard) shows SSD Phoenix Low Volume
with Efficiency actuals through August 2026, keyed by forest (NAMPRD04..NAMPRD11).

This sweeps every SSD-named object: full column signature, then a targeted probe
of any column whose name suggests an actual/forecast discriminator.

Read-only. Metadata and small aggregates only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
S.append_ledger_from(OUT / "v6_24_p1_query_ledger.csv")

cat = json.loads((OUT / "_stepA_catalogue.json").read_text(encoding="utf-8"))["catalogue"]
ssd = [o for o in cat if re.search(r"ssd|phoenix|phx", o["object_name"], re.I)]
print(f"SSD_OBJECTS={len(ssd)}")

names = [o["object_name"] for o in ssd]
placeholders = ",".join("?" for _ in names)
rows = S.run(
    f"SELECT TABLE_NAME, COLUMN_NAME, DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS "
    f"WHERE TABLE_NAME IN ({placeholders}) ORDER BY TABLE_NAME, ORDINAL_POSITION",
    metric="SSD", obj="INFORMATION_SCHEMA.COLUMNS",
    purpose="Full column signature for every SSD-named object",
    params=tuple(names),
)
by_obj = {}
for r in rows:
    by_obj.setdefault(r[0], []).append((r[1], r[2]))

# Objects whose columns look like they carry observed history.
ACTUAL_COL = re.compile(r"actual|observed|history|ValueType|ModelVersion|^type$|DemandType", re.I)
interesting = []
for obj, cols in sorted(by_obj.items()):
    colnames = [c[0] for c in cols]
    hits = [c for c in colnames if ACTUAL_COL.search(c)]
    tag = "CANDIDATE" if hits else "-"
    print(f"{tag:<10} {obj}")
    print(f"           cols: {', '.join(colnames)}")
    if hits:
        interesting.append((obj, colnames, hits))

print(f"\nCANDIDATES_WITH_ACTUAL_SHAPED_COLUMNS={len(interesting)}")
(OUT / "_p1b_ssd_columns.json").write_text(
    json.dumps({"columns": by_obj, "candidates": [i[0] for i in interesting]},
               indent=1), encoding="utf-8")
S.save_ledger()
