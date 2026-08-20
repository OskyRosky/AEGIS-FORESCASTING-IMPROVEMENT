# V6.0F R8-FIX-2 - Backtest Artifact v2 Contract Closure

**Status token:** `V6_0F_R8_FIX2_BACKTEST_ARTIFACT_V2_CONTRACT_COMPLETED`

**Nature:** documentation and contract only. No model execution, Tesseract
extraction, SQL write, Shiny change, Docker action, or Azure action.

## 1. What was created

| Artifact | Purpose |
|---|---|
| `backtest_v2_artifact_contract.csv` | Defines the 25-column v2 row schema, sources, semantics, and validation rules |
| `backtest_v2_scope_matrix.csv` | Defines six eligible HDD combinations and records two SSD-Phoenix exclusions |
| `backtest_v2_model_contract.csv` | Freezes the 15 authorized Viewer models and four family mappings |
| `backtest_v2_generation_plan.md` | Separates existing data, safe backfill, missing model output, prohibited fabrication, and execution gates |
| `backtest_v2_validation_plan.csv` | Defines 25 blocking checks for the future generated artifact |
| `r8fix2_open_decisions.csv` | Records eight decisions requiring approval before execution or assembly |
| `r8fix2_closure_summary.md` | Closes the documentation stage and records the next gate |

The durable recovery record is maintained separately at
`V6/outputs/V6_0F_WORK_RECOVERY_AND_STATUS.md`.

## 2. Contract outcome

The future `forecast_viewer_model_outputs_v2.csv` must:

- Preserve the legacy 21 columns.
- Add `metric`, `scenario`, `granularity`, and `extraction_run_id`.
- Cover only authorized HDD combinations with governed actuals.
- Preserve Horizon and all 15 AEGIS models.
- Support History Window filtering through real dates and rolling origins.
- Pair every model forecast with a governed actual and extraction lineage.
- Exclude SSD-Phoenix because it has no actuals.

The verified 204,300 legacy rows may be metadata-backfilled without rerunning
their models. The other 557 HDD key-combinations require authorized model
execution.

## 3. What remains open

Eight decisions remain open:

1. All six HDD combinations versus a Boon-first subset.
2. One 15-model run versus phased model groups.
3. Neural model timing.
4. Honest handling of Basilisk's shorter history.
5. Top-up handling for the six missing Enterprise/Region keys.
6. Rolling-origin cadence.
7. Champion recomputation scope.
8. Evidence-based extraction lineage for legacy rows.

Recommendations are recorded in `r8fix2_open_decisions.csv`; none is treated as
approved merely because it is recommended.

## 4. Is R8-FIX-3 blocked?

**Yes.**

R8-FIX-3 remains blocked by:

- Explicit user authorization.
- Resolution of the execution-scope decisions.
- A frozen run manifest covering scope, models, cadence, input checksums, and
  Basilisk history behavior.

No model may run until those gates are closed. R8-FIX-2 completion does not
authorize R8-FIX-3.

## 5. Recommended next step

Review and approve or amend `r8fix2_open_decisions.csv`. After every
R8-FIX-3-start blocker is resolved, request explicit R8-FIX-3 authorization.
Until then, preserve the current legacy Viewer and unwired resolver unchanged.

## 6. Governance

| Invariant | Result |
|---|---|
| No Shiny modification | Respected |
| No Viewer or Forecast modification | Respected |
| No scenario resolver wiring | Respected |
| No Assistant or LLM modification | Respected |
| No model execution | Respected |
| No Tesseract extraction | Respected |
| No SQL write | Respected |
| No Docker or Azure action | Respected |
| V1 through V5 untouched | Respected |
| Not advanced to R8-FIX-3 | Respected |
