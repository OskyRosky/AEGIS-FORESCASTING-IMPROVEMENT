# V3.2D — Candidate Remediation + Governed Full Backtest (FINAL, COMPLETE)

- Stage: V3.2D
- Active root: V3 (V1 and V2 frozen, untouched)
- Run date: 2026-06-26
- Champion (reference, NOT re-fit): ETS Explicit — governed median MASE 6.901143533373399
- Governed metric: MASE/RMSSE with training-only lag-1 first-difference denominator (EPSILON=1e-6), from `model_lab.benchmark_denominators`. NOT seasonal.
- Backtest universe: 454 governed entity-windows, 39 series, 12 unique window_ids, horizon h30.
- Overall status: **COMPLETE**. All 6 candidates fully evaluated on all 454 governed entity-windows.
- Completion method: authorized **Option B** — XGB-IMP-v2 run in ISOLATION (60-min budget) to finish its missing windows, then merged into the existing partial-run canonical outputs. No other candidate was re-run.

---

## 1. XGB-IMP-v2 completion status

- The controlled 30-min run had left XGB-IMP-v2 INCOMPLETE at 417/454 windows (`TIME_BUDGET_EXCEEDED`, by design).
- Per Oscar's Option B authorization, XGB-IMP-v2 was re-run in ISOLATION with a 60-min wall-clock budget via `python/model_lab/run_v3_2d_xgb_completion.py`.
- Result: **stop_status = ok**, n_windows = **454/454**, raw_neg = **0**, runtime = 1339.35s, wall = **22.4 min** — well within the 60-min budget.
- Governed COMPLETE result: median MASE **27.950413**, median RMSSE **6.426824** (the partial 30-min figure was 27.454; the complete figure is 27.950).
- No global or per-candidate budget was exceeded; the run finished naturally.

## 2. Merge status

The isolated XGB-IMP-v2 full results were merged into the existing partial-run canonical outputs (other candidates untouched):

- `candidate_outputs/full_candidate_outputs.csv` — replaced 12,510 partial XGB rows with 13,620 complete rows (454 windows × 30 horizon). Total now **81,720** rows (6 candidates × 454 × 30). PASS.
- `metrics/full_backtest_metrics_summary.csv` — XGB candidate row updated to complete (**n_windows = 454**, completion_status = ok). PASS.
- `runtime_checks/full_runtime_results.csv` — XGB `full_backtest` row updated to complete (454 windows, 1339.35s, gate VIABLE, status ok). PASS.
- `candidate_recommendations.csv` — XGB recommendation refreshed (median MASE 27.950; runtime 22.3 min within 60-min budget). PASS.
- `logs/full_backtest_run_log.csv` — old XGB rows replaced with complete XGB per-window log.
- `_v3_2d_run_summary.json` — `overall_status = COMPLETE`; `incomplete_candidates = []`; `budget_events = []`; added `xgb_completion` block and `max_wall_clock_budget_minutes_for_completion = 60.0`.
- `runtime_checks/xgb_completion_results.csv` — isolated-completion audit record written.

## 3. Final runtime results (governed full backtest, 454 entity-windows)

| Candidate | Stage | Windows | Runtime | Proj. full (min) | Gate | Status |
|---|---|---|---|---|---|---|
| FNAR-V2 | full_backtest | 454 | 195.7s | 3.26 | VIABLE | ok |
| NLIN-DLIN_FIXED | full_backtest | 454 | 1.0s | 0.02 | VIABLE | ok |
| SMLP-TCN | full_backtest | 454 | 29.2s | 0.49 | VIABLE | ok |
| ENET-RIDGE | full_backtest | 454 | 1.4s | 0.02 | VIABLE | ok |
| LGBM-IMP-v2 | full_backtest | 454 | 462.9s | 7.72 | VIABLE | ok |
| XGB-IMP-v2 | full_backtest | 454 | 1339.3s | 22.32 | VIABLE | ok |

- GBM re-gate (subset, single-model horizon-feature, n_estimators=300, log1p): LGBM proj 11.84 min VIABLE; XGB proj 24.18 min VIABLE.
- XGB's actual complete full backtest = 22.3 min, within both the 25-min daily-refresh threshold and the 60-min completion budget.

## 4. Final metrics summary (governed, COMPLETE)

| Candidate | Model | Family | DL/ML | Median MASE | Median RMSSE | raw_neg | Windows | Status |
|---|---|---|---|---|---|---|---|---|
| SMLP-TCN | SmallMLPGlobal | lightweight_neural | DL | 18.783 | 4.790 | 0 | 454 | complete |
| ENET-RIDGE | Ridge_direct_multi_horizon | linear_ml | ML | 19.331 | 5.028 | 0 | 454 | complete |
| NLIN-DLIN_FIXED | NLinear_log_space_fixed | linear_dl | DL | 24.816 | 6.641 | 0 | 454 | complete |
| LGBM-IMP-v2 | LightGBM_candidate_improved_v2 | gradient_boosting | ML | 26.747 | 6.328 | 0 | 454 | complete |
| XGB-IMP-v2 | XGBoost_candidate_improved_v2 | gradient_boosting | ML | 27.950 | 6.427 | 0 | 454 | complete |
| FNAR-V2 | FastNeuralAR_MLP_v2_direct | lightweight_neural | DL | 81.668 | 22.405 | 0 | 454 | complete |

- Ranking by governed median MASE (best→worst): SMLP-TCN 18.783 < ENET-RIDGE 19.331 < NLIN-DLIN_FIXED 24.816 < LGBM-IMP-v2 26.747 < XGB-IMP-v2 27.950 < FNAR-V2 81.668.
- Best new DL candidate: **SMLP-TCN** (18.783). Best new ML candidate: **ENET-RIDGE** (19.331).
- All candidates non-negative-clean (raw_neg = 0); NLIN log-space fix confirmed (27 → 0).

## 5. Final comparison vs ETS Explicit champion (6.901) and baselines

- **No candidate beat the champion (6.901)** or the top-baseline band (AutoARIMA 8.089 / FixedGrowth_1_5 8.649 / ETS_Current 8.654).
- vs-champion ratios: SMLP 2.72x, ENET 2.80x, NLIN 3.60x, LGBM 3.88x, XGB 4.05x, FNAR 11.83x.
- Context vs current registry FastNeuralAR (739.922): every candidate is dramatically better — FNAR-V2 (81.7) is ~9x better than the registered 739.9; SMLP-TCN (18.8) is ~39x better.
- Net: candidates are mid-pack — strong relative to the worst current registry entries, but not competitive with the ETS Explicit champion.

## 6. Final recommendation by candidate (advisory only — NO auto-promotion)

| Candidate | Median MASE | vs champion | Runtime | Guardrail | Recommendation |
|---|---|---|---|---|---|
| SMLP-TCN | 18.783 | 2.72x | 29.2s | PASS | keep as challenger (best new DL) |
| ENET-RIDGE | 19.331 | 2.80x | 1.4s | PASS | keep as challenger (best new ML) |
| NLIN-DLIN_FIXED | 24.816 | 3.60x | 1.0s | PASS | keep as challenger (non-neg fix confirmed) |
| LGBM-IMP-v2 | 26.747 | 3.88x | 462.9s | PASS | keep as challenger (runtime within 60-min budget) |
| XGB-IMP-v2 | 27.950 | 4.05x | 1339.3s | PASS | keep as challenger (runtime 22.3 min within 60-min budget) |
| FNAR-V2 | 81.668 | 11.83x | 195.7s | PASS | keep as challenger (huge improvement over registered FastNeuralAR 739.9) |

- All six are retained as CHALLENGERS only. None is promoted. The champion (ETS Explicit) is unchanged.

## 7. Governance confirmation

- Non-negativity: ALL candidates raw_neg = 0 (NLIN fix 27 → 0). PASS.
- Governed denominator: training-only lag-1 first-difference, EPSILON = 1e-6. Enforced. No seasonal denominator.
- Determinism: RANDOM_SEED = 42, PYTHONHASHSEED = 42.
- Champion NOT re-fit; anchors used as governed reference only.
- Scope respected: all experiments confined to `outputs/v3_2b_model_candidates/`. No config, registry, governance, forecast, interval, or `data/processed` artifact changed. V1 and V2 untouched.

## 8. V3.2D final status

- **Overall status: COMPLETE.** All 6 candidates fully evaluated on all 454 governed entity-windows.
- Completion respected the 60-min isolated budget (XGB finished in 22.4 min).
- Champion unchanged; no promotion performed.
- V3.2D is officially **CLOSED**.

## 9. Recommended next step

- No further model optimization at this time (per Oscar's directive). V3.2D is closed.
- The ETS Explicit champion remains clearly superior; the six remediated/new candidates are documented challengers with complete governed evaluations for future reference.
- Standing rule recorded for future full runs: global wall-clock budget = **60 minutes**.

---

## Appendix A — Files created/updated in the completion phase

- `python/model_lab/run_v3_2d_xgb_completion.py` — isolated XGB completion + merge harness (Option B). (Temporary; removed after closure.)
- `outputs/v3_2b_model_candidates/runtime_checks/xgb_completion_results.csv` — isolated-completion audit record.
- `outputs/v3_2b_model_candidates/logs/v3_2d_xgb_completion.log`, `logs/v3_2d_xgb_completion_stderr.log` — completion console/progress and stderr capture.
- Merged/updated: `candidate_outputs/full_candidate_outputs.csv`, `metrics/full_backtest_metrics_summary.csv`, `runtime_checks/full_runtime_results.csv`, `candidate_recommendations.csv`, `logs/full_backtest_run_log.csv`, `_v3_2d_run_summary.json`.
- Regenerated: `v3_2d_report.md` (this report), `v3_2d_validation.csv`.

## Appendix B — Historical partial run (30-min controlled run)

- The earlier 30-min controlled run stopped at XGB window 417/454 with `TIME_BUDGET_EXCEEDED` (by design, not a fault). Its partial artifacts (`partial_*`, `v3_2d_partial_report.md`) remain as a historical record.
- The earlier overnight "11h hang" was diagnosed as machine sleep suspending the process, NOT a code defect; AC sleep was disabled and budgets/partial-output controls were added.
