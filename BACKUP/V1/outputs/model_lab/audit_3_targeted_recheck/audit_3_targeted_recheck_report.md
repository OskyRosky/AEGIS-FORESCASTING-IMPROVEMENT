# AUDIT #3 — Block 5.27B Targeted Re-check: Major-1 Closure

**Platform:** TESSERACT v2 / AEGIS Forecast Improvement Platform
**Stage:** 5 — Model Lab
**Block:** 5.27B — Targeted Claude Re-check (READ-ONLY)
**Scope:** Verify ONLY whether Major-1 (MASE/RMSSE denominator computed on the test horizon, contradicting the training-only contract) has been fully closed by the 5.27A fix. This is **not** a full re-audit of Stage 5.

---

## 1. Executive Summary

Major-1 is **fully closed**. The 5.27A fix replaced the test-horizon naive denominator with the contractually required **in-sample, training-only lag-1 naive** denominator (MAE for MASE, MSE for RMSSE), and the change is consistently implemented across code, shared utility, unit tests, documentation, configuration, and recomputed outputs. All five verification points pass on evidence. No rankings, tournament, or champion artifacts were created. It is safe to proceed to Block 5.28.

One **advisory note** (non-blocking) accompanies this approval: the headline metric magnitudes shifted materially (global median MASE 0.9996 → 11.43; global median RMSSE 1.0042 → 3.10; rows beating naive ~50% → 4.5%). This is the **expected and correct** consequence of moving from an out-of-sample 30-day flat-naive denominator to the textbook in-sample one-step lag-1 denominator, not a residual defect. It should be documented during 5.28 onboarding so the absolute MASE/RMSSE scale and the "beats naive" diagnostic are not misread.

---

## 2. Verdict

```
MAJOR_1_CLOSED_APPROVE_TO_PROCEED_TO_5.28_CHALLENGER_ONBOARDING
```

---

## 3. Verification Points & Evidence

### 3.1 Code, docs, and configs agree on the denominator definition — PASS

| Source | Denominator definition | Slice / test usage |
| --- | --- | --- |
| [benchmark_denominators.py](../../../python/model_lab/benchmark_denominators.py) | MASE = `mean(abs(diff(y_train)))`; RMSSE = `mean(diff(y_train)^2)` | actuals filtered `train_start_date <= date <= train_end_date`; `record_type == "actual"` only |
| [scoring_definitions.yaml](../../../config/scoring_definitions.yaml) | `training_only_lag_1_naive_mae` / `..._mse`; `mean_abs_first_difference_over_training_actuals` | `slice: training_only`, `never_use_test: true` |
| [ranking_policy.yaml](../../../config/ranking_policy.yaml) | `method: training_only_lag_1_naive_mae` | `slice: training_only`, `never_use_test: true` |
| [benchmark_semantics_v1.md](../../../docs/benchmark_semantics/benchmark_semantics_v1.md) | `mean(abs(y_train[t] - y_train[t-1]))` / `mean((y_train[t] - y_train[t-1])^2)` | "El denominador nunca se calcula sobre test"; RMSSE uses `<= train_end_date` only |

All four sources explicitly exclude: Block 5.19 naive forecasts, seasonal naive, and the Drift model as the denominator, and require an epsilon floor. They are mutually consistent.

### 3.2 Denominator no longer uses test-horizon actuals — PASS

- [benchmark_denominators.py](../../../python/model_lab/benchmark_denominators.py) builds the denominator strictly from actuals with `date <= train_end_date`, requires ≥ 2 training observations, and computes lag-1 first differences via `training["value"].diff().dropna()`. The old `naive_benchmark_forecasts.csv` (test-horizon flat naive) is no longer used as the denominator anywhere.
- [calculate_mase.py](../../../python/model_lab/calculate_mase.py) and [calculate_rmsse.py](../../../python/model_lab/calculate_rmsse.py) import `build_and_write_denominators` and join `mase_denominator_mae` / `rmsse_denominator_mse` by `entity_key + window_id`; MASE = `mae_model / mase_denominator_mae`, RMSSE = `sqrt(model_mse / rmsse_denominator_mse)`.
- [apply_non_negative_policy.py](../../../python/model_lab/apply_non_negative_policy.py) recomputes adjusted MASE/RMSSE against the same training-only denominators (it imports `build_and_write_denominators` and joins the same columns), and writes adjusted copies without overwriting baseline forecasts.

### 3.3 Unit tests pin the training-only denominator — PASS

[test_training_only_denominator.py](../../../python/model_lab/test_training_only_denominator.py) is deterministic and asserts the exact contract. All 8 checks recorded **passed** in [denominator_unit_test_report.csv](../denominator_reconciliation/denominator_unit_test_report.csv):

| Test | Result |
| --- | --- |
| uses_only_actuals_through_train_end_date | passed |
| does_not_use_test_period_actuals | passed |
| mase_denominator_is_training_first_difference_mae | passed |
| rmsse_denominator_is_training_first_difference_mse | passed |
| changing_test_actuals_does_not_change_denominator | passed |
| seasonal_naive_is_not_used | passed |
| block_519_naive_forecast_is_not_used | passed |
| epsilon_floor_behavior | passed |

The test mutates test-horizon actuals to extreme values and asserts the denominator is unchanged — directly proving no test leakage into the denominator.

### 3.4 Recomputed outputs are valid and complete — PASS

| Output | Key counts | Status |
| --- | --- | --- |
| [denominator_reconciliation_summary.csv](../denominator_reconciliation/denominator_reconciliation_summary.csv) | 39 entities, 454 windows, 454 denominator rows, 0 floored (MASE & RMSSE), epsilon 1e-6 | Complete |
| [mase_summary.csv](../mase/mase_summary.csv) | 3,178 metric rows, 39 entities, 454 windows, 7 models; global median MASE 11.43 | Complete |
| [rmsse_guardrail_summary.csv](../rmsse/rmsse_guardrail_summary.csv) | 3,178 rows; global median RMSSE 3.10; pct_high_risk 36.8% | Complete |
| [non_negative_policy_summary.csv](../non_negative_policy/non_negative_policy_summary.csv) | 95,340 forecast rows, 735 clipped; MASE before/after 11.43/11.43; RMSSE 3.10/3.09 | Complete |
| [aggregation_summary.csv](../aggregation_hierarchy/aggregation_summary.csv) | 3,178 entity-window, 273 entity-model (39×7), 7 models | Complete |
| [significance_summary.csv](../statistical_significance/significance_summary.csv) | 7 models, 39 entities, 21 pairwise, 10,000 bootstrap | Complete |

Timestamps form a coherent forward pipeline on 2026-06-12 (denominators 14:41 → MASE 14:41:17 → RMSSE 14:41:36 → non-negative 14:41:57 → aggregation 14:42:20 → significance 14:42:38). The denominator computation is deterministic, so the per-stage rebuilds produce identical values. [build_aggregation_hierarchy.py](../../../python/model_lab/build_aggregation_hierarchy.py) consumes the recomputed `non_negative_policy/non_negative_mase_scores.csv` and `non_negative_rmsse_scores.csv`, confirming the new denominator flows through the entire chain.

**Sanity of the magnitude shift:** Previously the denominator was a 30-day out-of-sample flat naive (large error → MASE ≈ 1). The corrected denominator is the in-sample one-step naive error (small for smooth/trending daily storage series), so a 30-day-ahead model error divided by it yields MASE ≫ 1. The new values (median MASE 11.43, median denominator MAE 35.98) are internally consistent and methodologically standard (M4/M5-style MASE). 0 floored rows is also consistent with a non-degenerate in-sample series.

### 3.5 Safe to proceed to 5.28 — PASS

- `outputs/model_lab/tournament/` is **empty** and `outputs/model_lab/rankings/` is **empty** — no champion, ranking, or tournament artifacts were created (consistent with the read-only / no-selection contract for this block).
- The non-negative policy and metric scripts read `full_baseline/full_baseline_forecasts.csv` read-only and write to their own output folders; baseline and benchmark/reference forecasts are not overwritten.
- The benchmark contract (MASE primary, RMSSE guardrail, equal-entity-weighted median-of-medians aggregation, no cohort-relative normalization) remains intact across config and docs.

---

## 4. Blockers

None. No condition prevents proceeding to Block 5.28.

---

## 5. Advisory Note (non-blocking, for 5.28 onboarding)

The denominator correction changed the **meaning and scale** of the headline metrics:

- Global median MASE: 0.9996 → **11.43**
- Global median RMSSE: 1.0042 → **3.10**
- Rows beating naive (MASE < 1): ~50% → **4.5%**

This is correct behavior, not a defect. However, when challengers are onboarded in 5.28, the absolute MASE scale and the "beats naive" diagnostic must be interpreted against an **in-sample one-step lag-1 naive** baseline (a deliberately hard bar for 30-day-ahead forecasts), not the previous out-of-sample flat naive. Recommend a one-line interpretation note in the 5.28 onboarding/ranking documentation to prevent stakeholder misreading. This does not affect the integrity of the closure.

---

## 6. Decision

Major-1 is fully closed on the evidence: the denominator is defined and computed as the training-only in-sample lag-1 naive (MAE for MASE, MSE for RMSSE), test-horizon actuals are provably excluded, the definition is pinned by passing deterministic unit tests, all downstream outputs are recomputed and complete, and no premature selection artifacts exist.

```
MAJOR_1_CLOSED_APPROVE_TO_PROCEED_TO_5.28_CHALLENGER_ONBOARDING
```
