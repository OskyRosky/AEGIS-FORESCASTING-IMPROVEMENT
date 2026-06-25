# Stage 07 — Block 7.11 | Forecast Viewer (FORECASTING / Viewer)

## General summary
The FORECASTING → Viewer page (previously a placeholder "Forecast Explorer") is now a
real, read-only governed page that visually compares **actual values** against
**model forecasts** for any of the 45 governed series. It is built entirely on existing
governed artifacts — no forecasts, metrics, or models are generated or recomputed.

## Data sources (read-only governed artifacts)
- `data/processed/forecasts.csv` — 65,095 rows. Columns: entity_key, date, forecast_value,
  model_version, forecast_version, scenario, resource, value_type, source_file.
- `data/processed/actuals.csv` — 84,537 rows. Columns: entity_key, date, actual_value,
  forecast_version, scenario, resource, source_file.
- `data/processed/entities.csv` — 45 rows (entity inventory, per-entity model_count).
- `forecast_comparison.csv` is **empty** (0 rows) and is intentionally NOT used.

## Governed facts honored
- 45 series; **each series maps to exactly one model_version** (16 distinct models total).
  The Model selector is therefore reactive to the selected series.
- Clean history/forecast split: actuals end 2026-04-27, forecasts start 2026-04-28.

## Controls
1. **Series / entity** — `fv_entity`, 45 entities from forecasts.entity_key.
2. **Model** — `fv_model`, reactive to entity (single model_version per series).
3. **Forecast horizon (days)** — `fv_horizon`, 5/10/15/20/25/30/45/60 (default 30).
4. **History window** — `fv_history`, Last 30/60/90/180 days + All history (default 90).

## Chart
- highcharter (0.9.5) datetime line chart.
- Actual line (blue #2e75b6) from actuals.actual_value.
- Forecast line (amber #d97706, dashed) from forecasts.forecast_value.
- Dashed vertical "Forecast start" marker at the first forecast date.
- Empty/invalid selections render a calm no-series chart (no errors).
- `suspendWhenHidden=FALSE` + a resize dispatch on nav so the chart fills width when shown.

## Validation
- HTTP 200, rendered length 77,696 bytes.
- 14/14 HTML content checks PASS; 24/24 validation rows PASS.
- Home / Overview / Universe / TTL pages unchanged (no regressions).
- No forbidden language (winner / absolute best / unconditional champion / the best model).

## Recommendation
READY_FOR_OSCAR_VISUAL_REVIEW_7_11_FORECAST_VIEWER
