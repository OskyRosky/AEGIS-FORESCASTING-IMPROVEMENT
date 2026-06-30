# V3.3C-fit — Clean Challenger Live-Fit Trainer

**Stage status:** `V3_3C_FIT_CLEAN_CHALLENGERS_COMPLETED`
**Date:** 2026-06-27
**Scope:** Implement a clean, torch-free live-fit path for the 5 remaining clean
challengers, without using the contaminated legacy runner, and leave the daily
15-model runner prepared for the corrected benchmark.

---

## 1. Executive summary

The 5 clean challengers (AutoARIMA, ETS Explicit, Theta, LightGBM, XGBoost) now
have a working **clean live-fit** path implemented in
`python/model_lab/run_daily_clean_challengers.py`. The path is **torch-free**,
imports its model libraries **lazily** (only under `--execute`), and **never**
imports the legacy NBEATS/NHITS challenger runner or the model registry (which
would pull in NBEATS/NHITS at module load).

A bounded **smoke test** (1 entity × 1 window) fit all 5 challengers
successfully: **5/5 SMOKE_PASS**, 30-day horizon each, **150 forecast rows**,
**0 NaN**. All output was written to **staging only**. No champion change, no
promotion to `data/processed`, no productive forecast or interval change, no
governance change.

The full clean live-fit across all entity-windows remains **gated behind
benchmark authorization** and was **not** executed in this stage.

---

## 2. Why this stage was needed

Stage V3.3C-exec (`V3_3C_EXECUTION_WIRING_COMPLETED`) wired execution routing but
left the 5 clean challengers marked `EXECUTION_PATH_NOT_READY`, because:

- The legacy daily challenger runner is **contaminated** — it imports NBEATS /
  NHITS and the retired FastNeuralAR_MLP original, which are prohibited models.
- `model_lab/models/model_registry.py` imports `NBEATSModel` and `NHITSModel` at
  module top level, so importing the registry violates the no-NBEATS/NHITS rule.
- The 5 registry challenger classes (AutoARIMAModel, ETSModel, ThetaModel,
  LightGBMModel, XGBoostModel) are **placeholders** raising `NotImplementedError`;
  the real fit logic lived only inside the contaminated legacy runner.

This stage delivers a clean replacement fit path so the challengers can
participate in the corrected benchmark **without** touching any prohibited code.

---

## 3. 15-model canonical universe (unchanged)

| Family | Count | Models |
|---|---|---|
| Growth baseline | 4 | FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6 |
| Statistical | 5 | ARIMA_Fixed, AutoARIMA, ETS Explicit, ETS_Current, Theta |
| Machine learning | 3 | LightGBM, LinearRegression, XGBoost |
| Deep Learning | 3 | FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN |

Total = 15. Prohibited models (NBEATS, NHITS, FastNeuralAR_MLP original) are
**not** in scope.

---

## 4. Clean challenger live-fit implementation

Five clean forecaster functions were replicated (torch-free, lazy-import) into
`run_daily_clean_challengers.py`:

| Model | Family | job_plan name | Library | Method |
|---|---|---|---|---|
| AutoARIMA | Statistical | AutoARIMA | pmdarima | `auto_arima` (seasonal=False, max_p/q=2) |
| ETS Explicit | Statistical | ETS | statsmodels | `ExponentialSmoothing` (trend=add, seasonal=None) |
| Theta | Statistical | Theta | statsmodels | `tsa.forecasting.theta.ThetaModel` (deseasonalize=False) |
| LightGBM | Machine learning | LightGBM | lightgbm | `LGBMRegressor` recursive (n_lags=7, n_estimators=100) |
| XGBoost | Machine learning | XGBoost | xgboost | `XGBRegressor` recursive (n_lags=7, n_estimators=100) |

Design choices:
- **Theta uses statsmodels**, not darts, to remain strictly torch-free.
- All fits are deterministic (RANDOM_SEED=42, single-threaded trees).
- Training slice bounded by `train_start_date..train_end_date`; forecast horizon
  is 30 days (`test_start_date..test_end_date`) from the data contract.
- No model is ever invented: a fit failure is captured as `failed` with the
  blocker recorded; it never emits placeholder values.

The 3 Deep Learning models are **not** challengers here — they are wired as
`reuse_frozen_artifact` (no live training, reuse closed V3.2B output).

---

## 5. Smoke test result

| Model | Fit attempted | Status | Rows | NaN |
|---|---|---|---|---|
| AutoARIMA | TRUE | SMOKE_PASS | 30 | 0 |
| ETS Explicit | TRUE | SMOKE_PASS | 30 | 0 |
| Theta | TRUE | SMOKE_PASS | 30 | 0 |
| LightGBM | TRUE | SMOKE_PASS | 30 | 0 |
| XGBoost | TRUE | SMOKE_PASS | 30 | 0 |

Total: **5/5 passed**, **150 forecast rows**, **0 NaN**. Mode = `smoke_test`
(1 entity × 1 window). Output: `staging/clean_challenger_fit_outputs.csv`.

---

## 6. What is ready for the benchmark

- **5 clean challengers** — clean live-fit path validated; status
  `CLEAN_LIVE_FIT_READY` / `READY_FOR_BENCHMARK_AUTHORIZATION`.
- **3 Deep Learning models** — `FROZEN_REUSE` (reuse closed V3.2B candidate
  output); no training required.
- **7 baseline/stat/ML models** (4 growth + ARIMA_Fixed + ETS_Current +
  LinearRegression) — route via `run_full_baseline_execution.py`,
  `READY_FOR_BENCHMARK_AUTHORIZATION`.

The full 15-model daily runner is prepared and consistent (master light modes
report 15 models / 0 prohibited).

---

## 7. What remains missing / gated

- The **full clean live-fit** across all entity-windows (up to 454 windows) was
  **not** run — gated behind explicit benchmark authorization.
- The **corrected full benchmark** end-to-end was **not** run.
- No scheduler created. No V3.3D / V3.3E / V3.3F started. No V4 started.

---

## 8. Governance confirmation

- **No legacy contaminated runner used**; no NBEATS/NHITS/registry import.
- **Prohibited-model guard: CLEAN** (NBEATS, NHITS, FastNeuralAR_MLP all
  excluded from active daily scope; legacy presence documented).
- **Staging only** — no promotion to `data/processed` (verified: no files
  modified after 2026-06-27).
- **No champion change, no productive forecast change, no interval change, no
  governance change.**
- **V1 / V2 untouched.**

---

## 9. Recommended next step

Request explicit authorization to run the **corrected full benchmark** (or a
larger bounded `--max-windows` validation) using the clean challenger live-fit
path, the DL frozen-reuse artifacts, and the baseline generation path, then
compare against the current champion under governance review.

> Full benchmark / full 454-window execution requires your explicit
> authorization and was deliberately **not** performed in this stage.
