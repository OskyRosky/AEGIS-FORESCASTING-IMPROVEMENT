# Block 5.29B - Challenger Sandbox Execution Report

Generated: 2026-06-12T15:53:09

## 1. Dependency State

- Available forecasting backends: ['pmdarima', 'darts', 'statsmodels', 'lightgbm', 'xgboost', 'torch']
- Missing forecasting backends: ['neuralforecast', 'statsforecast']

## 2. Sandbox Scope

- Scope: controlled subset (NOT the full 454-window backtest).
- Entities selected: 5 (volume-diversity selection).
- Windows per entity: 1 (latest window).

| entity_key | window_id | train_end_date | test_start_date | test_end_date |
| --- | --- | --- | --- | --- |
| NAM-Dedicated | 12 | 2026-03-28 | 2026-03-29 | 2026-04-27 |
| NAM-Multitenant | 12 | 2026-03-28 | 2026-03-29 | 2026-04-27 |
| NAM-TDF | 12 | 2026-03-28 | 2026-03-29 | 2026-04-27 |
| POL-Go Local | 12 | 2026-03-28 | 2026-03-29 | 2026-04-27 |
| SWE-Go Local | 12 | 2026-03-28 | 2026-03-29 | 2026-04-27 |

## 3. Execution Status

| model_name | sandbox_status | attempted | forecast_rows | eligible_candidate |
| --- | --- | --- | --- | --- |
| AutoARIMA | sandbox_passed | True | 150 | True |
| Theta | sandbox_passed | True | 150 | True |
| ETS Explicit | sandbox_passed | True | 150 | True |
| LightGBM | sandbox_passed | True | 150 | True |
| XGBoost | sandbox_passed | True | 150 | True |
| NBEATS | sandbox_passed | True | 150 | True |
| NHITS | sandbox_blocked_dependency_missing | False | 0 | False |

## 4. Forecast Contract Validation

- Checks passed: 42
- Checks failed: 0
- Models with no forecasts (blocked/not-attempted): 1

## 5. Official-Execution Candidate Assessment

- Eligible candidate models: ['AutoARIMA', 'Theta', 'ETS Explicit', 'LightGBM', 'XGBoost', 'NBEATS']
- official_execution_allowed: False
  (Sandbox eligibility never sets official_execution_ready.)

## 6. Remaining Blockers

- Forecasting dependencies are not installed. No challenger could run; all challengers are blocked pending dependency resolution.
- Missing packages: ['neuralforecast', 'statsforecast']

## 7. Recommendation

**PROCEED_TO_5.29C_CHALLENGER_OFFICIAL_EXECUTION_PREP**

