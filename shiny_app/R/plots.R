# TESSERACT v2 | plots.R | plotly chart builders
build_comparison_chart <- function(recommendations_data) {
  if (is.null(recommendations_data)) {
    return(
      plot_ly() %>%
        layout(
          title = "Run setup.R to generate sample data",
          paper_bgcolor = "rgba(0,0,0,0)",
          plot_bgcolor = "rgba(0,0,0,0)"
        )
    )
  }

  df <- recommendations_data %>% arrange(wmape_improvement_pct)

  plot_ly(
    data = df,
    y = ~reorder(entity_key, wmape_improvement_pct),
    x = ~wmape_improvement_pct,
    type = "bar",
    orientation = "h",
    name = "wMAPE improvement",
    marker = list(color = ifelse(df$wmape_improvement_pct < 0, APP_COLORS$improvement, APP_COLORS$decline))
  ) %>%
    layout(
      xaxis = list(title = "wMAPE delta from recommendations.csv (%)", ticksuffix = "%"),
      yaxis = list(title = "", automargin = TRUE),
      legend = list(orientation = "h", y = -0.18, x = 0),
      margin = list(l = 0, r = 10, t = 5, b = 40),
      paper_bgcolor = "rgba(0,0,0,0)",
      plot_bgcolor = "rgba(0,0,0,0)"
    )
}

build_overlay_chart <- function(actuals_data, forecasts_data, entity_key) {
  if (is.null(actuals_data) || is.null(forecasts_data)) {
    return(
      plot_ly() %>%
        layout(title = "Run setup.R to populate data", paper_bgcolor = "rgba(0,0,0,0)")
    )
  }

  act <- actuals_data %>% filter(entity_key == !!entity_key)
  fct <- forecasts_data %>% filter(entity_key == !!entity_key, model_group == "baseline")

  plot_ly() %>%
    add_lines(
      data = act, x = ~actual_date, y = ~value,
      name = "Actuals",
      line = list(color = APP_COLORS$actual, width = 2.5)
    ) %>%
    add_lines(
      data = fct, x = ~forecast_date, y = ~value,
      name = "Current TESSERACT (FixedGrowth1.5%)",
      line = list(color = APP_COLORS$primary, dash = "dash", width = 2)
    ) %>%
    layout(
      shapes = list(
        list(
          type = "line",
          x0 = FORECAST_START_DATE, x1 = FORECAST_START_DATE,
          y0 = 0, y1 = 1,
          yref = "paper",
          line = list(color = "#999", dash = "dot", width = 1)
        )
      ),
      annotations = list(
        list(
          x = FORECAST_START_DATE, y = 1, yref = "paper", xanchor = "left",
          text = "  Forecast start", showarrow = FALSE,
          font = list(color = "#999", size = 11)
        )
      ),
      xaxis = list(title = ""),
      yaxis = list(title = "TB"),
      legend = list(orientation = "h", y = -0.15, x = 0),
      paper_bgcolor = "rgba(0,0,0,0)",
      plot_bgcolor = "rgba(0,0,0,0)"
    )
}
