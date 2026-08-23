# TESSERACT v2 | tabs_v6_24_mvp.R
# V6.24 MVP | Four read-only pages over the governed P4-P7 artifacts.
#
# Every number rendered here is READ from navigation_contract / taxonomy_counts
# or from the governed series artifacts. Nothing on these pages is computed:
# no accuracy, no rankings, no forecasts, no backtests, no readiness, no counts.
#
# Structure follows the existing app: each page is a panel() keyed by
# data-section, switched client-side like every other section.

# ---------------------------------------------------------------- shared bits
# v24_badge / v24_badges_ui / v24_kv / v24_card are defined in
# R/v6_24_read_only_loader.R because the server renders with them too.

v24_horizon_banner <- function() {
  tags$div(
    class = "v24-horizon-banner",
    tags$strong(V6_24_FORECAST_TYPE),
    tags$span(paste0(" \u2014 ", V6_24_FORECAST_STEPS, " daily steps. ",
                     "This MVP forecasts ", V6_24_FORECAST_STEPS,
                     " days ahead of each series' last observed actual. ",
                     "It is not a multi-year forecast."))
  )
}

v24_section_head <- function(title, subtitle) {
  tags$div(
    class = "v24-head",
    tags$h2(class = "v24-title", title),
    tags$p(class = "v24-sub", subtitle),
    v24_horizon_banner()
  )
}

# Cascading filter controls. Options are rendered by the server from
# navigation_contract, so the UI cannot offer a path that has no series.
v24_filter_bar <- function(ns_prefix) {
  tags$div(
    class = "v24-filterbar",
    tags$div(class = "v24-filterbar-head",
             tags$strong("Select a series"),
             tags$span(class = "v24-note",
                       "Filter options come from navigation_contract. Only paths ",
                       "with at least one available series are offered.")),
    tags$div(
      class = "v24-filter-row",
      lapply(V6_24_FILTER_AXES, function(ax) {
        tags$div(class = "v24-filter-cell",
                 uiOutput(paste0(ns_prefix, "_sel_", ax)))
      })
    ),
    tags$div(class = "v24-filter-status", uiOutput(paste0(ns_prefix, "_status")))
  )
}

# ---------------------------------------------------------------- 1. Overview

section_v24_overview <- function() {
  panel(
    "v24_overview",
    v24_section_head(
      "V6.24 MVP \u2014 Overview",
      paste("Governed product coverage read from navigation_contract and",
            "taxonomy_counts. No value on this page is computed in Shiny.")),
    tags$div(class = "v24-cards", uiOutput("v24_ov_cards")),
    tags$div(
      class = "v24-grid-2",
      tags$div(class = "v24-panel",
               tags$h3("Coverage by metric"),
               DT::DTOutput("v24_ov_by_metric")),
      tags$div(class = "v24-panel",
               tags$h3("Availability and signal quality"),
               DT::DTOutput("v24_ov_by_signal"))
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Aggregation policy"),
      tags$ul(
        class = "v24-list",
        tags$li(tags$strong("Medians only. "),
                "Product tiles use median WAPE / SMAPE / RMSE / MAE. Mean error ",
                "is not shown anywhere: a handful of degenerate series-model ",
                "pairs push the cohort mean WAPE to ~6.7e19 while the median ",
                "is ~0.06."),
        tags$li(tags$strong("Series-weighted. "),
                "Each series contributes its own median once. Backtest density ",
                "differs by metric, so row weighting would over-weight the ",
                "densest metric."),
        tags$li(tags$strong("Missing is not zero. "),
                "A median that is not computable is shown as ",
                tags$em("not computable"), ", never as 0.")
      )
    ),
    tags$div(class = "v24-panel",
             tags$h3("Artifact load status"),
             DT::DTOutput("v24_ov_loader"))
  )
}

# ---------------------------------------------------------------- 2. Viewer

section_v24_viewer <- function() {
  panel(
    "v24_viewer",
    v24_section_head(
      "V6.24 MVP \u2014 Series Viewer",
      paste("Observed history and governed backtests for one selected series.",
            "Accuracy and rankings are read from the artifacts, never",
            "recalculated here.")),
    v24_filter_bar("v24_vw"),
    tags$div(class = "v24-panel", uiOutput("v24_vw_identity")),
    tags$div(class = "v24-panel", uiOutput("v24_vw_champion")),
    tags$div(
      class = "v24-panel",
      tags$h3("Observed history"),
      plotly::plotlyOutput("v24_vw_actuals", height = "320px")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Backtest \u2014 actual versus model prediction"),
      tags$div(class = "v24-inline-ctl", uiOutput("v24_vw_model_sel")),
      plotly::plotlyOutput("v24_vw_backtest", height = "340px")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Model ranking for this series"),
      tags$p(class = "v24-note", uiOutput("v24_vw_rank_note", inline = TRUE)),
      DT::DTOutput("v24_vw_ranking")
    )
  )
}

# ---------------------------------------------------------------- 3. Forecast

section_v24_forecast <- function() {
  panel(
    "v24_forecast",
    v24_section_head(
      "V6.24 MVP \u2014 Forecast",
      paste("Governed 30-step forward forecast for one selected series, read",
            "verbatim from forecast_outputs. No forecast is generated here.")),
    v24_filter_bar("v24_fc"),
    tags$div(class = "v24-panel", uiOutput("v24_fc_identity")),
    tags$div(
      class = "v24-panel",
      tags$h3("Forecast"),
      tags$div(class = "v24-inline-ctl", uiOutput("v24_fc_model_sel")),
      plotly::plotlyOutput("v24_fc_chart", height = "360px")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Forecast rows"),
      tags$p(class = "v24-note",
             "predicted_value is shown exactly as the model produced it. ",
             "Negative and extreme values are flagged, never clipped."),
      DT::DTOutput("v24_fc_table")
    )
  )
}

# ---------------------------------------------------------------- 4. Taxonomy

section_v24_taxonomy <- function() {
  panel(
    "v24_taxonomy",
    v24_section_head(
      "V6.24 MVP \u2014 Taxonomy and Availability",
      paste("Counts read verbatim from taxonomy_counts. Shiny does not",
            "recompute any count on this page.")),
    tags$div(
      class = "v24-panel",
      tags$h3("Notes"),
      tags$ul(
        class = "v24-list",
        tags$li("Key is a routing/display value, not a global canonical axis. ",
                "102 distinct keys cover 140 series, so a key alone does not ",
                "identify a series \u2014 the six-level filter path does."),
        tags$li("Filter options are constrained to valid product paths. ",
                "An option is only offered when at least one available series ",
                "sits behind it."),
        tags$li("Conditional axes are carried explicitly as NOT_APPLICABLE or ",
                "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE. They are shown as they ",
                "are, never renamed or dropped.")
      )
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Scope"),
      tags$div(class = "v24-inline-ctl", uiOutput("v24_tx_scope_sel")),
      DT::DTOutput("v24_tx_table")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Caveat counts across the cohort"),
      DT::DTOutput("v24_tx_caveats")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Filter option contract"),
      tags$p(class = "v24-note",
             "Every option below is reachable and non-empty by construction."),
      DT::DTOutput("v24_tx_filters")
    )
  )
}
