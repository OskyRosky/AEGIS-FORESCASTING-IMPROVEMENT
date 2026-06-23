# Stage 07 Models Champion Page MVP - Block B

## Purpose
Extended Models > Champion with Series-Level Diagnostic Evidence below the preserved governed Champion Decision Block A.

## Source
Selected source: `outputs/model_lab/tournament_engine/tournament_entity_model_scores.csv`. It contains 507 rows, 39 series, and 13 models at entity x model grain.

## Diagnostic Method
Series-level leadership is based on the lowest existing governed `median_mase` per entity. Existing `median_mase` and `median_rmsse` values are read from the artifact; MASE/RMSSE are not recomputed from raw actuals or forecasts.

## Summary
- Total series: 39
- Models evaluated per series: 13
- Series where ETS Explicit leads: 4
- Series where ETS Explicit does not lead: 35
- Most frequent series-level leader: Theta (8)
- Largest ETS gap vs local leader: 51.981

## Tie Handling
Exact ties on the lowest median MASE are retained. All tied leaders are shown in the series-level evidence table and counted in the leadership count chart.

## UI Added
- Diagnostic summary cards
- Leadership count chart
- Series-level evidence table
- Exceptions review table
- Diagnostic governance note
- Source lineage update for `tournament_entity_model_scores.csv`

## Scope Controls
This diagnostic section does not change the champion decision, does not create a composite score, and does not introduce weights. Local series-level leadership does not replace ETS Explicit as selected champion under conditions.

## Launch Result
- URL: http://127.0.0.1:3838
- Port: 3838
- PID: 36268
- HTTP status: 200
- Stop command: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny_v1.ps1 -PidToStop 36268`

## Validation
Validation outputs are in `stage07_models_champion_series_evidence_mvp_validation.csv`. All checks passed.

## Safety
No data artifacts, Stage 05 outputs, Stage 06 outputs, processed data, model outputs, forecasts, tournaments, or champion decisions were modified.
