# TESSERACT v2 | cards.R | reusable card components
comparison_card <- function() {
  div(
    class = "card border-0 shadow-sm",
    div(
      class = "card-body",
      div(
        class = "d-flex justify-content-between align-items-center mb-2",
        tags$small(
          class = "text-muted text-uppercase fw-semibold",
          style = "font-size: 10px; letter-spacing: .5px;",
          "Accuracy comparison - wMAPE improvement by entity"
        ),
        tags$small(
          class = "d-flex gap-3 text-muted",
          style = "font-size: 11px;",
          tags$span(HTML("&#9608;&#9608; Improvement"), style = paste0("color: ", APP_COLORS$improvement, ";")),
          tags$span(HTML("&#9608;&#9608; Decline"), style = paste0("color: ", APP_COLORS$decline, ";"))
        )
      ),
      plotlyOutput("chart_comparison", height = "250px")
    )
  )
}

recommendations_card <- function() {
  div(
    class = "card border-0 shadow-sm h-100",
    div(
      class = "card-body",
      tags$small(
        class = "text-muted text-uppercase fw-semibold d-block mb-2",
        style = "font-size: 10px; letter-spacing: .5px;",
        "Model recommendations"
      ),
      div(
        class = "row g-2 mb-3",
        div(class = "col-6", uiOutput("rec_replace")),
        div(class = "col-6", uiOutput("rec_test")),
        div(class = "col-6", uiOutput("rec_keep")),
        div(class = "col-6", uiOutput("rec_review"))
      ),
      uiOutput("best_model_box")
    )
  )
}

llm_insight_card <- function() {
  div(
    class = "card border-0 border-start border-3 border-primary bg-light mb-3",
    div(
      class = "card-body py-2",
      div(
        class = "d-flex justify-content-between align-items-center mb-1",
        tags$small(class = "fw-semibold", "AI Insight - C9 LLM Layer"),
        tags$small(class = "badge bg-warning text-dark", STAGE_LABELS$llm)
      ),
      tags$p(class = "small text-muted fst-italic mb-0", textOutput("llm_insight", inline = TRUE))
    )
  )
}

opportunities_card <- function() {
  div(
    class = "card border-0 shadow-sm",
    div(
      class = "card-body",
      tags$small(
        class = "text-muted text-uppercase fw-semibold d-block mb-2",
        style = "font-size: 10px; letter-spacing: .5px;",
        "Top improvement opportunities"
      ),
      DTOutput("tbl_opportunities")
    )
  )
}
