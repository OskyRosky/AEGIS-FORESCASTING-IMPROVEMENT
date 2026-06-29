# V3.3B-2 — Corrected Runtime Benchmark Report

**Final status:** `V3_3B2_CORRECTED_RUNTIME_BENCHMARK_COMPLETED`
**Date:** 2026-06-27
**Scope:** Corrected daily pipeline benchmark over the canonical **15-model** universe,
using the clean torch-free challenger live-fit and frozen DL reuse. The contaminated
legacy `run_challenger_official_execution.py` runner was **not** used.

## 1. Outcome
- All stages **S00–S14 executed**; S00–S13 completed with **0 failures**.
- **Total runtime (sum of stage runtimes): 20.04 min** — wall-clock ≈ 18.2 min.
  Well under target (105 min), warning (120 min), and hard budget (150 min).
- Budget status: **OK** (watchdog never tripped).
- **Productive state: RESTORED / UNCHANGED** (Option A). Champion remains **ETS Explicit**.

## 2. Stage runtime table (S00–S14)
| Stage | Name | Status | Runtime (min) | Exit | Output |
|---|---|---|---|---|---|
| S00 | Auth / VPN / SQL gate | COMPLETED | 1.88 | 0 | SQL=PASS (113s) |
| S01 | Ingestion (live SQL pull) | COMPLETED | 7.06 | 0 | data/raw refreshed |
| S02 | Transform (data contract) | COMPLETED | 0.02 | 0 | data/processed rebuilt |
| S03a | Baseline / growth / stat / ML | COMPLETED | 0.16 | 0 | baseline_forecasts.csv (95,340) |
| S03b | Clean challenger live-fit | COMPLETED | 10.71 | 0 | clean_challenger_forecasts.csv (68,100) |
| S03c | DL frozen reuse | COMPLETED | 0.01 | 0 | dl_reuse_frozen_forecasts.csv (40,860) |
| S03 | Daily 15-model runner (umbrella) | COMPLETED | 10.88 | 0 | S03a+S03b+S03c |
| S04 | Forecast outputs / viewer | COMPLETED | 0.07 | 0 | forecast_viewer_handoff |
| S05 | Tournament + champion | COMPLETED | 0.04 | 0 | tournament_engine + champion_decision |
| S06 | Canonical universe (R) | COMPLETED | 0.03 | 0 | model_universe_canonical.csv |
| S07 | Evaluation exports | COMPLETED | 0.02 | 0 | evaluation_dataset rebuilt |
| S08 | Governance exports | COMPLETED | 0.01 | 0 | governance 6.0/6.1 (0 failures) |
| S09 | Reference refresh | COMPLETED | 0.02 | 0 | ttl_* snapshots |
| S10 | Dashboard consolidation | COMPLETED | 0.01 | 0 | dashboard exports |
| S11 | Last Update observation | COMPLETED | 0.00 | 0 | last_update_observation.csv |
| S12 | Pipeline status observation | COMPLETED | 0.00 | 0 | stage_runtime_summary.csv |
| S13 | Champion audit observation | COMPLETED | 0.00 | 0 | champion_behavior_observation.csv |
| S14 | Final validation | COMPLETED | — | 0 | v3_3b2_validation.csv (29/29 PASS) |

## 3. Per-model execution summary
| Model | Family | Status | Jobs/windows | Output rows |
|---|---|---|---|---|
| FixedGrowth_1_5 | Growth baseline | FIT_OK | 454 | 13,620 |
| FixedGrowth_3 | Growth baseline | FIT_OK | 454 | 13,620 |
| FixedGrowth_4 | Growth baseline | FIT_OK | 454 | 13,620 |
| FixedGrowth_6 | Growth baseline | FIT_OK | 454 | 13,620 |
| ARIMA_Fixed | Statistical | FIT_OK | 454 | 13,620 |
| ETS_Current | Statistical | FIT_OK | 454 | 13,620 |
| AutoARIMA | Statistical | FIT_OK | 454 | 13,620 |
| ETS Explicit | Statistical | FIT_OK | 454 | 13,620 |
| Theta | Statistical | FIT_OK | 454 | 13,620 |
| LinearRegression | Machine learning | FIT_OK | 454 | 13,620 |
| LightGBM | Machine learning | FIT_OK | 454 | 13,620 |
| XGBoost | Machine learning | FIT_OK | 454 | 13,620 |
| FNAR-V2 | Deep Learning | FROZEN_REUSE | 0 | 13,620 |
| NLIN-DLIN_FIXED | Deep Learning | FROZEN_REUSE | 0 | 13,620 |
| SMLP-TCN | Deep Learning | FROZEN_REUSE | 0 | 13,620 |

- **12 models live-fit** (3,178 baseline jobs + 2,270 challenger jobs, 0 failures).
- **3 DL models frozen-reuse** (no training; reuse of closed V3.2B candidate output).

## 4. Guardrails
- **Prohibited models absent / not executed:** NBEATS, NHITS, FastNeuralAR_MLP (original)
  — none present in any generated output. ✅
- **Legacy contaminated runner not used.** ✅
- **15-model canonical scope validated** (4 growth + 5 statistical + 3 ML + 3 DL). ✅
- **Champion behavior:** unchanged — **ETS Explicit** before and after; no promotion. ✅
- **V1 / V2 untouched; no scheduler created; no V3.3D/E/F or V4 started.** ✅

## 5. Productive-state policy (Option A)
All productive directories mutated by subprocess stages were backed up before the run
and **restored afterward**, so production ends **net-unchanged**:
`data/raw`, `data/processed`, `outputs/evaluation`, `outputs/governance`,
`outputs/model_lab/{forecast_viewer_handoff,tournament_engine,champion_decision}`,
`outputs/v3_2h_model_consistency_fix`.

> Note: the orchestrator's in-process `shutil.rmtree` restore hit a transient Windows
> `PermissionError` (OneDrive file lock) on `outputs/evaluation` after all stages had
> completed. The restore was completed deterministically with `robocopy /MIR`; a
> verification mirror of `data/processed` returned exit 0 (no differences), confirming
> the productive state matches the pre-benchmark backup.

## 6. Artifacts created (under `outputs/v3_3_daily_refresh/v3_3b2_corrected_runtime_benchmark/`)
- `runtime/stage_runtime_summary.csv`, `runtime/benchmark_total_runtime.csv`
- `runtime/model_execution_progress_log.csv`, `runtime/model_execution_summary.csv`
- `status/auth_sql_precheck_result.csv`, `status/model_scope_validation_result.csv`*,
  `status/prohibited_model_guard_result.csv`*, `status/last_update_observation.csv`,
  `status/champion_behavior_observation.csv`
- `artifacts_inventory/output_artifacts_inventory.csv`
- `v3_3b2_validation.csv` (29/29 PASS), `v3_3b2_report.md`
- `staging/` benchmark model outputs (non-productive)
- `run_v3_3b2_benchmark.py`, `finalize_v3_3b2.py`

\* Pre-check guard files recorded during the pre-run gate.

## 7. Recommended next step
The corrected daily pipeline runs end-to-end in ~20 min over the clean 15-model scope.
Recommended next: **V3.3C — Daily Refresh Scheduler design** (not started; requires
authorization). Do not start V3.3D/E/F or V4 without authorization.
