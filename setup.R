# ============================================================
# TESSERACT v2 Forecast Improvement Platform
# setup.R — Stage 0: Project Foundation
# ============================================================
# Run this script ONCE from the project root to:
#   1. Verify folder structure
#   2. Install required R packages
#   3. Generate sample data for the Shiny wireframe
#
# After running: open shiny_app/app.R and click "Run App"
# ============================================================

cat("==========================================================\n")
cat("TESSERACT v2 Forecast Improvement Platform — Stage 0\n")
cat("==========================================================\n\n")

# ── 1. Verify folders ─────────────────────────────────────────
dirs <- c(
  "data/sample", "data/raw",
  "outputs/baseline", "outputs/metrics",
  "outputs/model_lab", "outputs/governance",
  "shiny_app", "scripts", "docs/wireframes",
  "notebooks", "tests"
)
invisible(lapply(dirs, dir.create, recursive = TRUE, showWarnings = FALSE))
cat("✓ Folder structure ready\n\n")

# ── 2. Install packages ───────────────────────────────────────
cat("Checking required packages...\n")
pkgs <- c("shiny", "bslib", "DT", "plotly", "dplyr", "readr", "tidyr")
for (p in pkgs) {
  if (!requireNamespace(p, quietly = TRUE)) {
    cat(sprintf("  Installing %s...\n", p))
    install.packages(p, quiet = TRUE)
  }
  cat(sprintf("  ✓ %s\n", p))
}
cat("\n")

# ── 3. Generate sample data ───────────────────────────────────
cat("Generating sample data in data/sample/...\n")
library(dplyr)
library(readr)

set.seed(42)

ENTITIES <- c(
  "NAM-TDF", "EUR-Dedicated", "APC-Dedicated", "che-Go-Local",
  "deu-Go-Local", "MEA-Dedicated", "APJ-Dedicated", "nam-TDF",
  "APJ-Local", "APC-Local", "EUR-Gallatin", "NAM-Dedicated"
)

RUN_ID        <- "baseline_HDD_Enterprise_20260529"
ANCHOR_DATE   <- as.Date("2024-01-01")
LAST_ACTUAL   <- as.Date("2026-05-29")
FCT_END       <- as.Date("2027-12-31")

# Entity profiles (base TB, weekly growth rate)
profiles <- data.frame(
  entity_key  = ENTITIES,
  base_value  = c(5000, 3500, 2000, 800, 1200, 600, 1800, 2800, 900, 750, 450, 1100),
  growth_rate = c(0.015, 0.020, 0.018, 0.030, 0.025, 0.012, 0.022, 0.016,
                  0.019, 0.021, 0.013, 0.017),
  stringsAsFactors = FALSE
)

# ── actuals.csv ───────────────────────────────────────────────
act_dates <- seq.Date(ANCHOR_DATE, LAST_ACTUAL, by = "week")

actuals <- expand.grid(
  entity_key  = ENTITIES,
  actual_date = act_dates,
  stringsAsFactors = FALSE
) %>%
  left_join(profiles, by = "entity_key") %>%
  arrange(entity_key, actual_date) %>%
  mutate(
    week_num   = as.numeric(actual_date - ANCHOR_DATE) / 7,
    value      = base_value * (1 + growth_rate / 52)^week_num *
                   pmax(0.85, 1 + rnorm(n(), 0, 0.03)),
    resource   = "HDD",
    scenario   = "Enterprise",
    granularity = "Region",
    data_source = "SubstrateBE_M2CP_Demand_History"
  ) %>%
  select(entity_key, resource, scenario, granularity,
         actual_date, value, data_source)

write_csv(actuals, "data/sample/actuals.csv")
cat("  ✓ actuals.csv\n")

# ── forecasts.csv (baseline only — TESSERACT current) ─────────
fct_dates <- seq.Date(LAST_ACTUAL + 7, FCT_END, by = "week")

# Compute last actual value per entity for perturbation anchor
last_actuals <- actuals %>%
  group_by(entity_key) %>%
  filter(actual_date == max(actual_date)) %>%
  select(entity_key, last_value = value)

forecasts <- expand.grid(
  entity_key    = ENTITIES,
  forecast_date = fct_dates,
  stringsAsFactors = FALSE
) %>%
  left_join(last_actuals, by = "entity_key") %>%
  mutate(
    run_id           = RUN_ID,
    resource         = "HDD",
    scenario         = "Enterprise",
    granularity      = "Region",
    model_name       = "FixedGrowth1.5%",
    model_group      = "baseline",
    forecast_version = LAST_ACTUAL,
    value_type       = "Forecast-Mean",
    weeks_ahead      = as.numeric(forecast_date - LAST_ACTUAL) / 7,
    value            = last_value * (1 + 0.015 / 52)^weeks_ahead
  ) %>%
  select(run_id, entity_key, resource, scenario, granularity,
         forecast_date, value, model_name, model_group,
         forecast_version, value_type)

write_csv(forecasts, "data/sample/forecasts.csv")
cat("  ✓ forecasts.csv  (baseline only — candidates arrive in Stage 5)\n")

# ── run_metadata.csv ──────────────────────────────────────────
run_meta <- data.frame(
  run_id             = RUN_ID,
  run_timestamp      = as.POSIXct("2026-05-29 08:00:00"),
  resource           = "HDD",
  scenario           = "Enterprise",
  granularity        = "Region",
  forecast_version   = LAST_ACTUAL,
  entities_evaluated = length(ENTITIES),
  horizon_days       = 1460L,
  step_size          = 30L,
  run_type           = "baseline",
  notes              = "Stage 3: TESSERACT v2 baseline replication"
)
write_csv(run_meta, "data/sample/run_metadata.csv")
cat("  ✓ run_metadata.csv\n")

# ── metrics.csv (empty — Stage 4 populates this) ─────────────
metrics_empty <- data.frame(
  run_id = character(), entity_key = character(),
  model_name = character(), model_group = character(),
  horizon_bucket = character(),
  mape = double(), wmape = double(), smape = double(),
  mae = double(), rmse = double(), mase = double(),
  mad = double(), mpe = double(), bias_pct = double(),
  slope_err = double(), drift_score = double(),
  stability_score = double(), fva = double(), n_obs = integer()
)
write_csv(metrics_empty, "data/sample/metrics.csv")
cat("  ✓ metrics.csv     (empty — populated in Stage 4)\n")

# ── rankings.csv (empty — Stage 4 populates this) ────────────
rankings_empty <- data.frame(
  run_id = character(), entity_key = character(),
  model_name = character(), model_group = character(),
  horizon_bucket = character(),
  composite_score = double(),
  wmape_rank = integer(), bias_rank = integer(),
  slope_rank = integer(), stability_rank = integer(),
  mase_rank = integer(), overall_rank = integer(),
  is_winner = logical()
)
write_csv(rankings_empty, "data/sample/rankings.csv")
cat("  ✓ rankings.csv    (empty — populated in Stage 4)\n")

# ── recommendations.csv (sample — for wireframe) ─────────────
recommendations <- data.frame(
  run_id = RUN_ID,
  entity_key = ENTITIES,
  current_model = c(
    "ExponentialSmoothing", "FixedGrowth2%", "ExponentialSmoothing",
    "FixedGrowth1.5%",      "ARIMA(0,2,2)", "Theta",
    "ETS(A,A,N)",           "FixedGrowth3%", "FixedGrowth2%",
    "ARIMA(0,2,2)",         "FixedGrowth1.5%", "ExponentialSmoothing"
  ),
  recommended_model = c(
    "AutoARIMA", "AutoARIMA", "LightGBM",
    "AutoARIMA", "Theta",     "Theta",
    "ETS(A,A,N)", "FixedGrowth3%", "AutoARIMA",
    "Theta",     "AutoARIMA", "LightGBM"
  ),
  recommendation = c(
    "Replace", "Replace", "Test",
    "Replace", "Test",    "Keep",
    "Keep",    "Review",  "Test",
    "Test",    "Replace", "Test"
  ),
  confidence_level = c(
    "High",   "High",   "Medium",
    "High",   "Medium", "High",
    "High",   "Low",    "Medium",
    "Medium", "High",   "Medium"
  ),
  wmape_improvement_pct = c(
    -10.3, -8.7, -8.2,
    -6.7,  -6.1,  0.2,
     0.4,   1.4,  -5.5,
    -4.8,  -7.1,  -5.9
  ),
  primary_reason = c(
    "AutoARIMA captures trend change",     "AutoARIMA wins on wMAPE",
    "LightGBM handles nonlinear growth",   "AutoARIMA wins consistently",
    "Theta wins on medium horizon",        "Current model competitive",
    "Current model competitive",           "Mixed horizon signals",
    "AutoARIMA moderate improvement",      "Theta wins short horizon",
    "AutoARIMA wins clearly",              "LightGBM wins with lag features"
  ),
  stringsAsFactors = FALSE
)
write_csv(recommendations, "data/sample/recommendations.csv")
cat("  ✓ recommendations.csv (sample data — real values arrive in Stage 4+5)\n\n")

# ── Done ──────────────────────────────────────────────────────
cat("==========================================================\n")
cat("✓ Stage 0 complete.\n\n")
cat("Next steps:\n")
cat("  1. Open shiny_app/app.R in RStudio\n")
cat("  2. Click 'Run App'\n")
cat("  3. Platform opens in browser at localhost\n\n")
cat("Stage 1 (wireframe) is already done — see docs/wireframes/\n")
cat("Stage 2 (data contract) is defined — see data/sample/*.csv\n")
cat("Stage 3 (baseline replication) starts with SSMS queries\n")
cat("==========================================================\n")
