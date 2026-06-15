# TESSERACT v2 | forecast_chart_ui.R | forecast chart module UI
forecast_chart_ui <- function(id, height = "360px") {
  ns <- NS(id)
  plotlyOutput(ns("chart"), height = height)
}
