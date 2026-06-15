# Block 5.29D-Recovery - Official Execution Recovery Report

Generated: 2026-06-13T16:11:28

## Interrupted NBEATS Run

NBEATS produced partial official rows before the re-scope decision and is now deferred for runtime impracticality. It is not treated as a statistical failure.

## Preserved Completed Outputs

Completed official forecasts were preserved for AutoARIMA, Theta, ETS Explicit, LightGBM, and XGBoost.

## Excluded Partial Outputs

Partial NBEATS rows and all NHITS rows are excluded from the final official forecast file.

## FastNeuralAR_MLP Sandbox

FastNeuralAR_MLP passed the recovery sandbox before official execution.

## FastNeuralAR_MLP Official Execution

- Official rows: 13620
- Runtime seconds: 124.16
- Minimum lag count used: 30
- Negative forecasts reported: 55

## Final Official Output Reconciliation

- Final official models: AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, FastNeuralAR_MLP
- Expected rows: 81720
- Actual rows: 81720

## Model Summary

| model_name | status | forecast_rows | expected_rows |
| --- | --- | ---: | ---: |
| AutoARIMA | official_model_passed | 13620 | 13620 |
| Theta | official_model_passed | 13620 | 13620 |
| ETS Explicit | official_model_passed | 13620 | 13620 |
| LightGBM | official_model_passed | 13620 | 13620 |
| XGBoost | official_model_passed | 13620 | 13620 |
| FastNeuralAR_MLP | official_model_passed | 13620 | 13620 |
| NBEATS | deferred_runtime_impractical | 0 | 0 |
| NHITS | deferred_dependency_blocked | 0 | 0 |

## Contract Validation

- Checks passed: 18
- Checks failed: 0

## Safety Findings

- No metrics, rankings, tournament outputs, or champion selections were created.
- Baseline outputs, official baseline metrics, aggregation/significance outputs, and Shiny were not modified by this recovery script.
- NBEATS is deferred for runtime impracticality only.
- NHITS is deferred for dependency incompatibility only.

## Recommendation

**PROCEED_TO_5.29E_CHALLENGER_METRICS_SCORING**
