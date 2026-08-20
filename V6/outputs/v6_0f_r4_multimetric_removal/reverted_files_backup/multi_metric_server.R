# =====================================================================
# AEGIS V6.0F | multi_metric_server.R | Multi-Metric Accuracy server
# ---------------------------------------------------------------------
# Read-only. Subsets governed artifacts for display and never recomputes
# a business measure, runs a model, or queries a database.
# =====================================================================

mm_num <- function(x, digits = 3) {
  v <- suppressWarnings(as.numeric(x))
  if (length(v) == 0 || is.na(v)) return("\u2014")
  format(round(v, digits), big.mark = ",", trim = TRUE, scientific = FALSE)
}

mm_kpi <- function(label, value, cls = "") {
  tags$div(class = paste("acc-kpi-card", cls),
           tags$div(class = "acc-kpi-label", label),
           tags$div(class = "acc-kpi-value", value))
}

mm_dt <- function(df, page = 10) {
  if (is.null(df) || nrow(df) == 0) {
    return(DT::datatable(data.frame(Message = "No rows for this selection."),
                         rownames = FALSE, options = list(dom = "t")))
  }
  DT::datatable(df, rownames = FALSE,
                options = list(pageLength = page, scrollX = TRUE, dom = "tip"))
}

multi_metric_server <- function(input, output, session) {

  if (!isTRUE(tryCatch(mm_is_available(), error = function(e) FALSE))) {
    return(invisible(NULL))
  }

  # ---- Dependent filter chain (all options come from the artifact) ----
  v_metric <- reactive(.llm_or(input$mm_metric, ""))

  output$mm_db_type_ui <- renderUI({
    ch <- mm_choices("DB Type", v_metric())
    selectInput("mm_db_type", NULL, choices = ch,
                selected = if (length(ch)) unname(ch[[1]]) else NULL, width = "100%")
  })
  v_db <- reactive(.llm_or(input$mm_db_type, ""))

  # Scenario is optional by contract. When the source has no scenario
  # column the control is replaced by a static, honest label.
  scen_opts <- reactive({
    req(nzchar(v_db()))
    mm_options("Scenario", v_db(), enabled_only = FALSE)
  })

  output$mm_scenario_ui <- renderUI({
    o <- scen_opts()
    if (nrow(o) == 0) {
      return(tags$div(class = "fv-model-note",
                      tags$div(class = "fv-model-note-line", "Not applicable")))
    }
    enabled <- o[tolower(as.character(o$enabled)) == "true", , drop = FALSE]
    if (nrow(enabled) == 0) {
      return(tagList(
        tags$div(class = "fv-model-note",
                 tags$div(class = "fv-model-note-line", "Not applicable"),
                 tags$div(class = "fv-model-note-diag",
                          .llm_or(o$reason_if_disabled[1],
                                  "This source has no scenario dimension."))),
        tags$p(class = "fvb-field-hint",
               "No scenario value is sent and none is assumed.")
      ))
    }
    ch <- stats::setNames(enabled$filter_value, enabled$filter_label)
    selectInput("mm_scenario", NULL, choices = ch,
                selected = unname(ch[[1]]), width = "100%")
  })

  v_scen <- reactive({
    o <- scen_opts()
    if (nrow(o) == 0) return("")
    enabled <- o[tolower(as.character(o$enabled)) == "true", , drop = FALSE]
    if (nrow(enabled) == 0) return(o$filter_value[1])
    .llm_or(input$mm_scenario, enabled$filter_value[1])
  })

  output$mm_granularity_ui <- renderUI({
    ch <- mm_choices("Granularity", v_scen())
    selectInput("mm_granularity", NULL, choices = ch,
                selected = if (length(ch)) unname(ch[[1]]) else NULL, width = "100%")
  })
  v_gran <- reactive(.llm_or(input$mm_granularity, ""))

  output$mm_key_ui <- renderUI({
    ch <- mm_choices("Key", v_gran())
    selectInput("mm_key", NULL, choices = ch,
                selected = if (length(ch)) unname(ch[[1]]) else NULL, width = "100%")
  })
  v_key <- reactive(.llm_or(input$mm_key, ""))

  output$mm_version_ui <- renderUI({
    ch <- mm_choices("Forecast Version", v_key())
    tagList(
      selectInput("mm_version", NULL, choices = ch,
                  selected = if (length(ch)) unname(ch[[1]]) else NULL, width = "100%"),
      if (length(ch) == 1)
        tags$p(class = "fvb-field-hint", "Only one forecast version is retained.")
    )
  })
  v_version <- reactive(.llm_or(input$mm_version, ""))

  sel <- reactive({
    mm_selection(metric = v_metric(), db_type = v_db(), scenario = v_scen(),
                 granularity = v_gran(), key = v_key(), version = v_version())
  })

  comp <- reactive({
    s <- sel()
    if (!nzchar(s$metric_id)) return(NULL)
    mm_computability(s$metric_id, s$db_type, s$granularity)
  })

  avail <- reactive({
    s <- sel()
    if (!nzchar(s$metric_id)) return(NULL)
    mm_availability(s$metric_id, s$db_type, s$granularity)
  })

  # ---- Disabled-option notes (shown, never silently hidden) ----------
  output$mm_metric_note <- renderUI({
    d <- mm_disabled("Metric")
    if (nrow(d) == 0) return(NULL)
    tags$p(class = "fvb-field-hint",
           sprintf("%d metric(s) unavailable: %s",
                   nrow(d),
                   paste(sprintf("%s (%s)", d$filter_label, d$reason_if_disabled),
                         collapse = "; ")))
  })

  output$mm_db_type_note <- renderUI({
    d <- mm_disabled("DB Type", v_metric())
    if (nrow(d) == 0) return(NULL)
    tags$p(class = "fvb-field-hint",
           sprintf("%d variant(s) unavailable: %s",
                   nrow(d),
                   paste(sprintf("%s (%s)", d$filter_label, d$reason_if_disabled),
                         collapse = "; ")))
  })

  # ---- Status badges -------------------------------------------------
  output$mm_status_badges <- renderUI({
    s <- sel(); cp <- comp(); av <- avail()
    if (is.null(cp)) return(tags$p(class = "fv-step-hint", "Select a metric to begin."))
    single <- identical(as.character(cp$computability_status),
                        "single_version_accuracy_only")
    unit <- .llm_or(as.character(av$limitation), "")
    tags$div(
      class = "fv-avail-note",
      mm_badge("Metric", s$metric_id),
      mm_badge("DB type", s$db_type),
      mm_badge("Scenario",
               if (identical(s$scenario, "not_applicable")) "Not applicable" else s$scenario,
               if (identical(s$scenario, "not_applicable")) "pill-amber" else "pill-blue"),
      mm_badge("Granularity", s$granularity),
      mm_badge("Availability", as.character(cp$evidence_level), "pill-blue"),
      mm_badge("Computability", as.character(cp$computability_status),
               if (single) "pill-amber" else "pill-blue"),
      if (single) mm_badge("Single-version accuracy only", "not drift", "pill-amber"),
      tags$p(class = "fv-avail-note", unit)
    )
  })

  # ---- Gating notice: what the UI may and may not show ----------------
  output$mm_gating_notice <- renderUI({
    cp <- comp()
    if (is.null(cp)) return(NULL)
    views <- mm_allowed_views(cp)
    row <- function(label, ok, why) {
      tags$li(tags$b(label), ": ",
              if (ok) tags$span(class = "pill pill-blue", "available")
              else tags$span(class = "pill pill-amber", "not available"),
              if (!ok && nzchar(why)) tags$span(paste0(" \u00b7 ", why)))
    }
    reasons <- gsub("|", " \u00b7 ", as.character(cp$not_computable_reason), fixed = TRUE)
    tags$div(
      class = "shell-card",
      tags$h4(class = "shell-card-title", "What this selection supports"),
      tags$ul(
        class = "guide-list",
        row("Accuracy", mm_truthy(cp$accuracy_computable), reasons),
        row("Cross-version trend", mm_truthy(cp$drift_computable), reasons),
        row("Plan-to-plan comparison", mm_truthy(cp$cross_plan_computable), reasons),
        row("Forecast curve", mm_truthy(cp$forecast_curve_computable), reasons),
        row("Error by horizon", mm_truthy(cp$horizon_error_computable), reasons)
      ),
      tags$p(class = "fv-avail-note",
             "Allowed views for this source: ",
             if (length(views)) paste(views, collapse = ", ") else "none"),
      if (!mm_truthy(cp$drift_computable))
        tags$p(class = "fv-avail-note",
               tags$span(class = "pill pill-amber", "Not drift"),
               " This selection reports observed accuracy for the retained cycle only. ",
               "It is not a movement between plans."),
      tags$p(class = "fv-avail-note",
             "Raw values are never aggregated across metrics because units differ and remain unverified.")
    )
  })

  # ---- KPI cards ------------------------------------------------------
  output$mm_kpi_cards <- renderUI({
    r <- mm_rankings_for(sel(), scope = "key")
    if (nrow(r) == 0) {
      return(tags$div(class = "acc-kpi-grid",
                      mm_kpi("Rows", "\u2014"), mm_kpi("Avg MAPE", "\u2014"),
                      mm_kpi("Avg accuracy", "\u2014"), mm_kpi("Worst MAPE", "\u2014")))
    }
    sv <- nzchar(v_version())
    row <- if (sv) r[r$forecast_version == sel()$forecast_version, , drop = FALSE] else r
    if (nrow(row) == 0) row <- r
    tags$div(
      class = "acc-kpi-grid",
      mm_kpi("Evaluation windows", mm_num(row$row_count[1], 0)),
      mm_kpi("Avg MAPE", mm_num(row$avg_mape[1])),
      mm_kpi("Avg accuracy", mm_num(row$avg_accuracy[1])),
      mm_kpi("Worst MAPE", mm_num(row$max_mape[1]), "acc-kpi-bad"),
      mm_kpi("Min accuracy", mm_num(row$min_accuracy[1]), "acc-kpi-bad"),
      mm_kpi("Avg bias %", mm_num(row$avg_bias_pct[1])),
      mm_kpi("Window range",
             paste(row$evaluation_start_min[1], "\u2192", row$evaluation_end_max[1]),
             "acc-kpi-wide"),
      mm_kpi("Sources merged", mm_num(row$source_object_count[1], 0))
    )
  })

  # ---- Tables ---------------------------------------------------------
  ranking_view <- reactive({
    r <- mm_rankings_for(sel(), scope = "combo")
    cols <- c("metric_id", "db_type", "scenario", "granularity", "entity_key",
              "forecast_version", "row_count", "avg_mape", "max_mape",
              "avg_accuracy", "min_accuracy", "avg_bias_pct", "unit",
              "availability_status", "computability_status",
              "not_computable_reason", "source_object_count")
    mm_numify(r[, intersect(cols, names(r)), drop = FALSE], MM_NUMERIC_COLS)
  })

  output$mm_ranking_table <- DT::renderDataTable(mm_dt(ranking_view()))

  detail_view <- reactive({
    n <- mm_normalized_for(sel())
    cols <- c("entity_key", "forecast_version", "evaluation_start_date",
              "evaluation_end_date", "count", "mean_actual", "mean_forecast",
              "mae", "rmse", "bias_pct", "mape", "smape", "accuracy",
              "unit", "data_quality_status", "source_file")
    mm_numify(n[, intersect(cols, names(n)), drop = FALSE], MM_NUMERIC_COLS)
  })

  output$mm_detail_table <- DT::renderDataTable(mm_dt(detail_view()))

  availability_view <- reactive({
    a <- mm_get("availability")
    cols <- c("metric_id", "metric_name", "db_type", "scenario", "granularity",
              "local_available", "local_rows", "local_versions", "local_keys",
              "availability_status", "evidence_level", "limitation", "next_action")
    mm_numify(a[, intersect(cols, names(a)), drop = FALSE], MM_NUMERIC_COLS)
  })

  output$mm_availability_table <- DT::renderDataTable(mm_dt(availability_view(), 16))

  output$mm_lineage_table <- DT::renderDataTable({
    l <- mm_get("lineage")
    cols <- c("source_object", "source_file", "source_table", "source_rows",
              "normalized_rows", "ranking_rows", "lineage_status", "evidence_level")
    mm_dt(l[, intersect(cols, names(l)), drop = FALSE], 16)
  })

  # ---- Downloads (governed CSV, served from the artifact as displayed) -
  dl <- function(name, data_fn) {
    downloadHandler(
      filename = function() sprintf("AEGIS_%s_%s.csv", name, format(Sys.Date())),
      content = function(file) utils::write.csv(data_fn(), file, row.names = FALSE)
    )
  }
  output$mm_dl_ranking <- dl("multi_metric_ranking", ranking_view)
  output$mm_dl_detail <- dl("multi_metric_detail", detail_view)
  output$mm_dl_availability <- dl("multi_metric_coverage", availability_view)

  for (id in c("mm_status_badges", "mm_gating_notice", "mm_kpi_cards",
               "mm_ranking_table", "mm_detail_table", "mm_availability_table",
               "mm_lineage_table", "mm_db_type_ui", "mm_scenario_ui",
               "mm_granularity_ui", "mm_key_ui", "mm_version_ui")) {
    outputOptions(output, id, suspendWhenHidden = FALSE)
  }

  invisible(NULL)
}
