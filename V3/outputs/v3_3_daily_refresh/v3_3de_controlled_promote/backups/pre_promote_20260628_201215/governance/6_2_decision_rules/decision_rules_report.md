# Stage 06 Block 6.2 Decision Rules / Action Framework

## Purpose
Block 6.2 converts Model Lab evidence, risks, statuses, and champion conditions into explicit governance actions for downstream decision making and dashboard-safe communication.

## Inputs Read
The block reads Stage 06 6.0/6.1 governance artifacts, Stage 05 closure-pack outputs, champion-decision artifacts, tournament/sanity context, and Audit #5 context. No source artifact is edited.

## Action Framework
The framework defines KEEP, KEEP_WITH_CONDITIONS, MONITOR, REVIEW, REVIEW_INVESTIGATE, TEST_LATER, DEFER, EXCLUDE_FROM_CHAMPION_CONSIDERATION, SURFACE_ON_DASHBOARD, DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER, BENCHMARK_REFERENCE, and MODEL_POOL_REFERENCE.

## Risk-To-Action Mapping
Risks R-001 through R-007 are mapped to governed actions. All active risks and conditions carry forward to dashboard-safe communication.

## Model-Level Recommendations
All 15 final Model Lab models are assigned governance recommendations. Non-champion active models remain governed reference models unless a specific risk or deferral rule applies.

## ETS Explicit Governance
ETS Explicit remains the selected champion with conditions. It is governed as KEEP_WITH_CONDITIONS + MONITOR. It must not be described as an unconditional winner.

## FastNeuralAR_MLP Governance
FastNeuralAR_MLP is retained transparently but mapped to REVIEW_INVESTIGATE + EXCLUDE_FROM_CHAMPION_CONSIDERATION because of high MASE/RMSSE behavior and possible scale or recursive-collapse risk.

## NBEATS / NHITS Governance
NBEATS and NHITS are mapped to TEST_LATER + DEFER. They are deferred future-work candidates, not discarded concepts.

## FixedGrowth_6 Governance
FixedGrowth_6 is mapped to REVIEW + MONITOR due to manual review carry-forward.

## Audit And Sanity Carry-Forward
Audit #4, Audit #5 F-010, and 5.30A carry-forwards are preserved through traceability and dashboard surfacing rules.

## Dashboard Implications
The dashboard must surface champion conditions, medium confidence, active risks, deferrals, and manual-review flags. Tournament standing must not be presented as a champion decision.

## Validation Results
Validation failures: 0.

## Scope And Safety
No models, forecasts, metrics, aggregation, significance, tournament outputs, champion decision outputs, Stage 05 files, prior Stage 06 files, or Shiny files were modified.

## Next Step
Proceed to 6.3 Champion Conditions Protocol if inspection passes.

Generated: 2026-06-14T10:32:59
