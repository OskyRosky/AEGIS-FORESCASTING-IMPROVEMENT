# Stage 07 — V2 Forecast Chart Interval Simplification (80% only)

**Active root:** V2 (V1 frozen)
**Scope:** Forecasting → Forecast page only. Read-only on data, models and champion.
**Decision (Oscar, 2026-06-25):** For executive visualization, display only the 80%
prediction interval. The 95% interval is technically honest but visually clutters the
chart, so 80% becomes the operational display level. The 95% columns remain untouched
in the governed artifact.

## What changed
The Forward Forecast chart (`fvf_chart`) now draws only the **80%** prediction interval
lines (Upper 80% / Lower 80%, dashed amber). The two 95% series (Upper 95% / Lower 95%)
are no longer added to the chart, so they do not appear in the chart, legend or tooltip.
Governance notes were updated to explain the 80%-only display and to confirm the 95%
columns still exist in the artifact but are not displayed.

## Files modified
1. `V2/shiny_app/R/helpers.R`
   - `fvf_chart()` — removed the `add_iv_line("upper_95", ...)` and
     `add_iv_line("lower_95", ...)` calls; keeps only `upper_80` and `lower_80`.
     Added a governance comment.
   - `fvf_summary()` — `iv_levels` changed from `"80%, 95%"` to `"80%"`; the drawable
     interval-row counter now keys off `lower_80` instead of `lower_95` (same rows,
     consistent with the 80%-only display).
2. `V2/shiny_app/ui/tabs.R`
   - `section_forecast()` setup note expanded with the 80%-only governance paragraph
     (relative-residual calibration, heavy upper tail rationale) while keeping the
     existing 1–30 day horizon note.
3. `V2/shiny_app/server/server.R`
   - `output$fvf_notes` data-notes now show: Interval shown 80% · method · calibrated
     horizon 1–30 days · Shiny only visualizes governed interval columns · 95% columns
     remain in the artifact but are not displayed for visual clarity.

## What was NOT changed
- No interval, residual or quantile is computed in Shiny (read-only columns only).
- `forecasts_with_intervals_relative.csv` and `forecasts.csv` were not modified.
- 95% interval columns remain in the governed artifact.
- No models/tournaments/backtests were run.
- Champion decision unchanged (ETS Explicit · CHAMPION_SELECTED_WITH_CONDITIONS).
- Viewer / Accuracy / TTL / Models / Governance / Reference pages untouched.

## Forecast window behavior (unchanged except 95% removal)
- 30-day window: mean + 80% lower/upper lines.
- 60 / 90 / 180 / full window: mean across the full window; 80% lines only through
  forecast day 30; point forecast after day 30.
- No 95% lines in any window.

## Validation
All 17 checks passed. The app launches via `scripts/start_shiny.ps1` on port 3838 and
returns HTTP 200. See the companion CSVs for per-check detail.

**Final status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_FORECAST_INTERVAL_80_ONLY
