# V6.24-P9B — Staged Implementation Plan

Seven stages from here to handoff. One area per stage, validated before the next.

**Ordering note.** The two owner documents disagreed on P9D/P9E. This plan uses
**P9D = Backtest Configuration, P9E = Highcharts Results**, because the chart
consumes the horizon and model selection — building it first would mean rebuilding
it. This is recorded as open question Q1 and should be confirmed before P9C closes.

---

## Files that are never touched

Every stage below inherits this list:

```
R/viewer_pilot.R          R/forecast_pilot.R      R/taxonomy_navigation.R
R/helpers.R               R/llm_explain.R         R/llm_compose.R
R/artifact_export.R       R/data_loader.R         R/libraries.R
ui/tabs_v6_16_viewer.R    ui/tabs.R (beyond the 4 existing section calls)
every file under V6/data/processed and V6/data/raw
V1 through V5
```

The work happens in three V6.24 files plus one new helpers file.

---

## P9C — Selection UX Parity

**Purpose.** Replace the flat six-dropdown bar with the guided navigator.

**Changes.** Two-column layout: rail of progressive fields on the left, route
panel on the right. Render an axis only when it discriminates; collapse a
single-value conditional axis to a read-only context chip. Breadcrumb chips from
`filter_level_1..6`. Status badge from `product_status`. Route metadata cards.
Last-axis label from `key_axis_status`. Searchable control for the 140-key list.
**Share one selection between Viewer and Forecast.** Split presentation helpers
out of the loader into `R/v6_24_ui_helpers.R`.

**Files.** `ui/tabs_v6_24_mvp.R`, `server/v6_24_mvp_server.R`, `www/custom.css`,
new `R/v6_24_ui_helpers.R`, one source line in `global.R`.

**Validation.** 140/140 complete paths resolve to exactly one series. Zero empty
options across all axes. Key is never first. Zero no-signal series gain a
champion. Artifacts byte-identical. **Verified in a real browser, reading values.**

**Risk** MEDIUM · **Screenshots** required · Token
`V6_24_P9C_SELECTION_UX_PARITY_COMPLETED`

---

## P9D — Backtest Configuration Parity

**Purpose.** Rebuild Card B.

**Changes.** Horizon radios 5/10/15/20/25/30 filtering
`model_backtests_15_models.horizon_steps`; disabled chips for anything the
artifact does not cover. Four family checkbox groups. Champion star gated on
`champion_visible`. Live model count. **Analyze Backtest** commits; **Reset**
restores defaults (champion when visible, plus ETS Explicit and a few
comparators).

**The family question.** V6.24 carries three coarse families; the legacy display
uses four, and the two partitions cut across each other. Take the four-family
classification from `forecast_viewer_model_outputs.csv`, which already classifies
the identical 15 model names. Document the map explicitly — do not infer it at
runtime.

**Files.** `ui/tabs_v6_24_mvp.R`, `server/v6_24_mvp_server.R`, `www/custom.css`,
`R/v6_24_ui_helpers.R`.

**Validation.** All 15 models appear exactly once across four groups. Horizon 5
returns only `horizon_steps == 5`. Zero stars on the 15 no-signal series. No
accuracy recomputed. Artifacts byte-identical.

**Risk** MEDIUM · **Screenshots** required · Token
`V6_24_P9D_BACKTEST_CONFIGURATION_PARITY_COMPLETED`

---

## P9E — Highcharts Backtest Results

**Purpose.** Replace the Plotly backtest chart.

**Changes.** Port `fvp_chart()`: title, contextual subtitle, datetime axis with
crosshair, reserved-blue actual line, one line per selected model, `.fvp_palette`,
per-series tooltips, interactive legend, export menu, calm empty state. Add the
notes panel beneath. Test whether `v24_resize_hook()` can be removed — remove it
only if the charts still draw.

**Files.** `server/v6_24_mvp_server.R`, `ui/tabs_v6_24_mvp.R`,
`R/v6_24_ui_helpers.R`.

**Validation.** Chart plots only artifact rows. Legend toggles series. Export menu
present. No `plotly::` call remains in the Viewer. Artifacts byte-identical.
Verified in a browser.

**Risk** MEDIUM · **Screenshots** required · Token
`V6_24_P9E_HIGHCHARTS_BACKTEST_RESULTS_COMPLETED`

---

## P9F — Forecast Page Highcharts

**Purpose.** Move the Forecast page to Highcharts.

**Changes.** Port `fvf_chart()` with a boundary marker at `train_end_date`.
Grouped model selector defaulting to champion, or ETS Explicit when suppressed.
Keep the 30-step banner. Preserve negative and extreme flags without clipping.

**Keep separate**: the backtest horizon is a control (1–30); the forward horizon
is a fixed fact (30). The forward horizon must never become a slider.

**Files.** `server/v6_24_mvp_server.R`, `ui/tabs_v6_24_mvp.R`,
`R/v6_24_ui_helpers.R`.

**Validation.** Exactly 30 forward points. All 15 governed models selectable, no
legacy names. No page renders "4-year", "1,440" or "1440". Zero Plotly anywhere.
Artifacts byte-identical.

**Risk** MEDIUM · **Screenshots** required · Token
`V6_24_P9F_FORECAST_PAGE_HIGHCHARTS_COMPLETED`

---

## P9G — Assistant + Download Integration

**Purpose.** Mount the assistant and add download of the visible selection.

**Changes.** `llm_explain_ui`/`llm_explain_server` on the V6.24 Viewer and
Forecast with the four default quick prompts. A V6.24 evidence pack built from the
selected row (see the assistant notes — this is the one real design decision).
Download actuals, backtests, forecasts, rankings and the contract row as CSV,
reusing the format modal.

**Files.** `ui/tabs_v6_24_mvp.R`, `server/v6_24_mvp_server.R`, two registration
lines in `server/server.R`, `R/v6_24_ui_helpers.R`.

**Validation.** Assistant computes nothing and invents nothing. A suppressed
champion is never presented as a recommendation. Downloaded rows match the visible
selection exactly — forecast download is exactly 30 rows, ranking exactly 15. The
local-mock disclosure is present. Artifacts byte-identical.

**Risk** MEDIUM · **Screenshots** required · Token
`V6_24_P9G_ASSISTANT_DOWNLOAD_INTEGRATION_COMPLETED`

---

## P9H — Visual QA Final

**Purpose.** Walk the product, compare side by side, fix only cosmetics.

**Changes.** Card hierarchy on Overview and the token that wraps as
`GOVERNED_30_STE...`. Spacing and typography aligned to the `fvx-`/`fvb-` scale.
Caveat palette re-graded so informational badges stop reading as errors. Loader
table behind a technical toggle. Legacy versus V6.24 made explicit in the sidebar.

**Files.** `www/custom.css` and minor UI polish only. **No server logic.**

**Validation.** Side-by-side screenshots. Every P9C–P9G validation still passes.
No behaviour change.

**Risk** LOW · **Screenshots** required · Token
`V6_24_P9H_VISUAL_QA_FINAL_COMPLETED`

---

## P10 — Final Handoff

Documentation only, and only once P9H accepts the experience.

---

## Rules that apply to every stage

1. Forecasting is not removed.
2. One area per stage.
3. Highcharts for final charts; no Plotly.
4. Governed artifacts are the only data source.
5. Shiny computes nothing.
6. Nothing hardcoded — no series lists, no `GBRP267`.
7. Technical **and visual** validation. A headless pass is not a pass.
8. Each stage closes with: what changed, what was validated, what remains.
