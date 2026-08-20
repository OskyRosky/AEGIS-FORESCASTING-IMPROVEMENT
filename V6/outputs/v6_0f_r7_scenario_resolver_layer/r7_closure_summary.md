# V6.0F-R7 — Scenario Resolver Layer — Closure Summary

**Status token:** `V6_0F_R7_SCENARIO_RESOLVER_LAYER_COMPLETED`

---

## 1. What was built

| Component | Path | Size |
|---|---|---|
| Resolver | `V6/shiny_app/R/scenario_resolver.R` | 13 functions |
| Production DuckDB | `V6/data/storage/r6_phase1.duckdb` | **25.76 MB** |
| Metadata slices | `V6/data/storage/ui_metadata/` | **62.4 KB**, 5 files |

The R5b manifest listed the storage as `TO_BUILD_IN_R7`; R7 built it as a **derivation** of the R6 CSV artifacts. No Tesseract access.

| DuckDB table | Rows |
|---|---:|
| `viewer_hdd` | 817,386 |
| `forecast_hdd` | 565,104 |
| `forecast_ssd` | 651,480 |

---

## 2. Test results

**25 checks executed, 25 PASS, 0 FAIL.** All 11 mandatory cases plus 14 dropdown and filter checks.

| Case | Result |
|---|---|
| T1 HDD-EDB / Enterprise / Forest / NAMPRD07 | 1,097 rows, FULL, 0.089 s |
| T2 HDD-EDB / Consumer / Forest / NAMPRD07 | 1,097 rows, FULL, 0.083 s |
| T3 Basilisk / Forest / `namprd07` | 954 rows, 0.078 s |
| T4 Basilisk / Forest / `NAMPRD07` | **954 rows** — identical to T3 |
| T5 SSD / Low Volume No Efficiency | 2,196 rows, forecast_ssd, 0.079 s |
| T6 SSD / Low Volume With Efficiency | 2,196 rows, forecast_ssd, 0.079 s |
| T7 HDD Region / `APC-Dedicated` | 3,291 rows, FULL, 0.080 s |
| T8 Memory | `OUT_OF_SCOPE` |
| T9 SSD hidden scenario | `NOT_EXPOSED` |
| T10 CPU and IOPS | `NOT_AVAILABLE_IN_PHASE1` |
| T11 SSD-MCDB | `BLOCKED_O1` |

**T3 vs T4 is the important one.** It proves risk RB1 is handled: the same forest resolves whether the user supplies `namprd07` or `NAMPRD07`.

---

## 3. Design decisions taken

| # | Decision | Reason |
|---|---|---|
| 1 | `key_lower` materialised at **build** time | An `UPDATE` after `CREATE` inflated the file from 25.8 MB to 33.0 MB |
| 2 | `granularity` materialised as `'Forest'` on `forecast_ssd` | The R6 SSD artifact has no granularity column; normalising the schema avoids special-casing in the resolver |
| 3 | SSD-Phoenix on the **Viewer** page resolves to `forecast_ssd` | Per D3 the page still renders, forecast-only with an amber badge, rather than showing nothing |
| 4 | The `actual` series survives a model filter on the Viewer | Selecting a model must not hide the ground truth |
| 5 | Blocked selections return a **status**, never an error | The UI can render an honest explanation instead of failing |
| 6 | The resolver is **not yet sourced** by `global.R` | R7 must not change app behaviour; R8 wires it in |

---

## 4. Status vocabulary

| Status | Meaning | Example |
|---|---|---|
| `AVAILABLE` | Resolves to a DuckDB query | HDD and the 2 SSD-Phoenix scenarios |
| `OUT_OF_SCOPE` | No source exists | Memory |
| `NOT_EXPOSED` | Exists but withheld from this release | 22 SSD-Phoenix scenarios |
| `NOT_AVAILABLE_IN_PHASE1` | Scheduled for Phase 2 | CPU, IOPS |
| `BLOCKED_O1` | Awaiting a decision | SSD-MCDB |
| `UNKNOWN_SELECTION` | Not in the registry | defensive |

---

## 5. Byproduct cleanup

Registered in `r5b_byproducts_cleanup.csv` **before** deletion, as required.

| Path | Size | Action |
|---|---:|---|
| `bench/csv_partitioned` | 322.81 MB | 🗑️ Deleted |
| `bench/parquet` | 183.42 MB | 🗑️ Deleted |
| **Freed** | **506.23 MB** | |

All 12 protected R5b artifacts were retained, plus `bench/ui_metadata` and `bench/r6_phase1.duckdb`. Both deleted stores are reproducible from `bench_storage.R`.

---

## 6. Remaining risks

| ID | Risk | Severity | Note |
|---|---|---|---|
| RB1 | Key casing differs between scenarios | 🟢 **Closed** | Handled by `key_lower`; proven by T3/T4 |
| RB5 | The DuckDB file must be rebuilt when R6 re-extracts | 🟠 Medium | `build_storage.R` regenerates it; not yet automated |
| RB9 | Basilisk exposes only 2 model types and 1 version | 🟠 Medium | R8 must render this honestly, not as a broken control |
| RN1 | The resolver is not wired into the app | 🟡 Low | Intentional; R8 adds the `source()` call |
| RN2 | Region grain has no NAMPRD07 | 🟡 Low | By design; region keys are region names |

---

## 7. Can R8 proceed?

**Yes.** Every prerequisite is in place:

| Prerequisite | Status |
|---|---|
| Data extracted and validated | ✅ R6 Phase 1 |
| Storage format chosen and built | ✅ R5b + R7 |
| Dropdown resolution per control | ✅ R7 |
| Query contract per table | ✅ R7 |
| Key matching policy | ✅ R7, proven |
| Blocked-state vocabulary | ✅ R7 |

R8 needs only to add `source("R/scenario_resolver.R")` to `global.R` and wire the six controls into **Forecasting → Viewer**.

---

## 8. Governance

| Invariant | Result |
|---|---|
| No Shiny UI changes | Respected — only `R/scenario_resolver.R` created |
| Viewer and Forecast untouched | Respected |
| Assistant and LLM untouched | Respected — hash `A4DB09B4` |
| No Tesseract queries | Respected |
| No SQL writes | Respected |
| R6 artifacts unmodified | Respected |
| No heavy CSV loaded by the resolver | Respected |
| CPU, IOPS, SSD-MCDB, Memory excluded | Respected |
| Other 22 SSD scenarios not exposed | Respected |
| V1 to V5 untouched | Respected |
| No Azure, no Docker | Respected |
| Byproducts registered before deletion | Respected |
| Not advanced to R8, R9, R9b, R9c, R10, G1, G2, R6 Phase 2 | Respected |
