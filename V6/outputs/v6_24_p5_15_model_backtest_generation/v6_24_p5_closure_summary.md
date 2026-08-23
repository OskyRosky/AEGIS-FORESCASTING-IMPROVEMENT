# V6.24-P5 — Full 15-Model Backtest Generation

**Stage:** V6.24-P5
**Status:** **COMPLETE.**
**Runtime:** **5.85 minutes** against a 120-minute hard budget (4.9%).
**Failures:** **0** across 1,350 model-series runs.
**Final artifact:** promoted — `model_backtests_15_models.parquet`, **614,190 rows**.

P5 generated **historical backtest estimates only**. No forward forecasts, no accuracy, no
rankings, no navigation artifacts. Those belong to P6 and P7.

---

## 1. What was produced

| Metric | Series | Models | Series-model pairs | Prediction rows | Origins/series | Target range |
|---|---:|---:|---:|---:|---|---|
| HDD | 50 | 15 | 750 | **204,300** | 5–12 | 2025-05-03 → 2026-07-19 |
| SSD | 50 | 15 | 750 | **225,000** | 10 | 2026-06-21 → 2026-08-22 |
| CPU | 20 | 15 | 300 | **89,910** | 10 | 2022-04-26 → 2023-07-20 |
| IOPS | 20 | 15 | 300 | **94,980** | 10–11 | 2020-08-27 → 2023-07-20 |
| **Total** | **140** | **15** | **2,100** | **614,190** | | |

- **1,350 model-series newly generated** (SSD + CPU + IOPS) → 409,890 rows
- **750 model-series reused** (HDD, not re-run) → 204,300 rows

The generated row count is **409,890 — exactly the figure P5A forecast from the D2 window
contract**, to the digit. That is a strong signal that the window contract and the runner agree
on the same policy.

---

## 2. Progress and budget

| Milestone | Elapsed | ETA at the time | Model-series | Rows | Failures |
|---|---:|---:|---:|---:|---:|
| 10% | 0.61m | 5.50m | 135 | 40,500 | 0 |
| 30% | 1.58m | 3.68m | 405 | 121,500 | 0 |
| 50% | 2.65m | 2.65m | 675 | 202,491 | 0 |
| 70% | 3.94m | 1.69m | 945 | 285,090 | 0 |
| 90% | 4.99m | 0.55m | 1,215 | 368,412 | 0 |
| **100%** | **5.85m** | 0.00m | **1,350** | **409,890** | **0** |

27 batches: 9 in Phase A (12 non-neural models, 10-series batches), 18 in Phase B (3 neural
models, 5-series batches). Every batch checkpointed to
`data/model_runs/v6_24_p5_work/checkpoints/`.

| Budget | Limit | Observed | Utilisation |
|---|---:|---:|---:|
| Hard wall clock | 120m | **5.85m** | **4.9%** |
| Soft stop | 105m | 5.85m | 5.6% |
| P5A forecast | 20–40m | 5.85m | Faster than forecast |

The P5B smoke extrapolation predicted about 7 minutes. The actual was 5.85. Phase A ran first
by design so that a neural failure could not have destroyed the cheap completed work — it never
had to.

---

## 3. The checks that decide whether this artifact is trustworthy

| Check | Expected | Observed |
|---|---|---|
| `prediction_date` = `target_date` | 0 offsets | **0 of 614,190** |
| `train_end_date` < `target_date` | 0 violations | **0** |
| `horizon_steps` = `target_date − train_end_date` | 0 mismatches | **0** |
| Non-HDD `actual_value` matches `actuals_normalized` | 0 mismatches | **0, max delta 0.00e+00** |
| Every non-HDD `target_date` observed | 0 orphans | **0** |
| **Invented dates** | **0** | **0** |
| Duplicate series/model/target/origin | 0 | **0** |
| NaN predictions | 0 | **0** |
| Newest observation preserved | 90 of 90 | **90 of 90** |

The reconciliation is independent: the validator re-joins every non-HDD row back to
`actuals_normalized` rather than trusting the runner. **Maximum absolute delta is exactly 0.0.**

---

## 4. D2 policy held across the full cohort

The owner-approved sparse-observed policy behaved as it did in the smoke test, at 30× the scale:

- Burn-in consumed only the **oldest** observations.
- The latest origin was **forced at `max_date − 30`** wherever valid.
- Rows were emitted **only for real observed target dates**.
- **All 90 non-HDD series reach their newest observation.** IOPS backtests now run to
  **2023-07-20** instead of stopping around December 2022 under the old strict-contiguity rule.

**Nothing was filled, resampled or interpolated.** Where the calendar has gaps, the run produced
fewer real rows rather than manufactured observations.

---

## 5. HDD reuse

**HDD was not re-run.** Zero HDD entries appear in the execution ledger.

| Item | Value |
|---|---|
| Source | `v6_17_full_multimetric_productive_artifact_generation/forecast_viewer_model_outputs_v2_full.parquet` |
| Series | 50 (46 unique keys) |
| Models | 15 |
| Rows reused | **204,300** |
| Recomputed | **NO** — predicted and actual values carried verbatim |
| Join grain | `metric + scenario + granularity + series_key` |
| Rows removed by dedup | **0** |
| Horizon rows recomputed | **0** |
| `source_generation_status` | `REUSED_HDD_EXISTING_ARTIFACT` |

**The join deliberately uses the full route grain, never `key` alone.** Four HDD cohort keys
(`APC-MSIT`, `CAN-Go Local`, `EURP309`, `ITA-Go Local`) appear under two routes each, so a
key-only join would cross-match distinct series. That is the exact defect that produced a false
FAIL in P4's first audit; the lesson carried forward.

Two HDD fields are honestly empty rather than invented: `train_start_date` is null and
`burn_in_count` is `-1`, because the source artifact never recorded them. Both are marked
`NOT_PRESENT_IN_SOURCE` in the schema report and in every HDD row's caveat.

---

## 6. Model catalog

All **15 governed models** cover all **140 series**. Zero prohibited models.

| Family | Models |
|---|---|
| Baseline (7) | FixedGrowth_1_5/_3/_4/_6, ARIMA_Fixed, ETS_Current, LinearRegression |
| Challenger (5) | AutoARIMA, **ETS Explicit**, Theta, LightGBM, XGBoost |
| Neural (3) | FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN |

`ETS Explicit` is written **with a space** per decision D3, so the generated rows union cleanly
with the reused HDD rows. It was mapped explicitly, never substituted.

`NBEATS`, `NHITS` and `FastNeuralAR_MLP` confirmed absent — 0 rows.

Determinism: every stochastic model is seeded with `RANDOM_SEED = 42`, and SMLP-TCN uses pooled
global models built once per origin index across all 90 series, matching the HDD reference.
Re-running P5 on the same inputs reproduces the same predictions.

---

## 7. Three things worth carrying into P6

**P5-DQ03 — backtest density is not uniform.** HDD averages 4,086 rows per series, SSD 4,500,
CPU 4,496, IOPS 4,749. Accuracy averages would therefore be computed over different row counts
per metric. Not an error, but **P6 should report per-series accuracy first and aggregate second**,
so density does not silently drive the ranking (P5-UQ02).

**P5-DQ02 — reused HDD rows lack training-window provenance.** Fine for accuracy, which needs
actual, predicted, target_date and horizon. Relevant only if P6 wants to compare training-window
length across metrics.

**P5-DQ04 — LinearRegression emitted ill-conditioned matrix warnings** on gappy IOPS series,
carried over from the smoke test. All 614,190 predictions are finite and 0 are NaN, so nothing is
blocked — but it points at near-collinear lag features on sparse series. Worth a look if
LinearRegression accuracy looks anomalous in P6.

---

## 8. Governance

| Constraint | Observed |
|---|---|
| No SQL | 0 queries |
| Raw Parquet untouched | Read only |
| `actuals_normalized` / `cohort_manifest` untouched | Read only |
| HDD not re-run | 0 HDD entries in the execution ledger |
| No forward forecasts | None. All target dates are observed historical dates |
| No `forecast_outputs` | 0 files |
| No `accuracy_metrics` | 0 files |
| No `model_rankings` | 0 files |
| No `navigation_contract` | 0 files |
| No `taxonomy_counts` | 0 files |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |

**Promotion was gated.** All 14 promotion conditions were evaluated before writing anything to
`processed/`. Had any failed, the checkpoints would have stayed in `work/` and nothing would have
been promoted.

---

## 9. Artifacts

**Processed** — `V6/data/processed/v6_24_mvp_cohort/`

| Artifact | Rows |
|---|---:|
| `model_backtests_15_models.parquet` | **614,190** |
| `model_backtests_15_models.csv` | 614,190 |

**Reports** — `V6/outputs/v6_24_p5_15_model_backtest_generation/`

| File | Rows |
|---|---:|
| `v6_24_p5_reduced_status_table.csv` | 7 |
| `v6_24_p5_preflight_check.csv` | 8 |
| `v6_24_p5_progress_log.csv` | 11 |
| `v6_24_p5_execution_ledger.csv` | **1,350** |
| `v6_24_p5_batch_runtime_ledger.csv` | 27 |
| `v6_24_p5_model_series_completion_matrix.csv` | 5 |
| `v6_24_p5_failure_ledger.csv` | **0** |
| `v6_24_p5_output_schema_report.csv` | 26 |
| `v6_24_p5_date_alignment_validation.csv` | 5 |
| `v6_24_p5_actual_value_reconciliation.csv` | 4 |
| `v6_24_p5_no_invented_dates_validation.csv` | **90** |
| `v6_24_p5_hdd_reuse_mapping.csv` | 1 |
| `v6_24_p5_prediction_row_count_summary.csv` | 5 |
| `v6_24_p5_model_catalog_validation.csv` | 18 |
| `v6_24_p5_budget_report.csv` | 4 |
| `v6_24_p5_promotion_gate.csv` | 14 |
| `v6_24_p5_data_quality_report.csv` | 5 |
| `v6_24_p5_unresolved_questions.csv` | 3 |
| `v6_24_p5_validation.csv` | 42 |
| `v6_24_p5_closure_summary.md` | — |

**Work** — `V6/data/model_runs/v6_24_p5_work/`: 27 batch checkpoints, batch ledger, failure
ledger, run log.

---

## 10. Cohort readiness after P5

| Metric | Actuals | 15 backtests | Forecast | Viewer-ready |
|---|---|---|---|---|
| HDD | ✅ | ✅ | ✅ | ✅ |
| SSD | ✅ | **✅ new** | ❌ P6 | After P6/P7 |
| CPU | ✅ | **✅ new** | ❌ P6 | After P6/P7 |
| IOPS | ✅ | **✅ new** | ❌ P6 | After P6/P7 |

**All 140 series now have actuals and 15 governed backtests.** The remaining gap is forward
forecast for the 90 non-HDD series.

`cohort_manifest.has_15_model_backtests` still reads FALSE for those 90 — P4 wrote it and P5 is
forbidden from modifying the manifest. **P6 or P7 must update that flag**, or the completeness
gate will under-report what actually exists.

---

## 11. Next stage

**P6 — Forecast Generation.** Forward forecasts for the 90 non-HDD series, then
`accuracy_metrics` and `model_rankings`. Three open questions are logged; none blocks P6.

---

**V6_24_P5_15_MODEL_BACKTEST_GENERATION_COMPLETED**

Stopping here. P6 not started, no forward forecasts generated, no accuracy calculated, no
rankings calculated, no `navigation_contract`, no `taxonomy_counts`, Shiny untouched, no push.
