-- =====================================================================
-- Stage 07 - V2 Forecast Interval - Etapa 1 - MANUAL SQL (READ-ONLY)
-- Run these in SSMS or Azure Data Studio against:
--   Server   : tesseractearth.database.windows.net   (tcp 1433)
--   Database : TesseractEarthDW
--   Driver   : ODBC Driver 18 for SQL Server
--   Auth     : Microsoft Entra ID (interactive)  -- no passwords in code
-- Table      : [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
--
-- NOTE: The real source columns are [Key], [DateTime], [Value],
-- [ModelVersion], [ForecastVersion], [Scenario], [Resource], [ValueType]
-- (NOT EntityKey / Date). The queries below use the REAL column names.
-- All queries are strictly SELECT (read-only). They change nothing.
-- =====================================================================

-- Query 1 - Distinct ValueType counts (the key question) ---------------
SELECT [ValueType], COUNT(*) AS n
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
GROUP BY [ValueType]
ORDER BY n DESC;

-- Query 1b - Same, but scoped to the LATEST Enterprise ForecastVersion
-- (this matches what the ingestion actually pulls) --------------------
SELECT [ValueType], COUNT(*) AS n
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
  AND [ForecastVersion] = (
      SELECT MAX([ForecastVersion])
      FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
      WHERE [Scenario] = 'Enterprise'
        AND [ValueType] = 'Forecast-Mean'
  )
GROUP BY [ValueType]
ORDER BY n DESC;

-- Query 2 - Date / key / model coverage by ValueType -------------------
SELECT
    [ValueType],
    COUNT(DISTINCT [DateTime])     AS date_count,
    COUNT(DISTINCT [ModelVersion]) AS model_count,
    COUNT(DISTINCT [Key])          AS key_count,
    MIN([DateTime])                AS min_date,
    MAX([DateTime])                AS max_date,
    COUNT(*)                       AS row_count
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
GROUP BY [ValueType]
ORDER BY [ValueType];

-- Query 3 - Sample non-mean rows (inspect what they look like) ---------
SELECT TOP 100 *
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
  AND [ValueType] <> 'Forecast-Mean'
ORDER BY [DateTime], [ValueType];

-- Query 4 - Resource x ValueType breakdown -----------------------------
SELECT
    [Resource],
    [ValueType],
    COUNT(*) AS row_count
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
GROUP BY [Resource], [ValueType]
ORDER BY [Resource], row_count DESC;

-- Query 5 - For one key+model+version, do Mean and any bound co-exist
-- on the same DateTime? (alignment check for a wide contract) ----------
SELECT TOP 200
    [Key], [DateTime], [ModelVersion], [ForecastVersion],
    [ValueType], [Value]
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
  AND [Key] = 'APC-Dedicated'      -- example key; change as needed
ORDER BY [DateTime], [ValueType];
