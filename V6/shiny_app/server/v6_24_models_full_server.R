# TESSERACT v2 | v6_24_models_full_server.R
# V6.24-P9K | Server for Models FULL - Universe.
#
# Read-only. Every output renders values produced by
# R/v6_24_models_full_helpers.R, which reads the governed artifacts and derives
# nothing beyond cohort medians. No tournament, no pairwise, no global champion.

v6_24_models_full_server <- function(input, output, session,
                                    shared_selection = NULL) {

  mf_summary <- reactive(v6_24_mf_universe_summary())
  mf_table   <- reactive(v6_24_mf_universe_table())
  mf_champs  <- reactive(v6_24_mf_champion_counts())

  # ---- scope line -------------------------------------------------------
  output$v24mf_scope_line <- renderUI({
    s <- mf_summary()
    tags$ul(
      class = "v24mf-scope",
      tags$li(tags$b(s$n_models), " governed models"),
      tags$li(tags$b(s$n_series), " operational series"),
      tags$li(tags$b(format(s$n_rows, big.mark = ",")),
              " model-series accuracy rows"),
      tags$li(tags$b(s$n_metrics), " measures: ",
              paste(s$metrics, collapse = ", ")),
      tags$li("Source: ", tags$code("accuracy_metrics"), ", ",
              tags$code("navigation_contract"), ", ",
              tags$code("model_rankings"))
    )
  })

  # ---- what changed -----------------------------------------------------
  output$v24mf_changed <- renderUI({
    s <- mf_summary(); L <- V6_24_MF_LEGACY_SCOPE
    tags$div(
      tags$table(
        class = "v24mf-compare",
        tags$thead(tags$tr(tags$th(""), tags$th("Previous model section"),
                           tags$th("V6.24 universe"))),
        tags$tbody(
          tags$tr(tags$td("Models"), tags$td(L$models), tags$td(s$n_models)),
          tags$tr(tags$td("Entities / series"), tags$td(L$entities),
                  tags$td(s$n_series)),
          tags$tr(tags$td("Metric coverage"), tags$td(L$metric),
                  tags$td("CPU, HDD, IOPS, SSD")),
          tags$tr(tags$td("Model overlap"), tags$td(colspan = "2",
                  paste0(L$overlap, " models appear in both"))),
          tags$tr(tags$td("Only in the previous section"),
                  tags$td(colspan = "2", L$legacy_only)),
          tags$tr(tags$td("Only in V6.24"), tags$td(colspan = "2",
                  paste(L$v624_only, collapse = ", ")))
        )
      ),
      tags$p(class = "v24-note",
             paste0("The previous section also relied on ",
                    paste(L$absent_in_v624, collapse = ", "),
                    ". None of those has a successor artifact in V6.24, so ",
                    "none of them appears on this page as current evidence. ",
                    "Figures from the two scopes are not comparable."))
    )
  })

  # ---- families ---------------------------------------------------------
  output$v24mf_families <- renderUI({
    fm <- v6_24_mf_family_map()
    groups <- lapply(V6_24_FAMILY_ORDER, function(k) {
      d <- fm[fm$display_family_key == k, , drop = FALSE]
      if (!nrow(d)) return(NULL)
      tags$div(
        class = "v24mf-family",
        tags$div(class = "v24mf-family-head",
                 unname(V6_24_FAMILY_LABEL[[k]]),
                 tags$span(class = "v24mf-family-count",
                           paste0(nrow(d), " models"))),
        tags$ul(class = "v24mf-family-list", lapply(seq_len(nrow(d)), function(i)
          tags$li(tags$span(class = "v24mf-model", d$model_name[i]),
                  tags$span(class = "v24mf-govfam",
                            paste0("governed: ", d$governed_family[i])))))
      )
    })
    tagList(
      tags$div(class = "v24mf-families", groups),
      tags$p(class = "v24-note",
             paste("The four families above are a display grouping only. The",
                   "governed classification recorded in the artifact is shown",
                   "beside each model, and the two partitions cut across each",
                   "other by design."))
    )
  })

  # ---- summary cards ----------------------------------------------------
  output$v24mf_cards <- renderUI({
    s <- mf_summary()
    cell <- function(label, value, cls = "") {
      tags$div(class = paste("v24-acc-card", cls),
               tags$div(class = "v24-acc-card-label", label),
               tags$div(class = "v24-acc-card-value", value))
    }
    tags$div(
      class = "v24-acc-grid",
      cell("Governed models", s$n_models),
      cell("Operational series", s$n_series),
      cell("Model-series rows", format(s$n_rows, big.mark = ",")),
      cell("Measures available", s$n_metrics),
      cell("Series with a presentable champion", s$champion_visible),
      cell("Series with no usable signal", s$champion_suppressed),
      cell("Models leading at least one series", s$distinct_winners),
      cell("Source", "accuracy_metrics + navigation_contract")
    )
  })

  # ---- universe table ---------------------------------------------------
  output$v24mf_table <- DT::renderDataTable({
    tb <- mf_table()
    if (is.null(tb) || !nrow(tb)) return(v6_24_dt(NULL))
    out <- data.frame(
      Model = tb$model_name,
      `Display family` = tb$display_family,
      `Governed family` = tb$governed_family,
      `Accuracy rows` = as.integer(tb$accuracy_rows),
      `Series covered` = as.integer(tb$series_covered),
      `Median MAE` = vapply(tb$median_mae, v6_24_acc_fmt, character(1)),
      `Median RMSE` = vapply(tb$median_rmse, v6_24_acc_fmt, character(1)),
      `Median WAPE` = vapply(tb$median_wape, v6_24_acc_fmt, character(1)),
      `Median SMAPE` = vapply(tb$median_smape, v6_24_acc_fmt, character(1)),
      `WAPE not computable` = as.integer(tb$noncomputable_wape),
      `Extreme MAE rows` = as.integer(tb$extreme_mae_rows),
      `Series-level champion count` = as.integer(tb$series_champion_count),
      check.names = FALSE, stringsAsFactors = FALSE)
    v6_24_dt(out, page_length = 15L, paging = FALSE, searching = FALSE)
  })

  # ---- champion count chart --------------------------------------------
  output$v24mf_chart <- highcharter::renderHighchart({
    ch <- mf_champs()
    if (is.null(ch) || !nrow(ch)) {
      return(v6_24_hc_empty("No champion counts available."))
    }
    s <- mf_summary()
    ch <- ch[order(-ch$series_champion_count), , drop = FALSE]
    pts <- lapply(seq_len(nrow(ch)), function(i)
      list(y = as.integer(ch$series_champion_count[i]),
           name = as.character(ch$model_name[i])))
    sub <- paste0(nrow(ch), " models lead at least one of the ",
                  s$champion_visible,
                  " series whose champion may be presented  \u00b7  ",
                  s$champion_suppressed, " no-signal series excluded")
    highcharter::highchart() |>
      highcharter::hc_chart(type = "bar",
                            style = list(fontFamily = V6_24_CHART_FONT)) |>
      highcharter::hc_title(
        text = "Series-level champion count by model",
        style = list(fontSize = "15px", fontWeight = "600", color = "#102a43")) |>
      highcharter::hc_subtitle(
        text = sub, style = list(fontSize = "12px", color = "#627d98")) |>
      highcharter::hc_xAxis(categories = as.list(as.character(ch$model_name)),
                            title = list(text = NULL),
                            labels = list(style = list(fontSize = "11px"))) |>
      highcharter::hc_yAxis(title = list(text = "Series led"),
                            allowDecimals = FALSE) |>
      highcharter::hc_legend(enabled = FALSE) |>
      highcharter::hc_tooltip(
        headerFormat = "",
        pointFormat = paste0("<b>{point.name}</b><br/>Leads {point.y} series",
                             "<br/>Series-level count, not a global champion")) |>
      highcharter::hc_exporting(enabled = TRUE) |>
      highcharter::hc_credits(enabled = FALSE) |>
      highcharter::hc_plotOptions(bar = list(
        color = "#2e75b6", borderRadius = 2,
        dataLabels = list(enabled = TRUE))) |>
      highcharter::hc_add_series(name = "Series led", data = pts)
  })

  # ---- assistant --------------------------------------------------------
  local({
    id <- function(s) paste0("v24_mfu_asst_", s)
    st <- reactiveValues(intent = NULL, question = "", stamp = NULL)
    for (p in V6_24_MF_UNIVERSE_PROMPTS) {
      local({
        pp <- p
        observeEvent(input[[id(pp$id)]], {
          st$intent <- pp$intent; st$question <- pp$label
          st$stamp <- format(Sys.time(), "%H:%M:%S")
        }, ignoreInit = TRUE)
      })
    }
    observeEvent(input[[id("generate")]], {
      q <- input[[id("question")]]
      st$question <- if (is.null(q)) "" else trimws(q)
      st$intent <- if (nzchar(st$question)) v6_24_mf_intent(st$question)
                   else "mf_summary"
      st$stamp <- format(Sys.time(), "%H:%M:%S")
    }, ignoreInit = TRUE)

    output[[id("answer")]] <- renderUI({
      if (is.null(st$intent)) {
        return(tags$p(class = "v24-note",
                      paste("Pick a quick prompt or type a question. Answers",
                            "come only from the governed model artifacts.")))
      }
      a <- v6_24_mf_answer(v6_24_mf_evidence(), st$question, st$intent)
      tags$div(
        class = if (isTRUE(a$bounded)) "llm-panel v24-asst v24-asst-bounded"
                else "llm-panel v24-asst",
        tags$p(class = "v24-asst-q", tags$strong("Question: "), st$question),
        tags$p(class = "v24-asst-lead", a$lead),
        if (nzchar(a$body)) tags$p(class = "v24-asst-body", a$body),
        if (length(a$bullets))
          tags$ul(class = "v24-list", lapply(a$bullets, tags$li)),
        tags$div(
          class = "v24-asst-evidence",
          tags$span(class = "v24-asst-evlabel", "Evidence used:"),
          tags$span(if (identical(a$used, "none") || !length(a$used))
            "no artifact supports this question"
            else paste(a$used, collapse = " \u00b7 ")),
          tags$span(class = "v24-asst-caveat", paste0("Caveats: ", a$caveats))
        ),
        tags$p(class = "v24-asst-stamp",
               paste0("Composed locally at ", st$stamp, " \u00b7 ",
                      V6_24_ASSISTANT_ENGINE, " \u00b7 intent: ", a$intent))
      )
    })
    outputOptions(output, id("answer"), suspendWhenHidden = FALSE)
  })

  # ==========================================================================
  # V6.24-P9L | Ranking Diagnostics.
  # Pending vs applied, matching the P9D/P9H pattern: controls stage a request
  # and Analyze commits it. Read-only throughout.
  # ==========================================================================
  rk <- reactiveValues(metric = "MAE", family = "All",
                       sort_by = "metric_asc", applied = NULL)

  output$v24mfr_scope_line <- renderUI({
    s <- v6_24_mf_universe_summary()
    tags$ul(
      class = "v24mf-scope",
      tags$li(tags$b(s$n_models), " governed models \u00b7 ",
              tags$b(s$n_series), " operational series \u00b7 ",
              tags$b(format(s$n_rows, big.mark = ",")), " model-series rows"),
      tags$li(tags$b(s$champion_visible), " series with a presentable champion \u00b7 ",
              tags$b(s$champion_suppressed), " no-signal series suppressed"),
      tags$li("Measures read from ", tags$code("accuracy_metrics"),
              "; champions from ", tags$code("navigation_contract"))
    )
  })

  output$v24mfr_metric_ui <- renderUI({
    selectInput("v24mfr_metric", NULL, choices = V6_24_MF_RANK_METRIC_LABELS,
                selected = rk$metric, width = "100%")
  })
  output$v24mfr_family_ui <- renderUI({
    selectInput("v24mfr_family", NULL,
                choices = c("All", unname(V6_24_FAMILY_LABEL)),
                selected = rk$family, width = "100%")
  })
  output$v24mfr_sort_ui <- renderUI({
    selectInput("v24mfr_sort", NULL, choices = V6_24_MF_SORT_OPTIONS,
                selected = rk$sort_by, width = "100%")
  })

  observeEvent(input$v24mfr_go, {
    rk$metric <- if (is.null(input$v24mfr_metric)) "MAE" else input$v24mfr_metric
    rk$family <- if (is.null(input$v24mfr_family)) "All" else input$v24mfr_family
    rk$sort_by <- if (is.null(input$v24mfr_sort)) "metric_asc" else input$v24mfr_sort
    rk$applied <- list(metric = rk$metric, family = rk$family,
                       sort_by = rk$sort_by,
                       stamp = format(Sys.time(), "%H:%M:%S"))
  }, ignoreInit = TRUE)

  observeEvent(input$v24mfr_reset, {
    rk$metric <- "MAE"; rk$family <- "All"; rk$sort_by <- "metric_asc"
    rk$applied <- NULL
  }, ignoreInit = TRUE)

  applied_rk <- reactive(rk$applied)
  rk_rows <- reactive({
    a <- applied_rk()
    if (is.null(a)) return(NULL)
    v6_24_mf_ranking_rows(a$metric, a$family, a$sort_by)
  })

  output$v24mfr_applied <- renderUI({
    a <- applied_rk()
    if (is.null(a)) return(tags$span(class = "v24-note", "Nothing analysed yet."))
    tags$span(class = "v24-note v24-note-ok",
              sprintf("Analysed: %s \u00b7 %s \u00b7 %s",
                      a$metric, a$family, a$stamp))
  })

  output$v24mfr_cards <- renderUI({
    a <- applied_rk()
    cell <- function(label, value, cls = "") {
      tags$div(class = paste("v24-acc-card", cls),
               tags$div(class = "v24-acc-card-label", label),
               tags$div(class = "v24-acc-card-value", value))
    }
    if (is.null(a)) {
      return(tags$div(class = "v24-acc-grid",
        cell("Governed models", "\u2014"), cell("Operational series", "\u2014"),
        cell("Selected measure", "\u2014"), cell("Evidence type", "\u2014"),
        cell("Lowest diagnostic median", "Click Analyze", "v24-acc-wide"),
        cell("Most series led", "Click Analyze", "v24-acc-wide")))
    }
    s <- v6_24_mf_ranking_summary(rk_rows(), a$metric)
    tags$div(
      class = "v24-acc-grid",
      cell("Governed models", s$n_models),
      cell("Operational series", s$n_series),
      cell("Selected measure", s$metric),
      cell("Evidence type", s$evidence_type),
      cell("Lowest diagnostic median",
           tagList(tags$span(s$best_median_model),
                   tags$span(class = "v24-acc-sub",
                             paste0("median ", s$metric, " ",
                                    v6_24_acc_fmt(s$best_median_value),
                                    " \u00b7 not a champion"))),
           "v24-acc-wide v24-acc-good"),
      cell("Most series led",
           tagList(tags$span(s$most_champ_model),
                   tags$span(class = "v24-acc-sub",
                             paste0(s$most_champ_count, " of ",
                                    s$champion_visible,
                                    " presentable series \u00b7 series-level count, not a global champion"))),
           "v24-acc-wide"),
      cell("No-signal series suppressed", s$champion_suppressed),
      cell(paste0("Rows with no computable ", s$metric), s$noncomputable),
      if (isTRUE(!s$agree))
        cell("The two headlines disagree",
             paste0("Lowest median is ", s$best_median_model,
                    "; most series led is ", s$most_champ_model,
                    ". Neither is a winner."),
             "v24-acc-wide")
    )
  })

  output$v24mfr_table <- DT::renderDataTable({
    a <- applied_rk()
    if (is.null(a)) return(v6_24_dt(NULL))
    d <- rk_rows()
    if (is.null(d) || !nrow(d)) return(v6_24_dt(NULL))
    out <- data.frame(
      Position = as.integer(d$diagnostic_position),
      Model = d$model_name,
      `Display family` = d$display_family,
      `Governed family` = d$governed_family,
      `Median (selected)` = vapply(d$median_selected, v6_24_acc_fmt, character(1)),
      `Median MAE` = vapply(d$median_mae, v6_24_acc_fmt, character(1)),
      `Median RMSE` = vapply(d$median_rmse, v6_24_acc_fmt, character(1)),
      `Median WAPE` = vapply(d$median_wape, v6_24_acc_fmt, character(1)),
      `Median SMAPE` = vapply(d$median_smape, v6_24_acc_fmt, character(1)),
      `Series led` = as.integer(d$series_champion_count),
      `Share of presentable` = paste0(
        format(round(100 * d$series_champion_share, 1), nsmall = 1), "%"),
      `Not computable` = as.integer(d$selected_excluded),
      `Extreme rows` = as.integer(d$extreme_mae_rows),
      check.names = FALSE, stringsAsFactors = FALSE)
    v6_24_dt(out, page_length = 15L, paging = FALSE, searching = FALSE)
  })

  output$v24mfr_metric_chart <- highcharter::renderHighchart({
    a <- applied_rk()
    if (is.null(a)) {
      return(v6_24_hc_empty("Choose a measure, then click Analyze Ranking Diagnostics."))
    }
    d <- rk_rows()
    d <- d[is.finite(d$median_selected), , drop = FALSE]
    if (!nrow(d)) return(v6_24_hc_empty("No computable medians for this selection."))
    d <- d[order(d$median_selected), , drop = FALSE]
    pts <- lapply(seq_len(nrow(d)), function(i) list(
      y = round(as.numeric(d$median_selected[i]), 6),
      name = as.character(d$model_name[i]),
      fam = as.character(d$display_family[i]),
      champ = as.integer(d$series_champion_count[i])))
    highcharter::highchart() |>
      highcharter::hc_chart(type = "bar",
                            style = list(fontFamily = V6_24_CHART_FONT)) |>
      highcharter::hc_title(text = paste0("Diagnostic median ", a$metric),
        style = list(fontSize = "15px", fontWeight = "600", color = "#102a43")) |>
      highcharter::hc_subtitle(
        text = paste0(nrow(d), " models \u00b7 ", a$family,
                      " \u00b7 cohort medians, lower is better \u00b7 not a ranking"),
        style = list(fontSize = "12px", color = "#627d98")) |>
      highcharter::hc_xAxis(categories = as.list(as.character(d$model_name)),
                            title = list(text = NULL),
                            labels = list(style = list(fontSize = "11px"))) |>
      highcharter::hc_yAxis(title = list(text = paste0("Median ", a$metric))) |>
      highcharter::hc_legend(enabled = FALSE) |>
      highcharter::hc_tooltip(headerFormat = "", pointFormat = paste0(
        "<b>{point.name}</b><br/>Family: {point.fam}<br/>Diagnostic median ",
        a$metric, ": <b>{point.y}</b><br/>Leads {point.champ} series")) |>
      highcharter::hc_exporting(enabled = TRUE) |>
      highcharter::hc_credits(enabled = FALSE) |>
      highcharter::hc_plotOptions(bar = list(color = "#2e75b6",
        borderRadius = 2, dataLabels = list(enabled = FALSE))) |>
      highcharter::hc_add_series(name = paste0("Median ", a$metric), data = pts)
  })

  output$v24mfr_champ_chart <- highcharter::renderHighchart({
    a <- applied_rk()
    if (is.null(a)) {
      return(v6_24_hc_empty("Click Analyze Ranking Diagnostics."))
    }
    ch <- v6_24_mf_champion_count_rows()
    if (!nrow(ch)) return(v6_24_hc_empty("No champion counts available."))
    s <- v6_24_mf_universe_summary()
    ch <- ch[order(-ch$series_champion_count), , drop = FALSE]
    pts <- lapply(seq_len(nrow(ch)), function(i) list(
      y = as.integer(ch$series_champion_count[i]),
      name = as.character(ch$model_name[i]),
      fam = as.character(ch$display_family[i])))
    highcharter::highchart() |>
      highcharter::hc_chart(type = "bar",
                            style = list(fontFamily = V6_24_CHART_FONT)) |>
      highcharter::hc_title(text = "Series-level champion count",
        style = list(fontSize = "15px", fontWeight = "600", color = "#102a43")) |>
      highcharter::hc_subtitle(
        text = paste0(nrow(ch), " models lead at least one series \u00b7 bars sum to ",
                      s$champion_visible, " presentable series \u00b7 ",
                      s$champion_suppressed, " no-signal series excluded"),
        style = list(fontSize = "12px", color = "#627d98")) |>
      highcharter::hc_xAxis(categories = as.list(as.character(ch$model_name)),
                            title = list(text = NULL),
                            labels = list(style = list(fontSize = "11px"))) |>
      highcharter::hc_yAxis(title = list(text = "Series led"),
                            allowDecimals = FALSE) |>
      highcharter::hc_legend(enabled = FALSE) |>
      highcharter::hc_tooltip(headerFormat = "", pointFormat = paste0(
        "<b>{point.name}</b><br/>Family: {point.fam}<br/>",
        "Number of series where this model is the presentable champion: ",
        "<b>{point.y}</b>")) |>
      highcharter::hc_exporting(enabled = TRUE) |>
      highcharter::hc_credits(enabled = FALSE) |>
      highcharter::hc_plotOptions(bar = list(color = "#0f9d6e",
        borderRadius = 2, dataLabels = list(enabled = TRUE))) |>
      highcharter::hc_add_series(name = "Series led", data = pts)
  })

  output$v24mfr_disagree <- DT::renderDataTable({
    a <- applied_rk()
    if (is.null(a)) return(v6_24_dt(NULL))
    d <- v6_24_mf_metric_disagreement_rows()
    if (is.null(d) || !nrow(d)) return(v6_24_dt(NULL))
    out <- d
    names(out)[names(out) == "model_name"] <- "Model"
    names(out)[names(out) == "best_position"] <- "Best position"
    names(out)[names(out) == "worst_position"] <- "Worst position"
    names(out)[names(out) == "position_spread"] <- "Spread"
    v6_24_dt(out, page_length = 15L, paging = FALSE, searching = FALSE)
  })

  # ---- ranking assistant ------------------------------------------------
  local({
    id <- function(s) paste0("v24_mfr_asst_", s)
    st <- reactiveValues(intent = NULL, question = "", stamp = NULL)
    for (p in V6_24_MF_RANKING_PROMPTS) {
      local({
        pp <- p
        observeEvent(input[[id(pp$id)]], {
          st$intent <- pp$intent; st$question <- pp$label
          st$stamp <- format(Sys.time(), "%H:%M:%S")
        }, ignoreInit = TRUE)
      })
    }
    observeEvent(input[[id("generate")]], {
      q <- input[[id("question")]]
      st$question <- if (is.null(q)) "" else trimws(q)
      st$intent <- if (nzchar(st$question)) v6_24_mr_intent(st$question)
                   else "mr_summary"
      st$stamp <- format(Sys.time(), "%H:%M:%S")
    }, ignoreInit = TRUE)

    output[[id("answer")]] <- renderUI({
      if (is.null(st$intent)) {
        return(tags$p(class = "v24-note",
                      paste("Run Analyze Ranking Diagnostics, then pick a quick",
                            "prompt or type a question.")))
      }
      e <- v6_24_mr_evidence(applied_rk(), rk_rows())
      a <- v6_24_mr_answer(e, st$question, st$intent)
      tags$div(
        class = if (isTRUE(a$bounded)) "llm-panel v24-asst v24-asst-bounded"
                else "llm-panel v24-asst",
        tags$p(class = "v24-asst-q", tags$strong("Question: "), st$question),
        tags$p(class = "v24-asst-lead", a$lead),
        if (nzchar(a$body)) tags$p(class = "v24-asst-body", a$body),
        if (length(a$bullets))
          tags$ul(class = "v24-list", lapply(a$bullets, tags$li)),
        tags$div(
          class = "v24-asst-evidence",
          tags$span(class = "v24-asst-evlabel", "Evidence used:"),
          tags$span(if (identical(a$used, "none") || !length(a$used))
            "no artifact supports this question"
            else paste(a$used, collapse = " \u00b7 ")),
          tags$span(class = "v24-asst-caveat", paste0("Caveats: ", a$caveats))
        ),
        tags$p(class = "v24-asst-stamp",
               paste0("Composed locally at ", st$stamp, " \u00b7 ",
                      V6_24_ASSISTANT_ENGINE, " \u00b7 intent: ", a$intent))
      )
    })
    outputOptions(output, id("answer"), suspendWhenHidden = FALSE)
  })

  # ==========================================================================
  # V6.24-P9M | Champion FULL.
  #
  # SELECTION BEHAVIOUR
  #   Prefers the SHARED V6.24 selection used by Viewer, Accuracy and Forecast,
  #   passed in as `shared_selection`. When nothing is selected there, a compact
  #   selector built from navigation_contract takes over, and the banner says
  #   which of the two is in force. Nothing is ever defaulted silently.
  # ==========================================================================
  ch_shared <- reactive({
    if (is.null(shared_selection)) return(NULL)
    r <- try(shared_selection(), silent = TRUE)
    if (inherits(r, "try-error") || is.null(r) || !NROW(r)) return(NULL)
    as.character(r$series_id[1])
  })

  output$v24mfc_series_ui <- renderUI({
    if (!is.null(ch_shared())) return(NULL)   # shared selection wins
    nav <- v6_24_tbl("nav_contract")
    if (is.null(nav) || !nrow(nav)) return(NULL)
    ids <- as.character(nav$series_id)
    labs <- as.character(nav$route_display_label)
    ord <- order(labs)
    selectInput("v24mfc_series", "Choose a series",
                choices = stats::setNames(ids[ord], labs[ord]),
                selected = ids[ord][1], width = "480px")
  })

  ch_series <- reactive({
    s <- ch_shared()
    if (!is.null(s)) return(s)
    input$v24mfc_series
  })

  output$v24mfc_selection_banner <- renderUI({
    if (!is.null(ch_shared())) {
      r <- shared_selection()
      tags$div(class = "v24-shared-ok",
        tags$div(class = "v24-shared-head",
                 tags$span(class = "v24-pill", "Shared selection"),
                 tags$strong(as.character(r$route_display_label[1]))),
        tags$p(class = "v24-note",
               paste0("Using the current V6.24 selected series. Change it from ",
                      "Forecasting \u2192 Viewer.")))
    } else {
      tags$div(class = "v24-shared-empty",
        tags$strong("No series is selected in Forecasting \u2192 Viewer."),
        tags$span(paste("Using the page selector below instead. Selecting a",
                        "series in the Viewer will take over automatically.")))
    }
  })

  output$v24mfc_scope_line <- renderUI({
    s <- v6_24_mf_champion_summary()
    tags$ul(
      class = "v24mf-scope",
      tags$li(tags$b(s$n_series), " operational series \u00b7 ",
              tags$b(s$presentable), " with a presentable champion \u00b7 ",
              tags$b(s$suppressed), " no-signal suppressed"),
      tags$li(tags$b(s$n_leaders), " models lead at least one series \u00b7 ",
              "ranking policy ", tags$code(s$ranking_policy)),
      tags$li("Source: ", tags$code("navigation_contract"), ", ",
              tags$code("model_rankings"), ", ",
              tags$code("series_signal_quality"), ", ",
              tags$code("accuracy_metrics"))
    )
  })

  output$v24mfc_cards <- renderUI({
    s <- v6_24_mf_champion_summary()
    cell <- function(label, value, cls = "") {
      tags$div(class = paste("v24-acc-card", cls),
               tags$div(class = "v24-acc-card-label", label),
               tags$div(class = "v24-acc-card-value", value))
    }
    tags$div(
      class = "v24-acc-grid",
      cell("Operational series", s$n_series),
      cell("Presentable champion series", s$presentable),
      cell("No-signal suppressed series", s$suppressed),
      cell("Models leading at least one series", s$n_leaders),
      cell("Most series led",
           tagList(tags$span(s$top_model),
                   tags$span(class = "v24-acc-sub",
                             paste0(s$top_count, " series \u00b7 ",
                                    format(round(100 * s$top_share, 1), nsmall = 1),
                                    "% of presentable \u00b7 a count, not a cohort decision"))),
           "v24-acc-wide"),
      cell("Evidence type", s$evidence_type),
      cell("Ranking policy", s$ranking_policy),
      cell("Champion for the whole cohort", s$global_champion,
           "v24-acc-wide")
    )
  })

  output$v24mfc_dist_chart <- highcharter::renderHighchart({
    d <- v6_24_mf_champion_distribution()
    if (is.null(d) || !nrow(d)) {
      return(v6_24_hc_empty("No champion distribution available."))
    }
    s <- v6_24_mf_champion_summary()
    pts <- lapply(seq_len(nrow(d)), function(i) list(
      y = as.integer(d$series_champion_count[i]),
      name = as.character(d$model_name[i]),
      fam = as.character(d$display_family[i]),
      share = paste0(format(round(100 * d$share_of_presentable[i], 1),
                            nsmall = 1), "%")))
    highcharter::highchart() |>
      highcharter::hc_chart(type = "bar",
                            style = list(fontFamily = V6_24_CHART_FONT)) |>
      highcharter::hc_title(text = "Series-level champion distribution",
        style = list(fontSize = "15px", fontWeight = "600", color = "#102a43")) |>
      highcharter::hc_subtitle(
        text = paste0("No-signal series excluded; this is not a cohort-wide ",
                      "champion \u00b7 bars sum to ", s$presentable,
                      " presentable series"),
        style = list(fontSize = "12px", color = "#627d98")) |>
      highcharter::hc_xAxis(categories = as.list(as.character(d$model_name)),
                            title = list(text = NULL),
                            labels = list(style = list(fontSize = "11px"))) |>
      highcharter::hc_yAxis(title = list(text = "Series led"),
                            allowDecimals = FALSE) |>
      highcharter::hc_legend(enabled = FALSE) |>
      highcharter::hc_tooltip(headerFormat = "", pointFormat = paste0(
        "<b>{point.name}</b><br/>Family: {point.fam}<br/>",
        "Series where this model is the presentable champion: <b>{point.y}</b>",
        "<br/>Share of presentable series: {point.share}")) |>
      highcharter::hc_exporting(enabled = TRUE) |>
      highcharter::hc_credits(enabled = FALSE) |>
      highcharter::hc_plotOptions(bar = list(color = "#7a5195",
        borderRadius = 2, dataLabels = list(enabled = TRUE))) |>
      highcharter::hc_add_series(name = "Series led", data = pts)
  })

  output$v24mfc_dist_table <- DT::renderDataTable({
    d <- v6_24_mf_champion_distribution()
    if (is.null(d) || !nrow(d)) return(v6_24_dt(NULL))
    out <- data.frame(
      Model = as.character(d$model_name),
      `Display family` = as.character(d$display_family),
      `Governed family` = as.character(d$governed_family),
      `Series led` = as.integer(d$series_champion_count),
      `Share of presentable` = paste0(
        format(round(100 * d$share_of_presentable, 1), nsmall = 1), "%"),
      `Median MAE` = vapply(d$median_mae, v6_24_acc_fmt, character(1)),
      `Median RMSE` = vapply(d$median_rmse, v6_24_acc_fmt, character(1)),
      `Median WAPE` = vapply(d$median_wape, v6_24_acc_fmt, character(1)),
      `Median SMAPE` = vapply(d$median_smape, v6_24_acc_fmt, character(1)),
      Note = "series-level count, not a cohort decision",
      check.names = FALSE, stringsAsFactors = FALSE)
    v6_24_dt(out, page_length = 15L, paging = FALSE, searching = FALSE)
  })

  output$v24mfc_selected <- renderUI({
    sid <- ch_series()
    if (is.null(sid) || !nzchar(sid)) {
      return(tags$p(class = "v24-note", "Select a series to see its champion."))
    }
    x <- v6_24_mf_selected_series_champion(sid)
    if (is.null(x)) return(tags$p(class = "v24-note", "No contract row for this series."))
    kv <- function(k, v) tags$li(tags$span(class = "v24-k", k),
                                 tags$span(class = "v24-v", v))
    head_block <- if (isTRUE(x$presentable)) {
      tags$div(class = "v24-shared-ok",
        tags$div(class = "v24-shared-head",
                 tags$span(class = "v24-cell-badge v24-cell-gold",
                           "Presentable series-level champion"),
                 tags$strong(x$champion_model)),
        tags$p(class = "v24-note",
               paste0("For this series only. Other series are led by other ",
                      "models, and V6.24 defines no champion for the cohort.")))
    } else {
      tags$div(class = "v24-suppressed",
        tags$strong("No presentable champion for this series."),
        tags$p(paste0(
          "Signal quality is ", x$signal_quality,
          ", so champion_visible is FALSE. Every observed actual is zero, which ",
          "means a model predicting zero scores a perfect error without having ",
          "modelled anything.")),
        tags$p(class = "v24-note",
               tags$span(class = "v24-cell-badge v24-cell-slate",
                         "Internal tie-break / reference model, not presentable"),
               " ", x$champion_model))
    }
    tagList(
      head_block,
      tags$ul(
        class = "v24-kv-list",
        kv("Series", x$series_id),
        kv("Route", x$route),
        kv("Metric", x$metric),
        kv("Product status", x$product_status),
        kv("Signal quality", x$signal_quality),
        kv("champion_visible", if (isTRUE(x$presentable)) "TRUE" else "FALSE"),
        kv("Champion model", x$champion_model),
        kv("Champion family", x$champion_family),
        kv("Rank within this series",
           if (is.na(x$champion_rank)) "\u2014" else x$champion_rank),
        kv("Ranked by", paste0(x$rank_metric, " = ",
                               v6_24_acc_fmt(x$rank_value, 6))),
        kv("Champion validity", x$validity),
        kv("Ranking policy", x$ranking_policy),
        kv("Caveat badge", x$caveat_badge)
      ),
      if (nzchar(x$caveat_message))
        tags$p(class = "v24-caveat-msg", x$caveat_message)
    )
  })

  output$v24mfc_rank_note <- renderUI({
    sid <- ch_series()
    if (is.null(sid) || !nzchar(sid)) return(NULL)
    x <- v6_24_mf_selected_series_champion(sid)
    if (is.null(x)) return(NULL)
    if (isTRUE(x$presentable)) {
      tags$p(class = "v24-note v24-note-ok",
             paste0("Ranking for ", x$label,
                    ". The top row is this series' champion."))
    } else {
      tags$p(class = "v24-note v24-note-warn",
             paste0("Ranking for ", x$label,
                    " is not meaningful: every observed actual is zero, so the ",
                    "order is an internal tie-break rather than a comparison of ",
                    "model quality. No row here is best or recommended."))
    }
  })

  # `lazy_render = FALSE` is required here. This is the only V6.24 table whose
  # data always changes while its own section is hidden, because the series is
  # chosen over in the Viewer. With DT's default lazy rendering the new value is
  # stashed and never drawn, so the table stays frozen on the first series that
  # was rendered while every surrounding panel reports the new one.
  output$v24mfc_top5 <- DT::renderDataTable({
    sid <- ch_series()
    if (is.null(sid) || !nzchar(sid)) return(v6_24_dt(NULL))
    j <- v6_24_mf_selected_series_ranking(sid, 5L)
    if (!nrow(j)) return(v6_24_dt(NULL))
    x <- v6_24_mf_selected_series_champion(sid)
    presentable <- isTRUE(x$presentable)
    mark <- ifelse(
      toupper(as.character(j$is_series_champion)) == "TRUE",
      if (presentable) v6_24_cell_badge("\u2605 series champion", "gold")
      else v6_24_cell_badge("tie-break only", "slate"), "")
    out <- data.frame(
      Rank = as.integer(j$rank_within_series),
      Model = as.character(j$model_name),
      `Display family` = as.character(j$display_family),
      `Governed family` = as.character(j$model_family),
      MAE = vapply(j$mae, v6_24_acc_fmt, character(1)),
      RMSE = vapply(j$rmse, v6_24_acc_fmt, character(1)),
      WAPE = ifelse(as.character(j$wape_status) == "COMPUTED",
                    vapply(j$wape, v6_24_acc_fmt, character(1)), "not computable"),
      SMAPE = ifelse(as.character(j$smape_status) == "COMPUTED",
                     vapply(j$smape, v6_24_acc_fmt, character(1)), "not computable"),
      `champion_visible` = if (presentable) "TRUE" else "FALSE",
      Champion = mark,
      Note = if (presentable) "ranking within this series"
             else "not meaningful - no signal",
      check.names = FALSE, stringsAsFactors = FALSE)
    v6_24_dt(out, page_length = 5L, paging = FALSE, searching = FALSE,
             lazy_render = FALSE)
  })

  output$v24mfc_policy <- renderUI({
    p <- v6_24_mf_champion_policy_summary()
    tagList(
      tags$ul(
        class = "v24-list",
        tags$li(tags$b("Policy version. "), tags$code(p$policy),
                " \u2014 read from the contract, not chosen here."),
        tags$li(tags$b("Primary metric. "),
                paste(p$primary_metrics, collapse = ", "),
                ". Lower error is better."),
        tags$li(tags$b("Tie-break. "),
                "Where the metrics cannot separate models, a deterministic ",
                "tie-break assigns a name. On an all-zero series every model ",
                "scores identically, so the tie-break is the only thing acting ",
                "\u2014 which is exactly why those champions are suppressed."),
        tags$li(tags$b("Visibility gate. "),
                "champion_visible decides whether the result may be presented. ",
                p$n_presentable, " series pass it, ", p$n_suppressed, " do not."),
        tags$li(tags$b("Medians are not the champion. "),
                "The cohort medians on the other Models pages summarise ",
                "the same artifact but do not select the per-series champion."),
        tags$li(tags$b("Governed vs display. "),
                "The policy, the ranking and the visibility gate are governed. ",
                "The four-family grouping used for display is not.")
      ),
      tags$p(class = "v24-note",
             paste0("Champion validity across the cohort: ",
                    paste(names(p$validity), unname(p$validity),
                          sep = " = ", collapse = " \u00b7 ")))
    )
  })

  output$v24mfc_legacy <- renderUI({
    L <- v6_24_mf_legacy_champion_facts()
    s <- v6_24_mf_champion_summary()
    tagList(
      tags$p(class = "v24-note",
             tags$span(class = "v24-cell-badge v24-cell-slate", "Historical"),
             " The statements below describe the earlier model work. They are ",
             "not a current V6.24 conclusion."),
      tags$table(
        class = "v24mf-compare",
        tags$thead(tags$tr(tags$th(""), tags$th("Previous Champion page"),
                           tags$th("V6.24"))),
        tags$tbody(
          tags$tr(tags$td("Scope"), tags$td(paste0(L$legacy_entities,
                  " HDD entities")), tags$td(paste0(s$n_series, " series"))),
          tags$tr(tags$td("Decision"), tags$td("one model for everything"),
                  tags$td("per series")),
          tags$tr(tags$td("Models leading"), tags$td("1"),
                  tags$td(s$n_leaders)),
          tags$tr(tags$td(paste0(L$legacy_model, " status")),
                  tags$td("selected with conditions"),
                  tags$td(paste0("presentable champion on ",
                                 L$ets_presentable_v624, " of ",
                                 L$presentable_total, " series")))
        )
      ),
      tags$p(paste0(
        "On this cohort ", L$legacy_model, " appears as champion_model_name on ",
        L$ets_rows_v624, " contract rows, but ", L$ets_suppressed_v624,
        " of those are no-signal series where the tie-break assigns it and the ",
        "champion is suppressed. That leaves ", L$ets_presentable_v624,
        " presentable series. Restating the earlier sentence as a current ",
        "conclusion would contradict this cohort, so this page does not."))
    )
  })

  # ---- champion assistant -----------------------------------------------
  local({
    id <- function(s) paste0("v24_mfc_asst_", s)
    st <- reactiveValues(intent = NULL, question = "", stamp = NULL)
    for (p in V6_24_MF_CHAMPION_PROMPTS) {
      local({
        pp <- p
        observeEvent(input[[id(pp$id)]], {
          st$intent <- pp$intent; st$question <- pp$label
          st$stamp <- format(Sys.time(), "%H:%M:%S")
        }, ignoreInit = TRUE)
      })
    }
    observeEvent(input[[id("generate")]], {
      q <- input[[id("question")]]
      st$question <- if (is.null(q)) "" else trimws(q)
      st$intent <- if (nzchar(st$question)) v6_24_mc_intent(st$question)
                   else "mc_summary"
      st$stamp <- format(Sys.time(), "%H:%M:%S")
    }, ignoreInit = TRUE)

    output[[id("answer")]] <- renderUI({
      if (is.null(st$intent)) {
        return(tags$p(class = "v24-note",
                      paste("Pick a quick prompt or type a question. Answers",
                            "come only from the governed champion evidence.")))
      }
      sid <- ch_series()
      sel <- if (!is.null(sid) && nzchar(sid))
        v6_24_mf_selected_series_champion(sid) else NULL
      a <- v6_24_mc_answer(v6_24_mc_evidence(sel), st$question, st$intent)
      tags$div(
        class = if (isTRUE(a$bounded)) "llm-panel v24-asst v24-asst-bounded"
                else "llm-panel v24-asst",
        tags$p(class = "v24-asst-q", tags$strong("Question: "), st$question),
        tags$p(class = "v24-asst-lead", a$lead),
        if (nzchar(a$body)) tags$p(class = "v24-asst-body", a$body),
        if (length(a$bullets))
          tags$ul(class = "v24-list", lapply(a$bullets, tags$li)),
        tags$div(
          class = "v24-asst-evidence",
          tags$span(class = "v24-asst-evlabel", "Evidence used:"),
          tags$span(if (identical(a$used, "none") || !length(a$used))
            "no artifact supports this question"
            else paste(a$used, collapse = " \u00b7 ")),
          tags$span(class = "v24-asst-caveat", paste0("Caveats: ", a$caveats))
        ),
        tags$p(class = "v24-asst-stamp",
               paste0("Composed locally at ", st$stamp, " \u00b7 ",
                      V6_24_ASSISTANT_ENGINE, " \u00b7 intent: ", a$intent))
      )
    })
    outputOptions(output, id("answer"), suspendWhenHidden = FALSE)
  })

  # These outputs live in a CSS-toggled section that starts hidden, so Shiny
  # would otherwise suspend them and the page would render empty.
  for (o in c("v24mf_scope_line", "v24mf_changed", "v24mf_families",
              "v24mf_cards", "v24mf_table", "v24mf_chart",
              "v24mfr_scope_line", "v24mfr_metric_ui", "v24mfr_family_ui",
              "v24mfr_sort_ui", "v24mfr_applied", "v24mfr_cards",
              "v24mfr_table", "v24mfr_metric_chart", "v24mfr_champ_chart",
              "v24mfr_disagree",
              "v24mfc_scope_line", "v24mfc_cards", "v24mfc_dist_chart",
              "v24mfc_dist_table", "v24mfc_selection_banner",
              "v24mfc_series_ui", "v24mfc_selected", "v24mfc_rank_note",
              "v24mfc_top5", "v24mfc_policy", "v24mfc_legacy")) {
    try(outputOptions(output, o, suspendWhenHidden = FALSE), silent = TRUE)
  }

  invisible(NULL)
}
