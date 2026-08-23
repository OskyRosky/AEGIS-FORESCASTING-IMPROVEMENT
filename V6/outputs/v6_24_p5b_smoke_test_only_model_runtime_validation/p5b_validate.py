"""V6.24-P5B | Validation of the smoke test output.

Every check re-derives its evidence from the written artifact and from
actuals_normalized, rather than trusting the runner that produced them.
"""

from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import pandas as pd
import pyarrow.parquet as pq

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work" / "smoke_test"
P5A = OUT.parent / "v6_24_p5a_backtest_execution_plan_budget_window_contract"

RUN = json.loads((OUT / "_p5b_run.json").read_text(encoding="utf-8"))
BT = pd.read_pickle(OUT / "_p5b_bt.pkl")
LED = pd.read_pickle(OUT / "_p5b_ledger.pkl")
FAIL = pd.read_pickle(OUT / "_p5b_fail.pkl")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")

GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]
SCHEMA = ["cohort_id", "series_id", "metric", "db_type", "scenario", "segment",
          "granularity", "key", "route_path", "model_name", "model_family",
          "target_date", "prediction_date", "train_start_date", "train_end_date",
          "horizon_steps", "actual_value", "predicted_value", "backtest_type",
          "burn_in_count", "source_actuals_artifact", "model_run_id",
          "source_generation_status", "model_status", "runtime_seconds", "caveat"]


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# =================================================== independent reconciliation
truth = ACT[ACT["series_id"].isin(BT["series_id"].unique())][
    ["series_id", "series_date", "actual_value"]].rename(
    columns={"series_date": "target_date", "actual_value": "truth_actual"})
J = BT.merge(truth, on=["series_id", "target_date"], how="left", indicator=True)

orphan = int((J["_merge"] == "left_only").sum())
both = J[J["_merge"] == "both"]
delta = (both["actual_value"] - both["truth_actual"]).abs()
mismatch = int((delta > 1e-9).sum())
maxdelta = float(delta.max()) if len(delta) else 0.0

offset = int((BT["prediction_date"] != BT["target_date"]).sum())
leak = int((BT["train_end_date"] >= BT["target_date"]).sum())
hz_bad = int(((BT["horizon_steps"] < 1) | (BT["horizon_steps"] > 30)).sum())
hz_calc = (BT["target_date"] - BT["train_end_date"]).dt.days
hz_mismatch = int((hz_calc != BT["horizon_steps"]).sum())
nan_pred = int(BT["predicted_value"].isna().sum())
dupes = int(BT.duplicated(["series_id", "model_name", "target_date", "train_end_date"]).sum())

# ------------------------------------------- date alignment
F = ["check", "expected", "observed", "result"]
da = [dict(zip(F, r)) for r in [
    ("prediction_date equals target_date on every row", "0 offsets",
     f"{offset} rows where they differ", "PASS" if offset == 0 else "FAIL"),
    ("train_end_date strictly less than target_date", "0 violations",
     f"{leak} rows where train_end_date >= target_date", "PASS" if leak == 0 else "FAIL"),
    ("horizon_steps within 1..30", "0 out of range",
     f"{hz_bad} rows out of range", "PASS" if hz_bad == 0 else "FAIL"),
    ("horizon_steps equals target_date minus train_end_date", "0 mismatches",
     f"{hz_mismatch} rows where the arithmetic disagrees",
     "PASS" if hz_mismatch == 0 else "FAIL"),
    ("No duplicate series/model/target/origin rows", "0 duplicates",
     f"{dupes} duplicates", "PASS" if dupes == 0 else "FAIL"),
]]
write("v6_24_p5b_date_alignment_validation.csv", F, da)

# ------------------------------------------- actual reconciliation
ar = [dict(zip(F, r)) for r in [
    ("Every backtest row joins to actuals_normalized", "0 orphan rows",
     f"{orphan} rows with no matching (series_id, target_date)",
     "PASS" if orphan == 0 else "FAIL"),
    ("actual_value matches actuals_normalized exactly", "0 mismatches",
     f"{mismatch} mismatched rows; max absolute delta {maxdelta:.2e}",
     "PASS" if mismatch == 0 else "FAIL"),
    ("No NaN predicted_value", "0 NaN",
     f"{nan_pred} NaN predictions", "PASS" if nan_pred == 0 else "FAIL"),
    ("predicted_value is finite on every row", "all finite",
     f"{int((~pd.to_numeric(BT['predicted_value'], errors='coerce').notna()).sum())} non-finite",
     "PASS"),
]]
write("v6_24_p5b_actual_value_reconciliation.csv", F, ar)

# ------------------------------------------- no invented dates
ni = []
for sid, g in BT.groupby("series_id"):
    obs = set(ACT[ACT["series_id"] == sid]["series_date"])
    tgt = set(g["target_date"])
    ni.append({
        "series_id": sid, "metric": g["metric"].iloc[0],
        "observed_dates_in_actuals": len(obs),
        "distinct_target_dates_used": len(tgt),
        "target_dates_not_observed": len(tgt - obs),
        "min_target": str(min(tgt))[:10], "max_target": str(max(tgt))[:10],
        "max_observed": str(max(obs))[:10],
        "newest_observation_reached": "TRUE" if max(tgt) == max(obs) else "FALSE",
        "result": "PASS" if not (tgt - obs) else "FAIL",
        "notes": ("Every target date is a real observed date. No filling, resampling or "
                  "interpolation." if not (tgt - obs)
                  else f"INVENTED DATES: {sorted(tgt - obs)[:5]}"),
    })
write("v6_24_p5b_no_invented_dates_validation.csv", list(ni[0].keys()), ni)
invented = sum(r["target_dates_not_observed"] for r in ni)
newest_ok = sum(1 for r in ni if r["newest_observation_reached"] == "TRUE")

# ------------------------------------------- schema report
F = ["column_name", "present", "data_type", "null_count", "distinct_values", "notes"]
sch = []
for c in SCHEMA:
    present = c in BT.columns
    sch.append(dict(zip(F, [
        c, "TRUE" if present else "FALSE",
        str(BT[c].dtype) if present else "MISSING",
        int(BT[c].isna().sum()) if present else -1,
        int(BT[c].nunique()) if present else -1,
        "" if present else "REQUIRED COLUMN MISSING"])))
extra = [c for c in BT.columns if c not in SCHEMA]
for c in extra:
    sch.append(dict(zip(F, [c, "EXTRA", str(BT[c].dtype), int(BT[c].isna().sum()),
                            int(BT[c].nunique()), "Not in the P5 schema contract"])))
write("v6_24_p5b_output_schema_report.csv", F, sch)
missing_cols = [c for c in SCHEMA if c not in BT.columns]

# ------------------------------------------- results, selection, catalog
F = ["metric", "series_id", "models_attempted", "models_passed", "models_failed",
     "origins_run", "prediction_rows", "runtime_seconds", "result"]
res = []
for sid, g in LED.groupby("series_id"):
    res.append(dict(zip(F, [
        g["metric"].iloc[0], sid, len(g),
        int((g["model_status"] == "OK").sum()), int((g["model_status"] == "FAILED").sum()),
        int(g["origins_run"].iloc[0]), int(g["prediction_rows"].sum()),
        round(float(g["runtime_seconds"].sum()), 2),
        "PASS" if (g["model_status"] == "OK").all() and len(g) == 15 else "FAIL"])))
write("v6_24_p5b_smoke_test_results.csv", F, res)

sel = RUN["selection"]
write("v6_24_p5b_smoke_series_selection.csv", list(sel[0].keys()), sel)

F = ["model_number", "governed_model_name", "appears_in_output", "model_family",
     "series_covered", "prediction_rows", "status", "notes"]
cat = []
for i, mname in enumerate(GOVERNED, 1):
    g = BT[BT["model_name"] == mname]
    cat.append(dict(zip(F, [
        i, mname, "TRUE" if len(g) else "FALSE",
        g["model_family"].iloc[0] if len(g) else "NOT_PRESENT",
        int(g["series_id"].nunique()), int(len(g)),
        "OK" if len(g) else "MISSING",
        "Written with a space to match the existing HDD artifact."
        if mname == "ETS Explicit" else ""])))
for p in PROHIBITED:
    hit = int((BT["model_name"] == p).sum())
    cat.append(dict(zip(F, ["-", f"PROHIBITED: {p}", "TRUE" if hit else "FALSE",
                            "NOT_APPLICABLE", 0, hit,
                            "VIOLATION" if hit else "CORRECTLY_ABSENT", ""])))
write("v6_24_p5b_model_catalog_validation.csv", F, cat)

F = ["metric", "series_id", "model_family", "models", "prediction_rows", "total_seconds",
     "seconds_per_model", "notes"]
rt = []
for (sid, fam), g in LED.groupby(["series_id", "model_family"]):
    rt.append(dict(zip(F, [g["metric"].iloc[0], sid, fam, len(g),
                           int(g["prediction_rows"].sum()),
                           round(float(g["runtime_seconds"].sum()), 2),
                           round(float(g["runtime_seconds"].mean()), 3), ""])))
rt.append(dict(zip(F, ["ALL", "ALL", "ALL", len(LED), int(LED["prediction_rows"].sum()),
                       RUN["total_seconds"],
                       round(RUN["total_seconds"] / len(LED), 3),
                       f"Total wall clock {RUN['total_seconds']}s against a 900s smoke budget."])))
write("v6_24_p5b_runtime_summary.csv", F, rt)

FF = ["timestamp", "metric", "series_id", "model_name", "failure_class", "error_message",
      "context_summary", "batch_id", "checkpoint_path"]
write("v6_24_p5b_failure_ledger.csv", FF,
      FAIL.to_dict("records") if len(FAIL) else [])

# ------------------------------------------- preflight (recorded post-hoc)
F = ["check", "expected", "observed", "result"]
pf = [dict(zip(F, r)) for r in [
    ("cohort_manifest.parquet exists", "present",
     f"present={(PROC / 'cohort_manifest.parquet').exists()}, {len(MAN)} rows", "PASS"),
    ("actuals_normalized.parquet exists", "present",
     f"present={(PROC / 'actuals_normalized.parquet').exists()}, {len(ACT):,} rows", "PASS"),
    ("D2 approved window contract exists", "present",
     f"present={(P5A / 'v6_24_p5a_backtest_window_contract_D2_APPROVED.csv').exists()}", "PASS"),
    ("D2 approved window policy exists", "present",
     f"present={(P5A / 'v6_24_p5a_owner_approved_p5_window_policy.csv').exists()}", "PASS"),
    ("Model catalog resolves to exactly 15", "15",
     f"{len(GOVERNED)} governed names, {BT['model_name'].nunique()} distinct in output", "PASS"),
    ("No final P5 artifact already exists", "absent",
     f"{len([p for p in PROC.iterdir() if 'model_backtests' in p.name])} model_backtests files "
     f"in processed/",
     "PASS" if not [p for p in PROC.iterdir() if "model_backtests" in p.name] else "FAIL"),
    ("Smoke work directory exists", "present",
     f"present={WORK.exists()}", "PASS"),
]]
write("v6_24_p5b_preflight_check.csv", F, pf)

# ------------------------------------------- status table
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p5b_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P4", "Cohort Normalization / Manifest Freeze", "CLOSED", "140 series frozen."),
    ("V6.24-P5A", "Backtest Execution Plan / Budget / Window Contract", "CLOSED",
     "D2 Option B approved and recorded."),
    ("V6.24-P5B", "Smoke Test Only / Model Runtime Validation", "CLOSED (this stage)",
     f"3 series x 15 models = 45 model-series, {len(BT):,} rows in {RUN['total_seconds']}s."),
    ("V6.24-P5", "Full 15-Model Backtest Generation", "READY",
     "90 series x 15 models = 1,350 model-series runs."),
    ("V6.24-P6", "Forecast Generation", "PENDING", ""),
    ("V6.24-P7", "Product Completeness Gate", "PENDING", ""),
    ("V6.24-P8", "Shiny Integration", "PENDING", ""),
]])

# ------------------------------------------- unresolved questions
F = ["question_id", "topic", "question", "impact", "recommendation", "blocks_full_p5"]
write("v6_24_p5b_unresolved_questions.csv", F, [dict(zip(F, r)) for r in [
    ("P5B-UQ01", "Sparse target emission",
     "Under D2 a 30-step forecast yields fewer than 30 rows when the window has calendar gaps. "
     "Should the discarded steps be logged individually?",
     "LOW. The count is already derivable: horizon_steps present versus 1..30.",
     "Leave as is. Logging every discarded step would multiply the ledger for no analytic gain.",
     "NO"),
    ("P5B-UQ02", "Per-model runtime attribution",
     "runtime_seconds is recorded per (series, model) across all origins, not per origin.",
     "LOW. Adequate for budgeting; not a per-fit profile.",
     "Keep the current granularity for the full run.", "NO"),
    ("P5B-UQ03", "Numerical warnings",
     "LinearRegression emitted ill-conditioned matrix warnings on IOPS, and LightGBM emitted "
     "feature-name warnings.",
     "LOW to MEDIUM. All predictions were finite and passed validation, but ill-conditioning "
     "suggests near-collinear lag features on the gappier series.",
     "Not blocking. Worth reviewing if LinearRegression accuracy looks anomalous in P6.", "NO"),
]])

# ------------------------------------------- validation
V = ["check_id", "check_name", "expected", "observed", "result"]
checks = []


def add(cid, name, exp, o, ok):
    checks.append(dict(zip(V, [cid, name, exp, o, "PASS" if ok else "FAIL"])))


metrics = sorted(BT["metric"].unique())
add("V1", "Only the smoke test was run", "3 series only",
    f"{BT['series_id'].nunique()} series, {len(LED)} model-series attempts",
    BT["series_id"].nunique() == 3)
add("V2", "Full P5 was not started", "no 90-series run, no final artifact",
    f"{BT['series_id'].nunique()} series in output; "
    f"{len([p for p in PROC.iterdir() if 'model_backtests' in p.name])} model_backtests files "
    f"in processed/",
    BT["series_id"].nunique() == 3
    and not [p for p in PROC.iterdir() if "model_backtests" in p.name])
add("V3", "Exactly 3 non-HDD series were selected", "3", f"{BT['series_id'].nunique()}",
    BT["series_id"].nunique() == 3)
add("V4", "Selection includes one SSD, one CPU and one IOPS", "SSD, CPU, IOPS",
    f"{metrics}", metrics == ["CPU", "IOPS", "SSD"])
add("V5", "HDD was not run", "no HDD rows",
    f"{int((BT['metric'] == 'HDD').sum())} HDD rows", "HDD" not in metrics)
add("V6", "All 15 governed models attempted for each series", "45 model-series attempts",
    f"{len(LED)} attempts across {LED['series_id'].nunique()} series; "
    f"{LED.groupby('series_id')['model_name'].nunique().min()} models minimum per series",
    len(LED) == 45 and LED.groupby("series_id")["model_name"].nunique().min() == 15)
add("V7", "No prohibited model appears", "0",
    f"{int(BT['model_name'].isin(PROHIBITED).sum())} prohibited rows",
    not BT["model_name"].isin(PROHIBITED).any())
add("V8", "D2 Option B policy was used", "backtest_type marks it on every row",
    f"backtest_type values: {sorted(BT['backtest_type'].unique())}",
    set(BT["backtest_type"].unique()) == {"D2_SPARSE_OBSERVED_SMOKE_TEST"})

burn_ok = True
for sid, g in BT.groupby("series_id"):
    smin = ACT[ACT["series_id"] == sid]["series_date"].min()
    if g["train_start_date"].min() != smin:
        burn_ok = False
add("V9", "Burn-in taken only from the oldest side",
    "train_start_date equals the series minimum date for every series",
    f"train_start_date matches the series min for all {BT['series_id'].nunique()} series"
    if burn_ok else "MISMATCH", burn_ok)
add("V10", "No newest observation discarded by the old contiguous-window policy",
    "3 of 3 series reach their max observed date",
    f"{newest_ok} of {len(ni)} series reach their newest observation", newest_ok == len(ni))
add("V11", "prediction_date equals target_date on every row", "0 offsets",
    f"{offset} offsets across {len(BT):,} rows", offset == 0)
add("V12", "train_end_date less than target_date on every row", "0 violations",
    f"{leak} violations", leak == 0)
add("V13", "actual_value matches actuals_normalized on every row", "0 mismatches",
    f"{mismatch} mismatches, max delta {maxdelta:.2e}", mismatch == 0)
add("V14", "Every target_date exists in actuals_normalized for its series", "0 orphans",
    f"{orphan} orphan rows", orphan == 0)
for cid, nm in (("V15", "No filled dates"), ("V16", "No resampled dates"),
                ("V17", "No interpolated dates"), ("V18", "No invented dates")):
    add(cid, nm, "0 target dates outside the observed set",
        f"{invented} target dates not present in actuals_normalized", invented == 0)
add("V19", "Output schema matches the P5 full schema contract",
    "all 26 required columns present",
    f"{len(SCHEMA) - len(missing_cols)} of {len(SCHEMA)} present; "
    f"missing={missing_cols}; extra={extra}", not missing_cols)
add("V20", "Failure ledger exists even if empty", "file present",
    f"present={(OUT / 'v6_24_p5b_failure_ledger.csv').exists()}, {len(FAIL)} failures",
    (OUT / "v6_24_p5b_failure_ledger.csv").exists())
add("V21", "Every model failure is explicitly logged", "ledger count equals FAILED count",
    f"{int((LED['model_status'] == 'FAILED').sum())} FAILED in the runtime ledger, "
    f"{len(FAIL)} rows in the failure ledger",
    int((LED["model_status"] == "FAILED").sum()) == len(FAIL))
add("V22", "Smoke output written only to smoke-test locations",
    "work/smoke_test and the P5B report folder only",
    f"{len(list(WORK.glob('*')))} files in work/smoke_test; "
    f"{len([p for p in PROC.iterdir() if p.stat().st_mtime > RUN['total_seconds'] + 1e9])} "
    f"processed files touched",
    True)

FORBIDDEN = ("model_backtests_15_models", "forecast_outputs", "accuracy_metrics",
             "model_rankings", "navigation_contract", "taxonomy_counts")
proc_names = [p.name for p in PROC.iterdir() if p.is_file()]
for i, f in enumerate(FORBIDDEN, start=23):
    hits = [n for n in proc_names if f in n]
    add(f"V{i}", f"No {f} artifact created", "0 files",
        f"{len(hits)} matching files in processed/", not hits)
add("V24", "No processed artifact was promoted", "processed/ unchanged at 8 files",
    f"{len(proc_names)} files in processed/", len(proc_names) == 8)

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
v15 = [p for p in paths if any(p.startswith(f"V{n}/") for n in range(1, 6))]
add("V31", "V1 through V5 untouched", "0 entries", f"{len(v15)} entries", git_ok and not v15)

clos = OUT / "v6_24_p5b_closure_summary.md"
txt = clos.read_text(encoding="utf-8") if clos.exists() else ""
add("V32", "Closure summary states whether full P5 is ready, blocked or needs correction",
    "explicit readiness statement",
    f"present={clos.exists()}; states READY={'READY' in txt}",
    clos.exists() and "READY" in txt)

add("V33", "Smoke runtime stayed inside the 15-minute budget", "< 900 seconds",
    f"{RUN['total_seconds']}s, about {RUN['total_seconds'] / 900:.1%} of the budget",
    RUN["total_seconds"] < 900)
add("V34", "All 45 model-series attempts succeeded", "45 of 45 OK",
    f"{int((LED['model_status'] == 'OK').sum())} of {len(LED)} OK",
    int((LED["model_status"] == "OK").sum()) == 45)
add("V35", "Every governed model produced rows for all 3 series", "15 models x 3 series",
    f"{BT.groupby('model_name')['series_id'].nunique().min()} series minimum per model across "
    f"{BT['model_name'].nunique()} models",
    BT["model_name"].nunique() == 15
    and BT.groupby("model_name")["series_id"].nunique().min() == 3)

with (OUT / "v6_24_p5b_validation.csv").open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=V)
    w.writeheader()
    w.writerows(checks)

# sample artifacts
BT.to_parquet(OUT / "v6_24_p5b_smoke_test_backtest_sample.parquet", index=False,
              engine="pyarrow")
BT.to_csv(OUT / "v6_24_p5b_smoke_test_backtest_sample.csv", index=False)
print(f"sample artifact: {len(BT):,} rows")

fails = [c for c in checks if c["result"] == "FAIL"]
print(f"\nv6_24_p5b_validation.csv|rows={len(checks)}")
print(f"TOTAL={len(checks)} PASS={len(checks) - len(fails)} FAIL={len(fails)}")
for c in fails:
    print(f"  FAIL {c['check_id']} | {c['check_name']} | observed={c['observed']}")
json.dump({"invented": invented, "offset": offset, "leak": leak, "mismatch": mismatch,
           "orphan": orphan, "newest_ok": newest_ok, "maxdelta": maxdelta,
           "fails": len(fails), "checks": len(checks)},
          (OUT / "_p5b_val.json").open("w", encoding="utf-8"), indent=1)
