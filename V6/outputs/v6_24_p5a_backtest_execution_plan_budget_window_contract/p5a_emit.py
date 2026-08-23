"""V6.24-P5A | Emit the execution plan, budget, contracts and risk register.

Planning only. No models are fitted and no product artifact is created.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
V617 = OUT.parent / "v6_17_full_multimetric_productive_artifact_generation"

MODELS = json.loads((OUT / "_p5a_models.json").read_text(encoding="utf-8"))
W = pd.read_csv(OUT / "v6_24_p5a_backtest_window_contract.csv", dtype=str)
for c in ("observation_count", "calendar_span_days", "missing_calendar_days",
          "valid_origin_count", "target_date_count", "sampled_origin_count",
          "proposed_burn_in_count"):
    W[c] = W[c].astype(int)
NEW = W[W["in_p5_workload"].str.upper() == "TRUE"]

LAGS, HORIZON, ORIGINS = MODELS["LAGS"], MODELS["HORIZON_DAYS"], 11
GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS_Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost", "FNAR-V2", "NLIN-DLIN_FIXED",
            "SMLP-TCN"]
REGISTERED = MODELS["all"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


# --------------------------------------------------- 1. status
F = ["stage", "name", "current_status", "notes"]
write("v6_24_p5a_reduced_status_table.csv", F, [dict(zip(F, r)) for r in [
    ("V6.24-P4", "Cohort Normalization / Manifest Freeze", "CLOSED",
     "140 series, 48,916 normalized actual rows."),
    ("V6.24-P5A", "Backtest Execution Plan / Budget / Window Contract",
     "CLOSED (this stage)",
     "Plan only. Two blocking-grade findings raised for owner decision."),
    ("V6.24-P5", "15-Model Backtest Generation", "READY PENDING OWNER DECISION",
     "1,350 model-series runs. Two decisions required first (see owner decisions file)."),
    ("V6.24-P6", "Forecast Generation", "PENDING", "Plus accuracy_metrics and model_rankings."),
    ("V6.24-P7", "Product Completeness Gate", "PENDING",
     "Produces navigation_contract and taxonomy_counts AFTER the gate."),
    ("V6.24-P8", "Shiny Integration", "PENDING", ""),
    ("V6.24-P9", "Visual QA / Demo Readiness", "PENDING", ""),
]])

# --------------------------------------------------- 2. model catalog
F = ["model_number", "governed_model_name", "registered_name_in_code", "model_family",
     "implementation_path", "implementation_status", "cost_class", "is_champion",
     "name_matches_governed_list", "notes"]
FAM = {**{m: "Baseline" for m in MODELS["base"]},
       **{m: "Challenger" for m in MODELS["chal"]},
       **{m: "Neural" for m in MODELS["neural"]}}
COST = {**{m: "LOW" for m in MODELS["base"]},
        **{m: "MEDIUM" for m in MODELS["chal"]},
        **{m: "HIGH" for m in MODELS["neural"]}}
PILOT = "V6/outputs/v6_16_five_case_viewer_uiux_lab/build_v6_16_pilot_backtest.py"
cat = []
for i, gov in enumerate(GOVERNED, 1):
    reg = gov if gov in REGISTERED else ("ETS Explicit" if gov == "ETS_Explicit" else None)
    matched = reg is not None and reg in REGISTERED
    cat.append(dict(zip(F, [
        i, gov, reg or "NOT_FOUND", FAM.get(reg, "UNKNOWN"), PILOT,
        "RESOLVED" if matched else "MODEL_IMPLEMENTATION_UNRESOLVED",
        COST.get(reg, "UNKNOWN"),
        "TRUE" if gov == "ETS_Explicit" else "FALSE",
        "TRUE" if reg == gov else "FALSE",
        ("Registered in code and in the existing HDD artifact as 'ETS Explicit' with a SPACE, "
         "not an underscore. Same model, different spelling. P5 must map the name explicitly "
         "rather than substitute silently." if gov == "ETS_Explicit"
         else f"Registered in {FAM.get(reg)} group."),
    ])))
for p in PROHIBITED:
    cat.append(dict(zip(F, ["-", f"PROHIBITED: {p}", "NOT_REGISTERED", "NOT_APPLICABLE",
                            "NOT_APPLICABLE", "CORRECTLY_ABSENT", "NOT_APPLICABLE", "FALSE",
                            "NOT_APPLICABLE",
                            "Confirmed absent from the registry. Must never be introduced."])))
write("v6_24_p5a_model_catalog_contract.csv", F, cat)

# --------------------------------------------------- 3. workload
F = ["metric", "series_to_run", "unique_keys", "models", "model_series_runs",
     "actual_rows", "obs_min", "obs_median", "obs_max", "sampled_origins_per_series",
     "valid_origins_min", "valid_origins_max", "series_origin_units",
     "origin_level_fits", "target_dates", "prediction_rows",
     "est_output_mb", "cost_profile", "caveat"]
wl = []
for m in ("SSD", "CPU", "IOPS"):
    g = NEW[NEW["metric"] == m]
    so = int(g["valid_origin_count"].sum())
    tg = int(g["target_date_count"].sum())
    wl.append(dict(zip(F, [
        m, len(g), g["series_id"].nunique(), 15, len(g) * 15,
        int(g["observation_count"].sum()), int(g["observation_count"].min()),
        int(g["observation_count"].median()), int(g["observation_count"].max()),
        ORIGINS, int(g["valid_origin_count"].min()), int(g["valid_origin_count"].max()),
        so, so * 15, tg, tg * 15, round(tg * 15 * 250 / 1e6, 1),
        "3 HIGH neural + 5 MEDIUM challenger + 7 LOW baseline",
        ("Windowed actuals; 2 calendar gaps per series" if m == "SSD"
         else f"STALE to 2023-07-20; {int(g['missing_calendar_days'].min())}-"
              f"{int(g['missing_calendar_days'].max())} calendar gaps per series"),
    ])))
tot_so = int(NEW["valid_origin_count"].sum())
tot_tg = int(NEW["target_date_count"].sum())
wl.append(dict(zip(F, [
    "TOTAL_NEW_P5", 90, int(NEW["series_id"].nunique()), 15, 1350,
    int(NEW["observation_count"].sum()), int(NEW["observation_count"].min()),
    int(NEW["observation_count"].median()), int(NEW["observation_count"].max()),
    ORIGINS, int(NEW["valid_origin_count"].min()), int(NEW["valid_origin_count"].max()),
    tot_so, tot_so * 15, tot_tg, tot_tg * 15, round(tot_tg * 15 * 250 / 1e6, 1),
    "1,350 model-series runs", "90 series x 15 models = 1,350 model-series runs"])))
hdd = W[W["metric"] == "HDD"]
wl.append(dict(zip(F, [
    "HDD_REUSE_ONLY", 50, int(hdd["series_id"].nunique()), 15, 750,
    int(hdd["observation_count"].sum()), int(hdd["observation_count"].min()),
    int(hdd["observation_count"].median()), int(hdd["observation_count"].max()),
    ORIGINS, int(hdd["valid_origin_count"].min()), int(hdd["valid_origin_count"].max()),
    0, 0, 0, 0, 0.0, "NOT_RUN",
    "REUSE/REFERENCE ONLY. HDD backtests already exist in local artifacts and must NOT be "
    "re-run in P5."])))
wl.append(dict(zip(F, [
    "FINAL_PRODUCT_COVERAGE", 140, "NOT_APPLICABLE", 15, 2100, "NOT_APPLICABLE",
    "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", ORIGINS, "NOT_APPLICABLE",
    "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE",
    "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE",
    "140 series x 15 models = 2,100 series-model combinations: 750 HDD reused from local "
    "artifacts plus 1,350 newly generated in P5."])))
write("v6_24_p5a_workload_estimate.csv", F, wl)

# --------------------------------------------------- 5. HDD schema mapping
F = ["source_hdd_artifact", "model_name", "date_column", "target_date_column",
     "actual_column", "prediction_column", "forecast_start_date_column", "horizon_column",
     "grain_columns", "row_semantics", "notes"]
ART = "V6/outputs/v6_17_full_multimetric_productive_artifact_generation/" \
      "forecast_viewer_model_outputs_v2_full.parquet"
write("v6_24_p5a_hdd_backtest_schema_mapping.csv", F, [dict(zip(F, r)) for r in [
    (ART, "all 15 governed models", "date", "date", "actual_value", "forecast_value",
     "forecast_start_date", "horizon_days",
     "metric|scenario|granularity|series_key|model_name|forecast_start_date|horizon_days",
     "ONE ROW PER (series, model, forecast_start_date, horizon_day)",
     "The artifact is per-date AND per-origin: each origin contributes 30 rows, one per "
     "horizon day. 'date' is the TARGET date, so date = forecast_start_date + horizon_days. "
     "Confirmed: 4,915 series-origins x 15 models x 30 days = 2,211,750 rows in the R6P1 "
     "lineage."),
    (ART, "reference generator", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE",
     "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE", "NOT_APPLICABLE",
     "GENERATOR",
     "run_v6_17_viewer_backtests.py, which imports build_v6_16_pilot_backtest.py for the model "
     f"registry. LAGS={LAGS}, HORIZON_DAYS={HORIZON}, origins sampled by np.linspace between "
     f"min+{LAGS + HORIZON + 4}d and max-{HORIZON}d, 11 per series (5 for HDD-Basilisk)."),
    (ART, "P5 alignment requirement", "series_date", "target_date", "actual_value",
     "predicted_value", "forecast_start_date", "horizon_steps",
     "cohort_id|series_id|model_name|forecast_start_date|horizon_steps",
     "P5 MUST MATCH THIS GRAIN",
     "P5 output must be one row per (series, model, origin, horizon step) so it can be unioned "
     "with the HDD artifact. Column names are renamed to the P4 vocabulary but semantics are "
     "identical."),
]])

# --------------------------------------------------- 6. budget
F = ["budget_name", "max_wall_clock_minutes", "soft_stop_minutes", "finalization_minutes",
     "batch_size_series", "batch_size_model_series", "checkpoint_frequency", "stop_behavior",
     "partial_artifact_behavior", "completion_required_for_success", "notes"]
write("v6_24_p5a_execution_budget_plan.csv", F, [dict(zip(F, r)) for r in [
    ("P5_FULL_RUN", 120, 105, 15, 10, 150, "AFTER_EVERY_BATCH",
     "At soft stop (105 min) finish the current batch, checkpoint, then stop. At hard stop "
     "(120 min) stop cleanly and write the failure ledger.",
     "Partial results stay in V6/data/model_runs/v6_24_p5_work/checkpoints/ and are NEVER "
     "promoted to processed/. Shiny must not see them.",
     "ALL 1,350 model-series runs must complete, or the owner must approve a documented "
     "exception. No silent missing model rows.",
     f"Reference calibration: the HDD run completed 4,915 series-origins x 15 models = 73,725 "
     f"fits within a 4-hour budget with a 38-minute reserve. P5 needs {tot_so * 15:,} fits, "
     f"about {tot_so * 15 / 73725:.0%} of that, so roughly 20-40 minutes is expected. The "
     f"2-hour budget carries a wide margin."),
    ("PHASE_A_NON_NEURAL", 60, 50, 5, 10, 120, "AFTER_EVERY_BATCH",
     "12 low/medium-cost models. Finish current batch at soft stop.",
     "Checkpoint CSV per batch under temp_outputs/.", "All 90 series x 12 models",
     "Baselines and challengers. Cheap and stable. Run first so a budget overrun cannot cost "
     "the whole cohort."),
    ("PHASE_B_NEURAL", 60, 55, 10, 5, 15, "AFTER_EVERY_BATCH",
     "3 high-cost models (FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN). Isolated phase.",
     "Checkpoint CSV per batch under temp_outputs/.", "All 90 series x 3 models",
     "Isolated so neural instability cannot take down the cheap models, mirroring the two-phase "
     "structure of the HDD reference run."),
]])

# --------------------------------------------------- 7. batching
F = ["batch_id", "phase", "metric", "series_count", "model_count",
     "expected_model_series_runs", "expected_prediction_rows", "checkpoint_path",
     "resume_key", "risk_level", "notes"]
WORK = "V6/data/model_runs/v6_24_p5_work"
batches, bid = [], 0
for phase, models, mcount in (("A_non_neural", "12 baseline + challenger", 12),
                              ("B_neural", "3 neural", 3)):
    for m in ("SSD", "CPU", "IOPS"):
        g = NEW[NEW["metric"] == m]
        size = 10 if phase.startswith("A") else 5
        for i in range(0, len(g), size):
            bid += 1
            chunk = g.iloc[i:i + size]
            batches.append(dict(zip(F, [
                f"B{bid:03d}", phase, m, len(chunk), mcount, len(chunk) * mcount,
                int(chunk["target_date_count"].sum()) * mcount,
                f"{WORK}/checkpoints/{phase}_{m}_{i // size + 1:02d}.csv",
                f"{phase}|{m}|{i // size + 1:02d}",
                "HIGH" if phase.startswith("B") else "LOW",
                f"Series {i + 1}-{min(i + size, len(g))} of {len(g)} for {m}. "
                f"Resume key lets P5 skip completed batches on restart.",
            ])))
write("v6_24_p5a_batch_checkpoint_plan.csv", F, batches)

# --------------------------------------------------- 8. failure policy
F = ["failure_class", "trigger", "detection", "p5_behavior", "run_marked_incomplete",
     "owner_approval_required", "recorded_fields", "notes"]
REC = "series_id, model_name, metric, error_type, error_message, timestamp, batch_id, origin_date"
write("v6_24_p5a_failure_policy.csv", F, [dict(zip(F, r)) for r in [
    ("MODEL_IMPLEMENTATION_UNRESOLVED",
     "A governed model has no executable implementation.",
     "Registry check at startup before any fitting.",
     "ABORT before any work. Never substitute a different model.", "TRUE", "TRUE", REC,
     "P5A verified all 15 resolve, so this should not trigger."),
    ("MODEL_RUNTIME_FAILURE", "A model raises during fit or predict.",
     "try/except around each (series, model, origin) unit.",
     "Record the failure, continue with other units. Do NOT write a NaN prediction row.",
     "TRUE", "TRUE", REC,
     "No silent NaN. A missing row must be visible in the failure ledger, not disguised."),
    ("SERIES_TOO_SHORT_AFTER_BURN_IN", "Fewer than 65 training rows at an origin.",
     "Pre-flight from the window contract, then re-checked at runtime.",
     "Skip that origin, record it. If a series has zero valid origins, abort the series and "
     "record it.", "TRUE", "TRUE", REC,
     "P5A measured 0 of 90 series with zero valid origins, so this is not expected."),
    ("DEPENDENCY_MISSING", "An import fails (sklearn, statsmodels, lightgbm, xgboost).",
     "Import-only capability check at startup.",
     "ABORT before any work.", "TRUE", "TRUE", REC,
     "P5A confirmed the pilot module imports cleanly."),
    ("TIME_BUDGET_EXCEEDED", "Soft or hard stop reached.",
     "Elapsed-time check before each batch.",
     "Finish the current batch, checkpoint, stop cleanly. Partial output stays in work/.",
     "TRUE", "TRUE", REC, "Partial results must never be promoted to processed/."),
    ("VALUE_ERROR", "Non-finite or non-numeric prediction.",
     "np.isfinite check on every prediction vector.",
     "Reject the unit and record it as a failure. Never write the row.", "TRUE", "TRUE", REC,
     "The HDD reference already enforces this."),
    ("DATE_ALIGNMENT_FAILURE",
     "prediction_date != target_date, or actual_value does not match actuals_normalized.",
     "Post-batch assertion joining predictions back to actuals_normalized on "
     "(series_id, target_date).",
     "ABORT the batch. This is a correctness failure, not a tolerable one.", "TRUE", "TRUE", REC,
     "THE MOST IMPORTANT CHECK. A silent one-day offset would make every accuracy number wrong "
     "while looking plausible."),
    ("OUTPUT_SCHEMA_FAILURE", "A checkpoint lacks a contract column or has a wrong dtype.",
     "Schema assertion before each checkpoint write.",
     "ABORT the batch.", "TRUE", "TRUE", REC, ""),
]])

# --------------------------------------------------- 9. output schema
F = ["column_name", "data_type", "required", "source", "definition", "invariant", "notes"]
SC = [
    ("cohort_id", "string", "TRUE", "cohort_manifest", "Frozen cohort identifier.",
     "Must exist in cohort_manifest.", ""),
    ("series_id", "string", "TRUE", "cohort_manifest", "Series identity and join key.",
     "Must exist in cohort_manifest; 90 distinct values in P5 output.", ""),
    ("metric", "string", "TRUE", "cohort_manifest", "SSD | CPU | IOPS.",
     "HDD must NOT appear: it is reused, not regenerated.", ""),
    ("db_type", "string", "TRUE", "cohort_manifest", "DB branch axis.",
     "Explicit placeholder where the source has none.", ""),
    ("scenario", "string", "TRUE", "cohort_manifest", "Consumed | Failover | NOT_APPLICABLE.",
     "", ""),
    ("segment", "string", "TRUE", "cohort_manifest", "NOT_APPLICABLE for all P5 metrics.", "", ""),
    ("granularity", "string", "TRUE", "cohort_manifest", "Forest | Region.", "", ""),
    ("key", "string", "TRUE", "cohort_manifest", "Series entity.", "", ""),
    ("route_path", "string", "TRUE", "cohort_manifest", "Taxonomy route.", "", ""),
    ("model_name", "string", "TRUE", "model registry", "Governed model name.",
     "Exactly 15 distinct values; must match the governed catalog.",
     "Write 'ETS Explicit' with a space to stay consistent with the HDD artifact."),
    ("model_family", "string", "TRUE", "model registry", "Baseline | Challenger | Neural.", "", ""),
    ("target_date", "date", "TRUE", "computed", "The date being predicted.",
     "Must exist in actuals_normalized for this series_id.", ""),
    ("prediction_date", "date", "TRUE", "computed", "The date the prediction refers to.",
     "MUST EQUAL target_date.", "Guards against a visual offset between actual and estimate."),
    ("train_start_date", "date", "TRUE", "computed", "First date in the training window.",
     "Equals the series min date. Burn-in is left-side only.", ""),
    ("train_end_date", "date", "TRUE", "computed", "Origin date. Last date used for training.",
     "MUST BE STRICTLY LESS THAN target_date.", "Guards against leakage of future actuals."),
    ("horizon_steps", "int", "TRUE", "computed", "Days ahead: target_date - train_end_date.",
     "Between 1 and 30.", ""),
    ("actual_value", "double", "TRUE", "actuals_normalized", "Observed value at target_date.",
     "MUST EQUAL actuals_normalized for (series_id, target_date).",
     "Joined, never recomputed."),
    ("predicted_value", "double", "TRUE", "model", "Model estimate for target_date.",
     "Must be finite. NaN rows are rejected, not written.", ""),
    ("backtest_type", "string", "TRUE", "constant", "Always 'backtest'.",
     "Matches the HDD artifact's forecast_type.", ""),
    ("burn_in_count", "int", "TRUE", "window contract", "Oldest observations reserved as warm-up.",
     "Taken from the LEFT of the series only.", ""),
    ("source_actuals_artifact", "string", "TRUE", "constant",
     "processed/v6_24_mvp_cohort/actuals_normalized.parquet", "", ""),
    ("model_run_id", "string", "TRUE", "runtime", "Identifier for the P5 execution.",
     "Stable within one run.", ""),
    ("model_status", "string", "TRUE", "runtime", "OK | FAILED.",
     "Only OK rows may be promoted to processed/.", ""),
    ("runtime_seconds", "double", "TRUE", "runtime", "Fit plus predict time for the unit.", "", ""),
    ("caveat", "string", "TRUE", "cohort_manifest", "Carried from the manifest.",
     "STALE_ACTUALS_SOURCE must survive onto CPU and IOPS rows.", ""),
]
write("v6_24_p5a_model_backtest_output_schema_contract.csv", F,
      [dict(zip(F, r)) for r in SC])
print("part 1 emitted")
