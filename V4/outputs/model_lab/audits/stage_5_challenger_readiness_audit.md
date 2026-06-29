# Stage 5 Challenger Readiness Audit (AUDIT #2)

**Reviewer role:** Independent Principal ML Architect / Forecasting Systems Auditor
**Trigger:** Pre-challenger gate. Baseline pipeline complete; baseline ranking published.
**Mode:** Review only. No code, configs, data, or outputs were modified.
**Audit date:** 2026-06-11
**Predecessor:** `stage_5_pre_training_audit.md` (AUDIT #1)

---

## A. Executive Summary

The baseline pipeline is **engineered well and is leakage-clean**. AUDIT #1's blocking items were genuinely remediated: zero-actual handling, absolute bias, RMSE entity-scale normalization, an explicit multi-step forecasting/leakage policy, and defined stability/horizon semantics now exist. Baseline models are implemented, executed across all 454 windows × 7 models (3,178 jobs, 0 failures, 95,340 forecast rows), and metrics are computed with a defensible per-group engine. I verified leakage safety empirically: `LinearRegression` forecasts recursively from training history plus its own predictions only, every baseline extrapolates from the training slice alone, and the training slice is hard-bounded by `train_end_date` with an explicit anti-leakage assertion. **There is no temporal leakage and no horizon contamination.**

However, the **benchmark that challengers would be compared against is not methodologically valid as published**, and two issues are severe enough to invalidate any challenger comparison run today:

1. **The published scores are cohort-relative, not absolute.** Normalization is pure percentile-rank *within the set of models present in each entity-window*. The "ETS_Current 64.18 … FixedGrowth_6 17.04" table is a within-cohort ranking of 7 baselines, not a fixed yardstick. Adding 7 challengers changes every denominator and re-rates the baselines. The published baseline numbers therefore cannot serve as a stable bar, and challenger scores computed in any different cohort are not comparable to them.

2. **The ranking contradicts raw accuracy.** On the raw per-model metric table, `FixedGrowth_1_5` is the **best model on every averaged metric** (wMAPE 4.9%, vs `ETS_Current` 18.2%; RMSE 7,132 vs 19,593; lower MAPE, SMAPE, and |bias| too), yet it is published **3rd**. `ETS_Current` is published **1st** despite having the **worst MAPE of all seven models**. Rank-based scoring measures *how often a model beats peers by any margin*, not *how accurate it is*. The published ordering is not explainable to stakeholders and would propagate into challenger comparisons.

Because the central purpose of this gate is "is the benchmark valid for fair challenger comparison," and the answer today is no, challenger onboarding is **BLOCKED** pending a small, well-scoped set of corrections. The platform plumbing is sound; the defect is concentrated in ranking/normalization **semantics**, not engineering.

---

## B. Architecture Assessment

**Strengths**
- Clean stage decomposition with single-purpose scripts (full execution → metrics → policy design → dry run → publication), each guarded against scope creep.
- Strong execution gating retained from AUDIT #1: `training_enabled`/`dry_run`/`BASELINE_SMOKE_TEST` triple-gate; full execution asserts exactly 3,178 baseline jobs and 30-day horizons.
- Leakage controls are explicit and verifiable: `_training_slice` bounds data by `train_end_date` and raises on any row beyond it; `multistep_forecasting.yaml` codifies `no_actual_values_allowed_during_prediction_horizon: true`.
- Per-job failure isolation in full execution; 0/3,178 failures observed.

**Weaknesses**
- **Config drift between two weight systems.** `config/scoring_weights.yaml` (wmape/mape/rmse/bias/stability/horizon) is *not* the schema the ranking uses. Ranking uses `ranking_metric_weights.csv` (wmape/mape/rmse/smape/abs_bias) with **no stability and no horizon**. Two parallel, divergent scoring definitions invite mistakes when challengers arrive. (Medium)
- **`stability` and `horizon` are defined but unused.** They were the explicit AUDIT #1 fix, yet the published ranking ignores them. The composite is not what the design documents imply. (Medium)
- **Inconsistent strategy guard.** `_validate_linear_regression_strategy` runs only in the smoke path, not in `run_full_baseline_execution.py`. Safe today because the model is internally correct, but the guard should be uniform. (Low)
- **Reproducibility chain is not fingerprinted.** Publication derives from the dry-run summary, which derives from `baseline_metrics.csv`, which derives from `full_baseline_forecasts.csv`. No content hash or forecast `run_id` is carried into the published artifacts, so a published score cannot be cryptographically tied to the exact forecast set that produced it. `tests/` is still empty. (Medium)

---

## C. Benchmark Assessment

**Forecast generation: valid and leakage-free.**
- `LinearRegression` (lags=30) builds its lag vector purely from training history and appends predictions recursively — no future actuals. Verified.
- `ARIMA_Fixed` (0,2,0), `ETS_Current` (hand-rolled Holt linear, α=0.8/β=0.2), and `FixedGrowth_*` all extrapolate from the training slice only. Verified.
- Metrics join forecasts to actuals on `forecast_date`; windows are non-overlapping; no actuals enter the prediction horizon. No horizon contamination.

**Benchmark validity: not valid as a fixed reference. (CRITICAL)**
- The score distribution confirms pure rank normalization: `entity_window_composite` spans exactly 0–100 with median 50.0 across 3,178 rows. In every entity-window the best-of-cohort model is forced to ~100 and the worst to ~0 **regardless of absolute error**. The numbers encode *relative position among whatever models are present*, not accuracy.
- Consequence for challengers: scoring challengers in a separate cohort is invalid (each cohort is independently rescaled to 0–100). Scoring them jointly with baselines is fair, but then the **published baseline numbers change**, so they are not a "benchmark" in any fixed sense. Either way, the current publication cannot anchor challenger comparison.

**Benchmark ordering contradicts accuracy. (CRITICAL)**
- Raw per-model averages (`baseline_metrics_by_model.csv`):

  | Model | avg wMAPE | avg MAPE | avg RMSE | avg SMAPE | avg \|bias\| | Published rank/score |
  |---|---|---|---|---|---|---|
  | FixedGrowth_1_5 | **0.049** | **0.316** | **7,132** | **0.059** | 4,554 | 3rd / 60.20 |
  | FixedGrowth_3 | 0.051 | 0.320 | 7,461 | 0.060 | 3,092 | 5th / 48.75 |
  | LinearRegression | 0.133 | 0.419 | 7,833 | 0.072 | 4,603 | 2nd / 60.92 |
  | ETS_Current | 0.182 | 0.524 (worst) | 19,593 | 0.090 | 13,685 | **1st / 64.18** |
  | ARIMA_Fixed | 0.214 (worst) | 0.486 | 71,673 (worst) | 0.137 (worst) | 59,361 (worst) | 4th / 50.32 |

- `FixedGrowth_1_5` dominates `ETS_Current` on **every** averaged metric yet ranks below it. `ETS_Current` has the **worst MAPE** of all models yet is the published #1. This is the classic rank-vs-magnitude divergence: rank scoring rewards frequent narrow wins and is blind to occasional catastrophic losses. The artifacts never reconcile this contradiction, so the benchmark's "winner" depends entirely on which lens (rank vs accuracy) you choose.

**No absolute skill anchor. (HIGH)**
- There is no naive/seasonal-naive reference and no scaled error metric (MASE/RMSSE). Nothing in the benchmark answers "does any model actually have skill?" A rank-only benchmark cannot quantify *how much* better a challenger is — only that it out-ranks peers. This is exactly the signal needed to justify promoting a challenger.

**Forecast sanity: unconstrained negatives. (HIGH)**
- `outlier_root_causes.csv` shows baselines emitting large negative forecasts for non-negative demand: `ARIMA_Fixed` forecast_range down to **−17,661,382**; `ETS_Current` to **−2,173,310**; `LinearRegression` negative ranges too. RMSE reaches ~12.1M and wMAPE 469% at structural-break windows. No non-negativity floor or forecast clamp exists. This both corrupts metrics and will distort any challenger normalized against these absurd baseline errors.

---

## D. Ranking Methodology Assessment

**Defensible elements**
- Aggregation is genuinely entity-balanced: percentile-rank within entity-window → **median across windows** (robust to window outliers) → **mean across entities** (one entity, one vote). Entity-dominance flag threshold (>10% share) is sound and did not fire.
- Outlier policy is transparent and non-destructive: winsorize to entity p99, **no row exclusions, no silent removal**. Tie-breaking is deterministic.
- Weights sum to 1.0 (0.30/0.15/0.20/0.20/0.15). Direction handling is consistent (lower-is-better → higher-is-better post-normalization).

**Defects**
- **Rank normalization discards magnitude (CRITICAL, see Section C).** Appropriate for a relative tournament position metric, but it is being published and consumed as an accuracy benchmark. The two are not interchangeable and the difference is undocumented.
- **Metric redundancy collapses the composite (HIGH).** wMAPE + MAPE + SMAPE carry 65% of weight and are mutually collinear. After rank normalization the per-model component scores are nearly identical across all five metrics (e.g., ETS_Current: 63.9/64.1/63.2/63.9/63.5; FixedGrowth_6: 18.4/16.2/16.5/18.4/16.5). The five-metric composite therefore behaves like a **single latent "average rank" dimension** — the appearance of multi-dimensional evaluation is illusory, and RMSE/bias have little independent influence.
- **Outlier control is near-inert under rank scoring (HIGH).** Clipping the worst value to p99 rarely changes its rank (worst stays worst), so winsorization barely moves scores. The dry-run `flags` file is **empty** — `outlier_dominance`, `metric_dominance`, `score_spread`, and `instability` all passed — giving false comfort, while the separate `outlier_drilldown` shows RMSE up to 12M and wMAPE up to 469%. The diagnostics validate the scoring math but mask the underlying forecast-quality problem.
- **Cohort-composition bias from correlated variants (MEDIUM).** Four of seven models are `FixedGrowth_*` clones (only the growth rate differs). Highly correlated entrants split rank space and bias percentile ranks for the whole cohort. When 7 challengers join, composition shifts again and all ranks move — a moving-target benchmark.
- **Ranking instability is plausible but untested (MEDIUM).** Published global scores are tightly clustered for the middle of the field (50.3 / 48.8). The dry run reports a min-gap instability check, but there is no bootstrap/resampling confidence interval on the global scores, so the stability of the order is asserted, not demonstrated.

---

## E. Critical Risks

| # | Severity | Risk | Business impact | Technical impact |
|---|---|---|---|---|
| C-1 | **Critical** | Cohort-relative rank normalization published as a fixed benchmark | Stakeholders will treat "64.18" as an absolute bar; challenger comparisons will be apples-to-oranges and could promote a worse model | Adding challengers changes every entity-window denominator; baseline scores are not reproducible across cohorts; no valid way to compare published baseline scores to challenger scores |
| C-2 | **Critical** | Published ranking contradicts raw accuracy (FixedGrowth_1_5 best on all metrics → 3rd; ETS_Current worst MAPE → 1st) | A demonstrably more accurate model is presented as inferior; future "champion" selection may be indefensible and erode trust in the platform | Rank scoring measures win-frequency, not error magnitude; the benchmark's conclusion is lens-dependent and unreconciled |

---

## F. High / Medium / Low Risks

| # | Severity | Risk | Business impact | Technical impact |
|---|---|---|---|---|
| H-1 | High | No absolute skill anchor (no naive baseline, no MASE/RMSSE) | Cannot quantify how much a challenger improves, or whether any model beats a trivial forecast | Promotion decisions lack an objective effect-size; rank-only output has no magnitude semantics |
| H-2 | High | Metric redundancy collapses 5-metric composite to ~1 rank dimension | False confidence in "multi-metric" rigor; bias/RMSE effectively ignored | Collinear wMAPE/MAPE/SMAPE = 65% weight; component scores near-identical across metrics |
| H-3 | High | Unconstrained negative forecasts (down to −17.6M for non-negative demand) | Absurd forecasts reach metrics/dashboards; distorts baseline error bar challengers are measured against | No non-negativity floor; ARIMA(0,2,0)/Holt extrapolate explosively at structural breaks |
| H-4 | High | Outlier controls inert under rank normalization; dry-run flags empty | False "all clear" hides catastrophic outliers found in drilldown | p99 clip does not change ranks; sensitivity check cannot fire |
| M-1 | Medium | Two divergent weight schemes; stability/horizon defined but unused | Documentation says one thing, ranking does another | `scoring_weights.yaml` vs `ranking_metric_weights.csv` drift |
| M-2 | Medium | Cohort-composition bias from 4 correlated FixedGrowth variants | Benchmark order shifts purely from which models are present | Correlated entrants distort percentile ranks; challengers will shift them again |
| M-3 | Medium | Structural breaks at window 5 (actuals jump to millions) unhandled | wMAPE up to 469% pollutes aggregates | Window validation is observation-count based, not calendar/continuity/level-shift aware (carried from AUDIT #1) |
| M-4 | Medium | Reproducibility chain not fingerprinted; no tests | Cannot prove a published score maps to a specific forecast run; regressions undetected | No data/config hash in artifacts; `tests/` empty |
| L-1 | Low | Strategy guard only in smoke path, not full execution | Low today; future ML models could slip an unsafe path | `_validate_linear_regression_strategy` not called in full run |
| L-2 | Low | `ETS_Current` is hand-rolled Holt, not statsmodels ETS | Reproduction fidelity to real TESSERACT ETS unverified | Fixed α/β; no seasonality; may not match production ETS |

---

## G. Recommended Corrections

**Must fix before challengers (resolves C-1, C-2, H-1, H-3):**
1. **Decide and document what the benchmark measures.** Either (a) adopt a **cohort-stable absolute normalization** (e.g., score each metric against a fixed reference scale or a naive-forecast baseline, so a model's score does not depend on which peers are present), or (b) explicitly commit to **joint re-ranking** of baselines+challengers in one cohort and stop treating the current baseline numbers as a fixed bar — relabel them as a within-baseline snapshot.
2. **Add an absolute skill anchor.** Introduce a seasonal-naive (or naive drift) reference and report **MASE/RMSSE** alongside ranks, so challenger improvement is measurable in magnitude, not just position.
3. **Reconcile the rank-vs-accuracy contradiction.** Publish, next to the rank scores, the entity-balanced **magnitude** view (e.g., entity-balanced median wMAPE/MASE) and explain any divergence. A benchmark whose #1 is the worst-MAPE model must justify that explicitly or change methodology.
4. **Add a non-negativity floor / forecast sanity clamp** (and/or model-level guards) so demand forecasts cannot go negative; re-examine the metric impact afterward.

**Should fix before challengers (resolves H-2, H-4, M-1, M-2):**
5. **De-collinearize the composite:** keep one primary percentage metric (wMAPE), drop or down-weight MAPE/SMAPE, and ensure RMSE/MASE and bias retain real influence. Re-introduce the **stability and horizon** terms the design promises, or remove them from the docs.
6. **Make outlier control meaningful under the chosen normalization** (if magnitude-aware scoring is adopted, winsorization will actually bind); wire the drilldown's structural-break findings into the dry-run flags so the "all clear" reflects forecast quality, not just score math.
7. **Resolve correlated-variant bias:** treat the FixedGrowth family explicitly (e.g., collapse to a representative or report family-aware) so cohort composition doesn't drive ranks.
8. **Unify the weight configuration** to a single source of truth.

**Hygiene (M-3, M-4, L-1, L-2):**
9. Add level-shift/continuity detection to window generation; segregate or flag structural-break windows.
10. Stamp forecast `run_id` + input content hashes into metrics, dry-run, and publication artifacts; add a minimal test suite (leakage, 30-day horizon, no-future-actuals, normalization monotonicity, ranking determinism).
11. Apply the multistep strategy guard in full execution; document `ETS_Current` fidelity vs production.

---

## H. Challenger Readiness Decision

**BLOCKED.**

Rationale: the pipeline is leakage-clean and operationally sound, but the published baseline benchmark is **cohort-relative** (C-1) and its ordering **contradicts absolute accuracy** (C-2). Onboarding challengers against this benchmark today would produce comparisons that are not reproducible across cohorts and not defensible against raw accuracy, with a real risk of crowning a less accurate "champion." The remediation is narrow and concentrated in ranking/normalization semantics plus a forecast sanity floor — not a re-architecture. Once corrections 1–4 (and ideally 5–8) are in place and the rank-vs-accuracy divergence is reconciled, this should move quickly to **APPROVED WITH CHANGES** and then to challenger execution.

What is explicitly **clear and does not block**: temporal leakage (none), horizon contamination (none), recursive `LinearRegression` safety (verified), training-window bounding (asserted), entity-balanced aggregation structure (sound), and execution guards (strong).

---

## I. Final Verdict

**BLOCKED** — for challenger onboarding, pending benchmark-semantics corrections (C-1, C-2, H-1, H-3 mandatory). The baseline *forecasting* and *metrics* layers are valid and leakage-free; the baseline *ranking/publication* layer is not yet a sound basis for fair challenger comparison.
