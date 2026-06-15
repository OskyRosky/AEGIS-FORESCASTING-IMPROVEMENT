# Challenger Execution Planning Report - Stage 5.29A

Created timestamp: 2026-06-12T15:22:45
Run id: challenger_execution_planning_20260612_152245

## Purpose of 5.29A

Block 5.29A defines the official execution plan for the seven onboarded
challenger models. It is planning only: no model is trained, no forecast is
generated, no metric is calculated, and no ranking, tournament, or champion
output is created. Official execution remains blocked for every challenger. The
plan is designed to make Block 5.29B (Challenger Sandbox Execution)
straightforward and safe.

## Execution Order

Statistical challengers run first, then machine learning, then deep learning.

| order | model_name | model_family | priority | runtime_class | dependency_status |
| --- | --- | --- | --- | --- | --- |
| 1 | AutoARIMA | statistical | high | medium | blocked_dependency_missing |
| 2 | Theta | statistical | high | light | blocked_dependency_missing |
| 3 | ETS Explicit | statistical | high | light | blocked_dependency_missing |
| 4 | LightGBM | machine_learning | medium | medium | blocked_dependency_missing |
| 5 | XGBoost | machine_learning | medium | medium | blocked_dependency_missing |
| 6 | NBEATS | deep_learning | low | heavy | blocked_dependency_missing |
| 7 | NHITS | deep_learning | low | heavy | blocked_dependency_missing |

## Dependency Gaps

Dependency availability is inherited from Stage 5.28 onboarding. No packages were
installed in this block. Required dependencies currently unavailable:
darts, lightgbm, neuralforecast, pmdarima, statsforecast, statsmodels, torch, xgboost.

- Models ready for sandbox now (a usable backend present): 0
- Models blocked by missing dependencies: 7

Each missing dependency has a recommended (planned) resolution recorded in
`challenger_dependency_resolution_plan.csv`. Resolution is a prerequisite for
sandbox (where no fallback exists) and for all official execution.

## Sandbox Plan

Sandbox execution uses a controlled subset, not all 454 windows. The recommended
first sandbox scope is the latest 1 window across 5
representative entities, for any challenger whose dependencies allow it. Success
requires error-free fit/predict, schema-compliant 30-day forecasts, and no
NaN/inf values within the sandbox runtime budget. See
`challenger_sandbox_plan.csv`.

## Official Execution Gates

All gates must pass before any official challenger run; each is blocking:

- GATE-01 dependencies_resolved: All required dependencies for the model are installed and recorded.
- GATE-02 sandbox_passed: Model passed sandbox execution on the controlled subset.
- GATE-03 no_leakage_controls_failed: All mapped leakage controls verified and none failed.
- GATE-04 tuning_budget_locked: Tuning mode, max trials, and runtime budget are locked.
- GATE-05 hyperparameter_space_locked: Hyperparameter search space is locked and pre-registered.
- GATE-06 random_seed_locked: Random seed or deterministic policy is locked and recorded.
- GATE-07 output_schema_validated: Forecast output schema matches the challenger forecast output contract.
- GATE-08 official_windows_locked: Official backtesting windows are locked for the official run.
- GATE-09 no_post_hoc_tuning: No tuning occurs after official evaluation on benchmark windows.
- GATE-10 no_tournament_feedback_tuning: No tuning from tournament rank, champion, significance, MASE, or RMSSE outcomes.

## Tuning Budget Plan

Tuning is conservative and pre-registered. Statistical challengers have smaller
budgets; ML and deep-learning challengers have explicitly bounded budgets. For
every model, `official_results_may_tune_model = false`, inner validation is
required, and a random seed is required.

| model_name | tuning_allowed | tuning_mode | max_trials | max_runtime_minutes |
| --- | --- | --- | --- | --- |
| AutoARIMA | True | library_auto_search_bounded | limited_by_library_auto_search | 20 |
| Theta | False | fixed_default | 1 | 10 |
| ETS Explicit | True | bounded_grid | 10 | 20 |
| LightGBM | True | bounded_random_search | 20 | 45 |
| XGBoost | True | bounded_random_search | 20 | 45 |
| NBEATS | True | bounded_config_search | 5 | 90 |
| NHITS | True | bounded_config_search | 5 | 90 |

## Leakage Controls

All leakage controls from the Stage 5.26 No-Tuning-Leakage Contract remain in
force and are mapped to every challenger. No model may use official MASE, RMSSE,
statistical significance, tournament rank, or champion feedback for tuning.
Tuning is restricted to inner validation on training-only data. Gates GATE-03,
GATE-09, and GATE-10 enforce these constraints before official execution.

## Dashboard-Readiness Note

All planning artifacts are emitted as flat, tabular CSVs with explicit columns
and a single-row summary, so they can be loaded directly by the Shiny
presentation layer without transformation. The forecast output contract fixes
the schema future challenger forecasts must satisfy, keeping downstream MASE,
RMSSE, non-negative policy, and aggregation steps compatible.

## Recommendation

PROCEED_TO_5.29B_CHALLENGER_SANDBOX_EXECUTION
