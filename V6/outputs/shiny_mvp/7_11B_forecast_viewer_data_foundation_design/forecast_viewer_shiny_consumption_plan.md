# Forecast Viewer — Shiny Consumption Plan

> Describes how Shiny should consume the **future** consolidated artifact once it exists.
> No Shiny code is changed in this block.

## Loading

- Load the consolidated artifact **once at app init** via the existing governed loader (7.0E pattern),
  same as other cached artifacts. No computation inside Shiny — read + filter only.
- Prefer parquet (via `arrow`) if available for fast columnar reads; otherwise CSV is fine at ~177k rows.

## Desired UI behavior

1. **Select series** — `selectInput` populated from `series_key` (39 multi-model series; the 6 final-only
   series are either hidden or clearly badged "single-model only").
2. **Select models** — `checkboxGroupInput` listing the models available for the chosen series, grouped by
   `display_family`:
   - baseline_reference (FixedGrowth_1_5/3/4/6)
   - statistical (ARIMA_Fixed, ETS_Current, AutoARIMA, ETS Explicit ★champion, Theta)
   - machine_learning (LinearRegression, LightGBM, XGBoost)
   - neural_lightweight_high_risk (FastNeuralAR_MLP — badge "high risk")
   - deep_learning_deferred (NBEATS, NHITS — shown disabled, "not available")
3. **Select horizon** — `selectInput` 5, 10, 15, 20, 25, 30, 45, 60 days.
4. **Select history window** — actual-history lookback control.
5. **Analyze Forecast** — `actionButton`; chart renders only after click (snapshot inputs with
   `eventReactive`).
6. **Chart** — highcharter: one **Actual** line + one line per selected model's `forecast_value` over
   `date`; champion line emphasized; high-risk model dashed/badged.
7. **Intervals** — if `lower_bound`/`upper_bound` are non-NA, draw an `arearange` uncertainty band;
   **today they are NA**, so the Viewer must show an explicit note: *"Prediction intervals not available
   for these models."*

## Honesty banners the Viewer must render

- "Showing historical backtest forecasts (2025-05-03 → 2026-04-27), not forward production forecasts."
- "Multi-model comparison available for 39 of 45 series."
- "Deep-learning models (NBEATS/NHITS) were deferred and are not available."
- "FastNeuralAR_MLP is a lightweight neural candidate flagged high-risk; not a validated champion."

## Chart regression fix (carry-over from 7.11-REV1)

Render the highchart in a **static, always-present container** (fixed-height `highchartOutput` placed
directly in the section, with `outputOptions(suspendWhenHidden = FALSE)`), **not** inside a button-gated
dynamic `renderUI`. Toggle visibility/empty-state via a reactive flag, but keep the chart node mounted so
Highcharts binds with a real width. This resolves the blank-chart issue.
