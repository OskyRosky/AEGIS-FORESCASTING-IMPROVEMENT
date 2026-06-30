# Forecast Viewer — Future Artifact Creation Plan

> **STATUS: PLAN ONLY. The artifact is NOT created in this block.**
> No forecasts generated, no models run, no metrics recomputed, no synthetic data.
> This describes exactly how a *future* block should build the consolidated artifact
> by **curating existing Stage 5 outputs only**.

## Target artifact

`forecast_viewer_model_outputs` — one long-format, tidy, multi-model forecast table for Shiny.

## Source files to join (all existing, read-only)

| Role | File | Provides |
|---|---|---|
| Baseline forecasts | `outputs/model_lab/full_baseline/full_baseline_forecasts.csv` | 7 baseline models × 39 series (forecast only) |
| Challenger forecasts + actuals | `outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv` | 6 challenger models × 39 series (forecast + actual + error) |
| Actuals (full) | `data/processed/actuals.csv` | Actuals for all 45 series (to attach actuals to baseline rows) |
| Model metadata | `outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv` | origin, family, champion, deferred, risk flags |
| Series catalog | `data/processed/entities.csv` | series_key list + labels |
| Final production forecast (optional) | `data/processed/forecasts.csv` | the single chosen forward model per series |

## Join keys

- Forecast rows ↔ model metadata: `model_name`.
- Baseline forecast rows ↔ actuals: `entity_key` + `forecast_date` (= `date` in actuals).
- All rows ↔ series catalog: `entity_key` (→ `series_key`).

## Row construction rules

1. **Challenger rows** (`challenger_actual_forecast_join.csv`): already carry `actual_value` and
   `forecast_value` — map directly. `model_origin = challenger`, `forecast_type = backtest`.
2. **Baseline forecast-only rows** (`full_baseline_forecasts.csv`): carry `forecast_value` only; attach
   `actual_value` by left-joining `actuals.csv` on `entity_key` + date. `model_origin = baseline`,
   `forecast_type = backtest`.
3. **Model family metadata**: left-join `model_lab_final_model_universe.csv` on `model_name` to populate
   `model_family`, `model_origin`, `is_selected_champion`, `risk_status`.
4. **Deferred models** (NBEATS, NHITS): include as **metadata-only** rows in a companion model-catalog,
   `is_deferred = TRUE`, with **no forecast rows** (do NOT fabricate forecasts).
5. **Final production forecast** (optional second `forecast_type = final_production` layer): may be unioned
   from `forecasts.csv` so the Viewer can also show the chosen forward model. Keep clearly separated by
   `forecast_type`.
6. **Prediction intervals**: leave `lower_bound`, `upper_bound`, `interval_level` as `NA` (not available).

## Validation steps the future block must run

- **Row-count reconciliation**: output baseline rows == input baseline rows (95,340); output challenger
  rows == input challenger rows (81,720); no row inflation from the actuals join (1:1 on key).
- **No synthetic forecasts**: every `forecast_value` traces to a source row (`source_artifact` populated);
  zero generated values.
- **No model recomputation**: pipeline performs joins/relabeling only — assert no model/inference call.
- **Series coverage**: 39 series multi-model + 6 series final-only = 45 accounted for.
- **Model coverage**: 13 models present for the 39 multi-model series (7 baseline + 6 challenger);
  NBEATS/NHITS absent from forecast rows.
- **Champion flag**: exactly one `is_selected_champion = TRUE` model (ETS Explicit).
- **Date range**: backtest rows within 2025-05-03 → 2026-04-27.

## Explicit non-goals

- No forecasting, no fitting, no tuning, no metric recompute, no tournament re-run, no champion change,
  no package install, no synthetic rows, no edits to any source artifact.
