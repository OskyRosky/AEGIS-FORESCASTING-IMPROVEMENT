# Stage 07 Tournament Score Formula & Composite Score Readiness Audit

## Purpose
Read-only diagnostic to determine whether an official governed Tournament Score formula with explicit weights already exists, and whether the ingredients exist to design a future Composite Tournament Score layer.

## Bottom Line
No governed official composite Tournament Score formula with explicit numeric weights was found.
Governed tournament metrics and evidence are available: official median MASE, official median RMSSE, pairwise evidence, guardrail/risk status, champion eligibility, champion confidence, and conditions.

## Score / Formula Findings
- `tournament_model_scorecard.csv` contains model-level MASE/RMSSE, guardrail, risk, and champion eligibility columns.
- Existing score-like columns in tournament scorecard: none.
- Existing rank/position columns in tournament scorecard: none.
- Historical/config/documentation references to ranking/weights exist, but they were not found as a final governed composite Tournament Score formula for Stage 07 display.
- No final governed numeric weights were found.

## Tournament Scorecard Summary
- Row count: 13
- Models included: ARIMA_Fixed, ETS_Current, FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6, LinearRegression, AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, FastNeuralAR_MLP
- Columns: run_id, model_name, model_origin, model_family, entity_count, official_median_mase, official_median_rmsse, median_wmape, median_smape, median_bias, mase_guardrail_status, rmsse_guardrail_status, risk_status, audit_risk_flag, eligible_for_champion_consideration, champion_exclusion_reason, created_timestamp
- MASE exists: yes (`official_median_mase`).
- RMSSE exists: yes (`official_median_rmsse`).
- Coverage exists: partial (`entity_count`).
- Risk/eligibility exists: yes (`risk_status`, `audit_risk_flag`, `eligible_for_champion_consideration`, `champion_exclusion_reason`, guardrail statuses).
- Champion flag exists in related champion/universe artifacts, not as a selected-champion flag in the tournament scorecard.
- Existing weighted score/rank appears already computed: no.

## Pairwise Evidence Summary
- Pairwise rows: 78
- Columns: run_id, model_a, model_b, model_a_origin, model_b_origin, paired_entity_count, median_delta_mase, bootstrap_ci_low, bootstrap_ci_high, sign_test_p_value, bh_adjusted_p_value, practical_threshold, practically_meaningful, statistically_supported, comparison_status, created_timestamp
- Grain: pairwise model_a x model_b, plus separate model-level evidence summary artifact.
- Pairwise evidence can support Tournament page visualizations: yes, as governed pair-level evidence and model-level support counts.

## Champion Governance Confirmation
- Selected champion under conditions: `ETS Explicit`.
- Decision type: `CHAMPION_SELECTED_WITH_CONDITIONS`.
- Median MASE: `6.901143533373399`.
- Median RMSSE: `1.856193218184295`.
- Pairwise supported better / worse: `8` / `0`.
- Confidence: `medium`.
- Conditions: `Proceed through 5.31B closure pack; retain FastNeuralAR_MLP high-risk investigation and NBEATS/NHITS exclusion notes as non-champion conditions.`.
- Total pairwise comparisons: `78` from tournament summary.
- Dashboard-approved language examples found: ETS Explicit was selected as champion with conditions. | ETS Explicit is the current recommended champion candidate under the Model Lab governance framework. | The champion decision has medium confidence and must be interpreted with documented carry-forward risks.

## Composite Score Readiness
Classification: Requires Oscar decision on weights.
The ingredients are largely ready as governed components, but no final official weighted formula exists. A future Composite Tournament Score would need explicit approval before implementation.

## Optional Future Scoring Design Questions for Oscar
- Should a score be UI-only/proposed or become a governed scoring artifact?
- Should MASE/RMSSE form the accuracy core, and should RMSSE be a penalty or guardrail badge?
- Should pairwise support contribute numerically or remain a separate evidence panel?
- Should coverage be a penalty, separate column, or eligibility filter?
- Should risk/conditions be numeric penalties or visible badges only?
- Should confidence affect the score or remain explanatory only?
- Should high-risk/deferred models remain visible but excluded from champion consideration?

## Validation
- PASS: no data artifacts modified.
- PASS: no Shiny source files modified.
- PASS: no models run.
- PASS: no forecasts generated.
- PASS: no tournaments rerun.
- PASS: no metrics recalculated.
- PASS: no champion decision changed.
- PASS: only audit outputs were created under `outputs/shiny_mvp/7_TOURNAMENT_SCORE_AUDIT/`.

## Recommendation
READY_FOR_OSCAR_REVIEW_TOURNAMENT_SCORE_AUDIT