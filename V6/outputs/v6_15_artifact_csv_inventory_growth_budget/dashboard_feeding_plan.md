# V6.15 Dashboard Feeding Plan

## 1. Snapshot boundary

The inventory is a pre-V6.15 snapshot. It includes every existing file under:

- `V6/outputs/`
- `V6/data/processed/`
- `V6/data/storage/`
- `V6/shiny_app/R/scenario_resolver.R`

It excludes `V6/outputs/v6_15_artifact_csv_inventory_growth_budget/` itself so
the current count is stable and non-recursive.

## 2. What currently feeds Shiny

`V6/shiny_app/R/data_loader.R` is the central file registry. It defines 42
paths in the inventory boundary:

- 41 registered paths exist.
- 39 are CSV files.
- 2 are Markdown evidence files.
- Together the 41 present inputs occupy 107.055 MB.
- The single absent path is the roadmap-only
  `V6/outputs/model_lab/ttl/ttl_capacity_view.csv`.

Current registered inputs by location:

| Location | Present inputs | Role |
|---|---:|---|
| `V6/data/processed/` | 19 | Forecast, actual, Viewer, model evaluation, TTL prototype, and canonical model data |
| `V6/outputs/model_lab/` | 19 | Closure pack, tournament, challenger, audit, and methodology evidence |
| `V6/outputs/governance/` | 3 | Champion-condition and audit evidence |

The active Viewer backtest reads only:

`V6/data/processed/forecast_viewer_model_outputs.csv`

It has 204,300 rows, 39 series, 15 models, and horizons 1 through 30. The
superseded pilot file remains registered for provenance but is not read by the
active Viewer accessor.

The active forward Forecast path:

1. Prefers
   `V6/data/processed/forecasts_with_intervals_relative_60d_calibrated.csv`.
2. Falls back to `V6/data/processed/forecasts.csv`.
3. Reads observed history from `V6/data/processed/actuals.csv`.

Shiny reads these files into its governed loader cache. It does not run models
or persist reshaped output.

## 3. Runtime-ready but currently unwired inputs

`V6/data/storage/` contains:

- `r6_phase1.duckdb`
- `ui_metadata/available_keys.csv`
- `ui_metadata/available_model_types.csv`
- `ui_metadata/available_scenarios.csv`
- `ui_metadata/available_versions.csv`
- `ui_metadata/scenario_registry.csv`

The DuckDB contains Phase-1 `viewer_hdd`, `forecast_hdd`, and `forecast_ssd`
tables. The metadata files support dependent controls. These are productive
future inputs, but they do not currently feed Shiny because
`V6/shiny_app/R/scenario_resolver.R` remains intentionally unwired.

## 4. Productive upstream data

The three large R6 source CSVs contain 2,033,970 rows and 421.344 MB:

- `r6_phase1_viewer_hdd.csv`
- `r6_phase1_forecast_hdd.csv`
- `r6_phase1_forecast_ssd_phoenix.csv`

They are governed upstream sources used outside Shiny to build the compact
storage layer. They must not be loaded directly into each dashboard session.

## 5. Evidence-only files

The inventory classifies 1,878 files as evidence-only. They include:

- Validation registers.
- Closure reports.
- Runtime logs.
- Audit outputs.
- Screenshots and backups.
- Diagnostic scripts and historical reports.

Evidence-only means the file is neither a current registered Shiny input, a
runtime-ready storage input, a processed data artifact, a governed extraction
source, nor a pure contract/specification.

## 6. Contract/spec-only files

The inventory classifies 261 files as contract/spec-only. Classification uses
contract, schema, policy, plan, decision, dictionary, taxonomy, normalization,
and scope naming plus the known contract-stage directories.

These files define expected behavior or data shape. Shiny must never treat them
as facts to chart.

## 7. Future feeding model

After separately authorized implementation:

### Viewer

- R8-FIX-3-equivalent execution produces raw backtest outputs outside Shiny.
- A later assembly stage validates and writes the v2 record artifact.
- The validated backtest table is added to DuckDB outside Shiny.
- Only after that may the unified Viewer query the table through a governed
  resolver.

### Forecast

- HDD and SSD-Phoenix Phase-1 forecast rows already exist in DuckDB.
- SSD-Phoenix remains Forecast-only because it has no actuals.
- CPU and IOPS require a later governed extraction before they can feed the
  product.

## 8. Non-negotiable data-cooking rule

**Shiny never cooks data. All cooking happens outside the dashboard.**

Outside Shiny:

- Extract.
- Normalize.
- Run models.
- Calculate backtests.
- Assemble artifacts.
- Validate lineage and row grain.
- Build or update DuckDB and metadata.

Inside Shiny:

- Open governed files or read-only storage.
- Apply parameterized filters.
- Select rows for controls, charts, notes, and downloads.
- Display honest empty or blocked states.

Shiny must not train, backtest, impute, pad, synthesize, aggregate into new
governed facts, rewrite artifacts, or silently repair missing data.
