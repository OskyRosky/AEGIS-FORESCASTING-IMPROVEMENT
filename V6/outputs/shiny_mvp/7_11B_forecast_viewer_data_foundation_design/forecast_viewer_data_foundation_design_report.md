# Forecast Viewer — Data Foundation Design Report (Block 7.11B)

**Mode:** READ-ONLY diagnosis + engineering design. No implementation. No Shiny/data/model change.
**Root:** `V1`. **Blueprint:** `docs/updated_blueprint/updated_tesseract_forecast_improvement_blueprint.md`.

---

## 1. Executive recommendation

**`CREATE_FORECAST_VIEWER_DATA_FOUNDATION_BEFORE_SHINY`**

The multi-model forecast data Oscar wants **exists** (Stage 5 Model Lab outputs), but it is **split across
two files and never consolidated** into a visualization-ready artifact. The right move is to build a
single governed consolidated artifact (curation of existing outputs — no new modeling) **before** finishing
the Shiny Forecast Viewer. The Viewer should be limited to the honest final-forecast view *only if* Oscar
decides not to build the foundation.

---

## 2. Stage ownership (Blueprint alignment)

- Multi-model forecasts are **Stage 5 (Model Lab)** outputs.
- The consolidated `forecast_viewer_model_outputs` is a **Stage 5 → Stage 7 handoff artifact** (curation
  for presentation), NOT Stage 3/4/6 work and NOT a Shiny-only bug.
- Root cause = **missing consolidation artifact** + **Shiny bound to the final single-model forecast**.
- See `forecast_viewer_blueprint_alignment.md`.

## 3. Series inventory (45 series)

- **39 of 45 series** have full multi-model backtest coverage (13 models each).
- **6 series** are final-forecast-only: AUT-Go Local, CHL-Go Local, DNK-Go Local, EUR-Go Local,
  IDN-Go Local, MYS-Go Local.
- Full table: `forecast_viewer_series_inventory.csv`.

## 4. Representative MVP series

APC-Dedicated, APC-MSIT, APC-Multitenant, ARE-Go Local, AUS-Go Local (+ BRA-Go Local) — all preferred and
all available with the full 13-model lineup. See
`forecast_viewer_representative_series_recommendation.csv`.

## 5. Model coverage by family (per representative series — identical 13-model lineup)

| Family (display) | Models |
|---|---|
| baseline_reference | FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6 |
| statistical | ARIMA_Fixed, ETS_Current, AutoARIMA, **ETS Explicit ★champion**, Theta |
| machine_learning | LinearRegression, LightGBM, XGBoost |
| neural_lightweight_high_risk | FastNeuralAR_MLP (`risk_flag = TRUE`, not champion-eligible) |
| deep_learning_deferred | NBEATS, NHITS — **deferred, no forecasts produced** |

See `forecast_viewer_model_coverage_by_series.csv`.

## 6. Forecast values vs backtest values

- `full_baseline_forecasts.csv` → **historical backtest, forecast-only** (7 baseline models).
- `challenger_actual_forecast_join.csv` → **historical backtest, forecast + actual + error** (6 challenger
  models). Also present: `challenger_scoring_forecasts.csv`, `challenger_official_forecasts.csv` (same
  shape).
- `data/processed/forecasts.csv` → **final forward production forecast**, 1 model per series.
- **Honest "today" capability:** the Viewer can show, per series, the **actual line plus up to 13 model
  backtest forecasts** over 2025-05-03 → 2026-04-27 for 39 series — clearly labeled as backtest, no
  intervals, no deep learning.

## 7. Confidence / prediction intervals

- **None available.** 0 of the forecast time-series artifacts contain forecast prediction bands.
- The 8 artifacts with interval-like column names hold **metric-level statistics** (p95 MASE/RMSSE,
  bootstrap CIs on metric deltas, score percentiles, forecast variance) — **not** per-date forecast bands.
- Interval visualization is a **future model-output extension**. See
  `forecast_viewer_interval_availability.csv`.

## 8. Artifact design options

CSV vs parquet vs partitioned vs per-file vs wide — full matrix in
`forecast_viewer_artifact_design_options.csv`. At ~177k rows: **long-format single file** wins;
**CSV for the MVP, parquet for scale/Azure**. Wide and per-file formats rejected.

## 9. Recommended canonical schema

Long, tidy: `series_key, series_label, date, actual_value, model_name, model_origin, model_family,
forecast_value, forecast_type, horizon_days, forecast_start_date, run_id, source_artifact, is_baseline,
is_challenger, is_deferred, is_selected_champion, risk_status, window_id, lower_bound, upper_bound,
interval_level`. Required/optional/future flags in `forecast_viewer_recommended_schema.csv`.

## 10. Future artifact creation plan

Join baseline + challenger + actuals + model metadata; attach actuals to baseline by `entity_key`+date;
deferred models as metadata-only; intervals NA; full validation suite. See
`forecast_viewer_artifact_creation_plan.md`. **Not executed in this block.**

## 11. Shiny consumption plan

Load once via governed loader; series → model checkboxes (by family) → horizon → history → Analyze;
highchart actual + selected models; intervals note; static chart container to fix the blank-chart
regression. See `forecast_viewer_shiny_consumption_plan.md`.

## 12. Recommended file format & location

- **Primary:** `data/processed/forecast_viewer_model_outputs.parquet`
- **Sample/diff:** `data/processed/forecast_viewer_model_outputs_sample.csv`
- **Manifest:** `data/processed/forecast_viewer_model_outputs_manifest.csv`
- For an MVP without `arrow`, CSV-only is acceptable: `forecast_viewer_model_outputs.csv` + manifest.

## 13. Governance & audit

Manifest + checksums, schema/row-count/coverage/champion/interval validations at build, no recomputation
in Shiny, documented limitations. See `forecast_viewer_governance_plan.md`.

## 14. Risks & limitations

1. Backtest-only (no forward multi-model). 2. 6 series single-model only. 3. No deep learning.
4. No prediction intervals. 5. Challenger forecasts post-date blocking AUDIT #2 → treat as evidence.

## 15. Final recommendation

Build the consolidated data foundation (Stage 5 → Stage 7 handoff, curation only) **before** continuing the
Shiny Forecast Viewer; pause the multi-model Viewer build until the artifact exists, while the final-forecast
view can proceed as an honest interim. This is a **corrective Stage 5 handoff artifact**, surfaced by Stage 7.
