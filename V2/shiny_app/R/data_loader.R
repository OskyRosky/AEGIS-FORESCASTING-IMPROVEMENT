# =====================================================================
# TESSERACT v2 | data_loader.R | Block 7.0E Governed Data Loader
# ---------------------------------------------------------------------
# GOVERNANCE CONTRACT (read-only):
#   - Reads existing closure-pack / governance / audit artifacts only.
#   - Does NOT recompute metrics, run models, or generate forecasts.
#   - Does NOT change the champion decision or champion language.
#   - Missing non-critical artifacts NEVER stop the app: empty frames
#     and status objects are returned instead.
#   - No new packages are required: base R `read.csv` is used when
#     `readr` is not available.
# This block ONLY exposes data to future blocks. It does not populate
# any dashboard page.
# =====================================================================

# Private cache (isolated, not attached to globalenv)
.tess_loader_env <- new.env(parent = emptyenv())

# ---------------------------------------------------------------------
# 1. Project root resolution (robust)
# ---------------------------------------------------------------------
find_project_root <- function(start = getwd()) {
  is_root <- function(d) {
    dir.exists(file.path(d, "outputs", "model_lab")) &&
      dir.exists(file.path(d, "shiny_app"))
  }
  # Common case: runApp working dir is the V1 root.
  candidates <- c(start, dirname(start))
  for (cand in candidates) {
    if (is_root(cand)) return(normalizePath(cand, winslash = "/", mustWork = FALSE))
  }
  # Walk upward looking for the governed root markers.
  cur <- normalizePath(start, winslash = "/", mustWork = FALSE)
  for (i in seq_len(6)) {
    if (is_root(cur)) return(cur)
    if (file.exists(file.path(cur, "ACTIVE_PROJECT_ROOT.md"))) return(cur)
    parent <- dirname(cur)
    if (identical(parent, cur)) break
    cur <- parent
  }
  # Fallback: original working directory (never throws).
  normalizePath(start, winslash = "/", mustWork = FALSE)
}

# ---------------------------------------------------------------------
# 2. Safe readers (read-only, never throw)
# ---------------------------------------------------------------------
.tess_read_csv_file <- function(path) {
  if (is.null(path) || !file.exists(path)) return(data.frame())
  out <- tryCatch({
    if (requireNamespace("readr", quietly = TRUE)) {
      as.data.frame(
        readr::read_csv(path, show_col_types = FALSE, progress = FALSE),
        stringsAsFactors = FALSE
      )
    } else {
      utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
    }
  }, error = function(e) {
    # Last-resort base reader (handles odd encodings / readr issues).
    tryCatch(
      utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE),
      error = function(e2) data.frame()
    )
  })
  if (is.null(out)) data.frame() else out
}

.tess_read_text_file <- function(path) {
  if (is.null(path) || !file.exists(path)) return(character(0))
  tryCatch(
    readLines(path, warn = FALSE, encoding = "UTF-8"),
    error = function(e) tryCatch(readLines(path, warn = FALSE),
                                 error = function(e2) character(0))
  )
}

# ---------------------------------------------------------------------
# 3. Artifact registry definition
#    requirement: required | optional | roadmap
#    type:        csv | text
# ---------------------------------------------------------------------
build_artifact_registry <- function() {
  rows <- list(
    # --- Closure pack (required governed outputs) ---
    c("key_results",                "closure_pack", "csv",  "required",
      "outputs/model_lab/model_lab_closure_pack/model_lab_key_results.csv"),
    c("champion_summary",           "closure_pack", "csv",  "required",
      "outputs/model_lab/model_lab_closure_pack/model_lab_champion_summary.csv"),
    c("final_model_universe",       "closure_pack", "csv",  "required",
      "outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv"),
    c("risk_register_final",        "closure_pack", "csv",  "required",
      "outputs/model_lab/model_lab_closure_pack/model_lab_risk_register_final.csv"),
    c("deferred_models",            "closure_pack", "csv",  "optional",
      "outputs/model_lab/model_lab_closure_pack/model_lab_deferred_models.csv"),
    c("next_steps",                 "closure_pack", "csv",  "optional",
      "outputs/model_lab/model_lab_closure_pack/model_lab_next_steps.csv"),
    c("dashboard_handoff_manifest", "closure_pack", "csv",  "optional",
      "outputs/model_lab/model_lab_closure_pack/model_lab_dashboard_handoff_manifest.csv"),
    c("artifact_manifest",          "closure_pack", "csv",  "optional",
      "outputs/model_lab/model_lab_closure_pack/model_lab_artifact_manifest.csv"),

    # --- Tournament engine (required for standings / evidence) ---
    c("tournament_standings",       "tournament",   "csv",  "required",
      "outputs/model_lab/tournament_engine/tournament_preliminary_standings.csv"),
    c("tournament_scorecard",       "tournament",   "csv",  "required",
      "outputs/model_lab/tournament_engine/tournament_model_scorecard.csv"),
    c("tournament_pairwise",        "tournament",   "csv",  "optional",
      "outputs/model_lab/tournament_engine/tournament_pairwise_evidence.csv"),

    # --- Challenger diagnostics (optional, diagnostic-only metrics) ---
    c("challenger_metrics",         "challenger",   "csv",  "optional",
      "outputs/model_lab/challenger_metrics/challenger_metrics_by_model_diagnostic.csv"),
    c("challenger_aggregation",     "challenger",   "csv",  "optional",
      "outputs/model_lab/challenger_aggregation_significance/challenger_aggregation_by_model.csv"),

    # --- Governance: champion conditions (required for conditions page) ---
    c("champion_conditions",        "governance",   "csv",  "required",
      "outputs/governance/6_3_champion_conditions/champion_conditions_protocol.csv"),
    c("champion_dashboard_language","governance",   "csv",  "required",
      "outputs/governance/6_3_champion_conditions/champion_dashboard_language.csv"),

    # --- Audit trail (optional governed evidence) ---
    c("audit_4_summary",            "audit",        "csv",  "optional",
      "outputs/model_lab/audit_4/audit_4_summary.csv"),
    c("audit_5_findings",           "audit",        "csv",  "optional",
      "outputs/model_lab/audit_5/audit_5_findings.csv"),
    c("audit_5_report",             "audit",        "text", "optional",
      "outputs/model_lab/audit_5/audit_5_final_report.md"),
    c("tournament_sanity_summary",  "audit",        "csv",  "optional",
      "outputs/model_lab/tournament_sanity_review/tournament_sanity_summary.csv"),

    # --- Methodology / reference (text) ---
    c("benchmark_semantics",        "methodology",  "text", "optional",
      "docs/benchmark_semantics/benchmark_semantics_v1.md"),
    c("champion_decision_report",   "methodology",  "text", "optional",
      "outputs/model_lab/champion_decision/champion_decision_report.md"),

    # --- Forecasting data (optional, for explorer/accuracy later) ---
    c("forecasts",                  "forecasting",  "csv",  "optional",
      "data/processed/forecasts.csv"),
    c("actuals",                    "forecasting",  "csv",  "optional",
      "data/processed/actuals.csv"),
    c("forecast_comparison",        "forecasting",  "csv",  "optional",
      "data/processed/forecast_comparison.csv"),
    c("entities",                   "forecasting",  "csv",  "optional",
      "data/processed/entities.csv"),
    c("run_metadata",               "forecasting",  "csv",  "optional",
      "data/processed/run_metadata.csv"),

    # --- Stage 05H FULL multi-model handoff (Forecast Viewer - ACTIVE) ---
    # Long/tidy historical BACKTEST comparison artifact: 39 eligible series,
    # 13 models each, horizons 1-30. Read-only; the ACTIVE full Forecast Viewer
    # Backtest Comparison section consumes ONLY this artifact (Block
    # 7.11-FULL-REBIND). It is never modified by the app.
    c("forecast_viewer_full",           "forecasting", "csv", "optional",
      "data/processed/forecast_viewer_model_outputs.csv"),
    c("forecast_viewer_full_manifest",  "forecasting", "csv", "optional",
      "data/processed/forecast_viewer_model_outputs_manifest.csv"),

    # --- Stage 05H pilot multi-model handoff (superseded by full; kept for
    #     provenance only - the ACTIVE viewer no longer reads the pilot). ---
    c("forecast_viewer_pilot",          "forecasting", "csv", "optional",
      "data/processed/forecast_viewer_model_outputs_pilot.csv"),
    c("forecast_viewer_pilot_manifest", "forecasting", "csv", "optional",
      "data/processed/forecast_viewer_model_outputs_pilot_manifest.csv"),

    # --- TTL / capacity-to-live (no governed artifact yet -> roadmap) ---
    c("ttl_capacity",               "ttl",          "csv",  "roadmap",
      "outputs/model_lab/ttl/ttl_capacity_view.csv"),

    # --- TTL PROTOTYPE (SIMULATED supply + TTL; REAL demand from forecasts).
    #     Not governed. Mirrors AEGIS capacity views so the swap to the real
    #     SQL sources (vw_SubstrateBE_MonthsToLive_*, HLC_BE_Future_Supply_*)
    #     is a drop-in replacement. See python/shiny_mvp/build_ttl_prototype.py.
    c("ttl_supply_demand_timeseries", "ttl",        "csv",  "optional",
      "data/processed/ttl_supply_demand_timeseries.csv"),
    c("ttl_months_to_live_snapshot",  "ttl",        "csv",  "optional",
      "data/processed/ttl_months_to_live_snapshot.csv")
  )

  reg <- do.call(rbind, lapply(rows, function(r) {
    data.frame(
      artifact_key = r[1],
      category     = r[2],
      type         = r[3],
      requirement  = r[4],
      rel_path     = r[5],
      stringsAsFactors = FALSE
    )
  }))
  rownames(reg) <- NULL
  reg
}

# ---------------------------------------------------------------------
# 4. Core load routine (populates the private cache)
# ---------------------------------------------------------------------
load_governed_artifacts <- function(root = find_project_root(), verbose = TRUE) {
  reg <- build_artifact_registry()
  data_store <- list()
  presence   <- character(nrow(reg))
  abs_paths  <- character(nrow(reg))
  n_rows     <- integer(nrow(reg))
  n_cols     <- integer(nrow(reg))

  for (i in seq_len(nrow(reg))) {
    key   <- reg$artifact_key[i]
    type  <- reg$type[i]
    p     <- file.path(root, reg$rel_path[i])
    abs_paths[i] <- p
    if (file.exists(p)) {
      presence[i] <- "available"
      if (identical(type, "csv")) {
        df <- .tess_read_csv_file(p)
        data_store[[key]] <- df
        n_rows[i] <- nrow(df)
        n_cols[i] <- ncol(df)
      } else {
        txt <- .tess_read_text_file(p)
        data_store[[key]] <- txt
        n_rows[i] <- length(txt)
        n_cols[i] <- 1L
      }
      if (verbose) cat(sprintf("[loader] available : %-28s (%s)\n", key, reg$rel_path[i]))
    } else {
      presence[i] <- "missing"
      data_store[[key]] <- if (identical(type, "csv")) data.frame() else character(0)
      n_rows[i] <- 0L
      n_cols[i] <- 0L
      lvl <- if (identical(reg$requirement[i], "required")) "MISSING " else "missing "
      if (verbose) cat(sprintf("[loader] %s: %-28s (%s)\n", lvl, key, reg$rel_path[i]))
    }
  }

  reg$presence  <- presence
  reg$abs_path  <- abs_paths
  reg$n_rows    <- n_rows
  reg$n_cols    <- n_cols
  reg$status    <- mapply(function(req, pres) {
    if (identical(req, "roadmap")) return("roadmap")
    if (identical(pres, "available")) return(paste0(req, "_available"))
    paste0(req, "_missing")
  }, reg$requirement, reg$presence)

  assign("root", root, envir = .tess_loader_env)
  assign("registry", reg, envir = .tess_loader_env)
  assign("data", data_store, envir = .tess_loader_env)
  assign("loaded_at", format(Sys.time(), "%Y-%m-%dT%H:%M:%S"), envir = .tess_loader_env)
  invisible(reg)
}

# ---------------------------------------------------------------------
# 5. Public accessors (used by future population blocks)
# ---------------------------------------------------------------------
tess_artifact <- function(artifact_key) {
  store <- tryCatch(get("data", envir = .tess_loader_env), error = function(e) NULL)
  if (is.null(store) || is.null(store[[artifact_key]])) return(data.frame())
  store[[artifact_key]]
}

load_csv_artifact <- function(artifact_key) {
  val <- tess_artifact(artifact_key)
  if (is.data.frame(val)) val else data.frame()
}

load_text_artifact <- function(artifact_key) {
  val <- tess_artifact(artifact_key)
  if (is.character(val)) val else character(0)
}

get_artifact_status <- function() {
  reg <- tryCatch(get("registry", envir = .tess_loader_env), error = function(e) NULL)
  if (is.null(reg)) return(build_artifact_registry())
  reg
}

# ---------------------------------------------------------------------
# 6. Package availability (NO installation performed)
# ---------------------------------------------------------------------
get_package_availability <- function() {
  spec <- list(
    list("highcharter", "Primary interactive charts",
         "Fallback to plotly (installed) or static placeholder"),
    list("reactable",   "Styled interactive tables",
         "Fallback to DT (installed) or styled HTML/CSS table"),
    list("DT",          "Export / search-heavy tables",
         "Skip export/search-only tables if missing"),
    list("plotly",      "Chart fallback when highcharter absent",
         "Static placeholder if also missing"),
    list("shiny",       "App runtime",
         "Hard requirement - report blocking issue if missing"),
    list("bslib",       "Theme / layout",
         "Report blocking issue if missing"),
    list("htmltools",   "HTML tag building",
         "Report blocking issue if missing")
  )
  do.call(rbind, lapply(spec, function(s) {
    data.frame(
      package_name   = s[[1]],
      available      = isTRUE(requireNamespace(s[[1]], quietly = TRUE)),
      planned_usage  = s[[2]],
      fallback_strategy = s[[3]],
      stringsAsFactors = FALSE
    )
  }))
}

# ---------------------------------------------------------------------
# 7. Safe initializer for app startup (never stops the app)
# ---------------------------------------------------------------------
tess_init_governed_loader <- function() {
  tryCatch({
    load_governed_artifacts(verbose = FALSE)
    TRUE
  }, error = function(e) {
    message("[loader] non-fatal init issue: ", conditionMessage(e))
    # Ensure accessors still work with empty store.
    assign("registry", build_artifact_registry(), envir = .tess_loader_env)
    assign("data", list(), envir = .tess_loader_env)
    FALSE
  })
}
