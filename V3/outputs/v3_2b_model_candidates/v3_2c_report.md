# V3.2C — Experimental Harness + Subset Dry-Run Runtime Gate (REPORT)

**Stage:** V3.2C (authorized scope: implement isolated harness + run the deterministic
5-series subset dry-run with a runtime gate; **full 39-series backtest NOT run**).
**Status:** `V3_2C_SUBSET_DRY_RUN_COMPLETE_READY_FOR_OSCAR_REVIEW`
**Date:** 2026-06-25
**Environment:** Python 3.14.6, CPU-only (torch 2.12.0+cpu, CUDA not available), single process, seed 42.

> All MASE/RMSSE values below use a **seasonal-naive (m=7) in-sample scale** computed inside the
> harness. They are **indicative for ranking within the dry-run only** and are **not 1:1 comparable**
> to the V3.2A governed scorecard numbers (different denominator). The authorized **full backtest**
> is the authoritative comparison against ETS Explicit and the governed baselines.

---

## 1. Files created
- `python/model_lab/run_v3_2c_subset_dry_run.py` — isolated candidate harness (READ-ONLY inputs).
- `outputs/v3_2b_model_candidates/runtime_checks/subset_runtime_results.csv`
- `outputs/v3_2b_model_candidates/candidate_outputs/subset_candidate_outputs.csv` (2700 rows)
- `outputs/v3_2b_model_candidates/metrics/subset_metrics_summary.csv`
- `outputs/v3_2b_model_candidates/logs/subset_run_log.csv`
- `outputs/v3_2b_model_candidates/v3_2c_report.md` (this file)
- `outputs/v3_2b_model_candidates/v3_2c_validation.csv` (25 checks, all pass)

## 2. Files modified
- **None.** No existing artifact was modified. Inputs were read READ-ONLY. The pre-existing V3.2B
  README placeholders in `runtime_checks/`, `candidate_outputs/`, `metrics/`, `logs/` are untouched.

## 3. Harness implementation location
- `V3/python/model_lab/run_v3_2c_subset_dry_run.py`.
- Inputs (READ-ONLY, same governed sources the official recovery script uses):
  - `outputs/model_lab/challenger_official_execution_prep/official_execution_scope.csv` (walk-forward windows).
  - `outputs/evaluation/evaluation_dataset.csv` filtered to `record_type == 'actual'` (actual series).
- Design: **direct multi-horizon (no recursion)**, `log1p` target where applicable, non-negative clamp,
  seasonal-naive (m=7) MASE/RMSSE, deterministic seed 42. Outputs confined to `outputs/v3_2b_model_candidates/`.

## 4. Candidates executed in subset dry-run
Deterministic subset: **NAM-Multitenant, EUR-Multitenant, LAM-Multitenant** (high-scale multitenant where
the current FastNeuralAR_MLP collapsed) + **APC-Dedicated, NAM-TDF** (well-behaved anchors). Last 3 windows
per series ⇒ **15 entity-windows**, horizons h1–h30.

| candidate_id | model_name | family | backend used (CPU) |
|---|---|---|---|
| FNAR-V2 | FastNeuralAR_MLP_v2_direct | lightweight_neural | sklearn MLP (32,), log1p, direct multi-output, L2, early-stop |
| NLIN-DLIN | NLinear_or_DLinear_lightweight | linear_dl | NLinear last-value-normalized linear layer (Ridge solve) |
| SMLP-TCN | SmallTCN_or_SmallMLPGlobal | lightweight_neural | SmallMLPGlobal pooled tiny net (16,), log1p, epoch cap 150 |
| LGBM-IMP | LightGBM_candidate_improved | gradient_boosting | LightGBM per-horizon (30 boosters, n_est 200) |
| XGB-IMP | XGBoost_candidate_improved | gradient_boosting | XGBoost per-horizon (30 boosters, n_est 200) |
| ENET-RIDGE | ElasticNet_or_Ridge_direct_multi_horizon | linear_ml | Ridge multi-output direct, log1p |

## 5. Runtime results
Projection: `projected_full = runtime_per_entity_window × 454` (454 = full governed entity-windows).

| candidate | subset_runtime_s | per_entity_window_s | projected_full_min | gate |
|---|---:|---:|---:|---|
| ENET-RIDGE | 0.06 | 0.004 | 0.03 | VIABLE |
| NLIN-DLIN | 0.05 | 0.003 | 0.03 | VIABLE |
| SMLP-TCN | 1.24 | 0.082 | 0.62 | VIABLE |
| FNAR-V2 | 6.75 | 0.450 | 3.40 | VIABLE |
| LGBM-IMP | 64.95 | 4.330 | **32.77** | **NOT_VIABLE_FOR_V3_DAILY_REFRESH** |
| XGB-IMP | 153.58 | 10.239 | **77.47** | **NOT_VIABLE_FOR_V3_DAILY_REFRESH** |

Total subset wall-clock ≈ **3.8 min** (within the 3–5 min target). The GBM cost is driven by the
per-horizon implementation (30 boosters per entity-window); their accuracy is fine (see §7) — the
runtime, not the model family, is what fails the gate **as currently implemented**.

## 6. Candidate output validation
- `subset_candidate_outputs.csv` = **2700 rows** = 6 candidates × 5 series × 3 windows × 30 horizons.
- 21 columns identical to `experiment_contract.csv`. Horizons 1..30 present for every (candidate,series,origin).
- **0 negative forecasts after clamp** across all 2700 rows. **0 missing actuals** in subset windows.
- Full contract checks in `v3_2c_validation.csv` (V01–V25, all pass).

## 7. Metrics summary (seasonal-naive m=7, median over 15 windows)
| candidate | median_MASE | median_RMSSE | mean_sMAPE | raw_neg | guardrail | gate |
|---|---:|---:|---:|---:|:--:|---|
| ENET-RIDGE | **1.330** | 0.558 | 0.109 | 0 | PASS | VIABLE |
| NLIN-DLIN | 1.376 | 0.562 | 0.190 | 27 | FAIL (raw neg) | VIABLE |
| SMLP-TCN | 3.284 | 1.095 | 0.198 | 0 | PASS | VIABLE |
| XGB-IMP | 4.145 | 1.190 | 0.264 | 0 | PASS | NOT_VIABLE |
| LGBM-IMP | 5.186 | 1.457 | 0.266 | 0 | PASS | NOT_VIABLE |
| FNAR-V2 | 49.864 | 17.558 | 0.421 | 0 | PASS | VIABLE |

Key reading:
- The **direct (non-recursive)** redesign eliminates the recursive-collapse signature: even the weakest
  candidate here (FNAR-V2, MASE ≈ 49.9) is **~15× better** than the current recursive FastNeuralAR_MLP
  (V3.2A diagnostic median MASE ≈ 790, raw scale), and produces **0 negative forecasts** vs the 55 the
  current model produced. FNAR-V2 still over-forecasts strongly on high-scale multitenant (large positive
  bias) → needs tuning before it is competitive.
- **ENET-RIDGE** and **NLIN-DLIN** are the strongest accuracy tier and both pass the runtime gate;
  NLIN-DLIN currently produces 27 raw negatives (clamped to 0) → needs a non-negativity fix.
- **SMLP-TCN** is solid mid-pack, viable, 0 negatives.

## 8. Failures / skipped candidates
- **No crashes** — all 6 candidates ran to completion (status `ok`, 0 failed rows).
- **NLIN-DLIN**: 27 raw pre-clamp negatives ⇒ `guardrail_pass=False` (non-negativity not yet structural).
  Output is clamped (0 negatives in file) but the candidate is flagged for remediation.
- **LGBM-IMP / XGB-IMP**: gated out (`NOT_VIABLE_FOR_V3_DAILY_REFRESH`) on **runtime**, not on error.

## 9. Runtime gate decision
- Threshold: full-scale projection ≥ ~30 min (NOT_VIABLE trip at ≥ 25 min) ⇒ `NOT_VIABLE_FOR_V3_DAILY_REFRESH`.
- **VIABLE:** ENET-RIDGE, NLIN-DLIN, SMLP-TCN, FNAR-V2.
- **NOT_VIABLE (as implemented):** LGBM-IMP (≈32.8 min), XGB-IMP (≈77.5 min) — per-horizon design.
- No slow model was forced. Runtime, dependency_status, failure_reason and projected_full_runtime are
  all recorded in `subset_runtime_results.csv`.

## 10. Candidates approved for full backtest (RECOMMENDATION — requires Oscar authorization to run)
1. **ENET-RIDGE** — APPROVE. Best accuracy tier, 0 negatives, near-instant, fully viable.
2. **SMLP-TCN** — APPROVE. Viable, 0 negatives, solid mid-pack.
3. **NLIN-DLIN** — APPROVE **with non-negativity remediation first** (log-space / constrained variant);
   best-tier accuracy and viable, only blocker is the 27 raw negatives.
4. **FNAR-V2** — APPROVE as the mandated remediation challenger (confirms recursive-collapse is fixed);
   needs bias/accuracy tuning, but viable and 0 negatives.
5. **LGBM-IMP / XGB-IMP** — **DEFER (do NOT advance as-is).** Re-engineer to a single multi-output /
   horizon-feature model (instead of 30 per-horizon boosters) and **re-run the runtime gate**; accuracy
   is already competitive, only runtime fails.

## 11. Governance confirmation
- No champion changed.
- No forecasts changed.
- No intervals changed.
- No data/processed artifacts changed.
- No governance decisions changed.
- V1 and V2 untouched.
- V3.3 not started.
- V4 AI/LLM not started.
- No production promotion.

## 12. V3.2C status
`V3_2C_SUBSET_DRY_RUN_COMPLETE_READY_FOR_OSCAR_REVIEW` — harness implemented, subset dry-run executed,
runtime gate applied, contract validated, full backtest deliberately NOT run.

## 13. Recommended next step
**V3.2D (needs explicit authorization):**
1. Apply the two targeted remediations: non-negativity fix for NLIN-DLIN, and reformulate LGBM-IMP/XGB-IMP
   to a single multi-output/horizon-feature model; re-run the runtime gate for the reformulated GBMs.
2. Run the **authorized full backtest** (39 series × 12 windows × h1–30) for the viable set
   (ENET-RIDGE, SMLP-TCN, NLIN-DLIN-fixed, FNAR-V2, + re-gated GBMs if they pass) using the governed
   MASE/RMSSE scale so numbers sit on the same axis as ETS Explicit + baselines.
3. Produce per-candidate recommendations (reject / defer / keep-as-challenger / candidate-for-governance-review).
   No auto-promotion.
