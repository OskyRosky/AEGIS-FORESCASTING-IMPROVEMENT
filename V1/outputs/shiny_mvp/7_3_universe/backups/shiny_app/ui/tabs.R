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
section_home <- function() {
  # --- Governed data binding (read-only, from the 7.0E loader cache) ---
  kr <- home_key_results()
  cs <- home_champion_summary()

  champion_model <- first_label(
    cs_value(cs, "selected_champion_model"),
    kr_value(kr, "selected_champion"),
    APP_CHAMPION
  )
  decision_status <- first_label(
    cs_value(cs, "decision_type"),
    kr_value(kr, "champion_decision"),
    APP_CHAMPION_DECISION
  )
  confidence <- first_label(
    cs_value(cs, "decision_confidence"),
    APP_CHAMPION_CONFIDENCE
  )
  confidence_label <- paste0(toupper(substring(confidence, 1, 1)),
                             substring(confidence, 2), " confidence")

  median_mase  <- fmt_metric(cs_value(cs, "official_median_mase"))
  median_rmsse <- fmt_metric(cs_value(cs, "official_median_rmsse"))
  better_count <- first_label(cs_value(cs, "supported_better_count"), fallback = "\u2014")
  worse_count  <- first_label(cs_value(cs, "supported_worse_count"),  fallback = "\u2014")

  universe_n    <- first_label(kr_value(kr, "tournament_models"), fallback = "\u2014")
  baseline_n    <- first_label(kr_value(kr, "final_baseline_models"), fallback = "\u2014")
  challenger_n  <- first_label(kr_value(kr, "final_challenger_models"), fallback = "\u2014")
  pairwise_n    <- first_label(kr_value(kr, "tournament_pairwise_comparisons"), fallback = "\u2014")

  panel(
    "home", active = TRUE,

    # A. Hero ----------------------------------------------------------------
    section_head(
      "TESSERACT v2 Forecast Improvement Platform",
      "Read-only governed dashboard for reviewing forecast improvement evidence, model lab outcomes, champion conditions, and governance artifacts."
    ),
    card_grid(
      kpi_card(APP_STAGE, "Build stage", pill = "Active", pill_class = "pill-green"),
      kpi_card("Approved with conditions", "Governance state", pill = "Governed", pill_class = "pill-amber"),
      kpi_card("Read-only", "Operating mode", pill = "No recompute", pill_class = "pill-blue"),
      kpi_card(APP_VERSION, "Active version", pill = "Model Lab closed", pill_class = "pill-blue")
    ),

    # B. Purpose cards -------------------------------------------------------
    tags$h3(class = "section-block-title", "Why this dashboard exists"),
    card_grid(
      shell_card("Governed Review", "Audit-ready evidence",
                 "Presents governed Model Lab outputs and audit-ready evidence exactly as produced \u2014 nothing is regenerated in the dashboard."),
      shell_card("Goal #3 Alignment", "Codebase ownership",
                 "Supports deeper ownership of the TESSERACT v2 forecast generation codebase and documents improvement opportunities in accuracy, maintainability, automation, and process governance."),
      shell_card("Read-only Evidence Layer", "No recompute",
                 "Reads existing artifacts only: no recompute, no model rerun, and no forecast generation. The dashboard cannot alter any governed decision."),
      shell_card("Next Review Path", "Suggested route",
                 "Recommended path: Overview \u2192 Universe \u2192 Tournament \u2192 Champion \u2192 Risks \u2192 Audit \u2192 Accuracy \u2192 Explorer.")
    ),

    # C. Governed snapshot ---------------------------------------------------
    tags$h3(class = "section-block-title", "Governed snapshot"),
    card_grid(
      kpi_card(champion_model, "Selected champion (with conditions)",
               pill = "Conditions apply", pill_class = "pill-amber"),
      kpi_card("Selected with conditions", "Governed champion decision",
               pill = "Evidence-backed", pill_class = "pill-green"),
      kpi_card(confidence_label, "Decision confidence",
               pill = "Governed", pill_class = "pill-blue"),
      kpi_card("MASE / RMSSE", "Primary / guardrail metric",
               pill = "Benchmark semantics", pill_class = "pill-blue")
    ),
    tags$div(
      style = "margin-top:16px;",
      info_list(
        info_row("Champion decision", "Selected champion with conditions (governed)"),
        info_row("Primary metric (MASE)", paste0("Median ", median_mase, " \u2014 lower is stronger")),
        info_row("Guardrail metric (RMSSE)", paste0("Median ", median_rmsse)),
        info_row("Supported comparisons", paste0(better_count, " supported better \u00b7 ", worse_count, " supported worse")),
        info_row("Model universe", paste0(universe_n, " tournament models (", baseline_n, " baseline + ", challenger_n, " challenger)")),
        info_row("Pairwise evidence", paste0(pairwise_n, " governed pairwise comparisons"))
      )
    ),
    tags$p(
      class = "shell-card-detail", style = "margin-top:10px;",
      "This is an evidence-backed recommendation, not an unconditional ranking. Champion conditions and full evidence are in the Models and Governance sections."
    ),

    # D. Dashboard map -------------------------------------------------------
    tags$h3(class = "section-block-title", "Dashboard map"),
    card_grid(
      shell_card("PROJECT", "Purpose & overview",
                 "Dashboard purpose (this page) and the executive overview of the review."),
      shell_card("FORECASTING", "Explorer / Accuracy / TTL",
                 "Forecast exploration, accuracy evidence, and the TTL capacity view (roadmap)."),
      shell_card("MODELS", "Universe / Tournament / Champion / Comparison",
                 "Model universe, tournament standings, champion decision, and comparison evidence."),
      shell_card("GOVERNANCE", "Conditions / Risks / Audit",
                 "Champion conditions, risk register, and the audit trail."),
      shell_card("REFERENCE", "Artifacts / Methodology / Downloads / Version",
                 "Source artifacts, methodology, downloads, and version information.")
    ),

    # E. Visual inspection note ---------------------------------------------
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
            "Please review this dashboard visually before moving to the next Stage 07 block."
          )
        )
      )
    )
  )
}

section_overview <- function() {
  panel(
    "overview",
    section_head("Executive Overview",
                 "Headline status of the forecast improvement review (read-only)."),
    card_grid(
      kpi_card("Approved", "Governance state", pill = "Stage 07", pill_class = "pill-green"),
      kpi_card(APP_CHAMPION, "Governed champion", pill = "Conditions apply", pill_class = "pill-amber"),
      kpi_card(APP_CHAMPION_CONFIDENCE, "Decision confidence", pill = "Governed", pill_class = "pill-blue"),
      kpi_card(APP_VERSION, "Active version", pill = "Read-only", pill_class = "pill-blue")
    ),
    tags$div(
      style = "margin-top:18px;",
      shell_card("Summary", "Review status",
                 "All headline values shown here are placeholders and will be bound to governed artifacts in a later block.")
    )
  )
}

section_explorer <- function() {
  panel(
    "explorer",
    section_head("Forecast Explorer",
                 "Actual vs baseline vs challenger forecast curves (placeholder \u2014 charting block)."),
    card_grid(
      shell_card("Series", "Actual vs forecast", "Per-entity actual and forecast curves will be charted here."),
      shell_card("Filters", "Entity / model / window", "Read-only selectors for entity, model and backtest window."),
      shell_card("Source", "Governed forecasts", "Bound to processed forecasts/actuals in a later block.")
    ),
    tags$div(style = "margin-top:18px;", controls_preview())
  )
}

section_accuracy <- function() {
  panel(
    "accuracy",
    section_head("Accuracy Overview",
                 "Official MASE / RMSSE plus diagnostic metrics by model (placeholder)."),
    card_grid(
      shell_card("Primary", "MASE / RMSSE", "Absolute benchmark metric (MASE) with RMSSE guardrail."),
      shell_card("Diagnostics", "wMAPE / SMAPE / bias", "Supporting diagnostics \u2014 never the primary score."),
      shell_card("Granularity", "Model / entity", "Errors broken down by model and entity in a later block.")
    )
  )
}

section_ttl <- function() {
  panel(
    "ttl",
    section_head("TTL / Capacity View",
                 "Months-to-Live / capacity perspective \u2014 pending a governed artifact."),
    card_grid(
      planned_card("TTL view", "No governed TTL/capacity artifact exists yet; this section stays Planned until one is produced.")
    )
  )
}

section_universe <- function() {
  panel(
    "universe",
    section_head("Model Universe",
                 "Baseline, challenger and deferred models with status and eligibility (placeholder)."),
    info_list(
      info_row("Baselines", "7 governed baseline models in the tournament universe."),
      info_row("Challengers", "6 audited challengers competing in the tournament."),
      info_row("Deferred", "NBEATS (runtime) and NHITS (dependency) excluded from the tournament."),
      info_row("Status", "Placeholders pending artifact binding.")
    ),
    tags$div(style = "margin-top:18px;", controls_preview())
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

