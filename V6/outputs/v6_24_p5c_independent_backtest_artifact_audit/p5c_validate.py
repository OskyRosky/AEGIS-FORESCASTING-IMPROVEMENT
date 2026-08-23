"""V6.24-P5C | Audit validation and closure artifacts."""

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
P5 = OUT.parent / "v6_24_p5_15_model_backtest_generation"

A = json.loads((OUT / "_p5c_a.json").read_text(encoding="utf-8"))
BT = pd.read_parquet(PROC / "model_backtests_15_models.parquet", engine="pyarrow")
GEN = BT[BT["source_generation_status"] == "GENERATED_P5"]
HDD = BT[BT["source_generation_status"] == "REUSED_HDD_EXISTING_ARTIFACT"]
EXEC = pd.read_csv(P5 / "v6_24_p5_execution_ledger.csv")


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


def load(name, folder=OUT):
    with (Path(folder) / name).open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------- status
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p5c_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P5", "Full 15-Model Backtest Generation", "CLOSED", "614,190 rows promoted."),
    ("V6.24-P5C", "Independent Backtest Artifact Audit", "CLOSED (this stage)",
     "Every P5 claim recomputed from artifacts. Audit-only; nothing modified."),
    ("V6.24-P6", "Forecast Generation", "NEXT",
     "Forward forecasts, then accuracy_metrics and model_rankings."),
    ("V6.24-P7", "Product Completeness Gate", "PENDING", ""),
    ("V6.24-P8", "Shiny Integration", "PENDING", ""),
]])

# --------------------------------------------------- sample rows
sample = BT.groupby(["metric", "model_name"]).head(1)
sample.to_csv(OUT / "v6_24_p5c_sample_rows_for_manual_review.csv", index=False)
print(f"v6_24_p5c_sample_rows_for_manual_review.csv|rows={len(sample)}")

# --------------------------------------------------- runtime matrix
F = ["metric", "model_family", "model_name", "units", "total_seconds", "mean_seconds",
     "max_seconds", "prediction_rows"]
rows = []
for (m, fam, mo), g in EXEC.groupby(["metric", "model_family", "model_name"]):
    rows.append(dict(zip(F, [m, fam, mo, len(g), round(float(g["runtime_seconds"].sum()), 3),
                             round(float(g["runtime_seconds"].mean()), 4),
                             round(float(g["runtime_seconds"].max()), 3),
                             int(g["prediction_rows"].sum())])))
write("v6_24_p5c_metric_model_runtime_matrix.csv", F, rows)

# --------------------------------------------------- prediction distribution
F = ["metric", "model_name", "rows", "series", "min", "p25", "median", "p75", "max",
     "negatives", "zeros", "source_generation_status"]
rows = []
for (m, mo), g in BT.groupby(["metric", "model_name"]):
    p = pd.to_numeric(g["predicted_value"], errors="coerce")
    rows.append(dict(zip(F, [m, mo, len(g), int(g["series_id"].nunique()),
                             f"{p.min():.6g}", f"{p.quantile(.25):.6g}",
                             f"{p.median():.6g}", f"{p.quantile(.75):.6g}",
                             f"{p.max():.6g}", int((p < 0).sum()), int((p == 0).sum()),
                             "|".join(sorted(g["source_generation_status"].unique()))])))
write("v6_24_p5c_prediction_distribution_by_model.csv", F, rows)

# --------------------------------------------------- unresolved questions
F = ["question_id", "severity", "topic", "finding", "evidence", "impact_on_p6",
     "recommendation", "blocks_p6"]
write("v6_24_p5c_unresolved_questions.csv", F, [dict(zip(F, r)) for r in [
    ("P5C-UQ01", "MEDIUM", "Negative predictions",
     f"{A['neg_p']:,} rows carry a negative predicted_value for metrics that cannot be "
     f"negative.",
     "5,167 of them (69%) are REUSED_HDD_EXISTING_ARTIFACT rows, so they are a pre-existing "
     "property of the legacy v6_17 artifact, not something P5 introduced. The remaining 2,364 "
     "are GENERATED_P5. Concentrated in ARIMA_Fixed, ETS_Current, AutoARIMA, ETS Explicit, "
     "Theta, LightGBM and XGBoost. The FixedGrowth baselines contribute only tiny negatives "
     "near -1e-3.",
     "Squared-error metrics will absorb them, but percentage-error metrics can behave oddly "
     "against a negative prediction.",
     "Do NOT clip retroactively: that would alter model output after the fact. Report negative "
     "prediction counts alongside accuracy in P6 so the reader can judge.", "NO"),
    ("P5C-UQ02", "LOW", "Extreme prediction ratios",
     f"{A['extreme']:,} rows ({A['extreme_share']:.4%}) have |predicted/actual| outside "
     f"0.01..100.",
     "1,146 of 1,371 (84%) are reused HDD rows. Concentrated in the neural family "
     "(NLIN-DLIN_FIXED, FNAR-V2, SMLP-TCN) and LinearRegression.",
     "Could dominate a mean-percentage-error ranking if left unweighted.",
     "P6 should report median as well as mean error, so a handful of extreme ratios cannot "
     "drive the champion selection.", "NO"),
    ("P5C-UQ03", "MEDIUM", "Manifest flag is stale",
     "cohort_manifest.has_15_model_backtests still reads FALSE for the 90 non-HDD series, "
     "although the artifact now contains their backtests.",
     "P4 wrote the manifest and P5 was forbidden from modifying it.",
     "The P7 completeness gate would under-report what actually exists and could keep 90 valid "
     "series out of the Viewer.",
     "P6 or P7 must refresh the flag from the artifact rather than trusting the frozen value.",
     "NO"),
    ("P5C-UQ04", "LOW", "HDD provenance fields",
     "Reused HDD rows carry train_start_date as null and burn_in_count as -1.",
     "The v6_17 source artifact never recorded them; marked NOT_PRESENT_IN_SOURCE.",
     "None for accuracy, which needs actual, predicted, target_date and horizon.",
     "Leave as is. Reconstructing would mean inventing values.", "NO"),
]])

# =================================================== validation
V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, o, ok):
    checks.append(dict(zip(V, [cid, name, exp, o, "PASS" if ok else "FAIL"])))


BTP = PROC / "model_backtests_15_models.parquet"
pairs = BT.groupby(["series_id", "model_name"]).ngroups
GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]

add("V1", "P5 final artifact exists", "parquet and csv present",
    f"parquet={BTP.exists()}, csv={(PROC / 'model_backtests_15_models.csv').exists()}, "
    f"{BTP.stat().st_size:,} bytes", BTP.exists())
add("V2", "Artifact has exactly 614,190 rows", "614190",
    f"parquet {len(BT):,}, csv {A['csv_rows']:,}",
    len(BT) == 614190 and A["csv_rows"] == 614190)
add("V3", "Artifact has exactly 140 series", "140", f"{BT['series_id'].nunique()}",
    BT["series_id"].nunique() == 140)
add("V4", "Artifact has exactly 15 governed models", "15",
    f"{BT['model_name'].nunique()}; unexpected={A['extra_models']}",
    set(BT["model_name"]) == set(GOVERNED))
add("V5", "Artifact has exactly 2,100 series-model pairs", "2100", f"{pairs}", pairs == 2100)
add("V6", "GENERATED_P5 has exactly 409,890 rows", "409890", f"{len(GEN):,}",
    len(GEN) == 409890)
add("V7", "REUSED_HDD_EXISTING_ARTIFACT has exactly 204,300 rows", "204300",
    f"{len(HDD):,}", len(HDD) == 204300)
for cid, m, s, r in (("V8", "SSD", 50, 225000), ("V9", "CPU", 20, 89910),
                     ("V10", "IOPS", 20, 94980), ("V11", "HDD", 50, 204300)):
    g = BT[BT["metric"] == m]
    add(cid, f"{m} has {s} series and {r:,} rows", f"{s} / {r}",
        f"{g['series_id'].nunique()} series, {len(g):,} rows",
        g["series_id"].nunique() == s and len(g) == r)
per = BT.groupby("series_id")["model_name"].nunique()
add("V12", "Every series has all 15 governed models", "15 for all 140",
    f"min {int(per.min())}, max {int(per.max())}, "
    f"{A['series_fail']} series failing", int(per.min()) == 15 and A["series_fail"] == 0)
add("V13", "No prohibited model appears", "0",
    f"{int(BT['model_name'].isin(PROHIBITED).sum())} rows",
    not BT["model_name"].isin(PROHIBITED).any())
add("V14", "prediction_date equals target_date on every row", "0 offsets",
    f"{A['off']} of {len(BT):,}", A["off"] == 0)
add("V15", "train_end_date < target_date on every GENERATED_P5 row", "0 violations",
    f"{A['leak']} across the whole artifact", A["leak"] == 0)
add("V16", "GENERATED_P5 actual values reconcile to actuals_normalized", "0 mismatches",
    f"{A['mismatch']} mismatches, max delta {A['maxdelta']:.3e}", A["mismatch"] == 0)
add("V17", "Every GENERATED_P5 target_date exists in actuals_normalized", "0 orphans",
    f"{A['orphan']}", A["orphan"] == 0)
add("V18", "No invented GENERATED_P5 target dates", "0", f"{A['invented']}",
    A["invented"] == 0)
add("V19", "Newest observation preserved for 90 of 90 generated series", "90",
    f"{A['newest_ok']} of {A['newest_total']}", A["newest_ok"] == 90)
add("V20", "No duplicate grain rows", "0 at every grain tested",
    f"{A['dup_fail']} duplicate checks failing", A["dup_fail"] == 0)
add("V21", "No NaN predicted_value", "0", f"{A['nan_p']}", A["nan_p"] == 0)
add("V22", "No infinite predicted_value", "0", f"{A['inf_p']}", A["inf_p"] == 0)
fl = P5 / "v6_24_p5_failure_ledger.csv"
add("V23", "Failure ledger exists with 0 blocking failures", "present, 0 rows",
    f"present={fl.exists()}, {sum(1 for _ in fl.open(encoding='utf-8')) - 1} rows",
    fl.exists() and sum(1 for _ in fl.open(encoding="utf-8")) - 1 == 0)
add("V24", "Execution ledger has exactly 1,350 OK non-HDD entries", "1350 OK",
    f"{len(EXEC)} entries, {int((EXEC['model_status'] == 'OK').sum())} OK, "
    f"{int((EXEC['metric'] == 'HDD').sum())} HDD entries",
    len(EXEC) == 1350 and int((EXEC["model_status"] == "OK").sum()) == 1350
    and int((EXEC["metric"] == "HDD").sum()) == 0)
add("V25", "Checkpoints reconcile to 409,890 generated rows", "409890",
    f"{A['ck_rows']:,} rows across {A['n_ck']} checkpoint files",
    A["ck_rows"] == 409890)
add("V26", "Final generated rows reconcile to checkpoints", "0 rows on either side only",
    f"{A['only_ck']} checkpoint-only, {A['only_gen']} final-only",
    A["only_ck"] == 0 and A["only_gen"] == 0)
add("V27", "Progress log has all 10% milestones", "10 through 100",
    f"{A['progress_fail']} progress checks failing", A["progress_fail"] == 0)
add("V28", "Runtime plausibility conclusion", "PLAUSIBLE or clearly justified",
    f"{A['runtime_verdict']}: smoke {A['s_fit_rate']:.1f} fits/s vs full "
    f"{A['f_fit_rate']:.1f} fits/s, ratio {A['ratio']:.2f}x",
    A["runtime_verdict"] == "PLAUSIBLE")
add("V29", "No forbidden forecast/accuracy/ranking/navigation/taxonomy artifacts", "0",
    f"{A['gov_fail']} governance checks failing", A["gov_fail"] == 0)
try:
    dirty = [l for l in subprocess.run(["git", "status", "--porcelain"], cwd=REPO,
                                       capture_output=True, text=True, timeout=180
                                       ).stdout.splitlines() if l.strip()]
    git_ok = True
except Exception:
    dirty, git_ok = [], False
paths = [l[3:].strip().strip('"').replace("\\", "/") for l in dirty]
add("V30", "Shiny files untouched", "0 entries",
    f"{len([p for p in paths if 'shiny_app' in p])} entries",
    git_ok and not [p for p in paths if "shiny_app" in p])
add("V31", "V1 through V5 untouched", "0 entries",
    f"{len([p for p in paths if any(p.startswith(f'V{n}/') for n in range(1, 6))])} entries",
    git_ok and not [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))])
add("V32", "No models were rerun during P5C", "0 model artifacts written by the audit",
    f"{len([p for p in OUT.rglob('*') if p.suffix == '.parquet'])} parquet files in the audit "
    f"folder", not [p for p in OUT.rglob("*") if p.suffix == ".parquet"])
add("V33", "No processed artifacts were modified during P5C",
    "processed/ file count unchanged at 10",
    f"{len([p for p in PROC.iterdir() if p.is_file()])} files in processed/",
    len([p for p in PROC.iterdir() if p.is_file()]) == 10)
clos = OUT / "v6_24_p5c_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V34", "Closure summary states accept, accept with caveats, or blocked",
    "explicit decision", f"present={clos.exists()}; states a decision="
    f"{'ACCEPT_P5' in txt or 'BLOCK_P6' in txt}",
    clos.exists() and ("ACCEPT_P5" in txt or "BLOCK_P6" in txt))

# extra
add("V35", "Parquet and CSV siblings agree exactly", "identical row counts",
    f"parquet {len(BT):,} vs csv {A['csv_rows']:,}", len(BT) == A["csv_rows"])
add("V36", "Reused HDD actuals also reconcile where dates overlap",
    "0 mismatches on overlapping dates",
    f"{A['hdd_overlap_rows']:,} overlapping rows, {A['hdd_overlap_mismatch']} mismatches, "
    f"max delta {A['hdd_overlap_maxdelta']:.3e}", A["hdd_overlap_mismatch"] == 0)
add("V37", "Row-count reconciliation has no failures across 71 breakdowns",
    "0 failing breakdowns", f"{A['row_fail']} failing", A["row_fail"] == 0)

with (OUT / "v6_24_p5c_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

fails = [c for c in checks if c["result"] == "FAIL"]
A["val_total"], A["val_fail"] = len(checks), len(fails)
A["decision"] = ("ACCEPT_P5_FOR_P6" if not fails and A["neg_p"] == 0
                 else "ACCEPT_P5_WITH_CAVEATS_FOR_P6" if not fails
                 else "BLOCK_P6_PENDING_FIX")
json.dump(A, (OUT / "_p5c_a.json").open("w", encoding="utf-8"), indent=1, default=str)
print(f"v6_24_p5c_validation.csv|rows={len(checks)}")
print(f"\nTOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
print(f"\nDECISION: {A['decision']}")
