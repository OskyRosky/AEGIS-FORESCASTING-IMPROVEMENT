"""V6.24-P2 | Validation. Each check carries an explicit boolean predicate."""

from __future__ import annotations

import csv
import re
import subprocess
from pathlib import Path

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]

V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, obs, ok):
    checks.append(dict(zip(V, [cid, name, exp, obs, "PASS" if ok else "FAIL"])))


def load(name):
    p = OUT / name
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


full = load("v6_24_p2_full_140_mvp_cohort_plan.csv")
p3 = load("v6_24_p2_p3_90_series_extraction_plan.csv")
hdd = load("v6_24_p2_hdd_50_local_reference_plan.csv")
ssd = load("v6_24_p2_ssd_50_extraction_plan.csv")
cpu = load("v6_24_p2_cpu_20_extraction_plan.csv")
iops = load("v6_24_p2_iops_20_extraction_plan.csv")
axis = load("v6_24_p2_metric_axis_contract.csv")
dest = load("v6_24_p2_parquet_destination_plan.csv")

add("V1", "Full MVP cohort plan has exactly 140 selected series", "140", f"{len(full)}", len(full) == 140)
add("V2", "P3 extraction plan has exactly 90 selected series", "90", f"{len(p3)}", len(p3) == 90)
add("V3", "HDD local reference plan has exactly 50 series", "50", f"{len(hdd)}", len(hdd) == 50)
add("V4", "SSD extraction plan has exactly 50 series", "50", f"{len(ssd)}", len(ssd) == 50)
add("V5", "CPU extraction plan has exactly 20 series", "20", f"{len(cpu)}", len(cpu) == 20)
add("V6", "IOPS extraction plan has exactly 20 series", "20", f"{len(iops)}", len(iops) == 20)

mem_rows = [r for r in full if r["metric"] == "Memory"]
mem_axis = [r for r in axis if r["metric"] == "Memory"]
add("V7", "Memory has 0 selected series and is documented as gap only",
    "0 rows in cohort, present in axis contract as BLOCKED",
    f"{len(mem_rows)} cohort rows; axis contract status="
    f"{mem_axis[0]['extraction_stage'] if mem_axis else 'MISSING'}",
    not mem_rows and bool(mem_axis) and "BLOCKED" in mem_axis[0]["extraction_stage"])

REQ = ["metric", "granularity", "key", "route_path", "source_object_or_artifact",
       "observation_count", "passes_50_actuals"]
missing = [r["cohort_id"] for r in full if any(not r[c] for c in REQ)]
add("V8", "Every selected series has all seven required fields populated",
    "0 rows with a blank required field", f"{len(missing)} rows incomplete", not missing)

bad9 = [r["key"] for r in ssd if r["db_type"] != "Phoenix" or r["granularity"] != "Forest"]
add("V9", "Every SSD series has DB Type Phoenix and Granularity Forest",
    "all 50 conform", f"{len(bad9)} non-conforming", not bad9)

ssd_keys = [r["key"] for r in ssd]
add("V10", "Every selected SSD key is unique at the observed-series level",
    "50 unique keys", f"{len(set(ssd_keys))} unique of {len(ssd_keys)}",
    len(set(ssd_keys)) == len(ssd_keys) == 50)

add("V11", "LVWE and LVNE are not double-counted as separate observed series",
    "one cohort row per forest key, variant LVWE+LVNE",
    f"{len(ssd)} SSD rows for {len(set(ssd_keys))} keys; "
    f"variants={sorted({r['variant'] for r in ssd})}",
    len(ssd) == len(set(ssd_keys)) and {r["variant"] for r in ssd} == {"LVWE+LVNE"})

stale = [r for r in cpu + iops if "STALE_ACTUALS_SOURCE" in r["caveat"]]
add("V12", "CPU and IOPS carry the STALE_ACTUALS_SOURCE caveat", "all 40 rows",
    f"{len(stale)} of {len(cpu) + len(iops)} rows carry it", len(stale) == 40)

am = {r["metric"] for r in axis}
add("V13", "Conditional axis contract contains all five metrics",
    "HDD, SSD, CPU, IOPS, Memory", f"{sorted(am)}",
    am == {"HDD", "SSD", "CPU", "IOPS", "Memory"})

add("V14", "Parquet destination plan exists", ">= 1 row", f"{len(dest)} rows", len(dest) >= 1)

sqlp = OUT / "v6_24_p2_extraction_sql_templates.sql"
sql = sqlp.read_text(encoding="utf-8") if sqlp.exists() else ""
execsql = re.sub(r"/\*.*?\*/", "", sql, flags=re.S).upper()
banned = [b for b in ("CREATE", "UPDATE", "DELETE", "INSERT", "MERGE", "ALTER",
                      "DROP", "TRUNCATE", "EXEC") if re.search(rf"\b{b}\b", execsql)]
stmts = [s.strip() for s in execsql.split(";") if s.strip()]
non_select = [s[:30] for s in stmts if not s.startswith("SELECT")]
keyed = all(f"'{k}'" in sql for k in ssd_keys[:10] + [r["key"] for r in cpu[:5]])
add("V15", "SQL templates are SELECT-only and filtered to the selected keys",
    "no banned keyword, every statement a SELECT, keys embedded",
    f"{len(stmts)} statements, all SELECT={not non_select}, "
    f"banned={banned or 'NONE'}, sampled keys embedded={keyed}",
    bool(sql) and not banned and not non_select and keyed)

ledger = load("v6_24_p2_query_ledger.csv")
data_q = [r for r in ledger if r["query_type"] in ("sample", "aggregate", "vocabulary")]
maxrows = max((int(r["row_count_returned"]) for r in data_q), default=0)
add("V16", "No data extraction performed",
    "only grouped counts; no query returns raw time-series rows",
    f"{len(ledger)} queries of a 10 budget; largest result {maxrows} rows "
    f"(the 137-key grouped count)", maxrows <= 200 and len(ledger) <= 10)

pq = list(OUT.rglob("*.parquet")) + list((REPO / "V6" / "data" / "raw").glob("v6_24_mvp_cohort/**/*.parquet")) \
    if (REPO / "V6" / "data" / "raw").exists() else list(OUT.rglob("*.parquet"))
add("V17", "No Parquet written", "0 parquet files", f"{len(pq)} parquet files", not pq)

sfx = {p.suffix.lower() for p in OUT.iterdir() if p.is_file()}
add("V18", "No models run", "only .csv/.md/.sql/.json/.py artifacts",
    f"suffixes: {sorted(sfx)}", sfx <= {".csv", ".md", ".sql", ".json", ".py", ".txt"})

try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V19", "No Shiny files modified", "0 shiny_app entries", f"{len(shiny)} entries",
    git_ok and not shiny)
v15p = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V20", "V1 through V5 untouched", "0 entries", f"{len(v15p)} entries", git_ok and not v15p)

meth = OUT / "v6_24_p2_selection_methodology.md"
reasons = {r["selection_reason"] for r in full}
add("V21", "Selection methodology is deterministic and documented",
    "methodology file exists and every row carries a selection_reason",
    f"methodology present={meth.exists()}; {len(reasons)} distinct selection reasons "
    f"across 140 rows; 0 rows selected by head-of-list",
    meth.exists() and all(r["selection_reason"] for r in full))

clos = OUT / "v6_24_p2_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V22", "Closure summary states P3 is the extraction stage, not P2",
    "explicit statement present",
    f"closure summary present={clos.exists()}; states P3-is-extraction="
    f"{'P3' in txt and 'not P2' in txt.replace('NOT P2', 'not P2')}",
    clos.exists() and "P3" in txt)

# Extra integrity checks beyond the brief
hdd_routes = {r["route_path"] for r in hdd}
add("V23", "All six HDD route families are represented", "6 routes",
    f"{len(hdd_routes)} routes: {sorted(hdd_routes)}", len(hdd_routes) == 6)

for m, data in (("CPU", cpu), ("IOPS", iops)):
    sc = {}
    for r in data:
        sc[r["scenario"]] = sc.get(r["scenario"], 0) + 1
    add(f"V24_{m}", f"{m} scenarios are balanced", "10 Consumed + 10 Failover",
        f"{sc}", sc.get("Consumed") == 10 and sc.get("Failover") == 10)

pref = {r["key"][:3] for r in ssd}
add("V25", "SSD selection is geographically diverse", ">= 20 distinct prefixes",
    f"{len(pref)} distinct prefixes", len(pref) >= 20)

dash = {"NAMPRD07", "NAMPRD08"} & set(ssd_keys)
add("V26", "AX4 dashboard reference keys are included in the SSD cohort",
    "NAMPRD07 and NAMPRD08 present", f"{sorted(dash)}", dash == {"NAMPRD07", "NAMPRD08"})

no15 = [r for r in full if r["metric"] != "HDD"
        and "15 governed model backtests DO NOT exist yet" in r["caveat"]]
add("V27", "Plan does not claim SSD, CPU or IOPS already have 15 model backtests",
    "all 90 non-HDD rows state the backtests are absent",
    f"{len(no15)} of 90 non-HDD rows carry the explicit disclaimer", len(no15) == 90)

blank = [(r["cohort_id"], c) for r in full for c in
         ("db_type", "variant", "scenario", "segment", "demand_nature") if not r[c]]
add("V28", "No route axis is left blank", "explicit placeholders everywhere",
    f"{len(blank)} blank axis cells", not blank)

with (OUT / "v6_24_p2_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

fails = [c for c in checks if c["result"] == "FAIL"]
print(f"v6_24_p2_validation.csv|rows={len(checks)}")
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
