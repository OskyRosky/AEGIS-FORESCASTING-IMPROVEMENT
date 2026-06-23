# TESSERACT v2 | header.R | governed shell header helpers
app_header_title <- function() {
  tags$span(
    tags$strong("TESSERACT v2"),
    tags$span(" | Forecast Improvement Platform", class = "header-subtitle")
  )
}

run_context_badge <- function() {
  tags$div(
    class = "header-badges",
    tags$span(class = "badge rounded-pill text-bg-light", paste("Active:", APP_VERSION)),
    tags$span(class = "badge rounded-pill governance-badge", APP_STAGE_LABEL),
    tags$span(class = "badge rounded-pill text-bg-success", "Governance-approved"),
    tags$span(class = "badge rounded-pill text-bg-info", "Read-only / no recompute")
  )
}

app_header <- function() {
  tags$header(
    class = "app-header",
    tags$div(class = "app-header-title", app_header_title()),
    run_context_badge()
  )
}
