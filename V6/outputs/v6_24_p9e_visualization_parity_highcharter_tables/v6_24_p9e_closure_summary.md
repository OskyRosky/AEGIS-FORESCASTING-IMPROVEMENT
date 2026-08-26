# V6.24-P9E — Visualization Parity: Highcharter Charts + Product Tables

**Stage:** V6.24-P9E
**Scope:** every V6.24 MVP chart and table
**Shiny remains read-only.** No governed artifact was modified.

---

## 1. What P9E was asked to do

Not "migrate the backtest chart". Make **all** V6.24 visual output look like one
product with the legacy Forecasting section:

- every V6.24 chart on Highcharter, not Plotly
- lines, not point clouds
- actual and forecast in **different colours** on the same time axis
- tables on the application's real table library, not hand-rolled HTML

All four are done.

---

## 2. What changed

### Charts — 3 of 3 migrated

| Chart | Before | After |
|---|---|---|
| Observed history | Plotly line | Highcharter line, markers off (562 points) |
| Backtest comparison | **Plotly markers-only** | Highcharter: actual line + one line per model |
| Forecast | Plotly lines+markers | Highcharter: blue actual line, green dashed forecast, `Forecast start` boundary |

The backtest chart was the worst offender: it drew `mode = "markers"` for the
actual *and* every model, so the comparison read as a scatter cloud. It is now
seven line series with a heavier navy actual on top.

Every chart carries an interactive legend, an export menu, a contextual
subtitle (key · horizon · model count · date range) and a per-series tooltip.

### Tables — 8 of 8 migrated

`v24_table()` produced a plain `<table class="v24-tbl">`. All eight V6.24 tables
now go through `v6_24_dt()`, a DT wrapper whose options mirror the legacy
tables (`stripe hover row-border`, `dom = "ftip"`, `scrollX`).

Two tables also gained content:

- **Model ranking** — added `Family` (from the P9D display map) and `SMAPE`.
  The champion cell is a badge and is still gated on `champion_visible`: a
  suppressed series reads `technical only`, never `champion`.
- **Forecast rows** — added `Model`; negative and extreme are badges, and the
  underlying values remain exactly as the model produced them.

### Forecast champion default

`v24_fc_champion_note` now states, in words, which of the three cases applies:
showing the champion, inspecting a non-champion, or *no model can be presented
as a winner*. This is the P9F specification's foundation, not P9F itself — the
executive layout is still P9F's job.

---

## 3. A real defect found and fixed

The migration exposed a **date bug that predates P9E**.

`series_date`, `target_date` and `forecast_date` are stored as midnight-UTC
timestamps. R reads them as `POSIXct`, and `as.character()` renders them in the
**server's local zone**. On a UTC-6 machine the governed `2022-04-30` printed as
`2022-04-29 18:00:00` — a governed date shown one day early.

It was visible in three places: the P9D backtest note, the backtest availability
range, and the **Forecast rows table**, where every one of the 30 forecast dates
was off by a day.

I only caught it because the new chart (which uses `as.Date`, UTC by default)
disagreed with the note beside it. All V6.24 date rendering now goes through
`v6_24_as_date()`, and the chart, the table and the note agree:
`2022-04-30 → 2023-06-25`, and forecast step 1 = `2023-07-21`, matching
`navigation_contract.forecast_start_date` exactly.

---

## 4. One of my own checks was wrong

My first probe reported the ranking table had **0 rows**. It had 15.

DataTables with `scrollX` splits a table into a header-only clone plus the real
body table. `querySelector('table.dataTable')` returned the clone. The table was
correct; my selector was not. Corrected to read `.dataTables_scrollBody`.

Worth recording because it is the same failure mode as P8: a check that looks
authoritative and measures the wrong node.

---

## 5. htmlwidgets in hidden sections — resolved, not worked around

P8 hit `lazyRender` errors when DT rendered inside a hidden section. I expected
that risk to return.

It did not. htmlwidgets **defers** rendering while its container is hidden and
completes it on the visibility change; `www/custom.js` already fires a resize on
section switch. Measured: 0 JS console errors, and Overview/Taxonomy/Forecast
tables render on first visit (4 / 5 / 10 / 4 / 9 / 15 rows). No legacy file was
changed to achieve this.

---

## 6. Governance

- **0** processed artifacts modified
- **0** raw artifacts modified
- **0** legacy files modified — `R/helpers.R`, `ui/tabs.R`, `server/server.R`,
  `www/custom.js` all untouched
- Plotly **retained** in `R/libraries.R`: 14 legacy usages still need it.
  P9E only guarantees V6.24 charts are Highcharter.
- No SQL, no model execution, no forecast regeneration, no accuracy or ranking
  recalculation, no assistant, no downloads, no push

Legacy Forecasting was re-checked in the browser after the change: section
activates, its Highcharts chart renders.

---

## 7. What is deliberately not done

- **Forecast executive layout** — champion-first framing is specified and the
  default is correct, but the layout redesign is **P9F**
- **Assistant / downloads** — P9G
- **Visual polish pass** — P9H
- **Legacy Plotly** — stays until the legacy section itself is retired

---

## 8. Known caveats

1. **The backtest line is sparse by design.** Horizon equality at h=5 yields ~10
   target dates across 14 months. That is the D2 rolling-origin design, not a
   gap. Raised as Q1.
2. **Fifteen MVP series are entirely zero.** Their charts are flat lines at 0.
   That is honest; the champion is suppressed and no winner is claimed.
3. **The display family map remains display-only**, unchanged from P9D.

---

## 9. Next stage

**READY_FOR_P9F_FORECAST_POLISH.**

P9F should make Forecast executive: lead with the champion, demote the model
picker to inspection, and surface accuracy context for the chosen model. The
data contract and the champion gate it needs are already in place.

`V6_24_P9E_VISUALIZATION_PARITY_HIGHCHARTER_TABLES_COMPLETED`
