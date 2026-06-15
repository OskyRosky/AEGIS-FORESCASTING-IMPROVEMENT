# Block 5.29F - Challenger Aggregation & Significance Report

Generated: 2026-06-13T17:27:28

## Purpose

Create challenger-only aggregation and statistical evidence artifacts without rankings, tournament scores, winners, or champions.

## Final Challenger Set

AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, FastNeuralAR_MLP

## Deferred Models Excluded

- NBEATS: deferred_runtime_impractical.
- NHITS: deferred_dependency_blocked.

## Official Aggregation Hierarchy

Metrics are first aggregated to entity/model medians across windows. Model-level official MASE and RMSSE are then medians across entity-level medians, preserving equal entity weighting.

## Model-Level Diagnostic Results

The table below is diagnostic only and is not sorted as a ranking.

| model_name | official_median_mase | official_median_rmsse | median_wmape | median_smape | negative_rows |
| --- | ---: | ---: | ---: | ---: | ---: |
| AutoARIMA | 8.088530 | 1.859013 | 0.009911 | 0.009913 | 115 |
| Theta | 10.642290 | 2.819225 | 0.014164 | 0.014341 | 0 |
| ETS Explicit | 6.901144 | 1.856193 | 0.008755 | 0.008735 | 133 |
| LightGBM | 16.041042 | 4.061386 | 0.020561 | 0.020759 | 0 |
| XGBoost | 14.547628 | 3.880790 | 0.015663 | 0.015768 | 3 |
| FastNeuralAR_MLP | 739.921888 | 164.622417 | 0.861341 | 1.480670 | 55 |

## Pairwise Significance Method

Pairwise comparisons use entity-level median MASE, paired by entity, with 10,000 bootstrap iterations, deterministic seed 20260612, exact paired sign tests, Benjamini-Hochberg correction, and a practical threshold of 0.02.

## Pairwise Evidence Results

- Pairwise comparisons: 15
- Supported differences: 12
- Inconclusive comparisons: 3

## Family-Level Diagnostics

| model_family | models_in_family | median_official_mase | median_official_rmsse |
| --- | --- | ---: | ---: |
| lightweight_neural | FastNeuralAR_MLP | 739.921888 | 164.622417 |
| machine_learning | LightGBM, XGBoost | 15.294335 | 3.971088 |
| statistical | AutoARIMA, Theta, ETS Explicit | 8.088530 | 1.859013 |

## FastNeuralAR_MLP Risk / Performance Note

FastNeuralAR_MLP remains included, but is flagged for Audit #4 review because its official median MASE is 739.921888 and official median RMSSE is 164.622417. This is diagnostic evidence only and not a removal decision.

## Outlier Risk Review

- Risk flags: 4

## Validation Results

- Checks passed: 14
- Checks failed: 0

## Scope and Safety Findings

- No rankings, tournament scores, winners, or champions were created.
- Baseline aggregation/significance outputs and Shiny were not modified.

## Readiness for Audit #4

**PROCEED_TO_AUDIT_4_OFFICIAL_CHALLENGER_RESULTS_READINESS_AUDIT**
