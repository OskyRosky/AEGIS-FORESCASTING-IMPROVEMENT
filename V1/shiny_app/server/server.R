# TESSERACT v2 | server.R | read-only server (Block 7.11 Forecast Viewer)

app_server <- function(input, output, session) {

  # --- Forecast Viewer (FORECASTING / Viewer) ------------------------------
  # Read-only reactivity: filters existing governed forecast/actual rows.
  # No model runs, no forecast generation, no metric recompute.

  # Keep the model selector in sync with the chosen entity.
  observeEvent(input$fv_entity, {
    models <- fv_models_for_entity(input$fv_entity)
    sel    <- if (length(models)) models[[1]] else character(0)
    updateSelectInput(session, "fv_model", choices = models, selected = sel)
  }, ignoreInit = TRUE)

  # Honest model-availability note under the model selector (reacts live to the
  # selected entity, before the chart is rendered).
  output$fv_model_note <- renderUI({
    ent     <- input$fv_entity
    models  <- fv_models_for_entity(ent)
    glob    <- fv_model_count_global()
    n_ent   <- length(models)
    note <- if (n_ent <= 1) {
      "Only one model is available for this selected series in the current forecast artifact."
    } else {
      paste0(n_ent, " models are available for this selected series.")
    }
    tags$div(
      class = "fv-model-note",
      tags$div(class = "fv-model-note-line", note),
      tags$div(class = "fv-model-note-diag",
               paste0("Available models for selected series: ", n_ent,
                      "  \u00b7  Total models in forecast artifacts: ", glob))
    )
  })

  # Snapshot the chosen setup ONLY when the user clicks "Analyze forecast".
  # eventReactive does not fire on init, so nothing renders before the click.
  fv_request <- eventReactive(input$fv_go, {
    list(
      entity  = input$fv_entity,
      model   = input$fv_model,
      horizon = suppressWarnings(as.numeric(input$fv_horizon)),
      history = suppressWarnings(as.numeric(input$fv_history))
    )
  })

  # Result column: empty state until the first click, then availability + chart.
  output$fv_view <- renderUI({
    if (is.null(input$fv_go) || input$fv_go == 0) {
      return(tags$div(
        class = "fv-empty-card",
        tags$div(class = "fv-empty-icon", "\u25C8"),
        tags$div(class = "fv-empty-title", "No forecast rendered yet"),
        tags$p(class = "fv-empty-text",
               "Choose a series, model, horizon, and history window, then click Analyze forecast to render the forecast.")
      ))
    }
    tagList(
      uiOutput("fv_availability"),
      tags$div(
        class = "fv-chart-wrap",
        highcharter::highchartOutput("fv_chart", height = "480px")
      )
    )
  })

  # E. Data-availability / explanation panel (snapshot of the analyzed setup).
  output$fv_availability <- renderUI({
    r  <- fv_request()
    av <- fv_availability(r$entity, r$model, r$horizon, r$history)
    cell <- function(label, value) {
      tags$div(class = "fv-avail-card",
               tags$div(class = "fv-avail-label", label),
               tags$div(class = "fv-avail-value", value))
    }
    horizon_val <- if (av$horizon_clipped) {
      paste0(av$horizon_displayed, " of ", av$horizon_requested, " (clipped)")
    } else {
      as.character(av$horizon_displayed)
    }
    tagList(
      tags$div(class = "fv-avail-title", "Forecast data availability"),
      tags$div(
        class = "fv-avail-grid",
        cell("Selected entity", av$entity),
        cell("Selected model", av$model),
        cell("Available forecast points", av$n_forecast_total),
        cell("Available history points", av$n_actual),
        cell("Models for this entity", av$n_models_entity),
        cell("Horizon requested (days)", av$horizon_requested),
        cell("Horizon points displayed", horizon_val),
        cell("Models in artifacts (global)", av$n_models_global)
      ),
      if (av$horizon_clipped)
        tags$p(class = "fv-avail-note",
               "Requested horizon exceeds the available forecast points for this series/model \u2014 showing all available points."),
      if (av$n_forecast_total == 0 && av$n_actual == 0)
        tags$p(class = "fv-avail-note",
               "No forecast data is available for this selected series/model/horizon.")
    )
  })

  # Main interactive highcharter chart (driven by the analyzed snapshot).
  output$fv_chart <- highcharter::renderHighchart({
    r <- fv_request()
    fv_chart(r$entity, r$model, r$horizon, r$history)
  })
  # Render even while the section is hidden so it is ready on first navigation;
  # custom.js dispatches a resize when the section is shown to reflow the chart.
  outputOptions(output, "fv_chart", suspendWhenHidden = FALSE)

  invisible(NULL)
}
