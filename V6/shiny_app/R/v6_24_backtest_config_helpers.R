# TESSERACT v2 | v6_24_backtest_config_helpers.R
# V6.24-P9D | Backtest Configuration for the V6.24 MVP Viewer.
#
# CONTRACT
#   Configuration FILTERS prepared rows. It never recomputes accuracy, never
#   regenerates a backtest, and never invents a horizon. Every value shown is
#   read from a governed artifact.
#
#   Champion visibility is read from navigation_contract.champion_visible, so a
#   no-signal series can never gain a star or a "winner" label. No series name
#   and no model name is hardcoded as a special case.

# The 15 governed models, in governed spelling. "ETS Explicit" carries a space:
# it is a registry name, not a display string, and must never be normalised.
V6_24_GOVERNED_MODELS <- c(
  "FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
  "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
  "LightGBM", "LinearRegression", "XGBoost",
  "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"
)

# DISPLAY-ONLY family map.
#
# The governed artifacts carry a three-value model_family (Baseline / Challenger
# / Neural) whose partition CUTS ACROSS the four families the product displays -
# ETS Explicit is a Challenger but is shown under Statistical, LinearRegression
# is a Baseline but is shown under Machine Learning. So the four-family split
# cannot be derived from accuracy_metrics.
#
# It is taken from the legacy display source
# data/processed/forecast_viewer_model_outputs.csv, which classifies the exact
# same 15 model names. That file is 49 MB, so the validated result is embedded
# here rather than parsed at every startup; v6_24_validate_family_map() re-checks
# it against the source on demand.
#
# THIS MAP IS FOR GROUPING CHECKBOXES ONLY. It is never used for rankings,
# accuracy, forecast generation, champion selection or any governance decision.
V6_24_FAMILY_ORDER <- c("growth_baseline", "statistical",
                        "machine_learning", "lightweight_neural")
V6_24_FAMILY_LABEL <- c(
  growth_baseline    = "Growth Baseline",
  statistical        = "Statistical",
  machine_learning   = "Machine Learning",
  lightweight_neural = "Deep Learning"
)
V6_24_DISPLAY_FAMILY <- c(
  FixedGrowth_1_5    = "growth_baseline",
  FixedGrowth_3      = "growth_baseline",
  FixedGrowth_4      = "growth_baseline",
  FixedGrowth_6      = "growth_baseline",
  ARIMA_Fixed        = "statistical",
  AutoARIMA          = "statistical",
  `ETS Explicit`     = "statistical",
  ETS_Current        = "statistical",
  Theta              = "statistical",
  LightGBM           = "machine_learning",
  LinearRegression   = "machine_learning",
  XGBoost            = "machine_learning",
  `FNAR-V2`          = "lightweight_neural",
  `NLIN-DLIN_FIXED`  = "lightweight_neural",
  `SMLP-TCN`         = "lightweight_neural"
)

V6_24_FAMILY_MAP_SOURCE <- "data/processed/forecast_viewer_model_outputs.csv"
V6_24_FAMILY_MAP_USE <- "DISPLAY_GROUPING_ONLY"

# Horizons the product offers, and the ones it must show as unavailable.
V6_24_HORIZON_CHOICES <- c(5, 10, 15, 20, 25, 30)
V6_24_HORIZON_UNAVAILABLE <- c(35, 45)
V6_24_HORIZON_NOTE <- "Prepared artifact covers 1-30 day horizons."

# Governance reference model, used when no champion may be presented.
V6_24_REFERENCE_MODEL <- "ETS Explicit"

#' Validate the display family map against the governed model list, and against
#' the legacy source when it is available.
v6_24_validate_family_map <- function(check_source = TRUE) {
  mapped <- names(V6_24_DISPLAY_FAMILY)
  out <- list(
    governed_n = length(V6_24_GOVERNED_MODELS),
    mapped_n = length(mapped),
    missing = setdiff(V6_24_GOVERNED_MODELS, mapped),
    extra = setdiff(mapped, V6_24_GOVERNED_MODELS),
    families = unname(V6_24_FAMILY_ORDER),
    counts = table(factor(unname(V6_24_DISPLAY_FAMILY),
                          levels = V6_24_FAMILY_ORDER)),
    source_checked = FALSE, source_agrees = NA, source_note = "")
  out$ok <- length(out$missing) == 0 && length(out$extra) == 0 &&
    sum(out$counts) == length(V6_24_GOVERNED_MODELS)

  if (isTRUE(check_source)) {
    p <- file.path("..", V6_24_FAMILY_MAP_SOURCE)
    if (!file.exists(p)) {
      out$source_note <- "legacy display source not present; embedded map used"
      return(out)
    }
    ref <- tryCatch({
      d <- utils::read.csv(p, stringsAsFactors = FALSE,
                           colClasses = c("model_name" = "character",
                                          "model_family" = "character"),
                           nrows = 200000)
      d <- unique(d[, c("model_name", "model_family")])
      stats::setNames(trimws(d$model_family), trimws(d$model_name))
    }, error = function(e) NULL)
    if (is.null(ref)) {
      out$source_note <- "legacy display source unreadable; embedded map used"
      return(out)
    }
    out$source_checked <- TRUE
    same <- vapply(V6_24_GOVERNED_MODELS, function(m) {
      identical(unname(ref[[m]]), unname(V6_24_DISPLAY_FAMILY[[m]]))
    }, logical(1))
    out$source_agrees <- all(same)
    out$source_note <- if (all(same)) "embedded map matches the legacy source"
                       else paste("DISAGREES for:",
                                  paste(names(same)[!same], collapse = ", "))
    out$ok <- out$ok && all(same)
  }
  out
}

#' Models grouped for display, in governed family order.
v6_24_family_groups <- function() {
  lapply(V6_24_FAMILY_ORDER, function(f) {
    list(family = f, label = unname(V6_24_FAMILY_LABEL[[f]]),
         models = names(V6_24_DISPLAY_FAMILY)[V6_24_DISPLAY_FAMILY == f])
  })
}

#' Backtest availability for one series.
#'
#' A caveat is NOT unavailability. A no-signal or low-confidence series still has
#' prepared backtest rows and stays fully analysable.
v6_24_backtest_availability <- function(series_id) {
  empty <- list(available = FALSE, rows = 0L, models = 0L, horizons = integer(0),
                min_date = "", max_date = "",
                message = "No series selected yet.",
                status = "NO_SELECTION")
  if (is.null(series_id) || !nzchar(series_id)) return(empty)
  bt <- v6_24_tbl("backtests")
  if (!nrow(bt)) {
    return(modifyList(empty, list(
      message = "The prepared backtest artifact is not loaded.",
      status = "ARTIFACT_MISSING")))
  }
  g <- bt[as.character(bt$series_id) == series_id, , drop = FALSE]
  if (!nrow(g)) {
    return(modifyList(empty, list(
      message = "Backtest not available for this selected series.",
      status = "NOT_AVAILABLE")))
  }
  hz <- sort(unique(as.integer(g$horizon_steps)))
  list(
    available = TRUE,
    rows = nrow(g),
    models = length(unique(as.character(g$model_name))),
    horizons = hz,
    # P9E | UTC-safe: target_date is a midnight-UTC timestamp, so as.character()
    # would shift the governed day in a negative-offset server timezone.
    min_date = format(v6_24_as_date(min(g$target_date)), "%Y-%m-%d"),
    max_date = format(v6_24_as_date(max(g$target_date)), "%Y-%m-%d"),
    message = paste("Prepared actual and", length(unique(g$model_name)),
                    "model backtest rows are available for this selected series."),
    status = "AVAILABLE")
}

#' Offered horizons for a series: the product list intersected with what the
#' artifact actually carries. Never extrapolated.
v6_24_available_horizons <- function(series_id) {
  av <- v6_24_backtest_availability(series_id)
  if (!isTRUE(av$available)) return(integer(0))
  intersect(V6_24_HORIZON_CHOICES, av$horizons)
}

v6_24_default_horizon <- function(series_id) {
  h <- v6_24_available_horizons(series_id)
  if (!length(h)) return(NA_integer_)
  if (5 %in% h) 5L else as.integer(min(h))
}

#' Champion for a series, honouring champion_visible.
#'
#' Returns the model name and whether it may be PRESENTED as a winner. When
#' champion_visible is FALSE the name is still returned for technical display,
#' but `meaningful` is FALSE and no star may be drawn.
v6_24_champion <- function(series_id) {
  out <- list(model = "", meaningful = FALSE, validity = "", reason = "",
              rank_metric = "", rank_value = NA_real_)
  r <- v6_24_nav_row(series_id)
  if (is.null(r)) return(out)
  list(
    model = as.character(r$champion_model_name[1]),
    meaningful = identical(as.character(r$champion_visible[1]), "TRUE"),
    validity = as.character(r$champion_validity[1]),
    reason = as.character(r$champion_reason[1]),
    rank_metric = as.character(r$champion_rank_metric[1]),
    rank_value = suppressWarnings(as.numeric(r$champion_rank_value[1])))
}

#' Default model selection for a series.
#'
#' Around five or six models, never all fifteen. When a champion may be
#' presented it leads the set; when it may not, the governance reference model
#' leads instead and nothing is labelled a winner.
v6_24_default_models <- function(series_id) {
  ch <- v6_24_champion(series_id)
  comparators <- c("FixedGrowth_3", "LightGBM", "XGBoost", "SMLP-TCN")
  base <- if (isTRUE(ch$meaningful) && nzchar(ch$model)) {
    c(ch$model, V6_24_REFERENCE_MODEL, comparators)
  } else {
    c(V6_24_REFERENCE_MODEL, comparators)
  }
  out <- unique(base[base %in% V6_24_GOVERNED_MODELS])
  out <- utils::head(out, 6L)
  # Only offer models the artifact actually has for this series.
  present <- v6_24_models_for_series(series_id)
  if (length(present)) out <- out[out %in% present]
  if (!length(out)) out <- utils::head(present, 1L)
  out
}

#' Governed models present in the backtest artifact for a series.
v6_24_models_for_series <- function(series_id) {
  if (is.null(series_id) || !nzchar(series_id)) return(character(0))
  bt <- v6_24_tbl("backtests")
  if (!nrow(bt)) return(character(0))
  m <- unique(as.character(bt[as.character(bt$series_id) == series_id,
                              "model_name"]))
  V6_24_GOVERNED_MODELS[V6_24_GOVERNED_MODELS %in% m]
}

#' Checkbox label for one model. The star is drawn only when the champion may be
#' presented as a recommendation.
v6_24_model_label <- function(model, champion) {
  if (isTRUE(champion$meaningful) && identical(model, champion$model)) {
    return(paste0(model, "  \u2605 champion"))
  }
  model
}

#' Filter prepared backtest rows for the applied configuration.
#'
#' Horizon uses EQUALITY on horizon_steps, matching the legacy viewer, which
#' compares models at one horizon rather than mixing several. Nothing is
#' recomputed and no row is created.
v6_24_backtest_rows <- function(series_id, models, horizon) {
  bt <- v6_24_tbl("backtests")
  if (!nrow(bt) || is.null(series_id) || !nzchar(series_id) ||
      is.null(models) || !length(models)) {
    return(bt[0, , drop = FALSE])
  }
  g <- bt[as.character(bt$series_id) == series_id &
            as.character(bt$model_name) %in% models, , drop = FALSE]
  if (!is.null(horizon) && !is.na(horizon)) {
    g <- g[as.integer(g$horizon_steps) == as.integer(horizon), , drop = FALSE]
  }
  g
}
