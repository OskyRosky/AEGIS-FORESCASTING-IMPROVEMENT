# TESSERACT v2 | v6_24_mvp_server.R
# V6.24 MVP | Read-only server for the four V6.24 pages.
#
# READ-ONLY CONTRACT
#   No model execution. No forecast generation. No backtest generation.
#   No accuracy calculation. No ranking calculation. No readiness derivation.
#   No taxonomy derivation. No writes of any kind.
#
#   Champion suppression, caveats, availability and counts are read as FIELDS
#   from the governed artifacts. There is no hardcoded series list anywhere in
#   this file - not for no-signal series, not for the low-confidence series.

v6_24_mvp_server <- function(input, output, session) {

  d <- v6_24_load_all()
  nav_all <- v6_24_operational()

  # ------------------------------------------------------------ filter engine
  # Builds the cascading selectors for one page prefix. Options at each depth
  # come from navigation_contract filtered by the choices already made, so an
  # empty result set is unreachable rather than merely discouraged.
  make_filter_flow <- function(prefix) {

    chosen <- function() {
      out <- list()
      for (ax in V6_24_FILTER_AXES) {
        v <- input[[paste0(prefix, "_", ax)]]
        if (!is.null(v) && nzchar(v)) out[[ax]] <- v
      }
      out
    }

    # Choices for an axis depend only on the axes ABOVE it.
    opts_for <- function(axis) {
      depth <- match(axis, V6_24_FILTER_AXES)
      parents <- V6_24_FILTER_AXES[seq_len(depth - 1)]
      ch <- chosen()
      ch <- ch[names(ch) %in% parents]
      v6_24_axis_options(axis, ch)
    }

    for (ax in V6_24_FILTER_AXES) {
      local({
        axis <- ax
        output[[paste0(prefix, "_sel_", axis)]] <- renderUI({
          opts <- opts_for(axis)
          lab <- V6_24_FILTER_LABELS[[axis]]
          if (!length(opts)) {
            return(tags$div(class = "v24-filter-disabled",
                            tags$label(lab),
                            tags$div(class = "v24-filter-none",
                                     "select the level above")))
          }
          cur <- input[[paste0(prefix, "_", axis)]]
          sel <- if (!is.null(cur) && cur %in% opts) cur else opts[1]
          selectInput(paste0(prefix, "_", axis), lab,
                      choices = opts, selected = sel, width = "100%")
        })
      })
    }

    # The resolved series for this page. A complete six-level path resolves to
    # exactly one row; anything shorter is reported honestly instead of guessed.
    resolved <- reactive({
      rows <- v6_24_resolve(chosen())
      if (nrow(rows) == 1L) rows[1, , drop = FALSE] else NULL
    })

    output[[paste0(prefix, "_status")]] <- renderUI({
      rows <- v6_24_resolve(chosen())
      if (nrow(rows) == 1L) {
        tags$div(class = "v24-filter-ok",
                 tags$strong("Selected: "), rows$series_id[1],
                 tags$span(class = "v24-note",
                           paste0("  \u2014 path ", rows$valid_filter_path[1])))
      } else if (nrow(rows) == 0L) {
        tags$div(class = "v24-filter-warn",
                 "No series matches this combination.")
      } else {
        tags$div(class = "v24-filter-warn",
                 paste0(nrow(rows), " series match. Complete the remaining ",
                        "levels to select one."))
      }
    })

    resolved
  }

  vw_series <- make_filter_flow("v24_vw")
  fc_series <- make_filter_flow("v24_fc")

  # ------------------------------------------------------------ 1. Overview
  output$v24_ov_cards <- renderUI({
    g <- v6_24_tax_scope("GLOBAL")
    if (!nrow(g)) return(tags$p("taxonomy_counts is not available."))
    n <- nav_all
    tagList(
      v24_card("Operational series", g$operational_series_count[1],
               "navigation_contract OPERATIONAL_ENTITY rows"),
      v24_card("Product ready", sum(n$product_ready == "TRUE"),
               "derived from governed artifacts"),
      v24_card("Viewer visible", g$viewer_visible_count[1], NULL),
      v24_card("Forecast visible", g$forecast_visible_count[1], NULL),
      v24_card("Ranking visible", sum(n$ranking_visible == "TRUE"), NULL),
      v24_card("Champion visible", g$champion_visible_count[1],
               "suppressed where not meaningful"),
      v24_card("Available", g$available_count[1], NULL),
      v24_card("Available with caveat", g$available_with_caveat_count[1], NULL),
      v24_card("No-signal series", g$no_signal_count[1],
               "all actuals are zero"),
      v24_card("Low-confidence window",
               sum(n$low_confidence_backtest_window_flag == "TRUE"),
               "backtest window is a zero tail"),
      v24_card("Forecast type", V6_24_FORECAST_TYPE, V6_24_HORIZON_LABEL),
      v24_card("Median WAPE", v6_24_fmt_median(g$median_wape[1]),
               "series-weighted median, never a mean")
    )
  })

  output$v24_ov_by_metric <- DT::renderDT({
    bm <- v6_24_tax_scope("BY_METRIC")
    if (!nrow(bm)) return(NULL)
    out <- data.frame(
      Metric = bm$filter_value,
      Series = bm$operational_series_count,
      `Viewer visible` = bm$viewer_visible_count,
      `Forecast visible` = bm$forecast_visible_count,
      `Champion visible` = bm$champion_visible_count,
      Available = bm$available_count,
      `With caveat` = bm$available_with_caveat_count,
      `No signal` = bm$no_signal_count,
      `Median WAPE` = vapply(bm$median_wape, v6_24_fmt_median, character(1)),
      check.names = FALSE, stringsAsFactors = FALSE)
    DT::datatable(out, rownames = FALSE, options = list(dom = "t", paging = FALSE))
  })

  output$v24_ov_by_signal <- DT::renderDT({
    sq <- v6_24_tax_scope("BY_SIGNAL_QUALITY")
    cv <- v6_24_tax_scope("BY_CHAMPION_VALIDITY")
    if (!nrow(sq)) return(NULL)
    out <- rbind(
      data.frame(Scope = "Signal quality", Value = sq$filter_value,
                 Series = sq$operational_series_count,
                 `Champion visible` = sq$champion_visible_count,
                 check.names = FALSE, stringsAsFactors = FALSE),
      data.frame(Scope = "Champion validity", Value = cv$filter_value,
                 Series = cv$operational_series_count,
                 `Champion visible` = cv$champion_visible_count,
                 check.names = FALSE, stringsAsFactors = FALSE))
    DT::datatable(out, rownames = FALSE, options = list(dom = "t", paging = FALSE))
  })

  output$v24_ov_loader <- DT::renderDT({
    v <- d$validation
    if (is.null(v)) return(NULL)
    DT::datatable(v, rownames = FALSE,
                  options = list(pageLength = 10, dom = "tp"))
  })

  # ------------------------------------------------------------ 2. Viewer
  output$v24_vw_identity <- renderUI({
    r <- vw_series()
    if (is.null(r)) return(tags$p(class = "v24-note",
                                  "Complete the filter path to load a series."))
    tagList(
      tags$h3(r$route_display_label[1]),
      tags$ul(
        class = "v24-kv-list",
        v24_kv("Series", r$series_id[1]),
        v24_kv("Metric", r$metric[1]),
        v24_kv("DB type", r$db_type[1]),
        v24_kv("Scenario", r$scenario[1]),
        v24_kv("Segment", r$segment[1]),
        v24_kv("Granularity", r$granularity[1]),
        v24_kv("Key", r$key[1]),
        v24_kv("Key role", r$key_axis_status[1]),
        v24_kv("Route", r$route_path[1]),
        v24_kv("Product status", r$product_status[1]),
        v24_kv("Signal quality", r$signal_quality_status[1])
      ),
      v24_badges_ui(r$caveat_badge[1]),
      tags$p(class = "v24-caveat-msg", r$caveat_message[1])
    )
  })

  output$v24_vw_champion <- renderUI({
    r <- vw_series()
    if (is.null(r)) return(NULL)
    # Suppression is driven by the champion_visible FIELD, not by any list.
    if (identical(as.character(r$champion_visible[1]), "TRUE")) {
      tagList(
        tags$h3("Champion model"),
        tags$ul(class = "v24-kv-list",
                v24_kv("Champion", r$champion_model_name[1]),
                v24_kv("Ranked by", r$champion_rank_metric[1]),
                v24_kv("Value", v6_24_fmt_median(r$champion_rank_value[1], 6)),
                v24_kv("Validity", r$champion_validity[1]),
                v24_kv("Median WAPE", v6_24_fmt_median(r$median_wape[1])),
                v24_kv("Median MAE", v6_24_fmt_median(r$median_mae[1], 6)))
      )
    } else {
      tagList(
        tags$h3("Champion model"),
        tags$div(class = "v24-suppressed",
                 tags$strong("Champion is not meaningful for this no-signal series."),
                 tags$p(paste("Every observed actual for this series is zero, so a",
                              "champion is only a technical tie-break. Models below",
                              "are shown for technical inspection and must not be",
                              "read as a recommendation."))),
        tags$ul(class = "v24-kv-list",
                v24_kv("Technical champion (not a recommendation)",
                       r$champion_model_name[1]),
                v24_kv("Validity", r$champion_validity[1]))
      )
    }
  })

  output$v24_vw_model_sel <- renderUI({
    r <- vw_series()
    if (is.null(r)) return(NULL)
    rk <- d$model_rankings
    rk <- rk[rk$series_id == r$series_id[1], , drop = FALSE]
    rk <- rk[order(as.integer(rk$rank_within_series)), , drop = FALSE]
    models <- as.character(rk$model_name)
    # Default to the champion only when it is a meaningful recommendation.
    dflt <- if (identical(as.character(r$champion_visible[1]), "TRUE"))
      as.character(r$champion_model_name[1]) else
        if ("ETS Explicit" %in% models) "ETS Explicit" else models[1]
    selectInput("v24_vw_model", "Model", choices = models, selected = dflt,
                width = "320px")
  })

  output$v24_vw_actuals <- plotly::renderPlotly({
    r <- vw_series()
    if (is.null(r)) return(plotly::plotly_empty())
    a <- d$actuals
    a <- a[a$series_id == r$series_id[1], , drop = FALSE]
    a <- a[order(a$series_date), , drop = FALSE]
    plotly::plot_ly(a, x = ~series_date, y = ~actual_value, type = "scatter",
                    mode = "lines", name = "actual") |>
      plotly::layout(xaxis = list(title = ""), yaxis = list(title = "actual"),
                     margin = list(t = 20))
  })

  output$v24_vw_backtest <- plotly::renderPlotly({
    r <- vw_series()
    m <- input$v24_vw_model
    if (is.null(r) || is.null(m)) return(plotly::plotly_empty())
    b <- d$backtests
    b <- b[b$series_id == r$series_id[1] & b$model_name == m, , drop = FALSE]
    if (!nrow(b)) return(plotly::plotly_empty())
    b <- b[order(b$target_date), , drop = FALSE]
    plotly::plot_ly(b, x = ~target_date, y = ~actual_value, type = "scatter",
                    mode = "markers", name = "actual",
                    marker = list(size = 4)) |>
      plotly::add_trace(y = ~predicted_value, mode = "markers",
                        name = paste("predicted -", m),
                        marker = list(size = 4)) |>
      plotly::layout(xaxis = list(title = ""), yaxis = list(title = "value"),
                     margin = list(t = 20))
  })

  output$v24_vw_rank_note <- renderUI({
    r <- vw_series()
    if (is.null(r)) return(NULL)
    tags$span(paste0("Ranking policy ", V6_24_RANKING_POLICY,
                     ". Ranks and errors are read from model_rankings and ",
                     "accuracy_metrics; nothing is recalculated in Shiny."))
  })

  output$v24_vw_ranking <- DT::renderDT({
    r <- vw_series()
    if (is.null(r)) return(NULL)
    sid <- r$series_id[1]
    rk <- d$model_rankings
    rk <- rk[rk$series_id == sid, , drop = FALSE]
    ac <- d$accuracy_metrics
    ac <- ac[ac$series_id == sid, , drop = FALSE]
    j <- merge(rk, ac[, c("model_name", "mae", "rmse", "wape", "smape",
                          "wape_status")],
               by = "model_name", all.x = TRUE)
    j <- j[order(as.integer(j$rank_within_series)), , drop = FALSE]
    show_champ <- identical(as.character(r$champion_visible[1]), "TRUE")
    out <- data.frame(
      Rank = j$rank_within_series,
      Model = j$model_name,
      `Ranked by` = j$primary_rank_metric,
      `Rank value` = vapply(j$primary_rank_value,
                            function(x) v6_24_fmt_median(x, 6), character(1)),
      WAPE = ifelse(j$wape_status == "COMPUTED",
                    vapply(j$wape, function(x) v6_24_fmt_median(x, 6),
                           character(1)),
                    "not computable"),
      MAE = vapply(j$mae, function(x) v6_24_fmt_median(x, 6), character(1)),
      RMSE = vapply(j$rmse, function(x) v6_24_fmt_median(x, 6), character(1)),
      Champion = ifelse(j$is_series_champion == "TRUE",
                        if (show_champ) "champion" else "technical only", ""),
      check.names = FALSE, stringsAsFactors = FALSE)
    DT::datatable(out, rownames = FALSE,
                  options = list(pageLength = 15, dom = "t", paging = FALSE))
  })

  # ------------------------------------------------------------ 3. Forecast
  output$v24_fc_identity <- renderUI({
    r <- fc_series()
    if (is.null(r)) return(tags$p(class = "v24-note",
                                  "Complete the filter path to load a series."))
    tagList(
      tags$h3(r$route_display_label[1]),
      tags$ul(
        class = "v24-kv-list",
        v24_kv("Series", r$series_id[1]),
        v24_kv("Forecast type", r$forecast_type[1]),
        v24_kv("Forecast steps", r$forecast_steps[1]),
        v24_kv("Forecast window",
               paste(r$forecast_start_date[1], "\u2192", r$forecast_end_date[1])),
        v24_kv("Latest actual", {
          fo <- d$forecast_outputs
          fo <- fo[fo$series_id == r$series_id[1], , drop = FALSE]
          if (nrow(fo)) v6_24_fmt_median(fo$latest_actual_value[1], 4) else "n/a"
        }),
        v24_kv("Negative forecast rows", r$negative_forecast_count[1]),
        v24_kv("Extreme forecast rows", r$extreme_forecast_count[1]),
        v24_kv("Product status", r$product_status[1])
      ),
      v24_badges_ui(r$caveat_badge[1])
    )
  })

  output$v24_fc_model_sel <- renderUI({
    r <- fc_series()
    if (is.null(r)) return(NULL)
    fo <- d$forecast_outputs
    models <- sort(unique(as.character(
      fo[fo$series_id == r$series_id[1], "model_name"])))
    dflt <- if (identical(as.character(r$champion_visible[1]), "TRUE"))
      as.character(r$champion_model_name[1]) else
        if ("ETS Explicit" %in% models) "ETS Explicit" else models[1]
    selectInput("v24_fc_model", "Model", choices = models, selected = dflt,
                width = "320px")
  })

  fc_rows <- reactive({
    r <- fc_series()
    m <- input$v24_fc_model
    if (is.null(r) || is.null(m)) return(NULL)
    fo <- d$forecast_outputs
    fo <- fo[fo$series_id == r$series_id[1] & fo$model_name == m, , drop = FALSE]
    if (!nrow(fo)) return(NULL)
    fo[order(as.integer(fo$forecast_step)), , drop = FALSE]
  })

  output$v24_fc_chart <- plotly::renderPlotly({
    f <- fc_rows()
    r <- fc_series()
    if (is.null(f)) return(plotly::plotly_empty())
    # Recent observed history for context. Read, not recomputed.
    a <- d$actuals
    a <- a[a$series_id == r$series_id[1], , drop = FALSE]
    a <- a[order(a$series_date), , drop = FALSE]
    if (nrow(a) > 90) a <- utils::tail(a, 90)
    p <- plotly::plot_ly()
    if (nrow(a)) {
      p <- plotly::add_trace(p, x = a$series_date, y = a$actual_value,
                             type = "scatter", mode = "lines",
                             name = "observed actual")
    }
    plotly::add_trace(p, x = f$forecast_date, y = f$predicted_value,
                      type = "scatter", mode = "lines+markers",
                      name = paste0("forecast (", V6_24_FORECAST_STEPS,
                                    " steps)")) |>
      plotly::layout(xaxis = list(title = ""), yaxis = list(title = "value"),
                     margin = list(t = 20))
  })

  output$v24_fc_table <- DT::renderDT({
    f <- fc_rows()
    if (is.null(f)) return(NULL)
    out <- data.frame(
      Step = f$forecast_step,
      Date = as.character(f$forecast_date),
      `Predicted value` = vapply(f$predicted_value,
                                 function(x) v6_24_fmt_median(x, 6),
                                 character(1)),
      Negative = f$negative_forecast_flag,
      Extreme = f$extreme_forecast_flag,
      check.names = FALSE, stringsAsFactors = FALSE)
    DT::datatable(out, rownames = FALSE,
                  options = list(pageLength = 30, dom = "t", paging = FALSE))
  })

  # ------------------------------------------------------------ 4. Taxonomy
  output$v24_tx_scope_sel <- renderUI({
    tx <- d$tax_counts
    scopes <- unique(as.character(tx$count_scope))
    selectInput("v24_tx_scope", "Count scope", choices = scopes,
                selected = scopes[1], width = "420px")
  })

  output$v24_tx_table <- DT::renderDT({
    sc <- input$v24_tx_scope
    tx <- d$tax_counts
    if (is.null(sc)) return(NULL)
    r <- tx[tx$count_scope == sc, , drop = FALSE]
    out <- data.frame(
      Axis = r$filter_axis, Value = r$filter_value,
      Parent = r$parent_filter_path,
      Series = r$operational_series_count,
      Viewer = r$viewer_visible_count,
      Forecast = r$forecast_visible_count,
      Champion = r$champion_visible_count,
      `No signal` = r$no_signal_count,
      Available = r$available_count,
      `With caveat` = r$available_with_caveat_count,
      `Median WAPE` = vapply(r$median_wape, v6_24_fmt_median, character(1)),
      `Median MAE` = vapply(r$median_mae, function(x) v6_24_fmt_median(x, 6),
                            character(1)),
      check.names = FALSE, stringsAsFactors = FALSE)
    DT::datatable(out, rownames = FALSE,
                  options = list(pageLength = 25, scrollX = TRUE))
  })

  output$v24_tx_caveats <- DT::renderDT({
    n <- nav_all
    codes <- unlist(lapply(n$caveat_badge, v6_24_badges))
    if (!length(codes)) return(NULL)
    tb <- as.data.frame(table(codes), stringsAsFactors = FALSE)
    names(tb) <- c("Caveat", "Series")
    tb$Severity <- vapply(tb$Caveat, v6_24_caveat_severity, character(1))
    tb$Blocking <- "no"
    tb <- tb[order(-tb$Series), c("Caveat", "Severity", "Series", "Blocking")]
    DT::datatable(tb, rownames = FALSE,
                  options = list(dom = "t", paging = FALSE))
  })

  output$v24_tx_filters <- DT::renderDT({
    rows <- list()
    for (ax in V6_24_FILTER_AXES) {
      opts <- v6_24_axis_options(ax)
      for (o in opts) {
        sub <- nav_all[as.character(nav_all[[ax]]) == o, , drop = FALSE]
        rows[[length(rows) + 1]] <- data.frame(
          Axis = ax, Option = o, Series = nrow(sub),
          `Viewer visible` = sum(sub$viewer_visible == "TRUE"),
          check.names = FALSE, stringsAsFactors = FALSE)
      }
    }
    out <- do.call(rbind, rows)
    DT::datatable(out, rownames = FALSE,
                  options = list(pageLength = 25, scrollX = TRUE))
  })

  invisible(NULL)
}
