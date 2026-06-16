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
          tags$span(id = "tess-guide-title-text", "Dashboard")
        ),
        tags$button(id = "tess-guide-close", class = "tess-overlay-close",
                    type = "button", "\u00D7")
      ),
      tags$div(
        class = "tess-overlay-body tess-guide-body",

        guide_entry(
          "dashboard", "Dashboard",
          "This is the landing page of the dashboard. It gives an overall view of the forecast improvement platform status (Stage 07) and a map of everything you will find inside.",
          list(
            "Status cards: confirm the dashboard is initialized and running in read-only mode.",
            "Platform map: summarizes the four main blocks (Overview, Champion & Models, Evidence and Governance).",
            "Use the left sidebar to navigate; collapse it with the \u2630 button and hover an icon to reveal its subsections."
          ),
          "Read-only mode: no models, forecasts or metrics are recomputed."
        ),

        guide_entry(
          "executive", "Executive Overview",
          "Shows the high-level status of the forecast improvement review, designed for a quick read by decision makers.",
          list(
            "Key indicators (KPIs): governance state, current champion, decision confidence and active version.",
            "Each KPI includes a context tag (for example, 'Stage 07' or 'Conditions apply').",
            "A summary of the review status is shown at the bottom."
          ),
          "Values shown are placeholders and will be bound to governed artifacts in later blocks."
        ),

        guide_entry(
          "champion", "Champion",
          "Presents the champion model selected under governance: the central decision of the review.",
          list(
            "Decision: the selected champion model (a conditional, not unconditional, selection).",
            "Confidence: the confidence level recorded by governance.",
            "Policy: the champion is shown from governed artifacts, with no recomputation.",
            "The controls preview (horizon, model family) is illustrative only and is disabled."
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
          "universe", "Model Universe",
          "Lists the model families considered in the governed review, giving context on the alternatives evaluated.",
          list(
            "ETS: exponential smoothing \u2014 the champion family.",
            "ARIMA, Seasonal naive and TSLM: reference and comparison alternatives.",
            "Includes a controls preview (read-only)."
          )
        ),

        guide_entry(
          "tournament", "Tournament Evidence",
          "Summarizes the backtesting and ranking evidence that supports the champion selection.",
          list(
            "Protocol: rolling-origin validation.",
            "Ranking: the ranking table will be bound to governed metrics.",
            "Metric policy: definitions follow the Stage 07 policy."
          )
        ),

        guide_entry(
          "pairwise", "Pairwise Evidence",
          "Shows head-to-head comparisons between models, to understand their relative strengths.",
          list(
            "Direct comparisons between pairs of models.",
            "Evidence will be bound to governed artifacts in a later block."
          )
        ),

        guide_entry(
          "risk", "Risk Register",
          "Captures the risks identified for the forecast improvement review and their tracking.",
          list(
            "Each risk (R-01, R-02, R-03) describes a threat and its mitigation.",
            "Covers seasonal drift, structural-break sensitivity and data latency.",
            "The status reflects tracking under governance."
          )
        ),

        guide_entry(
          "actions", "Governance Actions",
          "Records the decisions and actions taken by the governance board.",
          list(
            "Approved action, associated conditions and owner.",
            "Next steps defined by governance."
          )
        ),

        guide_entry(
          "audit", "Audit Trail",
          "Provides the chronological record of governed checkpoints, for traceability.",
          list(
            "Checkpoint, stage, version and active policy.",
            "Lets you verify the approved status of the review."
          )
        ),

        guide_entry(
          "sources", "Source Artifacts",
          "Indicates the governed artifacts that feed the dashboard, giving transparency on the data origin.",
          list(
            "outputs/governance, outputs/evaluation and outputs/model_lab: governed outputs.",
            "config: governed YAML policies (read-only)."
          )
        ),

        guide_entry(
          "methodology", "Methodology",
          "Explains the review methodology and the metric policy applied.",
          list(
            "Rolling-origin backtesting for out-of-sample evaluation.",
            "Metrics with governed definitions (Stage 07 scoring policy).",
            "Governed and conditional champion selection."
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
