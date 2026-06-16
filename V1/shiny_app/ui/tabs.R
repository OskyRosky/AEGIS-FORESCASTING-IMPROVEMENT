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

# ---------------------------------------------------------------------------
# Sections
# ---------------------------------------------------------------------------
section_dashboard <- function() {
  panel(
    "dashboard", active = TRUE,
    section_head("TESSERACT v2 Dashboard",
                 "Forecast Improvement Platform \u2014 Stage 07 Shiny MVP"),
    card_grid(
      shell_card("Layout ready", "Shell initialized",
                 "Header + collapsible sidebar + body structure initialized."),
      shell_card("Read-only mode", "No recompute",
                 "No model rerun, no forecast recomputation, no metric recalculation."),
      shell_card("Next step", "Populate further",
                 "Sections are scaffolded and will be bound to governed artifacts block by block.")
    ),
    tags$h3(class = "section-block-title", "Platform map"),
    card_grid(
      shell_card("Overview", "Executive view", "Headline status and KPIs (placeholders)."),
      shell_card("Champion & Models", "Decision & universe", "Governed champion and model universe."),
      shell_card("Evidence", "Tournament & risk", "Tournament, pairwise and risk register."),
      shell_card("Governance", "Actions & audit", "Governance actions and audit trail.")
    )
  )
}

section_executive <- function() {
  panel(
    "executive",
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

section_champion <- function() {
  panel(
    "champion",
    section_head("Champion", "Governed champion decision (read-only display)."),
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

section_universe <- function() {
  panel(
    "universe",
    section_head("Model Universe",
                 "Families considered in the governed review (read-only)."),
    info_list(
      info_row("ETS family", "Exponential smoothing \u2014 governed champion family."),
      info_row("ARIMA family", "Auto-regressive integrated moving average."),
      info_row("Seasonal naive", "Seasonal baseline reference."),
      info_row("TSLM", "Time-series linear model with trend/seasonality.")
    ),
    tags$div(style = "margin-top:18px;", controls_preview())
  )
}

section_tournament <- function() {
  panel(
    "tournament",
    section_head("Tournament Evidence",
                 "Backtesting / ranking evidence summary (placeholders)."),
    card_grid(
      shell_card("Protocol", "Rolling-origin", "Backtesting protocol used during the governed review."),
      shell_card("Ranking", "Pending binding", "Model ranking table will be bound to governed metrics."),
      shell_card("Metric policy", "Governed", "Metric definitions follow the Stage 07 metric policy.")
    )
  )
}

section_pairwise <- function() {
  panel(
    "pairwise",
    section_head("Pairwise Evidence",
                 "Head-to-head model comparisons (placeholder)."),
    shell_card("Pairwise comparisons", "Pending binding",
               "Pairwise comparison evidence will be bound to governed artifacts in a later block.")
  )
}

section_risk <- function() {
  panel(
    "risk",
    section_head("Risk Register",
                 "Risks tracked for the forecast improvement review."),
    info_list(
      info_row("R-01", "Seasonal drift in upcoming periods \u2014 monitor."),
      info_row("R-02", "Structural break sensitivity \u2014 contingency model retained."),
      info_row("R-03", "Data latency at month boundaries \u2014 governed ingestion."),
      info_row("Status", "Placeholders pending artifact binding.")
    )
  )
}

section_actions <- function() {
  panel(
    "actions",
    section_head("Governance Actions",
                 "Decisions and actions recorded by governance."),
    info_list(
      info_row("Action", "Approved to Stage 07 Shiny MVP."),
      info_row("Conditions", "Champion selected with conditions."),
      info_row("Owner", "Governance board."),
      info_row("Next", "Bind cards/tables to governed artifacts.")
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

section_sources <- function() {
  panel(
    "sources",
    section_head("Source Artifacts",
                 "Governed artifacts that will feed the dashboard."),
    info_list(
      info_row("outputs/governance", "Governance decisions and audit records."),
      info_row("outputs/evaluation", "Evaluation and backtesting outputs."),
      info_row("outputs/model_lab", "Model lab results."),
      info_row("config", "Governed YAML policies (read-only).")
    )
  )
}

section_methodology <- function() {
  panel(
    "methodology",
    section_head("Methodology",
                 "Metric policy and review methodology (read-only)."),
    card_grid(
      shell_card("Backtesting", "Rolling-origin", "Out-of-sample evaluation across origins."),
      shell_card("Metrics", "Governed definitions", "Metrics follow the Stage 07 scoring policy."),
      shell_card("Selection", "With conditions", "Champion selection is governed and conditional.")
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
    section_dashboard(),
    section_executive(),
    section_champion(),
    section_conditions(),
    section_universe(),
    section_tournament(),
    section_pairwise(),
    section_risk(),
    section_actions(),
    section_audit(),
    section_sources(),
    section_methodology(),
    section_version()
  )
}

