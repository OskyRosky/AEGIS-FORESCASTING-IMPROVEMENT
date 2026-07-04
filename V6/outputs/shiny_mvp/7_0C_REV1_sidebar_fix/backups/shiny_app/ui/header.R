# TESSERACT v2 | header.R | governed navbar header helpers
app_header_title <- function() {
  tags$span(
    tags$strong("TESSERACT v2"),
    tags$span(" | Forecast Improvement Platform", class = "text-white-50 fw-normal fs-6")
  )
}

run_context_badge <- function() {
  nav_item(
    tags$div(
      class = "d-flex align-items-center gap-2 me-2",
      tags$span(class = "badge rounded-pill text-bg-light", paste("Active:", APP_VERSION)),
      tags$span(class = "badge rounded-pill governance-badge", APP_STAGE_LABEL),
      tags$span(class = "badge rounded-pill text-bg-success", "Governance-approved")
    )
  )
}
