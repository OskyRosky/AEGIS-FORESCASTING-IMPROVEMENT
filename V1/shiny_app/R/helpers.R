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

# ---------------------------------------------------------------------------
# Block 7.11 | Forecast Viewer governed data accessors (read-only)
# Read existing governed forecast/actual artifacts from the 7.0E loader cache.
# These NEVER generate forecasts, never recompute metrics, never run models,
# and never invent values. They only filter and reshape existing rows for
# interactive display.
# ---------------------------------------------------------------------------

# Cached governed reads (loader already parsed these at init).
fv_forecasts <- function() {
  df <- tryCatch(load_csv_artifact("forecasts"), error = function(e) data.frame())
  if (is.data.frame(df)) df else data.frame()
}
fv_actuals <- function() {
  df <- tryCatch(load_csv_artifact("actuals"), error = function(e) data.frame())
  if (is.data.frame(df)) df else data.frame()
}

# Sorted unique entity keys that actually have forecast rows (so a selection
# always has something to chart).
fv_entity_choices <- function(fc = fv_forecasts()) {
  if (!is.data.frame(fc) || !("entity_key" %in% names(fc)) || nrow(fc) == 0) {
    return(character(0))
  }
  sort(unique(trimws(as.character(fc$entity_key))))
}

# Model versions available for a given entity (from the forecasts artifact).
fv_models_for_entity <- function(entity, fc = fv_forecasts()) {
  if (is.null(entity) || !nzchar(entity) || !is.data.frame(fc) ||
      !all(c("entity_key", "model_version") %in% names(fc))) {
    return(character(0))
  }
  hit <- fc$model_version[trimws(as.character(fc$entity_key)) == entity]
  sort(unique(trimws(as.character(hit))))
}

# Allowed forecast-horizon options (days).
fv_horizon_choices <- function() c(5, 10, 15, 20, 25, 30, 45, 60)

# Total distinct model versions available across ALL forecast artifacts.
fv_model_count_global <- function(fc = fv_forecasts()) {
  if (!is.data.frame(fc) || !("model_version" %in% names(fc)) || nrow(fc) == 0) {
    return(0L)
  }
  length(unique(trimws(as.character(fc$model_version))))
}

# Filtered actual series for an entity, trimmed to a history window (days).
# hist_days <= 0 (or NA) means "all available history".
fv_actual_series <- function(entity, hist_days = 90, ac = fv_actuals()) {
  if (is.null(entity) || !nzchar(entity) || !is.data.frame(ac) ||
      !all(c("entity_key", "date", "actual_value") %in% names(ac))) {
    return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  }
  a <- ac[trimws(as.character(ac$entity_key)) == entity, , drop = FALSE]
  if (nrow(a) == 0) return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  d <- as.Date(a$date)
  v <- suppressWarnings(as.numeric(a$actual_value))
  keep <- !is.na(d) & !is.na(v)
  out <- data.frame(date = d[keep], value = v[keep])
  out <- out[order(out$date), , drop = FALSE]
  if (!is.null(hist_days) && !is.na(hist_days) && hist_days > 0 && nrow(out) > 0) {
    cutoff <- max(out$date) - as.integer(hist_days)
    out <- out[out$date > cutoff, , drop = FALSE]
  }
  out
}

# Filtered forecast series for an entity + model, trimmed to a horizon (days)
# counted from the first forecast date forward. Never extends beyond available
# forecast rows (no invented future values).
fv_forecast_series <- function(entity, model, horizon_days = 30, fc = fv_forecasts()) {
  if (is.null(entity) || !nzchar(entity) || !is.data.frame(fc) ||
      !all(c("entity_key", "date", "forecast_value") %in% names(fc))) {
    return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  }
  f <- fc[trimws(as.character(fc$entity_key)) == entity, , drop = FALSE]
  if (!is.null(model) && nzchar(model) && "model_version" %in% names(f)) {
    f <- f[trimws(as.character(f$model_version)) == model, , drop = FALSE]
  }
  if (nrow(f) == 0) return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  d <- as.Date(f$date)
  v <- suppressWarnings(as.numeric(f$forecast_value))
  keep <- !is.na(d) & !is.na(v)
  out <- data.frame(date = d[keep], value = v[keep])
  out <- out[order(out$date), , drop = FALSE]
  if (!is.null(horizon_days) && !is.na(horizon_days) && horizon_days > 0 && nrow(out) > 0) {
    out <- out[seq_len(min(nrow(out), as.integer(horizon_days))), , drop = FALSE]
  }
  out
}

# Small summary list describing the currently selected combination.
fv_summary <- function(entity, model, horizon_days = 30, hist_days = 90) {
  a <- fv_actual_series(entity, hist_days)
  f <- fv_forecast_series(entity, model, horizon_days)
  list(
    entity        = if (is.null(entity) || !nzchar(entity)) "\u2014" else entity,
    model         = if (is.null(model)  || !nzchar(model))  "\u2014" else model,
    horizon       = if (is.null(horizon_days) || is.na(horizon_days)) "\u2014"
                    else paste0(as.integer(horizon_days), " days"),
    n_actual      = nrow(a),
    n_forecast    = nrow(f),
    forecast_start = if (nrow(f) > 0) format(min(f$date), "%Y-%m-%d") else "\u2014",
    last_actual    = if (nrow(a) > 0) format(max(a$date), "%Y-%m-%d") else "\u2014"
  )
}

# Richer data-availability snapshot for the explanation panel. Reports, for the
# selected combination, how many forecast/actual points exist, how many models
# the entity has (vs globally), and how the requested horizon compares with what
# can actually be displayed (so a short model list / clipped horizon is honest).
fv_availability <- function(entity, model, horizon_days = 30, hist_days = 90) {
  ent_models  <- fv_models_for_entity(entity)
  glob_models <- fv_model_count_global()
  a    <- fv_actual_series(entity, hist_days)
  fall <- fv_forecast_series(entity, model, horizon_days = 0)   # all forecast rows
  req  <- if (is.null(horizon_days) || is.na(horizon_days) || horizon_days <= 0)
            nrow(fall) else as.integer(horizon_days)
  shown <- min(nrow(fall), req)
  list(
    entity            = if (is.null(entity) || !nzchar(entity)) "\u2014" else entity,
    model             = if (is.null(model)  || !nzchar(model))  "\u2014" else model,
    n_forecast_total  = nrow(fall),
    n_actual          = nrow(a),
    n_models_entity   = length(ent_models),
    models_entity     = ent_models,
    n_models_global   = glob_models,
    horizon_requested = req,
    horizon_displayed = shown,
    horizon_clipped   = (req > nrow(fall))
  )
}

# A calm empty-state highchart (no series), shown when a combination has no data.
fv_empty_chart <- function(
    msg = "No forecast data is available for this selected series/model/horizon.") {
  highcharter::highchart() |>
    highcharter::hc_title(text = msg,
                          style = list(fontSize = "14px", color = "#627d98")) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_xAxis(visible = FALSE) |>
    highcharter::hc_yAxis(visible = FALSE)
}

# Build the interactive Forecast Viewer highchart for the selected combination.
# Actual (history) and Forecast (future) as two professional lines, with a
# dashed plot line marking the forecast start. Reads only existing rows.
fv_chart <- function(entity, model, horizon_days = 30, hist_days = 90) {
  a <- fv_actual_series(entity, hist_days)
  f <- fv_forecast_series(entity, model, horizon_days)
  if (nrow(a) == 0 && nrow(f) == 0) return(fv_empty_chart())

  a_df <- if (nrow(a) > 0)
    data.frame(x = highcharter::datetime_to_timestamp(a$date), y = round(a$value, 3)) else NULL
  f_df <- if (nrow(f) > 0)
    data.frame(x = highcharter::datetime_to_timestamp(f$date), y = round(f$value, 3)) else NULL

  ttl_entity <- if (is.null(entity) || !nzchar(entity)) "\u2014" else entity
  ttl_model  <- if (is.null(model)  || !nzchar(model))  "\u2014" else model

  plot_lines <- list()
  if (nrow(f) > 0) {
    plot_lines <- list(list(
      value = highcharter::datetime_to_timestamp(min(f$date)),
      color = "#9aa5b1", width = 1.5, dashStyle = "Dash", zIndex = 4,
      label = list(text = "Forecast start",
                   style = list(color = "#627d98", fontSize = "10px"))
    ))
  }

  # Stock chart -> built-in range selector + navigator + scrollbar give the
  # user true horizontal time navigation (zoom + scroll) over the series.
  hc <- highcharter::highchart(type = "stock") |>
    highcharter::hc_chart(zoomType = "x", panning = list(enabled = TRUE),
                          panKey = "shift",
                          style = list(fontFamily = "Inter, system-ui, sans-serif")) |>
    highcharter::hc_title(text = ttl_entity,
                          style = list(fontSize = "15px", fontWeight = "600", color = "#102a43")) |>
    highcharter::hc_subtitle(text = paste0("Model: ", ttl_model),
                             style = list(fontSize = "12px", color = "#627d98")) |>
    highcharter::hc_xAxis(type = "datetime", title = list(text = NULL),
                          plotLines = plot_lines) |>
    highcharter::hc_yAxis(title = list(text = "Value"), opposite = FALSE) |>
    highcharter::hc_legend(enabled = TRUE) |>
    highcharter::hc_tooltip(shared = TRUE, xDateFormat = "%Y-%m-%d", valueDecimals = 3,
                            headerFormat = paste0(
                              "<span style='font-size:11px;color:#627d98'>",
                              ttl_entity, " \u00b7 ", ttl_model,
                              "</span><br/><b>{point.key}</b><br/>")) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_navigator(enabled = TRUE) |>
    highcharter::hc_scrollbar(enabled = TRUE) |>
    highcharter::hc_rangeSelector(
      enabled = TRUE, selected = 4,
      buttons = list(
        list(type = "month", count = 1, text = "1m"),
        list(type = "month", count = 3, text = "3m"),
        list(type = "month", count = 6, text = "6m"),
        list(type = "ytd", text = "YTD"),
        list(type = "all", text = "All"))) |>
    highcharter::hc_plotOptions(
      line   = list(marker = list(enabled = FALSE), lineWidth = 2),
      series = list(showInNavigator = TRUE))

  if (!is.null(a_df)) {
    hc <- hc |> highcharter::hc_add_series(
      name = "Actual", type = "line", color = "#2e75b6",
      data = highcharter::list_parse(a_df))
  }
  if (!is.null(f_df)) {
    hc <- hc |> highcharter::hc_add_series(
      name = "Forecast", type = "line", color = "#d97706", dashStyle = "ShortDash",
      data = highcharter::list_parse(f_df))
  }
  hc
}

# ===========================================================================
# Block 7.11-FULL-REBIND | Forecast Viewer BACKTEST accessors (read-only)
# ---------------------------------------------------------------------------
# These read ONLY the Stage 05H FULL multi-model handoff artifact
# (data/processed/forecast_viewer_model_outputs.csv) via the governed loader
# cache. They NEVER read forecasts.csv for the backtest section, NEVER generate
# forecasts, NEVER recompute metrics, NEVER run models, and NEVER persist
# reshaped data. They only filter / reshape existing rows in memory for
# charting. The pilot artifact is no longer read by the active viewer.
#
# Artifact semantics: historical / BACKTEST model comparison (NOT the forward
# production forecast). One row per series x model x date x horizon_days.
# Prediction intervals are NOT available in this artifact. 39 eligible series,
# 13 models each, horizons 1-30.
# ===========================================================================

# Fixed family order for grouped model checkboxes.
FVP_FAMILY_ORDER <- c("growth_baseline", "statistical",
                      "machine_learning", "lightweight_neural")
FVP_FAMILY_LABELS <- c(
  growth_baseline    = "Growth baseline",
  statistical        = "Statistical",
  machine_learning   = "Machine learning",
  lightweight_neural = "Lightweight neural"
)

# Horizon options exposed in the UI (artifact covers 1..30; the UI offers this
# governed subset only). 35 / 45 do NOT exist in the artifact and are shown as
# disabled "Not available in current artifact" chips, never as real options.
fvp_horizon_choices <- function() c(5, 10, 15, 20, 25, 30)
fvp_horizon_unavailable <- function() c(35, 45)

# Recommended default model selection (omitted safely if unavailable).
fvp_default_models <- function() {
  c("ETS Explicit", "ARIMA_Fixed", "FixedGrowth_3",
    "LightGBM", "XGBoost", "FastNeuralAR_MLP")
}

# Cached governed read of the FULL backtest artifact (parsed at loader init).
fvp_data <- function() {
  df <- tryCatch(load_csv_artifact("forecast_viewer_full"),
                 error = function(e) data.frame())
  if (!is.data.frame(df) || nrow(df) == 0) return(data.frame())
  # Normalize key text columns once (trim only; no value changes).
  for (col in c("series_key", "model_name", "model_family",
                "model_origin", "risk_status")) {
    if (col %in% names(df)) df[[col]] <- trimws(as.character(df[[col]]))
  }
  df
}

# Sorted unique pilot series keys.
fvp_series_choices <- function(df = fvp_data()) {
  if (!is.data.frame(df) || !("series_key" %in% names(df)) || nrow(df) == 0) {
    return(character(0))
  }
  sort(unique(df$series_key))
}

# Per-model metadata for the selected series (family / origin / risk / champion).
# Returns a data.frame ordered by family then model_name.
fvp_model_meta <- function(series, df = fvp_data()) {
  empty <- data.frame(model_name = character(0), model_family = character(0),
                      model_origin = character(0), risk_status = character(0),
                      is_selected_champion = logical(0),
                      stringsAsFactors = FALSE)
  if (is.null(series) || !nzchar(series) || !is.data.frame(df) || nrow(df) == 0 ||
      !all(c("series_key", "model_name") %in% names(df))) {
    return(empty)
  }
  g <- df[df$series_key == series, , drop = FALSE]
  if (nrow(g) == 0) return(empty)
  champ <- if ("is_selected_champion" %in% names(g))
    .tess_as_logical(g$is_selected_champion) else rep(FALSE, nrow(g))
  meta <- data.frame(
    model_name           = g$model_name,
    model_family         = if ("model_family" %in% names(g)) g$model_family else "",
    model_origin         = if ("model_origin" %in% names(g)) g$model_origin else "",
    risk_status          = if ("risk_status" %in% names(g)) g$risk_status else "",
    is_selected_champion = champ %in% TRUE,
    stringsAsFactors     = FALSE
  )
  meta <- unique(meta)
  fam_rank <- match(meta$model_family, FVP_FAMILY_ORDER)
  fam_rank[is.na(fam_rank)] <- length(FVP_FAMILY_ORDER) + 1L
  meta[order(fam_rank, meta$model_name), , drop = FALSE]
}

# Models available for the selected series (character vector, family-ordered).
fvp_models_for_series <- function(series, df = fvp_data()) {
  meta <- fvp_model_meta(series, df)
  if (nrow(meta) == 0) return(character(0))
  meta$model_name
}

# A friendly checkbox label for a model row (adds champion / risk badges).
fvp_model_label <- function(model_name, is_champion, risk_status) {
  lbl <- model_name
  if (isTRUE(is_champion)) lbl <- paste0(lbl, "  \u2605 champion")
  if (identical(tolower(trimws(as.character(risk_status))), "high_risk")) {
    lbl <- paste0(lbl, "  \u26A0 high risk")
  }
  lbl
}

# Actual series for a pilot series, trimmed to a history window (days).
# actual_value is constant across models/horizons for a given date, so we
# deduplicate by date. hist_days <= 0 (or NA) means "full pilot window".
fvp_actual_series <- function(series, hist_days = 0, df = fvp_data()) {
  if (is.null(series) || !nzchar(series) || !is.data.frame(df) || nrow(df) == 0 ||
      !all(c("series_key", "date", "actual_value") %in% names(df))) {
    return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  }
  g <- df[df$series_key == series, , drop = FALSE]
  if (nrow(g) == 0) return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  d <- as.Date(g$date)
  v <- suppressWarnings(as.numeric(g$actual_value))
  keep <- !is.na(d) & !is.na(v)
  out <- unique(data.frame(date = d[keep], value = v[keep]))
  out <- out[order(out$date), , drop = FALSE]
  out <- .fvp_apply_history(out, hist_days)
  out
}

# Forecast series for a pilot series + single model + horizon, trimmed to a
# history window (days). Reads ONLY existing forecast_value rows.
fvp_forecast_series <- function(series, model, horizon_days, hist_days = 0,
                                df = fvp_data()) {
  if (is.null(series) || !nzchar(series) || is.null(model) || !nzchar(model) ||
      !is.data.frame(df) || nrow(df) == 0 ||
      !all(c("series_key", "model_name", "date",
             "forecast_value", "horizon_days") %in% names(df))) {
    return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  }
  g <- df[df$series_key == series & df$model_name == model, , drop = FALSE]
  if (!is.null(horizon_days) && !is.na(horizon_days)) {
    h <- suppressWarnings(as.numeric(g$horizon_days))
    g <- g[!is.na(h) & h == as.numeric(horizon_days), , drop = FALSE]
  }
  if (nrow(g) == 0) return(data.frame(date = as.Date(character(0)), value = numeric(0)))
  d <- as.Date(g$date)
  v <- suppressWarnings(as.numeric(g$forecast_value))
  keep <- !is.na(d) & !is.na(v)
  out <- data.frame(date = d[keep], value = v[keep])
  out <- out[order(out$date), , drop = FALSE]
  out <- .fvp_apply_history(out, hist_days)
  out
}

# Apply a trailing history window (days) relative to the latest date present.
.fvp_apply_history <- function(out, hist_days) {
  if (is.null(hist_days) || is.na(hist_days) || hist_days <= 0 || nrow(out) == 0) {
    return(out)
  }
  cutoff <- max(out$date) - as.integer(hist_days)
  out[out$date >= cutoff, , drop = FALSE]
}

# A calm empty-state highchart (no series). Used as the STATIC chart's initial
# render before Analyze is clicked, and when a combination has no data.
fvp_empty_chart <- function(
    msg = "Select a series, choose models and horizon, then click Analyze Forecast.") {
  highcharter::highchart() |>
    highcharter::hc_title(text = msg,
                          style = list(fontSize = "13px", color = "#627d98",
                                       fontWeight = "500")) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_xAxis(visible = FALSE) |>
    highcharter::hc_yAxis(visible = FALSE) |>
    highcharter::hc_chart(
      style = list(fontFamily = "Inter, system-ui, sans-serif"))
}

# Distinct color per model line (stable order; actual is reserved blue).
.fvp_palette <- c(
  "#d97706", "#2e9e5b", "#9b59b6", "#e0508a", "#0e7490",
  "#b45309", "#1f77b4", "#7f8c1a", "#c0392b", "#16a085",
  "#8e44ad", "#2c3e50", "#d35400"
)

# Build the multi-model Forecast Viewer highchart for the selected combination.
# One ACTUAL line plus one forecast line per selected model, for a single
# horizon and history window. Tooltip carries model_family / risk_status.
fvp_chart <- function(series, models, horizon_days = 5, hist_days = 0,
                      df = fvp_data()) {
  models <- models[!is.na(models) & nzchar(models)]
  a <- fvp_actual_series(series, hist_days, df)
  if (length(models) == 0 && nrow(a) == 0) {
    return(fvp_empty_chart(
      "No data for this selection. Choose a series, at least one model, and a horizon."))
  }
  meta <- fvp_model_meta(series, df)

  ser_lbl <- if (is.null(series) || !nzchar(series)) "\u2014" else series
  # Date range across the actual line + every selected model forecast line.
  drange <- a$date
  for (m in models) {
    fr <- fvp_forecast_series(series, m, horizon_days, hist_days, df)
    drange <- c(drange, fr$date)
  }
  drange <- drange[!is.na(drange)]
  dr_txt <- if (length(drange)) {
    paste0(format(min(drange), "%Y-%m-%d"), " \u2192 ", format(max(drange), "%Y-%m-%d"))
  } else "\u2014"

  ttl <- "Backtest Comparison"
  sub <- paste0(ser_lbl, "  \u00b7  horizon ", as.integer(horizon_days),
                " days  \u00b7  ", length(models),
                if (length(models) == 1) " model" else " models",
                "  \u00b7  ", dr_txt)

  hc <- highcharter::highchart() |>
    highcharter::hc_chart(
      type = "line", zoomType = "x",
      panning = list(enabled = TRUE), panKey = "shift",
      style = list(fontFamily = "Inter, system-ui, sans-serif")) |>
    highcharter::hc_title(
      text = ttl,
      style = list(fontSize = "15px", fontWeight = "600", color = "#102a43")) |>
    highcharter::hc_subtitle(
      text = sub, style = list(fontSize = "12px", color = "#627d98")) |>
    highcharter::hc_xAxis(type = "datetime", title = list(text = NULL)) |>
    highcharter::hc_yAxis(title = list(text = "Value"), opposite = FALSE) |>
    highcharter::hc_legend(enabled = TRUE) |>
    highcharter::hc_tooltip(shared = FALSE, xDateFormat = "%Y-%m-%d",
                            valueDecimals = 2) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_plotOptions(
      line = list(marker = list(enabled = TRUE, radius = 3), lineWidth = 2))

  # Actual line (reserved blue, slightly heavier).
  if (nrow(a) > 0) {
    a_df <- data.frame(x = highcharter::datetime_to_timestamp(a$date),
                       y = round(a$value, 3))
    hc <- hc |> highcharter::hc_add_series(
      name = "Actual", type = "line", color = "#10477e", lineWidth = 3,
      marker = list(enabled = TRUE, radius = 3, symbol = "circle"),
      data = highcharter::list_parse2(a_df),
      tooltip = list(
        headerFormat = "",
        pointFormat = paste0(
          "<b>Actual</b><br/>{point.x:%Y-%m-%d}<br/>",
          "Actual value: <b>{point.y:.2f}</b>")))
  }

  # One forecast line per selected model (family-ordered for stable colors).
  ordered_models <- meta$model_name[meta$model_name %in% models]
  if (length(ordered_models) == 0) ordered_models <- models
  for (i in seq_along(ordered_models)) {
    m <- ordered_models[[i]]
    f <- fvp_forecast_series(series, m, horizon_days, hist_days, df)
    if (nrow(f) == 0) next
    mrow <- meta[meta$model_name == m, , drop = FALSE]
    fam  <- if (nrow(mrow)) mrow$model_family[[1]] else ""
    risk <- if (nrow(mrow)) mrow$risk_status[[1]] else ""
    champ <- if (nrow(mrow)) isTRUE(mrow$is_selected_champion[[1]]) else FALSE
    series_name <- fvp_model_label(m, champ, risk)
    col <- .fvp_palette[[((i - 1) %% length(.fvp_palette)) + 1]]
    dash <- if (identical(tolower(risk), "high_risk")) "ShortDash" else "Solid"
    f_df <- data.frame(x = highcharter::datetime_to_timestamp(f$date),
                       y = round(f$value, 3))
    hc <- hc |> highcharter::hc_add_series(
      name = series_name, type = "line", color = col, dashStyle = dash,
      data = highcharter::list_parse2(f_df),
      tooltip = list(
        headerFormat = "",
        pointFormat = paste0(
          "<b>", htmltools::htmlEscape(m), "</b><br/>",
          "{point.x:%Y-%m-%d}<br/>",
          "Forecast: <b>{point.y:.2f}</b><br/>",
          "Horizon: ", as.integer(horizon_days), " days<br/>",
          "Family: ", htmltools::htmlEscape(fam), "<br/>",
          "Risk: ", htmltools::htmlEscape(if (nzchar(risk)) risk else "ok"))))
  }
  hc
}

# Snapshot summary for the data-notes panel (Section 7). Read-only counts.
fvp_summary <- function(series, models, horizon_days = 5, hist_days = 0,
                        df = fvp_data()) {
  models <- models[!is.na(models) & nzchar(models)]
  a <- fvp_actual_series(series, hist_days, df)
  rows_used <- 0L
  dmin <- NA; dmax <- NA
  dates <- a$date
  for (m in models) {
    f <- fvp_forecast_series(series, m, horizon_days, hist_days, df)
    rows_used <- rows_used + nrow(f)
    dates <- c(dates, f$date)
  }
  dates <- dates[!is.na(dates)]
  if (length(dates)) { dmin <- min(dates); dmax <- max(dates) }
  list(
    series       = if (is.null(series) || !nzchar(series)) "\u2014" else series,
    n_models     = length(models),
    models       = models,
    horizon      = as.integer(horizon_days),
    n_actual     = nrow(a),
    rows_used    = rows_used,
    date_min     = if (is.na(dmin)) "\u2014" else format(dmin, "%Y-%m-%d"),
    date_max     = if (is.na(dmax)) "\u2014" else format(dmax, "%Y-%m-%d")
  )
}

# ===========================================================================
# Block 7.11-FULL-REBIND | Forecast Viewer FORWARD accessors (read-only)
# ---------------------------------------------------------------------------
# These read ONLY data/processed/actuals.csv (observed history) and
# data/processed/forecasts.csv (forward production forecast) via the governed
# loader cache. They NEVER generate forecasts, NEVER recompute metrics, NEVER
# run models, NEVER change the champion, and NEVER persist reshaped data.
#
# Artifact semantics: forecasts.csv is the FORWARD production forecast - a
# SINGLE selected model_version per series, with dates AFTER the last actual
# date. It is NOT a multi-model comparison and has NO horizon_days column.
# ===========================================================================

# Cached governed read of the forward production forecast (forecasts.csv).
fvf_forecasts <- function() {
  df <- tryCatch(load_csv_artifact("forecasts"), error = function(e) data.frame())
  if (!is.data.frame(df) || nrow(df) == 0) return(data.frame())
  for (col in c("entity_key", "model_version", "value_type")) {
    if (col %in% names(df)) df[[col]] <- trimws(as.character(df[[col]]))
  }
  df
}

# Cached governed read of observed actuals (actuals.csv).
fvf_actuals <- function() {
  df <- tryCatch(load_csv_artifact("actuals"), error = function(e) data.frame())
  if (!is.data.frame(df) || nrow(df) == 0) return(data.frame())
  if ("entity_key" %in% names(df)) df$entity_key <- trimws(as.character(df$entity_key))
  df
}

# All forward series (45). Union of forecast + actual entity keys, sorted.
fvf_series_choices <- function(fdf = fvf_forecasts(), adf = fvf_actuals()) {
  keys <- character(0)
  if (is.data.frame(fdf) && "entity_key" %in% names(fdf)) keys <- c(keys, fdf$entity_key)
  if (is.data.frame(adf) && "entity_key" %in% names(adf)) keys <- c(keys, adf$entity_key)
  keys <- keys[!is.na(keys) & nzchar(keys)]
  sort(unique(keys))
}

# The single forward model_version (production model) for a series.
fvf_model_version <- function(series, fdf = fvf_forecasts()) {
  if (is.null(series) || !nzchar(series) || !is.data.frame(fdf) || nrow(fdf) == 0 ||
      !all(c("entity_key", "model_version") %in% names(fdf))) return("\u2014")
  v <- unique(fdf$model_version[fdf$entity_key == series])
  v <- v[!is.na(v) & nzchar(v)]
  if (length(v) == 0) return("\u2014")
  paste(v, collapse = ", ")
}

# Last observed actual date for a series (the forecast-start boundary).
fvf_boundary_date <- function(series, adf = fvf_actuals()) {
  if (is.null(series) || !nzchar(series) || !is.data.frame(adf) || nrow(adf) == 0 ||
      !all(c("entity_key", "date") %in% names(adf))) return(as.Date(NA))
  d <- as.Date(adf$date[adf$entity_key == series])
  d <- d[!is.na(d)]
  if (length(d) == 0) return(as.Date(NA))
  max(d)
}

# Observed actual history for a series, trimmed to a trailing window (days).
# Aggregated to one point per date (mean) to avoid duplicate lines.
fvf_actual_history <- function(series, hist_days = 180, adf = fvf_actuals()) {
  empty <- data.frame(date = as.Date(character(0)), value = numeric(0))
  if (is.null(series) || !nzchar(series) || !is.data.frame(adf) || nrow(adf) == 0 ||
      !all(c("entity_key", "date", "actual_value") %in% names(adf))) return(empty)
  g <- adf[adf$entity_key == series, , drop = FALSE]
  if (nrow(g) == 0) return(empty)
  d <- as.Date(g$date)
  v <- suppressWarnings(as.numeric(g$actual_value))
  keep <- !is.na(d) & !is.na(v)
  if (!any(keep)) return(empty)
  agg <- stats::aggregate(list(value = v[keep]), list(date = d[keep]), FUN = mean)
  agg <- agg[order(agg$date), , drop = FALSE]
  if (!is.null(hist_days) && !is.na(hist_days) && hist_days > 0 && nrow(agg) > 0) {
    cutoff <- max(agg$date) - as.integer(hist_days)
    agg <- agg[agg$date >= cutoff, , drop = FALSE]
  }
  agg
}

# Forward forecast line for a series, limited to the next N days after the last
# actual. Aggregated to one point per date (mean). window_days <= 0 = full.
fvf_forecast_series <- function(series, window_days = 90, fdf = fvf_forecasts(),
                                adf = fvf_actuals()) {
  empty <- data.frame(date = as.Date(character(0)), value = numeric(0))
  if (is.null(series) || !nzchar(series) || !is.data.frame(fdf) || nrow(fdf) == 0 ||
      !all(c("entity_key", "date", "forecast_value") %in% names(fdf))) return(empty)
  g <- fdf[fdf$entity_key == series, , drop = FALSE]
  if (nrow(g) == 0) return(empty)
  d <- as.Date(g$date)
  v <- suppressWarnings(as.numeric(g$forecast_value))
  keep <- !is.na(d) & !is.na(v)
  if (!any(keep)) return(empty)
  agg <- stats::aggregate(list(value = v[keep]), list(date = d[keep]), FUN = mean)
  agg <- agg[order(agg$date), , drop = FALSE]
  # Keep only future rows (strictly after the last actual date), if known.
  bnd <- fvf_boundary_date(series, adf)
  if (!is.na(bnd)) agg <- agg[agg$date > bnd, , drop = FALSE]
  if (!is.null(window_days) && !is.na(window_days) && window_days > 0 && nrow(agg) > 0) {
    start <- min(agg$date)
    agg <- agg[agg$date <= start + as.integer(window_days), , drop = FALSE]
  }
  agg
}

# Calm empty-state chart for the forward section (static container initial state).
fvf_empty_chart <- function(
    msg = "Select a series and windows, then click Analyze Forward Forecast.") {
  highcharter::highchart() |>
    highcharter::hc_title(text = msg,
                          style = list(fontSize = "13px", color = "#0f766e",
                                       fontWeight = "500")) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_xAxis(visible = FALSE) |>
    highcharter::hc_yAxis(visible = FALSE) |>
    highcharter::hc_chart(
      style = list(fontFamily = "Inter, system-ui, sans-serif"))
}

# Forward forecast chart: observed actual history (solid) up to the last actual
# date, then the single production forecast line (dashed) after a labelled
# "Forecast start" vertical boundary.
fvf_chart <- function(series, fwd_window = 90, hist_window = 180,
                      fdf = fvf_forecasts(), adf = fvf_actuals()) {
  a <- fvf_actual_history(series, hist_window, adf)
  f <- fvf_forecast_series(series, fwd_window, fdf, adf)
  if (nrow(a) == 0 && nrow(f) == 0) {
    return(fvf_empty_chart(
      "No actual history or forward forecast was found for this series."))
  }
  bnd <- fvf_boundary_date(series, adf)
  mver <- fvf_model_version(series, fdf)
  ser_lbl <- if (is.null(series) || !nzchar(series)) "\u2014" else series

  drange <- c(a$date, f$date); drange <- drange[!is.na(drange)]
  dr_txt <- if (length(drange)) {
    paste0(format(min(drange), "%Y-%m-%d"), " \u2192 ", format(max(drange), "%Y-%m-%d"))
  } else "\u2014"
  sub <- paste0(ser_lbl, "  \u00b7  model ", mver,
                "  \u00b7  forward production forecast  \u00b7  ", dr_txt)

  bnd_ts <- if (!is.na(bnd)) highcharter::datetime_to_timestamp(bnd) else NULL

  hc <- highcharter::highchart() |>
    highcharter::hc_chart(
      type = "line", zoomType = "x",
      panning = list(enabled = TRUE), panKey = "shift",
      style = list(fontFamily = "Inter, system-ui, sans-serif")) |>
    highcharter::hc_title(
      text = "Forward Forecast",
      style = list(fontSize = "15px", fontWeight = "600", color = "#0b3d2e")) |>
    highcharter::hc_subtitle(
      text = sub, style = list(fontSize = "12px", color = "#3f7d6c")) |>
    highcharter::hc_yAxis(title = list(text = "Value"), opposite = FALSE) |>
    highcharter::hc_legend(enabled = TRUE) |>
    highcharter::hc_tooltip(shared = FALSE, xDateFormat = "%Y-%m-%d",
                            valueDecimals = 2) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_plotOptions(
      line = list(marker = list(enabled = FALSE), lineWidth = 2))

  # X axis with the "Forecast start" boundary plotLine.
  if (!is.null(bnd_ts)) {
    hc <- hc |> highcharter::hc_xAxis(
      type = "datetime", title = list(text = NULL),
      plotLines = list(list(
        value = bnd_ts, color = "#0f766e", width = 2, dashStyle = "Dash",
        zIndex = 5,
        label = list(text = "Forecast start",
                     style = list(color = "#0f766e", fontWeight = "600",
                                  fontSize = "11px")))))
  } else {
    hc <- hc |> highcharter::hc_xAxis(type = "datetime", title = list(text = NULL))
  }

  if (nrow(a) > 0) {
    a_df <- data.frame(x = highcharter::datetime_to_timestamp(a$date),
                       y = round(a$value, 3))
    hc <- hc |> highcharter::hc_add_series(
      name = "Actual history", type = "line", color = "#10477e", lineWidth = 2.5,
      data = highcharter::list_parse2(a_df),
      tooltip = list(headerFormat = "",
                     pointFormat = paste0("<b>Actual</b><br/>{point.x:%Y-%m-%d}<br/>",
                                          "Value: <b>{point.y:.2f}</b>")))
  }
  if (nrow(f) > 0) {
    f_df <- data.frame(x = highcharter::datetime_to_timestamp(f$date),
                       y = round(f$value, 3))
    hc <- hc |> highcharter::hc_add_series(
      name = "Forward forecast", type = "line", color = "#0f9d6e",
      dashStyle = "ShortDash", lineWidth = 2.5,
      data = highcharter::list_parse2(f_df),
      tooltip = list(headerFormat = "",
                     pointFormat = paste0(
                       "<b>Forward forecast</b><br/>{point.x:%Y-%m-%d}<br/>",
                       "Value: <b>{point.y:.2f}</b><br/>",
                       "Model: ", htmltools::htmlEscape(mver))))
  }
  hc
}

# Snapshot summary for the forward data-notes panel. Read-only counts.
fvf_summary <- function(series, fwd_window = 90, hist_window = 180,
                        fdf = fvf_forecasts(), adf = fvf_actuals()) {
  a <- fvf_actual_history(series, hist_window, adf)
  f <- fvf_forecast_series(series, fwd_window, fdf, adf)
  bnd <- fvf_boundary_date(series, adf)
  dr <- c(a$date, f$date); dr <- dr[!is.na(dr)]
  list(
    series        = if (is.null(series) || !nzchar(series)) "\u2014" else series,
    model_version = fvf_model_version(series, fdf),
    n_actual      = nrow(a),
    n_forecast    = nrow(f),
    boundary      = if (is.na(bnd)) "\u2014" else format(bnd, "%Y-%m-%d"),
    date_min      = if (length(dr)) format(min(dr), "%Y-%m-%d") else "\u2014",
    date_max      = if (length(dr)) format(max(dr), "%Y-%m-%d") else "\u2014",
    fwd_first     = if (nrow(f)) format(min(f$date), "%Y-%m-%d") else "\u2014",
    fwd_last      = if (nrow(f)) format(max(f$date), "%Y-%m-%d") else "\u2014"
  )
}
