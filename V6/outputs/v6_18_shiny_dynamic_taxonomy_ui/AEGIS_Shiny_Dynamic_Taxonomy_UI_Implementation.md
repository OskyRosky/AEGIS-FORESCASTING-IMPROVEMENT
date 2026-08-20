# AEGIS V6.18 Shiny Dynamic Taxonomy UI Implementation

## Status

Implementation and automated validation are complete. The stage remains open until
Oscar completes the visual review.

Status token:

`AEGIS_SHINY_DYNAMIC_UI_IMPLEMENTED_AWAITING_OWNER_VISUAL_VALIDATION`

## Source inputs and precedence

1. Governed prepared V6.17 artifacts define current operational behavior.
2. The Master Catalog defines canonical taxonomy validity and applicability.
3. The HTML mockup provides visual and interaction direction only.

| Source | Use | SHA-256 |
|---|---|---|
| `AEGIS_Master_Catalog_Discovery_E0_E10.md` | Canonical five-metric taxonomy, 38 route contracts, 34 routable routes and axis applicability | `620A9F77A418D74616D18AB7F9DD71DDF42761A5F6C7582867B86F23F5B715A8` |
| `AEGIS_Dynamic_Taxonomy_Dashboard_Mockup.html` | Conditional rail, breadcrumb, route cards, explicit states and compact technical styling | `0947BE6C2F013D0581BA9A12348193DBC959095EC3EABF11A01208C5EFFE3D78` |
| V6.17 Viewer metadata and Parquet | Current actual-bearing Viewer population | Governed V6.17 input |
| V6.17 Forecast metadata and Parquet | Current forward Forecast population | Governed V6.17 input |

The simulated time series, hard-coded KPI counts and JavaScript architecture in the
mockup were not copied into Shiny.

## Preflight reconciliation

| Measure | Observed |
|---|---:|
| Full discovered logical taxonomy | 6,383 leaves |
| E10 routable taxonomy routes | 34 |
| Current Viewer routes | 6 |
| Current Viewer cases | 596 |
| Current Forecast routes | 8 |
| Current Forecast cases | 896 |
| Taxonomy-valid but not currently implemented routes | 30 |
| Viewer models | Exactly 15 |

The 30-route gap is 34 routable E10 routes minus four direct V6.17 canonical EDB
matches. Four additional V6.17 routes remain operational through explicit
compatibility handling:

- two HDD Basilisk routes use prepared-artifact source precedence;
- two SSD-Phoenix routes preserve the prepared legacy volume/efficiency variants.

## Shared navigation architecture

`v6_18_navigation_contract.csv` is the one prepared navigation contract consumed by
both Viewer and Forecast. It contains 901 rows:

- 896 operational entity rows;
- five informational route rows.

The shared R module:

- loads the contract once;
- applies page-specific visibility and eligibility;
- renders Metric first;
- conditionally renders only applicable operational dimensions;
- labels entities as Region, Forest, or Forest + SKU;
- uses searchable entity controls;
- renders the selected-route breadcrumb and metadata cards;
- resolves the friendly taxonomy back to the legacy prepared fields
  `metric`, `scenario`, `granularity`, and `series_key`;
- rejects hidden or stale values before they reach a provider query.

Viewer and Forecast use the same resolver and UI module. Their eligibility differs:

- Viewer exposes HDD only because all Viewer routes must have actuals.
- Forecast exposes operational HDD and SSD-Phoenix routes, plus honest informational
  states for CPU, IOPS, SSD-MCDB and Memory.

## Current operational navigation

### HDD EDB

`Metric -> Demand Nature -> DB Type -> Segment -> Granularity -> Region/Forest`

- Demand Nature: Organic
- DB Type: EDB
- Segment: Consumer or Enterprise
- Granularity: Region or Forest

### HDD Basilisk

`Metric -> Demand Nature -> DB Type -> Granularity -> Region/Forest`

Segment disappears. The prepared V6.17 artifact remains operational under source
precedence even though the Master Catalog serving view is marked empty.

### SSD Phoenix Forecast

`Metric -> DB Type -> Prepared Forecast Variant -> Granularity -> Forest`

The prepared variants are:

- Low Volume No Efficiency
- Low Volume With Efficiency

They are not renamed to Organic/Inorganic because no governed mapping exists.
This is recorded as a `BACKEND_GAP`, while the current prepared Forecast cases remain
reachable.

## Viewer changes

- Added the shared conditional taxonomy navigator.
- Simplified user-facing navigator copy to `Selection`.
- Moved `Reset Selection` beside `Analyze Backtest`.
- Wired the outer reset action through the module reset function.
- Reset now clears Metric and downstream state, restores Horizon to 5 days and History
  Window to the full default, clears analyzed output, and recreates the six default
  model selections when a route is selected again.
- The governed V6.17 model metadata now keeps all 15 model checkboxes and all four
  families visible for incomplete, unavailable, and operational routes.
- `Analyze Backtest` is disabled until the selected route has a runnable prepared
  backtest; the model panel remains visible while unavailable.
- Removed the user-facing generic Key / Series selector.
- Added a breadcrumb, route metadata cards, searchable Region/Forest selectors and
  explicit unsupported states.
- Preserved Horizon, History Window, Analyze Backtest and prepared-row download.
- Preserved exactly 15 verified AEGIS models.
- Preserved lazy Arrow filtering and collection of only the selected entity.
- Preserved actual-versus-selected-model chart behavior.
- Kept SSD-Phoenix absent from Viewer.

## Forecast changes

- Added the same shared navigator with Forecast-specific eligibility.
- Structured the page explicitly as `Data Selection`, `Forecast Configuration`, and
  `Forecast Results`.
- Reframed the result as a prepared forward-looking 30/60-day answer rather than a
  backtest.
- Simplified user-facing navigator copy to `Data Selection`.
- Moved `Reset Selection` beside `Analyze Forward Forecast`.
- Wired the outer reset action through the module reset function.
- Reset now clears Metric and downstream state, restores Forecast Window to 30 days,
  removes route-dependent history state, and clears analyzed output.
- Disabled `Analyze Forward Forecast` until a prepared route is selected.
- Anchored the mandatory dashed `Forecast start` line to the first prepared forecast
  date for both HDD and SSD-Phoenix, independent of the selected display window.
- Increased Forecast Start contrast and positioned its complete label inside the plot
  for both actual-bearing and forecast-only charts.
- Added an explicit chart transition legend: Actual history, Forecast start, and
  Forward forecast. Forecast-only routes omit the Actual history legend item.
- Ensured actual history is displayed only before the Forecast start boundary.
- Added conditional prepared prediction-interval rendering; the current productive
  Forecast artifact has no interval columns, so the UI reports that honestly.
- Expanded Forecast Data Notes with route, entity, model, version, Forecast Start,
  both windows, point counts, date range, interval state, artifact, and forecast-only
  status.
- Preserved Forecast Window and Actual History Window.
- Preserved HDD actual-history plus forward-forecast behavior.
- Preserved SSD-Phoenix forecast-only behavior without fabricated actuals.
- Added `BACKEND_GAP` states for CPU, IOPS and SSD-MCDB.
- Added `NOT_ROUTABLE` for Memory.
- Preserved lazy Arrow filtering and frozen prepared model/version behavior.

## Empty and informational states

Implemented in the shared state renderer:

- `NOT_ROUTABLE`
- `NOT_CURRENTLY_IMPLEMENTED`
- `BACKEND_GAP`
- `FORECAST_ONLY`

Existing provider chart states continue to cover:

- `NO_DATA`
- `INSUFFICIENT_HISTORY`
- `SERVING_EMPTY`
- `ACTUALS_NOT_AVAILABLE`

Status text is displayed outside selectors. No status value is inserted as a
selectable option.

## Automated validation

Validation time: 2026-08-18 15:31 -06:00.

| Area | Result |
|---|---|
| R syntax parsing | PASS |
| Shiny startup | PASS |
| HTTP `200` | PASS |
| Full Viewer resolver sweep | PASS, 596/596 |
| Full Forecast resolver sweep | PASS, 896/896 |
| Viewer models | PASS, exactly 15 |
| Viewer chart | PASS, actual plus six selected model series |
| HDD Forecast chart | PASS, actual plus forecast |
| SSD-Phoenix Forecast chart | PASS, forecast-only |
| Breadcrumb | PASS |
| Conditional removal | PASS |
| Hidden stale-state rejection | PASS |
| Generic Key selector absent | PASS |
| SSD-Phoenix absent from Viewer | PASS |
| Backend states | PASS |
| Productive Parquet sizes | PASS, unchanged from V6.17 manifest |
| Owner-facing Selection copy | PASS |
| Viewer outer reset behavior | PASS |
| Forecast outer reset behavior | PASS |
| Reset clears analyzed output | PASS |
| Viewer defaults after route reselection | PASS, six models |
| Viewer dropdown clipping | PASS, six conditional control types |
| Forecast dropdown clipping | PASS, five conditional control types |
| Viewer model universe | PASS, exactly 15 |
| Viewer unavailable-route model panel | PASS, 15 visible in four families |
| Viewer unavailable Analyze state | PASS, disabled |
| Forecast product structure | PASS, Selection / Configuration / Results |
| HDD Forecast start | PASS, aligned to first prepared forecast date |
| HDD 30/60-day boundary stability | PASS |
| SSD-Phoenix Forecast start | PASS, forecast-only and aligned |
| Forecast Data Notes | PASS, complete and route-specific |
| Prediction interval behavior | PASS, conditional; current artifact has none |
| Viewer pass-3 regression | PASS |
| HDD final chart transition | PASS, actual / boundary / forecast |
| SSD-Phoenix NAMPRD07 final chart | PASS, boundary / forecast only |
| Forecast Start full-label visibility | PASS, HDD and SSD-Phoenix screenshots |
| Viewer pass-4 regression | PASS |

The validation CSVs contain 83 persisted checks:

- 30 Viewer checks;
- 36 Forecast checks;
- 17 reactive reset checks.

Owner visual polish pass applied: user-facing taxonomy wording simplified to Selection;
reset control moved to action/configuration area; reset now calls module reset function
from outer Viewer/Forecast action rows.

Owner visual polish pass 2 applied: dropdown menus no longer clip inside selection
cards; Backtest Configuration always preserves the 15-model selection panel even when
selected route is unavailable.

Owner visual polish pass 3 applied: Forecast now has product-level Selection, Forecast
Configuration and Forecast Results structure; Forecast Start boundary line is mandatory
and validated for HDD and SSD-Phoenix forecast-only routes.

Owner visual polish pass 4 applied: Forecast Results now consistently render actual
history plus forward forecast where actuals exist, forecast-only forward series where
actuals do not exist, and a mandatory Forecast start boundary line in both cases.

## Backend gaps and known limitations

- CPU and IOPS have valid taxonomy routes but no governed productive V6.17 inputs.
- SSD-MCDB has valid taxonomy routes but no governed productive V6.17 forecast.
- Memory has no routable productive source.
- HDD Inorganic is taxonomy-valid but absent from V6.17 prepared artifacts.
- SSD-Phoenix Organic/Inorganic mapping is unresolved; legacy prepared variants are
  shown verbatim.
- No current operational V6.17 route uses Forest_SKU. Separate Forest and SKU support
  is implemented in the shared module but is not marked as an operational journey.
- HDD Basilisk remains a documented source-precedence discrepancy.

No unsupported journey was marked as operational and no data was fabricated.

## Dashboard feeding

| Page | Prepared feed | Access |
|---|---|---|
| Viewer | `v6_18_navigation_contract.csv` | Read once, metadata filtering |
| Viewer | `forecast_viewer_model_outputs_v2_full.parquet` | Lazy selected-entity filtering |
| Forecast | `v6_18_navigation_contract.csv` | Read once, metadata filtering |
| Forecast | `forecast_forward_outputs_v6_17_full.parquet` | Lazy selected-entity filtering, prepared window rendering and artifact-derived Forecast Start |

Shiny remains read-only. It performs no model execution, retraining, forecast
generation, backtest regeneration, dashboard-side joins, aggregation, extraction or
artifact preparation.

## Owner visual checklist

### Viewer

1. Open Viewer and confirm Metric is first and only HDD is available.
2. Select HDD -> Organic -> EDB -> Enterprise -> Region -> APC-Dedicated.
3. Confirm breadcrumb order and six route metadata cards.
4. Confirm 15 model checkboxes are present.
5. Click Analyze Backtest and inspect the actual and model lines.
6. Change Horizon, History Window, and model selections; click Reset Selection.
7. Confirm Metric and downstream controls clear, Horizon returns to 5 days, History
   Window returns to default, and analyzed results disappear.
8. Reselect the route and confirm the six default models are selected.
9. Change EDB to Basilisk and confirm Segment disappears and the entity clears.
10. Change Organic to Inorganic and confirm DB Type, Segment and Granularity disappear
   and `NOT_CURRENTLY_IMPLEMENTED` appears.

### Forecast

1. Select HDD -> Organic -> EDB -> Consumer -> Forest -> APCP150.
2. Confirm Actual History Window is active and the chart shows actual history before
   the dashed `Forecast start` boundary plus the forward forecast after it.
3. Compare 30 and 60 days and confirm the same Forecast Start date remains aligned.
4. Confirm Forecast Data Notes include all route, model, version, window, point, date,
   interval, and artifact fields.
5. Select SSD -> Phoenix -> Low Volume No Efficiency -> Forest -> APCP150.
6. Confirm `FORECAST_ONLY`, zero actual points, one forecast series, and the mandatory
   `Forecast start` boundary.
7. Change Forecast Window; click Reset Selection and confirm Metric and downstream
   controls clear, Forecast Window returns to 30 days, and analyzed results disappear.
8. Select CPU and confirm only `BACKEND_GAP` appears downstream.
9. Select SSD -> MCDB and confirm variant and granularity controls disappear.
10. Select Memory and confirm `NOT_ROUTABLE` with no downstream controls.
11. Inspect responsiveness, breadcrumb readability, metadata cards and chart clarity.

## Intentionally not touched

- V1-V5
- model code and hyperparameters
- productive Viewer and Forecast artifacts
- Tesseract extraction and SQL
- Docker and Azure
- Assistant/LLM behavior
- `scenario_resolver.R`
- Forecast regeneration and backtest regeneration

## Owner gate

V6.18 must not be declared complete until Oscar approves the live visual review.
