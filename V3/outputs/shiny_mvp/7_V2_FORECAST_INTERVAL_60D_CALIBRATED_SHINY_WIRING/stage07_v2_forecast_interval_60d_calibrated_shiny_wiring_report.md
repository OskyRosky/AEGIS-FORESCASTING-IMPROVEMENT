# Stage 07 — V2 Forecast 60-Day Calibrated Interval Shiny Wiring Report

## Objective
Update Forecasting → Forecast so Shiny reads the new backtest-calibrated 60-day
interval artifact and visualizes only the 80% prediction interval through
forecast day 60. After day 60 the forecast continues as a point estimate only.
The app remains strictly read-only: it never computes, recalibrates, inflates or
generates intervals/residuals/quantiles, and never alters `forecast_value`.

## Primary governed artifact
`data/processed/forecasts_with_intervals_relative_60d_calibrated.csv`
(forecasts.csv columns + governed 80% prediction-interval columns, calibrated for
forecast days 1–60; 80% only, no 95% columns).

## Files modified
- `shiny_app/R/data_loader.R` — registered new optional key
  `forecasts_with_intervals_60d_calibrated` → calibrated 60d artifact path.
- `shiny_app/R/helpers.R` — `fvf_forecasts()` now PREFERS the calibrated 60d
  artifact and detects intervals using only the 80% columns; falls back to
  `forecasts.csv` (point only) if the calibrated artifact is missing/empty (never
  silently to the older 30d interval artifact). `fvf_summary()` now reports
  `iv_horizon = 1–60 days`, holdout coverage (80%) and calibration method.
  `fvf_chart()` interval comment updated (day 30 → day 60).
- `shiny_app/server/server.R` — `output$fvf_notes` data-notes grid now shows
  forecast artifact, interval shown, method, calibrated horizon (1–60), holdout
  coverage, calibration method, grain and sample size; the longer-window note
  fires when window > 60; the 95%-not-shown wording and missing-artifact fallback
  wording were updated.
- `shiny_app/ui/tabs.R` — setup note replaced with the exact calibrated-60d
  wording; "How to use" dashed-line bullet and footer method-note updated to the
  calibrated artifact (with point-only fallback) and to state Shiny only
  visualizes governed interval columns.

## Interval-detection change
The calibrated artifact has NO 95% columns, so `fvf_forecasts()` now treats the
presence of `forecast_lower_80` + `forecast_upper_80` as the interval signal
(previously required 95% columns). The chart already drew only 80% lines, and the
per-row `interval_available` flag makes the 80% lines stop naturally at day 60.

## Smoke verification (series APC-Dedicated)
- Source = `forecasts_with_intervals_relative_60d_calibrated.csv`, HAS_IV = TRUE.
- Next 30: 80% lines through day ~30. Next 60: 80% lines through day 60.
- Next 180: forecast mean to day 180, 80% lines only through day 60 (iv_rows=60).
- All 95% columns NA; chart series = Actual history | Forward forecast | Upper 80%
  | Lower 80% (no 95% series, no arearange/ribbon).
- Summary: calibrated horizon 1–60 days, holdout coverage (80%) 0.7979,
  calibration method global_inflation, grain entity_key_x_horizon_bucket,
  sample 987, levels 80%.

## Guardrails confirmed
- No data artifacts modified (forecasts.csv and the calibrated artifact are
  read-only).
- No models/forecasts/tournaments run; no metrics recalculated.
- Champion decision unchanged; Viewer/Accuracy/TTL/Models/Governance/Reference
  untouched.
- Shiny only reads interval columns; it performs no interval math.

## Launch
Single clean instance: PID 20096 on http://127.0.0.1:3838 — HTTP 200.

## Status
READY_FOR_OSCAR_VISUAL_REVIEW_V2_FORECAST_60D_CALIBRATED_INTERVALS
