# V6.23-P0 — Viewer Scope Fix, closure

## Result

`V6_23_P0_VIEWER_SCOPE_FIX_COMPLETED`

All nine blocking validations pass. The Viewer now exposes the full local
cohort, and nothing was fabricated to achieve it.

## The Viewer, before and after

| | Before | After |
|---|---|---|
| Header | `596 entities / 6 routes` | `894 cases / 8 routes` + `596 backtest · 298 forecast-only` |
| Metric selector | HDD only | **HDD and SSD** |
| Visible cases | 596 | **894** |
| Backtest-capable | 596 | 596, unchanged |
| Forecast-only visible | 0 | **298** |
| `PROD` | absent | absent, now by an explicit quarantine rule |
| Header source | hardcoded string | derived from the contract at runtime |

## Root cause

All 300 SSD rows in `v6_18_navigation_contract.csv` carried
`viewer_visible = FALSE`. That was a V6.18 decision, not a bug in the data: the
contract has always distinguished *visible in the selector* from *eligible for a
backtest*, and V6.18 set both to FALSE for SSD.

The fix separates the two questions again. `viewer_visible` now means "this case
exists locally and the user may select it". `viewer_eligible` still means "a
backtest can actually be rendered", and it remains FALSE for every SSD case.

## What each selection now renders

**HDD** — verified on `HDD → Organic → EDB → Consumer → Region → APC-MSIT`:
observed actuals plus one line per selected governed model, 7 series for actual
plus 6 models, Analyze Backtest enabled, 15 models available.

**SSD Phoenix** — verified on
`SSD → Phoenix → Low Volume No Efficiency → Forest → NAMPRD07`:

* route state `FORECAST_ONLY`
* banner: *"No observed actuals or 15-model backtest estimates are available for
  SSD - Phoenix. Nothing was fabricated. Open the Forecast section to see the
  prepared forward forecast for this forest."*
* zero fabricated series
* Analyze Backtest disabled
* the chart area explains the state instead of showing a blank panel
* route cards read `PREPARED_FORECAST_ONLY` and `Actuals: Not available`

**Forecast** — unchanged and re-verified: SSD Phoenix renders one forward
forecast series of 30 points with the `Forecast start` boundary at 2026-08-12
and no fabricated history.

## Blocking validation

| Check | Result |
|---|---|
| V1 Metric selector includes HDD and SSD | PASS |
| V2 Header no longer presents 596/6 as the full scope | PASS |
| V3 HDD renders observed values plus model estimates | PASS |
| V4 SSD Phoenix selectable in the Viewer | PASS |
| V5 No fabricated SSD actuals or 15-model estimates | PASS |
| V6 SSD Phoenix shows a clean forecast-only state | PASS |
| V7 Forecast still renders SSD Phoenix | PASS |
| V8 No SQL, no training, no recomputation | PASS |
| V9 V1–V5 untouched | PASS |

## Two findings worth carrying forward

**1. `PROD` is still visible in the Forecast selector.** This fix removed it
from the Viewer, as instructed. Forecast was deliberately left alone: changing
`forecast_visible` would alter behaviour that V6.18 and V6.20 already validated,
and the task was Viewer-scoped. If `PROD` should disappear everywhere, that is a
one-line change to the same `QUARANTINED_ENTITIES` set plus a Forecast
re-validation. Recommended, but not done unilaterally.

**2. The V6.22 cohort manifest is still not wired into Shiny.** The Viewer and
the manifest now agree at 894 cases, but they agree because both derive from the
same V6.17 artifacts — not because Shiny reads the manifest. That is the correct
separation today: the contract drives navigation, the manifest is a generation
plan. Worth stating explicitly so nobody assumes a link that does not exist.

## Governance

No SQL. No model training. No recomputation. No fabricated actuals or estimates.
Shiny still reads prepared artifacts and Parquet only. Productive Parquet files
unchanged. V1 through V5 untouched. Nothing pushed.

## Next step

The visual blocker is cleared. The blocker for V6.23 generation is unchanged and
is not a UI problem: `FORECAST_MODEL_VOCABULARY_UNGOVERNED` still needs an owner
decision, because the forward artifact uses 30 model names disjoint from the
governed 15.
