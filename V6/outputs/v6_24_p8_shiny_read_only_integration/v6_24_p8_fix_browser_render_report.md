# V6.24-P8-FIX — Browser Render Defect

Found when the owner asked to see the app running. Recorded here rather than
quietly folded into P8, because the P8 closure claimed the pages rendered and
that claim was only **structurally** true.

---

## What was wrong

Opening **V6.24 MVP → Overview** in a real browser showed the page shell — title,
horizon banner, panel headings, static text — but **every card, table and chart
was blank.**

## Root cause

Two distinct failures, one behind the other.

**1. Shiny suspends outputs inside hidden elements.**
These pages are plain `<section data-section>` divs that `custom.js` shows and
hides with CSS. They are not `tabsetPanel` tabs, so Shiny has no idea they ever
become visible. By default Shiny suspends any output whose container is hidden
at render time — for a section that starts hidden, that means *never rendering*.

**2. htmlwidgets cannot initialise in a `display:none` container.**
After un-suspending, DT threw
`TypeError: Cannot read properties of null (reading 'lazyRender')` on the client.
Worse, that JS exception aborted the rest of the output message batch, so the
plain `uiOutput` cards beside the tables went blank too. That is why the first
symptom looked like "nothing renders" rather than "tables do not render".

## The fix

| Change | File |
|---|---|
| `outputOptions(suspendWhenHidden = FALSE)` for all 33 V6.24 outputs | `server/v6_24_mvp_server.R` |
| Replaced every `DT::datatable` with a plain HTML table (`v24_table()`) | `R/v6_24_read_only_loader.R`, `server/v6_24_mvp_server.R` |
| Replaced every `DT::DTOutput` with `uiOutput` | `ui/tabs_v6_24_mvp.R` |
| Added a resize hook so plotly re-measures when a V6.24 section is shown | `ui/tabs_v6_24_mvp.R` |
| Table styling | `www/custom.css` |

A static HTML table has no client-side init step, so it renders correctly whether
its section is visible or not. The tables here are small — 4 to 192 rows — so
nothing of value was lost. Plotly was kept because charts are the point of the
Viewer and Forecast pages, and a resize event is enough to make it re-measure.

## Why the P8 test suite missed it

This is the important part.

- **`shiny::testServer`** runs the reactive graph headlessly. It has no DOM, so
  it never simulates output suspension or widget initialisation. All 31 checks
  passed against code that rendered nothing in a browser.
- **The HTTP launch check** requested `/` and asserted the four sections were in
  the served HTML. They were — the page *shell* is server-rendered. The dynamic
  content arrives later over the websocket, which a single GET never sees.

Both tests were correct about what they measured. Neither measured what the user
would actually see. A headless reactive test and an HTML string check cannot
substitute for rendering the page.

## Verified after the fix

Confirmed in a real browser, not by assertion:

| Page | Observed |
|---|---|
| Overview | 12 cards render: 140 / 140 / 140 / 140 / 140 / **125** champion visible, 53 available, 87 with caveat, 15 no-signal, 1 low-confidence |
| Overview | Coverage-by-metric and signal-quality tables render |
| Viewer | Cascading filters render and update; path resolves to one series |
| Viewer | Observed-history and backtest charts draw; the 11 sampled origins are visible as distinct prediction segments |
| Viewer | Ranking table lists all 15 models; rank 1 `FixedGrowth_1_5`, wape 0.039158, marked champion |
| Viewer (no-signal) | `NO_SIGNAL` and `CHAMPION_NOT_MEANINGFUL` badges; *"Champion is not meaningful for this no-signal series"*; technical champion `ETS Explicit` labelled **not a recommendation**; history draws a flat line at zero |
| Forecast | Observed history plus exactly 30 forward steps, labelled "forecast (30 steps)" |
| Taxonomy | GLOBAL row 140/140/140/125/15; caveat table matches P7 exactly; filter option contract shows CPU 20, HDD 50, IOPS 20, SSD 50 |

The no-signal page is the strongest single piece of evidence: it shows the P6C
ranking correction (`ETS Explicit`, not `FNAR-V2`), the P7 contract fields and
the P8 rendering all working together on one screen.

## Regression status

Both automated suites re-run after the fix: **app smoke 25/25**, **reactive
server 31/31**. Governed artifacts remain byte-identical.

## What P9 should carry forward

**Add a real browser render check to the test suite.** Every V6.24 page should be
loaded in a headless browser and asserted to contain its expected values, not
merely its expected markup. This defect class is invisible to both testServer and
a plain HTTP GET.
