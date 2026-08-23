"""V6.24-P2 | Generate SELECT-only extraction templates for P3.

Keys are embedded from the actual selection so the templates cannot drift from
the plan. Nothing is executed here.
"""

from __future__ import annotations

import json
from pathlib import Path

OUT = Path(__file__).resolve().parent
rows = json.loads((OUT / "_p2_selection.json").read_text(encoding="utf-8"))["rows"]


def keys_of(metric, scenario=None):
    return sorted({r["key"] for r in rows if r["metric"] == metric
                   and (scenario is None or r["scenario"] == scenario)})


def sql_list(keys, per_line=4, indent="    "):
    q = [f"'{k}'" for k in keys]
    lines = [", ".join(q[i:i + per_line]) for i in range(0, len(q), per_line)]
    return f",\n{indent}".join(lines)


ssd = keys_of("SSD")
cpu_c, cpu_f = keys_of("CPU", "Consumed"), keys_of("CPU", "Failover")
iops_c, iops_f = keys_of("IOPS", "Consumed"), keys_of("IOPS", "Failover")

tpl = f"""/* ============================================================================
   V6.24-P2 | Extraction SQL templates for V6.24-P3
   ----------------------------------------------------------------------------
   STATUS: TEMPLATES ONLY. NOT EXECUTED IN P2.
   These are SELECT-only and filtered to the exact keys selected in
   v6_24_p2_full_140_mvp_cohort_plan.csv.

   Governance:
     - No CREATE, UPDATE, DELETE, INSERT, MERGE, ALTER or DROP anywhere.
     - Every statement is filtered to the selected keys. No unbounded scans.
     - HDD is absent by design: it is already local and must not be re-downloaded.

   Database: TesseractEarthDW
   Auth    : ActiveDirectoryIntegrated (Interactive hangs once its token expires)
   ============================================================================ */


/* ----------------------------------------------------------------------------
   TEMPLATE 1 of 3 - SSD Phoenix LVWE  ({len(ssd)} forest keys)
   Destination: V6/data/raw/v6_24_mvp_cohort/ssd/ssd_lvwe_actuals_raw.parquet

   Assumptions, verified in P1B and P2:
     - Mean_Actual is the observed series. It is stored as VARCHAR, so it is
       CAST explicitly below. P2Q004 confirmed all 17,596 values parse cleanly.
     - End_Date is the series date. 130 distinct values over 132 calendar days.
     - Count is the rolling window size, 1..7, mean 5.22. Kept for transparency.
     - Key is a forest identifier. There is no scenario axis in this source.
     - A single Forecast_Version exists: 2026-03-12.
   Expected scope: roughly 6,400 rows ({len(ssd)} keys x about 128 observations).
---------------------------------------------------------------------------- */
SELECT
    'SSD'                                AS metric,
    'Phoenix'                            AS db_type,
    'LVWE'                               AS forecast_variant,
    'Forest'                             AS granularity,
    m.[Key]                              AS series_key,
    m.Start_Date                         AS window_start,
    m.End_Date                           AS series_date,
    TRY_CAST(m.[Count]       AS INT)     AS window_obs_count,
    TRY_CAST(m.Mean_Actual   AS FLOAT)   AS actual_value,
    m.Mean_Forecast                      AS forecast_value,
    TRY_CAST(m.MAE           AS FLOAT)   AS mae,
    TRY_CAST(m.RMSE          AS FLOAT)   AS rmse,
    TRY_CAST(m.Bias          AS FLOAT)   AS bias,
    m.Bias_Pct                           AS bias_pct,
    m.MAPE                               AS mape,
    m.SMAPE                              AS smape,
    m.Accuracy                           AS accuracy,
    m.Forecast_Version                   AS forecast_version
FROM dbo.[forecast_substrateBE_ssd_phx_lvwe_metrics] AS m
WHERE m.Mean_Actual IS NOT NULL
  AND m.[Key] IN (
    {sql_list(ssd)}
  )
ORDER BY m.[Key], m.End_Date;


/* ----------------------------------------------------------------------------
   TEMPLATE 2 of 3 - SSD Phoenix LVNE  (same {len(ssd)} forest keys)
   Destination: V6/data/raw/v6_24_mvp_cohort/ssd/ssd_lvne_actuals_raw.parquet

   CRITICAL: LVNE shares an IDENTICAL Mean_Actual with LVWE. P1B012 returned
   zero differing rows, while P1B013 found 6,720 rows where Mean_Forecast
   differs. LVNE is extracted for its FORECAST VARIANT ONLY.

   Its actual_value column must NOT be loaded into actuals_normalized.parquet,
   and these keys must NOT be counted as additional observed series. Doing so
   would double-count the cohort from 50 SSD series to 100.
---------------------------------------------------------------------------- */
SELECT
    'SSD'                                AS metric,
    'Phoenix'                            AS db_type,
    'LVNE'                               AS forecast_variant,
    'Forest'                             AS granularity,
    m.[Key]                              AS series_key,
    m.Start_Date                         AS window_start,
    m.End_Date                           AS series_date,
    TRY_CAST(m.[Count]       AS INT)     AS window_obs_count,
    TRY_CAST(m.Mean_Actual   AS FLOAT)   AS actual_value_DO_NOT_LOAD_AS_ACTUALS,
    m.Mean_Forecast                      AS forecast_value,
    TRY_CAST(m.MAE           AS FLOAT)   AS mae,
    TRY_CAST(m.RMSE          AS FLOAT)   AS rmse,
    TRY_CAST(m.Bias          AS FLOAT)   AS bias,
    m.Bias_Pct                           AS bias_pct,
    m.MAPE                               AS mape,
    m.SMAPE                              AS smape,
    m.Accuracy                           AS accuracy,
    m.Forecast_Version                   AS forecast_version
FROM dbo.[forecast_substrateBE_ssd_phx_lvne_metrics] AS m
WHERE m.Mean_Actual IS NOT NULL
  AND m.[Key] IN (
    {sql_list(ssd)}
  )
ORDER BY m.[Key], m.End_Date;


/* ----------------------------------------------------------------------------
   TEMPLATE 3a of 3 - CPU actuals  ({len(cpu_c)} Consumed + {len(cpu_f)} Failover keys)
   Destination: V6/data/raw/v6_24_mvp_cohort/cpu/cpu_actuals_raw.parquet

   Assumptions, verified in P1 and P2:
     - ModelVersion = 'Actual' is the only marker of observed history. ValueType
       is useless: it reads 'Forecast-Mean' on every row of every table.
     - Key is a composite region-environment string, e.g. 'CHN-Gallatin'.
     - Scenario carries Consumed / Failover. There is NO DB Type column.
     - CAVEAT: STALE_ACTUALS_SOURCE. Latest observation is 2023-07-20.
     - There is NO forecast column in this table.
   Expected scope: roughly 8,000 rows.
---------------------------------------------------------------------------- */
SELECT
    'CPU'                                AS metric,
    'UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE' AS db_type,
    a.Scenario                           AS scenario,
    'Region'                             AS granularity,
    a.[Key]                              AS series_key,
    a.[DateTime]                         AS series_date,
    a.Value                              AS actual_value,
    a.ValueRef                           AS value_reference,
    a.ModelVersion                       AS model_version,
    a.ForecastVersion                    AS forecast_version,
    a.Fleet, a.Workload, a.Resource, a.Unit, a.[Type]
FROM dbo.[forecast_substrateBE_cpu_actual_region] AS a
WHERE a.ModelVersion = 'Actual'
  AND a.Value IS NOT NULL
  AND (
        (a.Scenario = 'Consumed' AND a.[Key] IN (
            {sql_list(cpu_c, indent="            ")}
        ))
     OR (a.Scenario = 'Failover' AND a.[Key] IN (
            {sql_list(cpu_f, indent="            ")}
        ))
  )
ORDER BY a.Scenario, a.[Key], a.[DateTime];


/* ----------------------------------------------------------------------------
   TEMPLATE 3b of 3 - IOPS actuals  ({len(iops_c)} Consumed + {len(iops_f)} Failover keys)
   Destination: V6/data/raw/v6_24_mvp_cohort/iops/iops_actuals_raw.parquet

   Same contract as CPU. IOPS has no DB Type axis by design.
   CAVEAT: STALE_ACTUALS_SOURCE. Latest observation is 2023-07-20.
   Expected scope: roughly 14,000 rows.
---------------------------------------------------------------------------- */
SELECT
    'IOPS'                               AS metric,
    'NOT_APPLICABLE'                     AS db_type,
    a.Scenario                           AS scenario,
    'Region'                             AS granularity,
    a.[Key]                              AS series_key,
    a.[DateTime]                         AS series_date,
    a.Value                              AS actual_value,
    a.ValueRef                           AS value_reference,
    a.ModelVersion                       AS model_version,
    a.ForecastVersion                    AS forecast_version,
    a.Fleet, a.Workload, a.Resource, a.Unit, a.[Type]
FROM dbo.[forecast_substrateBE_iops_actual_region] AS a
WHERE a.ModelVersion = 'Actual'
  AND a.Value IS NOT NULL
  AND (
        (a.Scenario = 'Consumed' AND a.[Key] IN (
            {sql_list(iops_c, indent="            ")}
        ))
     OR (a.Scenario = 'Failover' AND a.[Key] IN (
            {sql_list(iops_f, indent="            ")}
        ))
  )
ORDER BY a.Scenario, a.[Key], a.[DateTime];


/* ----------------------------------------------------------------------------
   HDD - NO TEMPLATE BY DESIGN

   The 50 HDD series are ALREADY_LOCAL in:
     forecast_viewer_model_outputs_v2_full.parquet
     forecast_forward_outputs_v6_17_full.parquet

   They already carry actuals, all 15 governed model backtests and forecast.
   P3 must NOT re-download HDD. P4 reads them locally and folds them into the
   same cohort_manifest so Viewer and Forecast share one unified cohort.
---------------------------------------------------------------------------- */

/* END OF TEMPLATES */
"""

(OUT / "v6_24_p2_extraction_sql_templates.sql").write_text(tpl, encoding="utf-8")
print(f"templates written | SSD={len(ssd)} CPU={len(cpu_c)}+{len(cpu_f)} "
      f"IOPS={len(iops_c)}+{len(iops_f)}")

# Validate the executable SQL only. The governance banner itself names the
# forbidden keywords, so block comments must be stripped before scanning.
import re

executable = re.sub(r"/\*.*?\*/", "", tpl, flags=re.S).upper()
banned = ["CREATE", "UPDATE", "DELETE", "INSERT", "MERGE", "ALTER", "DROP", "TRUNCATE", "EXEC"]
found = [b for b in banned if re.search(rf"\b{b}\b", executable)]
stmts = [s for s in executable.split(";") if s.strip()]
non_select = [s.strip()[:40] for s in stmts if not s.strip().startswith("SELECT")]

print(f"executable_statements={len(stmts)}")
print(f"all_start_with_SELECT={not non_select}" + (f" | offenders={non_select}" if non_select else ""))
print(f"banned_keywords_in_executable_sql={found or 'NONE'}")
