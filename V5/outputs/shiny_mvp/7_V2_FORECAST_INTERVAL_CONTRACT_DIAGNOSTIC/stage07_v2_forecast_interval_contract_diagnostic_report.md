# Stage 07 — V2 Forecast Interval Contract Diagnostic (READ-ONLY)

> Diagnostic only. No data, model, governed artifact, or Shiny source was modified. No model was run.

## 1. General Summary
The Forecast page's forward production forecast (`data/processed/forecasts.csv`) is **point forecast only**
(`forecast_value` = mean). There are **no** prediction-interval columns anywhere in the contract.
The artifact is generated fresh by `python/transform/build_data_contract.py::_build_forecasts()`
from `data/raw/hdd_region_forecasts.csv`, which is exported from the SQL table
`[TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]`. **Both** the SQL query and the transform
explicitly filter `ValueType = 'Forecast-Mean'`. The SQL source table **has a `ValueType` discriminator
column**, so the upstream database *may* already contain `Forecast-Lower` / `Forecast-Upper` (or quantile)
rows that are being filtered out — this is the single most important thing to verify, and it cannot be
confirmed without querying the database. The repo's own backtest models
(`python/model_lab/models/*.py`) are deterministic or unimplemented placeholders and cannot natively
emit intervals; the backtest artifact `forecast_viewer_model_outputs.csv` already has
`lower_bound/upper_bound/interval_level` columns but they are hardcoded to `NA`.

## 2. Files Created
- outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC/stage07_v2_forecast_interval_contract_diagnostic_report.md
- outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC/stage07_v2_forecast_interval_contract_diagnostic_validation.csv
- outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC/stage07_v2_forecast_interval_current_contract.csv
- outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC/stage07_v2_forecast_interval_lineage_files.csv
- outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC/stage07_v2_forecast_interval_required_changes.csv
- outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC/stage07_v2_forecast_interval_recommended_contract.csv
- outputs/shiny_mvp/7_V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC/stage07_v2_forecast_interval_open_decisions.csv

## 3. Files Modified
None. This block is strictly read-only.

## 4. Current Forecast Contract
- Path: `data/processed/forecasts.csv` · 65,095 rows · 45 keys · 16 model versions · forecast_version `2026-05-01`.
- Columns: `entity_key, date, forecast_value, model_version, forecast_version, scenario, resource, value_type, source_file`.
- `value_type`: single value `Forecast-Mean` (100% of rows). `scenario`: `Enterprise` only.
- Date range (forecast): `2026-04-28 → 2030-04-25`.
- Grain / uniqueness: `entity_key × date × model_version` (de-duplicated, keep first).
- Format: **point forecast only**. One value column; no interval columns. (Not a value_type long format today.)

## 5. Interval Availability Status
**`INTERVALS_NOT_AVAILABLE`** in the Forecast source. No `forecast_lower/upper`, `lower_bound/upper_bound`,
`prediction_interval_*`, `p05/p10/p50/p90/p95`, `quantile`, or `interval_level` columns exist in
`forecasts.csv`. The backtest artifact has the column *names* but all values are `NA`.

## 6. Forecast Generation Lineage
```
SQL [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
    WHERE Scenario='Enterprise' AND ModelVersion<>'actual' AND ValueType='Forecast-Mean'
  └─ python/ingestion/queries.py (HDD_REGION_FORECASTS_QUERY)
  └─ python/ingestion/export_hdd_region.py  →  data/raw/hdd_region_forecasts.csv
       └─ python/transform/build_data_contract.py::_build_forecasts()
            (2nd filter: value_type == 'Forecast-Mean'; FORECASTS_COLUMNS has no interval cols)
          →  data/processed/forecasts.csv   (run_metadata.csv: 65,095 rows, 2026-06-10 run)
```
- Writer **located**: `python/transform/build_data_contract.py`. Generated fresh (not copied); `source_file` hardcoded to the raw filename.
- Note: production `model_version` names here (ARIMA, ExponentialSmoothing, FixedGrowth1%…) are **upstream/SQL** models, distinct from the repo's python backtest models (ARIMA_Fixed, FixedGrowth_1_5…). The Forecast page's forward forecast is produced **upstream**, not by this repo's python.

## 7. Model / Code Capability For Intervals
- `python/requirements.txt` = only `pandas, pyodbc, python-dotenv`. No `statsmodels/statsforecast/darts/torch`.
- `python/model_lab/models/fixed_growth_model.py` `predict()` → deterministic `last_value + step*increment` (no variance). ARIMA_Fixed / ETS_Current likewise deterministic. Theta / AutoARIMA / ETS Explicit = `NotImplementedError` placeholders.
- Only interval reference in code: `build_forecast_viewer_handoff_pilot.py:267-269` sets bounds to `pd.NA` ("intervals not available in any source").
- **Classification:** `NOT_SUPPORTED_BY_CURRENT_CODE` for the repo's python models; **`UNKNOWN`** for the SQL production source until `SELECT DISTINCT [ValueType]` is checked on the database (the table's `ValueType` column implies other types may exist upstream).

## 8. Recommended Future Contract
Wide, additive, NA-safe columns on `forecasts.csv` (see recommended_contract.csv):
`forecast_value, forecast_lower_80, forecast_upper_80, forecast_lower_95, forecast_upper_95,
interval_method, interval_level_available` + existing keys + optional `run_timestamp`.
Keep `value_type` for lineage. Non-negative capping is a generation-side rule, not Shiny.

## 9. Wide vs Long Format Recommendation
**Recommend Wide.** Pros: trivial for Shiny (one row per `entity_key × date`; direct columns feed a
highcharter `arearange`; no pivot; backward compatible because new columns are additive and NA-safe).
Long (`value_type = Forecast-Mean/Lower/Upper` + `interval_level`) is more normalized and mirrors the SQL
`ValueType` discriminator, but forces a pivot in Shiny, triples row count, and risks join bugs.

## 10. Files That Would Need Modification
See required_changes.csv (14 entries, A–J). Highlights:
- **A/B (high, model generation):** `build_data_contract.py` (schema + drop Forecast-Mean filter), `ingestion/queries.py` + `export_hdd_region.py` (pass through interval rows/columns).
- **C (optional):** `model_lab/build_forecast_viewer_handoff_pilot.py` NA hardcode; `model_lab/models/*.py` probabilistic predict.
- **D/E (required):** new schema/data-quality validation (numeric, lower≤mean≤upper, level set, non-negative).
- **F/G/H (low–medium, visualization):** `shiny_app/R/helpers.R` loader + `fvf_chart` arearange band, `server/server.R` Data notes, `ui/tabs.R` labels.
- **I/J:** methodology docs + stage manifests.

## 11. Governance / Statistical Decisions Required
See open_decisions.csv (D1–D10). Most important: **D1 source of truth** (verify DB `ValueType` first),
**D2 level(s)** (80/95/both), **D3 method** (model-native vs residual-bootstrap vs empirical backtest vs quantile),
**D4 symmetry**, **D5 granularity** (per key×model×horizon), **D6 calibration**, **D7 non-negative cap**,
**D8 governed vs diagnostic**, **D9 dashboard label**, **D10 missing behavior**. Defaults are recommended but
**all require Oscar's approval**; none decided silently.

## 12. Future Shiny Implementation Plan
Once the governed artifact carries bounds: loader reads interval columns → `fvf_chart` adds a shaded
`arearange` band (95 outer, optional 80 inner) **behind** the existing mean line → actual-history line and
"Forecast start" boundary unchanged → Data notes show interval level + method + source → if columns are
`NA` for a key/model, render point forecast only with a clear "No prediction interval available" note.
No recomputation in Shiny.

## 13. Risks / Warnings
- **Fake precision** if intervals are invented in Shiny — forbidden.
- **Statistical invalidity** from naive residual σ without calibration.
- **Inconsistency across model families** (deterministic FixedGrowth has no honest interval).
- **Deterministic models** can't provide native intervals; would need bootstrap/empirical bands.
- **Coverage error** (too narrow/wide) without backtest calibration.
- **Shiny cannot validate** interval correctness — must trust the governed source.
- **Contract compatibility**: keep new columns additive + NA-safe so the current Forecast page keeps working.

## 14. Confirmation No Data/Governed Artifacts Were Modified
Confirmed. Read-only inspection only.

## 15. Confirmation No Shiny Source Files Were Modified
Confirmed.

## 16. Confirmation No Model Scripts Were Modified
Confirmed.

## 17. Confirmation No Models / Forecasts Were Run
Confirmed. No execution; CSV headers/rows and source read only.

## 18. Confirmation Champion Decision Was Not Changed
Confirmed.

## 19. Validation Summary
27 checks: 24 pass, 3 warning (SQL ValueType filter — DB may hold Lower/Upper; model-capability classification UNKNOWN for SQL source pending DB check), 0 fail. See validation.csv.

## 20. Recommended Next Step
**Verify the database first.** Run (read-only) `SELECT DISTINCT [ValueType] FROM
[TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region] WHERE [Scenario]='Enterprise'`.
- If `Forecast-Lower` / `Forecast-Upper` (or quantiles) exist → cheapest, safest path:
  unfilter ingestion + transform and pivot into the wide contract (model-native, governed).
- If they do not exist → Oscar chooses an interval method (D3) and the upstream/pipeline produces a
  governed interval artifact before any Shiny change.

## 21. Total Execution Time
~7 minutes.

---

**Status:** V2_FORECAST_INTERVAL_CONTRACT_DIAGNOSTIC_COMPLETED_WITH_WARNINGS
