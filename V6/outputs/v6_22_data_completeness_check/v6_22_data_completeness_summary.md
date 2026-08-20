# V6.22-CHECK — Data Completeness Verification Before Shiny Landing

## Result

`V6_22_DATA_COMPLETENESS_CHECK_COMPLETED`

All ten acceptance criteria pass. Every one of the 894 cohort cases falls into
exactly one data availability class. `MISSING_OR_INCONSISTENT` is **zero**.

This was a verification-only gate: nothing was regenerated, no model ran, no
artifact was modified, and the frozen V6.22 manifest was read but never touched.

## What each case can actually display

| Layer | Cases | Observed values | 15 governed model estimates | Forecast values |
|---|---:|---|---|---|
| `FULL_VIEWER_AND_FORECAST` | **596** | Yes | Yes, exactly 15 | Yes |
| `FORECAST_ONLY` | **298** | No | No | Yes |
| `INVALID_OR_QUARANTINED` (PROD) | 2, outside the cohort | — | — | — |
| `MISSING_OR_INCONSISTENT` | **0** | — | — | — |
| **Total in selectors** | **894** | | | |

Row-level evidence behind those flags:

* Observed values on the 596 full cases range from **2,250 to 5,400 rows** each.
* Forward forecast rows are uniform at **732 rows per case**, on all 894.
* All 596 full cases carry **exactly 15** governed models — not 14, not 16.
* The 298 forecast-only cases carry **zero** governed models and **zero**
  actual records, in both the Viewer and the forward artifact.

## Route group truth table

| Route group | Cases | In selector | Observed | 15 models | Forecast | Shiny behaviour |
|---|---:|---|---|---|---|---|
| HDD Basilisk | 202 | Yes | Yes | Yes | Yes | Viewer: actuals + 15 model backtests. Forecast: history + forward + boundary |
| HDD EDB Consumer | 197 | Yes | Yes | Yes | Yes | Same |
| HDD EDB Enterprise | 197 | Yes | Yes | Yes | Yes | Same |
| SSD Phoenix Low Volume No Efficiency | 147 | Yes | **No** | **No** | Yes | Forecast-only chart, no fabricated actuals, not in Viewer |
| SSD Phoenix Low Volume With Efficiency | 151 | Yes | **No** | **No** | Yes | Same |
| CPU | 0 | Yes, as `BACKEND_GAP` | No | No | No | Selector stops at an explicit backend-gap state |
| IOPS | 0 | Yes, as `BACKEND_GAP` | No | No | No | Same |

The three distinctions the owner asked to make explicit:

* **HDD** = observed + 15 governed model estimates + forecast.
* **SSD Phoenix** = forecast-only. No actuals, no 15-model backtest, not
  eligible for Accuracy.
* **CPU / IOPS** = unavailable until a governed SQL extraction. Zero rows exist
  and none was fabricated.

## The 15 governed Viewer models

Verified present on all 596 full cases:

`ARIMA_Fixed`, `AutoARIMA`, `ETS Explicit`, `ETS_Current`, `Theta`,
`FixedGrowth_1_5`, `FixedGrowth_3`, `FixedGrowth_4`, `FixedGrowth_6`,
`LightGBM`, `LinearRegression`, `XGBoost`, `FNAR-V2`, `NLIN-DLIN_FIXED`,
`SMLP-TCN`.

Deliberately **not** claimed: that all 894 cases carry these estimates. Only
596 do. The remaining 298 have none, by data.

## SSD Phoenix behaviour, confirmed line by line

| Requirement | Result |
|---|---|
| Present in the cohort and selection list | 298 cases |
| Has forecast values | 298 |
| Has observed actual values | 0 |
| Has forward-artifact actual records | 0 |
| Has governed 15-model backtest estimates | 0 |
| Classifiable as forecast-only | 298, `taxonomy_alignment = LEGACY_VARIANT` |
| Eligible for Accuracy or backtest | 0 |

Expected Shiny landing: SSD Phoenix **appears in the Forecast selector** and
renders a forecast-only chart with the `Forecast start` boundary. It is absent
from the Viewer selector because it has nothing to backtest. Nothing is hidden
and nothing is fabricated.

## PROD quarantine

Two cases, both `SSD - Phoenix ... | Forest | PROD`, excluded from the active
cohort and recorded in `v6_22_declared_not_buildable.csv` with reason
`INVALID_ENTITY_QUARANTINED`. `PROD` appears zero times in the cohort manifest.

## Shiny landing requirements

1. Selectors expose **HDD** (596 full cases) and **SSD Phoenix** (298
   forecast-only cases).
2. HDD renders observed values, the 15 governed model estimates, and the
   forward forecast.
3. SSD Phoenix renders a forecast-only state.
4. CPU and IOPS stop at an explicit `BACKEND_GAP` state.
5. Shiny reads prepared artifacts and Parquet **only**.
6. No SQL, no training, no recalculation inside Shiny.

Points 5 and 6 already hold as of V6.21B: Accuracy metrics are precomputed
outside Shiny and `acc_compute()` is a pure filter.

## Next step

The data is complete and consistent for the whole 894-case cohort. The
remaining blocker before V6.23 is unchanged and is **not** a data problem:

> `FORECAST_MODEL_VOCABULARY_UNGOVERNED` — the Viewer uses 15 governed models,
> the forward artifact uses 30 from a disjoint vocabulary, intersection zero.
> An owner decision is due **before** V6.23 generation.
