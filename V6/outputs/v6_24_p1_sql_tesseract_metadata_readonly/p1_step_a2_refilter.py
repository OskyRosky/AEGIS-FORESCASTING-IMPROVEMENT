"""V6.24-P1 Step A2 | Precise local re-filter of the downloaded object catalogue.

No SQL is issued here: the full catalogue was already retrieved in Step A.
Fixes the over-broad IOPS pattern and surfaces the Demand_* naming family.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
data = json.loads((OUT / "_stepA_catalogue.json").read_text(encoding="utf-8"))
cat = data["catalogue"]
print(f"TOTAL_OBJECTS={len(cat)}")

PATTERNS = {
    "SSD": r"ssd|phoenix",
    "CPU": r"cpu|vcore|processor",
    "IOPS": r"iops|rops",
    "MEMORY": r"memory|\bmem\b|ram_",
    "HDD": r"hdd",
}

matches = {}
for metric, pat in PATTERNS.items():
    rx = re.compile(pat, re.I)
    hits = [o for o in cat if rx.search(o["object_name"])]
    matches[metric] = hits
    print(f"\n===== {metric} | matched={len(hits)} =====")

# The HDD family proves the naming convention for actuals/demand sources.
print("\n### DEMAND_* FAMILY (likely actuals convention) ###")
for o in cat:
    if re.search(r"demand", o["object_name"], re.I):
        print(f"  {o['schema_name']}.{o['object_name']}|{o['type_desc']}")

print("\n### ACTUAL/HISTORY NAMED OBJECTS ###")
for o in cat:
    if re.search(r"actual|histor", o["object_name"], re.I):
        print(f"  {o['schema_name']}.{o['object_name']}|{o['type_desc']}")

(OUT / "_stepA2_matches.json").write_text(
    json.dumps(matches, indent=1), encoding="utf-8"
)
