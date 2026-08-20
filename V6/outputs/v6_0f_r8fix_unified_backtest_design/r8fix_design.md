# V6.0F-R8-FIX — Unified Backtest Viewer — Design

**Status:** design only. No Shiny change, no model run, no extraction.

---

## 1. The corrected target

One box. No Scenario explorer. No Forecast Version.

```
SET UP THE BACKTEST VIEW
 1 Metric   2 Scenario   3 Granularity   4 Key / Series
 5 Horizon  6 History window
 7 Models  (15 AEGIS, grouped by family)
 8 Analyze Backtest
──────────────────────────────────────────────────────
BACKTEST COMPARISON
 Chart: Actual + selected models
 DATA NOTES: Metric · Scenario · Granularity · Key
             Horizon · Models selected · Actual points · Forecast points · Date range
```

---

## 2. What the current artifact is — now verified, not assumed

`data/processed/forecast_viewer_model_outputs.csv` · 204,300 rows · 21 columns

| Property | Value |
|---|---|
| Series | 39 |
| Models | **15**, exactly the authorised list |
| Families | growth_baseline, statistical, machine_learning, lightweight_neural |
| Horizons | 1–30 days |
| Rolling origins | 12 (2025-05-02 → 2026-03-28) |
| Dates | 2025-05-03 → 2026-04-27 |
| `forecast_type` | `backtest` (single value) |
| Intervals | columns exist but are entirely `NA` |
| **Metric / Scenario / Granularity** | **absent** |

**Which combination is it?** The key names alone could not tell us — region names repeat across scenarios, so all three Region combinations matched 39/39. It was settled by comparing actual values on the overlapping window:

| Candidate | Rows matched | Exact match | Median abs. difference |
|---|---:|---:|---:|
| **HDD - EDB / Enterprise / Region** | 38,266 | **96.6 %** | **0.0000** |
| HDD - EDB / Consumer / Region | 38,217 | 0 % | 27,762 |
| HDD - Basilisk / Basilisk / Region | 6,309 | 0 % | 27,051 |

The existing backtest is **HDD - EDB / Enterprise / Region**, covering **39 of 45** keys.

---

## 3. The missing artifact

**`forecast_viewer_model_outputs_v2.csv`** — the same 21 columns plus **four** new ones:

| New column | Purpose |
|---|---|
| `metric` | HDD - EDB / HDD - Basilisk |
| `scenario` | Enterprise / Consumer / Basilisk |
| `granularity` | Region / Forest |
| `extraction_run_id` | Links each actual back to the governed R6 extraction |

The existing 204,300 rows are backfilled with `HDD - EDB / Enterprise / Region` — a **verified** label, not a guess. Everything else must be produced by running the 15 AEGIS models against the actuals extracted in R6.

**Without this artifact the unified Viewer cannot exist.** Metric, Scenario and Granularity would be controls with nothing behind them.

---

## 4. Coverage gap

| Metric | Scenario | Granularity | Keys | Months of actuals | Backtest today |
|---|---|---|---:|---:|---|
| HDD - EDB | Enterprise | Region | 45 | 11 | 🟡 39 of 45 |
| HDD - EDB | Enterprise | Forest | 152 | 11 | ❌ none |
| HDD - EDB | Consumer | Region | 45 | 11 | ❌ none |
| HDD - EDB | Consumer | Forest | 152 | 11 | ❌ none |
| HDD - Basilisk | Basilisk | Region | 47 | 5 | ❌ none |
| HDD - Basilisk | Basilisk | Forest | 155 | 5 | ❌ none |
| SSD - Phoenix | 2 scenarios | Forest | 300 | **0** | ⛔ **impossible** |

**Coverage today: 39 of 596 key-combinations — 6.5 %.**

**SSD-Phoenix cannot be backtested at all.** Tesseract holds no actual series for it, so there is nothing to compare a model against. It is a forecast-only metric and belongs on the Forecast page, not the Viewer.

---

## 5. Run estimate

| Block | Keys | Origins | Rows | Model fits |
|---|---:|---:|---:|---:|
| Top-up Enterprise Region | 6 | 11 | 29,700 | 990 |
| Enterprise Forest | 152 | 11 | 752,400 | 25,080 |
| Consumer Region | 45 | 11 | 222,750 | 7,425 |
| Consumer Forest | 152 | 11 | 752,400 | 25,080 |
| Basilisk Region | 47 | 5 | 105,750 | 3,525 |
| Basilisk Forest | 155 | 5 | 348,750 | 11,625 |
| **New total** | **557** | — | **≈ 2.21 M** | **≈ 73,725** |
| **Final artifact** | **596** | — | **≈ 2.42 M** | — |

Roughly **12× the current artifact**. The three neural models (FNAR-V2, SMLP-TCN, NLIN-DLIN_FIXED) dominate the cost.

Storage is not a concern: the R5b benchmark compressed 2.03 M rows into 25.8 MB of DuckDB, so ~2.42 M rows lands near 30 MB.

---

## 6. Stage plan

| Stage | Name | Touches Shiny | Runs models |
|---|---|---|---|
| R8-FIX-0 | This design | no | no |
| R8-FIX-1 | Revert the Scenario explorer | yes (removal only) | no |
| R8-FIX-2 | Backtest input contract | no | no |
| R8-FIX-3 | **Backtest execution** | no | **YES** |
| R8-FIX-4 | Artifact assembly and storage | no | no |
| R8-FIX-5 | Unified Setup Backtest View | yes | no |
| R8-FIX-6 | Validation and closure | no | no |

R8-FIX-1 can start immediately: it only removes what I added. R8-FIX-3 is the only stage that runs models and needs an explicit, separate authorisation.

---

## 7. Interim option

R8-FIX-1 and R8-FIX-5 can ship **before** the new backtests. The unified box would work today for **HDD - EDB / Enterprise / Region**, with the other five combinations selectable but marked *"Backtest not yet available for this combination"*.

That delivers the correct UX immediately and lets the data catch up, without inventing a single value.

---

## 8. Decisions needed

| ID | Decision | Recommendation |
|---|---|---|
| D1 | Which combinations get a new backtest | All 6, or the Boon slice first |
| D2 | Rolling origin cadence | Match the months of actuals per scenario (Basilisk has only 5) |
| D3 | Compute budget for 73,725 fits | Run the 12 cheap models first, add the 3 neural ones after |
| D4 | Viewer behaviour without a backtest | Selectable but disabled with an explicit reason |
| D5 | SSD-Phoenix in the Viewer | Remove from the metric list; it is forecast-only |
| D6 | Champion flag per scenario | Recompute, never copy |
| D7 | Backfill the existing 204,300 rows | Yes — the label is verified |
| D8 | Where the v2 artifact lives | CSV as the record, DuckDB as what Shiny reads |
| D9 | Six uncovered Enterprise Region keys | Top them up |
| D10 | Keep Horizon | Yes — it is the reason the page exists |
