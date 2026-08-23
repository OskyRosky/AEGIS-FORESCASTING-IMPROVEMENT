# V6.24-P1B — SSD Actuals Correction

**Date:** 2026-08-23
**Trigger:** Owner evidence from the AX4 Security dashboard
**Status:** P1's SSD conclusion was **WRONG**. Corrected here.

---

## 1. What P1 got wrong, and why

P1 reported:

> **SSD** — `FORECAST_ONLY`. No actuals source found anywhere.

**That was incorrect.** SSD has current actuals through **2026-08-22**.

Two concrete method failures caused it:

1. **Wrong key axis.** P1 searched SSD by `Key` = *region* in the
   `forecast_substrateBE_ssd_*` tables, mirroring the HDD pattern. SSD actuals are keyed by
   **forest** (`NAMPRD08`, `NAMPRD03`, `INDPRD01`, `GBRP302`, `KORP216`, …).

2. **Insufficient coverage.** P1 catalogued **102** SSD-named objects and probed **3**. Its own
   closure summary admitted this in UQ02 — "only the highest-signal ones were probed" — yet the
   headline conclusion was still stated as settled fact. That was an overreach: a partial search
   was reported as a negative result.

The owner's dashboard showed SSD Phoenix Low Vol. w/ Efficiency actuals for keys
NAMPRD04–NAMPRD11 through August 2026, which contradicted the report directly.

---

## 2. What the exhaustive sweep found

All 102 SSD-named objects had their full column signature read (Q001 of the P1B ledger),
then every object with an actual-shaped column was probed.

| Source | Granularity | Value column | Combos >50 | Window | Currency |
|---|---|---|---:|---|---|
| `forecast_substrateBE_ssd_phx_lvwe_metrics` | Forest | `Mean_Actual` | **136** | 2026-04-07 → **2026-08-22** | **Current** |
| `forecast_substrateBE_ssd_phx_lvne_metrics` | Forest | `Mean_Actual` | **136** | 2026-04-03 → **2026-08-22** | **Current** |
| `SubstrateBE_SSD_Demand_History` | Forest | `SubstrateSSDDemandTB` | 142 | 2021-06-10 → 2021-11-08 | Stale 5y |
| `Greenland_SSD_HDD_Forest_Daily_Raw` | Region × Forest | `SSDDemandTB` | 139 | 2020-07-10 → 2021-06-15 | Stale 5y |

`lvwe` and `lvne` decode to **Low Volume With Efficiency** and **Low Volume No Efficiency** —
exactly the scenario named in the dashboard selector.

### Verification against the owner's dashboard

Sampling `NAMPRD08` from `lvwe` (Q008) returned, for the final window:

| Field | Value |
|---|---|
| Window | 2026-08-16 → 2026-08-22 |
| `Mean_Actual` | **11219.51** |
| `Mean_Forecast` | **11917.44** |
| `Accuracy` | **93.78** |

The dashboard chart for NAMPRD08 shows actual ≈ 11,200 against forecast ≈ 11,900 in
August 2026. **The figures match.** This is the source behind the AX4 dashboard.

---

## 3. Revised metric capacity

| Metric | Combos >50 | Ready for extraction | Note |
|---|---:|---|---|
| HDD | 604 | Already local | Current to 2026-08-17 |
| **SSD** | **272** | **YES** | Current to 2026-08-22, Forest granularity |
| CPU | 60 | YES | Stale: stops 2023-07-20 |
| IOPS | 58 | YES | Stale: stops 2023-07-20 |
| Memory | 0 | No | Governed views empty |

**Total: 994 combinations across four metrics.**

SSD is no longer Forecast-only. It qualifies for the Viewer.

---

## 4. Caveats the owner must weigh

**a. The current SSD actuals are windowed aggregates, not raw daily points.**
Each `lvwe`/`lvne` row covers a rolling 6–7 day window (`Start_Date`, `End_Date`, `Count`),
and `Mean_Actual` is the mean actual over that window. There is one row per key per day,
so it does behave as a daily series — but it is derived, not raw. The raw daily sources
(`Greenland_SSD_HDD_Forest_Daily_Raw`, `SubstrateBE_SSD_Demand_History`) both closed in 2021.
Logged as **UQ09**.

**b. SSD history is short.** 131 observations per key versus HDD's 1,105–24,905. It clears the
50-observation threshold but supports a much shorter backtest. Logged as **UQ10**.

**c. lvwe and lvne may not be independent.** Both carry the same 137 keys over nearly the same
window. If they are one series with two efficiency treatments rather than two scenarios, SSD
contributes 136 combinations, not 272. Logged as **UQ11**.

**d. A single forecast version.** Both tables carry only `Forecast_Version = 2026-03-12` and a
single `Mean_Forecast` column — one model, not fifteen. The actuals are what P2 needs; the
15 AEGIS model backtests still have to be generated downstream.

---

## 5. Correction to the Viewer decision

V6.23-P1 excluded SSD from the Viewer because no SSD actuals existed **locally**. That decision
was correct for the data available at the time, and P1B does not overturn it retroactively.

But P1's stronger claim — that SSD has no actuals **in SQL** — is now withdrawn.
Once the 272 combinations are extracted in P2, **SSD becomes Viewer-eligible** and the
Viewer/Forecast parity gap narrows.

---

## 6. Operational note

`Authentication=ActiveDirectoryInteractive` connected initially but its token cache expired
mid-session and then blocked indefinitely with no visible prompt, stalling three runs for
roughly ten minutes each. `Authentication=ActiveDirectoryIntegrated` connects in about five
seconds and is now attempted first in `_p1_sql.connect()`, with Interactive retained as fallback.

---

**V6_24_P1B_SSD_ACTUALS_CORRECTION_COMPLETED**

Still read-only. Nothing extracted, no Parquet, no models, no Shiny changes, no push.
