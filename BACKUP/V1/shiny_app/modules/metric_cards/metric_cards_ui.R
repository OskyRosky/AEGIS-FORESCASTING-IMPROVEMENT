# TESSERACT v2 | metric_cards_ui.R | metric cards module UI
metric_cards_ui <- function(id) {
  ns <- NS(id)
  div(
    class = "row g-3 mb-3",
    div(class = "col-md-3 col-6", uiOutput(ns("entities"))),
    div(class = "col-md-3 col-6", uiOutput(ns("improved"))),
    div(class = "col-md-3 col-6", uiOutput(ns("delta"))),
    div(class = "col-md-3 col-6", uiOutput(ns("best")))
  )
}
