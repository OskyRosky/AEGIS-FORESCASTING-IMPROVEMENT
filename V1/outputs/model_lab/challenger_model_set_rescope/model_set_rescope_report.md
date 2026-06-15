# Block 5.29D-Recovery - Model Set Re-scope Report

Generated: 2026-06-13T16:08:35

## Original Model Set

The started 5.29D official set contained AutoARIMA, Theta, ETS Explicit,
LightGBM, XGBoost, and NBEATS. NHITS was already deferred.

## Runtime and Dependency Issue

NBEATS became runtime-impractical for the current MVP/prototype execution
profile. NHITS remains dependency-blocked due to Python 3.14 /
neuralforecast / ray incompatibility.

## Final Model Set

The current official challenger set is AutoARIMA, Theta, ETS Explicit,
LightGBM, XGBoost, and FastNeuralAR_MLP.

## Deferred Models

- NBEATS: `deferred_runtime_impractical`; too slow for MVP/prototype automation
  in the current Python/container execution context.
- NHITS: `deferred_dependency_blocked`; Python 3.14 / neuralforecast / ray
  incompatibility.

## FastNeuralAR_MLP Role

FastNeuralAR_MLP provides a lightweight neural/autoregressive comparison
similar in spirit to NNETAR. It uses lagged actuals and an sklearn MLPRegressor
with fixed settings.

## Workload Impact

The final workload remains six official models over 454 entity-windows and a
30-day horizon, for 81,720 forecast rows.

## Scope and Safety

This re-scope does not calculate metrics, rankings, tournament outputs, or
champion selections. It does not rewrite historical evidence for NBEATS or
NHITS.

## Recommendation

Proceed with recovery execution: preserve completed official forecasts, exclude
partial NBEATS rows, sandbox FastNeuralAR_MLP, run it officially if sandbox
passes, and validate the final forecast contract.
