# V6.24-P2A — SSD Selected Cohort Verification / Pre-P3 Gate

**Stage:** V6.24-P2A
**Purpose:** prove, before P3 begins, that all 50 selected SSD series have more than 50 real
parseable actual observations.
**Mode:** Read-only verification.
**Queries:** 3 of an 8 budget.
**Result:** **All 50 pass. Zero replacements needed.**

---

## 1. The ambiguity this gate was created to resolve

The V6.24-P2 closure summary, Table 5, reported the SSD observation range as **24–131**.

`24` is below the 50-observation threshold, which raised a legitimate concern that an
ineligible key might have entered the cohort.

**It did not.** The `24–131` figure was the range of the **eligible pool** (136 keys), not the
range of the **50 selected keys**. That was a reporting defect in my P2 summary: I carried the
pool range into a table whose other columns described the selection. The number was accurate
but the label was misleading.

The selection code itself was never at risk — `p2_select_cohort.py` filters on
`obs > 50` before any selection begins, and then ranks by `-obs`, so it takes the
highest-observation key within each geographic prefix.

**But that is an argument from code, not from evidence.** This gate re-measures the 50 keys
directly from SQL, without trusting the P2 plan file.

---

## 2. Independent SQL verification

`P2AQ001` re-measured all 50 selected keys against
`forecast_substrateBE_ssd_phx_lvwe_metrics`:

| Measure | Result |
|---|---|
| Keys verified | **50 of 50** |
| Parseable actual observations | **131 minimum, 131 maximum** — identical across all 50 |
| Keys above the 50 threshold | **50 of 50** |
| Non-parseable `Mean_Actual` values | **0** |
| Null `Mean_Actual` values | **0** |
| Distinct `End_Date` values per key | 130 |
| Date range | 2026-04-07 → 2026-08-22, identical for all 50 |

Every selected key clears the threshold by a factor of **2.6×**. The margin is not marginal.

**Parse expression used:** `TRY_CAST(Mean_Actual AS FLOAT)`.
This matters because `Mean_Actual` is stored as **varchar** while `Mean_Forecast` is `float`.
`TRY_CAST` returns null on a parse failure rather than raising, so counting its nulls separately
from genuine `NULL` values distinguishes *"the value is missing"* from *"the value is present
but is not a number"*. Both counts are zero.

---

## 3. No double counting

`P2AQ002` re-confirmed, restricted to the 50 selected keys, that LVNE carries an **identical**
`Mean_Actual` to LVWE:

```
SELECT Key, End_Date, Mean_Actual FROM lvwe WHERE Key IN (<50 keys>)
EXCEPT
SELECT Key, End_Date, Mean_Actual FROM lvne WHERE Key IN (<50 keys>)
  -> 0 rows
```

Zero differing rows. The verification file therefore holds **50 rows for 50 unique keys**, with
`variant_contract = "LVWE+LVNE (one observed series, two forecast variants)"`.

LVNE is still extracted in P3, but for its `Mean_Forecast` only. Its actual column is emitted as
`actual_value_DO_NOT_LOAD_AS_ACTUALS` so the constraint is enforced by the column name rather
than by documentation. Loading both would inflate the cohort from 50 SSD series to 100.

---

## 4. Replacements

**None required.** `v6_24_p2a_ssd_replacements.csv` is written with headers and zero rows.

`P2AQ003` retrieved the full eligible pool as a contingency: **136 keys** clear 50 parseable
actuals, so **86 spares** were available had any selection failed. None did.

---

## 5. P3 readiness after P2A

| Metric | Series for P3 | Status | Caveat |
|---|---:|---|---|
| SSD | **50** | **VERIFIED — ready** | Windowed actuals; `Mean_Actual` is varchar and must be CAST; no 15-model backtests yet |
| CPU | 20 | Carried forward from P2, unchanged | `STALE_ACTUALS_SOURCE` to 2023-07-20; no backtests yet |
| IOPS | 20 | Carried forward from P2, unchanged | `STALE_ACTUALS_SOURCE` to 2023-07-20; no backtests yet |
| **Total** | **90** | Unchanged | HDD stays local, 0 downloads |

This gate was scoped to SSD only. CPU and IOPS rows are carried forward byte-identical apart
from a provenance note. The corrected P3 plan still holds exactly **90** rows.

---

## 6. Governance

| Constraint | Observed |
|---|---|
| SQL budget | **3 of 8** |
| No full extraction | Largest result was 136 rows of grouped counts. No time-series rows returned |
| No Parquet | 0 files |
| No models | Only `.csv`, `.md`, `.json`, `.py` artifacts |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |

---

## 7. Deliverables

| File | Rows | Purpose |
|---|---:|---|
| `v6_24_p2a_ssd_selected_50_verification.csv` | **50** | Per-key evidence, measured from SQL |
| `v6_24_p2a_ssd_replacements.csv` | **0** | Headers only. No replacements needed |
| `v6_24_p2a_corrected_ssd_50_extraction_plan.csv` | **50** | Final SSD list for P3 |
| `v6_24_p2a_corrected_p3_90_series_extraction_plan.csv` | **90** | Final P3 plan |
| `v6_24_p2a_query_ledger.csv` | 3 | Every query with auth mode and duration |
| `v6_24_p2a_validation.csv` | 19 | All checks |
| `v6_24_p2a_closure_summary.md` | — | This file |

---

## 8. What I would tighten going forward

The defect here was **reporting**, not selection: I labelled a pool statistic as if it described
the selection. A summary table whose rows say "Selected" must only carry statistics computed
over the selected rows.

From P3 onward, every summary figure should be computed from the artifact it claims to
describe, not from an upstream pool. This gate exists because that discipline slipped once.

---

**V6_24_P2A_SSD_SELECTED_COHORT_VERIFICATION_COMPLETED**

Stopping here. P3 not started, no data extracted, no Parquet written, no models run, no Shiny
changes, no push.
