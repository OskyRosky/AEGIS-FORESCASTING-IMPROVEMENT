# V6.23-P0 | Current Viewer scope, as found

## The symptom

The Viewer header read **"596 entities / 6 routes"** and the Metric selector
offered **only HDD**. SSD Phoenix was absent from the Viewer entirely.

## Why the count was 596

596 is the number of route × key cases that carry **actuals and 15-model
backtests**. It was being presented as if it were the whole visual scope of the
page. The local cohort is larger:

| Layer | Cases |
|---|---:|
| Backtest-capable (HDD) | 596 |
| Forecast-only (SSD Phoenix) | 298 |
| **Total local visible** | **894** |
| Quarantined and correctly excluded (`PROD`) | 2 |

## Why SSD was invisible

Measured directly in `v6_18_navigation_contract.csv`:

| base_metric | Rows | viewer_visible | viewer_eligible | forecast_visible | has_actuals |
|---|---:|---:|---:|---:|---:|
| HDD | 596 | 596 | 596 | 596 | 596 |
| SSD | 300 | **0** | 0 | 300 | 0 |

All 300 SSD rows carried `viewer_visible = FALSE`. That was a deliberate V6.18
decision, recorded at the time as "SSD-Phoenix absent from Viewer", and the
Viewer help text stated it explicitly.

## Why that decision was wrong for this product

The contract already distinguishes two different questions:

* `viewer_visible` — should this appear in the Viewer's selectors?
* `viewer_eligible` — can the Viewer actually render a backtest for it?

V6.18 collapsed both to FALSE for SSD. The effect was that a user could not see
298 prepared cases that exist locally and have real forward forecasts. The page
was not wrong about the data; it was hiding scope.

## What was NOT wrong

* `viewer_eligible = FALSE` for SSD is **correct**. Those cases genuinely have
  no actuals and no backtest.
* The Forecast page was already correct: 896 cases, SSD included.
* No fabricated data existed anywhere.
