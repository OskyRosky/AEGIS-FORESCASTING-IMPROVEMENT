# V3.2F — Full Model Results Integration into Shiny

**Status:** `V3_2F_FULL_MODEL_SHINY_INTEGRATION_COMPLETED`
**Scope:** Read-only integration of the complete evaluated model universe (base/statistical champion + ML + DL challengers) from CLOSED V3.2D/V3.2E into the live Shiny dashboard's Models views, plus an integrated **Evaluation Results** section.
**Champion:** ETS Explicit — **unchanged**. No forecasts, intervals, or governance decisions were modified.

---

## 1. Executive summary

V3.2F surfaces, inside the existing Tesseract V3 Shiny dashboard, the full set of
models that were evaluated during the CLOSED V3.2D/V3.2E phases — the governed
champion **ETS Explicit** together with the machine-learning and deep-learning
challengers — presented as **backtest evaluation results**, not as production
forecasts. The work is an *integration* into the existing Models group (Universe,
Tournament, Champion) plus a new **Evaluation Results** sub-tab; it is explicitly
**not** an isolated "Candidate Lab" island. Everything is read-only: no model was
fitted, no backtest was re-run, no forecast or interval was regenerated, and the
champion selection was not changed. The app builds and serves successfully
(HTTP 200) with the five new governed-compact artifacts loaded.

## 2. Inputs used

- Closed **V3.2E Candidate Decision Package** (`outputs/v3_2e_candidate_decision_package/`,
  15/15 validation checks PASS).
- Governed compact summaries derived from the CLOSED **V3.2D/V3.2E** evaluation
  (medians, ranking, champion comparison, runtime/guardrails).
- No raw candidate execution output (`full_candidate_outputs.csv`) was copied;
  only compact, dashboard-ready summaries were produced.

## 3. data/processed artifacts created

| File | Rows × Cols | Purpose |
|------|-------------|---------|
| `model_evaluation_summary.csv` | 7 × 12 | Per-model family/role, median MASE/RMSSE, vs-champion ratio, decision |
| `model_evaluation_ranking.csv` | 7 × 8 | Final ranking (rank 0 = ETS Explicit reference) |
| `model_champion_comparison.csv` | 6 × 8 | Each challenger vs champion, gap, promotion eligibility |
| `model_runtime_guardrails.csv` | 6 × 10 | Runtime, windows completed, guardrail status |
| `model_dashboard_summary.csv` | 1 × 11 | Headline KPIs + final-decision / status message |

All five are governed-compact, read-only summaries. `data/processed` is gitignored.

## 4. Shiny files modified

- `shiny_app/R/data_loader.R` — registered 5 optional artifacts under category `model_eval`.
- `shiny_app/R/helpers.R` — added accessors (`model_eval_summary()`, `…_ranking()`,
  `…_champion_comparison()`, `…_runtime_guardrails()`, `model_eval_dashboard_values()`)
  and four static `uni-table` HTML table builders (read-only, no DT/server handlers).
- `shiny_app/ui/tabs.R` — added `section_evaluation()`, registered it in `app_sections()`,
  and enriched `section_universe`, `section_tournament`, `section_champion`.
- `shiny_app/ui/sidebar.R` — added an **Evaluation** link under the Models group.
- `shiny_app/ui/body.R` — added a guide-overlay entry for the Evaluation section.

## 5. How Models → Universe was updated

`section_universe` gained a collapsible block **"Full evaluated model universe
(challengers)"** that lists the champion reference plus every ML and DL challenger
from the evaluated universe, so the Universe view now reflects the *complete* set of
models considered, not only the statistical entrants.

## 6. How Models → Tournament was updated

`section_tournament` footer now cross-references the integrated **Evaluation Results**
view, directing users to the governed backtest comparison of all challengers against
the champion, keeping the Tournament narrative connected to the full evaluation.

## 7. How Models → Champion was updated

`section_champion` gained a collapsible block **"Challenger evaluation (V3.2D/V3.2E)"**
that shows the best ML and DL challengers and their gap to ETS Explicit, reinforcing
*why* the champion is unchanged while exposing the underlying evaluation.

## 8. Evaluation Results section added

A new **Evaluation Results** section (`section_evaluation()`) was added under the
Models group and registered in `app_sections()`. It contains:
- a banner card stating these are backtest evaluation results (not production);
- an "Evaluation at a glance" KPI row (champion, best DL, best ML, candidates promoted);
- "How to read these results";
- the **Final ranking** table;
- **Evaluation summary & decision**, **Champion comparison**, and **Runtime & guardrails** tables.
Section switching reuses the generic `data-section` JS toggle — no JS change was needed.

## 9. Validation result

`outputs/v3_2f_full_model_shiny_integration/v3_2f_validation.csv` — **25/25 checks PASS**,
covering V3.2E pre-conditions, artifact creation, Models-view enrichment, app load,
HTTP 200, and all no-change governance guarantees (champion/forecast/interval/governance,
no model or backtest execution, V1/V2 untouched, V3.3/V4 not started).

## 10. Local app test result

- R parse check: 5/5 modified files `PARSE_OK`.
- Smoke test (sourced `global.R` + `ui/body.R`): accessors, four table builders,
  `section_evaluation()`, and sidebar Evaluation link all rendered with non-empty data;
  `champion=ETS Explicit`, `best_dl=SMLP-TCN`, `best_ml=ENET-RIDGE`, `promoted=0`, `total=6`.
- App launched on port 3838 (pid 17292), single listener; `Invoke-WebRequest` → **HTTP 200**.
- stderr log: no `Error`; only a benign readr parsing warning. App stopped cleanly after test.
- Closure re-verification (pid 34344): served HTML (262 KB) contains all four Models
  `data-section` panels (universe, tournament, champion, evaluation) and the names
  ETS Explicit, SMLP-TCN, ENET-RIDGE and FNAR-V2; stderr had 0 errors / 1 benign warning.

## 11. Governance confirmation

- Champion **ETS Explicit** unchanged (MASE 6.901144, RMSSE 1.856193).
- Best DL challenger **SMLP-TCN** (MASE 18.782572) and best ML challenger
  **ENET-RIDGE** (MASE 19.330846) shown as evaluation only.
- `total_candidates_promoted = 0`; no promotion, no governance decision changed.
- `forecasts.csv` and prediction intervals untouched; no model run, no backtest re-run.
- No future forecasts produced. V1/ and V2/ untouched. Shiny remains read-only.

## 12. Known limitations

- Challenger metrics are point-in-time summaries from the CLOSED V3.2D/V3.2E run; they
  are not recomputed live and will not change unless a future authorized phase re-evaluates.
- Tables are static `uni-table` HTML (no sorting/filtering) to avoid server/DT changes.
- `data/processed` is gitignored, so the new CSVs are local artifacts.

## 13. Next recommended step

Hold. **V3.3 is not started.** Awaiting explicit user authorization before initiating
any further phase (e.g., refreshed evaluation or champion re-assessment).
