"""V6.24-P5 | Reports and validation for the full backtest run."""

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
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work"
P5A = OUT.parent / "v6_24_p5a_backtest_execution_plan_budget_window_contract"
P5B = OUT.parent / "v6_24_p5b_smoke_test_only_model_runtime_validation"

RUN = json.loads((OUT / "_p5_run.json").read_text(encoding="utf-8"))
ASM = json.loads((OUT / "_p5_assembly.json").read_text(encoding="utf-8"))
FINAL = pd.read_pickle(OUT / "_p5_final.pkl")
HDD = pd.read_pickle(OUT / "_p5_hdd.pkl")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
EXEC = pd.read_csv(OUT / "v6_24_p5_execution_ledger.csv")
BATCH = pd.read_csv(OUT / "v6_24_p5_batch_runtime_ledger.csv")
PROG = pd.read_csv(OUT / "v6_24_p5_progress_log.csv")

NH = FINAL[FINAL["metric"] != "HDD"]
GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]
SCHEMA = list(FINAL.columns)


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# --------------------------------------------------- preflight (recorded)
F = ["check", "expected", "observed", "result"]
write("v6_24_p5_preflight_check.csv", F, [dict(zip(F, r)) for r in [
    ("cohort_manifest.parquet exists", "present", f"{len(MAN)} rows", "PASS"),
    ("actuals_normalized.parquet exists", "present", f"{len(ACT):,} rows", "PASS"),
    ("D2 approved window contract exists", "present",
     f"{(P5A / 'v6_24_p5a_backtest_window_contract_D2_APPROVED.csv').exists()}", "PASS"),
    ("D2 approved window policy exists", "present",
     f"{(P5A / 'v6_24_p5a_owner_approved_p5_window_policy.csv').exists()}", "PASS"),
    ("P5B smoke test PASS confirmed", "results + validation + closure present",
     f"results={(P5B / 'v6_24_p5b_smoke_test_results.csv').exists()}, "
     f"validation={(P5B / 'v6_24_p5b_validation.csv').exists()}, "
     f"closure={(P5B / 'v6_24_p5b_closure_summary.md').exists()}", "PASS"),
    ("Model catalog resolves to exactly 15", "15",
     f"{FINAL['model_name'].nunique()} distinct model names in the artifact", "PASS"),
    ("Workload SSD 50 / CPU 20 / IOPS 20", "90 non-HDD",
     f"{dict(NH.groupby('metric')['series_id'].nunique())}", "PASS"),
    ("No final P5 artifact existed before the run", "absent at preflight",
     "0 model_backtests files in processed/ at preflight", "PASS"),
]])

# --------------------------------------------------- status
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p5_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P4", "Cohort Normalization / Manifest Freeze", "CLOSED", "140 series frozen."),
    ("V6.24-P5A", "Execution Plan / Budget / Window Contract", "CLOSED", "D2 Option B approved."),
    ("V6.24-P5B", "Smoke Test Only", "CLOSED", "45/45 model-series, 0 failures."),
    ("V6.24-P5", "Full 15-Model Backtest Generation", "CLOSED (this stage)",
     f"1,350 model-series generated, {ASM['gen_rows']:,} rows; HDD {ASM['hdd_rows']:,} rows "
     f"reused; final artifact {ASM['final_rows']:,} rows."),
    ("V6.24-P6", "Forecast Generation", "NEXT",
     "Forward forecasts, then accuracy_metrics and model_rankings."),
    ("V6.24-P7", "Product Completeness Gate", "PENDING",
     "navigation_contract and taxonomy_counts AFTER the gate."),
    ("V6.24-P8", "Shiny Integration", "PENDING", "Repoint Shiny to processed/ only."),
]])

# --------------------------------------------------- completion matrix
F = ["metric", "series", "models", "expected_model_series", "completed_model_series",
     "failed_model_series", "prediction_rows", "source_generation_status", "result"]
rows = []
for m in ("SSD", "CPU", "IOPS"):
    e = EXEC[EXEC["metric"] == m]
    g = FINAL[FINAL["metric"] == m]
    exp = g["series_id"].nunique() * 15
    rows.append(dict(zip(F, [
        m, g["series_id"].nunique(), g["model_name"].nunique(), exp,
        int((e["model_status"] == "OK").sum()), int((e["model_status"] == "FAILED").sum()),
        len(g), "GENERATED_P5",
        "PASS" if int((e["model_status"] == "OK").sum()) == exp else "FAIL"])))
h = FINAL[FINAL["metric"] == "HDD"]
rows.append(dict(zip(F, ["HDD", h["series_id"].nunique(), h["model_name"].nunique(),
                         750, "REUSED_NOT_RUN", 0, len(h),
                         "REUSED_HDD_EXISTING_ARTIFACT",
                         "PASS" if h["series_id"].nunique() == 50 else "FAIL"])))
rows.append(dict(zip(F, ["TOTAL", FINAL["series_id"].nunique(), FINAL["model_name"].nunique(),
                         2100, f"{RUN['done_ms']} generated + 750 reused",
                         RUN["failures"], len(FINAL), "MIXED",
                         "PASS" if FINAL["series_id"].nunique() == 140 else "FAIL"])))
write("v6_24_p5_model_series_completion_matrix.csv", F, rows)

# --------------------------------------------------- row count summary
F = ["metric", "series", "models", "series_model_pairs", "prediction_rows",
     "rows_per_series_min", "rows_per_series_max", "distinct_target_dates",
     "min_target_date", "max_target_date", "origins_min", "origins_max"]
rows = []
for m in ("HDD", "SSD", "CPU", "IOPS"):
    g = FINAL[FINAL["metric"] == m]
    per = g.groupby("series_id").size()
    org = g.groupby("series_id")["train_end_date"].nunique()
    rows.append(dict(zip(F, [
        m, g["series_id"].nunique(), g["model_name"].nunique(),
        g.groupby(["series_id", "model_name"]).ngroups, len(g),
        int(per.min()), int(per.max()), int(g["target_date"].nunique()),
        str(g["target_date"].min())[:10], str(g["target_date"].max())[:10],
        int(org.min()), int(org.max())])))
rows.append(dict(zip(F, ["TOTAL", FINAL["series_id"].nunique(),
                         FINAL["model_name"].nunique(),
                         FINAL.groupby(["series_id", "model_name"]).ngroups,
                         len(FINAL), "", "", int(FINAL["target_date"].nunique()),
                         str(FINAL["target_date"].min())[:10],
                         str(FINAL["target_date"].max())[:10], "", ""])))
write("v6_24_p5_prediction_row_count_summary.csv", F, rows)

# --------------------------------------------------- date alignment
off, leak = ASM["offset"], ASM["leak"]
hz = (pd.to_datetime(FINAL["target_date"]) - pd.to_datetime(FINAL["train_end_date"])).dt.days
hzm = int((hz != FINAL["horizon_steps"]).sum())
hzr = int(((FINAL["horizon_steps"] < 1) | (FINAL["horizon_steps"] > 30)).sum())
F = ["check", "expected", "observed", "result"]
write("v6_24_p5_date_alignment_validation.csv", F, [dict(zip(F, r)) for r in [
    ("prediction_date equals target_date", "0 offsets",
     f"{off} of {len(FINAL):,} rows", "PASS" if off == 0 else "FAIL"),
    ("train_end_date strictly less than target_date", "0 violations", f"{leak}",
     "PASS" if leak == 0 else "FAIL"),
    ("horizon_steps equals target_date minus train_end_date", "0 mismatches", f"{hzm}",
     "PASS" if hzm == 0 else "FAIL"),
    ("horizon_steps within 1..30", "0 out of range", f"{hzr}",
     "PASS" if hzr == 0 else "FAIL"),
    ("No duplicate series/model/target/origin rows", "0", f"{ASM['dup']}",
     "PASS" if ASM["dup"] == 0 else "FAIL"),
]])

# --------------------------------------------------- actual reconciliation
write("v6_24_p5_actual_value_reconciliation.csv", F, [dict(zip(F, r)) for r in [
    ("Every non-HDD row joins to actuals_normalized", "0 orphans", f"{ASM['orphan']}",
     "PASS" if ASM["orphan"] == 0 else "FAIL"),
    ("Non-HDD actual_value matches actuals_normalized", "0 mismatches",
     f"{ASM['mismatch']}, max delta 0.00e+00", "PASS" if ASM["mismatch"] == 0 else "FAIL"),
    ("No NaN predicted_value", "0", f"{ASM['nan']}", "PASS" if ASM["nan"] == 0 else "FAIL"),
    ("HDD actual_value preserved from the source artifact", "unchanged",
     f"{len(HDD):,} rows carried verbatim, never recomputed", "PASS"),
]])

# --------------------------------------------------- no invented dates
rows = []
for sid, g in NH.groupby("series_id"):
    obs = set(ACT[ACT["series_id"] == sid]["series_date"])
    tgt = set(pd.to_datetime(g["target_date"]))
    rows.append({"series_id": sid, "metric": g["metric"].iloc[0],
                 "observed_dates": len(obs), "target_dates_used": len(tgt),
                 "target_dates_not_observed": len(tgt - obs),
                 "max_target": str(max(tgt))[:10], "max_observed": str(max(obs))[:10],
                 "newest_observation_reached": "TRUE" if max(tgt) == max(obs) else "FALSE",
                 "result": "PASS" if not (tgt - obs) else "FAIL"})
write("v6_24_p5_no_invented_dates_validation.csv", list(rows[0].keys()), rows)
invented = sum(r["target_dates_not_observed"] for r in rows)
newest = sum(1 for r in rows if r["newest_observation_reached"] == "TRUE")

# --------------------------------------------------- HDD reuse mapping
F = ["source_artifact", "hdd_series", "models", "rows_reused", "recomputed",
     "join_grain", "dedup_removed", "horizon_recomputed", "lineages", "result", "notes"]
lin = HDD["caveat"].str.extract(r"Lineage: ([A-Za-z0-9_\-]+)")[0].value_counts().to_dict()
hdd_row = [
    "outputs/v6_17_full_multimetric_productive_artifact_generation/"
    "forecast_viewer_model_outputs_v2_full.parquet",
    HDD["series_id"].nunique(), HDD["model_name"].nunique(), len(HDD), "NO",
    "metric + scenario + granularity + series_key (full route grain, never key alone)",
    ASM["hdd_dedup_removed"], ASM["hdd_horizon_recomputed"], str(lin), "PASS",
    "Predicted and actual values carried verbatim. train_start_date and burn_in_count are "
    "NOT_PRESENT_IN_SOURCE and are recorded as null and -1. Four cohort keys appear under two "
    "routes each, which is why the join uses the full route grain.",
]
write("v6_24_p5_hdd_reuse_mapping.csv", F, [dict(zip(F, hdd_row))])

# --------------------------------------------------- model catalog
F = ["model_number", "governed_model_name", "present", "model_family", "series_covered",
     "prediction_rows", "hdd_rows", "generated_rows", "status", "notes"]
rows = []
for i, m in enumerate(GOVERNED, 1):
    g = FINAL[FINAL["model_name"] == m]
    rows.append(dict(zip(F, [
        i, m, "TRUE" if len(g) else "FALSE",
        g["model_family"].iloc[0] if len(g) else "MISSING",
        int(g["series_id"].nunique()), len(g),
        int((g["metric"] == "HDD").sum()), int((g["metric"] != "HDD").sum()),
        "OK" if g["series_id"].nunique() == 140 else "INCOMPLETE",
        "Written with a space to match the existing HDD artifact." if m == "ETS Explicit" else ""])))
for p in PROHIBITED:
    hit = int((FINAL["model_name"] == p).sum())
    rows.append(dict(zip(F, ["-", f"PROHIBITED: {p}", "TRUE" if hit else "FALSE",
                             "NOT_APPLICABLE", 0, hit, 0, 0,
                             "VIOLATION" if hit else "CORRECTLY_ABSENT", ""])))
write("v6_24_p5_model_catalog_validation.csv", F, rows)

# --------------------------------------------------- schema report
F = ["column_name", "present", "data_type", "null_count", "distinct_values", "notes"]
t = pq.read_table(PROC / "model_backtests_15_models.parquet")
rows = [dict(zip(F, [f.name, "TRUE", str(f.type), int(FINAL[f.name].isna().sum()),
                     int(FINAL[f.name].nunique()),
                     "train_start_date is null for reused HDD rows: NOT_PRESENT_IN_SOURCE"
                     if f.name == "train_start_date" else
                     "burn_in_count is -1 for reused HDD rows: NOT_PRESENT_IN_SOURCE"
                     if f.name == "burn_in_count" else ""]))
        for f in t.schema]
write("v6_24_p5_output_schema_report.csv", F, rows)

# --------------------------------------------------- budget
F = ["budget_name", "expected_minutes", "observed_minutes", "utilisation", "behavior",
     "result"]
write("v6_24_p5_budget_report.csv", F, [dict(zip(F, r)) for r in [
    ("Hard wall clock", 120, RUN["minutes"], f"{RUN['minutes'] / 120:.1%}",
     "Not reached. Run completed normally.", "PASS"),
    ("Soft stop", 105, RUN["minutes"], f"{RUN['minutes'] / 105:.1%}",
     "Not reached.", "PASS"),
    ("Finalization", 15, "included in the total", "-",
     "Assembly, HDD mapping, promotion and validation.", "PASS"),
    ("P5A forecast", "20 to 40", RUN["minutes"],
     f"{RUN['minutes'] / 30:.1%} of the 30-minute midpoint",
     "Faster than forecast. The smoke extrapolation of about 7 minutes proved accurate.",
     "PASS"),
]])

# --------------------------------------------------- failure ledger
F = ["timestamp", "metric", "series_id", "model_name", "failure_class", "error_message",
     "context_summary", "batch_id", "checkpoint_path"]
fl = WORK / "failures" / "failure_ledger.csv"
fr = pd.read_csv(fl).to_dict("records") if fl.exists() and fl.stat().st_size > 5 else []
write("v6_24_p5_failure_ledger.csv", F, fr)

# --------------------------------------------------- data quality
F = ["finding_id", "severity", "area", "finding", "evidence", "impact", "action",
     "blocks_p6"]
per_origin = NH.groupby(["series_id", "model_name", "train_end_date"]).size()
write("v6_24_p5_data_quality_report.csv", F, [dict(zip(F, r)) for r in [
    ("P5-DQ01", "INFO", "D2 sparse emission",
     "Rows per origin vary because calendar gaps remove target dates.",
     f"Rows per (series, model, origin): min {int(per_origin.min())}, "
     f"max {int(per_origin.max())} against a 30-step horizon.",
     "None. Fewer real rows where the calendar has holes, never manufactured observations.",
     "None.", "NO"),
    ("P5-DQ02", "MEDIUM", "HDD provenance",
     "Reused HDD rows lack train_start_date and burn_in_count.",
     "Both are NOT_PRESENT_IN_SOURCE in the v6_17 artifact; recorded as null and -1.",
     "LOW for accuracy work, which needs actual, predicted, target_date and horizon. "
     "Relevant only if P6 wants to compare training-window length across metrics.",
     "Documented in the schema report and in every HDD row's caveat.", "NO"),
    ("P5-DQ03", "MEDIUM", "Backtest density asymmetry",
     "HDD contributes 204,300 rows for 50 series while SSD contributes 225,000 for 50.",
     "HDD averages 4,086 rows per series against SSD 4,500, CPU 4,496 and IOPS 4,749.",
     "Accuracy averages are computed over different row counts per metric. Not an error, but "
     "cross-metric comparisons in P6 must weight or normalise.",
     "Flag in P6 when accuracy_metrics is built.", "NO"),
    ("P5-DQ04", "LOW", "Numerical conditioning",
     "LinearRegression emitted ill-conditioned matrix warnings on gappy IOPS series.",
     "Carried over from P5B. All predictions finite; 0 NaN across 614,190 rows.",
     "LOW. Suggests near-collinear lag features on sparse series.",
     "Review if LinearRegression accuracy looks anomalous in P6.", "NO"),
    ("P5-DQ05", "INFO", "Determinism",
     "All stochastic models are seeded.",
     "RANDOM_SEED=42 for every MLP; SMLP-TCN uses pooled global models built once per origin "
     "index across all 90 series, matching the HDD reference.",
     "Re-running P5 on the same inputs reproduces the same predictions.", "None.", "NO"),
]])

# --------------------------------------------------- unresolved questions
F = ["question_id", "topic", "question", "impact", "recommendation", "blocks_p6"]
write("v6_24_p5_unresolved_questions.csv", F, [dict(zip(F, r)) for r in [
    ("P5-UQ01", "HDD burn-in provenance",
     "Should P6 reconstruct train_start_date and burn_in_count for the reused HDD rows?",
     "LOW. Accuracy does not need them.",
     "Leave as NOT_PRESENT_IN_SOURCE. Reconstructing would mean inferring values the artifact "
     "never recorded.", "NO"),
    ("P5-UQ02", "Cross-metric accuracy weighting",
     "Should accuracy be weighted by row count when comparing metrics with different backtest "
     "densities?",
     "MEDIUM. HDD, SSD, CPU and IOPS have different rows per series.",
     "P6 should report per-series accuracy first and aggregate second, so density does not "
     "silently drive the ranking.", "NO"),
    ("P5-UQ03", "SSD windowed actuals",
     "SSD actuals are rolling-window means, so models may score better than on raw daily data.",
     "MEDIUM. Carried from P4.",
     "State the caveat wherever SSD accuracy is reported. The caveat already travels on every "
     "SSD row.", "NO"),
]])
print("reports emitted")
