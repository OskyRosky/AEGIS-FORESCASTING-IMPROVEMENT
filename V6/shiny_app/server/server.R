# TESSERACT v2 | server.R | read-only server (Block 7.11-FULL-REBIND Forecast Viewer)

app_server <- function(input, output, session) {

  viewer_pilot_server(input, output, session)
  forecast_pilot_server(input, output, session)

  if (FALSE) {
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
        "Select a series, tick one or more models, choose a horizon, then click Analyze Backtest."))
    }
    r <- fvp_request()
    if (length(r$models) == 0) {
      return(fvp_empty_chart(
        "No models selected \u2014 tick at least one model and click Analyze Backtest again."))
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

  }

  if (FALSE) {
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
             paste0("View: forward production forecast  \u00b7  source: ",
                    s$source_file, " + actuals.csv  \u00b7  forecast span: ",
                    s$fwd_first, " \u2192 ", s$fwd_last, ".")),
      # ---- Governed prediction-interval metadata (read-only) ----
      if (isTRUE(s$has_intervals) && s$n_interval > 0) {
        tagList(
          tags$div(
            class = "fv-avail-grid",
            cell("Forecast artifact", s$source_file),
            cell("Interval shown", s$iv_levels),
            cell("Interval method", s$iv_method),
            cell("Calibrated horizon", s$iv_horizon),
            cell("Holdout coverage (80%)", s$iv_holdout),
            cell("Calibration method", s$iv_cal_method),
            cell("Calibration grain", s$iv_grain),
            cell("Calibration sample size", s$iv_sample)
          ),
          if (isTRUE(s$point_anomaly))
            tags$p(class = "fv-avail-note",
                   tags$span(class = "pill pill-amber", "Point anomaly"),
                   paste0(" forecast_point_scale_anomaly = TRUE for this key: the ",
                          "production point forecast scale is inconsistent with ",
                          "backtest/actuals. The interval is proportional to the ",
                          "point but does NOT correct the point forecast.")),
          if (!is.null(s$fwd_window) && !is.na(s$fwd_window) && s$fwd_window > 60)
            tags$p(class = "fv-avail-note",
                   "Prediction intervals are shown through forecast day 60; later forecast days are point forecast only."),
          tags$p(class = "fv-avail-note",
                 "Only the 80% prediction interval is displayed. Wider 95% intervals are intentionally not shown because heavy upper-tail historical residuals can make them visually excessive for operational review. Shiny only visualizes interval columns from the governed artifact; it does not compute intervals, residuals or quantiles.")
        )
      } else {
        tags$p(class = "fv-avail-note",
               if (identical(s$source_file, "forecasts.csv"))
                 "60-day calibrated interval artifact is not available; point forecast is shown only."
               else
                 "Prediction interval columns are not available for the selected rows; point forecast is shown only.")
      },
      if (s$n_forecast == 0)
        tags$p(class = "fv-avail-note",
               "No forward forecast rows were found after the last actual date for this series.")
    )
  })

  }

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
        cell("Route \u00d7 key cases covered", "\u2014"),
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
      cell("Route \u00d7 key cases covered", s$n_series),
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

  # Per-series binding KPI strip (gated on Analyze TTL).
  output$ttl_series_kpis <- renderUI({
    if (is.null(input$ttl_go) || input$ttl_go == 0) return(NULL)
    k <- ttl_series_kpi(ttl_request()$series, ttl_snap)
    cell <- function(label, value, sub = NULL, color = NULL, cls = "") {
      tags$div(class = paste("acc-kpi-card", cls),
               tags$div(class = "acc-kpi-label", label),
               tags$div(class = "acc-kpi-value",
                        style = if (!is.null(color)) paste0("color:", color, ";") else NULL,
                        value),
               if (!is.null(sub))
                 tags$div(class = "acc-kpi-label",
                          style = "margin-top:2px;font-weight:500;", sub))
    }
    tags$div(
      class = "acc-kpi-grid",
      cell("TTL (binding)", k$ttl_txt, sub = k$status, color = k$status_color),
      cell("Constraining resource", k$resource),
      cell("Utilization (today)", k$util_txt),
      cell("Method", k$method,
           sub = if (!identical(k$cross_txt, "\u2014")) paste0("crossover ", k$cross_txt) else "estimated TTL")
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

  # Keep TTL outputs alive across tab switches (render even while hidden) so the
  # page is fully populated the first time the user opens it.
  for (.ttl_out in c("ttl_summary_cards", "ttl_series_kpis", "ttl_gauge",
                     "ttl_line", "ttl_heatmap", "ttl_table")) {
    outputOptions(output, .ttl_out, suspendWhenHidden = FALSE)
  }

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
  # MODELS / CHAMPION PAGE MVP - BLOCK A + BLOCK B
  # Governed read-only champion decision display and series-level diagnostic
  # evidence. No composite score, weights, metrics, forecasts, tournaments, or
  # champion decisions are computed here.
  # ==========================================================================
  output$champion_conditions_table <- DT::renderDataTable({
    champion_conditions_table()
  })

  output$champion_sources_table <- DT::renderDataTable({
    champion_sources_table()
  })

  output$champion_leadership_count_chart <- plotly::renderPlotly({
    champion_leadership_count_chart()
  })

  output$champion_series_evidence_table <- DT::renderDataTable({
    champion_series_evidence_table()
  })

  output$champion_exceptions_table <- DT::renderDataTable({
    champion_exceptions_table()
  })

  # Champion diagnostic outputs live inside collapsible sections (some closed by
  # default); render eagerly so DT/plotly do not blank when initially hidden.
  outputOptions(output, "champion_leadership_count_chart", suspendWhenHidden = FALSE)
  outputOptions(output, "champion_series_evidence_table",  suspendWhenHidden = FALSE)

  # Governance: Risk Register ------------------------------------------------
  output$risk_register_table <- DT::renderDataTable({
    risk_register_table()
  })

  output$risk_deferred_models_table <- DT::renderDataTable({
    risk_deferred_models_table()
  })

  # Risk tables live inside collapsible sections; render eagerly so DT does not
  # blank when a box is initially collapsed.
  outputOptions(output, "risk_register_table",         suspendWhenHidden = FALSE)
  outputOptions(output, "risk_deferred_models_table",  suspendWhenHidden = FALSE)

  # Governance: Audit Trail --------------------------------------------------
  output$audit_findings_table <- DT::renderDataTable({
    audit_findings_table()
  })

  output$audit_next_steps_table <- DT::renderDataTable({
    audit_next_steps_table()
  })

  # Reference: Source Artifacts ----------------------------------------------
  output$artifact_lineage_table <- DT::renderDataTable({
    artifact_lineage_table()
  })

  output$artifact_catalog_table <- DT::renderDataTable({
    artifact_catalog_table()
  })

  # V4.7C | Governed artifact downloads. Each curated CSV opens a
  # multi-format modal: CSV is served VERBATIM from its governed path
  # (read-only, no recomputation); MD/TXT/HTML/PDF/DOCX are rendered,
  # human-readable copies of the same governed data.
  register_artifact_downloads(input, output, session)

  # The chart + model picker / count / notes live in a section that is hidden at
  # page load; render them eagerly (suspendWhenHidden = FALSE) so the static
  # chart containers and controls are populated on first navigation. custom.js
  # dispatches a resize when the section is shown to reflow the charts.
  outputOptions(output, "fvp_chart",        suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_model_groups", suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_model_count",  suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_notes",        suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_availability",         suspendWhenHidden = FALSE)
  outputOptions(output, "fvp_download_ui",          suspendWhenHidden = FALSE)
  outputOptions(output, "ffp_case_status",         suspendWhenHidden = FALSE)
  outputOptions(output, "ffp_history_control",     suspendWhenHidden = FALSE)
  outputOptions(output, "ffp_chart",               suspendWhenHidden = FALSE)
  outputOptions(output, "ffp_notes",               suspendWhenHidden = FALSE)
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
  outputOptions(output, "champion_leadership_count_chart", suspendWhenHidden = FALSE)
  outputOptions(output, "champion_series_evidence_table",  suspendWhenHidden = FALSE)
  outputOptions(output, "champion_exceptions_table",       suspendWhenHidden = FALSE)
  outputOptions(output, "risk_register_table",             suspendWhenHidden = FALSE)
  outputOptions(output, "risk_deferred_models_table",      suspendWhenHidden = FALSE)
  outputOptions(output, "audit_findings_table",            suspendWhenHidden = FALSE)
  outputOptions(output, "audit_next_steps_table",          suspendWhenHidden = FALSE)
  outputOptions(output, "artifact_lineage_table",          suspendWhenHidden = FALSE)
  outputOptions(output, "artifact_catalog_table",          suspendWhenHidden = FALSE)

  # V4.6 | On-demand local LLM explanation panels (mock, read-only).
  # Each renders a precomputed V4.4 mock response when the user clicks.
  # No compute, no LLM, no Azure, no champion/governance change.
  # V4.7B expands coverage to the 9 governed MVP modules (Models, Forecasting,
  # Governance). The Viewer (explorer) reuses the forecast_viewer response.
  llm_explain_server("llm_models_universe",     "models_universe")
  llm_explain_server("llm_tournament",          "tournament")
  llm_explain_server("llm_champion_overview",   "champion_overview")
  llm_explain_server("llm_forecast_viewer",     "forecast_viewer")
  llm_explain_server("llm_forecasting_accuracy", "forecasting_accuracy")
  llm_explain_server("llm_forecasting_forecast", "forecasting_forecast")
  llm_explain_server("llm_forecasting_ttl",     "forecasting_ttl")
  llm_explain_server("llm_governance_risks",    "governance_risks")
  llm_explain_server("llm_governance_audit",    "governance_audit")

  # V4.7C | Reference / Artifacts assistant (explains the governed
  # artifacts, their relationships and how to interpret them). Uses a
  # custom 5-prompt set; read-only, never decides.
  llm_explain_server("llm_reference_artifacts", "reference_artifacts",
                     quick_prompts = .LLM_REFERENCE_ARTIFACTS_PROMPTS)

  invisible(NULL)
}
