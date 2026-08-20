# V6.0F-R5 — Governed Extraction Contract — Closure Summary

**Status token:** `V6_0F_R5_GOVERNED_EXTRACTION_CONTRACT_COMPLETED`

**Nature:** contract and measured estimation. No data extracted, no Shiny change, no resolver implemented.

---

## 1. What was created

| File | Rows | Purpose |
|---|---:|---|
| extraction_scope_contract.csv | 23 | Table, columns, filters and status per combination |
| version_selection_policy.csv | 11 | How many versions and by what rule |
| time_window_policy.csv | 14 | Historical and forward window per metric and page |
| key_extraction_policy.csv | 11 | Key coverage and mandatory keys |
| viewer_extraction_contract.csv | 17 | Actual and forecast filters plus type rules |
| forecast_extraction_contract.csv | 18 | Forward filters and version rules |
| extraction_volume_estimate.csv | 12 | Measured volumes and phase totals |
| excluded_scope_register.csv | 16 | Every exclusion with reason and re-entry condition |
| r5_open_decisions.csv | 10 | Decisions with options and recommendation |
| r5_validation.csv | 34 | Validation register |
| latest_version_footprint.csv | 7 | Supporting measurement |
| windowed_volume_estimate.csv | 9 | Supporting measurement |
| hdd_forest_execution_time_probe.csv | 8 | Supporting measurement |

---

## 2. What was decided

| Area | Decision |
|---|---|
| Phasing | **Phase 1** HDD (3 scenarios × 2 granularities) + SSD-Phoenix (2 scenarios). **Phase 2** CPU and IOPS. |
| Versions | Latest **3** for true version columns. For HDD forest, latest run **per scenario**. |
| Time window | **12 months back, 24 months forward** (2025-08-12 → 2028-08-12). |
| Keys | **Full key inventory** for every extracted source. NAMPRD07 mandatory for HDD forest and SSD-Phoenix. |
| Type | `TRIM()` mandatory. Markers excluded. Grouped by family, never 162 flat entries. |
| Memory | Not extracted. |
| SSD-MCDB | Blocked. |
| CPU byDB | Blocked. |

---

## 3. Measured volumes

| Phase | Rows to extract | Source rows | Share |
|---|---:|---:|---:|
| Phase 1 (Boon slice) | **1,549,656** | 145,131,510 | 1.1% |
| Phase 2 (CPU + IOPS) | **6,020,004** | 98,774,856 | 6.1% |
| **Combined** | **7,569,660** | **243,906,366** | **3.1%** |

Every figure is a measured `COUNT_BIG` under the proposed filters, not an extrapolation.

---

## 4. Principal risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| **RK1** | `execution_time` is a **run stamp, not a version**. Two runs 73 seconds apart carry identical row counts, and each run covers a single scenario. Taking "latest N" would silently return one scenario and could duplicate a run. | 🔴 Critical | Rule: latest run **per scenario**. Recorded as O12. |
| **RK2** | Phase 2 at 6.02M rows will not survive flat CSV in Shiny memory. | 🔴 Critical | R5b must decide the storage format before phase 2. |
| **RK3** | `type` is a CHAR column with padding. Any filter without `TRIM` fails silently and returns nothing. | 🔴 Critical | Rule embedded in both extraction contracts. |
| **RK4** | The latest HDD region version holds only 43 of 52 keys and 2 of 3 scenarios. | 🟠 High | Resolve the version **per scenario**, never globally. |
| **RK5** | Basilisk forest has **one** execution_time. No version comparison is possible. | 🟠 High | Documented; the UI must not imply a version selector there. |
| **RK6** | IOPS is stale: latest version is 2026-01-01 (region) and 2025-12-30 (forest). | 🟠 High | Flagged as an exception in the time window policy. |
| **RK7** | `hdd_region.ModelVersion` has 46,490 blank rows. | 🟡 Medium | Bucket as Unspecified. Never drop silently. |
| **RK8** | `SSD_TotalForecast.Type` is 72% `TotalPerturbed` and its meaning is unconfirmed. | 🟡 Medium | Fix to `Total` for the first release. Recorded as O13. |

---

## 5. Recommendation for R5b

| # | Recommendation |
|---|---|
| 1 | Evaluate **parquet** first. It is the smallest change from the current CSV loader and handles 7.5M rows comfortably. |
| 2 | Evaluate **duckdb** if the Viewer needs interactive filtering across all keys and versions at once. |
| 3 | Partition by `metric` + `granularity` so a page loads only what it needs, never the whole extract. |
| 4 | Set a hard budget: any single page load must read under 1M rows. |
| 5 | Decide whether phase 1 can ship on CSV while phase 2 waits for the new format. |

---

## 6. Recommendation for R6

| # | Recommendation |
|---|---|
| 1 | Extract **phase 1 only**. It is 1.55M rows and unblocks the Boon deliverable. |
| 2 | Record a snapshot manifest: table, filter, version, row count, extraction timestamp, checksum. |
| 3 | Verify NAMPRD07 is present in the extracted output before declaring success. |
| 4 | Re-run the key and scenario counts against the extract and reconcile them with this contract. |

---

## 7. Is R6 blocked?

**Partially blocked.**

| Scope | Status |
|---|---|
| **Phase 1 (HDD + SSD-Phoenix)** | ✅ **Not blocked.** Every source, filter, key, version and window is defined and measured. R6 can proceed on approval. |
| **Phase 2 (CPU + IOPS)** | ⛔ **Blocked by R5b.** 6.02M rows without a storage decision would break the app. |
| **SSD - MCDB** | ⛔ Blocked by O1. |
| **CPU byDB** | ⛔ Blocked by O3. |

Recommended sequence: approve **O4, O5, O11, O12, O14, O15** → run **R6 phase 1** → run **R5b** → run **R6 phase 2**.

---

## 8. Governance

| Invariant | Result |
|---|---|
| No data extracted | Respected |
| No full table proposed | Respected — 3.1% of source |
| Read-only SQL only | Respected |
| No SQL writes | Respected |
| Shiny, Viewer, Forecast, Assistant untouched | Respected |
| V1 to V5 untouched | Respected |
| No simulated data, no zero filling, no invented values | Respected |
| No Azure, no Docker | Respected |
| Not advanced to R5b R6 R7 R8 R9 R9b R9c R10 G1 G2 | Respected |
