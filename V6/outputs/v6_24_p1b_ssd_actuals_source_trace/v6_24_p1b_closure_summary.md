# V6.24-P1B — SSD Actuals Source Trace / AX4 Reconciliation

**Stage:** V6.24-P1B
**Purpose:** Correct the SSD portion of V6.24-P1 before P2 begins.
**Mode:** Read-only SQL metadata and aggregates.
**Database:** `TesseractEarthDW` on `tesseractearth.database.windows.net`
**Auth mode used:** `ActiveDirectoryIntegrated` (~5s). Interactive was not used — see §7.
**Queries:** 18 of a 25 budget. All recorded in `v6_24_p1b_query_ledger.csv`.

---

## 1. Formal correction of V6.24-P1

V6.24-P1 stated:

> **SSD** — `FORECAST_ONLY`. No actuals source found anywhere.

**This conclusion is formally withdrawn. It was wrong.**

SSD has observed actuals running through **2026-08-22**, at forest granularity, for
**136 keys** that clear the 50-observation threshold.

### Why P1 got it wrong

| Failure | Detail |
|---|---|
| **Wrong key axis** | P1 searched SSD by `Key` = *region*, copying the HDD pattern. SSD actuals are keyed by **forest** (`NAMPRD07`, `APCPRD01`, `EURP107`). |
| **Partial search reported as a negative result** | P1 catalogued **102** SSD objects and probed **3**. It logged the gap as UQ02 yet still stated the negative conclusion as settled fact. A partial search cannot produce a negative finding. |
| **Wrong object class** | P1 only looked at `forecast_substrateBE_ssd_*` demand/forecast tables. The actuals live in **accuracy metrics** tables, a class P1 never considered. |

P1B swept **all 102** SSD objects (`v6_24_p1b_ssd_object_sweep.csv`): 2 HIGH, 4 MEDIUM,
49 LOW, 47 NONE.

---

## 2. Answers to the thirteen required questions

**Q1. Was an SSD actual-bearing source found?**
Yes. Four sources: two current, two historic.

**Q2. Which table is the best source?**
`forecast_substrateBE_ssd_phx_lvwe_metrics`. `lvwe` decodes to **Low Volume With Efficiency**,
matching the AX4 scenario selector exactly. `..._lvne_metrics` (**Low Volume No Efficiency**)
carries the same observed series with a different forecast.

**Q3. What kind of source is it?**
`DASHBOARD_AGGREGATED_ACTUALS_SOURCE`. Each row is a **rolling window**, not a raw daily point:
`Count` ranges 1–7 with a mean of **5.22** (P1B005). However there are **130 distinct `End_Date`
values across 132 calendar days** (P1B014), so the series behaves as daily with two gaps.

**Q4. Column semantics.**

| Role | Column |
|---|---|
| Series date | `End_Date` (with `Start_Date` bounding the window) |
| Key | `Key` — forest |
| Actual | `Mean_Actual` |
| Forecast | `Mean_Forecast` |
| Accuracy | `Accuracy`, `MAPE`, `SMAPE`, `MAE`, `RMSE`, `Bias`, `Bias_Pct` |
| Variant | the table itself (LVWE vs LVNE) |
| Version | `Forecast_Version` — a single value, `2026-03-12` |
| Window size | `Count` |

**Q5. Does LVWE have >50 observed actuals per key?**
Yes. **136 of 137** keys. Observations per key 24–131, mean 128.4. Zero null `Mean_Actual`.

**Q6. Does LVNE have >50?**
Yes. **136 of 137**. Observations 25–132, mean 129.4. Zero nulls.

**Q7. How many SSD combinations pass >50?**

> **136 — not 272.**

The preliminary P1B figure of 272 was wrong and is corrected here. `EXCEPT` comparison
(P1B012) returned **0 rows** where `Mean_Actual` differs between LVWE and LVNE, while
P1B013 found **6,720 rows** where `Mean_Forecast` differs.
**LVWE and LVNE are two forecast variants over one shared observed series**, not two scenarios.

**Q8. Are the keys forest-level?**
Yes. All 137 are forest identifiers: `APCP150`, `APCPRD01`–`APCPRD06`, `AREP273`, `AUSP282`,
`AUTP296`, `BRAP284`, `CANPRD01`, `CHEP278`, `DEUP281`, `EURP107`, `NAMPRD07`, `NAMPRD08`, …

**Q9. Does it match the AX4 dashboard?**
Yes, for both requested keys.

| Key | Window | SQL `Mean_Actual` | SQL `Mean_Forecast` | SQL `Accuracy` |
|---|---|---:|---:|---:|
| NAMPRD08 | 2026-08-16 → 2026-08-22 | **11219.51** | **11917.44** | **93.78** |
| NAMPRD07 | 2026-08-16 → 2026-08-22 | **9996.28** | **10905.34** | **90.91** |

The owner's dashboard shows NAMPRD08 at roughly 11,200 actual against 11,900 forecast and
NAMPRD07 at roughly 10,000 against 10,900, both in August 2026. **Reconciled.**

**Q10. Is SSD ready for controlled Parquet extraction in P2?**
Yes — `SSD_READY_FOR_PARQUET_EXTRACTION`, subject to P1B-UQ01 below.

**Q11. Caveats to carry into P2.**
1. Windowed aggregate, not raw daily (mean window 5.22 days).
2. Short history: 130 daily points versus HDD's 1,105–24,905.
3. A single `Forecast_Version` (2026-03-12).
4. LVWE and LVNE share actuals — do not double-count.
5. No raw daily source covers the current period.

**Q12. Does SSD still need 15-model backtest generation?**
**Yes.** Each table holds exactly **one** `Mean_Forecast` column, i.e. one model. Across both
variants that is two forecasts, not fifteen. The 15 AEGIS model backtests must still be
generated in P5 from the extracted actuals.

**Q13. Is a raw daily source available?**

**No — not for the current period.** Three findings establish this:

- `sys.sql_modules` lineage (P1B004) returned **0 hits**: no procedure or view inside the
  database builds LVWE/LVNE. The pipeline is external and cannot be traced read-only.
- `forecast_staging_agent_SSD`, the obvious staging candidate, is **empty** — `COUNT(*)`
  returned 0 despite a catalogue estimate of ~1,000 rows (P1B015).
- The two genuine raw daily sources both closed in 2021:

| Source | Keys >50 | Window |
|---|---:|---|
| `Greenland_SSD_HDD_Forest_Daily_Raw` | 139 | 2020-07-10 → 2021-06-15 |
| `SubstrateBE_SSD_Demand_History` | 142 | 2021-06-10 → 2021-11-08 |

**116 of the Greenland forests also appear in LVWE** (P1B018), so the key spaces overlap — but
the time windows are five years apart with **zero temporal overlap**. The raw sources therefore
cannot validate or extend LVWE.

> **Recommendation:** treat `Mean_Actual` as the **official observed series** for this cohort.
> Logged for owner sign-off as P1B-UQ01.

---

## 3. Corrected capacity

| Metric | Actuals source | Combos >50 | Freshness | Ready for P2 |
|---|---|---:|---|---|
| HDD | Confirmed (P1) | 604 | Current to 2026-08-17 | **No — already local** |
| **SSD** | **Confirmed (P1B)** | **136** | **Current to 2026-08-22** | **YES** |
| CPU | Confirmed (P1) | 60 | **Stale — stops 2023-07-20** | YES, flagged |
| IOPS | Confirmed (P1) | 58 | **Stale — stops 2023-07-20** | YES, flagged |
| Memory | None | 0 | No data | No — blocked |

**P2 extraction scope: SSD + CPU + IOPS = 254 combinations.** HDD is the local baseline.

Against the 130–150 mixed-cohort target, the extractable set alone reaches 254 across three
metrics, and 858 including the local HDD baseline. The target is comfortably met with room to
select representatively.

---

## 4. What changed versus the preliminary P1B report

| Item | Preliminary | Corrected here | Basis |
|---|---|---|---|
| SSD combinations >50 | 272 | **136** | P1B012: LVWE and LVNE share one actual series |
| LVWE/LVNE relationship | "possibly two scenarios" | **Two forecast variants, one observed series** | P1B012 / P1B013 |
| Raw daily source | "closed in 2021" | Same, plus **lineage proven absent** and staging table **proven empty** | P1B004 / P1B015 |
| Series continuity | not measured | **130 distinct dates over 132 days** | P1B014 |
| Null actuals | not measured | **zero nulls in both tables** | P1B005 / P1B007 |

---

## 5. Governance

| Constraint | Observed |
|---|---|
| Read-only | `readonly=True`; only `SELECT` on `sys.*`, `INFORMATION_SCHEMA.*`, plus `GROUP BY`/`EXCEPT` aggregates and `TOP` samples |
| Query budget | **18 of 25** |
| Longest query | 6.33s. Nothing approached the 5-minute stop rule |
| No full extraction | Largest data result was the 137-row key vocabulary |
| No Parquet | 0 files |
| No models | Only `.csv`, `.md`, `.json`, `.py` artifacts |
| Shiny untouched | 0 `shiny_app` entries in `git status` |
| V1–V5 untouched | 0 entries |
| No push | None executed |
| HDD not re-inventoried | Carried forward from P1 as context only |

---

## 6. Deliverables

| File | Purpose |
|---|---|
| `v6_24_p1b_query_ledger.csv` | 18 queries with auth mode, status, duration, row count |
| `v6_24_p1b_ssd_object_sweep.csv` | All 102 SSD objects scored HIGH/MEDIUM/LOW/NONE |
| `v6_24_p1b_ssd_column_mapping.csv` | 43 columns with role and confidence |
| `v6_24_p1b_ssd_actuals_source_assessment.csv` | 5 candidate sources classified |
| `v6_24_p1b_ssd_dashboard_reconciliation.csv` | NAMPRD07 and NAMPRD08 against AX4 |
| `v6_24_p1b_ssd_route_capacity_detail.csv` | 4 variants with observation ranges |
| `v6_24_p1b_corrected_capacity_by_metric.csv` | Corrected readiness for all five metrics |
| `v6_24_p1b_corrected_p2_readiness_plan.csv` | P2 scope — readiness only, no extraction |
| `v6_24_p1b_unresolved_questions.csv` | 6 open questions |
| `v6_24_p1b_validation.csv` | 19 checks |
| `v6_24_p1b_closure_summary.md` | This file |

---

## 7. Operational notes

**Auth.** `ActiveDirectoryInteractive` connected initially in P1 but its token cache expired
mid-session and then blocked indefinitely with no visible prompt, stalling three runs for about
ten minutes each. P1B uses `ActiveDirectoryIntegrated` first (~5s), with Interactive as fallback
and a 90-second ceiling, per the brief. `auth_mode` is recorded on every ledger row.

**Ledger durability.** During the preliminary P1B work a helper script wrote the P1 ledger
without first loading it, truncating 70 rows to 17. That ledger was rebuilt from recorded console
output and flagged `RECONSTRUCTED`. The P1B helper now loads before writing and persists via
`atexit`, so a crash cannot lose the audit trail.

---

## 8. Recommended next step

P2 should plan controlled extraction for **SSD + CPU + IOPS**, with HDD as the local baseline.

Two owner decisions should be settled first:

1. **P1B-UQ01** — accept `Mean_Actual` (rolling 1–7 day window) as the official SSD observed
   series? P1B recommends yes.
2. **P1B-UQ04** — accept a cohort mixing 2026 HDD/SSD history with 2023 CPU/IOPS history, or
   find a fresher CPU/IOPS source first?

---

**V6_24_P1B_SSD_ACTUALS_SOURCE_TRACE_COMPLETED**

Stopping here. P2 not started, no Parquet, no models, no Shiny changes, no push.
