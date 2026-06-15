# Stage 5 Pre-Training Audit — AEGIS / TESSERACT Forecast Generation Platform

**Reviewer role:** Principal Forecasting Architect / Principal ML Engineer / Principal MLOps Engineer
**Scope:** Independent pre-training review of Stage 5 (Model Lab) before block 5.9 (Baseline Production Models Execution).
**Mode:** Review only. No code changed, no models trained, no forecasts generated, no configs altered.
**Audit date:** 2026-06-11

---

## 1. Executive Summary

The platform's *temporal foundations are sound*. Walk-forward windows are constructed correctly (train strictly precedes test, test horizon is exactly 30 days, test windows are non-overlapping and contained within actuals). The lag/rolling feature engineering is genuinely leakage-safe — I verified this empirically against `feature_dataset.csv`, not just by reading code. The execution guard is a real double-gate and currently prevents any accidental training run.

However, the platform is **not yet methodologically complete for the stated goal of "fair model tournaments."** The entire scoring/evaluation layer that 5.9 depends on is either unimplemented or under-specified, and in its current designed form the composite score is **mathematically invalid** (it sums scale-dependent and scale-independent metrics without normalization, and treats signed bias as if lower-is-better). Several execution-time behaviours required to even run the baseline `LinearRegression` model (multi-step lag population, NaN feature handling) are unspecified. Run history is overwritten rather than appended, undermining MLOps auditability. There are zero automated tests.

You can safely proceed to **implement and run baseline forecast generation**, but the **tournament/ranking outputs must not be trusted** until the metric fixes below land. Verdict: **APPROVED WITH CHANGES**.

---

## 2. Architecture Review

**Strengths**
- Clean separation of stages: window generation → feature build → orchestration (plan) → manifest → guarded entry point → contract design. Each script is single-purpose and idempotent.
- `ForecastModel` ABC (`base_model.py`) enforces a uniform `fit / predict / get_model_name / get_model_family / validate_input` contract. Registry (`model_registry.py`) is simple, explicit, and validates subclass typing on registration.
- Inputs are loaded from a single canonical source (`outputs/evaluation/evaluation_dataset.csv`), keeping windows and features consistent.
- Config-driven (`config/*.yaml`), with a PyYAML loader plus a safe fallback parser.

**Weaknesses**
- **Data-source ambiguity per model.** Univariate baselines (`ARIMA_Fixed`, `ETS_Current`, `FixedGrowth_*`) operate on the raw target series and do **not** need `feature_dataset.csv`, yet the orchestrator counts feature rows for them and the contract implies a single dataset feeds all models. There is no declared mapping of "which model consumes which data contract." This will cause confusion and silent mistakes in 5.9.
- The `predict(horizon, future_data=None)` signature does not distinguish recursive vs direct multi-step forecasting, nor how exogenous/lag features are supplied across a 30-day horizon. This is the single biggest architectural gap before any feature-consuming model runs.
- The fallback YAML parser only supports one level of nesting. It is adequate for today's flat configs but is a latent trap if configs ever gain structure.

---

## 3. Forecasting Methodology Review

**Strengths**
- Walk-forward / expanding-window design is appropriate for production time-series backtesting.
- Horizon (30d), minimum train (365 obs) and minimum test (30 obs) thresholds are sensible and enforced.

**Concerns**
- **`ARIMA_Fixed` = ARIMA(0,2,0).** Double differencing with no AR/MA terms is a pure second-difference random walk; its 30-day forecast is a straight-line extrapolation of the local slope and is prone to explosive/implausible trajectories. This is acceptable *only* as a faithful reproduction of current TESSERACT behaviour — it must not be presented as a defensible model. Document it as a "reproduction baseline," not a recommendation.
- **`ETS_Current` seasonality is unspecified.** Daily data with a 30-day horizon needs an explicit decision on trend/seasonal components and seasonal period. "Current ExponentialSmoothing baseline" is not a reproducible spec.
- **No final lock-box / hold-out separation.** All 454 windows are used both to evaluate and (later) to select the tournament winner. Selecting the best model on the same windows used to score it introduces optimistic selection bias. Consider reserving the most recent N windows as a final, untouched evaluation set.
- **Expanding-window only.** There is no rolling fixed-window option to test recency sensitivity. Optional, but worth noting for models whose behaviour drifts with training-set length.

---

## 4. Backtesting Integrity Review

**Verified correct (empirically, from `backtesting_windows.csv`):**
- `train_end_date` is always the day before `test_start_date` — no train/test overlap.
- Test horizon is exactly 30 days for every window (`_validate_windows` enforces it).
- Test windows step back by exactly 30 days and **do not overlap** each other.
- All test windows fall within available actuals (latest actual 2026-04-27 = most recent window's `test_end_date`); **no forecasting into a period without ground truth**.
- Window IDs are stable (most recent = highest id) and counts reconcile: 39 entities, 454 windows, 6,356 planned jobs = 454 × 14 models. ✔

**Residual risks**
- **Gap blindness.** Windows are validated by *observation count*, not calendar continuity. An entity with internal date gaps could pass the 365/30 thresholds while having a sparse or discontinuous series. Add a contiguity/gap check before training.
- The 365-observation minimum is effectively never binding given multi-year histories (oldest window already has ~2,100+ train obs). The ~14 missing windows (468 − 454) come from shorter-history entities; confirm those entities are intentionally short and not truncated by a data bug.

**Temporal leakage verdict: SAFE.**

---

## 5. Feature Engineering Review

**Verified leakage-safe (empirically):**
- Lag features use `groupby(entity).shift(lag)` — strictly backward. Confirmed: `lag_7` on 2019-07-08 equals the 2019-07-01 value.
- Rolling features apply `shift(1)` *before* rolling, with `min_periods=window`, so the current row is excluded and no partial-window values are emitted. Confirmed: `rolling_mean_7` on 2019-07-08 = mean of 07-01…07-07.
- Calendar features are deterministic functions of the date — no leakage.

**Look-ahead bias verdict: SAFE for the dataset as written.**

**But — critical execution-time gaps (not leakage, but blocking):**
- **Multi-step lag availability.** For a 30-day horizon, `lag_1/lag_7/lag_14` are not known beyond the first few horizon days unless the model recursively feeds its own predictions back in (or uses direct multi-horizon models). The feature contract and the 5.8 execution contract are **silent** on this. This directly affects the baseline `LinearRegression` (`lags=30`) and every ML challenger. Without a defined strategy, 5.9 will either crash on missing features or silently leak future actuals at predict time.
- **NaN handling.** The first 90 rows per entity have NaN lags (and NaN rolling until `min_periods` is met). No declared imputation/drop policy. Models must not be fed NaNs nor silently drop early training rows in an inconsistent way.
- **`year` as a raw numeric feature.** Tree models (LightGBM/XGBoost) cannot extrapolate beyond training-year ranges; raw `year` invites train/serve skew. Prefer cyclical/relative encodings. (Challenger concern, not a 5.9 blocker.)

---

## 6. Model Registry Review

**Strengths**
- All 14 models are registered, typed against `ForecastModel`, and grouped into coherent families (`BaselineProduction`, `Statistical`, `MachineLearning`, `DeepLearning`).
- `model_metadata.py` cleanly documents capabilities (multivariate/exogenous/probabilistic). Registry and metadata names are consistent.
- Registry is the single source of truth used by the orchestrator and manifest; counts reconcile end-to-end.

**Concerns**
- Every model is a `NotImplementedError` placeholder. Expected at this stage, but means 5.9 is implementation *and* execution, not just execution.
- Metadata is a separate hand-maintained list from the classes; they can drift. Consider deriving capability flags from the classes or adding a test that asserts parity. (No tests currently exist to catch drift.)
- `LinearRegression` metadata claims `supports_exogenous = True` but no exogenous contract is defined. Reconcile before relying on it.

**Registry design verdict: correct and sufficient for both baseline and challenger models.**

---

## 7. Execution / MLOps Review

**Strengths**
- **Strong double-gate.** `run_model_lab.py` blocks when `training_enabled` is false (`blocked_by_config`), blocks again when `dry_run` is true (`dry_run_only`), and even with both flipped raises `NotImplementedError`. Three independent barriers — accidental training is effectively impossible today.
- Manifest cross-check: execution refuses to proceed if `manifest.planned_jobs` ≠ live job-plan length.
- Current audit state is correct: `blocked_by_config`, 0 executed, 6,356 skipped.

**Critical / High MLOps gaps**
- **Run history is overwritten, not appended.** `run_manifest.csv`, `run_metadata.csv`, and `execution_audit.csv` are written with `to_csv(...)` (single row, no append). Every run clobbers the previous one. This directly contradicts the 5.8 contract requirement that "logs must be sufficient to reconstruct job-level execution history." For an auditable platform this is a real defect.
- **No input fingerprinting.** The manifest records job counts but no hash/version of `evaluation_dataset.csv`, `feature_dataset.csv`, `backtesting_windows.csv`, or config files. A silent change to inputs would not be detected, breaking reproducibility guarantees.
- **No random-seed / determinism policy.** LightGBM/XGBoost/NBEATS/NHITS are non-deterministic without seeds. Not a 5.9 baseline blocker, but required before any challenger tournament is called "fair."
- Minor inconsistency: `create_run_manifest.py` reads `execution_config["training_enabled"]` (KeyError on absence) while `run_model_lab.py` uses `.get(..., False)`. Both fail safe, but standardize.
- `tests/` is **empty.** There is no automated regression protection for window correctness, leakage-safety, or guard behaviour. The `validate_*.py` scripts are manual checks, not a test suite.

---

## 8. Metrics and Tournament Review

This is the weakest area and the primary reason ranking outputs cannot yet be trusted.

- **Composite score is mathematically invalid as designed.** `scoring_weights.yaml` does a raw weighted sum of `wmape, mape, rmse, bias, stability, horizon`. RMSE is **scale-dependent and unbounded**; wMAPE/MAPE/SMAPE are scale-free ratios. Summing them with fixed weights means RMSE (and therefore high-volume entities) dominates the score arbitrarily. Metrics **must be normalized** (e.g., per-entity min-max or rank-based, or scaled RMSE such as RMSSE) before any weighted composite. Weights do sum to 1.00 — that is the only thing currently correct about the composite.
- **Bias is signed but treated as lower-is-better.** A model that under-forecasts (negative bias) would improve the composite if summed raw. Use `|bias|` or a symmetric penalty.
- **`stability_score` and `horizon_score` are undefined.** They appear in the metrics schema with prose descriptions only — no formula in config or contract. You cannot rank on metrics that have no definition.
- **Zero/near-zero actual handling undefined.** wMAPE and especially MAPE explode or divide-by-zero when actuals are 0 or tiny. No epsilon/flooring policy is specified anywhere.
- **SMAPE is computed but unused** in the composite (it's in `metrics_output_schema.csv` but absent from `scoring_weights.yaml`). Meanwhile wMAPE + MAPE are highly collinear, effectively double-counting percentage error. Decide on one or two non-redundant percentage metrics.
- `tournament.yaml` (`top_n_models: 10`, future horizons 5/10/30/90) is reasonable, but `generate_forecasts: true` over 5/10/30/90 horizons multiplies output volume — confirm storage/runtime budget given 6,356 jobs.

**Output contracts (5.8):** the forecast/metrics/tournament schemas in `contracts/` are well-structured and lineage-aware (run_id/job_id/entity/model/window). They are *structurally* sufficient. They are *semantically* insufficient because they reference scores (`stability_score`, `horizon_score`, `composite_score`) that have no agreed definition.

---

## 9. Critical Risks

1. **Invalid composite scoring** — summing unnormalized scale-dependent (RMSE) and scale-free (wMAPE/MAPE) metrics; RMSE/high-volume entities will dominate rankings. Any tournament result is currently meaningless.
2. **Undefined metrics** — `stability_score` and `horizon_score` have no formula; ranking cannot be computed reproducibly.
3. **Unspecified multi-step forecasting / lag population** for the 30-day horizon — blocks `LinearRegression` and all feature-consuming models; risk of crash or future leakage at predict time.
4. **Zero/near-zero actual handling absent** — MAPE/wMAPE division-by-zero will produce NaN/Inf and corrupt aggregates.
5. **Run history overwritten** — no append-only audit trail; violates the platform's own 5.8 traceability contract.

## 10. High Risks

1. **Signed bias in composite** treated as lower-is-better.
2. **No final hold-out window** — selection bias from scoring and choosing winners on the same windows.
3. **Gap blindness** in window validation (observation count, not calendar continuity).
4. **`ARIMA_Fixed` (0,2,0) instability** over 30 days — acceptable only as a labelled reproduction baseline.
5. **No input fingerprinting / no random seeds** — reproducibility not guaranteed (seeds matter for challengers).
6. **Zero automated tests** — no regression protection for leakage-safety, window correctness, or the execution guard.

## 11. Medium Risks

1. Model→data-contract mapping undefined (univariate baselines don't need `feature_dataset.csv` but the plan treats all models uniformly).
2. NaN feature policy (first ~90 rows per entity) undefined.
3. `year` as raw numeric feature (extrapolation/skew for tree models).
4. SMAPE computed but unused; wMAPE/MAPE redundancy.
5. Config/inconsistency: `.get()` vs `[]` access to execution flags; one-level-only fallback YAML parser.
6. `ETS_Current` seasonal spec not pinned down.
7. `LinearRegression` metadata claims exogenous support with no exogenous contract.

---

## 12. Required Fixes Before 5.9

These must be addressed before baseline execution produces trustworthy, rankable output. Items marked **(forecast-only)** are not needed merely to *generate* baseline forecasts but **are** needed before any metric/tournament output is believed.

1. **Define the metric layer precisely (forecast-only after this):** exact formulas for wMAPE, MAPE, SMAPE, RMSE, bias, `stability_score`, `horizon_score`, including the zero/near-zero actual policy (epsilon or wMAPE-only).
2. **Fix the composite:** normalize all components to a common, lower-is-better, scale-free basis (per-entity min-max, rank, or RMSSE) before weighting; use `|bias|` or a symmetric penalty. Re-validate weights sum (currently 1.00 — keep).
3. **Specify multi-step forecasting** for feature-consuming models (recursive vs direct), and how lag/rolling features are populated across the 30-day horizon without using future actuals. Required for `LinearRegression`.
4. **Define NaN feature handling** (drop vs impute, applied consistently in train and test).
5. **Make run artifacts append-only** (`run_manifest`, `run_metadata`, `execution_audit`) so run history is preserved per `run_id`.
6. **Add a calendar-continuity / gap check** to window validation.
7. **Pin `ETS_Current` and document `ARIMA_Fixed`** explicitly as reproduction baselines with their exact specs.
8. **Add a minimal test suite** asserting: no train/test overlap, 30-day horizon, lag/rolling leakage-safety, and that the guard blocks when `training_enabled=false` or `dry_run=true`.

## 13. Optional Improvements

- Add input fingerprint hashes (data + configs) to the run manifest for reproducibility.
- Reserve a final lock-box window set for unbiased winner selection.
- Add fixed-window (rolling) backtesting as an alternative to expanding-window.
- Replace raw `year` with relative/cyclical encodings for tree/DL models.
- Set and record random seeds for LightGBM/XGBoost/NBEATS/NHITS.
- Derive model metadata from classes (or add a parity test) to prevent drift.
- Confirm storage/runtime budget for 5/10/30/90-day forecast generation across 6,356 jobs.

---

## 14. Final Verdict

**APPROVED WITH CHANGES**

The temporal backbone is correct and the leakage posture is genuinely safe — train/test separation, 30-day horizon, non-overlapping in-sample test windows, and backward-only features are all verified. The execution guard is robust and currently makes accidental training impossible. On those grounds the platform is structurally safe to move toward baseline execution.

It is **not** ready to produce trustworthy *evaluation/tournament* results. The composite score is mathematically invalid as designed, two scored metrics are undefined, zero-actual handling is missing, multi-step lag population is unspecified, and run history is overwritten. Implement the Section 12 fixes first. Concretely:

- `ARIMA_Fixed`, `ETS_Current`, and the `FixedGrowth_*` models (univariate, raw-series) can be implemented and run to *generate forecasts* with low risk once their specs are pinned (fixes 7) — they do not depend on the feature dataset.
- `LinearRegression` (lags=30) **must not** be run until the multi-step lag/NaN strategy (fixes 3 and 4) is defined, or it will crash or leak future values.
- **No tournament ranking should be published** until the metric and composite fixes (fixes 1, 2, 5) are complete.

Proceed to 5.9 implementation; gate the *execution* of metric-dependent and feature-dependent paths behind the required fixes.
