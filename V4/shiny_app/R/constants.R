# TESSERACT v2 | constants.R | governed app constants
APP_VERSION <- "V4"
APP_STAGE <- "Stage 07"
APP_STAGE_LABEL <- "Stage 07 Shiny MVP Build"
APP_AUDIT_STATE <- "APPROVE_WITH_CONDITIONS_TO_SHINY_MVP"
APP_CHAMPION <- "ETS Explicit"
APP_CHAMPION_DECISION <- "CHAMPION_SELECTED_WITH_CONDITIONS"
APP_CHAMPION_CONFIDENCE <- "medium"
APP_POLICY <- "Read-only / no recompute"

APP_COLORS <- list(
  primary = "#2E75B6",
  navbar = "#1F3864",
  navy = "#102A43",
  ink = "#132238",
  muted = "#5D6D7E",
  panel = "#F7F9FC",
  success = "#1F7A4D",
  warning = "#B7791F",
  current = "#CCCCCC",
  actual = "#111111",
  improvement = "#2E75B6",
  decline = "#E74C3C"
)

STAGE_LABELS <- list(
  active = "Stage 07 Shiny MVP Build",
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
  fg = "#111111",
  base_font = bslib::font_google("Inter")
)
