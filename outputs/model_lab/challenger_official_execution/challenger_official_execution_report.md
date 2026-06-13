# Block 5.29D-Recovery - Challenger Official Execution Report

Generated: 2026-06-13T16:11:28

## Final Official Model Set

AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, FastNeuralAR_MLP

## Deferred Models

- NBEATS: deferred_runtime_impractical; too slow for MVP/prototype automation in the current Python/container execution context.
- NHITS: deferred_dependency_blocked; Python 3.14 / neuralforecast / ray incompatibility.

## FastNeuralAR_MLP Replacement Rationale

FastNeuralAR_MLP supplies a lightweight neural/autoregressive comparison similar in spirit to NNETAR while remaining practical for MVP and future container automation.

## Official Scope

- Entity-windows: 454
- Horizon days: 30
- Expected final rows: 81720

## Execution Results

- Actual final rows: 81720
- FastNeuralAR_MLP runtime seconds: 124.16
- FastNeuralAR_MLP minimum lag count used: 30
- FastNeuralAR_MLP negative forecasts reported: 55

## Row Reconciliation

- Expected total forecast rows: 81720
- Actual total forecast rows: 81720

## Contract Validation

- Failed checks: 0

## Safety Findings

- NBEATS partial rows are excluded.
- NHITS rows are excluded.
- No metric, ranking, tournament, or champion outputs were created.

## Recommendation for 5.29E

**PROCEED_TO_5.29E_CHALLENGER_METRICS_SCORING**
