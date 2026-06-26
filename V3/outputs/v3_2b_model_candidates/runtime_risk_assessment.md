# V3.2B — Runtime Risk Assessment

**Scope:** V3 only. Governs which candidates are allowed into the V3.2C dry-run and full backtest.
**Guiding principle (Oscar):** *runtime first*. A model that cannot run inside a future daily
refresh window is not useful, no matter how accurate.

---

## 1. Why N-BEATS / N-HiTS are NOT primary candidates

- Both are heavy deep stacked-residual architectures. In prior AEGIS work they showed
  **colossal runtime** and were already **deferred** in the governed risk register
  (NBEATS/NHITS, deferred for runtime/dependency).
- For a forecasting universe fit **per series × per window** (39 series × 12 windows = 468 fits
  per candidate, ×30 horizons), per-fit cost dominates. Deep residual stacks make each fit
  expensive enough to threaten any daily-refresh budget.
- They remain **available** (`darts 0.44.1`) and are kept as deferred fallbacks ONLY if every
  lightweight candidate fails. They are explicitly excluded as PRIMARY candidates per V3.2B
  rule 13.

## 2. Which candidates are lightweight (preferred)

| Candidate | Why lightweight |
|---|---|
| FastNeuralAR_MLP_v2_direct | Single small MLP, direct multi-horizon (one fit, no 30-step recursion), early stopping, L2 |
| NLinear / DLinear | Essentially a linear layer over a lookback window; very few parameters; epoch-capped |
| SmallTCN / SmallMLPGlobal | Deliberately tiny net, strict epoch/iteration cap; SmallMLPGlobal is a global one-pass MLP |
| LightGBM (improved) | Gradient boosting, fast on tabular lag features; already mid-pack and stable in V3.2A |
| XGBoost (improved) | Same class; fast histogram boosting |
| ElasticNet / Ridge (direct multi-horizon) | Closed-form/convex linear fit; the fastest fallback of all |

## 3. Which candidates require a dependency check

- All six primary candidates' dependencies are **already installed** in the V3 environment
  (verified 2026-06-25): `numpy 2.4.6`, `pandas 3.0.3`, `scikit-learn 1.9.0`, `scipy 1.17.1`,
  `lightgbm 4.6.0`, `xgboost 3.2.0`, `torch 2.12.0+cpu`, `darts 0.44.1`, `statsmodels 0.14.6`.
- **torch is CPU-only** (`torch.cuda.is_available() == False`). The DL candidates (NLinear/DLinear,
  SmallTCN/SmallMLPGlobal) must therefore be sized for CPU: small width, low epoch cap, early
  stopping. This is the main dependency-driven runtime constraint.
- TCN uses 1-D convolutions; if CPU runtime is poor it is dropped in favor of **SmallMLPGlobal**
  (the registered fallback) — no large architecture is built either way.

## 4. Runtime gate to be applied (in V3.2C)

1. **Subset dry-run first, always.** 5 series, reduced windows. Target total **<= 3-5 minutes**.
2. Record `runtime_seconds` and `runtime_per_series` in `runtime_checks/runtime_gate_results.csv`.
3. Extrapolate to full scope (39 series × 12 windows). If projected full runtime is reasonable
   for a future daily job, the candidate is allowed into the full backtest.
4. If a candidate approaches **~30 minutes** (subset-projected or observed), mark it
   `NOT_VIABLE_FOR_V3_DAILY_REFRESH` and DO NOT run the full backtest.
5. Record `failure_reason` for any candidate that cannot run or exceeds the gate.

## 5. When to discard a model for cost/time

- Subset dry-run fails to complete within the 3-5 minute target with no easy lightweight fix.
- Projected full runtime is incompatible with a daily refresh (≈30 min threshold).
- Dependency/numeric problems that cannot be resolved without heavy engineering.
- In all cases: mark `deferred`/`excluded` with a reason; never silently drop, never force-run.

## 6. Expected runtime ranking (a priori, to be confirmed empirically in V3.2C)

Fastest → slowest (expected): ElasticNet/Ridge < LightGBM ≈ XGBoost <
FastNeuralAR_MLP_v2_direct < NLinear/DLinear < SmallTCN/SmallMLPGlobal ≪ (excluded) N-BEATS/N-HiTS.
