# V6.0C — Current Pipeline Defect Report

**Stage:** V6.0C — Multi-Metric Scope Diagnosis
**Nature:** Diagnosis only. No defect was corrected in this stage.
**Date:** 2026-08-11

All figures below were measured directly from the local repository. No SQL was executed.

---

## D-01 — Source identity is destroyed during metric consolidation

`python/evaluation/generate_baseline_metrics.py` concatenates four physically
different tables into a single frame and keeps only `source_file` as a trace of
origin.

| Source file | Rows | Keys | Versions |
| --- | --- | --- | --- |
| `hdd_region_metrics.csv` | 2,550 | 45 | 3 |
| `hdd_forest_metrics.csv` | 8,828 | 155 | 3 |
| `ssd_phx_lvwe_metrics.csv` | 7,776 | 137 | 1 |
| `ssd_phx_lvne_metrics.csv` | 7,913 | 137 | 1 |
| **Total in `baseline_metrics.csv`** | **27,067** | 269 distinct | 7 distinct |

`metric_id`, `db_type`, `granularity` and `scenario` are never materialised.
`source_file` is a filename, not a governed dimension, so nothing downstream can
isolate a metric without parsing a string.

**Severity:** high. This is the root cause of D-02.

---

## D-02 — Rankings blend SSD-Phoenix LVWE and LVNE

`_build_rankings` groups by `Key` and `Forecast_Version` only.

LVWE and LVNE share **both** of those values: the same 137 forest keys and the
same single version `2026-03-12`. Every SSD key therefore collapses into one
ranking row that averages two different series.

Measured collision:

| Measure | Value |
| --- | --- |
| Ranking groups total | 736 |
| Groups mixing more than one source table | **137** |
| Distinct keys affected | **137** |
| Underlying rows folded together | **15,689 of 27,067 (58.0%)** |
| `source_file` present in `baseline_rankings.csv` | **No** |

Worked example for `NAMPRD07`:

| Series | Rows | avg MAPE |
| --- | --- | --- |
| LVNE only | 58 | 4.4984 |
| LVWE only | 57 | 4.5133 |
| Published ranking row `2026-03-12` | 115 | **4.5058 (blended)** |

The published number corresponds to no real series.

HDD is not currently affected because region keys (`APC-Dedicated`) and forest
keys (`APCP150`) are disjoint namespaces and their version strings differ. That
is a coincidence of naming, not a designed guarantee.

**Severity:** high. Fix belongs to V6.0E.

---

## D-03 — Shiny Accuracy does not consume the official metrics

`shiny_app/R/helpers.R` defines `acc_data <- function() fvp_data()`, and
`fvp_data()` reads `data/processed/forecast_viewer_model_outputs.csv`.

The governed artifact registry in `shiny_app/R/data_loader.R` contains no entry
for `outputs/metrics/baseline_metrics.csv` or `baseline_rankings.csv`.

Consequence: the official TESSERACT accuracy metrics — including every SSD-Phoenix
row already present locally — are computed, written to disk, and never surfaced.
The Accuracy page shows an HDD-only backtest of 39 series instead.

**Severity:** high. Fix belongs to V6.0F.

---

## D-04 — Scenario is structurally absent from every metrics table

Verified column sets:

| Source | Scenario column |
| --- | --- |
| `forecast_substrateBE_hdd_region` (fact) | **Present**, locally filtered to `Enterprise` |
| `hdd_region_metrics.csv` | **Absent** |
| `hdd_forest_metrics.csv` | **Absent** |
| `ssd_phx_lvwe_metrics.csv` | **Absent** |
| `ssd_phx_lvne_metrics.csv` | **Absent** |

Scenario exists only at fact grain. Any design that makes Scenario a mandatory
filter level would force the pipeline either to invent a value or to drop four of
the six local sources.

**Severity:** medium, but it is a hard design constraint for V6.0D.

---

## D-05 — `forecast_comparison.csv` is structurally empty

The file contains a header and zero rows.

| Boundary | Value |
| --- | --- |
| Last actual date | 2026-04-27 |
| First forecast date | 2026-04-28 |
| Overlapping dates | **0** |

`_build_comparison` performs a same-date inner join, but the ingestion layer
extracts only the latest forecast version, which by construction starts after the
last actual. The join can never produce rows under the current query design.

This is a design defect, not a transient data gap.

**Severity:** medium. Affects any future horizon error work.

---

## D-06 — The local HDD fact extract holds a single forecast version

`hdd_region_forecasts.csv` contains exactly one `ForecastVersion` (`2026-05-01`),
while the source table retains 48 monthly versions according to E1B.

Consequence: even HDD-EDB cannot support cross-plan or drift analysis locally.
Any claim that HDD is "fully workable" applies to the source, not to this
repository's current snapshot.

**Severity:** medium. Re-ingestion is Track B and remains gated.

---

## D-07 — Metric selection is hardcoded across the ingestion and evaluation layers

| File | Hardcoded literal |
| --- | --- |
| `python/ingestion/queries.py` | `forecast_substrateBE_hdd_region`, `Scenario = 'Enterprise'`, `ValueType = 'Forecast-Mean'` |
| `python/ingestion/export_hdd_region.py` | output filenames `hdd_region_forecasts.csv` and `hdd_region_actuals.csv` |
| `python/ingestion/export_official_metrics.py` | a static four-entry `TABLE_EXPORTS` list |
| `python/transform/build_data_contract.py` | input filenames and the `Forecast-Mean` filter |
| `python/evaluation/generate_baseline_metrics.py` | a static four-entry `RAW_METRICS_FILES` list |

Adding a metric today requires editing five files. This is the pattern the
multi-metric foundation must remove.

**Severity:** high. Fix belongs to V6.0D and V6.0E.

---

## D-08 — Repository markers do not reflect the real stage

| File | Stale content |
| --- | --- |
| `V6/VERSION_INFO.md` | The "Active Root Rules" section still states that all active work must happen inside V5 |
| `V6/config/project_root_policy.json` | `next_stage` and `next_block` still point to V6.0A and V6.0B, both already closed |

**Severity:** low, but it misleads anyone resuming the project.

---

## Cross-cutting note on granularity

SSD-Phoenix grain was previously recorded as an inference. It is now verified
locally: all 137 LVWE keys and all 137 LVNE keys are a strict subset of the 155
HDD **forest** keys, with **zero** intersection against the 45 region keys.
`NAMPRD07` follows the same pattern — present in forest and SSD sources, absent
from every region source.
