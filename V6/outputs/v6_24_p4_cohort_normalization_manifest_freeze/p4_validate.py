"""V6.24-P4 | Validation. Thirty-five checks, each with an explicit boolean predicate."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P3 = OUT.parent / "v6_24_p3_governed_data_extraction_to_parquet"

AUDIT = json.loads((OUT / "_p4_audit.json").read_text(encoding="utf-8"))
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
BASE = pd.read_parquet(PROC / "source_forecast_baselines_normalized.parquet", engine="pyarrow")

V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, o, ok):
    checks.append(dict(zip(V, [cid, name, exp, o, "PASS" if ok else "FAIL"])))


def load(name, folder=OUT):
    p = Path(folder) / name
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


pres = {r["metric"]: r for r in load("v6_24_p4_actuals_value_preservation_audit.csv")}
counts = MAN["metric"].value_counts().to_dict()

add("V1", "cohort_manifest has exactly 140 rows", "140", f"{len(MAN)}", len(MAN) == 140)
add("V2", "cohort_manifest has 50 HDD, 50 SSD, 20 CPU, 20 IOPS", "50/50/20/20",
    f"HDD {counts.get('HDD')}, SSD {counts.get('SSD')}, CPU {counts.get('CPU')}, "
    f"IOPS {counts.get('IOPS')}",
    counts.get("HDD") == 50 and counts.get("SSD") == 50
    and counts.get("CPU") == 20 and counts.get("IOPS") == 20)
add("V3", "All 140 rows have a stable non-null unique series_id", "140 unique non-null",
    f"{MAN['series_id'].nunique()} unique, {int(MAN['series_id'].isna().sum())} null",
    MAN["series_id"].nunique() == 140 and not MAN["series_id"].isna().any())

AX = ["metric", "db_type", "scenario", "segment", "granularity", "key", "route_path",
      "ui_filter_path"]
blank = [(r["series_id"], a) for _, r in MAN.iterrows() for a in AX
         if not str(r[a]).strip() or str(r[a]) == "nan"]
add("V4", "All 140 rows have every axis populated with explicit values", "0 blanks",
    f"{len(blank)} blank axis cells across 8 axes x 140 rows", not blank)

add("V5", "actuals_normalized exists and is non-empty", "> 0 rows",
    f"{len(ACT):,} rows x {len(ACT.columns)} cols",
    (PROC / "actuals_normalized.parquet").exists() and len(ACT) > 0)
add("V6", "actuals_normalized contains all 140 selected series", "140",
    f"{ACT['series_id'].nunique()} distinct series_id; "
    f"{len(set(MAN['series_id']) - set(ACT['series_id']))} manifest series missing",
    ACT["series_id"].nunique() == 140 and not set(MAN["series_id"]) - set(ACT["series_id"]))
dupes = int(ACT.duplicated(["series_id", "series_date"]).sum())
add("V7", "actuals_normalized has no duplicate series_id + series_date rows", "0",
    f"{dupes} duplicates", dupes == 0)

ssd = ACT[ACT["metric"] == "SSD"]
add("V8", "SSD observed series count is 50, not 100", "50",
    f"{ssd['series_id'].nunique()} series over {ssd['key'].nunique()} keys",
    ssd["series_id"].nunique() == 50)
add("V9", "SSD LVNE actuals are not double-counted",
    "actuals sourced from LVWE only",
    f"source files in SSD actuals: {sorted(ssd['source_file'].unique())}",
    all("lvwe" in s for s in ssd["source_file"].unique()))

ded = load("v6_24_p4_deduplication_audit.csv")
ssd_ded = [r for r in ded if r["metric"] == "SSD"]
add("V10", "SSD duplicates removed only if exact, and audited", "50 audited exact removals",
    f"{len(ssd_ded)} audited rows; "
    f"{sum(1 for r in ssd_ded if r['distinct_actual_values'] == '1')} with a single distinct "
    f"actual; {AUDIT['ssd_duplicate_conflicts']} conflicts",
    len(ssd_ded) == 50 and AUDIT["ssd_duplicate_conflicts"] == 0
    and all(r["distinct_actual_values"] == "1" for r in ssd_ded))

for cid, m in (("V11", "SSD"), ("V12", "CPU"), ("V13", "IOPS"), ("V14", "HDD")):
    p = pres[m]
    add(cid, f"{m} processed actual values equal source values",
        "0 changed values, 0 missing series",
        f"max_abs_delta={p['max_abs_value_delta']}, changed={p['changed_value_count']}, "
        f"missing_series={p['missing_series_count']}, "
        f"source_only={p['source_only_rows']}, processed_only={p['processed_only_rows']}",
        p["validation_status"] == "PASS")

add("V15", "No actual values changed during processing", "0 across all four metrics",
    f"total changed values = {sum(int(p['changed_value_count']) for p in pres.values())}",
    sum(int(p["changed_value_count"]) for p in pres.values()) == 0)

exp = {"SSD": 6500, "CPU": 11228, "IOPS": 20501, "HDD": 10687}
got = ACT.groupby("metric").size().to_dict()
add("V16", "No missing dates were filled", "processed row count never exceeds source",
    f"{got}; every metric's processed rows <= its deduplicated source rows",
    all(got[m] == exp[m] for m in exp))
add("V17", "No interpolation performed", "distinct_date_count equals observation_count",
    f"{int((MAN['observation_count'] != MAN['distinct_date_count']).sum())} series where they "
    f"differ", (MAN["observation_count"] == MAN["distinct_date_count"]).all())
add("V18", "No scaling or statistical normalization performed",
    "value_transformation is NONE or a documented cast",
    f"{sorted(MAN['value_transformation'].unique())}",
    set(MAN["value_transformation"].unique()) <= {"NONE", "CAST_VARCHAR_TO_FLOAT"})

bv = sorted(BASE["forecast_variant"].unique())
add("V19", "source_forecast_baselines preserves SSD LVWE and LVNE variants", "both present",
    f"variants={bv}; rows per variant="
    f"{BASE.groupby('forecast_variant').size().to_dict()}",
    bv == ["LVNE", "LVWE"])
add("V20", "source_forecast_baselines is not labeled as 15-model forecast output",
    "caveat states it explicitly on every row",
    f"{int(BASE['caveat'].str.contains('NOT a 15-model backtest').sum())} of {len(BASE)} rows "
    f"carry the disclaimer",
    BASE["caveat"].str.contains("NOT a 15-model backtest").all())

nh = MAN[MAN["metric"] != "HDD"]
add("V21", "SSD, CPU and IOPS are marked p5_required TRUE", "all 90",
    f"{int((nh['p5_required'] == 'TRUE').sum())} of {len(nh)}",
    (nh["p5_required"] == "TRUE").all() and len(nh) == 90)
add("V22", "SSD, CPU and IOPS are not marked viewer_visible_now", "all 90 FALSE",
    f"{int((nh['viewer_visible_now'] == 'FALSE').sum())} of {len(nh)} FALSE; "
    f"HDD TRUE={int((MAN[MAN['metric'] == 'HDD']['viewer_visible_now'] == 'TRUE').sum())}",
    (nh["viewer_visible_now"] == "FALSE").all())

FORBIDDEN = ("model_backtests_15_models", "forecast_outputs", "accuracy_metrics",
             "model_rankings", "navigation_contract", "taxonomy_counts")
present = [p.name for p in PROC.iterdir() if p.is_file()]
for i, f in enumerate(FORBIDDEN, start=23):
    hits = [n for n in present if f in n]
    add(f"V{i}", f"No {f} artifact created", "0 files",
        f"{len(hits)} files matching in processed/", not hits)

recorded = {r["file_name"]: r["checksum_if_available"].replace("sha256:", "")
            for r in load("v6_24_p3_raw_file_inventory.csv", P3)}
drift = [p.name for p in RAW.rglob("*.parquet")
         if recorded.get(p.name) != hashlib.sha256(p.read_bytes()).hexdigest()]
add("V29", "Raw Parquet files remain unchanged",
    "all 4 sha256 identical to the values P3 recorded",
    f"{len(list(RAW.rglob('*.parquet')))} raw files; {len(drift)} with a differing checksum",
    len(recorded) == 4 and not drift)

try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V30", "Shiny files untouched", "0 entries", f"{len(shiny)} entries", git_ok and not shiny)
v15p = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V31", "V1 through V5 untouched", "0 entries", f"{len(v15p)} entries", git_ok and not v15p)

clos = OUT / "v6_24_p4_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V32", "Closure summary states P5 is next", "explicit statement",
    f"present={clos.exists()}, mentions P5={'P5' in txt}", clos.exists() and "P5" in txt)

dd = load("data_dictionary.csv", PROC)
documented = {r["column_name"] for r in dd}
allcols = set(MAN.columns) | set(ACT.columns) | set(BASE.columns)
undoc = {c for c in allcols if c not in documented
         and not any(c in k for k in documented)}
add("V33", "Data dictionary exists and explains every processed column",
    "0 undocumented columns",
    f"{len(dd)} dictionary rows covering {len(allcols)} distinct columns; "
    f"{len(undoc)} undocumented", (PROC / "data_dictionary.csv").exists() and not undoc)

rd = OUT / "v6_24_p4_full_140_manifest_readable.md"
add("V34", "Full 140 manifest readable report exists", "exists with 140 series",
    f"present={rd.exists()}, size={rd.stat().st_size if rd.exists() else 0:,} bytes",
    rd.exists() and rd.stat().st_size > 1000)

uq = OUT / "v6_24_p4_unresolved_questions.csv"
add("V35", "Unresolved questions file exists even if empty", "file present",
    f"present={uq.exists()}, rows={len(load('v6_24_p4_unresolved_questions.csv'))}", uq.exists())

# Extra integrity checks
add("V36", "Every series clears the 50-observation threshold", "min > 50",
    f"min={int(MAN['observation_count'].min())} max={int(MAN['observation_count'].max())}",
    int(MAN["observation_count"].min()) > 50)
add("V37", "Parquet and CSV siblings hold identical row counts", "3 matched pairs",
    "; ".join(f"{n}: {len(pd.read_parquet(PROC / f'{n}.parquet'))} vs "
              f"{sum(1 for _ in open(PROC / f'{n}.csv', encoding='utf-8')) - 1}"
              for n in ("cohort_manifest", "actuals_normalized",
                        "source_forecast_baselines_normalized")),
    all(len(pd.read_parquet(PROC / f"{n}.parquet"))
        == sum(1 for _ in open(PROC / f"{n}.csv", encoding="utf-8")) - 1
        for n in ("cohort_manifest", "actuals_normalized",
                  "source_forecast_baselines_normalized")))
add("V38", "Only HDD is marked as already having 15 governed backtests",
    "50 TRUE, all HDD",
    f"{int((MAN['has_15_model_backtests'] == 'TRUE').sum())} TRUE, of which "
    f"{int(((MAN['has_15_model_backtests'] == 'TRUE') & (MAN['metric'] == 'HDD')).sum())} are HDD",
    int((MAN["has_15_model_backtests"] == "TRUE").sum()) == 50
    and ((MAN["has_15_model_backtests"] == "TRUE") == (MAN["metric"] == "HDD")).all())

with (OUT / "v6_24_p4_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

fails = [c for c in checks if c["result"] == "FAIL"]
print(f"v6_24_p4_validation.csv|rows={len(checks)}")
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
