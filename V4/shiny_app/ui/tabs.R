# TESSERACT v2 | tabs.R | populated dashboard sections (Block 7.0C)
# Content structure appropriated from MassiveForecasting-V3/body.R (tabItems),
# rebuilt as plain Shiny section panels. All interactive controls are
# read-only previews: no server handlers, no model/forecast/metric recompute.

# ---------------------------------------------------------------------------
# Small UI helpers
# ---------------------------------------------------------------------------
section_head <- function(title, subtitle) {
  tags$div(
    class = "section-head",
    tags$h1(class = "section-title", title),
    tags$p(class = "section-subtitle", subtitle)
  )
}

shell_card <- function(label, title, detail, label_class = "shell-card-tag") {
  tags$div(
    class = "shell-card",
    tags$span(class = label_class, label),
    tags$h3(class = "shell-card-title", title),
    tags$p(class = "shell-card-detail", detail)
  )
}

kpi_card <- function(value, label, pill = NULL, pill_class = "pill-blue") {
  tags$div(
    class = "shell-card",
    if (!is.null(pill)) tags$span(class = paste("pill", pill_class), pill),
    tags$div(class = "kpi-value", value),
    tags$div(class = "kpi-label", label)
  )
}

info_row <- function(key, val) {
  tags$li(tags$span(class = "info-key", key), tags$span(class = "info-val", val))
}

info_list <- function(...) tags$ul(class = "info-list", ...)

card_grid <- function(...) tags$div(class = "shell-card-grid", ...)

panel <- function(value, ..., active = FALSE) {
  tags$section(
    class = paste("content-section", if (active) "is-active" else ""),
    `data-section` = value,
    ...
  )
}

# Read-only "controls preview" block (appropriates the forecast controls of
# MassiveForecasting-V3: horizon slider, model selector, action buttons).
controls_preview <- function() {
  tags$div(
    class = "preview-controls",
    tags$div(
      class = "preview-controls-head",
      tess_icon("sliders"),
      tags$span("Controls preview"),
      tags$span(class = "preview-tag", "read-only")
    ),
    tags$div(
      class = "preview-row",
      tags$label("Horizon (months)"),
      tags$input(type = "range", min = "1", max = "18", value = "12",
                 class = "preview-range", disabled = NA)
    ),
    tags$div(
      class = "preview-row",
      tags$label("Model family"),
      tags$select(
        class = "preview-select", disabled = NA,
        tags$option("ETS (governed champion)"),
        tags$option("ARIMA family"),
        tags$option("Seasonal naive"),
        tags$option("TSLM")
      )
    ),
    tags$div(
      class = "preview-actions",
      tags$button(class = "preview-btn preview-btn-primary", type = "button", disabled = NA, "Preview"),
      tags$button(class = "preview-btn", type = "button", disabled = NA, "Reset")
    ),
    tags$p(class = "preview-note",
           "Interactive controls are intentionally disabled in this read-only shell.")
  )
}

# Planned (not-yet-bound) placeholder block, used for sections whose governed
# artifact does not exist yet (TTL / Downloads).
planned_card <- function(title, detail) {
  tags$div(
    class = "shell-card",
    tags$span(class = "pill pill-amber", "Planned"),
    tags$h3(class = "shell-card-title", title),
    tags$p(class = "shell-card-detail", detail)
  )
}

# ---------------------------------------------------------------------------
# Sections (PROJECT / FORECASTING / MODELS / GOVERNANCE / REFERENCE)
# ---------------------------------------------------------------------------

# A single numbered step in the Home methodology flow (kept small + minimal).
home_step <- function(num, title, detail) {
  tags$div(
    class = "home-step",
    tags$span(class = "home-step-num", num),
    tags$div(
      class = "home-step-body",
      tags$h4(class = "home-step-title", title),
      tags$p(class = "home-step-detail", detail)
    )
  )
}

# A collapsible (+/-) section: shows a title + one-line summary, expands on
# click to reveal `...` content. Pure client-side toggle (see custom.js).
home_collapse <- function(title, summary, ..., open = FALSE) {
  tags$div(
    class = paste("home-collapse", if (open) "is-open" else ""),
    tags$button(
      class = "home-collapse-head", type = "button",
      tags$div(
        class = "home-collapse-heading",
        tags$span(class = "home-collapse-title", title),
        tags$span(class = "home-collapse-summary", summary)
      ),
      tags$span(class = "home-collapse-icon", `aria-hidden` = "true")
    ),
    tags$div(class = "home-collapse-body", ...)
  )
}

section_home <- function() {
  panel(
    "home", active = TRUE,

    # A. Hero ----------------------------------------------------------------
    section_head(
      "AEGIS Forecast Improvement Platform",
      "A dashboard for reviewing a broader, evidence-based way of generating forecasts."
    ),

    # B. Why this dashboard exists (collapsible) -----------------------------
    home_collapse(
      "Why this dashboard exists",
      "Why we are moving beyond a few fixed models to an evidence-based comparison.",
      tags$div(
        class = "home-prose",
        tags$p(
          "The current forecasting process relies on a small set of basic forecasting models, ",
          "chosen mostly one by one. This dashboard explores a broader, evidence-based ",
          "way of generating forecasts: instead of trusting a few fixed models, it compares ",
          "a wider universe of candidates and lets the data decide which approach forecasts ",
          "most accurately."
        ),
        tags$p(
          "The methodology goes beyond the current baseline by evaluating statistical models, ",
          "machine learning models, and a deep learning candidate side by side \u2014 under the ",
          "same rules, on the same history, and with the same accuracy metrics."
        )
      )
    ),

    # C. How the methodology works (collapsible) -----------------------------
    home_collapse(
      "How the methodology works",
      "The 5 steps from historical data to a governed model recommendation.",
      tags$div(
        class = "home-flow",
        home_step("1", "Historical data",
                  "Start from historical demand and forecast data for each series."),
        home_step("2", "Baseline & challenger models",
                  "Run the current baseline models alongside statistical, machine learning, and deep learning challengers."),
        home_step("3", "Rolling evaluation windows",
                  "Test every model empirically across expanding / rolling time windows, so results reflect many repeated forecasting situations \u2014 not a single lucky split."),
        home_step("4", "Forecast accuracy metrics",
                  "Score each model with governed accuracy metrics: MASE as the primary measure and RMSSE as a guardrail, supported by diagnostics such as wMAPE, SMAPE, and bias where applicable."),
        home_step("5", "Model tournament",
                  "Combine those scores into a model tournament that ranks the candidates and supports a governed recommendation.")
      )
    ),

    # D. Model families compared (collapsible) -------------------------------
    home_collapse(
      "Model families compared",
      "Baseline, statistical, machine learning and deep learning candidates.",
      info_list(
        info_row("Baseline / reference", "The current forecasting approaches, kept as the comparison point."),
        info_row("Statistical models", "Classical time-series methods (for example ARIMA, ETS, and Theta-style models)."),
        info_row("Machine learning models", "Feature-based learners such as gradient boosting and regression approaches."),
        info_row("Deep learning candidate", "A neural forecasting candidate included to test more complex patterns.")
      ),
      tags$p(class = "shell-card-detail", style = "margin-top:10px;",
             "The full, detailed model list lives in MODELS / Universe.")
    ),

    # E. Where to go next (collapsible) --------------------------------------
    home_collapse(
      "Where to go next",
      "Quick links to the Overview, Universe, Tournament, Champion and Risks pages.",
      info_list(
        info_row("PROJECT / Overview", "Macro summary of the most important results."),
        info_row("MODELS / Universe", "The complete set of models considered in the review."),
        info_row("MODELS / Tournament", "Ranked, head-to-head tournament evidence."),
        info_row("MODELS / Champion", "The governed model recommendation and its conditions."),
        info_row("GOVERNANCE / Risks", "Open risks and models that were deferred."),
        info_row("FORECASTING / Explorer", "Visual forecast exploration.")
      )
    )
  )
}

section_overview <- function() {
  # Read-only governed reads (7.0E loader). Never recompute; safe fallbacks.
  cs <- home_champion_summary()
  kr <- home_key_results()
  au <- home_audit6_summary()

  champ      <- first_label(cs_value(cs, "selected_champion_model"), APP_CHAMPION)
  origin     <- cs_value(cs, "model_origin", "challenger")
  family     <- cs_value(cs, "model_family", "statistical")
  confidence <- first_label(cs_value(cs, "decision_confidence"), APP_CHAMPION_CONFIDENCE)
  mase       <- fmt_metric(cs_value(cs, "official_median_mase"), 2)
  rmsse      <- fmt_metric(cs_value(cs, "official_median_rmsse"), 2)
  better     <- first_label(cs_value(cs, "supported_better_count"))
  worse      <- first_label(cs_value(cs, "supported_worse_count"))
  pairwise   <- first_label(kr_value(kr, "tournament_pairwise_comparisons"))
  conditions <- cs_value(cs, "conditions",
                         "Conditions are retained in the governed closure pack.")

  # Audit #6 governance summary (governed artifact, not hardcoded).
  verdict    <- cs_value(au, "overall_verdict", "APPROVE_WITH_CONDITIONS_TO_SHINY_MVP")
  blockers   <- first_label(cs_value(au, "blocker_count"), "0")
  advisories <- first_label(cs_value(au, "advisory_count"))
  ready      <- cs_value(au, "ready_for_shiny_mvp", "True")
  approved   <- if (grepl("APPROVE", toupper(verdict))) "Approved with conditions" else verdict

  ni <- function(x) if (length(x) != 1 || is.na(x)) "\u2014" else as.character(x)

  panel(
    "overview",

    # A. Header --------------------------------------------------------------
    section_head(
      "Executive Overview",
      "A read-only macro summary of the AEGIS forecast improvement review."
    ),

    # B. Intro ---------------------------------------------------------------
    tags$div(
      class = "home-prose",
      tags$p(
        "Everything below is read directly from the governed closure pack and ",
        "audit trail. Nothing here is recalculated, and no forecasts or models ",
        "are run by the dashboard. Expand each section for the most relevant ",
        "evidence."
      )
    ),

    # 1) Models \u2014 governed champion --------------------------------------
    home_collapse(
      "Models \u2014 governed champion",
      "Which model was selected, under what conditions, and the evidence behind it.",
      tags$div(
        class = "home-prose",
        tags$p(
          tags$strong(champ), " was selected as the governed champion ",
          tags$strong("with conditions"), " \u2014 not as an unconditional ",
          "winner. The selection is supported by consistent accuracy metrics ",
          "and head-to-head evidence across the model universe."
        )
      ),
      info_list(
        info_row("Champion model", paste0(champ, " (", origin, " \u00b7 ", family, ")")),
        info_row("Selection status", "Selected with conditions"),
        info_row("Decision confidence", confidence),
        info_row("Median MASE (primary)", paste0(mase, " \u00b7 lower is stronger")),
        info_row("Median RMSSE (guardrail)", paste0(rmsse, " \u00b7 stability check")),
        info_row("Pairwise evidence",
                 paste0(ni(better), " better \u00b7 ", ni(worse),
                        " worse \u00b7 across ", ni(pairwise), " comparisons"))
      )
    ),

    # 2) Forecast \u2014 structural evidence coverage -------------------------
    home_collapse(
      "Forecast \u2014 evidence base",
      "The data the review was scored on, described as coverage \u2014 not a new performance metric.",
      tags$div(
        class = "home-prose",
        tags$p(
          "The review compared models on a broad, complete historical backtest. ",
          "The governed tournament evidence base covers ", tags$strong("39 series"), " across ",
          tags$strong("13 governed tournament models"), ", at ", tags$strong("horizons 1\u201330"),
          ", with complete actual and forecast values \u2014 no gaps."
        ),
        tags$p(
          "This is the shared, like-for-like basis the tournament used to score ",
          "every model. It is shown here as evidence coverage, not as a ",
          "forecast-accuracy improvement."
        )
      ),
      info_list(
        info_row("Series covered", "39"),
        info_row("Models compared", "13"),
        info_row("Forecast horizons", "1\u201330"),
        info_row("Actuals / forecasts", "Complete \u00b7 no missing values")
      )
    ),

    # 3) Governance ----------------------------------------------------------
    home_collapse(
      "Governance",
      "The audited approval state for handing this dashboard off \u2014 with its conditions.",
      tags$div(
        class = "home-prose",
        tags$p(
          tags$strong("Approved with conditions for dashboard handoff."), " ",
          "Audit #6 cleared this dashboard for handoff with no blockers, under ",
          "explicit conditions: it must stay read-only, must not recompute ",
          "metrics or rerun models, and must keep risks and caveats visible. ",
          "This is a dashboard-handoff approval, not a production sign-off."
        ),
        tags$p(conditions)
      ),
      info_list(
        info_row("Audit #6 verdict", approved),
        info_row("Blockers", ni(blockers)),
        info_row("Advisories", ni(advisories)),
        info_row("Ready for handoff", ni(ready)),
        info_row("Dashboard contract", "Read-only \u00b7 no recompute")
      )
    )
  )
}

section_explorer <- function() {
  # Stage 07 Forecast Viewer Exploratory Layout Cleanup: the Viewer page hosts the
  # historical Backtest Comparison ONLY (forward production forecast lives on the
  # separate Forecast page, section_forecast()).
  #   Source: data/processed/forecast_viewer_model_outputs.csv (39 series).
  # The layout is horizontal/compact: a single setup card (series + horizon +
  # history + Analyze on one row, model family cards wrapped below) over a
  # full-width chart and data notes. The chart lives in a STATIC container
  # (always in the DOM) to avoid blank-chart regressions, and never renders
  # before the user clicks Analyze Backtest.

  # ---- Backtest section inputs ----
  bt_series      <- fvp_series_choices()                 # 39 eligible series
  bt_default     <- if (length(bt_series)) bt_series[[1]] else NULL
  horizon_opts   <- fvp_horizon_choices()                # 5..30
  horizon_named  <- stats::setNames(as.character(horizon_opts),
                                    paste0(horizon_opts, " days"))
  horizon_unavail <- fvp_horizon_unavailable()           # 35, 45 (disabled)

  panel(
    "explorer",
    section_head(
      "Forecast Viewer",
      "Exploratory historical backtest view. Select a key/series, models and horizon to visually compare historical model behavior against known actuals. This page does not generate future forecasts."
    ),

    # ---- How to use this viewer (collapsed by default) ---------------------
    home_collapse(
      "How to use this viewer",
      "An exploratory sandbox to compare historical model fit against known actuals.",
      tags$ul(
        class = "fvb-how-list",
        tags$li("This is an ", tags$b("exploratory"), " backtest viewer."),
        tags$li("The ", tags$b("actual"), " values are already known \u2014 they are real history."),
        tags$li("Each model line is a ", tags$b("historical backtest forecast"), ", not a future forecast."),
        tags$li("Use it to visually compare how well each model fits a series at a chosen horizon, and to corroborate the governed results yourself."),
        tags$li("The ", tags$b("Deep Learning"), " family shows the three final deep-learning challengers selected during the codebase review (V3.2D/V3.2E) as historical backtest lines \u2014 they are ", tags$b("not"), " production forecasts and do ", tags$b("not"), " change the champion."),
        tags$li("It does ", tags$b("not"), " generate future forecasts, recalculate metrics, or change the champion."),
        tags$li("The forward production forecast lives on the separate ", tags$b("Forecast"), " page.")
      ),
      open = FALSE
    ),

    # =====================================================================
    # BOX 1 \u2014 SET UP THE BACKTEST VIEW (controls only, numbered steps).
    # Analyze Backtest is the LAST step, at the bottom of this box.
    # =====================================================================
    tags$section(
      class = "fvx-section fvx-backtest fvb fvb-setup-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "Backtest"),
        tags$h3(class = "fvx-section-title", "Set up the backtest view"),
        tags$span(class = "pill pill-blue", "Historical \u00b7 multi-model")
      ),
      tags$p(
        class = "fvb-setup-lead",
        "Choose what to compare, then run step 5. ",
        "Source: ", tags$code("forecast_viewer_model_outputs.csv"), "."
      ),

      # Steps 1-3: series / horizon / history -----------------------------
      tags$div(
        class = "fvb-controls",
        tags$div(
          class = "fvb-field fvb-field-series",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "1"), "Select key / series"),
          selectInput("fvp_series", NULL, choices = bt_series,
                      selected = bt_default, width = "100%"),
          tags$p(class = "fvb-field-hint",
                 "One of the 39 eligible multi-model keys/series.")
        ),
        tags$div(
          class = "fvb-field fvb-field-horizon",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "2"), "Horizon"),
          radioButtons("fvp_horizon", NULL, choices = horizon_named,
                       selected = "5", inline = TRUE),
          tags$div(
            class = "fvb-horizon-unavail",
            lapply(horizon_unavail, function(h)
              tags$span(class = "fv-horizon-chip is-disabled",
                        title = "Not available in current artifact",
                        paste0(h, " days"))),
            tags$span(class = "fvb-field-hint",
                      "Artifact covers 5\u201330-day horizons.")
          )
        ),
        tags$div(
          class = "fvb-field fvb-field-history",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "3"), "History window"),
          selectInput("fvp_history", NULL,
                      choices = c("Last 90 days" = 90, "Last 180 days" = 180,
                                  "Full available window" = 0),
                      selected = 0, width = "100%"),
          tags$p(class = "fvb-field-hint",
                 "How much of the date range to show.")
        )
      ),

      # Step 4: model family cards (wrapped horizontally) -----------------
      tags$div(
        class = "fvb-models",
        tags$div(
          class = "fvb-models-head",
          tags$span(class = "fvb-field-label",
                    tags$span(class = "fvb-step-num", "4"), "Models"),
          uiOutput("fvp_model_count", inline = TRUE)
        ),
        uiOutput("fvp_model_groups"),
        tags$p(class = "fvb-field-hint",
               "Tick one or more models. Grouped by family; \u2605 marks the governed champion.")
      ),

      # Step 5: Analyze Backtest (bottom of the setup box) ----------------
      tags$div(
        class = "fvb-analyze-row",
        tags$div(
          class = "fvb-analyze-label",
          tags$span(class = "fvb-step-num", "5"),
          tags$span(class = "fvb-field-label", "Analyze Backtest")
        ),
        actionButton("fvp_go", "Analyze Backtest",
                     class = "fv-analyze-btn fvb-analyze-btn"),
        tags$p(class = "fvb-field-hint fvb-analyze-hint",
               "Renders the chart and data notes below. Updates only on click \u2014 no auto-refresh.")
      )
    ),

    # =====================================================================
    # BOX 2 \u2014 BACKTEST COMPARISON (results only: chart + data notes).
    # Separate, collapsible box. Action-gated: empty state until Analyze.
    # =====================================================================
    home_collapse(
      "Backtest Comparison",
      "Chart and data notes for the analyzed setup. Renders after Analyze Backtest.",
      tags$div(
        class = "fvb-result",
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvb-field-label", "Backtest chart")
        ),
        tags$div(
          class = "fv-chart-wrap fvb-chart-wrap",
          highcharter::highchartOutput("fvp_chart", height = "600px")
        ),
        tags$div(
          class = "fvb-result-head fvb-notes-head",
          tags$span(class = "fvb-field-label", "Data notes")
        ),
        uiOutput("fvp_notes"),
        tags$div(
          class = "fv-warn-card",
          tags$ul(
            class = "fv-warn-list",
            tags$li(tags$span(class = "pill pill-amber", "Backtest"),
                    "This section uses historical backtest comparison data. Actual values are already known. This is for comparing model behavior, not future production forecast."),
            tags$li(tags$span(class = "pill pill-slate", "No intervals"),
                    "Prediction intervals are not available in this artifact, so only point forecasts are drawn.")
          )
        )
      ),
      open = TRUE
    ),

    # Methodology note -------------------------------------------------------
    tags$p(
      class = "fv-method-note",
      "This page visualizes the governed backtest artifact only. It does not generate forecasts, recalculate metrics, rerun tournaments, or change any champion decision. The forward production forecast is shown on the separate Forecast page."
    )
  )
}

section_forecast <- function() {
  # Stage 07 Forecasting Sidebar Correction: dedicated Forecast page hosts the
  # single-model Forward Forecast ONLY (moved out of the Viewer page).
  #   Sources: data/processed/actuals.csv (history) +
  #            data/processed/forecasts.csv (production), 45 series.
  # Action-gated: the chart lives in a STATIC container and renders only after
  # the user clicks Analyze Forward Forecast.

  fw_series <- fvf_series_choices()                      # 45 series

  panel(
    "forecast",
    section_head(
      "Forecast",
      "Single-model forward forecast. Select a key / series and forecast window to view actual history followed by the forward production forecast."
    ),

    # B. How to use this forecast view (collapsed by default) --------------
    home_collapse(
      "How to use this forecast view",
      "A simple guide to the forward production forecast shown on this page.",
      tags$ul(
        class = "fvb-how-list",
        tags$li("This page shows the ", tags$b("forward production forecast"), " for one ", tags$b("key / series"), " at a time."),
        tags$li("The ", tags$b("solid line"), " is actual history up to the last actual date."),
        tags$li("The ", tags$b("dashed line"), " is the future forecast read from the governed calibrated forecast artifact (", tags$code("forecasts_with_intervals_relative_60d_calibrated.csv"), ", with a point-only fallback to ", tags$code("forecasts.csv"), ")."),
        tags$li("The ", tags$b("vertical boundary"), " marks the forecast start (the last actual date)."),
        tags$li("Each key / series has ", tags$b("one selected production model / version"), "."),
        tags$li("This page does ", tags$b("not"), " compare multiple models \u2014 historical multi-model backtest comparison lives in ", tags$b("Viewer"), ".")
      ),
      open = FALSE
    ),

    # =====================================================================
    # BOX 1 \u2014 SET UP THE FORECAST VIEW (controls only, numbered steps).
    # Comes FIRST: configure here, then the chart + data notes fill in below.
    # Analyze Forward Forecast is the LAST step, at the bottom of this box.
    # =====================================================================
    tags$section(
      class = "fvx-section fvx-forward fvb fvb-setup-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "Forward"),
        tags$h3(class = "fvx-section-title", "Set up the forecast view"),
        tags$span(class = "pill pill-teal", "Future \u00b7 single-model")
      ),
      tags$p(
        class = "fvb-setup-lead",
        "Choose a key / series, a forecast window and an actual-history window, then run step 4. ",
        "Sources: ", tags$code("actuals.csv"), " + ", tags$code("forecasts.csv"),
        " (45 series, one selected model per series)."
      ),
      tags$p(
        class = "fvb-setup-note",
        "Prediction intervals are backtest-calibrated from relative residuals and shown at the 80% level for operational clarity. The calibrated interval artifact currently supports forecast days 1\u201360. For longer windows, the forecast continues as a point estimate after day 60. Shiny only visualizes interval columns from the governed artifact."
      ),

      # Steps 1, 2, 3 --------------------------------------------------
      tags$div(
        class = "fvb-controls",
        tags$div(
          class = "fvb-field fvb-field-series",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "1"), "Select key / series"),
          selectInput("fvf_series", NULL, choices = fw_series,
                      selected = if (length(fw_series)) fw_series[[1]] else NULL,
                      width = "100%"),
          tags$p(class = "fvb-field-hint",
                 "Choose one of the 45 production keys / series.")
        ),
        tags$div(
          class = "fvb-field fvb-field-history",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "2"), "Forecast window"),
          selectInput("fvf_window", NULL,
                      choices = c("Next 30 days" = 30, "Next 60 days" = 60,
                                  "Next 180 days" = 180),
                      selected = 30, width = "100%"),
          tags$p(class = "fvb-field-hint",
                 "How far into the future to draw the forward forecast line.")
        ),
        tags$div(
          class = "fvb-field fvb-field-history",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "3"), "Actual history shown before forecast"),
          selectInput("fvf_history", NULL,
                      choices = c("Last 90 days" = 90,
                                  "Last 180 days" = 180,
                                  "Last 365 days" = 365),
                      selected = 180, width = "100%"),
          tags$p(class = "fvb-field-hint",
                 "How much observed history to show before the forecast start boundary.")
        )
      ),

      # Step 4 \u2014 Analyze Forward Forecast (bottom of the setup box) --------
      tags$div(
        class = "fvb-analyze-row",
        tags$div(
          class = "fvb-analyze-label",
          tags$span(class = "fvb-step-num", "4"),
          tags$span(class = "fvb-field-label", "Analyze Forward Forecast")
        ),
        actionButton("fvf_go", "Analyze Forward Forecast",
                     class = "fv-analyze-btn fvb-analyze-btn"),
        tags$p(class = "fvb-field-hint fvb-analyze-hint",
               "Renders the forecast chart and data notes below. Click again any time you change the key / series, forecast window or history window to refresh. Changing selectors alone does not auto-refresh.")
      ),

      # Production model / version note (compact, below the controls).
      uiOutput("fvf_model_note")
    ),

    # =====================================================================
    # BOX 2 \u2014 FORECAST CHART (results: chart + data notes).
    # Separate, collapsible box. Action-gated: empty state until Analyze.
    # =====================================================================
    home_collapse(
      "Forecast Chart",
      "Actual history, the forward production forecast and the forecast start boundary for the selected key / series.",
      tags$div(
        class = "fvb-result",
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvb-field-label", "Forecast chart")
        ),
        tags$div(
          class = "fv-chart-wrap fvb-chart-wrap",
          highcharter::highchartOutput("fvf_chart", height = "560px")
        ),
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvb-field-label", "Data notes")
        ),
        uiOutput("fvf_notes"),
        tags$div(
          class = "fv-warn-card fv-warn-card-fwd",
          tags$ul(
            class = "fv-warn-list",
            tags$li(tags$span(class = "pill pill-teal", "Forward"),
                    "This page uses the forward production forecast artifact. It is a single selected forecast per key / series, not a multi-model comparison."),
            tags$li(tags$span(class = "pill pill-slate", "Boundary"),
                    "The vertical \u201cForecast start\u201d line marks the last actual date; everything to its right is projected, not observed.")
          )
        )
      ),
      open = TRUE
    ),

    # Footer note ------------------------------------------------------------
    tags$p(
      class = "fv-method-note",
      "This page reads actuals.csv and the governed calibrated forecast artifact (forecasts_with_intervals_relative_60d_calibrated.csv, point-only fallback to forecasts.csv). It only visualizes interval columns already present in the governed artifact \u2014 it does not generate forecasts, compute or recalibrate intervals, residuals or quantiles, compare models, rerun tournaments, recalculate metrics, or change champion decisions."
    )
  )
}

section_accuracy <- function() {
  # Stage 07 Accuracy Page MVP: heatmap-first accuracy diagnostics derived in
  # memory from the FROZEN Stage 05H backtest artifact
  # (data/processed/forecast_viewer_model_outputs.csv). These are dashboard
  # diagnostics only - they are never persisted and never change the champion.
  # Heatmap + table live in STATIC containers and render only after the user
  # clicks Analyze Accuracy.

  acc_series    <- acc_series_choices()                  # 39 eligible series
  acc_models    <- acc_model_choices()                   # 13 family-ordered models
  horizon_opts  <- acc_horizon_choices()                 # 5..30
  horizon_named <- stats::setNames(as.character(horizon_opts),
                                   paste0(horizon_opts, " days"))

  panel(
    "accuracy",
    section_head(
      "Accuracy",
      "Exploratory backtest accuracy diagnostics from the frozen model-comparison artifact. Use this page to see where errors are highest or most stable across keys, models and horizons."
    ),

    # B. How to use this accuracy view (collapsed by default) --------------
    home_collapse(
      "How to use this accuracy view",
      "An exploratory accuracy sandbox to see where backtest error is highest or most stable.",
      tags$ul(
        class = "fvb-how-list",
        tags$li("This is an ", tags$b("exploratory"), " accuracy diagnostics view built from historical ", tags$b("backtest"), " outputs."),
        tags$li("It helps you spot which ", tags$b("keys / series"), " and ", tags$b("models"), " have higher or lower error."),
        tags$li("Heatmap color shows ", tags$b("relative severity"), " for the selected metric and horizon \u2014 red = higher error, blue = lower / more stable."),
        tags$li(tags$b("Lower error is better"), " for every metric shown."),
        tags$li("These are ", tags$b("dashboard diagnostics"), " from the frozen backtest artifact \u2014 not official governance metrics."),
        tags$li("This page does ", tags$b("not"), " generate forecasts, rerun tournaments, change champion decisions, or compute official MASE / RMSSE.")
      ),
      open = FALSE
    ),

    # =====================================================================
    # BOX 1 \u2014 SET UP THE ACCURACY VIEW (controls only, numbered steps).
    # Comes FIRST: configure here, then the summary + results fill in below.
    # Analyze Accuracy is the LAST step, at the bottom of this box.
    # =====================================================================
    tags$section(
      class = "fvx-section fvx-backtest fvb fvb-setup-section acc-setup-section",
      tags$div(
        class = "fvb-setup-head",
        tags$span(class = "fvx-section-kicker", "Accuracy"),
        tags$h3(class = "fvx-section-title", "Set up the accuracy view"),
        tags$span(class = "pill pill-blue", "Backtest \u00b7 diagnostics")
      ),
      tags$p(
        class = "fvb-setup-lead",
        "Choose a horizon, metric, models and filters, then run step 6. ",
        "Source: ", tags$code("forecast_viewer_model_outputs.csv"), "."
      ),

      # Steps 1, 2, 4, 5 -------------------------------------------------
      tags$div(
        class = "fvb-controls",
        tags$div(
          class = "fvb-field fvb-field-horizon",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "1"), "Select horizon"),
          radioButtons("acc_horizon", NULL, choices = horizon_named,
                       selected = "30", inline = TRUE),
          tags$p(class = "fvb-field-hint",
                 "Backtest horizon (days) used to compute the diagnostics.")
        ),
        tags$div(
          class = "fvb-field fvb-field-history",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "2"), "Select metric"),
          selectInput("acc_metric", NULL, choices = ACC_METRICS,
                      selected = "MAE", width = "100%"),
          tags$p(class = "fvb-field-hint",
                 "Drives the heatmap color (standardized) and the severity ranking. Lower is better.")
        ),
        tags$div(
          class = "fvb-field fvb-field-series",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "4"), "Filter key / series"),
          selectizeInput("acc_series", NULL, choices = acc_series,
                         selected = NULL, multiple = TRUE, width = "100%",
                         options = list(placeholder = "All eligible keys / series")),
          tags$p(class = "fvb-field-hint",
                 "Leave empty to include every eligible key / series.")
        ),
        tags$div(
          class = "fvb-field fvb-field-history",
          tags$label(class = "fvb-field-label",
                     tags$span(class = "fvb-step-num", "5"), "Rows shown"),
          selectInput("acc_topn", NULL,
                      choices = c("Top 10" = 10, "Top 20" = 20, "All (39)" = 39),
                      selected = 20, width = "100%"),
          tags$p(class = "fvb-field-hint",
                 "Heatmap keeps this many keys, ranked worst-first by the selected metric.")
        )
      ),

      # Step 3 \u2014 model selector -------------------------------------------
      tags$div(
        class = "fvb-models",
        tags$div(
          class = "fvb-models-head",
          tags$span(class = "fvb-field-label",
                    tags$span(class = "fvb-step-num", "3"), "Select models")
        ),
        selectizeInput("acc_models", NULL,
                       choices = c("All models" = "__ALL__", acc_models),
                       selected = "__ALL__", multiple = TRUE, width = "100%",
                       options = list(placeholder = "All models")),
        tags$p(class = "fvb-field-hint",
               "Keep All models or restrict to one or several.")
      ),

      # Step 6 \u2014 Analyze Accuracy (bottom of the setup box) ----------------
      tags$div(
        class = "fvb-analyze-row",
        tags$div(
          class = "fvb-analyze-label",
          tags$span(class = "fvb-step-num", "6"),
          tags$span(class = "fvb-field-label", "Analyze Accuracy")
        ),
        actionButton("acc_go", "Analyze Accuracy",
                     class = "fv-analyze-btn fvb-analyze-btn"),
        tags$p(class = "fvb-field-hint fvb-analyze-hint",
               "Renders the summary, heatmap and metric table below. Click again any time you change the horizon, metric or filters to refresh every result. All values are computed in memory from the governed backtest artifact; nothing is written back.")
      )
    ),

    # C. Accuracy summary (auto-fills after Analyze, above the results) -----
    home_collapse(
      "Accuracy summary",
      "Headline coverage and the worst / most stable pockets for the analyzed setup.",
      uiOutput("acc_summary_cards"),
      open = TRUE
    ),

    # =====================================================================
    # BOX 2 \u2014 HEATMAP (results: heatmap only).
    # Separate, collapsible box. Action-gated: empty state until Analyze.
    # =====================================================================
    home_collapse(
      "Heatmap",
      "Severity by key / series and model. Color uses standardized relative severity for the selected metric and horizon; lower is better.",
      tags$div(
        class = "fvb-result",
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvb-field-label", "Severity heatmap")
        ),
        tags$div(
          class = "fv-chart-wrap fvb-chart-wrap",
          plotly::plotlyOutput("acc_heatmap", height = "560px")
        ),
        tags$div(
          class = "fv-warn-card",
          tags$ul(
            class = "fv-warn-list",
            tags$li(tags$span(class = "pill pill-amber", "Diagnostics"),
                    "These are dashboard diagnostics derived from the frozen backtest output. They are not official governance metrics and do not change champion selection."),
            tags$li(tags$span(class = "pill pill-slate", "Standardized"),
                    "Heatmap color uses a robust standardized severity score (median / IQR) so different measures are visually comparable.")
          )
        )
      ),
      open = TRUE
    ),

    # =====================================================================
    # BOX 3 \u2014 METRIC VALUES TABLE (results: raw + standardized table).
    # Separate, collapsible box. Same action-gated source as the heatmap.
    # =====================================================================
    home_collapse(
      "Metric values (raw + standardized)",
      "Per key / series and model values for the selected metric and horizon. Raw values plus the standardized severity score used by the heatmap; lower is better.",
      tags$div(
        class = "fvb-result",
        tags$div(
          class = "fvb-result-head",
          tags$span(class = "fvb-field-label", "Metric values (raw + standardized)")
        ),
        tags$div(class = "tess-table-wrap",
                 DT::dataTableOutput("acc_table")),
        tags$div(
          class = "fv-warn-card",
          tags$ul(
            class = "fv-warn-list",
            tags$li(tags$span(class = "pill pill-slate", "Standardized"),
                    "The standardized column matches the heatmap color (robust median / IQR score). The other columns show raw measure values."),
            tags$li(tags$span(class = "pill pill-blue", "Backtest only"),
                    "Accuracy uses historical backtest data only (never the forward forecast / actuals files). It does not generate forecasts.")
          )
        )
      ),
      open = TRUE
    ),

    # Footer note ----------------------------------------------------------
    tags$p(
      class = "fv-method-note",
      "This page reads the governed backtest artifact and computes display diagnostics in memory. It does not generate forecasts, rerun tournaments, change champion decisions, or compute official MASE / RMSSE governance metrics."
    )
  )
}

section_ttl <- function() {
  # Stage 07 TTL PROTOTYPE. DEMAND is our REAL forecast; SUPPLY and the derived
  # Months-to-Live (TTL) are SIMULATED (python/shiny_mvp/build_ttl_prototype.py)
  # and clearly labelled as such. This is an illustrative example of how the
  # forecasting work feeds a Time-To-Live / capacity view; it is NOT governed
  # and does not change any champion. It mirrors the AEGIS capacity views so a
  # later swap to the real SQL sources is a drop-in replacement.

  ttl_series <- ttl_series_choices()
  n_series   <- length(ttl_series)

  ttl_step <- function(num, title, control, hint = NULL, extra = NULL) {
    tags$div(
      class = "fv-step",
      tags$div(
        class = "fv-step-head",
        tags$span(class = "fv-step-num", as.character(num)),
        tags$span(class = "fv-step-title", title)
      ),
      control,
      if (!is.null(hint)) tags$p(class = "fv-step-hint", hint),
      extra
    )
  }

  panel(
    "ttl",

    # A. Header --------------------------------------------------------------
    section_head(
      "TTL / Capacity View",
      "Time-to-Live (Months to Live): how long until forecast demand reaches supply, so capacity can be added before a shortage. Prototype example built on our forecasts."
    ),

    # B. How to use this TTL / Capacity View (collapsed by default) ---------
    home_collapse(
      "How to use this TTL / Capacity View",
      "A quick guide to reading Months-to-Live, the supply-vs-demand crossover and the utilization heatmap.",
      tags$div(
        class = "home-prose",
        tags$p(
          "This view explains how long each series has before forecast demand reaches ",
          "available supply. Select a series, click Analyze TTL, and review the ",
          "Months-to-Live gauge, the supply-vs-demand crossover chart, and the projected ",
          "utilization heatmap. Demand is based on the forecast artifact; supply and TTL ",
          "are currently simulated/prototype inputs until validated supply artifacts are ",
          "available."
        )
      ),
      open = FALSE
    ),

    # C. TTL Capacity Overview (open) --- prototype note + fleet KPI cards ---
    home_collapse(
      "TTL Capacity Overview",
      "Prototype status and the fleet-wide TTL band summary across all series.",
      tags$div(
        class = "ttl-callout ttl-callout-proto",
        tags$span(class = "pill pill-amber", "Prototype \u00b7 simulated supply"),
        tags$h3(class = "ttl-callout-title",
                "Demand is real (our forecast) \u00b7 Supply & TTL are simulated"),
        tags$p(
          class = "ttl-callout-text",
          "This page shows how forecasting improvements feed a Time-To-Live view. ",
          "The demand line comes from our real forecasts; supply and the derived ",
          "Months-to-Live are simulated for illustration. Real AEGIS sources ",
          "(", tags$code("vw_SubstrateBE_MonthsToLive_*"), ", ",
          tags$code("HLC_BE_Future_Supply_TimeSeries_*"),
          ") are identified but not yet validated as governed artifacts."
        )
      ),
      uiOutput("ttl_summary_cards"),
      open = TRUE
    ),

    # D. Set up the TTL view (open) --- controls only -----------------------
    home_collapse(
      "Set up the TTL view",
      "Choose a series and run Analyze TTL to populate the selected-series results below.",
      tags$div(
        class = "fv-setup-panel",
        ttl_step(
          1, "Select series",
          selectInput("ttl_series", NULL, choices = ttl_series,
                      selected = if (n_series) ttl_series[[1]] else NULL,
                      width = "100%"),
          "Series are sorted shortest Time-to-Live first (most urgent at the top)."
        ),
        tags$div(
          class = "fv-step fv-step-action",
          tags$div(
            class = "fv-step-head",
            tags$span(class = "fv-step-num", "2"),
            tags$span(class = "fv-step-title", "Analyze")
          ),
          actionButton("ttl_go", "Analyze TTL", class = "fv-analyze-btn"),
          tags$p(class = "fv-step-hint",
                 "The gauge and chart update only after you click Analyze TTL.")
        ),
        tags$p(class = "fv-entity-note",
               "Demand = real forecast. Supply & TTL = simulated. Nothing is written back.")
      ),
      open = TRUE
    ),

    # E. TTL Results -- Selected Series (open) --- KPI cards + gauge + line --
    home_collapse(
      "TTL Results \u2014 Selected Series",
      "Result metrics, the Months-to-Live gauge and the supply-vs-demand crossover for the selected series.",
      tags$div(
        class = "fv-result",
        uiOutput("ttl_series_kpis"),
        tags$div(
          class = "fv-step-head ttl-result-subhead",
          tags$span(class = "fv-step-title", "Months to Live")
        ),
        tags$div(
          class = "ttl-gauge-wrap",
          highcharter::highchartOutput("ttl_gauge", height = "300px")
        ),
        tags$div(
          class = "fv-notes-head ttl-result-subhead",
          tags$span(class = "fv-step-title", "Supply vs Demand (crossover)")
        ),
        tags$div(
          class = "fv-chart-wrap",
          highcharter::highchartOutput("ttl_line", height = "380px")
        )
      ),
      open = TRUE
    ),

    # F. Projected Utilization Heatmap (open) --- fleet view ----------------
    home_collapse(
      "Projected Utilization Heatmap",
      "Fleet-wide projected monthly utilization, most-urgent series first.",
      tags$p(
        class = "fvx-section-lead",
        "Projected monthly utilization across all series. Red indicates series ",
        "approaching or exceeding capacity; cooler colors indicate more headroom."
      ),
      tags$div(
        class = "fv-chart-wrap",
        plotly::plotlyOutput("ttl_heatmap", height = "640px")
      ),
      open = TRUE
    ),

    # G. Time-to-Live Snapshot Table (collapsed; long table) ----------------
    home_collapse(
      "Time-to-Live Snapshot Table",
      "Per-series TTL status, sorted by most urgent capacity risk first.",
      tags$p(
        class = "fvx-section-lead",
        "Snapshot of TTL status by series, sorted by most urgent capacity risk first."
      ),
      tags$div(class = "tess-table-wrap",
               DT::dataTableOutput("ttl_table")),

      # TTL color legend
      tags$div(
        class = "ttl-legend",
        lapply(names(TTL_BANDS), function(k) {
          b <- TTL_BANDS[[k]]
          tags$span(class = "ttl-legend-item",
                    tags$span(class = "ttl-legend-swatch",
                              style = paste0("background:", b$color, ";")),
                    paste0(b$label, " (", b$hint, ")"))
        })
      ),

      tags$p(
        class = "fv-method-note",
        "Prototype only. Demand is our real forecast; supply and the derived ",
        "Months-to-Live are simulated for illustration. This page does not ",
        "generate new forecasts, recompute governed metrics, or change any ",
        "selected champion. It will be repointed to governed AEGIS capacity ",
        "sources once those are validated."
      ),
      open = FALSE
    )
  )
}

# Small inline badge built on the existing .pill classes (no new CSS).
.tess_badge <- function(text, pill_class = "pill-blue") {
  paste0('<span class="pill ', pill_class, '">', htmltools::htmlEscape(text), '</span>')
}

# Build the governed model universe table as a static DT widget (read-only).
# All values come straight from the final_model_universe artifact; nothing is
# recomputed. Badges only re-label existing columns for readability.
universe_table_widget <- function(df = universe_normalized()) {
  if (!is.data.frame(df) || nrow(df) == 0) {
    return(tags$div(
      class = "shell-card",
      tags$span(class = "pill pill-amber", "Artifact missing"),
      tags$h3(class = "shell-card-title", "Model universe unavailable"),
      tags$p(class = "shell-card-detail",
             "The governed final_model_universe artifact could not be read. No values are shown.")
    ))
  }

  origin_badge <- ifelse(
    df$model_origin == "baseline",
    .tess_badge("Baseline", "pill-blue"),
    ifelse(df$model_origin == "challenger",
           .tess_badge("Challenger", "pill-amber"),
           .tess_badge(ifelse(nzchar(df$model_origin), df$model_origin, "\u2014"), "pill-blue"))
  )

  status_txt   <- universe_status_label(df$final_status)
  status_badge <- ifelse(
    df$final_status == "selected_champion",
    .tess_badge(status_txt, "pill-green"),
    ifelse(grepl("^deferred", df$final_status),
           .tess_badge(status_txt, "pill-amber"),
           .tess_badge(status_txt, "pill-blue"))
  )

  yn <- function(flag, yes_txt, no_txt, yes_cls = "pill-green", no_cls = "pill-amber") {
    ifelse(flag %in% TRUE, .tess_badge(yes_txt, yes_cls),
           ifelse(flag %in% FALSE, .tess_badge(no_txt, no_cls), "\u2014"))
  }

  tournament_badge <- yn(df$included_in_tournament, "Included", "Excluded")
  eligible_badge   <- yn(df$eligible_for_champion, "Eligible", "Not eligible")
  champion_badge   <- ifelse(df$selected_champion %in% TRUE,
                             .tess_badge("Selected champion (with conditions)", "pill-green"),
                             "\u2014")
  risk_badge       <- ifelse(df$risk_flag %in% TRUE,
                             .tess_badge("Risk flag", "pill-amber"),
                             .tess_badge("None", "pill-blue"))

  family_txt   <- ifelse(nzchar(df$model_family),
                         gsub("_", " ", df$model_family), "\u2014")
  deferred_txt <- ifelse(nzchar(df$deferred_reason),
                         gsub("_", " ", df$deferred_reason), "\u2014")

  tbl <- data.frame(
    Model      = htmltools::htmlEscape(df$model_name),
    Origin     = origin_badge,
    Family     = htmltools::htmlEscape(family_txt),
    Status     = status_badge,
    Tournament = tournament_badge,
    `Champion eligibility` = eligible_badge,
    Champion   = champion_badge,
    Risk       = risk_badge,
    `Deferred reason` = htmltools::htmlEscape(deferred_txt),
    check.names = FALSE,
    stringsAsFactors = FALSE
  )

  DT::datatable(
    tbl,
    rownames  = FALSE,
    escape    = FALSE,
    class     = "stripe hover row-border",
    options   = list(
      paging        = FALSE,
      searching     = TRUE,
      info          = FALSE,
      ordering      = TRUE,
      scrollX       = TRUE,
      dom           = "ft",
      columnDefs    = list(list(className = "dt-left", targets = "_all"))
    )
  )
}

# Visual family blocks for the Universe page: one card per model family with a
# plain-language description and the models in it as labelled chips (read-only).
universe_families_ui <- function(df = universe_normalized()) {
  if (!is.data.frame(df) || nrow(df) == 0 || !("model_family" %in% names(df))) {
    return(tags$p(class = "shell-card-detail", "The model universe is unavailable."))
  }

  fam_meta <- list(
    statistical = list(
      label = "Statistical",
      desc  = "Classical time-series methods (ARIMA, ETS, Theta). Today's production approach lives here, alongside the selected champion."
    ),
    growth_baseline = list(
      label = "Growth baselines",
      desc  = "Simple fixed-growth anchors (for example +1.5% or +3% per period). Naive references that any serious model is expected to beat."
    ),
    machine_learning = list(
      label = "Machine learning",
      desc  = "Feature-based learners such as linear regression and gradient boosting. Flexible, but they need enough signal to shine."
    ),
    deep_learning = list(
      label = "Deep Learning",
      desc  = "Three lightweight deep-learning challengers (SMLP-TCN, NLIN-DLIN_FIXED, FNAR-V2) evaluated in the closed V3.2D/V3.2E candidate study. They carry more capacity than classic machine learning but, on this data, stay well above the statistical leaders."
    )
  )

  fam_order <- c("statistical", "growth_baseline", "machine_learning",
                 "deep_learning")
  fams <- unique(df$model_family)
  fams <- c(intersect(fam_order, fams), setdiff(fams, fam_order))

  blocks <- lapply(fams, function(fam) {
    sub   <- df[df$model_family == fam, , drop = FALSE]
    meta  <- fam_meta[[fam]]
    label <- if (!is.null(meta)) meta$label else gsub("_", " ", fam)
    desc  <- if (!is.null(meta)) meta$desc else ""

    chips <- lapply(seq_len(nrow(sub)), function(i) {
      r        <- sub[i, ]
      is_champ <- isTRUE(r$selected_champion %in% TRUE)
      is_risk  <- isTRUE(r$risk_flag %in% TRUE)
      is_base  <- identical(as.character(r$model_origin), "baseline")
      tags$div(
        class = paste("uni-chip",
                      if (is_champ) "is-champion" else if (is_risk) "is-risk" else ""),
        tags$span(class = "uni-chip-name", r$model_name),
        tags$span(
          class = paste("uni-chip-tag", if (is_base) "uni-tag-base" else "uni-tag-chall"),
          if (is_base) "Baseline" else "Challenger"
        ),
        if (is_champ) tags$span(class = "uni-chip-tag uni-tag-champ", "\u2605 Champion"),
        if (is_risk)  tags$span(class = "uni-chip-tag uni-tag-risk", "Risk flag")
      )
    })

    tags$div(
      class = "uni-family",
      tags$div(
        class = "uni-family-head",
        tags$span(class = "uni-family-title", label),
        tags$span(class = "uni-family-count",
                  paste0(nrow(sub), if (nrow(sub) == 1) " model" else " models"))
      ),
      tags$p(class = "uni-family-desc", desc),
      tags$div(class = "uni-chip-row", chips)
    )
  })

  tags$div(class = "uni-family-grid", blocks)
}

# Static HTML table for the visible model set. Rendered as plain HTML (not a
# DT widget) so it draws reliably even inside a collapsed section. Read-only;
# excludes deferred models (caller passes the already-filtered frame).
universe_static_table_ui <- function(df) {
  if (!is.data.frame(df) || nrow(df) == 0) {
    return(tags$p(class = "shell-card-detail", "No active models to display."))
  }
  fam_label <- function(r) {
    if (!is.null(r$family_label) && nzchar(r$family_label)) return(r$family_label)
    x <- as.character(r$model_family)
    ifelse(nzchar(x), gsub("_", " ", x), "\u2014")
  }
  has_mase <- "median_mase" %in% names(df)
  has_src  <- "evidence_source" %in% names(df)
  src_label <- function(x) {
    switch(as.character(x),
           governed_tournament  = "Governed tournament",
           candidate_evaluation = "Candidate evaluation",
           if (nzchar(as.character(x))) gsub("_", " ", as.character(x)) else "\u2014")
  }

  rows <- lapply(seq_len(nrow(df)), function(i) {
    r        <- df[i, ]
    is_champ <- isTRUE(r$selected_champion %in% TRUE)
    is_base  <- identical(as.character(r$model_origin), "baseline")
    elig     <- isTRUE(r$eligible_for_champion %in% TRUE)
    tags$tr(
      class = if (is_champ) "uni-row-champ" else NULL,
      tags$td(
        tags$span(class = "uni-td-name", r$model_name),
        if (is_champ) tags$span(class = "uni-chip-tag uni-tag-champ",
                                style = "margin-left:8px;", "\u2605 Champion")
      ),
      tags$td(tags$span(
        class = paste("uni-chip-tag", if (is_base) "uni-tag-base" else "uni-tag-chall"),
        if (is_base) "Baseline" else "Challenger")),
      tags$td(fam_label(r)),
      if (has_mase) tags$td(fmt_metric(r$median_mase, 2)),
      tags$td(if (elig)
                tags$span(class = "uni-chip-tag uni-tag-champ", "Eligible")
              else
                tags$span(class = "uni-chip-tag uni-tag-muted", "Not eligible")),
      if (has_src) tags$td(tags$span(class = "shell-card-detail",
                                     style = "font-size:12px;", src_label(r$evidence_source)))
    )
  })

  tags$table(
    class = "uni-table",
    tags$thead(tags$tr(
      tags$th("Model"), tags$th("Origin"), tags$th("Family"),
      if (has_mase) tags$th("Median MASE"),
      tags$th("Champion eligible"),
      if (has_src) tags$th("Evidence")
    )),
    tags$tbody(rows)
  )
}

section_universe <- function() {
  # --- Governed data binding (read-only, from the 7.0E loader cache) ---
  uni   <- universe_normalized()
  champ <- first_label(universe_champion_name(uni), APP_CHAMPION)

  # Visible model set: active models that entered the governed tournament.
  # Deferred deep-learning candidates (e.g. NBEATS, NHITS) are intentionally
  # excluded from the visible Universe page. The underlying artifact is never
  # modified.
  vis <- if (is.data.frame(uni) && "included_in_tournament" %in% names(uni)) {
    uni[uni$included_in_tournament %in% TRUE, , drop = FALSE]
  } else uni

  n_vis <- if (is.data.frame(vis)) nrow(vis) else 0L
  n_fam <- if (is.data.frame(vis) && "model_family" %in% names(vis))
             length(unique(vis$model_family)) else 0L
  fam_intro <- sprintf(
    "AEGIS compares %d models across %d families \u2014 growth baselines, statistical methods, machine learning and deep learning. ETS Explicit is the governed champion under conditions.",
    n_vis, n_fam)

  panel(
    "universe",

    # A. Header --------------------------------------------------------------
    section_head(
      "Model Universe",
      "The set of models AEGIS compares \u2014 baselines, challengers and the governed champion \u2014 explained from the ground up."
    ),

    # B. How to read this universe (FIRST, open by default) ------------------
    home_collapse(
      "How to read this universe",
      "Start here: what baselines, challengers, the tournament and the champion actually mean.",
      info_list(
        info_row("Baseline (current & reference)",
                 "Today's production approach plus simple reference models. They anchor the comparison \u2014 they are not improvement candidates themselves."),
        info_row("Challenger (candidate)",
                 "New candidate models proposed to improve on the baselines. Each one is evaluated head-to-head inside the governed tournament."),
        info_row("Included in tournament",
                 "The model entered the governed rolling-origin ranking that compares every candidate on the same history."),
        info_row("Champion eligible",
                 "A governed flag marking a model as allowed to be considered for champion. It does not, by itself, decide the champion."),
        info_row("Evidence source",
                 "Where each model's accuracy comes from: the governed rolling-origin tournament (12 models) or the closed V3.2D/V3.2E candidate evaluation (the 3 deep-learning challengers). Both are read on the same governed backtest history."),
        info_row("Selected champion (with conditions)",
                 paste0("The governed choice (", champ,
                        "). It is approved with conditions and must be read together with the documented risks and governance notes \u2014 never as an unconditional winner."))
      ),
      open = FALSE
    ),

    # C. Model families compared (collapsible, closed) -----------------------
    home_collapse(
      "Model families compared",
      "The four active model families in play, from simple growth baselines to deep-learning challengers.",
      tags$p(class = "uni-fam-intro", fam_intro),
      universe_families_ui(vis),
      open = FALSE
    ),

    # D. Current model universe table (collapsible, closed) ------------------
    home_collapse(
      "Current model universe (15 models)",
      "Every active model with its origin, family, median MASE, champion eligibility and evidence source.",
      universe_static_table_ui(vis),
      open = FALSE
    )
  )
}

# Static HTML "league table" for the tournament. Plain HTML (not a DT widget)
# so it renders reliably inside a collapsible and reads like a sports standings
# table. Read-only; the caller passes the joined scorecard + evidence frame
# already ordered for readability. No composite score is computed here.
tournament_league_table_ui <- function(df) {
  if (!is.data.frame(df) || nrow(df) == 0) {
    return(tags$p(class = "shell-card-detail",
                  "Governed tournament evidence is unavailable."))
  }
  fam_label <- function(x) ifelse(nzchar(x), gsub("_", " ", x), "\u2014")
  num <- function(x, d = 2) {
    x <- suppressWarnings(as.numeric(x))
    if (length(x) != 1 || is.na(x)) "\u2014" else formatC(x, format = "f", digits = d)
  }
  int <- function(x) {
    x <- suppressWarnings(as.numeric(x))
    if (length(x) != 1 || is.na(x)) "\u2014" else as.character(as.integer(round(x)))
  }

  rows <- lapply(seq_len(nrow(df)), function(i) {
    r        <- df[i, ]
    is_champ <- isTRUE(r$selected_champion %in% TRUE)
    elig     <- isTRUE(r$eligible_for_champion_consideration %in% TRUE)
    risk     <- tolower(trimws(as.character(r$risk_status)))
    net      <- suppressWarnings(as.numeric(r$net_supported_evidence))
    net_cls  <- if (is.na(net)) "uni-tag-muted" else if (net > 0) "uni-tag-champ" else if (net < 0) "uni-tag-risk" else "uni-tag-muted"
    net_txt  <- if (is.na(net)) "\u2014" else if (net > 0) paste0("+", int(net)) else int(net)
    risk_cls <- if (risk %in% c("high", "high_risk")) "uni-tag-risk" else if (risk %in% c("medium", "med")) "uni-tag-base" else "uni-tag-muted"
    risk_lbl <- if (nzchar(risk) && risk != "na") risk else "low"
    tags$tr(
      class = if (is_champ) "uni-row-champ" else NULL,
      tags$td(as.character(i)),
      tags$td(
        tags$span(class = "uni-td-name", r$model_name),
        if (is_champ) tags$span(class = "uni-chip-tag uni-tag-champ",
                                style = "margin-left:8px;", "\u2605 Champion")
      ),
      tags$td(fam_label(r$model_family)),
      tags$td(int(r$supported_better_count)),
      tags$td(int(r$supported_worse_count)),
      tags$td(int(r$inconclusive_count)),
      tags$td(tags$span(class = paste("uni-chip-tag", net_cls), net_txt)),
      tags$td(num(r$official_median_mase)),
      tags$td(num(r$official_median_rmsse)),
      tags$td(tags$span(class = paste("uni-chip-tag", risk_cls), risk_lbl)),
      tags$td(if (elig)
                tags$span(class = "uni-chip-tag uni-tag-champ", "Eligible")
              else
                tags$span(class = "uni-chip-tag uni-tag-muted", "Not eligible"))
    )
  })

  tags$div(
    style = "overflow-x:auto;",
    tags$table(
      class = "uni-table",
      tags$thead(tags$tr(
        tags$th("#"), tags$th("Model"), tags$th("Family"),
        tags$th("Better"), tags$th("Worse"), tags$th("Inconclusive"),
        tags$th("Net evidence"), tags$th("MASE"), tags$th("RMSSE"),
        tags$th("Risk"), tags$th("Eligibility")
      )),
      tags$tbody(rows)
    )
  )
}

# Dendrogram-style "Tournament Evidence Tree". Pure HTML/CSS, built from the
# governed league frame (scorecard + pairwise evidence summary). It is a VISUAL
# GROUPING only: the 13 active models are branched by their governed net
# head-to-head evidence so you can see how they cluster/separate. It does NOT
# recompute metrics, invent scores, create weights, or replace the selected
# champion under conditions.
tournament_evidence_tree_ui <- function(df) {
  if (!is.data.frame(df) || nrow(df) == 0) {
    return(tags$p(class = "shell-card-detail",
                  "Governed tournament evidence is unavailable."))
  }
  num <- function(x, d = 2) {
    x <- suppressWarnings(as.numeric(x))
    if (length(x) != 1 || is.na(x)) "\u2014" else formatC(x, format = "f", digits = d)
  }
  int <- function(x) {
    x <- suppressWarnings(as.numeric(x))
    if (length(x) != 1 || is.na(x)) "\u2014" else as.character(as.integer(round(x)))
  }
  net_vec <- suppressWarnings(as.numeric(df$net_supported_evidence))
  n_all   <- nrow(df)
  champ_idx <- which(df$selected_champion %in% TRUE)
  champ     <- if (length(champ_idx) >= 1) df[champ_idx[1], , drop = FALSE] else df[1, , drop = FALSE]
  champ_net <- suppressWarnings(as.numeric(champ$net_supported_evidence))
  champ_net_txt <- if (length(champ_net) != 1 || is.na(champ_net)) "\u2014"
                   else if (champ_net > 0) paste0("+", as.integer(round(champ_net)))
                   else as.character(as.integer(round(champ_net)))

  fam_class <- function(f) {
    f <- tolower(as.character(f))
    if (grepl("statistic", f)) "fam-stat"
    else if (grepl("growth", f)) "fam-growth"
    else if (grepl("machine", f)) "fam-ml"
    else if (grepl("neural|deep", f)) "fam-neural"
    else "fam-other"
  }
  fam_label <- function(f) {
    f <- tolower(as.character(f))
    if (grepl("statistic", f)) "Statistical"
    else if (grepl("growth", f)) "Growth baseline"
    else if (grepl("machine", f)) "Machine learning"
    else if (grepl("neural|deep", f)) "Neural"
    else gsub("_", " ", f)
  }

  leaf <- function(i) {
    net   <- net_vec[i]
    champ <- isTRUE(df$selected_champion[i] %in% TRUE)
    risk  <- tolower(as.character(df$risk_status[i]))
    elig  <- isTRUE(df$eligible_for_champion_consideration[i] %in% TRUE)
    net_txt <- if (is.na(net)) "\u2014" else if (net > 0) paste0("+", as.integer(round(net))) else as.character(as.integer(round(net)))
    net_cls <- if (is.na(net) || net == 0) "is-zero" else if (net > 0) "is-pos" else "is-neg"
    flag <- if (!elig) tags$span(class = "tev-leaf-flag is-inelig", "Not eligible")
            else if (risk %in% c("high", "high_risk")) tags$span(class = "tev-leaf-flag is-risk", "High risk")
            else if (risk %in% c("medium", "medium_risk")) tags$span(class = "tev-leaf-flag is-warn", "Medium risk")
            else NULL
    tags$div(
      class = paste("tev-leaf", fam_class(df$model_family[i]), if (champ) "is-champ" else NULL),
      tags$div(
        class = "tev-leaf-top",
        if (champ) tags$span(class = "tev-leaf-star", "\u2605"),
        tags$span(class = "tev-leaf-name", df$model_name[i]),
        tags$span(class = paste("tev-leaf-net", net_cls), net_txt)
      ),
      tags$div(
        class = "tev-leaf-meta",
        tags$span(class = "tev-leaf-fam", fam_label(df$model_family[i])),
        tags$span(class = "tev-leaf-mase", paste0("MASE ", num(df$official_median_mase[i]))),
        flag
      )
    )
  }

  tier_def <- list(
    list(key = "strong",   title = "Strong evidence", hint = "net \u2265 +5",     test = function(n) !is.na(n) & n >= 5),
    list(key = "positive", title = "Positive evidence", hint = "net +1 to +4",  test = function(n) !is.na(n) & n >= 1 & n <= 4),
    list(key = "even",     title = "Even record",     hint = "net = 0",         test = function(n) !is.na(n) & n == 0),
    list(key = "behind",   title = "Net negative",    hint = "net < 0",         test = function(n) !is.na(n) & n < 0)
  )

  branches <- lapply(tier_def, function(t) {
    idx <- which(t$test(net_vec))
    if (length(idx) == 0) return(NULL)
    tags$div(
      class = paste0("tev-branch tev-branch-", t$key),
      tags$div(
        class = "tev-branch-head",
        tags$div(
          class = paste0("tev-tier tev-tier-", t$key),
          tags$span(class = "tev-tier-title", t$title),
          tags$span(class = "tev-tier-hint", t$hint),
          tags$span(class = "tev-tier-count", paste0(length(idx), " model", if (length(idx) != 1) "s" else ""))
        )
      ),
      tags$div(class = "tev-leaves", lapply(idx, leaf))
    )
  })
  branches <- branches[!vapply(branches, is.null, logical(1))]

  legend <- tags$div(
    class = "tev-legend",
    tags$span(class = "tev-leg-item", tags$span(class = "tev-leg-dot fam-stat"), "Statistical"),
    tags$span(class = "tev-leg-item", tags$span(class = "tev-leg-dot fam-growth"), "Growth baseline"),
    tags$span(class = "tev-leg-item", tags$span(class = "tev-leg-dot fam-ml"), "Machine learning"),
    tags$span(class = "tev-leg-item", tags$span(class = "tev-leg-dot fam-neural"), "Neural"),
    tags$span(class = "tev-leg-item", tags$span(class = "tev-leaf-star tev-leg-star", "\u2605"), "Selected champion (conditions)")
  )

  tags$div(
    class = "tev",
    tags$div(
      class = "tev-outcome",
      tags$div(
        class = "tev-outcome-head",
        tags$span(class = "tev-outcome-kicker", "Tournament outcome"),
        tags$div(
          class = "tev-outcome-name",
          tags$span(class = "tev-outcome-star", "\u2605"),
          champ$model_name
        ),
        tags$span(class = "tev-outcome-tag", "Selected champion under conditions")
      ),
      tags$div(
        class = "tev-outcome-stats",
        tags$div(class = "tev-outcome-stat",
                 tags$span(class = "tev-outcome-stat-value",
                           paste0(int(champ$supported_better_count), " / ",
                                  int(champ$supported_worse_count), " / ",
                                  int(champ$inconclusive_count))),
                 tags$span(class = "tev-outcome-stat-label", "Better / Worse / Inconclusive")),
        tags$div(class = "tev-outcome-stat",
                 tags$span(class = "tev-outcome-stat-value tev-outcome-pos", champ_net_txt),
                 tags$span(class = "tev-outcome-stat-label", "Net evidence")),
        tags$div(class = "tev-outcome-stat",
                 tags$span(class = "tev-outcome-stat-value", num(champ$official_median_mase)),
                 tags$span(class = "tev-outcome-stat-label", "MASE (lowest)")),
        tags$div(class = "tev-outcome-stat",
                 tags$span(class = "tev-outcome-stat-value", num(champ$official_median_rmsse)),
                 tags$span(class = "tev-outcome-stat-label", "RMSSE (guardrail)"))
      )
    ),
    tags$p(
      class = "tev-note",
      "Visual grouping from governed tournament evidence. This tree does not recompute metrics or replace the selected champion under conditions. Models are branched by their net head-to-head evidence (supported better minus supported worse); the grouping is a reading aid, not an official score, weighting, or elimination."
    ),
    tags$div(
      class = "tev-tree",
      tags$div(
        class = "tev-root",
        tags$div(
          class = "tev-node-root",
          tags$span(class = "tev-root-big", as.character(n_all)),
          tags$span(class = "tev-root-label", "models \u00b7 governed evidence")
        )
      ),
      tags$div(class = "tev-branches", branches)
    ),
    legend
  )
}

# Current 15-model ranking table from the canonical universe artifact. Pure
# HTML (not a DT widget) so it renders inside a collapsible. Read-only; ordered
# by median MASE. Shows the evidence source (governed tournament vs candidate
# evaluation) so the two populations are never silently merged.
universe_canonical_ranking_table_ui <- function(df = universe_normalized()) {
  if (!is.data.frame(df) || nrow(df) == 0 || !("median_mase" %in% names(df))) {
    return(tags$p(class = "shell-card-detail",
                  "The current model ranking is unavailable."))
  }
  df <- df[order(suppressWarnings(as.numeric(df$median_mase))), , drop = FALSE]
  fam_label <- function(r) {
    if (!is.null(r$family_label) && nzchar(r$family_label)) return(r$family_label)
    x <- as.character(r$model_family)
    ifelse(nzchar(x), gsub("_", " ", x), "\u2014")
  }
  src_label <- function(x) {
    switch(as.character(x),
           governed_tournament  = tags$span(class = "uni-chip-tag uni-tag-base", "Governed tournament"),
           candidate_evaluation = tags$span(class = "uni-chip-tag uni-tag-chall", "Candidate evaluation"),
           tags$span(class = "uni-td-dash", "\u2014"))
  }
  num <- function(x, d = 2) {
    x <- suppressWarnings(as.numeric(x))
    if (length(x) != 1 || is.na(x)) "\u2014" else formatC(x, format = "f", digits = d)
  }
  rows <- lapply(seq_len(nrow(df)), function(i) {
    r        <- df[i, ]
    is_champ <- isTRUE(r$selected_champion %in% TRUE)
    is_base  <- identical(as.character(r$model_origin), "baseline")
    tags$tr(
      class = if (is_champ) "uni-row-champ" else NULL,
      tags$td(as.character(i)),
      tags$td(
        tags$span(class = "uni-td-name", r$model_name),
        if (is_champ) tags$span(class = "uni-chip-tag uni-tag-champ",
                                style = "margin-left:8px;", "\u2605 Champion")
      ),
      tags$td(fam_label(r)),
      tags$td(tags$span(
        class = paste("uni-chip-tag", if (is_base) "uni-tag-base" else "uni-tag-chall"),
        if (is_base) "Baseline" else "Challenger")),
      tags$td(num(r$median_mase)),
      tags$td(num(r$median_rmsse)),
      tags$td(src_label(r$evidence_source))
    )
  })
  tags$div(
    style = "overflow-x:auto;",
    tags$table(
      class = "uni-table",
      tags$thead(tags$tr(
        tags$th("#"), tags$th("Model"), tags$th("Family"), tags$th("Origin"),
        tags$th("Median MASE"), tags$th("Median RMSSE"), tags$th("Evidence source")
      )),
      tags$tbody(rows)
    )
  )
}

section_tournament <- function() {
  vals <- tournament_summary_values()
  league <- tournament_league_data()
  dv <- model_eval_dashboard_values()
  canon <- universe_normalized()
  n_models <- if (is.data.frame(canon)) nrow(canon) else 0L
  n_fam <- if (is.data.frame(canon) && "model_family" %in% names(canon))
             length(unique(canon$model_family)) else 0L
  champ_name <- first_label(universe_champion_name(canon), APP_CHAMPION)
  n <- function(x) {
    if (length(x) != 1 || is.na(x) || !nzchar(as.character(x))) "\u2014" else as.character(x)
  }
  panel(
    "tournament",
    section_head(
      "Tournament Standings",
      sprintf("AEGIS compares %d models across %d families. Median MASE is the primary metric, RMSSE is the guardrail, and ETS Explicit is selected under conditions.",
              n_models, n_fam)
    ),

    # A. How to read this tournament (FIRST, open) --------------------------
    home_collapse(
      "How to read this tournament",
      "Start here: what the tournament compares, the metrics, and why ETS Explicit is selected under conditions.",
      info_list(
        info_row("What is being compared",
                 paste0("The current universe is ", n_models, " models across ", n_fam,
                        " families (growth baselines, statistical, machine learning, deep learning). Each is scored on the same governed walk-forward backtest history.")),
        info_row("MASE is the primary metric",
                 "MASE measures forecast error. Lower is better \u2014 think of it as the model's score."),
        info_row("RMSSE is the guardrail",
                 "RMSSE is a second error metric used as a guardrail, so a model cannot look good on one metric while failing on another."),
        info_row("Two evidence sources",
                 "12 models were ranked inside the governed bootstrap pairwise tournament. The 3 deep-learning challengers were evaluated separately in the closed V3.2D/V3.2E candidate study and did not enter the pairwise bootstrap \u2014 their median MASE/RMSSE are shown for the same backtest, but they have no pairwise record."),
        info_row("Pairwise evidence (governed 12)",
                 "Inside the governed tournament, each pair of models has a head-to-head outcome (supported better, worse, or inconclusive). This record is shown in the legacy tournament evidence below."),
        info_row("Selected champion under conditions",
                 paste0(champ_name, " has the lowest median MASE and the strongest head-to-head record (8 supported-better, 0 supported-worse, confidence medium), so it is the selected champion under conditions \u2014 not an unconditional winner."))
      ),
      open = TRUE
    ),

    # B. Current model universe summary (collapsible, open) -----------------
    home_collapse(
      "Current model universe",
      "The current universe at a glance: how many models and families, the metrics, and the selected champion.",
      card_grid(
        kpi_card(as.character(n_models), "Models",
                 pill = "Current universe", pill_class = "pill-blue"),
        kpi_card(as.character(n_fam), "Families",
                 pill = "Growth / Stat / ML / DL", pill_class = "pill-blue"),
        kpi_card(vals$primary_metric, "Primary metric",
                 pill = "Lower is better", pill_class = "pill-blue"),
        kpi_card(vals$guardrail_metric, "Guardrail",
                 pill = "Lower is better", pill_class = "pill-blue"),
        kpi_card(champ_name, "Champion under conditions",
                 pill = "Governed", pill_class = "pill-green")
      ),
      open = FALSE
    ),

    # C. Current model ranking (15 models) ----------------------------------
    home_collapse(
      "Current model ranking (15 models)",
      "All current models ranked by median MASE, with median RMSSE guardrail and the evidence source for each.",
      tags$p(
        class = "shell-card-detail",
        "Median MASE is the primary score (lower is better); median RMSSE is the guardrail. \u201cGoverned tournament\u201d models were ranked in the bootstrap pairwise tournament; \u201cCandidate evaluation\u201d models (the deep-learning challengers) were scored on the same backtest in the closed V3.2D/V3.2E study. No challenger beat the champion or the top baseline band, so the champion is unchanged."
      ),
      universe_canonical_ranking_table_ui(canon),
      open = FALSE
    ),

    # D. Challenger evaluation at a glance (collapsed) ----------------------
    home_collapse(
      "Challenger evaluation at a glance",
      "Machine-learning and deep-learning challengers evaluated during the codebase review (V3.2D/V3.2E), compared to ETS Explicit on the same governed backtest.",
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-blue", "Backtest evaluation \u00b7 not production"),
        tags$p(class = "shell-card-detail", dv$status_message)
      ),
      card_grid(
        kpi_card(dv$champion_name, "Champion (unchanged)",
                 pill = paste0("MASE ", dv$champion_mase), pill_class = "pill-green"),
        kpi_card(dv$best_dl_challenger, "Best DL challenger",
                 pill = paste0("MASE ", dv$best_dl_mase), pill_class = "pill-blue"),
        kpi_card(dv$best_ml_challenger, "Best ML challenger",
                 pill = paste0("MASE ", dv$best_ml_mase), pill_class = "pill-blue"),
        kpi_card(dv$total_models, "Candidates evaluated",
                 pill = "Governed backtest", pill_class = "pill-blue"),
        kpi_card(dv$total_promoted, "Candidates promoted",
                 pill = "Champion unchanged", pill_class = "pill-green")
      ),
      open = FALSE
    ),

    # E. Challenger ranking (collapsed) - EVALUATION TABLE ------------------
    home_collapse(
      "Challenger evaluation detail (V3.2D/V3.2E)",
      "Every evaluated candidate ranked by governed median MASE, with the champion shown as the reference row.",
      tags$p(
        class = "shell-card-detail",
        "Median MASE is the primary score (lower is better), with median RMSSE as guardrail, computed on the same governed walk-forward backtest used for the champion. No challenger reached the champion or the top baseline band, so none was promoted."
      ),
      model_eval_ranking_table_ui(),
      open = FALSE
    ),

    # F. Evaluation summary & decision (collapsed) --------------------------
    home_collapse(
      "Evaluation summary & decision",
      "Per-model family, role, accuracy, guardrails and the documented decision for each evaluated candidate.",
      model_eval_summary_table_ui(),
      open = FALSE
    ),

    # G. Runtime & guardrails (collapsed) -----------------------------------
    home_collapse(
      "Runtime & guardrails",
      "Runtime viability, window completeness and non-negativity guardrail per challenger.",
      model_eval_runtime_table_ui(),
      open = FALSE
    ),

    # H. Legacy governed tournament evidence (13 models) --------------------
    home_collapse(
      "About the legacy 13-model tournament",
      "Why the head-to-head evidence below covers 13 models, not 15.",
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-amber", "Legacy governed evidence"),
        tags$p(
          class = "shell-card-detail",
          "The governed bootstrap pairwise tournament was run on 13 models (78 pairwise comparisons) and is a CLOSED artifact. It included an earlier high-risk neural model (FastNeuralAR_MLP) that has since been retired, and it predates the 3 deep-learning challengers, which were evaluated separately and never entered the pairwise bootstrap. The evidence tree, league view and head-to-head details below are preserved exactly as governed, and are LABELLED legacy. The current 15-model ranking above is the authoritative view of today's universe."
        )
      ),
      open = FALSE
    ),

    # H.1 Legacy Tournament Evidence Tree -----------------------------------
    home_collapse(
      "Legacy tournament evidence tree (13 models)",
      "A dendrogram-style grouping of the 13 governed tournament models by net head-to-head evidence, with ETS Explicit highlighted as the selected champion under conditions.",
      tournament_evidence_tree_ui(league),
      open = FALSE
    ),

    # H.2 Legacy Tournament League View -------------------------------------
    home_collapse(
      "Legacy tournament league view (13 models)",
      "League-style scoreboard for the 13 governed tournament models: better / worse / inconclusive, net evidence, primary metric and guardrail.",
      tags$p(
        class = "uni-fam-intro",
        "Each model plays every other model. \u201cBetter\u201d, \u201cWorse\u201d and \u201cInconclusive\u201d count the governed head-to-head outcomes; \u201cNet evidence\u201d is better minus worse. MASE and RMSSE are the governed error metrics (lower is better). Rows are ordered by net evidence, then MASE, for readability only. This reflects the 13-model governed tournament (legacy)."
      ),
      tournament_league_table_ui(league),
      open = FALSE
    ),

    # H.3 Legacy Head-to-head evidence details ------------------------------
    home_collapse(
      "Legacy head-to-head evidence details (78 comparisons)",
      "Technical pairwise comparisons behind the 13-model governed better / worse / inconclusive record.",
      tags$p(
        class = "shell-card-detail",
        "Each row is one model-vs-model comparison. The governed tournament has 78 rows because 13 models are compared against each other in a round-robin design. The table reports MASE deltas, bootstrap confidence intervals, p-values, adjusted p-values, practical threshold flags and comparison status. This is legacy governed evidence."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("tournament_pairwise_table")),
      open = FALSE
    ),

    # Footer note (single sentence, no policy table) ------------------------
    tags$p(
      class = "tess-foot-note",
      "This page reads governed Model Lab and candidate-evaluation artifacts and does not recompute metrics or change the champion decision. The current 15-model ranking aggregates already-computed medians; the 13-model pairwise tournament is preserved as labelled legacy evidence. None of the challengers was promoted."
    )
  )
}

# Compact "Champion at a glance" strip: a clean horizontal summary of the
# essential governed facts (NOT a wall of KPI cards).
champion_glance_ui <- function(vals) {
  item <- function(label, value, primary = FALSE) {
    tags$div(
      class = paste("champ-glance-item", if (primary) "is-primary" else ""),
      tags$div(class = "champ-glance-label", label),
      tags$div(class = "champ-glance-value", value)
    )
  }
  tags$div(
    class = "champ-glance",
    item("Champion", vals$champion, primary = TRUE),
    item("Decision", "Selected under conditions"),
    item("Median MASE", vals$mase_display),
    item("Median RMSSE", vals$rmsse_display),
    item("Pairwise support", paste0(vals$supported_better, " better / ", vals$supported_worse, " worse")),
    item("Confidence", vals$confidence)
  )
}

# Dual callout explaining the two distinct ideas Oscar found confusing:
# the GLOBAL governed champion (ETS Explicit) vs the most frequent
# SERIES-LEVEL leader (e.g. Theta). Pure HTML/CSS, no recompute.
champion_dual_ui <- function(vals, series_vals) {
  tags$div(
    class = "champ-dual",
    tags$div(
      class = "champ-dual-pane is-global",
      tags$span(class = "champ-dual-kicker", "Global governed champion"),
      tags$div(class = "champ-dual-model",
               tags$span(class = "champ-dual-star", "\u2605"), vals$champion),
      tags$p(class = "champ-dual-note",
             "Selected under conditions from aggregate tournament evidence: median MASE, RMSSE guardrail, pairwise support, eligibility, risk and governance conditions.")
    ),
    tags$div(class = "champ-dual-vs", "vs"),
    tags$div(
      class = "champ-dual-pane is-local",
      tags$span(class = "champ-dual-kicker", "Local series leaders"),
      tags$div(class = "champ-dual-model", series_vals$most_frequent_leader),
      tags$p(class = "champ-dual-note",
             "Models that win individual series locally (lowest median MASE for that series). Diagnostic only \u2014 local series leadership does not decide or replace the global governed champion.")
    )
  )
}

# Compact diagnostic stat strip for the series-level section.
champion_series_stat_ui <- function(series_vals) {
  item <- function(label, value, tone = "") {
    tags$div(
      class = paste("champ-glance-item", tone),
      tags$div(class = "champ-glance-label", label),
      tags$div(class = "champ-glance-value", value)
    )
  }
  tags$div(
    class = "champ-glance",
    item("Total series", series_vals$total_series),
    item("ETS Explicit leads", series_vals$ets_leads, "is-good"),
    item("Another model leads", series_vals$ets_not_leads, "is-warn"),
    item("Largest ETS gap", series_vals$largest_ets_gap)
  )
}

# "Series leadership map": a compact grid of one tile per series, grouped by
# the local series-level leader. ETS Explicit-led series are highlighted green.
# Pure HTML/CSS from governed entity x model scores; no recompute, no new score.
champion_series_leadership_map_ui <- function(evidence = champion_series_evidence(),
                                              champion = APP_CHAMPION) {
  if (!is.data.frame(evidence) || nrow(evidence) == 0) {
    return(tags$p(class = "shell-card-detail",
                  "Series-level diagnostic evidence is unavailable."))
  }
  num <- function(x, d = 2) {
    x <- suppressWarnings(as.numeric(x))
    if (length(x) != 1 || is.na(x)) "\u2014" else formatC(x, format = "f", digits = d)
  }
  leaders_list <- strsplit(as.character(evidence$series_level_leader), ";\\s*")
  primary <- vapply(seq_along(leaders_list), function(i) {
    ls <- leaders_list[[i]]
    if (champion %in% ls) champion else ls[[1]]
  }, character(1))

  uniq_leaders <- unique(primary)
  grp_size <- vapply(uniq_leaders, function(l) sum(primary == l), integer(1))
  is_ets_grp <- uniq_leaders == champion
  uniq_leaders <- uniq_leaders[order(!is_ets_grp, -grp_size, uniq_leaders)]

  groups <- lapply(uniq_leaders, function(l) {
    idx <- which(primary == l)
    is_ets <- identical(l, champion)
    tiles <- lapply(idx, function(i) {
      r <- evidence[i, ]
      tile_ets <- isTRUE(r$status == "ETS leads")
      ttl <- paste0(
        r$entity_key, " \u2014 local leader: ", r$series_level_leader,
        " (MASE ", num(r$leader_median_mase), ")",
        if (!is.na(r$ets_median_mase))
          paste0("; ETS Explicit MASE ", num(r$ets_median_mase),
                 ", rank ", r$ets_rank_by_mase) else ""
      )
      tags$div(
        class = paste("clead-tile", if (tile_ets) "is-ets" else ""),
        title = ttl,
        tags$span(class = "clead-tile-name", r$entity_key)
      )
    })
    tags$div(
      class = paste("clead-group", if (is_ets) "is-ets" else ""),
      tags$div(
        class = "clead-group-head",
        if (is_ets) tags$span(class = "clead-star", "\u2605"),
        tags$span(class = "clead-group-name", l),
        tags$span(class = "clead-group-count", length(idx))
      ),
      tags$div(class = "clead-tiles", tiles)
    )
  })

  tags$div(
    class = "clead",
    tags$div(
      class = "clead-legend",
      tags$span(class = "clead-leg-item",
                tags$span(class = "clead-leg-dot is-ets"), "ETS Explicit leads this series"),
      tags$span(class = "clead-leg-item",
                tags$span(class = "clead-leg-dot"), "Another model leads locally")
    ),
    tags$div(class = "clead-groups", groups)
  )
}

section_champion <- function() {
  vals <- champion_decision_values()
  series_vals <- champion_series_summary_values()

  panel(
    "champion",
    section_head(
      "Champion",
      "ETS Explicit is the selected champion under conditions. This page separates the global governed decision from series-level diagnostic evidence."
    ),

    # 0. What is the Champion (open, plain-language explainer) --------------
    home_collapse(
      "What is the Champion",
      "Read this first: what \u201cchampion\u201d means here, and what it does not mean.",
      info_list(
        info_row("The selected governed model",
                 paste0("The champion (", vals$champion, ") is the single model AEGIS selected to represent the current universe of 15 models. It is chosen on aggregate evidence across all series, not on any one series.")),
        info_row("Chosen on aggregate evidence",
                 "Selection combines the lowest median MASE, the RMSSE guardrail, pairwise support, champion eligibility, risk and governance conditions — there is no single composite score."),
        info_row("Selected under conditions",
                 "The champion is approved with documented conditions, not as an unconditional winner. It must be read together with the governance notes."),
        info_row("Not best in every series",
                 "A different model can have the lowest error on some individual series. That is expected and diagnostic only — it does not change or replace the governed champion.")
      ),
      open = TRUE
    ),

    # 1. Champion at a glance (open) ----------------------------------------
    home_collapse(
      "Champion at a glance",
      "The essential governed facts: champion, decision, primary metric, guardrail, pairwise support and confidence.",
      champion_glance_ui(vals),
      open = TRUE
    ),

    # 2. Why ETS Explicit was selected (open) -------------------------------
    home_collapse(
      "Why ETS Explicit was selected",
      "The global evidence behind the selected champion under conditions.",
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-green", "Selected under conditions"),
        tags$h3(class = "shell-card-title", "Global governed champion decision"),
        tags$p(
          class = "shell-card-detail",
          paste0(vals$champion, " was selected because it combines strong global evidence: the lowest official median MASE, strong pairwise support, acceptable guardrail behaviour, eligibility, and governance conditions. It is the selected champion under conditions \u2014 not an unconditional winner \u2014 and does not lead every individual series.")
        ),
        info_list(
          info_row("Primary accuracy evidence", paste0("Official median MASE = ", vals$mase_display, " (lowest in the tournament)")),
          info_row("Guardrail evidence", paste0("Official median RMSSE = ", vals$rmsse_display)),
          info_row("Pairwise support", paste0(vals$supported_better, " supported better / ",
                                              vals$supported_worse, " supported worse / ",
                                              vals$pairwise_total, " comparisons")),
          info_row("Decision confidence", vals$confidence),
          info_row("Eligibility & conditions", "Eligible for champion consideration and selected under governed conditions.")
        )
      ),
      open = TRUE
    ),

    # 3. Series-level diagnostic evidence (open) ----------------------------
    home_collapse(
      "Series-level diagnostic evidence",
      "Global champion vs local series leaders: where ETS Explicit leads and where another model wins individual series.",
      tags$h3(class = "section-block-title", "Global champion vs local series leaders"),
      tags$p(
        class = "uni-fam-intro",
        "Across 39 series, the local best-performing model may differ. This diagnostic view shows where ETS Explicit leads and where another model has the lower median MASE. It does not replace the governed champion decision."
      ),
      champion_dual_ui(vals, series_vals),
      tags$p(
        class = "shell-card-detail",
        "Theta leads more individual series, but ETS Explicit remains the global governed champion because the champion decision is based on aggregate tournament evidence: median MASE, RMSSE guardrail, pairwise support, eligibility, risk and governance conditions. Local series leadership is diagnostic only."
      ),
      champion_series_stat_ui(series_vals),
      tags$p(
        class = "shell-card-detail",
        "Series leadership map: one tile per series, grouped by the local series-level leader. Green tiles are series where ETS Explicit has the lowest median MASE."
      ),
      champion_series_leadership_map_ui(),
      tags$p(
        class = "shell-card-detail",
        "Scope: this diagnostic is computed over the governed tournament models. The three Deep Learning challengers (SMLP-TCN, NLIN-DLIN_FIXED, FNAR-V2) have median MASE of roughly 18–80, far above the local leaders (MASE ≈ 6–11), so they lead 0 individual series and do not change any leader shown here."
      ),
      open = TRUE
    ),

    # 4. Leadership count by model (collapsed) ------------------------------
    home_collapse(
      "Challenger evaluation (V3.2D/V3.2E)",
      "How the evaluated machine-learning and deep-learning challengers compare to ETS Explicit — and why none was promoted.",
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-green", "Champion unchanged"),
        tags$h3(class = "shell-card-title", "No challenger was promoted"),
        tags$p(
          class = "shell-card-detail",
          "The codebase review evaluated six challengers across statistical, machine-learning and deep-learning families on the same governed backtest. The best deep-learning challenger (SMLP-TCN) and the best machine-learning challenger (ENET-RIDGE) both land far above ETS Explicit on median MASE and do not reach even the top baseline band. No challenger was promoted, and no production forecast was replaced."
        ),
        info_list(
          info_row("Champion (reference)", paste0(vals$champion, " \u2014 median MASE ", vals$mase_display)),
          info_row("Best DL challenger", "SMLP-TCN \u2014 median MASE 18.783 (2.72x champion)"),
          info_row("Best ML challenger", "ENET-RIDGE \u2014 median MASE 19.331 (2.80x champion)"),
          info_row("Promotion outcome", "0 challengers promoted; ETS Explicit remains the selected champion under conditions."),
          info_row("Full detail", "The complete challenger ranking, evaluation summary and runtime/guardrails live on the Tournament page (backtest evaluation, not production forecasts).")
        )
      ),
      tags$p(
        class = "shell-card-detail",
        "Champion comparison: each challenger against ETS Explicit \u2014 ratio, gap and promotion eligibility."
      ),
      model_eval_champion_table_ui(),
      open = FALSE
    ),

    # 5. Leadership count by model (collapsed) ------------------------------
    home_collapse(
      "Leadership count by model",
      "How many individual series each model leads locally. This does not decide the global champion.",
      tags$p(
        class = "shell-card-detail",
        "Leadership count by model shows how many individual series each model leads locally (lowest median MASE). This chart counts local series leaders only. It does not decide the global champion. Theta may lead more individual series, while ETS Explicit remains the global governed champion because the champion decision is based on overall tournament evidence, pairwise support, guardrails, risk, eligibility and conditions."
      ),
      tags$div(class = "shell-card", plotly::plotlyOutput("champion_leadership_count_chart", height = "520px")),
      open = FALSE
    ),

    # 6. Series-level details (collapsed) -----------------------------------
    home_collapse(
      "Series-level details",
      "Detailed per-series comparison between the local leader and ETS Explicit.",
      tags$p(
        class = "shell-card-detail",
        "One row per series: the local series-level leader, the leader's median MASE, ETS Explicit's median MASE, the gap versus the local leader, and ETS Explicit's rank. Sorted to show local exceptions first."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("champion_series_evidence_table")),
      open = FALSE
    ),

    # Footer note -----------------------------------------------------------
    tags$p(
      class = "tess-foot-note",
      "This page reads governed Model Lab artifacts and does not recompute metrics or change the champion decision. Governance conditions, approved language and source lineage live on the Governance pages."
    )
  )
}

section_risks <- function() {
  vals <- risk_register_values()

  panel(
    "risks",
    section_head(
      "Risk Register",
      "Governed risk register from the Model Lab closure pack. These are the open risks and deferred models carried forward from the review. No risk is computed on this page."
    ),

    # A. About the Risk Register (collapsed by default) ---------------------
    home_collapse(
      "About the Risk Register",
      "What this governed, read-only register shows \u2014 and what it does not do.",
      tags$div(
        class = "home-prose",
        tags$p(
          "This page summarizes governed risks carried forward from the Model Lab ",
          "closure pack. It is a read-only register: risks are displayed for ",
          "transparency, auditability, and future follow-up. This page does not ",
          "add, remove, downgrade, recompute, or resolve any risk."
        )
      ),
      open = FALSE
    ),

    # B. Risk Register Overview (open) --- all summary cards together -------
    home_collapse(
      "Risk Register Overview",
      "Severity counts and carry-forward summary across the governed register.",
      card_grid(
        kpi_card(vals$total, "Registered risks",
                 pill = "Governed register", pill_class = "pill-blue"),
        kpi_card(vals$high, "High",
                 pill = "Highest severity", pill_class = "pill-red"),
        kpi_card(vals$medium, "Medium",
                 pill = "Carry-forward", pill_class = "pill-amber"),
        kpi_card(paste0(vals$advisory, " / ", vals$minor), "Advisory / Minor",
                 pill = "Non-blocking", pill_class = "pill-blue")
      ),
      card_grid(
        kpi_card(vals$carry_forward_dashboard, "Carried forward to dashboard",
                 pill = "Must stay visible", pill_class = "pill-green"),
        kpi_card(vals$carry_forward_future, "Carried forward to future work",
                 pill = "Future investigation", pill_class = "pill-blue"),
        kpi_card(vals$deferred, "Deferred models",
                 pill = "Not in final tournament", pill_class = "pill-amber"),
        shell_card("Governance", "Read-only register",
                   "Risks are read from the governed closure pack. This page does not add, remove, or downgrade any risk.")
      ),
      open = TRUE
    ),

    # C. Governed Risk Register table (open) --------------------------------
    home_collapse(
      "Governed Risk Register",
      "One row per governed risk, ordered by severity (high first).",
      tags$p(
        class = "shell-card-detail",
        "One row per governed risk, ordered by severity. Carry-forward flags show ",
        "which risks remain visible on the dashboard and which require future follow-up."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("risk_register_table")),
      open = TRUE
    ),

    # D. Deferred Models table (open; short table) --------------------------
    home_collapse(
      "Deferred Models",
      "Models deferred from the final tournament, documented as future-work candidates.",
      tags$p(
        class = "shell-card-detail",
        "Models deferred from the final tournament for runtime, dependency, or ",
        "environment reasons. These are documented as future-work candidates and are not rejected."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("risk_deferred_models_table")),
      open = TRUE
    ),

    # E. Conditional Decision Context (collapsed) ---------------------------
    home_collapse(
      "Conditional Decision Context",
      "How these risks map to the conditional champion decision.",
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-amber", "Carry-forward"),
        tags$h3(class = "shell-card-title", "Conditional decision context"),
        tags$p(
          class = "shell-card-detail",
          "These risks are the monitoring side of the conditional champion decision. They include the high-risk model under investigation, the deferred deep-learning models retained for future work, and the audit and sanity conditions carried into closure."
        )
      ),
      open = FALSE
    )
  )
}

section_audit <- function() {
  vals <- audit_summary_values()

  fmt_count <- function(x) if (is.na(x)) "\u2014" else as.character(as.integer(x))

  panel(
    "audit",
    section_head(
      "Audit Trail",
      "Independent governance audits that supported the conditional champion decision. These verdicts are read from governed artifacts and are not recomputed on this page."
    ),

    # A. About the Audit View (collapsed by default) ------------------------
    home_collapse(
      "About the Audit View",
      "What this governed, read-only audit view shows \u2014 and what it does not do.",
      tags$div(
        class = "home-prose",
        tags$p(
          paste0(
            "This page summarizes the governed audit trail for the forecasting ",
            "improvement work. It explains what was reviewed, what evidence was ",
            "carried forward, which findings remain visible, and what next steps ",
            "were identified. This page is read-only: it does not recompute models, ",
            "change governance decisions, or modify audit evidence."
          )
        )
      ),
      open = FALSE
    ),

    # B. Audit Trail Overview (open) --- all KPI cards together -------------
    home_collapse(
      "Audit Trail Overview",
      "Verdicts and finding counts across the independent governance audits.",
      card_grid(
        kpi_card(vals$a4_verdict, "Audit #4 verdict",
                 pill = "Challenger readiness", pill_class = "pill-green"),
        kpi_card(paste0(fmt_count(vals$a4_blockers), " / ", fmt_count(vals$a4_major),
                        " / ", fmt_count(vals$a4_minor), " / ", fmt_count(vals$a4_advisory)),
                 "Audit #4 blockers / major / minor / advisory",
                 pill = "Findings", pill_class = "pill-blue"),
        kpi_card(paste0(fmt_count(vals$sanity_models), " models \u00b7 ",
                        fmt_count(vals$sanity_pairwise), " pairwise"),
                 "Sanity review scope",
                 pill = "5.30A review", pill_class = "pill-blue"),
        kpi_card(paste0(fmt_count(vals$sanity_blockers), " blockers"),
                 "Sanity review result",
                 pill = if (isTRUE(vals$sanity_ready)) "Ready for 5.31" else "Pending",
                 pill_class = "pill-green")
      ),
      card_grid(
        kpi_card(vals$a5_verdict, "Audit #5 verdict",
                 pill = "Closure / handoff", pill_class = "pill-green"),
        kpi_card(fmt_count(vals$a5_total), "Audit #5 findings reviewed",
                 pill = "Independent audit", pill_class = "pill-blue"),
        kpi_card(fmt_count(vals$a5_pass), "Findings passed",
                 pill = "No action required", pill_class = "pill-green"),
        kpi_card(paste0(fmt_count(vals$a5_minor), " minor / ",
                        fmt_count(vals$a5_advisory), " advisory"),
                 "Non-blocking conditions",
                 pill = paste0(fmt_count(vals$a5_blocking_closure), " blocking"),
                 pill_class = "pill-amber")
      ),
      open = TRUE
    ),

    # C. Governance Timeline (open) -----------------------------------------
    home_collapse(
      "Governance Timeline",
      "Chronological view of key governance, review, and closure events carried forward from the audit trail.",
      tags$p(
        class = "shell-card-detail",
        "The conditional champion decision passed through three independent governance gates before the dashboard handoff. Each gate approved with conditions and zero blockers."
      ),
      card_grid(
        shell_card("Audit #4", "Challenger results readiness",
                   "Approved with conditions to proceed to the 5.30 tournament engine. Zero blockers; conditions carried forward."),
        shell_card("Sanity review (5.30A)", "Tournament sanity",
                   paste0(fmt_count(vals$sanity_models), " models and ",
                          fmt_count(vals$sanity_pairwise),
                          " pairwise comparisons reviewed. Zero blockers; ready for the 5.31 champion decision.")),
        shell_card("Audit #5", "Closure / dashboard handoff",
                   "Final independent audit. Approved with conditions; zero blockers and zero major findings across all required areas."),
        shell_card("Handoff", "Governed dashboard",
                   "All required dashboard sections covered with verified artifacts. No source outputs were modified by the audits.")
      ),
      open = TRUE
    ),

    # D. Audit Findings (open) ----------------------------------------------
    home_collapse(
      "Audit Findings",
      "Governed audit findings and conditions carried forward for transparency, follow-up, and closure tracking.",
      tags$p(
        class = "shell-card-detail",
        "One row per governed finding, ordered by severity. Closure and handoff flags show whether a finding blocks Model Lab closure or the dashboard handoff. There are no blocking findings."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("audit_findings_table")),
      open = TRUE
    ),

    # E. Governance Next Steps (collapsed) ----------------------------------
    home_collapse(
      "Governance Next Steps",
      "Next actions identified by the audit trail. These items guide follow-up work but are not recomputed on this page.",
      tags$p(
        class = "shell-card-detail",
        "Next steps recorded in the Model Lab closure pack, carried forward to the dashboard and future work."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("audit_next_steps_table")),
      open = FALSE
    ),

    # F. Independent Verification (collapsed) -------------------------------
    home_collapse(
      "Independent Verification",
      "Independent verification evidence and audit references used to support the governed closure status.",
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-green", "Approve with conditions"),
        tags$h3(class = "shell-card-title", "Independent verification"),
        tags$p(
          class = "shell-card-detail",
          "These audits verified closure-pack completeness, champion-decision consistency, risk carry-forward, and dashboard-handoff readiness. They are read-only checks: no models were rerun, no metrics recomputed, and no source outputs altered. The conditional, medium-confidence champion status must be surfaced on the dashboard rather than presented as an unconditional outcome."
        )
      ),
      open = FALSE
    )
  )
}

section_artifacts <- function() {
  vals <- artifact_catalog_values()

  download_card <- function(spec) {
    available <- artifact_is_available(spec$key)
    tags$div(
      class = "artifact-dl-card",
      tags$div(class = "artifact-dl-meta",
        tags$span(class = "artifact-dl-title", spec$label),
        tags$span(class = "artifact-dl-desc", spec$desc)
      ),
      if (available) {
        downloadButton(paste0("dl_", spec$key), "CSV",
                       class = "artifact-dl-btn", icon = shiny::icon("download"))
      } else {
        tags$span(class = "pill pill-amber", "Unavailable")
      }
    )
  }

  panel(
    "artifacts",
    section_head(
      "Source Artifacts",
      "The governed artifacts that feed this dashboard. Everything here is read-only: files are listed and served exactly as produced by the Model Lab, with no recomputation."
    ),

    # A. About the Artifacts Reference (collapsed) --------------------------
    home_collapse(
      "About the Artifacts Reference",
      "What this read-only reference lists \u2014 and what it does not change.",
      tags$div(
        class = "home-prose",
        tags$p(
          paste0(
            "This page lists the governed artifacts used by the dashboard. It ",
            "helps reviewers understand which files support the views, where the ",
            "evidence comes from, and whether each artifact is available for ",
            "dashboard consumption. This page is read-only and does not modify artifacts."
          )
        )
      ),
      open = FALSE
    ),

    # B. Artifact Overview (open) -------------------------------------------
    home_collapse(
      "Artifact Overview",
      "Registry totals and current availability across the governed artifacts.",
      card_grid(
        kpi_card(as.character(vals$total), "Governed artifacts",
                 pill = "Registry", pill_class = "pill-blue"),
        kpi_card(as.character(vals$available), "Available now",
                 pill = "Loaded", pill_class = "pill-green"),
        kpi_card(as.character(vals$categories), "Artifact categories",
                 pill = "Domains", pill_class = "pill-blue"),
        kpi_card(as.character(vals$roadmap), "Roadmap (not yet produced)",
                 pill = "Future work", pill_class = "pill-amber")
      ),
      open = TRUE
    ),

    # C. Governed Artifact Inventory (open) ---------------------------------
    home_collapse(
      "Governed Artifact Inventory",
      "Inventory of dashboard artifacts, their purpose, and their current availability status.",
      tags$h3(class = "section-block-title", "Governed downloads"),
      tags$p(
        class = "shell-card-detail",
        "Download the key governed CSVs directly. Each file is served verbatim from its closure-pack / tournament-engine path."
      ),
      tags$div(
        class = "artifact-dl-grid",
        lapply(ARTIFACT_DOWNLOAD_SPECS, download_card)
      ),
      tags$h3(class = "section-block-title", "Full artifact catalog"),
      tags$p(
        class = "shell-card-detail",
        "The complete governed artifact registry resolved by the data loader, with availability status and source path. Required artifacts are all present."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("artifact_catalog_table")),
      open = TRUE
    ),

    # D. Artifact Notes / Lineage / Evidence (collapsed) --------------------
    home_collapse(
      "Artifact Notes / Lineage / Evidence",
      "Data lineage and the read-only governance note for the dashboard artifacts.",
      tags$h3(class = "section-block-title", "Dashboard data lineage"),
      tags$p(
        class = "shell-card-detail",
        "Each dashboard section is backed by a governed artifact. This is the handoff manifest produced by the Model Lab closure pack."
      ),
      tags$div(class = "tess-table-wrap", DT::dataTableOutput("artifact_lineage_table")),
      tags$div(
        class = "shell-card",
        tags$span(class = "pill pill-green", "Read-only"),
        tags$h3(class = "shell-card-title", "Single source of truth"),
        tags$p(
          class = "shell-card-detail",
          "The dashboard never edits, recomputes, or regenerates these artifacts. Downloads return the exact governed files on disk, so what you export matches what the dashboard renders."
        )
      ),
      open = FALSE
    )
  )
}

section_methodology <- function() {
  meta <- methodology_dataset_values()
  panel(
    "methodology",
    section_head(
      "Methodology",
      "How data reaches the dashboard, and how the dashboard is organized. The dashboard only reads governed data \u2014 it never recomputes, edits, or writes back."
    ),

    # A. About the Methodology Reference (collapsed) ------------------------
    home_collapse(
      "About the Methodology Reference",
      "What this read-only reference documents \u2014 and what it does not compute.",
      tags$div(
        class = "home-prose",
        tags$p(
          paste0(
            "This page explains the methodology behind the dashboard views, ",
            "including how forecasting evidence, model comparison, intervals, TTL, ",
            "and governance references are organized. This page is read-only and ",
            "documents the approach; it does not compute forecasts, intervals, or ",
            "governance decisions."
          )
        )
      ),
      open = FALSE
    ),

    # B. Methodology Overview (open) ----------------------------------------
    home_collapse(
      "Methodology Overview",
      "How data reaches the dashboard, what it consumes, and how the views are organized.",
      tags$h3(class = "section-block-title", "Data pipeline"),
      card_grid(
        shell_card(
          "Stage 1 \u00b7 Ingestion", "TESSERACT v2 (SQL)",
          "Enterprise HDD-region series are queried from TesseractEarthDW (forecast_substrateBE_hdd_region) by the Python ingestion layer and exported to data/raw/."
        ),
        shell_card(
          "Stage 2 \u00b7 Processing", "Governed CSV contract",
          "Raw exports are validated and reshaped into the read-only data contract in data/processed/ and the Model Lab closure pack \u2014 no shifted dates, no imputations, no recompute."
        ),
        shell_card(
          "Stage 3 \u00b7 Consumption", "This dashboard",
          "The Shiny app loads the governed CSVs through a read-only loader at startup and renders them as-is. It is a consumer, not a producer, of data."
        )
      ),
      tags$h3(class = "section-block-title", "Current dataset"),
      card_grid(
        kpi_card(meta$entity_count, "Series (entities)"),
        kpi_card(meta$model_count, "Models"),
        kpi_card(meta$forecast_version, "Forecast version", pill = "Enterprise", pill_class = "pill-blue"),
        kpi_card(meta$run_date, "Data contract build")
      ),
      info_list(
        info_row("Actuals", paste0(meta$actual_rows, " rows  \u00b7  ", meta$actual_range)),
        info_row("Forecasts", paste0(meta$forecast_rows, " rows  \u00b7  ", meta$forecast_range)),
        info_row("Source table", "TesseractEarthDW.dbo.forecast_substrateBE_hdd_region (Scenario = Enterprise, ValueType = Forecast-Mean)"),
        info_row("Build note", meta$notes)
      ),
      tags$h3(class = "section-block-title", "What the dashboard consumes"),
      info_list(
        info_row("Forecast data", "forecasts.csv, actuals.csv, entities.csv, run_metadata.csv (data/processed)"),
        info_row("Backtest", "forecast_viewer_model_outputs.csv \u2014 per-model backtest used by the Viewer and Accuracy pages"),
        info_row("Model Lab", "closure pack: key results, model universe, champion summary, risk register, next steps"),
        info_row("Tournament", "preliminary standings, model scorecard, pairwise evidence"),
        info_row("Governance", "audit findings, sanity review, champion conditions and dashboard language")
      ),
      tags$h3(class = "section-block-title", "Dashboard structure"),
      info_list(
        info_row("Project", "Home, Overview \u2014 purpose, scope and the governed snapshot."),
        info_row("Forecasting", "Viewer, Accuracy, Forecast, TTL \u2014 series-level views and diagnostics."),
        info_row("Models", "Universe, Tournament, Champion \u2014 the model landscape and selection."),
        info_row("Governance", "Risks, Audit \u2014 the risk register and the audit trail."),
        info_row("Reference", "Artifacts, Methodology, Version \u2014 sources, data lineage and build metadata.")
      ),
      open = TRUE
    ),

    # C. Architecture Diagram (open) ----------------------------------------
    home_collapse(
      "Architecture Diagram",
      "Visual map of the ingestion \u2192 processing \u2192 consumption flow.",
      tags$div(
        class = "method-figure",
        tags$div(class = "method-figure-title", "Dashboard architecture diagram"),
        tags$img(
          src = "reference/aegis_v3_architecture_diagram_visual_v3.png",
          alt = "AEGIS V3 architecture diagram: upstream producer pipeline versus read-only Shiny consumer",
          style = "max-width: 100%; height: auto; border-radius: 8px; margin: 8px 0;"
        ),
        tags$div(
          class = "method-figure-text",
          paste0(
            "The upstream pipeline (Tesseract / SQL to ingestion to raw and processed ",
            "to Model Lab to forecast, interval and governance artifacts) produces and ",
            "governs all data. The Shiny dashboard is a read-only consumer and never ",
            "downloads, cleans, trains, recalculates, or writes artifacts. Dashed ",
            "components (daily refresh, AI/LLM layer) are V3 planned / optional."
          )
        ),
        tags$span(class = "method-figure-tag", "V3 architecture")
      ),
      open = TRUE
    ),

    # D. Project Documentation (collapsed placeholder) ----------------------
    home_collapse(
      "Project Documentation",
      "Full project write-up \u2014 scope, methodology and governance.",
      tags$div(
        class = "method-figure method-figure-doc",
        tags$div(class = "method-figure-icon", shiny::icon("file-lines")),
        tags$div(class = "method-figure-title", "Full project document"),
        tags$div(
          class = "method-figure-text",
          "This document is generated from the governed Markdown source and is provided as read-only project documentation."
        ),
        tags$div(
          class = "method-doc-actions",
          tags$a(
            class = "btn btn-default",
            href = "reference/aegis_v3_project_documentation.pdf",
            target = "_blank", rel = "noopener",
            shiny::icon("arrow-up-right-from-square"), " Open in new tab"
          ),
          tags$a(
            class = "btn btn-default",
            href = "reference/aegis_v3_project_documentation.pdf",
            download = "aegis_v3_project_documentation.pdf",
            shiny::icon("download"), " Download PDF"
          )
        ),
        tags$iframe(
          src = "reference/aegis_v3_project_documentation.pdf",
          class = "method-doc-frame",
          title = "AEGIS V3 Project Documentation",
          style = "width: 100%; height: 720px; border: 1px solid #c8d6c4; border-radius: 8px; margin-top: 10px;"
        ),
        tags$span(class = "method-figure-tag", "V3 documentation")
      ),
      open = FALSE
    ),

    # E. Methodology Notes (collapsed) --------------------------------------
    home_collapse(
      "Methodology Notes",
      "Read-only behavior and where to find the full machine-readable artifact list.",
      tags$p(
        class = "method-note",
        "The full machine-readable list \u2014 with availability, row counts and paths \u2014 lives on the Artifacts page."
      ),
      tags$span(class = "shell-card-tag", "Read-only \u00b7 single source of truth"),
      open = FALSE
    )
  )
}

section_version <- function() {
  meta <- methodology_dataset_values()
  reg  <- artifact_registry_view()
  cat  <- artifact_catalog_values(reg)
  rt   <- version_runtime_values()
  panel(
    "version",
    section_head("Version Info", "Build, data and runtime metadata for this governed release."),

    # A. About the Version Reference (collapsed) ----------------------------
    home_collapse(
      "About the Version Reference",
      "What this read-only reference confirms about the build you are viewing.",
      tags$div(
        class = "home-prose",
        tags$p(
          paste0(
            "This page summarizes dashboard version metadata, build context, ",
            "artifact freshness, and read-only status. It helps reviewers confirm ",
            "what version of the dashboard and governed artifacts they are viewing."
          )
        )
      ),
      open = FALSE
    ),

    # B. Version Overview (open) --------------------------------------------
    home_collapse(
      "Version Overview",
      "Dashboard and forecast version with current artifact availability.",
      card_grid(
        kpi_card(APP_VERSION, "App version"),
        kpi_card(meta$forecast_version, "Forecast version", pill = "Enterprise", pill_class = "pill-blue"),
        kpi_card(paste0(cat$available, " / ", cat$total), "Artifacts available")
      ),
      open = TRUE
    ),

    # C. Build / Runtime Metadata (open) ------------------------------------
    home_collapse(
      "Build / Runtime Metadata",
      "Governance build context and the current R runtime environment.",
      tags$h3(class = "section-block-title", "Build & governance"),
      info_list(
        info_row("Audit state", version_audit_label()),
        info_row("Policy", APP_POLICY),
        info_row("Champion", paste0(APP_CHAMPION, " \u2014 selected with conditions (confidence: ", APP_CHAMPION_CONFIDENCE, ")"))
      ),
      tags$h3(class = "section-block-title", "Runtime"),
      info_list(
        info_row("Artifacts loaded", paste0(cat$available, " available  \u00b7  ", cat$roadmap, " roadmap  \u00b7  ", cat$total, " registered")),
        info_row("Data loaded at", rt$loaded_at),
        info_row("R packages", paste0(rt$pkg_available, " / ", rt$pkg_total, " available",
                                      if (!identical(rt$pkg_missing, "none") && !identical(rt$pkg_missing, "\u2014"))
                                        paste0("   \u00b7   missing: ", rt$pkg_missing) else "")),
        info_row("Project root", rt$root)
      ),
      open = TRUE
    ),

    # D. Artifact Freshness / Last Update (open) ----------------------------
    home_collapse(
      "Artifact Freshness / Last Update",
      "The governed data snapshot currently loaded by the dashboard.",
      info_list(
        info_row("Forecast version", meta$forecast_version),
        info_row("Series \u00d7 models", paste0(meta$entity_count, " series  \u00b7  ", meta$model_count, " models")),
        info_row("Data contract build", meta$run_date),
        info_row("Coverage", paste0("Actuals ", meta$actual_range, "   \u00b7   Forecasts ", meta$forecast_range))
      ),
      open = TRUE
    ),

    # E. Version Notes (collapsed) ------------------------------------------
    home_collapse(
      "Version Notes",
      "Read-only status for this governed build.",
      tags$span(class = "shell-card-tag", "Read-only \u00b7 governed build"),
      open = FALSE
    )
  )
}

# ---------------------------------------------------------------------------
# Assemble all sections
# ---------------------------------------------------------------------------
app_sections <- function() {
  tags$div(
    class = "content-inner",
    section_home(),
    section_overview(),
    section_explorer(),
    section_accuracy(),
    section_forecast(),
    section_ttl(),
    section_universe(),
    section_tournament(),
    section_champion(),
    section_risks(),
    section_audit(),
    section_artifacts(),
    section_methodology(),
    section_version()
  )
}
