# Stage 07 — V2 Forecast Viewer Final Layout Refinement

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_FORECAST_VIEWER_FINAL_LAYOUT_REFINEMENT
**Page:** Forecasting > Viewer (`section_explorer`) — V2 only
**App:** http://127.0.0.1:3838 · PID 6028 · HTTP 200 · LEN 199345

## General summary
Refined the Viewer into a clean two-box layout that matches Oscar's intended
structure: a collapsed-by-default guidance block, a dedicated **Set up the backtest
view** box with numbered steps 1–5 (Analyze Backtest is the last step at the bottom),
and a **separate Backtest Comparison** results box (collapsible, open by default) that
holds the large chart and the data notes together. All read-only/action-gated behavior
and governance guardrails are preserved.

## Files created
- `outputs/shiny_mvp/7_V2_FORECAST_VIEWER_FINAL_LAYOUT_REFINEMENT/stage07_v2_forecast_viewer_final_layout_refinement_report.md`
- `..._validation.csv`
- `..._launch.csv`

## Files modified
- `shiny_app/ui/tabs.R` — `section_explorer()` restructured into two separate boxes; "How to use" collapsed by default; steps numbered 1–5; Analyze Backtest moved to bottom; chart + notes moved into the "Backtest Comparison" collapsible.
- `shiny_app/www/custom.css` — added `.fvb-step-num` badge, `.fvb-analyze-row`/`.fvb-analyze-btn`/`.fvb-analyze-hint`, made `.fvb-field-label` inline-flex (+ dark variant).
- `shiny_app/ui/body.R` — CSS cache-bust `?v=20260624h` → `?v=20260624i`.

## Viewer layout before
- "How to use this viewer" expanded by default.
- A single box held both the setup controls AND the chart/notes; the Analyze button sat in the top control row.

## Viewer layout after
- **A. Title + subtitle.**
- **B.** "How to use this viewer" — **collapsed by default**.
- **C. Box 1 — Set up the backtest view** (controls only): Row 1 = ①Select key/series · ②Horizon · ③History window; Row 2 = ④Models (family cards); Row 3 = ⑤**Analyze Backtest** button at the bottom.
- **D. Box 2 — Backtest Comparison** (results only, collapsible/expandable, open by default): empty state until Analyze, then the large 600px chart with **Data notes directly below it in the same box**.
- **E.** Footer governance note retained.

## How to use viewer collapse status
DONE — `home_collapse(..., open = FALSE)`; the block renders collapsed (no `is-open`).

## Setup box status
DONE — Box 1 is its own `.fvx-section.fvb-setup-section` card; controls only, no chart inside.

## Numbered controls status
DONE — five `.fvb-step-num` badges: 1 Select key/series, 2 Horizon, 3 History window, 4 Models, 5 Analyze Backtest.

## Analyze Backtest placement status
DONE — in `.fvb-analyze-row` after the model selector; verified ordering models < analyze < results.

## Backtest Comparison results box status
DONE — Box 2 is a separate `home_collapse("Backtest Comparison", …, open = TRUE)` below the setup box, with collapsible header.

## Chart / data notes status
DONE — chart (600px, full width) and data notes live together inside Box 2's `.fvb-result`. Data notes only after Analyze.

## Action-gated behavior status
PRESERVED — `eventReactive(input$fvp_go)`; `fvp_chart`/`fvp_notes` show empty states until clicked; selectors do not auto-render; chart container stable (`suspendWhenHidden=FALSE`).

## Guardrails honored
V2 only; V1 untouched. No data/governed-artifact writes. No models/forecasts/tournaments
run. No metric recompute (MASE/RMSSE). Champion (ETS Explicit under conditions) unchanged.
Forward Forecast not in Viewer. Viewer reads `forecast_viewer_model_outputs.csv` only (not
`forecasts.csv`). No Scenario dropdown added.

## Validation summary
- Parse: tabs.R / server.R / body.R → PARSE_ALL_OK.
- Isolated render smoke: **23/23 TRUE** + ordering check TRUE.
- Live: HTTP 200, LEN 199345, stderr clean, single instance on 3838.

## App launch details
- URL http://127.0.0.1:3838 · PID 6028.
- Logs: `outputs/shiny_mvp/7_V2_FORECAST_VIEWER_FINAL_LAYOUT_REFINEMENT/logs/viewer_final_refinement_stdout.log` (+ `_stderr.log`).
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 6028`.

## What Oscar should review
Open http://127.0.0.1:3838 (Ctrl+F5 to refresh CSS): confirm "How to use" is collapsed,
the numbered setup box (1–5 with Analyze at the bottom), the separate Backtest Comparison
box below with the large chart, and Data notes appearing under the chart after Analyze.
