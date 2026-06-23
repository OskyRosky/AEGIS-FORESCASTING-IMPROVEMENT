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

  # Summary cards (selected series / model / horizon / counts).
  output$fv_summary_cards <- renderUI({
    s <- fv_summary(input$fv_entity, input$fv_model,
                    suppressWarnings(as.numeric(input$fv_horizon)),
                    suppressWarnings(as.numeric(input$fv_history)))
    fv_card <- function(label, value) {
      tags$div(class = "fv-summary-card",
               tags$div(class = "fv-summary-label", label),
               tags$div(class = "fv-summary-value", value))
    }
    tags$div(
      class = "fv-summary",
      fv_card("Series / entity", s$entity),
      fv_card("Model", s$model),
      fv_card("Horizon", s$horizon),
      fv_card("Actual observations", s$n_actual),
      fv_card("Forecast points", s$n_forecast)
    )
  })

  # Main interactive highcharter chart.
  output$fv_chart <- highcharter::renderHighchart({
    fv_chart(input$fv_entity, input$fv_model,
             suppressWarnings(as.numeric(input$fv_horizon)),
             suppressWarnings(as.numeric(input$fv_history)))
  })
  # Render even while the section is hidden so it is ready on first navigation;
  # custom.js dispatches a resize when the section is shown to reflow the chart.
  outputOptions(output, "fv_chart", suspendWhenHidden = FALSE)

  invisible(NULL)
}
