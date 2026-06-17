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

# ---------------------------------------------------------------------------
# Block 7.3 | Model Universe governed data accessors (read-only)
# Read from the 7.0E governed loader cache. These NEVER recompute, never run
# models, and never alter the champion decision. They only read existing
# artifact columns and derive simple counts for display.
# ---------------------------------------------------------------------------

# Coerce a character/logical-ish column to a clean logical vector.
# Accepts TRUE/FALSE, "True"/"False", "true"/"false", 1/0. Anything else -> NA.
.tess_as_logical <- function(x) {
  if (is.logical(x)) return(x)
  s <- trimws(tolower(as.character(x)))
  out <- rep(NA, length(s))
  out[s %in% c("true", "t", "1", "yes", "y")]  <- TRUE
  out[s %in% c("false", "f", "0", "no", "n")] <- FALSE
  out
}

# Load the final model universe artifact (one row per governed model).
universe_models <- function() {
  df <- tryCatch(load_csv_artifact("final_model_universe"),
                 error = function(e) data.frame())
  if (!is.data.frame(df)) return(data.frame())
  df
}

# Normalize the universe data frame: trim text, coerce flag columns to logical.
universe_normalized <- function(df = universe_models()) {
  if (!is.data.frame(df) || nrow(df) == 0) return(df)
  flag_cols <- c("included_in_tournament", "eligible_for_champion",
                 "selected_champion", "risk_flag")
  for (col in flag_cols) {
    if (col %in% names(df)) df[[col]] <- .tess_as_logical(df[[col]])
  }
  text_cols <- c("model_name", "model_origin", "model_family",
                 "final_status", "deferred_reason")
  for (col in text_cols) {
    if (col %in% names(df)) {
      v <- as.character(df[[col]])
      v <- trimws(v)
      v[is.na(v)] <- ""
      df[[col]] <- v
    }
  }
  df
}

# Count rows where a logical column is TRUE (NA-safe).
.tess_count_true <- function(df, col) {
  if (!is.data.frame(df) || !(col %in% names(df))) return(NA_integer_)
  v <- .tess_as_logical(df[[col]])
  sum(v %in% TRUE)
}

# Count rows where a text column equals a given value (NA-safe).
.tess_count_eq <- function(df, col, value) {
  if (!is.data.frame(df) || !(col %in% names(df))) return(NA_integer_)
  sum(trimws(as.character(df[[col]])) == value, na.rm = TRUE)
}

# Derive the governed universe counts as a named list (all read from artifact).
universe_counts <- function(df = universe_normalized()) {
  if (!is.data.frame(df) || nrow(df) == 0) {
    return(list(total = NA_integer_, baselines = NA_integer_,
                challengers = NA_integer_, in_tournament = NA_integer_,
                deferred = NA_integer_, champion_eligible = NA_integer_,
                selected_champion = NA_integer_, risk_flagged = NA_integer_))
  }
  list(
    total             = nrow(df),
    baselines         = .tess_count_eq(df, "model_origin", "baseline"),
    challengers       = .tess_count_eq(df, "model_origin", "challenger"),
    in_tournament     = .tess_count_true(df, "included_in_tournament"),
    deferred          = if ("included_in_tournament" %in% names(df))
                          sum(.tess_as_logical(df$included_in_tournament) %in% FALSE) else NA_integer_,
    champion_eligible = .tess_count_true(df, "eligible_for_champion"),
    selected_champion = .tess_count_true(df, "selected_champion"),
    risk_flagged      = .tess_count_true(df, "risk_flag")
  )
}

# Name of the selected champion (read-only), with safe fallback.
universe_champion_name <- function(df = universe_normalized()) {
  if (!is.data.frame(df) || nrow(df) == 0 ||
      !all(c("model_name", "selected_champion") %in% names(df))) {
    return(NA_character_)
  }
  hit <- df$model_name[.tess_as_logical(df$selected_champion) %in% TRUE]
  if (length(hit) == 0) return(NA_character_)
  as.character(hit[[1]])
}

# Human-friendly label for the governed model status column.
universe_status_label <- function(status) {
  s <- trimws(as.character(status))
  dplyr::case_when(
    s == "selected_champion"             ~ "Selected champion (with conditions)",
    s == "active_tournament_model"       ~ "Active tournament model",
    s == "deferred_runtime_impractical"  ~ "Deferred \u2013 runtime impractical",
    s == "deferred_dependency_blocked"   ~ "Deferred \u2013 dependency blocked",
    grepl("^deferred", s)                ~ "Deferred",
    TRUE                                  ~ ifelse(nzchar(s), s, "\u2014")
  )
}
