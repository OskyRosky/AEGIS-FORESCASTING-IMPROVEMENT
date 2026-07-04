# V3.3C-exec — Daily 15-Model Execution Wiring — Report

**Status token:** `V3_3C_EXECUTION_WIRING_COMPLETED`
**Date:** 2026-06-27
**Scope:** Execution-wiring only. No full 454-window run, no benchmark, no backtest,
no full daily refresh, no scheduler. Staging only — never promotes to
`data/processed`, never changes the champion.

---

## 1. What this stage did

Wired the real execution path for the daily 15-model runner so the pipeline can
execute/generate the allowed models and fuse the 3 Deep Learning models as
`reuse_frozen_artifact`, without ever using NBEATS, NHITS, or the original
FastNeuralAR_MLP.

- `--execute` is now implemented behind a mandatory `--allow-execute` flag.
- The 3 DL models are **executed now** as frozen reuse (no training).
- Baseline (7) and clean-challenger (5) live-fit paths are **wired but gated**
  behind benchmark authorization — they are documented, not run.

## 2. Files modified

| File | Change |
|------|--------|
| `python/model_lab/run_daily_15_model_refresh.py` | Added EXEC/staging paths, DL frozen name map, exec-status tokens, `execute_dl_reuse()`, `build_merged_status()`, exec artifact writers, rewrote `run_execute()` + parser/docstring. |
| `python/model_lab/run_daily_clean_challengers.py` | Added `execute_clean_challengers()` staging executor; rewired `run_execute()` to stage clean-challenger status; extended import + parser. |

## 3. Files created (staging / execution-wiring)

All under `outputs/v3_3_daily_refresh/v3_3c_exec_execution_wiring/`:

- `execution_plan.csv` — per-model execution plan (15 rows)
- `execution_wiring_status.csv` — per-component wiring status
- `staging_artifact_inventory.csv` — inventory of staged files
- `prohibited_model_guard_result.csv` — guard audit (CLEAN)
- `dl_reuse_execution_result.csv` — DL reuse result (3 rows)
- `staging/daily_15_model_outputs.csv` — merged 15-model manifest
- `staging/dl_reuse_frozen_forecasts.csv` — 40,860 re-staged frozen DL rows
- `staging/clean_challenger_execution_status.csv` — clean challenger status (5 rows)
- `v3_3c_exec_report.md` — this report
- `v3_3c_exec_validation.csv` — 24-check validation (all PASS)

## 4. Execution result per family

| Family | Models | Execution status | Notes |
|--------|--------|------------------|-------|
| Growth baseline (4) + ARIMA_Fixed, ETS_Current, LinearRegression | 7 | `READY_FOR_BENCHMARK_AUTHORIZATION` | Live gen/fit exists in `run_full_baseline_execution.py`; heavy full run gated behind benchmark auth. Not executed. |
| AutoARIMA, ETS Explicit, Theta, LightGBM, XGBoost | 5 | `EXECUTION_PATH_NOT_READY` | Clean live-fit trainer not yet implemented; routed to clean entrypoint; legacy NBEATS runner excluded. |
| FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN | 3 | `EXECUTED_REUSE_FROZEN` | Frozen V3.2B/D candidate-study outputs re-staged (13,620 rows each, 40,860 total). No training. |

## 5. DL display → frozen model mapping (verified)

| Dashboard code | Frozen internal model_name | Rows |
|----------------|----------------------------|------|
| FNAR-V2 | `FastNeuralAR_MLP_v2_direct` | 13,620 |
| NLIN-DLIN_FIXED | `NLinear_log_space_fixed` | 13,620 |
| SMLP-TCN | `SmallMLPGlobal` | 13,620 |

Source: `outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv`.

## 6. Prohibited model guard

`prohibited_model_guard()` ran before any staging work and returned **CLEAN**.
NBEATS, NHITS, and FastNeuralAR_MLP (original) are all absent from the active
scope. The legacy `run_challenger_official_execution.py` (which hard-codes
NBEATS) is **not** used as the daily runner.

## 7. Execution paths still missing (next authorized work)

- **Clean challenger live-fit trainer** (AutoARIMA, ETS Explicit, Theta,
  LightGBM, XGBoost): build a clean fit path parameterized by model list with
  NBEATS/NHITS excluded. Command when ready:
  `python python/model_lab/run_daily_clean_challengers.py --execute --allow-execute`.
- **Baseline full run** (7 models): exists but is a heavy full run —
  `python python/model_lab/run_full_baseline_execution.py` — gated behind
  benchmark authorization.

## 8. Safety confirmation

- Staging only — `data/processed` unchanged (no file newer than 2026-06-27).
- Champion unchanged (ETS Explicit). No forecast/interval/governance change.
- No scheduler created. No V3.3D/E/F or V4 work started. V1/V2 untouched.
- Full benchmark / 454-window run NOT executed.

## 9. Validation

24/24 checks PASS — see `v3_3c_exec_validation.csv`.

## 10. Recommended next step

Await authorization for the benchmark stage, then either (a) implement the clean
challenger live-fit trainer, or (b) run the gated baseline/benchmark execution
under explicit benchmark authorization.
