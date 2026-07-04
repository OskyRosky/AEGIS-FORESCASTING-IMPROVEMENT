# V3.2B — Model Candidate Experimental Harness + Lightweight Candidate Design

**Stage:** V3.2B (scaffolding + design only — no training, no replacement, no promotion)
**Scope:** V3 only. V1 and V2 untouched.
**Date:** 2026-06-25
**Status:** V3_2B_HARNESS_DESIGNED_READY_FOR_OSCAR_REVIEW

> This stage builds the governed experimental framework to evaluate replacement/improvement
> candidates for FastNeuralAR_MLP. No model was trained, no forecast was produced, no champion
> or governed artifact was modified. Heavy training is deferred to V3.2C and requires explicit
> authorization. Principle: **runtime first**.

---

## 1. Files created

All under `outputs/v3_2b_model_candidates/` (new, isolated experiment workspace):
- `report.md` (this file)
- `validation.csv` (25 checks)
- `candidate_registry.csv` (6 candidates + 5 reference/excluded anchors)
- `experiment_contract.csv` (21-field output data dictionary)
- `backtest_plan.md`
- `runtime_risk_assessment.md`
- `candidate_outputs/README.md`
- `metrics/README.md`
- `logs/README.md`
- `runtime_checks/README.md`

Directories created: `candidate_outputs/`, `metrics/`, `logs/`, `runtime_checks/`.

## 2. Files modified

None. No existing file was modified. (Repo memory updated separately as a working note, not a
project artifact.)

## 3. Candidate strategy

Do **not** replace the model blindly. Build a governed experimental harness and evaluate a small
set of **lightweight, comparable, operable** candidates against the frozen champion (ETS Explicit)
and the existing baselines, with a hard **runtime-first** gate. Three lanes:

1. **Remediation** of the current model → `FastNeuralAR_MLP_v2_direct` (fix the diagnosed root cause).
2. **Lightweight DL** → NLinear/DLinear and SmallTCN/SmallMLPGlobal (small, epoch-capped, CPU-sized).
3. **ML** → improved LightGBM, improved XGBoost, ElasticNet/Ridge multi-horizon (often the most
   practical for a daily refresh).

N-BEATS / N-HiTS are **excluded as primary candidates** (prior colossal runtime; deferred fallbacks only).

## 4. FastNeuralAR_MLP_v2 remediation plan

`FNAR-V2 / FastNeuralAR_MLP_v2_direct` directly attacks the V3.2A diagnosis (recursive collapse +
negative forecasts + scale issues):
- **No recursive multi-step** as the primary implementation. Use **direct multi-horizon** output
  (predict h1..h30 without feeding predictions back as lags) → removes the compounding-error path.
- **Target transform `log1p`** on the series, with a **safe inverse (`expm1`)** → stabilizes scale
  on high-magnitude multi-tenant series.
- **Non-negative clamp** on the inverse-transformed output → eliminates the 55 negative forecasts
  seen in V3.2A.
- **Early stopping** + **L2 regularization** → reduce the high-variance single-layer behavior.
- **Record** runtime_seconds, negative_forecast_count (pre-clamp), and guardrail pass/fail per series.

## 5. Lightweight DL candidates

- **`NLIN-DLIN / NLinear_or_DLinear_lightweight`** (family `linear_dl`, torch 2.12.0+cpu): a
  near-linear layer over a fixed lookback window. Implement simple and controlled; **epoch cap +
  early stopping mandatory**; runtime gate mandatory. If not viable, mark dependency/runtime status
  and do not force.
- **`SMLP-TCN / SmallTCN_or_SmallMLPGlobal`** (family `lightweight_neural`, torch 2.12.0+cpu): a
  deliberately **small** net with a **strict epoch/iteration cap**, early stopping, and non-negative
  clamp. If TCN's CPU runtime is poor, fall back to **SmallMLPGlobal** (a single global one-pass MLP).
  No large architecture is built.

## 6. ML candidates

- **`LGBM-IMP / LightGBM_candidate_improved`** (gradient_boosting) — already stable and mid-pack in
  V3.2A; improved tuning, direct multi-horizon, runtime recorded.
- **`XGB-IMP / XGBoost_candidate_improved`** (gradient_boosting) — same evaluation structure.
- **`ENET-RIDGE / ElasticNet_or_Ridge_direct_multi_horizon`** (linear_ml) — convex, fastest fallback,
  non-negative clamp.
All ML candidates use the **same horizons, same series, same windows, same champion/baseline
comparison**, runtime recorded, **no auto-promotion**.

## 7. Runtime gate

Mandatory and applied in V3.2C **before** any full backtest:
- **Subset dry-run first** (5 series, reduced windows), total target **<= 3-5 minutes**.
- Record `runtime_seconds` + `runtime_per_series` in `runtime_checks/runtime_gate_results.csv`.
- Project to full scope (39 series × 12 windows). If a candidate approaches **~30 minutes**, mark it
  `NOT_VIABLE_FOR_V3_DAILY_REFRESH` and skip the full backtest.
- Any candidate that fails to run or exceeds the gate is marked `deferred`/`excluded` with a
  `failure_reason`. Never silently dropped, never force-run.

## 8. Experiment contract

`experiment_contract.csv` defines the standard schema every candidate output row must follow (21
fields): candidate_id, model_name, model_family, series_key, forecast_origin, horizon,
forecast_date, forecast_value, actual_value, error, abs_error, squared_error, mase, rmsse,
smape_or_mae_if_available, runtime_seconds, status, failure_reason, guardrail_pass,
negative_forecast_count, notes. This guarantees every candidate is measured identically and is
directly comparable to the V3.2A scorecard axis.

## 9. Backtest plan

`backtest_plan.md` fixes: the 39-series universe (+ 5-series deterministic dry-run subset),
horizons h1..h30, expanding walk-forward (12 windows, MIN_TRAIN=365, aligned to
`config/backtesting.yaml`), metrics (MASE primary, RMSSE guardrail, sMAPE/wMAPE/bias/negatives +
runtime), comparison anchors (ETS Explicit + baselines, never re-fit), failure handling, guardrails
(non-negativity, MASE/RMSSE, horizon-stability), and promotion/rejection criteria. Same cutoffs and
windows for every candidate and anchor → apples-to-apples deltas.

## 10. Dependency assessment

Verified in the V3 Python environment on 2026-06-25 (all importable):

| Package | Version | Used by |
|---|---|---|
| python | 3.14.6 | all |
| numpy | 2.4.6 | all |
| pandas | 3.0.3 | all |
| scikit-learn | 1.9.0 | FNAR-V2, ElasticNet/Ridge |
| scipy | 1.17.1 | metrics |
| lightgbm | 4.6.0 | LightGBM improved |
| xgboost | 3.2.0 | XGBoost improved |
| torch | 2.12.0+cpu | NLinear/DLinear, SmallTCN/SmallMLPGlobal |
| darts | 0.44.1 | (deferred) N-BEATS/N-HiTS only |
| statsmodels | 0.14.6 | available |

Key constraint: **torch is CPU-only** (`torch.cuda.is_available() == False`) → all DL candidates
must be CPU-sized (small width, low epoch cap, early stopping). No new dependency installs required.

## 11. Governance confirmation

- No champion changed. ✅ (ETS Explicit remains the governed champion under conditions.)
- No forecasts changed. ✅
- No intervals changed. ✅
- No data/processed artifacts changed. ✅
- No governance decisions changed. ✅
- V1 and V2 untouched. ✅
- V3.3 not started. ✅ (no daily job/orchestrator)
- V4 AI/LLM not started. ✅
- No production promotion. ✅ (no candidate implemented or trained; harness/design only)

## 12. V3.2B status

`V3_2B_HARNESS_DESIGNED_READY_FOR_OSCAR_REVIEW`. The experimental framework, candidate registry,
output contract, backtest plan, and runtime gate are defined. No training executed.

## 13. Recommended V3.2C plan

1. Implement the 6 candidates behind one isolated harness script in `python/model_lab/` that writes
   ONLY to `outputs/v3_2b_model_candidates/`.
2. **Subset dry-run** (5 series, reduced windows) → fill `runtime_checks/runtime_gate_results.csv`.
   Apply the runtime gate; mark any candidate `NOT_VIABLE_FOR_V3_DAILY_REFRESH`.
3. For candidates that pass: **full backtest** (39 series, 12 windows, h1..h30) →
   `candidate_outputs/*.csv` + `metrics/*.csv`, all conforming to `experiment_contract.csv`.
4. **Compare** against ETS Explicit and baselines (never re-fit anchors).
5. Produce a per-candidate recommendation: **reject / defer / keep as challenger / candidate for
   governance review** — with NO auto-promotion. Promotion stays a separate Oscar-authorized step.
