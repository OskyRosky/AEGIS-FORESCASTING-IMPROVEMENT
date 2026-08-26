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

  # ------------------------------------------------------------ selection
  # P9C | One shared progressive selection for the whole V6.24 section.
  #
  # State is held explicitly rather than read back from the inputs, because
  # that is what makes a downstream reset deterministic: when a parent axis
  # changes, every axis below it is cleared in one place instead of relying on
  # each control noticing that its old value disappeared.
  sel <- reactiveValues()
  for (.a in V6_24_FILTER_AXES) sel[[.a]] <- ""

  chosen <- reactive({
    out <- list()
    for (a in V6_24_FILTER_AXES) out[[a]] <- sel[[a]]
    out
  })

  # Register one observer per axis. Choosing an axis clears everything below.
  for (.ax in V6_24_FILTER_AXES) {
    local({
      axis <- .ax
      depth <- match(axis, V6_24_FILTER_AXES)
      observeEvent(input[[paste0("v24_sel_", axis)]], {
        v <- input[[paste0("v24_sel_", axis)]]
        v <- if (is.null(v)) "" else as.character(v)
        if (identical(sel[[axis]], v)) return()
        sel[[axis]] <- v
        for (d in V6_24_FILTER_AXES[-seq_len(depth)]) sel[[d]] <- ""
      }, ignoreInit = TRUE, ignoreNULL = FALSE)
    })
  }

  plan_now <- reactive(v6_24_selection_plan(chosen()))

  # The rail. Only axes that can still discriminate become controls; an axis
  # with a single possible value is stated as context instead of asked.
  output$v24_sel_controls <- renderUI({
    sp <- plan_now()
    items <- list()
    for (a in V6_24_FILTER_AXES) {
      st <- sp$plan[[a]]
      if (is.null(st) || identical(st$state, "LOCKED")) next
      if (identical(st$state, "CONTEXT")) {
        shown <- st$selected
        if (isTRUE(st$conditional)) {
          w <- V6_24_CONDITIONAL_WORDING[[st$selected]]
          shown <- if (is.null(w) || is.na(w)) st$selected else w
        }
        items[[length(items) + 1]] <- tags$div(
          class = paste("v24-field is-context",
                        if (isTRUE(st$conditional)) "is-na" else ""),
          tags$label(class = "v24-field-label", st$label),
          tags$div(class = "v24-context-value", shown),
          tags$p(class = "v24-field-hint",
                 if (isTRUE(st$conditional))
                   "Shown as context; there is nothing to choose here."
                 else "Only one value applies on this branch."))
        next
      }
      # A real choice. Long lists get a searchable control.
      ctl <- if (length(st$values) > 12) {
        selectizeInput(
          paste0("v24_sel_", a), NULL,
          choices = c("Select..." = "", stats::setNames(st$values, st$values)),
          selected = st$selected, width = "100%",
          options = list(placeholder = paste("Search", tolower(st$label)),
                         maxOptions = 400, create = FALSE))
      } else {
        selectInput(
          paste0("v24_sel_", a), NULL,
          choices = c("Select..." = "", stats::setNames(st$values, st$values)),
          selected = st$selected, width = "100%")
      }
      items[[length(items) + 1]] <- tags$div(
        class = "v24-field",
        tags$label(class = "v24-field-label", st$label),
        ctl,
        tags$p(class = "v24-field-hint", V6_24_AXIS_HINT[[a]]))
    }
    tagList(items)
  })

  output$v24_sel_breadcrumb <- renderUI(v6_24_breadcrumb(plan_now()$plan))

  # The shared selected series. Everything downstream reads this one reactive,
  # so the Viewer and the Forecast page can never disagree about the series.
  selected_series <- reactive({
    sp <- plan_now()
    if (nrow(sp$rows) == 1L) sp$rows[1, , drop = FALSE] else NULL
  })

  output$v24_sel_state <- renderUI({
    sp <- plan_now()
    n <- nrow(sp$rows)
    if (n == 1L) {
      r <- sp$rows[1, , drop = FALSE]
      return(tagList(
        v6_24_status_badge(as.character(r$product_status[1])),
        v24_badges_ui(r$caveat_badge[1])))
    }
    if (n == 0L) {
      return(tags$div(class = "v24-rbadge is-empty",
                      tags$strong("No match"),
                      tags$span("No operational series matches this path.")))
    }
    tags$div(class = "v24-rbadge is-pending",
             tags$strong(paste0(n, " series in scope")),
             tags$span("Complete the remaining levels to resolve one series."))
  })

  output$v24_sel_cards <- renderUI({
    r <- selected_series()
    if (is.null(r)) {
      return(tags$p(class = "v24-note",
                    "Route details appear once the path resolves to one series."))
    }
    tagList(v6_24_route_cards(r), v6_24_context_notes(r))
  })

  # Read-only mirror for pages that consume the selection but must not own an
  # independent series selector. Rendered once per consuming page under its own
  # output id: a single id used twice makes Shiny warn about a duplicate output
  # and leaves one of the two panels stale.
  v24_shared_selection_ui <- function() {
    r <- selected_series()
    if (is.null(r)) {
      return(tags$div(
        class = "v24-shared-empty",
        tags$strong("No series selected yet."),
        tags$span(paste("The V6.24 selection is shared across the section.",
                        "Open Forecasting \u2192 Viewer to choose a series."))))
    }
    tags$div(
      class = "v24-shared-ok",
      tags$div(class = "v24-shared-head",
               tags$span(class = "v24-pill", "Shared selection"),
               tags$strong(as.character(r$route_display_label[1]))),
      v6_24_breadcrumb(plan_now()$plan),
      tags$p(class = "v24-note",
             paste0("Series ", as.character(r$series_id[1]),
                    " \u00b7 change it from Forecasting \u2192 Viewer.")))
  }
  output$v24_shared_selection <- renderUI(v24_shared_selection_ui())
  output$v24_acc_shared_selection <- renderUI(v24_shared_selection_ui())

  vw_series <- selected_series
  fc_series <- selected_series

  # ------------------------------------------------ backtest configuration
  # P9D | Pending versus applied configuration.
  #
  # Changing a control updates the PENDING state only. The results panel reads
  # the APPLIED state, which advances solely when Analyze Backtest is clicked.
  # This is the legacy behaviour and it matters here: with several models and
  # thousands of prepared rows, redrawing on every checkbox tick feels broken.
  cfg <- reactiveValues(models = character(0), horizon = NA_integer_,
                        applied = NULL, series = "")

  bt_avail <- reactive({
    r <- selected_series()
    v6_24_backtest_availability(if (is.null(r)) "" else as.character(r$series_id[1]))
  })

  cur_series <- reactive({
    r <- selected_series()
    if (is.null(r)) "" else as.character(r$series_id[1])
  })

  reset_config <- function(sid) {
    cfg$series <- sid
    cfg$models <- v6_24_default_models(sid)
    cfg$horizon <- v6_24_default_horizon(sid)
    cfg$applied <- NULL
  }

  # A new series invalidates the whole configuration, including anything the
  # user had already analysed for the previous one.
  observeEvent(cur_series(), {
    reset_config(cur_series())
  }, ignoreInit = FALSE)

  observeEvent(input$v24_bt_reset, reset_config(cur_series()), ignoreInit = TRUE)

  observeEvent(input$v24_bt_horizon, {
    v <- suppressWarnings(as.integer(input$v24_bt_horizon))
    if (!is.na(v)) cfg$horizon <- v
  }, ignoreInit = TRUE)

  # One observer per family group so a tick in any group updates the pending set.
  for (.f in V6_24_FAMILY_ORDER) {
    local({
      fam <- .f
      observeEvent(input[[paste0("v24_bt_fam_", fam)]], {
        picked <- character(0)
        for (f2 in V6_24_FAMILY_ORDER) {
          v <- input[[paste0("v24_bt_fam_", f2)]]
          if (!is.null(v)) picked <- c(picked, as.character(v))
        }
        cfg$models <- V6_24_GOVERNED_MODELS[V6_24_GOVERNED_MODELS %in% picked]
      }, ignoreInit = TRUE, ignoreNULL = FALSE)
    })
  }

  observeEvent(input$v24_bt_analyze, {
    if (!isTRUE(bt_avail()$available) || !length(cfg$models)) return()
    cfg$applied <- list(series = cur_series(), models = cfg$models,
                        horizon = cfg$horizon,
                        at = format(Sys.time(), "%H:%M:%S"))
  }, ignoreInit = TRUE)

  output$v24_bt_availability <- renderUI({
    a <- bt_avail()
    if (identical(a$status, "NO_SELECTION")) {
      return(tags$div(class = "v24-avail is-pending",
                      tags$strong("No series selected"),
                      tags$span("Choose a series above to configure a backtest.")))
    }
    if (!isTRUE(a$available)) {
      return(tags$div(class = "v24-avail is-none",
                      tags$strong("Backtest not available"),
                      tags$span(a$message)))
    }
    tags$div(class = "v24-avail is-ok",
             tags$strong("Backtest available"),
             tags$span(a$message))
  })

  output$v24_bt_horizon_ui <- renderUI({
    sid <- cur_series()
    hz <- v6_24_available_horizons(sid)
    if (!length(hz)) {
      return(tags$div(class = "v24-field-hint",
                      "No governed horizon is available for this selection."))
    }
    sel <- if (!is.na(cfg$horizon) && cfg$horizon %in% hz) cfg$horizon else hz[1]
    radioButtons("v24_bt_horizon", NULL, inline = TRUE,
                 choiceNames = paste0(hz, " days"),
                 choiceValues = as.character(hz),
                 selected = as.character(sel))
  })

  output$v24_bt_model_count <- renderUI({
    n <- length(cfg$models)
    tags$span(class = "v24-model-count",
              sprintf("%d of %d selected", n, length(V6_24_GOVERNED_MODELS)))
  })

  output$v24_bt_model_groups <- renderUI({
    sid <- cur_series()
    ch <- v6_24_champion(sid)
    present <- v6_24_models_for_series(sid)
    tags$div(
      class = "v24-fam-grid",
      lapply(v6_24_family_groups(), function(g) {
        avail <- g$models[g$models %in% present]
        if (!length(avail)) avail <- g$models
        tags$div(
          class = "v24-fam",
          tags$div(class = "v24-fam-title", g$label),
          checkboxGroupInput(
            paste0("v24_bt_fam_", g$family), NULL,
            choiceNames = lapply(avail, function(m) {
              lbl <- v6_24_model_label(m, ch)
              if (isTRUE(ch$meaningful) && identical(m, ch$model))
                tags$span(m, tags$span(class = "v24-star", "\u2605 champion"))
              else tags$span(lbl)
            }),
            choiceValues = as.list(avail),
            selected = intersect(avail, cfg$models)))
      }))
  })

  output$v24_bt_champion_note <- renderUI({
    sid <- cur_series()
    if (!nzchar(sid)) return(NULL)
    ch <- v6_24_champion(sid)
    if (isTRUE(ch$meaningful)) {
      return(tags$p(class = "v24-field-hint",
                    sprintf("Champion for this series is %s, ranked by %s.",
                            ch$model, ch$rank_metric)))
    }
    tags$div(class = "v24-soft-note",
             tags$strong("Champion is not meaningful for this no-signal series."),
             tags$span(paste("Models can still be compared technically, but none",
                             "is presented as a winner.")))
  })

  output$v24_bt_analyze_btn <- renderUI({
    ok <- isTRUE(bt_avail()$available) && length(cfg$models) > 0
    if (!ok) {
      return(tags$span(
        class = "v24-btn-primary is-disabled",
        title = "Select a series with prepared backtest rows and at least one model",
        "Analyze Backtest"))
    }
    actionButton("v24_bt_analyze", "Analyze Backtest", class = "v24-btn-primary")
  })

  output$v24_bt_applied <- renderUI({
    a <- cfg$applied
    if (is.null(a)) {
      return(tags$p(class = "v24-field-hint is-pending",
                    "Nothing analysed yet for this selection."))
    }
    tags$p(class = "v24-applied",
           sprintf("Analysed: %d model%s at horizon %s days \u00b7 %s",
                   length(a$models), if (length(a$models) == 1) "" else "s",
                   a$horizon, a$at))
  })

  # Applied configuration, exposed for the results panel and for P9E.
  applied_cfg <- reactive(cfg$applied)

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

  output$v24_ov_by_metric <- DT::renderDataTable({
    bm <- v6_24_tax_scope("BY_METRIC")
    if (!nrow(bm)) return(v6_24_dt(NULL))
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
    v6_24_dt(out, paging = FALSE, searching = FALSE)
  })

  output$v24_ov_by_signal <- DT::renderDataTable({
    sq <- v6_24_tax_scope("BY_SIGNAL_QUALITY")
    cv <- v6_24_tax_scope("BY_CHAMPION_VALIDITY")
    if (!nrow(sq)) return(v6_24_dt(NULL))
    out <- rbind(
      data.frame(Scope = "Signal quality", Value = sq$filter_value,
                 Series = sq$operational_series_count,
                 `Champion visible` = sq$champion_visible_count,
                 check.names = FALSE, stringsAsFactors = FALSE),
      data.frame(Scope = "Champion validity", Value = cv$filter_value,
                 Series = cv$operational_series_count,
                 `Champion visible` = cv$champion_visible_count,
                 check.names = FALSE, stringsAsFactors = FALSE))
    v6_24_dt(out, paging = FALSE, searching = FALSE)
  })

  output$v24_ov_loader <- DT::renderDataTable({
    v <- d$validation
    if (is.null(v)) return(v6_24_dt(NULL))
    v6_24_dt(v, page_length = 10L)
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

  output$v24_vw_model_sel <- renderUI(NULL)

  # P9E | Highcharter. Observed history as a single line, markers off because a
  # series runs to several hundred points.
  output$v24_vw_actuals <- highcharter::renderHighchart({
    r <- vw_series()
    if (is.null(r)) {
      return(v6_24_hc_empty("Complete the filter path to load a series."))
    }
    v6_24_hc_actuals(r$series_id[1], r$route_display_label[1])
  })

  # P9E | Highcharter backtest comparison. Reads the APPLIED configuration, so
  # it changes only when Analyze Backtest is clicked, and draws LINES - the
  # observed actual plus one line per selected model at the single applied
  # horizon. Row filtering stays in v6_24_backtest_rows(); this output only
  # draws what that function returns.
  output$v24_vw_backtest <- highcharter::renderHighchart({
    a <- applied_cfg()
    r <- vw_series()
    lbl <- if (is.null(r)) NULL else r$route_display_label[1]
    ch <- if (is.null(a)) NULL else v6_24_champion(a$series)
    v6_24_hc_backtest(a, lbl, ch)
  })

  output$v24_vw_notes <- renderUI({
    a <- applied_cfg()
    if (is.null(a)) {
      return(tags$p(class = "v24-note",
                    "Configure the backtest above and click Analyze Backtest."))
    }
    b <- v6_24_backtest_rows(a$series, a$models, a$horizon)
    # P9E | Dates go through v6_24_as_date so this note states the same governed
    # day as the chart above it. as.character() on the raw POSIXct rendered the
    # timestamp in the server's local zone and shifted it back a day.
    bd <- v6_24_as_date(b$target_date)
    tags$p(class = "v24-note",
           sprintf(paste("%s prepared rows across %d model%s at horizon %s days,",
                         "%s to %s. Rows are filtered from",
                         "model_backtests_15_models; nothing is recomputed."),
                   format(nrow(b), big.mark = ","), length(a$models),
                   if (length(a$models) == 1) "" else "s", a$horizon,
                   if (nrow(b)) format(min(bd), "%Y-%m-%d") else "-",
                   if (nrow(b)) format(max(bd), "%Y-%m-%d") else "-"))
  })

  output$v24_vw_rank_note <- renderUI({
    r <- vw_series()
    if (is.null(r)) return(NULL)
    tags$span(paste0("Ranking policy ", V6_24_RANKING_POLICY,
                     ". Ranks and errors are read from model_rankings and ",
                     "accuracy_metrics; nothing is recalculated in Shiny."))
  })

  output$v24_vw_ranking <- DT::renderDataTable({
    r <- vw_series()
    if (is.null(r)) return(v6_24_dt(NULL))
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
    fam <- vapply(as.character(j$model_name), function(m) {
      k <- V6_24_DISPLAY_FAMILY[[m]]
      if (is.null(k)) "\u2014" else unname(V6_24_FAMILY_LABEL[[k]])
    }, character(1), USE.NAMES = FALSE)
    # escape = FALSE is set in v6_24_dt, so the champion cell may carry a badge.
    champ <- ifelse(
      j$is_series_champion == "TRUE",
      if (show_champ) v6_24_cell_badge("\u2605 champion", "gold")
      else v6_24_cell_badge("technical only", "slate"),
      "")
    out <- data.frame(
      Rank = as.integer(j$rank_within_series),
      Model = as.character(j$model_name),
      Family = fam,
      `Ranked by` = j$primary_rank_metric,
      `Rank value` = vapply(j$primary_rank_value,
                            function(x) v6_24_fmt_median(x, 6), character(1)),
      WAPE = ifelse(j$wape_status == "COMPUTED",
                    vapply(j$wape, function(x) v6_24_fmt_median(x, 6),
                           character(1)),
                    "not computable"),
      SMAPE = vapply(j$smape, function(x) v6_24_fmt_median(x, 6), character(1)),
      MAE = vapply(j$mae, function(x) v6_24_fmt_median(x, 6), character(1)),
      RMSE = vapply(j$rmse, function(x) v6_24_fmt_median(x, 6), character(1)),
      Champion = champ,
      check.names = FALSE, stringsAsFactors = FALSE)
    v6_24_dt(out, page_length = 15L, paging = FALSE, searching = FALSE)
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

  # P9E | The default is the champion ONLY when champion_visible is TRUE. When
  # it is FALSE the governance reference model leads instead and nothing is
  # labelled a winner - see v24_fc_champion_note below.
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

  output$v24_fc_champion_note <- renderUI({
    r <- fc_series()
    if (is.null(r)) return(NULL)
    m <- input$v24_fc_model
    ch <- v6_24_champion(r$series_id[1])
    if (isTRUE(ch$meaningful)) {
      if (!is.null(m) && identical(m, ch$model)) {
        tags$p(class = "v24-note v24-note-ok",
               sprintf(paste("Showing the champion for this series: %s,",
                             "ranked by %s. Other governed models remain",
                             "selectable for inspection."),
                       ch$model, ch$rank_metric))
      } else {
        tags$p(class = "v24-note",
               sprintf(paste("Inspecting %s. The champion for this series is",
                             "%s."), m, ch$model))
      }
    } else {
      tags$p(class = "v24-note v24-note-warn",
             paste("No model can be presented as a winner for this series:",
                   "every observed actual is zero, so the ranking is a",
                   "technical tie-break only. The forecast below is shown for",
                   "inspection and is not a recommendation."))
    }
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

  # P9E | Highcharter. Observed history in the reserved actual blue, then the
  # governed forward forecast in a distinct green, dashed, behind a labelled
  # "Forecast start" boundary - so actual and forecast are unmistakable on the
  # same time axis. Values are drawn exactly as the model produced them.
  output$v24_fc_chart <- highcharter::renderHighchart({
    r <- fc_series()
    m <- input$v24_fc_model
    if (is.null(r) || is.null(m) || !nzchar(m)) {
      return(v6_24_hc_empty("Complete the filter path to load a forecast."))
    }
    ch <- v6_24_champion(r$series_id[1])
    v6_24_hc_forecast(r$series_id[1], m, r$route_display_label[1],
                      meaningful = isTRUE(ch$meaningful) &&
                        identical(m, ch$model))
  })

  output$v24_fc_table <- DT::renderDataTable({
    f <- fc_rows()
    if (is.null(f)) return(v6_24_dt(NULL))
    flag <- function(x, tone, label) {
      ifelse(as.character(x) == "TRUE", v6_24_cell_badge(label, tone), "")
    }
    out <- data.frame(
      Step = as.integer(f$forecast_step),
      Date = format(v6_24_as_date(f$forecast_date), "%Y-%m-%d"),
      Model = as.character(f$model_name),
      `Predicted value` = vapply(f$predicted_value,
                                 function(x) v6_24_fmt_median(x, 6),
                                 character(1)),
      Negative = flag(f$negative_forecast_flag, "warn", "negative"),
      Extreme = flag(f$extreme_forecast_flag, "warn", "extreme"),
      check.names = FALSE, stringsAsFactors = FALSE)
    v6_24_dt(out, page_length = 10L, searching = FALSE)
  })

  # ------------------------------------------------------------ 4. Taxonomy
  output$v24_tx_scope_sel <- renderUI({
    tx <- d$tax_counts
    scopes <- unique(as.character(tx$count_scope))
    selectInput("v24_tx_scope", "Count scope", choices = scopes,
                selected = scopes[1], width = "420px")
  })

  output$v24_tx_table <- DT::renderDataTable({
    sc <- input$v24_tx_scope
    tx <- d$tax_counts
    if (is.null(sc)) return(v6_24_dt(NULL))
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
    v6_24_dt(out, page_length = 15L)
  })

  output$v24_tx_caveats <- DT::renderDataTable({
    n <- nav_all
    codes <- unlist(lapply(n$caveat_badge, v6_24_badges))
    if (!length(codes)) return(v6_24_dt(NULL))
    tb <- as.data.frame(table(codes), stringsAsFactors = FALSE)
    names(tb) <- c("Caveat", "Series")
    tb$Severity <- vapply(tb$Caveat, v6_24_caveat_severity, character(1))
    tb$Blocking <- "no"
    tb <- tb[order(-tb$Series), c("Caveat", "Severity", "Series", "Blocking")]
    v6_24_dt(tb, paging = FALSE, searching = FALSE)
  })

  output$v24_tx_filters <- DT::renderDataTable({
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
    v6_24_dt(out, page_length = 15L)
  })

  # ------------------------------------------------- P9G evidence assistant
  # One wiring function serves both panels. The evidence is rebuilt on every
  # request from the CURRENT selection and applied configuration, so a panel
  # can never answer about a series the user has moved away from.
  v24_wire_assistant <- function(prefix, prompts, fc_model_input = NULL) {
    id <- function(s) paste0("v24_", prefix, "_asst_", s)
    state <- reactiveValues(intent = NULL, question = "", stamp = NULL)

    for (p in prompts) {
      local({
        pp <- p
        observeEvent(input[[id(pp$id)]], {
          state$intent <- pp$intent
          state$question <- pp$label
          state$stamp <- format(Sys.time(), "%H:%M:%S")
        }, ignoreInit = TRUE)
      })
    }

    observeEvent(input[[id("generate")]], {
      q <- input[[id("question")]]
      state$question <- if (is.null(q)) "" else trimws(q)
      # Free text is routed by intent; an empty box falls back to a summary.
      state$intent <- if (nzchar(state$question))
        v6_24_assistant_intent(state$question) else "summary"
      state$stamp <- format(Sys.time(), "%H:%M:%S")
    }, ignoreInit = TRUE)

    output[[id("answer")]] <- renderUI({
      if (is.null(state$intent)) {
        return(tags$p(class = "v24-note",
                      paste("Pick a quick prompt or type a question. Answers",
                            "come only from the governed artifacts for the",
                            "series selected above.")))
      }
      r <- selected_series()
      sid <- if (is.null(r)) NULL else r$series_id[1]
      fm <- if (is.null(fc_model_input)) NULL else input[[fc_model_input]]
      e <- v6_24_evidence(sid, applied_cfg(), fm)
      a <- v6_24_assistant_answer(e, state$question, state$intent)

      tags$div(
        class = if (isTRUE(a$bounded)) "llm-panel v24-asst v24-asst-bounded"
                else "llm-panel v24-asst",
        tags$p(class = "v24-asst-q",
               tags$strong("Question: "), state$question),
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
          tags$span(class = "v24-asst-caveat",
                    paste0("Caveats: ", a$caveats))
        ),
        tags$p(class = "v24-asst-stamp",
               paste0("Composed locally at ", state$stamp, " \u00b7 ",
                      V6_24_ASSISTANT_ENGINE, " \u00b7 intent: ", a$intent))
      )
    })
    outputOptions(output, id("answer"), suspendWhenHidden = FALSE)
  }

  v24_wire_assistant("vw", V6_24_VIEWER_PROMPTS)
  v24_wire_assistant("fc", V6_24_FORECAST_PROMPTS, "v24_fc_model")

  # P9H | The Accuracy assistant answers about the ANALYZED accuracy rows, not
  # about one series, so it uses its own evidence builder and composer. Same
  # deterministic local engine, same refusal behaviour.
  local({
    id <- function(s) paste0("v24_acc_asst_", s)
    st <- reactiveValues(intent = NULL, question = "", stamp = NULL)
    for (p in V6_24_ACCURACY_PROMPTS) {
      local({
        pp <- p
        observeEvent(input[[id(pp$id)]], {
          st$intent <- pp$intent
          st$question <- pp$label
          st$stamp <- format(Sys.time(), "%H:%M:%S")
        }, ignoreInit = TRUE)
      })
    }
    observeEvent(input[[id("generate")]], {
      q <- input[[id("question")]]
      st$question <- if (is.null(q)) "" else trimws(q)
      st$intent <- if (nzchar(st$question))
        v6_24_accuracy_intent(st$question) else "acc_summary"
      st$stamp <- format(Sys.time(), "%H:%M:%S")
    }, ignoreInit = TRUE)

    output[[id("answer")]] <- renderUI({
      if (is.null(st$intent)) {
        return(tags$p(class = "v24-note",
                      paste("Run Analyze Accuracy, then pick a quick prompt or",
                            "type a question. Answers come only from the rows",
                            "that were analyzed.")))
      }
      e <- v6_24_accuracy_evidence(applied_acc(), acc_rows())
      a <- v6_24_accuracy_answer(e, st$question, st$intent)
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

  # ------------------------------------------------------- 4. Accuracy (P9H)
  # Scoped to the series selected in the Viewer - the same shared selection that
  # drives Forecast. There is no cohort-wide Top-N view: this page answers "how
  # did the 15 governed models do on THIS series".
  #
  # Pending vs applied, matching the P9D backtest pattern: the controls stage a
  # request, Analyze Accuracy commits it, and every result reads the committed
  # request only.
  acc <- reactiveValues(metric = "MAE", models = V6_24_GOVERNED_MODELS,
                        applied = NULL)

  output$v24_acc_window <- renderUI({
    # The horizon is DISCLOSED, not selectable. accuracy_metrics holds one row
    # per series x model covering horizons 1-30, so a horizon filter would
    # return six identical result sets. The legacy options are shown struck
    # through, the pattern P9D used for the unavailable 35/45 backtest horizons.
    tagList(
      tags$div(class = "v24-acc-window-banner",
               tags$strong("Governed aggregate over horizons 1-30"),
               tags$p(V6_24_ACC_WINDOW_NOTE)),
      tags$div(
        class = "v24-acc-hz-row",
        tags$span(class = "v24-acc-hz-label", "Legacy per-horizon options:"),
        lapply(V6_24_ACC_LEGACY_HORIZONS, function(h)
          tags$span(class = "v24-acc-hz-off", paste0(h, " days")))
      )
    )
  })

  output$v24_acc_metric_ui <- renderUI({
    selectInput("v24_acc_metric", NULL, choices = V6_24_ACC_METRIC_LABELS,
                selected = acc$metric, width = "320px")
  })

  output$v24_acc_models_ui <- renderUI({
    groups <- lapply(V6_24_FAMILY_ORDER, function(f) {
      ms <- names(V6_24_DISPLAY_FAMILY)[V6_24_DISPLAY_FAMILY == f]
      tags$div(
        class = "v24-bt-family",
        tags$div(class = "v24-bt-family-head", V6_24_FAMILY_LABEL[[f]]),
        checkboxGroupInput(paste0("v24_acc_fam_", f), NULL,
                           choices = ms, selected = ms[ms %in% acc$models])
      )
    })
    tagList(
      tags$div(class = "v24-bt-families", groups),
      tags$p(class = "v24-field-hint",
             "All 15 governed models are selected by default. No other model exists in the artifact.")
    )
  })

  acc_pending_models <- reactive({
    ms <- unlist(lapply(V6_24_FAMILY_ORDER,
                        function(f) input[[paste0("v24_acc_fam_", f)]]))
    ms <- ms[!is.na(ms) & nzchar(ms)]
    V6_24_GOVERNED_MODELS[V6_24_GOVERNED_MODELS %in% ms]
  })

  observeEvent(input$v24_acc_go, {
    r <- selected_series()
    if (is.null(r)) return(NULL)          # nothing to analyze without a series
    ms <- acc_pending_models()
    if (!length(ms)) ms <- V6_24_GOVERNED_MODELS
    acc$metric <- if (is.null(input$v24_acc_metric)) "MAE" else input$v24_acc_metric
    acc$models <- ms
    acc$applied <- list(
      metric = acc$metric, models = ms,
      series_id = as.character(r$series_id[1]),
      label = as.character(r$route_display_label[1]),
      stamp = format(Sys.time(), "%H:%M:%S"))
  }, ignoreInit = TRUE)

  observeEvent(input$v24_acc_reset, {
    acc$metric <- "MAE"; acc$models <- V6_24_GOVERNED_MODELS
    acc$applied <- NULL
  }, ignoreInit = TRUE)

  # Changing the selected series invalidates a previous analysis, so the page
  # cannot show accuracy for a series the user has navigated away from.
  observeEvent(selected_series(), { acc$applied <- NULL }, ignoreInit = TRUE)

  applied_acc <- reactive(acc$applied)

  acc_rows <- reactive({
    a <- applied_acc()
    if (is.null(a)) return(NULL)
    v6_24_acc_rows(a$metric, a$models, a$series_id)
  })

  output$v24_acc_applied <- renderUI({
    a <- applied_acc()
    if (is.null(a)) {
      r <- selected_series()
      return(tags$span(
        class = "v24-note",
        if (is.null(r)) "Select a series in the Viewer first."
        else "Nothing analysed yet."))
    }
    tags$span(class = "v24-note v24-note-ok",
              sprintf("Analysed: %s over %d model%s \u00b7 %s \u00b7 %s",
                      a$metric, length(a$models),
                      if (length(a$models) == 1) "" else "s",
                      a$label, a$stamp))
  })

  output$v24_acc_cards <- renderUI({
    a <- applied_acc()
    cell <- function(label, value, cls = "") {
      tags$div(class = paste("v24-acc-card", cls),
               tags$div(class = "v24-acc-card-label", label),
               tags$div(class = "v24-acc-card-value", value))
    }
    if (is.null(a)) {
      return(tags$div(
        class = "v24-acc-grid",
        cell("Models compared", "\u2014"), cell("Accuracy window", "\u2014"),
        cell("Selected metric", "\u2014"), cell("Target dates", "\u2014"),
        cell("Best model", "Click Analyze Accuracy", "v24-acc-wide"),
        cell("Weakest model", "Click Analyze Accuracy", "v24-acc-wide")))
    }
    s <- v6_24_acc_summary(acc_rows(), a$metric)
    best_cls <- if (isTRUE(s$no_signal)) "v24-acc-wide" else "v24-acc-wide v24-acc-good"
    worst_cls <- if (isTRUE(s$no_signal)) "v24-acc-wide" else "v24-acc-wide v24-acc-bad"
    tags$div(
      class = "v24-acc-grid",
      cell("Models compared", s$n_models),
      cell("Accuracy window", "horizons 1-30"),
      cell("Selected metric", s$metric),
      cell("Target dates evaluated",
           if (is.na(s$target_dates)) "\u2014" else s$target_dates),
      cell("Best model",
           if (isTRUE(s$no_signal)) s$best
           else tagList(tags$span(s$best), tags$span(class = "v24-acc-sub",
                paste0(a$metric, " ", v6_24_acc_fmt(s$best_value)))),
           best_cls),
      cell("Weakest model",
           if (isTRUE(s$no_signal)) s$worst
           else tagList(tags$span(s$worst), tags$span(class = "v24-acc-sub",
                paste0(a$metric, " ", v6_24_acc_fmt(s$worst_value)))),
           worst_cls),
      if (isTRUE(s$no_signal))
        cell("Why no best model",
             paste("Every observed actual for this series is zero, so an error",
                   "of zero means the model predicted zero against zero. That",
                   "is a degenerate identity, not performance, and no model is",
                   "presented as best."),
             "v24-acc-wide"),
      if (s$excluded > 0 || s$extreme > 0)
        cell("Set aside",
             paste0(s$excluded, " model row(s) with no computable ", a$metric,
                    " \u00b7 ", s$extreme, " extreme value(s) flagged"),
             "v24-acc-wide")
    )
  })

  output$v24_acc_heatmap <- highcharter::renderHighchart({
    a <- applied_acc()
    if (is.null(a)) {
      r <- selected_series()
      return(v6_24_hc_empty(
        if (is.null(r)) "Select a series in the Viewer to see its accuracy."
        else "Choose a metric and models, then click Analyze Accuracy."))
    }
    v6_24_acc_heatmap(acc_rows(), a$metric)
  })

  output$v24_acc_table <- DT::renderDataTable({
    a <- applied_acc()
    if (is.null(a)) return(v6_24_dt(NULL))
    v6_24_acc_table(acc_rows(), a$metric)
  })

  # ------------------------------------------------------------ visibility
  # These pages live in plain <section data-section> divs that custom.js shows
  # and hides with CSS. Shiny suspends outputs inside hidden elements by
  # default, so without this every card, table and chart stays blank until the
  # output happens to be visible at render time - which, for a section that
  # starts hidden, is never. Un-suspend them explicitly.
  v24_outputs <- c(
    "v24_ov_cards", "v24_ov_by_metric", "v24_ov_by_signal", "v24_ov_loader",
    "v24_sel_controls", "v24_sel_breadcrumb", "v24_sel_state", "v24_sel_cards",
    "v24_shared_selection", "v24_acc_shared_selection",
    "v24_vw_identity", "v24_vw_champion", "v24_vw_model_sel",
    "v24_vw_actuals", "v24_vw_backtest", "v24_vw_rank_note", "v24_vw_ranking",
    "v24_vw_notes",
    "v24_bt_availability", "v24_bt_horizon_ui", "v24_bt_model_count",
    "v24_bt_model_groups", "v24_bt_champion_note", "v24_bt_analyze_btn",
    "v24_bt_applied",
    "v24_fc_identity", "v24_fc_model_sel", "v24_fc_champion_note",
    "v24_fc_chart", "v24_fc_table",
    "v24_acc_window", "v24_acc_metric_ui", "v24_acc_models_ui",
    "v24_acc_applied", "v24_acc_cards", "v24_acc_heatmap", "v24_acc_table",
    "v24_tx_scope_sel", "v24_tx_table", "v24_tx_caveats", "v24_tx_filters"
  )
  for (o in v24_outputs) {
    try(outputOptions(output, o, suspendWhenHidden = FALSE), silent = TRUE)
  }

  # P9M | Expose the shared selection so Models FULL > Champion can reuse the
  # very same series the Viewer, Accuracy and Forecast pages are showing.
  # Purely additive: the return value was invisible(NULL) and nothing on any
  # page reads it, so no behaviour changes here.
  invisible(list(selected_series = selected_series))
}



