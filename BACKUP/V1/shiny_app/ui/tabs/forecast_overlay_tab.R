# TESSERACT v2 | forecast_overlay_tab.R | forecast overlay navigation panel
forecast_overlay_tab <- function() {
  nav_panel(
    "Forecast Overlay",
    icon = icon("chart-area"),
    div(
      class = "container-fluid py-3 px-4",
      div(
        class = "row g-2 mb-3",
        div(
          class = "col-md-3",
          selectInput(
            "sel_entity", "Entity:",
            choices = if (!is.null(actuals)) sort(unique(actuals$entity_key)) else c("Run setup.R first"),
            width = "100%"
          )
        ),
        div(
          class = "col-md-3",
          selectInput(
            "sel_horizon", "Horizon view:",
            choices = c("Full range", "Actuals only", "Forecast only"),
            width = "100%"
          )
        )
      ),
      div(
        class = "card border-0 shadow-sm mb-3",
        div(class = "card-body", plotlyOutput("chart_overlay", height = "360px"))
      ),
      div(
        class = "row g-3",
        div(
          class = "col-md-4",
          div(
            class = "card border-0 shadow-sm",
            div(
              class = "card-body",
              tags$small(class = "text-muted text-uppercase fw-semibold d-block mb-2",
                         style = "font-size:10px;", "Current TESSERACT"),
              uiOutput("overlay_stats_current")
            )
          )
        ),
        div(
          class = "col-md-4",
          div(
            class = "card border-0 shadow-sm",
            div(
              class = "card-body",
              tags$small(class = "text-muted text-uppercase fw-semibold d-block mb-2",
                         style = "font-size:10px;", "Best Candidate (Stage 5)"),
              p(class = "small text-muted fst-italic", "Available after Stage 5 - Model Lab")
            )
          )
        ),
        div(
          class = "col-md-4",
          div(
            class = "card border-0 shadow-sm",
            div(
              class = "card-body",
              tags$small(class = "text-muted text-uppercase fw-semibold d-block mb-2",
                         style = "font-size:10px;", "Delta (Stage 4+5)"),
              p(class = "small text-muted fst-italic", "Available after Stage 4 + Stage 5")
            )
          )
        )
      )
    )
  )
}
