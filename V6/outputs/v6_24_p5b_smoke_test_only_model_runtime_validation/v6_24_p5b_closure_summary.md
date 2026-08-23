# V6.24-P5B — Smoke Test Only / Model Runtime Validation

**Stage:** V6.24-P5B — smoke test only
**Result:** **PASS.** 45 of 45 model-series attempts succeeded, 0 failures.
**Runtime:** **13.4 seconds** against a 900-second budget (1.5%).
**Full P5 verdict:** **READY.**

Nothing was promoted to `processed/`. The 90-series workload was not started.

---

## 1. What ran

| Metric | Series | Rows in actuals | Origins | Models | Prediction rows | Runtime | Result |
|---|---|---:|---:|---:|---:|---:|---|
| SSD | `SSD__Phoenix__Forest__NAMPRD08` | 130 | 10 | 15 | 4,500 | 3.76s | **PASS** |
| CPU | `CPU__Consumed__Region__CHN-Gallatin` | 556 | 10 | 15 | 4,455 | 4.02s | **PASS** |
| IOPS | `IOPS__Consumed__Region__APC-Multitenant` | 1,103 | 11 | 15 | 4,845 | 4.66s | **PASS** |
| **Total** | **3** | | **31** | **15** | **13,800** | **13.4s** | **PASS** |

All three preferred series were present in the cohort, so no substitution was needed. These are
the hardest cases by design: NAMPRD08 is the AX4 dashboard reference key, CHN-Gallatin is the
shortest CPU series, and APC-Multitenant is the gappiest IOPS series with 20 missing calendar
days.

---

## 2. The checks that actually matter

| Check | Expected | Observed |
|---|---|---|
| `prediction_date` equals `target_date` | 0 offsets | **0 of 13,800** |
| `train_end_date` < `target_date` | 0 violations | **0** |
| `horizon_steps` equals `target_date − train_end_date` | 0 mismatches | **0** |
| `actual_value` matches `actuals_normalized` | 0 mismatches | **0**, max delta **0.0** |
| Every `target_date` exists in `actuals_normalized` | 0 orphans | **0** |
| **Invented dates** | **0** | **0** |
| Duplicate series/model/target/origin rows | 0 | **0** |
| NaN predictions | 0 | **0** |

The reconciliation is independent: the validator re-joins every backtest row back to
`actuals_normalized` on `(series_id, target_date)` rather than trusting the runner that wrote it.
**Maximum absolute delta is exactly 0.0** — the actuals were joined, never recomputed.

---

## 3. D2 sparse-observed policy works as approved

**No date was invented.** A model still forecasts 30 steps from each origin, but a row is emitted
only when that target date exists in `actuals_normalized`. Predictions landing on unobserved
calendar days are discarded, never written.

The evidence is in the per-origin row counts:

| Metric | Rows per origin per model | Interpretation |
|---|---|---|
| SSD | **30 of 30** | Windows fully contiguous |
| CPU | **28–30** | Gaps drop 0–2 steps |
| IOPS | **28–30** | Gaps drop 0–2 steps |

Fewer real rows where the calendar has holes, rather than manufactured observations to fill them.

**And the recency rule holds.** All three series reach their newest observation:

| Series | Max observed | Max backtest target | Reached |
|---|---|---|---|
| SSD NAMPRD08 | 2026-08-22 | **2026-08-22** | ✅ |
| CPU CHN-Gallatin | 2023-07-20 | **2023-07-20** | ✅ |
| IOPS APC-Multitenant | 2023-07-20 | **2023-07-20** | ✅ |

That last row is the point of the whole D2 amendment. Under the old strict-contiguity rule this
series would have stopped at **2022-12-26**, seven months short. It now reaches 2023-07-20 with
11 valid origins instead of 5.

Burn-in behaved correctly: `train_start_date` equals each series' minimum date, so warm-up
consumed only the oldest observations.

---

## 4. Model catalog

All **15 governed models** produced rows for all 3 series. Zero failures.

| Family | Models | Status |
|---|---|---|
| Baseline (7) | FixedGrowth_1_5/_3/_4/_6, ARIMA_Fixed, ETS_Current, LinearRegression | OK |
| Challenger (5) | AutoARIMA, **ETS Explicit**, Theta, LightGBM, XGBoost | OK |
| Neural (3) | FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN | OK |

`ETS Explicit` is written **with a space**, matching the existing HDD artifact, per decision D3.
It was mapped explicitly, never substituted.

Prohibited models (`NBEATS`, `NHITS`, `FastNeuralAR_MLP`) confirmed absent — 0 rows.

The neural models were the cheapest surprise of the run: FNAR-V2 at ~1.3s per series and
SMLP-TCN at ~0.02s, because SMLP-TCN reuses pooled global models built once per origin index,
exactly as the HDD reference does.

---

## 5. Implications for the full run

Measured smoke throughput: **13,800 rows in 13.4 seconds**, i.e. 3 series × 15 models × ~10
origins = **465 fits in 13.4s**, about **35 fits per second**.

The full P5 workload is **13,740 origin-level fits**. At the observed rate that is roughly
**7 minutes**, well inside the 105-minute soft stop. The 2-hour budget carries a very wide
margin.

One caveat on that extrapolation: the smoke series are three of the shorter ones, and fit cost
grows with training length. Even at five times slower the full run lands near 35 minutes.

---

## 6. Three observations worth carrying forward

**P5B-UQ03 — numerical warnings.** `LinearRegression` emitted *ill-conditioned matrix* warnings
on IOPS (`rcond ≈ 1e-16`), and LightGBM emitted feature-name warnings. Every prediction was
finite and passed validation, so nothing is blocked. But ill-conditioning points at near-collinear
lag features on the gappier series. Worth a look if LinearRegression accuracy looks anomalous in
P6 — flagged rather than buried.

**P5B-UQ01 — sparse emission is not logged step-by-step.** When a window has gaps, the discarded
forecast steps are not individually recorded. The count is derivable from the `horizon_steps`
present, so a per-step ledger would multiply the output for no analytic gain.

**P5B-UQ02 — runtime is attributed per (series, model)**, aggregated across origins, not per
individual fit. Adequate for budgeting, not a per-fit profile.

None of the three blocks the full run.

---

## 7. Governance

| Constraint | Observed |
|---|---|
| Only the smoke test ran | 3 series, 45 model-series attempts |
| Full P5 not started | No 90-series run |
| `model_backtests_15_models` not created | **0 files** in `processed/` |
| Nothing promoted to processed | `processed/` unchanged at **8 files** |
| No forecast, accuracy, ranking, navigation or taxonomy artifacts | None |
| HDD not run | 0 HDD rows |
| No SQL | 0 queries |
| Raw Parquet untouched | Read only |
| `actuals_normalized` / `cohort_manifest` untouched | Read only |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |

Smoke output lives only in
`V6/data/model_runs/v6_24_p5_work/smoke_test/` and this report folder.

---

## 8. Artifacts

| Artifact | Rows | Purpose |
|---|---:|---|
| `v6_24_p5b_smoke_test_backtest_sample.parquet` / `.csv` | **13,800** | Full smoke output in the P5 schema |
| `v6_24_p5b_smoke_test_results.csv` | 3 | Per-series result |
| `v6_24_p5b_date_alignment_validation.csv` | 5 | Alignment invariants |
| `v6_24_p5b_actual_value_reconciliation.csv` | 4 | Independent join against actuals |
| `v6_24_p5b_no_invented_dates_validation.csv` | 3 | Per-series proof of zero invented dates |
| `v6_24_p5b_model_catalog_validation.csv` | 18 | 15 governed + 3 prohibited |
| `v6_24_p5b_output_schema_report.csv` | 26 | Column-by-column schema conformance |
| `v6_24_p5b_runtime_summary.csv` | 10 | Runtime by family |
| `v6_24_p5b_failure_ledger.csv` | **0** | Empty by design; the file exists |
| `v6_24_p5b_smoke_series_selection.csv` | 3 | Selection with reasons |
| `v6_24_p5b_preflight_check.csv` | 7 | Input availability |
| `v6_24_p5b_reduced_status_table.csv` | 7 | Stage status |
| `v6_24_p5b_unresolved_questions.csv` | 3 | Open items, none blocking |
| `v6_24_p5b_validation.csv` | 35 | All checks |
| `v6_24_p5b_closure_summary.md` | — | This file |

Work artifacts: `smoke_checkpoint.parquet`, `smoke_runtime_ledger.csv`,
`smoke_failure_ledger.csv` under `data/model_runs/v6_24_p5_work/smoke_test/`.

---

## 9. Verdict

**Full P5 is READY.**

The 15 models run, the D2 window policy behaves exactly as approved, predictions align to actuals
with zero drift, no dates are invented, the newest observations are preserved, and the schema
matches the P5 contract. Runtime is a small fraction of the budget.

Awaiting the formal V6.24-P5 prompt to run the 90-series workload.

---

**V6_24_P5B_SMOKE_TEST_ONLY_MODEL_RUNTIME_VALIDATION_COMPLETED**

Stopping here. Full P5 not started, no 90-series workload run, no final
`model_backtests_15_models` created, nothing promoted to processed, no forecasts, no accuracy, no
rankings, no navigation_contract, no taxonomy_counts, Shiny untouched, no push.
