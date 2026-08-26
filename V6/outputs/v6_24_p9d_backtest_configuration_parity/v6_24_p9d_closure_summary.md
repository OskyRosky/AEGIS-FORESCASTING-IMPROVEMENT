# V6.24-P9D — Backtest Configuration Parity — Closure Summary

**Status: COMPLETE. Validation 48 PASS / 0 FAIL, plus a 59-check reactive suite.
Verified in a real browser.**

**Verdict: `READY_FOR_P9E_HIGHCHARTS_BACKTEST_RESULTS`.**

---

## 1. What changed

The bare model dropdown is gone. Card B now mirrors the legacy Backtest
Configuration block.

| Before (P9C) | After (P9D) |
|---|---|
| No availability signal | Green **Backtest available** banner with the row and model count |
| No horizon control | Radios 5/10/15/20/25/30, with **35 and 45 struck through** and the note *"Prepared artifact covers 1-30 day horizons."* |
| No history control | History window select |
| One flat dropdown, one model at a time | **Four family groups**, multi-select, 15 models |
| No champion indicator | **★ champion** beside the champion, only when it may be presented |
| Redrew on every change | **Analyze Backtest** commits; **Reset Selection** restores defaults |
| No feedback on what was analysed | *"Analysed: 5 models at horizon 5 days · 19:32:03"* |

## 2. Files

**One new file, four modified. No legacy Forecasting file touched.**

| File | Change |
|---|---|
| `R/v6_24_backtest_config_helpers.R` | **NEW** — model list, family map, availability, horizons, champion, defaults, row filtering |
| `ui/tabs_v6_24_mvp.R` | Card B added; Results became Card C |
| `server/v6_24_mvp_server.R` | pending vs applied configuration |
| `www/custom.css` | Card B styles |
| `global.R` | one `source()` line |

## 3. The family map — the one real obstacle

The governed artifacts carry a **three**-value `model_family` (Baseline 7 /
Challenger 5 / Neural 3). The product displays **four** families. The two
partitions **cut across each other**:

- `ETS Explicit` is a *Challenger* but displays under **Statistical**
- `LinearRegression` is a *Baseline* but displays under **Machine Learning**

So the four-family split **cannot** be derived from `accuracy_metrics`.

It is taken from `forecast_viewer_model_outputs.csv`, the legacy display source,
which classifies the **identical 15 model names**. Validated: 15 mapped, 0
missing, 0 extra, each model exactly once, counts 4/5/3/3, and the embedded map
re-checked against the source at runtime.

The map is stamped `DISPLAY_GROUPING_ONLY` and is never used for rankings,
accuracy, forecast generation, champion selection or any governance decision.

That 49 MB file is not parsed at startup — the validated result is embedded, and
`v6_24_validate_family_map()` re-verifies it on demand.

## 4. A caveat is not missing data

This was worth being careful about. `NO_SIGNAL` and
`LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO` describe *interpretation*, not
*availability*. Both were verified to report **Backtest available** with their
full prepared rows, and the browser confirmed the green banner on a no-signal
series.

Only a series with genuinely no rows reports unavailable, and only then is
Analyze disabled.

## 5. Champion star

Driven entirely by `navigation_contract.champion_visible`:

- **Signal-present**: `FixedGrowth_1_5 ★ champion` in the Growth Baseline group,
  plus *"Champion for this series is FixedGrowth_1_5, ranked by wape."*
- **No-signal**: **no star in any of the four groups**, and a soft amber note —
  *"Champion is not meaningful for this no-signal series."*

No series name and no model name is hardcoded as a special case.

## 6. Defaults

Six models for a signal-present series — champion, `ETS Explicit`,
`FixedGrowth_3`, `LightGBM`, `XGBoost`, `SMLP-TCN`. Five when no champion may be
presented, led by `ETS Explicit` as the governance reference.

Never all fifteen: the palette that P9E will inherit holds thirteen colours, and
fifteen lines would be unreadable.

## 7. Analyze commits, it does not react

Configuration changes update **pending** state. The results panel reads
**applied** state, which advances only on the Analyze click. Changing the series
clears any previous analysis, so nothing stale survives a selection change.

`applied_cfg()` exposes `series`, `models`, `horizon` and a timestamp — this is
exactly what P9E needs to build the Highcharts comparison.

## 8. Horizon semantics

The horizon filters `model_backtests_15_models.horizon_steps` by **equality**,
matching the legacy `fvp_forecast_series`. The legacy chart compares models at one
horizon; a cumulative `<=` filter would mix step-1 and step-30 predictions on the
same line and make the comparison unreadable. Recorded as Q1 in case you prefer
the alternative — it is a one-line change in P9E.

## 9. Two things I fixed rather than left

**A Shiny ID collision.** `uiOutput("v24_bt_horizon")` rendered a
`radioButtons("v24_bt_horizon", ...)`, and Shiny warned that one ID served both an
input and an output. It worked, but it is exactly the kind of latent fragility
that breaks later. The output is now `v24_bt_horizon_ui`.

**A wrong test expectation, not a wrong product.** A check asserted that
no-signal defaults must not lead with the champion model name. It failed —
because P6C's tie-break crowns `ETS Explicit` for all 15 no-signal series, and
`ETS Explicit` is also the governance reference. The names coincide **by design**.
The real invariant is that no star is drawn and nothing is labelled a winner, and
that holds. The test now asserts that instead.

## 10. What was deliberately NOT changed

The backtest chart is **still Plotly**. It now reads the applied configuration
and draws multiple models, but migrating it to Highcharts is P9E and was not
started. No assistant, no downloads, no Forecast page change.

The Forecast champion-first decision is documented in
`v6_24_p9d_forecast_champion_default_note.md` for P9F, and implemented nowhere.

---

**V6_24_P9D_BACKTEST_CONFIGURATION_PARITY_COMPLETED**
