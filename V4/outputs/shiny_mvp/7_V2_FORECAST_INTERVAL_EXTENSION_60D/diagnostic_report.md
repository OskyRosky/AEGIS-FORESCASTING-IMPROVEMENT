# Stage 07 — V2 Forecast Interval Extension to 60 Days

**Mode:** Diagnose-first (upstream, pre-Shiny). No Shiny touched. No models run.
No original data artifact modified. No fabricated bands created.

## Objective
Evaluate whether a governed artifact with 80% relative-residual prediction
intervals can be produced for `forecast_horizon_day` 1–60 (currently 1–30).

## Final status
**60-day intervals require model lab / backtest extension.**

Calibrated 80% intervals for horizons 31–60 **cannot** be produced today because
**no governed backtest evidence exists beyond horizon 30**. Producing bands for
31–60 now would mean fabricating them, which is explicitly out of scope.

## 4-point diagnostic

### 1. Backtest evidence for horizons 31–60 in `forecast_viewer_model_outputs.csv`
**ABSENT.** `horizon_days` ranges strictly 1–30 (5,902 rows per horizon,
177,060 total). Nothing exists at 31–60.

### 2. Process/script able to generate a 31–60 backtest
**Engine exists but is capped at 30.**
- `config/backtesting.yaml` → `forecast_horizon_days: 30`, `validation_method: walk_forward`,
  `n_windows: 12`, `expanding_window: true`.
- Upstream sources feeding the handoff builder are both capped at `horizon_day` 1–30, 12 windows:
  - `outputs/model_lab/full_baseline/full_baseline_forecasts.csv` (hmin 1, hmax 30, 12 windows)
  - `outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv` (hmin 1, hmax 30, 12 windows)
- Extending to 60 requires **re-running the walk-forward backtest with
  `forecast_horizon_days: 60`**, which re-fits the 13 models across the windows
  = running models. Out of scope without explicit go-ahead.

### 3. Recalibrate relative-residual method for 1–60
**Method extends trivially; data does not.** The relative-residual builder
(`build_interval_calibration_relative.py`) uses `bucket_of(h)` with buckets
`1_7`, `8_14`, `15_30` and returns `None` for h>30. Adding buckets `31_45`,
`46_60` is a one-line change — but there are **no residuals in 31–60 to
quantile**, so calibration would have nothing to compute from.

### 4. Out-of-sample coverage validation for 60
**Not possible now** (no holdout residuals at 31–60). Data availability is NOT
the blocker: of the 12 backtest cutoffs, **10 have enough future actuals to
evaluate a 60-day horizon**; only 2 are truncated:
- 2026-02-27 → needs actuals to 2026-04-28 (missing; actuals end 2026-04-27)
- 2026-03-29 → needs actuals to 2026-05-28 (missing)

Actuals range: 2019-07-01 → 2026-04-27.

## What is missing to unblock 31–60 intervals
A single upstream step: **re-execute the Model Lab walk-forward backtest at
`forecast_horizon_days: 60`** to materialize residual evidence for horizons
31–60, then recalibrate.

## Recommended next step (Model Lab task, NOT Shiny)
1. Set `config/backtesting.yaml` → `forecast_horizon_days: 60` (new run; do not
   overwrite the 30-day governed run).
2. Re-run the walk-forward backtest. Expect ~10/12 windows to yield full 60-day
   evaluation; the last 2 cutoffs will be partial at long horizons (document the
   reduced sample for buckets 31_45 / 46_60).
3. Regenerate the handoff (`build_forecast_viewer_handoff.py`) to produce a
   60-day `forecast_viewer_model_outputs` variant.
4. Extend `build_interval_calibration_relative.py` with buckets `31_45`,
   `46_60`; re-run with holdout coverage validation.
5. Only then create the candidate Shiny artifact
   `data/processed/forecasts_with_intervals_relative_60d.csv` with
   `interval_available = TRUE` for calibrated horizons and
   `interval_unavailable_reason = outside_calibrated_horizon_1_60` afterward.

## Governance attestation
- No Shiny files modified.
- No original data artifacts modified (`forecasts.csv`,
  `forecasts_with_intervals_relative.csv`, backtest CSVs untouched).
- No models run.
- No champion change.
- No fabricated intervals created.
