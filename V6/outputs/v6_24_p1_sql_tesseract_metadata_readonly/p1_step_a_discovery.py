"""V6.24-P1 Step A | Open discovery of candidate objects for SSD, CPU, IOPS, Memory.

Searches sys.objects by name pattern rather than confirming a pre-baked list, so
that tables absent from repository evidence are still found.
"""

from __future__ import annotations

import json
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent

# Broad name patterns. Deliberately wider than the repository candidate list.
PATTERNS = {
    "SSD": ["%ssd%", "%phoenix%"],
    "CPU": ["%cpu%", "%processor%", "%core%"],
    "IOPS": ["%iops%", "%iop_%", "%io_%"],
    "MEMORY": ["%memory%", "%mem_%", "%ram%"],
    "HDD": ["%hdd%"],
}

# 1. Full object catalogue (one query, then filter locally to avoid many queries)
rows = S.run(
    """
    SELECT s.name AS schema_name, o.name AS object_name, o.type_desc, o.create_date, o.modify_date
    FROM sys.objects o
    JOIN sys.schemas s ON s.schema_id = o.schema_id
    WHERE o.type IN ('U','V')
    ORDER BY s.name, o.name
    """,
    metric="ALL", obj="sys.objects",
    purpose="Enumerate every user table and view in TesseractEarthDW",
)

catalogue = [
    {"schema_name": r[0], "object_name": r[1], "type_desc": r[2],
     "create_date": str(r[3]), "modify_date": str(r[4])}
    for r in rows
]
print(f"TOTAL_OBJECTS={len(catalogue)}")

# 2. Pattern match locally
matches = {}
for metric, pats in PATTERNS.items():
    hits = []
    for obj in catalogue:
        low = obj["object_name"].lower()
        for p in pats:
            frag = p.strip("%").replace("_", "")
            if frag and frag in low.replace("_", ""):
                hits.append(obj)
                break
    matches[metric] = hits
    print(f"{metric}|matched_objects={len(hits)}")
    for h in hits:
        print(f"  {metric}|{h['schema_name']}.{h['object_name']}|{h['type_desc']}")

(OUT / "_stepA_catalogue.json").write_text(
    json.dumps({"catalogue": catalogue, "matches": matches}, indent=1),
    encoding="utf-8",
)
S.save_ledger()
