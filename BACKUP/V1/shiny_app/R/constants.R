# TESSERACT v2 | constants.R | app constants
DATA_PATH <- "../data/sample"

APP_COLORS <- list(
  primary = "#2E75B6",
  navbar = "#1F3864",
  current = "#CCCCCC",
  actual = "#111111",
  improvement = "#2E75B6",
  decline = "#E74C3C"
)

STAGE_LABELS <- list(
  sample = "Stage 0 · Sample data active",
  accuracy = "Stage 4: Evaluation Platform",
  models = "Stage 5: Model Lab",
  validation = "Stage 6: Validation Lab",
  governance = "Stage 6: Governance",
  llm = "Stage 7"
)

FORECAST_START_DATE <- "2026-05-29"

app_theme <- bslib::bs_theme(
  version = 5,
  primary = APP_COLORS$primary,
  bg = "#FFFFFF",
  fg = "#111111"
)
