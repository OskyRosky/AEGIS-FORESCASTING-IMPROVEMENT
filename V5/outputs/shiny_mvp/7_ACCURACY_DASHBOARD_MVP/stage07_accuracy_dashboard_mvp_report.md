# Stage 07 - Accuracy Page MVP - Validation Report
Read-only validation of the heatmap-first Accuracy page. No data artifacts were modified; no models, forecasts or tournaments were run.

## Data source
- Artifact: `data/processed/forecast_viewer_model_outputs.csv`
- Rows: 177060
- Series: 39  |  Models: 13
- Horizons present: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30]
- Columns: 21

## Diagnostics computed (in memory)
- Per series x model x horizon: n_points, MAE, RMSE, sMAPE, wMAPE, signed_bias, abs_bias_severity, error_variability.
- Standardized severity = (value - median) / IQR (z-score fallback).
- MASE / RMSSE excluded: no governed scale baseline bundled with the artifact.

## Validation summary: 26 pass, 0 warning, 0 fail

| Check | Status | Details |
|---|---|---|
| accuracy_page_exists | pass | section_accuracy() is defined in ui/tabs.R |
| accuracy_not_placeholder_only | pass | Placeholder shell_card text replaced with a real heatmap + table layout |
| reads_backtest_artifact | pass | acc_data() reuses fvp_data() which reads forecast_viewer_model_outputs.csv |
| does_not_read_forecasts_csv | pass | Accuracy code never calls the forward forecast loader / forecasts.csv |
| does_not_read_actuals_csv | pass | Accuracy code never calls the actuals loader / actuals.csv |
| horizon_selector_5_to_30 | pass | acc_horizon_choices() = 5,10,15,20,25,30 and bound to radioButtons('acc_horizon') |
| heatmap_exists | pass | plotly heatmap output acc_heatmap is wired UI <-> server |
| heatmap_uses_standardized_score | pass | Heatmap z-values are the standardized severity score (winsorized for color) |
| table_exists | pass | DT table output acc_table is wired UI <-> server |
| table_includes_raw_metrics | pass | acc_table() emits raw MAE/RMSE/sMAPE/wMAPE/bias/variability columns |
| table_includes_standardized_score | pass | acc_table() includes a std_score(metric) column |
| metric_selector_exists | pass | Metric selector acc_metric bound to ACC_METRICS |
| horizon_selector_exists | pass | Horizon selector acc_horizon present |
| analyze_button_exists | pass | Analyze Accuracy action button present |
| heatmap_and_table_action_gated | pass | Heatmap, table and summary cards render an empty state until acc_go is clicked |
| no_writes_to_processed_data | pass | Accuracy helpers contain no write/persist calls to data/processed |
| no_model_run | pass | No model fitting/forecast generation in the Accuracy code path |
| no_tournament_rerun | pass | No tournament logic invoked by the Accuracy page |
| no_champion_change | pass | Accuracy never reads/writes champion selection flags |
| viewer_page_exists | pass | Viewer (Backtest) page still present |
| forecast_page_exists | pass | Forecast (Forward) page still present |
| forward_forecast_outside_viewer | pass | Forward Forecast (fvf_chart) is not inside the Viewer page body |
| ttl_page_exists | pass | TTL page still present |
| outputs_eager_render | pass | Accuracy outputs set suspendWhenHidden = FALSE (hidden panel renders eagerly) |
| accuracy_css_present | pass | Accuracy summary-card CSS appended to custom.css |
| mase_rmsse_excluded_documented | pass | MASE/RMSSE excluded with documented rationale (no governed scale baseline) |

## Guarantees
- forecast_viewer_model_outputs.csv / forecasts.csv / actuals.csv: unchanged.
- No model fitting, forecast generation, tournament rerun or champion change.
- Derived metrics are dashboard diagnostics only; never written to data/processed.
