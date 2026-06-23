# Stage 05H-PILOT-QA - Forecast Viewer Pilot Artifact Review

**QA timestamp:** 2026-06-18 11:54:09  
**Mode:** READ-ONLY QA. No Shiny touched, no models run, no forecasts generated, pilot artifact not overwritten, full artifact not created.

**Recommendation:** `PILOT_READY_WITH_MINOR_WARNINGS`

## Series coverage

| series_key | model_count | models_available | date_min | date_max | row_count | actual_value_coverage_pct | forecast_value_coverage_pct | horizon_min | horizon_max | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APC-Dedicated | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2025-05-03 | 2026-04-27 | 4680 | 100.0 | 100.0 | 1 | 30 | usable |
| APC-MSIT | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2025-05-03 | 2026-04-27 | 4680 | 100.0 | 100.0 | 1 | 30 | usable |
| APC-Multitenant | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2025-05-03 | 2026-04-27 | 4680 | 100.0 | 100.0 | 1 | 30 | usable |

## Model coverage

| model_name | model_origin | model_family | risk_status | is_selected_champion | series_covered | rows | forecast_value_coverage_pct |
| --- | --- | --- | --- | --- | --- | --- | --- |
| FixedGrowth_1_5 | baseline | growth_baseline | ok | False | 3 | 1080 | 100.0 |
| FixedGrowth_3 | baseline | growth_baseline | ok | False | 3 | 1080 | 100.0 |
| FixedGrowth_4 | baseline | growth_baseline | ok | False | 3 | 1080 | 100.0 |
| FixedGrowth_6 | baseline | growth_baseline | high_risk | False | 3 | 1080 | 100.0 |
| FastNeuralAR_MLP | challenger | lightweight_neural | high_risk | False | 3 | 1080 | 100.0 |
| LightGBM | challenger | machine_learning | ok | False | 3 | 1080 | 100.0 |
| LinearRegression | baseline | machine_learning | ok | False | 3 | 1080 | 100.0 |
| XGBoost | challenger | machine_learning | ok | False | 3 | 1080 | 100.0 |
| ARIMA_Fixed | baseline | statistical | ok | False | 3 | 1080 | 100.0 |
| AutoARIMA | challenger | statistical | ok | False | 3 | 1080 | 100.0 |
| ETS Explicit | challenger | statistical | high_risk | True | 3 | 1080 | 100.0 |
| ETS_Current | baseline | statistical | ok | False | 3 | 1080 | 100.0 |
| Theta | challenger | statistical | ok | False | 3 | 1080 | 100.0 |

## Horizon coverage

| horizon_days | rows | series_covered | models_covered | in_ui_horizon_set |
| --- | --- | --- | --- | --- |
| 1 | 468 | 3 | 13 | False |
| 2 | 468 | 3 | 13 | False |
| 3 | 468 | 3 | 13 | False |
| 4 | 468 | 3 | 13 | False |
| 5 | 468 | 3 | 13 | True |
| 6 | 468 | 3 | 13 | False |
| 7 | 468 | 3 | 13 | False |
| 8 | 468 | 3 | 13 | False |
| 9 | 468 | 3 | 13 | False |
| 10 | 468 | 3 | 13 | True |
| 11 | 468 | 3 | 13 | False |
| 12 | 468 | 3 | 13 | False |
| 13 | 468 | 3 | 13 | False |
| 14 | 468 | 3 | 13 | False |
| 15 | 468 | 3 | 13 | True |
| 16 | 468 | 3 | 13 | False |
| 17 | 468 | 3 | 13 | False |
| 18 | 468 | 3 | 13 | False |
| 19 | 468 | 3 | 13 | False |
| 20 | 468 | 3 | 13 | True |
| 21 | 468 | 3 | 13 | False |
| 22 | 468 | 3 | 13 | False |
| 23 | 468 | 3 | 13 | False |
| 24 | 468 | 3 | 13 | False |
| 25 | 468 | 3 | 13 | True |
| 26 | 468 | 3 | 13 | False |
| 27 | 468 | 3 | 13 | False |
| 28 | 468 | 3 | 13 | False |
| 29 | 468 | 3 | 13 | False |
| 30 | 468 | 3 | 13 | True |

### UI horizon set check (5,10,15,20,25,30,45,60)

- Present in artifact: [5, 10, 15, 20, 25, 30]
- Missing from artifact: [45, 60]
- Artifact horizon range: 1..30 (30 distinct, contiguous daily horizons)

## Actual / Forecast QA

- actual_value missing: 0.00%
- forecast_value missing: 0.00%
- actual_value is consistent across models for the same series/date (single actual line plottable)
- forecast_value varies by model for the same series/date (distinct forecast lines plottable)

## Grain / duplicate check

- Grain: series_key × model_name × date × horizon_days
- Duplicate grain rows: 0

## Chart readiness

| series_key | can_plot_single_actual_line | can_plot_forecast_line_per_model | horizon_filterable | date_window_filterable | models_plottable | chart_ready |
| --- | --- | --- | --- | --- | --- | --- |
| APC-Dedicated | True | True | True | True | 13 | True |
| APC-MSIT | True | True | True | True | 13 | True |
| APC-Multitenant | True | True | True | True | 13 | True |

## Human preview (series = APC-Dedicated, horizon_days = 1)

### Long preview

| series_key | date | actual_value | model_name | model_family | forecast_value | horizon_days | risk_status | is_selected_champion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | FixedGrowth_1_5 | growth_baseline | 2428.13071863 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | FixedGrowth_3 | growth_baseline | 2429.3441772600004 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | FixedGrowth_4 | growth_baseline | 2430.1531496800003 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | FixedGrowth_6 | growth_baseline | 2431.77109452 | 1 | high_risk | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | FastNeuralAR_MLP | lightweight_neural | 3002.397724496418 | 1 | high_risk | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | LightGBM | machine_learning | 2406.1651421988663 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | LinearRegression | machine_learning | 2425.41135206566 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | XGBoost | machine_learning | 2418.581298828125 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | ARIMA_Fixed | statistical | 2428.601522 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | AutoARIMA | statistical | 2421.414728369362 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | ETS Explicit | statistical | 2425.3617450529896 | 1 | high_risk | True |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | ETS_Current | statistical | 2429.006645520248 | 1 | ok | False |
| APC-Dedicated | 2025-05-03 00:00:00 | 2427.007518 | Theta | statistical | 2423.1472878123527 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | FixedGrowth_1_5 | growth_baseline | 2188.1161363125 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | FixedGrowth_3 | growth_baseline | 2189.209647625 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | FixedGrowth_4 | growth_baseline | 2189.938655166666 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | FixedGrowth_6 | growth_baseline | 2191.39667025 | 1 | high_risk | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | FastNeuralAR_MLP | lightweight_neural | 2692.231981342424 | 1 | high_risk | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | LightGBM | machine_learning | 2192.5171476200967 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | LinearRegression | machine_learning | 2202.8863865315184 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | XGBoost | machine_learning | 2195.992431640625 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | ARIMA_Fixed | statistical | 2182.374441 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | AutoARIMA | statistical | 2210.090964343419 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | ETS Explicit | statistical | 2210.5662191554666 | 1 | high_risk | True |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | ETS_Current | statistical | 2180.1070699802112 | 1 | ok | False |
| APC-Dedicated | 2025-06-02 00:00:00 | 2184.020518 | Theta | statistical | 2203.768061469916 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | FixedGrowth_1_5 | growth_baseline | 1317.9164579145 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | FixedGrowth_3 | growth_baseline | 1318.575086829 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | FixedGrowth_4 | growth_baseline | 1319.014172772 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | FixedGrowth_6 | growth_baseline | 1319.892344658 | 1 | high_risk | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | FastNeuralAR_MLP | lightweight_neural | 1593.277444199501 | 1 | high_risk | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | LightGBM | machine_learning | 1315.5063281372625 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | LinearRegression | machine_learning | 1264.516784173591 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | XGBoost | machine_learning | 1309.5128173828125 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | ARIMA_Fixed | statistical | 1301.6462639999995 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | AutoARIMA | statistical | 1280.7222960407091 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | ETS Explicit | statistical | 1279.2525879446462 | 1 | high_risk | True |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | ETS_Current | statistical | 1298.0048813953058 | 1 | ok | False |
| APC-Dedicated | 2025-07-02 00:00:00 | 1304.021445 | Theta | statistical | 1329.5481116664655 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | FixedGrowth_1_5 | growth_baseline | 1281.0005631915 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | FixedGrowth_3 | growth_baseline | 1281.6407433830002 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | FixedGrowth_4 | growth_baseline | 1282.0675301773335 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | FixedGrowth_6 | growth_baseline | 1282.9211037660002 | 1 | high_risk | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | FastNeuralAR_MLP | lightweight_neural | 527.9432398017332 | 1 | high_risk | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | LightGBM | machine_learning | 1279.7648090034745 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | LinearRegression | machine_learning | 1280.0791712689506 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | XGBoost | machine_learning | 1289.3204345703125 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | ARIMA_Fixed | statistical | 1281.1120790000004 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | AutoARIMA | statistical | 1279.4349860014036 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | ETS Explicit | statistical | 1262.4848287176164 | 1 | high_risk | True |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | ETS_Current | statistical | 1280.726727522577 | 1 | ok | False |
| APC-Dedicated | 2025-08-01 00:00:00 | 1280.843396 | Theta | statistical | 1280.7648969558106 | 1 | ok | False |

### Wide preview (date × model forecast pivot)

| date | series_key | actual_value | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2025-05-03 00:00:00 | APC-Dedicated | 2427.007518 | 2428.601522 | 2421.414728369362 | 2425.3617450529896 | 2429.006645520248 | 3002.397724496418 | 2428.13071863 | 2429.3441772600004 | 2430.1531496800003 | 2431.77109452 | 2406.1651421988663 | 2425.41135206566 | 2423.1472878123527 | 2418.581298828125 |
| 2025-06-02 00:00:00 | APC-Dedicated | 2184.020518 | 2182.374441 | 2210.090964343419 | 2210.5662191554666 | 2180.1070699802112 | 2692.231981342424 | 2188.1161363125 | 2189.209647625 | 2189.938655166666 | 2191.39667025 | 2192.5171476200967 | 2202.8863865315184 | 2203.768061469916 | 2195.992431640625 |
| 2025-07-02 00:00:00 | APC-Dedicated | 1304.021445 | 1301.6462639999995 | 1280.7222960407091 | 1279.2525879446462 | 1298.0048813953058 | 1593.277444199501 | 1317.9164579145 | 1318.575086829 | 1319.014172772 | 1319.892344658 | 1315.5063281372625 | 1264.516784173591 | 1329.5481116664655 | 1309.5128173828125 |
| 2025-08-01 00:00:00 | APC-Dedicated | 1280.843396 | 1281.1120790000004 | 1279.4349860014036 | 1262.4848287176164 | 1280.726727522577 | 527.9432398017332 | 1281.0005631915 | 1281.6407433830002 | 1282.0675301773335 | 1282.9211037660002 | 1279.7648090034745 | 1280.0791712689506 | 1280.7648969558106 | 1289.3204345703125 |

## Validation summary

| check_name | status | details |
| --- | --- | --- |
| pilot_artifact_exists | pass | data\processed\forecast_viewer_model_outputs_pilot.csv |
| required_columns_exist | pass | all present |
| no_shiny_files_modified | pass | QA is read-only on artifact; writes only outputs/model_lab/forecast_viewer_handoff_pilot_qa/ |
| pilot_artifact_not_overwritten | pass | artifact opened read-only; no write back to data/processed pilot CSV |
| no_full_artifact_created | pass | only QA preview/report files written |
| no_models_run | pass | no model fitting/inference |
| no_forecasts_generated | pass | QA reads existing forecast_value only |
| only_three_pilot_series | pass | present=['APC-Dedicated', 'APC-MSIT', 'APC-Multitenant'] |
| models_available_per_series | pass | model_counts=[13, 13, 13] (consistent=True) |
| model_families_populated | pass | families=['growth_baseline', 'lightweight_neural', 'machine_learning', 'statistical'] |
| horizon_days_populated | pass | min=1 max=30 distinct=30 |
| selected_ui_horizons_present | warning | present=[5, 10, 15, 20, 25, 30]; missing=[45, 60] |
| actual_value_populated | pass | missing=0.00% (0 rows) |
| forecast_value_populated | pass | missing=0.00% (0 rows) |
| actual_value_consistent_per_series_date | pass | actual_value identical across models for same series/date |
| forecast_value_varies_by_model | pass | 100.0% of series/date groups have >1 distinct forecast |
| values_numeric | pass | actual_value and forecast_value parse as numeric |
| date_parsing | pass | 0 unparseable dates |
| horizon_parsing | pass | 0 unparseable horizons |
| no_duplicate_grain_rows | pass | grain=['series_key', 'model_name', 'date', 'horizon_days']; duplicate_rows=0 |
| forecasts_not_all_identical | pass | models produce differing forecasts |
| chart_readiness_assessed | pass | series_ready=3/3 |
| long_preview_created | pass | series=APC-Dedicated, horizon=1, dates=4, rows=52 |
| wide_preview_created | pass | pivot date×model; 4 rows × 16 cols |

## Notes / limitations

- Backtest comparison data only (not forward production forecast).
- UI mockup horizons (5,10,...,60) are a SUBSET selection over the artifact's contiguous daily horizons; they map cleanly to existing horizon_days values.
- No prediction intervals (lower/upper/interval_level all NA) - point lines only.
- Deep-learning models (NBEATS/NHITS) intentionally absent (deferred); out of MVP scope.

**Final recommendation:** `PILOT_READY_WITH_MINOR_WARNINGS`
