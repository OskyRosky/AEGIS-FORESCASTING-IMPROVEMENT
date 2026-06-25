# Challenger Dependency Resolution Report (Block 5.29B-Fix)

Generated: 2026-06-12T15:50:18

## Installation Outcome

- Dependencies importable: ['darts', 'lightgbm', 'pmdarima', 'statsmodels', 'torch', 'xgboost']
- Dependencies unresolved: ['neuralforecast', 'statsforecast']

## Challengers Now Sandbox-Runnable

- AutoARIMA (backend: ['pmdarima'])
- Theta (backend: ['darts'])
- ETS Explicit (backend: ['statsmodels'])
- LightGBM (backend: ['lightgbm'])
- XGBoost (backend: ['xgboost'])
- NBEATS (backend: ['darts', 'torch'])

## Challengers Still Blocked

- NHITS (no importable backend; requires one of [['neuralforecast', 'torch']])

## Can Sandbox Proceed?

Yes - 6 of 7 challengers can run in the sandbox. Re-run the sandbox; remaining blocked models stay documented.

