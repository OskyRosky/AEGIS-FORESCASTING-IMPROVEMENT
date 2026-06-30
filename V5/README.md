# TESSERACT v2 Forecast Improvement Platform

**Goal #3 — Execution Blueprint**

> Current TESSERACT = Baseline. Proposed framework = Improvement candidate. Data decides.

---

## Quick Start

```r
# 1. Open RStudio and set working directory to project root
setwd("path/to/tesseract-forecast-improvement")

# 2. Run setup (once)
source("setup.R")

# 3. Launch the platform
shiny::runApp("shiny_app")
```

---

## Stage Progress

| Stage | Name                    | Status     | Output |
|-------|-------------------------|------------|--------|
| 0     | Project Foundation      | ✓ Complete | Folder structure + Shiny launches |
| 1     | Vision & Wireframe      | ✓ Complete | `docs/wireframes/` · Executive Landing Page |
| 2     | Data Contract           | ✓ Complete | `data/sample/*.csv` — 6 schemas defined |
| 3     | Baseline Replication    | ○ Pending  | SSMS queries ready — run against TesseractEarthDW |
| 4     | Evaluation Platform     | ○ Pending  | `outputs/metrics/` · `outputs/rankings/` |
| 5     | Model Lab               | ○ Pending  | `outputs/model_lab/` · AutoARIMA · Theta · LightGBM |
| 6     | Validation & Governance | ○ Pending  | `outputs/governance/` · composite score |
| 7     | UI/UX + LLM Insights    | ○ Pending  | Executive UX · Ollama / Claude API narratives |
| 8     | Codebase Improvement    | ○ Pending  | `docs/codebase_improvement/` · G3 deliverable |

---

## Project Structure

```
tesseract-forecast-improvement/
├── setup.R                        ← Run once: installs packages + generates sample data
├── README.md                      ← This file
│
├── data/
│   ├── sample/                    ← Data contract files (6 CSVs)
│   │   ├── forecasts.csv          ← Forecast values (baseline + candidate)
│   │   ├── actuals.csv            ← Actual demand values
│   │   ├── metrics.csv            ← Accuracy metrics by entity/model/horizon
│   │   ├── rankings.csv           ← Composite scores and rankings
│   │   ├── run_metadata.csv       ← Run context and parameters
│   │   └── recommendations.csv   ← Keep/Test/Replace/Review decisions
│   └── raw/                       ← Raw exports from TesseractEarthDW (Stage 3)
│
├── shiny_app/
│   └── app.R                      ← Main Shiny application (all 6 tabs)
│
├── scripts/
│   ├── baseline_replication.R     ← Stage 3: reproduce TESSERACT output
│   ├── evaluation_engine.R        ← Stage 4: compute all metrics
│   ├── model_lab.R                ← Stage 5: run candidate models
│   └── governance.R               ← Stage 6: composite score + recommendations
│
├── outputs/
│   ├── baseline/                  ← Stage 3 outputs
│   ├── metrics/                   ← Stage 4 outputs
│   ├── model_lab/                 ← Stage 5 outputs
│   └── governance/                ← Stage 6 outputs
│
├── docs/
│   ├── wireframes/                ← Stage 1 wireframes
│   └── codebase_improvement/      ← Stage 8 deliverable
│
├── notebooks/                     ← Exploration and analysis notebooks
└── tests/                         ← Unit tests for evaluation engine
```

---

## Data Contract

Every CSV in `data/sample/` follows a fixed schema. The critical field present in
`forecasts`, `metrics`, and `rankings`:

```
model_group: "baseline" | "candidate"
```

This field enables the Baseline vs Improvement comparison in every Shiny tab.

---

## Required R Packages

```r
# Installed automatically by setup.R
c("shiny", "bslib", "DT", "plotly", "dplyr", "readr", "tidyr")
```

---

## Stage 3 — Baseline Replication (Next Step)

Run these queries in SSMS against `TesseractEarthDW` and save results as CSV to `data/raw/`:

**forecasts_raw.csv** — current TESSERACT production forecasts
```sql
SELECT [Key] AS entity_key, [DateTime] AS forecast_date, [Value] AS value,
       [ModelVersion] AS model_name, [ForecastVersion] AS forecast_version,
       [Scenario] AS scenario, [Resource] AS resource, [ValueType] AS value_type
FROM [TesseractEarthDW].[dbo].[forecast_substrateBE_hdd]
WHERE ForecastVersion = (SELECT MAX(ForecastVersion) FROM [dbo].[forecast_substrateBE_hdd])
  AND Scenario = 'Enterprise' AND ValueType = 'Forecast-Mean'
ORDER BY entity_key, forecast_date
```

**actuals_raw.csv** — actual demand history
```sql
SELECT ([Region] + '-' + [Environment]) AS entity_key,
       CAST([datadate] AS date) AS actual_date,
       SUM(ISNULL([EnterpriseTB], 0)) AS value
FROM [TesseractEarthDW].[dbo].[SubstrateBE_M2CP_Demand_History]
WHERE [Forest] IN (
    SELECT DISTINCT [Forest] FROM [dbo].[SubstrateBE_M2CP_Demand_History]
    GROUP BY [Forest] HAVING MAX(datadate) = (SELECT MAX(datadate) FROM [dbo].[SubstrateBE_M2CP_Demand_History])
) AND datadate >= '2024-01-01'
GROUP BY [datadate], ([Region] + '-' + [Environment])
ORDER BY entity_key, actual_date
```

---

*TESSERACT v2 Forecast Improvement Platform · Goal #3 · Substrate Platform CR*
