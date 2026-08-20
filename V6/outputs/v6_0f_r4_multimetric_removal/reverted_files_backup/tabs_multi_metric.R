# =====================================================================
# AEGIS V6.0F | tabs_multi_metric.R | Multi-Metric Accuracy section
# ---------------------------------------------------------------------
# Read-only section bound to the V6.0E governed artifacts. Every filter
# option comes from metric_filter_options.csv; nothing about a metric is
# hardcoded here. View availability is driven by the computability
# artifact, never decided in the UI.
# =====================================================================

mm_badge <- function(label, value, cls = "pill-blue") {
  tags$span(class = paste("pill", cls), paste0(label, ": ", value))
}

section_multi_metric <- function() {
  available <- tryCatch(mm_is_available(), error = function(e) FALSE)

  if (!available) {
    return(panel(
      "multimetric",
      section_head(
        "Multi-Metric Accuracy",
        "Official accuracy metrics across every governed metric and variant."
      ),
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-amber", "Not available"),
        tags$h3(class = "shell-card-title", "Multi-metric artifacts were not found"),
        tags$p(class = "shell-card-detail",
               "The dashboard looked for the governed artifacts under ",
               tags$code("outputs/metrics_multi"),
               " and did not find them. The rest of the dashboard is unaffected.")
      )
    ))
  }

  metric_choices <- mm_choices("Metric")
  metric_default <- if (length(metric_choices)) unname(metric_choices[[1]]) else NULL

  panel(
    "multimetric",

    section_head(
      "Multi-Metric Accuracy",
      paste("Official accuracy metrics for every governed metric and variant.",
            "Each source keeps its own identity, so variants are never blended.")
    ),

    home_collapse(
      "How to read this page",
      "One metric at a time, with the variant kept separate and the limits stated.",
      tags$ul(
        class = "fvb-how-list",
        tags$li("Choose a ", tags$b("Metric"), " first. Everything below narrows to it."),
        tags$li(tags$b("DB Type"), " separates variants of the same metric. They are never pooled."),
        tags$li(tags$b("Scenario"), " only exists for sources that physically have it. Otherwise it reads ", tags$b("Not applicable"), "."),
        tags$li(tags$b("Granularity"), " distinguishes region keys from forest keys. They are never compared."),
        tags$li("Values are read verbatim from governed artifacts. Nothing on this page is recomputed."),
        tags$li("When a source retains a single forecast version, the page shows ", tags$b("point accuracy"), " for that cycle and explicitly not drift.")
      ),
      open = FALSE
    ),

    # ---- Setup ---------------------------------------------------------
    tags$section(
      class = "fvx-section fvb fvb-setup-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "Selection"),
        tags$h3(class = "fvx-section-title", "Choose what to inspect"),
        tags$span(class = "pill pill-blue", "Read-only")
      ),
      tags$p(class = "fvb-setup-lead",
             "Options come from ", tags$code("metric_filter_options.csv"),
             ". Unavailable combinations are listed with their reason instead of being hidden."),

      tags$div(
        class = "fvb-controls",
        tags$div(
          class = "fvb-field",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "1"), "Metric"),
          selectInput("mm_metric", NULL, choices = metric_choices,
                      selected = metric_default, width = "100%"),
          uiOutput("mm_metric_note")
        ),
        tags$div(
          class = "fvb-field",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "2"), "DB Type"),
          uiOutput("mm_db_type_ui"),
          uiOutput("mm_db_type_note")
        ),
        tags$div(
          class = "fvb-field",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "3"), "Scenario"),
          uiOutput("mm_scenario_ui")
        ),
        tags$div(
          class = "fvb-field",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "4"), "Granularity"),
          uiOutput("mm_granularity_ui")
        ),
        tags$div(
          class = "fvb-field",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "5"), "Key"),
          uiOutput("mm_key_ui")
        ),
        tags$div(
          class = "fvb-field",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "6"), "Forecast Version"),
          uiOutput("mm_version_ui")
        )
      )
    ),

    # ---- Status badges -------------------------------------------------
    tags$section(
      class = "fvx-section",
      tags$h3(class = "fvx-section-title", "Status of this selection"),
      uiOutput("mm_status_badges"),
      uiOutput("mm_gating_notice")
    ),

    # ---- KPI ------------------------------------------------------------
    tags$section(
      class = "fvx-section",
      tags$h3(class = "fvx-section-title", "Observed accuracy"),
      uiOutput("mm_kpi_cards"),
      tags$p(class = "fv-avail-note",
             "Source: ", tags$code("official_metric_rankings.csv"),
             " and ", tags$code("official_metrics_normalized.csv"), ".")
    ),

    # ---- Rankings -------------------------------------------------------
    tags$section(
      class = "fvx-section",
      tags$h3(class = "fvx-section-title", "Isolated rankings"),
      tags$p(class = "fv-avail-note",
             "Grouped by metric, DB type, scenario, granularity, key and forecast version. ",
             "Two variants can never collapse into one row."),
      DT::dataTableOutput("mm_ranking_table"),
      tags$div(class = "llm-download",
               downloadButton("mm_dl_ranking", "Download ranking (CSV)",
                              class = "preview-btn"))
    ),

    # ---- Detail ---------------------------------------------------------
    tags$section(
      class = "fvx-section",
      tags$h3(class = "fvx-section-title", "Evaluation windows for this selection"),
      DT::dataTableOutput("mm_detail_table"),
      tags$div(class = "llm-download",
               downloadButton("mm_dl_detail", "Download detail (CSV)",
                              class = "preview-btn"))
    ),

    # ---- Coverage -------------------------------------------------------
    tags$section(
      class = "fvx-section",
      tags$h3(class = "fvx-section-title", "Coverage across all known metrics"),
      tags$p(class = "fv-avail-note",
             "Sources that are not available are listed with a status and a reason. ",
             "They are never shown as zero."),
      DT::dataTableOutput("mm_availability_table"),
      tags$div(class = "llm-download",
               downloadButton("mm_dl_availability", "Download coverage (CSV)",
                              class = "preview-btn"))
    ),

    # ---- Lineage --------------------------------------------------------
    home_collapse(
      "Traceability",
      "Where every row on this page comes from.",
      DT::dataTableOutput("mm_lineage_table")
    ),

    # ---- Assistant ------------------------------------------------------
    # button_label is accepted but unused by llm_explain_ui; panel_title and
    # panel_sub are the parameters that actually render.
    llm_explain_ui("llm_multi_metric", "Multi-Metric Accuracy",
                   panel_title = "Ask AEGIS about this metric selection",
                   panel_sub = paste(
                     "Grounded in the governed multi-metric artifacts.",
                     "It explains availability, computability and why a view is unavailable.",
                     "It never presents single-version accuracy as drift."))
  )
}
