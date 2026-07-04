# Stage 07 — V2 Forecasting > Accuracy Layout Cleanup (Round 1)

**Active root:** V2 (V1 frozen — untouched)
**Status:** READY_FOR_OSCAR_VISUAL_REVIEW
**App:** http://127.0.0.1:3838 — HTTP 200, PID 50244, single clean instance on port 3838

## Objective
Apply the approved Viewer page pattern to **Forecasting > Accuracy**. Previous Accuracy
page was too vertical and visually mixed. New structure:
collapsed explanation → summary/KPIs in a collapsible box → setup in a separate box →
results in a separate box with a large heatmap + metric table below.

## What changed
1. **Page header** — title `Accuracy` + subtitle
   *"Exploratory backtest accuracy diagnostics from the frozen model-comparison artifact.
   Use this page to see where errors are highest or most stable across keys, models and horizons."*
2. **"How to use this accuracy view"** — collapsible, **collapsed by default**.
3. **"Accuracy summary"** — collapsible box (open) holding the KPI cards
   (no longer loose at the top). KPI label *Series covered* → **Keys covered**.
4. **"Set up the accuracy view"** — separate full-width setup box with numbered controls:
   1 Select horizon · 2 Select metric · 3 Select models · 4 Filter key / series ·
   5 Rows shown · 6 **Analyze Accuracy** (button at the bottom in a dedicated row).
5. **"Heatmap"** — separate results box, **open by default**, containing the large
   standardized-severity heatmap with the metric values table directly below.
   ("Standardized" kept only as the subtitle explanation, not as the box title.)
6. **Footer** — single short governance note.

## Behavior preserved
- Action-gated: heatmap, metric table and summary stay in their empty states
  ("Click Analyze Accuracy…") until the user clicks **Analyze Accuracy** (`acc_go`).
- All input/output IDs unchanged (`acc_horizon`, `acc_metric`, `acc_models`, `acc_series`,
  `acc_topn`, `acc_go`, `acc_summary_cards`, `acc_heatmap`, `acc_table`) — server contract intact.
- Data source unchanged: `data/processed/forecast_viewer_model_outputs.csv` only.

## Safety
- No data or governed artifacts modified.
- No models, forecasts or tournaments run.
- No official MASE / RMSSE recomputation — in-memory display diagnostics only.
- Champion decision unchanged.
- Only Forecasting > Accuracy touched; Viewer / Forecast / TTL / Models / Governance / Reference untouched.

## Validation
- Parse OK for tabs.R, server.R, body.R.
- Isolated render smoke: 26/26 checks TRUE + control ordering (models < analyze < result) TRUE.
- Launch: HTTP 200, LEN 201722, PID 50244 on 3838; stderr clean.
- CSS cache version bumped `?v=20260624j` → `?v=20260624k`.

## Files modified
- `V2/shiny_app/ui/tabs.R` — `section_accuracy()` rewritten to the Viewer pattern.
- `V2/shiny_app/server/server.R` — KPI label *Series covered* → *Keys covered* (both states).
- `V2/shiny_app/ui/body.R` — CSS cache-busting version bump.
