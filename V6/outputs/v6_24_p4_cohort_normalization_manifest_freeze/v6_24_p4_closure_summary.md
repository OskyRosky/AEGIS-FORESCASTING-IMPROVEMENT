# V6.24-P4 — Cohort Normalization / Manifest Freeze

**Stage:** V6.24-P4
**Status:** **COMPLETED.** The first official **processed** layer for the MVP now exists.
**Next stage:** **P5 — 15-Model Backtest Generation.**

---

## 1. What was produced

`V6/data/processed/v6_24_mvp_cohort/`

| Artifact | Rows | Purpose |
|---|---:|---|
| `cohort_manifest.parquet` / `.csv` | **140** | The frozen cohort. One row per observed series |
| `actuals_normalized.parquet` / `.csv` | **48,916** | One row per series per date, one schema for four metrics |
| `source_forecast_baselines_normalized.parquet` / `.csv` | **13,050** | SSD LVWE/LVNE source forecasts |
| `data_dictionary.csv` | 46 | Every column defined, derived-vs-verbatim marked |
| `p4_processing_readme.md` | — | Contracts for anyone reading this layer |

| Metric | Series | Keys | Actual rows | Date range |
|---|---:|---:|---:|---|
| HDD | 50 | 46 | 10,687 | 2025-05-02 → 2026-08-17 |
| SSD | 50 | 50 | 6,500 | 2026-04-13 → 2026-08-22 |
| CPU | 20 | 10 | 11,228 | 2022-01-04 → 2023-07-20 |
| IOPS | 20 | 10 | 20,501 | 2020-06-23 → 2023-07-20 |
| **Total** | **140** | | **48,916** | |

---

## 2. Values were not altered

This was the central obligation, and it is proven rather than asserted. The audit **re-reads
every source independently** and compares, instead of trusting the code that wrote the output.

| Metric | Source rows | Processed rows | Max abs delta | Changed values | Result |
|---|---:|---:|---:|---:|---|
| HDD | 10,687 | 10,687 | **0.0** | **0** | PASS |
| SSD | 6,500 | 6,500 | **1.11e-16** | **0** | PASS |
| CPU | 11,228 | 11,228 | **0.0** | **0** | PASS |
| IOPS | 20,501 | 20,501 | **0.0** | **0** | PASS |

The SSD figure is float representation noise from the `varchar → float` cast. The audit
re-derived `actual_value` with an independent parser from the retained source text; zero values
differ beyond 1e-9.

**No scaling. No standardization. No smoothing. No interpolation. No date filling. No
missing-to-zero.** `distinct_date_count` equals `observation_count` for all 140 series, which is
the structural proof that no date was invented.

---

## 3. The HDD lineage problem, and how it was resolved

This was the one genuine risk of blocking, and it deserves a straight account.

`forecast_viewer_model_outputs_v2_full.parquet` mixes **two extraction lineages**:

| Lineage | Selected series | Coverage |
|---|---:|---|
| `R6P1-20260812T100822` | **44** | All six routes; 0 internal conflicts |
| `LEGACY_STAGE05H_VERIFIED_R8FIX0` | **6** | EDB Enterprise Region only |

Naively grouping by `(metric, scenario, granularity, series_key, date)` reported **4,993
conflicting groups**, which looked like a blocking ambiguity. Three measurements resolved it:

1. **The lineages are disjoint over the selected set.** Zero grain groups appear in both. So the
   union is unambiguous — there is no "which lineage wins" decision to make.
2. **R6P1 alone would lose 6 series entirely** (0 rows for those keys), while the union
   reproduces the P2 plan's observation counts **exactly for all 50**.
3. **The remaining conflicts are float noise.** Measured spread across all conflicting groups:
   absolute `0.0000000009`, relative `0.0000%`. Not a data disagreement.

So P4 took the deduplicated union. The audit then returned max delta `0.0` and 0 changed values
against an independent re-read, confirming it.

**One thing I got wrong on the way.** My first preservation audit reported HDD FAIL with 1,300
changed values. That was **my audit's bug, not the data's**: I joined source to processed on
`key + date`, but four HDD keys appear under two routes each (`APC-MSIT` sits under both EDB
Consumer Region and EDB Enterprise Region), so the join cross-matched distinct series. The
processed data was correct throughout — `series_id + series_date` had 0 duplicates. Fixing the
join to the full route grain returned PASS. I mention it because a green check that was green for
the wrong reason would have been worse than a red one.

---

## 4. Deduplication

| Metric | Removed | Basis |
|---|---:|---|
| SSD | **50** | One exact duplicate per key on 2026-04-22 |
| HDD | **193,613** | Model and run repetitions of the same observation |
| CPU / IOPS | 0 | None required |

The two are different in kind and the audit says so.

**SSD** — the source genuinely holds a duplicate row. All 50 groups carry an identical
`actual_value`, `forecast_value` and `window_start`, so keep-first is lossless. **Zero
conflicting groups**; had any conflicted, P4 would have blocked. Every removal is recorded
individually in `v6_24_p4_deduplication_audit.csv`.

**HDD** — the local artifact stores one row per model per run, so each observation repeats 15+
times. Collapsing 204,300 rows to 10,687 is not data loss; it is reading the artifact at the
right grain.

---

## 5. Contracts frozen here

**`series_id` is the join key for P5/P6/P7.** Deterministic, order-independent:

```
HDD__<db_type>__<segment|NA>__<granularity>__<key-slug>
SSD__Phoenix__Forest__<key-slug>
CPU__<scenario>__Region__<key-slug>
IOPS__<scenario>__Region__<key-slug>
```

`(series_id, series_date)` is unique — **0 duplicates** across 48,916 rows.

> **Join on `series_id`, never on `key`.** HDD has 46 unique keys for 50 series.

**SSD is 50 observed series, never 100.** `actuals_normalized` takes SSD actuals from **LVWE
only**; `source_forecast_baselines_normalized` holds **both** variants tagged by
`forecast_variant`. Switching variant in the UI must change the forecast line, never the actual.

**Source baselines are not model output.** All 13,050 rows carry a caveat saying so explicitly.
CPU and IOPS have **no** source baseline at all — they will have only the 15 generated models
with nothing external to compare against.

---

## 6. What the cohort still lacks

| Metric | Actuals | 15 backtests | Forecast | Viewer now | Next |
|---|---|---|---|---|---|
| HDD | ✅ | ✅ | ✅ | **TRUE** | — |
| SSD | ✅ | ❌ | ❌ | FALSE | **P5** |
| CPU | ✅ | ❌ | ❌ | FALSE | **P5** |
| IOPS | ✅ | ❌ | ❌ | FALSE | **P5** |

**Only 50 of 140 could render in the Viewer today.** All 90 non-HDD series carry
`viewer_visible_now = FALSE` and `p5_required = TRUE` **in the manifest**, not merely in prose.

P7 must derive `navigation_contract` and `taxonomy_counts` **after** the completeness gate, so a
series lacking its backtests cannot reach the selector. That is what prevents the V6.23 failure
mode: a selectable combination that renders "Backtest unavailable".

---

## 7. Governance

| Constraint | Observed |
|---|---|
| No SQL run | 0 queries. P4 read only local Parquet and CSV |
| Raw Parquet unchanged | 4 files, all 4 sha256 identical to the values P3 recorded |
| No forbidden artifacts | 0 files matching `model_backtests_15_models`, `forecast_outputs`, `accuracy_metrics`, `model_rankings`, `navigation_contract`, `taxonomy_counts` |
| No models, forecasts, accuracy or rankings | None |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |

---

## 8. Reports

| File | Rows |
|---|---:|
| `v6_24_p4_reduced_status_table.csv` | 8 |
| `v6_24_p4_manifest_summary.csv` | 4 |
| `v6_24_p4_actuals_summary_by_metric.csv` | 4 |
| `v6_24_p4_full_140_manifest_readable.md` | 140 series |
| `v6_24_p4_actuals_value_preservation_audit.csv` | 4 |
| `v6_24_p4_deduplication_audit.csv` | 51 |
| `v6_24_p4_source_forecast_baseline_summary.csv` | 5 |
| `v6_24_p4_series_id_mapping.csv` | 140 |
| `v6_24_p4_schema_report.csv` | 72 |
| `v6_24_p4_data_quality_report.csv` | 5 |
| `v6_24_p4_unresolved_questions.csv` | 4 |
| `v6_24_p4_validation.csv` | 38 |
| `v6_24_p4_closure_summary.md` | — |

---

## 9. Next stage

**P5 — 15-Model Backtest Generation**, for the 90 non-HDD series. It should:

1. Read `actuals_normalized.parquet` and model by `series_id`.
2. Reuse the 15 governed model names already present in the HDD artifact, so the vocabulary
   stays consistent across metrics.
3. Write `model_backtests_15_models.parquet` into the same processed folder.
4. **Set the horizon from the shortest series, not the median** — the cohort spans 75 to 1,103
   observations, and HDD Basilisk at 75 plus IOPS CHN-Gallatin at 429 are the binding
   constraints (P4-UQ04).

Four open questions are logged; **none blocks P5**.

---

**V6_24_P4_COHORT_NORMALIZATION_MANIFEST_FREEZE_COMPLETED**

Stopping here. P5 not started, no models run, no forecasts generated, no accuracy or rankings
calculated, no `navigation_contract` or `taxonomy_counts`, Shiny untouched, no push.
