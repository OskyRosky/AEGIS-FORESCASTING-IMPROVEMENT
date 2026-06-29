# Stage 07 - V2 Forecast Interval Artifact (Etapa 2B-v1)

**Status:** `V2_FORECAST_INTERVAL_ARTIFACT_V1_COMPLETED_WITH_WARNINGS`
**Etapa 3 (Shiny) is BLOCKED** pending a scale fix (see Section: Critical Finding).
**Scope:** Artifact/contract only. No Shiny, UI, server, models, SQL, or champion touched.
**Date:** 2026-06-24

## 1. Objective
Generate a governed, reproducible empirical prediction-interval artifact for the
Forecast page using backtest residual evidence for horizons 1-30 days, as an honest v1.
Bands are calculated **before** Shiny and stored in a candidate data artifact.

## 2. What was built
- Reproducible builder: `python/model_lab/build_interval_calibration.py`.
- Candidate data artifact: `data/processed/forecasts_with_intervals.csv`
  (additive; `forecasts.csv` was **NOT** overwritten).
- 9 diagnostic outputs in this folder.

## 3. Method
Empirical residual-quantile intervals.
`residual = actual_value - forecast_value` from the backtest artifact;
80% from residual quantiles q10/q90, 95% from q025/q975; applied additively to the
production point forecast; lower bounds capped at 0; upper uncapped.
Calibration grain (fallback): **entity_key x horizon_bucket** -> resource x bucket ->
global x bucket. Horizon scope strictly **1-30 days**; no extrapolation.

## 4. Structural results (all pass)
- Rows preserved: 65,095 in / 65,095 out. Original 9 columns intact; `forecast_value` unchanged.
- Bands present: **1,350 rows** (45 keys x 30 days). All 45 keys received bands
  (1,170 rows key-level; 180 rows resource fallback for the 6 keys absent from backtest).
- Beyond 30 days: **63,745 rows** NA, `interval_unavailable_reason=outside_calibrated_horizon_1_30`.
- `interval_extrapolated=False` everywhere. Monotonicity holds (0 violations). No lower < 0.
- In-sample coverage: 80% in [0.798, 0.805]; 95% in [0.949, 0.950] (near nominal, but in-sample/tautological).

## 5. CRITICAL FINDING (why Etapa 3 is blocked)
The backtest series and the production forecast series are on **different, key-dependent
scales** for the same `entity_key`:

| entity_key | prod forecast median | backtest actual median | ratio |
|---|---|---|---|
| APC-Dedicated | 35.9 | 1,295.9 | **36.1x** |
| APC-MSIT | 2,539.8 | 2,291.7 | 0.90x |
| APC-Multitenant | 883,188 | 537,698 | 0.61x |
| ... (39 keys) | ... | ... | 0.30x - 36x |

Because residual **offsets are absolute**, transferring them across mismatched scales
produces **non-credible bands**: e.g. `APC-Dedicated` point 29.1 -> upper_95 902.4.
**240 of 1,350 band rows (~18%) have a 95% band wider than 2x the point forecast**, with
astronomical outliers on the high-scale keys. Even `actuals.csv` gives a third scale,
so the three sources are not directly comparable per key.

**Conclusion:** the v1 absolute-residual artifact is structurally valid but **not safe to
visualize**. It must not advance to Shiny as-is.

## 6. Recommended fix (v1.1, before Etapa 3)
Switch to **relative residuals** (scale-invariant):
`relative_error = (actual - forecast) / actual`; band = `forecast_value * (1 + rel_quantile)`.
Also resolve the root cause of the three-way scale difference between `forecasts.csv`,
`forecast_viewer_model_outputs.csv`, and `actuals.csv` (units / aggregation).

## 7. Interval contract columns added
`forecast_horizon_day`, `forecast_lower_80/upper_80/lower_95/upper_95`, `interval_available`,
`interval_method` (`empirical_backtest_residual_quantile`), `interval_source`
(`forecast_viewer_model_outputs.csv`), `interval_level_available` (`80,95`/NA),
`interval_calibration_grain`, `interval_calibration_sample_size`, `interval_horizon_bucket`,
`interval_extrapolated` (False), `interval_unavailable_reason`.

## 8. Governance notes
- Intervals are **empirical, backtest-calibrated** - NOT native model confidence intervals.
- NOT model-specific (production->backtest model mapping is unreliable); a **portfolio proxy**.
- Calibrated for horizons **1-30 only**; rows beyond 30 intentionally have no bands.
- Coverage shown is **in-sample** (needs out-of-sample holdout to be meaningful).
- Shiny must only visualize these columns later; for windows > 30 days show point forecast after day 30.

## 9. Files in this folder
- `..._report.md` (this file)
- `..._validation.csv`
- `..._contract_summary.csv`
- `..._calibration_table.csv`
- `..._coverage_report.csv`
- `..._unavailable_summary.csv`
- `..._sample_rows.csv`
- `..._scale_mismatch_diagnostic.csv`
- `..._next_steps.csv`
Data artifact: `data/processed/forecasts_with_intervals.csv` (candidate).
