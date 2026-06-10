# TESSERACT v2 | helpers.R | shared UI helpers
kpi_card <- function(label, value, subtitle = "", color = "primary") {
  div(
    class = "card h-100 border-0 shadow-sm",
    div(
      class = "card-body py-3",
      p(class = "small text-muted mb-1 text-uppercase fw-semibold",
        style = "font-size: 10px; letter-spacing: 0.5px;",
        label),
      h3(class = paste0("mb-0 fw-semibold text-", color), value),
      p(class = "small text-muted mt-1 mb-0", subtitle)
    )
  )
}

placeholder <- function(title, description, stage_label) {
  div(
    class = "d-flex flex-column align-items-center justify-content-center",
    style = "min-height: 340px;",
    tags$i(class = "bi bi-hourglass-split text-muted", style = "font-size: 2.5rem;"),
    h5(class = "mt-3 text-muted", title),
    p(class = "text-muted small text-center", style = "max-width: 320px;", description),
    tags$span(class = "badge bg-warning text-dark mt-2", paste("Available:", stage_label))
  )
}

rec_count_card <- function(label, count, color) {
  div(
    class = paste0("card border-", color, " h-100"),
    div(
      class = "card-body p-2 text-center",
      h4(class = paste0("mb-1 fw-bold text-", color), count),
      tags$span(class = paste0("badge bg-", color), label)
    )
  )
}
