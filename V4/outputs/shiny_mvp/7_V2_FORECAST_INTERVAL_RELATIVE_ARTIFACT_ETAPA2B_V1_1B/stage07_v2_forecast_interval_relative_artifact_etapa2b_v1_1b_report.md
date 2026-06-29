# Stage 07 - V2 Forecast Interval Relative-Residual Artifact (Etapa 2B-v1.1b)

**Status:** `V2_FORECAST_INTERVAL_RELATIVE_ARTIFACT_COMPLETED_WITH_WARNINGS`
**Headline:** Relative method fixed the absolute-offset absurdity and is **out-of-sample coverage-validated**.
The **80% band is tight and useful**; the **95% band is honest but wide**. Oscar must pick the default band level before Etapa 3.
**Scope:** Upstream candidate artifact only. No Shiny / models / champion / forecasts.csv changes.
**Date:** 2026-06-24

## 1. Objective
Replace the rejected absolute-residual intervals with **relative (proportional)** empirical
prediction intervals computed from backtest evidence, for horizons 1-30 only.

## 2. Method
Relative residuals computed **inside** the backtest (scale-invariant):
`relative_error = (actual_value - forecast_value) / forecast_value`, then applied to the
production point: `band = forecast_value * (1 + relative_quantile)`.
80% from q10/q90, 95% from q025/q975. Lower bounds capped at 0; upper uncapped.

## 3. Guardrails applied
- **Near-zero denominators:** excluded 4,148 backtest rows (1,041 with `forecast<=0`;
  3,107 with `|forecast| < 1% of key median |forecast|`). Scale-aware, documented in
  `interval_near_zero_excluded_count`.
- **Winsorization:** relative error clipped to **[-0.95, p99 = 26.18]** before quantiles
  (`interval_relative_error_clip_lower/upper`).
- **Fallback:** entity_key x horizon_bucket -> resource(HDD) x bucket -> global x bucket
  (min n: key>=20, fallback>=30).
- **Horizon limit:** bands only for forecast_horizon_day 1-30; >30 -> NA,
  reason `outside_calibrated_horizon_1_30`, `interval_extrapolated=False`.

## 4. Out-of-sample coverage (the key validation)
Temporal holdout = last 3 backtest cutoffs (2026-01-27, 2026-02-26, 2026-03-28); quantiles
trained on the earlier 9 cutoffs, coverage measured on the holdout actuals.

| level | holdout coverage | target range | result |
|---|---|---|---|
| 80% | **0.809** | 0.70 - 0.90 | PASS |
| 95% | **0.922** | 0.90 - 0.99 | PASS |

Coverage is honest (out-of-sample), not tautological. Both levels land within target.

## 5. Band-width credibility (the warning)
On the 1,350 available rows:
- **80% band width / forecast: median 0.16** (tight, useful).
- **95% band width / forecast: median 5.41, p95 26.2.**
- 95% band > 2x forecast: **925 rows (68.5%)**; > 5x forecast: **745 rows (55.2%)**.

The wide 95% band is a genuine property of the backtest: at the 97.5th percentile the models
under-predict by ~9x for some volatile keys/horizons, so the honest upper band is wide. The
coverage result (0.922) confirms the width is justified rather than a method bug. This is **not**
the absolute-method absurdity (bands unrelated to the point); here bands are proportional and
coverage-validated, but the 95% level is wide.

## 6. APC-Dedicated treatment
Interval is now **proportional and sane**: point 29.1 -> 95% [15.8, 85.3]
(vs the rejected absolute method 29 -> 902). However the production point itself is still
~36x below backtest/actuals, so `forecast_point_scale_anomaly = TRUE`. The interval expresses
uncertainty around the point; **it does not correct the point's scale anomaly** (separate review).

## 7. Calibration grain
1,170 rows `entity_key_x_horizon_bucket`; 180 rows `resource_x_horizon_bucket` fallback
(the 6 Go Local keys absent from backtest). 0 global fallback. Sample sizes in
`interval_calibration_sample_size`.

## 8. Contract columns added
`forecast_horizon_day`, `forecast_lower_80/upper_80/lower_95/upper_95`, `interval_available`,
`interval_method` (`empirical_backtest_relative_residual_quantile`), `interval_source`
(`forecast_viewer_model_outputs.csv`), `interval_level_available`, `interval_calibration_grain`,
`interval_calibration_sample_size`, `interval_horizon_bucket`, `interval_extrapolated`,
`interval_unavailable_reason`, `interval_relative_error_clip_lower`,
`interval_relative_error_clip_upper`, `interval_near_zero_excluded_count`,
`interval_holdout_coverage_80`, `interval_holdout_coverage_95`, `forecast_point_scale_anomaly`.

## 9. Preservation
65,095 rows in / out. Original 9 columns unchanged; `forecast_value` untouched.
Written to `data/processed/forecasts_with_intervals_relative.csv`; `forecasts.csv` NOT overwritten.

## 10. Recommendation
The artifact is **credible** (proportional + out-of-sample coverage-validated). The only open
choice is the **default band level for Shiny**: recommend **default 80%** (tight, coverage 0.809),
offering 95% as an explicit "wide/honest" option. With that decision, Etapa 3 can proceed.

## 11. Files in this folder
report.md, validation.csv, artifact_contract_summary.csv, calibration_table.csv,
holdout_coverage_report.csv, unavailable_summary.csv, band_width_diagnostic.csv,
apc_dedicated_sample.csv, top_widest_rows.csv, next_steps.csv.
Reproducible builder: `python/model_lab/build_interval_calibration_relative.py`.
