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

# ---------------------------------------------------------------------------
# Block 7.1 | Home page governed data accessors (read-only)
# These read from the 7.0E governed loader cache. They NEVER recompute and
# always fall back to safe labels so the Home page renders even if an
# artifact is missing.
# ---------------------------------------------------------------------------

# Load the long-format key_results artifact (metric_name / metric_value / ...).
home_key_results <- function() {
  df <- tryCatch(load_csv_artifact("key_results"), error = function(e) data.frame())
  if (is.data.frame(df)) df else data.frame()
}

# Load the single-row champion_summary artifact.
home_champion_summary <- function() {
  df <- tryCatch(load_csv_artifact("champion_summary"), error = function(e) data.frame())
  if (is.data.frame(df)) df else data.frame()
}

# Pull a metric_value from key_results by metric_name (returns character).
kr_value <- function(df, name, fallback = NA_character_) {
  if (!is.data.frame(df) || nrow(df) == 0 ||
      !all(c("metric_name", "metric_value") %in% names(df))) {
    return(fallback)
  }
  hit <- df$metric_value[df$metric_name == name]
  if (length(hit) == 0) return(fallback)
  v <- hit[[1]]
  if (is.null(v) || (length(v) == 1 && is.na(v))) return(fallback)
  as.character(v)
}

# Pull a single column value from the wide champion_summary row.
cs_value <- function(df, col, fallback = NA_character_) {
  if (!is.data.frame(df) || nrow(df) == 0 || !(col %in% names(df))) return(fallback)
  v <- df[[col]][[1]]
  if (is.null(v) || (length(v) == 1 && is.na(v))) return(fallback)
  as.character(v)
}

# Format a numeric-like value safely for display.
fmt_metric <- function(x, digits = 2, fallback = "\u2014") {
  n <- suppressWarnings(as.numeric(x))
  if (length(n) == 0 || is.na(n)) return(fallback)
  formatC(round(n, digits), format = "f", digits = digits)
}

# First non-missing label among candidates (used for layered fallbacks).
first_label <- function(..., fallback = "\u2014") {
  for (v in list(...)) {
    if (!is.null(v) && length(v) == 1 && !is.na(v) && nzchar(as.character(v))) {
      return(as.character(v))
    }
  }
  fallback
}
