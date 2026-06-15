# Aggregation Policy - Stage 5.24

Created timestamp: 2026-06-12T14:42:20

## Official Metrics

- MASE is the primary benchmark metric.
- RMSSE is guardrail only.
- Official scores use non-negative adjusted forecasts from Block 5.23.

## Official Model Score

The official model MASE is calculated with equal entity weighting:

1. For each entity/model, calculate the median MASE across that entity's windows.
2. For each model, calculate the median of those entity/model median MASE values across entities.

This is recorded as `official_median_mase`.

## RMSSE Guardrail Aggregation

RMSSE follows the same hierarchy:

1. For each entity/model, calculate the median RMSSE across that entity's windows.
2. For each model, calculate the median of those entity/model median RMSSE values across entities.

This is recorded as `official_median_rmsse`, but RMSSE remains a guardrail metric only.

## Diagnostics

Row-level means and p95 values are diagnostics only. They are not official model scores.

## Weighting Policy

Equal entity weighting is enforced. Entities with more windows do not dominate the global model score.

## Deferred Decisions

No champion is selected in this block. No ranking is created in this block. Final winner selection is deferred to later blocks.
