# Stage 07 — V2 Forecast Page Layout Cleanup

## General Summary
Refactored **Forecasting > Forecast** to follow the approved Viewer/Accuracy layout pattern.
The page now opens with a collapsed **"How to use this forecast view"** guide, a full-width
**"Set up the forecast view"** box with numbered controls (1 Select key / series, 2 Forecast
window, 3 Actual history window, 4 Analyze Forward Forecast), and a separate open
**"Forecast Chart"** results box that holds the chart plus the Data notes. The old left-controls /
right-chart split was removed. Visible label "Forward chart" was renamed to **"Forecast Chart"**.
Server logic, inputs/outputs and action-gating were reused unchanged. Only `ui/tabs.R` was edited.

## Files Created
- outputs/shiny_mvp/7_V2_FORECAST_PAGE_LAYOUT_CLEANUP/stage07_v2_forecast_page_layout_cleanup_report.md
- outputs/shiny_mvp/7_V2_FORECAST_PAGE_LAYOUT_CLEANUP/stage07_v2_forecast_page_layout_cleanup_validation.csv
- outputs/shiny_mvp/7_V2_FORECAST_PAGE_LAYOUT_CLEANUP/stage07_v2_forecast_page_layout_cleanup_launch.csv

## Files Modified
- shiny_app/ui/tabs.R — `section_forecast()` refactored to the home_collapse + setup box + results box pattern; removed now-unused local `fv_step` helper.

## Forecast Page Before
- Title + subtitle, then a single `fvx-section` with a two-column `fv-setup` layout: setup panel on the left (steps 1–4) and a `fv-result` chart panel on the right (steps 5–6 chart + data notes). Old "Forward chart" label and "Set up the forward view" title.

## Forecast Page After
1. Page title **Forecast** + single-model subtitle.
2. Collapsed **How to use this forecast view** guide.
3. Full-width **Set up the forecast view** box, numbered steps 1–4, Analyze at the bottom.
4. Full-width **Forecast Chart** results box (open) with the chart, then Data notes.
5. Short footer note.

## How To Use Forecast Status
PRESENT and COLLAPSED by default (`home_collapse(..., open = FALSE)`). Explains solid = actual history, dashed = future forecast from forecasts.csv, vertical boundary = forecast start, one selected production model per key/series, and that multi-model backtest comparison lives in Viewer.

## Setup Box Status
Separate full-width box `fvx-section fvx-forward fvb fvb-setup-section` titled **Set up the forecast view**, controls only.

## Numbered Controls Status
1 Select key / series (`fvf_series`) · 2 Forecast window (`fvf_window`) · 3 Actual history window (`fvf_history`) · 4 Analyze Forward Forecast (`fvf_go`).

## Analyze Forward Forecast Placement Status
Final step at the bottom of the setup box, in a `fvb-analyze-row` after the controls.

## Forecast Chart Results Box Status
Separate **Forecast Chart** `home_collapse` (open by default) below the setup box; chart `highchartOutput("fvf_chart")` at 560px (wider than the old right column). Label "Forward chart" removed.

## Data Notes Placement Status
Inside the Forecast Chart box, directly below the chart (`uiOutput("fvf_notes")`); renders only after Analyze Forward Forecast.

## Action-Gated Behavior Status
Preserved. `fvf_chart` shows an empty state until `input$fvf_go > 0`; `fvf_notes` shows a hint until clicked; both snapshot via `eventReactive(input$fvf_go)`. Changing selectors does not auto-refresh.

## Data Source Confirmation
Reads `data/processed/actuals.csv` (`fvf_actuals()`) + `data/processed/forecasts.csv` (`fvf_forecasts()`). Does NOT read `forecast_viewer_model_outputs.csv`.

## Confirmation Forecast Is Separate From Viewer
Viewer (`section_viewer()`) was not modified; Forward Forecast remains on the dedicated Forecast page only.

## Confirmation No Data/Governed Artifacts Were Modified
Only `ui/tabs.R` (UI) was edited. No data/processed or governed artifacts touched.

## Confirmation No Models / Forecasts / Tournaments Were Run
None executed.

## Confirmation No Metrics Were Recomputed
No MASE/RMSSE or other metric recomputation.

## Confirmation Champion Decision Was Not Changed
No champion logic touched.

## Validation Summary
Parse OK; 18/18 render smoke checks TRUE (title, collapsed how-to, setup box, steps 1–4, analyze button, Forecast Chart box, no "Forward chart" label, chart + notes outputs, footer, no viewer csv, order setup→chart and chart→notes). See validation.csv (all PASS).

## App Launch Details
- URL: http://127.0.0.1:3838
- PID: 30112
- HTTP: 200, content length 205258
- stderr: clean
- Logs: outputs/shiny_mvp/7_V2_FORECAST_PAGE_LAYOUT_CLEANUP/logs/forecast_layout_{stdout,stderr}.log
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 30112`

## What Oscar Should Review
Open Forecasting > Forecast and confirm the order: How to use (collapsed) → Set up the forecast view (steps 1–4, Analyze at the end) → Forecast Chart (chart + Data notes after Analyze). Confirm the chart renders only after clicking Analyze Forward Forecast and refreshes when re-clicked after changing the key/series, window or history.

## Total Execution Time
~5 minutes.

READY_FOR_OSCAR_VISUAL_REVIEW_V2_FORECAST_PAGE_LAYOUT_CLEANUP
