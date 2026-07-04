# Stage 07 · Block 7.11-PILOT-REBIND — Forecast Viewer Pilot Rebind Report

**Block:** Stage 07 — Block 7.11-PILOT-REBIND — Forecast Viewer Pilot Rebind to Stage 05H Multi-Model Artifact
**Active root:** `V1`
**Recommendation:** `READY_FOR_OSCAR_VISUAL_REVIEW_7_11_PILOT_REBIND`

---

## 1. Objective

Rebind the Shiny Forecast Viewer to the Stage 05H pilot multi-model artifact
`data/processed/forecast_viewer_model_outputs_pilot.csv` and deliver a guided
workflow: pick one series → tick multiple models grouped by family → choose a
horizon (5/10/15/20/25/30 only) → choose a history window → click **Analyze
Forecast** → see one actual line plus one line per selected model, with data
notes and governance warnings. Fix the blank-chart regression by making the
chart container static.

## 2. Data source

- Governed loader key: `forecast_viewer_pilot` →
  `data/processed/forecast_viewer_model_outputs_pilot.csv` (14,040 rows, 21 cols).
- Optional informational key: `forecast_viewer_pilot_manifest`.
- The pilot viewer does **not** read `forecasts.csv` or `forecast_comparison.csv`.

## 3. What was built (read-only consumption)

- New `fvp_*` accessor/chart family appended to `shiny_app/R/helpers.R`:
  `fvp_data`, `fvp_series_choices`, `fvp_model_meta`, `fvp_models_for_series`,
  `fvp_horizon_choices` (5–30 only), `fvp_default_models`, `fvp_actual_series`,
  `fvp_forecast_series`, `fvp_empty_chart`, `fvp_chart` (multi-line), `fvp_summary`.
- `shiny_app/ui/tabs.R` `section_explorer()` rebuilt as a guided, sectioned
  workflow with a **static** `highchartOutput("fvp_chart")` always in the DOM.
- `shiny_app/server/server.R` rebuilt: series-reactive grouped checkboxes,
  Analyze-gated static chart, data-notes snapshot.
- `shiny_app/www/custom.css`: added `.fvp-*` and warning-card styles (light + dark).
- `shiny_app/R/data_loader.R`: registered the two pilot artifact keys.

## 4. Blank-chart regression fix

Root cause: the chart `highchartOutput` previously lived inside a
button-gated `uiOutput("fv_view")`, so the container was created late and
initialised at zero width → blank chart. Fix: the chart container is now
declared statically in `section_explorer()` and is present from page load;
the Analyze button controls the **data** rendered, not the container. Measured
container width after render = 641px (non-zero). `suspendWhenHidden = FALSE`
keeps it ready under the custom section-based navigation.

## 5. Validation

- `stage07_11_PILOT_REBIND_validation.csv` — 41 checks, all `pass`.
- `stage07_11_PILOT_REBIND_ui_data_contract.csv` — control → artifact column map.
- `stage07_11_PILOT_REBIND_chart_readiness.csv` — chart render diagnostics.

Live verification (Playwright against the running app):
- 3 series only; horizons 5–30 only (45/60 absent).
- 4 family groups; defaults pre-ticked; champion/high-risk badges shown.
- Empty state before Analyze; chart draws 1 Actual + N model lines after Analyze.
- All series `visible:true` on fresh render; horizon switch re-renders.

## 6. App launch

- URL: http://127.0.0.1:3839
- Process id: 37864 (listening on port 3839)
- HTTP: 200
- Logs: `outputs/shiny_mvp/7_11_PILOT_REBIND_forecast_viewer/pilot_rebind_stdout.log` / `pilot_rebind_stderr.log`
- Stop: `powershell -ExecutionPolicy Bypass -File scripts\stop_shiny_v1.ps1 -PidToStop 37864`

## 7. Known limitations

- Horizons capped at 30 days (the pilot artifact does not contain 45/60).
- Lines are a historical **backtest** model comparison, not a forward production forecast.
- No prediction intervals (NA in the pilot artifact); point forecasts only.
- Pilot scope is 3 series / 13 models (NBEATS/NHITS deferred, not present).

## 8. Confirmations

- No Stage 05/06 artifacts modified.
- Pilot artifact read-only; not modified.
- No models run, no forecasts generated, no metrics recomputed, no tournament
  rerun, no champion changed, no full artifact created, no reshaped data persisted.
