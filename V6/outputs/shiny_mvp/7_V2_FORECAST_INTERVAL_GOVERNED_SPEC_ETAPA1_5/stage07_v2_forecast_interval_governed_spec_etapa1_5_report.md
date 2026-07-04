# Stage 07 - V2 Forecast Interval - Governed Specification (Etapa 1.5)

**Status:** `V2_FORECAST_INTERVAL_GOVERNED_SPEC_COMPLETED_WITH_WARNINGS`
**Scope:** SPECIFICATION ONLY. No code, data, forecasts.csv, Shiny, models, metrics, or champion touched. V2 only.
**Date:** 2026-06-24

## 1. Objective
Define the governed method, contract, validation rules, fallback strategy, and
future implementation plan for generating **prediction intervals** in the forecast
artifact (Branch 2B), **before** any code changes. The dashboard will never compute
intervals; it will only visualize a governed artifact.

## 2. Key diagnostic findings (read-only)

### 2.1 Model-name mapping is NOT reliable
| Production (forecasts.csv, 16) | Backtest (forecast_viewer_model_outputs.csv, 13) |
|---|---|
| ARIMA, ExponentialSmoothing | ARIMA_Fixed, AutoARIMA, ETS Explicit, ETS_Current, Theta |
| FixedGrowth1/2/3/5% | FixedGrowth_1_5/3/4/6 |
| 10 ensembles (e.g. FixedGrowth2%_ARIMA_Ensemble) | (none) |
| - | LightGBM, XGBoost, LinearRegression, FastNeuralAR_MLP |

- `ARIMA -> {ARIMA_Fixed, AutoARIMA}` and `ExponentialSmoothing -> {ETS Explicit, ETS_Current}` are **ambiguous** (1 prod -> 2 backtest).
- FixedGrowth rate schemes differ (1% vs 1_5); **no clean match**.
- **All 10 production ensembles are absent** from the backtest.
- Net: **0 clean matches, 1 weak, 2 ambiguous, 13 none -> per-model calibration is infeasible.**

### 2.2 Production forecasts have no native error evidence
`forecasts.csv` is **future-only** (2026-04-28 -> 2030-04-25); `actuals.csv` ends 2026-04-27.
**Zero overlap** -> production-model residuals cannot be computed directly. The backtest
artifact (a **different** model population) is the only residual evidence available.

### 2.3 Horizon evidence gap (critical)
Backtest `horizon_days` only spans **1-30 days**. Production forecasts run to **~1450 days**.
Beyond 30 days there is **no empirical evidence** -> long-horizon bands would be
extrapolation, not calibration.

### 2.4 Sample thinness
~13,620 backtest rows per model across 45 keys x 30 horizons -> roughly **~10 obs per
(key x horizon x model)**. Too thin for stable 95% quantiles without pooling into buckets.

### 2.5 Existing interval columns are empty
Backtest `lower_bound`, `upper_bound`, `interval_level` are **100% NA**.

## 3. Recommended method
**Empirical / backtest-calibrated residual-quantile prediction intervals.**
Reject naive +/-2 sigma. Compute residual quantiles (e.g. 10/90 for 80%, 2.5/97.5 for 95%)
from backtest `actual_value - forecast_value`, at **key x horizon-bucket** grain, applied
additively to the production point forecast. Bands are an honest **portfolio proxy** and
must be labeled as such.

## 4. Recommended contract (wide, additive, NA-safe)
Adds: `forecast_lower_80`, `forecast_upper_80`, `forecast_lower_95`, `forecast_upper_95`,
`interval_method`, `interval_source`, `interval_level_available`,
`interval_calibration_grain`, `interval_calibration_sample_size`, `interval_horizon_bucket`,
`interval_extrapolated`. All existing columns and consumers unchanged.

## 5. Fallback hierarchy (preferred -> last resort)
1. key x mapped-model x horizon-bucket - INFEASIBLE (no reliable mapping)
2. key x model-family x horizon-bucket - partial/ambiguous
3. **key x horizon-bucket - PREFERRED**
4. resource x horizon-bucket - fallback (single resource HDD)
5. global x horizon-bucket - last resort

## 6. Horizon strategy
Buckets `1-7 / 8-14 / 15-30` are evidence-backed. Buckets `>30` (31-60 ... 365+) have
**no evidence** -> either leave NA or populate with `interval_extrapolated=TRUE` plus an
explicit caveat (Oscar decision D2/D11). Never silently extrapolate.

## 7. Deterministic models
`FixedGrowth*` get **empirical** bands (from backtest residuals), explicitly labeled
empirical - never presented as native probabilistic intervals.

## 8. Validation & coverage plan
VR1-VR15: monotonicity (`lower_95<=lower_80<=forecast<=upper_80<=upper_95`), non-negative
cap (>=0 for HDD), NA-together, additive-only rebuild, and **empirical coverage backtest**
(80% band ~covers 80%, 95% ~95%) reported by resource x horizon-bucket x grain.

## 9. Governance / labeling
Dashboard label: **"Prediction interval (backtest-calibrated)"**. Governance doc must record
method, residual source, the **model-population caveat**, the **30-day horizon limit**, the
0-cap coverage distortion, and coverage results.

## 10. Decisions Oscar must approve (blocking marked)
See `..._open_questions_for_oscar.csv`. Blocking: D2 (long-horizon handling), D3 (grain),
D5 (accept portfolio proxy), D11 (is a 30-day-only honest band acceptable for the business,
or must long-horizon bands exist - this determines whether 2B is viable as designed).

## 11. Files in this folder
- `stage07_v2_forecast_interval_governed_spec_etapa1_5_report.md` (this file)
- `stage07_v2_forecast_interval_governed_spec_etapa1_5_validation.csv`
- `stage07_v2_forecast_interval_model_mapping_diagnostic.csv`
- `stage07_v2_forecast_interval_method_decisions.csv`
- `stage07_v2_forecast_interval_recommended_contract.csv`
- `stage07_v2_forecast_interval_fallback_hierarchy.csv`
- `stage07_v2_forecast_interval_validation_rules.csv`
- `stage07_v2_forecast_interval_future_file_changes.csv`
- `stage07_v2_forecast_interval_open_questions_for_oscar.csv`
