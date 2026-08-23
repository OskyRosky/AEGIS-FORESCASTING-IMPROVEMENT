# P8 Integration Notes — Shiny Read-Only Consumption

Written by V6.24-P7 for whoever builds V6.24-P8.

**The architectural rule is absolute: Shiny reads finished artifacts and computes
nothing.** Every count, median, champion, badge, label and date the Viewer needs is
already precomputed. If P8 finds itself writing a `group_by` or a `mean()`, that is a
signal the contract is missing a field — extend the contract in a governed stage, do
not compute it at runtime.

---

## 1. The only two files P8 should read for navigation

```
V6/data/processed/v6_24_mvp_cohort/navigation_contract.parquet   140 rows, 66 columns
V6/data/processed/v6_24_mvp_cohort/taxonomy_counts.parquet       192 rows, 10 scopes
```

Series data comes from the existing governed artifacts:

```
actuals_normalized.parquet          observed history
model_backtests_15_models.parquet   backtest lines
forecast_outputs.parquet            30-step forward lines
accuracy_metrics.parquet            per-series-model error
model_rankings.parquet              full 1..15 ranking
```

**Shiny must not read SQL. Shiny must not read scattered outputs as product truth.**

## 2. Building the filter panel

Read `v6_24_p7_filter_option_contract.csv`, or derive the same thing from
`taxonomy_counts` scopes. The six stages, in order:

```
1. metric  →  2. db_type  →  3. scenario  →  4. segment  →  5. granularity  →  6. key
```

At each stage, offer **only** the options whose `parent_filter_path` matches the current
selection. Every option in the contract has at least one series behind it, so the user
can never reach an empty result.

Conditional axes carry `NOT_APPLICABLE` or `UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE`
explicitly. **Display them as a disabled or collapsed step — do not drop them silently,
and do not rename them.** The value is real information about the source.

Do not add an `All` option. None exists in the artifacts.

## 3. Key is not a canonical axis

`key` has only **102 distinct values across 140 series**; 38 rows share a key with
another row. Selecting by key alone is ambiguous.

- Use `valid_filter_path` as the series selection value.
- Read `key_axis_status` to label the step correctly: `ROUTING_VALUE_REGION` when
  granularity is Region, `IDENTIFIER_VALUE_FOREST` when Forest.
- **Never place Key at the top of the filter stack.**

## 4. Visibility — filter on fields, never on hardcoded lists

| Field | Use |
|---|---|
| `viewer_visible` | show the series in the Viewer |
| `forecast_visible` | show the Forecast panel |
| `ranking_visible` | show the ranking table |
| `champion_visible` | show the champion recommendation |
| `product_status` | `AVAILABLE` vs `AVAILABLE_WITH_CAVEAT` |

**`champion_visible = FALSE` for 15 series.** Those series stay fully selectable and
their charts render normally — only the champion recommendation is suppressed. Bind the
champion tile's visibility to this field. Do not maintain a list of series names.

## 5. Caveat badges

`caveat_badge` is a pipe-separated list of codes, or `NONE`. Split on `|` and render one
badge per code. `caveat_message` carries prose already written for the user.

Severity and display guidance live in `v6_24_p7_caveat_contract.csv`. **No caveat is
blocking** — a caveat annotates, it never hides data.

Two codes apply to all 140 series and belong in a persistent footer rather than a
per-series badge: `STALE_MANIFEST_FLAG_IGNORED` (governance only, not user-facing) and
`GOVERNED_30_STEP_FORECAST_ONLY`.

## 6. Aggregate tiles — median only

Use `median_wape`, `median_smape`, `median_rmse`, `median_mae` from `taxonomy_counts` at
the scope matching the user's current filter selection.

**There is deliberately no mean column in either artifact.** Mean `wape` across the
cohort is `6.697e+19` versus a median of `0.0638` — a mean-based tile would display a
meaningless number.

When a median is empty, read the matching `*_status` column and render
`STRUCTURALLY_NOT_COMPUTABLE`. **Never render an empty median as `0`** — that would make
a dead series look perfect.

## 7. Forecast panel

Every row carries `forecast_type = GOVERNED_30_STEP_DAILY_FORECAST` and
`forecast_steps = 30`, plus per-series `forecast_start_date` and `forecast_end_date`.

Show the horizon as a **persistent label**, not a tooltip. Thirty days is a real product
limit of the current governed models, and burying it invites the four-year misreading
that P6 explicitly blocked.

Note that `forecast_start_date` differs by metric because each series forecasts from its
own last observation: CPU and IOPS start 2023-07-21, HDD between 2026-04-27 and
2026-07-20, SSD 2026-08-23. **Do not force a shared x-axis origin across metrics.**

## 8. Viewer = Forecast parity

Parity is guaranteed by the contract: the same 140 series and the same 15 governed
models on both sides, verified in `v6_24_p7_viewer_forecast_parity_report.csv`.

P8 preserves parity by driving both panels from the same `navigation_contract` row. If
the Viewer and Forecast panels ever resolve their series list differently, parity is
broken regardless of what the artifacts say.

## 9. Model vocabulary

Exactly 15 governed models. `ETS Explicit` is spelled **with a space** — it is a
registry name, not a display string. Do not normalise, prettify or substitute model
names.

## 10. What P8 must not do

- Do not compute rankings, counts, accuracy, forecasts or backtests at runtime.
- Do not read SQL.
- Do not clip negative or extreme values — they are real model output and were
  deliberately preserved end to end.
- Do not modify any artifact under `processed/`.
- Do not hide no-signal series; suppress only their champion.
- Do not invent an `All` option or a Memory metric.
