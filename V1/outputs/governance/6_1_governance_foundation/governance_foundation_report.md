# Block 6.1 - Governance Foundation

Generated: 2026-06-14T10:24:31

## Purpose of Stage 06

Stage 06 converts Model Lab outputs into governance rules, decision language,
risk carry-forward, and dashboard-safe contracts. It is not another Model Lab.

## Output Location

All new artifacts are written under `outputs/governance/` to keep governance
additions separate from audited Stage 05 outputs.

## Relationship to Stage 05

Stage 05 remains the source for model execution, metrics, tournament, and
champion decision artifacts. Stage 06 interprets those outputs for governance
and dashboard handoff without modifying them.

## Core Governance Principles

1. Evidence over rank.
2. No silent loss of risk.
3. Single source of truth.
4. Additive correction over silent mutation.
5. Honest dashboard communication.

## Tournament Rank vs Champion Decision

Tournament standing is preliminary evidence. It is not the same as a champion
decision. The champion decision source of truth is `champion_decision.csv`.

## ETS Explicit as Conditional Champion

ETS Explicit is the selected champion with conditions and medium confidence.
It must not be described as an unconditional or absolute winner.

## F-010 Handling

Audit #5 F-010 is resolved through an additive governed correction. The Stage
05 manifest is not edited; downstream consumers should interpret the closure
summary artifact as present.

## Dashboard Risk Disclosure

Shiny and future dashboards must surface risks and conditions, including
FastNeuralAR_MLP high-risk behavior, NBEATS runtime deferral, NHITS dependency
deferral, and the conditional champion state.

## Source Safety

No models, forecasts, metrics, tournament artifacts, champion decision outputs,
Stage 05 artifacts, or Shiny files were modified by Blocks 6.0/6.1.
