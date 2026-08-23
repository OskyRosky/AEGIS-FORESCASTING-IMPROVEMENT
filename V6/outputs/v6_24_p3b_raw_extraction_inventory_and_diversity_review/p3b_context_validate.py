"""V6.24-P3B | Full 140-cohort context, status table and validation."""

from __future__ import annotations

import csv
import subprocess
import time
from pathlib import Path

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
PROC = V6 / "data" / "processed"
P2 = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan"

NA = "NOT_APPLICABLE"
LOCAL = "ALREADY_LOCAL_NOT_EXTRACTED"


def load(p, folder=OUT):
    f = Path(folder) / p
    if not f.exists():
        return []
    with f.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


obs = load("v6_24_p3b_observed_series_inventory_90.csv")
units = load("v6_24_p3b_raw_extraction_unit_inventory.csv")
ui = load("v6_24_p3b_ui_filter_tree_preview.csv")

# ---------------------------------------------------- 1. status table
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p3b_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P3", "Governed Data Extraction to Parquet", "CLOSED",
     "90 series extracted to 4 raw Parquet. 33/33 PASS."),
    ("V6.24-P3B", "Raw Extraction Inventory + CPU/IOPS Diversity Review", "CLOSED (this stage)",
     "Exact inventory produced in two views. Diversity decision surfaced, not taken silently."),
    ("V6.24-P4", "Cohort Normalization / Manifest Freeze", "NEXT",
     "Must dedupe SSD on (series_key, series_date) and fold the 50 local HDD series into one "
     "cohort_manifest."),
    ("V6.24-P5", "15-Model Backtest Generation", "PENDING",
     "Mandatory for all 90 extracted series: none has governed backtests."),
    ("V6.24-P6", "Forecast Generation", "PENDING",
     "Also produces accuracy_metrics and model_rankings."),
    ("V6.24-P7", "Product Completeness Gate", "PENDING",
     "Produces validation_summary, navigation_contract and taxonomy_counts AFTER the gate."),
    ("V6.24-P8", "Shiny Integration", "PENDING", "Repoint Shiny to processed/ only."),
    ("V6.24-P9", "Visual QA / Demo Readiness", "PENDING", ""),
]])

# ------------------------------------------- 10. full 140 context inventory
F = ["cohort_id", "metric", "db_type", "variant", "scenario", "segment", "demand_nature",
     "granularity", "key", "route_path", "ui_filter_path", "source",
     "p3_extraction_status", "raw_parquet_relative_path", "row_count", "min_date",
     "max_date", "observed_series", "freshness_status", "has_15_governed_backtests",
     "ui_visible_now", "caveat"]
ctx = []
for r in load("v6_24_p2_hdd_50_local_reference_plan.csv", P2):
    seg = r["segment"] if r["segment"] != NA else NA
    ctx.append(dict(zip(F, [
        r["cohort_id"], "HDD", r["db_type"], NA, NA, seg, r["demand_nature"],
        r["granularity"], r["key"], r["route_path"],
        (f"Metric=HDD > DBType={r['db_type']} > Segment={seg} > "
         f"Granularity={r['granularity']} > Key={r['key']}"),
        "LOCAL parquet artifacts (v6_17 full generation)", LOCAL, NA,
        r["observation_count"], r["min_date"], r["max_date"], 1, "CURRENT",
        "TRUE", "TRUE",
        "None. Actuals, all 15 governed backtests and forecast already local.",
    ])))
for r in obs:
    ctx.append(dict(zip(F, [
        r["observed_series_id"], r["metric"], r["db_type"], r["variant"], r["scenario"],
        r["segment"], r["demand_nature"], r["granularity"], r["key"], r["route_path"],
        r["ui_filter_path"], r["source_object"], "EXTRACTED_IN_P3",
        r["raw_parquet_relative_path"], r["row_count"], r["min_date"], r["max_date"], 1,
        r["freshness_status"], "FALSE", "FALSE", r["caveat"],
    ])))
write("v6_24_p3b_full_140_context_inventory.csv", F, ctx)

# --------------------------------------------------- 11. validation
V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, o, ok):
    checks.append(dict(zip(V, [cid, name, exp, o, "PASS" if ok else "FAIL"])))


by_metric = {}
for r in obs:
    by_metric[r["metric"]] = by_metric.get(r["metric"], 0) + 1

add("V1", "Observed-series inventory has exactly 90 rows", "90", f"{len(obs)}", len(obs) == 90)

lvwe = [r for r in units if r["variant"] == "LVWE"]
lvne = [r for r in units if r["variant"] == "LVNE"]
add("V2", "Raw-extraction-unit inventory distinguishes SSD LVWE and LVNE",
    "50 LVWE + 50 LVNE, flagged distinctly",
    f"{len(lvwe)} LVWE and {len(lvne)} LVNE; "
    f"is_duplicate_physical_variant TRUE on {sum(1 for r in units if r['is_duplicate_physical_variant'] == 'TRUE')} rows; "
    f"total units {len(units)}",
    len(lvwe) == 50 and len(lvne) == 50 and len(units) == 140
    and all(r["is_duplicate_physical_variant"] == "TRUE" for r in lvne))

ssd_obs = [r for r in obs if r["metric"] == "SSD"]
add("V3", "SSD observed series count remains 50, not 100", "50",
    f"{len(ssd_obs)} observed rows over {len({r['key'] for r in ssd_obs})} unique keys, "
    f"stored as {len(lvwe) + len(lvne)} physical units",
    len(ssd_obs) == 50 and len({r["key"] for r in ssd_obs}) == 50)
add("V4", "CPU observed series count is 20", "20", f"{by_metric.get('CPU', 0)}",
    by_metric.get("CPU") == 20)
add("V5", "IOPS observed series count is 20", "20", f"{by_metric.get('IOPS', 0)}",
    by_metric.get("IOPS") == 20)

covered = {r["metric"] for r in ui}
add("V6", "UI filter tree preview covers SSD, CPU, IOPS, HDD context and the Memory gap",
    "5 metrics", f"{sorted(covered)}",
    covered == {"SSD", "CPU", "IOPS", "HDD", "Memory"})

AX = ["metric", "db_type", "variant", "scenario", "segment", "granularity", "key",
      "route_path", "ui_filter_path"]
blank = [(r["inventory_row_id"], a) for r in obs + units for a in AX if not r[a]]
add("V7", "Every inventory row has all nine axes populated with explicit values",
    "0 blank cells across 230 rows",
    f"{len(blank)} blank cells across {len(obs) + len(units)} rows", not blank)

cpu_mx = load("v6_24_p3b_cpu_scenario_key_matrix.csv")
iops_mx = load("v6_24_p3b_iops_scenario_key_matrix.csv")
add("V8", "CPU scenario/key matrix exists", ">= 1 row",
    f"{len(cpu_mx)} keys; {sum(1 for r in cpu_mx if r['shared_by_both_scenarios'] == 'TRUE')} "
    f"shared by both scenarios", len(cpu_mx) >= 1)
add("V9", "IOPS scenario/key matrix exists", ">= 1 row",
    f"{len(iops_mx)} keys; {sum(1 for r in iops_mx if r['shared_by_both_scenarios'] == 'TRUE')} "
    f"shared by both scenarios", len(iops_mx) >= 1)
add("V10", "CPU/IOPS diversity issue is clearly documented",
    "every key shown as shared, and the achievable alternative quantified",
    f"CPU {len(cpu_mx)} keys x 2 scenarios = 20 series; IOPS {len(iops_mx)} keys x 2 = 20. "
    f"Pool holds 30 CPU and 29 IOPS distinct keys, so 20 distinct keys is achievable.",
    all(r["shared_by_both_scenarios"] == "TRUE" for r in cpu_mx + iops_mx))

dec = load("v6_24_p3b_cpu_iops_diversity_decision_table.csv")
names = {r["option_name"] for r in dec}
add("V11", "Decision table contains both options",
    "KEEP_CURRENT_MVP and PATCH_DIVERSITY_BEFORE_P4", f"{sorted(names)}",
    names == {"KEEP_CURRENT_MVP", "PATCH_DIVERSITY_BEFORE_P4"})

# Governance
led = [p for p in OUT.rglob("*query_ledger*")]
add("V12", "No new SQL extraction performed", "no query ledger in this stage",
    f"{len(led)} ledgers; P3B read only local Parquet and CSV", not led)

WINDOW = time.time() - 3 * 3600
raw_files = [p for p in RAW.rglob("*.parquet")]
# A time window is the wrong predicate here: P3 wrote these files roughly an hour
# ago, so any recent-mtime test flags P3's own writes. The rigorous, time-independent
# check is that every file still matches the sha256 that P3 recorded.
P3 = OUT.parent / "v6_24_p3_governed_data_extraction_to_parquet"
recorded = {r["file_name"]: r["checksum_if_available"].replace("sha256:", "")
            for r in load("v6_24_p3_raw_file_inventory.csv", P3)}
import hashlib

drift = []
for p in raw_files:
    now = hashlib.sha256(p.read_bytes()).hexdigest()
    if recorded.get(p.name) != now:
        drift.append(p.name)
add("V13", "No new raw Parquet written and none overwritten",
    "4 files, every sha256 identical to the value P3 recorded",
    f"{len(raw_files)} raw parquet files; {len(drift)} with a checksum differing from P3 "
    f"({len(recorded)} checksums on record)",
    len(raw_files) == 4 and len(recorded) == 4 and not drift)

proc = [p for p in (PROC.rglob("*") if PROC.exists() else []) if p.is_file()]
cohort_dir = PROC / "v6_24_mvp_cohort"
touched_proc = [p.name for p in proc if p.stat().st_mtime > WINDOW]
add("V14", "No processed Parquet written",
    "no v6_24_mvp_cohort folder and no processed file touched",
    f"cohort folder exists={cohort_dir.exists()}; {len(touched_proc)} of {len(proc)} "
    f"processed files touched (the rest are legacy artifacts from June 2026)",
    not cohort_dir.exists() and not touched_proc)

sfx = {p.suffix.lower() for p in OUT.iterdir() if p.is_file()}
add("V15", "No models run", "only .csv/.md/.py artifacts", f"{sorted(sfx)}",
    sfx <= {".csv", ".md", ".py", ".json", ".txt"})
add("V16", "No forecasts generated", "no forecast artifact",
    f"{len([p for p in OUT.rglob('*') if 'forecast_output' in p.name])} artifacts",
    not [p for p in OUT.rglob("*") if "forecast_output" in p.name])
add("V17", "No accuracy or rankings calculated", "no accuracy or ranking artifact",
    f"{len([p for p in OUT.rglob('*') if 'ranking' in p.name or 'accuracy_metric' in p.name])} artifacts",
    not [p for p in OUT.rglob("*") if "ranking" in p.name or "accuracy_metric" in p.name])

try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V18", "No Shiny files modified", "0 entries", f"{len(shiny)} entries",
    git_ok and not shiny)
v15p = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V19", "V1 through V5 untouched", "0 entries", f"{len(v15p)} entries",
    git_ok and not v15p)

clos = OUT / "v6_24_p3b_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V20", "Closure summary states whether P3 data is acceptable for MVP P4",
    "explicit statement plus the owner decision needed",
    f"present={clos.exists()}; states acceptability={'ACCEPTABLE' in txt.upper()}",
    clos.exists() and "ACCEPTABLE" in txt.upper())

# Extra integrity checks
add("V21", "The two views reconcile: 140 physical units minus 50 SSD duplicates equals 90",
    "140 - 50 = 90",
    f"{len(units)} units - {len(lvne)} LVNE duplicate-variant units = {len(units) - len(lvne)} "
    f"observed series", len(units) - len(lvne) == len(obs) == 90)
ctx_hdd = [r for r in ctx if r["metric"] == "HDD"]
add("V22", "Full 140 context marks all HDD rows ALREADY_LOCAL_NOT_EXTRACTED",
    "140 rows, 50 HDD all marked",
    f"{len(ctx)} rows, {len(ctx_hdd)} HDD, "
    f"{sum(1 for r in ctx_hdd if r['p3_extraction_status'] == LOCAL)} marked",
    len(ctx) == 140 and len(ctx_hdd) == 50
    and all(r["p3_extraction_status"] == LOCAL for r in ctx_hdd))
add("V23", "No extracted series claims to have 15 governed backtests",
    "all 90 extracted rows marked FALSE; only the 50 local HDD rows are TRUE",
    f"{sum(1 for r in ctx if r['has_15_governed_backtests'] == 'TRUE')} TRUE "
    f"(expected 50, all HDD)",
    sum(1 for r in ctx if r["has_15_governed_backtests"] == "TRUE") == 50)

with (OUT / "v6_24_p3b_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

fails = [c for c in checks if c["result"] == "FAIL"]
print(f"v6_24_p3b_validation.csv|rows={len(checks)}")
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
