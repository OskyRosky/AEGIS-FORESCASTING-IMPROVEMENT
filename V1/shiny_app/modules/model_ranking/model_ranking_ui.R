# TESSERACT v2 | model_ranking_ui.R | model ranking module UI
model_ranking_ui <- function(id) {
  ns <- NS(id)
  DTOutput(ns("ranking_table"))
}
