# Block 5.30 - Tournament Engine Report

Generated: 2026-06-13T18:07:40

## Purpose

Build a unified baseline + challenger tournament framework with preliminary standings and pairwise evidence. This block does not select a winner or champion.

## Audit #4 Approval Status

- Verdict: APPROVE_WITH_CONDITIONS_TO_PROCEED_TO_5.30_TOURNAMENT_ENGINE
- Blockers: 0
- Major findings: 0

## Baseline Model Universe

ARIMA_Fixed, ETS_Current, LinearRegression, FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6

## Challenger Model Universe

AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, FastNeuralAR_MLP

## Excluded / Deferred Models

- NBEATS: deferred_runtime_impractical; partial/checkpoint rows are not consumed.
- NHITS: deferred_dependency_blocked.

## Official Metrics and Aggregation Logic

Primary metric is official_median_mase. RMSSE is a guardrail. The tournament consumes entity-level medians and model-level equal-entity-weighted medians from audited aggregation artifacts.

## Pairwise Evidence Method

Pairwise evidence uses entity-level paired MASE, 10,000 bootstrap iterations, seed 20260612, exact sign tests, BH correction, and practical threshold 0.02.
- Pairwise comparisons: 78
- Supported differences: 43
- Inconclusive comparisons: 35

## Preliminary Standings Disclaimer

Preliminary standings are for 5.30A sanity review only. Position 1 is not a winner and not a champion. Final champion/no-champion decision is deferred to 5.31.

| position | model_name | origin | official_median_mase | official_median_rmsse | risk_status | audit_risk | eligible_for_champion_consideration |
| ---: | --- | --- | ---: | ---: | --- | --- | --- |
| 1 | ETS Explicit | challenger | 6.901144 | 1.856193 | low | False | True |
| 2 | AutoARIMA | challenger | 8.088530 | 1.859013 | low | False | True |
| 3 | FixedGrowth_1_5 | baseline | 8.649281 | 2.271838 | low | False | True |
| 4 | ETS_Current | baseline | 8.654171 | 2.273019 | low | False | True |
| 5 | LinearRegression | baseline | 9.495769 | 2.751763 | low | False | True |
| 6 | Theta | challenger | 10.642290 | 2.819225 | low | False | True |
| 7 | ARIMA_Fixed | baseline | 11.789916 | 3.493345 | low | False | True |
| 8 | FixedGrowth_3 | baseline | 12.989046 | 3.019316 | low | False | True |
| 9 | XGBoost | challenger | 14.547628 | 3.880790 | low | False | True |
| 10 | LightGBM | challenger | 16.041042 | 4.061386 | low | False | True |
| 11 | FixedGrowth_4 | baseline | 16.529080 | 4.072356 | low | False | True |
| 12 | FixedGrowth_6 | baseline | 27.015391 | 5.083541 | medium | False | True |
| 13 | FastNeuralAR_MLP | challenger | 739.921888 | 164.622417 | high | True | False |

## Risk Register

- Risk rows: 14
- FastNeuralAR_MLP high-risk condition is carried forward.
- NBEATS partial-row condition is carried forward.

## Validation Results

- Checks passed: 15
- Checks failed: 0

## Scope and Safety Findings

- No forecasts or metrics were recalculated.
- Baseline, challenger source, Audit #4, and Shiny outputs were not modified.
- No winner or champion artifact was created.

## Recommendation for 5.30A

**PROCEED_TO_5.30A_TOURNAMENT_SANITY_REVIEW**
