# Stage 07 - Block 7.11-FULL-REBIND Validation Report

Generated: 2026-06-19 09:10:13

Forecast Viewer full rebind to the Stage 05H full artifact. Two clearly separated
sections: **Backtest Comparison** (multi-model historical) and **Forward Forecast**
(single production model into the future). Read-only; no models run, no artifacts
modified.

## Check summary

- pass: 28
- warning: 0
- fail: 0

## Backtest Comparison (Section 1)

- Source: `data/processed/forecast_viewer_model_outputs.csv`
- Series exposed: **39**
- Models exposed: **13** across 4 families (growth_baseline, lightweight_neural, machine_learning, statistical)
- Horizons in artifact: 1-30 days
- Horizon choices exposed: 5, 10, 15, 20, 25, 30 (35 / 45 shown disabled)
- forecast_type: backtest
- Date range: 2025-05-03 -> 2026-04-27
- Selected champion: ETS Explicit
- High-risk models: ETS Explicit, FastNeuralAR_MLP, FixedGrowth_6

## Forward Forecast (Section 2)

- Source: `data/processed/forecasts.csv` (+ `actuals.csv` for history)
- Series exposed (union): **45**
- Model versions: ARIMA, ExponentialSmoothing, ExponentialSmoothing_ARIMA_Ensemble, FixedGrowth1%, FixedGrowth2%, FixedGrowth2%_ARIMA_Ensemble, FixedGrowth2%_FixedGrowth1%_Ensemble, FixedGrowth3%, FixedGrowth3%_ARIMA_Ensemble, FixedGrowth3%_ExponentialSmoothing_Ensemble, FixedGrowth3%_FixedGrowth1%_Ensemble, FixedGrowth4%_ARIMA_Ensemble, FixedGrowth4%_ExponentialSmoothing_Ensemble, FixedGrowth5%, FixedGrowth5%_ARIMA_Ensemble, FixedGrowth5%_ExponentialSmoothing_Ensemble
- value_type: Forecast-Mean
- Forecast date range: 2026-04-28 -> 2030-04-25
- Actual date range: 2019-07-01 -> 2026-04-27
- All backtest series are a subset of forward series: True

## Live render verification

- Backtest chart drew an actual line plus multiple model forecast lines after
  clicking **Analyze Backtest** (gated; empty before click).
- Forward chart drew an actual-history line, a forward-forecast line, and a vertical
  **Forecast start** boundary at the actual/forecast transition after clicking
  **Analyze Forward Forecast** (gated; empty before click).

## Artifacts written by this block

- `stage07_11_FULL_REBIND_report.md`
- `stage07_11_FULL_REBIND_validation.csv`
- `stage07_11_FULL_REBIND_ui_data_contract.csv`
- `stage07_11_FULL_REBIND_chart_readiness.csv`
- `stage07_11_FULL_REBIND_series_summary.csv`

No `data/processed` artifact was modified. No Stage 05 / Stage 06 output was modified.
