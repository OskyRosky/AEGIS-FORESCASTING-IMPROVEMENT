# V6.24-P3B — Raw Extraction Inventory + CPU/IOPS Diversity Review

**Stage:** V6.24-P3B — small control stage
**Mode:** Documentation, inventory and decision support only.
**SQL queries:** **0.** Nothing was extracted, written, normalized or deduplicated.
**Verdict:** the P3 data is **ACCEPTABLE for MVP P4**. One owner decision is offered, not taken.

---

## 1. The distinction that was missing from P3

P3's reporting was accurate but too aggregated. The core confusion is that **two different
counts are both correct**, depending on what you are counting:

| View | Purpose | SSD | CPU | IOPS | Total |
|---|---|---:|---:|---:|---:|
| **A. Observed series** | product / UI truth | **50** | 20 | 20 | **90** |
| **B. Raw extraction units** | physical file truth | **100** | 20 | 20 | **140** |

The entire 50-row gap is SSD. `ssd_lvwe_raw.parquet` and `ssd_lvne_raw.parquet` each hold the
same 50 forest keys, but they are **two forecast variants over one observed series**, not two
observed series.

Both views are now materialised as separate files so neither can be mistaken for the other:

- `v6_24_p3b_observed_series_inventory_90.csv` — **90 rows**
- `v6_24_p3b_raw_extraction_unit_inventory.csv` — **140 rows**

The reconciliation is explicit: **140 physical units − 50 LVNE duplicate-variant units = 90
observed series** (validation check V21).

Every LVNE row is flagged `is_duplicate_physical_variant = TRUE` and
`is_observed_series = FALSE`, so a downstream loader cannot silently double-count.

---

## 2. Exact downloaded inventory

Every row in both inventories carries all nine axes populated with explicit values and
**zero blank cells** across 230 rows:

`metric, db_type, variant, scenario, segment, granularity, key, route_path, ui_filter_path`

Plus per-series measurements read directly from the Parquet: `min_date`, `max_date`,
`row_count`, `distinct_date_count`, `duplicate_row_count`, `parseable_actual_count`,
`non_parseable_actual_count`, `freshness_status`, `caveat`.

### UI filter paths, exactly as they will render

```
SSD    Metric=SSD  > DBType=Phoenix > Variant=LVWE|LVNE > Granularity=Forest > Key=<50 forests>
CPU    Metric=CPU  > Scenario=Consumed|Failover > Granularity=Region > Key=<10 regions>
IOPS   Metric=IOPS > Scenario=Consumed|Failover > Granularity=Region > Key=<10 regions>
HDD    Metric=HDD  > DBType=EDB|Basilisk > Segment=Consumer|Enterprise > Granularity=Forest|Region > Key
Memory NOT_RENDERED
```

Three axis rules that UI/UX must respect, all now recorded in
`v6_24_p3b_metric_axis_value_inventory.csv` with `applies_to_ui`:

1. **SSD `Variant` changes the forecast line, never the actual line.** LVWE and LVNE hold an
   identical `Mean_Actual`. If selecting a variant moves the observed curve, that is a bug.
2. **CPU `db_type` must not be rendered.** Its value is the placeholder
   `UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE`. It documents an absence; it is not a filter option.
3. **`Segment` is conditional and belongs only to HDD.** It applies under EDB and is
   `NOT_APPLICABLE` under Basilisk. No extracted metric has a segment axis.

---

## 3. CPU / IOPS diversity review

### What the matrices show

`v6_24_p3b_cpu_scenario_key_matrix.csv` and `..._iops_...` list every key against every
scenario. The result is unambiguous:

| Metric | Series | Unique keys | Scenarios | Keys shared by both scenarios |
|---|---:|---:|---:|---:|
| CPU | 20 | **10** | 2 | **10 of 10** |
| IOPS | 20 | **10** | 2 | **10 of 10** |

Every key appears under both `Consumed` and `Failover`. Each key therefore contributes 2 of the
20 series.

### Is 20 distinct keys achievable?

**Yes.** Measured from the P2 candidate pool:

| Metric | Distinct keys in pool | Per scenario |
|---|---:|---|
| CPU | **30** | Consumed 30, Failover 30 |
| IOPS | **29** | Consumed 29, Failover 29 |

There is ample headroom. The constraint was never the data.

### Whose fault, and what kind of fault

Mine, in P2. I ran the region round-robin **independently per scenario** over pools with
identical observation counts, so both passes ranked the same keys first and selected the same
10. My own rule said "balance keys across available regions" and I served it only within each
scenario, not across the metric.

**This is a selection-diversity weakness, not a data defect.** The series count is exactly as
planned, every series clears its threshold, and P3 validated 33/33.

### The trade-off I want on the record

Option B is not strictly better, and I would be misleading you if I presented it that way.

**Because every key exists under both scenarios, the Viewer can compare `Consumed` against
`Failover` for the same region.** That is a real demand-planning question — how much headroom
does this region need if failover engages. Move to 20 distinct keys and that comparison
disappears entirely, because no region would appear under both.

So the choice is: **geographic breadth** versus **like-for-like comparability**. Not
"diverse" versus "lazy".

---

## 4. Decision required from the owner

| Option | Meaning | Work | Recommended |
|---|---|---|---|
| **A. KEEP_CURRENT_MVP** | 20 series over 10 keys × 2 scenarios, as extracted | **None** | **YES** |
| B. PATCH_DIVERSITY_BEFORE_P4 | Reselect for 20 distinct keys, 10 per scenario | Small: one extra filtered SELECT per metric | No |

**Recommendation: Option A.** The data is valid, the counts match the plan, the owner is
prioritising MVP speed, and the current structure supports an analysis that Option B would
remove. Option B remains cheap if geographic breadth later matters more than comparability.

**I have not applied either option.** Nothing was re-extracted and nothing was patched.

---

## 5. What the cohort still lacks

`v6_24_p3b_full_140_context_inventory.csv` records `has_15_governed_backtests` per series:

| Metric | Series | Has 15 governed backtests |
|---|---:|---|
| HDD | 50 | **TRUE** — already local |
| SSD | 50 | **FALSE** — P5 |
| CPU | 20 | **FALSE** — P5 |
| IOPS | 20 | **FALSE** — P5 |

**50 of 140.** Every extracted row also carries `ui_visible_now = FALSE` and
`ui_visible_after_p5_p6_p7 = TRUE`. The cohort is not Viewer-ready and this inventory says so
in the data, not only in prose.

---

## 6. Governance

| Constraint | Observed |
|---|---|
| No new SQL extraction | **0 queries.** No query ledger exists for this stage |
| No raw Parquet written or overwritten | 4 files present, **0 modified** |
| No processed Parquet | `processed/v6_24_mvp_cohort` does not exist; 0 legacy files touched |
| No normalization, no deduplication | The 2026-04-22 duplicates remain in the raw files, reported not removed |
| No models, forecasts, accuracy or rankings | None |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |

---

## 7. Deliverables

| File | Rows | Purpose |
|---|---:|---|
| `v6_24_p3b_reduced_status_table.csv` | 8 | Stage status |
| `v6_24_p3b_observed_series_inventory_90.csv` | **90** | Product/UI truth |
| `v6_24_p3b_raw_extraction_unit_inventory.csv` | **140** | Physical file truth |
| `v6_24_p3b_ui_filter_tree_preview.csv` | 5 | Filter tree per metric |
| `v6_24_p3b_metric_axis_value_inventory.csv` | 24 | Every axis value with `applies_to_ui` |
| `v6_24_p3b_ssd_variant_inventory.csv` | **50** | LVWE vs LVNE per key |
| `v6_24_p3b_cpu_scenario_key_matrix.csv` | 10 | Scenario × key |
| `v6_24_p3b_iops_scenario_key_matrix.csv` | 10 | Scenario × key |
| `v6_24_p3b_cpu_iops_diversity_decision_table.csv` | 2 | Both options with trade-offs |
| `v6_24_p3b_full_140_context_inventory.csv` | **140** | Whole cohort, HDD as context |
| `v6_24_p3b_validation.csv` | 23 | All checks |
| `v6_24_p3b_closure_summary.md` | — | This file |

---

## 8. Next stage

**P4 — Cohort Normalization / Manifest Freeze.** It must:

1. Build `cohort_manifest.parquet` over all **140** series, HDD included.
2. Build `actuals_normalized.parquet` loading SSD actuals from **LVWE only**, deduplicated on
   `(series_key, series_date)`, with the row delta recorded.
3. Load **both** LVWE and LVNE as forecast baselines, tagged by `forecast_variant`.
4. Apply the owner's CPU/IOPS decision.
5. Build `data_dictionary.csv`.

---

**V6_24_P3B_RAW_EXTRACTION_INVENTORY_AND_DIVERSITY_REVIEW_COMPLETED**

Stopping here. P4 not started, nothing re-extracted, no Parquet written, nothing normalized, no
models run, Shiny untouched, no push.
