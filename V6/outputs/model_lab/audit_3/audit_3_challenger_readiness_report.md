# AUDIT #3 — Stage 5 Methodological Foundation Review (Block 5.27)

**Reviewer role:** Independent Senior Forecasting Systems Auditor
**Trigger:** Pre-challenger gate. Blocks 5.18–5.26 complete; challenger onboarding (5.28) not started.
**Mode:** Read-only. No code, configs, data, or outputs were modified. No models run. No rankings, tournament, or champion outputs created.
**Audit date:** 2026-06-12
**Predecessors:** `stage_5_pre_training_audit.md` (AUDIT #1), `stage_5_challenger_readiness_audit.md` (AUDIT #2 = BLOCKED)
**Project root:** `AEGIS-FORESCASTING-IMPROVEMENT`

---

## 1. Executive Summary

**APPROVED WITH CONDITIONS.**

The Stage 5 remediation that AUDIT #2 demanded has been implemented to a high standard and is, in the
main, methodologically sound. The cohort-relative percentile benchmark is formally deprecated; MASE is the
primary absolute metric, RMSSE is a true guardrail, the aggregation hierarchy enforces equal entity
weighting, statistical significance is computed at the correct (entity-level) unit with Benjamini-Hochberg
correction, the non-negative policy preserves originals and only writes adjusted copies, and the
no-tuning-leakage contract is comprehensive. No premature ranking, tournament, or champion output exists.
Every headline record count reconciles exactly with the expected facts.

There is **one material discrepancy** that prevents an unconditional approval: the **MASE/RMSSE denominator
is computed on the test horizon (out-of-sample lag-1 flat naive error), but the governing contract and
design document both mandate an in-sample, training-only lag-1 naive denominator that "never uses test."**
This is not forecast leakage and does not break cohort-stability (the denominator is model-independent, so
challenger MASE values remain comparable when scored by the same official engine). However, the official
benchmark-metric definition is currently **self-contradictory between code and contract**, which can produce
inconsistent or misinterpreted challenger comparisons if a challenger team implements MASE per the written
contract. This must be reconciled and pinned before 5.28.

A secondary robustness concern follows directly from the same choice: the out-of-sample denominator can be
near-zero on flat/low-variation entities, inflating individual MASE rows to extreme values
(`global_mean_mase` ≈ 2.53M). The official median aggregation absorbs this, but the epsilon floor (1e-6) is
too small to be principled.

Because the comparison machinery is internally consistent and the defect is a definition/documentation
reconciliation rather than a leakage or fairness break, this is **APPROVE_WITH_CONDITIONS**, not a block.

---

## 2. Overall Verdict

> **APPROVE_WITH_CONDITIONS**

---

## 3. Audit Scope

Reviewed (read-only):

- **Configs:** `config/ranking_policy.yaml`, `config/scoring_definitions.yaml`, `config/execution.yaml`,
  `config/backtesting.yaml`.
- **Benchmark semantics:** `docs/benchmark_semantics/benchmark_semantics_v1.md`.
- **Code (engines):** `run_naive_benchmark.py`, `run_seasonal_naive.py`, `calculate_mase.py`,
  `calculate_rmsse.py`, `apply_non_negative_policy.py`, `build_aggregation_hierarchy.py`,
  `build_statistical_significance.py`, `build_no_tuning_leakage_contract.py`.
- **Outputs (summaries + impact tables):** `benchmark_reference/`, `seasonal_benchmark/`, `mase/`, `rmsse/`,
  `non_negative_policy/`, `aggregation_hierarchy/`, `statistical_significance/`,
  `no_tuning_leakage_contract/`.
- **Premature-output checks:** `tournament/`, `rankings/`, `dashboard/` (all empty / absent).
- **Core baseline anchors:** `full_baseline/`, `backtesting_windows.csv`, `outputs/evaluation/`.

---

## 4. Methodological Review

### 4.1 MASE (Block 5.21) — primary metric
- Computed per entity/window/model as `mean(|actual − model_forecast|) / mean(|actual − naive_forecast|)`,
  using the **lag-1 naive** reference (not seasonal naive). Correct primary-metric intent.
- Interpretation preserved (`<1` beats naive). `by_model`/`by_entity`/`summary` are diagnostics only; **no
  ranking or champion** is emitted.
- **Finding (Major):** the denominator uses the **test-window** naive error. The naive reference
  (`run_naive_benchmark.py`) carries the last training actual flat across the 30-day **test** horizon, and
  `calculate_mase.py` averages `|actual − naive|` over those **test** dates. The contract
  (`ranking_policy.yaml`: `slice: training_only`, `never_use_test: true`) and the design doc
  (`benchmark_semantics_v1.md`: "El denominador nunca se calcula sobre test") mandate the **in-sample
  training-only** one-step naive MAE. Code and contract disagree on the definition of the primary metric.

### 4.2 RMSSE (Block 5.22) — guardrail
- Computed as `sqrt(MSE_model / MSE_naive)`; `risk_status` buckets (`beats_naive`/`acceptable`/`warning`/
  `high_risk`) are diagnostic. **Not used as a ranking metric.** Correct guardrail role.
- Inherits the same denominator-definition finding as MASE (same naive reference).

### 4.3 Non-negative policy (Block 5.23)
- Writes an **adjusted copy** with `original_forecast_value`, `adjusted_forecast_value`, `was_clipped`; clips
  with `clip(lower=0)`. **Originals are never overwritten;** outputs land in a separate directory.
- Recomputes MASE/RMSSE on adjusted forecasts and records before/after medians. Correct and conservative.

### 4.4 Aggregation hierarchy (Block 5.24)
- Official model MASE = **median across entities of (median MASE across that entity's windows)** — a
  two-level median with **equal entity weighting**. Entities with more windows cannot dominate. Correct.
- Consumes the **non-negative adjusted** MASE/RMSSE (official forecasts). Row-level means/p95 are explicitly
  diagnostics. **No ranking/champion.**

### 4.5 Statistical significance (Block 5.25)
- Comparison unit = **entity-level median MASE** (from `aggregation_by_entity_model.csv`), **not raw forecast
  rows** — correctly avoids window-count domination.
- Paired bootstrap over entities (10,000 iters, fixed seed `20260612`), exact binomial **sign test**,
  **Benjamini-Hochberg** across all 21 pairwise p-values, and a **practical MASE threshold (0.02)**.
- `evidence_status` requires CI sign + BH significance + practical significance to declare support; otherwise
  `inconclusive`. **No winner/champion/ranking** is produced. Methodologically conservative and correct.

### 4.6 No-tuning-leakage contract (Block 5.26)
- Comprehensive: temporal isolation, feature-leakage rules, tuning prohibitions (no tuning on official
  MASE/RMSSE/significance/tournament/champion feedback), sandbox vs official mode, preregistration fields,
  reproducibility + audit metadata, blocking conditions. `audit_ready=true`,
  `challengers_ready_for_official_execution=0`. Correctly gates 5.28.

---

## 5. Artifact Validation

| Artifact area | Expected files | Status | Notes |
|---|---|---|---|
| Benchmark semantics | `benchmark_semantics_v1.md`, configs | ✅ Present | `ranking_policy.yaml` now `policy_stage: 5.18`, percentile method deprecated. **Denominator clause contradicts code (see §4.1).** |
| Lag-1 naive | 3 files in `benchmark_reference/` | ✅ Present | Leakage-safe forecast generation; flat last-train value over horizon. |
| Seasonal naive | 3 files in `seasonal_benchmark/` | ✅ Present | Reference/diagnostic only; not wired into primary denominator. |
| MASE | 4 files in `mase/` | ✅ Present | Primary metric; diagnostics only by model/entity. |
| RMSSE | 4 files in `rmsse/` | ✅ Present | Guardrail; risk buckets, no ranking. |
| Non-negative policy | 6 files in `non_negative_policy/` | ✅ Present | Originals preserved; adjusted copies + recomputed metrics. |
| Aggregation hierarchy | 5 files in `aggregation_hierarchy/` | ✅ Present | Equal-entity-weight two-level median; policy.md present. |
| Statistical significance | 4 files in `statistical_significance/` | ✅ Present | Entity-level unit; BH; no champion. |
| No-tuning-leakage | 5 files in `no_tuning_leakage_contract/` | ✅ Present | Contract + checklist + preregistration template + manifest. |
| Premature outputs | `tournament/`, `rankings/`, `dashboard/` | ✅ Empty | No champion/tournament/ranking created. |

---

## 6. Record Count Validation

| Area | Expected | Observed | Status |
|---|---|---|---|
| Naive windows planned/completed/failed | 454 / 454 / 0 | 454 / 454 / 0 | ✅ |
| Naive forecast rows | 13,620 | 13,620 | ✅ |
| Seasonal naive planned/completed/failed | 454 / 452 / 2 | 454 / 452 / 2 | ✅ |
| Seasonal naive forecast rows | 13,560 | 13,560 | ✅ |
| MASE metric rows / entities / windows / models | 3,178 / 39 / 454 / 7 | 3,178 / 39 / 454 / 7 | ✅ |
| Global median MASE | ≈ 0.9996 | 0.99958 | ✅ |
| RMSSE metric rows | 3,178 | 3,178 | ✅ |
| Global median RMSSE | ≈ 1.0042 | 1.00422 | ✅ |
| Non-negative forecast rows | 95,340 | 95,340 | ✅ |
| Negative rows clipped | 735 | 735 | ✅ |
| Affected models (3) | ARIMA_Fixed / ETS_Current / LinearRegression | 462 / 201 / 72 = 735 | ✅ |
| Min original forecast | ≈ −17.6M | −17,661,382.65 → adjusted 0.0 | ✅ |
| Aggregation canonical / entity-model / model rows | 3,178 / 273 / 7 | 3,178 / 273 / 7 | ✅ (273 = 39×7) |
| Significance pairwise / models / entities | 21 / 7 / 39 | 21 / 7 / 39 | ✅ |
| Bootstrap iterations | 10,000 | 10,000 | ✅ |
| Supported / inconclusive comparisons | 12 / 9 | 12 / 9 | ✅ |
| No-tuning controls / blocking / ready | 12 / 12 / 0 | 12 / 12 / 0, audit_ready=true | ✅ |

All counts reconcile.

---

## 7. Leakage Assessment

- **Forecast-generation leakage: NONE.** The naive reference uses only the last actual at/before
  `train_end_date` (with an explicit "Training leakage detected" guard). Baseline forecasts were already
  verified leakage-clean in AUDIT #1/#2. Challengers are gated by the 5.26 contract.
- **Significance-unit integrity: PASS.** Entity-level median MASE is the unit; raw rows are not the official
  unit.
- **Important nuance (not forecast leakage):** the MASE/RMSSE **denominator** is evaluated on the test
  horizon. The naive *forecast* itself is leakage-free, but computing the scaling denominator on test
  **violates the written contract** (`never_use_test: true`). This is a definition/contract-compliance defect
  (§4.1, §9 Major-1), not a temporal information leak into forecasts.

---

## 8. Challenger Readiness Assessment

The platform is structurally and procedurally ready to begin challenger onboarding:

- An absolute, cohort-stable primary metric exists (MASE); adding challengers does **not** rescale baseline
  scores because the naive denominator is model-independent.
- A guardrail (RMSSE), equal-weight aggregation, significance evidence, and a binding no-tuning-leakage
  contract are all in place.
- No premature champion/tournament/ranking output exists to bias onboarding.

The single reservation is that the **definition of the primary metric must be unambiguous and consistent
between code and contract before challengers are scored against it.** As long as challengers are evaluated by
the same official engine (which the contract mandates), comparison remains internally valid; the risk is
external/interpretive (a challenger team coding to the written contract would compute a different MASE).

---

## 9. Blockers

### Critical blockers
- **None.** No issue invalidates challenger comparison when challengers are scored by the same official
  engine, and no leakage or premature champion exists.

### Major issues
- **Major-1 — MASE/RMSSE denominator definition mismatch (code vs contract).** Implementation uses the
  out-of-sample test-horizon lag-1 flat-naive error; `ranking_policy.yaml` and `benchmark_semantics_v1.md`
  mandate the in-sample, training-only lag-1 naive MAE that "never uses test." The governing definition of
  the primary benchmark metric is self-contradictory and must be reconciled and pinned before 5.28.

### Minor issues
- **Minor-1 — Near-zero denominator fragility / weak floor.** The test-horizon denominator can be near-zero
  on flat entities, inflating individual MASE rows (`global_mean_mase` ≈ 2.53M). The official **median**
  aggregation contains this, but `EPSILON = 1e-6` is not a principled floor. Adopt an entity-scaled floor or
  a minimum-denominator policy and report floored rows (currently tracked).
- **Minor-2 — Diagnostic mean exposure.** `diagnostic_mean_mase` carries multi-million values; ensure
  downstream UI/consumers never treat the mean as the official score (the median is official).

### Informational findings
- **Info-1 — Missing optional configs.** `config/model_registry.yaml` and `config/training_job_plan.yaml` are
  absent. The contract manifest already classifies these as **informational, non-blocking** for 5.27/5.28;
  the registry exists in code (`python/model_lab/models/model_registry.py`). Not a blocker.
- **Info-2 — Seasonal naive 2 controlled failures.** Expected (insufficient seasonal lookback on 2 windows);
  seasonal naive is reference/diagnostic only and is **not** the official denominator, so the official metric
  is unaffected.
- **Info-3 — README.md (repo root) remains stale** from earlier stages; does not affect Stage 5 artifacts.

---

## 10. Required Fixes Before 5.28

1. **Reconcile and pin the MASE/RMSSE denominator definition (Major-1).** Choose one, explicitly, and make
   code, `ranking_policy.yaml`, and `benchmark_semantics_v1.md` agree:
   - **Option A (match the contract):** recompute the denominator as the **in-sample training-only lag-1
     naive MAE** (`mean(|y_t − y_{t-1}|)` over the training slice), then recompute MASE/RMSSE,
     non-negative-adjusted scores, aggregation, and significance. (More robust to near-zero denominators.)
   - **Option B (match the code):** formally redefine the official metric as a **test-horizon relative error
     vs the lag-1 flat naive**, update the contract/doc to remove `never_use_test: true`, and justify the
     choice for the long-horizon capacity use case.
   - Either way, add a unit test asserting the denominator follows the pinned definition, and document it in
     the challenger preregistration template so challengers compute MASE identically.

---

## 11. Recommended Improvements (non-blocking)

- Replace the fixed `1e-6` denominator floor with an **entity-scaled floor** (e.g., fraction of entity mean
  actual) and surface floored-row counts in the official summaries.
- Add a regression test asserting `tournament/`, `rankings/`, and champion artifacts remain empty until their
  designated blocks.
- Stamp input data/config content hashes into the MASE/RMSSE/aggregation/significance summaries to lock the
  reproducibility chain (the contract already requires this for challengers; apply it to baselines too).
- Refresh the stale root `README.md` to reflect the true Stage 5 state.
- Consider reporting both the in-sample and test-horizon scaled errors side-by-side once Major-1 is resolved,
  so the chosen primary metric is interpretable against the alternative.

---

## 12. Final Decision

> **APPROVE_WITH_CONDITIONS**

The Stage 5 methodological foundation (MASE primary, RMSSE guardrail, non-negative policy, equal-weight
aggregation, entity-level significance with BH, no-tuning-leakage contract) is sound, cohort-stable,
leakage-free in forecast generation, and free of premature champion/tournament outputs. Approval is
conditioned on reconciling and pinning the single primary-metric denominator definition (Major-1) so that
challengers are scored against an unambiguous, contract-consistent benchmark.

---

## 13. Suggested Next Step

**Fix the Major-1 denominator definition (reconcile code ↔ contract and pin it with a test), then proceed to
5.28 Challenger Onboarding.** Re-running AUDIT #3 in full is not required if Major-1 is closed with a
documented diff and a passing denominator unit test; a targeted re-verification of the corrected MASE/RMSSE
definition is sufficient.

---

*Audit conducted in read-only mode. No code, configs, data, or outputs were modified; no models, rankings,
tournaments, or champion selections were created. All findings are evidence-based and cite repository
artifacts inspected on 2026-06-12.*
