# V6.24-P3 — Governed Data Extraction to Parquet

**Stage:** V6.24-P3
**Status:** **EXTRACTION COMPLETED.** Next stage is **P4**.
**Queries:** 4, each filtered to the approved keys.
**Files written:** 4 raw Parquet + 4 manifest copies.
**HDD:** not extracted, by design.

---

## 1. What was extracted

| Unit | Metric | Source object | Rows | Series | Date range |
|---|---|---|---:|---:|---|
| LVWE | SSD | `forecast_substrateBE_ssd_phx_lvwe_metrics` | **6,550** | 50 keys | 2026-04-13 → 2026-08-22 |
| LVNE | SSD | `forecast_substrateBE_ssd_phx_lvne_metrics` | **6,600** | same 50 keys | 2026-04-09 → 2026-08-22 |
| CPU | CPU | `forecast_substrateBE_cpu_actual_region` | **11,228** | 20 | 2022-01-04 → 2023-07-20 |
| IOPS | IOPS | `forecast_substrateBE_iops_actual_region` | **20,501** | 20 | 2020-06-23 → 2023-07-20 |
| | | **Total** | **44,879** | **90** | |

**90 non-HDD series.** SSD contributes **50 observed series**, not 100: LVWE and LVNE are two
forecast variants over one shared observed series.

Every file was **re-read from disk and validated** after writing. No extraction was treated as
complete until the written file had been read back: row counts matched the SQL result exactly,
zero unexpected keys, zero missing keys, sha256 recorded for each file.

---

## 2. Extraction taxonomy

```
HDD    -> DB Type (EDB | Basilisk) -> Segment (Consumer | Enterprise, EDB only)
          -> Granularity (Forest | Region) -> Key
          ALREADY_LOCAL_NOT_EXTRACTED

SSD    -> DB Type Phoenix -> Variant (LVWE | LVNE) -> Granularity Forest -> Key
          Scenario NOT_APPLICABLE: no scenario axis exists in the source
          Variant is a FORECAST variant, not a second observed series

CPU    -> Scenario (Consumed | Failover) -> Granularity Region -> Key
          DB Type UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE. Not invented.

IOPS   -> Scenario (Consumed | Failover) -> Granularity Region -> Key
          DB Type NOT_APPLICABLE by design

Memory -> not selected, not extracted. Awareness gap only.
```

`v6_24_p3_full_taxonomy_extracted_series_report.csv` holds **140 rows** — one per extracted
series per variant — with all conditional axes populated and **zero blank cells**. Explicit
placeholders are used throughout so UI/UX can build conditional filters without guessing.

---

## 3. Two findings I am not glossing over

### DQ01 — the SSD source contains one exact-duplicate row per key

LVWE holds 6,550 rows over only **6,500 distinct `(series_key, series_date)` pairs**.
The extras are **50 duplicate groups, exactly one per forest key**, all on
`series_date = 2026-04-22` with `window_start = 2026-04-16`.

All 50 groups carry an **identical** `actual_value`, `forecast_value` and `window_start`. They
are byte-identical rows, not conflicting measurements. LVNE shows the same pattern.

**Consequence:** the real observation count per SSD key is **130 distinct dates**, not 131 rows.
Both figures are far above the 50 threshold, so no key fails and the cohort is unaffected.

**I left the duplicates in the raw files deliberately.** Raw means raw: P3's job is faithful
capture, not cleaning. **P4 must dedupe on `(series_key, series_date)`** when building
`actuals_normalized`. Keep-first is safe and lossless because the rows are identical.

This also refines what I reported in P2A. I said "131 parseable actuals per key". More precisely:
**131 rows, 130 distinct dates**. Both clear the threshold; the earlier phrasing was imprecise.

### DQ02 — CPU and IOPS span only 10 distinct regions, not 20

Each metric has 20 series, but over just **10 distinct keys**, with every key appearing in both
`Consumed` and `Failover`.

This is structurally valid — a series is `(scenario, key)`, and P2's rule of 10 Consumed +
10 Failover is satisfied. But **geographic coverage is 10 regions, not 20**.

The cause is mine: in P2 I ran the region round-robin independently per scenario over pools with
identical observation counts, so both passes selected the same 10 keys. The rule I wrote said
"balance keys across available regions" and I under-served it.

**This is a selection-diversity weakness, not a data defect.** I did not silently change the
cohort here — P3 extracts what P2/P2A approved. Logged as **P3-UQ01** for a P4 decision.
Reselection is cheap: the pools hold 30 CPU and 29 IOPS keys per scenario, so 20 distinct
regions is achievable.

---

## 4. SSD LVWE / LVNE consistency

| Check | Expected | Observed | Result |
|---|---|---|---|
| Observed series | 50, not 100 | **50** | PASS |
| `Mean_Actual` identical | 100% | **6,650 of 6,650 matched rows** | PASS |
| `Mean_Actual` differing | 0 | **0** | PASS |
| `Mean_Forecast` differing | > 0 | **2,520 of 6,650 (37.9%)** | PASS |
| Max date | 2026-08-22 | **2026-08-22** | PASS |
| Non-parseable `Mean_Actual` | 0 | **0** | PASS |

The variants diverge on roughly 38% of rows for these 50 keys and agree on the rest. Both are
retained as forecast baselines for P5/P6 comparison.

**On the varchar cast:** `Mean_Actual` is varchar in source. I kept the original text as
`actual_value_source_text` alongside the cast `actual_value`, so the conversion is **auditable
rather than trusted**. Zero rows have source text present with a null cast — no silent coercion,
no silent row dropping.

---

## 5. CPU / IOPS staleness

| Metric | Earliest | Latest | Expected | Source changed | Days behind SSD |
|---|---|---|---|---|---:|
| CPU | 2022-01-04 | **2023-07-20** | 2023-07-20 | **NO** | 1,129 |
| IOPS | 2020-06-23 | **2023-07-20** | 2023-07-20 | **NO** | 1,129 |

The source has not moved since P1. All 40 CPU and IOPS taxonomy rows carry
`STALE_ACTUALS_SOURCE, latest date 2023-07-20`. The caveat is in the data, not just in prose.

A second gap: **neither table carries any forecast column** (`NOT_PRESENT_IN_SOURCE`). Unlike
SSD, CPU and IOPS will have only the 15 generated models with no external baseline to compare
against. Logged as DQ04 / P3-UQ03.

---

## 6. What this cohort still does NOT have

**Only HDD has 15 governed model backtests.** All 90 extracted series carry an explicit
disclaimer in their `caveat` column:

> *15 governed model backtests DO NOT exist yet and must be generated in P5.*

The cohort becomes Viewer-complete only after **P5** and **P6**. The P7 gate is what must
enforce this, and `navigation_contract` / `taxonomy_counts` must be derived **after** the gate
so a series that failed cannot reach the selector. That is what prevents a repeat of the V6.23
failure mode: a selectable combination that renders "Backtest unavailable".

---

## 7. Governance

| Constraint | Observed |
|---|---|
| Only approved series extracted | 90 exactly; 0 unexpected keys, 0 missing keys |
| HDD not extracted | 0 HDD files; no HDD rows in any raw file |
| Nothing under `processed/` | **0 files** |
| No normalization | Raw files retain source column names and the duplicate rows |
| No models, forecasts, accuracy or rankings | None. SSD accuracy columns are **source** columns copied verbatim, not computed |
| No `navigation_contract` / `taxonomy_counts` | None created |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |

---

## 8. Deliverables

**Raw data** — `V6/data/raw/v6_24_mvp_cohort/`

| Path | Rows | Bytes |
|---|---:|---:|
| `ssd/ssd_lvwe_raw.parquet` | 6,550 | see inventory |
| `ssd/ssd_lvne_raw.parquet` | 6,600 | see inventory |
| `cpu/cpu_actuals_raw.parquet` | 11,228 | see inventory |
| `iops/iops_actuals_raw.parquet` | 20,501 | see inventory |
| `manifests/raw_extraction_manifest.csv` | 4 | |
| `manifests/raw_file_inventory.csv` | 4 | |
| `manifests/raw_schema_inventory.csv` | 82 | |
| `manifests/raw_row_count_validation.csv` | 4 | |

**Reports** — `V6/outputs/v6_24_p3_governed_data_extraction_to_parquet/`

| File | Rows |
|---|---:|
| `v6_24_p3_reduced_status_table.csv` | 12 |
| `v6_24_p3_extraction_manifest.csv` | 4 |
| `v6_24_p3_full_taxonomy_extracted_series_report.csv` | **140** |
| `v6_24_p3_full_140_cohort_context_report.csv` | **140** |
| `v6_24_p3_raw_file_inventory.csv` | 4 |
| `v6_24_p3_raw_schema_inventory.csv` | 82 |
| `v6_24_p3_raw_row_count_validation.csv` | 4 |
| `v6_24_p3_source_to_parquet_mapping.csv` | 4 |
| `v6_24_p3_query_ledger.csv` | 4 |
| `v6_24_p3_ssd_lvwe_lvne_consistency_check.csv` | 8 |
| `v6_24_p3_cpu_iops_staleness_report.csv` | 2 |
| `v6_24_p3_data_quality_report.csv` | 5 |
| `v6_24_p3_unresolved_questions.csv` | 3 |
| `v6_24_p3_validation.csv` | 33 |
| `v6_24_p3_closure_summary.md` | — |

---

## 9. Next stage

**P4 — Candidate Cohort Selection / Normalization.** It must:

1. Build `cohort_manifest.parquet` covering all **140** series, HDD included, so Viewer and
   Forecast share one cohort.
2. Build `actuals_normalized.parquet`, **deduplicating SSD on `(series_key, series_date)`** and
   recording the row delta.
3. Decide **P3-UQ01**: keep CPU/IOPS at 10 regions × 2 scenarios, or reselect for 20 distinct
   regions.
4. Build `data_dictionary.csv`.

None of the three open questions blocks P4.

---

**V6_24_P3_GOVERNED_DATA_EXTRACTION_TO_PARQUET_COMPLETED**

Stopping here. P4 not started, nothing normalized, no models run, no forecasts generated, no
accuracy or rankings calculated, Shiny untouched, no push.
