# V6.24-P9B — Existing Forecasting: Interaction Notes

How the Forecasting section actually behaves, read from the source. This is the
UX reference V6.24 must grow into.

---

## 1. The shape of a Forecasting page

Both `section_explorer()` (Viewer) and `section_forecast()` (Forecast) follow the
same three-card rhythm, and that rhythm is the thing to copy:

```
section_head(title, purpose)
home_collapse("How to use this viewer", ...)      collapsed by default
  A  Selection                 <- guided navigator + live route context
  B  Backtest Configuration    <- horizon, models, Analyze / Reset
  C  Results                   <- Highcharts + download + notes
llm_explain_ui(...)            <- assistant closes the section
```

Each card carries a **kicker letter** (`A`, `B`, `C`), a title, and a **pill** with
a live count — `596 Viewer-complete cases / 6 routes`, `15 verified models`. The
counts come from the contract, never from a literal.

The help block is a *collapse*, closed by default. The page does not lecture the
user before they have seen anything.

## 2. Selection is a two-column navigator, not a row of dropdowns

`taxonomy_navigation_ui(id)` builds:

- **`.fvtn-rail`** on the left — the title "Selection" and `uiOutput("controls")`,
  which renders only the fields that apply.
- **`.fvtn-route-panel`** on the right — `breadcrumb`, `route_state`,
  `route_metadata`.

The left side asks; the right side answers, continuously, as you choose.

### The conditional axis chain

`taxonomy_route_context()` walks a branch-specific chain and narrows the candidate
rows at each step. The `axis()` closure returns `""` when a level has not been
chosen yet, and the function returns early — so **downstream fields simply do not
exist until their parent is chosen**.

```
HDD : demand_nature -> (stop if Inorganic)
                    -> db_type -> (segment only when EDB)
                    -> granularity
                    -> Forest_SKU ? forest + sku : entity_value
SSD : db_type -> (stop if MCDB)
              -> prepared_scenario -> granularity -> entity_value
```

This is what the owner means by "se iban abriendo todas hasta el Key". It is not a
cosmetic difference: an axis that does not apply is **absent**, not shown holding
the word `NOT_APPLICABLE`.

`taxonomy_control()` renders each field with a label, a `"Select..."` placeholder,
an optional hint, and switches to `selectizeInput` with search when a list is long
(`maxOptions = 400`). Long key lists stay usable.

`taxonomy_resolve_selection()` returns the single `OPERATIONAL_ENTITY` row, or
`NULL`. Detail panels only draw when exactly one row resolves.

### The route panel

- **Breadcrumb**: chips of the path so far, `HDD > Organic > EDB > Consumer >
  Forest > APCP153`, or the words `Select a Metric` when empty.
- **Route state**: a green `OPERATIONAL` badge with "Prepared route and entity are
  available."
- **Route metadata**: a six-cell card grid — ROUTE, DISPLAY LABEL, ENTITY TYPE,
  SERVING STATUS, SUPPORT, ACTUALS — then a traceability note such as "Direct
  canonical-taxonomy match."

The value of this panel is that it **resolves the friendly selection back to the
source fields**, so the user can see what they actually picked.

### Absence is explained, not hidden

A teal callout states that N prepared cases are **forecast-only and not selectable
here**, because they carry no actuals and no backtests, and that *"nothing was
fabricated"*. The tone is worth copying: the app explains a gap instead of quietly
dropping rows.

## 3. Backtest Configuration commits, it does not react

- **Horizon**: `radioButtons` over `fvp_horizon_choices()` = 5/10/15/20/25/30.
  `fvp_horizon_unavailable()` = 35/45 render as **struck-through disabled chips**
  with "Prepared artifact covers 1-30 day horizons." The limit is shown, not
  hidden.
- **History window**: a `selectInput` that filters prepared dates only.
- **Models**: four checkbox groups ordered by `FVP_FAMILY_ORDER`
  (`growth_baseline`, `statistical`, `machine_learning`, `lightweight_neural`)
  and labelled by `FVP_FAMILY_LABELS` (Growth Baseline, Statistical, Machine
  Learning, **Deep Learning**). A live count reads "N models selected."
- **Champion**: `fvp_model_label()` appends `" ★ champion"` to the label. Note
  that high-risk badges are deliberately **not** rendered — the design chooses one
  badge over a wall of them.
- **Analyze Backtest / Reset Selection**, with the note *"Renders the chart and
  notes below. Updates only on click."*

That last line is a deliberate design decision. With several models and thousands
of points, re-rendering on every checkbox tick would feel broken. **V6.24 currently
re-renders on every change.**

## 4. Results is one rich Highcharts chart

`fvp_chart()` builds:

| Aspect | Configuration |
|---|---|
| Chart | `type="line"`, `zoomType="xy"`, panning with `panKey="shift"` |
| Title | `Backtest Comparison` |
| Subtitle | `{series} · horizon {N} days · {M} models · {min} → {max}` |
| X axis | `datetime`, crosshair on |
| Y axis | `Value`, crosshair on |
| Legend | enabled — Highcharts gives click-to-toggle for free |
| Tooltip | `xDateFormat="%Y-%m-%d"`, 2 decimals, per-series `pointFormat` carrying model, date, value, horizon, family, risk |
| Export | `hc_exporting(enabled = TRUE)` |
| Actual | reserved blue `#10477e`, `lineWidth = 3` |
| Models | `.fvp_palette`, 13 colours, **family-ordered so colours are stable** |

Data goes in as `data.frame(x = datetime_to_timestamp(date), y = round(value, 3))`
through `list_parse2()`.

`fvp_empty_chart()` is a calm titled chart with hidden axes — the state before
Analyze is pressed. Not a blank box, not an error.

Under the chart sit `fvp_download_ui` and `fvp_notes`.

## 5. The assistant closes the section

`llm_explain_ui("llm_forecast_viewer", "Forecast Viewer")` renders at the **end**
of the section. The comment in the source is explicit about why: *"It closes the
section, it does not introduce it."* The user reads first, then asks.

Four default quick prompts, matching the owner's screenshot exactly: *Summarize
the key takeaway*, *Explain what changed*, *Explain the main risk*, *What should I
pay attention to?* Plus a free-text box and **Generate explanation**.

A four-step timed "thinking" animation runs before the panel renders, and every
answer carries the disclosure *"Local mock · governed evidence only · no model or
champion changes."*

**The constraint that matters**: `llm_explain_get(page_id)` returns a response
keyed by **page**, not by selection. The assistant explains the *section*, not the
series currently on screen. Any V6.24 assistant must either build a
selection-aware evidence pack or be honest that it is section-level.

## 6. Downloads

Two different patterns exist:

- `artifact_export.R` — a **format modal** offering CSV, MD, TXT, HTML, and
  PDF/DOCX when pandoc is present. Built for whole small artifacts (≤ 15 rows),
  with CSV served as a verbatim `file.copy`.
- `fvp_pilot_download_rows()` in `viewer_pilot.R` — **rows for the current
  selection**. This is the closer match for "download analysis".

The right combination for V6.24 is the *modal* from the first and the *filtering*
from the second.

## 7. Two details worth stealing outright

**`outputOptions(output, "breadcrumb", suspendWhenHidden = FALSE)`** —
`taxonomy_navigation.R` line 532. The legacy code already knew that outputs inside
CSS-toggled sections need un-suspending. P8 rediscovered this the hard way, through
a page that rendered blank in the browser while 56 automated checks passed.

**Counts are always derived.** `taxonomy_viewer_scope()` computes the numbers in
the help text and the pills from the contract. No count is ever typed into the UI.
V6.24 follows the same discipline; it should keep doing so.
