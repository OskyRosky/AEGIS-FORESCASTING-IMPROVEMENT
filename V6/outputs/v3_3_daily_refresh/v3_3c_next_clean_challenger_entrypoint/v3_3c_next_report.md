# V3.3C-next — Clean Challenger Entrypoint + DL Reuse Wiring

**Status:** `V3_3C_NEXT_CLEAN_CHALLENGER_ENTRYPOINT_COMPLETED`
**Date:** 2026-06-26
**Scope:** Build the clean challenger entrypoint, wire the 3 active DL models as `reuse_frozen_artifact`, and update the main 15-model runner plan. No training, no backtest, no benchmark, no scheduler, no champion change, no forecast/interval change, no governance change, no V3.3D/E/F, no V4. V1/V2 untouched.

---

## 1. Executive summary

`python/model_lab/run_daily_clean_challengers.py` is created as the clean daily challenger entrypoint. It references **only** the 5 allowed challengers from the canonical 15-model universe (AutoARIMA, ETS Explicit, Theta, LightGBM, XGBoost) and **never imports or references NBEATS / NHITS / FastNeuralAR_MLP**. The 3 active Deep Learning models (FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN) are wired as `reuse_frozen_artifact`. The main runner `run_daily_15_model_refresh.py` was updated so its plan now routes the 5 challengers to the clean entrypoint and reports **0 clean-entrypoint gaps**. All 6 permitted commands PASS.

## 2. Why this stage was needed

After V3.3C the main runner validated the 15-model scope, but the 5 statistical/ML challengers had **no clean producer** — their only existing path was the legacy `run_challenger_official_execution.py`, which hard-codes NBEATS in `APPROVED_MODELS`. V3.3C-next closes that gap with a dedicated clean entrypoint and formalizes the DL reuse decision.

## 3. Legacy runner issue

`run_challenger_official_execution.py` has `APPROVED_MODELS = [AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, NBEATS]` and `DEFERRED_MODEL = "NHITS"`. NBEATS is prohibited (heavy torch/CPU, governance-deferred, caused the V3.3B partial). That script is therefore **excluded from the daily execution path** and retained only as legacy/historical/research. It is **not modified** by this stage.

## 4. Clean challenger entrypoint design

`run_daily_clean_challengers.py` is stdlib-only and shares the reusable `prohibited_model_guard` (imported from `run_daily_15_model_refresh`). Modes:
- `--dry-run` — prints the 5 allowed challengers, runs the guard, writes `clean_challenger_scope.csv` + `prohibited_model_guard_result.csv`; ends `DAILY_CLEAN_CHALLENGER_SCOPE_VALIDATED`.
- `--validate-scope` — confirms count=5, each required model present, all within the canonical 15, and no prohibited model.
- `--plan` — writes `daily_runner_plan_updated.csv` + `dl_reuse_wiring.csv` + `clean_challenger_scope.csv`.
- `--execute` — BLOCKED (requires `--allow-execute`; even then prints `EXECUTE_NOT_IMPLEMENTED_IN_V3_3C_NEXT` and exits — no fitting).

## 5. Models included in the clean challenger entrypoint

| Model | Family | Challenger type | Action |
|---|---|---|---|
| AutoARIMA | Statistical | statistical_challenger | train |
| ETS Explicit | Statistical | statistical_challenger | train (CHAMPION) |
| Theta | Statistical | statistical_challenger | train |
| LightGBM | Machine learning | ml_challenger | train |
| XGBoost | Machine learning | ml_challenger | train |

## 6. Models excluded

NBEATS, NHITS, FastNeuralAR_MLP (original), any legacy Evaluation Challengers group, and anything outside the canonical 15. The guard aborts with `PROHIBITED_MODEL_IN_DAILY_SCOPE` if any appears (unit-verified previously with injected NBEATS/NHITS).

## 7. DL reuse wiring

`dl_reuse_wiring.csv` records the 3 active DL models as `reuse_frozen_artifact`:

| Model | Frozen source | Daily training available | Reuse status | Gap to daily training |
|---|---|---|---|---|
| FNAR-V2 | full_candidate_outputs.csv (V3.2B) | NO | frozen_closed_candidate_study_v3_2b | locate/rebuild candidate-study trainer |
| NLIN-DLIN_FIXED | full_candidate_outputs.csv (V3.2B) | NO | frozen_closed_candidate_study_v3_2b | locate/rebuild candidate-study trainer |
| SMLP-TCN | full_candidate_outputs.csv (V3.2B) | NO | frozen_closed_candidate_study_v3_2b | locate/rebuild candidate-study trainer |

No synthetic results were invented; no daily DL training was faked. The reuse is explicit and the gap to live training is documented.

## 8. Updated daily 15-model plan

`run_daily_15_model_refresh.py --plan` now reports: train daily (8), generate daily (4), reuse frozen (3), **clean-entrypoint gaps (0)**. Stage 2 of the plan routes the 5 challengers to `run_daily_clean_challengers.py` with status `READY`. See `daily_runner_plan_updated.csv` and the runner's `daily_15_model_runner_plan.csv`.

## 9. What is now ready for benchmark

- Stage 1 baseline (7 models) — clean & ready (`run_full_baseline_execution.py`).
- Stage 2 clean challengers (5 models) — clean entrypoint defined; scope/guard/plan ready.
- Stage 3 DL (3 models) — reuse frozen artifacts.
- Aggregation, tournament/champion, viewer handoff — ready.
The daily model path is now **scope-clean and prohibited-free** end-to-end.

## 10. What remains missing

- **Live fit execution** for the 5 clean challengers is scaffolded behind `--allow-execute` but intentionally not implemented in this stage (no training run now).
- **Daily DL training** for the 3 DL models has no live trainer; reuse-frozen until the V3.2B candidate-study trainer is located/rebuilt.

## 11. Risks / caveats

- The clean entrypoint defines the daily challenger scope and guard but does not yet fit models; a later authorized stage must implement the fit wiring (model classes via registry, NBEATS/NHITS excluded).
- DL models remain frozen; daily runs cannot retrain them.
- Legacy challenger runner remains in the repo (historical) — must never be wired into the daily path.

## 12. Recommended next step

Authorize the **execution-wiring stage** (implement `--allow-execute` fit for the 5 clean challengers + DL reuse merge), re-run dry-run to confirm 15/0-prohibited, then run the corrected benchmark (with your authorization). Do not start V3.3D/E/F or V4 without authorization.

## 13. Files created / modified

**Created:** `python/model_lab/run_daily_clean_challengers.py`; `outputs/v3_3_daily_refresh/v3_3c_next_clean_challenger_entrypoint/` → `clean_challenger_scope.csv`, `dl_reuse_wiring.csv`, `daily_runner_plan_updated.csv`, `prohibited_model_guard_result.csv`, `v3_3c_next_report.md`, `v3_3c_next_validation.csv`.
**Modified:** `python/model_lab/run_daily_15_model_refresh.py` (5 challenger entries routed to clean entrypoint; plan stage 2 updated). No forecast/interval/champion/governance/productive data changed.
