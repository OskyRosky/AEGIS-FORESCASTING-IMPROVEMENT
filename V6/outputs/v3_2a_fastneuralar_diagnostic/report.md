# V3.2A — FastNeuralAR_MLP Diagnostic / Current Baseline Audit

**Stage:** V3.2A (diagnostic only — no training, no replacement, no promotion)
**Scope:** V3 only. V1 and V2 untouched.
**Date:** 2026-06-25
**Status:** V3_2A_DIAGNOSTIC_COMPLETED_READY_FOR_OSCAR_REVIEW

> This is a read-only audit. No model was trained, no forecast was regenerated, no
> champion was changed, no governed artifact was modified. All numbers below are copied
> verbatim from existing governed artifacts. Where a metric does not exist it is reported
> as `not_available` with the artifact that would be required to produce it.

---

## 1. Files inspected

Code / implementation:
- `python/model_lab/run_challenger_official_execution_recovery.py` (GOVERNED producer of FastNeuralAR_MLP forecasts; lines 185–245 contain `_make_lag_matrix`, `_fit_fast_neural`, `_forecast_fast_neural`)
- `python/model_lab/run_challenger_official_execution.py` (current official `FORECASTERS` dict, lines 298–305 — FastNeuralAR_MLP is NOT in it; it was added by the recovery script)
- `python/model_lab/run_backtest_60d.py` (lines 165–203 — same MLP implementation, used by the 60-day backtest harness)
- `python/model_lab/run_challenger_model_set_rescope.py` (design rationale)
- `python/model_lab/build_challenger_aggregation_significance.py` (risk note text)
- `python/model_lab/build_model_lab_closure_pack.py` (risk register R-001 + next step NS-003)
- `python/model_lab/build_tournament_sanity_review.py` (sanity review note)
- `python/model_lab/build_champion_decision.py` (champion exclusion narrative)
- `MassiveForecasting-V3/forecast_models_registry.R` (legacy R engine registry — does NOT define FastNeuralAR_MLP)
- `shiny_app/R/data_loader.R` (Shiny governed loader registry — confirms what each page consumes)

Artifacts:
- `outputs/model_lab/tournament_engine/tournament_model_scorecard.csv`
- `outputs/model_lab/tournament_engine/tournament_model_evidence_summary.csv`
- `outputs/model_lab/tournament_engine/tournament_entity_model_scores.csv`
- `outputs/model_lab/challenger_metrics/challenger_metrics_by_model_diagnostic.csv`
- `outputs/model_lab/challenger_official_execution/challenger_official_forecasts.csv`
- `outputs/model_lab/challenger_official_execution/challenger_official_execution_summary.csv`
- `outputs/model_lab/audit_5/audit_5_findings.csv`
- `data/processed/forecast_viewer_model_outputs.csv` (+ manifest)
- `data/processed/forecasts.csv`

## 2. Files created

All under `outputs/v3_2a_fastneuralar_diagnostic/` (new folder — nothing overwritten):
- `report.md` (this file)
- `validation.csv`
- `model_inventory.csv`
- `current_performance_summary.csv`
- `recommended_candidates.csv`

## 3. FastNeuralAR_MLP code location

The governed forecasts were produced by **`python/model_lab/run_challenger_official_execution_recovery.py`**.

- It is a **real model**, not a stub or placeholder (no `NotImplementedError`).
- Backend: `sklearn.neural_network.MLPRegressor` inside a `Pipeline([StandardScaler, MLPRegressor])`.
- Hyperparameters (lines 205–213): `hidden_layer_sizes=(32,)`, `activation="relu"`, `solver="adam"`, `max_iter=300`, `random_state=RANDOM_SEED (42)`, `early_stopping` enabled when ≥20 training rows.
- Features: autoregressive lag matrix, `n_lags = min(30, max(2, len(values) - 1))`.
- **Multi-step strategy = recursive** (lines 221–232): each predicted value is appended back into `history` and reused as a lag for the next step. This is the key implementation choice behind the failure (see §9).
- It is fit **per entity × per window** (one tiny local model per series), not a single global model.

The same MLP code is mirrored in `run_backtest_60d.py` (60-day harness). The **R** engine registry `MassiveForecasting-V3/forecast_models_registry.R` does **not** define FastNeuralAR_MLP — the model is Python-only. The current `run_challenger_official_execution.py` `FORECASTERS` dict lists only AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, NBEATS; FastNeuralAR_MLP was appended via the recovery script.

## 4. Current artifact inventory

See `model_inventory.csv` for the full table. Summary:

| Artifact | Rows w/ FastNeuralAR | Role |
|---|---|---|
| tournament_model_scorecard.csv | 1 | Aggregate official metrics (MASE/RMSSE/guardrails/risk) |
| tournament_model_evidence_summary.csv | 1 | Head-to-head W/D/L vs 12 models |
| tournament_entity_model_scores.csv | 39 | Per-series (entity) scores |
| challenger_metrics_by_model_diagnostic.csv | 1 | Diagnostic aggregate over 454 entity-window rows |
| challenger_official_forecasts.csv | 13,620 | Raw backtest forecasts (h1–30) |
| data/processed/forecast_viewer_model_outputs.csv | present | Consolidated backtest consumed by Shiny Viewer/Accuracy |

There is **no per-horizon breakdown artifact** and **no runtime/timing artifact** for FastNeuralAR_MLP (see §4/§8 → `not_available`).

## 5. Current performance summary

See `current_performance_summary.csv`. Headline (official, `tournament_model_scorecard.csv`, 39-entity aggregate):

| Metric | FastNeuralAR_MLP | ETS Explicit (champion) | Best baseline |
|---|---|---|---|
| official_median_mase | **739.92** | 6.90 | AutoARIMA 8.09 |
| official_median_rmsse | **164.62** | 1.856 | ETS Explicit 1.856 / AutoARIMA 1.859 |
| median_wmape | 0.861 | 0.00876 | — |
| median_smape | 1.481 | 0.00874 | — |
| median_bias | **-17,656.88** | -10.80 | — |
| mase_guardrail_status | **fail** | pass | pass |
| rmsse_guardrail_status | **fail** | pass | pass |
| risk_status | **high** | low | low |
| audit_risk_flag | **True** | False | False |
| eligible_for_champion_consideration | **False** | True | True |

Diagnostic grain (`challenger_metrics_by_model_diagnostic.csv`, 454 entity-window rows): median MASE **790.96**, median RMSSE **171.44**, median bias **-20,513.59**, **negative_forecast_rows = 55**.

## 6. Comparison against champion / baselines

Full ranking by `official_median_mase` (lower is better), copied from the scorecard:

| # | Model | MASE | RMSSE | Risk |
|---|---|---|---|---|
| 1 | ETS Explicit (champion) | 6.90 | 1.856 | low |
| 2 | AutoARIMA | 8.09 | 1.859 | low |
| 3 | FixedGrowth_1_5 | 8.65 | 2.272 | low |
| 4 | ETS_Current | 8.65 | 2.273 | low |
| 5 | LinearRegression | 9.50 | 2.752 | low |
| 6 | Theta | 10.64 | 2.819 | low |
| 7 | ARIMA_Fixed | 11.79 | 3.493 | low |
| 8 | FixedGrowth_3 | 12.99 | 3.019 | low |
| 9 | XGBoost | 14.55 | 3.881 | low |
| 10 | LightGBM | 16.04 | 4.061 | low |
| 11 | FixedGrowth_4 | 16.53 | 4.072 | low |
| 12 | FixedGrowth_6 | 27.02 | 5.084 | medium |
| **13** | **FastNeuralAR_MLP** | **739.92** | **164.62** | **high** |

FastNeuralAR_MLP is **last of 13**, ~**107× worse** than the champion on MASE and ~**89× worse** on RMSSE. Head-to-head (`tournament_model_evidence_summary.csv`): **0 better / 12 worse / 0 inconclusive, net -12** — it lost to every other model. (Champion ETS Explicit: 8 / 0 / 4, net +8.)

## 7. Failure patterns

- **Every horizon bucket and every series**: the model ranks last overall (13/13) and is high-risk on the aggregate.
- **Per-series (entity)**: `tournament_entity_model_scores.csv` holds 39 FastNeuralAR rows; the worst series show catastrophic negative bias explosions (e.g. NAM-Multitenant and EUR-Multitenant with bias in the millions, JPN-Go Local MASE > 1,700). These are consistent with recursive runaway on multi-tenant high-scale series.
- **Negative forecasts**: 55 rows produce negative demand — invalid for a non-negative capacity domain.
- **Over/under forecast**: strongly **negative** median bias (-17,656 official / -20,513 diagnostic) → systematic under/divergent forecasting, not noise.
- **Per-horizon detail (h1…h30)**: `not_available` — artifacts aggregate per entity/model, not per horizon. Would require a per-horizon residual artifact from the backtest to confirm the exact compounding curve.

## 8. Runtime / stability findings

- **Runtime/timing**: `not_available` — no timing column is recorded in any governed artifact. `challenger_official_execution_summary.csv` reports execution completed (`official_forecast_execution_completed = True`, models_passed = 6) with **no timeout or runtime exception**. So the model is cheap enough to run; the problem is **accuracy/stability**, not speed.
- **Stability**: unstable. Recursive multi-step feedback + tiny per-series training history + no non-negativity constraint produce divergent trajectories and 55 negative-forecast rows. Documented governance risk: closure pack **R-001** (`high`, "High MASE/RMSSE; possible scale or recursive collapse issue", carried_forward) and next step **NS-003** ("Investigate FastNeuralAR_MLP implementation issue — Review scale/normalization or recursive collapse behavior").

## 9. Root-cause hypothesis

The evidence points to an **implementation / configuration problem, not a fundamentally unusable model family**:

1. **Recursive multi-step collapse (primary).** `_forecast_fast_neural` feeds each prediction back as a lag (`history.append(pred)`), so any bias compounds across the 30-step horizon → exponential drift, confirmed by the extreme bias on long-horizon multi-tenant series.
2. **No non-negativity / no target transform.** Raw values are scaled with `StandardScaler` but predictions are not clamped to ≥0 and there is no log/relative transform, allowing the 55 negative forecasts and scale explosions on high-magnitude series.
3. **Tiny local fit + light architecture.** One `MLPRegressor(hidden_layer_sizes=(32,))` per entity-window with `max_iter=300`, no L1/L2 or dropout, trained on very short per-series histories → under-regularized, high-variance.

Governed sources agree, e.g. Audit #5: *"FastNeuralAR_MLP exhibits extreme error (median MASE 739.92 / RMSSE 164.62) consistent with a scale/normalization or recursive-collapse implementation issue; flagged and isolated, not silently dropped."* Champion exclusion reason: *"Audit #4 high-risk flag: extreme MASE/RMSSE and possible scale or recursive-collapse issue."*

**Conclusion:** the deep-learning *family* is not disproven; the *current implementation* is. This favors a "fix/replace the implementation" path in V3.2B over abandoning neural models outright.

## 10. Candidate replacement options

See `recommended_candidates.csv`. Summary (no implementation in this stage):

1. **Fix FastNeuralAR_MLP** — direct multi-horizon output (avoid recursion) + non-negativity clamp + log/relative target transform + regularization. Low effort, directly addresses the documented root cause. **Priority 1.**
2. **DLinear / NLinear** — simple, robust linear DL baselines that handle limited per-series data well. Medium effort. **Priority 2.**
3. **Pragmatic ML tuning (LightGBM / XGBoost)** — already present and stable (no negatives), currently mid-pack; tuning could make them a safe non-neural alternative. Low effort. **Priority 2.**
4. **N-BEATS / N-HiTS** — `darts` already used by the NBEATS forecaster; currently deferred (runtime/dependency). Medium-high effort. **Priority 3.**
5. **TCN** — temporal conv net, robust to recursion issues. Medium effort. **Priority 3.**
6. **Defer deep learning** — fallback if V3.2B evidence shows DL adds no value over tuned ML.

## 11. Current and Future Artifact Lineage

This table answers the mandatory lineage questions (what produces/consumes each artifact, and where new V3.2B candidate artifacts should live). It is **inventory + recommendation only — nothing is moved or modified**.

| artifact_name | current_path | generated_by_script | consumed_by_shiny_page | model_scope | is_governed | is_experimental | recommended_future_path | notes |
|---|---|---|---|---|---|---|---|---|
| forecasts.csv | data/processed/forecasts.csv | upstream Tesseract ingest + transform (data contract build) | Forecasting › Forecast (forward) | champion/production forward forecast | yes | no | data/processed/ (unchanged) | Productive forward forecast values. Do not write candidate output here. |
| forecasts_with_intervals_relative_60d_calibrated.csv | data/processed/forecasts_with_intervals_relative_60d_calibrated.csv | python/model_lab/recalibrate_interval_60d_80.py | Forecasting › Forecast (80% interval) | champion interval band | yes | no | data/processed/ (unchanged) | Governed interval artifact. |
| forecast_viewer_model_outputs.csv | data/processed/forecast_viewer_model_outputs.csv | python/model_lab/build_forecast_viewer_handoff.py | Forecasting › Viewer + Accuracy | all 13 models incl FastNeuralAR_MLP | yes | no | data/processed/ (unchanged) | Consolidated backtest. A NEW model only appears here AFTER promotion. |
| challenger_official_forecasts.csv | outputs/model_lab/challenger_official_execution/challenger_official_forecasts.csv | run_challenger_official_execution(_recovery).py | none (upstream) | challengers incl FastNeuralAR_MLP | yes | no | outputs/model_lab/... (unchanged) | Raw backtest forecasts where FastNeuralAR predictions physically live (13,620 rows). |
| tournament_model_scorecard.csv | outputs/model_lab/tournament_engine/tournament_model_scorecard.csv | python/model_lab/ tournament engine builder | Models › Tournament + Universe | all models | yes | no | outputs/model_lab/... (unchanged) | FastNeuralAR official metrics row lives here. |
| tournament_model_evidence_summary.csv | outputs/model_lab/tournament_engine/tournament_model_evidence_summary.csv | tournament engine builder | Models › Tournament (league/tree) | all models | yes | no | outputs/model_lab/... (unchanged) | Head-to-head W/D/L. |
| tournament_entity_model_scores.csv | outputs/model_lab/tournament_engine/tournament_entity_model_scores.csv | tournament engine builder | Models › Champion (series leaders) | per-series × model | yes | no | outputs/model_lab/... (unchanged) | Per-series FastNeuralAR scores (39 rows). |
| model_lab_champion_summary.csv | outputs/model_lab/model_lab_closure_pack/model_lab_champion_summary.csv | python/model_lab/build_model_lab_closure_pack.py | Models › Champion + Home/Overview | champion | yes | no | outputs/model_lab/... (unchanged) | Champion = ETS Explicit, frozen. |
| model_lab_final_model_universe.csv | outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv | build_model_lab_closure_pack.py | Models › Universe | all models | yes | no | outputs/model_lab/... (unchanged) | Model taxonomy/registry view. |
| challenger_metrics_by_model_diagnostic.csv | outputs/model_lab/challenger_metrics/challenger_metrics_by_model_diagnostic.csv | calculate_challenger_metrics.py | none (diagnostic) | challengers | yes | no | outputs/model_lab/... (unchanged) | Diagnostic 454-row aggregate. |
| **(NEW) candidate raw forecasts** | — | (V3.2B) new candidate runner | none until promoted | new candidate(s) | no | yes | **outputs/v3_2b_model_candidates/** | Experimental forecasts go here first, NOT data/processed/. |
| **(NEW) candidate metrics/evidence** | — | (V3.2B) candidate evaluation | none until promoted | new candidate(s) | no | yes | **outputs/v3_2b_model_candidates/** | Backtest/runtime/stability comparison vs FastNeuralAR + champion. |
| **(NEW) promoted governed artifact** | — | (V3.2B) handoff builder after Oscar approval | Viewer/Accuracy/Tournament once approved | promoted candidate | yes (after promotion) | no | outputs/model_lab/... then data/processed/ | Only governed/promoted artifacts reach data/processed/. |

### Direct answers to the 10 lineage questions
1. **Scripts that generate Shiny's forecasts/estimates today:** upstream Tesseract ingest + transform (data contract build) → `forecasts.csv`; `build_forecast_viewer_handoff.py` → `forecast_viewer_model_outputs.csv`; tournament engine builders → scorecard/evidence; `recalibrate_interval_60d_80.py` → interval artifact.
2. **Files with productive forecast values today:** `data/processed/forecasts.csv` (forward) and the interval artifacts `forecasts_with_intervals_relative*.csv`.
3. **Files with backtest / model outputs today:** `data/processed/forecast_viewer_model_outputs.csv` (consolidated) and `outputs/model_lab/challenger_official_execution/challenger_official_forecasts.csv` (raw).
4. **Files with tournament / champion / metrics today:** `outputs/model_lab/tournament_engine/tournament_model_scorecard.csv`, `tournament_model_evidence_summary.csv`, `tournament_entity_model_scores.csv`, and `outputs/model_lab/model_lab_closure_pack/model_lab_champion_summary.csv`.
5. **What Shiny consumes per page:** Viewer + Accuracy → `forecast_viewer_model_outputs.csv`; Forecast → `forecasts.csv` + `forecasts_with_intervals_relative_60d_calibrated.csv` + `actuals.csv`; Models/Universe → `model_lab_final_model_universe.csv`; Models/Tournament → tournament scorecard + evidence_summary + pairwise; Champion → `model_lab_champion_summary.csv` + `tournament_entity_model_scores.csv`.
6. **Where FastNeuralAR_MLP is defined/registered:** `python/model_lab/run_challenger_official_execution_recovery.py` (governed producer); mirrored in `run_backtest_60d.py`; NOT in the R registry.
7. **Where its current predictions live:** `outputs/model_lab/challenger_official_execution/challenger_official_forecasts.csv` (raw) and inside `data/processed/forecast_viewer_model_outputs.csv` (consolidated).
8. **Where its current metrics live:** tournament scorecard + evidence_summary + entity_model_scores + `challenger_metrics_by_model_diagnostic.csv`.
9. **Artifacts to create for new V3.2B candidates:** candidate raw forecasts, candidate per-model/per-series metrics, and a candidate-vs-baseline comparison (backtest + runtime + stability).
10. **Where they should be hosted initially:** **`outputs/v3_2b_model_candidates/`** for all experiments/evidence; reuse `outputs/model_lab/...` only when extending an existing Model Lab pattern; **`data/processed/` is reserved for governed/promoted artifacts** that Shiny consumes — experimental candidate outputs must NOT be written there at the start.

## 12. V3.2A status

`V3_2A_DIAGNOSTIC_COMPLETED_READY_FOR_OSCAR_REVIEW`. Diagnosis complete; no training, no replacement, no promotion performed. Awaiting Oscar's go-ahead to scope V3.2B.

## 13. Recommended V3.2B plan

1. **Create the experiment workspace** `outputs/v3_2b_model_candidates/` (no `data/processed/` writes).
2. **Fix-first**: re-run FastNeuralAR_MLP with direct multi-horizon output (no recursion) + non-negativity clamp + log/relative target transform + light regularization; backtest on the same 39 series / same windows for an apples-to-apples comparison.
3. **Benchmark robust simple-DL** (DLinear/NLinear) and **tuned ML** (LightGBM/XGBoost) on the same harness.
4. **Optionally** trial N-BEATS / N-HiTS / TCN if the simple options underperform.
5. **Compare on backtest accuracy + runtime + stability** (incl. negative-forecast count), write evidence CSVs into `outputs/v3_2b_model_candidates/`.
6. **NO auto-promote**: champion stays ETS Explicit (frozen). Only after Oscar reviews evidence do we promote a candidate via the handoff builder into `outputs/model_lab/...` then `data/processed/`.

---

## Governance confirmation

- No champion changed. ✅ (ETS Explicit remains the governed champion under conditions.)
- No forecasts changed. ✅
- No intervals changed. ✅
- No data artifacts changed. ✅ (data/processed/ untouched.)
- No model registry changed. ✅
- V1 and V2 untouched. ✅
- V4 AI/LLM not started. ✅
- V3.3 pipeline not started. ✅
- No models trained, no candidates implemented, no promotion. ✅
- Only NEW files written, all under `outputs/v3_2a_fastneuralar_diagnostic/`. ✅
