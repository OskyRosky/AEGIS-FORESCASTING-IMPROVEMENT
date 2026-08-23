# TESSERACT v2 | v6_24_read_only_loader.R
# V6.24 MVP | Governed read-only loader for the P4-P7 processed artifacts.
#
# ARCHITECTURAL CONTRACT
#   Everything is cooked outside Shiny. This file only READS finished artifacts.
#   It never trains a model, never generates a forecast or backtest, never
#   computes accuracy or rankings, never derives readiness or taxonomy from
#   scratch, and never writes to disk.
#
#   Readiness, visibility, champion suppression, caveats and counts are all
#   FIELDS carried by navigation_contract / taxonomy_counts. Nothing here
#   recomputes them and nothing here hardcodes a series name.
#
# Source of truth: V6/data/processed/v6_24_mvp_cohort/

V6_24_COHORT_DIR <- "../data/processed/v6_24_mvp_cohort"

V6_24_FORECAST_TYPE  <- "GOVERNED_30_STEP_DAILY_FORECAST"
V6_24_FORECAST_STEPS <- 30L
V6_24_HORIZON_LABEL  <- "30 daily steps ahead of each series' last observed actual"
V6_24_RANKING_POLICY <- "P6C_RANKING_POLICY_V2"
V6_24_NO_SIGNAL      <- "NO_SIGNAL_ALL_ZERO_ACTUALS"
V6_24_TRAILING_ZERO  <- "TRAILING_ZERO_LATEST_ACTUAL"
V6_24_SIGNAL_PRESENT <- "SIGNAL_PRESENT"
V6_24_CHAMP_MEANING  <- "MEANINGFUL_ACCURACY_RANKING"
V6_24_CHAMP_NOT      <- "NOT_MEANINGFUL_NO_SIGNAL"

# Filter axes, in product order. Key is LAST on purpose: it is a routing /
# display value, not a globally unique canonical axis (102 distinct keys cover
# 140 series), so it can never be the entry point.
V6_24_FILTER_AXES <- c("metric", "db_type", "scenario", "segment",
                       "granularity", "key")
V6_24_FILTER_LABELS <- c(metric = "Metric", db_type = "DB Type",
                         scenario = "Scenario", segment = "Segment",
                         granularity = "Granularity", key = "Key")

# Expected shapes, asserted at load so a silent artifact swap cannot pass.
V6_24_EXPECTED <- list(
  nav_contract     = list(rows = 140L,   key_col = "series_id", unique_key = TRUE),
  tax_counts       = list(rows = 192L,   key_col = "count_row_id", unique_key = TRUE),
  forecast_outputs = list(rows = 63000L, key_col = NULL, unique_key = FALSE),
  model_rankings   = list(rows = 2100L,  key_col = NULL, unique_key = FALSE),
  accuracy_metrics = list(rows = 2100L,  key_col = NULL, unique_key = FALSE),
  signal_quality   = list(rows = 140L,   key_col = "series_id", unique_key = TRUE),
  actuals          = list(rows = NA_integer_, key_col = NULL, unique_key = FALSE),
  backtests        = list(rows = NA_integer_, key_col = NULL, unique_key = FALSE)
)

V6_24_FILES <- list(
  nav_contract     = "navigation_contract",
  tax_counts       = "taxonomy_counts",
  forecast_outputs = "forecast_outputs",
  model_rankings   = "model_rankings",
  accuracy_metrics = "accuracy_metrics",
  signal_quality   = "series_signal_quality",
  actuals          = "actuals_normalized",
  backtests        = "model_backtests_15_models"
)

V6_24_REQUIRED_COLS <- list(
  nav_contract = c("series_id", "metric", "db_type", "scenario", "segment",
                   "granularity", "key", "route_path", "valid_filter_path",
                   "parent_filter_path", "key_axis_status", "route_display_label",
                   "viewer_visible", "forecast_visible", "ranking_visible",
                   "champion_visible", "product_ready", "product_status",
                   "champion_model_name", "champion_rank_metric",
                   "champion_rank_value", "champion_validity",
                   "signal_quality_status", "caveat_badge", "caveat_message",
                   "low_confidence_backtest_window_flag", "forecast_type",
                   "forecast_steps", "forecast_start_date", "forecast_end_date",
                   "median_wape", "median_smape", "median_rmse", "median_mae",
                   "median_wape_status", "negative_forecast_count",
                   "extreme_forecast_count", "manifest_flag_used_for_readiness"),
  tax_counts = c("count_row_id", "count_scope", "filter_axis", "filter_value",
                 "operational_series_count", "viewer_visible_count",
                 "forecast_visible_count", "champion_visible_count",
                 "no_signal_count", "available_count",
                 "available_with_caveat_count", "median_wape", "median_mae"),
  forecast_outputs = c("series_id", "model_name", "forecast_date", "forecast_step",
                       "predicted_value", "negative_forecast_flag",
                       "extreme_forecast_flag", "forecast_type",
                       "latest_actual_value"),
  model_rankings = c("series_id", "model_name", "rank_within_series",
                     "is_series_champion", "primary_rank_metric",
                     "primary_rank_value", "champion_validity",
                     "ranking_policy_version"),
  accuracy_metrics = c("series_id", "model_name", "mae", "rmse", "wape", "smape",
                       "wape_status"),
  signal_quality = c("series_id", "signal_quality_status", "sum_abs_actual",
                     "latest_actual_value"),
  actuals = c("series_id", "series_date", "actual_value"),
  backtests = c("series_id", "model_name", "target_date", "actual_value",
                "predicted_value")
)

.v6_24_env <- new.env(parent = emptyenv())

.v6_24_path <- function(stem) {
  pq <- file.path(V6_24_COHORT_DIR, paste0(stem, ".parquet"))
  cs <- file.path(V6_24_COHORT_DIR, paste0(stem, ".csv"))
  if (file.exists(pq)) list(path = pq, fmt = "parquet")
  else if (file.exists(cs)) list(path = cs, fmt = "csv")
  else list(path = pq, fmt = "missing")
}

# Read-only. Parquet preferred (already a dependency of this app via
# viewer_pilot / forecast_pilot); CSV is the fallback so the module still works
# if arrow is unavailable. No package is installed here.
.v6_24_read <- function(stem) {
  loc <- .v6_24_path(stem)
  if (identical(loc$fmt, "missing")) return(NULL)
  out <- NULL
  if (identical(loc$fmt, "parquet") && requireNamespace("arrow", quietly = TRUE)) {
    out <- tryCatch(
      as.data.frame(arrow::read_parquet(loc$path)),
      error = function(e) NULL)
  }
  if (is.null(out)) {
    cs <- file.path(V6_24_COHORT_DIR, paste0(stem, ".csv"))
    if (file.exists(cs)) {
      out <- tryCatch(
        as.data.frame(readr::read_csv(cs, show_col_types = FALSE,
                                      progress = FALSE)),
        error = function(e) NULL)
      if (!is.null(out)) loc$fmt <- "csv"
    }
  }
  attr(out, "v6_24_source") <- loc$path
  attr(out, "v6_24_format") <- loc$fmt
  out
}

#' Load every V6.24 artifact once and cache it for the session.
#' Returns a list with one element per table plus `$validation` and `$ok`.
v6_24_load_all <- function(force = FALSE) {
  if (!force && !is.null(.v6_24_env$data)) return(.v6_24_env$data)

  tables <- list()
  checks <- list()
  add <- function(id, check, expected, observed, result) {
    checks[[length(checks) + 1]] <<- data.frame(
      table = id, check = check, expected = as.character(expected),
      observed = as.character(observed), result = result,
      stringsAsFactors = FALSE)
  }

  for (id in names(V6_24_FILES)) {
    stem <- V6_24_FILES[[id]]
    df <- .v6_24_read(stem)
    exp <- V6_24_EXPECTED[[id]]

    if (is.null(df)) {
      add(id, "file exists and loads", "present", "MISSING", "FAIL")
      tables[[id]] <- data.frame()
      next
    }
    add(id, "file exists and loads", "present",
        paste0(attr(df, "v6_24_format"), ": ", basename(attr(df, "v6_24_source"))),
        "PASS")

    if (!is.na(exp$rows)) {
      add(id, "row count", exp$rows, nrow(df),
          if (identical(nrow(df), as.integer(exp$rows))) "PASS" else "FAIL")
    } else {
      add(id, "row count", "any (>0)", nrow(df),
          if (nrow(df) > 0) "PASS" else "FAIL")
    }

    need <- V6_24_REQUIRED_COLS[[id]]
    miss <- setdiff(need, names(df))
    add(id, "required columns present", paste(length(need), "columns"),
        if (length(miss)) paste("MISSING:", paste(miss, collapse = ", "))
        else "all present",
        if (length(miss)) "FAIL" else "PASS")

    if (!is.null(exp$key_col) && exp$unique_key && exp$key_col %in% names(df)) {
      dups <- sum(duplicated(df[[exp$key_col]]))
      add(id, paste0("no duplicate ", exp$key_col), "0", dups,
          if (dups == 0L) "PASS" else "FAIL")
    }
    tables[[id]] <- df
  }

  nav <- tables$nav_contract
  fo  <- tables$forecast_outputs
  rk  <- tables$model_rankings

  if (nrow(nav)) {
    ft <- unique(as.character(nav$forecast_type))
    add("nav_contract", "forecast_type constant", V6_24_FORECAST_TYPE,
        paste(ft, collapse = "|"),
        if (identical(ft, V6_24_FORECAST_TYPE)) "PASS" else "FAIL")
    fs <- unique(as.integer(nav$forecast_steps))
    add("nav_contract", "forecast_steps", V6_24_FORECAST_STEPS,
        paste(fs, collapse = "|"),
        if (identical(fs, V6_24_FORECAST_STEPS)) "PASS" else "FAIL")
    mf <- unique(as.character(nav$manifest_flag_used_for_readiness))
    add("nav_contract", "stale manifest flag not used for readiness", "FALSE",
        paste(mf, collapse = "|"),
        if (identical(mf, "FALSE")) "PASS" else "FAIL")
    add("nav_contract", "no mean-based column exists", "0",
        length(grep("mean", names(nav), ignore.case = TRUE)),
        if (length(grep("mean", names(nav), ignore.case = TRUE)) == 0L)
          "PASS" else "FAIL")
  }
  if (nrow(fo)) {
    ft <- unique(as.character(fo$forecast_type))
    add("forecast_outputs", "forecast_type constant", V6_24_FORECAST_TYPE,
        paste(ft, collapse = "|"),
        if (identical(ft, V6_24_FORECAST_TYPE)) "PASS" else "FAIL")
    rng <- range(as.integer(fo$forecast_step))
    add("forecast_outputs", "forecast_step domain", "1..30",
        paste(rng, collapse = ".."),
        if (identical(rng, c(1L, 30L))) "PASS" else "FAIL")
  }
  if (nrow(rk)) {
    pv <- unique(as.character(rk$ranking_policy_version))
    add("model_rankings", "corrected ranking policy", V6_24_RANKING_POLICY,
        paste(pv, collapse = "|"),
        if (identical(pv, V6_24_RANKING_POLICY)) "PASS" else "FAIL")
    nch <- sum(as.character(rk$is_series_champion) == "TRUE")
    add("model_rankings", "one champion per series", "140", nch,
        if (identical(nch, 140L)) "PASS" else "FAIL")
  }

  validation <- do.call(rbind, checks)
  tables$validation <- validation
  tables$ok <- !any(validation$result == "FAIL")
  tables$loaded_at <- format(Sys.time(), "%Y-%m-%d %H:%M:%S")
  .v6_24_env$data <- tables
  tables
}

#' Convenience accessor for one table.
v6_24_tbl <- function(id) {
  d <- v6_24_load_all()
  if (is.null(d[[id]])) data.frame() else d[[id]]
}

#' Operational rows only: the product's selectable universe.
#' Filter options are derived from THIS, so an option can never be empty.
v6_24_operational <- function() {
  nav <- v6_24_tbl("nav_contract")
  if (!nrow(nav)) return(nav)
  nav[as.character(nav$viewer_visible) == "TRUE", , drop = FALSE]
}

#' Valid options for one axis given the choices already made.
#' Returns only values that still have at least one operational series behind
#' them, which is what makes an empty selection unreachable by construction.
v6_24_axis_options <- function(axis, chosen = list()) {
  df <- v6_24_operational()
  if (!nrow(df) || !axis %in% names(df)) return(character(0))
  for (a in names(chosen)) {
    v <- chosen[[a]]
    if (is.null(v) || !nzchar(v) || !a %in% names(df)) next
    df <- df[as.character(df[[a]]) == v, , drop = FALSE]
  }
  if (!nrow(df)) return(character(0))
  sort(unique(as.character(df[[axis]])))
}

#' Resolve a full selection to rows. A complete six-level path resolves to
#' exactly one series because the path, not the key, is what identifies it.
v6_24_resolve <- function(chosen = list()) {
  df <- v6_24_operational()
  if (!nrow(df)) return(df)
  for (a in V6_24_FILTER_AXES) {
    v <- chosen[[a]]
    if (is.null(v) || !nzchar(v)) next
    df <- df[as.character(df[[a]]) == v, , drop = FALSE]
  }
  df
}

#' One navigation row by series_id.
v6_24_nav_row <- function(series_id) {
  nav <- v6_24_tbl("nav_contract")
  if (!nrow(nav) || is.null(series_id) || !nzchar(series_id)) return(NULL)
  r <- nav[as.character(nav$series_id) == series_id, , drop = FALSE]
  if (!nrow(r)) NULL else r[1, , drop = FALSE]
}

#' Split the pipe-separated caveat_badge field into codes.
v6_24_badges <- function(badge) {
  if (is.null(badge) || !nzchar(badge)) return(character(0))
  b <- unlist(strsplit(as.character(badge), "|", fixed = TRUE))
  b[nzchar(b)]
}

# Display severity per caveat code, mirroring v6_24_p7_caveat_contract.csv.
# A caveat annotates; it never blocks and never hides data.
V6_24_CAVEAT_SEVERITY <- c(
  NONE = "info",
  NO_SIGNAL = "high",
  CHAMPION_NOT_MEANINGFUL = "high",
  LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO = "high",
  TRAILING_ZERO_LATEST_ACTUAL = "medium",
  NEGATIVE_BACKTEST_PREDICTIONS_PRESENT = "low",
  EXTREME_BACKTEST_RATIO_PRESENT = "low",
  NEGATIVE_FORECAST_PRESENT = "low",
  EXTREME_FORECAST_PRESENT = "low",
  STALE_MANIFEST_FLAG_IGNORED = "info",
  GOVERNED_30_STEP_FORECAST_ONLY = "info"
)

v6_24_caveat_severity <- function(code) {
  s <- V6_24_CAVEAT_SEVERITY[[code]]
  if (is.null(s)) "info" else s
}

#' A taxonomy_counts row for a scope / value, read verbatim. Never recomputed.
v6_24_tax_scope <- function(scope, value = NULL) {
  tx <- v6_24_tbl("tax_counts")
  if (!nrow(tx)) return(tx)
  r <- tx[as.character(tx$count_scope) == scope, , drop = FALSE]
  if (!is.null(value)) r <- r[as.character(r$filter_value) == value, , drop = FALSE]
  r
}

#' Format a median for display. A non-computable median stays explicit; it is
#' never rendered as 0, which would make a dead series look perfect.
v6_24_fmt_median <- function(x, digits = 4) {
  if (is.null(x) || length(x) == 0 || is.na(x)) return("not computable")
  formatC(as.numeric(x), format = "f", digits = digits)
}

# ---------------------------------------------------------------------
# Shared presentation helpers.
#
# These live here, not in the UI file, because BOTH ui/tabs_v6_24_mvp.R and
# server/v6_24_mvp_server.R render with them. global.R sources this file, so
# they are defined regardless of UI/server load order. They are pure tag
# builders: no data access, no computation.
# ---------------------------------------------------------------------

v24_badge <- function(code) {
  sev <- v6_24_caveat_severity(code)
  shiny::tags$span(class = paste0("v24-badge v24-badge-", sev), code)
}

v24_badges_ui <- function(badge_field) {
  codes <- v6_24_badges(badge_field)
  if (!length(codes)) codes <- "NONE"
  shiny::tags$div(class = "v24-badges", lapply(codes, v24_badge))
}

v24_kv <- function(k, v) {
  shiny::tags$li(class = "v24-kv",
                 shiny::tags$span(class = "v24-kv-k", k),
                 shiny::tags$span(class = "v24-kv-v", v))
}

v24_card <- function(title, value, sub = NULL) {
  shiny::tags$div(
    class = "v24-card",
    shiny::tags$div(class = "v24-card-title", title),
    shiny::tags$div(class = "v24-card-value", value),
    if (!is.null(sub)) shiny::tags$div(class = "v24-card-sub", sub)
  )
}
