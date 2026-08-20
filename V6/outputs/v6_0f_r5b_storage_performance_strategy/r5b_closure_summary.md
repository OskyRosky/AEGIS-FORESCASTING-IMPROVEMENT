# V6.0F-R5b — Storage & Performance Strategy — Closure Summary

**Status token:** `V6_0F_R5B_STORAGE_PERFORMANCE_STRATEGY_COMPLETED`

**Nature:** measurement and design. No Shiny change, no re-extraction, no Docker, no Azure.

---

## 1. What was measured

Five options, benchmarked against the real R6 Phase 1 artifacts (2,033,970 rows, 421 MB).

| Option | Disk | Cold key filter | Session memory | Verdict |
|---|---:|---:|---:|---|
| A — Plain CSV | 421.34 MB | 0.69 s load + 0.080 s | 155.9 MB | ❌ Rejected |
| B — Partitioned CSV | 322.81 MB | ~0.25 s | ~30 MB per partition | ❌ Rejected |
| **C — DuckDB** | **23.51 MB** | **0.005 s** | **~0 MB** | ✅ **Recommended** |
| D — Parquet partitioned | 183.42 MB | 3.174 s | ~0 MB | ❌ Rejected |
| E — UI metadata slices | 0.05 MB | 0.003 s | negligible | ✅ Complement |

All 8 mandatory benchmarks (B1–B8) were executed on CSV, DuckDB and Parquet.

---

## 2. What is recommended

**DuckDB** for the fact data, **four CSV metadata slices** for the dropdowns.

| Reason | Evidence |
|---|---|
| 94% smaller than CSV | 23.51 MB vs 421.34 MB |
| Removes the session memory problem entirely | 0 MB vs 155.9 MB per session |
| Fastest measured queries | 0.002–0.008 s across all eight benchmarks |
| Genuine lazy evaluation | Only matching rows leave the engine |
| Docker and Azure ready | Embedded, no server, no port, no credentials |
| Scales to Phase 2 | Projected 95–115 MB combined |

---

## 3. What is not recommended

| Option | Why |
|---|---|
| Plain CSV | 155.9 MB per session does not scale with concurrent users |
| Partitioned CSV | 14 files to keep in sync, still loads whole partitions, no pushdown |
| **Parquet** | Measured, not assumed: string predicates cannot be pushed down, so a key filter took **3.17 s** versus 0.005 s in DuckDB. Also 8× larger because column types were not inferred. |

---

## 4. Files created

| File | Purpose |
|---|---|
| storage_options_comparison.csv | Five options with measured figures |
| benchmark_results.csv | 36 measured benchmark rows |
| storage_sizes.csv | Disk footprint per option |
| recommended_storage_architecture.md | Full architecture and query patterns |
| ui_metadata_strategy.csv | Four dropdown slices |
| shiny_loading_contract.csv | 14 rules covering every read on both pages |
| r6_phase1_storage_manifest.csv | CSV → DuckDB mapping |
| r5b_risk_register.csv | 10 risks |
| r5b_validation.csv | 24 checks, all PASS |
| bench_storage.R · diag_keys.R | Reproducible benchmark scripts |
| bench/ | DuckDB, Parquet, partitioned CSV and metadata built during the benchmark |

---

## 5. Finding that matters more than the benchmark

**Basilisk and EDB use different key namespaces in the same table.**

| Scenario | Key format | Example |
|---|---|---|
| HDD - EDB | uppercase | `NAMPRD07` |
| HDD - Basilisk | lowercase, short | `namprd07`, `apcprd01` |

The benchmark caught it because a case-sensitive filter returned **0 rows** where R6 had reported **954**. R6 was right — its check was case-insensitive.

**Consequence for R7:** key matching must be case-insensitive (`lower(key) = lower(?)`), and the Key dropdown must be scoped per scenario. Logged as risk RB1.

---

## 6. Dependencies added

`duckdb 1.5.5`, `arrow 25.0.0` and `DBI 1.3.0` were installed in the local R environment, which previously had none of them.

`arrow` is **not required** going forward since Parquet was rejected. Only **`duckdb` and `DBI`** need to enter the Docker image.

---

## 7. Is R7 unblocked?

**Yes.**

| Prerequisite | Status |
|---|---|
| Data extracted and validated | ✅ R6 Phase 1 |
| Dictionaries for scenario, key, version, type | ✅ R3 |
| UI contract and cascade | ✅ R2 |
| Storage format chosen with evidence | ✅ **R5b** |
| Loading contract per control and chart | ✅ **R5b** |

R7 can now build the Scenario Resolver against DuckDB, with the key-casing rule built in from the start.

---

## 8. Pending for R6 Phase 2

| Item | Status |
|---|---|
| Storage architecture | ✅ Resolved — no change needed |
| Projected size | ~70–90 MB added, ~95–115 MB combined |
| O1 (SSD-MCDB) | Still open |
| O3 (CPU byDB / DBType control) | Still open |
| Authorisation | Not granted |

---

## 9. Governance

| Invariant | Result |
|---|---|
| No Shiny changes | Respected |
| No Tesseract re-extraction | Respected |
| R6 artifacts unmodified | Respected — opened read-only |
| No SQL writes | Respected |
| No simulated data, no zero filling | Respected |
| Assistant and LLM untouched | Respected — hash A4DB09B4 |
| V1 to V5 untouched | Respected |
| No Docker, no Azure | Respected |
| Not advanced to R7, R8, R9, R9b, R9c, R10, G1, G2 or R6 Phase 2 | Respected |
