# =====================================================================
# AEGIS V6.0F | multi_metric_loader.R | governed multi-metric loader
# ---------------------------------------------------------------------
# GOVERNANCE CONTRACT (read-only):
#   - Reads ONLY the V6.0E artifacts under outputs/metrics_multi.
#   - Does NOT recompute any business measure, run models or query SQL.
#   - Missing artifacts NEVER stop the app: empty frames are returned and
#     the section degrades to an explicit "not available" state.
#   - Extends the existing assistant by ADDING page entries to the loaded
#     response index. The legacy pack file is never modified.
# =====================================================================

.mm_env <- new.env(parent = emptyenv())

MM_ARTIFACTS <- list(
  normalized    = "official_metrics_normalized.csv",
  rankings      = "official_metric_rankings.csv",
  filters       = "metric_filter_options.csv",
  availability  = "metric_availability_status.csv",
  computability = "metric_computability_status.csv",
  lineage       = "metric_source_lineage.csv",
  quality       = "metric_data_quality_checks.csv",
  registry      = "metric_registry_resolved.csv",
  assistant     = "assistant_metric_context.csv"
)

MM_PACK_FILE <- "metric_assistant_evidence_pack.json"

# Identity columns such as forecast_version must not be type-guessed: readr
# turns "2026-03-12" into a Date and the exact-match filters then fail.
.mm_read_chr <- function(path) {
  out <- NULL
  if (requireNamespace("readr", quietly = TRUE)) {
    out <- tryCatch(
      as.data.frame(readr::read_csv(path, col_types = readr::cols(.default = readr::col_character()),
                                    progress = FALSE), stringsAsFactors = FALSE),
      error = function(e) NULL)
  }
  if (is.null(out)) {
    out <- tryCatch(utils::read.csv(path, colClasses = "character", check.names = FALSE,
                                    stringsAsFactors = FALSE),
                    error = function(e) data.frame())
  }
  out[is.na(out)] <- ""
  out
}

# Presentation-only coercion. Never applied to identity columns.
mm_numify <- function(df, cols) {
  for (cl in intersect(cols, names(df))) {
    df[[cl]] <- suppressWarnings(as.numeric(df[[cl]]))
  }
  df
}

MM_NUMERIC_COLS <- c("row_count", "n_windows", "avg_mape", "max_mape", "avg_smape",
                     "avg_rmse", "avg_mae", "avg_bias_pct", "avg_accuracy",
                     "min_accuracy", "source_object_count", "count", "mean_actual",
                     "mean_forecast", "mae", "rmse", "bias", "bias_pct", "mape",
                     "smape", "accuracy", "local_rows", "local_versions", "local_keys",
                     "source_rows", "normalized_rows", "ranking_rows")

mm_dir <- function(root = NULL) {
  if (is.null(root)) root <- tryCatch(find_project_root(getwd()), error = function(e) getwd())
  file.path(root, "outputs", "metrics_multi")
}

# ---------------------------------------------------------------------
# Load every artifact once. Never throws.
# ---------------------------------------------------------------------
mm_load <- function() {
  if (!is.null(.mm_env$data)) return(invisible(TRUE))

  dir <- mm_dir()
  store <- list()
  status <- list()

  for (key in names(MM_ARTIFACTS)) {
    path <- file.path(dir, MM_ARTIFACTS[[key]])
    if (file.exists(path)) {
      df <- tryCatch(.mm_read_chr(path), error = function(e) data.frame())
      store[[key]] <- df
      status[[key]] <- list(available = TRUE, rows = nrow(df), path = path)
    } else {
      store[[key]] <- data.frame()
      status[[key]] <- list(available = FALSE, rows = 0L, path = path)
    }
  }

  pack_path <- file.path(dir, MM_PACK_FILE)
  pack <- NULL
  if (file.exists(pack_path) && requireNamespace("jsonlite", quietly = TRUE)) {
    pack <- tryCatch(jsonlite::fromJSON(pack_path, simplifyVector = FALSE),
                     error = function(e) NULL)
  }
  status[[MM_PACK_FILE]] <- list(available = !is.null(pack),
                                 rows = if (is.null(pack)) 0L else length(pack$responses),
                                 path = pack_path)

  .mm_env$data <- store
  .mm_env$pack <- pack
  .mm_env$status <- status
  .mm_env$dir <- dir
  invisible(TRUE)
}

mm_get <- function(key) {
  mm_load()
  out <- .mm_env$data[[key]]
  if (is.null(out) || !is.data.frame(out)) data.frame() else out
}

mm_status <- function() {
  mm_load()
  st <- .mm_env$status
  data.frame(
    artifact  = names(st),
    available = vapply(st, function(x) isTRUE(x$available), logical(1)),
    rows      = vapply(st, function(x) as.integer(x$rows), integer(1)),
    stringsAsFactors = FALSE
  )
}

mm_is_available <- function() {
  mm_load()
  nrow(mm_get("filters")) > 0 && nrow(mm_get("rankings")) > 0
}

# ---------------------------------------------------------------------
# Dependent filter helpers. Options come from the artifact only; nothing
# about a metric is hardcoded here.
# ---------------------------------------------------------------------
mm_options <- function(level, parent_value = NULL, enabled_only = TRUE) {
  f <- mm_get("filters")
  if (nrow(f) == 0) return(f)
  out <- f[f$filter_name == level, , drop = FALSE]
  if (!is.null(parent_value) && nzchar(parent_value)) {
    out <- out[out$parent_value == parent_value, , drop = FALSE]
  }
  if (enabled_only) out <- out[tolower(as.character(out$enabled)) == "true", , drop = FALSE]
  out[order(suppressWarnings(as.numeric(out$display_order))), , drop = FALSE]
}

mm_choices <- function(level, parent_value = NULL) {
  o <- mm_options(level, parent_value)
  if (nrow(o) == 0) return(character(0))
  stats::setNames(o$filter_value, o$filter_label)
}

mm_disabled <- function(level, parent_value = NULL) {
  f <- mm_get("filters")
  if (nrow(f) == 0) return(f)
  out <- f[f$filter_name == level & tolower(as.character(f$enabled)) != "true", , drop = FALSE]
  if (!is.null(parent_value) && nzchar(parent_value)) {
    out <- out[out$parent_value == parent_value, , drop = FALSE]
  }
  out
}

# Resolve the currently selected identity from the composite filter value.
mm_selection <- function(metric = NULL, db_type = NULL, scenario = NULL,
                         granularity = NULL, key = NULL, version = NULL) {
  parts <- function(x) if (is.null(x) || !nzchar(x)) character(0) else strsplit(x, "::", fixed = TRUE)[[1]]
  p <- parts(version)
  if (length(p) < 6) p <- parts(key)
  if (length(p) < 5) p <- parts(granularity)
  if (length(p) < 4) p <- parts(scenario)
  if (length(p) < 3) p <- parts(db_type)
  if (length(p) < 2) p <- parts(metric)
  list(
    metric_id        = if (length(p) >= 1) p[1] else "",
    db_type          = if (length(p) >= 2) p[2] else "",
    scenario         = if (length(p) >= 3) p[3] else "",
    granularity      = if (length(p) >= 4) p[4] else "",
    entity_key       = if (length(p) >= 5) p[5] else "",
    forecast_version = if (length(p) >= 6) p[6] else ""
  )
}

mm_computability <- function(metric_id, db_type, granularity) {
  c_df <- mm_get("computability")
  if (nrow(c_df) == 0) return(NULL)
  hit <- c_df[c_df$metric_id == metric_id &
                c_df$db_type == db_type &
                c_df$granularity == granularity, , drop = FALSE]
  if (nrow(hit) == 0) return(NULL)
  as.list(hit[1, , drop = TRUE])
}

mm_availability <- function(metric_id, db_type, granularity) {
  a_df <- mm_get("availability")
  if (nrow(a_df) == 0) return(NULL)
  hit <- a_df[a_df$metric_id == metric_id &
                a_df$db_type == db_type &
                a_df$granularity == granularity, , drop = FALSE]
  if (nrow(hit) == 0) return(NULL)
  as.list(hit[1, , drop = TRUE])
}

mm_truthy <- function(x) {
  isTRUE(tolower(trimws(as.character(x))) %in% c("true", "yes", "1"))
}

mm_allowed_views <- function(comp) {
  if (is.null(comp)) return(character(0))
  v <- trimws(as.character(comp$shiny_allowed_views))
  if (!nzchar(v) || identical(v, "none")) return(character(0))
  strsplit(v, "|", fixed = TRUE)[[1]]
}

# Filtered slices used by the tables. Plain subsetting, no joins.
mm_rankings_for <- function(sel, scope = c("key", "combo")) {
  scope <- match.arg(scope)
  r <- mm_get("rankings")
  if (nrow(r) == 0) return(r)
  out <- r[r$metric_id == sel$metric_id &
             r$db_type == sel$db_type &
             r$granularity == sel$granularity, , drop = FALSE]
  if (scope == "key" && nzchar(sel$entity_key)) {
    out <- out[out$entity_key == sel$entity_key, , drop = FALSE]
  }
  out
}

mm_normalized_for <- function(sel) {
  n <- mm_get("normalized")
  if (nrow(n) == 0) return(n)
  out <- n[n$metric_id == sel$metric_id &
             n$db_type == sel$db_type &
             n$granularity == sel$granularity, , drop = FALSE]
  if (nzchar(sel$entity_key)) out <- out[out$entity_key == sel$entity_key, , drop = FALSE]
  if (nzchar(sel$forecast_version)) {
    out <- out[out$forecast_version == sel$forecast_version, , drop = FALSE]
  }
  out
}

mm_context_for <- function(sel) {
  ctx <- mm_get("assistant")
  if (nrow(ctx) == 0) return(NULL)
  hit <- ctx[ctx$metric_id == sel$metric_id &
               ctx$db_type == sel$db_type &
               ctx$granularity == sel$granularity, , drop = FALSE]
  if (nzchar(sel$entity_key)) hit <- hit[hit$entity_key == sel$entity_key, , drop = FALSE]
  if (nzchar(sel$forecast_version)) {
    hit <- hit[hit$forecast_version == sel$forecast_version, , drop = FALSE]
  }
  if (nrow(hit) == 0) return(NULL)
  as.list(hit[1, , drop = TRUE])
}

# ---------------------------------------------------------------------
# Assistant extension: ADD the multi-metric entries to the already-loaded
# response index. The legacy pack file is never touched, and if anything
# is missing the assistant keeps its current behaviour.
# ---------------------------------------------------------------------
mm_register_assistant_pack <- function() {
  mm_load()
  pack <- .mm_env$pack
  if (is.null(pack) || is.null(pack$responses)) return(invisible(FALSE))
  if (!exists("llm_explain_load", mode = "function")) return(invisible(FALSE))

  ok <- tryCatch({
    llm_explain_load()
    idx <- get("responses", envir = .llm_explain_env)
    added <- 0L
    for (r in pack$responses) {
      pid <- r$page_id
      if (!is.null(pid) && is.null(idx[[pid]])) {
        idx[[pid]] <- r
        added <- added + 1L
      }
    }
    assign("responses", idx, envir = .llm_explain_env)
    .mm_env$assistant_pages_added <- added
    TRUE
  }, error = function(e) {
    message("[multi-metric] assistant pack not registered: ", conditionMessage(e))
    FALSE
  })
  invisible(ok)
}

mm_assistant_pages <- function() {
  mm_load()
  pack <- .mm_env$pack
  if (is.null(pack) || is.null(pack$responses)) return(character(0))
  vapply(pack$responses, function(r) as.character(r$page_id), character(1))
}

# Safe initializer for app startup.
mm_init <- function() {
  tryCatch({
    mm_load()
    mm_register_assistant_pack()
    TRUE
  }, error = function(e) {
    message("[multi-metric] non-fatal init issue: ", conditionMessage(e))
    FALSE
  })
}
