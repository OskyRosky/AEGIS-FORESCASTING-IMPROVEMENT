# V6.15 - Artifact, CSV, Metric/Key Inventory + Growth Budget

**Status token:** `V6_15_ARTIFACT_CSV_INVENTORY_GROWTH_BUDGET_COMPLETED`

**Final status:** completed as inventory, budget, and planning only.

## 1. Artifacts created

| Artifact | Status |
|---|---|
| `v6_status_simple.csv` | Complete |
| `current_file_inventory.csv` | Complete |
| `current_file_summary.csv` | Complete |
| `csv_inventory_summary.csv` | Complete |
| `metric_scenario_key_inventory.csv` | Complete |
| `model_universe_verification.csv` | Complete |
| `growth_budget_by_scope.csv` | Complete |
| `dashboard_feeding_plan.md` | Complete |
| `implementation_budget_summary.md` | Complete |
| `v6_15_validation.csv` | Complete; 33/33 PASS |
| `v6_15_closure_summary.md` | Complete |

## 2. Exact current inventory

The current inventory is deliberately frozen immediately before V6.15 output
creation. The V6.15 directory is excluded to prevent recursive self-counting.

| Measure | Exact result |
|---|---:|
| Relevant files | 2,195 |
| Relevant CSV files | 1,465 |
| Total size | 1,882.215 MB |
| CSV size | 1,828.207 MB |
| Files under `V6/outputs/` | 2,164 |
| Files under `V6/data/processed/` | 24 |
| Files under `V6/data/storage/` | 6 |
| Resolver source files included | 1 |
| Present registered Shiny inputs | 41 |
| Present registered Shiny CSV inputs | 39 |
| Evidence-only files | 1,878 |
| Contract/spec-only files | 261 |
| Productive runtime inputs | 47 |

The V6.15 stage itself adds 11 handoff artifacts, of which eight are CSV and
three are Markdown. Therefore the comparable relevant footprint immediately
after closure is 2,206 files and 1,473 CSV files, while the frozen baseline
counts above remain the source for all inventory summaries.

## 3. Verified model universe

**The model universe is 15, not 16.**

The 15 names in the legacy Viewer artifact exactly match the 15 names in the
Backtest Artifact v2 model contract:

- Four growth baselines.
- Five statistical models.
- Three machine-learning models.
- Three lightweight-neural models displayed as Deep Learning.

No sixteenth model is authorized by current evidence.

## 4. Metric and key coverage

| Scope | Combinations | Keys or key-combinations | Current local data |
|---|---:|---:|---|
| HDD Viewer + Forecast | 6 | 596 | Phase-1 actuals and forecasts |
| SSD-Phoenix Forecast only | 2 | 300 | Phase-1 forecasts; no actuals |
| CPU Forecast only | 4 | 1,520 summed contract keys | Not extracted locally |
| IOPS Forecast only | 4 | 1,196 summed contract keys | Not extracted locally |
| Total exposed first-release combinations | 16 | — | Eight locally extracted |

The HDD legacy backtest covers only 39 key-combinations, all in
`HDD - EDB / Enterprise / Region`. Full HDD scope therefore requires 557 new
key-combinations and finishes at 596.

SSD-Phoenix has no actuals and remains excluded from Viewer backtests.

## 5. Projected growth

| Scope | Models | New rows | Estimated new CSVs | Estimated artifacts | Estimated storage |
|---|---:|---:|---:|---:|---:|
| Five-case pilot | 15 | 24,750 | 1 | 5 | 5.95 MB |
| Formal Boon/NAMPRD07 slice | 15 | 782,100 | 3 | 8 | 385.71 MB |
| All six HDD, non-neural phase | 12 | 1,769,400 | 1 | 5 | 425.10 MB |
| All six HDD, neural phase | 3 | 442,350 | 1 | 5 | 106.28 MB |
| All six HDD, complete | 15 | 2,211,750 | 3 | 8 | 1,090.77 MB |
| SSD-Phoenix Forecast reuse | N/A | 651,480 existing | 0 | 3 | 0 MB |

The complete-scope estimate is conservative: it retains both raw phase CSVs,
writes the assembled record CSV, and includes proportional DuckDB growth.

## 6. Can V6.16 start?

**No. V6.16 remains blocked pending explicit authorization.**

Before V6.16:

1. Approve the V6.15 inventory and classification.
2. Choose the next scope: five-case pilot, formal Boon slice, or all six HDD
   combinations.
3. Close the model-phase, neural timing, origin cadence, Basilisk history,
   missing-key, champion, and lineage decisions.
4. Define exact pilot keys if the five-case option is selected.

## 7. Is backtest execution still blocked?

**Yes.**

No backtest execution was started. A future execution stage additionally
requires:

- A frozen run manifest.
- Input checksums.
- Expected units and row counts.
- Time caps and stop conditions.
- Explicit user authorization to run models.

## 8. Recommended next step

Review `implementation_budget_summary.md` and
`growth_budget_by_scope.csv`. Select and authorize the next planning scope.
Do not modify Shiny or run a backtest from V6.15.

## 9. Governance

| Invariant | Result |
|---|---|
| No UI or Shiny implementation | Respected |
| Resolver remains unwired | Respected |
| No models or backtests run | Respected |
| No forecast or backtest output created | Respected |
| No Tesseract extraction | Respected |
| No Docker or Azure action | Respected |
| V1 through V5 untouched | Respected |
| Forecast, Viewer, and Assistant code untouched | Respected |
| V6.16 not started | Respected |
