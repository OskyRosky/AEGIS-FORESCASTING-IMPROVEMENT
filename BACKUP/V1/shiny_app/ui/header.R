# TESSERACT v2 | header.R | navbar header helpers
app_header_title <- function() {
  tags$span(
    tags$strong("TESSERACT v2"),
    tags$span(" · Forecast Improvement Platform", class = "text-white-50 fw-normal fs-6")
  )
}

run_context_badge <- function() {
  nav_item(
    if (!is.null(run_meta)) {
      tags$small(
        class = "text-white-50 small me-3 d-none d-md-block",
        paste0(
          "ForecastVersion: ", run_meta$forecast_version[1],
          "  ·  Resource: ", run_meta$resource[1],
          "  ·  ", run_meta$entities_evaluated[1], " entities"
        )
      )
    }
  )
}
