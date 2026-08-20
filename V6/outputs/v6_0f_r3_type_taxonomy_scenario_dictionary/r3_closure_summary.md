# V6.0F-R3 — Type Taxonomy + Scenario Dictionary — Closure Summary

**Status token:** `V6_0F_R3_TYPE_TAXONOMY_SCENARIO_DICTIONARY_COMPLETED`

**Nature:** documentation plus read-only aggregate queries. No Shiny, no product code, no dataset extraction.

---

## 1. What was created

| File | Rows | Purpose |
|---|---:|---|
| scenario_dictionary.csv | 29 | UI label ↔ raw value ↔ carrier column ↔ source table |
| key_column_dictionary.csv | 11 | The five key column forms with counts and samples |
| version_column_dictionary.csv | 11 | Version columns with cardinality and range |
| hdd_forest_type_taxonomy.csv | 162 | Every `type` value classified |
| ui_label_normalization_rules.csv | 24 | Display normalisation, raw value always preserved |
| model_type_values_raw.csv | 825 | Supporting evidence across 10 tables |
| scenario_dictionary_validation.csv | 34 | Validation register |
| r3_closure_summary.md | — | This file |

---

## 2. What was validated

| Area | Result |
|---|---|
| Every exposed scenario has a physical source | 16 of 16 |
| Raw values preserved | 100% |
| Scenario never mixed with Type | separate dictionaries |
| SSD-Phoenix exposure | exactly 2, per D2 |
| Memory selectable | never |
| Key forms documented | all five: `Key`, `MyKey`, `Forest`, `Forest_SKU`, `forest_name` |
| Taxonomy completeness | 162 of 162 values, reconciling to 53,922,502 rows exactly |
| Queries | read-only aggregates only |

---

## 3. Corrections to earlier statements

| # | Earlier claim | Verified value |
|---|---|---|
| 1 | HDD forest `type` has **25** values | **162** values. The earlier figure came from a TOP-N sample, not a full `GROUP BY`. |
| 2 | `type` is simply a model list | It mixes **actuals**, **models**, **baselines**, **ensembles** and **data quality markers**. |

---

## 4. New findings

| # | Finding | Consequence |
|---|---|---|
| F1 | HDD forest `type` is a **CHAR column**: all 162 values are space-padded | Any join or filter must `TRIM`. Without it, every match fails silently. Blocks R7. |
| F2 | `type` composition: 100 ensembles, 42 fixed baselines, 10 statistical, 6 growth baselines, 3 markers, 1 actual | A flat 162-item selector is unusable. Grouping by `model_family` is required. Answers O10. |
| F3 | Three values are **not models**: `stubbed` (1,597), `Extrapolated` (2,048), `Fixed_NA` (8,512) | Must be excluded from the model selector and never plotted as a forecast. |
| F4 | `hdd_region.ModelVersion` has **46,490 rows with an empty string** | Needs an explicit "Unspecified" bucket, not a blank dropdown entry. |
| F5 | `hdd_region` stores both `ARIMA` and `Arima` | Display normalisation required; raw values preserved. |
| F6 | `actual` exists **only** in HDD forest (4,372,036 rows) and HDD region (830,299 rows) | Confirms D3: Viewer FULL is HDD only. |
| F7 | `forecast_substrateBE_hdd.execution_time` spans 30,998 versions from 2021-01-01 to 2026-07-23 | A version dropdown cannot list them all. Blocks R5. |
| F8 | `SSD_TotalForecast.Type` has only 2 values: `Total` and `TotalPerturbed` | This is not a model dimension. SSD has no model selector. |
| F9 | `MCDB_ForestSKU.ModelVersion` is a single value `prophet`; `SSD_Phoenix_Organic` is a single value `Combined` | No model selector for these sources either. |

---

## 5. What remains open

### Blocks R5 (Extraction Contract)

| ID | Question |
|---|---|
| O1 | SSD - MCDB scenario selection still undefined |
| O4 | How many forecast versions to extract — F7 makes this urgent |
| O5 | Temporal window of the extract |

### Blocks R7 (Scenario Resolver)

| ID | Question |
|---|---|
| O3 | Is DBType a fourth control, or are the byDB tables a separate Scenario |
| F1 | The resolver must apply TRIM on `type`; confirm no other CHAR columns behave the same |
| F4 | Confirm the "Unspecified" bucket wording for blank model versions |

### Resolved by R3

| ID | Resolution |
|---|---|
| O2 | `consumer` → display `Consumer`, raw value preserved. Rule recorded. |
| O10 | Expose grouped by `model_family`, not as 162 flat entries. Recommendation recorded. |

---

## 6. Governance

| Invariant | Result |
|---|---|
| Shiny, Viewer, Forecast, Assistant untouched | Respected |
| V1 to V5 untouched | Respected |
| Read-only SQL only | Respected |
| No full table extracted | Respected |
| No large data artifact | Respected — largest output is 825 rows |
| No invented labels | Respected — every label traces to a queried value |
| Scenario and Type kept separate | Respected |
| Raw values preserved | Respected |
| No Azure, no Docker | Respected |
| Not advanced to R5 R5b R6 R7 R8 R9 R9b R9c R10 G1 G2 | Respected |
