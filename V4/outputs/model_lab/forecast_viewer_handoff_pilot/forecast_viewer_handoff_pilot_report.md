# Stage 05H-PILOT - Forecast Viewer Multi-Model Handoff (PILOT)

**Build timestamp:** 2026-06-18 11:42:19  
**Mode:** Data-engineering consolidation of EXISTING Stage 5 outputs. No models run, no forecasts generated, no metrics recomputed, no champion change.

## Semantics

This artifact contains **historical BACKTEST** model forecasts for model comparison. It is **NOT** the forward production forecast. The dashboard must label it as *model comparison / backtest evidence*.

## 1-2. Selected series and coverage

Pilot series selected: **APC-Dedicated, APC-MSIT, APC-Multitenant**

| series_key | series_label | has_actuals | has_baseline_forecasts | has_challenger_forecasts | baseline_model_count | challenger_model_count | total_model_count | models_available | min_date | max_date | status | selected_for_pilot |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| APC-Dedicated | APC-Dedicated | True | True | True | 7 | 6 | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2019-07-01 | 2026-04-27 | usable | True |
| APC-MSIT | APC-MSIT | True | True | True | 7 | 6 | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2019-07-01 | 2026-04-27 | usable | True |
| APC-Multitenant | APC-Multitenant | True | True | True | 7 | 6 | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2019-07-01 | 2026-04-27 | usable | True |
| ARE-Go Local | ARE-Go Local | True | True | True | 7 | 6 | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2019-07-01 | 2026-04-27 | usable | False |
| AUS-Go Local | AUS-Go Local | True | True | True | 7 | 6 | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2019-07-01 | 2026-04-27 | usable | False |
| BRA-Go Local | BRA-Go Local | True | True | True | 7 | 6 | 13 | ARIMA_Fixed | AutoARIMA | ETS Explicit | ETS_Current | FastNeuralAR_MLP | FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | LightGBM | LinearRegression | Theta | XGBoost | 2020-09-22 | 2026-04-27 | usable | False |

## 3-4. Models available per series

| series_key | model_count |
| --- | --- |
| APC-Dedicated | 13 |
| APC-MSIT | 13 |
| APC-Multitenant | 13 |

## 5. Source artifacts used

- outputs/model_lab/full_baseline/full_baseline_forecasts.csv (baseline forecasts)
- outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv (challenger forecasts + actuals)
- data/processed/actuals.csv (actuals for baseline rows)
- outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv (origin/family/champion/risk)
- outputs/model_lab/model_lab_closure_pack/model_lab_deferred_models.csv (deferred exclusion)
- outputs/model_lab/model_lab_closure_pack/model_lab_risk_register_final.csv (risk)

## 6-7. Rows and date range

- Total rows: **14,040**
- Distinct models: **13**
- Date range: **2025-05-03 -> 2026-04-27**

## 8. Backtest vs production

Historical **backtest** comparison (not forward production).

## 9. Prediction intervals

**Not available** in any source. lower_bound/upper_bound/interval_level = NA.

## 10-11. Readiness

Artifact is structurally ready for a **Shiny pilot rebind** (read-only). Full 39-series build can reuse this builder with the full series list.

## 12. Dashboard limitations to display

- Backtest window only (not forward production).
- Pilot = 3 series only.
- No deep-learning forecasts (NBEATS/NHITS deferred).
- FastNeuralAR_MLP is lightweight-neural / high-risk, not a champion.
- No prediction intervals (point forecasts only).

## Output format
Primary consumable written as **CSV (fallback, no parquet engine)**, plus sample CSV + manifest CSV.
