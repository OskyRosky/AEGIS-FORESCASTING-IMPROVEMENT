# V6.21B Registry and Accuracy Hardening — Closure Summary

## Final status

`V6_21B_REGISTRY_ACCURACY_HARDENING_COMPLETED`

Accuracy was migrated under **option A**. The fallback (option C, temporary
disablement) was not needed: both blocking validations passed.

## Registry option chosen, and why

**Mixed, and recorded explicitly rather than decided silently:**

* **Option 1 for Accuracy.** `acc_data()` resolves the precomputed artifact
  through `tess_collect_parquet_artifact("accuracy_metrics_parquet")`. This is
  the page the stage migrates, so it proves the registry Parquet path end to end.
* **Option 2 for the Viewer and Forecast providers.** They keep their direct
  `arrow::open_dataset()` reads. Option 1 was rejected for them because it could
  not be shown to be behaviour-neutral: both providers push a `dplyr::filter`
  down and collect a single case, whereas the registry accessor returns a full
  dataset or a materialised frame. Rewiring two pages that already passed V6.18
  and V6.20 validation was not necessary to close the V6.20 blocker.

Either way the registry now **knows** all three Parquet artifacts, which is the
actual protection: a future Parquet-only migration can no longer break a page
silently. The registry grew from 43 entries with zero Parquet to **46 entries
with 3 lazy Parquet entries**. Lazy means the loader records presence, row count
and column count from Parquet metadata and never materialises the file: the
2,416,050-row Viewer artifact is registered without being read.

## Exact grouping key used

```
metric + scenario + granularity + series_key + model_name + horizon_days
```

`forecast_start_date` is deliberately **not** in the key: aggregating across
rolling origins is the existing intended semantic and `n_points` counts them.
`extraction_run_id` is **not** in the key either, but the builder verifies no
group mixes runs and aborts if one does.

## Counts

| Measure | Value |
|---|---:|
| Rows in the artifact | 268,200 |
| Distinct route × key cases | 596 |
| Distinct series_key entities | 391 |
| Distinct models | 15 |
| Horizons present in the artifact | 1–30 |
| Horizons exposed by the selector | 5, 10, 15, 20, 25, 30 |
| Non-finite pairs dropped before grouping | 0 |

## V1 — formula equivalence

1,200 comparisons over 5 series shared by both artifacts, at horizons 5 and 30,
on the common legacy grouping.

| Metric | Max absolute difference |
|---|---:|
| n_points | 0 |
| sMAPE | 0 |
| wMAPE | 4e-12 |
| MAE | 1.3039e-8 |
| signed_bias | 1.3039e-8 |
| abs_bias_severity | 1.3039e-8 |
| RMSE | 1.4901e-8 |
| error_variability | 4.4703e-8 |

All within the 1e-6 tolerance. The residual is float32/float64 rounding in the
CSV round-trip, not a formula difference.

## V2 — route context proof

`DNK-Go Local` appears as **three separate rows**, one per route, at horizon 30
with ETS Explicit:

| Route | n_points | MAE |
|---|---:|---:|
| HDD - Basilisk / Basilisk / Region | 5 | 0.000000 |
| HDD - EDB / Consumer / Region | 11 | 0.002535 |
| HDD - EDB / Enterprise / Region | 11 | 1.622905 |

These are three different time series with three different error profiles.
Grouping on the raw key would have blended them into one meaningless number.
**197 of the 391 entities** appear in more than one route, up to three.

## F8 — n_points heterogeneity: a methodological caveat for ranking

The artifact spans two extraction runs and they do not mix:

| Run | Groups | n_points min / median / max |
|---|---:|---|
| `LEGACY_STAGE05H_VERIFIED_R8FIX0` | 17,550 | 7 / 12 / 12 |
| `R6P1-20260812T100822` | 250,650 | 5 / 11 / 11 |

Aggregation is therefore safe. **But `n_points` is not comparable across runs**,
and Accuracy is a ranking page. `acc_standardize()` computes a robust
`(x - median) / IQR` score across the whole cohort and treats a case backed by 5
rolling origins as exactly as reliable as one backed by 12.

Assessment: the standardisation **remains arithmetically defensible** — it is a
robust relative severity score, not a confidence statement, and it never claims
statistical significance. What breaks is the *interpretation* once the cohort
grows more heterogeneous. Two specific hazards:

1. Cases with few origins have noisier metrics and can dominate the worst-first
   ranking for reasons of sample size rather than model quality.
2. When CPU and IOPS routes are added, the cohort will mix metrics with
   different physical units and different scales. A single IQR computed across
   all of them would be meaningless. **Standardisation should then become
   per-metric, or at least per-route**, before those routes are exposed.

This is recorded as a caveat, not fixed here: changing the standardisation would
have changed Accuracy's output, which this stage explicitly must not do.

## The "All ..." label and its unit

Before: `All (39)` — hardcoded, silently wrong, and the unit was never stated.
After: **`All cases (596)`**, derived at runtime from `acc_case_count()`.

The unit question turned out to matter more than the number. All three
components — heatmap rows, table rows and summary cards — now rank the **same**
unit, the route × key case, because `acc_compute()` returns the route-qualified
case label. The summary card was relabelled from "Keys covered" to
"Route × key cases covered" so it no longer implies entities.

## Accuracy: migrated, not disabled

* `acc_data()` reads the precomputed Parquet through the registry and caches it.
* `acc_compute()` is now a **filter**: zero arithmetic expressions remain inside
  it. Shiny no longer computes MAE, RMSE, sMAPE, wMAPE, bias or variability.
* `acc_heatmap()`, `acc_table()` and `acc_summary()` are unchanged; the return
  schema of `acc_compute()` is identical to before.

## Performance

| Measurement | Baseline (before any edit) | After |
|---|---:|---:|
| Data load | 0.163 s | 0.087 s |
| `acc_compute` horizon 5 | 0.299 s | 0.043 s |
| `acc_compute` horizon 30 | 0.249 s | 0.023 s |
| **Total** | **0.711 s** | **0.150 s** |
| Groups produced | 585 | 8,940 |

About **4.7× faster while covering 15× more cases**, because the expensive
per-group aggregation moved out of Shiny entirely.

## Forward Forecast LLM panel

Restored at `ui/tabs_v6_16_viewer.R` line 303. All **10 of 10**
`llm_explain_server()` registrations now have a live UI mount; no other orphan
was found. The layer stays mock-only and read-only.

## Known gaps, reported not fixed

* `lower_bound` and `upper_bound` are empty throughout the V6.17 artifact.
  Accuracy does not use them, so it is unaffected; prediction intervals remain
  a separate gap.
* The artifact contains horizons 1–30 while the Accuracy and Viewer selectors
  expose only six of them. 24 horizons are computed and never reachable from the
  UI. Not normalised, per F6.
* 61,836 sMAPE and 71,685 wMAPE values are NA, from zero denominators on flat
  zero-actual series such as the Basilisk route. This is correct behaviour and
  matches the legacy formula.
* `V6/data/processed` remains ignored by Git and unprotected.

## Exact next step

The two V6.20 generation blockers are now closed: the registry knows Parquet and
Accuracy is aligned with the V6.17 universe. The remaining blockers are the
**V6.19 cohort gate** ones, unchanged by this stage:

1. recover or regenerate the missing E11 cohort sources;
2. resolve the SSD-Phoenix 144 vs 152 mapping;
3. obtain an explicit owner decision on the generation scope.

Before exposing CPU and IOPS routes, revisit `acc_standardize()` as described
above.
