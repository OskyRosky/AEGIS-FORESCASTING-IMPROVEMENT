# Denominator Reconciliation Report - Block 5.27A

Created timestamp: 2026-06-12T14:43:07

## AUDIT #3 Major-1 Finding

AUDIT #3 found that the prior MASE/RMSSE implementation used test-horizon lag-1 flat naive forecast error as the denominator. That conflicted with the approved benchmark semantics requiring a training-only lag-1 naive denominator.

## Selected Fix

Option A was implemented:

- MASE denominator = in-sample training-only lag-1 naive MAE.
- RMSSE denominator = in-sample training-only lag-1 naive MSE.
- Denominators are computed independently for each `entity_key` + `window_id`.
- Only `record_type == actual` rows with `actual_date <= train_end_date` are used.
- Test-horizon actuals, Block 5.19 naive forecasts, seasonal naive forecasts, Drift, and previous metric tables are not used as denominators.
- Epsilon floor = `1e-6`.

## Code Changes

- Added `python/model_lab/benchmark_denominators.py`.
- Updated `calculate_mase.py` and `calculate_rmsse.py` to consume training-only denominators.
- Updated `apply_non_negative_policy.py` and inspector logic to recompute adjusted metrics with training-only denominators.
- Regenerated downstream aggregation and statistical significance outputs from corrected adjusted metrics.

## Documentation and Config Changes

- Updated `docs/benchmark_semantics/benchmark_semantics_v1.md`.
- Updated `config/scoring_definitions.yaml`.
- Updated `config/ranking_policy.yaml`.

## Outputs Regenerated

- `outputs/model_lab/denominator_reconciliation/`
- `outputs/model_lab/mase/`
- `outputs/model_lab/rmsse/`
- `outputs/model_lab/non_negative_policy/` metric-derived outputs
- `outputs/model_lab/aggregation_hierarchy/`
- `outputs/model_lab/statistical_significance/`

## Denominator Results

- denominator rows: 454
- entities: 39
- windows: 454
- MASE floored rows: 0
- RMSSE floored rows: 0
- median MASE denominator: 35.978816480006145
- median RMSSE denominator: 22479.82042517081

## Before/After Headline Metrics

- previous global median MASE: 0.9995779032967591
- corrected global median MASE: 11.434868860671395
- previous global median RMSSE: 1.0042237370985716
- corrected global median RMSSE: 3.1022343013746028
- previous denominator floored rows: 56
- corrected MASE denominator floored rows: 0
- corrected RMSSE denominator floored rows: 0

## Regenerated Output Checks

- MASE rows: 3178
- RMSSE rows: 3178
- non-negative MASE median after: 11.434868860671395
- non-negative RMSSE median after: 3.089294350289633
- aggregation entity-window rows: 3178
- significance pairwise comparisons: 21

## Validation Results

- denominator unit tests passed: True
- inspectors passed for MASE, RMSSE, non-negative policy, aggregation hierarchy, and statistical significance during Block 5.27A execution.

## Closure Rationale

Major-1 is closed because code, docs, configs, metric outputs, aggregation outputs, and statistical significance outputs now share the same official training-only lag-1 denominator definition. Block 5.19 naive benchmark forecasts remain valid reference forecasts but are no longer used as the MASE/RMSSE denominator.
