# Block 5.29D - Challenger Official Execution Report

Generated: 2026-06-13T15:43:35

## Purpose

Execute official challenger forecasts for the six approved candidates over the locked 5.29C official scope. This block creates forecast and execution audit artifacts only.

## Official Candidate List

| model_name | model_family | official_candidate |
| --- | --- | --- |
| AutoARIMA | statistical | True |
| Theta | statistical | True |
| ETS Explicit | statistical | True |
| LightGBM | machine_learning | True |
| XGBoost | machine_learning | True |
| NBEATS | deep_learning | True |

## NHITS Deferred Status

- NHITS was not run and produced zero forecast rows.
- Deferred reason: deferred_dependency_blocked: NHITS depends solely on neuralforecast, which cannot be made importable on Python 3.14 - modern neuralforecast requires ray (no 3.14 wheel) and the legacy fallback is incompatible with the installed pytorch-lightning. Excluded from the immediate official run; re-enable on a Python 3.11/3.12 environment.

## Official Scope

- Entity-window rows: 454
- Horizon days: 30
- Expected rows per active model: 13620
- Expected total rows: 81720

## Model Execution Results

| model_name | status | attempted_windows | passed_windows | failed_windows | forecast_rows | expected_rows | runtime_seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| AutoARIMA | official_model_passed | 454 | 454 | 0 | 13620 | 13620 | 935.262838 |
| Theta | official_model_passed | 454 | 454 | 0 | 13620 | 13620 | 3.864319 |
| ETS Explicit | official_model_passed | 454 | 454 | 0 | 13620 | 13620 | 17.690698 |
| LightGBM | official_model_passed | 454 | 454 | 0 | 13620 | 13620 | 20.155779 |
| XGBoost | official_model_passed | 454 | 454 | 0 | 13620 | 13620 | 28.63315 |
| NBEATS | official_model_partial | 5 | 5 | 0 | 150 | 13620 | 142.477646 |
| NHITS | official_model_deferred | 0 | 0 | 0 | 0 | 0 | 0.0 |

## Forecast Row Reconciliation

- Expected total forecast rows: 81720
- Actual total forecast rows: 68250

## Contract Validation

- Checks passed: 14
- Checks failed: 2
- FAIL ALL / expected_total_rows_reconciled: expected=81720 actual=68250
- FAIL NBEATS / per_model_expected_rows_reconciled: expected=13620 actual=150

## Failures

- NBEATS: official_model_partial (0 failed windows, 150 rows).

## Scope and Safety Findings

- Used only the locked official_execution_scope.csv rows selected for official execution.
- NHITS remained deferred_dependency_blocked and has no forecast rows.
- Metrics, rankings, tournament outputs, champion selection, baseline outputs, aggregation/significance outputs, and Shiny were not modified by this script.

## Recommendation for 5.29E

**BLOCK_5.29E_PENDING_OFFICIAL_EXECUTION_COMPLETION**

## Runtime

- Total execution time: 0.00 seconds
