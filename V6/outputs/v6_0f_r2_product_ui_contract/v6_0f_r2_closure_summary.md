# V6.0F-R2 — Product / UI Decision Contract — Closure Summary

**Status token:** `V6_0F_R2_PRODUCT_UI_DECISION_CONTRACT_COMPLETED`

**Nature:** documentation only. No code, no Shiny, no data, no SQL, no Docker, no Azure.

---

## Deliverables

| # | File | Purpose |
|---|---|---|
| 1 | ui_decision_contract.csv | 29 rows: every Metric x Scenario x Granularity combination with source, key, badge and exposure flag |
| 2 | metric_scope_register.csv | The 9 requested metrics with in-scope decision and reason |
| 3 | viewer_scenario_contract.csv | 18 rows: what Viewer renders per combination |
| 4 | forecast_scenario_contract.csv | 20 rows: what Forecast renders per combination |
| 5 | control_cascade_spec.md | Control order, cascade rules, badge rules, empty states |
| 6 | out_of_scope_notice_copy.md | Approved wording for Memory, badges and provenance |
| 7 | remaining_questions_register.csv | 10 open questions with the stage each one blocks |
| 8 | v6_0f_r2_validation.csv | 20 checks, all PASS |
| 9 | v6_0f_r2_closure_summary.md | This file |

---

## Contract in one view

| Layer | Decision |
|---|---|
| Control order | Metric → Scenario → Granularity → Key → Forecast Version → Model/Type |
| Metrics in scope | 8 of 9. Memory excluded (D1) |
| Viewer FULL | HDD - EDB and HDD - Basilisk only, Region and Forest (D3) |
| Viewer FORECAST-ONLY | CPU, CPU Failover, IOPS, IOPS Failover, SSD - Phoenix (D3) |
| SSD - Phoenix scenarios exposed | 2 of 24 (D2) |
| Keys | exactly as stored in Tesseract, Forest_SKU preserved (D4) |
| type | separate model dimension, never merged with Scenario (D5) |
| Granularity | separate control Region / Forest (D6) |
| Delivery surface | inside Forecasting → Viewer and Forecasting → Forecast; no new tab (D7) |

---

## Exposure counts

| Category | Combinations |
|---|---:|
| Exposed in first release | 16 |
| Documented but not exposed | 12 |
| Out of scope | 1 |
| **Total contract rows** | **29** |

---

## Blocking questions carried forward

| ID | Blocks | Summary |
|---|---|---|
| O1 | R5 | SSD - MCDB scenario selection undefined |
| O2 | R3 | HDD Forest casing mismatch on 'consumer' |
| O3 | R2/R7 | Is DBType a fourth control |
| O4 | R5 | How many forecast versions to extract |
| O5 | R5 | Temporal window of the extract |
| O6 | G1 | Confirm the exact Boon deliverable |
| O7 | R9b | Accuracy re-sync in the same release |
| O8 | R9c | Assistant coverage decision |
| O9 | R5b | Storage format for large sources |
| O10 | R3 | Individual vs grouped type values |

---

## Governance

| Invariant | Result |
|---|---|
| Documentation only | Respected |
| No code modified by R2 | Respected |
| No SQL executed | Respected |
| No data extracted | Respected |
| No Docker or Azure | Respected |
| Not advanced to R3 R5 R5b R6 R7 R8 R9 R9b R9c R10 G1 G2 | Respected |
