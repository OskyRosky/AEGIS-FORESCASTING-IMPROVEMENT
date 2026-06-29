# V3.2E — Candidate Decision Package (FINAL)

- Stage: V3.2E (analysis / decision / documentation ONLY — no training, no backtests, no forecasts, no Shiny, no data/processed writes)
- Active root: V3 (V1 and V2 frozen, untouched)
- Date: 2026-06-26
- Source of truth: V3.2D FINAL COMPLETE run (`outputs/v3_2b_model_candidates/`)
- Governed metric: MASE/RMSSE with training-only lag-1 first-difference denominator (EPSILON=1e-6), NON-seasonal — confirmed identical to V3.2D.
- Champion (reference, NOT re-fit): **ETS Explicit** — governed median MASE **6.901144**, RMSSE **1.856193**.
- Output location: `outputs/v3_2e_candidate_decision_package/`

---

## 1. Executive summary

V3.2D produced a complete, governed evaluation of 6 remediated/new forecasting candidates over all 454 governed entity-windows (39 series × 12 window dates, horizon 30). This decision package converts those final results into a formal model-decision record.

**Outcome:** No candidate is competitive with the governed champion. The best candidate (SMLP-TCN, median MASE 18.783) is **2.72× worse** than ETS Explicit (6.901) and still **2.17× worse** than the top governed baseline band (~8.65). Therefore:

- **Champion remains ETS Explicit.** No promotion. No production forecast replacement.
- All 6 candidates are retained as **documented experimental challengers** only.
- **Best deep-learning challenger: SMLP-TCN.** **Best machine-learning challenger: ENET-RIDGE.**
- The FastNeuralAR remediation (FNAR-V2, 81.668) hugely improves the original FastNeuralAR_MLP (≈739.9, ~9× better) but remains far from the champion.
- **Recommendation:** close V3.2 model-improvement with no further optimization now; the next stage is **V3.2F — Candidate Results Shiny Integration** (read-only summaries), pending Oscar's authorization.

## 2. V3.2D evidence used

Inputs read for this decision (all under `outputs/v3_2b_model_candidates/`):

- `v3_2d_report.md` (FINAL COMPLETE), `v3_2d_validation.csv` (overall_status=COMPLETE), `_v3_2d_run_summary.json` (overall_status=COMPLETE, incomplete_candidates=[], budget_events=[], xgb_completion block).
- `candidate_outputs/full_candidate_outputs.csv` (81,720 rows).
- `metrics/full_backtest_metrics_summary.csv` (candidates + governed anchors).
- `runtime_checks/full_runtime_results.csv` (per-candidate runtime + gate).
- `candidate_recommendations.csv` (advisory per-candidate).

Governed reference anchors confirmed in the metrics summary:

- ETS Explicit (champion): median MASE 6.901144, RMSSE 1.856193.
- Top baseline band: AutoARIMA 8.089, FixedGrowth_1_5 8.649, ETS_Current 8.654 (~8.65).
- Original FastNeuralAR_MLP (under audit): median MASE 739.922.

## 3. Candidate universe

6 candidates, all completed on 454/454 windows, raw_neg=0, status=ok:

| Candidate | Model | Family | DL/ML |
|---|---|---|---|
| FNAR-V2 | FastNeuralAR_MLP_v2_direct | lightweight_neural | DL |
| NLIN-DLIN_FIXED | NLinear_log_space_fixed | linear_dl | DL |
| SMLP-TCN | SmallMLPGlobal | lightweight_neural | DL |
| ENET-RIDGE | Ridge_direct_multi_horizon | linear_ml | ML |
| LGBM-IMP-v2 | LightGBM_candidate_improved_v2 | gradient_boosting | ML |
| XGB-IMP-v2 | XGBoost_candidate_improved_v2 | gradient_boosting | ML |

## 4. Champion comparison

Champion ETS Explicit median MASE = 6.901144. Every candidate is materially worse:

| Candidate | Median MASE | vs champion | Gap (MASE) | Promotion eligible |
|---|---|---|---|---|
| SMLP-TCN | 18.783 | 2.72× | +11.88 | No |
| ENET-RIDGE | 19.331 | 2.80× | +12.43 | No |
| NLIN-DLIN_FIXED | 24.816 | 3.60× | +17.91 | No |
| LGBM-IMP-v2 | 26.747 | 3.88× | +19.85 | No |
| XGB-IMP-v2 | 27.950 | 4.05× | +21.05 | No |
| FNAR-V2 | 81.668 | 11.83× | +74.77 | No |

No candidate even reaches the top governed baseline band (~8.65); the closest (SMLP-TCN) is still 2.17× worse than that band.

## 5. Ranking final (governed median MASE, best → worst)

| Rank | Candidate | Median MASE | Median RMSSE | Family |
|---|---|---|---|---|
| — (ref) | ETS Explicit (champion) | 6.901 | 1.856 | statistical |
| 1 | SMLP-TCN | 18.783 | 4.790 | lightweight_neural (DL) |
| 2 | ENET-RIDGE | 19.331 | 5.028 | linear_ml (ML) |
| 3 | NLIN-DLIN_FIXED | 24.816 | 6.641 | linear_dl (DL) |
| 4 | LGBM-IMP-v2 | 26.747 | 6.328 | gradient_boosting (ML) |
| 5 | XGB-IMP-v2 | 27.950 | 6.427 | gradient_boosting (ML) |
| 6 | FNAR-V2 | 81.668 | 22.405 | lightweight_neural (DL) |

## 6. Best DL candidate

**SMLP-TCN (SmallMLPGlobal)** — median MASE 18.783, RMSSE 4.790, runtime 29.2s, raw_neg=0. Best of the three deep-learning candidates and best overall candidate, but 2.72× the champion. Retain as documented DL challenger only.

## 7. Best ML candidate

**ENET-RIDGE (Ridge_direct_multi_horizon)** — median MASE 19.331, RMSSE 5.028, runtime 1.4s, raw_neg=0. Best of the three machine-learning candidates; fastest viable candidate. 2.80× the champion. Retain as documented ML challenger only.

## 8. FastNeuralAR remediation conclusion

The original FastNeuralAR_MLP (recursive, 55 negative forecasts, median MASE ≈739.9) was remediated as **FNAR-V2** (direct multi-horizon, log1p, non-negativity clamp, regularization). Result: median MASE **81.668**, raw_neg **0** — roughly **9× better** than the registered model and non-negativity-clean. This validates that the original defect was an implementation issue (recursive collapse + no transform), not the family per se. However, 81.668 is still **11.83× the champion**, so FNAR-V2 does NOT compete and is retained as a documented challenger only.

## 9. Runtime conclusion

All 6 candidates are runtime-VIABLE under the governed 25-min daily-refresh threshold and the 60-min completion budget:

| Candidate | Runtime | Note |
|---|---|---|
| NLIN-DLIN_FIXED | 1.0s | trivial |
| ENET-RIDGE | 1.4s | trivial |
| SMLP-TCN | 29.2s | fast |
| FNAR-V2 | 195.7s (3.3 min) | viable |
| LGBM-IMP-v2 | 462.9s (7.7 min) | viable |
| XGB-IMP-v2 | 1339.3s (22.3 min) | viable, within 60-min budget |

Runtime is not a blocker for any candidate; accuracy is. (XGB is the slowest at 22.3 min — acceptable but the heaviest if ever operationalized.)

## 10. Guardrail conclusion

- Non-negativity: ALL candidates raw_neg = 0 across all 81,720 rows (NLIN log-space fix confirmed 27 → 0; FNAR-V2 55 → 0). PASS.
- Governed denominator: training-only lag-1 first-difference, EPSILON=1e-6, non-seasonal. Enforced and identical to V3.2D.
- Determinism: RANDOM_SEED=42, PYTHONHASHSEED=42.
- All candidate `status=ok`; all 454/454 windows complete; no budget events.

## 11. Decision table by candidate

| Candidate | Final decision | Reason | Dashboard visibility |
|---|---|---|---|
| SMLP-TCN | keep as documented challenger | best DL & best overall candidate, but 2.72× champion | show as best DL challenger |
| ENET-RIDGE | keep as documented challenger | best ML candidate, fastest, but 2.80× champion | show as best ML challenger |
| NLIN-DLIN_FIXED | keep as documented challenger | non-neg fix validated, but 3.60× champion | show in full challenger table |
| LGBM-IMP-v2 | keep as documented challenger | viable runtime, but 3.88× champion | show in full challenger table |
| XGB-IMP-v2 | keep as documented challenger | complete (454/454), but 4.05× champion, slowest | show in full challenger table |
| FNAR-V2 | keep as documented challenger | huge improvement vs original FastNeuralAR (≈739.9→81.7) but 11.83× champion | show as remediation evidence |

## 12. Promotion decision

**No model promotion.** No candidate is promoted to champion. No production forecast replacement. The governed champion **ETS Explicit** remains in force, unchanged.

## 13. Governance decision

- Champion unchanged (ETS Explicit, CHAMPION_SELECTED_WITH_CONDITIONS).
- No governance decisions modified. No registry change.
- All candidates remain experimental/documented challengers under V3.2 scope.
- Decision is evidence-based on the governed V3.2D metrics; no new computation was performed in V3.2E.

## 14. Dashboard handoff recommendation for V3.2F

For the future (separately authorized) **V3.2F — Candidate Results Shiny Integration**, expose READ-ONLY summaries only (NOT raw per-window data, NOT future forecasts). Proposed summaries are defined in `v3_2f_shiny_handoff_contract.csv`. None are copied to `data/processed` in this stage; the contract only proposes names and columns for a later, separately-authorized preparation step. Recommended placement: a clearly-labeled "Model Lab / Candidate evaluation (experimental, non-governed)" view, distinct from the governed champion/forecast pages.

## 15. Final recommendation

Close V3.2 model-improvement with no further optimization at this time. The champion (ETS Explicit) is decisively superior; the remediated/new candidates are documented for future reference. Proceed — only upon Oscar's authorization — to **V3.2F** to surface the candidate-evaluation summaries in Shiny as an experimental, read-only view.

## 16. Risks / caveats

- Candidate metrics are governed and complete but reflect a 12-window walk-forward backtest; they are evaluation evidence, not production guarantees.
- FNAR-V2's large improvement over the registered FastNeuralAR is real but must not be misread as competitiveness — it is still 11.83× the champion.
- If V3.2F surfaces these numbers, they must be clearly labeled "experimental / non-governed / not the production champion" to avoid implying any promotion.
- XGB-IMP-v2 is the slowest candidate (22.3 min); if ever operationalized it would dominate the daily-refresh budget.

## 17. Explicit confirmation — V3.2E does not change production artifacts

V3.2E is analysis/decision/documentation only. It does NOT:
- re-train, run models, or re-execute backtests;
- generate future forecasts;
- modify `data/processed`;
- change production forecasts, intervals, champion, or governance decisions;
- touch Shiny;
- touch V1 or V2;
- start V3.3 or V4.

All new outputs are written exclusively under `outputs/v3_2e_candidate_decision_package/`.
