# TESSERACT v2 | v6_24_viz_helpers.R
# V6.24-P9E | Visualization parity: Highcharter charts and DT tables.
#
# CONTRACT
#   Every value drawn here is READ from a governed artifact. This file does not
#   compute, interpolate, smooth, resample, clip or impute anything. A gap in
#   the data stays a gap; a negative forecast stays negative.
#
#   Highcharts is the product chart library (the legacy Forecasting section uses
#   it through fvp_chart/fvf_chart in R/helpers.R, and www/custom.js already
#   fires a resize on section switch specifically so Highcharts can re-measure).
#   DT is the product table library. V6.24 uses both, so the MVP and the legacy
#   section look like one application rather than two.

# Palette. The values mirror the legacy .fvp_palette so a model keeps a familiar
# colour between the two sections; V6.24 keeps its own copy rather than reaching
# into a legacy internal.
V6_24_ACTUAL_COLOR   <- "#10477e"  # reserved for observed actuals
V6_24_FORECAST_COLOR <- "#0f9d6e"  # reserved for the forward forecast
V6_24_MODEL_PALETTE <- c(
  "#d97706", "#2e9e5b", "#9b59b6", "#e0508a", "#0e7490",
  "#b45309", "#1f77b4", "#7f8c1a", "#c0392b", "#16a085",
  "#8e44ad", "#2c3e50", "#d35400"
)

V6_24_CHART_FONT <- "Inter, system-ui, sans-serif"

#' UTC-safe governed date.
#'
#' The governed artifacts store series_date / target_date / forecast_date as
#' timestamps at midnight UTC. R reads them as POSIXct, so as.character() would
#' render them in the SERVER's local zone and silently shift the date by a day
#' in any negative-offset timezone - a governed 2022-04-30 printed as
#' "2022-04-29 18:00:00". Every V6.24 date must go through this function so the
#' chart, the table and the notes all state the same governed day.
v6_24_as_date <- function(x) {
  if (inherits(x, "Date")) return(x)
  if (inherits(x, "POSIXt")) return(as.Date(x, tz = "UTC"))
  as.Date(as.character(x))
}

#' Format a date range for a chart subtitle.
v6_24_date_range_text <- function(dates) {
  d <- v6_24_as_date(dates)
  d <- d[!is.na(d)]
  if (!length(d)) return("\u2014")
  paste0(format(min(d), "%Y-%m-%d"), " \u2192 ", format(max(d), "%Y-%m-%d"))
}

#' Calm empty / pending state chart.
#'
#' Used before Analyze Backtest is clicked and whenever a selection resolves to
#' no governed rows. It is a real Highcharts object, so the pending state and
#' the rendered state share one container and one library.
v6_24_hc_empty <- function(msg, color = "#627d98") {
  highcharter::highchart() |>
    highcharter::hc_chart(style = list(fontFamily = V6_24_CHART_FONT)) |>
    highcharter::hc_title(
      text = msg,
      style = list(fontSize = "13px", color = color, fontWeight = "500")) |>
    highcharter::hc_xAxis(visible = FALSE) |>
    highcharter::hc_yAxis(visible = FALSE) |>
    highcharter::hc_credits(enabled = FALSE)
}

#' Shared chart chrome: title, subtitle, axes, legend, tooltip, export menu.
#'
#' plotOptions pins type "line" with a thin line and small markers, which is
#' what keeps every V6.24 chart line-based instead of a cloud of points.
v6_24_hc_base <- function(title, subtitle, y_label = "Value",
                          title_color = "#102a43", subtitle_color = "#627d98",
                          marker = TRUE) {
  highcharter::highchart() |>
    highcharter::hc_chart(
      type = "line", zoomType = "xy",
      panning = list(enabled = TRUE), panKey = "shift",
      style = list(fontFamily = V6_24_CHART_FONT)) |>
    highcharter::hc_title(
      text = title,
      style = list(fontSize = "15px", fontWeight = "600", color = title_color)) |>
    highcharter::hc_subtitle(
      text = subtitle,
      style = list(fontSize = "12px", color = subtitle_color)) |>
    highcharter::hc_xAxis(type = "datetime", title = list(text = NULL),
                          crosshair = TRUE) |>
    highcharter::hc_yAxis(title = list(text = y_label), opposite = FALSE,
                          crosshair = TRUE) |>
    highcharter::hc_legend(enabled = TRUE) |>
    highcharter::hc_tooltip(shared = FALSE, xDateFormat = "%Y-%m-%d",
                            valueDecimals = 2) |>
    highcharter::hc_exporting(enabled = TRUE) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_plotOptions(
      line = list(
        lineWidth = 2,
        marker = list(enabled = marker, radius = 2.5, symbol = "circle"),
        states = list(hover = list(lineWidth = 3))))
}

#' Build the (x, y) payload for one line. NA values are dropped, never filled.
v6_24_hc_points <- function(dates, values) {
  d <- v6_24_as_date(dates)
  ok <- !is.na(d) & !is.na(values)
  if (!any(ok)) return(NULL)
  df <- data.frame(
    x = highcharter::datetime_to_timestamp(d[ok]),
    y = round(as.numeric(values[ok]), 6))
  df <- df[order(df$x), , drop = FALSE]
  highcharter::list_parse2(df)
}

# ------------------------------------------------------------------ 1. actuals

#' Observed history for one series, as a line.
#'
#' Markers are disabled: an actuals series runs to several hundred points and
#' markers would turn the line into a smear.
v6_24_hc_actuals <- function(series_id, label = NULL) {
  a <- v6_24_tbl("actuals")
  a <- a[as.character(a$series_id) == series_id, , drop = FALSE]
  if (!nrow(a)) {
    return(v6_24_hc_empty("No observed history for this series."))
  }
  a$series_date <- v6_24_as_date(a$series_date)
  a <- a[order(a$series_date), , drop = FALSE]
  lbl <- if (is.null(label) || !nzchar(label)) series_id else label
  sub <- paste0(lbl, "  \u00b7  ", format(nrow(a), big.mark = ","),
                " observed points  \u00b7  ",
                v6_24_date_range_text(a$series_date))

  v6_24_hc_base("Observed history", sub, y_label = "Actual value",
                marker = FALSE) |>
    highcharter::hc_add_series(
      name = "Actual", type = "line", color = V6_24_ACTUAL_COLOR,
      lineWidth = 2.5, marker = list(enabled = FALSE),
      data = v6_24_hc_points(a$series_date, a$actual_value),
      tooltip = list(
        headerFormat = "",
        pointFormat = paste0("<b>Actual</b><br/>{point.x:%Y-%m-%d}<br/>",
                             "Value: <b>{point.y:.4f}</b>")))
}

# ----------------------------------------------------------------- 2. backtest

#' Viewer backtest comparison chart.
#'
#' One observed-actual line plus one line per selected model, all at the single
#' applied horizon. Rows come from v6_24_backtest_rows(), which filters
#' model_backtests_15_models with horizon_steps == horizon (equality, matching
#' the legacy viewer). Nothing is recomputed and no point is synthesised.
v6_24_hc_backtest <- function(cfg, label = NULL, champion = NULL) {
  if (is.null(cfg)) {
    return(v6_24_hc_empty(paste(
      "Choose a horizon and the models to compare, then click",
      "Analyze Backtest.")))
  }
  b <- v6_24_backtest_rows(cfg$series, cfg$models, cfg$horizon)
  if (!nrow(b)) {
    return(v6_24_hc_empty(paste0(
      "No prepared backtest rows for this configuration at horizon ",
      cfg$horizon, " days.")))
  }
  b$target_date <- v6_24_as_date(b$target_date)
  lbl <- if (is.null(label) || !nzchar(label)) cfg$series else label

  # The observed actual is carried on every backtest row, so one distinct pair
  # per target_date is the observed line. unique() reads it, it does not build it.
  act <- unique(b[, c("target_date", "actual_value")])
  act <- act[order(act$target_date), , drop = FALSE]

  n_mod <- length(cfg$models)
  sub <- paste0(
    lbl, "  \u00b7  horizon ", as.integer(cfg$horizon), " days  \u00b7  ",
    n_mod, if (n_mod == 1) " model" else " models", "  \u00b7  ",
    v6_24_date_range_text(b$target_date))

  hc <- v6_24_hc_base("Backtest comparison", sub) |>
    highcharter::hc_add_series(
      name = "Actual", type = "line", color = V6_24_ACTUAL_COLOR,
      lineWidth = 3, zIndex = 5,
      marker = list(enabled = TRUE, radius = 3, symbol = "circle"),
      data = v6_24_hc_points(act$target_date, act$actual_value),
      tooltip = list(
        headerFormat = "",
        pointFormat = paste0("<b>Actual</b><br/>{point.x:%Y-%m-%d}<br/>",
                             "Observed: <b>{point.y:.4f}</b>")))

  # Governed order keeps a model on the same colour between selections.
  ordered <- V6_24_GOVERNED_MODELS[V6_24_GOVERNED_MODELS %in% cfg$models]
  if (!length(ordered)) ordered <- cfg$models
  for (i in seq_along(ordered)) {
    m <- ordered[[i]]
    g <- b[as.character(b$model_name) == m, , drop = FALSE]
    if (!nrow(g)) next
    g <- g[order(g$target_date), , drop = FALSE]
    is_champ <- !is.null(champion) && isTRUE(champion$meaningful) &&
      identical(m, champion$model)
    nm <- if (is_champ) paste0(m, " \u2605") else m
    fam <- V6_24_FAMILY_LABEL[[unname(V6_24_DISPLAY_FAMILY[[m]])]]
    col <- V6_24_MODEL_PALETTE[[((i - 1) %% length(V6_24_MODEL_PALETTE)) + 1]]
    hc <- hc |> highcharter::hc_add_series(
      name = nm, type = "line", color = col, lineWidth = 2,
      data = v6_24_hc_points(g$target_date, g$predicted_value),
      tooltip = list(
        headerFormat = "",
        pointFormat = paste0(
          "<b>", htmltools::htmlEscape(m), "</b>",
          if (is_champ) " \u2605 champion" else "", "<br/>",
          "{point.x:%Y-%m-%d}<br/>",
          "Backtest estimate: <b>{point.y:.4f}</b><br/>",
          "Horizon: ", as.integer(cfg$horizon), " days<br/>",
          "Family: ", htmltools::htmlEscape(fam))))
  }
  hc
}

# ----------------------------------------------------------------- 3. forecast

#' Forward forecast chart: observed history then the governed 30-step forecast.
#'
#' The two lines carry deliberately different colours and the forecast is dashed
#' behind a labelled "Forecast start" boundary, so where history ends and the
#' forecast begins is unambiguous. Forecast values are drawn exactly as the
#' model produced them - negatives are not clipped.
v6_24_hc_forecast <- function(series_id, model, label = NULL,
                              hist_days = 120L, meaningful = FALSE) {
  fo <- v6_24_tbl("forecast_outputs")
  f <- fo[as.character(fo$series_id) == series_id &
            as.character(fo$model_name) == model, , drop = FALSE]
  if (!nrow(f)) {
    return(v6_24_hc_empty("No governed forecast rows for this selection."))
  }
  f$forecast_date <- v6_24_as_date(f$forecast_date)
  f <- f[order(as.integer(f$forecast_step)), , drop = FALSE]

  a <- v6_24_tbl("actuals")
  a <- a[as.character(a$series_id) == series_id, , drop = FALSE]
  if (nrow(a)) {
    a$series_date <- v6_24_as_date(a$series_date)
    a <- a[order(a$series_date), , drop = FALSE]
    if (nrow(a) > hist_days) a <- utils::tail(a, hist_days)
  }

  lbl <- if (is.null(label) || !nzchar(label)) series_id else label
  n_neg <- sum(as.character(f$negative_forecast_flag) == "TRUE", na.rm = TRUE)
  n_ext <- sum(as.character(f$extreme_forecast_flag) == "TRUE", na.rm = TRUE)
  role <- if (isTRUE(meaningful)) "champion" else "reference model"
  sub <- paste0(
    model, "  \u00b7  ", role, "  \u00b7  ", nrow(f),
    "-step daily forecast  \u00b7  ", v6_24_date_range_text(f$forecast_date))
  if (n_neg > 0 || n_ext > 0) {
    sub <- paste0(sub, "  \u00b7  ", n_neg, " negative, ", n_ext,
                  " extreme (shown unclipped)")
  }

  # Boundary = last observed actual date. Read, not chosen.
  bnd <- if (nrow(a)) max(a$series_date, na.rm = TRUE) else NA
  hc <- v6_24_hc_base(lbl, sub, title_color = "#0b3d2e",
                      subtitle_color = "#3f7d6c", marker = FALSE)
  if (!is.na(bnd)) {
    hc <- hc |> highcharter::hc_xAxis(
      type = "datetime", title = list(text = NULL), crosshair = TRUE,
      plotLines = list(list(
        value = highcharter::datetime_to_timestamp(bnd),
        color = "#0f766e", width = 2, dashStyle = "Dash", zIndex = 5,
        label = list(text = "Forecast start",
                     style = list(color = "#0f766e", fontWeight = "600",
                                  fontSize = "11px")))))
  }

  if (nrow(a)) {
    hc <- hc |> highcharter::hc_add_series(
      name = "Observed actual", type = "line", color = V6_24_ACTUAL_COLOR,
      lineWidth = 2.5, marker = list(enabled = FALSE),
      data = v6_24_hc_points(a$series_date, a$actual_value),
      tooltip = list(
        headerFormat = "",
        pointFormat = paste0("<b>Observed actual</b><br/>{point.x:%Y-%m-%d}<br/>",
                             "Value: <b>{point.y:.4f}</b>")))
  }

  fc_name <- paste0("Forecast (", nrow(f), " steps)")
  hc |> highcharter::hc_add_series(
    name = fc_name, type = "line", color = V6_24_FORECAST_COLOR,
    dashStyle = "ShortDash", lineWidth = 2.5, zIndex = 4,
    marker = list(enabled = TRUE, radius = 3, symbol = "circle"),
    data = v6_24_hc_points(f$forecast_date, f$predicted_value),
    tooltip = list(
      headerFormat = "",
      pointFormat = paste0(
        "<b>Forecast</b><br/>{point.x:%Y-%m-%d}<br/>",
        "Predicted: <b>{point.y:.4f}</b><br/>",
        "Model: ", htmltools::htmlEscape(model))))
}

# ------------------------------------------------------------------- 4. tables

#' V6.24 table renderer, using the application's table library (DT).
#'
#' Options mirror the legacy Forecasting tables - stripe/hover/row-border,
#' "ftip" layout, horizontal scroll - so a V6.24 table and a legacy table read
#' the same way. NA is rendered as an em dash and never as zero.
#'
#' `lazy_render = FALSE` disables DT's lazy rendering. DT normally stashes a new
#' value and returns without drawing whenever the output element has zero size,
#' and it only flushes that stash on a later resize. Sections here are toggled
#' with CSS, so a table whose data changes while its own section is hidden never
#' redraws and silently keeps showing the previous rows. Tables in that position
#' must opt out.
v6_24_dt <- function(df, page_length = 10L, searching = TRUE, paging = TRUE,
                     dom = NULL, align_left = NULL, lazy_render = NULL) {
  if (is.null(df) || !NROW(df)) {
    return(DT::datatable(
      data.frame(Message = "No rows to display."),
      rownames = FALSE, options = list(dom = "t"), class = "stripe row-border",
      lazyRender = lazy_render))
  }
  df <- as.data.frame(df, stringsAsFactors = FALSE, check.names = FALSE)
  for (j in seq_along(df)) {
    if (is.character(df[[j]])) df[[j]][is.na(df[[j]])] <- "\u2014"
  }
  if (is.null(dom)) dom <- if (isTRUE(paging)) "ftip" else "t"
  cdefs <- list(list(className = "dt-left", targets = "_all"))
  DT::datatable(
    df,
    rownames = FALSE,
    escape = FALSE,
    selection = "none",
    lazyRender = lazy_render,
    class = "stripe hover row-border",
    options = list(
      pageLength = page_length,
      paging = isTRUE(paging),
      searching = isTRUE(searching),
      info = isTRUE(paging),
      ordering = TRUE,
      scrollX = TRUE,
      dom = dom,
      columnDefs = cdefs
    )
  )
}

#' Small inline HTML badge used inside DT cells (escape = FALSE above).
v6_24_cell_badge <- function(text, tone = "slate") {
  sprintf('<span class="v24-cell-badge v24-cell-%s">%s</span>',
          tone, htmltools::htmlEscape(text))
}
