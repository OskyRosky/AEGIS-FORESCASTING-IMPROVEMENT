# V6.24-P9H — Accuracy UX Parity Study + Integration

**Stage:** V6.24-P9H
**Scope:** a new Accuracy page inside V6.24 MVP, between Viewer and Forecast
**Downloads:** deferred to P9G2 — not implemented, not pretended.
**Shiny remains read-only.** No governed artifact was modified.

---

## 1. What this page is

Accuracy for **the series selected in the Viewer** — the same shared selection
that drives Forecast. It answers *"how did the 15 governed models do on THIS
series?"* with a summary, a model × measure severity heatmap, a per-model table
and an evidence-grounded assistant.

Sidebar order is now **Overview → Viewer → Accuracy → Forecast → Taxonomy**.

---

## 2. The blocking finding, and the owner's ruling

The legacy Accuracy page offers a 5/10/15/20/25/30 horizon selector because its
artifact, `v6_21b_accuracy_metrics.parquet`, carries a `horizon` column.

**The V6.24 artifact does not.** `accuracy_metrics.parquet` is exactly 2,100
rows = 140 series × 15 models, **one row each**, aggregating every horizon 1–30
across the full D2 window (300 target dates, 2022-04-26 → 2023-07-20).

So a horizon filter had no honest implementation: wiring it would show six
identical result sets, and computing per-horizon accuracy from
`model_backtests_15_models` is forbidden (V42,
`BLOCKED_ACCURACY_RECALCULATION`). I stopped and asked rather than pick one.

**Owner ruling:** disclose the window, show the legacy horizons struck through,
do not recalculate, do not block. That is what shipped — the same pattern P9D
used for the unavailable 35/45 backtest horizons.

---

## 3. Two legacy behaviours I deliberately did not copy

**Mean → median.** The legacy heatmap ranks series worst-first by
`mean(metric_value)`. On this cohort the mean is unusable: LinearRegression has
a mean MAE of **5.86e21** against a median of **870**, and the worst-five list
by mean overlaps the median list by only **2 of 5**. P6/P7 already set medians
as the governed aggregate.

**`error_variability` does not exist in V6.24.** The legacy "most stable" card
uses it. V6.24's artifact has no such column, so best and weakest both come from
the selected metric, as the prompt specified.

---

## 4. A degenerate result the first build shipped, and the fix

The first version reported the *most favourable pocket* as
`apcp150 · ARIMA_Fixed` with **MAE 0** — and `apcp150` is one of the 15 all-zero
series. I checked before assuming: **all 195 rows in the cohort with an error of
exactly 0 belong to those 15 no-signal series.** The model predicted zero
against an actual of zero.

That is a degenerate identity, not accuracy, and presenting it as the best
result would have been the same trap P6C found in the ranking tie-break. A
no-signal series now gets **no best model** on either card, with an explicit
"Why no best model" explanation, and the assistant refuses the same claim. The
rows stay visible, badged `no signal`.

---

## 5. Bugs I introduced and caught

**Heatmap module missing.** `type: "heatmap"` resolved through `modules/map.js`
and died in `updateParallelArrays`. highcharter does not ship the heatmap module
by default; fixed with `hc_add_dependency("modules/heatmap.js")`.

**Reserved property collision.** My tooltip used a custom point key named
`series`. `point.series` is the Highcharts series object, so the tooltip would
have rendered `[object Object]`. Renamed to `series_label` — then the redesign
removed it anyway.

**Duplicate output id.** Mounting the shared-selection banner on Accuracy made
Shiny warn that `v24_shared_selection` had two outputs, which leaves one panel
stale. The banner now takes an id.

**Unreadable severity.** An extreme cell produced a severity around 1.9e20 and
the table printed it raw. It now goes through the same formatter as every other
number.

**A brace I deleted.** An edit removed the closing `}` of `v6_24_acc_rows()`.
Caught by the headless probe before the app ever started.

---

## 6. Scope correction from the owner

My first build was a **cohort-wide Top-20/50/100 view across all 140 series**.
That was wrong on two counts: Accuracy belongs **between Viewer and Forecast**,
and it must follow **the Viewer's selection**, not rank the whole cohort.

Rebuilt: the Top-N and scope controls are gone, the page carries the shared
selection banner, and the heatmap axes were transposed from series × models to
**models × measures** — which with one series is the view that actually informs,
since a model can look fine on MAE and poor on WAPE.

---

## 7. Governance

- **0** processed artifacts modified · **0** raw · **0** V1–V5
- Legacy `section_accuracy()` and every `acc_*` helper **untouched**
- No SQL, no model execution, no forecast or backtest regeneration
- **No accuracy recomputed**: the helper never reads `model_backtests_15_models`
- Severity is stamped `VISUALIZATION_ONLY` and never enters a ranking
- No push, no `git add .`

---

## 8. Known caveats

1. **No per-horizon accuracy.** Disclosed, not hidden. Q1.
2. **Screenshots are narrow.** The shared browser panel reported
   `window.innerWidth` of 279px, so element captures look squeezed;
   `setViewportSize` does not affect an IDE-docked window. The chart itself is
   verified correct in the DOM (15 × 7 = 105 cells, colour axis, export menu).
3. **P9F was skipped** and remains unbuilt. Q5.

---

## 9. Next stage

**READY_FOR_P9I_FINAL_VISUAL_QA**, with P9G2 (downloads) and possibly P9F
outstanding. Neither blocks a visual QA pass.

`V6_24_P9H_ACCURACY_PARITY_COMPLETED`
