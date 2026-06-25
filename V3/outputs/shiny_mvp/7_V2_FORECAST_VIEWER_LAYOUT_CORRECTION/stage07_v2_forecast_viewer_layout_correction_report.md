# Stage 07 — V2 Forecast Viewer Layout Correction

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_FORECAST_VIEWER_LAYOUT_CORRECTION
**Page:** Forecasting > Viewer (`section_explorer`) — V2 only
**App:** http://127.0.0.1:3838 · PID 16284 · HTTP 200 · LEN 198334

## Root cause of "it still looks the same"
The Viewer code already had the corrected stacked layout (setup card on top, chart
below). The reason Oscar still saw the old **left-controls / right-chart** layout is
that he was viewing a **stale Shiny instance (PID 23372) on port 3838** that had been
started *before* the previous rewrite — it was serving the old `section_explorer`. The
new layout was running on port 3839. This stage stops both stale instances and relaunches
a single clean instance on **port 3838**, so the URL Oscar normally opens now serves the
corrected page. The requested label/chart refinements were also applied.

## Files modified
- `shiny_app/ui/tabs.R` — series label "Series" → **"Select key / series"**; subtitle reworded ("does not generate future forecasts"); chart height 520px → **600px** with `.fvb-chart-wrap` class.
- `shiny_app/www/custom.css` — added `.fvb-chart-wrap` (full-width, larger chart) rules.
- `shiny_app/ui/body.R` — CSS cache-bust `?v=20260624g` → `?v=20260624h`.

## Files created
- `outputs/shiny_mvp/7_V2_FORECAST_VIEWER_LAYOUT_CORRECTION/stage07_v2_forecast_viewer_layout_correction_report.md`
- `..._validation.csv`
- `..._launch.csv`

## Layout before vs after
- **Before (what Oscar saw on stale 3838):** two columns — vertical setup steps on the left, chart on the right, data notes in the right column.
- **After:** one **full-width setup box** ("Set up the backtest view") with Select key/series · Horizon · History window · Analyze Backtest on Row A and model family cards on Row B; then a **full-width 600px chart** below; then **Data notes** below the chart, only after Analyze Backtest.

## Action-gating (unchanged, verified)
`fvp_request <- eventReactive(input$fvp_go, …)`; both `fvp_chart` and `fvp_notes` show
empty states until `input$fvp_go > 0`; selectors do not auto-render; chart container is
static in the DOM.

## Guardrails honored
V2 only; V1 untouched. No data/governed-artifact writes. No models/forecasts/tournaments
run. No metric recompute (MASE/RMSSE). Champion (ETS Explicit under conditions) unchanged.
Forward Forecast not in Viewer. Viewer reads `forecast_viewer_model_outputs.csv` only (not
`forecasts.csv`). No Scenario dropdown added.

## Validation
- Parse: tabs.R / server.R / body.R → PARSE_ALL_OK.
- Isolated render smoke: **19/19 TRUE** (incl. select_key_label, setup_box, result_block, chart_600, no_old_two_col, no_analyze_forecast, no_forward_chart, no_forecasts_csv).
- Live: HTTP 200, LEN 198334, stderr clean, single instance on 3838.

## Launch
- URL http://127.0.0.1:3838 · PID 16284.
- Logs: `outputs/shiny_mvp/7_V2_FORECAST_VIEWER_LAYOUT_CORRECTION/logs/viewer_layout_correction_stdout.log` (+ `_stderr.log`).
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 16284`.
