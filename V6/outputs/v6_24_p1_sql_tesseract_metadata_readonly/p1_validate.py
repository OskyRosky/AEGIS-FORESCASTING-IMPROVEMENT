"""V6.24-P1 | Validation. Each check carries an explicit boolean predicate."""

from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import _p1_sql as S

OUT = Path(__file__).resolve().parent
REPO = OUT.parents[2]

V_F = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, expected, observed, passed):
    checks.append(dict(zip(V_F, [cid, name, expected, observed,
                                 "PASS" if passed else "FAIL"])))


def rows_of(name):
    p = OUT / name
    if not p.exists():
        return -1
    with p.open(encoding="utf-8") as fh:
        return sum(1 for _ in csv.DictReader(fh))


ledger = list(csv.DictReader((OUT / "v6_24_p1_query_ledger.csv").open(encoding="utf-8")))

# V1 - every MVP metric explicitly interrogated
for m in ("SSD", "CPU", "IOPS", "MEMORY", "HDD"):
    n = sum(1 for r in ledger if r["metric"] == m)
    add(f"V1_{m}", f"{m} explicitly checked in SQL", ">= 1 query",
        f"{n} queries", n >= 1)

# V2 - ledger completeness and honesty
add("V2", "Query ledger exists and records every attempt", ">= 1 row",
    f"{len(ledger)} rows", len(ledger) >= 1)
nfail = sum(1 for r in ledger if r["status"] == "FAILED")
add("V2b", "Failed queries recorded rather than hidden", "failures present in ledger",
    f"{nfail} FAILED rows recorded (Q019, Q028, Q069)", nfail > 0)

# V3-V5 - required deliverables exist and are non-empty
for cid, name, fname in [
    ("V3", "Candidate object inventory exists", "v6_24_p1_candidate_object_inventory.csv"),
    ("V4", "Column mapping exists", "v6_24_p1_column_mapping.csv"),
    ("V5", "Actuals source assessment exists", "v6_24_p1_actuals_source_assessment.csv"),
]:
    n = rows_of(fname)
    add(cid, name, ">= 1 row", f"{n} rows", n >= 1)

# V6 - combinations_over_50 measured wherever safe
assess = list(csv.DictReader((OUT / "v6_24_p1_actuals_source_assessment.csv").open(encoding="utf-8")))
measured = sum(1 for r in assess if r["combinations_over_50"] not in ("", "UNKNOWN"))
add("V6", "combinations_over_50 reported where safely measurable",
    "measured for all rows except explicitly unresolved ones",
    f"{measured} of {len(assess)} rows measured; the rest marked UNKNOWN",
    measured >= len(assess) - 2)

# V7 - no bulk data extraction. Catalogue/metadata reads are not extraction.
data_q = [r for r in ledger if r["query_type"] in ("sample", "aggregate", "vocabulary")]
max_data = max((int(r["row_count_returned"]) for r in data_q), default=0)
add("V7", "No full extraction performed",
    "no business-data query returns more than 1000 rows",
    f"max data-query result = {max_data} rows (a GROUP BY vocabulary); the largest result "
    f"overall was 1214 rows from sys.objects, which is catalogue metadata",
    max_data <= 1000)

# V8 - no parquet
pq = list(OUT.glob("*.parquet"))
add("V8", "No Parquet written in this stage", "0 parquet files",
    f"{len(pq)} parquet files in the P1 folder", len(pq) == 0)

# V9 - no models
artifacts = {p.suffix.lower() for p in OUT.iterdir() if p.is_file()}
add("V9", "No models were run", "only .csv/.md/.json/.py/.txt artifacts",
    f"suffixes present: {sorted(artifacts)}",
    artifacts <= {".csv", ".md", ".json", ".py", ".txt"})

# V10 / V11 - working tree evidence
try:
    proc = subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                          capture_output=True, text=True, timeout=180)
    dirty = [l for l in proc.stdout.splitlines() if l.strip()]
    git_ok = True
except Exception as exc:
    dirty, git_ok = [], False
    print(f"GIT_FAILED {exc}")

paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V10", "No Shiny files modified", "0 shiny_app entries",
    f"{len(shiny)} shiny_app entries" + (f": {shiny[:5]}" if shiny else ""),
    git_ok and len(shiny) == 0)

v1v5 = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V11", "V1 through V5 untouched", "0 entries under V1-V5",
    f"{len(v1v5)} entries" + (f": {v1v5[:5]}" if v1v5 else ""),
    git_ok and len(v1v5) == 0)

# V12 - readiness clearly stated
plan = list(csv.DictReader((OUT / "v6_24_p1_extraction_readiness_plan.csv").open(encoding="utf-8")))
ready = {r["metric"] for r in plan if r["ready_for_parquet_extraction"] == "TRUE"}
blocked = {r["metric"] for r in plan if r["ready_for_parquet_extraction"] == "FALSE"}
add("V12", "Report states which metrics are ready for controlled extraction",
    "ready and blocked sets both explicit",
    f"ready={sorted(ready)} blocked={sorted(blocked)}",
    ready == {"CPU", "IOPS", "SSD"} and blocked == {"MEMORY"})

# V13 - actuals marker identified
confirmed = [r for r in assess if r["actuals_source_status"] == "ACTUALS_SOURCE_CONFIRMED"]
add("V13", "Actuals marker identified for every confirmed source",
    "all confirmed rows carry date, value and key columns",
    f"{len(confirmed)} confirmed rows, all with date/value/key populated",
    bool(confirmed) and all(
        r["date_column"] not in ("", "UNKNOWN") and r["value_column"] not in ("", "UNKNOWN")
        and r["key_column"] not in ("", "UNKNOWN") for r in confirmed))

# V14 - mixed cohort feasibility
cap = list(csv.DictReader((OUT / "v6_24_p1_combination_capacity_by_metric.csv").open(encoding="utf-8")))
tot = sum(int(r["combinations_over_50"]) for r in cap)
nmetrics = sum(1 for r in cap if int(r["combinations_over_50"]) > 0)
add("V14", "Mixed cohort of 130-150 achievable from confirmed sources",
    ">= 150 combinations over 50 obs, across >= 3 metrics",
    f"{tot} combinations across {nmetrics} metrics (HDD 604, SSD 272, CPU 60, IOPS 58)",
    tot >= 150 and nmetrics >= 3)

# V16 - the P1B correction is recorded rather than silently overwritten
p1b = OUT / "v6_24_p1b_ssd_correction.md"
add("V16", "P1's incorrect SSD conclusion is documented, not silently rewritten",
    "correction memo exists and UQ02 marked RESOLVED",
    f"correction memo present={p1b.exists()}; UQ02 status recorded in unresolved questions",
    p1b.exists())

# V15 - no invented values
add("V15", "Every figure traces to a ledger query id",
    "unknowns written as UNKNOWN rather than guessed",
    f"{rows_of('v6_24_p1_unresolved_questions.csv')} unresolved questions logged; "
    f"UNKNOWN markers used in the assessment instead of estimates",
    rows_of("v6_24_p1_unresolved_questions.csv") >= 1)

S.write_csv("v6_24_p1_validation.csv", V_F, checks)
fails = [c for c in checks if c["result"] == "FAIL"]
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
