# V6.24-P5A — Backtest Execution Plan / Budget / Window Contract

> ## AMENDMENT — D2 APPROVED 2026-08-23
>
> The owner approved **D2 = Option B**, recorded as
> **`V6_24_P5_WINDOW_POLICY_D2_OPTION_B`** in
> `v6_24_p5a_owner_approved_p5_window_policy.csv` (8 rules).
>
> **R01 is CLOSED.** The window contract was recomputed under the approved rule:
>
> | Measure | Strict contiguity | **D2 Option B** |
> |---|---:|---:|
> | Series preserving their newest observation | 68 of 90 | **90 of 90** |
> | IOPS valid origins per series | 5–6 | **10–11** |
> | IOPS last backtest target | ~2022-12-26 | **2023-07-20** |
> | Total target dates | 24,000 | **27,326** |
> | Prediction rows | 360,000 | **409,890** |
> | Origin-level fits | 12,000 | **13,740** |
>
> The seven-month IOPS recency gap is gone. **No date was filled, resampled or
> interpolated** — the rule accepts fewer *real* targets rather than manufacturing any.
> The +14% workload stays far inside the 2-hour budget.
>
> **P5 is no longer blocked. It is ready to run on the formal P5 prompt.**
> Sections 4 and 9 below describe the pre-approval state and are retained as audit history.
> The binding contract is `v6_24_p5a_backtest_window_contract_D2_APPROVED.csv`.

---

**Stage:** V6.24-P5A — planning and control
**Status:** **COMPLETED.**
**P5 readiness:** **READY. D2 approved; awaiting the formal P5 prompt.**
**Models run:** none. No product artifact created.

---

## 1. Bottom line

The plan is complete and the workload is comfortable. But measuring the real cohort surfaced
**two findings that would have damaged P5 if it had simply run**. Neither is a reason to stop —
one needs a decision, the other needs a code change.

| # | Finding | Severity |
|---|---|---|
| **R01** | **All 20 IOPS series would stop backtesting around December 2022**, seven months short of their newest actuals | **HIGH — needs decision D2** |
| **R02** | The reference generator **raises** on a gappy test window instead of skipping it | **HIGH — needs a code change, no decision** |

---

## 2. Workload

| Metric | Series | Models | Model-series runs | Valid origins/series | Target dates | Prediction rows |
|---|---:|---:|---:|---|---:|---:|
| SSD | 50 | 15 | 750 | 10 of 11 | 15,000 | 225,000 |
| CPU | 20 | 15 | 300 | 8–10 of 11 | 5,880 | 88,200 |
| IOPS | 20 | 15 | 300 | 5–6 of 11 | 3,120 | 46,800 |
| **New in P5** | **90** | **15** | **1,350** | | **24,000** | **360,000** |
| HDD | 50 | 15 | **750 — REUSE ONLY, not re-run** | | | |
| **Final coverage** | **140** | **15** | **2,100** | | | |

Roughly 90 MB uncompressed. Volume is not a risk.

---

## 3. Backtest window contract

Derived by reading the actual generator, not by inventing a policy.

```
LAGS = 30, HORIZON_DAYS = 30
first_origin = min_date + 64 days        <- burn-in is LEFT-SIDE ONLY
last_origin  = max_date - 30 days
11 origins sampled evenly between them
training = date <= origin
test     = origin < date <= origin + 30
```

**The newest data is never burned.** The last origin sits exactly 30 days before the series
maximum, so the final target date *is* the series maximum. Burn-in consumes only the oldest
observations. This was verified against the HDD artifact: 4,915 series-origins × 15 models × 30
horizon days = **2,211,750 rows**, which matches the R6P1 lineage row count exactly.

**Invariants enforced on every output row:**

| Invariant | Purpose |
|---|---|
| `prediction_date = target_date` | No visual offset between actual and estimate |
| `train_end_date < target_date` | No leakage of future actuals |
| `actual_value` joined from `actuals_normalized` | Never recomputed |
| `1 <= horizon_steps <= 30` | Alignment sanity |

---

## 4. R01 — the finding that matters

**Measured, per series:**

| Metric | Calendar gaps | Valid origins (of 11) | Newest observation preserved |
|---|---|---:|---|
| SSD | 2 | 10 | **50 of 50** |
| CPU | 1–7 | 8–10 | **18 of 20** |
| IOPS | **8–23** | **5–6** | **0 of 20** |

The reference policy demands a test window of **exactly 30 contiguous days**. IOPS series carry
8–23 missing calendar days, so the later origins fail that test and get dropped. The consequence:

> `IOPS__Consumed__Region__APC-Multitenant` — actuals run to **2023-07-20**, but the last
> backtest target would be **2022-12-26**.

**About seven months of the most recent IOPS history would never be validated.** That directly
contradicts the owner's core rule that the newest observations must be preserved for
backtesting. It is not tail-trimming by design — it is a **gap side-effect** — but the product
consequence is identical.

I did not patch this. It changes backtest semantics, so it belongs to the owner as **D2**.

**Recommended: option B.** Replace "exactly 30 contiguous days" with "at least 20 observations
inside the 30-day window", and always force a final origin at `max_date - 30`.

Why not the alternatives: option A leaves IOPS seven months stale. Option C — resampling to a
daily grid — is **forbidden**, because it means filling dates, which P4 explicitly refused to do
and P5 must not do either. Option B preserves recency **without inventing a single observation**.

---

## 5. R02 — the reference code cannot be reused unmodified

```python
# run_v6_17_viewer_backtests.py, training_and_test()
if len(training) < LAGS + HORIZON_DAYS + 5 or len(test) != HORIZON_DAYS:
    raise ValueError(...)
```

It **raises**, it does not skip. HDD has **zero** calendar gaps, so this never fired. SSD, CPU
and IOPS all have gaps, so P5 would crash on its first gappy origin.

**Fix:** pre-filter origins using `v6_24_p5a_backtest_window_contract.csv`, which already lists
`valid_origin_count` per series, and wrap origin evaluation in the failure policy. No decision
needed — this is straightforward engineering, but it had to be found before the run, not during.

---

## 6. Model catalog

**All 15 governed models resolve to executable implementations.** Import-only check passed.

| Family | Count | Models | Cost |
|---|---:|---|---|
| Baseline | 7 | FixedGrowth_1_5/_3/_4/_6, ARIMA_Fixed, ETS_Current, LinearRegression | LOW |
| Challenger | 5 | AutoARIMA, ETS Explicit, Theta, LightGBM, XGBoost | MEDIUM |
| Neural | 3 | FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN | HIGH |

Prohibited models (`NBEATS`, `NHITS`, `FastNeuralAR_MLP`) confirmed **absent** from the registry.

**One naming discrepancy (R03).** The governed catalog spells the champion `ETS_Explicit`; the
code and the HDD artifact both use **`ETS Explicit` with a space**. Same model. P5 must map
explicitly and write the space form so its output unions cleanly with HDD. **Not substituted
silently** — recorded in the catalog contract.

Dependencies all import: numpy 2.4.6, pandas 3.0.3, sklearn 1.9.0, statsmodels 0.14.6,
lightgbm 4.6.0, xgboost 3.2.0, pmdarima 2.1.1, pyarrow 25.0.1.

---

## 7. Budget and batching

| Budget | Minutes | Behavior |
|---|---:|---|
| Hard wall clock | **120** | Stop cleanly, write the failure ledger |
| Soft stop | **105** | Finish the current batch, checkpoint, stop |
| Finalization | **15** | Validate and promote |

**Expected actual runtime: roughly 20–40 minutes.** Calibrated against the HDD reference, which
completed 73,725 fits inside a 4-hour budget. P5 needs **12,000** origin-level fits, about 16% of
that. The 2-hour budget carries a wide margin.

**27 batches**, two phases:

| Phase | Models | Batch size | Risk |
|---|---|---:|---|
| A — non-neural | 12 | 10 series | LOW |
| B — neural | 3 | 5 series | HIGH, isolated |

Phase A runs first so a budget overrun cannot cost the cheap models. This mirrors the HDD
reference structure.

```
V6/data/model_runs/v6_24_p5_work/
  checkpoints/  logs/  failures/  temp_outputs/  runtime_ledger/
```

**Partial results stay in `work/` and are never promoted to `processed/`.** Shiny must never read
that folder. Promotion happens only after P5 validation passes.

---

## 8. Failure policy

Eight failure classes, all with the same spine: **record it, never disguise it**.

- No model substitution without owner approval.
- **No silent NaN predictions** — a failed unit produces no row, and the failure ledger shows it.
- No silently dropped series.
- Every failure records `series_id, model_name, metric, error_type, error_message, timestamp,
  batch_id, origin_date`.

**The most important check is `DATE_ALIGNMENT_FAILURE`.** After every batch, predictions are
joined back to `actuals_normalized` on `(series_id, target_date)` and the actual must match
exactly. A one-day offset would be invisible and would make every accuracy number in P6 wrong
while looking entirely plausible.

---

## 9. Owner decisions

| ID | Decision | Recommendation | Blocks P5 |
|---|---|---|---|
| **D2** | **Non-contiguous test windows** | **B: minimum 20 observations in the window, plus a forced origin at `max_date - 30`** | **YES** |
| D1 | Origins per series | A: 11, matching HDD | No |
| D3 | Champion name spelling | A: keep `ETS Explicit` with a space | No |
| D4 | Behavior on model failure | A: mark the run incomplete | No |
| D5 | Re-run HDD? | A: reuse, do not re-run | No |

**Only D2 blocks.** Without it, P5 will run successfully and produce a cohort whose IOPS
backtests silently stop seven months early.

---

## 10. Deliverables

| File | Rows |
|---|---:|
| `v6_24_p5a_reduced_status_table.csv` | 7 |
| `v6_24_p5a_model_catalog_contract.csv` | 18 |
| `v6_24_p5a_workload_estimate.csv` | 6 |
| `v6_24_p5a_backtest_window_contract.csv` | **140** |
| `v6_24_p5a_hdd_backtest_schema_mapping.csv` | 3 |
| `v6_24_p5a_execution_budget_plan.csv` | 3 |
| `v6_24_p5a_batch_checkpoint_plan.csv` | 27 |
| `v6_24_p5a_failure_policy.csv` | 8 |
| `v6_24_p5a_model_backtest_output_schema_contract.csv` | 25 |
| `v6_24_p5a_runtime_risk_register.csv` | 8 |
| `v6_24_p5a_owner_decisions_before_p5.csv` | 5 |
| `v6_24_p5a_dependency_check.csv` | 8 |
| `v6_24_p5a_dry_run_readiness_check.csv` | 7 |
| `v6_24_p5a_validation.csv` | — |
| `v6_24_p5a_closure_summary.md` | — |

---

## 11. Governance

| Constraint | Observed |
|---|---|
| No full model generation | Only an import-only registry check. Zero fits |
| No `model_backtests_15_models` artifact | Not created |
| No forecasts, accuracy or rankings | None |
| P4 processed artifacts untouched | Read only |
| Raw Parquet untouched | Read only |
| No SQL | 0 queries |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |

---

## 12. Next step

**P5 is ready to execute once D2 is answered.** Confirm the test-window rule and P5 can run
1,350 model-series runs inside the 2-hour budget, with an expected actual runtime of 20–40
minutes.

---

**V6_24_P5A_BACKTEST_EXECUTION_PLAN_BUDGET_WINDOW_CONTRACT_COMPLETED**

Stopping here. Full P5 not started, no models run, no backtest artifact generated, no forecasts,
no accuracy or rankings, Shiny untouched, no push.
