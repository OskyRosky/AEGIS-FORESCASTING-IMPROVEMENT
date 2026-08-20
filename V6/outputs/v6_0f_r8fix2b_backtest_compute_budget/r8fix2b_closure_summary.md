# V6.0F R8-FIX-2B - Backtest Compute Budget Closure

**Status token:** `V6_0F_R8_FIX2B_BACKTEST_COMPUTE_BUDGET_COMPLETED`

**Nature:** read-only measurement and estimation. No model execution.

## 1. Artifacts created

| Artifact | Purpose |
|---|---|
| `compute_budget_estimate.csv` | Legacy dimensions and scaled scope/model-group estimates |
| `model_family_cost_estimate.csv` | Family and per-model runtime allocations with evidence confidence |
| `budget_scenarios.csv` | 30-minute, one-hour, two-to-three-hour, overnight, and full-run budgets |
| `recommended_execution_plan.md` | Scaling method, uncertainty, gates, and recommended phased plan |
| `r8fix2b_validation.csv` | Measurement, formula, scope, and governance validation |
| `r8fix2b_closure_summary.md` | Stage closure and authorization boundary |

## 2. Measured legacy dimensions

| Measure | Result |
|---|---:|
| Series | 39 |
| Distinct origin dates | 12 |
| Series-origin units | 454 |
| Horizons | 30 |
| Models | 15 |
| Rows | 204,300 |

The artifact reconciles exactly as `454 x 15 x 30 = 204,300`.

## 3. Compute estimate

| Scope | 12 non-neural | 3 neural | Full 15 |
|---|---:|---:|---:|
| All six HDD combinations | 117.68 min | 40.75 min | 158.43 min |
| Formal Boon slice | 41.61 min | 14.41 min | 56.02 min |
| NAMPRD07 Enterprise/Forest pilot | 0.26 min | 0.09 min | 0.35 min |

These are model-only linear projections. They do not include startup,
checkpointing, validation, serialization, retry, or R8-FIX-4 assembly.

## 4. Recommended budget

- Pilot: 30 minutes for all 15 models on NAMPRD07 Enterprise/Forest.
- Phase A: up to 3 hours for all six HDD combinations and 12 non-neural models.
- Phase B: up to 1 hour for all six HDD combinations and 3 neural models.
- Recommended full authorization window: 4 hours.
- Conservative unattended contingency: 8 hours.

The formal Boon slice can fit its 12 non-neural models in a one-hour window.
The full 15-model Boon estimate is 56.02 minutes and is too tight for a
one-hour operational cap.

## 5. Limitations

- Non-neural per-model values are allocations from measured group stages, not
  isolated timings.
- Neural values are isolated historical measurements.
- Forest workload behavior may differ from the legacy Region workload.
- Linear scaling is a budget model, not a runtime guarantee.
- Improved historical LightGBM/XGBoost variants were materially slower than
  the exact Viewer models and support retaining an overnight contingency.

## 6. Authorization boundary

R8-FIX-3 has not started and remains unauthorized. Before it can start:

1. Resolve the R8-FIX-2 open decisions.
2. Freeze the run manifest and stop conditions.
3. Obtain explicit user authorization for R8-FIX-3.

## 7. Governance

| Invariant | Result |
|---|---|
| No full or partial backtest run | Respected |
| No model execution | Respected |
| No Shiny change | Respected |
| No Viewer Forecast Assistant or LLM change | Respected |
| No resolver wiring | Respected |
| No Tesseract extraction | Respected |
| No project SQL write | Respected |
| No Docker or Azure action | Respected |
| V1 through V5 untouched | Respected |
| Not advanced to R8-FIX-3 | Respected |
