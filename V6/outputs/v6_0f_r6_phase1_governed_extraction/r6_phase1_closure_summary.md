# V6.0F-R6 Phase 1 — Governed Extraction — Closure Summary

**Status token:** `V6_0F_R6_PHASE1_GOVERNED_EXTRACTION_COMPLETED`

**Extraction run id:** `R6P1-20260812T100822`

---

## 1. What was extracted

| Artifact | Rows | Size | Content |
|---|---:|---:|---|
| r6_phase1_viewer_hdd.csv | 817,386 | 187.5 MB | Actual + forecast, 3 scenarios × 2 granularities |
| r6_phase1_forecast_hdd.csv | 565,104 | 137.2 MB | Forward only, 3 scenarios × 2 granularities |
| r6_phase1_forecast_ssd_phoenix.csv | 651,480 | 96.7 MB | Forward only, 2 portal scenarios |
| **Total** | **2,033,970** | **421.4 MB** | |

Plus 6 metadata artifacts: manifest (14 rows), key inventory (8), version inventory (8), data quality checks (51), lineage (3), validation (42).

### Coverage detail

| Metric | Scenario | Granularity | Keys | Viewer rows | Forecast rows |
|---|---|---|---:|---:|---:|
| HDD - EDB | Enterprise | Region | 45 | 145,673 | 97,356 |
| HDD - EDB | Enterprise | Forest | 152 | 166,668 | 111,264 |
| HDD - EDB | Consumer | Region | 45 | 145,673 | 97,356 |
| HDD - EDB | Consumer | Forest | 152 | 166,668 | 111,264 |
| HDD - Basilisk | Basilisk | Region | 47 | 44,834 | 34,404 |
| HDD - Basilisk | Basilisk | Forest | 155 | 147,870 | 113,460 |
| SSD - Phoenix | Low Volume No Efficiency | Forest | 148 | — | 324,276 |
| SSD - Phoenix | Low Volume With Efficiency | Forest | 152 | — | 327,204 |

---

## 2. What was not extracted

| Item | Reason |
|---|---|
| CPU, CPU Failover | Phase 2, blocked by R5b |
| IOPS, IOPS Failover | Phase 2, blocked by R5b |
| CPU byDB | Blocked by O3 |
| SSD - MCDB | Blocked by O1 |
| Memory | Out of scope, D1 |
| 22 other SSD-Phoenix scenarios | Not exposed in the first release, D2 |
| 30,995 of 30,998 execution_time runs | Only the latest run per scenario was used |
| `stubbed`, `Extrapolated`, `Fixed_NA` | Data quality markers, not models |

---

## 3. Validation

**51 of 51 data quality checks PASS. 42 of 42 validation checks PASS.**

| Area | Result |
|---|---|
| Actual series present | 6 of 6 HDD combinations |
| Forecast artifact free of actuals | 6 of 6 |
| Time windows respected | 14 of 14 |
| Null values | 0 |
| Marker rows | 0 |
| NAMPRD07 in HDD forest | 1,097 rows per EDB scenario, 954 for Basilisk |
| NAMPRD07 in SSD-Phoenix | 2,196 rows per scenario |

### Reconciliation against R5

| Measure | R5 estimate | R6 actual | Variance |
|---|---:|---:|---:|
| Unique rows | 1,549,656 | 1,468,866 | −5.2% |
| Rows across artifacts | — | 2,033,970 | — |

The 2.03M figure exceeds the estimate because the forward rows appear in **both** the viewer and the forecast artifact by design: one artifact per page. Unique row volume is 1.47M, which reconciles with the R5 estimate to within 5.2%.

---

## 4. Findings

| # | Finding | Consequence |
|---|---|---|
| **FD1** | **HDD Basilisk has only one forecast version** at both granularities (region 2026-05-29, forest 2026-05-29 21:17:55). | No version comparison is possible for Basilisk. The UI must not offer a version selector there. |
| **FD2** | **Basilisk data starts 2026-01-02**, not 2025-08-12. The 12-month history window cannot be filled. | The Viewer will show a shorter history for Basilisk. This must be stated, not padded. |
| **FD3** | **Basilisk forest carries only 2 model types** versus 25 for Enterprise and 17 for Consumer. | The model selector will be nearly empty for Basilisk. |
| **FD4** | **NAMPRD07 does not exist at region grain**, by design. Region keys are names like `APC-Multitenant`. | The demo key applies only to the Forest granularity. |
| **FD5** | **Only `Total` appears in the SSD forward window**; `TotalPerturbed` is absent. | Resolves O13 for this window: no control is needed. |
| **FD6** | **421 MB of CSV** for phase 1 alone. | Confirms R5b is mandatory before the Shiny integration. Loading 187 MB into a Shiny session is not viable. |
| **FD7** | Enterprise and Consumer forest artifacts have **identical row counts** (166,668 / 111,264). | Expected: both runs come from the same batch minutes apart. Worth a spot check in R7. |

---

## 5. Remaining risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| RK-A | 421 MB CSV cannot be loaded by Shiny as-is | 🔴 Critical | R5b must choose parquet or duckdb and a partitioning scheme |
| RK-B | Basilisk has a single version and a short history | 🟠 High | Surface honestly in the UI; never pad |
| RK-C | The forecast artifact duplicates rows already in the viewer artifact | 🟡 Medium | R7 may read one source and derive the other |
| RK-D | Enterprise and Consumer forest counts are identical | 🟡 Medium | Verify in R7 that the two scenarios really differ in value |

---

## 6. Can R7 proceed?

**Not yet. R5b must come first.**

| Prerequisite | Status |
|---|---|
| Data extracted and validated | ✅ Complete |
| Scenario, key, version and type dictionaries | ✅ Complete (R3) |
| Storage format able to serve the Shiny app | ❌ **Missing — R5b** |

Building the resolver against a 187 MB CSV would bake in a design that cannot ship. **Recommended next stage: R5b.**

---

## 7. Governance

| Invariant | Result |
|---|---|
| Only HDD and SSD-Phoenix | Respected |
| No full table extraction | Respected |
| No CPU, IOPS, byDB, MCDB, Memory | Respected |
| Only 2 SSD-Phoenix scenarios | Respected |
| Read-only SQL only, no writes | Respected |
| No simulated data, no zero filling | Respected |
| Shiny, Viewer, Forecast, Assistant untouched | Respected |
| V1 to V5 untouched | Respected |
| No Azure, no Docker | Respected |
| Not advanced to R5b, R6 Phase 2, R7, R8, R9, R9b, R9c, R10, G1, G2 | Respected |
