# TESSERACT v2 | forecast_overlay_server.R | forecast overlay outputs
forecast_overlay_server <- function(input, output, session) {
  output$chart_overlay <- renderPlotly({
    build_overlay_chart(actuals, forecasts, input$sel_entity)
  })

  output$overlay_stats_current <- renderUI({
    if (is.null(actuals) || is.null(forecasts)) {
      return(p(class = "small text-muted", "No data"))
    }

    rec <- if (!is.null(recommendations)) {
      recommendations %>% filter(entity_key == input$sel_entity)
    } else {
      NULL
    }

    model_name <- if (!is.null(rec) && nrow(rec) > 0) rec$current_model[1] else "FixedGrowth1.5%"

    tagList(
      p(class = "small mb-1", tags$strong("Model: "), tags$code(model_name)),
      p(class = "small text-muted mb-0 fst-italic", "wMAPE · MASE · Bias available in Stage 4")
    )
  })
}
