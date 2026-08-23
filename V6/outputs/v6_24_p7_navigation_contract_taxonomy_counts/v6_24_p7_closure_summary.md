# V6.24-P7 — Navigation Contract / Taxonomy Counts — Closure Summary

**Status: COMPLETE. Validation 51 PASS / 0 FAIL.**

**Verdict: `READY_FOR_P8_WITH_CAVEATS`.**

Two new canonical artifacts were created. Nothing else in `processed/` changed —
all 16 frozen artifacts were verified **byte-identical by sha256** before and after.

---

## 1. What was built

| Artifact | Rows | Purpose |
|---|---|---|
| `navigation_contract.parquet` / `.csv` | **140** `OPERATIONAL_ENTITY` rows, 66 columns | One row per MVP series: identity, taxonomy, availability, champion, caveats, forecast window and precomputed medians |
| `taxonomy_counts.parquet` / `.csv` | **192** rows across **10 scopes** | Filter panels, tiles and availability counts with nothing left to compute at runtime |

**Every one of the 10 taxonomy scopes partitions the cohort to exactly 140 series.**

## 2. Readiness was derived, never trusted

Readiness for all four layers — backtest, accuracy, ranking, forecast — was computed
directly from the governed artifacts: model coverage, per-model row counts, champion
uniqueness, ranking policy version, forecast step counts and forecast type.

Result: **140/140 `product_ready`**.

`cohort_manifest.has_15_model_backtests` reads `FALSE` for **90 series that are in fact
fully ready**. Had P7 trusted it, every SSD, CPU and IOPS series would have vanished
from the Viewer. The flag is recorded on every row as
`manifest_has_15_model_backtests_original`, alongside
`manifest_flag_used_for_readiness = FALSE`, so the trap is documented **inside the
contract** rather than in a report nobody rereads.

## 3. Product availability

| Status | Series |
|---|---|
| `AVAILABLE` | 53 |
| `AVAILABLE_WITH_CAVEAT` | 87 |
| `NOT_AVAILABLE` | **0** |

All 140 are viewer-visible, forecast-visible and ranking-visible. Parity holds in both
directions: **no viewer-visible row lacks forecast visibility, and none the reverse.**

## 4. Champion visibility honours P6C

| Signal quality | Series | Champion visible |
|---|---|---|
| `SIGNAL_PRESENT` | 121 | 121 |
| `TRAILING_ZERO_LATEST_ACTUAL` | 4 | 4 |
| `NO_SIGNAL_ALL_ZERO_ACTUALS` | **15** | **0** |

The 15 no-signal series remain fully **selectable** — hiding them would make the cohort
silently smaller than the 140 the pipeline reports, and a user could not tell a dead
series from a missing one. But their champion is suppressed, because for an all-zero
series the champion is a technical tie-break, not a recommendation.

`champion_visible = TRUE` occurs **only** where
`champion_validity = MEANINGFUL_ACCURACY_RANKING`.

## 5. Key is not a canonical axis — proven, not asserted

The six-level path `metric|db_type|scenario|segment|granularity|key` yields **140
distinct values for 140 series**. `key` alone yields only **102 distinct values**, and
**38 rows share a key with another row**.

Every row therefore carries `key_axis_status` declaring Key's role at that granularity —
`ROUTING_VALUE_REGION` or `IDENTIFIER_VALUE_FOREST` — and `valid_filter_path` is the
field that actually identifies a series. **P8 must not offer Key as a top-level filter.**

## 6. Conditional axes are explicit, never faked

The taxonomy is genuinely ragged and was preserved as-is:

- `db_type` is `NOT_APPLICABLE` for IOPS and
  `UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE` for CPU.
- `scenario` is `NOT_APPLICABLE` for HDD and SSD.
- `segment` is `NOT_APPLICABLE` for CPU, IOPS, SSD and the 17 HDD Basilisk series.

No token was normalised, renamed or invented. **Across all six filter stages, zero
empty options are exposed** — every option derives from a real operational row. No
`All` option was fabricated, because none exists in the artifacts.

## 7. Caveats are machine-readable and non-blocking

Eleven caveat codes, none blocking. Notable counts: `NO_SIGNAL` 15,
`CHAMPION_NOT_MEANINGFUL` 15, `LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO` 1,
`NEGATIVE_BACKTEST_PREDICTIONS_PRESENT` 56, `EXTREME_BACKTEST_RATIO_PRESENT` 51,
`NEGATIVE_FORECAST_PRESENT` 15, `EXTREME_FORECAST_PRESENT` 7. Two informational codes
apply to the whole cohort: `STALE_MANIFEST_FLAG_IGNORED` and
`GOVERNED_30_STEP_FORECAST_ONLY`.

The low-confidence flag was **derived**, not hardcoded: it marks any series with
historical signal whose backtest window sums to zero. Exactly one series qualifies
(`SSD__Phoenix__Forest__GBRP267`), but the rule would catch any future case.

## 8. Aggregation is median-only and series-weighted

`navigation_contract` and `taxonomy_counts` expose `median_wape`, `median_smape`,
`median_rmse` and `median_mae` — and **no mean column exists anywhere in either
artifact**, so a P8 tile cannot accidentally bind to one.

The justification is measured, not theoretical: mean `wape` across `accuracy_metrics`
is **6.697e+19**; the median is **0.0638**.

Medians are series-weighted — each series contributes its own median once, never one
row per backtest row — because backtest density differs by metric. Where a median is
not computable it is left **empty with an explicit status column**, never coerced to
zero. **16 series have a non-computable median `wape`** — the 15 no-signal series plus
the low-confidence one — and none of them reads as `0`.

## 9. The forecast horizon is stated honestly everywhere

Every navigation and taxonomy row carries `forecast_type =
GOVERNED_30_STEP_DAILY_FORECAST` and `forecast_steps = 30`. **No row anywhere claims a
1,440-day or four-year horizon.** Per-series `forecast_start_date` and
`forecast_end_date` are precomputed from `forecast_outputs`.

## 10. Governance

All 16 frozen artifacts verified byte-identical by sha256. Shiny, V1–V5 and raw Parquet
verified clean via `git status`. No SQL, no models re-run, no accuracy or ranking
recalculation, no staging, no push.

## 11. P8 readiness — READY_FOR_P8_WITH_CAVEATS

P8 may build the Shiny read-only integration. Four caveats travel with the contract:

1. **P8 must compute nothing at runtime.** Every count, median, champion, badge and
   date is precomputed. Runtime computation is how Viewer and Forecast drift apart.
2. **Filter on fields, never on lists.** Use `champion_visible`, `product_status` and
   `caveat_badge` — never a hardcoded series list.
3. **Do not offer Key as a top-level filter.** It is not unique.
4. **Disclose the 30-day horizon persistently**, not in a tooltip. It is a real product
   limit, and burying it invites exactly the four-year misreading P6 blocked.

---

**V6_24_P7_NAVIGATION_CONTRACT_TAXONOMY_COUNTS_COMPLETED**
