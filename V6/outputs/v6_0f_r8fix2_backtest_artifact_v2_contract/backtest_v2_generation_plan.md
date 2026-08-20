# R8-FIX-2 Backtest Artifact v2 Generation Plan

## Purpose and stage boundary

This document defines how a future, explicitly authorized R8-FIX-3 model run
must produce `forecast_viewer_model_outputs_v2.csv`. R8-FIX-2 does not execute
models, extract data, modify Shiny, or assemble the final artifact.

## 1. Data that already exists

### Legacy backtest

`V6/data/processed/forecast_viewer_model_outputs.csv` contains:

- 204,300 rows and 21 columns.
- 39 series.
- All 15 authorized AEGIS models.
- Four model families.
- Horizons 1 through 30.
- 12 rolling origins from 2025-05-02 through 2026-03-28.
- Target dates from 2025-05-03 through 2026-04-27.
- Historical backtest forecasts and observed actual values.

Actual-value reconciliation completed in R8-FIX-0 verifies that these rows
represent `HDD - EDB / Enterprise / Region`. The 39 legacy keys cover 39 of the
45 governed keys in that combination.

### Governed actuals and lineage

R6 Phase 1 provides governed actual series for all six HDD combinations:

| Metric | Scenario | Granularity | Keys | Approximate available history |
|---|---|---|---:|---|
| HDD - EDB | Enterprise | Region | 45 | 11 months |
| HDD - EDB | Enterprise | Forest | 152 | 11 months |
| HDD - EDB | Consumer | Region | 45 | 11 months |
| HDD - EDB | Consumer | Forest | 152 | 11 months |
| HDD - Basilisk | Basilisk | Region | 47 | 5 months |
| HDD - Basilisk | Basilisk | Forest | 155 | 5 months |

The governed extraction is recorded as `R6P1-20260812T100822`. Its Viewer data
is stored in `V6/outputs/v6_0f_r6_phase1_governed_extraction/` and represented
in `V6/data/storage/r6_phase1.duckdb`.

SSD-Phoenix has forecast rows but no actual series. It cannot support an actual
versus model backtest and is excluded from the Viewer contract.

## 2. Data that is missing

The intended HDD universe contains 596 key-combinations. Only 39 have a legacy
backtest, leaving 557 key-combinations without model results:

- Six missing `HDD - EDB / Enterprise / Region` keys.
- All 152 `HDD - EDB / Enterprise / Forest` keys.
- All 45 `HDD - EDB / Consumer / Region` keys.
- All 152 `HDD - EDB / Consumer / Forest` keys.
- All 47 `HDD - Basilisk / Basilisk / Region` keys.
- All 155 `HDD - Basilisk / Basilisk / Forest` keys.

R8-FIX-0 estimates approximately 2.21 million new forecast rows and 73,725
model fits for complete coverage under its proposed origin cadence. These are
planning estimates, not generated data.

## 3. Work that requires model execution

Every uncovered key-combination requires backtest execution for all 15 models:

- Four growth baselines.
- Five statistical models.
- Three machine-learning models.
- Three lightweight-neural models.

For each authorized combination, execution must use only governed R6 actuals,
the approved rolling-origin cadence, and horizons 1 through 30. Champion flags
must be recomputed for each eligible scope; they cannot be copied from the
legacy Enterprise/Region result.

Execution may be operationally phased into 12 non-neural models followed by
the three neural models, but `forecast_viewer_model_outputs_v2.csv` is not
complete until all 15 authorized models are present for the approved scope.

No model execution is authorized by this plan. R8-FIX-3 remains a separate
approval gate.

## 4. Work that can be backfilled without rerunning models

The 204,300 legacy rows can retain their existing model forecasts and receive:

- `metric = HDD - EDB`
- `scenario = Enterprise`
- `granularity = Region`
- `extraction_run_id` linked to the governed actual lineage

The first three labels are verified by R8-FIX-0 actual-value reconciliation,
not inferred from key names.

The extraction identifier may be assigned only after deterministic
reconciliation of each legacy actual to the governed R6 actual source.
`R6P1-20260812T100822` must not be stamped onto an unmatched row merely to
satisfy a non-null constraint. Unmatched rows must be reported and must block
artifact assembly until lineage is resolved.

Backfill must not alter any legacy forecast value, model identity, horizon,
origin, risk flag, or interval field.

## 5. History Window behavior

History Window is a Viewer query choice, not a duplicated label on every row.
The artifact supports it through `date`, `forecast_start_date`, and the
available governed date range for each combination.

- EDB may expose only windows supported by its governed history.
- Basilisk must expose its shorter available history honestly.
- No missing dates may be padded.
- No synthetic actuals or zero-filled values may be introduced to make window
  lengths appear equal.

## 6. Values that must never be faked

The following are prohibited:

- Actual observations for any metric, scenario, granularity, key, or date.
- SSD-Phoenix actuals or backtests.
- Forecast values for a model that was not executed.
- Basilisk history before its real first observation.
- Results for the six uncovered Enterprise/Region keys copied from other keys.
- Model, family, origin, champion, risk, or interval values copied across
  combinations without governed computation.
- Extraction lineage assigned without evidence.
- Missing neural-model output represented as zero, NA, or a successful run.

## 7. Required R8-FIX-3 gates

Before execution begins:

1. Resolve every decision in `r8fix2_open_decisions.csv`.
2. Obtain explicit authorization for R8-FIX-3.
3. Freeze the approved scope, model phases, origin cadence, and Basilisk
   history rule in a run manifest.
4. Record a run identifier and the governed input checksums.
5. Validate outputs against `backtest_v2_validation_plan.csv`.

R8-FIX-3 must produce raw model outputs only. Assembly into the final CSV and
DuckDB table remains R8-FIX-4.
