# V6.24-P9B — Current V6.24 MVP: UX Gap Notes

What P8 built, what is genuinely good, and where it falls short of Forecasting.

---

## 1. What V6.24 does better, and must not lose

Three things in the new section are **ahead** of the legacy Forecasting, and the
migration must protect them:

**The Overview page.** Forecasting has no landing summary at all — the Viewer
opens straight into Selection. The twelve coverage cards (140 operational, 125
champion visible, 53 available, 87 with caveat, 15 no-signal, 1 low-confidence)
answer "what is in this product?" before the user picks anything. The owner said
plainly he wants this kept and carried into Forecasting.

**No-signal handling.** A series whose every actual is zero stays fully
selectable, its charts draw, and only the *champion recommendation* is replaced
with an explicit message. Legacy has no such concept. This encodes P6C's
correction and P7's `champion_visible` field, and a regression here would silently
undo two stages of work.

**Honest missing values.** A non-computable median renders as *"not computable"*,
never as `0`. Sixteen series have a non-computable median WAPE. Turning those into
zero would make dead series look perfect.

Everything below is a gap. None of it changes these three.

## 2. Selection — the main complaint

`v24_filter_bar()` renders **six dropdowns in one row, always**, with a single
green status line beneath.

It is functionally correct: 140 of 140 complete paths resolve to exactly one
series, and across 177 filter-option rows **zero have zero series**. But it is not
the experience the owner wants, and the specific failures are:

| Legacy | V6.24 today |
|---|---|
| Fields appear as their parent is chosen | All six always visible |
| An inapplicable axis is **absent** | Shows the literal `NOT_APPLICABLE` |
| Breadcrumb chips | One line of text |
| Route metadata card grid | Flat key/value list |
| `OPERATIONAL` badge | `product_status` as one more row |
| Last axis labelled Forest / Region | Always labelled **Key** |
| Long lists get a searchable control | Plain select for 140 keys |

The last-axis label is the sharpest example of a gap that costs almost nothing to
close: `navigation_contract` already carries `key_axis_status` with
`ROUTING_VALUE_REGION` and `IDENTIFIER_VALUE_FOREST`. P7 emitted the field; P8
simply never read it.

There is also a **structural duplication**: the Viewer and Forecast pages each own
an independent copy of the filter flow (`v24_vw_*` and `v24_fc_*`). The user
selects the same series twice. The legacy taxonomy module is already
page-parameterised — `taxonomy_navigation_server(id, page)` — which shows the
shape the V6.24 selection should have had.

## 3. Backtest configuration — essentially absent

There is no configuration card. There is a single `selectInput` listing 15 models
above the chart. Compared with Card B, V6.24 has:

- no horizon selector, though `model_backtests_15_models.horizon_steps` carries
  values 1–30 and the filter is directly feasible;
- no family grouping;
- no champion star on the control;
- no multi-model comparison — **one model at a time**;
- no Analyze / Reset, so every dropdown change re-renders immediately.

The champion *is* handled correctly, in its own block, with suppression. That
logic is right; it just needs to move into a proper card.

## 4. Charts — the wrong library

Three plotly outputs: `v24_vw_actuals`, `v24_vw_backtest`, `v24_fc_chart`.

This was my error in P8, and it was not a judgement call: `R/libraries.R` line 11
already declares `library(highcharter)` with the comment *"interactive forecast
charting (Forecast Viewer)"*. The convention existed and I broke it.

Concretely, the plotly charts lack: title and contextual subtitle, crosshairs,
click-to-toggle legend, an export menu, rich per-series tooltips carrying family
and risk, a stable family-ordered palette, and a calm empty state.

There is also a symptom worth noting. `ui/tabs_v6_24_mvp.R` contains
`v24_resize_hook()` — a JavaScript listener that fires `window.resize` when a
V6.24 sidebar link is clicked, purely because a plotly widget built inside a
`display:none` container measures zero width. Highcharts reflows more reliably, so
this hook is likely removable in P9E. It should be verified, not assumed.

## 5. Forecast page

The horizon disclosure is **better** than legacy: a persistent banner naming
`GOVERNED_30_STEP_DAILY_FORECAST` on all four pages, and no page anywhere renders
"4-year" or "1,440".

What is missing: Highcharts, a boundary marker between observed history and
forecast, family grouping in the model selector, and any export.

One subtlety to preserve: the backtest horizon (1–30, a control) and the forward
horizon (fixed 30, a fact) are **different things**. The forward horizon is the
proven capability of the governed models, not a user preference, and it must not
become a slider.

## 6. Caveats — right substance, wrong volume

Eleven codes render as coloured chips driven entirely by `caveat_badge`. Nothing
is hardcoded, which is exactly right.

The problem is tone. Both `NO_SIGNAL` and `CHAMPION_NOT_MEANINGFUL` map to `high`
severity and render red. **87 of 140 series carry at least one badge**, and a
perfectly healthy series showing two red chips reads as broken. The information
should stay; the visual weight should be re-graded.

`STALE_MANIFEST_FLAG_IGNORED` applies to all 140 series and is a governance note.
It does not belong in the product view at all.

## 7. Technical debt

**Presentation helpers live in the data loader.** `v24_card`, `v24_kv`,
`v24_badge`, `v24_badges_ui` and `v24_table` sit in
`R/v6_24_read_only_loader.R`. They were moved there during P8 because the server
renders with them and the UI file is sourced on a different path — a real bug that
`shiny::testServer` caught. The fix was correct; the location is not. They belong
in `R/v6_24_ui_helpers.R`, sourced from `global.R` alongside the loader.

**Thirty-three `outputOptions(suspendWhenHidden = FALSE)` calls** in a loop at the
end of the server module. This is necessary and correct — but the legacy code
already did it at `taxonomy_navigation.R` line 532. Following the existing pattern
would have saved discovering it through a blank page.

**Two parallel visual languages.** `v24-` classes were written from scratch rather
than reusing `fvx-` / `fvb-` / `fvtn-`. There is no collision risk, but the
spacing, card and typography scales differ, which is precisely why the section
reads as a separate product.

## 8. Honest summary

P8 delivered a **correct** section, and correctness was the right goal for that
stage: readiness derived from artifacts rather than the stale flag, champion
suppression driven by a field, zero empty filter options, artifacts byte-identical.

What it did not deliver is a section that feels like the same product. The gap is
almost entirely presentational — the data layer underneath is sound and needs no
change. That is the good news for P9C onward: **every gap in this document can be
closed without touching a single governed artifact.**
