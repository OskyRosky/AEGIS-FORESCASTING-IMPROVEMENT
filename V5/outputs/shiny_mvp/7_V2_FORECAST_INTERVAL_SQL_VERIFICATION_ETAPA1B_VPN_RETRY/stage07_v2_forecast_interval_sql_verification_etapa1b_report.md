# Stage 07 - V2 Forecast Interval - SQL Verification (Etapa 1B - VPN Retry)

**Status:** `UPSTREAM_INTERVALS_NOT_AVAILABLE_REQUIRES_GENERATION_METHOD`
**Scope:** Read-only. No code, data, CSV, Shiny, or SQL source modified. V2 only.
**Date:** 2026-06-24

## 1. Objective
Retry the upstream SQL verification (after Oscar reconnected the Microsoft VPN) to
determine whether `[TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]`
contains `ValueType` values other than `Forecast-Mean` for `Scenario = 'Enterprise'`.

## 2. Connection result
- **VPN / network:** `Test-NetConnection ...:1433` -> `TcpTestSucceeded = True` (RemoteAddress 20.51.9.131).
- **Driver:** ODBC Driver 18 for SQL Server present.
- **pyodbc:** 5.3.0.
- **Auth:** Microsoft Entra ID `ActiveDirectoryInteractive` -> `CONNECTED_OK`.
- All 5 read-only SELECT queries executed successfully against the live table.

## 3. Results (live, definitive)

### Query 1 - ValueType counts (Enterprise)
| ValueType | n |
|---|---|
| Forecast-Mean | 5,094,743 |

**Only `Forecast-Mean` exists.** No `Forecast-Lower`, `Forecast-Upper`, `P10`, `P90`, or quantile rows.

### Query 2 - Coverage by ValueType (Enterprise, full table)
| ValueType | date_count | model_count | key_count | min_date | max_date | row_count |
|---|---|---|---|---|---|---|
| Forecast-Mean | 4,859 | 143 | 52 | 2017-01-05 | 2030-04-25 | 5,094,743 |

### Query 3 - Sample non-mean rows
**0 rows returned.** (Table columns observed: `DateTime, Key, Value, ModelVersion, ForecastVersion, Fleet, Workload, Resource, Unit, Type, Scenario, ValueType`.)

### Query 4 - Resource x ValueType
| Resource | ValueType | row_count |
|---|---|---|
| HDD | Forecast-Mean | 5,094,743 |

### Query 5 - Latest ForecastVersion by ValueType (Enterprise)
| ValueType | row_count | key_count | model_count | min_date | max_date |
|---|---|---|---|---|---|
| Forecast-Mean | 150,032 | 45 | 17 | 2019-07-01 | 2030-04-25 |

The latest-version grain (45 keys / 17 models) matches `forecasts.csv` (45 keys / 16-17 models).

## 4. Interpretation
The upstream production source contains **point forecasts only** (`Forecast-Mean`).
Prediction intervals do **not** exist at the source for Enterprise. The earlier
double `Forecast-Mean` filter (SQL + transform) is therefore **not** discarding
hidden bounds - there are none to discard. This resolves the Etapa 0/1 `UNKNOWN`:
intervals must be **generated**, not extracted (Branch 2B).

## 5. Branch decision
- **2A (extract upstream intervals): RULED OUT.**
- **2B (generate/calibrate intervals): CONFIRMED as the required path.**

## 6. Notes for Branch 2B
- Deterministic models (`FixedGrowth*`) have no honest statistical interval - decide
  to omit their bands or use an explicitly-labeled empirical residual band.
- Stochastic-capable models (ARIMA, ExponentialSmoothing) can use model-native or
  empirical residual-quantile bands calibrated on backtest errors.
- New contract columns must be **additive and NA-safe**.
- Use the term **"intervalos de prediccion"** (not "intervalos de confianza").

## 7. Files in this folder
- `stage07_v2_forecast_interval_sql_verification_etapa1b_report.md` (this file)
- `stage07_v2_forecast_interval_sql_verification_etapa1b_validation.csv`
- `stage07_v2_forecast_interval_sql_value_type_counts.csv`
- `stage07_v2_forecast_interval_sql_coverage_by_valuetype.csv`
- `stage07_v2_forecast_interval_sql_sample_non_mean_rows.csv` (headers only - 0 rows)
- `stage07_v2_forecast_interval_sql_resource_by_valuetype.csv`
- `stage07_v2_forecast_interval_sql_latest_forecast_version_by_valuetype.csv`
- `stage07_v2_forecast_interval_sql_next_steps.csv`
