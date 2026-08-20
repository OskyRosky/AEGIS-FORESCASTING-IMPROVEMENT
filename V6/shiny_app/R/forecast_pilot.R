# V6.17 | Read-only productive forward Forecast provider.

FFP_PILOT_REL_PATH <- file.path(
  "outputs", "v6_17_full_multimetric_productive_artifact_generation",
  "forecast_forward_outputs_v6_17_full.parquet"
)
FFP_METADATA_REL_PATH <- file.path(
  "outputs", "v6_17_full_multimetric_productive_artifact_generation",
  "v6_17_forecast_dropdown_metadata.csv"
)

.ffp_pilot_env <- new.env(parent = emptyenv())

ffp_pilot_path <- function(root = find_project_root()) {
  file.path(root, FFP_PILOT_REL_PATH)
}

ffp_metadata_path <- function(root = find_project_root()) {
  file.path(root, FFP_METADATA_REL_PATH)
}

ffp_pilot_data <- function(refresh = FALSE) {
  if (!isTRUE(refresh) &&
      exists("metadata", envir = .ffp_pilot_env, inherits = FALSE)) {
    return(get("metadata", envir = .ffp_pilot_env, inherits = FALSE))
  }
  path <- ffp_metadata_path()
  if (!file.exists(path)) {
    stop("V6.17 Forecast metadata is missing: ", path)
  }
  df <- utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  required <- c(
    "metric", "scenario", "granularity", "series_key", "has_actuals",
    "forecast_only", "forecast_available"
  )
  missing <- setdiff(required, names(df))
  if (length(missing) > 0) {
    stop(
      "V6.17 Forecast metadata is missing columns: ",
      paste(missing, collapse = ", ")
    )
  }
  df$has_actuals <- .tess_as_logical(df$has_actuals)
  df$forecast_only <- .tess_as_logical(df$forecast_only)
  df$forecast_available <- .tess_as_logical(df$forecast_available)
  if (anyNA(df$has_actuals) || anyNA(df$forecast_only) ||
      anyNA(df$forecast_available)) {
    stop("V6.17 Forecast metadata contains invalid required values.")
  }
  assign("metadata", df, envir = .ffp_pilot_env)
  df
}

ffp_pilot_dataset <- function(refresh = FALSE) {
  if (!isTRUE(refresh) &&
      exists("dataset", envir = .ffp_pilot_env, inherits = FALSE)) {
    return(get("dataset", envir = .ffp_pilot_env, inherits = FALSE))
  }
  path <- ffp_pilot_path()
  if (!file.exists(path)) {
    stop("V6.17 Forecast Parquet artifact is missing: ", path)
  }
  dataset <- arrow::open_dataset(path, format = "parquet")
  assign("dataset", dataset, envir = .ffp_pilot_env)
  dataset
}

ffp_metrics <- function(df = ffp_pilot_data()) {
  unique(df$metric)
}

ffp_scenarios <- function(metric, df = ffp_pilot_data()) {
  unique(df$scenario[df$metric == metric])
}

ffp_granularities <- function(metric, scenario, df = ffp_pilot_data()) {
  unique(df$granularity[df$metric == metric & df$scenario == scenario])
}

ffp_keys <- function(metric, scenario, granularity, df = ffp_pilot_data()) {
  keep <- df$metric == metric &
    df$scenario == scenario &
    df$granularity == granularity
  sort(unique(df$series_key[keep]))
}

ffp_case_data <- function(metric, scenario, granularity, series_key,
                          df = ffp_pilot_data()) {
  if (is.null(series_key) || !nzchar(series_key)) return(df[0, , drop = FALSE])
  result <- ffp_pilot_dataset() |>
    dplyr::filter(
      .data$metric == .env$metric,
      .data$scenario == .env$scenario,
      .data$granularity == .env$granularity,
      .data$series_key == .env$series_key
    ) |>
    dplyr::collect()
  result$date <- as.Date(result$date)
  result$value <- suppressWarnings(as.numeric(result$value))
  result$has_actuals <- .tess_as_logical(result$has_actuals)
  result$forecast_only <- .tess_as_logical(result$forecast_only)
  if (anyNA(result$date) || anyNA(result$value) || anyNA(result$has_actuals) ||
      anyNA(result$forecast_only)) {
    stop("V6.17 Forecast case contains invalid required values.")
  }
  result
}

ffp_case_has_actuals <- function(df) {
  is.data.frame(df) && nrow(df) > 0 && any(df$record_type == "actual")
}

ffp_empty_case <- function() {
  data.frame(
    date = as.Date(character()),
    value = numeric(),
    record_type = character(),
    forecast_version = character(),
    model_name = character(),
    has_actuals = logical(),
    forecast_only = logical(),
    stringsAsFactors = FALSE
  )
}

ffp_window_data <- function(df, forecast_days = 30, history_days = 180) {
  actual <- df[df$record_type == "actual", , drop = FALSE]
  forecast <- df[df$record_type == "forecast", , drop = FALSE]
  if (nrow(actual) > 0 && nrow(forecast) > 0) {
    actual <- actual[actual$date < min(forecast$date), , drop = FALSE]
  }
  if (nrow(actual) > 0 && !is.na(history_days) && history_days > 0) {
    cutoff <- max(actual$date) - as.integer(history_days) + 1L
    actual <- actual[actual$date >= cutoff, , drop = FALSE]
  }
  if (nrow(forecast) > 0 && !is.na(forecast_days) && forecast_days > 0) {
    cutoff <- min(forecast$date) + as.integer(forecast_days) - 1L
    forecast <- forecast[forecast$date <= cutoff, , drop = FALSE]
  }
  actual <- actual[order(actual$date), , drop = FALSE]
  forecast <- forecast[order(forecast$date), , drop = FALSE]
  list(actual = actual, forecast = forecast)
}

ffp_interval_data <- function(forecast) {
  empty <- data.frame(
    date = as.Date(character()), lower = numeric(), upper = numeric()
  )
  if (!is.data.frame(forecast) || nrow(forecast) == 0 ||
      !all(c("lower_bound", "upper_bound") %in% names(forecast))) {
    return(empty)
  }
  lower <- suppressWarnings(as.numeric(forecast$lower_bound))
  upper <- suppressWarnings(as.numeric(forecast$upper_bound))
  keep <- !is.na(forecast$date) & !is.na(lower) & !is.na(upper) & lower <= upper
  data.frame(
    date = forecast$date[keep], lower = lower[keep], upper = upper[keep]
  )
}

ffp_interval_status <- function(forecast) {
  intervals <- ffp_interval_data(forecast)
  if (nrow(intervals) == 0) {
    if (all(c("lower_bound", "upper_bound") %in% names(forecast))) {
      return("Not shown \u00b7 prepared bounds are empty")
    }
    return("Not available in prepared artifact")
  }
  if ("interval_level" %in% names(forecast)) {
    levels <- suppressWarnings(as.numeric(forecast$interval_level))
    levels <- unique(levels[!is.na(levels)])
    if (length(levels) > 0) {
      return(paste0("Shown \u00b7 ", paste0(round(levels * 100), "%", collapse = ", ")))
    }
  }
  "Shown \u00b7 prepared lower and upper bounds"
}

ffp_empty_chart <- function(
    message = "Select Metric through Actual History Window, then analyze.") {
  highcharter::highchart() |>
    highcharter::hc_title(
      text = message,
      style = list(
        fontSize = "13px", color = "#0f766e", fontWeight = "500"
      )
    ) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_xAxis(visible = FALSE) |>
    highcharter::hc_yAxis(visible = FALSE) |>
    highcharter::hc_chart(
      style = list(fontFamily = "Inter, system-ui, sans-serif")
    )
}

ffp_chart <- function(request) {
  rows <- ffp_window_data(
    request$data, request$forecast_window, request$history_window
  )
  actual <- rows$actual
  forecast <- rows$forecast
  if (nrow(actual) == 0 && nrow(forecast) == 0) {
    return(ffp_empty_chart("No prepared forecast rows exist for this setup."))
  }
  dates <- c(actual$date, forecast$date)
  date_text <- paste0(min(dates), " \u2192 ", max(dates))
  mode_text <- if (nrow(actual) > 0) {
    "actual history + forward forecast"
  } else {
    "forecast-only \u00b7 no actual history"
  }
  subtitle <- paste(
    request$metric, request$scenario, request$granularity, request$series,
    mode_text, date_text, sep = " \u00b7 "
  )
  boundary <- if (nrow(forecast) > 0) min(forecast$date) else as.Date(NA)

  hc <- highcharter::highchart() |>
    highcharter::hc_chart(
      type = "line", zoomType = "xy",
      panning = list(enabled = TRUE), panKey = "shift",
      style = list(fontFamily = "Inter, system-ui, sans-serif")
    ) |>
    highcharter::hc_title(
      text = "Forward Forecast",
      style = list(fontSize = "15px", fontWeight = "600", color = "#0b3d2e")
    ) |>
    highcharter::hc_subtitle(
      text = subtitle, style = list(fontSize = "12px", color = "#3f7d6c")
    ) |>
    highcharter::hc_xAxis(
      type = "datetime", title = list(text = NULL), crosshair = TRUE,
      plotLines = if (!is.na(boundary)) {
        list(list(
          value = highcharter::datetime_to_timestamp(boundary),
          color = "#b45309", width = 3, dashStyle = "ShortDash", zIndex = 7,
          label = list(
            text = "Forecast start",
            rotation = 0,
            align = if (nrow(actual) > 0) "right" else "left",
            x = if (nrow(actual) > 0) -8 else 8,
            y = 18,
            style = list(
              color = "#92400e", fontWeight = "700", fontSize = "12px",
              textOutline = "3px #ffffff", whiteSpace = "nowrap",
              textOverflow = "none"
            )
          )
        ))
      } else {
        list()
      }
    ) |>
    highcharter::hc_yAxis(
      title = list(text = "Value"), opposite = FALSE, crosshair = TRUE
    ) |>
    highcharter::hc_legend(enabled = TRUE) |>
    highcharter::hc_tooltip(
      shared = FALSE, xDateFormat = "%Y-%m-%d", valueDecimals = 2
    ) |>
    highcharter::hc_exporting(enabled = TRUE) |>
    highcharter::hc_credits(enabled = FALSE) |>
    highcharter::hc_plotOptions(
      line = list(marker = list(enabled = FALSE), lineWidth = 2)
    )

  if (nrow(actual) > 0) {
    actual_data <- data.frame(
      x = highcharter::datetime_to_timestamp(actual$date),
      y = round(actual$value, 3)
    )
    hc <- hc |>
      highcharter::hc_add_series(
        name = "Actual history", type = "line", color = "#10477e",
        lineWidth = 2.5, data = highcharter::list_parse2(actual_data)
      )
  }
  if (nrow(forecast) > 0) {
    intervals <- ffp_interval_data(forecast)
    if (nrow(intervals) > 0) {
      lower_data <- data.frame(
        x = highcharter::datetime_to_timestamp(intervals$date),
        y = round(intervals$lower, 3)
      )
      upper_data <- data.frame(
        x = highcharter::datetime_to_timestamp(intervals$date),
        y = round(intervals$upper, 3)
      )
      hc <- hc |>
        highcharter::hc_add_series(
          name = "Prediction interval lower", type = "line",
          color = "#67c5aa", dashStyle = "Dot", lineWidth = 1.5,
          data = highcharter::list_parse2(lower_data)
        ) |>
        highcharter::hc_add_series(
          name = "Prediction interval upper", type = "line",
          color = "#67c5aa", dashStyle = "Dot", lineWidth = 1.5,
          data = highcharter::list_parse2(upper_data)
        )
    }
    forecast_data <- data.frame(
      x = highcharter::datetime_to_timestamp(forecast$date),
      y = round(forecast$value, 3)
    )
    hc <- hc |>
      highcharter::hc_add_series(
        name = "Forward forecast", type = "line", color = "#0f9d6e",
        dashStyle = "ShortDash", lineWidth = 2.5,
        data = highcharter::list_parse2(forecast_data)
      )
  }
  hc
}

ffp_summary <- function(request) {
  rows <- ffp_window_data(
    request$data, request$forecast_window, request$history_window
  )
  actual <- rows$actual
  forecast <- rows$forecast
  dates <- c(actual$date, forecast$date)
  versions <- unique(forecast$forecast_version)
  versions <- versions[!is.na(versions) & nzchar(versions)]
  models <- unique(forecast$model_name)
  models <- models[!is.na(models) & nzchar(models)]
  forecast_start <- if (nrow(forecast) > 0) min(forecast$date) else as.Date(NA)
  list(
    metric = request$metric,
    scenario = request$scenario,
    granularity = request$granularity,
    series = request$series,
    forecast_window = paste0(request$forecast_window, " days"),
    actual_history_window = if (nrow(actual) > 0) {
      paste0(request$history_window, " days")
    } else {
      "Not applicable \u00b7 forecast-only"
    },
    actual_history_state = if (nrow(actual) > 0) "Available" else "Not available",
    actual_points = nrow(actual),
    forecast_points = nrow(forecast),
    forecast_start = if (!is.na(forecast_start)) {
      format(forecast_start, "%Y-%m-%d")
    } else {
      "\u2014"
    },
    date_min = if (length(dates) > 0) format(min(dates), "%Y-%m-%d") else "\u2014",
    date_max = if (length(dates) > 0) format(max(dates), "%Y-%m-%d") else "\u2014",
    model = if (length(models) > 0) paste(models, collapse = ", ") else "\u2014",
    version = if (length(versions) > 0) paste(versions, collapse = ", ") else "\u2014",
    forecast_only = nrow(actual) == 0,
    forecast_mode = if (nrow(actual) > 0) {
      "Actual history + forward forecast"
    } else {
      "Forecast-only \u00b7 actuals not available"
    },
    interval_shown = ffp_interval_status(forecast),
    artifact = basename(FFP_PILOT_REL_PATH)
  )
}

forecast_pilot_server <- function(input, output, session) {
  ffp_all <- ffp_pilot_data()
  taxonomy <- taxonomy_navigation_server("ffp_taxonomy", "forecast")

  ffp_route <- reactive(taxonomy$resolved())

  ffp_case <- reactive({
    route <- ffp_route()
    if (is.null(route)) return(ffp_empty_case())
    ffp_case_data(
      route$source_metric, route$source_scenario, route$source_granularity,
      route$source_series_key, ffp_all
    )
  })

  output$ffp_case_status <- renderUI({
    case <- ffp_case()
    if (nrow(case) == 0) {
      return(tags$div(
        class = "fvb-pilot-status is-unavailable",
        tags$span(class = "pill pill-amber", "Select route"),
        "Complete Selection to configure a prepared forward forecast."
      ))
    }
    if (ffp_case_has_actuals(case)) {
      tags$div(
        class = "fvb-pilot-status is-available",
        tags$span(class = "pill pill-green", "Actuals available"),
        "Prepared actual history and forward forecast rows are available."
      )
    } else {
      route <- ffp_route()
      tags$div(
        class = "fvb-pilot-status is-forecast-only",
        tags$span(class = "pill pill-teal", "Forecast-only"),
        paste0(
          "No actuals exist for ", route$display_label,
          "; the prepared forward forecast remains eligible."
        )
      )
    }
  })

  output$ffp_history_control <- renderUI({
    case <- ffp_case()
    req(nrow(case) > 0)
    has_actuals <- ffp_case_has_actuals(case)
    tags$div(
      class = "fvb-field fvb-field-history",
      tags$label(
        class = "fvb-field-label",
        "Actual History Window"
      ),
      selectInput(
        "ffp_history", NULL,
        choices = if (has_actuals) {
          c("Last 90 days" = 90, "Last 180 days" = 180, "Last 365 days" = 365)
        } else {
          c("Not available \u2014 forecast-only" = 0)
        },
        selected = if (has_actuals) 180 else 0,
        width = "100%"
      ),
      tags$p(
        class = "fvb-field-hint",
        if (has_actuals) {
          "How much prepared actual history to show before forecast start."
        } else {
          "SSD-Phoenix has no actuals; this control is intentionally not applicable."
        }
      )
    )
  })
  ffp_analysis_ready <- reactiveVal(FALSE)
  ffp_current_available <- reactive({
    case <- ffp_case()
    nrow(case) > 0 && any(case$record_type == "forecast")
  })

  observeEvent(input$ffp_go, {
    ffp_analysis_ready(TRUE)
  }, ignoreInit = TRUE)

  observeEvent(input$ffp_reset_selection, {
    has_actuals <- ffp_case_has_actuals(ffp_case())
    taxonomy$reset()
    updateSelectInput(session, "ffp_window", selected = "30")
    updateSelectInput(
      session, "ffp_history", selected = if (has_actuals) "180" else "0"
    )
    ffp_analysis_ready(FALSE)
  }, ignoreInit = TRUE)

  output$ffp_analyze_button <- renderUI({
    actionButton(
      "ffp_go", "Analyze Forward Forecast",
      class = "fv-analyze-btn fvb-analyze-btn",
      disabled = !isTRUE(ffp_current_available())
    )
  })

  ffp_request <- eventReactive(input$ffp_go, {
    route <- ffp_route()
    if (is.null(route)) {
      return(list(
        metric = "", display_label = "", scenario = "", granularity = "",
        scenario_label = "Scenario", entity_label = "Entity", series = "",
        forecast_window = 0,
        history_window = 0, data = ffp_empty_case()
      ))
    }
    list(
      metric = route$base_metric,
      display_label = route$display_label,
      scenario = route$source_scenario,
      scenario_label = if (identical(route$base_metric, "SSD")) {
        "Prepared Forecast Variant"
      } else {
        "Scenario"
      },
      granularity = route$source_granularity,
      entity_label = route$entity_label,
      series = route$source_series_key,
      forecast_window = suppressWarnings(as.numeric(input$ffp_window)),
      history_window = suppressWarnings(as.numeric(input$ffp_history)),
      data = ffp_case()
    )
  }, ignoreNULL = FALSE)

  output$ffp_chart <- highcharter::renderHighchart({
    if (!isTRUE(ffp_analysis_ready())) {
      return(ffp_empty_chart())
    }
    ffp_chart(ffp_request())
  })

  output$ffp_chart_legend <- renderUI({
    if (!isTRUE(ffp_analysis_ready())) return(NULL)
    rows <- ffp_window_data(
      ffp_request()$data,
      ffp_request()$forecast_window,
      ffp_request()$history_window
    )
    item <- function(type, label) {
      tags$span(
        class = "ffp-chart-legend-item",
        tags$span(class = paste("ffp-chart-legend-swatch", type)),
        label
      )
    }
    tags$div(
      class = "ffp-chart-legend",
      `aria-label` = "Forecast chart transition",
      if (nrow(rows$actual) > 0) item("is-actual", "Actual history"),
      item("is-boundary", "Forecast start"),
      item("is-forecast", "Forward forecast")
    )
  })

  output$ffp_notes <- renderUI({
    if (!isTRUE(ffp_analysis_ready())) {
      return(tags$p(
        class = "fv-step-hint",
        "Click Analyze Forward Forecast to see the prepared setup and counts."
      ))
    }
    summary <- ffp_summary(ffp_request())
    cell <- function(label, value) {
      tags$div(
        class = "fv-avail-card",
        tags$div(class = "fv-avail-label", label),
        tags$div(class = "fv-avail-value", value)
      )
    }
    tagList(
      tags$div(
        class = "fv-avail-grid",
        cell("Metric", summary$metric),
        cell("Prepared route", ffp_request()$display_label),
        cell(ffp_request()$scenario_label, summary$scenario),
        cell("Granularity", summary$granularity),
        cell(ffp_request()$entity_label, summary$series),
        cell("Forecast mode", summary$forecast_mode),
        cell("Model", summary$model),
        cell("Model version", summary$version),
        cell("Forecast Start", summary$forecast_start),
        cell("Forecast Window", summary$forecast_window),
        cell("Actual History Window", summary$actual_history_window),
        cell("Actual-history availability", summary$actual_history_state),
        cell("Actual Points", summary$actual_points),
        cell("Forecast Points", summary$forecast_points),
        cell(
          "Date Range",
          paste0(summary$date_min, " \u2192 ", summary$date_max)
        ),
        cell("Prediction interval", summary$interval_shown),
        cell("Forecast artifact", summary$artifact)
      ),
      tags$p(
        class = "fv-avail-note",
        paste0(
          "Forecast Start is derived from the first prepared forecast date (",
          summary$forecast_start,
          "). Shiny filters the frozen artifact and does not generate forecasts."
        )
      )
    )
  })
}
