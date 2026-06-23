# Champion Series-Level Artifact Verification

## Purpose
Read-only verification of `tournament_entity_model_scores.csv` after Champion Block B.

## Artifact
- Full path: `C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT\V1\outputs\model_lab\tournament_engine\tournament_entity_model_scores.csv`
- Exists: `True`
- File size: `82108` bytes
- Last modified: `2026-06-13T18:07:40`

## Schema
Columns: run_id, model_name, model_origin, model_family, entity_key, median_mase, median_rmsse, median_wmape, median_smape, median_bias, entity_weight, audit_risk_flag, created_timestamp

Required columns confirmed: `entity_key`, `model_name`, `median_mase`, `median_rmsse`.

## Row Count And Grain
- Rows: 507
- Unique entities: 39
- Unique models: 13
- Expected rows from entities x models: 507
- Duplicate entity x model rows: 0

## Models Found
- ARIMA_Fixed
- AutoARIMA
- ETS Explicit
- ETS_Current
- FastNeuralAR_MLP
- FixedGrowth_1_5
- FixedGrowth_3
- FixedGrowth_4
- FixedGrowth_6
- LightGBM
- LinearRegression
- Theta
- XGBoost

Missing expected models: none.
Extra models: none.

## ETS Explicit Coverage
- ETS Explicit rows: 39
- Appears once per entity: True
- Missing ETS entities: none

## Leadership Verification
Series-level leader is the model with the lowest existing `median_mase` per entity. Exact ties are retained and all tied leaders are counted.

- ETS Explicit leads: 4
- ETS Explicit does not lead: 35
- Most frequent leader: Theta (8 tie-aware leads)

## Largest ETS Gap
- Entity: ESP-Go Local
- Local leader: LightGBM
- Local leader median MASE: 15.98228529838295
- ETS Explicit median MASE: 67.96281339453596
- Gap: 51.98052809615301
- ETS rank by median MASE: 11

## Tie Handling
- Entities with tied lowest median MASE: 0
- Tie details: none

## No Recompute Statement
This verification only reads existing `median_mase` and `median_rmsse` values from the artifact. It does not recompute MASE/RMSSE from actuals or forecasts, does not rerun tournaments, and does not change the champion decision.

## Validation
Validation file: `stage07_champion_series_artifact_verification_validation.csv`.
