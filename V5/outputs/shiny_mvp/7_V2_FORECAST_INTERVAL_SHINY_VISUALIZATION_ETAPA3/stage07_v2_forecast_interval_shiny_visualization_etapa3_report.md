# Stage 07 · V2 Forecast Interval — Shiny Visualization (Etapa 3)

**Status:** READY_FOR_OSCAR_VISUAL_REVIEW_V2_FORECAST_INTERVAL_SHINY_VISUALIZATION
**Active root:** V2 only (V1 frozen, never touched)
**Golden rule honored:** Shiny never cooks. It only *reads and draws* governed interval columns.

---

## 1. General Summary

Etapa 3 wires the **governed prediction-interval artifact** into the Shiny
**Forecasting → Forecast** page. The Forecast Chart now draws the **80%** and
**95%** prediction-interval bounds as **dashed / dotted lines** (no shaded
bands), layered on top of the existing actual-history and forward forecast-mean
series. All interval values are read directly from
`data/processed/forecasts_with_intervals_relative.csv`; nothing is computed in
the app. Interval lines only appear for rows where `interval_available = TRUE`
and the bound columns are not `NA`, which naturally limits them to the first
**30 forecast days**. For 90/180-day / full windows, the point forecast
continues past day 30 while the interval lines stop. The page also explains the
intervals through a compact setup note and an expanded data-notes panel
(method, source, levels, calibrated horizon, grain, sample size, and a point
scale-anomaly flag).

## 2. Files Created

- `outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_SHINY_VISUALIZATION_ETAPA3/stage07_v2_forecast_interval_shiny_visualization_etapa3_report.md` (this report)
- `..._validation.csv` — 32 governance/behavior checks (all PASS)
- `..._launch.csv` — app launch + HTTP-200 evidence and stop command
- `..._visual_checks.csv` — 15-item visual checklist for Oscar's review
- `outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_SHINY_VISUALIZATION_ETAPA3/logs/etapa3_intervals_stdout.log`, `..._stderr.log` (runtime logs)

## 3. Files Modified

All under `V2/shiny_app/` (Forecast page only):

- `R/data_loader.R` — registered governed artifact `forecasts_with_intervals` →
  `data/processed/forecasts_with_intervals_relative.csv` (optional).
- `R/helpers.R` — `fvf_forecasts()` (prefer interval artifact + safe fallback),
  `fvf_forecast_series()` (carry NA-safe interval columns + horizon_day),
  `fvf_chart()` (add 4 interval lines, no arearange),
  `fvf_summary()` (surface interval metadata + anomaly).
- `server/server.R` — `output$fvf_notes` now shows interval metadata, the
  anomaly flag, the fallback note, and the 30-day note.
- `ui/tabs.R` — added the governed setup note in the Forecast setup box.
- `www/custom.css` — `.fvb-setup-note` style (+ dark theme).
- `ui/body.R` — CSS cache-buster bumped `v=20260624k` → `v=20260624l`.

## 4. Forecast Data Source Update

- The Forecast page now reads `forecasts_with_intervals_relative.csv` first.
  Confirmed at runtime: `attr(fvf_forecasts(), "fvf_source")` =
  `forecasts_with_intervals_relative.csv`, `fvf_has_intervals` = `TRUE`,
  all four bound columns present.
- **Safe fallback:** if the interval artifact is missing/empty or lacks the four
  bound columns, `fvf_forecasts()` falls back to `forecasts.csv` and sets
  `fvf_has_intervals = FALSE` so the page degrades to a clean point-only view.
- `actuals.csv` is still read unchanged for the actual-history line.

## 5. Interval Visualization Design

- **Lines, not bands.** Four explicit line series are drawn — no `arearange`,
  no shaded ribbon.
  - Upper/Lower **80%**: dashed (`Dash`), amber `#d97706`, lineWidth 1.5.
  - Upper/Lower **95%**: dotted (`Dot`), red `#b91c1c`, lineWidth 1.5.
- Markers disabled; each bound is only drawn for rows where
  `interval_available = TRUE` and the value is not `NA`.
- Layering: solid actual history → dashed forecast mean → 80% dashed → 95%
  dotted → forecast-start vertical boundary.

## 6. 80% Interval Lines Status

PASS. `Lower 80%` and `Upper 80%` dashed amber lines render across the first 30
forecast days (drawable count = 30 for the validated keys). These are the tight,
default-honest band (holdout coverage ≈ 0.809).

## 7. 95% Interval Lines Status

PASS. `Lower 95%` and `Upper 95%` dotted red lines render across the same first
30 forecast days (drawable count = 30). Wider than the 80% lines, consistent
with the governed relative-residual calibration (holdout coverage ≈ 0.922). Both
80% **and** 95% appear together, as requested.

## 8. No Shaded Band Confirmation

PASS. `fvf_chart()` contains **no** `arearange` / filled-ribbon series. Intervals
are communicated exclusively through dashed/dotted boundary lines.

## 9. Forecast Window Behavior

- **30-day window:** 31 rows, 30 drawable interval rows; the last interval is at
  horizon day 30, and there are no interval values afterward.
- **90-day window:** 91 rows, but still only 30 drawable interval rows. The
  forecast mean continues for the full window while interval lines stop after
  day 30 (validated: bounds are `NA` after the last interval row).
- **180-day / full window:** same behavior — point forecast for the full window,
  interval lines only through day 30.

## 10. Setup Note Status

PASS. The Forecast setup box now shows the governed note:
*"Prediction intervals are backtest-calibrated and currently available for the
first 30 forecast days only. Longer windows continue as point forecast after day
30. Shiny only visualizes interval columns from the governed forecast artifact."*
The "Full forecast window" option was **not** removed.

## 11. Data Notes Status

PASS. When intervals are available, the data-notes panel adds a metadata grid:
Interval method (`empirical_backtest_relative_residual_quantile`), Interval
source (`forecast_viewer_model_outputs.csv`), Interval levels shown (`80%, 95%`),
Calibrated horizon (`1–30 days`), Calibration grain
(`entity_key_x_horizon_bucket`), Calibration sample size (e.g. `1040`). The
source line reflects `forecasts_with_intervals_relative.csv + actuals.csv`. For
90/180/full windows it adds: *"Prediction intervals are shown only through
forecast day 30; later forecast days are point forecast only."* When a series has
no interval rows it shows: *"Prediction interval columns are not available for
the selected rows; point forecast is shown only."*

## 12. Action-Gated Behavior Status

PASS. The chart and notes still render only after **Run** (step 4). The existing
`eventReactive(input$fvf_go, …)` gating and `req(...)` guards are preserved.

## 13. Fallback Behavior Status

PASS. Two layers of fallback: (a) artifact-level — `fvf_forecasts()` reverts to
`forecasts.csv` if the interval artifact is missing/empty; (b) row-level — keys
or rows without interval values render as point-only with an explanatory note.
Both branches are present and validated.

## 14. Confirmation Shiny Does Not Calculate Intervals

CONFIRMED. The Forecast page contains no `quantile()`, residual, standard-error,
`qnorm`, or band-width computation. Every bound is read straight from the
governed columns `forecast_lower_80/upper_80/lower_95/upper_95`. No interval,
residual, or quantile math runs in the dashboard.

## 15. Confirmation No Data Artifacts Were Modified

CONFIRMED. All file access in this stage is read-only. `forecasts.csv`,
`forecasts_with_intervals_relative.csv`, and `actuals.csv` are unchanged; no CSV
was written or overwritten by the app.

## 16. Confirmation No Models / Forecasts Were Run

CONFIRMED. No model training, scoring, backtesting, or forecasting was executed.
This stage is purely a visualization wiring of an existing governed artifact.

## 17. Confirmation Champion Decision Was Not Changed

CONFIRMED. No governance, champion, tournament, or ranking artifact was touched.
The selected production model per series is unchanged.

## 18. Validation Summary

- 32 automated checks — **all PASS** (`..._validation.csv`).
- All five modified R files parse cleanly (`parse()` OK).
- `server/server.R` reports no compile errors; the helper warnings are
  pre-existing static-lint noise (`div`, `p`, `tags`, `load_csv_artifact`
  resolved at runtime by Shiny/the loader) present across the whole file and not
  introduced here.
- Headless data-flow check confirmed: source attribute, interval columns,
  drawable counts (30 for both 30- and 90-day windows), `fvf_summary` metadata,
  point-anomaly flag for `APC-Dedicated`, and `fvf_chart()` building without
  error.

## 19. App Launch Details

- URL: `http://127.0.0.1:3839` — **HTTP 200** (port 3838 was busy; launcher
  auto-selected 3839).
- PID: `39380`.
- Logs: `outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_SHINY_VISUALIZATION_ETAPA3/logs/etapa3_intervals_stdout.log` / `..._stderr.log`.
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny.ps1 -PidToStop 39380`.

## 20. What Oscar Should Review

Open **Forecasting → Forecast**, pick a series (e.g. `APC-Dedicated`), choose a
90-day window, press **Run**, and check:
1. Solid actual history, dashed forecast mean, dashed **80%** lines, dotted
   **95%** lines, vertical forecast-start boundary.
2. Interval lines stop at day 30; the mean continues to day 90.
3. The green setup note and the data-notes interval metadata read correctly.
4. For `APC-Dedicated`, the amber **Point anomaly** note appears (the production
   point itself is scale-anomalous; the interval is proportional to it).
See `..._visual_checks.csv` for the full 15-item checklist.

## 21. Total Execution Time

Approximately 9 minutes of agent work in this stage (edits, syntax/parse checks,
headless data-flow validation, launch + HTTP-200 verification, and artifact
writing).

---

Please visually review Forecasting > Forecast and confirm whether the forecast mean, 80% interval lines, 95% interval lines, and 30-day interval note match the intended design.
