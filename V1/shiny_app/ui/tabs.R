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

section_home <- function() {
  panel(
    "home", active = TRUE,

    # A. Hero ----------------------------------------------------------------
    section_head(
      "TESSERACT v2 Forecast Improvement Platform",
      "A dashboard for reviewing a broader, evidence-based forecasting methodology for TESSERACT v2."
    ),

    # B. Why this dashboard exists (one clean prose card) --------------------
    tags$h3(class = "section-block-title", "Why this dashboard exists"),
    tags$div(
      class = "home-prose",
      tags$p(
        "TESSERACT v2 currently relies on a small set of basic forecasting models, ",
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
    ),

    # C. How the methodology works (simple 5-step flow) ----------------------
    tags$h3(class = "section-block-title", "How the methodology works"),
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
    ),

    # D. Model families compared --------------------------------------------
    tags$h3(class = "section-block-title", "Model families compared"),
    info_list(
      info_row("Baseline / reference", "The current forecasting approaches, kept as the comparison point."),
      info_row("Statistical models", "Classical time-series methods (for example ARIMA, ETS, and Theta-style models)."),
      info_row("Machine learning models", "Feature-based learners such as gradient boosting and regression approaches."),
      info_row("Deep learning candidate", "A neural forecasting candidate included to test more complex patterns.")
    ),
    tags$p(class = "shell-card-detail", style = "margin-top:10px;",
           "The full, detailed model list lives in MODELS / Universe."),

    # E. Where to go next ----------------------------------------------------
    tags$h3(class = "section-block-title", "Where to go next"),
    info_list(
      info_row("PROJECT / Overview", "Macro summary of the most important results (finalized later)."),
      info_row("MODELS / Universe", "The complete set of models considered in the review."),
      info_row("MODELS / Tournament", "Ranked, head-to-head tournament evidence."),
      info_row("MODELS / Champion", "The governed model recommendation and its conditions."),
      info_row("GOVERNANCE / Risks", "Open risks and models that were deferred."),
      info_row("FORECASTING / Explorer", "Visual forecast exploration (later block).")
    ),

    # F. Visual review note --------------------------------------------------
    tags$div(
      style = "margin-top:20px;",
      tags$div(
        class = "info-list",
        style = "padding:14px 18px;",
        tags$div(
          style = "display:flex; align-items:center; gap:10px;",
          tags$span(class = "pill pill-amber", "Visual review"),
          tags$span(
            style = "font-size:14px; color:#33455c;",
            "Please review this Home page visually before moving to the next Stage 07 block."
          )
        )
      )
    )
  )
}

section_overview <- function() {
  # Read-only governed reads (7.0E loader). Never recompute; safe fallbacks.
  cs <- home_champion_summary()
  kr <- home_key_results()
  uc <- universe_counts()

  champ      <- first_label(cs_value(cs, "selected_champion_model"), APP_CHAMPION)
  origin     <- cs_value(cs, "model_origin", "challenger")
  family     <- cs_value(cs, "model_family", "statistical")
  decision   <- first_label(cs_value(cs, "decision_type"), APP_CHAMPION_DECISION)
  confidence <- first_label(cs_value(cs, "decision_confidence"), APP_CHAMPION_CONFIDENCE)
  mase       <- fmt_metric(cs_value(cs, "official_median_mase"), 2)
  rmsse      <- fmt_metric(cs_value(cs, "official_median_rmsse"), 2)
  better     <- first_label(cs_value(cs, "supported_better_count"))
  worse      <- first_label(cs_value(cs, "supported_worse_count"))
  pairwise   <- first_label(kr_value(kr, "tournament_pairwise_comparisons"))
  conditions <- cs_value(cs, "conditions",
                         "Conditions are retained in the governed closure pack.")

  ni <- function(x) if (length(x) != 1 || is.na(x)) "\u2014" else as.character(x)

  panel(
    "overview",

    # A. Header --------------------------------------------------------------
    section_head(
      "Executive Overview",
      "A read-only macro summary of the TESSERACT v2 forecast improvement review."
    ),

    # B. Macro headline (real governed values) -------------------------------
    card_grid(
      kpi_card("Approved", "Governance state",
               pill = "With conditions", pill_class = "pill-amber"),
      kpi_card(champ, "Governed champion",
               pill = "Selected with conditions", pill_class = "pill-blue"),
      kpi_card(mase, "Median MASE \u00b7 primary metric",
               pill = "Lower is stronger", pill_class = "pill-blue"),
      kpi_card(rmsse, "Median RMSSE \u00b7 guardrail",
               pill = "Stability check", pill_class = "pill-blue")
    ),

    # C. What this overview shows --------------------------------------------
    tags$h3(class = "section-block-title", "What this overview shows"),
    tags$div(
      class = "home-prose",
      tags$p(
        "This page is a one-screen, read-only summary of the forecast ",
        "improvement review. Every figure below is read directly from the ",
        "governed closure pack \u2014 nothing here is recalculated, and no ",
        "forecasts or models are run by the dashboard."
      ),
      tags$p(
        "The review compared a broad universe of baseline and challenger ",
        "models on the same data, scored them with consistent accuracy ",
        "metrics, and selected a governed champion under explicit conditions."
      )
    ),

    # D. What the review concluded -------------------------------------------
    tags$h3(class = "section-block-title", "What the review concluded"),
    info_list(
      info_row("Champion decision", decision),
      info_row("Decision confidence", confidence),
      info_row("Champion model", paste0(champ, " (", origin, " \u00b7 ", family, ")")),
      info_row("Pairwise evidence",
               paste0(ni(better), " supported better \u00b7 ", ni(worse),
                      " worse \u00b7 across ", ni(pairwise), " comparisons"))
    ),

    # E. Model landscape at a glance (universe counts) -----------------------
    tags$h3(class = "section-block-title", "Model landscape at a glance"),
    info_list(
      info_row("Models reviewed", ni(uc$total)),
      info_row("Baselines / challengers",
               paste0(ni(uc$baselines), " / ", ni(uc$challengers))),
      info_row("Carried into the tournament", ni(uc$in_tournament)),
      info_row("Champion-eligible", ni(uc$champion_eligible)),
      info_row("Risk-flagged for follow-up", ni(uc$risk_flagged))
    ),

    # F. Conditions attached to the decision ---------------------------------
    tags$h3(class = "section-block-title", "Conditions attached to the decision"),
    tags$div(
      class = "home-prose",
      tags$p(conditions)
    ),

    # G. Where to go next ----------------------------------------------------
    tags$h3(class = "section-block-title", "Where to go next"),
    info_list(
      info_row("Home", "Why this dashboard exists and how the methodology works"),
      info_row("Model Universe", "The full list of governed baseline and challenger models"),
      info_row("Tournament", "** Pairwise standings and head-to-head evidence (planned)"),
      info_row("Accuracy", "** MASE / RMSSE detail by model and entity (planned)"),
      info_row("Risks", "** Model risk flags and follow-up notes (planned)"),
      info_row("TTL / Capacity", "** Forecast-to-capacity view (planned, source pending)")
    ),

    # H. Visual review note --------------------------------------------------
    tags$div(
      style = "margin-top:18px;",
      info_list(
        tags$li(
          tags$span(class = "pill pill-amber", "Visual review"),
          tags$span(class = "info-val",
                    "Please review this Executive Overview before we continue to the next Stage 07 block.")
        )
      )
    )
  )
}

section_explorer <- function() {
  # Stage 07 Forecasting Sidebar Correction: the Viewer page hosts the historical
  # Backtest Comparison ONLY. The forward production forecast was moved to its own
  # Forecast page (section_forecast()).
  #   Source: data/processed/forecast_viewer_model_outputs.csv (39 series).
  # The chart lives in a STATIC container (always in the DOM) to avoid blank-chart
  # regressions, and never renders before the user clicks Analyze Backtest.

  # ---- Backtest section inputs ----
  bt_series      <- fvp_series_choices()                 # 39 eligible series
  bt_default     <- if (length(bt_series)) bt_series[[1]] else NULL
  horizon_opts   <- fvp_horizon_choices()                # 5..30
  horizon_named  <- stats::setNames(as.character(horizon_opts),
                                    paste0(horizon_opts, " days"))
  horizon_unavail <- fvp_horizon_unavailable()           # 35, 45 (disabled)

  # Numbered "step" wrapper so the controls read as a guided workflow.
  fv_step <- function(num, title, control, hint = NULL, extra = NULL) {
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
    "explorer",
    section_head(
      "Forecast Viewer",
      "Historical multi-model Backtest Comparison. It renders only after you click Analyze Backtest. The forward production forecast now lives on the separate Forecast page."
    ),

    # =====================================================================
    # BACKTEST COMPARISON (full Stage 05H artifact)
    # =====================================================================
    tags$section(
      class = "fvx-section fvx-backtest",
      tags$div(
        class = "fvx-section-head",
        tags$span(class = "fvx-section-kicker", "Backtest"),
        tags$h3(class = "fvx-section-title", "Backtest Comparison"),
        tags$span(class = "pill pill-blue", "Historical \u00b7 multi-model")
      ),
      tags$p(
        class = "fvx-section-lead",
        "Actual known values versus multiple model forecasts over historical dates. ",
        "Source: ", tags$code("forecast_viewer_model_outputs.csv"),
        " (39 eligible series, 13 models, horizons 5\u201330)."
      ),

      tags$div(
        class = "fv-setup",
        tags$div(
          class = "fv-setup-panel",
          tags$div(class = "fv-setup-title", "Set up the backtest view"),

          fv_step(
            1, "Select series",
            selectInput("fvp_series", NULL, choices = bt_series,
                        selected = bt_default, width = "100%"),
            "Choose one of the 39 eligible multi-model series."
          ),
          fv_step(
            2, "Select models",
            uiOutput("fvp_model_groups"),
            "Tick one or more models. Grouped by family; \u2605 marks the selected challenger champion and \u26A0 marks higher-risk models (still selectable).",
            extra = uiOutput("fvp_model_count")
          ),
          fv_step(
            3, "Select horizon",
            tagList(
              radioButtons("fvp_horizon", NULL, choices = horizon_named,
                           selected = "5", inline = TRUE),
              tags$div(
                class = "fv-horizon-unavail",
                lapply(horizon_unavail, function(h)
                  tags$span(class = "fv-horizon-chip is-disabled",
                            title = "Not available in current artifact",
                            paste0(h, " days"))),
                tags$span(class = "fv-horizon-unavail-note",
                          "Not available in current artifact")
              )
            ),
            "The artifact covers 5\u201330 day horizons. 35 and 45 are shown disabled because they do not exist in the governed data."
          ),
          fv_step(
            4, "Select history window",
            selectInput("fvp_history", NULL,
                        choices = c("Last 90 days" = 90, "Last 180 days" = 180,
                                    "Full available window" = 0),
                        selected = 0, width = "100%"),
            "How much of the backtest date range to show."
          ),
          tags$div(
            class = "fv-step fv-step-action",
            tags$div(
              class = "fv-step-head",
              tags$span(class = "fv-step-num", "5"),
              tags$span(class = "fv-step-title", "Analyze")
            ),
            actionButton("fvp_go", "Analyze Backtest", class = "fv-analyze-btn"),
            tags$p(class = "fv-step-hint",
                   "The chart updates only after you click Analyze Backtest. Changing selectors does not auto-refresh.")
          ),
          tags$p(class = "fv-entity-note",
                 "Series, models and values are read directly from the governed Stage 05H full artifact.")
        ),

        tags$div(
          class = "fv-result",
          tags$div(
            class = "fv-step-head",
            tags$span(class = "fv-step-num", "6"),
            tags$span(class = "fv-step-title", "Backtest chart")
          ),
          tags$div(
            class = "fv-chart-wrap",
            highcharter::highchartOutput("fvp_chart", height = "520px")
          ),
          tags$div(
            class = "fv-notes-head",
            tags$span(class = "fv-step-num", "7"),
            tags$span(class = "fv-step-title", "Data notes")
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
        )
      )
    ),

    # Methodology note -------------------------------------------------------
    tags$p(
      class = "fv-method-note",
      "This page visualizes the governed Stage 05H backtest artifact only. It does not generate new forecasts, recalculate metrics, rerun tournaments, or change any champion. The forward production forecast is shown on the separate Forecast page."
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

  fv_step <- function(num, title, control, hint = NULL, extra = NULL) {
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
    "forecast",
    section_head(
      "Forecast",
      "Single-model Forward Forecast: actual history followed by the forward production forecast. It renders only after you click Analyze Forward Forecast."
    ),

    # =====================================================================
    # FORWARD FORECAST (production forecast + actual history)
    # =====================================================================
    tags$section(
      class = "fvx-section fvx-forward",
      tags$div(
        class = "fvx-section-head",
        tags$span(class = "fvx-section-kicker", "Forward"),
        tags$h3(class = "fvx-section-title", "Forward Forecast"),
        tags$span(class = "pill pill-teal", "Future \u00b7 single-model")
      ),
      tags$p(
        class = "fvx-section-lead",
        "Actual history up to the last actual date, then the forward production forecast after that point. ",
        "Sources: ", tags$code("actuals.csv"), " + ", tags$code("forecasts.csv"),
        " (45 series, one selected model per series)."
      ),

      tags$div(
        class = "fv-setup",
        tags$div(
          class = "fv-setup-panel",
          tags$div(class = "fv-setup-title", "Set up the forward view"),

          fv_step(
            1, "Select series",
            selectInput("fvf_series", NULL, choices = fw_series,
                        selected = if (length(fw_series)) fw_series[[1]] else NULL,
                        width = "100%"),
            "Choose one of the 45 production series."
          ),
          fv_step(
            2, "Forecast window",
            selectInput("fvf_window", NULL,
                        choices = c("Next 30 days" = 30, "Next 90 days" = 90,
                                    "Next 180 days" = 180,
                                    "Full forecast window" = 0),
                        selected = 90, width = "100%"),
            "How far into the future to draw the forward forecast line."
          ),
          fv_step(
            3, "Actual history window",
            selectInput("fvf_history", NULL,
                        choices = c("Last 90 actual days" = 90,
                                    "Last 180 actual days" = 180,
                                    "Last 365 actual days" = 365),
                        selected = 180, width = "100%"),
            "How much observed history to show before the forecast start boundary."
          ),
          tags$div(
            class = "fv-step fv-step-action",
            tags$div(
              class = "fv-step-head",
              tags$span(class = "fv-step-num", "4"),
              tags$span(class = "fv-step-title", "Analyze")
            ),
            actionButton("fvf_go", "Analyze Forward Forecast",
                         class = "fv-analyze-btn fv-analyze-btn-fwd"),
            tags$p(class = "fv-step-hint",
                   "The chart updates only after you click Analyze Forward Forecast. Changing selectors does not auto-refresh.")
          ),
          uiOutput("fvf_model_note"),
          tags$p(class = "fv-entity-note",
                 "Actual history and the forward production forecast are read directly from governed artifacts.")
        ),

        tags$div(
          class = "fv-result",
          tags$div(
            class = "fv-step-head",
            tags$span(class = "fv-step-num", "5"),
            tags$span(class = "fv-step-title", "Forward chart")
          ),
          tags$div(
            class = "fv-chart-wrap",
            highcharter::highchartOutput("fvf_chart", height = "520px")
          ),
          tags$div(
            class = "fv-notes-head",
            tags$span(class = "fv-step-num", "6"),
            tags$span(class = "fv-step-title", "Data notes")
          ),
          uiOutput("fvf_notes"),
          tags$div(
            class = "fv-warn-card fv-warn-card-fwd",
            tags$ul(
              class = "fv-warn-list",
              tags$li(tags$span(class = "pill pill-teal", "Forward"),
                      "This page uses the forward production forecast artifact. It is a single selected forecast per series, not a multi-model comparison."),
              tags$li(tags$span(class = "pill pill-slate", "Boundary"),
                      "The vertical \u201cForecast start\u201d line marks the last actual date; everything to its right is projected, not observed.")
            )
          )
        )
      )
    ),

    # Methodology note -------------------------------------------------------
    tags$p(
      class = "fv-method-note",
      "This page visualizes the governed forward production forecast only. It does not generate new forecasts, recalculate metrics, rerun tournaments, or change any champion."
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

  acc_step <- function(num, title, control, hint = NULL, extra = NULL) {
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
    "accuracy",
    section_head(
      "Accuracy",
      "Heatmap-first backtest accuracy diagnostics from the frozen Stage 05H model-comparison artifact. Standardized severity scores let different error measures be compared visually."
    ),

    # Summary cards (populated after Analyze Accuracy) ----------------------
    uiOutput("acc_summary_cards"),

    tags$section(
      class = "fvx-section acc-section",
      tags$div(
        class = "fvx-section-head",
        tags$span(class = "fvx-section-kicker", "Accuracy"),
        tags$h3(class = "fvx-section-title", "Standardized error heatmap"),
        tags$span(class = "pill pill-blue", "Backtest \u00b7 diagnostics")
      ),
      tags$p(
        class = "fvx-section-lead",
        "Per series \u00d7 model error severity at a chosen horizon. ",
        "Source: ", tags$code("forecast_viewer_model_outputs.csv"),
        " (39 series, 13 models, horizons 5\u201330). Red cells = higher error; ",
        "blue cells = lower error / more stable."
      ),

      tags$div(
        class = "fv-setup",
        tags$div(
          class = "fv-setup-panel",
          tags$div(class = "fv-setup-title", "Set up the accuracy view"),

          acc_step(
            1, "Select horizon",
            radioButtons("acc_horizon", NULL, choices = horizon_named,
                         selected = "30", inline = TRUE),
            "Backtest horizon (days) used to compute the diagnostics."
          ),
          acc_step(
            2, "Select metric",
            selectInput("acc_metric", NULL, choices = ACC_METRICS,
                        selected = "MAE", width = "100%"),
            "Drives both the heatmap color (standardized) and the headline severity ranking. All metrics: lower is better."
          ),
          acc_step(
            3, "Select models",
            selectizeInput("acc_models", NULL,
                           choices = c("All models" = "__ALL__", acc_models),
                           selected = "__ALL__", multiple = TRUE, width = "100%",
                           options = list(placeholder = "All models")),
            "Keep All models or restrict to one or several."
          ),
          acc_step(
            4, "Filter series",
            selectizeInput("acc_series", NULL, choices = acc_series,
                           selected = NULL, multiple = TRUE, width = "100%",
                           options = list(placeholder = "All eligible series")),
            "Leave empty to include every eligible series."
          ),
          acc_step(
            5, "Rows shown",
            selectInput("acc_topn", NULL,
                        choices = c("Top 10" = 10, "Top 20" = 20, "All (39)" = 39),
                        selected = 20, width = "100%"),
            "Heatmap keeps this many series, ranked worst-first by the selected metric."
          ),
          tags$div(
            class = "fv-step fv-step-action",
            tags$div(
              class = "fv-step-head",
              tags$span(class = "fv-step-num", "6"),
              tags$span(class = "fv-step-title", "Analyze")
            ),
            actionButton("acc_go", "Analyze Accuracy", class = "fv-analyze-btn"),
            tags$p(class = "fv-step-hint",
                   "The heatmap and table update only after you click Analyze Accuracy. Changing selectors does not auto-refresh.")
          ),
          tags$p(class = "fv-entity-note",
                 "All values are computed in memory from the governed Stage 05H backtest artifact. Nothing is written back.")
        ),

        tags$div(
          class = "fv-result",
          tags$div(
            class = "fv-step-head",
            tags$span(class = "fv-step-num", "7"),
            tags$span(class = "fv-step-title", "Severity heatmap (standardized)")
          ),
          tags$div(
            class = "fv-chart-wrap",
            plotly::plotlyOutput("acc_heatmap", height = "560px")
          ),
          tags$div(
            class = "fv-notes-head",
            tags$span(class = "fv-step-num", "8"),
            tags$span(class = "fv-step-title", "Metric values (raw + standardized)")
          ),
          tags$div(class = "tess-table-wrap",
                   DT::dataTableOutput("acc_table")),
          tags$div(
            class = "fv-warn-card",
            tags$ul(
              class = "fv-warn-list",
              tags$li(tags$span(class = "pill pill-amber", "Diagnostics"),
                      "These are dashboard diagnostics derived from the frozen Stage 05H backtest output. They are not official governance metrics and do not change champion selection."),
              tags$li(tags$span(class = "pill pill-slate", "Standardized"),
                      "Heatmap color uses a robust standardized severity score (median / IQR) so different measures are visually comparable. The table shows raw values."),
              tags$li(tags$span(class = "pill pill-blue", "Backtest only"),
                      "Accuracy uses historical backtest data only (never the forward forecast / actuals files). It does not generate forecasts.")
            )
          )
        )
      ),

      tags$p(
        class = "fv-method-note",
        "This page visualizes the governed Stage 05H backtest artifact only. It does not generate new forecasts, recompute official metrics, rerun tournaments, or change any selected champion under conditions. MASE / RMSSE are intentionally excluded here because no governed scale baseline is bundled with this artifact."
      )
    )
  )
}

section_ttl <- function() {
  # --- Check governed TTL artifact availability (read-only, no compute) ----
  reg <- tryCatch(get_artifact_status(), error = function(e) NULL)
  ttl_status <- "roadmap"
  if (is.data.frame(reg) && "key" %in% names(reg) && "status" %in% names(reg)) {
    row <- reg[reg$key == "ttl_capacity", , drop = FALSE]
    if (nrow(row) >= 1) ttl_status <- as.character(row$status[1])
  }
  source_available <- !is.na(ttl_status) &&
    !ttl_status %in% c("roadmap", "roadmap_missing", "optional_missing", "required_missing")

  # A small checklist row: label + status pill. Items we still have to build
  # are flagged with "**" so they are easy to spot as future work.
  ttl_check <- function(label, state, pill_class = "pill-amber") {
    tags$li(
      tags$span(class = "info-key", label),
      tags$span(class = "info-val",
                tags$span(class = paste("pill", pill_class), state))
    )
  }

  panel(
    "ttl",

    # A. Header --------------------------------------------------------------
    section_head(
      "TTL / Capacity View",
      "Planned view for connecting forecast outcomes to capacity timing, risk, and operational readiness."
    ),

    # B. Main status callout -------------------------------------------------
    tags$div(
      class = "ttl-callout",
      tags$span(class = "pill pill-amber", "Planned section"),
      tags$h3(class = "ttl-callout-title",
              "** TTL source not available yet \u2014 planned for capacity view **"),
      tags$p(
        class = "ttl-callout-text",
        "This page is reserved for a governed Months-to-Live / capacity artifact. ",
        "Until that artifact is available, the dashboard does not calculate or infer ",
        "TTL, and it does not derive any capacity health score from unrelated data."
      )
    ),

    # C. Capacity view readiness barometer -----------------------------------
    tags$h3(class = "section-block-title", "Capacity view readiness"),
    tags$p(class = "shell-card-detail", style = "margin:-6px 0 12px;",
           "This meter shows how ready the page is to display TTL \u2014 it is ",
           tags$strong("data/source readiness"),
           ", not capacity health and not operational health."),
    tags$div(
      class = "ttl-barometer",
      tags$div(
        class = "ttl-barometer-track",
        tags$div(class = "ttl-zone ttl-zone-missing", "Source missing"),
        tags$div(class = "ttl-zone ttl-zone-connected", "Source connected"),
        tags$div(class = "ttl-zone ttl-zone-ready", "Ready for interpretation"),
        # Marker pinned to the first zone while the source is missing.
        tags$div(
          class = if (source_available) "ttl-marker ttl-marker-connected" else "ttl-marker ttl-marker-missing",
          tags$span(class = "ttl-marker-dot"),
          tags$span(class = "ttl-marker-label",
                    if (source_available) "Source detected" else "Source missing / pending")
        )
      ),
      tags$div(
        class = "ttl-barometer-foot",
        tags$span(class = "ttl-readiness-state",
                  if (source_available) "State: source detected (preview only)" else "State: source unavailable"),
        tags$span(class = "ttl-readiness-score",
                  if (source_available) "Readiness: pending interpretation" else "Readiness: 0% \u00b7 pending source")
      )
    ),

    # D. Future interpretation cards ----------------------------------------
    tags$h3(class = "section-block-title", "What this page will show"),
    card_grid(
      shell_card("** Future view", "Time-to-impact",
                 "How many days or months remain before a capacity threshold is reached, once a governed TTL source exists."),
      shell_card("** Future view", "Capacity pressure",
                 "Forecast-driven resource pressure by entity, forest, region, or SKU \u2014 shown only if those fields exist in the governed source."),
      shell_card("** Future view", "Forecast-to-capacity bridge",
                 "The link between forecast outputs and capacity planning decisions, connecting the Model Lab to operational readiness.")
    ),

    # E. Required source checklist ------------------------------------------
    tags$h3(class = "section-block-title", "Required source checklist"),
    tags$ul(
      class = "info-list",
      ttl_check("** Governed TTL artifact",
                if (source_available) "Detected (preview)" else "Missing / roadmap",
                if (source_available) "pill-green" else "pill-amber"),
      ttl_check("** Entity mapping", "Pending source"),
      ttl_check("** Capacity threshold definition", "Pending source"),
      ttl_check("** Forecast linkage", "Pending source"),
      ttl_check("Visualization readiness", "Shell ready", "pill-green")
    ),

    # F. Methodology note ----------------------------------------------------
    tags$div(
      class = "ttl-method-note",
      tags$span(class = "pill pill-blue", "Methodology"),
      tags$span(
        "TTL will only be displayed when a governed source artifact exists. ",
        "This dashboard will not estimate TTL from unrelated data or create proxy capacity health scores."
      )
    ),

    # G. Visual review note --------------------------------------------------
    tags$div(
      style = "margin-top:18px;",
      tags$div(
        class = "info-list", style = "padding:14px 18px;",
        tags$div(
          style = "display:flex; align-items:center; gap:10px;",
          tags$span(class = "pill pill-amber", "Visual review"),
          tags$span(style = "font-size:14px; color:#33455c;",
                    "Please review this TTL placeholder visually before moving to the next Stage 07 block.")
        )
      )
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

section_universe <- function() {
  # --- Governed data binding (read-only, from the 7.0E loader cache) ---
  uni <- universe_normalized()
  cnt <- universe_counts(uni)
  champ <- first_label(universe_champion_name(uni), APP_CHAMPION)

  n <- function(x) if (is.null(x) || is.na(x)) "\u2014" else as.character(x)

  panel(
    "universe",

    # A. Header --------------------------------------------------------------
    section_head(
      "Model Universe",
      "Final baseline, challenger, deferred, and champion-eligible model set for the governed Model Lab."
    ),

    # B. Summary cards (counts read straight from the artifact) --------------
    card_grid(
      kpi_card(n(cnt$total), "Total models", pill = "Governed universe", pill_class = "pill-blue"),
      kpi_card(n(cnt$baselines), "Baselines", pill = "Reference families", pill_class = "pill-blue"),
      kpi_card(n(cnt$challengers), "Challengers", pill = "Candidate models", pill_class = "pill-amber"),
      kpi_card(n(cnt$in_tournament), "Included in tournament", pill = "Ranked", pill_class = "pill-green")
    ),
    card_grid(
      kpi_card(n(cnt$deferred), "Deferred models", pill = "Out of ranking", pill_class = "pill-amber"),
      kpi_card(n(cnt$champion_eligible), "Champion eligible", pill = "Governed eligibility", pill_class = "pill-blue"),
      kpi_card(n(cnt$selected_champion), "Selected champion (with conditions)", pill = champ, pill_class = "pill-green"),
      kpi_card(n(cnt$risk_flagged), "Models with risk flags", pill = "Review", pill_class = "pill-amber")
    ),

    # C. Main model universe table -------------------------------------------
    tags$h3(class = "section-block-title", "Governed model universe"),
    tags$div(class = "tess-table-wrap", universe_table_widget(uni)),

    # D. Governed interpretation notes ---------------------------------------
    tags$h3(class = "section-block-title", "How to read this universe"),
    info_list(
      info_row("Baselines",
               "Current and reference model families that anchor the comparison; they are not improvement candidates."),
      info_row("Challengers",
               "Candidate improvement models evaluated against the baselines inside the governed tournament."),
      info_row("Included in tournament",
               "Models that entered the governed rolling-origin ranking; deferred models did not."),
      info_row("Deferred models",
               "Excluded from the tournament ranking due to runtime or dependency constraints \u2014 not a quality verdict."),
      info_row("Champion eligibility",
               "A governed eligibility flag indicating a model could be considered for champion selection; it does not by itself decide the champion."),
      info_row("Selected champion (with conditions)",
               paste0("The governed champion selection (", champ,
                      ") is conditional: it is approved with conditions and must be read alongside the documented risks and governance notes."))
    )
  )
}

section_tournament <- function() {
  panel(
    "tournament",
    section_head("Tournament Standings",
                 "Model standings ranked by official MASE / RMSSE (placeholder)."),
    card_grid(
      shell_card("Protocol", "Rolling-origin", "Backtesting protocol used during the governed review."),
      shell_card("Ranking", "Pending binding", "Standings table will be bound to governed tournament metrics."),
      shell_card("Metric policy", "MASE primary", "MASE primary, RMSSE guardrail per benchmark semantics.")
    )
  )
}

section_champion <- function() {
  panel(
    "champion",
    section_head("Champion Decision", "Governed champion decision (read-only display)."),
    card_grid(
      shell_card("Decision", APP_CHAMPION,
                 "Selected champion under governance conditions; not an unconditional selection."),
      shell_card("Confidence", APP_CHAMPION_CONFIDENCE,
                 "Decision confidence recorded by governance."),
      shell_card("Policy", "No recompute",
                 "Champion is displayed from governed artifacts; nothing is recalculated here.")
    ),
    tags$div(style = "margin-top:18px;", controls_preview())
  )
}

section_comparison <- function() {
  panel(
    "comparison",
    section_head("Model Comparison Evidence",
                 "Model-vs-model scorecard and pairwise statistical support (placeholder)."),
    card_grid(
      shell_card("Scorecard", "Pending binding", "Unified model scorecard will be bound to governed artifacts."),
      shell_card("Pairwise", "Head-to-head", "Pairwise deltas with bootstrap CI and adjusted p-values."),
      shell_card("Support", "Significance", "Comparison status: supported difference vs inconclusive.")
    )
  )
}

section_conditions <- function() {
  panel(
    "conditions",
    section_head("Champion Conditions",
                 "Conditions attached to the governed champion decision."),
    info_list(
      info_row("Condition 1", "Monitor accuracy on the next governed evaluation cycle."),
      info_row("Condition 2", "Re-confirm seasonal stability before promotion."),
      info_row("Condition 3", "Keep fallback model available for contingency."),
      info_row("Status", "Tracked under governance \u2014 placeholders pending artifact binding.")
    )
  )
}

section_risks <- function() {
  panel(
    "risks",
    section_head("Risk Register",
                 "Open risks and deferred models tracked for the review (placeholder)."),
    info_list(
      info_row("FastNeuralAR_MLP", "High-risk MASE/RMSSE behaviour \u2014 not champion eligible."),
      info_row("NBEATS", "Deferred \u2014 runtime impractical for the MVP."),
      info_row("NHITS", "Deferred \u2014 dependency blocked (Python 3.14)."),
      info_row("FixedGrowth_6", "Manual review condition due to risk status."),
      info_row("Status", "Placeholders pending artifact binding.")
    )
  )
}

section_audit <- function() {
  panel(
    "audit",
    section_head("Audit Trail",
                 "Chronological record of governed checkpoints (read-only)."),
    info_list(
      info_row("Checkpoint", APP_AUDIT_STATE),
      info_row("Stage", APP_STAGE),
      info_row("Version", APP_VERSION),
      info_row("Policy", APP_POLICY)
    )
  )
}

section_artifacts <- function() {
  panel(
    "artifacts",
    section_head("Source Artifacts",
                 "Governed artifacts that feed the dashboard (placeholder)."),
    info_list(
      info_row("model_lab closure pack", "Key results, model universe, champion summary, risk register."),
      info_row("tournament_engine", "Standings, scorecard and pairwise evidence."),
      info_row("challenger_metrics", "Diagnostic metrics by model."),
      info_row("config", "Governed YAML policies (read-only).")
    )
  )
}

section_methodology <- function() {
  panel(
    "methodology",
    section_head("Methodology",
                 "Benchmark semantics and metric policy (read-only)."),
    card_grid(
      shell_card("Primary metric", "MASE", "Absolute benchmark score; cohort-stable, naive lag-1 denominator on training."),
      shell_card("Guardrail", "RMSSE", "Severe-degradation guardrail alongside the primary metric."),
      shell_card("Aggregation", "Median of medians", "Robust window \u2192 entity \u2192 global aggregation."),
      shell_card("Significance", "Bootstrap / sign-test", "Pairwise support with adjusted p-values.")
    )
  )
}

section_downloads <- function() {
  panel(
    "downloads",
    section_head("Downloads Center",
                 "General and per-section artifact downloads \u2014 pending a governed export."),
    card_grid(
      planned_card("Downloads", "Download handlers will be wired to governed closure-pack artifacts in a later block.")
    )
  )
}

section_version <- function() {
  panel(
    "version",
    section_head("Version Info", "Build and policy metadata."),
    info_list(
      info_row("Version", APP_VERSION),
      info_row("Stage", APP_STAGE),
      info_row("Policy", APP_POLICY),
      info_row("Audit state", "approved to Stage 07")
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
    section_comparison(),
    section_conditions(),
    section_risks(),
    section_audit(),
    section_artifacts(),
    section_methodology(),
    section_downloads(),
    section_version()
  )
}

