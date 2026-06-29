# Model Lab Closure Report

Generated: 2026-06-13T20:36:01

## Executive Summary

Stage 05 / Model Lab is completed pending final audit. ETS Explicit was selected as champion with conditions and medium confidence.

## Stage 05 Objective

Evaluate baseline and challenger forecasting models under corrected benchmark semantics, official metrics, aggregation, significance, tournament, and champion-decision governance.

## What Was Built

The stage produced baseline metrics, challenger execution and metrics, aggregation/significance layers, tournament artifacts, sanity review, champion decision, and this closure pack.

## Final Model Universe

The final universe includes 7 baseline models, 6 final challengers, and 2 deferred models.

## Challenger Journey

The challenger set was re-scoped after NBEATS became runtime-impractical and NHITS remained dependency-blocked. FastNeuralAR_MLP was added as a lightweight neural comparison.

## NBEATS/NHITS Deferral Rationale

NBEATS is deferred for MVP/runtime practicality. NHITS is deferred for Python 3.14 / neuralforecast / ray incompatibility.

## FastNeuralAR_MLP Rationale and Risk

FastNeuralAR_MLP provided a lightweight neural benchmark but showed high-risk MASE/RMSSE behavior consistent with possible scale or recursive-collapse issues. It remains documented for future investigation.

## Official Metrics / Tournament Summary

Tournament models: 13. Pairwise comparisons: 78. Champion decision: CHAMPION_SELECTED_WITH_CONDITIONS.

## Champion Decision Summary

Selected champion: ETS Explicit (challenger, statistical). Confidence: medium. Conditions: Proceed through 5.31B closure pack; retain FastNeuralAR_MLP high-risk investigation and NBEATS/NHITS exclusion notes as non-champion conditions..

## Conditions and Risks

The final risk register preserves FastNeuralAR_MLP, NBEATS, NHITS, Audit #4, tournament sanity, and medium-confidence champion-selection conditions.

## Dashboard Handoff

Dashboard handoff artifacts are listed in `model_lab_dashboard_handoff_manifest.csv`. Shiny was not modified in this stage.

## Artifacts Inventory

Important artifacts are inventoried in `model_lab_artifact_manifest.csv`.

## Recommendation for Audit #5

PROCEED_TO_AUDIT_5_MODEL_LAB_CLOSURE_DASHBOARD_HANDOFF_AUDIT
