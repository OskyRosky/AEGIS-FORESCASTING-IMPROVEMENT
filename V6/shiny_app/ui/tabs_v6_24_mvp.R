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
# v24_badge / v24_badges_ui / v24_kv / v24_card / v24_table are defined in
# R/v6_24_read_only_loader.R because the server renders with them too.

# P9E | Charts are htmlwidgets, and a widget laid out inside a display:none
# container measures zero width, so a chart built while its section is hidden
# would stay collapsed when the section is shown. www/custom.js already fires a
# resize 60 ms after a section switch for exactly this reason. That single
# resize can land before a DT table has finished drawing, so this hook adds two
# later ones; it is additive and V6.24-owned, and it changes no legacy file.
v24_resize_hook <- function() {
  tags$script(HTML(
    "document.addEventListener('click', function(e){",
    "  var a = e.target.closest('.sidebar-sublink');",
    "  if (!a) return;",
    "  var s = a.getAttribute('data-section') || '';",
    "  if (s.indexOf('v24_') !== 0) return;",
    "  [250, 600].forEach(function(d){",
    "    setTimeout(function(){ window.dispatchEvent(new Event('resize')); }, d);",
    "  });",
    "});"))
}

# Card A: Selection. Two-column navigator matching the Forecasting pattern -
# a rail of progressive fields on the left, live route context on the right.
# The rail is rendered by the server because which axes appear depends on the
# choices made so far.
v24_selection_card <- function() {
  n_ops <- nrow(v6_24_operational())
  tags$section(
    class = "v24-card-section",
    tags$div(
      class = "v24-card-head",
      tags$span(class = "v24-kicker", "A"),
      tags$h3(class = "v24-card-title", "Selection"),
      tags$span(class = "v24-pill", sprintf("%s operational series", n_ops))
    ),
    tags$p(
      class = "v24-card-lead",
      paste("Choose only the dimensions that apply to the branch.",
            "The breadcrumb and route cards resolve the selection back to the",
            "governed contract fields.")
    ),
    tags$div(
      class = "v24-nav",
      tags$div(
        class = "v24-nav-rail",
        tags$div(class = "v24-rail-title", "Selection"),
        uiOutput("v24_sel_controls")
      ),
      tags$div(
        class = "v24-nav-route",
        uiOutput("v24_sel_breadcrumb"),
        uiOutput("v24_sel_state"),
        uiOutput("v24_sel_cards")
      )
    )
  )
}

# Compact read-only mirror of the shared selection, used on pages that consume
# the selected series but must not own an independent series selector.
# The shared-selection banner appears on more than one page, so it takes an
# output id. Two pages rendering the same uiOutput id would make Shiny warn
# about a duplicate output and only one of them would update.
v24_shared_selection_banner <- function(id = "v24_shared_selection") {
  tags$div(class = "v24-shared-sel", uiOutput(id))
}

# Card B: Backtest Configuration. Mirrors the legacy block - availability
# banner, horizon radios with disabled chips for what the artifact does not
# cover, family-grouped model checkboxes, and an explicit Analyze commit.
v24_backtest_config_card <- function() {
  tags$section(
    class = "v24-card-section",
    tags$div(
      class = "v24-card-head",
      tags$span(class = "v24-kicker", "B"),
      tags$h3(class = "v24-card-title", "Backtest Configuration"),
      tags$span(class = "v24-pill v24-pill-slate",
                sprintf("%s governed models", length(V6_24_GOVERNED_MODELS)))
    ),
    uiOutput("v24_bt_availability"),
    tags$div(
      class = "v24-cfg-row",
      tags$div(
        class = "v24-cfg-cell",
        tags$label(class = "v24-field-label", "Horizon"),
        uiOutput("v24_bt_horizon_ui"),
        tags$div(class = "v24-horizon-chips",
                 lapply(V6_24_HORIZON_UNAVAILABLE, function(h)
                   tags$span(class = "v24-hchip is-disabled",
                             paste0(h, " days"))),
                 tags$span(class = "v24-field-hint", V6_24_HORIZON_NOTE))
      ),
      tags$div(
        class = "v24-cfg-cell",
        tags$label(class = "v24-field-label", "History window"),
        selectInput("v24_bt_history", NULL,
                    choices = c("Full available window" = "full"),
                    selected = "full", width = "100%"),
        tags$p(class = "v24-field-hint",
               "Filters prepared backtest dates only.")
      )
    ),
    tags$div(
      class = "v24-models-head",
      tags$label(class = "v24-field-label", "Models"),
      uiOutput("v24_bt_model_count", inline = TRUE)
    ),
    uiOutput("v24_bt_model_groups"),
    tags$p(class = "v24-field-hint",
           "All 15 governed AEGIS models are available and grouped by family."),
    uiOutput("v24_bt_champion_note"),
    tags$div(
      class = "v24-analyze-block",
      tags$label(class = "v24-field-label", "Analyze backtest"),
      tags$div(
        class = "v24-analyze-row",
        uiOutput("v24_bt_analyze_btn", inline = TRUE),
        actionButton("v24_bt_reset", "Reset Selection",
                     class = "v24-btn-secondary")
      ),
      tags$p(class = "v24-field-hint",
             "Prepares the comparison below. Updates only on click."),
      uiOutput("v24_bt_applied")
    )
  )
}

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

# Removed in P9C: the flat six-dropdown bar was replaced by v24_selection_card(),
# which renders only the axes that apply and shows live route context.

# P9G | Evidence-aware assistant card.
#
# It reuses the legacy assistant's CSS classes (llm-explain, llm-qp, ...) so it
# reads as the same product feature, but it is wired to the V6.24 evidence
# builder rather than to llm_explain.R, which can only serve page-keyed
# precomputed text and has no way to receive a selected series.
#
# The "Local evidence" badge is deliberate: there is no LLM and no network call
# behind this panel, and the UI must not imply otherwise.
v24_assistant_card <- function(prefix, prompts, title, subtitle) {
  id <- function(s) paste0("v24_", prefix, "_asst_", s)
  tags$div(
    class = "v24-card-section llm-explain",
    tags$div(
      class = "v24-card-head",
      tags$span(class = "v24-kicker", "D"),
      tags$h3(class = "v24-card-title", "Assistant"),
      tags$span(class = "v24-pill v24-pill-slate", "Evidence-grounded")
    ),
    tags$div(
      class = "llm-explain-titlewrap",
      tags$span(class = "llm-explain-kicker", "AEGIS Explanation Assistant"),
      tags$h4(class = "llm-explain-title", title),
      tags$p(class = "llm-explain-sub", subtitle)
    ),
    tags$div(
      class = "llm-explain-ask",
      tags$div(
        class = "llm-quickrow",
        tags$span(class = "llm-quick-label", "Quick prompts:"),
        lapply(prompts, function(p)
          actionButton(id(p$id), p$label, class = "llm-qp"))
      ),
      tags$label(`for` = id("question"), class = "llm-ask-label",
                 "Or ask your own question"),
      tags$textarea(
        id = id("question"), class = "form-control llm-ask-input", rows = 2,
        placeholder = "Example: Is this series safe to interpret?"
      ),
      tags$div(
        class = "llm-cta-row",
        actionButton(id("generate"), "Generate explanation",
                     class = "llm-explain-btn")
      )
    ),
    uiOutput(id("answer")),
    tags$div(
      class = "llm-explain-foot-badge",
      title = paste("Deterministic local composition from the governed V6.24",
                    "artifacts. No LLM, no network, no recomputation."),
      "Local evidence \u00b7 no LLM"
    )
  )
}

# ---------------------------------------------------------------- 1. Overview

section_v24_overview <- function() {
  panel(
    "v24_overview",
    v24_resize_hook(),
    v24_section_head(
      "Forecasting \u2014 Overview",
      paste("Governed product coverage read from navigation_contract and",
            "taxonomy_counts. No value on this page is computed in Shiny.")),
    tags$div(class = "v24-cards", uiOutput("v24_ov_cards")),
    tags$div(
      class = "v24-grid-2",
      tags$div(class = "v24-panel",
               tags$h3("Coverage by metric"),
               DT::dataTableOutput("v24_ov_by_metric")),
      tags$div(class = "v24-panel",
               tags$h3("Availability and signal quality"),
               DT::dataTableOutput("v24_ov_by_signal"))
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
             tags$p(class = "v24-note",
                    paste("Technical load-time validation of the governed",
                          "artifacts. Nothing here is a product metric.")),
             DT::dataTableOutput("v24_ov_loader"))
  )
}

# ---------------------------------------------------------------- 2. Viewer

section_v24_viewer <- function() {
  panel(
    "v24_viewer",
    v24_section_head(
      "Forecasting \u2014 Series Viewer",
      paste("Observed history and governed backtests for one selected series.",
            "Accuracy and rankings are read from the artifacts, never",
            "recalculated here.")),
    v24_selection_card(),
    tags$div(class = "v24-panel", uiOutput("v24_vw_identity")),
    tags$div(class = "v24-panel", uiOutput("v24_vw_champion")),
    v24_backtest_config_card(),
    tags$div(
      class = "v24-panel",
      tags$h3("Observed history"),
      highcharter::highchartOutput("v24_vw_actuals", height = "340px")
    ),
    tags$div(
      class = "v24-card-section",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "C"),
        tags$h3(class = "v24-card-title", "Results"),
        tags$span(class = "v24-pill v24-pill-slate",
                  "Actual versus selected model backtests")
      ),
      highcharter::highchartOutput("v24_vw_backtest", height = "420px"),
      uiOutput("v24_vw_notes")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Model ranking for this series"),
      tags$p(class = "v24-note", uiOutput("v24_vw_rank_note", inline = TRUE)),
      DT::dataTableOutput("v24_vw_ranking")
    ),
    v24_assistant_card("vw", V6_24_VIEWER_PROMPTS,
                       "Ask AEGIS about this series",
                       paste("Answered only from the governed V6.24 artifacts",
                             "for the series selected above."))
  )
}

# ---------------------------------------------------------------- 3. Forecast

section_v24_forecast <- function() {
  panel(
    "v24_forecast",
    v24_section_head(
      "Forecasting \u2014 Forecast",
      paste("Governed 30-step forward forecast for one selected series, read",
            "verbatim from forecast_outputs. No forecast is generated here.")),
    v24_shared_selection_banner(),
    tags$div(class = "v24-panel", uiOutput("v24_fc_identity")),
    tags$div(
      class = "v24-panel",
      tags$h3("Forecast"),
      tags$div(class = "v24-inline-ctl", uiOutput("v24_fc_model_sel")),
      uiOutput("v24_fc_champion_note"),
      highcharter::highchartOutput("v24_fc_chart", height = "420px")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Forecast rows"),
      tags$p(class = "v24-note",
             "predicted_value is shown exactly as the model produced it. ",
             "Negative and extreme values are flagged, never clipped."),
      DT::dataTableOutput("v24_fc_table")
    ),
    v24_assistant_card("fc", V6_24_FORECAST_PROMPTS,
                       "Ask AEGIS about this forecast",
                       paste("Answered only from forecast_outputs,",
                             "navigation_contract and model_rankings for the",
                             "selected series."))
  )
}

# ---------------------------------------------------------------- 4. Accuracy
# P9H | Accuracy diagnostics over the governed accuracy_metrics artifact.
#
# Structure mirrors the legacy Forecasting > Accuracy page - numbered setup box,
# summary cards, heatmap, metric table, assistant - so the two read as the same
# product. Two things differ on purpose and are stated on screen: the horizon is
# DISCLOSED CONTEXT rather than a filter (accuracy_metrics has no horizon axis),
# and the chart is Highcharter rather than Plotly.

section_v24_accuracy <- function() {
  panel(
    "v24_accuracy",
    v24_section_head(
      "Forecasting \u2014 Accuracy",
      paste("How the 15 governed models performed on the series selected in",
            "the Viewer. Values are read from accuracy_metrics; nothing is",
            "recomputed and no champion decision is made here.")),

    # The selection is the one made in the Viewer, shared with Forecast.
    v24_shared_selection_banner("v24_acc_shared_selection"),

    # ---- A. Setup -------------------------------------------------------
    tags$section(
      class = "v24-card-section v24-acc-setup",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "A"),
        tags$h3(class = "v24-card-title", "Set up the accuracy view"),
        tags$span(class = "v24-pill v24-pill-slate", "Backtest \u00b7 diagnostics")
      ),
      tags$p(class = "v24-card-lead",
             "Choose a metric and the models to compare, then run step 3. Source: ",
             tags$code("accuracy_metrics.parquet"),
             " \u2014 one governed row per model for the selected series."),

      # Step 1 - the accuracy window, disclosed rather than offered.
      tags$div(
        class = "v24-field v24-acc-window",
        tags$label(class = "v24-field-label",
                   tags$span(class = "v24-step-num", "1"),
                   "Backtest accuracy window"),
        uiOutput("v24_acc_window"),
        tags$p(class = "v24-field-hint",
               paste("The Viewer backtest chart does filter by horizon because",
                     "model_backtests_15_models carries horizon_steps per row.",
                     "Accuracy does not."))
      ),

      tags$div(
        class = "v24-field v24-acc-metric-field",
        tags$label(class = "v24-field-label",
                   tags$span(class = "v24-step-num", "2"), "Select metric"),
        uiOutput("v24_acc_metric_ui"),
        tags$p(class = "v24-field-hint",
               "Ranks the models and drives the best / weakest cards. Lower is better.")
      ),

      tags$div(
        class = "v24-acc-models",
        tags$label(class = "v24-field-label",
                   tags$span(class = "v24-step-num", "3"), "Select models"),
        uiOutput("v24_acc_models_ui")
      ),

      tags$div(
        class = "v24-bt-actions",
        tags$div(
          class = "v24-acc-analyze-label",
          tags$span(class = "v24-step-num", "4"),
          tags$span(class = "v24-field-label", "Analyze Accuracy")
        ),
        actionButton("v24_acc_go", "Analyze Accuracy",
                     class = "btn v24-btn-primary"),
        actionButton("v24_acc_reset", "Reset", class = "btn v24-btn-ghost"),
        uiOutput("v24_acc_applied", inline = TRUE)
      )
    ),

    # ---- B. Summary -----------------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Accuracy summary"),
      tags$p(class = "v24-note",
             "Headline accuracy for the selected series under the chosen metric."),
      uiOutput("v24_acc_cards")
    ),

    # ---- C. Heatmap -----------------------------------------------------
    tags$div(
      class = "v24-card-section",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "B"),
        tags$h3(class = "v24-card-title", "Model severity by measure"),
        tags$span(class = "v24-pill v24-pill-slate", "Severity \u00b7 display only")
      ),
      tags$p(class = "v24-card-lead",
             paste("Each row is a governed model, each column a governed",
                   "measure. Colour shows how that model compares with the",
                   "other models of this series on that measure. Red is worse,",
                   "blue is better.")),
      highcharter::highchartOutput("v24_acc_heatmap", height = "480px"),
      tags$div(
        class = "v24-warn-card",
        tags$ul(
          class = "v24-list",
          tags$li(tags$span(class = "v24-cell-badge v24-cell-warn", "Diagnostics"),
                  " These are read from the governed accuracy artifact. They ",
                  "are not a champion decision and do not change one."),
          tags$li(tags$span(class = "v24-cell-badge v24-cell-slate", "Standardized"),
                  " Colour is a robust severity score (median / IQR) computed ",
                  "within each measure, because MAE and SMAPE do not share a ",
                  "scale. The raw value is always in the tooltip and the table."),
          tags$li(tags$span(class = "v24-cell-badge v24-cell-slate", "Grey cells"),
                  " A grey cell means the artifact recorded that measure as ",
                  "not computable for that model, not that the value is zero.")
        )
      )
    ),

    # ---- D. Metric values table -----------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Model accuracy for this series"),
      tags$p(class = "v24-note",
             paste("One row per governed model, best-first by the selected",
                   "metric. Values at or above 1e6 are shown in scientific",
                   "notation and flagged; non-computable values say so and are",
                   "never turned into zero.")),
      DT::dataTableOutput("v24_acc_table")
    ),

    # ---- E. Assistant ---------------------------------------------------
    v24_assistant_card("acc", V6_24_ACCURACY_PROMPTS,
                       "Ask AEGIS about this accuracy view",
                       paste("Answered only from the accuracy rows of the",
                             "selected series, read from accuracy_metrics."))
  )
}

# ---------------------------------------------------------------- 5. Taxonomy

section_v24_taxonomy <- function() {
  panel(
    "v24_taxonomy",
    v24_section_head(
      "Forecasting \u2014 Taxonomy and Availability",
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
      DT::dataTableOutput("v24_tx_table")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Caveat counts across the cohort"),
      DT::dataTableOutput("v24_tx_caveats")
    ),
    tags$div(
      class = "v24-panel",
      tags$h3("Filter option contract"),
      tags$p(class = "v24-note",
             "Every option below is reachable and non-empty by construction."),
      DT::dataTableOutput("v24_tx_filters")
    )
  )
}

