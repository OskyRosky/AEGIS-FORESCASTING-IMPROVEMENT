# AEGIS V6.0F Work Recovery and Status

**Purpose:** durable source-of-truth handoff if the active chat or agent session is lost.

**Recovery checkpoint:** 2026-08-14, before R8-FIX-2.

**Current update:** R8-FIX-2 was subsequently completed as documentation and
contract work only. R8-FIX-2B was subsequently completed as a read-only compute
budget estimate. V6.15 was subsequently completed as a strict artifact, CSV,
metric/key, dashboard-feed, and growth inventory. V6.16 was then explicitly
authorized and completed as a bounded five-case Viewer UI/UX lab. Oscar's live
review triggered a V6.16 correction: unavailable Viewer keys are now empty, and
Forecast now supports the full prepared Metric-to-Window cascade for HDD and
SSD-Phoenix forecast-only cases. R8-FIX-3, V6.17, and the full backtest run
remain blocked and unauthorized.

## 1. Current worktree status

| Item | Value |
|---|---|
| Primary worktree | `C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT` |
| Branch | `main` |
| Git state | R1 through R8-FIX-1 artifacts are present but currently uncommitted |
| Required working location | Use the primary worktree above |
| Do not use | `C:\Users\oscarau\OneDrive - Microsoft\Desktop\Forecast Generation Codebase Improvement\AEGIS-FORESCASTING-IMPROVEMENT.worktrees\v6-aegis-forecasting-status-inspection` |

The isolated inspection worktree is a clean branch based on the July repository
state. It does not contain the recovered, uncommitted V6.0F work and must not be
used to continue implementation.

### Recovered uncommitted stage artifacts

| Stage | Artifact directory | Files |
|---|---|---:|
| R1 | `V6/outputs/v6_0f_r1_tesseract_metric_inventory/` | 18 |
| R2 | `V6/outputs/v6_0f_r2_product_ui_contract/` | 9 |
| R3 | `V6/outputs/v6_0f_r3_type_taxonomy_scenario_dictionary/` | 8 |
| R4 | `V6/outputs/v6_0f_r4_multimetric_removal/` | 10 |
| R5 | `V6/outputs/v6_0f_r5_governed_extraction_contract/` | 14 |
| R5b | `V6/outputs/v6_0f_r5b_storage_performance_strategy/` | 17 |
| R6 Phase 1 | `V6/outputs/v6_0f_r6_phase1_governed_extraction/` | 10 |
| R7 | `V6/outputs/v6_0f_r7_scenario_resolver_layer/` | 12 |
| R8 original | `V6/outputs/v6_0f_r8_viewer_integration/` | 10 |
| R8-FIX-0 | `V6/outputs/v6_0f_r8fix_unified_backtest_design/` | 9 |
| R8-FIX-1 | `V6/outputs/v6_0f_r8fix1_scenario_explorer_removal/` | 4 |
| R8-FIX-2 | `V6/outputs/v6_0f_r8fix2_backtest_artifact_v2_contract/` | 7 |
| R8-FIX-2B | `V6/outputs/v6_0f_r8fix2b_backtest_compute_budget/` | 6 |
| V6.15 | `V6/outputs/v6_15_artifact_csv_inventory_growth_budget/` | 11 |
| V6.16 | `V6/outputs/v6_16_five_case_viewer_uiux_lab/` | 18 |

## 2. Stage status

| Stage | Status | Durable evidence | Next action |
|---|---|---|---|
| R1 | Completed and validated | `v6_0f_r1_tesseract_metric_inventory/` | None |
| R2 | Completed and validated | `v6_0f_r2_product_ui_contract/` | None |
| R3 | Completed and validated | `v6_0f_r3_type_taxonomy_scenario_dictionary/` | None |
| R4 | Completed and validated | `v6_0f_r4_multimetric_removal/` | None |
| R5 | Completed and validated | `v6_0f_r5_governed_extraction_contract/` | None |
| R5b | Completed and validated | `v6_0f_r5b_storage_performance_strategy/` | None |
| R6 Phase 1 | Completed and validated | `v6_0f_r6_phase1_governed_extraction/` | Do not re-extract |
| R7 | Completed and validated, intentionally unwired | `scenario_resolver.R`, DuckDB store, metadata, and R7 validation | Preserve unwired |
| R8 original | Rejected as product UX and superseded | Historical `v6_0f_r8_viewer_integration/` evidence only | Do not restore Scenario Explorer |
| R8-FIX-0 | Completed and accepted | `v6_0f_r8fix_unified_backtest_design/` | Design governs subsequent work |
| R8-FIX-1 | Completed and validated | `v6_0f_r8fix1_scenario_explorer_removal/`; 36/36 checks PASS | Current valid Viewer state |
| R8-FIX-2 | Completed after this recovery checkpoint; it was the next authorized stage and was not started when this record was first created | `v6_0f_r8fix2_backtest_artifact_v2_contract/`; status token `V6_0F_R8_FIX2_BACKTEST_ARTIFACT_V2_CONTRACT_COMPLETED` | Review open decisions; do not run R8-FIX-3 |
| R8-FIX-2B | Completed as read-only measurement and estimation | `v6_0f_r8fix2b_backtest_compute_budget/`; status token `V6_0F_R8_FIX2B_BACKTEST_COMPUTE_BUDGET_COMPLETED` | Recommended future execution budget is four hours; authorization still required |
| V6.15 | Completed as inventory, budget, and planning only | `v6_15_artifact_csv_inventory_growth_budget/`; status token `V6_15_ARTIFACT_CSV_INVENTORY_GROWTH_BUDGET_COMPLETED` | Review scope and decisions; do not start V6.16 |
| V6.16 | Completed, visually reviewed, corrected, and revalidated as a bounded Viewer/Forecast UI/UX lab | `v6_16_five_case_viewer_uiux_lab/`; status token `V6_16_FIVE_CASE_VIEWER_UIUX_LAB_FIX_COMPLETED` | Oscar visual review; do not start V6.17 or the full run without explicit authorization |

## 3. Key technical facts

- The legacy Viewer artifact is
  `V6/data/processed/forecast_viewer_model_outputs.csv`.
- It has 204,300 rows, 39 series, 15 AEGIS models, 12 rolling origins, and
  horizons 1 through 30.
- Actual-value reconciliation verifies that the legacy artifact covers only
  `HDD - EDB / Enterprise / Region`.
- Existing coverage is 39 of 596 intended HDD key-combinations, approximately
  6.5 percent.
- The unified Viewer must preserve all 15 AEGIS models and the Horizon control.
- SSD-Phoenix has no actuals. It is forecast-only and belongs on Forecast, not
  Viewer.
- `V6/shiny_app/R/scenario_resolver.R` exists as the validated R7 deliverable,
  but no Shiny source or server file wires it into the app.
- `V6/data/storage/` exists and contains `r6_phase1.duckdb` plus five UI
  metadata slices under `ui_metadata/`.
- The V6.16 pilot artifact contains 6,750 rows across five cases, three origins,
  15 models, and horizons 1 through 30.
- The V6.16 Viewer reads
  `V6/outputs/v6_16_five_case_viewer_uiux_lab/forecast_viewer_model_outputs_v2_pilot.csv`
  only. It does not wire `scenario_resolver.R`.
- The corrected V6.16 Forecast reads
  `V6/outputs/v6_16_five_case_viewer_uiux_lab/forecast_forward_outputs_v6_16_pilot.csv`
  only. The artifact has 78,142 rows: 45 HDD keys with actuals and forecasts,
  plus 300 SSD-Phoenix scenario/key combinations without actuals.
- SSD-Phoenix is available only in Forecast, including Low Volume No
  Efficiency and Low Volume With Efficiency. It remains excluded from Viewer.
- The live V6.16 review app was validated from the primary worktree at
  `http://127.0.0.1:8081`.

## 4. Current product decision

The Viewer target is one unified **Set up the backtest view**:

`Metric -> Scenario -> Granularity -> Key / Series -> Horizon -> History Window -> Models -> Analyze Backtest`

Product constraints:

- No Scenario Explorer.
- No Multi-Metric tab.
- No Forecast Version control in Viewer.
- Do not create a second setup box.
- Do not remove Horizon or any of the 15 AEGIS models.

R8-FIX-1 remains the accepted recovery baseline. V6.16 is the current bounded
Viewer state: the same single-setup product decision implemented against the
five-case pilot artifact.

## 5. Authorized R8-FIX-2 stage and next gate

**R8-FIX-2 - Backtest Artifact v2 Contract**

At the recovery checkpoint, R8-FIX-2 was the next authorized stage and had not
started. It was then completed as documentation and contract work only. The
seven outputs are in
`V6/outputs/v6_0f_r8fix2_backtest_artifact_v2_contract/`.

The following constraints were respected during R8-FIX-2. V6.16 later modified
the Viewer only under its separate, explicit authorization:

- Do not run models.
- Do not extract from Tesseract.
- Do not modify Shiny.
- Do not wire `scenario_resolver.R`.
- Do not change Viewer, Forecast, Assistant, or LLM.
- Do not write SQL.
- Do not touch Docker or Azure.
- Do not touch V1 through V5.
- Do not advance to R8-FIX-3 without explicit authorization.

The required future record artifact is
`forecast_viewer_model_outputs_v2.csv`. R8-FIX-2 defines its contract; it does
not generate it.

### Current next gate

R8-FIX-3 is blocked by the open decisions in
`r8fix2_open_decisions.csv`, a frozen run manifest, and explicit user
authorization. Do not run models or advance to R8-FIX-3 without that approval.

R8-FIX-2B estimates the all-six-HDD model workload at 117.68 minutes for the
12 non-neural models, 40.75 minutes for the three neural models, and 158.43
minutes total. The recommended operational authorization window is four hours,
with an eight-hour unattended contingency. These are estimates, not an
authorization or evidence that any R8-FIX-3 model was run.

V6.15 freezes a pre-stage inventory of 2,195 relevant files, including 1,465
CSV files and 41 present registered Shiny inputs. It verifies 15 models, not
16, and estimates 2,211,750 new rows for the missing all-six-HDD backtest scope.
The V6.15 inventory must be reviewed before any later planning or execution
stage is authorized.

V6.16 closes the corrected Viewer/Forecast UI/UX lab with the original 27
checks plus 14 Viewer-fix and 19 Forecast-fix checks passing. The Viewer still
uses only five governed backtest cases. The full run, R8-FIX-3, and V6.17
require new explicit authorization.
