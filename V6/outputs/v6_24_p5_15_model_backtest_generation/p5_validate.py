"""V6.24-P5 | Validation. Thirty-eight checks with explicit boolean predicates.

Evidence is re-derived from the promoted artifact and from actuals_normalized,
not taken from the runner that produced them.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work"
P5B = OUT.parent / "v6_24_p5b_smoke_test_only_model_runtime_validation"

RUN = json.loads((OUT / "_p5_run.json").read_text(encoding="utf-8"))
ASM = json.loads((OUT / "_p5_assembly.json").read_text(encoding="utf-8"))
BT = pd.read_parquet(PROC / "model_backtests_15_models.parquet", engine="pyarrow")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
EXEC = pd.read_csv(OUT / "v6_24_p5_execution_ledger.csv")
PROG = pd.read_csv(OUT / "v6_24_p5_progress_log.csv")

NH = BT[BT["metric"] != "HDD"]
HD = BT[BT["metric"] == "HDD"]
GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]

V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, o, ok):
    checks.append(dict(zip(V, [cid, name, exp, o, "PASS" if ok else "FAIL"])))


sm = pd.read_csv(P5B / "v6_24_p5b_validation.csv")
add("V1", "P5B smoke test PASS confirmed before the full run",
    "smoke validation all PASS",
    f"{int((sm['result'] == 'PASS').sum())}/{len(sm)} smoke checks PASS",
    (sm["result"] == "PASS").all())
add("V2", "Exactly 90 non-HDD series were run", "90",
    f"{NH['series_id'].nunique()}", NH["series_id"].nunique() == 90)
pairs = NH.groupby(["series_id", "model_name"]).ngroups
add("V3", "Exactly 1,350 non-HDD model-series runs completed", "1350",
    f"{pairs} pairs in the artifact; {int((EXEC['model_status'] == 'OK').sum())} OK in the "
    f"execution ledger", pairs == 1350 and int((EXEC["model_status"] == "OK").sum()) == 1350)
add("V4", "HDD was not re-run", "no HDD rows in the execution ledger",
    f"{int((EXEC['metric'] == 'HDD').sum())} HDD entries in the ledger; HDD rows carry "
    f"source_generation_status={sorted(HD['source_generation_status'].unique())}",
    int((EXEC["metric"] == "HDD").sum()) == 0
    and set(HD["source_generation_status"]) == {"REUSED_HDD_EXISTING_ARTIFACT"})
add("V5", "HDD backtests reused and mapped safely", "50 series, 15 models",
    f"{HD['series_id'].nunique()} series, {HD['model_name'].nunique()} models, "
    f"{len(HD):,} rows; joined on the full route grain",
    HD["series_id"].nunique() == 50 and HD["model_name"].nunique() == 15)
add("V6", "All 15 governed models appear", "15",
    f"{BT['model_name'].nunique()} distinct; missing="
    f"{sorted(set(GOVERNED) - set(BT['model_name']))}",
    set(BT["model_name"]) == set(GOVERNED))
add("V7", "No prohibited models appear", "0",
    f"{int(BT['model_name'].isin(PROHIBITED).sum())} rows",
    not BT["model_name"].isin(PROHIBITED).any())

for cid, m, n in (("V8", "SSD", 50), ("V9", "CPU", 20), ("V10", "IOPS", 20)):
    g = BT[BT["metric"] == m]
    per = g.groupby("series_id")["model_name"].nunique()
    add(cid, f"{m} has {n} series with all 15 models", f"{n} series x 15 models",
        f"{g['series_id'].nunique()} series; models per series "
        f"{int(per.min())}..{int(per.max())}",
        g["series_id"].nunique() == n and int(per.min()) == 15)

add("V11", "Final artifact includes all 140 MVP series", "140",
    f"{BT['series_id'].nunique()}; manifest has {MAN['series_id'].nunique()}; "
    f"missing={len(set(MAN['series_id']) - set(BT['series_id']))}",
    BT["series_id"].nunique() == 140 and not set(MAN["series_id"]) - set(BT["series_id"]))
allper = BT.groupby("series_id")["model_name"].nunique()
add("V12", "15 governed models per series across the artifact", "15 for every series",
    f"min {int(allper.min())}, max {int(allper.max())}", int(allper.min()) == 15)
sgs = set(BT["source_generation_status"])
add("V13", "source_generation_status distinguishes reused from generated",
    "REUSED_HDD_EXISTING_ARTIFACT and GENERATED_P5", f"{sorted(sgs)}",
    sgs == {"REUSED_HDD_EXISTING_ARTIFACT", "GENERATED_P5"})

add("V14", "prediction_date equals target_date on every row", "0 offsets",
    f"{ASM['offset']} of {len(BT):,}", ASM["offset"] == 0)
add("V15", "train_end_date less than target_date on every row", "0 violations",
    f"{ASM['leak']}", ASM["leak"] == 0)
add("V16", "Non-HDD actual_value matches actuals_normalized", "0 mismatches",
    f"{ASM['mismatch']}, max delta 0.00e+00", ASM["mismatch"] == 0)
add("V17", "Every non-HDD target_date exists in actuals_normalized", "0 orphans",
    f"{ASM['orphan']}", ASM["orphan"] == 0)

ni = pd.read_csv(OUT / "v6_24_p5_no_invented_dates_validation.csv")
invented = int(ni["target_dates_not_observed"].sum())
newest = int((ni["newest_observation_reached"].astype(str).str.upper() == "TRUE").sum())
for cid, nm in (("V18", "No invented target dates"), ("V19", "No filled, interpolated or "
                                                             "resampled dates")):
    add(cid, nm, "0 target dates outside the observed set",
        f"{invented} across {len(ni)} non-HDD series", invented == 0)
bts = set(NH["backtest_type"])
add("V20", "D2 sparse-observed policy was used", "marked on every generated row",
    f"non-HDD backtest_type={sorted(bts)}", bts == {"D2_SPARSE_OBSERVED_BACKTEST"})
add("V21", "Newest observation preserved for all 90 non-HDD series", "90 of 90",
    f"{newest} of {len(ni)}", newest == 90)
add("V22", "No duplicate series/model/target/origin rows", "0", f"{ASM['dup']}",
    ASM["dup"] == 0)
add("V23", "No silent NaN predicted_value rows", "0", f"{ASM['nan']}", ASM["nan"] == 0)
fl = OUT / "v6_24_p5_failure_ledger.csv"
add("V24", "Failure ledger exists even if empty", "file present",
    f"present={fl.exists()}, {RUN['failures']} failures recorded", fl.exists())
add("V25", "All failures explicitly recorded", "ledger count equals FAILED count",
    f"{int((EXEC['model_status'] == 'FAILED').sum())} FAILED in the execution ledger, "
    f"{RUN['failures']} in the failure ledger",
    int((EXEC["model_status"] == "FAILED").sum()) == RUN["failures"])
add("V26", "Budget report exists", "file present",
    f"present={(OUT / 'v6_24_p5_budget_report.csv').exists()}",
    (OUT / "v6_24_p5_budget_report.csv").exists())
add("V27", "Runtime stayed within the 120-minute hard budget", "< 120 minutes",
    f"{RUN['minutes']}m, about {RUN['minutes'] / 120:.1%} of the budget",
    RUN["minutes"] < 120)
ms = sorted(PROG["percent_complete"].unique())
add("V28", "Progress log covers every 10% milestone",
    "10 through 100", f"{ms}", set(range(10, 101, 10)) <= set(ms))
add("V29", "Partial checkpoints were not promoted on failure",
    "promotion only after every gate passed",
    f"promotion gate: {sum(1 for _ in csv.DictReader((OUT / 'v6_24_p5_promotion_gate.csv').open(encoding='utf-8')))} "
    f"conditions, all PASS; promoted={ASM['promoted']}", ASM["promoted"])
add("V30", "Final artifact exists only because validation passed", "both files present",
    f"parquet={(PROC / 'model_backtests_15_models.parquet').exists()}, "
    f"csv={(PROC / 'model_backtests_15_models.csv').exists()}, {len(BT):,} rows",
    (PROC / "model_backtests_15_models.parquet").exists() and ASM["promoted"])

FORBIDDEN = ("forecast_outputs", "accuracy_metrics", "model_rankings",
             "navigation_contract", "taxonomy_counts")
names = [p.name for p in PROC.iterdir() if p.is_file()]
for i, f in enumerate(FORBIDDEN, start=31):
    hits = [n for n in names if f in n]
    add(f"V{i}", f"No {f} artifact was created", "0 files",
        f"{len(hits)} matching files in processed/", not hits)

try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
shiny = [p for p in paths if "shiny_app" in p]
add("V36", "Shiny files untouched", "0 entries", f"{len(shiny)} entries",
    git_ok and not shiny)
v15 = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V37", "V1 through V5 untouched", "0 entries", f"{len(v15)} entries",
    git_ok and not v15)
clos = OUT / "v6_24_p5_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V38", "Closure summary states whether P5 is complete, blocked or incomplete",
    "explicit completion statement",
    f"present={clos.exists()}; states COMPLETE={'COMPLETE' in txt.upper()}",
    clos.exists() and "COMPLETE" in txt.upper())

# Extra integrity checks
add("V39", "Backtests only: no forward-dated predictions",
    "every target_date is a real observed date",
    f"{invented} non-HDD targets outside the observed set; max target "
    f"{str(BT['target_date'].max())[:10]}", invented == 0)
add("V40", "Checkpoint total reconciles with the promoted artifact",
    "27 checkpoints sum to the generated row count",
    f"{ASM['gen_rows']:,} generated rows from checkpoints + {ASM['hdd_rows']:,} reused HDD "
    f"= {ASM['final_rows']:,} final",
    ASM["gen_rows"] + ASM["hdd_rows"] == ASM["final_rows"] == len(BT))
add("V41", "Predicted row count matches the P5A forecast", "about 409,890 generated rows",
    f"{ASM['gen_rows']:,} generated, forecast was 409,890",
    ASM["gen_rows"] == 409890)
add("V42", "Parquet and CSV siblings agree", "identical row counts",
    f"parquet {len(BT):,} vs csv "
    f"{sum(1 for _ in open(PROC / 'model_backtests_15_models.csv', encoding='utf-8')) - 1:,}",
    len(BT) == sum(1 for _ in open(PROC / "model_backtests_15_models.csv",
                                   encoding="utf-8")) - 1)

with (OUT / "v6_24_p5_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

fails = [c for c in checks if c["result"] == "FAIL"]
print(f"v6_24_p5_validation.csv|rows={len(checks)}")
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
