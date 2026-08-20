# =====================================================================
# V6.0F-R7 | Scenario Resolver Layer
# ---------------------------------------------------------------------
# Translates a UI selection into the physical source defined by the
# R2 product contract, the R3 dictionaries and the R5b storage decision.
#
#   Metric -> Scenario -> Granularity -> Key -> Forecast Version -> Model/Type
#
# Contract:
#   - Dropdowns are served from small CSV metadata slices.
#   - Series come from DuckDB via lazy, read-only, parameterised queries.
#   - The R6 fact CSV files (421 MB) are NEVER read here.
#   - Key matching is always case-insensitive: HDD - Basilisk stores
#     `namprd07` while HDD - EDB stores `NAMPRD07` (risk RB1).
#   - Scenario and Model/Type are distinct dimensions and never merged.
# =====================================================================

.sr_env <- new.env(parent = emptyenv())

SR_STATUS <- c("AVAILABLE", "OUT_OF_SCOPE", "NOT_EXPOSED",
               "NOT_AVAILABLE_IN_PHASE1", "BLOCKED_O1", "UNKNOWN_SELECTION")

# --------------------------------------------------------------- paths
sr_root <- function(start = getwd()) {
  p <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in 1:6) {
    if (dir.exists(file.path(p, "data", "storage"))) return(p)
    parent <- dirname(p)
    if (identical(parent, p)) break
    p <- parent
  }
  normalizePath(start, winslash = "/", mustWork = FALSE)
}

sr_paths <- function() {
  root <- sr_root()
  list(root = root,
       duckdb = file.path(root, "data", "storage", "r6_phase1.duckdb"),
       meta = file.path(root, "data", "storage", "ui_metadata"))
}

sr_storage_ready <- function() {
  p <- sr_paths()
  file.exists(p$duckdb) && dir.exists(p$meta)
}

# ------------------------------------------------------------ metadata
.sr_meta <- function(name) {
  if (!is.null(.sr_env[[name]])) return(.sr_env[[name]])
  f <- file.path(sr_paths()$meta, paste0(name, ".csv"))
  if (!file.exists(f)) return(NULL)
  d <- utils::read.csv(f, stringsAsFactors = FALSE, check.names = FALSE,
                       colClasses = "character")
  .sr_env[[name]] <- d
  d
}

sr_reset_cache <- function() {
  rm(list = ls(.sr_env), envir = .sr_env)
  invisible(TRUE)
}

.sr_eq <- function(x, v) !is.na(x) & trimws(x) == trimws(v)

# ------------------------------------------------------------ dropdowns
get_available_metrics <- function() {
  d <- .sr_meta("available_scenarios")
  if (is.null(d)) return(character(0))
  sort(unique(d$metric))
}

get_available_scenarios <- function(metric) {
  d <- .sr_meta("available_scenarios")
  if (is.null(d) || is.null(metric) || !nzchar(metric)) return(character(0))
  sort(unique(d$scenario_ui_label[.sr_eq(d$metric, metric)]))
}

get_available_granularities <- function(metric, scenario) {
  d <- .sr_meta("available_scenarios")
  if (is.null(d)) return(character(0))
  sel <- .sr_eq(d$metric, metric) & .sr_eq(d$scenario_ui_label, scenario)
  g <- unique(d$granularity[sel])
  g[order(match(g, c("Region", "Forest", "Forest_SKU")))]
}

get_available_keys <- function(metric, scenario, granularity) {
  d <- .sr_meta("available_keys")
  if (is.null(d)) return(character(0))
  sel <- .sr_eq(d$metric, metric) & .sr_eq(d$scenario_ui_label, scenario) &
         .sr_eq(d$granularity, granularity)
  sort(unique(d$key[sel]))  # displayed exactly as stored
}

get_available_versions <- function(metric, scenario, granularity, key = NULL) {
  d <- .sr_meta("available_versions")
  empty <- list(versions = character(0), count = 0L, single_version = FALSE,
                applies = FALSE,
                note = "No forecast version dimension for this selection.")
  if (is.null(d)) return(empty)
  sel <- .sr_eq(d$metric, metric) & .sr_eq(d$scenario_ui_label, scenario) &
         .sr_eq(d$granularity, granularity)
  v <- sort(unique(d$forecast_version[sel]), decreasing = TRUE)
  if (!length(v)) return(empty)
  list(versions = v, count = length(v), single_version = length(v) == 1L,
       applies = TRUE,
       note = if (length(v) == 1L)
         "Only one forecast version exists for this selection; the control must be disabled."
       else sprintf("%d forecast versions available.", length(v)))
}

get_available_model_types <- function(metric, scenario, granularity) {
  d <- .sr_meta("available_model_types")
  empty <- list(applies = FALSE, model_types = character(0), families = character(0),
                by_family = list(),
                note = "This source has no model dimension; no selector is rendered.")
  if (is.null(d)) return(empty)
  sel <- .sr_eq(d$metric, metric) & .sr_eq(d$scenario_ui_label, scenario) &
         .sr_eq(d$granularity, granularity)
  s <- d[sel, , drop = FALSE]
  if (!nrow(s)) return(empty)
  s <- s[order(s$model_family, s$model_type), , drop = FALSE]
  list(applies = TRUE,
       model_types = unique(s$model_type),
       families = unique(s$model_family),
       by_family = split(s$model_type, s$model_family),
       note = sprintf("%d model types across %d families.",
                      length(unique(s$model_type)), length(unique(s$model_family))))
}

# ------------------------------------------------------------- resolver
.sr_registry_row <- function(metric, scenario, granularity = NULL) {
  d <- .sr_meta("scenario_registry")
  if (is.null(d)) return(NULL)
  sel <- .sr_eq(d$metric, metric) & .sr_eq(d$scenario_ui_label, scenario)
  if (!any(sel)) sel <- .sr_eq(d$metric, metric)
  if (!any(sel)) return(NULL)
  s <- d[sel, , drop = FALSE]
  if (!is.null(granularity)) {
    g <- s[.sr_eq(s$granularity, granularity), , drop = FALSE]
    if (nrow(g)) s <- g
  }
  s[1, , drop = FALSE]
}

.sr_blocked <- function(status, metric, scenario, granularity, notes) {
  list(status = status, storage_type = NA_character_, duckdb_path = NA_character_,
       table_name = NA_character_, filters = list(metric = metric, scenario = scenario,
       granularity = granularity), query_sql = NA_character_, query_params = list(),
       expected_mode = "NOT_RENDERABLE", has_actuals = FALSE, has_forecast = FALSE,
       badge = "GREY", notes = notes)
}

resolve_series_query <- function(metric, scenario, granularity, key,
                                 version = NULL, model_type = NULL,
                                 page = c("viewer", "forecast")) {
  page <- match.arg(page)
  reg <- .sr_registry_row(metric, scenario, granularity)

  if (is.null(reg))
    return(.sr_blocked("UNKNOWN_SELECTION", metric, scenario, granularity,
                       "Selection is not present in the scenario registry."))
  if (!identical(reg$status, "AVAILABLE"))
    return(.sr_blocked(reg$status, metric, scenario, granularity, reg$reason))

  has_act <- identical(tolower(reg$has_actuals), "true")
  # SSD-Phoenix is forecast-only (D3): the Viewer page still renders, from the forecast table
  tbl <- if (page == "viewer" && has_act) reg$viewer_table else reg$forecast_table
  mode <- if (page == "viewer" && has_act) "FULL" else "FORECAST_ONLY"

  where <- c("metric = ?", "scenario_ui_label = ?", "granularity = ?", "key_lower = lower(?)")
  params <- list(metric, scenario, granularity, key)
  filters <- list(metric = metric, scenario_ui_label = scenario,
                  granularity = granularity, key_lower = sprintf("lower('%s')", key))

  is_forecast_tbl <- identical(tbl, "forecast_hdd") || identical(tbl, "forecast_ssd")
  if (is_forecast_tbl && !is.null(version) && nzchar(version)) {
    where <- c(where, "CAST(forecast_version AS VARCHAR) = ?")
    params <- c(params, list(version))
    filters$forecast_version <- version
  }
  has_model_dim <- identical(tbl, "viewer_hdd") || identical(tbl, "forecast_hdd")
  if (has_model_dim && !is.null(model_type) && length(model_type)) {
    ph <- paste(rep("?", length(model_type)), collapse = ", ")
    # 'actual' is the series_type, never a model choice: keep it regardless of the filter
    where <- c(where, sprintf(
      "(trim(model_type) IN (%s)%s)", ph,
      if (page == "viewer") " OR lower(trim(series_type)) = 'actual'" else ""))
    params <- c(params, as.list(model_type))
    filters$model_type <- paste(model_type, collapse = " | ")
  }

  cols <- if (identical(tbl, "viewer_hdd"))
            "key, date, value, series_type, model_type, raw_type"
          else if (identical(tbl, "forecast_hdd"))
            "key, forecast_date, forecast_value, forecast_version, model_type, raw_type"
          else "key, forecast_date, forecast_value, forecast_version, value_type"
  ord <- if (identical(tbl, "viewer_hdd")) "date" else "forecast_date"

  sql <- sprintf("SELECT %s FROM %s WHERE %s ORDER BY %s",
                 cols, tbl, paste(where, collapse = " AND "), ord)

  notes <- character(0)
  if (page == "viewer" && !has_act)
    notes <- c(notes, "No actuals for this metric: the Viewer renders the forecast series only.")
  if (identical(tbl, "forecast_ssd"))
    notes <- c(notes, "SSD-Phoenix has no model dimension; no model selector is rendered.")
  if (grepl("Basilisk", metric, fixed = TRUE))
    notes <- c(notes, "Basilisk stores lowercase short keys; matching is case-insensitive.")

  list(status = "AVAILABLE", storage_type = "duckdb", duckdb_path = sr_paths()$duckdb,
       table_name = tbl, filters = filters, query_sql = sql, query_params = params,
       expected_mode = mode, has_actuals = has_act && page == "viewer",
       has_forecast = TRUE, badge = reg$badge,
       notes = if (length(notes)) paste(notes, collapse = " ") else "")
}

# ------------------------------------------------------------- fetching
fetch_series_preview <- function(metric, scenario, granularity, key,
                                 version = NULL, model_type = NULL,
                                 page = c("viewer", "forecast"), limit = 100L) {
  page <- match.arg(page)
  r <- resolve_series_query(metric, scenario, granularity, key, version, model_type, page)
  if (!identical(r$status, "AVAILABLE"))
    return(list(resolution = r, rows = 0L, elapsed = 0, data = NULL))
  if (!requireNamespace("DBI", quietly = TRUE) ||
      !requireNamespace("duckdb", quietly = TRUE))
    return(list(resolution = r, rows = 0L, elapsed = 0, data = NULL,
                error = "duckdb and DBI are required"))

  t0 <- Sys.time()
  con <- DBI::dbConnect(duckdb::duckdb(shared_home = FALSE),
                        dbdir = r$duckdb_path, read_only = TRUE)
  on.exit(DBI::dbDisconnect(con, shutdown = TRUE), add = TRUE)
  sql <- if (is.null(limit)) r$query_sql else paste(r$query_sql, "LIMIT", as.integer(limit))
  d <- DBI::dbGetQuery(con, sql, params = r$query_params)
  list(resolution = r, rows = nrow(d),
       elapsed = as.numeric(difftime(Sys.time(), t0, units = "secs")), data = d)
}

fetch_series_count <- function(metric, scenario, granularity, key,
                               version = NULL, model_type = NULL,
                               page = c("viewer", "forecast")) {
  page <- match.arg(page)
  r <- resolve_series_query(metric, scenario, granularity, key, version, model_type, page)
  if (!identical(r$status, "AVAILABLE")) return(list(resolution = r, rows = 0L, elapsed = 0))
  t0 <- Sys.time()
  con <- DBI::dbConnect(duckdb::duckdb(shared_home = FALSE),
                        dbdir = r$duckdb_path, read_only = TRUE)
  on.exit(DBI::dbDisconnect(con, shutdown = TRUE), add = TRUE)
  n <- DBI::dbGetQuery(con, sub("^SELECT .*? FROM", "SELECT COUNT(*) AS n FROM",
                                sub(" ORDER BY .*$", "", r$query_sql)),
                       params = r$query_params)$n
  list(resolution = r, rows = as.integer(n),
       elapsed = as.numeric(difftime(Sys.time(), t0, units = "secs")))
}
