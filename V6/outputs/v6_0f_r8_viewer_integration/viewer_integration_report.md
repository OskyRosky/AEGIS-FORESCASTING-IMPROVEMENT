# V6.0F-R8 — Viewer Integration Report

## 1. Files touched

| File | Change | Lines | Reason |
|---|---|---:|---|
| `V6/shiny_app/global.R` | modified | +5 | Source the resolver and the Viewer scenario module |
| `V6/shiny_app/ui/body.R` | modified | +1 | Source the new Viewer UI block |
| `V6/shiny_app/ui/tabs.R` | modified | +4 | Insert `viewer_scenario_box()` inside `section_explorer()` |
| `V6/shiny_app/server/server.R` | modified | +4 | Call `viewer_scenario_server()` |
| `V6/shiny_app/ui/tabs_viewer_scenario.R` | **new** | 104 | The cascade UI block |
| `V6/shiny_app/server/viewer_scenario_server.R` | **new** | 221 | The Viewer server logic |

**14 insertions, 0 deletions** across the four modified files. Nothing was removed or rewritten. The legacy backtest boxes, the methodology note and the Assistant panel are byte-identical.

---

## 2. How the Viewer uses the resolver

The module never touches Tesseract, never reads a fact CSV, and never builds SQL by concatenation.

```
UI control  ──▶ get_available_*()      ──▶ ui_metadata/*.csv   (62 KB, eager)
selection   ──▶ resolve_series_query() ──▶ scenario_registry   (status + badge + SQL)
chart       ──▶ fetch_series_preview() ──▶ DuckDB              (read-only, parameterised)
```

`viewer_scenario_server()` defines only reactives and outputs. All physical knowledge — which table, which column, which predicate — lives in `R/scenario_resolver.R`.

---

## 3. How dropdowns load

Populated from four CSV slices totalling **62.4 KB**, read once and cached in the resolver environment. Loading them measured **0.002–0.003 s**. No fact table is opened to populate a control.

| Control | Slice | Rows |
|---|---|---:|
| Metric / Scenario / Granularity | available_scenarios.csv | 8 |
| Key | available_keys.csv | 896 |
| Forecast version | available_versions.csv | 16 |
| Model / Type | available_model_types.csv | 82 |

The Key control uses `server = TRUE` selectize, so the 155 Basilisk keys are filtered server-side rather than shipped to the browser.

---

## 4. How DuckDB is queried

One read-only connection per request, closed on exit:

```r
con <- DBI::dbConnect(duckdb::duckdb(shared_home = FALSE),
                      dbdir = "data/storage/r6_phase1.duckdb", read_only = TRUE)
on.exit(DBI::dbDisconnect(con, shutdown = TRUE), add = TRUE)
```

The predicate is always `key_lower = lower(?)`, which is what makes `namprd07` and `NAMPRD07` resolve to the same series.

Measured on the running app: **1,097 rows in 0.088 s** (HDD forest) and **732 rows in 0.088 s** (SSD-Phoenix).

---

## 5. Chart rules honoured

| Rule | Implementation |
|---|---|
| Actuals survive a model filter | The SQL keeps `series_type = 'actual'` regardless of the model predicate. Verified live: legend shows `Actual` next to the selected model. |
| No zero filling | Rows with a missing date or value are dropped, never replaced. |
| No invented actuals | `Actual` is drawn only from `series_type = 'actual'` rows in the extract. |
| Forecast-only is explicit | SSD-Phoenix renders a single `Forecast` line, an amber badge and a written notice. |
| Markers excluded | `stubbed`, `Extrapolated` and `Fixed_NA` never reach the model selector. |

---

## 6. Two defects found and fixed during integration

**D1 — Outputs never computed.** All eight new outputs stayed permanently in `recalculating`. Root cause: this app hides inactive panels, so Shiny suspends their outputs. The codebase already documents this at `server.R:497` and declares `suspendWhenHidden = FALSE` for every `fvp_*`, `acc_*` and `ttl_*` output. The new outputs now follow the same pattern.

**D2 — `actual` was offered as a selectable model.** `actual` is a *series type*, not a model. It was reaching `available_model_types.csv` through the family classifier. The build now excludes both the `Actual` and `Marker` families, dropping the slice from 88 to 82 rows.

---

## 7. Out of scope for R8

| Item | Reason |
|---|---|
| Forecast page | R9 |
| Accuracy page | R9b |
| Assistant coverage | R9c |
| CPU, IOPS | R6 Phase 2 |
| SSD-MCDB | Blocked by O1 |
| Memory | Out of scope, D1 |
| The other 22 SSD-Phoenix scenarios | Not exposed, D2 |
| Automating the DuckDB rebuild | Risk RB5, still open |
