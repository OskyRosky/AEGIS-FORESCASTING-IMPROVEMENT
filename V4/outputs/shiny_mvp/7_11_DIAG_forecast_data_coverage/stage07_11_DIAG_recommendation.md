# Stage 07 · Block 7.11-DIAG — Recommendation

## Recommendation code

**`READY_TO_FIX_FORECAST_VIEWER_WITH_EXISTING_MULTIMODEL_ARTIFACT`**
(with caveats: backtest window only · 39/45 entities · no deep learning)

## Why

The multi-model forecast data Oscar expects **already exists** in the Model Lab:
- `outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv` — 6 challenger models + actuals.
- `outputs/model_lab/full_baseline/full_baseline_forecasts.csv` — 7 baseline models.
- Together: **13 models × 39 entities**, families statistical / ML / growth / lightweight-neural.

The current Viewer only shows one model per series because it is bound to the **final single-model**
artifact `data/processed/forecasts.csv`, which is a different (production) deliverable.

No model run, no forecast generation, and no metric recompute is needed to deliver a multi-model
Viewer — only a **data-binding change** plus an honest framing of the backtest nature.

## Recommended path (NOT implemented in this block)

**Option A — Final-forecast Viewer (smallest change).**
Keep the current `forecasts.csv` binding; fix the REV1 blank-chart regression (render the highchart
in a static container, not inside the button-gated dynamic `renderUI`). Honestly labels it as the
single chosen production forecast per series. Does **not** satisfy Oscar's multi-model expectation.

**Option B — Multi-model backtest Viewer (matches Oscar's expectation).** *(recommended)*
Build a consolidated read-only artifact, e.g. `forecast_viewer_model_outputs.csv`, by unioning the
baseline + challenger backtest forecasts and joining the model family/origin from
`model_lab_final_model_universe.csv`. Then re-point the Viewer at it so selecting a series shows
**all available models** for that series, overlaid against actuals, with a clear "backtest window /
39 of 45 entities / no deep learning" disclaimer.

## Required consolidated schema (for Option B)

See `stage07_11_DIAG_required_forecast_viewer_schema.csv`. Columns:
`entity_key, entity_label, model_name, model_origin, model_family, forecast_date, target_date,
actual_value, forecast_value, horizon_days, run_id, source_artifact`.

## Decision needed from Oscar

1. **Option A** (fix single-model Viewer now), **or**
2. **Option B** (prepare the consolidated multi-model artifact, then re-bind the Viewer), **or**
3. Show the section as a **data-readiness state** until the consolidated artifact is approved.

This block performs **no** implementation — it only establishes that Option B is feasible with
existing data.
