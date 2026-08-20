# V6.0F-R4 — Multi-Metric Removal Report

**Objective:** remove the Multi-Metric section added in V6.0F. It was never requested and is not the final product (D7).

---

## 1. What was removed

The V6.0F integration was purely **additive**: 16 inserted lines across 5 files, plus 3 new files. No existing line had been modified or deleted. That made the removal exact rather than reconstructive.

| File | Removed |
|---|---|
| `global.R` | `source("R/multi_metric_loader.R")`, `source("server/multi_metric_server.R")`, `mm_init()` and their comment block (7 lines) |
| `server/server.R` | `multi_metric_server(...)`, `llm_explain_server("llm_multi_metric", ...)` and their comment block (6 lines) |
| `ui/body.R` | `source("ui/tabs_multi_metric.R")` (1 line) |
| `ui/sidebar.R` | Multi-Metric menu entry in the Forecasting group (1 line) |
| `ui/tabs.R` | `section_multi_metric()` in `app_sections()` (1 line) |

| File deleted | Backup |
|---|---|
| `R/multi_metric_loader.R` | `reverted_files_backup/` |
| `server/multi_metric_server.R` | `reverted_files_backup/` |
| `ui/tabs_multi_metric.R` | `reverted_files_backup/` |

The three deleted files were untracked by git, so a backup copy was kept rather than relying on version control.

---

## 2. Method

Surgical edits were used instead of `git checkout`, so that every removal is individually reviewable. The result was then verified against git HEAD.

**`git status --porcelain -- V6/shiny_app` returns empty.** The application directory is byte-identical to HEAD.

---

## 3. Verification performed

| Layer | Evidence |
|---|---|
| Code | 0 residual matches for `multi_metric`, `multimetric`, `mm_init`, `metrics_multi` in any `.R` file |
| R runtime | `section_multi_metric`, `multi_metric_server`, `mm_init` all report `exists() = FALSE` |
| Served HTML | `Multi-Metric`, `multimetric`, `multi_metric` all absent |
| Page weight | 316,354 → 303,501 bytes, consistent with removing one section |
| Assistant | 11 evidence pages load; registered ids identical to HEAD |
| Legacy pages | 14 sections present and unchanged |

---

## 4. Two findings worth recording

**Finding 1 — the `layer-group` icon is still in the HTML.** This is not a leftover. It belongs to the legacy **Model Universe** entry at `ui/sidebar.R` line 12. Verified, not a regression.

**Finding 2 — the assistant has 10 server registrations, not 11.** An earlier note in this workstream recorded 11. The correct figure at git HEAD is **10**, and the current figure is also 10, so parity is exact. The evidence pack itself contains 11 page responses; one of them has no `llm_explain_server()` registration in `server.R`. This predates V6.0F and is unrelated to the removal, but it is logged here as an open observation for R9c.

---

## 5. What was deliberately left alone

| Item | Reason |
|---|---|
| `V6/outputs/metrics_multi/` | Artifacts were not deleted, only unreferenced. They remain available as evidence of what V6.0E produced. No code path reads them any more. |
| `V6/outputs/v6_0c…`, `v6_0d…`, `v6_0e…`, `v6_0f…` | Historical record of the workstream, including its errors. |
| Everything outside `V6/shiny_app` | Out of R4 scope. |

---

## 6. Result

The dashboard is back to its pre-V6.0F state. The Scenario and Key integration will be built inside **Forecasting → Viewer** and **Forecasting → Forecast** in R8 and R9, following the contract frozen in V6.0F-R2.
