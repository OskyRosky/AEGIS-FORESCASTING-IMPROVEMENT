# Stage 06 Block 6.4 Dashboard Governance Contract

## Purpose
This block defines the formal read-only governance contract that the future Shiny MVP dashboard must follow.

## Dashboard Governance Principles
The dashboard is a presentation layer. It must not rerun models, regenerate forecasts, recalculate MASE/RMSSE, recompute aggregation/significance, change champion decisions, or hide risks and deferrals.

## Required Dashboard Sections
The MVP dashboard requires Executive Summary, Champion Decision, Champion Conditions, Model Universe, Tournament Standings, Baseline vs Challenger Scorecard, Pairwise Evidence, Risk Register, Deferred Models, Audit Status, Governance Actions, Methodology / Metric Policy, and Dashboard Handoff / Source Artifacts.

## Data Binding Contract
The data binding contract maps each dashboard section to audited CSV/MD artifacts. Allowed transformations are limited to display filtering, sorting, grouping, and label renaming. Prohibited transformations include recomputing metrics, changing champion decisions, changing confidence, hiding risks, and dropping deferred models.

## Do / Don't Rules
Dashboard copy must say ETS Explicit was selected as champion with conditions. It must not say ETS Explicit won, is the absolute best model, replaces all models, or has no caveats.

## Required Warning Labels
The contract requires labels for conditional champion status, medium confidence, tournament-standing caveat, FastNeuralAR_MLP high-risk investigation, NBEATS/NHITS deferral, Audit #5 approve-with-conditions, and no-recompute metric policy.

## Champion Communication Requirements
ETS Explicit must be shown as CHAMPION_SELECTED_WITH_CONDITIONS with confidence = medium. Tournament standings must be shown as evidence, not as a champion decision.

## Risk And Deferred Model Visibility
FastNeuralAR_MLP risk and NBEATS/NHITS deferrals must remain visible. They must not be hidden or described as discarded.

## Audit Status Visibility
Audit #5 approved dashboard handoff with conditions and the governed F-010 correction remains traceable.

## Read-Only / No-Recompute Requirements
Shiny must load static artifacts and may only transform them for display. It must not compute new metrics, scores, rankings, or champion decisions.

## Traceability
Dashboard requirements trace to champion decision, closure pack, tournament outputs, Audit #5, and Stage 06 governance artifacts.

## Validation Results
Validation failures: 0.

## Scope And Safety
No Stage 05 outputs, prior Stage 06 outputs, or Shiny files were modified.

## Next Step
Proceed to 6.5 Governance Closure Pack if inspection passes.

Generated: 2026-06-14T10:49:31
