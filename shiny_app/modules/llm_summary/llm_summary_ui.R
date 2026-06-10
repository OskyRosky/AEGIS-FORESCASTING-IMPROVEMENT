# TESSERACT v2 | llm_summary_ui.R | LLM summary module UI
llm_summary_ui <- function(id) {
  ns <- NS(id)
  tags$p(class = "small text-muted fst-italic mb-0", textOutput(ns("summary"), inline = TRUE))
}
