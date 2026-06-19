# Stage 05H - Forecast Viewer Multi-Model Handoff (FULL)

**Build timestamp:** 2026-06-18 20:53:18  
**Mode:** Data-engineering consolidation of EXISTING Stage 5 outputs. No models run, no forecasts generated, no metrics recomputed, no champion change.

## 1. What was built

A single long/tidy multi-model **backtest** handoff artifact (`forecast_viewer_model_outputs`) consolidating existing baseline + challenger Stage 5 forecast outputs for every eligible multi-model series, using the schema validated in the pilot.

## 2. Why Stage 05H and not Shiny

Shiny only consumes governed artifacts. This consolidation/join of Model Lab outputs is data engineering and must happen in the Model Lab layer, not in the dashboard. Shiny does not cook data, generate forecasts, or join baseline/challenger outputs.

## 3. Source artifacts used

- outputs/model_lab/full_baseline/full_baseline_forecasts.csv (baseline backtest forecasts)
- outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv (challenger backtest forecasts + actuals)
- data/processed/actuals.csv (actuals for baseline rows)
- data/processed/entities.csv (series universe)
- outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv (origin/family/champion/risk)
- outputs/model_lab/model_lab_closure_pack/model_lab_deferred_models.csv (deferred exclusion)
- outputs/model_lab/model_lab_closure_pack/model_lab_risk_register_final.csv (risk)
- outputs/model_lab/model_lab_closure_pack/model_lab_champion_summary.csv (champion context)

## 4. Included series

- Included (eligible multi-model): **39**
- Distinct models: **13**

## 5. Excluded series and why

- Excluded: **6** (actuals-only / final-only, no multi-model backtest coverage)
| series_key | exclusion_reason | has_actuals | has_baseline_forecasts | has_challenger_forecasts |
| --- | --- | --- | --- | --- |
| AUT-Go Local | final_only_no_multimodel_backtest_coverage | True | False | False |
| CHL-Go Local | final_only_no_multimodel_backtest_coverage | True | False | False |
| DNK-Go Local | final_only_no_multimodel_backtest_coverage | True | False | False |
| EUR-Go Local | final_only_no_multimodel_backtest_coverage | True | False | False |
| IDN-Go Local | final_only_no_multimodel_backtest_coverage | True | False | False |
| MYS-Go Local | final_only_no_multimodel_backtest_coverage | True | False | False |

## 6. Models available per series

Every included series carries the full **13-model** set (7 baseline + 6 challenger). Per-series model counts:

| series_key | model_count |
| --- | --- |
| APC-Dedicated | 13 |
| APC-MSIT | 13 |
| APC-Multitenant | 13 |
| ARE-Go Local | 13 |
| AUS-Go Local | 13 |
| BRA-Go Local | 13 |
| CAN-Go Local | 13 |
| CHE-Go Local | 13 |
| DEU-Go Local | 13 |
| ESP-Go Local | 13 |

(Full table: forecast_viewer_handoff_model_coverage.csv)

## 7. Date range

- Date range: **2025-05-03 -> 2026-04-27**

## 8. Horizons available

- Full horizon range: **1-30 days**
- UI horizons [5, 10, 15, 20, 25, 30] available for all included series/models: **YES**
- 45 and 60 day horizons are **not** present in the source data and are not added.

## 9. Backtest vs production

Historical **backtest** comparison (not forward production forecast).

## 10. Prediction intervals

**Not available** in any source. lower_bound/upper_bound/interval_level = NA.

## 11. Shiny readiness

Structurally ready for a full Forecast Viewer rebind (read-only). The viewer's existing `fvp_*` logic and pilot schema apply unchanged; only the governed artifact key would point at the full file. Awaiting Oscar approval.

## 12. Limitations to show in Shiny

- Backtest window only (not forward production).
- Point forecasts only (no prediction intervals).
- Deep-learning models (NBEATS/NHITS) deferred and not included.
- 6 actuals-only series are not available in the multi-model viewer.
- Champion flag (ETS Explicit) is governed metadata, not a viewer decision.

## 13. Next Stage 07 step

After Oscar reviews coverage, rebind the Forecast Viewer to the full artifact (governed loader key swap) and validate the multi-series view.

## Output
Primary consumable: **data\processed\forecast_viewer_model_outputs.csv** (CSV (fallback, no parquet engine)); plus sample CSV + manifest CSV. Rows: **177,060**; grain duplicates dropped: **0**.
