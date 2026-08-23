# V6.24-P2 — Controlled Parquet Extraction Plan

**Stage:** V6.24-P2
**Purpose:** define exactly what P3 will extract, where it will land, and which series form
the MVP cohort.
**Mode:** Planning only.

> ## P2 IS NOT THE EXTRACTION STAGE
>
> **P3 is the extraction stage, not P2.** P2 wrote **zero** Parquet files, extracted **zero**
> time-series rows, and ran **zero** models. The only SQL issued was 6 grouped-count queries
> against a budget of 10, used solely to size the candidate pools for representative selection.

---

## 1. The cohort

**140 series across four metrics. 90 to extract in P3. 50 already local.**

| Metric | Series | Pool | Source status | P3 extraction | Caveat |
|---|---:|---:|---|---|---|
| HDD | **50** | 596 | Local Parquet | **No** | None — the only metric that is product-complete today |
| SSD | **50** | 136 | `ssd_phx_lvwe` / `lvne` | **Yes** | Windowed actuals; no 15-model backtests yet |
| CPU | **20** | 60 | `cpu_actual_region` | **Yes** | `STALE_ACTUALS_SOURCE` to 2023-07-20; no backtests yet |
| IOPS | **20** | 58 | `iops_actual_region` | **Yes** | `STALE_ACTUALS_SOURCE` to 2023-07-20; no backtests yet |
| Memory | **0** | 0 | None | No | `BLOCKED_NO_USEFUL_ACTUALS_SOURCE` |

Every selected series clears **more than 50 observed actuals**. No series was chosen by taking
the head of a list.

---

## 2. Selection at a glance

Full detail in `v6_24_p2_selection_methodology.md`. Summary:

**HDD** — equal allocation across all six route families (9/8/9/8/8/8), remainder to the two
largest pools. Within each route, even stride sampling across the observation-count range.
Forest 26 / Region 24.

**SSD** — `NAMPRD07` and `NAMPRD08` force-included because P1B reconciled them against the
owner's AX4 dashboard. The remaining 48 chosen by round-robin across forest-key prefixes,
yielding **32 distinct geographies**.

> **Verified by V6.24-P2A.** The eligible SSD pool spans 24–131 observations, but that is a
> *pool* statistic. All 50 **selected** keys were re-measured directly from SQL and each has
> exactly **131** parseable actuals, 0 non-parseable and 0 null. No key at or below the
> 50-observation threshold was ever selected. See
> `V6/outputs/v6_24_p2a_ssd_selected_cohort_verification/`.

**CPU and IOPS** — exactly 10 `Consumed` + 10 `Failover` each, with region-prefix round-robin
inside each scenario.

---

## 3. Two decisions this plan locks in

### 3.1 SSD storage format — long, with `forecast_variant`

LVWE and LVNE hold an **identical** `Mean_Actual`; only `Mean_Forecast` differs. So:

- `actuals_normalized.parquet` loads `Mean_Actual` from **LVWE only** → 50 series.
- `forecast_outputs.parquet` loads **both** variants as two forecast baselines.

The LVNE template emits its actual column as `actual_value_DO_NOT_LOAD_AS_ACTUALS`, so the
rule is enforced by the column name itself rather than by documentation alone. Loading both
would silently inflate the cohort from 50 SSD series to 100.

### 3.2 `Mean_Actual` must be CAST

`Mean_Actual` is stored as **varchar** while `Mean_Forecast` is `float` — a mixed-typed table.
`P2Q004` confirmed all 17,596 values parse cleanly via `TRY_CAST`, with **0 non-numeric rows**,
so extraction is safe today. The templates cast explicitly. **P3 must fail loudly on any
`TRY_CAST` null rather than silently dropping rows**, because the varchar typing could admit
junk in a later refresh. Logged as P2-UQ01.

---

## 4. What the cohort does NOT have yet

**Only HDD has 15 governed model backtests.**

| Metric | Actuals | 15 governed backtests | Forecast baseline |
|---|---|---|---|
| HDD | Local | **Present** | Present |
| SSD | P3 | **Absent — P5** | 2 external (LVWE, LVNE) |
| CPU | P3 | **Absent — P5** | **None in source** |
| IOPS | P3 | **Absent — P5** | **None in source** |

This plan makes no claim otherwise. All 90 non-HDD rows carry an explicit disclaimer in their
`caveat` column, verified by check V27.

**Consequence:** 90 of the 140 series would fail the Viewer rule *"must have actuals + 15
models"* today. The cohort becomes Viewer-complete only after **P5** and **P6**. The P7
completeness gate is what must enforce this — no series may reach the Viewer selector before it
passes. This is the same failure mode as V6.23: a selectable combination that renders
"Backtest unavailable".

A second gap worth flagging: CPU and IOPS actuals tables carry **no forecast column at all**.
Unlike SSD, they will have only the 15 generated models with no external baseline to compare
against (P2-UQ05).

---

## 5. Destination structure

```
V6/data/raw/v6_24_mvp_cohort/          <- P3 writes here
  ssd/   ssd_lvwe_actuals_raw.parquet
         ssd_lvne_actuals_raw.parquet
  cpu/   cpu_actuals_raw.parquet
  iops/  iops_actuals_raw.parquet
  manifests/ extraction_manifest.csv

V6/data/processed/v6_24_mvp_cohort/    <- P4/P5/P6/P7 write here
  cohort_manifest.parquet              (P4) all 140 series, HDD included
  actuals_normalized.parquet           (P4)
  model_backtests_15_models.parquet    (P5)
  forecast_outputs.parquet             (P6)
  accuracy_metrics.parquet             (P6)
  data_dictionary.csv                  (P4)
  validation_summary.csv               (P7)
```

**HDD is not re-downloaded but does enter `cohort_manifest.parquet`**, so Viewer and Forecast
read one unified cohort. **Shiny must eventually read only from `processed/`** — never SQL,
never scattered outputs.

---

## 6. SQL templates

`v6_24_p2_extraction_sql_templates.sql` holds **4 statements, all `SELECT`**, with zero banned
keywords in executable SQL and every selected key embedded literally. There is deliberately
**no HDD template**: re-downloading HDD is prohibited.

---

## 7. Governance

| Constraint | Observed |
|---|---|
| No data extracted | 6 grouped-count queries; largest result 137 rows of counts, not time series |
| SQL budget | **6 of 10** |
| No Parquet | 0 files written |
| No models | Only `.csv`, `.md`, `.sql`, `.json`, `.py` artifacts |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |
| HDD not re-downloaded | No HDD template exists; all 50 HDD rows are `ALREADY_LOCAL` |

One query failed and is recorded rather than hidden: `P2Q001` attempted `AVG(Mean_Actual)` and
failed because the column is varchar. That failure is what surfaced the type issue in §3.2;
it was retried correctly as `P2Q004` with `TRY_CAST`.

---

## 8. Deliverables

| File | Rows | Purpose |
|---|---:|---|
| `v6_24_p2_reduced_status_table.csv` | 11 | Stage status P0 through P9 |
| `v6_24_p2_full_140_mvp_cohort_plan.csv` | **140** | The complete MVP cohort |
| `v6_24_p2_p3_90_series_extraction_plan.csv` | **90** | Only what P3 downloads |
| `v6_24_p2_hdd_50_local_reference_plan.csv` | **50** | Local HDD reference |
| `v6_24_p2_ssd_50_extraction_plan.csv` | **50** | SSD detail |
| `v6_24_p2_cpu_20_extraction_plan.csv` | **20** | CPU detail |
| `v6_24_p2_iops_20_extraction_plan.csv` | **20** | IOPS detail |
| `v6_24_p2_metric_axis_contract.csv` | 5 | Conditional axes per metric |
| `v6_24_p2_parquet_destination_plan.csv` | 13 | Path, artifact, writing stage |
| `v6_24_p2_selection_methodology.md` | — | Reproducible algorithm |
| `v6_24_p2_extraction_sql_templates.sql` | 4 SELECTs | P3 templates, not executed |
| `v6_24_p2_unresolved_questions.csv` | 5 | Open items, none blocking P3 |
| `v6_24_p2_validation.csv` | 28 | All checks |
| `v6_24_p2_closure_summary.md` | — | This file |
| `v6_24_p2_query_ledger.csv` | 6 | Every SQL query with auth mode |

---

## 9. Recommended next step

**P3 — Governed Data Extraction to Parquet.** Execute the four templates, write the four raw
Parquet files plus an extraction manifest, and validate row counts against the per-series
`observation_count` already recorded in this plan.

None of the five open questions blocks P3.

---

**V6_24_P2_CONTROLLED_PARQUET_EXTRACTION_PLAN_COMPLETED**

Stopping here. P3 not started, no data extracted, no Parquet written, no models run, no Shiny
changes, no push.
