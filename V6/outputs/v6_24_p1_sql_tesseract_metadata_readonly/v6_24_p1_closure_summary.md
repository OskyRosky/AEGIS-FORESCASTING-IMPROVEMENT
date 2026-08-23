# V6.24-P1 — SQL / Tesseract Metadata Read-Only — Closure Summary

**Stage:** V6.24-P1
**Mode:** Read-only metadata inspection
**Server:** `tesseractearth.database.windows.net`
**Database discovered:** `TesseractEarthDW` (the only user database; `master` is the other)
**Auth:** Microsoft Entra Interactive via ODBC Driver 18 (`pyodbc`)
**Queries executed:** 70, all recorded in `v6_24_p1_query_ledger.csv` (67 OK, 3 FAILED and disclosed)
**Validation:** 20 checks, 20 PASS, 0 FAIL

---

## 1. What was actually found

> **CORRECTION — see `v6_24_p1b_ssd_correction.md`.**
> The SSD conclusion in this summary was **wrong**. P1 probed only 3 of 102 SSD objects
> and searched by `Key` = region; SSD actuals are keyed by **forest** and live in the
> `ssd_phx_lvwe` / `ssd_phx_lvne` accuracy tables, current to **2026-08-22**.
> SSD has **272** combinations over the 50-observation threshold and **is Viewer-eligible**.
> Sections 1.3, 2 and 3 below are superseded on the SSD rows only; HDD, CPU, IOPS and
> Memory findings stand as written.

### 1.1 The decisive discovery: actuals are marked by `ModelVersion`, not `ValueType`

`ValueType` is `'Forecast-Mean'` in **every** table inspected, so it does not separate
observed history from forecast. The real marker is:

| Granularity | Marker column | Actuals predicate |
|---|---|---|
| Region | `ModelVersion` | `= 'actual'` (HDD) / `= 'Actual'` (CPU, IOPS) |
| Forest | `type` | `TRIM(type) = 'actual'` (HDD only) |

This was established by measuring vocabularies (Q029–Q046) and then probing directly
for the marker in every large table (Q047–Q049, Q067–Q068).

### 1.2 Confirmed actuals sources

| Metric | Granularity | Object | Predicate | Combos >50 | History |
|---|---|---|---|---:|---|
| HDD | Region | `forecast_substrateBE_hdd_region` | `ModelVersion='actual'` | **137** | 2019-07-01 → 2026-08-17 |
| HDD | Forest | `forecast_substrateBE_hdd` | `TRIM(type)='actual'` | **467** | 2019-07-01 → 2026-08-17 |
| CPU | Region | `forecast_substrateBE_cpu_actual_region` | `ModelVersion='Actual'` | **60** | 2022-01-04 → 2023-07-20 |
| IOPS | Region | `forecast_substrateBE_iops_actual_region` | `ModelVersion='Actual'` | **58** | 2020-06-23 → 2023-07-20 |

**Total: 722 route × key combinations with more than 50 real observations, across three metrics.**

Every single combination measured cleared the 50-observation threshold. There were no
partial or borderline series.

### 1.3 Metrics with no actuals

| Metric | Status | Evidence |
|---|---|---|
| **SSD** | `FORECAST_ONLY` | `forecast_substrateBE_ssd_region` carries only `ModelVersion='prophet'` and `Scenario='None'` (Q046, Q049). `forecast_substrateBE_SSD_Phoenix_Organic` carries only `ModelVersion='Combined'` over a wholly forward window 2025-08-08 → 2030-07-02 (Q051). `DemandPlan_SubstrateBE_SSD_Demand_Region_History` is a demand plan with forward dates to 2028 (Q054). No actuals marker exists in any of them. |
| **Memory** | `SERVING_VIEW_EMPTY` | `vw_SubstrateBE_Demand_Memory_Region` and `_Forest` both return **0 rows** (Q058, Q060). The only populated Memory object is `vw_SubstrateBE_MemoryRawData` with 54,599,306 rows of raw telemetry (`DataDate`, `Dagname`, `Forest`, `ConsumedRate`, `InstalledMemoryGBPerServer`) — no governed key/value/scenario contract (Q055–Q056). |

**This independently confirms the V6.23-P1 decision was correct.** SSD was excluded from the
Viewer because it had no actuals locally; P1 now proves it has no actuals in SQL either.

### 1.4 A uniform serving layer exists but is not the actuals source

Discovery found 38 views named `vw_SubstrateBE_Demand_<Metric><Scenario>_<Granularity>`
covering all five MVP metrics with one clean contract
(`Fleet, Workload, Resource, Unit, DemandType, DateTime, Key, [Environment], Value, ForecastVersion`).

They are **not** usable as actuals: sampled rows are forward-dated (2026–2030),
`DemandType` is `Organic|Perturbation` rather than actual/forecast, and both
`Demand_HddBasilisk_Region` and the two `Demand_Memory` views return 0 rows.
They serve demand plan. Logged as UQ08.

---

## 2. What this means for the mixed cohort

The owner's target was **130–150 complete combinations spanning several metrics**.

| | |
|---|---|
| Available with >50 real observations | **722** |
| Metrics available | **3** (HDD, CPU, IOPS) |
| Target | 130–150 |
| Verdict | **Achievable, with room to select representatively rather than take what is easy** |

A defensible mixed cohort of ~150 can be assembled as, for example, CPU 60 + IOPS 58 +
a representative HDD Region sample of ~32 drawn across Enterprise / Consumer / Basilisk.
The exact selection is a P2/P3 decision and is **not** made here.

**SSD and Memory cannot be part of a Viewer cohort.** SSD stays Forecast-only; Memory is absent.

---

## 3. The material risk the owner must decide on

**CPU and IOPS actuals stop at 2023-07-20. HDD actuals run to 2026-08-17.**

That is roughly a three-year gap. A cohort that mixes them would backtest HDD over recent
history and CPU/IOPS over history that ends three years earlier. The series are individually
valid and all clear the threshold, but they are not contemporaneous.

This is logged as **UQ01** and is the single most important open question before P2.
It is a data-ownership question, not something that can be resolved by more querying.

---

## 4. Governance

| Constraint | Observed |
|---|---|
| Read-only | Connection opened with `readonly=True`. Only `SELECT` against `sys.*`, `INFORMATION_SCHEMA.*` and `GROUP BY` aggregates. No DDL, no DML. |
| No full extraction | Largest business-data result was a 234-row `GROUP BY`. Largest result overall was 1,214 rows from `sys.objects`, which is catalogue metadata. No row-level data was persisted. |
| No Parquet | 0 `.parquet` files written. |
| No models run | Only `.csv`, `.md`, `.json`, `.py` artifacts produced. |
| Shiny untouched | 0 `shiny_app` entries in `git status`. |
| V1–V5 untouched | 0 entries under `V1/`–`V5/`. |
| Nothing pushed | No `git push` executed. |

Three queries failed and are recorded rather than hidden:
`Q019` (`sys.dm_db_partition_stats` — insufficient permission; replaced by `sys.partitions` in `Q021`),
`Q028` (`SSD_Phoenix_Organic` — uses `Forest`, not `Key`; retried correctly as `Q051`),
`Q069` (`cpu_byDB_forest` — assumed `ModelVersion` column absent; unresolved, logged as UQ05).

---

## 5. Deliverables

| File | Purpose |
|---|---|
| `v6_24_p1_query_ledger.csv` | All 70 queries with status, duration and row count |
| `v6_24_p1_candidate_object_inventory.csv` | 17 candidate objects with existence, emptiness and evidence |
| `v6_24_p1_column_mapping.csv` | 99 columns with inferred role and confidence |
| `v6_24_p1_actuals_source_assessment.csv` | 20 metric/route/source assessments |
| `v6_24_p1_combination_capacity_by_metric.csv` | Capacity per metric with main gap |
| `v6_24_p1_route_capacity_detail.csv` | 16 routes with observation ranges and date spans |
| `v6_24_p1_extraction_readiness_plan.csv` | Extraction plan — **plan only, nothing extracted** |
| `v6_24_p1_unresolved_questions.csv` | 8 open questions with impact and resolution path |
| `v6_24_p1_validation.csv` | 20 checks, all PASS |
| `v6_24_p1_closure_summary.md` | This file |

---

## 6. Recommended next step

**Do not start extraction yet.** Two decisions belong to the owner first:

1. **UQ01 — the CPU/IOPS staleness.** Accept a cohort with non-contemporaneous history,
   or locate a fresher CPU/IOPS actuals source before extracting?
2. **UQ02/UQ03 — SSD and Memory.** Confirm that SSD remains Forecast-only and that Memory
   is dropped from the MVP metric list, or escalate to the data owner.

Once those are answered, P2 can extract the confirmed CPU (60) and IOPS (58) Region
combinations under a manifest. HDD needs no extraction — it is already local.

---

**V6_24_P1_SQL_TESSERACT_METADATA_READONLY_COMPLETED**

Stopping here. No extraction started, no cohort selected, no models run, no Shiny changes, no push.
