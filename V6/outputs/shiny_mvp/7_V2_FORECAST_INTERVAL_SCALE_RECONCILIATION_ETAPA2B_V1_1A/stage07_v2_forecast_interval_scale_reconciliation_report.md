# Stage 07 - V2 Forecast Interval Scale Reconciliation (Etapa 2B-v1.1a)

**Status:** `SCALE_RECONCILIATION_COMPLETED_WITH_WARNINGS`
**Decision:** Relative-residual intervals are **safe to attempt** (scale-invariant). Proceed to 2B-v1.1b with guardrails. Etapa 3 (Shiny) stays blocked until 1.1b validates credibility + out-of-sample coverage.
**Scope:** Diagnostic only. No interval bands generated. No data/Shiny/model/champion changes.
**Date:** 2026-06-24

## 1. Objective
Determine whether `entity_key` / resource / units are comparable across the three artifacts,
and whether relative residuals can be transferred from backtest to production forecasts.

## 2. Artifacts inspected
- `data/processed/forecast_viewer_model_outputs.csv` (backtest; key col `series_key` -> entity_key); 39 keys.
- `data/processed/forecasts.csv` (production point forecast); 45 keys.
- `data/processed/actuals.csv` (history); 45 keys.

## 3. Key overlap
- 39 keys present in all three. 6 keys missing from backtest:
  AUT/CHL/DNK/EUR/IDN/MYS-Go Local. These need a resource/global fallback for relative error.
- Key names are identical across artifacts (same semantic entity by name).

## 4. Scale comparison (medians)
Per-key ratio `backtest_actual_median / production_forecast_median` across 39 keys:
- 32 keys within 2x (ok), 6 moderate (>2x), **1 extreme (APC-Dedicated 36x)**.
- Distribution: min 0.30, median 0.70, max 36.07.

Global `actuals_median / production_forecast_median`: median 0.30
(production forecasts are generally ~3x historical actuals over the 2026-2030 horizon).

## 5. CRITICAL: APC-Dedicated case study
| artifact | value | rows | median | p95 | date range |
|---|---|---|---|---|---|
| backtest_actual | actual_value | 4680 | **1295.9** | 2239.5 | 2025-05 .. 2026-04 |
| backtest_forecast | forecast_value | 4680 | 1307.9 | 2446.3 | 2025-05 .. 2026-04 |
| production_forecast | forecast_value | 1447 | **35.9** | 42.1 | 2026-04 .. 2030-04 |
| actuals | actual_value | 2491 | **977.0** | 2226.2 | 2019-07 .. 2026-04 |

**The backtest (1296) AND actuals.csv (977) agree (~thousands); the production forecast (36) is
the outlier (~36x smaller).** So for this key the scale anomaly lives in the *production point
forecast*, not in the backtest. This is a forecast-quality flag for Oscar, separate from intervals.

## 6. Why relative residuals are NOT blocked by this
The absolute method failed because it added backtest-scale offsets (~1300) to a production point
(~36). Relative residuals are computed **within** the backtest:
`relative_error = (backtest_actual - backtest_forecast) / backtest_forecast`,
then `band = production_forecast * (1 + relative_quantile)`. This is **scale-invariant**: the
bt-vs-prod absolute mismatch never propagates. The band scales with the production point itself,
so even APC-Dedicated yields a proportional (sane) band instead of a 900-wide offset.

## 7. Relative residual readiness
- 39 keys: `ready_relative_residual` (sufficient in-sample relative-error evidence).
- 6 keys: `fallback_needed_no_backtest` (Go Local set) -> resource(HDD)/global fallback.
- No key is fundamentally blocked.

## 8. Resource / scenario / grain findings
- `forecasts.csv` and `actuals.csv` carry `resource` (HDD) and `scenario` (Enterprise).
- Backtest has no `resource`/`scenario` columns; it is a single-resource (HDD) artifact by construction.
- Backtest horizon is 1-30 days only; production spans ~1450 days -> intervals remain horizon-limited to 1-30.

## 9. Required guardrails for 2B-v1.1b
1. Winsorize/cap relative_error (e.g. clip lower to -0.95; cap upper near p99) and guard `forecast≈0`.
2. Fallback hierarchy for relative error: entity_key x horizon_bucket -> resource x bucket -> global x bucket.
3. Re-validate band-width/forecast credibility (most rows should be < ~1) and out-of-sample coverage (holdout, not in-sample).
4. Keep APC-Dedicated production-point anomaly as a separate flag for Oscar.

## 10. Open items for Oscar (do not block intervals)
- Review APC-Dedicated production forecast scale (36x below backtest/actuals).
- Confirm whether the global forecasts-vs-actuals 3x spread is legitimate growth or unit drift.

## 11. Files in this folder
report.md, validation.csv, scale_by_key.csv, scale_ratio_diagnostic.csv, key_overlap.csv,
apc_dedicated_case_study.csv, scale_mismatch_flags.csv, relative_residual_readiness.csv, next_steps.csv.
Reproducible script: `python/model_lab/scale_reconciliation_diagnostic.py`.
