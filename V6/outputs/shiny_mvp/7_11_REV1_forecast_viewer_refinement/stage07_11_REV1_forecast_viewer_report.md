# Stage 07 — Block 7.11-REV1 — Forecast Viewer Interaction + Layout Refinement

## Summary
The Forecast Viewer (FORECASTING / Viewer) was refined from an auto-rendering, single-row
control page into an intentional, guided forecast-analysis workflow. The chart no longer
appears until the user completes the setup and clicks **Analyze forecast**. All data remains
read-only and is sourced from the governed 7.0E loader. No forecasts, metrics, models, or
champion decisions were generated, recalculated, or changed.

## Workflow
1. Select series / entity — "Choose the forecast series to inspect."
2. Select model — honest availability note + diagnostic (per-entity vs global counts).
3. Select horizon — 5 / 10 / 15 / 20 / 25 / 30 / 45 / 60 days.
4. Select history window — Last 30 / 60 / 90 / 180 days / All history.
5. Click **Analyze forecast** → availability panel + interactive chart render.

Before the click, a clean empty-state card is shown ("No forecast rendered yet …").

## Model availability finding
All 45 entities in `forecasts.csv` have **exactly one** `model_version` each; there are
**16 distinct models globally**. Because no entity contains more than one model, a
"compare multiple models" option would be fictitious and was intentionally **not** added.
Instead, a per-entity note honestly states: "Only one model is available for this selected
series in the current forecast artifact," plus a diagnostic line with the per-entity and
global model counts. See `stage07_11_REV1_model_availability_by_entity.csv`.

## Chart implementation
- highcharter 0.9.5 stock chart (`highchart(type = "stock")`).
- Actual = solid blue line (#2e75b6); Forecast = dashed amber line (#d97706).
- Dashed vertical plot line marks the forecast start.
- Shared tooltip header shows entity · model; points show date + value.
- Title = selected entity; subtitle = "Model: <model>".

## Horizontal navigation / zoom
Enabled via the stock chart: `hc_navigator` (drag handles), `hc_scrollbar`,
`hc_rangeSelector` (1m / 3m / 6m / YTD / All), x-axis `zoomType = "x"`, and shift-key panning.
This gives true horizontal time navigation, not just a single zoom — no limitation to report.

## Data sources (read-only)
forecasts.csv (forecast_value, model_version), actuals.csv (actual_value), plus entities.csv
for reference. forecast_comparison.csv is empty and not used.

## Safety
Work confined to V1/shiny_app. No writes to model_lab / data/processed / governance / audit.
No forbidden language. Dashboard remains read-only.

## Result
HTTP 200, LEN 76999. App listening at http://127.0.0.1:3838.
Recommendation: READY_FOR_OSCAR_VISUAL_REVIEW_7_11_REV1_FORECAST_VIEWER
