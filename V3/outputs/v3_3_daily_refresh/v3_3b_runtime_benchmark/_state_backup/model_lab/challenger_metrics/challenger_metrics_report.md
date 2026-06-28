# Block 5.29E - Challenger Metrics Scoring Report

Generated: 2026-06-13T16:26:54

## Purpose

Calculate official challenger metrics for the finalized six-model challenger forecast set. This block produces metrics only.

## Final Challenger Model Set

AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, FastNeuralAR_MLP

## Deferred Models Excluded

- NBEATS: deferred_runtime_impractical.
- NHITS: deferred_dependency_blocked.

## Forecast Row Reconciliation

- Official forecast rows: 81720
- Scoring forecast rows: 81720

## Actual Join Reconciliation

- Joined actual rows: 81720
- Missing actual rows: 0

## Non-Negative Scoring Adjustment

- Negative forecast rows adjusted for scoring: 306
- Raw challenger official forecasts were not overwritten.

## MASE/RMSSE Denominator Policy

- MASE denominator: training-only lag-1 naive MAE from training_only_denominators.csv.
- RMSSE denominator: square root of training-only lag-1 naive MSE from training_only_denominators.csv.
- No test actuals, 5.19 naive forecasts, seasonal naive, or tournament feedback were used for denominators.

## Diagnostic Metric Summary

The table below is diagnostic only and is not a ranking.

| model_name | metric_rows | median_mase | median_rmsse | median_wmape | median_smape | median_rmse | median_bias | negative_rows |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| AutoARIMA | 454 | 7.579717 | 1.981088 | 0.010379 | 0.010379 | 450.732959 | -23.308110 | 115 |
| ETS Explicit | 454 | 6.817774 | 1.889617 | 0.009186 | 0.009111 | 375.578439 | -4.954560 | 133 |
| FastNeuralAR_MLP | 454 | 790.959077 | 171.442293 | 0.895910 | 1.576479 | 20932.657459 | -20513.591512 | 55 |
| LightGBM | 454 | 17.090006 | 4.296580 | 0.020755 | 0.021136 | 693.113597 | -315.414869 | 0 |
| Theta | 454 | 9.685911 | 2.512566 | 0.013587 | 0.013650 | 484.151232 | -93.558724 | 0 |
| XGBoost | 454 | 14.219701 | 3.728092 | 0.016055 | 0.016164 | 614.958355 | -205.671444 | 3 |

## Validation Results

- Checks passed: 17
- Checks failed: 0

## Scope and Safety Findings

- Metrics were written only under outputs/model_lab/challenger_metrics/.
- No aggregation, significance, ranking, tournament, or champion outputs were created.
- Baseline outputs and Shiny were not modified.

## Recommendation for 5.29F

**PROCEED_TO_5.29F_CHALLENGER_AGGREGATION_AND_SIGNIFICANCE**
