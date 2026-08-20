# V6.0F-R8 — Viewer Integration — Closure Summary

**Status token:** `V6_0F_R8_VIEWER_INTEGRATION_COMPLETED`

---

## 1. What was implemented

A **Scenario explorer** block inside the existing `Forecasting → Viewer` page. No new tab.

```
Metric → Scenario → Granularity → Key → Forecast Version → Model / Type
```

- Dropdowns served from 62.4 KB of metadata slices
- Series served lazily from DuckDB, read-only and parameterised
- Badge, status notice, chart and data notes driven entirely by the resolver
- The legacy backtest boxes, methodology note and Assistant panel are untouched

**14 insertions, 0 deletions** across 4 files, plus 2 new Viewer-only files.

---

## 2. What was validated

| Suite | Result |
|---|---|
| Viewer tests | **17 / 17 PASS** |
| Empty states | **7 / 7 PASS** |
| Governance checks | **40 / 40 PASS** |
| Performance | worst case **0.090 s**, budget 1 s |
| Live browser | verified for HDD and SSD-Phoenix |

Live measurements taken from the running app:

| Selection | Badge | Rows | Time |
|---|---|---:|---:|
| HDD - EDB / Enterprise / Forest / NAMPRD07 | Actual + Forecast | 1,097 | 0.088 s |
| HDD - Basilisk / Basilisk / Forest / apc-Dedicated | Actual + Forecast | 954 | 0.089 s |
| SSD - Phoenix / Low Volume No Efficiency / NAMPRD07 | Forecast only | 732 | 0.088 s |

The decisive check: `namprd07` and `NAMPRD07` both return **954 rows**.

---

## 3. How to test it manually

1. Start the app from `V6/shiny_app`:
   `Rscript -e "options(shiny.port=8081, shiny.launch.browser=FALSE); shiny::runApp('.')"`
2. Open `http://127.0.0.1:8081` and click **Forecasting → Viewer**.
3. Confirm **Multi-Metric does not exist** in the sidebar.
4. In **Scenario explorer**, set Metric = `HDD - EDB`, Scenario = `Enterprise`, Granularity = `Forest`, Key = `NAMPRD07`.
   Expect the badge **Actual + Forecast**, a black `Actual` line plus the selected models, and notes reading `viewer_hdd · 1,097 rows`.
5. Switch Metric to `HDD - Basilisk`. Expect Key `namprd07` in lowercase and the chart still rendering.
6. Switch Metric to `SSD - Phoenix`. Expect the badge **Forecast only**, the amber notice, **no model selector**, and 3 forecast versions.
7. Confirm `Memory`, `CPU`, `IOPS` and `SSD - MCDB` never appear in the Metric list.
8. Scroll down and confirm the legacy **Set up the backtest view** box and **Analyze Backtest** still work.

---

## 4. Defects found and fixed

| # | Defect | Root cause | Fix |
|---|---|---|---|
| D1 | All 8 new outputs stuck in `recalculating` | This app hides inactive panels, so Shiny suspends their outputs. The codebase already handles this for every `fvp_*` output. | Added `suspendWhenHidden = FALSE`, matching the existing pattern |
| D2 | `actual` appeared as a selectable model | `actual` is a series type, not a model; the family classifier let it through | Excluded the `Actual` and `Marker` families from the metadata slice |

---

## 5. Open risks

| ID | Risk | Severity | Note |
|---|---|---|---|
| RB5 | The DuckDB store must be rebuilt whenever R6 re-extracts | 🟠 Medium | `build_storage.R` does it, but it is not automated |
| RB9 | Basilisk exposes 1 model type and 1 version | 🟠 Medium | Rendered honestly; nothing simulated |
| RN3 | The Viewer artifact is not versioned, so the version control reads *Not applicable* for HDD | 🟡 Low | Stated in the UI; the Forecast page will use the versioned tables |
| RN4 | Viewer and legacy backtest now show two different data sources on one page | 🟡 Low | Each box names its own source; consider consolidating after R9 |

---

## 6. What is left for R9

| Item | Status |
|---|---|
| Resolver | ✅ Reusable as is; `page = "forecast"` already implemented and tested |
| Storage | ✅ `forecast_hdd` and `forecast_ssd` tables already built |
| Version control | ✅ Applies fully on the Forecast page, unlike the Viewer |
| Work required | Wire the same cascade into `section_forecast()` and its server block |

**R9 is unblocked.** It is a narrower job than R8: the resolver, the storage and the loading contract already exist and are proven.

---

## 7. Governance

| Invariant | Result |
|---|---|
| Only the Viewer touched | Respected |
| Forecast, Accuracy, TTL, Universe, Tournament, Champion, Risks, Audit, Artifacts, Methodology, Version untouched | Respected |
| Assistant and LLM files untouched | Respected — hash `A4DB09B4` |
| Legacy Viewer not broken | Respected — verified live |
| No Multi-Metric tab | Respected |
| No heavy CSV read at runtime | Respected |
| No Tesseract query, no SQL write, no extraction | Respected |
| No simulated data, no zero filling, no invented actuals | Respected |
| V1 to V5 untouched | Respected |
| No Azure, no Docker | Respected |
| Not advanced to R9, R9b, R9c, R10, G1, G2, R6 Phase 2 | Respected |
