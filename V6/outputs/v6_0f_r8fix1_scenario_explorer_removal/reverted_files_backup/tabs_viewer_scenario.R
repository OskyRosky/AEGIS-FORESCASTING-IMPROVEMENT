# =====================================================================
# V6.0F-R8 | Viewer - Tesseract scenario explorer box
# ---------------------------------------------------------------------
# Additive UI block for the existing Forecasting -> Viewer page.
# Cascade: Metric -> Scenario -> Granularity -> Key -> Forecast Version
#          -> Model / Type
# Every control is populated by R/scenario_resolver.R from the metadata
# slices; the series itself is queried lazily from DuckDB.
# =====================================================================

viewer_scenario_box <- function() {
  metrics <- tryCatch(get_available_metrics(), error = function(e) character(0))

  tags$section(
    class = "fvx-section fvx-backtest fvb fvb-setup-section",
    id = "vsx-section",

    tags$div(
      class = "fvb-setup-head",
      tags$span(class = "fvx-section-kicker", "Tesseract"),
      tags$h3(class = "fvx-section-title", "Scenario explorer"),
      uiOutput("vsx_badge", inline = TRUE)
    ),
    tags$p(
      class = "fvb-setup-lead",
      "Governed Tesseract series for the scenarios extracted in Phase 1. ",
      "Source: ", tags$code("data/storage/r6_phase1.duckdb"),
      " \u00b7 run ", tags$code("R6P1"), "."
    ),

    tags$div(
      class = "fvb-controls",
      tags$div(
        class = "fvb-field",
        tags$label(class = "fvb-field-label",
                   tags$span(class = "fvb-step-num", "1"), "Metric"),
        selectInput("vsx_metric", NULL, choices = metrics,
                    selected = if (length(metrics)) metrics[[1]] else NULL,
                    width = "100%"),
        tags$p(class = "fvb-field-hint", "Metrics with governed data in Phase 1.")
      ),
      tags$div(
        class = "fvb-field",
        tags$label(class = "fvb-field-label",
                   tags$span(class = "fvb-step-num", "2"), "Scenario"),
        selectInput("vsx_scenario", NULL, choices = NULL, width = "100%"),
        tags$p(class = "fvb-field-hint", "Business scenario as stored in Tesseract.")
      ),
      tags$div(
        class = "fvb-field",
        tags$label(class = "fvb-field-label",
                   tags$span(class = "fvb-step-num", "3"), "Granularity"),
        selectInput("vsx_granularity", NULL, choices = NULL, width = "100%"),
        tags$p(class = "fvb-field-hint", "Region or Forest, where available.")
      ),
      tags$div(
        class = "fvb-field fvb-field-series",
        tags$label(class = "fvb-field-label",
                   tags$span(class = "fvb-step-num", "4"), "Key"),
        selectizeInput("vsx_key", NULL, choices = NULL, width = "100%",
                       options = list(placeholder = "Select a key")),
        tags$p(class = "fvb-field-hint",
               "Shown exactly as stored; matching is case-insensitive.")
      ),
      tags$div(
        class = "fvb-field",
        tags$label(class = "fvb-field-label",
                   tags$span(class = "fvb-step-num", "5"), "Forecast version"),
        uiOutput("vsx_version_ui"),
        uiOutput("vsx_version_hint")
      )
    ),

    tags$div(
      class = "fvb-models",
      tags$div(
        class = "fvb-models-head",
        tags$span(class = "fvb-field-label",
                  tags$span(class = "fvb-step-num", "6"), "Model / Type"),
        uiOutput("vsx_model_count", inline = TRUE)
      ),
      uiOutput("vsx_model_ui")
    ),

    uiOutput("vsx_state"),

    tags$div(
      class = "fvb-result",
      tags$div(
        class = "fvb-result-head",
        tags$span(class = "fvb-field-label", "Series")
      ),
      tags$div(
        class = "fv-chart-wrap fvb-chart-wrap",
        highcharter::highchartOutput("vsx_chart", height = "520px")
      ),
      uiOutput("vsx_notes")
    )
  )
}
