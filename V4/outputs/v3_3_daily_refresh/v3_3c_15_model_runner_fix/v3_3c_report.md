# V3.3C — 15-Model Daily Runner Fix

**Status:** `V3_3C_15_MODEL_RUNNER_FIX_COMPLETED`
**Date:** 2026-06-26
**Scope:** Build the clean daily 15-model runner (scope/guard/plan). No training, no backtest, no benchmark, no scheduler, no champion change, no model promotion, no V3.3D/E/F, no V4. V1/V2 untouched.

---

## 1. Executive summary

A new clean entrypoint **`python/model_lab/run_daily_15_model_refresh.py`** is now the canonical model-stage entrypoint for the V3.3 daily pipeline. It is **dependency-light (stdlib only)** so `--dry-run`, `--validate-scope` and `--plan` never import torch/darts and never touch productive outputs.

It encodes the **canonical 15-model universe** as a single source of truth, classifies every model by execution type, and enforces a **reusable prohibited-model guard** (NBEATS / NHITS / FastNeuralAR_MLP). All three permitted modes were executed and **PASS**; the dry-run prints exactly the 15 models with **zero prohibited models** and ends with `DAILY_15_MODEL_SCOPE_VALIDATED`. The scope also cross-checks clean against `data/processed/model_universe_canonical.csv` (15/15 match).

The legacy `run_challenger_official_execution.py` is explicitly **excluded** from the daily execution path while it hard-codes NBEATS.

## 2. Why V3.3B became partial

V3.3B invoked the legacy challenger runner, whose `APPROVED_MODELS` includes `"NBEATS"` (a heavy torch/CPU DL model). NBEATS did not finish within the 17-minute probe and was stopped; the stage was marked `STOPPED_NOT_IN_SCOPE` and V3.3B closed partial. Root cause = a prohibited model hard-coded into the only challenger execution list. V3.3C removes that runner from the daily path and replaces it with a guarded, scope-pure entrypoint.

## 3. Canonical 15-model runner design

Single source of truth = the `MODELS` table inside the runner (15 entries, 4 families). Each model carries: `family`, `action` (generate/train/reuse_frozen_artifact), `execution_type`, `entrypoint`, `entrypoint_status`, `output`, `status`, `missing_work`.

Modes:
- **`--validate-scope`** — checks count=15, family counts 4/5/3/3, DL names correct, prohibited absent, and soft cross-check vs the canonical CSV. Writes `model_training_scope.csv` + `prohibited_model_guard_result.csv`.
- **`--dry-run`** — prints the 15 models + per-model action, runs the guard, writes `daily_15_model_dry_run.csv` + `prohibited_model_guard_result.csv`. Ends `DAILY_15_MODEL_SCOPE_VALIDATED`.
- **`--plan`** — emits the staged execution plan (`daily_15_model_runner_plan.csv`), no execution.
- **`--execute`** — **BLOCKED**: requires `--allow-execute`, and even then prints `EXECUTE_NOT_IMPLEMENTED_IN_V3_3C` and exits (no training).

## 4. Prohibited model guard

`prohibited_model_guard(active_models)` is reusable and case-insensitive. If any of `NBEATS`, `NHITS`, `FastNeuralAR_MLP` appears in the active scope, the run aborts with `PROHIBITED_MODEL_IN_DAILY_SCOPE` (exit 2). Verified by unit test: injecting `['ETS Explicit','NBEATS','NHITS','XGBoost']` returned `['NBEATS','NHITS']` and the violation token. The canonical 15 scope returns **CLEAN**.

## 5. Models trained / generated daily

| Action | Count | Models | Entrypoint | Ready |
|---|---|---|---|---|
| generate | 4 | FixedGrowth_1_5/3/4/6 | run_full_baseline_execution.py | READY |
| train (baseline runner) | 3 | ARIMA_Fixed, ETS_Current, LinearRegression | run_full_baseline_execution.py | READY |
| train (challenger) | 5 | AutoARIMA, ETS Explicit, Theta, LightGBM, XGBoost | clean challenger variant (TBD) | GAP |

→ **7 of 15 are train/generate-ready today** via the clean baseline runner. **5 of 15** are train-daily models whose only current producer is the contaminated legacy challenger runner (gap — see §7).

## 6. Models reused as frozen artifacts

| Model | Family | Source | Action |
|---|---|---|---|
| FNAR-V2 | Deep Learning | full_candidate_outputs.csv (V3.2B) | reuse_frozen_artifact |
| NLIN-DLIN_FIXED | Deep Learning | full_candidate_outputs.csv (V3.2B) | reuse_frozen_artifact |
| SMLP-TCN | Deep Learning | full_candidate_outputs.csv (V3.2B) | reuse_frozen_artifact |

These 3 have **no live training code**. They are reused as frozen evidence from the closed V3.2B/D/E candidate study, aggregated by `build_canonical_universe.R`.

## 7. Missing execution paths

1. **Clean challenger entrypoint** for AutoARIMA, ETS Explicit, Theta, LightGBM, XGBoost — currently only produced by `run_challenger_official_execution.py`, which hard-codes NBEATS. Required: a parameterized clean runner (model list injected, NBEATS/NHITS excluded, guard called).
2. **Daily DL training** for FNAR-V2 / NLIN-DLIN_FIXED / SMLP-TCN — no live trainer exists. To train daily, the V3.2B candidate-study trainer must be located/rebuilt (out of daily scope today). Until then, reuse frozen artifacts.

## 8. Why NBEATS / NHITS / FastNeuralAR_MLP are excluded

- **NBEATS / NHITS** — governance-deferred (TEST_LATER + DEFER, GR-004/GR-005), heavy torch/CPU, not in the canonical 15, and NBEATS caused the V3.3B partial. Their class files and registry entries remain as historical code but are blocked from the daily scope by the guard.
- **FastNeuralAR_MLP (original)** — RETIRED (MASE 739.9, high risk); explicitly filtered out by `build_canonical_universe.R` and superseded by FNAR-V2.

## 9. Files created

- `python/model_lab/run_daily_15_model_refresh.py` (new clean runner)
- `outputs/v3_3_daily_refresh/v3_3c_15_model_runner_fix/model_training_scope.csv`
- `outputs/v3_3_daily_refresh/v3_3c_15_model_runner_fix/daily_15_model_dry_run.csv`
- `outputs/v3_3_daily_refresh/v3_3c_15_model_runner_fix/prohibited_model_guard_result.csv`
- `outputs/v3_3_daily_refresh/v3_3c_15_model_runner_fix/daily_15_model_runner_plan.csv`
- `outputs/v3_3_daily_refresh/v3_3c_15_model_runner_fix/v3_3c_report.md`
- `outputs/v3_3_daily_refresh/v3_3c_15_model_runner_fix/v3_3c_validation.csv`

## 10. Files modified

None. No existing source, config, forecast, interval, champion, or productive output was modified. (The legacy challenger runner was **not** edited — it is excluded by design, not changed.)

## 11. How to run dry-run

```powershell
$v3 = "C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V3"
Set-Location "$v3\python"; $env:PYTHONPATH = "$v3\python"
python model_lab\run_daily_15_model_refresh.py --dry-run
```
Result: prints the 15 models, `prohibited check : CLEAN`, ends `DAILY_15_MODEL_SCOPE_VALIDATED` (exit 0).

## 12. How to run validate-scope

```powershell
python model_lab\run_daily_15_model_refresh.py --validate-scope
```
Result: all checks PASS incl. `matches_canonical_universe_csv` (15/15), ends `DAILY_15_MODEL_SCOPE_VALIDATED` (exit 0).

## 13. Recommended path for the next benchmark

1. V3.3C-next: build the **clean challenger entrypoint** (§7.1) and wire DL **reuse** into the daily orchestrator.
2. Re-run `--dry-run` to confirm 15 models / 0 prohibited.
3. Only then re-run the corrected full benchmark (with your authorization), routing the model stage through `run_daily_15_model_refresh.py` instead of the legacy runner.

## 14. Risks / caveats

- 5 statistical/ML models still depend on a clean challenger entrypoint that does not yet exist; until built, a true daily run cannot regenerate them without touching the legacy (contaminated) runner.
- The 3 DL models are frozen; daily runs cannot retrain them.
- The runner is scope/plan/guard only — `--execute` is intentionally inert.

## 15. Next step

Authorize **V3.3C-next** (clean challenger entrypoint + DL reuse wiring), then a guarded dry-run, then the corrected benchmark. Do **not** start V3.3D/E/F or V4 without authorization.
