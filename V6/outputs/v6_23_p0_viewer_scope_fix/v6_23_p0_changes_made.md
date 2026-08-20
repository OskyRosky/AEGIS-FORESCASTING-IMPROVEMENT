# V6.23-P0 | Changes made

Four files. No SQL, no model run, no recomputation, no fabricated value.

## 1. `build_v6_18_navigation_contract.py` — the visibility rule

The rule that hid SSD:

```python
"viewer_visible": flag(viewer_row is not None),   # TRUE only if a backtest row exists
```

became:

```python
"viewer_visible": flag(row["series_key"] not in QUARANTINED_ENTITIES),
```

with a new, documented constant:

```python
QUARANTINED_ENTITIES = {"PROD"}
```

`viewer_eligible` was **not** touched. Visibility and eligibility are now
answering the two different questions the schema was designed for.

## 2. `v6_18_navigation_contract.csv` — regenerated

Regenerated from the builder so the artifact stays reproducible, then diffed
column by column against the previous version:

| Check | Result |
|---|---|
| Rows before / after | 901 / 901 |
| Column set identical | Yes |
| **Columns that changed** | **`viewer_visible` only** |
| `viewer_eligible` | Unchanged at 596 |
| `forecast_visible` / `forecast_eligible` | Unchanged at 896 |
| `viewer_visible` after | 894 = 596 HDD + 298 SSD |
| `PROD` viewer_visible | 0 of 2 |

## 3. `R/taxonomy_navigation.R` — derived scope counts

Added `taxonomy_viewer_scope()`, which returns `total`, `backtest`,
`forecast_only`, `routes` and `backtest_routes` from the contract, so the header
can never drift from the data again.

## 4. `R/viewer_pilot.R` — an honest forecast-only state

Previously a resolved route with no backtest fell into a generic amber
*"Backtest not available for this combination."* That is true but uninformative,
and it is the same message shown for a genuinely broken selection.

Added `fvp_forecast_only()` and three distinct states:

| Condition | State | Message |
|---|---|---|
| Backtest exists | Green, "Backtest available" | unchanged |
| Route resolves, no actuals | **Teal, "Forecast-only"** | "No observed actuals or 15-model backtest estimates are available for … Nothing was fabricated. Open the Forecast section …" |
| Anything else | Amber, "Unavailable" | unchanged |

The chart placeholder was given the same treatment, so a forecast-only selection
renders an explicit explanation rather than a blank or misleading panel.

## 5. `ui/tabs_v6_16_viewer.R` — header and help text

* Header pill: `"596 entities / 6 routes"` → `"894 cases / 8 routes"` plus a
  second pill `"596 backtest · 298 forecast-only"`, both derived at runtime.
* Help text: the line *"SSD-Phoenix is forecast-only and is not exposed in
  Viewer"* was false after this change and now describes the real behaviour.

## Deliberately not changed

* `viewer_eligible` — SSD still cannot be backtested, and the artifact says so.
* The model panel still shows all 15 governed models, per the V6.18 owner
  decision that it must never disappear. On a forecast-only route the banner
  states unambiguously that no estimates exist, and Analyze Backtest is disabled.
* The Forecast page. `PROD` is still visible there. See the closure summary.
