# =====================================================================
# V6.0F-R8 | Viewer - Tesseract scenario explorer server
# ---------------------------------------------------------------------
# Consumes R/scenario_resolver.R only. Never reads the R6 fact CSV files.
# Series come from DuckDB through read-only parameterised queries.
# =====================================================================

VSX_EMPTY_MESSAGES <- list(
  no_storage      = "Governed storage is not available. Run the R7 build step to create data/storage/r6_phase1.duckdb.",
  no_selection    = "Select a metric, scenario, granularity and key to load a series.",
  no_data         = "No data for the selected combination in the current snapshot.",
  out_of_scope    = "Out of scope: Memory has no populated forecast source in Tesseract.",
  not_exposed     = "Scenario documented in the inventory but not exposed in this release.",
  not_in_phase1   = "Metric not available in Phase 1. CPU and IOPS are scheduled for the next extraction.",
  blocked         = "Blocked: the scenario mapping for this metric is still undefined.",
  forecast_only   = "Forecast-only: actuals are not available in Phase 1 for this metric and scenario."
)

.vsx_note_card <- function(kind, text) {
  cls <- switch(kind, warn = "pill pill-amber", info = "pill pill-blue", "pill pill-slate")
  tags$div(class = "fv-warn-card",
           tags$ul(class = "fv-warn-list",
                   tags$li(tags$span(class = cls, switch(kind, warn = "Notice",
                                                         info = "Info", "Status")), text)))
}

.vsx_empty_chart <- function(msg) {
  highcharter::highchart() |>
    highcharter::hc_title(text = NULL) |>
    highcharter::hc_subtitle(text = msg, align = "center",
                             style = list(fontSize = "13px", color = "#64748b")) |>
    highcharter::hc_xAxis(visible = FALSE) |>
    highcharter::hc_yAxis(visible = FALSE) |>
    highcharter::hc_credits(enabled = FALSE)
}

viewer_scenario_server <- function(input, output, session) {

  if (!exists("resolve_series_query")) return(invisible(NULL))

  # ---- cascade -------------------------------------------------------
  observeEvent(input$vsx_metric, {
    sc <- get_available_scenarios(input$vsx_metric)
    updateSelectInput(session, "vsx_scenario", choices = sc,
                      selected = if (length(sc)) sc[[1]] else character(0))
  }, ignoreInit = FALSE)

  observeEvent(list(input$vsx_metric, input$vsx_scenario), {
    req(input$vsx_metric, input$vsx_scenario)
    g <- get_available_granularities(input$vsx_metric, input$vsx_scenario)
    updateSelectInput(session, "vsx_granularity", choices = g,
                      selected = if (length(g)) g[[1]] else character(0))
  })

  observeEvent(list(input$vsx_metric, input$vsx_scenario, input$vsx_granularity), {
    req(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    k <- get_available_keys(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    pref <- k[tolower(k) == "namprd07"]
    updateSelectizeInput(session, "vsx_key", choices = k, server = TRUE,
                         selected = if (length(pref)) pref[[1]]
                                    else if (length(k)) k[[1]] else character(0))
  })

  # ---- resolution ----------------------------------------------------
  resolution <- reactive({
    req(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    key <- input$vsx_key
    if (is.null(key) || !nzchar(key)) return(NULL)
    resolve_series_query(input$vsx_metric, input$vsx_scenario, input$vsx_granularity,
                         key, version = input$vsx_version,
                         model_type = input$vsx_models, page = "viewer")
  })

  # The Viewer artifact is not versioned; only SSD-Phoenix resolves to a
  # versioned forecast table on this page.
  version_applies <- reactive({
    r <- resolution()
    !is.null(r) && identical(r$status, "AVAILABLE") && identical(r$table_name, "forecast_ssd")
  })

  output$vsx_version_ui <- renderUI({
    req(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    v <- get_available_versions(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    if (!version_applies() || !v$applies)
      return(selectInput("vsx_version", NULL, choices = c("Not applicable" = ""),
                         width = "100%"))
    sel <- selectInput("vsx_version", NULL, choices = v$versions,
                       selected = v$versions[[1]], width = "100%")
    if (v$single_version) tagList(sel) else sel
  })

  output$vsx_version_hint <- renderUI({
    req(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    v <- get_available_versions(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    txt <- if (!version_applies())
      "The Viewer artifact is not versioned. Forecast versions apply on the Forecast page."
    else if (v$single_version)
      paste("Only one forecast version exists for this selection.", v$note)
    else v$note
    tags$p(class = "fvb-field-hint", txt)
  })

  # ---- model / type ---------------------------------------------------
  model_meta <- reactive({
    req(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
    get_available_model_types(input$vsx_metric, input$vsx_scenario, input$vsx_granularity)
  })

  output$vsx_model_ui <- renderUI({
    m <- model_meta()
    if (!isTRUE(m$applies))
      return(tags$p(class = "fvb-field-hint",
                    "This source has no model dimension, so no model selector is shown."))
    grouped <- lapply(m$by_family, as.list)
    sel <- setdiff(m$model_types, "Actual")
    selectInput("vsx_models", NULL, choices = grouped,
                selected = utils::head(sel, 3), multiple = TRUE, width = "100%")
  })

  output$vsx_model_count <- renderUI({
    m <- model_meta()
    if (!isTRUE(m$applies)) return(tags$span(class = "pill pill-slate", "Not applicable"))
    tags$span(class = "pill pill-blue",
              sprintf("%d types \u00b7 %d families", length(m$model_types),
                      length(m$families)))
  })

  # ---- badge ----------------------------------------------------------
  output$vsx_badge <- renderUI({
    r <- resolution()
    if (is.null(r)) return(tags$span(class = "pill pill-slate", "No selection"))
    switch(r$status,
      AVAILABLE = if (identical(r$expected_mode, "FULL"))
                    tags$span(class = "pill pill-blue", "Actual + Forecast")
                  else tags$span(class = "pill pill-amber", "Forecast only"),
      OUT_OF_SCOPE = tags$span(class = "pill pill-slate", "Out of scope"),
      NOT_EXPOSED = tags$span(class = "pill pill-slate", "Not exposed"),
      NOT_AVAILABLE_IN_PHASE1 = tags$span(class = "pill pill-slate", "Not in Phase 1"),
      BLOCKED_O1 = tags$span(class = "pill pill-slate", "Blocked"),
      tags$span(class = "pill pill-slate", r$status))
  })

  # ---- data -----------------------------------------------------------
  series <- reactive({
    r <- resolution()
    if (is.null(r) || !identical(r$status, "AVAILABLE")) return(NULL)
    fetch_series_preview(input$vsx_metric, input$vsx_scenario, input$vsx_granularity,
                         input$vsx_key, version = input$vsx_version,
                         model_type = input$vsx_models, page = "viewer", limit = NULL)
  })

  output$vsx_state <- renderUI({
    if (!sr_storage_ready()) return(.vsx_note_card("warn", VSX_EMPTY_MESSAGES$no_storage))
    r <- resolution()
    if (is.null(r)) return(.vsx_note_card("info", VSX_EMPTY_MESSAGES$no_selection))
    msg <- switch(r$status,
                  AVAILABLE = NULL,
                  OUT_OF_SCOPE = VSX_EMPTY_MESSAGES$out_of_scope,
                  NOT_EXPOSED = VSX_EMPTY_MESSAGES$not_exposed,
                  NOT_AVAILABLE_IN_PHASE1 = VSX_EMPTY_MESSAGES$not_in_phase1,
                  BLOCKED_O1 = VSX_EMPTY_MESSAGES$blocked,
                  r$notes)
    if (!is.null(msg)) return(.vsx_note_card("warn", msg))
    if (identical(r$expected_mode, "FORECAST_ONLY"))
      return(.vsx_note_card("warn", VSX_EMPTY_MESSAGES$forecast_only))
    NULL
  })

  output$vsx_chart <- highcharter::renderHighchart({
    if (!sr_storage_ready()) return(.vsx_empty_chart(VSX_EMPTY_MESSAGES$no_storage))
    r <- resolution()
    if (is.null(r)) return(.vsx_empty_chart(VSX_EMPTY_MESSAGES$no_selection))
    if (!identical(r$status, "AVAILABLE"))
      return(.vsx_empty_chart(switch(r$status,
        OUT_OF_SCOPE = VSX_EMPTY_MESSAGES$out_of_scope,
        NOT_EXPOSED = VSX_EMPTY_MESSAGES$not_exposed,
        NOT_AVAILABLE_IN_PHASE1 = VSX_EMPTY_MESSAGES$not_in_phase1,
        BLOCKED_O1 = VSX_EMPTY_MESSAGES$blocked, r$status)))

    s <- series()
    d <- s$data
    if (is.null(d) || !nrow(d)) return(.vsx_empty_chart(VSX_EMPTY_MESSAGES$no_data))

    is_viewer_tbl <- identical(r$table_name, "viewer_hdd")
    d$.x <- as.Date(if (is_viewer_tbl) d$date else d$forecast_date)
    d$.y <- suppressWarnings(as.numeric(if (is_viewer_tbl) d$value else d$forecast_value))
    d$.g <- if (is_viewer_tbl)
              ifelse(tolower(trimws(d$series_type)) == "actual", "Actual",
                     trimws(d$model_type))
            else "Forecast"
    d <- d[!is.na(d$.x) & !is.na(d$.y), , drop = FALSE]   # no zero filling
    if (!nrow(d)) return(.vsx_empty_chart(VSX_EMPTY_MESSAGES$no_data))

    hc <- highcharter::highchart() |>
      highcharter::hc_chart(zoomType = "x") |>
      highcharter::hc_xAxis(type = "datetime") |>
      highcharter::hc_yAxis(title = list(text = "Value")) |>
      highcharter::hc_tooltip(shared = TRUE, valueDecimals = 2) |>
      highcharter::hc_legend(enabled = TRUE) |>
      highcharter::hc_credits(enabled = FALSE)

    groups <- unique(d$.g)
    groups <- c(intersect("Actual", groups), setdiff(groups, "Actual"))
    for (g in groups) {
      sub <- d[d$.g == g, , drop = FALSE]
      sub <- sub[order(sub$.x), , drop = FALSE]
      hc <- highcharter::hc_add_series(
        hc, name = g, type = "line",
        color = if (identical(g, "Actual")) "#0f172a" else NULL,
        lineWidth = if (identical(g, "Actual")) 3 else 2,
        marker = list(enabled = FALSE),
        data = lapply(seq_len(nrow(sub)), function(i)
          list(highcharter::datetime_to_timestamp(sub$.x[i]), sub$.y[i])))
    }
    hc
  })

  output$vsx_notes <- renderUI({
    r <- resolution()
    s <- series()
    if (is.null(r) || is.null(s) || is.null(s$data)) return(NULL)
    tags$div(
      class = "fv-warn-card",
      tags$ul(
        class = "fv-warn-list",
        tags$li(tags$span(class = "pill pill-slate", "Source"),
                sprintf("DuckDB table %s \u00b7 %s rows \u00b7 %.3f s",
                        r$table_name, format(s$rows, big.mark = ","), s$elapsed)),
        tags$li(tags$span(class = "pill pill-slate", "Key"),
                sprintf("Requested '%s'; matched case-insensitively against the stored value.",
                        input$vsx_key)),
        if (nzchar(r$notes))
          tags$li(tags$span(class = "pill pill-amber", "Note"), r$notes)
      )
    )
  })

  # These outputs sit inside a panel that is hidden at page load; without
  # suspendWhenHidden = FALSE they never compute (same pattern as fvp_*).
  for (.o in c("vsx_badge", "vsx_state", "vsx_version_ui", "vsx_version_hint",
               "vsx_model_ui", "vsx_model_count", "vsx_chart", "vsx_notes"))
    outputOptions(output, .o, suspendWhenHidden = FALSE)

  invisible(NULL)
}
