# V6.0F-R1 — Recommended Shiny Correction Plan

**Status:** proposal only. No Shiny file has been modified. Requires Oscar's approval before any code change.

---

## 1. What went wrong

| # | Error | Evidence from Tesseract |
|---|---|---|
| 1 | A new **Multi-Metric** tab was created. It was never requested. | Requirement was to add Scenario and Key filters inside the existing Viewer and Forecast pages. |
| 2 | "Scenario" was redefined as a technical split (Metric / DB Type / Granularity) and rendered as *Not applicable*. | Scenario is a real physical column in 9 of 11 fact tables, carrying real business values. |
| 3 | The key universe was wrong. | HDD forest has **318** keys, not 155. HDD region has **52**, not 45. |
| 4 | Several tables were declared `SOURCE_NOT_LOCATED`. | **All 11** mapped tables exist and are populated. |
| 5 | Everything was built on stale local CSV snapshots. | Local metrics files hold ~48% of the current rows. The local fact extract holds 1 of 50 forecast versions. |
| 6 | Tests passed because they validated my own assumptions rather than the database. | 33/35 PASS in V6.0E while the underlying source model was incorrect. |

---

## 2. The corrected data model

The business concept **Scenario** is not one uniform column. It is carried by four different column names depending on the table:

| Carrier column | Tables | Values |
|---|---|---|
| `Scenario` | hdd_region, cpu_region, cpu_byDB_*, iops_region, SSD_TotalForecast, SSD_Phoenix_Organic, MCDB_ForestSKU | Enterprise / Consumer / Basilisk / Consumed / Failover / 24 SSD scenarios |
| `data_type` | forecast_substratebe_hdd (forest) | Basilisk / consumer / Enterprise |
| `CPU_type` | forecast_substrateBE_cpu | consumed / failover |
| `IOPS_type` | forecast_substrateBE_iops | consumed / failover |

The **Key** column is likewise not uniform: `Key`, `MyKey`, `Forest`, `Forest_SKU`, `forest_name`.

**Consequence:** the application needs a *resolver layer* that maps a UI Scenario label to `(table, scenario_column, scenario_value, key_column, date_column, version_column, value_column)`. That mapping is exactly `scenario_contract_from_tesseract.csv`.

---

## 3. Proposed correction — three steps

### Step A — Remove the Multi-Metric section (revert only)
Delete the section registration and menu entry, and the three files added in V6.0F. Nothing else is touched. The LLM assistant layer is unaffected because the multi-metric pack was injected at runtime, not written into `llm_explain.R`.

- `ui/tabs.R` — remove the `multimetric` section
- `ui/sidebar.R` — remove the Multi-Metric menu item under Forecasting
- `server/server.R` — remove the multimetric server hook and its `llm_explain_server()` registration
- delete the 3 files added in V6.0F

### Step B — Add Scenario and Key filters to Viewer and Forecast
In **Forecasting → Viewer** and **Forecasting → Forecast**, add two controls above the existing ones:

1. **Scenario** — a single dropdown whose choices are the `scenario_ui_label` values, filtered to those that are feasible for that page.
2. **Key** — a dropdown that repopulates reactively from the selected Scenario.

Every other control on those pages stays exactly as it is.

Feasible scenario counts per page, from `viewer_forecast_feasibility_by_scenario.csv`:

| Page | Requirement | Scenarios that qualify |
|---|---|---|
| Viewer | needs actual **and** forecast | **6 fully usable** (all HDD combinations), 3 partial |
| Forecast | needs forward forecast only | **25 usable** (everything except Memory) |

### Step C — Refresh the data behind them
Neither page can honour the new filters using today's local files. A governed extract is required for the sources listed in `local_artifact_gap_analysis.csv`. This is a separate authorised stage — not part of this proposal.

---

## 4. Decisions required from Oscar

| # | Question | Why it blocks |
|---|---|---|
| D1 | **Memory** has no forecast table in Tesseract. Its demand views return 0 rows. Should Memory be dropped, shown as unavailable, or is it sourced from somewhere outside Tesseract? | It is one of the 9 requested metrics and currently has no source. |
| D2 | SSD-Phoenix has **24 scenarios**. The portal shows 2 (Low Volume With/No Efficiency). Expose only those 2, all 24, or a chosen subset? | Determines the size of the Scenario dropdown. |
| D3 | Viewer needs actuals. Only HDD carries them in the fact tables. For CPU / IOPS / SSD, do we (a) show forecast only, (b) use the small region-level `*_Demand_Actual_Forecast` views, or (c) use the precomputed `Mean_Actual` from the metrics tables? | Determines whether Viewer covers 6 or 26 scenarios. |
| D4 | Forest-grain CPU and IOPS are keyed by `Forest_SKU` (714 / 552 keys), not by Forest. Should the Key filter show SKU-level keys or aggregate to Forest? | Changes the key universe by an order of magnitude. |
| D5 | HDD forest `type` holds 25 values (`actual`, ARIMA, bsts_*, Arima+Fixed_*). Is this the model dimension the Viewer should plot? | Viewer currently has its own model list from a different artifact. |
| D6 | Granularity: should Region and Forest be a separate control, or baked into the Scenario label as proposed here? | Affects control count on the page. |

---

## 5. What will not be touched

- `R/llm_explain.R`, `R/llm_compose.R`, `R/llm_client.R`, `modules/llm_summary/`
- `outputs/v4_4_mock_provider/v4_4_mock_responses.json` (SHA256 `A4DB09B4…`)
- All frozen legacy artifacts listed in the V6 governance register
- Accuracy, TTL, Universe, Tournament, Champion, Risks, Audit, Artifacts, Methodology and Version sections
