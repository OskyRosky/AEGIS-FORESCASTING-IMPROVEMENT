# TESSERACT v2 | server.R | read-only server (Block 7.11-FULL-REBIND Forecast Viewer)

app_server <- function(input, output, session) {

  # --- Forecast Viewer SECTION 1 : BACKTEST COMPARISON (full artifact) ------
  # Read-only reactivity: filters / reshapes existing rows from the Stage 05H
  # FULL artifact (forecast_viewer_model_outputs.csv) for charting only.
  # No model runs, no forecast generation, no metric recompute, no champion
  # change, and no persisted reshaped data.

  fvp_all <- fvp_data()  # cached governed read (parsed once at loader init)

  # Grouped model checkboxes for the selected series (re-renders on series
  # change). One checkboxGroupInput per model family; recommended defaults are
  # pre-ticked where available.
  output$fvp_model_groups <- renderUI({
    series <- input$fvp_series
    meta   <- fvp_model_meta(series, fvp_all)
    if (nrow(meta) == 0) {
      return(tags$p(class = "fv-step-hint",
                    "No models are available for this series in the pilot artifact."))
    }
    defaults <- intersect(fvp_default_models(), meta$model_name)
    fams <- FVP_FAMILY_ORDER[FVP_FAMILY_ORDER %in% meta$model_family]
    groups <- lapply(fams, function(fam) {
      rows <- meta[meta$model_family == fam, , drop = FALSE]
      choice_names <- lapply(seq_len(nrow(rows)), function(i) {
        tags$span(fvp_model_label(rows$model_name[i],
                                  rows$is_selected_champion[i],
                                  rows$risk_status[i]))
      })
      tags$div(
        class = "fvp-fam-group",
        tags$div(class = "fvp-fam-label",
                 if (!is.na(FVP_FAMILY_LABELS[fam])) FVP_FAMILY_LABELS[[fam]] else fam),
        checkboxGroupInput(
          inputId  = paste0("fvp_models_", fam),
          label    = NULL,
          choiceNames  = choice_names,
          choiceValues = as.list(rows$model_name),
          selected = intersect(defaults, rows$model_name)
        )
      )
    })
    tags$div(class = "fvp-model-grid", groups)
  })

  # Combined currently-selected models across the per-family checkbox groups.
  fvp_selected_models <- reactive({
    sel <- unlist(lapply(FVP_FAMILY_ORDER, function(f) {
      input[[paste0("fvp_models_", f)]]
    }), use.names = FALSE)
    sel <- sel[!is.na(sel) & nzchar(sel)]
    unique(sel)
  })

  # Live count of selected models (under the model picker, before Analyze).
  output$fvp_model_count <- renderUI({
    n <- length(fvp_selected_models())
    txt <- if (n == 0) {
      "No models selected yet \u2014 tick at least one model."
    } else {
      paste0(n, if (n == 1) " model selected." else " models selected.")
    }
    tags$div(class = "fv-model-note",
             tags$div(class = "fv-model-note-line", txt))
  })

  # Snapshot the chosen setup ONLY when the user clicks "Analyze Forecast".
  fvp_request <- eventReactive(input$fvp_go, {
    list(
      series  = input$fvp_series,
      models  = fvp_selected_models(),
      horizon = suppressWarnings(as.numeric(input$fvp_horizon)),
      history = suppressWarnings(as.numeric(input$fvp_history))
    )
  }, ignoreNULL = FALSE)

  # STATIC chart: the container is always in the DOM (declared in tabs.R), which
  # fixes the previous blank-chart regression. Before the first Analyze click we
  # render a calm empty state into the live container; afterwards we render the
  # multi-model chart from the analyzed snapshot.
  output$fvp_chart <- highcharter::renderHighchart({
    if (is.null(input$fvp_go) || input$fvp_go == 0) {
      return(fvp_empty_chart(
        "Select a series, tick one or more models, choose a horizon, then click Analyze Forecast."))
    }
    r <- fvp_request()
    if (length(r$models) == 0) {
      return(fvp_empty_chart(
        "No models selected \u2014 tick at least one model and click Analyze Forecast again."))
    }
    fvp_chart(r$series, r$models, r$horizon, r$history, fvp_all)
  })

  # Data notes (Section 7): snapshot of what the chart is showing.
  output$fvp_notes <- renderUI({
    if (is.null(input$fvp_go) || input$fvp_go == 0) {
      return(tags$p(class = "fv-step-hint",
                    "Click Analyze Backtest to see a summary of the rendered series, models, horizon and date range."))
    }
    r <- fvp_request()
    s <- fvp_summary(r$series, r$models, r$horizon, r$history, fvp_all)
    cell <- function(label, value) {
      tags$div(class = "fv-avail-card",
               tags$div(class = "fv-avail-label", label),
               tags$div(class = "fv-avail-value", value))
    }
    models_txt <- if (s$n_models == 0) "\u2014" else paste(s$models, collapse = ", ")
    tagList(
      tags$div(
        class = "fv-avail-grid",
        cell("Series", s$series),
        cell("Models selected", s$n_models),
        cell("Horizon (days)", s$horizon),
        cell("Actual points", s$n_actual),
        cell("Forecast points drawn", s$rows_used),
        cell("Date range", paste0(s$date_min, " \u2192 ", s$date_max))
      ),
      tags$p(class = "fv-avail-note",
             paste0("View: historical backtest comparison  \u00b7  source: ",
                    "forecast_viewer_model_outputs.csv  \u00b7  models drawn: ",
                    models_txt, ".")),
      if (s$rows_used == 0 && s$n_actual == 0)
        tags$p(class = "fv-avail-note",
               "No data was found for this series / model / horizon combination in the full artifact.")
    )
  })

  # --- Forecast Viewer SECTION 2 : FORWARD FORECAST ------------------------
  # Read-only: observed actuals (actuals.csv) + forward production forecast
  # (forecasts.csv). Single model_version per series, no multi-model picker,
  # no horizon selector. Action-gated on the "Analyze Forward Forecast" button.
  fvf_fdf <- fvf_forecasts()   # cached governed read (forward production)
  fvf_adf <- fvf_actuals()     # cached governed read (observed history)

  # Production model metadata for the selected series (updates on series change,
  # but only as a metadata note - it does NOT draw the chart).
  output$fvf_model_note <- renderUI({
    series <- input$fvf_series
    mver   <- fvf_model_version(series, fvf_fdf)
    bnd    <- fvf_boundary_date(series, fvf_adf)
    bnd_txt <- if (is.na(bnd)) "\u2014" else format(bnd, "%Y-%m-%d")
    tags$div(class = "fv-model-note",
             tags$div(class = "fv-model-note-line",
                      paste0("Production model: ", mver)),
             tags$div(class = "fv-model-note-diag",
                      paste0("Last actual (forecast start boundary): ", bnd_txt,
                             ". Single-model forward forecast \u2014 no model comparison here.")))
  })

  # Snapshot the forward setup ONLY when "Analyze Forward Forecast" is clicked.
  fvf_request <- eventReactive(input$fvf_go, {
    list(
      series  = input$fvf_series,
      window  = suppressWarnings(as.numeric(input$fvf_window)),
      history = suppressWarnings(as.numeric(input$fvf_history))
    )
  }, ignoreNULL = FALSE)

  # STATIC forward chart container: empty state before the first Analyze click,
  # then actual history + forward forecast with the "Forecast start" boundary.
  output$fvf_chart <- highcharter::renderHighchart({
    if (is.null(input$fvf_go) || input$fvf_go == 0) {
      return(fvf_empty_chart(
        "Select a series, a forecast window and an actual-history window, then click Analyze Forward Forecast."))
    }
    r <- fvf_request()
    fvf_chart(r$series, r$window, r$history, fvf_fdf, fvf_adf)
  })

  # Forward data notes: snapshot of what the forward chart is showing.
  output$fvf_notes <- renderUI({
    if (is.null(input$fvf_go) || input$fvf_go == 0) {
      return(tags$p(class = "fv-step-hint",
                    "Click Analyze Forward Forecast to see a summary of the actual history, forward forecast and boundary."))
    }
    r <- fvf_request()
    s <- fvf_summary(r$series, r$window, r$history, fvf_fdf, fvf_adf)
    cell <- function(label, value) {
      tags$div(class = "fv-avail-card",
               tags$div(class = "fv-avail-label", label),
               tags$div(class = "fv-avail-value", value))
    }
    tagList(
      tags$div(
        class = "fv-avail-grid",
        cell("Series", s$series),
        cell("Model version", s$model_version),
        cell("Forecast start", s$boundary),
        cell("Actual points", s$n_actual),
        cell("Forecast points", s$n_forecast),
        cell("Date range", paste0(s$date_min, " \u2192 ", s$date_max))
      ),
      tags$p(class = "fv-avail-note",
             paste0("View: forward production forecast  \u00b7  source: forecasts.csv + actuals.csv  \u00b7  forecast span: ",
                    s$fwd_first, " \u2192 ", s$fwd_last, ".")),
      if (s$n_forecast == 0)
        tags$p(class = "fv-avail-note",
               "No forward forecast rows were found after the last actual date for this series.")
    )
  })

  # ==========================================================================
  # ACCURACY PAGE MVP (acc_*) -- heatmap-first backtest diagnostics.
  # Read-only, computed in memory from the frozen Stage 05H backtest artifact.
  # Action-gated: nothing renders until the user clicks Analyze Accuracy.
  # ==========================================================================
  acc_all <- acc_data()

  # Snapshot the accuracy setup ONLY when "Analyze Accuracy" is clicked.
  acc_request <- eventReactive(input$acc_go, {
    list(
      horizon = suppressWarnings(as.numeric(input$acc_horizon)),
      metric  = input$acc_metric,
      models  = input$acc_models,
      series  = input$acc_series,
      topn    = suppressWarnings(as.numeric(input$acc_topn))
    )
  }, ignoreNULL = FALSE)

  # Computed diagnostics for the current snapshot (per series x model).
  acc_result <- reactive({
    r <- acc_request()
    models <- if (is.null(r$models) || length(r$models) == 0 ||
                  "__ALL__" %in% r$models) NULL else r$models
    series <- if (is.null(r$series) || length(r$series) == 0) NULL else r$series
    acc_compute(r$horizon, models, series, r$metric, acc_all)
  })

  # Summary cards at the top of the page.
  output$acc_summary_cards <- renderUI({
    cell <- function(label, value, cls = "") {
      tags$div(class = paste("acc-kpi-card", cls),
               tags$div(class = "acc-kpi-label", label),
               tags$div(class = "acc-kpi-value", value))
    }
    if (is.null(input$acc_go) || input$acc_go == 0) {
      return(tags$div(
        class = "acc-kpi-grid",
        cell("Series covered", "\u2014"),
        cell("Models covered", "\u2014"),
        cell("Selected horizon", "\u2014"),
        cell("Selected metric", "\u2014"),
        cell("Worst error pocket", "Click Analyze Accuracy", "acc-kpi-wide"),
        cell("Most stable pocket", "Click Analyze Accuracy", "acc-kpi-wide")
      ))
    }
    r <- acc_request()
    s <- acc_summary(acc_result(), r$metric, r$horizon)
    tags$div(
      class = "acc-kpi-grid",
      cell("Series covered", s$n_series),
      cell("Models covered", s$n_models),
      cell("Selected horizon", paste0(s$horizon, " days")),
      cell("Selected metric", s$metric),
      cell("Worst error pocket", s$worst, "acc-kpi-wide acc-kpi-bad"),
      cell("Most stable pocket", s$stable, "acc-kpi-wide acc-kpi-good")
    )
  })

  # STATIC heatmap container: empty state before the first Analyze click.
  output$acc_heatmap <- plotly::renderPlotly({
    if (is.null(input$acc_go) || input$acc_go == 0) {
      return(acc_empty_plot(
        "Choose a horizon, metric and filters, then click Analyze Accuracy."))
    }
    r <- acc_request()
    acc_heatmap(acc_result(), metric = r$metric, horizon = r$horizon,
                top_n = r$topn)
  })

  # Supporting diagnostics table (raw values + standardized score).
  output$acc_table <- DT::renderDataTable({
    if (is.null(input$acc_go) || input$acc_go == 0) {
      return(DT::datatable(
        data.frame(Message = "Click Analyze Accuracy to populate the metric table."),
        rownames = FALSE, options = list(dom = "t")))
    }
    r <- acc_request()
    acc_table(acc_result(), metric = r$metric)
  })

  # ==========================================================================
  # TTL PROTOTYPE (ttl_*) -- Time-to-Live / capacity view.
  # DEMAND = real forecast; SUPPLY + TTL = simulated. Read-only, not governed.
  # Band-count cards + heatmap + table render immediately (global view); the
  # per-series gauge and supply/demand line are gated behind Analyze TTL.
  # ==========================================================================
  ttl_snap <- ttl_snapshot()
  ttl_ts   <- ttl_timeseries()

  ttl_request <- eventReactive(input$ttl_go, {
    list(series = input$ttl_series)
  }, ignoreNULL = FALSE)

  # Band-count KPI cards (global; shown immediately).
  output$ttl_summary_cards <- renderUI({
    cell <- function(label, value, cls = "") {
      tags$div(class = paste("acc-kpi-card", cls),
               tags$div(class = "acc-kpi-label", label),
               tags$div(class = "acc-kpi-value", value))
    }
    s <- ttl_summary(ttl_snap)
    tags$div(
      class = "acc-kpi-grid",
      cell("Series", s$n_series),
      cell("Alert (< 3 mo)", s$n_alert, "acc-kpi-bad"),
      cell("Warning (3\u20136 mo)", s$n_warning),
      cell("Healthy (6\u201312 mo)", s$n_healthy, "acc-kpi-good"),
      cell("Cool (12+ mo)", s$n_cool),
      cell("Soonest crossover", paste0(s$soonest, " \u00b7 ", s$soonest_mtl),
           "acc-kpi-wide acc-kpi-bad")
    )
  })

  # Per-series gauge (gated on Analyze TTL).
  output$ttl_gauge <- highcharter::renderHighchart({
    if (is.null(input$ttl_go) || input$ttl_go == 0) {
      return(ttl_empty_gauge("Select a series and click Analyze TTL."))
    }
    ttl_gauge(ttl_request()$series, ttl_snap)
  })

  # Per-series supply vs demand line + crossover (gated on Analyze TTL).
  output$ttl_line <- highcharter::renderHighchart({
    if (is.null(input$ttl_go) || input$ttl_go == 0) {
      return(ttl_empty_chart("Select a series and click Analyze TTL."))
    }
    ttl_line_chart(ttl_request()$series, ttl_ts, ttl_snap)
  })

  # Fleet utilization heatmap (global; all series).
  output$ttl_heatmap <- plotly::renderPlotly({
    ttl_heatmap(ttl_ts, ttl_snap)
  })

  # Snapshot table (global; all series, most-urgent first).
  output$ttl_table <- DT::renderDataTable({
    ttl_table(ttl_snap)
  })

  # ==========================================================================
  # MODELS / TOURNAMENT PAGE MVP
  # Governed read-only display from tournament_model_scorecard.csv and
  # tournament_pairwise_evidence.csv. No composite score, weights, metrics,
  # forecasts, tournaments, or champion decisions are computed here.
  # ==========================================================================
  output$tournament_standings_table <- DT::renderDataTable({
    tournament_standings_table()
  })

  output$tournament_mase_rmsse_plot <- plotly::renderPlotly({
    tournament_tradeoff_plot()
  })

  output$tournament_pairwise_table <- DT::renderDataTable({
    tournament_pairwise_table()
  })

  # ==========================================================================
  # MODELS / CHAMPION PAGE MVP - BLOCK A
  # Governed read-only champion decision display. No series-level evidence,
  # composite score, weights, metrics, forecasts, tournaments, or champion
  # decisions are computed here.
  # ==========================================================================
  output$champion_conditions_table <- DT::renderDataTable({
    champion_conditions_table()
  })

  output$champion_sources_table <- DT::renderDataTable({
    champion_sources_table()
  })

  # The chart + model picker / count / notes live in a section that is hidden at
  # page load; render them eagerly (suspendWhenHidden = FALSE) so the static
  # chart containers and controls are populated on first navigation. custom.js
  # dispatches a resize when the section is shown to reflow the charts.
  outputOptions(output, "fvp_chart",        suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_model_groups", suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_model_count",  suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_notes",        suspendWhenHidden = FALSE)
  outputOptions(output, "fvf_chart",        suspendWhenHidden = FALSE)
  outputOptions(output, "fvf_model_note",   suspendWhenHidden = FALSE)
  outputOptions(output, "fvf_notes",        suspendWhenHidden = FALSE)
  outputOptions(output, "acc_summary_cards", suspendWhenHidden = FALSE)
  outputOptions(output, "acc_heatmap",       suspendWhenHidden = FALSE)
  outputOptions(output, "acc_table",         suspendWhenHidden = FALSE)
  outputOptions(output, "ttl_summary_cards", suspendWhenHidden = FALSE)
  outputOptions(output, "ttl_gauge",         suspendWhenHidden = FALSE)
  outputOptions(output, "ttl_line",          suspendWhenHidden = FALSE)
  outputOptions(output, "ttl_heatmap",       suspendWhenHidden = FALSE)
  outputOptions(output, "ttl_table",         suspendWhenHidden = FALSE)
  outputOptions(output, "tournament_standings_table", suspendWhenHidden = FALSE)
  outputOptions(output, "tournament_mase_rmsse_plot", suspendWhenHidden = FALSE)
  outputOptions(output, "tournament_pairwise_table",  suspendWhenHidden = FALSE)
  outputOptions(output, "champion_conditions_table",  suspendWhenHidden = FALSE)
  outputOptions(output, "champion_sources_table",     suspendWhenHidden = FALSE)

  invisible(NULL)
}
