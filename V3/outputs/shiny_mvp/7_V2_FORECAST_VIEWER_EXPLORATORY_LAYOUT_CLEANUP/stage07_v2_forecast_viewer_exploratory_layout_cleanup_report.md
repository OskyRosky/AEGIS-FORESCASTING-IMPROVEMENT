# Stage 07 — V2 Forecast Viewer Exploratory Backtest Layout Cleanup

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_FORECAST_VIEWER_EXPLORATORY_LAYOUT_CLEANUP
**Page:** Forecasting > Viewer (`section_explorer`) — V2 only
**App:** http://127.0.0.1:3839 · PID 33852 · HTTP 200 · LEN 198237

## 1. General summary
Forecasting > Viewer was rebuilt from a tall two-column "Set up the backtest view"
panel into a compact, **horizontal** exploratory sandbox. Controls (series, horizon,
history window, Analyze) sit on one wrapping row; model family cards wrap horizontally
below; the chart is full-width with the data notes beneath it. A new collapsible
**"How to use this viewer"** block (open by default) explains that the page is
exploratory, compares historical actuals vs historical backtest forecasts, and does
**not** generate forecasts, recompute metrics, or change the champion. Action-gating
is preserved (chart/notes render only after **Analyze Backtest**). No data, models,
metrics, or champion decisions were touched.

## 2. Files created
- `outputs/shiny_mvp/7_V2_FORECAST_VIEWER_EXPLORATORY_LAYOUT_CLEANUP/stage07_v2_forecast_viewer_exploratory_layout_cleanup_report.md`
- `..._validation.csv`
- `..._sources.csv`
- `..._launch.csv`

## 3. Files modified
- `shiny_app/ui/tabs.R` — `section_explorer()` fully rebuilt (horizontal layout + How-to-use block).
- `shiny_app/server/server.R` — Viewer empty-state wording "Analyze Forecast" → "Analyze Backtest" (2 spots). Logic unchanged.
- `shiny_app/www/custom.css` — `.fvp-model-grid` now wraps horizontally; new `.fvb*` layout block (+ dark variants).
- `shiny_app/ui/body.R` — CSS cache-bust `?v=20260624f` → `?v=20260624g`.

## 4. Viewer data source confirmation
Source (unchanged): `data/processed/forecast_viewer_model_outputs.csv`
- Rows: **177,060**
- Unique series: **39** · series_key column = `series_key`
- Unique models: **13** (ARIMA_Fixed, AutoARIMA, ETS Explicit, ETS_Current, FastNeuralAR_MLP, FixedGrowth_1_5/3/4/6, LightGBM, LinearRegression, Theta, XGBoost)
- Horizons in artifact: 1–30 (Viewer exposes 5–30)
- Date range: **2025-05-03 → 2026-04-27**
- Sample series: APC-Dedicated, APC-MSIT, APC-Multitenant, ARE-Go Local, AUS-Go Local, BRA-Go Local
- Viewer does **not** read `forecasts.csv`.

## 5. Series scope / HDD question
The Viewer is **not HDD-specific**. Its series are the **governed AX backtest series**
(region/segment keys like `APC-Dedicated`, `ARE-Go Local`), i.e. the historical
model-comparison universe in `forecast_viewer_model_outputs.csv`. The underlying
ingestion table is HDD-region based, but the Viewer artifact does not prove an
HDD-only filter — it is the governed multi-model backtest universe (39 eligible
series). A user-facing note now states: "Series come from the governed backtest
artifact — the historical model-comparison universe used by the Viewer."

## 6. Viewer page before
- Title "Forecast Viewer" + subtitle about "renders only after you click".
- Tall **two-column** layout: left = vertical numbered steps 1–5 (series, models as a tall
  family list, horizon, history, Analyze); right = chart + notes. Vertically heavy.

## 7. Viewer page after
- Title **"Forecast Viewer"** + subtitle "Exploratory historical backtest comparison…".
- Collapsible **"How to use this viewer"** (open) explaining the exploratory purpose.
- One **horizontal** setup card: Row 1 = Series · Horizon (inline) · History window · Analyze Backtest; Row 2 = model family cards wrapped horizontally + live selected-count.
- **Full-width** chart, then **Data notes**, then compact backtest/no-intervals note.
- Compact footer governance line.

## 8. Exploratory explanation status
DONE — "How to use this viewer" collapsible (open by default): exploratory, actuals
already known, model lines are historical backtests, visually compare fit / corroborate
governed results, does not generate forecasts/metrics/champion, forward forecast on the
Forecast page. Plus the governed-artifact source note.

## 9. Horizontal setup layout status
DONE — `.fvb-controls` flex row (series / horizon / history / Analyze) over `.fvb-models`
wrapped family cards. The old `.fv-setup-panel` vertical step column is gone.

## 10. Model selector status
DONE — `fvp_model_groups` retained (server unchanged) but `.fvp-model-grid` now wraps
the 4 family cards horizontally (Growth baseline / Statistical / Machine learning /
Lightweight neural). Champion ★ and high-risk ⚠ markers kept; live selected-count kept.

## 11. Chart / data notes status
DONE — chart full-width in a static `fv-chart-wrap` (blank-chart-safe). Data notes show
series, models selected, horizon, actual points, forecast points drawn, and date range.

## 12. Action-gated behavior status
PRESERVED — `fvp_request <- eventReactive(input$fvp_go, …)`; `fvp_chart` and `fvp_notes`
return empty states while `input$fvp_go == 0`; changing selectors does not auto-render;
chart container stays in the DOM.

## 13. Confirmation forward forecast is not in Viewer
CONFIRMED — no `fvf_*` outputs, no "Forward Forecast", no `forecasts.csv` in the Viewer.

## 14. Confirmation no data/governed artifacts were modified
CONFIRMED — only UI/server/CSS files changed; no writes to `data/` or governed outputs.

## 15. Confirmation no models / forecasts / tournaments were run
CONFIRMED — UI/CSS/text only.

## 16. Confirmation no metrics were recomputed
CONFIRMED — read-only viewer; no MASE/RMSSE/metric computation.

## 17. Confirmation champion decision was not changed
CONFIRMED — ETS Explicit (selected champion under conditions) unchanged.

## 18. Validation summary
- Parse: tabs.R / server.R / body.R all PARSE_OK.
- Isolated render smoke: **19/19 TRUE** (title, subtitle, how-to-use, source note,
  reads viewer csv, no forecasts.csv, all 4 selectors, Analyze Backtest, no "Analyze
  Forecast", horizontal controls, setup card, data notes, static chart, footer, no
  forward forecast, old vertical panel removed).
- Live: HTTP 200, LEN 198237, stderr clean.

## 19. App launch details
- URL: http://127.0.0.1:3839 · PID 33852 · port 3839 (3838 was busy → launcher fell back to 3839).
- Logs: `outputs/shiny_mvp/7_V2_FORECAST_VIEWER_EXPLORATORY_LAYOUT_CLEANUP/logs/viewer_exploratory_stdout.log` (+ `_stderr.log`).
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 33852`.

## 20. What Oscar should review
- Does the setup now read horizontally (one control row + wrapped model cards) instead of a tall left column?
- Is "How to use this viewer" clear that this is exploratory and separate from the Forecast page?
- After clicking **Analyze Backtest**, do the full-width chart and data notes read well?
- Confirm the Viewer shows only actuals + historical model backtests (no future forecast).

## 21. Total execution time
~10 minutes of agent work (single edit/launch pass, no relaunch loop).
