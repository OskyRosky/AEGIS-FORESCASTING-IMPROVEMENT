# P9J — V6.24 model evidence notes

## What V6.24 can support, proven from the artifacts

| Evidence | Present? | Proof |
|---|---|---|
| 15 governed models | **YES** | `accuracy_metrics.model_name` distinct = 15 |
| Every model scored on every series | **YES** | each model has exactly 140 series |
| 2,100 model-series rows | **YES** | 140 x 15 |
| Governed `model_family` (3-valued) | **YES** | Baseline 7 / Challenger 5 / Neural 3 |
| 4-family display grouping | **YES** | `V6_24_DISPLAY_FAMILY`, `DISPLAY_GROUPING_ONLY` |
| MAE, RMSE, WAPE, SMAPE, MAPE, median abs error, bias | **YES** | accuracy_metrics columns |
| Per-series rank + champion fields | **YES** | `rank_within_series`, `is_series_champion`, `champion_visible` |
| Signal quality and caveats | **YES** | `series_signal_quality`, `caveat_badge` |
| **MASE / RMSSE** | **NO** | no column matches `mase` or `rmsse` |
| **Global ranking** | **NO** | 15 rows per series; no global position column |
| **Pairwise tournament** | **NO** | no artifact in the cohort folder or V6.24 outputs |
| **Global champion decision** | **NO** | champion fields are per-series only |

## Cohort-wide medians, computed for the study only

Medians, never means — the cohort mean is destroyed by extreme values
(LinearRegression mean MAE 5.86e21 against a median of 870).

```
model              median MAE   median RMSE   median WAPE
Theta                  189.59        252.40        0.0514
FixedGrowth_6          217.26        299.59        0.0532
ETS_Current            217.71        363.61        0.0775
FixedGrowth_1_5        221.52        304.30        0.0539
FixedGrowth_3          224.70        295.71        0.0531
FixedGrowth_4          225.97        318.81        0.0529
AutoARIMA              247.99        349.11        0.0528
XGBoost                270.31        345.60        0.0577
ETS Explicit           284.19        412.78        0.0562
ARIMA_Fixed            301.72        478.66        0.1176
SMLP-TCN               318.31        409.27        0.0762
LightGBM               410.04        487.42        0.0711
NLIN-DLIN_FIXED        442.98        620.12        0.0715
FNAR-V2                515.86        607.44        0.0899
LinearRegression       870.16       1430.49        0.0870
```

**These figures are study evidence, not a governed ranking.** They were derived
here to answer "can a Universe page show anything useful?" — the answer is yes.
If a FULL page displays them it must label them as cohort medians read from
`accuracy_metrics`, not as a tournament result.

Note that median MAE and median WAPE disagree on the ordering: Theta leads on
MAE, AutoARIMA is close on WAPE, and ARIMA_Fixed is mid-table on MAE but worst
on WAPE. That is exactly why a single "standings" number would mislead.

## Championship distribution (125 presentable series)

```
FixedGrowth_6 21 · FixedGrowth_1_5 17 · AutoARIMA 16 · XGBoost 13 · Theta 12
ARIMA_Fixed 8 · LightGBM 7 · NLIN-DLIN_FIXED 7 · ETS_Current 7 · ETS Explicit 6
FixedGrowth_3 4 · FixedGrowth_4 4 · LinearRegression 2 · SMLP-TCN 1
```

14 of the 15 models win at least one series. `FixedGrowth_6` and
`FixedGrowth_1_5` — simple growth baselines — lead most often. That is a real
product finding and a much richer story than one global champion.

## Verdict per FULL page

- **Universe FULL** — fully supported. Build it.
- **Tournament FULL** — **not supported as a tournament.** No pairwise, no MASE,
  no RMSSE, no global rank. Build Ranking Diagnostics instead and disclose.
- **Champion FULL** — supported as a **per-series** champion with a
  championship distribution. A single global champion is **not** supported.
