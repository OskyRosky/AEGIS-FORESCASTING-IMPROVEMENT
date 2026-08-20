# V6.0F-R5b — Recommended Storage Architecture

## 1. Decision

**DuckDB single-file database for the fact data, plus four small CSV metadata slices for the dropdowns.**

| Measure | Plain CSV | **DuckDB** | Improvement |
|---|---:|---:|---:|
| Disk | 421.34 MB | **23.51 MB** | **94% smaller** |
| Memory held in the Shiny session | 155.9 MB | **~0 MB** | eliminated |
| Typical key filter | 0.080 s *after* a 0.69 s load | **0.005 s** | ~150× faster cold |
| Lazy query | no | **yes** | — |

Parquet was measured and **rejected**: string predicates such as `grepl` cannot be pushed down, so a key filter degraded to **3.17 s**, and the dataset was 183 MB — eight times larger than DuckDB because column types were not inferred.

---

## 2. Folder structure

```
V6/data/storage/
├── r6_phase1.duckdb              23.5 MB   <- the only fact source Shiny reads
└── ui_metadata/
    ├── available_scenarios.csv       14 rows
    ├── available_keys.csv           896 rows
    ├── available_versions.csv        16 rows
    └── available_model_types.csv     88 rows
```

The R6 CSV artifacts stay where they are, as the **immutable extraction record**. Shiny never reads them.

| DuckDB table | Rows | Source artifact |
|---|---:|---|
| `viewer_hdd` | 817,386 | r6_phase1_viewer_hdd.csv |
| `forecast_hdd` | 565,104 | r6_phase1_forecast_hdd.csv |
| `forecast_ssd` | 651,480 | r6_phase1_forecast_ssd_phoenix.csv |

---

## 3. How Shiny reads metadata

Load the four CSV slices **once at app start**. Combined they are 0.05 MB and load in under 0.01 s.

Every dropdown is populated from these slices, filtered in memory by the cascade `Metric → Scenario → Granularity → Key → Forecast Version → Model/Type`. **No dropdown ever touches the fact tables.**

---

## 4. How Shiny reads a filtered series

Open a **read-only** connection per request, query, close.

```r
con <- DBI::dbConnect(duckdb::duckdb(shared_home = FALSE),
                      dbdir = "data/storage/r6_phase1.duckdb", read_only = TRUE)
on.exit(DBI::dbDisconnect(con, shutdown = TRUE))

DBI::dbGetQuery(con, "
  SELECT date, value, series_type, model_type
  FROM viewer_hdd
  WHERE metric = ? AND scenario_ui_label = ? AND granularity = ?
    AND lower(key) = lower(?)
  ORDER BY date", list(metric, scenario, granularity, key))
```

Two rules:

| # | Rule |
|---|---|
| Q1 | Always parameterised. Never string-concatenated SQL. |
| Q2 | Always `lower(key) = lower(?)` — Basilisk stores `namprd07` while EDB stores `NAMPRD07` (risk RB1). |

---

## 5. How memory stays bounded

| Mechanism | Effect |
|---|---|
| Read-only connection, closed after each query | Nothing persists in the session |
| `SELECT` only the columns the chart needs | Typical result is 1,097–2,196 rows |
| Dropdowns served from 0.05 MB of metadata | No fact scan for UI population |
| Fact CSV files listed as `must_not_read` | Prevents accidental `fread` of 187 MB |

Measured worst case for a single chart request: **2,196 rows in 0.006 s**.

---

## 6. How lineage is preserved

| Layer | Artifact |
|---|---|
| Source query | `r6_phase1_lineage.csv` (table, columns, filters, timestamp) |
| Extraction unit | `r6_phase1_extraction_manifest.csv` (14 units with filters and row counts) |
| Row level | `extraction_run_id` column on every row — `R6P1-20260812T100822` |
| Storage mapping | `r6_phase1_storage_manifest.csv` |
| Raw values | `raw_type` retained alongside every normalised label |

The DuckDB build must be a **derivation, never an edit**: tables are created from the R6 CSV files, so any value in the app traces back to Tesseract through the manifest.

---

## 7. Preparing for Docker and Azure

| Concern | Why DuckDB fits |
|---|---|
| Docker image size | A 23.5 MB file adds almost nothing; 421 MB of CSV would |
| No server process | DuckDB is embedded — no extra container, no port, no credentials |
| Azure App Service / Container Apps | Ships as a read-only file inside the image or on a mounted volume |
| Azure Blob | The file can be downloaded at startup or mounted |
| Dependencies | Only `duckdb` and `DBI` need to be added to the image. `arrow` is not required since Parquet was rejected |
| Concurrency | Read-only connections are safe for multiple simultaneous sessions |

---

## 8. Scaling to R6 Phase 2

Phase 1 compressed 2,033,970 rows into 23.51 MB — about **12 bytes per row**.

Phase 2 adds roughly 6,020,004 rows, projecting to **~70–90 MB**, for a combined database near **95–115 MB**. That remains well inside what a container image and a read-only query layer handle comfortably. **Phase 2 does not require a different architecture.**

---

## 9. What must not happen

| # | Prohibition |
|---|---|
| N1 | Shiny must never `read.csv` or `fread` any `r6_phase1_*.csv` fact file |
| N2 | No fact table is loaded into a reactive value or global object |
| N3 | The DuckDB file is never written to at runtime — read-only connections only |
| N4 | Metadata slices are never regenerated at runtime; they are build artifacts |
| N5 | Key matching is never case-sensitive |

---

## 10. Residual risks

| ID | Risk | Severity |
|---|---|---|
| RB1 | Basilisk and EDB use different key namespaces and casing | 🔴 High |
| RB5 | The DuckDB file must be rebuilt whenever R6 re-extracts | 🟠 Medium |
| RB9 | Basilisk exposes only two model types | 🟠 Medium |
| RB7 | ~506 MB of benchmark byproducts remain on disk, reproducible from `bench_storage.R` | 🟡 Low |
