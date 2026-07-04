# Stage 07 - V2 Forecast Interval - SQL Verification (Etapa 1)

**Status:** `DB_ACCESS_NOT_AVAILABLE_MANUAL_SQL_REQUIRED`
**Scope:** Read-only verification of upstream `ValueType` values. No code, data, CSV, Shiny, or SQL source was modified. V2 only.

## 1. Objective
Verify whether the upstream table
`[TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]`
already contains `ValueType` values other than `Forecast-Mean`
(e.g. `Forecast-Lower`, `Forecast-Upper`, `P10`, `P90`, quantiles)
for `Scenario = 'Enterprise'`. This decides whether prediction intervals
already exist at the source (Branch 2A) or must be generated (Branch 2B).

## 2. Database access result
- **Server:** `tesseractearth.database.windows.net` (tcp 1433)
- **Database:** `TesseractEarthDW`
- **Driver:** `ODBC Driver 18 for SQL Server` (installed)
- **Auth configured in code:** Microsoft Entra ID `ActiveDirectoryInteractive` (browser sign-in; no passwords/secrets in code)
- **Tooling present:** python 3.14.6, pyodbc 5.3.0, az CLI
- **`az` login state:** NOT logged in (`az account show` -> "Please run az login")
- **Decision:** No non-interactive path to the DB exists from this environment.
  An interactive browser sign-in was deliberately **not** triggered, to avoid
  hanging the terminal or opening an unexpected auth prompt. Therefore the
  queries are delivered as manual SQL for Oscar to run.

## 3. What the code already tells us (static evidence)
- The ingestion query (`python/ingestion/queries.py`) selects `[ValueType]`
  and filters `WHERE ... AND ValueType = 'Forecast-Mean'`.
- The transform (`python/transform/build_data_contract.py`) applies a **second**
  filter `value_type == 'Forecast-Mean'`.
- => `Forecast-Mean` is filtered **twice**. If the table holds Lower/Upper or
  quantile rows for Enterprise, they are being silently discarded before they
  reach `forecasts.csv`. This is exactly the hypothesis Etapa 1 must confirm.

## 4. Column-name correction (important)
The Etapa 1 prompt referenced columns `[Date]` and `[EntityKey]`. Those are the
**post-rename contract names**, not the real SQL columns. The real source
columns are:
`[Key]`, `[DateTime]`, `[Value]`, `[ModelVersion]`, `[ForecastVersion]`,
`[Scenario]`, `[Resource]`, `[ValueType]`.
All manual queries in `..._manual_queries.sql` use the **real** names so they
run without error.

## 5. Queries provided (all read-only)
1. Distinct `ValueType` counts for Enterprise (the key question).
   - 1b. Same, scoped to the latest Enterprise `ForecastVersion`.
2. Coverage by `ValueType` (date/model/key counts, min/max date, row count).
3. `TOP 100` sample of non-`Forecast-Mean` rows.
4. `Resource` x `ValueType` breakdown.
5. Single key alignment check (do Mean + any bound share the same `DateTime`?).

## 6. How to complete this stage
1. Run `az login` (then the agent can pull a token and run the queries), **or**
   open `..._manual_queries.sql` in SSMS / Azure Data Studio and run it.
2. Paste Query 1 output into `..._value_type_counts.csv`, Query 2 into
   `..._coverage_by_valuetype.csv`, Query 3 samples into
   `..._sample_non_mean_rows.csv`.
3. Branch:
   - **2A** if any `ValueType` beyond `Forecast-Mean` appears -> intervals exist
     upstream; plan to stop discarding them (additive, NA-safe).
   - **2B** if only `Forecast-Mean` exists -> design a generation/calibration
     method (note: FixedGrowth models are deterministic, so no honest interval).

## 7. Files in this folder
- `stage07_v2_forecast_interval_sql_verification_etapa1_report.md` (this file)
- `stage07_v2_forecast_interval_sql_verification_etapa1_validation.csv`
- `stage07_v2_forecast_interval_sql_value_type_counts.csv`
- `stage07_v2_forecast_interval_sql_coverage_by_valuetype.csv`
- `stage07_v2_forecast_interval_sql_sample_non_mean_rows.csv`
- `stage07_v2_forecast_interval_sql_manual_queries.sql`
- `stage07_v2_forecast_interval_sql_next_steps.csv`
