# TESSERACT v2 | body.R | dashboard shell composition (Block 7.0C)
source("ui/sidebar.R")
source("ui/tabs.R")
source("ui/footer.R")

tess_help_overlay <- function() {
  tags$div(
    id = "tess-help-overlay",
    class = "tess-overlay",
    tags$div(
      class = "tess-overlay-card",
      tags$div(
        class = "tess-overlay-head",
        tags$h2("About AEGIS"),
        tags$button(id = "tess-help-close", class = "tess-overlay-close", type = "button", "\u00D7")
      ),
      tags$div(
        class = "tess-overlay-body",
        tags$p("Read-only dashboard for the forecast improvement review."),
        tags$ul(
          tags$li("Read-only dashboard \u2014 no model rerun, no recomputation."),
          tags$li("Use the left sidebar groups to expand and browse sections."),
          tags$li("Use the moon icon (top-right) to switch light / dark mode.")
        ),
        tags$p(class = "text-muted-sm", "Contact: oscarau@microsoft.com")
      )
    )
  )
}

# ---------------------------------------------------------------------------
# Section guide overlay ("Gu\u00eda de secci\u00f3n")
# Contextual guide: the central header button opens this modal and JS shows the
# entry matching the currently active section. Pure client-side, read-only.
# ---------------------------------------------------------------------------
guide_entry <- function(section, title, intro, items, note = NULL) {
  tags$div(
    class = "guide-entry",
    `data-guide` = section,
    `data-title` = title,
    tags$p(class = "guide-intro", intro),
    tags$ul(class = "guide-list", lapply(items, function(x) tags$li(x))),
    if (!is.null(note)) tags$p(class = "guide-note", note)
  )
}

tess_guide_overlay <- function() {
  tags$div(
    id = "tess-guide-overlay",
    class = "tess-overlay",
    tags$div(
      class = "tess-overlay-card tess-guide-card",
      tags$div(
        class = "tess-overlay-head tess-guide-head",
        tags$h2(
          tags$span(class = "tess-guide-head-icon", id = "tess-guide-head-icon",
                    tess_icon("table-columns")),
          tags$span(id = "tess-guide-title-text", "Project Home")
        ),
        tags$button(id = "tess-guide-close", class = "tess-overlay-close",
                    type = "button", "\u00D7")
      ),
      tags$div(
        class = "tess-overlay-body tess-guide-body",

        guide_entry(
          "home", "Project Home",
          "This is the landing page of the dashboard. It states the purpose and scope, and how it supports the goal of owning the forecasting codebase.",
          list(
            "Purpose and scope cards summarize what the dashboard is for.",
            "Dashboard map: the four working areas (Forecasting, Models, Governance, Reference).",
            "Use the left sidebar to navigate; collapse it with the \u2630 button and hover an icon to reveal its subsections."
          ),
          "Read-only mode: no models, forecasts or metrics are recomputed."
        ),

        guide_entry(
          "overview", "Executive Overview",
          "Shows the high-level status of the forecast improvement review, designed for a quick read by decision makers.",
          list(
            "Models: the governed champion, its conditions and the supporting accuracy evidence.",
            "Forecast: the evidence base the review was scored on (coverage, not a new metric).",
            "Governance: the audited approval state and the conditions attached to it."
          ),
          "All values are read from governed artifacts; nothing is recomputed."
        ),

        guide_entry(
          "explorer", "Forecast Explorer",
          "Lets you explore forecast curves: actual versus baseline versus challenger models, filtered by entity, model and window.",
          list(
            "Series: actual and forecast curves per entity.",
            "Filters: entity, model and backtest window (read-only).",
            "Charts and data are read directly from governed artifacts."
          ),
          "Charts are bound to governed forecasts/actuals; nothing is recomputed."
        ),

        guide_entry(
          "accuracy", "Accuracy Overview",
          "Presents the official accuracy metrics by model, with MASE as the primary score and RMSSE as guardrail.",
          list(
            "Primary: MASE (absolute benchmark) with RMSSE guardrail.",
            "Diagnostics: wMAPE, SMAPE and bias \u2014 supporting only, never the primary score.",
            "Granularity: errors by model and entity."
          )
        ),

        guide_entry(
          "ttl", "TTL / Capacity View",
          "A Months-to-Live / capacity perspective. It stays Planned until a governed TTL/capacity artifact exists.",
          list(
            "No governed TTL artifact is available yet.",
            "The section is intentionally marked Planned to avoid showing non-governed data."
          )
        ),

        guide_entry(
          "universe", "Model Universe",
          "Lists the full model universe: baseline, challenger and deferred models, with status, family and eligibility.",
          list(
            "7 baseline models and 6 audited challengers in the tournament.",
            "NBEATS and NHITS are deferred (runtime / dependency).",
            "Includes a controls preview (read-only)."
          )
        ),

        guide_entry(
          "tournament", "Tournament Standings",
          "Summarizes the tournament standings ranked by the official MASE / RMSSE metrics.",
          list(
            "Protocol: rolling-origin validation.",
            "Ranking: standings table bound to governed tournament metrics.",
            "Metric policy: MASE primary, RMSSE guardrail."
          )
        ),

        guide_entry(
          "champion", "Champion Decision",
          "Presents the champion model selected under governance: the central decision of the review.",
          list(
            "Decision: the selected champion model (a conditional, not unconditional, selection).",
            "Confidence: the confidence level recorded by governance.",
            "Policy: the champion is shown from governed artifacts, with no recomputation.",
            "The controls preview (horizon, model family) is illustrative only and is disabled."
          )
        ),

        guide_entry(
          "risks", "Risk Register",
          "Shows the governed risk register from the Model Lab closure pack: open risks and deferred models carried forward from the review.",
          list(
            "Each risk has a severity level (high, medium, advisory, minor) and a governed treatment.",
            "Carry-forward flags show which risks must stay visible on the dashboard and which feed future work.",
            "Deferred models (NBEATS, NHITS) are documented as future-work candidates, not rejected.",
            "No risk is computed here \u2014 the register is read from governed artifacts."
          )
        ),

        guide_entry(
          "audit", "Audit Trail",
          "Shows the independent governance audits that supported the conditional champion decision: Audit #4, the 5.30A sanity review, and Audit #5.",
          list(
            "Each gate approved with conditions and zero blockers before the dashboard handoff.",
            "Audit #5 findings are listed by severity, with closure and handoff blocking flags.",
            "Governed next steps are carried forward to the dashboard and future work.",
            "Read-only checks: no models were rerun and no source outputs were modified."
          )
        ),

        guide_entry(
          "artifacts", "Source Artifacts",
          "The governed artifact catalog that feeds the dashboard, with data lineage and direct CSV downloads.",
          list(
            "Catalog summary: total governed artifacts, available now, categories and roadmap items.",
            "Governed downloads: key closure-pack / tournament CSVs served verbatim from disk.",
            "Data lineage: each dashboard section mapped to its source artifact (handoff manifest).",
            "Read-only: files are never edited or recomputed by the dashboard."
          )
        ),

        guide_entry(
          "methodology", "Methodology",
          "Explains how data reaches the dashboard and how the dashboard is organized.",
          list(
            "Data pipeline: ingestion (SQL) \u2192 governed CSV contract \u2192 read-only consumption.",
            "Current dataset: governed series, models, version and date coverage.",
            "What the dashboard consumes: forecast, backtest, Model Lab, tournament and governance files.",
            "Dashboard structure and supporting reference material."
          )
        ),

        guide_entry(
          "version", "Version Info",
          "Summarizes the build, data and runtime metadata for this dashboard release.",
          list(
            "App version and governance policy.",
            "Audit state and the selected champion with its conditions.",
            "Data snapshot: forecast version, series, models and coverage.",
            "Runtime: artifacts loaded, load timestamp and package availability."
          )
        )
      )
    )
  )
}

app_ui <- function() {
  page_fillable(
    theme = app_theme,
    fillable = FALSE,
    padding = 0,
    gap = 0,
    tags$link(rel = "stylesheet", type = "text/css", href = "custom.css?v=20260624f"),
    tags$script(src = "custom.js?v=20260623b"),
    tags$div(
      class = "tess-app",
      app_header(),
      tags$div(
        class = "app-main",
        app_sidebar(),
        tags$main(
          class = "app-content",
          app_sections()
        )
      ),
      app_footer(),
      tess_help_overlay(),
      tess_guide_overlay()
    )
  )
}
