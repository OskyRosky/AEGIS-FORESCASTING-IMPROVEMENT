# V6.23-P1 | Selector policy changes

## The rule now enforced

> **Viewer** exposes only cases that can render a real backtest: observed
> actuals **and** the 15 governed model estimates.
> **Forecast** exposes every case that has a forward forecast.

A selection that would end in *"Backtest unavailable"* is no longer reachable.

## What P0 got wrong, and why

V6.23-P0 made SSD Phoenix visible in the Viewer selector on the reasoning that
hiding 298 local cases was hiding scope. That was half right: the cases should
be **discoverable**, but they should not be **selectable as backtest cases**,
because selecting one produced a dead end.

The distinction that matters is not visible-versus-hidden. It is
*selectable-as-a-backtest* versus *listed-as-forecast-only*.

## The change

### 1. `build_v6_18_navigation_contract.py`

```python
"viewer_visible": flag(
    row["series_key"] not in QUARANTINED_ENTITIES
    and viewer_row is not None
    and truth(viewer_row["viewer_available"])
    and truth(viewer_row["has_actuals"])
),
"forecast_visible": flag(row["series_key"] not in QUARANTINED_ENTITIES),
```

`viewer_visible` is now the same condition as `viewer_eligible`. That is
deliberate: it makes "every selectable case is complete" true **by
construction**, not by convention, so the two flags cannot drift apart again.

`PROD` is now excluded from **both** selectors. In P0 it was removed from the
Viewer only, and the Forecast exposure was reported as an open finding. This
stage's acceptance criteria require it excluded, so it now is.

### 2. Regenerated contract

| Flag | Before P1 | After P1 |
|---|---:|---:|
| `viewer_visible` | 894 | **596** |
| `viewer_eligible` | 596 | 596 |
| `forecast_visible` | 896 | **894** |
| `forecast_eligible` | 896 | 896 |

Rows unchanged at 901. Only the two `*_visible` columns moved.

### 3. `R/taxonomy_navigation.R`

`taxonomy_viewer_scope()` rewritten to return `selectable`, `routes`,
`forecast_only`, `forecast_only_labels` and `forecast_total`. The Viewer header
can no longer print a number that includes cases the user cannot select.

### 4. `ui/tabs_v6_16_viewer.R`

* Header pill: **"596 Viewer-complete cases / 6 routes"**.
* New forecast-only callout, placed after the selector and visually separate
  from it:

  > **Forecast-only, not selectable here** — 298 prepared cases (SSD - Phoenix)
  > are available in Forecast only. No observed actuals and no 15-model backtest
  > estimates exist for them in any local artifact, so there is nothing to
  > backtest and nothing was fabricated. Open the Forecast section to see their
  > prepared forward forecasts.

* Help text rewritten to state that every selectable case is complete.

### 5. `www/custom.css`

One small rule for the callout layout. No existing style changed.

### 6. `R/viewer_pilot.R` — kept, now unreachable

The forecast-only state added in P0 is retained as a **defensive fallback**. It
can no longer be triggered through the selector, but if a future contract change
ever exposed an incomplete case, the page would explain itself instead of
showing a broken panel. Left in place deliberately.

## Files changed

| File | Purpose |
|---|---|
| `V6/outputs/v6_18_shiny_dynamic_taxonomy_ui/build_v6_18_navigation_contract.py` | Visibility rule: Viewer requires completeness; PROD quarantined from both pages |
| `V6/outputs/v6_18_shiny_dynamic_taxonomy_ui/v6_18_navigation_contract.csv` | Regenerated; only the two `*_visible` columns changed |
| `V6/shiny_app/R/taxonomy_navigation.R` | `taxonomy_viewer_scope()` returns selectable and forecast-only counts |
| `V6/shiny_app/ui/tabs_v6_16_viewer.R` | Header count, help text, forecast-only callout |
| `V6/shiny_app/www/custom.css` | Callout layout only |
