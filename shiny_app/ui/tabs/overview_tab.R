# TESSERACT v2 | overview_tab.R | overview navigation panel
overview_tab <- function() {
  nav_panel(
    "Overview",
    icon = icon("chart-line"),
    div(
      class = "container-fluid py-3 px-4",
      div(
        class = "d-flex justify-content-between align-items-start mb-3",
        div(
          h5(class = "mb-0 fw-semibold", "Executive Overview"),
          p(class = "text-muted small mb-0", "Baseline (Current TESSERACT) vs Proposed (Improvement Candidates)")
        ),
        tags$small(class = "badge bg-success align-self-start mt-1", STAGE_LABELS$sample)
      ),
      div(
        class = "row g-3 mb-3",
        div(class = "col-md-3 col-6", uiOutput("kpi_entities")),
        div(class = "col-md-3 col-6", uiOutput("kpi_improved")),
        div(class = "col-md-3 col-6", uiOutput("kpi_delta")),
        div(class = "col-md-3 col-6", uiOutput("kpi_best"))
      ),
      div(
        class = "row g-3 mb-3",
        div(class = "col-md-7", comparison_card()),
        div(class = "col-md-5", recommendations_card())
      ),
      llm_insight_card(),
      opportunities_card()
    )
  )
}
