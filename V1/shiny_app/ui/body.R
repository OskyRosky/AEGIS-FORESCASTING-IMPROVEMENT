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
        tags$h2("About TESSERACT v2"),
        tags$button(id = "tess-help-close", class = "tess-overlay-close", type = "button", "\u00D7")
      ),
      tags$div(
        class = "tess-overlay-body",
        tags$p("Governed Shiny MVP for forecast improvement review (Stage 07)."),
        tags$ul(
          tags$li("Read-only dashboard \u2014 no model rerun, no recomputation."),
          tags$li("Use the left sidebar groups to expand and browse sections."),
          tags$li("Use the moon icon (top-right) to switch light / dark mode."),
          tags$li("Sections are populated block by block.")
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
          "This is the landing page of the dashboard. It states the purpose, scope and how the platform relates to the codebase-ownership goal (Goal #3).",
          list(
            "Purpose / Scope / Goal #3 cards summarize what the dashboard is for.",
            "Dashboard map: the four working areas (Forecasting, Models, Governance, Reference).",
            "Use the left sidebar to navigate; collapse it with the \u2630 button and hover an icon to reveal its subsections."
          ),
          "Read-only mode: no models, forecasts or metrics are recomputed."
        ),

        guide_entry(
          "overview", "Executive Overview",
          "Shows the high-level status of the forecast improvement review, designed for a quick read by decision makers.",
          list(
            "Key indicators (KPIs): governance state, current champion, decision confidence and active version.",
            "Each KPI includes a context tag (for example, 'Stage 07' or 'Conditions apply').",
            "A summary of the review status is shown at the bottom."
          ),
          "Values shown are placeholders and will be bound to governed artifacts in later blocks."
        ),

        guide_entry(
          "explorer", "Forecast Explorer",
          "Lets you explore forecast curves: actual versus baseline versus challenger models, filtered by entity, model and window.",
          list(
            "Series: actual and forecast curves per entity.",
            "Filters: entity, model and backtest window (read-only).",
            "Charting and data binding arrive in a later block."
          ),
          "Charting block: bound to governed forecasts/actuals; nothing is recomputed."
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
          "comparison", "Model Comparison Evidence",
          "Shows model-versus-model comparison: scorecard and pairwise statistical support.",
          list(
            "Scorecard: unified per-model metrics.",
            "Pairwise: head-to-head deltas with bootstrap CI and adjusted p-values.",
            "Support: comparison status (supported difference vs inconclusive)."
          )
        ),

        guide_entry(
          "conditions", "Champion Conditions",
          "Lists the conditions attached to the champion decision. Its approval is not unconditional: these conditions must be monitored.",
          list(
            "Each condition describes a monitoring commitment (accuracy, seasonal stability, fallback model).",
            "The status indicates that tracking is performed under governance."
          )
        ),

        guide_entry(
          "risks", "Risk Register",
          "Captures the open risks and deferred models identified for the review and their tracking.",
          list(
            "FastNeuralAR_MLP: high-risk behaviour, not champion eligible.",
            "NBEATS / NHITS: deferred for runtime / dependency reasons.",
            "FixedGrowth_6: manual review condition."
          )
        ),

        guide_entry(
          "audit", "Audit Trail",
          "Provides the chronological record of governed checkpoints and audits, for traceability.",
          list(
            "Audit chain, sanity checks and decisions.",
            "Lets you verify the approved status of the review."
          )
        ),

        guide_entry(
          "artifacts", "Source Artifacts",
          "Indicates the governed artifacts that feed the dashboard, giving transparency on the data origin.",
          list(
            "model_lab closure pack, tournament_engine and challenger_metrics outputs.",
            "config: governed YAML policies (read-only)."
          )
        ),

        guide_entry(
          "methodology", "Methodology",
          "Explains the benchmark semantics and the metric policy applied.",
          list(
            "MASE as primary absolute benchmark; RMSSE as guardrail.",
            "Robust median-of-medians aggregation (window \u2192 entity \u2192 global).",
            "Pairwise significance with bootstrap and adjusted p-values."
          )
        ),

        guide_entry(
          "downloads", "Downloads Center",
          "A general and per-section downloads center. It stays Planned until a governed export is wired.",
          list(
            "Download handlers will target governed closure-pack artifacts.",
            "The section is marked Planned for now."
          )
        ),

        guide_entry(
          "version", "Version Info",
          "Summarizes the build and policy metadata for this dashboard version.",
          list(
            "Active version, stage and policy.",
            "Audit state: approved to Stage 07."
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
    tags$link(rel = "stylesheet", type = "text/css", href = "custom.css"),
    tags$script(src = "custom.js"),
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
