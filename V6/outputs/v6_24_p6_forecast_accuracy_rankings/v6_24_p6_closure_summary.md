# V6.24-P6 — Forecast, Accuracy and Rankings — Closure Summary

**Status: PARTIALLY COMPLETE.** Accuracy and rankings delivered and promoted.
Forecast **blocked** pending an owner decision on the forecast horizon.

**Validation: 32 PASS / 4 BLOCKED / 0 FAIL of 36 checks.**

---

## 1. What was delivered

Two Shiny-facing artifacts were promoted to `V6/data/processed/v6_24_mvp_cohort/`:

| Artifact | Rows | Content |
|---|---|---|
| `accuracy_metrics.parquet` / `.csv` | 2,100 | 140 series × 15 models, per-series-model mae, rmse, mape, smape, wape, bias, plus negative and extreme counts |
| `model_rankings.parquet` / `.csv` | 2,100 | Full 1–15 ranking within every series, exactly 140 champions |

Accuracy is computed **per series first, then aggregated** — never pooled across
raw rows — because backtest density differs by metric (HDD 4,086 rows/series,
SSD 4,500, CPU 4,496, IOPS 4,749). Pooling would have silently weighted IOPS
above HDD.

## 2. The stale manifest flag was overridden, as required

`cohort_manifest.has_15_model_backtests` reads `FALSE` for 90 of 140 series.
That flag is **stale**: it was frozen in P4, before P5 generated the backtests.

P6 derived readiness directly from `model_backtests_15_models.parquet` and found
**140/140 series ready**, correcting **90 series** that the frozen flag would have
excluded. Had P6 trusted the manifest, two thirds of the cohort — every SSD, CPU
and IOPS series — would have silently vanished from the Viewer.

The P4 artifact was **not** repaired in place; it remains frozen. P7 must derive
readiness the same way. See `v6_24_p6_derived_backtest_readiness.csv`.

## 3. What is blocked, and why

`forecast_outputs` was **not produced**. Three mutually incompatible definitions of
"forecast horizon" exist, and no evidence supports choosing between them:

| Semantics | Value | Status |
|---|---|---|
| Prompt default assumption | 48 steps × 30 days = 1,440 days | **Not achievable** — no governed model reaches it |
| Existing HDD forward artifact | 732 daily steps | **Unusable** — built from 30 model names with **zero** overlap with the governed 15 |
| Proven model capability | **exactly 30 daily steps** | The only verified option |

This is not an inference. All **15 of 15 governed models were fitted on a real
cohort series** (`IOPS__Consumed__Region__APC-Multitenant`, 1,103 observations) and
each returned **exactly 30 steps**. The distinct set of emitted step counts across
all 15 models is `[30]`. Evidence: `v6_24_p6_forecast_horizon_probe.csv`.

The constraint is structural, not configurable:

- `HORIZON_DAYS = 30` is a module constant in `model_lab/run_v3_2c_subset_dry_run.py`.
- No governed call site accepts a horizon argument. Baselines call
  `model.predict(HORIZON_DAYS)`; challengers take only `(values)`.
- For the neural models, `build_xy(values, LAGS, HORIZON_DAYS)` makes 30 the
  **output dimension of the trained network**. A longer horizon is a different
  architecture, not a parameter change.
- A horizon-parameterised variant exists in `model_lab/run_backtest_60d.py`, but it
  covers only the 5 challengers and is **not** the governed import path.

Producing a forecast artifact under any of these three readings would mean
inventing a horizon. P6 stops instead.

## 4. Findings that constrain P7 and P8

**Mean-based accuracy aggregation is unusable.** 11 of 2,100 series-model pairs have
`wape > 100`, reaching a maximum of `1.25e23`. All 11 are HDD, concentrated in just
5 series, and are produced by `LinearRegression`, `FNAR-V2`, `SMLP-TCN`,
`ARIMA_Fixed` and `ETS Explicit`. This pushes the HDD **mean** wape to ~2.4e20 while
its **median** wape is a healthy 0.0506.

**P7/P8 must aggregate accuracy by median, never by mean.** A mean-based Viewer tile
would display a meaningless number.

Rankings are **not** affected: the degenerate models always lose their within-series
comparison. The worst champion value is 9.96 and **no champion exceeds wape = 100**.

**Negative and extreme predictions were reported, never clipped**, honouring the P5C
caveat. 7,531 negative predictions (1.23%) and 1,371 extreme ratios (0.22%). The
inheritance pattern P5C identified is confirmed exactly: the reused HDD artifact
carries 2.53% negatives against 0.58% for P5-generated rows.

## 5. Headline results

Champion wins are spread across all 15 models, which indicates the ranking is
discriminating rather than collapsing onto one model: `FixedGrowth_6` 21,
`FixedGrowth_1_5` 16, `AutoARIMA` 16, `FNAR-V2` 15, `XGBoost` 13, `Theta` 12, with
the remaining 9 models taking 47 between them.

Median wape by metric: HDD 0.0506, CPU 0.0559, SSD 0.0654, IOPS 0.0740.

The pattern is metric-specific — `FixedGrowth_6` wins 18 of 50 SSD series but only
2 of 50 HDD, while `FNAR-V2` wins 15 HDD series and none elsewhere. Any P7 default
model choice should therefore be made **per metric**, not globally.

## 6. Governance

Shiny untouched. No SQL or Tesseract access. No commit, no push. All 8 frozen
P4/P5 artifacts verified unmodified by mtime comparison before and after the run.
No `navigation_contract` or `taxonomy_counts` created — those are P7 scope. The
champion model name `ETS Explicit` is carried with its registry spelling, space and
all.

## 7. Recommended next step

**Do not start P7 yet.** P7 builds the navigation contract over the cohort, and the
question of whether `forecast_outputs` exists changes what it must expose.

Resolve **Q1** first: accept a 30-day horizon (the only verified option), authorise
recursive multi-step forecasting, or re-architect the models. Options B and C are
new modelling capabilities that P5B never validated; if either is chosen, Q2 applies
and a new smoke stage should measure recursive error compounding before anything
reaches the Viewer.

Six open questions are recorded in `v6_24_p6_unresolved_questions.csv`.

---

**V6_24_P6_BLOCKED_FORECAST_HORIZON_UNRESOLVED**
