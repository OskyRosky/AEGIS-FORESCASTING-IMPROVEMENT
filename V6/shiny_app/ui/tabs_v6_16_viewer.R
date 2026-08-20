# V6.18 | Shared dynamic taxonomy UI for Viewer and Forecast.

section_explorer <- function() {
  horizon_opts <- fvp_horizon_choices()
  horizon_named <- stats::setNames(
    as.character(horizon_opts), paste0(horizon_opts, " days")
  )

  panel(
    "explorer",
    section_head(
      "Forecast Viewer",
      paste(
        "Actual values versus selected model backtests for governed,",
        "actual-bearing prepared routes."
      )
    ),
    home_collapse(
      "How to use this viewer",
      "Navigate the operational selection, configure the comparison, then analyze.",
      tags$ul(
        class = "fvb-how-list",
        tags$li("Metric is the first selection control."),
        tags$li("Only dimensions that apply to the selected operational route appear."),
        tags$li("All 596 governed HDD entities and exactly 15 AEGIS models remain available."),
        tags$li("Actual values are known history; model lines are prepared backtests."),
        tags$li("SSD-Phoenix is forecast-only and is not exposed in Viewer."),
        tags$li(
          "Shiny reads prepared metadata and Parquet; it does not train, backtest, ",
          "aggregate, extract, or write data."
        )
      ),
      open = FALSE
    ),
    tags$section(
      class = "fvx-section fvx-backtest fvb fvb-setup-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "A"),
        tags$h3(class = "fvx-section-title", "Selection"),
        tags$span(class = "pill pill-blue", "596 entities / 6 routes")
      ),
      tags$p(
        class = "fvb-setup-lead",
        paste(
          "Choose only the dimensions displayed for the branch.",
          "The breadcrumb and route cards resolve back to the V6.17 source fields."
        )
      ),
      taxonomy_navigation_ui("fvp_taxonomy")
    ),
    tags$section(
      class = "fvx-section fvx-backtest fvb fvb-setup-section fvb-config-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "B"),
        tags$h3(class = "fvx-section-title", "Backtest Configuration"),
        tags$span(class = "pill pill-slate", "15 verified models")
      ),
      uiOutput("fvp_availability"),
      tags$div(
        class = "fvb-controls fvb-analysis-controls",
        tags$div(
          class = "fvb-field fvb-field-horizon",
          tags$label(class = "fvb-field-label", "Horizon"),
          radioButtons(
            "fvp_horizon", NULL, choices = horizon_named,
            selected = "5", inline = TRUE
          ),
          tags$div(
            class = "fvb-horizon-unavail",
            lapply(
              fvp_horizon_unavailable(),
              function(horizon) tags$span(
                class = "fv-horizon-chip is-disabled",
                title = "Not available in the prepared productive artifact",
                paste0(horizon, " days")
              )
            ),
            tags$span(
              class = "fvb-field-hint",
              "Prepared artifact covers 1-30 day horizons."
            )
          )
        ),
        tags$div(
          class = "fvb-field fvb-field-history",
          tags$label(class = "fvb-field-label", "History Window"),
          selectInput(
            "fvp_history", NULL,
            choices = c(
              "Last 30 days" = 30,
              "Last 60 days" = 60,
              "Last 90 days" = 90,
              "Full available window" = 0
            ),
            selected = 0, width = "100%"
          ),
          tags$p(
            class = "fvb-field-hint",
            "Filters prepared backtest dates only."
          )
        )
      ),
      tags$div(
        class = "fvb-models",
        tags$div(
          class = "fvb-models-head",
          tags$span(class = "fvb-field-label", "Models"),
          uiOutput("fvp_model_count", inline = TRUE)
        ),
        uiOutput("fvp_model_groups"),
        tags$p(
          class = "fvb-field-hint",
          "All 15 verified AEGIS models are available and grouped by family."
        )
      ),
      tags$div(
        class = "fvb-analyze-row",
        tags$div(
          class = "fvb-analyze-label",
          tags$span(class = "fvb-field-label", "Analyze Backtest")
        ),
        tags$div(
          class = "fvb-action-buttons",
          uiOutput("fvp_analyze_button", inline = TRUE),
          actionButton(
            "fvp_reset_selection", "Reset Selection",
            class = "fvb-secondary-action"
          )
        ),
        tags$p(
          class = "fvb-field-hint fvb-analyze-hint",
          "Renders the chart and notes below. Updates only on click."
        )
      )
    ),
    home_collapse(
      "Results",
      "Actual values versus selected prepared model backtests.",
      tags$div(
        class = "fvb-result",
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvx-section-kicker", "C"),
          tags$span(class = "fvb-field-label", "Backtest Results")
        ),
        tags$div(
          class = "fv-chart-wrap fvb-chart-wrap",
          highcharter::highchartOutput("fvp_chart", height = "600px")
        ),
        tags$div(
          class = "fvb-result-head fvb-notes-head",
          tags$span(class = "fvb-field-label", "Selected-route notes"),
          uiOutput("fvp_download_ui")
        ),
        uiOutput("fvp_notes")
      ),
      open = TRUE
    ),
    tags$p(
      class = "fv-method-note",
      paste(
        "Source: forecast_viewer_model_outputs_v2_full.parquet.",
        "Shiny performs lazy filtering of the selected prepared entity only."
      )
    ),
    llm_explain_ui("llm_forecast_viewer", "Forecast Viewer")
  )
}

section_forecast <- function() {
  panel(
    "forecast",
    section_head(
      "Forward Forecast",
      paste(
        "What will the selected prepared model forecast over the next 30 or 60 days?",
        "HDD includes actual history; SSD-Phoenix remains forecast-only."
      )
    ),
    home_collapse(
      "How to use this forecast view",
      "Navigate the operational selection, configure windows, then analyze.",
      tags$ul(
        class = "fvb-how-list",
        tags$li("HDD includes prepared actual history and forward forecasts."),
        tags$li("SSD-Phoenix remains forecast-only; no actuals are fabricated."),
        tags$li(
          "The current SSD-Phoenix volume/efficiency variants are preserved ",
          "until a governed Organic/Inorganic mapping exists."
        ),
        tags$li(
          "CPU, IOPS, SSD-MCDB and Memory stop at explicit informational states ",
          "because productive inputs are absent."
        ),
        tags$li("The dashboard does not generate forecasts or select model versions.")
      ),
      open = FALSE
    ),
    tags$section(
      class = "fvx-section fvx-forward fvb fvb-setup-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "A"),
        tags$h3(class = "fvx-section-title", "Data Selection"),
        tags$span(class = "pill pill-teal", "896 entities / 8 routes")
      ),
      tags$p(
        class = "fvb-setup-lead",
        "Unsupported branches do not expose empty downstream selectors."
      ),
      taxonomy_navigation_ui("ffp_taxonomy")
    ),
    tags$section(
      class = "fvx-section fvx-forward fvb fvb-setup-section fvb-config-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "B"),
        tags$h3(class = "fvx-section-title", "Forecast Configuration"),
        tags$span(class = "pill pill-slate", "30 / 60+ day prepared view")
      ),
      tags$p(
        class = "fvb-setup-lead",
        "Configure the prepared future window and optional observed history."
      ),
      uiOutput("ffp_case_status"),
      tags$div(
        class = "fvb-controls fvb-analysis-controls",
        tags$div(
          class = "fvb-field fvb-field-history",
          tags$label(class = "fvb-field-label", "Forecast Window"),
          selectInput(
            "ffp_window", NULL,
            choices = c(
              "Next 30 days" = 30,
              "Next 60 days" = 60,
              "Next 180 days" = 180
            ),
            selected = 30, width = "100%"
          ),
          tags$p(
            class = "fvb-field-hint",
            "Draws only the selected prepared forward horizon."
          )
        ),
        uiOutput("ffp_history_control")
      ),
      tags$div(
        class = "fvb-analyze-row",
        tags$div(
          class = "fvb-analyze-label",
          tags$span(class = "fvb-field-label", "Analyze Forward Forecast")
        ),
        tags$div(
          class = "fvb-action-buttons",
          uiOutput("ffp_analyze_button", inline = TRUE),
          actionButton(
            "ffp_reset_selection", "Reset Selection",
            class = "fvb-secondary-action"
          )
        ),
        tags$p(
          class = "fvb-field-hint fvb-analyze-hint",
          "Renders the prepared chart and route notes below."
        )
      )
    ),
    home_collapse(
      "Forecast Results",
      "Actual history before Forecast start and the prepared forward-looking result.",
      tags$div(
        class = "fvb-result",
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvx-section-kicker", "C"),
          tags$span(class = "fvb-field-label", "Forward Forecast Chart")
        ),
        uiOutput("ffp_chart_legend"),
        tags$div(
          class = "fv-chart-wrap fvb-chart-wrap",
          highcharter::highchartOutput("ffp_chart", height = "560px")
        ),
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvb-field-label", "Forecast Data Notes")
        ),
        uiOutput("ffp_notes")
      ),
      open = TRUE
    ),
    tags$p(
      class = "fv-method-note",
      paste(
        "Source: forecast_forward_outputs_v6_17_full.parquet.",
        "Shiny lazily filters the frozen prepared artifact and remains read-only."
      )
    ),
    # V6.21B | Restores the Forward Forecast assistant lost in the V6.16
    # rewrite. llm_explain_server("llm_forecasting_forecast", ...) was still
    # registered in server/server.R with no live UI mount. Mock-only, read-only,
    # positioned consistently with the Viewer panel.
    llm_explain_ui("llm_forecasting_forecast", "Forward Forecast")
  )
}
