# Block 5.29C - Challenger Official Execution Prep Report

Generated: 2026-06-12T17:00:53

## 1. Purpose

Prepare (not run) the official challenger execution for the six sandbox-passed challengers: freeze the candidate list, review official gates, lock scope / tuning policy / output contract, and estimate workload. No official forecasts, metrics, rankings, tournament, or champion are produced in this block.

## 2. Sandbox Result

- 6 of 7 challengers passed sandbox (AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, NBEATS); 900 contract-valid forecast rows.
- NHITS was blocked by an unresolved dependency.

## 3. Why These 6 Models Proceed

All six passed sandbox with schema-valid, finite, non-null forecasts and satisfy every official execution gate (dependencies resolved, leakage controls intact, tuning budget / hyperparameter space / random seed locked, output schema validated, official windows locked, no post-hoc or tournament-feedback tuning).

## 4. Why NHITS Is Deferred

- deferred_dependency_blocked: NHITS depends solely on neuralforecast, which cannot be made importable on Python 3.14 - modern neuralforecast requires ray (no 3.14 wheel) and the legacy fallback is incompatible with the installed pytorch-lightning. Excluded from the immediate official run; re-enable on a Python 3.11/3.12 environment.
- Recorded as status = deferred_dependency_blocked; not an official candidate. Model Lab completion is NOT blocked by this single deferral.

## 5. Official Execution Scope

- Entities: 39
- Entity-window pairs (real walk-forward scope): 454
- Horizon: 30 days
- execution_mode: official

### Scope discrepancy with originating spec (documented, not fabricated)

The originating 5.29C spec assumed a full 39 x 454 grid (17,706 entity-windows; 3,187,080 forecast rows for 6 models). The actual `backtesting_windows.csv` is a walk-forward design with 454 total entity-window pairs (7-12 windows per entity), so the true workload is 454 x 30 x 6 = 81,720 forecast rows. Artifacts use the REAL counts; the spec's grid assumption is flagged here for reconciliation before launch.

## 6. Expected Workload

- Per candidate: 454 x 30 = 13,620 rows.
- Total for 6 candidates: 81,720 rows.
- NBEATS is the heavy (dominant) runtime/cost driver; statistical/ML models are light-to-medium.

## 7. Gate Review Result

- Gates evaluated per model: 10.
- Candidates passing all gates: 6 / 6.
- Candidates not ready: none.
- NHITS: dependency/sandbox gates fail; remaining gates not applicable (deferred).

## 8. Locked Policy

- Tuning budgets, modes, and max trials locked per model.
- random_seed locked = 42; inner validation required; hyperparameter spaces pre-registered.
- official_results_may_tune_model = false for every model.

## 9. Output Contract

9 required columns; identical to the sandbox contract except execution_mode must be 'official' in the execution block.

## 10. Scope / Safety

- official_execution_run_performed = false.
- rankings_created / tournament_created / champion_selected = false.
- No challenger metrics, MASE, or RMSSE computed.
- Baseline, metric, aggregation, significance, and Shiny outputs untouched.

## 11. Recommendation

**PROCEED_TO_5.29D_CHALLENGER_OFFICIAL_EXECUTION**

All 6 candidates passed every official gate and the run scope, policy, and output contract are locked. Reconcile the scope-count assumption above, then proceed to 5.29D official execution.
