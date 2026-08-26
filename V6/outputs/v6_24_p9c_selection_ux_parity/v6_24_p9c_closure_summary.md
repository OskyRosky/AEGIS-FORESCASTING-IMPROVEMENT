# V6.24-P9C — Selection UX Parity — Closure Summary

**Status: COMPLETE. Validation 43 PASS / 0 FAIL. Verified in a real browser, not
only headlessly.**

**Verdict: `READY_FOR_P9D_BACKTEST_CONFIGURATION_PARITY`.**

---

## 1. What changed

The flat six-dropdown bar is gone. The V6.24 selection is now a guided
two-column navigator: a rail that asks one question at a time on the left, and a
route panel that answers continuously on the right.

| Before (P8) | After (P9C) |
|---|---|
| Six dropdowns, always visible | Only the axes that apply, revealed as their parent is chosen |
| Inapplicable axis shown as `NOT_APPLICABLE` | Shown as a muted context line: *"does not apply to this route"* |
| Final axis always labelled **Key** | Labelled **Forest**, **Region** or **Forest / SKU** from `key_axis_status` |
| One line of green text | Breadcrumb chips + status badge + 12-cell route card grid |
| Two independent filter bars | **One shared selection** driving Viewer and Forecast |
| Champion suppression only in a panel | Plus a context note in the route panel |

## 2. Files

**One new file, four modified. No legacy Forecasting file was touched.**

| File | Change |
|---|---|
| `R/v6_24_selection_helpers.R` | **NEW** — progressive axis resolution, dynamic label, breadcrumb, route cards, context notes |
| `ui/tabs_v6_24_mvp.R` | selection card replaces the filter bar; shared-selection mirror added |
| `server/v6_24_mvp_server.R` | one shared progressive selection with explicit state |
| `www/custom.css` | appended `v24-` navigator styles |
| `global.R` | one `source()` line |

## 3. How progressive disclosure actually works

`v6_24_selection_plan()` resolves each axis into one of three states:

- **CHOICE** — more than one real value remains, so ask.
- **CONTEXT** — exactly one value remains, so state it and move on.
- **LOCKED** — a parent is unchosen, so do not render it at all.

That third state is what the legacy Forecasting does and P8 did not: an axis that
cannot help you is **absent**, not sitting there holding the word
`NOT_APPLICABLE`.

Observed in the browser, the scope narrows honestly as you go:
**140 → 50 → 17 → 9 → resolved**.

## 4. State is explicit, so reset is deterministic

The server holds `sel` as `reactiveValues` rather than reading values back from
the inputs. Choosing an axis clears **every** axis below it in one place.

This matters: with re-derived options alone, a stale downstream value can survive
because its control happens to re-render with the old selection still in range.
Switching Metric from HDD to CPU now provably clears the previously chosen
Forest — check `T15`.

## 5. Dynamic labels

`key_axis_status` was emitted by P7 and simply never read by P8. Now:

| `key_axis_status` | Label |
|---|---|
| `ROUTING_VALUE_REGION` | Region |
| `IDENTIFIER_VALUE_FOREST` | Forest |
| `COMPOSITE_TOKEN_FOREST_SKU` | Forest / SKU |
| mixed, before granularity is chosen | Operational Key |

Verified for HDD Forest, HDD Region, SSD, CPU and IOPS, and confirmed in the
browser: after choosing Granularity = Forest, the final control is titled
**FOREST**.

The fallback only appears while granularity is still mixed, and it is neutral
rather than wrong.

## 6. Shared selection

One `selected_series()` reactive drives both pages. The Viewer owns the selector;
the Forecast page shows a read-only mirror with the same breadcrumb and a line
telling the user where to change it.

This follows the prompt exactly — *"Forecast may still have its own model
selector later, but not its own independent operational series selector."* Two
synchronised selectors would risk update loops for no product gain. Recorded as
open question Q1 in case it feels awkward in use.

## 7. Nothing is hardcoded

Every behaviour reads a field. Source scans confirm:

- no series identifier literal anywhere (`S2`, `S3`)
- no `route_path` positional parsing (`S1`) — which matters, because SSD carries
  `Phoenix` in the slot where HDD carries `Organic`
- no write call (`S4`), no SQL (`S5`)
- `demand_nature` is **read** from `actuals_normalized`, not typed in, so it stays
  true if the cohort ever stops being uniformly Organic

## 8. Two test bugs I found and fixed

Both were in my own validation, not the product:

- A regex to detect `route_path` parsing used `.` across the concatenated source.
  R's TRE lets `.` match newlines, so a comment on line 7 linked to a `vals[[1]]`
  far below and reported a violation that did not exist. Fixed by scanning line
  by line.
- A test asserted Scenario would show as context immediately after choosing
  Metric = HDD. It does not, and should not — DB Type has not been chosen yet, so
  everything below it is correctly LOCKED. The test expectation was wrong, not
  the behaviour.

## 9. Browser-real validation

The lesson from P8 is now enforced: **13 browser checks**, walking the full path
and reading rendered values rather than markup. Five screenshots recorded in the
manifest.

The legacy Forecasting section was re-opened afterwards and still renders its
Selection card, its *596 Viewer-complete cases / 6 routes* pill and its Backtest
Configuration.

## 10. What was deliberately NOT changed

Charts are still Plotly and still re-render on every change. There is no horizon
selector, no model family grouping, no champion star on a control, no
Analyze/Reset, no assistant and no downloads.

All of that is P9D through P9G. Fixing any of it here would have mixed two stages,
which rule 6 forbids and rule 7 makes unverifiable.

## 11. Known caveats

- The Forecast page cannot change the selection; it mirrors the Viewer (Q1).
- The final-axis fallback reads *Operational Key* before granularity is chosen (Q4).
- Card spacing and typography still differ from the legacy `fvx-`/`fvb-` scale;
  that convergence is P9H.

---

**V6_24_P9C_SELECTION_UX_PARITY_COMPLETED**
