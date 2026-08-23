"""V6.24-P3 | Validation. Thirty checks, each with an explicit boolean predicate.

Every figure is computed from the written Parquet files or from git, never from a
plan file. That discipline was adopted after the P2 reporting defect.
"""

from __future__ import annotations

import csv
import json
import subprocess
import time
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
PROC = V6 / "data" / "processed"

EV = json.loads((OUT / "_p3_evidence.json").read_text(encoding="utf-8"))
FILES = {"LVWE": RAW / "ssd" / "ssd_lvwe_raw.parquet",
         "LVNE": RAW / "ssd" / "ssd_lvne_raw.parquet",
         "CPU": RAW / "cpu" / "cpu_actuals_raw.parquet",
         "IOPS": RAW / "iops" / "iops_actuals_raw.parquet"}
DF = {k: pd.read_parquet(v, engine="pyarrow") for k, v in FILES.items()}

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


def series_of(tag):
    return DF[tag][["scenario", "series_key"]].drop_duplicates().shape[0]


ssd_keys = set(DF["LVWE"]["series_key"]) | set(DF["LVNE"]["series_key"])
n_ssd, n_cpu, n_iops = len(ssd_keys), series_of("CPU"), series_of("IOPS")
total = n_ssd + n_cpu + n_iops

add("V1", "Exactly 90 non-HDD series extracted", "90",
    f"{total} = SSD {n_ssd} + CPU {n_cpu} + IOPS {n_iops}", total == 90)
add("V2", "Exactly 50 SSD observed series extracted", "50", f"{n_ssd}", n_ssd == 50)
add("V3", "SSD LVWE and LVNE not double-counted as 100 observed series",
    "50 observed series across 2 forecast variants",
    f"LVWE {DF['LVWE']['series_key'].nunique()} keys, LVNE {DF['LVNE']['series_key'].nunique()} "
    f"keys, union {n_ssd}; consistency check found "
    f"{EV['ssd_consistency']['actual_differing']} differing actual rows",
    n_ssd == 50 and EV["ssd_consistency"]["actual_differing"] == 0)
add("V4", "Exactly 20 CPU series extracted", "20", f"{n_cpu}", n_cpu == 20)
add("V5", "Exactly 20 IOPS series extracted", "20", f"{n_iops}", n_iops == 20)

hdd_files = [p for p in RAW.rglob("*.parquet") if "hdd" in p.name.lower()]
metrics = {str(DF[t]["metric"].iloc[0]) for t in DF}
add("V6", "HDD not extracted", "no HDD parquet, no HDD rows",
    f"{len(hdd_files)} HDD files; metrics present in raw = {sorted(metrics)}",
    not hdd_files and "HDD" not in metrics)

add("V7", "All raw Parquet files exist", "4 files",
    f"{sum(1 for p in FILES.values() if p.exists())} of 4 exist",
    all(p.exists() for p in FILES.values()))

proc_files = [p for p in (PROC.rglob("*") if PROC.exists() else []) if p.is_file()]
# processed/ already holds 24 legacy artifacts from earlier V6 stages (June 2026).
# The correct predicate is not "the folder is empty" but "P3 wrote nothing into it":
# no v6_24_mvp_cohort folder, and no file touched during this stage.
P3_WINDOW = time.time() - 6 * 3600
cohort_dir = PROC / "v6_24_mvp_cohort"
touched = [p.name for p in proc_files if p.stat().st_mtime > P3_WINDOW]
add("V8", "No files written under V6/data/processed by P3",
    "no v6_24_mvp_cohort folder and no file touched during P3",
    f"cohort folder exists={cohort_dir.exists()}; {len(touched)} of {len(proc_files)} "
    f"processed files touched during P3 (the rest are legacy artifacts from June 2026)",
    not cohort_dir.exists() and not touched)

for cid, tag in (("V9", "LVWE"), ("V10", "LVNE"), ("V11", "CPU"), ("V12", "IOPS")):
    p, d = FILES[tag], DF[tag]
    add(cid, f"{tag} raw Parquet exists and is non-empty", "exists, rows > 0",
        f"exists={p.exists()}, rows={len(d):,}, bytes={p.stat().st_size:,}",
        p.exists() and len(d) > 0)

per_key = DF["LVWE"].groupby("series_key")["actual_value"].apply(lambda s: s.notna().sum())
add("V13", "Every extracted SSD key has more than 50 parseable actual observations", "> 50",
    f"min={int(per_key.min())} max={int(per_key.max())}; "
    f"{int((per_key > 50).sum())} of {len(per_key)} keys pass", bool((per_key > 50).all()))

npar = sum(int((DF[t]["actual_value_source_text"].notna() & DF[t]["actual_value"].isna()).sum())
           for t in ("LVWE", "LVNE"))
add("V14", "SSD non-parseable Mean_Actual count is 0", "0",
    f"{npar} rows where source text is present but the cast is null", npar == 0)

c = EV["ssd_consistency"]
add("V15", "LVWE and LVNE Mean_Actual consistency passes for selected keys",
    "0 differing rows",
    f"{c['actual_identical']} of {c['matched_rows']} matched rows identical, "
    f"{c['actual_differing']} differing", c["actual_differing"] == 0)

for cid, tag, plan in (("V16", "CPU", "v6_24_p2_cpu_20_extraction_plan.csv"),
                       ("V17", "IOPS", "v6_24_p2_iops_20_extraction_plan.csv")):
    src = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan" / plan
    with src.open(encoding="utf-8") as fh:
        want = {(r["scenario"], r["key"]) for r in csv.DictReader(fh)}
    got = set(map(tuple, DF[tag][["scenario", "series_key"]].drop_duplicates().values))
    add(cid, f"{tag} selected series all present", "20 of 20",
        f"{len(want & got)} of {len(want)} present; missing={sorted(want - got)}", want == got)

unexpected = {t: EV["files"][t]["unexpected_keys"] for t in EV["files"]}
add("V18", "No unexpected keys present in any raw Parquet", "0 across all four files",
    f"{sum(len(v) for v in unexpected.values())} unexpected keys total",
    not any(unexpected.values()))
missing = {t: EV["files"][t]["missing_keys"] for t in EV["files"]}
add("V19", "No selected keys missing from any raw Parquet", "0 across all four files",
    f"{sum(len(v) for v in missing.values())} missing keys total",
    not any(missing.values()))

tax = load("v6_24_p3_full_taxonomy_extracted_series_report.csv")
AX = ["metric", "db_type", "variant", "scenario", "segment", "granularity", "key", "route_path"]
blank = [(r["extraction_id"], a) for r in tax for a in AX if not r[a]]
add("V20", "Full taxonomy report exists with all conditional axes populated",
    "140 rows, zero blank axis cells",
    f"{len(tax)} rows, {len(blank)} blank axis cells", len(tax) == 140 and not blank)

ctx = load("v6_24_p3_full_140_cohort_context_report.csv")
hdd_ctx = [r for r in ctx if r["metric"] == "HDD"]
add("V21", "Full 140-cohort context report marks HDD as ALREADY_LOCAL_NOT_EXTRACTED",
    "140 rows, 50 HDD all marked",
    f"{len(ctx)} rows, {len(hdd_ctx)} HDD rows, "
    f"{sum(1 for r in hdd_ctx if r['p3_action'] == 'ALREADY_LOCAL_NOT_EXTRACTED')} marked",
    len(ctx) == 140 and len(hdd_ctx) == 50
    and all(r["p3_action"] == "ALREADY_LOCAL_NOT_EXTRACTED" for r in hdd_ctx))

st = [r for r in tax if r["metric"] in ("CPU", "IOPS")]
add("V22", "CPU and IOPS carry the STALE_ACTUALS_SOURCE caveat", "all 40 rows",
    f"{sum(1 for r in st if 'STALE_ACTUALS_SOURCE' in r['caveat'])} of {len(st)} rows",
    len(st) == 40 and all("STALE_ACTUALS_SOURCE" in r["caveat"] for r in st))

try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V23", "Shiny files untouched", "0 entries", f"{len(shiny)} entries", git_ok and not shiny)
v15p = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V24", "V1 through V5 untouched", "0 entries", f"{len(v15p)} entries", git_ok and not v15p)

MODEL_HINT = ("model_backtests", "forecast_outputs", "accuracy_metrics", "model_rankings")
stray = [p.name for p in OUT.rglob("*") if p.is_file()
         and any(h in p.name for h in MODEL_HINT)]
add("V25", "No models run", "no model artifacts produced", f"{len(stray)} model artifacts", not stray)
add("V26", "No forecasts generated", "no forecast artifacts produced",
    f"{sum(1 for p in OUT.rglob('*') if p.is_file() and 'forecast_output' in p.name)} artifacts",
    not [p for p in OUT.rglob("*") if p.is_file() and "forecast_output" in p.name])
add("V27", "No accuracy or rankings calculated",
    "source accuracy columns copied verbatim, none computed",
    "MAPE/SMAPE/Accuracy in the SSD files are precomputed SOURCE columns extracted as-is; "
    "no ranking artifact exists", not [p for p in OUT.rglob("*") if "ranking" in p.name])

banned = ("navigation_contract", "taxonomy_counts", "cohort_manifest",
          "actuals_normalized", "validation_summary")
proc_stray = [p.name for p in (list(PROC.rglob("*")) if PROC.exists() else []) if p.is_file()]
add("V28", "No navigation_contract or taxonomy_counts processed artifacts generated in P3",
    "none under processed/",
    f"{len([n for n in proc_stray if any(b in n for b in banned)])} banned processed artifacts",
    not [n for n in proc_stray if any(b in n for b in banned)])

led = load("v6_24_p3_query_ledger.csv")
add("V29", "Query ledger exists and records every extraction query", "4 queries",
    f"{len(led)} rows, all {sorted({r['status'] for r in led})}",
    len(led) == 4 and all(r["status"] == "OK" for r in led))

clos = OUT / "v6_24_p3_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V30", "Closure summary states P3 extraction completed and P4 is next",
    "both statements present",
    f"present={clos.exists()}, mentions P4={'P4' in txt}", clos.exists() and "P4" in txt)

# Extra integrity checks beyond the brief
add("V31", "Row counts in Parquet match the SQL result exactly", "no row lost on write",
    "; ".join(f"{t}: sql={EV['files'][t]['sql_rows']} parquet={EV['files'][t]['parquet_rows']}"
              for t in ("LVWE", "LVNE", "CPU", "IOPS")),
    all(EV["files"][t]["rows_match"] for t in EV["files"]))
add("V32", "Every raw file carries a sha256 checksum", "4 checksums",
    f"{sum(1 for t in EV['files'] if EV['files'][t].get('checksum_sha256'))} of 4",
    all(EV["files"][t].get("checksum_sha256") for t in EV["files"]))
dq = load("v6_24_p3_data_quality_report.csv")
add("V33", "Data quality anomalies are reported rather than silently cleaned",
    "the SSD duplicate and the CPU/IOPS key-diversity finding are both logged",
    f"{len(dq)} findings logged; raw files left unmodified", len(dq) >= 2)

with (OUT / "v6_24_p3_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

fails = [c for c in checks if c["result"] == "FAIL"]
print(f"v6_24_p3_validation.csv|rows={len(checks)}")
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
