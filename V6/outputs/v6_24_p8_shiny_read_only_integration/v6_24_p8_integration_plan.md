# V6.24-P8 — Shiny Integration Plan

Written during Phase 0, before any file was modified.

## 1. What the app looks like

The Shiny app is a hand-built dashboard (no `shinydashboard`), 53 files:

| Piece | File | Role |
|---|---|---|
| Entrypoint | `app.R` | sources `global.R`, `ui/header.R`, `ui/body.R`, `server/server.R`, then `shinyApp()` |
| Startup | `global.R` | sources every `R/` provider in order |
| Shell | `ui/body.R` | sources `ui/sidebar.R`, `ui/tabs.R`, `ui/tabs_v6_16_viewer.R`, `ui/footer.R`; defines `app_ui()` |
| Navigation | `ui/sidebar.R` | `stage07_menu()` returns groups of items, each with a `value` used as `data-section` |
| Sections | `ui/tabs.R` | `panel(value, ...)` helper; `app_sections()` composes every `section_*()` |
| Server | `server/server.R` | `app_server()` calls provider servers such as `viewer_pilot_server()` |
| Switching | `www/custom.js` | shows the section whose `data-section` matches the clicked sidebar link |

Providers that must not break: `R/llm_explain.R`, `R/llm_compose.R`,
`R/llm_client.R` (assistant), `R/viewer_pilot.R` and `R/forecast_pilot.R`
(legacy V6.17 pages), and `R/scenario_resolver.R` which exists but is
deliberately unwired.

The structure is legible and consistent, so
`V6_24_P8_BLOCKED_SHINY_STRUCTURE_UNCLEAR` does not apply.

## 2. Chosen approach — isolated module, minimal wiring

There is a clean precedent: `ui/tabs_v6_16_viewer.R` is a separate UI file
sourced by `body.R`, and `viewer_pilot_server()` is a separate server function
called by `app_server()`. **V6.24 follows exactly that precedent** rather than
inventing a new pattern or touching legacy section code.

**Three new files:**

| File | Contents |
|---|---|
| `R/v6_24_read_only_loader.R` | Read-only loader for the eight governed artifacts, with load-time validation; filter-option helpers; caveat severity map; shared tag helpers |
| `ui/tabs_v6_24_mvp.R` | The four V6.24 pages as `panel()` sections |
| `server/v6_24_mvp_server.R` | `v6_24_mvp_server()` — cascading filters, champion suppression, caveats, forecast rendering |

**Six modified files, each a minimal additive edit:**

| File | Edit |
|---|---|
| `global.R` | two `source()` lines |
| `ui/body.R` | one `source()` line |
| `ui/sidebar.R` | one new menu group with four items |
| `ui/tabs.R` | four `section_v24_*()` calls inside `app_sections()` |
| `server/server.R` | one call to `v6_24_mvp_server()` |
| `www/custom.css` | appended a `v24-`-prefixed style block; no existing rule altered |

No legacy section definition, provider or assistant file is touched. Nothing is
deleted. All new CSS class names are `v24-` prefixed so they cannot collide.

## 3. Why the loader is where the architecture is enforced

The rule is that everything is cooked outside Shiny. The loader is the single
place where that is made structural rather than aspirational:

- It only ever **reads**. There is no write call in any V6.24 file, and the
  smoke test scans the source to prove it.
- It **asserts the shape** of every artifact at load: row counts, required
  columns, key uniqueness, `forecast_type`, `forecast_step` domain, ranking
  policy version and champion count. A silent artifact swap fails loudly.
- It asserts `manifest_flag_used_for_readiness = FALSE`, so the stale flag trap
  cannot creep back in.
- It asserts **no mean column exists** in `navigation_contract`, so a tile
  cannot accidentally bind to one.

Parquet is preferred because `arrow` is already a dependency of
`viewer_pilot.R` and `forecast_pilot.R`. CSV is a fallback. **No package is
installed.**

## 4. Where the shared tag helpers live, and why

`v24_card`, `v24_kv`, `v24_badge` and `v24_badges_ui` are defined in the
**loader**, not in the UI file, because the server renders with them too.
`global.R` sources the loader, so they exist regardless of UI/server load order.

This was not the original design — the first version put them in the UI file and
the reactive test caught a `could not find function "v24_card"` failure. In the
running app it happened to work because `app.R` sources `body.R` before
`shinyApp()`, but it was a latent break waiting for any change in load order.

## 5. Contract fields the UI binds to

Nothing is hardcoded. Every behavioural decision reads a field:

| Behaviour | Field |
|---|---|
| Is the series selectable | `viewer_visible` |
| Show the forecast panel | `forecast_visible` |
| Show the champion as a recommendation | `champion_visible` |
| Which caveat badges to render | `caveat_badge` (pipe-separated) |
| Low-confidence warning | `low_confidence_backtest_window_flag` |
| Availability wording | `product_status` |
| Horizon label | `forecast_type`, `forecast_steps` |

There is no list of no-signal series and no `GBRP267` special case anywhere.

## 6. Filter flow

Options at each of the six levels are computed from `navigation_contract` rows
filtered by the levels above. An option is only offered when at least one
operational series sits behind it, so **an empty result is unreachable by
construction** rather than blocked by a guard.

Key is last, never first: 102 distinct keys cover 140 series, so a key alone
does not identify a series.

## 7. How this is verified

Three scripted suites, all run for real:

1. `p8_smoke_loader.R` — loader, filter cascade, every path resolution.
2. `p8_smoke_app.R` — sources the app as `app.R` does, builds the full UI,
   scans the V6.24 source for writes/computation/hardcoded lists, and compares
   artifact checksums before and after.
3. `p8_smoke_server.R` — `shiny::testServer()` against the real server module,
   exercising champion suppression, caveats and forecast rendering with series
   chosen **by field**, not by name.

Plus `p8_launch_check.R`, which boots the app on a local port and requests it
from a separate process — the first attempt deadlocked because the request was
issued from inside the app's own event loop.
