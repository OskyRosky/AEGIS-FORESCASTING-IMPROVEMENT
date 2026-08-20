# V6.17 | Read-only productive Viewer provider.
# Dropdowns use prepared metadata; selected cases are collected lazily from Parquet.

FVP_PILOT_REL_PATH <- file.path(
  "outputs", "v6_17_full_multimetric_productive_artifact_generation",
  "forecast_viewer_model_outputs_v2_full.parquet"
)
FVP_METADATA_REL_PATH <- file.path(
  "outputs", "v6_17_full_multimetric_productive_artifact_generation",
  "v6_17_viewer_dropdown_metadata.csv"
)
FVP_MODEL_METADATA_REL_PATH <- file.path(
  "outputs", "v6_17_full_multimetric_productive_artifact_generation",
  "v6_17_model_metadata.csv"
)
FVP_VERIFIED_MODEL_NAMES <- c(
  "FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
  "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
  "LightGBM", "LinearRegression", "XGBoost",
  "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"
)

.fvp_pilot_env <- new.env(parent = emptyenv())

fvp_pilot_path <- function(root = find_project_root()) {
  file.path(root, FVP_PILOT_REL_PATH)
}

fvp_metadata_path <- function(root = find_project_root()) {
  file.path(root, FVP_METADATA_REL_PATH)
}

fvp_model_metadata_path <- function(root = find_project_root()) {
  file.path(root, FVP_MODEL_METADATA_REL_PATH)
}

fvp_verified_model_universe <- function(refresh = FALSE) {
  if (!isTRUE(refresh) &&
      exists("model_universe", envir = .fvp_pilot_env, inherits = FALSE)) {
    return(get("model_universe", envir = .fvp_pilot_env, inherits = FALSE))
  }
  path <- fvp_model_metadata_path()
  if (!file.exists(path)) {
    stop("V6.17 Viewer model metadata is missing: ", path)
  }
  metadata <- utils::read.csv(
    path, stringsAsFactors = FALSE, check.names = FALSE
  )
  required <- c("model_name", "model_family", "include_in_viewer")
  missing <- setdiff(required, names(metadata))
  if (length(missing) > 0) {
    stop("V6.17 Viewer model metadata is missing columns: ",
         paste(missing, collapse = ", "))
  }
  metadata$include_in_viewer <- .tess_as_logical(metadata$include_in_viewer)
  metadata <- metadata[metadata$include_in_viewer %in% TRUE, required, drop = FALSE]
  metadata <- unique(metadata[c("model_name", "model_family")])
  if (nrow(metadata) != 15L ||
      !setequal(metadata$model_name, FVP_VERIFIED_MODEL_NAMES)) {
    stop("V6.17 Viewer model metadata must contain exactly the 15 verified models.")
  }
  if (!all(metadata$model_family %in% FVP_FAMILY_ORDER)) {
    stop("V6.17 Viewer model metadata contains an unsupported model family.")
  }
  family_rank <- match(metadata$model_family, FVP_FAMILY_ORDER)
  metadata <- metadata[order(family_rank, metadata$model_name), , drop = FALSE]
  metadata$model_origin <- ""
  metadata$risk_status <- ""
  metadata$is_selected_champion <- FALSE
  rownames(metadata) <- NULL
  assign("model_universe", metadata, envir = .fvp_pilot_env)
  metadata
}

fvp_pilot_data <- function(refresh = FALSE) {
  if (!isTRUE(refresh) &&
      exists("metadata", envir = .fvp_pilot_env, inherits = FALSE)) {
    return(get("metadata", envir = .fvp_pilot_env, inherits = FALSE))
  }
  path <- fvp_metadata_path()
  if (!file.exists(path)) {
    stop("V6.17 Viewer metadata is missing: ", path)
  }
  df <- utils::read.csv(path, stringsAsFactors = FALSE, check.names = FALSE)
  required <- c(
    "metric", "scenario", "granularity", "series_key", "has_actuals",
    "viewer_available", "model_count"
  )
  missing <- setdiff(required, names(df))
  if (length(missing) > 0) {
    stop("V6.17 Viewer metadata is missing columns: ",
         paste(missing, collapse = ", "))
  }
  df$has_actuals <- .tess_as_logical(df$has_actuals)
  df$viewer_available <- .tess_as_logical(df$viewer_available)
  df$model_count <- suppressWarnings(as.integer(df$model_count))
  if (anyNA(df$has_actuals) || anyNA(df$viewer_available) ||
      anyNA(df$model_count)) {
    stop("V6.17 Viewer metadata contains invalid required values.")
  }
  assign("metadata", df, envir = .fvp_pilot_env)
  df
}

fvp_pilot_dataset <- function(refresh = FALSE) {
  if (!isTRUE(refresh) &&
      exists("dataset", envir = .fvp_pilot_env, inherits = FALSE)) {
    return(get("dataset", envir = .fvp_pilot_env, inherits = FALSE))
  }
  path <- fvp_pilot_path()
  if (!file.exists(path)) {
    stop("V6.17 Viewer Parquet artifact is missing: ", path)
  }
  dataset <- arrow::open_dataset(path, format = "parquet")
  assign("dataset", dataset, envir = .fvp_pilot_env)
  dataset
}

fvp_pilot_catalog <- function(df = fvp_pilot_data()) {
  unique(df[c("metric", "scenario", "granularity")])
}

fvp_pilot_metrics <- function() {
  unique(fvp_pilot_data()$metric)
}

fvp_pilot_scenarios <- function(metric) {
  catalog <- fvp_pilot_catalog()
  unique(catalog$scenario[catalog$metric == metric])
}

fvp_pilot_granularities <- function(metric, scenario) {
  catalog <- fvp_pilot_catalog()
  unique(catalog$granularity[
    catalog$metric == metric & catalog$scenario == scenario
  ])
}

fvp_pilot_case_data <- function(metric, scenario, granularity, series_key = NULL,
                                df = fvp_pilot_data()) {
  if (is.null(series_key) || !nzchar(series_key)) {
    return(data.frame())
  }
  result <- fvp_pilot_dataset() |>
    dplyr::filter(
      .data$metric == .env$metric,
      .data$scenario == .env$scenario,
      .data$granularity == .env$granularity,
      .data$series_key == .env$series_key
    ) |>
    dplyr::collect()
  result$date <- as.Date(result$date)
  result$forecast_start_date <- as.Date(result$forecast_start_date)
  result$actual_value <- suppressWarnings(as.numeric(result$actual_value))
  result$forecast_value <- suppressWarnings(as.numeric(result$forecast_value))
  result$horizon_days <- suppressWarnings(as.integer(result$horizon_days))
  result$is_selected_champion <- .tess_as_logical(result$is_selected_champion)
  if (anyNA(result$date) || anyNA(result$forecast_start_date) ||
      anyNA(result$actual_value) || anyNA(result$forecast_value) ||
      anyNA(result$horizon_days) || anyNA(result$is_selected_champion)) {
    stop("V6.17 Viewer case contains invalid required values.")
  }
  result
}

fvp_pilot_keys <- function(metric, scenario, granularity, df = fvp_pilot_data()) {
  keep <- df$metric == metric &
    df$scenario == scenario &
    df$granularity == granularity &
    df$viewer_available
  sort(unique(df$series_key[keep]))
}

fvp_pilot_available <- function(metric, scenario, granularity, series_key = NULL,
                                df = fvp_pilot_data()) {
  if (is.null(series_key) || !nzchar(series_key)) return(FALSE)
  any(
    df$metric == metric &
      df$scenario == scenario &
      df$granularity == granularity &
      df$series_key == series_key &
      df$viewer_available
  )
}

fvp_pilot_download_rows <- function(metric, scenario, granularity, series_key,
                                    models, horizon_days,
                                    df = fvp_pilot_data()) {
  case <- fvp_pilot_case_data(metric, scenario, granularity, series_key, df)
  case[
    case$model_name %in% models &
      case$horizon_days == as.integer(horizon_days),
    , drop = FALSE
  ]
}

viewer_pilot_server <- function(input, output, session) {
  fvp_all <- fvp_pilot_data()
  taxonomy <- taxonomy_navigation_server("fvp_taxonomy", "viewer")

  fvp_route <- reactive(taxonomy$resolved())

  fvp_current_available <- reactive({
    route <- fvp_route()
    if (is.null(route)) return(FALSE)
    fvp_pilot_available(
      route$source_metric, route$source_scenario, route$source_granularity,
      route$source_series_key, fvp_all
    )
  })

  fvp_case <- reactive({
    route <- fvp_route()
    if (is.null(route)) return(data.frame())
    fvp_pilot_case_data(
      route$source_metric, route$source_scenario, route$source_granularity,
      route$source_series_key, fvp_all
    )
  })

  # V6.23-P0 | A route that resolves but carries no actuals is FORECAST-ONLY,
  # not "unavailable". SSD-Phoenix is now visible in the Viewer selector so the
  # local cohort is honestly exposed; it renders an explicit state instead of a
  # broken empty backtest.
  fvp_forecast_only <- reactive({
    route <- fvp_route()
    !is.null(route) && !isTRUE(route$has_actuals)
  })

  output$fvp_availability <- renderUI({
    route <- fvp_route()
    if (isTRUE(fvp_current_available())) {
      return(tags$div(
        class = "fvb-pilot-status is-available",
        tags$span(class = "pill pill-green", "Backtest available"),
        paste0(
          "Prepared actual and 15-model backtest rows are available for this ",
          tolower(route$entity_label), "."
        )
      ))
    }
    if (isTRUE(fvp_forecast_only())) {
      return(tags$div(
        class = "fvb-pilot-status is-forecast-only",
        tags$span(class = "pill pill-teal", "Forecast-only"),
        paste0(
          "No observed actuals or 15-model backtest estimates are available for ",
          route$display_label, ". Nothing was fabricated. ",
          "Open the Forecast section to see the prepared forward forecast for this ",
          tolower(route$entity_label), "."
        )
      ))
    }
    tags$div(
      class = "fvb-pilot-status is-unavailable",
      tags$span(class = "pill pill-amber", "Unavailable"),
      "Backtest not available for this combination."
    )
  })

  output$fvp_model_groups <- renderUI({
    case <- fvp_case()
    route <- fvp_route()
    meta <- fvp_verified_model_universe()
    if (!is.null(route) && nrow(case) > 0) {
      route_meta <- fvp_model_meta(route$source_series_key, case)
      matched <- match(meta$model_name, route_meta$model_name)
      has_route_meta <- !is.na(matched)
      meta$model_origin[has_route_meta] <-
        route_meta$model_origin[matched[has_route_meta]]
      meta$risk_status[has_route_meta] <-
        route_meta$risk_status[matched[has_route_meta]]
      meta$is_selected_champion[has_route_meta] <-
        route_meta$is_selected_champion[matched[has_route_meta]]
    }
    defaults <- intersect(fvp_default_models(), meta$model_name)
    families <- FVP_FAMILY_ORDER[FVP_FAMILY_ORDER %in% meta$model_family]
    groups <- lapply(families, function(family) {
      rows <- meta[meta$model_family == family, , drop = FALSE]
      choice_names <- lapply(seq_len(nrow(rows)), function(i) {
        tags$span(fvp_model_label(
          rows$model_name[i],
          rows$is_selected_champion[i],
          rows$risk_status[i]
        ))
      })
      tags$div(
        class = "fvp-fam-group",
        tags$div(
          class = "fvp-fam-label",
          if (!is.na(FVP_FAMILY_LABELS[family])) {
            FVP_FAMILY_LABELS[[family]]
          } else {
            family
          }
        ),
        checkboxGroupInput(
          inputId = paste0("fvp_models_", family),
          label = NULL,
          choiceNames = choice_names,
          choiceValues = as.list(rows$model_name),
          selected = intersect(defaults, rows$model_name)
        )
      )
    })
    tags$div(class = "fvp-model-grid", groups)
  })

  fvp_selected_models <- reactive({
    selected <- unlist(lapply(FVP_FAMILY_ORDER, function(family) {
      input[[paste0("fvp_models_", family)]]
    }), use.names = FALSE)
    unique(selected[!is.na(selected) & nzchar(selected)])
  })
  fvp_analysis_ready <- reactiveVal(FALSE)

  observeEvent(input$fvp_go, {
    fvp_analysis_ready(TRUE)
  }, ignoreInit = TRUE)

  observeEvent(input$fvp_reset_selection, {
    taxonomy$reset()
    meta <- fvp_verified_model_universe()
    for (family in FVP_FAMILY_ORDER) {
      rows <- meta[meta$model_family == family, , drop = FALSE]
      updateCheckboxGroupInput(
        session,
        paste0("fvp_models_", family),
        selected = intersect(fvp_default_models(), rows$model_name)
      )
    }
    updateRadioButtons(session, "fvp_horizon", selected = "5")
    updateSelectInput(session, "fvp_history", selected = "0")
    fvp_analysis_ready(FALSE)
  }, ignoreInit = TRUE)

  output$fvp_analyze_button <- renderUI({
    actionButton(
      "fvp_go", "Analyze Backtest",
      class = "fv-analyze-btn fvb-analyze-btn",
      disabled = !isTRUE(fvp_current_available())
    )
  })

  output$fvp_model_count <- renderUI({
    count <- length(fvp_selected_models())
    text <- if (count == 0) {
      "No models selected yet."
    } else {
      paste0(count, if (count == 1) " model selected." else " models selected.")
    }
    tags$div(
      class = "fv-model-note",
      tags$div(class = "fv-model-note-line", text)
    )
  })

  fvp_request <- eventReactive(input$fvp_go, {
    route <- fvp_route()
    if (is.null(route)) {
      return(list(available = FALSE, models = character(), data = data.frame()))
    }
    list(
      metric = route$base_metric,
      display_label = route$display_label,
      scenario = route$source_scenario,
      granularity = route$source_granularity,
      entity_label = route$entity_label,
      series = route$source_series_key,
      source_metric = route$source_metric,
      source_scenario = route$source_scenario,
      source_granularity = route$source_granularity,
      source_series_key = route$source_series_key,
      models = fvp_selected_models(),
      horizon = suppressWarnings(as.numeric(input$fvp_horizon)),
      history = suppressWarnings(as.numeric(input$fvp_history)),
      available = fvp_current_available(),
      data = fvp_case()
    )
  }, ignoreNULL = FALSE)

  output$fvp_chart <- highcharter::renderHighchart({
    if (!isTRUE(fvp_analysis_ready())) {
      if (isTRUE(fvp_forecast_only())) {
        return(fvp_empty_chart(paste(
          "Forecast-only route.",
          "No observed actuals or 15-model backtest estimates exist for this",
          "selection, so there is nothing to backtest.",
          "Use the Forecast section for the prepared forward forecast."
        )))
      }
      return(fvp_empty_chart(
        "Select Metric through Models, then click Analyze Backtest."
      ))
    }
    request <- fvp_request()
    if (!isTRUE(request$available)) {
      if (isTRUE(fvp_forecast_only())) {
        return(fvp_empty_chart(paste(
          "Forecast-only route.",
          "No observed actuals or 15-model backtest estimates exist for this",
          "selection. Nothing was fabricated."
        )))
      }
      return(fvp_empty_chart("Backtest not available for this combination."))
    }
    if (length(request$models) == 0) {
      return(fvp_empty_chart(
        "No models selected. Select at least one model and analyze again."
      ))
    }
    fvp_chart(
      request$series, request$models, request$horizon,
      request$history, request$data
    )
  })

  output$fvp_notes <- renderUI({
    if (!isTRUE(fvp_analysis_ready())) {
      return(tags$p(
        class = "fv-step-hint",
        "Click Analyze Backtest to see the analyzed setup and row counts."
      ))
    }
    request <- fvp_request()
    if (!isTRUE(request$available)) {
      return(tags$p(
        class = "fv-step-hint",
        "Backtest not available for this combination."
      ))
    }
    summary <- fvp_summary(
      request$series, request$models, request$horizon,
      request$history, request$data
    )
    cell <- function(label, value) {
      tags$div(
        class = "fv-avail-card",
        tags$div(class = "fv-avail-label", label),
        tags$div(class = "fv-avail-value", value)
      )
    }
    models_text <- if (summary$n_models == 0) {
      "\u2014"
    } else {
      paste(summary$models, collapse = ", ")
    }
    tagList(
      tags$div(
        class = "fv-avail-grid",
        cell("Metric", request$metric),
        cell("Prepared route", request$display_label),
        cell("Prepared scenario", request$scenario),
        cell("Granularity", request$granularity),
        cell(request$entity_label, summary$series),
        cell("Horizon (days)", summary$horizon),
        cell("Models selected", summary$n_models),
        cell("Actual points", summary$n_actual),
        cell("Forecast points", summary$rows_used),
        cell(
          "Date range",
          paste0(summary$date_min, " \u2192 ", summary$date_max)
        )
      ),
      tags$p(
        class = "fv-avail-note",
        paste0(
          "Source: forecast_viewer_model_outputs_v2_full.parquet \u00b7 models drawn: ",
          models_text, "."
        )
      )
    )
  })

  output$fvp_download_ui <- renderUI({
    if (!isTRUE(fvp_analysis_ready())) return(NULL)
    request <- fvp_request()
    if (!isTRUE(request$available) || length(request$models) == 0) return(NULL)
    downloadButton(
      "fvp_download", "Download analyzed rows",
      class = "btn btn-default btn-sm"
    )
  })

  output$fvp_download <- downloadHandler(
    filename = function() {
      request <- fvp_request()
      safe_key <- gsub("[^A-Za-z0-9_-]+", "_", request$series)
      paste0("AEGIS_V6_18_", safe_key, "_h", request$horizon, ".csv")
    },
    content = function(file) {
      request <- fvp_request()
      rows <- fvp_pilot_download_rows(
        request$source_metric, request$source_scenario,
        request$source_granularity, request$source_series_key,
        request$models, request$horizon, fvp_all
      )
      utils::write.csv(rows, file, row.names = FALSE, na = "")
    }
  )
}
