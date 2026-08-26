# V6.24-P9B — Forecasting → V6.24 Parity Map

Twenty-seven elements. The CSV carries the full detail; this is the narrative.

**Legend** — `AHEAD`: V6.24 is already better. `GAP`: V6.24 must catch up.
`EQUAL`: no material difference.

---

## Summary

| # | Element | Verdict | Stage |
|---|---|---|---|
| E01 | Sidebar navigation | EQUAL | P9H |
| E02 | Overview / landing summary | **AHEAD** | P9H |
| E03 | Selection card | **GAP** | P9C |
| E04 | Progressive filter disclosure | **GAP** | P9C |
| E05 | Breadcrumb / route cards | **GAP** | P9C |
| E06 | Dynamic axis labels | **GAP** | P9C |
| E07 | Route status card | **GAP** | P9C |
| E08 | Forecast-only messaging | EQUAL (no such population) | P9C |
| E09 | Backtest configuration card | **GAP** | P9D |
| E10 | Horizon selector | **GAP** | P9D |
| E11 | Model family grouping | **GAP** | P9D |
| E12 | Champion star | **GAP** | P9D |
| E13 | Analyze Backtest button | **GAP** | P9D |
| E14 | Reset Selection button | **GAP** | P9D |
| E15 | Backtest results chart | **GAP** | P9E |
| E16 | Highcharts legend / export | **GAP** | P9E |
| E17 | Download analysis | **GAP** | P9G |
| E18 | Forecast chart | **GAP** | P9F |
| E19 | Forecast model selector | **GAP** | P9F |
| E20 | Forecast horizon label | **AHEAD** | P9F |
| E21 | Caveat badges | **AHEAD** but too loud | P9H |
| E22 | No-signal handling | **AHEAD** | P9C |
| E23 | Low-confidence handling | **AHEAD** | P9D |
| E24 | Accuracy / ranking summary | GAP, deferred | post-P9H |
| E25 | Taxonomy / availability page | **AHEAD** | P9H |
| E26 | LLM Assistant | **GAP** | P9G |
| E27 | Governance / read-only | **AHEAD** | every stage |

**Six elements where V6.24 leads. Eighteen gaps. Three deferred or equal.**

---

## The gaps that matter most

### Selection (E03–E07) — P9C

The single largest complaint. Legacy asks one question at a time and answers
continuously in a route panel; V6.24 asks six questions at once and answers in one
line.

Everything needed is already in `navigation_contract`. Nothing must be computed
and nothing invented:

| Need | Field |
|---|---|
| Which axes apply | the six axis columns, with `NOT_APPLICABLE` / `UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE` already explicit |
| Breadcrumb | `filter_level_1..6` |
| Route cards | `route_path`, `route_display_label`, `granularity`, `key_axis_status` |
| Status badge | `product_status` |
| Last-axis label | `key_axis_status` |
| Uniqueness | `valid_filter_path` — 140 distinct for 140 series |

**The one thing not to copy**: legacy has a *Demand Nature* axis. V6.24 has no
equivalent — `demand_nature` is constant `Organic` across all 140 series in both
`cohort_manifest` and `actuals_normalized`. It cannot discriminate. And
`route_path` is **not positionally uniform** — SSD routes carry `Phoenix` in the
slot where HDD carries `Organic` — so parsing it by index to synthesise an axis
would produce a wrong control. Show demand nature as route context, never as a
filter.

### Backtest configuration (E09–E14) — P9D

Feasible today. `model_backtests_15_models.horizon_steps` carries 1–30 with the
same semantics as legacy `horizon_days`, so the 5/10/15/20/25/30 radios transfer
directly.

**One real mismatch.** Legacy groups models into four display families; the V6.24
artifact carries only three coarse ones:

| Legacy display family | Models | V6.24 `model_family` |
|---|---|---|
| Growth Baseline | FixedGrowth_1_5, _3, _4, _6 | Baseline |
| Statistical | ARIMA_Fixed, AutoARIMA, ETS Explicit, ETS_Current, Theta | Baseline ×3 / Challenger ×2 |
| Machine Learning | LightGBM, LinearRegression, XGBoost | Challenger ×2 / Baseline ×1 |
| Deep Learning | FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN | Neural |

The two partitions cut across each other, so the four-family display **cannot** be
derived from `accuracy_metrics.model_family`. It can be taken from
`forecast_viewer_model_outputs.csv`, which already classifies the **identical 15
model names** into the four families. That is reuse of an existing governed
classification, not invention — and it is the recommended route.

Two V6.24-only rules must ride along: the champion star is gated on
`champion_visible` so no-signal series show none, and the Reset default must not
select a suppressed champion.

### Charts (E15, E16, E18) — P9E and P9F

`fvp_chart()` and `fvf_chart()` are complete reference implementations. Only the
two data accessors change:

```
fvp_actual_series(series, ...)          ->  actuals_normalized
fvp_forecast_series(series, model, h)   ->  model_backtests_15_models
                                             filtered on horizon_steps
fvf_forecast_series(series, ...)        ->  forecast_outputs
```

Title, subtitle, palette, tooltip, axis and legend configuration port verbatim.
The export menu and interactive legend — both explicit owner requests — come free
with `hc_exporting(enabled = TRUE)` and `hc_legend(enabled = TRUE)`.

### Assistant (E26) — P9G

`llm_explain_ui` and `llm_explain_server` are fully parameterised and reusable
as-is. The four default quick prompts already match the owner's screenshot.

**The design point that must be decided before building**: `llm_explain_get(page_id)`
returns a response keyed by *page*, not by selection. Mounted naively, a V6.24
assistant would answer about the section while appearing to answer about the
selected series. That is worse than having no assistant. Either build a
selection-aware evidence pack over the governed artifacts, or state plainly that
the explanation is section-level.

### Downloads (E17) — P9G

Two patterns exist and the right answer combines them: the **format modal** from
`artifact_export.R`, and the **filtered-rows** approach from
`fvp_pilot_download_rows()`. V6.24 should export the visible selection — actuals,
backtests, forecast rows, rankings and the contract row — as CSV first.

---

## What V6.24 must not lose

Six elements where the new section already leads. Each stage should re-verify
them:

1. **Overview coverage cards** — the owner asked for these explicitly.
2. **No-signal champion suppression** — encodes P6C and P7; regression here is the
   highest-severity risk in the register.
3. **Low-confidence backtest-window flag** — derived, never hardcoded.
4. **Persistent 30-step horizon disclosure** — the misrepresentation P6 blocked.
5. **Caveat transparency** — keep all eleven codes; only re-grade the palette.
6. **Read-only governance** — 35 load-time validations and byte-identical
   artifacts.

---

## One line summary

**The data layer is sound and needs no change. Every one of the eighteen gaps is
presentational, and every field required to close them already exists in the
governed artifacts.**
