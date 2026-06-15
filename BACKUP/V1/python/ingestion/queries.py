"""SQL query constants for Stage 3 HDD Region ingestion.

ForecastVersion must be resolved dynamically. Do not use the global
MAX(ForecastVersion), because newer runs may belong to other scenarios, such as
Basilisk, and may not contain Enterprise rows.
"""


LATEST_ENTERPRISE_FORECAST_VERSION_QUERY = """
SELECT MAX([ForecastVersion])
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
AND [ValueType] = 'Forecast-Mean';
"""


HDD_REGION_FORECASTS_QUERY = """
SELECT
[DateTime],
[Key],
[Value],
[ModelVersion],
[ForecastVersion],
[Scenario],
[Resource],
[ValueType]
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [ForecastVersion] = (
SELECT MAX([ForecastVersion])
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
AND [ValueType] = 'Forecast-Mean'
)
AND [Scenario] = 'Enterprise'
AND [ModelVersion] <> 'actual'
AND [ValueType] = 'Forecast-Mean'
ORDER BY [Key], [DateTime];
"""


HDD_REGION_ACTUALS_QUERY = """
SELECT
[DateTime],
[Key],
[Value],
[ModelVersion],
[ForecastVersion],
[Scenario],
[Resource],
[ValueType]
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [ForecastVersion] = (
SELECT MAX([ForecastVersion])
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd_region]
WHERE [Scenario] = 'Enterprise'
AND [ValueType] = 'Forecast-Mean'
)
AND [Scenario] = 'Enterprise'
AND [ModelVersion] = 'actual'
AND [Value] > 0
AND [ValueType] = 'Forecast-Mean'
ORDER BY [Key], [DateTime];
"""
