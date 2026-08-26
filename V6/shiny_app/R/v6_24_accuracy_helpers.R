# TESSERACT v2 | v6_24_accuracy_helpers.R
# V6.24-P9H | Accuracy diagnostics for the V6.24 MVP.
#
# CONTRACT
#   Accuracy values are READ from accuracy_metrics.parquet. This file never
#   computes MAE, RMSE, WAPE, SMAPE, MAPE or bias from backtest rows. The only
#   number it derives is a standardized severity score used for HEATMAP COLOUR
#   ONLY, and that score is stamped VISUALIZATION_ONLY everywhere it appears.
#
#   TWO DIFFERENCES FROM THE LEGACY ACCURACY PAGE, both deliberate:
#
#   1. NO HORIZON AXIS. The legacy artifact v6_21b_accuracy_metrics.parquet
#      carries a `horizon` column, which is why the legacy page offers a
#      5/10/15/20/25/30 selector. The V6.24 artifact does NOT: it is exactly
#      2,100 rows = 140 series x 15 models, one row each, aggregating every
#      horizon 1..30 across the full D2 window. Offering a horizon filter here
#      would show six identical result sets, so the horizon is presented as
#      DISCLOSED CONTEXT instead of a control.
#
#   2. MEDIAN, NOT MEAN, to rank series. The legacy heatmap ranks series
#      worst-first by mean(metric_value). On this cohort the mean is unusable:
#      LinearRegression has mean MAE 5.86e21 against a median of 870, and the
#      worst-five list by mean overlaps the median list by only 2 of 5. P6/P7
#      already established medians as the governed aggregate statistic.

# Metric labels offered by the page, each mapped to a governed column and to
# the status column that says whether the value may be read at all.
V6_24_ACC_METRICS <- list(
  list(label = "MAE",                   col = "mae",   status = NULL),
  list(label = "RMSE",                  col = "rmse",  status = NULL),
  list(label = "WAPE",                  col = "wape",  status = "wape_status"),
  list(label = "SMAPE",                 col = "smape", status = "smape_status"),
  list(label = "MAPE",                  col = "mape",  status = "mape_status"),
  list(label = "Median absolute error", col = "median_absolute_error", status = NULL),
  list(label = "Absolute bias",         col = "bias",  status = NULL)
)

V6_24_ACC_METRIC_LABELS <- vapply(V6_24_ACC_METRICS, function(m) m$label, character(1))

# The horizons the legacy page offered. Kept ONLY so the page can show them as
# unavailable and say why, mirroring the struck-through 35/45 pattern from P9D.
V6_24_ACC_LEGACY_HORIZONS <- c(5, 10, 15, 20, 25, 30)

V6_24_ACC_WINDOW_NOTE <- paste(
  "Backtest accuracy window: governed aggregate over horizons 1-30.",
  "The accuracy_metrics artifact holds one row per series x model and does",
  "not expose separate 5/10/15/20/25/30 accuracy rows.")

V6_24_SEVERITY_STAMP <- "VISUALIZATION_ONLY"

#' Look up the metric definition for a label.
v6_24_acc_metric_def <- function(label) {
  for (m in V6_24_ACC_METRICS) if (identical(m$label, label)) return(m)
  V6_24_ACC_METRICS[[1]]
}

#' Robust standardized severity: (x - median) / IQR.
#'
#' Same shape as the legacy acc_standardize(), with the same fallbacks: a
#' z-score when IQR is zero but sd is not, and zeros when the values are
#' constant. This is a DISPLAY score. It never enters a ranking, a champion
#' decision or any governed field.
#'
#' Non-finite inputs return NA rather than 0, so a cell with no computable
#' metric stays visibly empty instead of masquerading as an average case.
v6_24_acc_severity <- function(x) {
  x <- suppressWarnings(as.numeric(x))
  v <- x[is.finite(x)]
  if (!length(v)) return(rep(NA_real_, length(x)))
  iqr <- stats::IQR(v, na.rm = TRUE)
  if (is.finite(iqr) && iqr > 0) {
    z <- (x - stats::median(v)) / iqr
  } else {
    s <- stats::sd(v)
    z <- if (is.finite(s) && s > 0) (x - mean(v)) / s else rep(0, length(x))
  }
  z[!is.finite(z)] <- NA_real_
  z
}

#' Which standardization branch was taken, for the validation report.
v6_24_acc_severity_method <- function(x) {
  v <- suppressWarnings(as.numeric(x)); v <- v[is.finite(v)]
  if (!length(v)) return("none")
  if (is.finite(stats::IQR(v)) && stats::IQR(v) > 0) return("median_iqr")
  if (is.finite(stats::sd(v)) && stats::sd(v) > 0) return("zscore")
  "constant"
}

#' Format a metric value so an extreme number stays readable.
#'
#' The cohort holds values up to 8.2e23. Printing that at fixed precision makes
#' a table unreadable, and rounding it hides it. Anything at or above 1e6 is
#' shown in scientific notation and is separately flagged as extreme.
v6_24_acc_fmt <- function(x, digits = 4) {
  v <- suppressWarnings(as.numeric(x))
  if (length(v) != 1) return(vapply(v, v6_24_acc_fmt, character(1), digits = digits))
  if (is.na(v)) return("not computable")
  if (!is.finite(v)) return("not finite")
  if (v != 0 && (abs(v) >= 1e6 || abs(v) < 1e-4)) {
    return(format(v, scientific = TRUE, digits = 3))
  }
  format(round(v, digits), big.mark = ",", trim = TRUE, scientific = FALSE)
}

V6_24_ACC_EXTREME_THRESHOLD <- 1e6

#' Accuracy rows for ONE selected series.
#'
#' The Accuracy page is scoped to the series chosen in the Viewer - the same
#' shared selection that drives Forecast - so this returns the 15 governed model
#' rows for that series and nothing else. There is no cohort-wide Top-N view:
#' accuracy answers "how did the models do on THIS series".
#'
#' FILTER ONLY. Every metric column is carried straight from accuracy_metrics.
v6_24_acc_rows <- function(metric_label = "MAE", models = NULL,
                           series_ids = NULL) {
  ac <- v6_24_tbl("accuracy_metrics")
  if (is.null(ac) || !nrow(ac)) return(NULL)
  d <- ac
  if (!is.null(models) && length(models)) {
    d <- d[as.character(d$model_name) %in% models, , drop = FALSE]
  }
  if (!is.null(series_ids) && length(series_ids)) {
    d <- d[as.character(d$series_id) %in% series_ids, , drop = FALSE]
  }
  if (!nrow(d)) return(d)

  def <- v6_24_acc_metric_def(metric_label)
  val <- suppressWarnings(as.numeric(d[[def$col]]))
  # Absolute bias: the artifact carries signed bias; the page ranks severity,
  # so the magnitude is what is compared. The sign stays in its own column.
  if (identical(def$col, "bias")) val <- abs(val)
  d$metric_value <- val
  d$metric_status <- if (is.null(def$status)) {
    ifelse(is.finite(val), "COMPUTED", "NOT_FINITE")
  } else {
    as.character(d[[def$status]])
  }
  # A status of anything other than COMPUTED means the metric may not be read
  # for this row. Blank the value rather than carry a number the artifact
  # declared meaningless.
  d$metric_value[d$metric_status != "COMPUTED"] <- NA_real_
  d$severity <- v6_24_acc_severity(d$metric_value)
  d$is_extreme <- is.finite(d$metric_value) &
    abs(d$metric_value) >= V6_24_ACC_EXTREME_THRESHOLD

  # Display label per series, resolved through navigation_contract so the
  # heatmap rows read as routes rather than raw ids. The no-signal flag comes
  # along because a zero-actual series produces a degenerate MAE of exactly 0
  # that would otherwise win the "most favourable" card.
  nav <- v6_24_tbl("nav_contract")
  lk <- stats::setNames(as.character(nav$route_display_label),
                        as.character(nav$series_id))
  lab <- unname(lk[as.character(d$series_id)])
  d$display_label <- ifelse(is.na(lab), as.character(d$series_id), lab)
  nz <- stats::setNames(toupper(as.character(nav$no_signal_flag)),
                        as.character(nav$series_id))
  d$no_signal <- unname(nz[as.character(d$series_id)]) %in% "TRUE"
  d
}

#' Summary values for the selected series.
#'
#' Best and worst are MODELS on this series, ranked by the selected metric.
#' Rows whose metric the artifact declared non-computable are excluded.
#'
#' A NO-SIGNAL SERIES GETS NO WINNER. All 195 rows in this cohort with an error
#' of exactly 0 belong to the 15 all-zero series: the model predicted zero
#' against an actual of zero. That is a degenerate identity, not performance, so
#' on such a series no model is presented as best - the same gate P6C applied to
#' the champion, and the same one the Viewer and Forecast pages already honour.
v6_24_acc_summary <- function(rows, metric_label, models_requested = NULL) {
  base <- list(n_models = 0L, n_rows = 0L, metric = metric_label,
               series_label = "\u2014", best = "\u2014", worst = "\u2014",
               best_value = NA_real_, worst_value = NA_real_,
               excluded = 0L, extreme = 0L, no_signal = FALSE,
               target_dates = NA_integer_, severity_method = "none",
               champion = "", champion_visible = FALSE)
  if (is.null(rows) || !nrow(rows)) return(base)
  computable <- is.finite(rows$metric_value)
  no_sig <- any(rows$no_signal %in% TRUE)
  ok <- rows[computable, , drop = FALSE]

  sid <- as.character(rows$series_id[1])
  ch <- tryCatch(v6_24_champion(sid),
                 error = function(e) list(model = "", meaningful = FALSE))

  out <- list(
    n_models = length(unique(as.character(rows$model_name))),
    n_rows = nrow(rows),
    metric = metric_label,
    series_label = as.character(rows$display_label[1]),
    excluded = sum(!computable),
    extreme = sum(rows$is_extreme, na.rm = TRUE),
    no_signal = no_sig,
    target_dates = suppressWarnings(as.integer(rows$n_target_dates[1])),
    severity_method = v6_24_acc_severity_method(rows$metric_value),
    champion = ch$model, champion_visible = isTRUE(ch$meaningful),
    best = "\u2014", worst = "\u2014",
    best_value = NA_real_, worst_value = NA_real_)

  if (nrow(ok) && !no_sig) {
    bi <- which.min(ok$metric_value)
    wi <- which.max(ok$metric_value)
    out$best <- as.character(ok$model_name[bi])
    out$worst <- as.character(ok$model_name[wi])
    out$best_value <- ok$metric_value[bi]
    out$worst_value <- ok$metric_value[wi]
  } else if (nrow(ok) && no_sig) {
    # Still report the spread so the page is not blank, but never as a winner.
    out$best <- "not meaningful \u2014 no signal"
    out$worst <- "not meaningful \u2014 no signal"
  }
  out
}

#' Rank the models of the selected series, best-first by the chosen metric.
v6_24_acc_model_order <- function(rows) {
  if (is.null(rows) || !nrow(rows)) return(character(0))
  ok <- rows[is.finite(rows$metric_value), , drop = FALSE]
  if (!nrow(ok)) {
    return(V6_24_GOVERNED_MODELS[
      V6_24_GOVERNED_MODELS %in% unique(as.character(rows$model_name))])
  }
  as.character(ok$model_name[order(ok$metric_value)])
}

#' Highcharter severity heatmap for ONE series: models x metrics.
#'
#' With a single selected series a series-by-model grid would be one row, so the
#' grid is transposed into something that actually informs the decision: each
#' row is a governed model, each column a governed measure, and colour is that
#' model's severity WITHIN that measure across the models of this series. That
#' shows at a glance which model is weak on which kind of error - a model can
#' look fine on MAE and terrible on WAPE.
#'
#' Severity is standardized per COLUMN, because MAE and SMAPE do not share a
#' scale and standardizing across the whole matrix would be meaningless.
v6_24_acc_heatmap <- function(rows, metric_label = "MAE", cap = 3) {
  if (is.null(rows) || !nrow(rows)) {
    return(v6_24_hc_empty(paste("Select a series in the Viewer, then click",
                                "Analyze Accuracy.")))
  }
  models <- v6_24_acc_model_order(rows)
  if (!length(models)) return(v6_24_hc_empty("No governed models for this series."))

  # Columns: every governed measure the artifact carries, so the map compares
  # kinds of error rather than repeating one number.
  cols <- V6_24_ACC_METRICS
  col_labels <- vapply(cols, function(m) m$label, character(1))

  # Build the value matrix first: rows = models, cols = measures.
  vals <- matrix(NA_real_, nrow = length(models), ncol = length(cols))
  stat <- matrix("COMPUTED", nrow = length(models), ncol = length(cols))
  ri <- stats::setNames(seq_along(models), models)
  for (j in seq_along(cols)) {
    def <- cols[[j]]
    v <- suppressWarnings(as.numeric(rows[[def$col]]))
    if (identical(def$col, "bias")) v <- abs(v)
    st <- if (is.null(def$status)) ifelse(is.finite(v), "COMPUTED", "NOT_FINITE")
          else as.character(rows[[def$status]])
    v[st != "COMPUTED"] <- NA_real_
    for (i in seq_len(nrow(rows))) {
      k <- ri[[as.character(rows$model_name[i])]]
      if (is.null(k)) next
      vals[k, j] <- v[i]
      stat[k, j] <- st[i]
    }
  }
  # Standardize DOWN each column: severity is relative to the other models of
  # this same series on this same measure.
  sev <- vals
  for (j in seq_len(ncol(vals))) sev[, j] <- v6_24_acc_severity(vals[, j])

  pts <- list(); n <- 0L
  for (i in seq_along(models)) {
    for (j in seq_along(cols)) {
      s <- sev[i, j]
      n <- n + 1L
      pts[[n]] <- list(
        x = j - 1L, y = i - 1L,
        value = if (is.na(s)) NULL else max(min(s, cap), -cap),
        raw = v6_24_acc_fmt(vals[i, j]),
        sev = if (is.na(s)) "not computable" else v6_24_acc_fmt(s, 2),
        status = stat[i, j],
        measure = col_labels[[j]],
        model = models[[i]])
    }
  }

  sub <- paste0(length(models),
                if (length(models) == 1) " model" else " models",
                "  \u00b7  ", length(cols), " governed measures  \u00b7  ",
                "ordered best-first by ", metric_label,
                "  \u00b7  severity standardized within each measure")

  hc <- highcharter::highchart() |>
    highcharter::hc_chart(type = "heatmap",
                          style = list(fontFamily = V6_24_CHART_FONT)) |>
    highcharter::hc_title(
      text = "Model accuracy severity",
      style = list(fontSize = "15px", fontWeight = "600", color = "#102a43")) |>
    highcharter::hc_subtitle(
      text = sub, style = list(fontSize = "12px", color = "#627d98")) |>
    highcharter::hc_xAxis(categories = as.list(col_labels), opposite = TRUE,
                          title = list(text = NULL),
                          labels = list(style = list(fontSize = "11px"))) |>
    highcharter::hc_yAxis(categories = as.list(models), reversed = TRUE,
                          title = list(text = NULL),
                          labels = list(style = list(fontSize = "11px"))) |>
    highcharter::hc_colorAxis(
      min = -cap, max = cap, stops = list(
        list(0, "#2c7bb6"), list(0.5, "#ffffbf"), list(1, "#d7191c"))) |>
    highcharter::hc_legend(enabled = TRUE, align = "right",
                           layout = "vertical", verticalAlign = "middle",
                           title = list(text = "Severity")) |>
    highcharter::hc_tooltip(
      useHTML = TRUE, headerFormat = "",
      pointFormat = paste0(
        "<b>{point.model}</b><br/>",
        "{point.measure} (raw): <b>{point.raw}</b><br/>",
        "Severity vs other models: {point.sev}<br/>",
        "Status: {point.status}")) |>
    highcharter::hc_exporting(enabled = TRUE) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_add_series(
      name = "Severity", type = "heatmap", data = pts,
      borderWidth = 1, borderColor = "#ffffff", nullColor = "#eef2f6",
      dataLabels = list(enabled = FALSE))

  # Highcharts serves heatmap from a separate module. highcharter does not ship
  # it in the default dependency set, so without this the series type resolves
  # through modules/map.js and the chart dies in updateParallelArrays.
  highcharter::hc_add_dependency(hc, "modules/heatmap.js")
}

#' DT metric table for the selected series: one row per governed model.
v6_24_acc_table <- function(rows, metric_label = "MAE") {
  if (is.null(rows) || !nrow(rows)) return(v6_24_dt(NULL))
  # Best-first by the selected metric; non-computable rows sink to the bottom.
  d <- rows[order(rows$metric_value, na.last = TRUE), , drop = FALSE]
  fam <- vapply(as.character(d$model_name), function(m) {
    k <- V6_24_DISPLAY_FAMILY[[m]]
    if (is.null(k)) "\u2014" else unname(V6_24_FAMILY_LABEL[[k]])
  }, character(1), USE.NAMES = FALSE)
  ch <- tryCatch(v6_24_champion(as.character(d$series_id[1])),
                 error = function(e) list(model = "", meaningful = FALSE))
  mark <- ifelse(
    as.character(d$model_name) == ch$model,
    if (isTRUE(ch$meaningful)) v6_24_cell_badge("\u2605 champion", "gold")
    else v6_24_cell_badge("technical only", "slate"), "")
  flag <- ifelse(d$no_signal %in% TRUE,
                 v6_24_cell_badge("no signal", "slate"),
                 ifelse(d$is_extreme %in% TRUE,
                        v6_24_cell_badge("extreme", "warn"),
                        ifelse(d$metric_status != "COMPUTED",
                               v6_24_cell_badge("not computable", "slate"), "")))
  out <- data.frame(
    Rank = ifelse(is.finite(d$metric_value), seq_len(nrow(d)), NA_integer_),
    Model = as.character(d$model_name),
    Family = fam,
    `Selected metric` = vapply(d$metric_value, v6_24_acc_fmt, character(1)),
    MAE = vapply(d$mae, v6_24_acc_fmt, character(1)),
    RMSE = vapply(d$rmse, v6_24_acc_fmt, character(1)),
    WAPE = ifelse(as.character(d$wape_status) == "COMPUTED",
                  vapply(d$wape, v6_24_acc_fmt, character(1)), "not computable"),
    SMAPE = ifelse(as.character(d$smape_status) == "COMPUTED",
                   vapply(d$smape, v6_24_acc_fmt, character(1)), "not computable"),
    `Signed bias` = vapply(d$bias, v6_24_acc_fmt, character(1)),
    `Target dates` = as.integer(d$n_target_dates),
    Champion = mark,
    Status = flag,
    check.names = FALSE, stringsAsFactors = FALSE)
  v6_24_dt(out, page_length = 15L, paging = FALSE, searching = FALSE)
}
