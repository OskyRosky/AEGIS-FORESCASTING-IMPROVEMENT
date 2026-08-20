# V6.0F-R1 — Tesseract Metric / Scenario / Key Inventory — Closure Summary

**Scope:** read-only diagnostic against `TesseractEarthDW`. No Shiny, Viewer, Forecast, Multi-Metric, data, model, refresh or Azure change was performed.

**Status token:** `V6_0F_R1_TESSERACT_METRIC_INVENTORY_COMPLETED`

---

## Deliverables (17 files in `V6/outputs/v6_0f_r1_tesseract_metric_inventory/`)

| File | Rows | Purpose |
|---|---:|---|
| tesseract_connection_validation.csv | 1 | Proof of connection |
| source_mapping_from_excel.csv | 24 | Excel mapping normalised |
| tesseract_table_existence.csv | 11 | Existence check |
| tesseract_related_tables_search.csv | 308 | Related object discovery |
| tesseract_table_columns_inventory.csv | 246 | Full column layouts |
| tesseract_table_row_counts.csv | 21 | Rows, date ranges, versions |
| tesseract_key_inventory_summary.csv | 21 | Key column and cardinality |
| tesseract_key_inventory_samples.csv | 1641 | Sample keys |
| namprd07_presence_by_table.csv | 21 | NAMPRD07 traceability |
| tesseract_scenario_values.csv | 56 | Real scenario values |
| tesseract_table_profiles.csv | 21 | Consolidated profile |
| tesseract_actual_forecast_views.csv | 9 | Actual vs forecast views and Memory |
| scenario_contract_from_tesseract.csv | 26 | **Corrected scenario contract** |
| viewer_forecast_feasibility_by_scenario.csv | 26 | **Viewer/Forecast feasibility** |
| local_artifact_gap_analysis.csv | 20 | **Local vs Tesseract gaps** |
| v6_0f_r1_validation.csv | 22 | Validation register |
| recommended_shiny_correction_plan.md | — | Proposed correction |

---

## Headline findings

1. **All 11 mapped tables exist.** The `SOURCE_NOT_LOCATED` verdicts issued in V6.0E were wrong.
2. **Scenario is a real column**, carried by four different names (`Scenario`, `data_type`, `CPU_type`, `IOPS_type`). It should not have been rendered as *Not applicable*.
3. **The key column name varies across five forms** (`Key`, `MyKey`, `Forest`, `Forest_SKU`, `forest_name`). Any generic loader must resolve it per source.
4. **Key counts were materially understated**: HDD forest 318 (not 155), HDD region 52 (not 45).
5. **SSD-Phoenix has 24 scenarios**, of which the portal surfaces 2.
6. **Only HDD carries actuals** inside the fact tables. CPU, IOPS and SSD are forecast-only there.
7. **Memory has no forecast source.** Its two demand views return 0 rows; only raw telemetry exists.
8. **All local artifacts are stale or truncated.** Metrics snapshots hold ~48% of current rows; the HDD region extract holds 1 of 50 forecast versions.
9. **The entire V6.0E/V6.0F multi-metric output rests on those stale snapshots** and must be treated as unreliable.

---

## Governance

| Constraint | Result |
|---|---|
| No Shiny modified | Respected |
| No Viewer modified | Respected |
| No Forecast modified | Respected |
| No Multi-Metric modified | Respected |
| No code deleted | Respected |
| No refresh executed | Respected |
| No model executed | Respected |
| No data modified | Respected |
| No Azure resource created | Respected |
| Not advanced to Boon | Respected |
| Not advanced to Docker | Respected |
| Read-only diagnostic only | Respected |

**Next gate:** Oscar reviews this inventory and answers decisions D1–D6 in `recommended_shiny_correction_plan.md`. No Shiny change proceeds before that.
