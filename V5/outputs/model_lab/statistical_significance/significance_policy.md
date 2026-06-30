# Statistical Significance Policy - Stage 5.25

Created timestamp: 2026-06-12T14:42:38

## Metrics

- MASE is the primary metric.
- RMSSE is guardrail only.
- RMSSE context is included in model summaries, but RMSSE is not used to determine statistical significance.

## Comparison Unit

Significance testing uses entity-level median MASE from `aggregation_by_entity_model.csv`.
Raw forecast rows are not used as the official significance unit, so entities with more windows do not dominate the evidence.

## Methods

- Paired bootstrap is performed over entities.
- The bootstrap uses 10,000 iterations and deterministic seed `20260612`.
- The sign test is paired by entity and ignores exact ties in the binomial denominator.
- Benjamini-Hochberg correction is applied across the 21 pairwise sign-test p-values.
- The practical threshold is `0.02` MASE.

## Evidence Scope

Pairwise support is not a champion decision. No model ranking is created in this block. Champion selection is deferred to later blocks.
