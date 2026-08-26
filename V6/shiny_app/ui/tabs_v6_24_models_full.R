# TESSERACT v2 | tabs_v6_24_models_full.R
# V6.24-P9K | Models FULL - Universe page.
#
# Isolated from ui/tabs.R so the legacy Models section is untouched. The page
# follows the legacy Universe layout - title, accordions, a model table, a
# closing assistant - but every number comes from the V6.24 governed artifacts
# and the page states plainly what it does NOT claim.

# Accordion matching the legacy home_collapse() look, kept local to this file so
# nothing in the legacy UI has to change.
v24mf_collapse <- function(title, subtitle, ..., open = FALSE) {
  tags$details(
    class = "v24mf-collapse", open = if (isTRUE(open)) NA else NULL,
    tags$summary(
      class = "v24mf-collapse-head",
      tags$div(
        tags$div(class = "v24mf-collapse-title", title),
        tags$div(class = "v24mf-collapse-sub", subtitle)
      )
    ),
    tags$div(class = "v24mf-collapse-body", ...)
  )
}

section_v24_models_full_universe <- function() {
  panel(
    "v24mf_universe",

    v24_section_head(
      "Models \u2014 Universe",
      paste("The governed V6.24 model universe: 15 models evaluated across",
            "140 operational series using the V6.24 artifacts.")),

    # ---- A. Scope disclosure -------------------------------------------
    tags$div(
      class = "v24mf-disclosure",
      tags$strong("This page describes the V6.24 model universe."),
      tags$p(paste("It does not compute a tournament and does not select a",
                   "global champion. Model comparison across the cohort is a",
                   "later stage (Ranking Diagnostics), and per-series champions",
                   "are a later stage (Champion).")),
      uiOutput("v24mf_scope_line")
    ),

    # ---- B. How to read this universe -----------------------------------
    v24mf_collapse(
      "How to read this universe",
      "Start here: what the governed universe is, what the families mean, and what this page does not claim.",
      tags$ul(
        class = "v24-list",
        tags$li(tags$b("Governed model universe. "),
                "Fifteen models are evaluated on every one of the 140 ",
                "operational series, giving 2,100 model-series accuracy rows. ",
                "Every model is scored on the same governed backtest."),
        tags$li(tags$b("Two family classifications. "),
                "The artifact carries a three-valued ", tags$code("model_family"),
                " (Baseline / Challenger / Neural). The four families shown ",
                "below are a ", tags$b("display grouping only"),
                " \u2014 the two partitions cut across each other."),
        tags$li(tags$b("Artifact evidence. "),
                "Accuracy comes from ", tags$code("accuracy_metrics"),
                ", per-series ranking from ", tags$code("model_rankings"),
                ", and champion visibility from ",
                tags$code("navigation_contract"), ". Nothing is recomputed here."),
        tags$li(tags$b("Per-series rankings. "),
                "Ranking in V6.24 is per series, not global. A model can lead ",
                "one series and trail on another."),
        tags$li(tags$b("Diagnostic medians. "),
                "The table shows cohort medians, never means. On this cohort ",
                "one model has a mean MAE of 5.9e21 against a median of 870, ",
                "so a mean would describe an outlier rather than the model."),
        tags$li(tags$b("Caveats. "),
                "Ratio metrics such as WAPE are recorded as not computable ",
                "where the denominator is zero across the evaluation window. ",
                "Those rows are excluded from that median, never set to zero."),
        tags$li(tags$b("What this page does not claim. "),
                "No head-to-head result, no bootstrap support, no global ",
                "winner, and no governed cross-series ranking.")
      ),
      open = FALSE
    ),

    # ---- C. What changed from the previous model section -----------------
    v24mf_collapse(
      "What changed from the previous model section",
      "The earlier Models section was built on a smaller, HDD-only scope with metrics V6.24 does not carry.",
      uiOutput("v24mf_changed"),
      open = FALSE
    ),

    # ---- D. Model families ----------------------------------------------
    v24mf_collapse(
      "Model families compared",
      "Four display families, shown alongside the governed three-valued classification.",
      uiOutput("v24mf_families"),
      open = TRUE
    ),

    # ---- E. Summary cards ------------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Universe at a glance"),
      tags$p(class = "v24-note",
             "Counts read from the governed artifacts. None of these is a ranking."),
      uiOutput("v24mf_cards")
    ),

    # ---- F. Universe table ----------------------------------------------
    tags$div(
      class = "v24-card-section",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "U"),
        tags$h3(class = "v24-card-title", "Current model universe"),
        tags$span(class = "v24-pill v24-pill-slate",
                  "Cohort diagnostic medians")
      ),
      tags$p(class = "v24-card-lead",
             paste("One row per governed model. Values are cohort diagnostic",
                   "medians read from accuracy_metrics, ordered by median MAE",
                   "for readability. This ordering is not a standing and not a",
                   "governed ranking.")),
      DT::dataTableOutput("v24mf_table"),
      tags$div(
        class = "v24-warn-card",
        tags$ul(
          class = "v24-list",
          tags$li(tags$span(class = "v24-cell-badge v24-cell-slate", "Diagnostic"),
                  " These medians describe the artifact. They do not select a ",
                  "model and do not decide any per-series champion."),
          tags$li(tags$span(class = "v24-cell-badge v24-cell-slate", "Per series"),
                  " The champion count is a ", tags$b("series-level"),
                  " count: how many of the 140 series that model leads, gated ",
                  "on champion visibility. It is not a global champion."),
          tags$li(tags$span(class = "v24-cell-badge v24-cell-warn", "Disagreement"),
                  " Median MAE and median WAPE do not produce the same order. ",
                  "That is expected, and it is why no single column is treated ",
                  "as the answer.")
        )
      )
    ),

    # ---- G. Optional chart ----------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Series-level champion count by model"),
      tags$p(class = "v24-note",
             paste("How many of the 140 operational series each model leads.",
                   "Read from navigation_contract, counting only series whose",
                   "champion may be presented. This is a distribution, not a",
                   "winner.")),
      highcharter::highchartOutput("v24mf_chart", height = "420px")
    ),

    # ---- H. What comes next ---------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("What comes next"),
      tags$ul(
        class = "v24-list",
        tags$li(tags$b("Ranking Diagnostics"),
                " \u2014 cohort comparison across models. It will be a ",
                "diagnostic summary, not a head-to-head tournament, because ",
                "V6.24 carries no pairwise evidence."),
        tags$li(tags$b("Champion"),
                " \u2014 the per-series champion, its distribution across ",
                "models, and the series where no champion may be presented.")
      )
    ),

    # ---- I. Assistant ----------------------------------------------------
    v24_assistant_card("mfu", V6_24_MF_UNIVERSE_PROMPTS,
                       "Ask AEGIS about this model universe",
                       paste("Answered only from accuracy_metrics,",
                             "model_rankings and navigation_contract."))
  )
}

# ---------------------------------------------------------------------------
# V6.24-P9L | Models FULL - Ranking Diagnostics.
#
# The honest replacement for the legacy Tournament page. It compares models
# across the cohort with medians the artifact supports and produces no winner.
# ---------------------------------------------------------------------------

section_v24_models_full_ranking <- function() {
  panel(
    "v24mf_ranking",

    v24_section_head(
      "Models \u2014 Ranking Diagnostics",
      paste("Cohort-level diagnostic comparisons across the governed V6.24",
            "model universe. This is not a head-to-head tournament.")),

    # ---- A. Disclosure --------------------------------------------------
    tags$div(
      class = "v24mf-disclosure v24mf-disclosure-warn",
      tags$strong("This page is not a head-to-head tournament."),
      tags$p(paste("V6.24 does not contain pairwise or bootstrap evidence,",
                   "p-values, or a global champion artifact, and it does not",
                   "carry the two error measures the earlier tournament ranked",
                   "on. What it does carry is per-series accuracy and per-series",
                   "champions, so this page compares cohort medians and counts",
                   "how many series each model leads. No winner is declared.")),
      uiOutput("v24mfr_scope_line")
    ),

    # ---- B. How to read --------------------------------------------------
    v24mf_collapse(
      "How to read Ranking Diagnostics",
      "What a diagnostic median is, what a series-level champion count is, and why neither produces a winner.",
      tags$ul(
        class = "v24-list",
        tags$li(tags$b("Cohort diagnostic medians. "),
                "For each model, the median of its per-series error across the ",
                "cohort. Lower is better for every error measure shown."),
        tags$li(tags$b("Median, not mean. "),
                "One model has a mean MAE of 5.9e21 against a median of 870. ",
                "A mean here would describe a single failure, not the model."),
        tags$li(tags$b("Series-level champion count. "),
                "How many of the 140 series a model leads, according to the ",
                "governed per-series ranking. It is a count of series, not a ",
                "cohort-wide decision."),
        tags$li(tags$b("No-signal series are excluded. "),
                "Fifteen series have all-zero actuals. A model predicting zero ",
                "against zero scores a perfect error there, so those series are ",
                "kept out of the champion counts entirely."),
        tags$li(tags$b("Why no winner is declared. "),
                "The metrics disagree with each other, and the model with the ",
                "best median is usually not the model that leads the most ",
                "series. Collapsing that into one ordering would hide the ",
                "disagreement rather than report it."),
        tags$li(tags$b("How this differs from the earlier model section. "),
                "That work compared 13 models over 39 HDD entities using a ",
                "paired statistical procedure. This cohort is 15 models over ",
                "140 series across four metrics, and the earlier evidence has ",
                "no successor artifact here. Figures from the two are not ",
                "comparable.")
      ),
      open = FALSE
    ),

    # ---- C. Setup --------------------------------------------------------
    tags$section(
      class = "v24-card-section v24-acc-setup",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "A"),
        tags$h3(class = "v24-card-title", "Set up the diagnostic comparison"),
        tags$span(class = "v24-pill v24-pill-slate", "Read-only \u00b7 diagnostic")
      ),
      tags$p(class = "v24-card-lead",
             "Choose a measure, a family and an ordering, then run step 4. Source: ",
             tags$code("accuracy_metrics"), " and ",
             tags$code("navigation_contract"), "."),
      tags$div(
        class = "v24-acc-controls",
        tags$div(
          class = "v24-field",
          tags$label(class = "v24-field-label",
                     tags$span(class = "v24-step-num", "1"), "Primary measure"),
          uiOutput("v24mfr_metric_ui"),
          tags$p(class = "v24-field-hint",
                 "Drives the diagnostic median column and the first chart. Lower is better.")
        ),
        tags$div(
          class = "v24-field",
          tags$label(class = "v24-field-label",
                     tags$span(class = "v24-step-num", "2"), "Display family"),
          uiOutput("v24mfr_family_ui"),
          tags$p(class = "v24-field-hint",
                 "Display grouping only; the governed family is shown per row.")
        ),
        tags$div(
          class = "v24-field",
          tags$label(class = "v24-field-label",
                     tags$span(class = "v24-step-num", "3"), "Order by"),
          uiOutput("v24mfr_sort_ui"),
          tags$p(class = "v24-field-hint",
                 "Ordering is for reading. It is not an official rank.")
        )
      ),
      tags$div(
        class = "v24-bt-actions",
        tags$div(
          class = "v24-acc-analyze-label",
          tags$span(class = "v24-step-num", "4"),
          tags$span(class = "v24-field-label", "Analyze Ranking Diagnostics")
        ),
        actionButton("v24mfr_go", "Analyze Ranking Diagnostics",
                     class = "btn v24-btn-primary"),
        actionButton("v24mfr_reset", "Reset", class = "btn v24-btn-ghost"),
        uiOutput("v24mfr_applied", inline = TRUE)
      )
    ),

    # ---- D. Cards --------------------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Diagnostic summary"),
      tags$p(class = "v24-note",
             paste("Read from the governed artifacts. Neither headline below",
                   "is a champion or a winner.")),
      uiOutput("v24mfr_cards")
    ),

    # ---- E. Table --------------------------------------------------------
    tags$div(
      class = "v24-card-section",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "B"),
        tags$h3(class = "v24-card-title", "Diagnostic comparison"),
        tags$span(class = "v24-pill v24-pill-slate", "Cohort medians")
      ),
      tags$p(class = "v24-card-lead",
             paste("One row per governed model. The position column reflects",
                   "the ordering you chose and changes with it; it is not an",
                   "official rank.")),
      DT::dataTableOutput("v24mfr_table")
    ),

    # ---- F. Chart 1 ------------------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Diagnostic median by model"),
      tags$p(class = "v24-note",
             "Cohort median of the selected measure. Lower is better."),
      highcharter::highchartOutput("v24mfr_metric_chart", height = "440px")
    ),

    # ---- G. Chart 2 ------------------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Series-level champion count by model"),
      tags$p(class = "v24-note",
             paste("Number of series where this model is the presentable",
                   "champion. No-signal series are excluded, so the bars sum to",
                   "the presentable-champion total, not to 140.")),
      highcharter::highchartOutput("v24mfr_champ_chart", height = "440px")
    ),

    # ---- H. Disagreement -------------------------------------------------
    tags$div(
      class = "v24-card-section",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "C"),
        tags$h3(class = "v24-card-title", "Where the measures disagree"),
        tags$span(class = "v24-pill v24-pill-slate", "Diagnostic only")
      ),
      tags$p(class = "v24-card-lead",
             paste("Each model's position under every available measure. If the",
                   "measures agreed, every row would be flat. The spread column",
                   "shows how far a model moves depending on which measure is",
                   "used, and it is the reason this page reports no single",
                   "ordering as the answer.")),
      DT::dataTableOutput("v24mfr_disagree")
    ),

    # ---- I. Assistant ----------------------------------------------------
    v24_assistant_card("mfr", V6_24_MF_RANKING_PROMPTS,
                       "Ask AEGIS about these ranking diagnostics",
                       paste("Answered only from accuracy_metrics and",
                             "navigation_contract for the analyzed setup."))
  )
}

# ---------------------------------------------------------------------------
# V6.24-P9M | Models FULL - Champion.
#
# Champion in V6.24 is a per-series fact gated by champion_visible. This page
# shows the distribution, the selected series, and the 15 series where no
# champion may be presented. It never names a champion for the cohort.
# ---------------------------------------------------------------------------

section_v24_models_full_champion <- function() {
  panel(
    "v24mf_champion",

    v24_section_head(
      "Models \u2014 Champion",
      paste("Series-level champion evidence for the governed V6.24 cohort.",
            "V6.24 does not declare a champion for the whole cohort.")),

    # ---- A. Disclosure --------------------------------------------------
    tags$div(
      class = "v24mf-disclosure v24mf-disclosure-warn",
      tags$strong("V6.24 does not select one champion for the whole cohort."),
      tags$p(paste("Champion evidence is recorded per series in the governed",
                   "contract and gated by champion_visible. Series whose",
                   "observed actuals are all zero receive no presentable",
                   "champion at all.")),
      uiOutput("v24mfc_scope_line")
    ),

    # ---- B. How to read --------------------------------------------------
    v24mf_collapse(
      "How to read Champion",
      "What a series-level champion is, what the visibility gate does, and why some series have none.",
      tags$ul(
        class = "v24-list",
        tags$li(tags$b("Champion is per series. "),
                "Each series has its own best-ranked model. A model that leads ",
                "one series often trails on another."),
        tags$li(tags$b("champion_visible is the gate. "),
                "The contract records whether a series' champion may be ",
                "presented. This page reads that field and never overrides it."),
        tags$li(tags$b("No-signal suppression. "),
                "Fifteen series have all-zero observed actuals. A model ",
                "predicting zero scores a perfect error there without having ",
                "modelled anything, so no champion is presentable."),
        tags$li(tags$b("Zero versus zero is not accuracy. "),
                "An error of exactly zero on an all-zero series is a degenerate ",
                "identity. Treating it as a win would rank an empty series ",
                "above a real one."),
        tags$li(tags$b("The distribution is a count. "),
                "How many series each model leads. It is not a cohort-wide ",
                "decision and the top row is not a winner."),
        tags$li(tags$b("Ranking policy. "),
                "Models are ranked within a series by an error metric where ",
                "lower is better, with a tie-break where the metrics cannot ",
                "separate them."),
        tags$li(tags$b("Why there is no cohort champion. "),
                "No artifact names one, and V6.24 holds no head-to-head ",
                "evidence that could support such a decision.")
      ),
      open = FALSE
    ),

    # ---- C. Cards --------------------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Champion evidence at a glance"),
      tags$p(class = "v24-note",
             "Counts read from the governed contract. None of these is a cohort-wide decision."),
      uiOutput("v24mfc_cards")
    ),

    # ---- D. Distribution chart -------------------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Series-level champion distribution"),
      tags$p(class = "v24-note",
             paste("No-signal series are excluded, so the bars sum to the",
                   "presentable total rather than to 140. This is a",
                   "distribution, not a cohort-wide champion.")),
      highcharter::highchartOutput("v24mfc_dist_chart", height = "440px")
    ),

    # ---- E. Distribution table -------------------------------------------
    tags$div(
      class = "v24-card-section",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "A"),
        tags$h3(class = "v24-card-title", "Champion distribution"),
        tags$span(class = "v24-pill v24-pill-slate", "Series-level counts")
      ),
      tags$p(class = "v24-card-lead",
             paste("One row per model that leads at least one presentable",
                   "series, ordered by how many. The order is a count, not a",
                   "ranking, and the top row is not a winner.")),
      DT::dataTableOutput("v24mfc_dist_table")
    ),

    # ---- F. Selected-series champion -------------------------------------
    tags$div(
      class = "v24-card-section",
      tags$div(
        class = "v24-card-head",
        tags$span(class = "v24-kicker", "B"),
        tags$h3(class = "v24-card-title", "Champion for the selected series"),
        tags$span(class = "v24-pill v24-pill-slate", "Per series")
      ),
      uiOutput("v24mfc_selection_banner"),
      tags$div(class = "v24-inline-ctl", uiOutput("v24mfc_series_ui")),
      uiOutput("v24mfc_selected")
    ),

    # ---- G. Top ranking for that series ----------------------------------
    tags$div(
      class = "v24-panel",
      tags$h3("Top ranked models for this series"),
      tags$p(class = "v24-note",
             paste("Ranking within this one series, read from model_rankings.",
                   "It is not a cohort-wide ranking.")),
      uiOutput("v24mfc_rank_note"),
      DT::dataTableOutput("v24mfc_top5")
    ),

    # ---- H. Ranking policy -----------------------------------------------
    v24mf_collapse(
      "Ranking policy and the visibility gate",
      "How a per-series champion is chosen, and what decides whether it may be shown.",
      uiOutput("v24mfc_policy"),
      open = FALSE
    ),

    # ---- I. Legacy note --------------------------------------------------
    v24mf_collapse(
      "What changed from the previous Champion page",
      "Historical context. The earlier decision is not a current V6.24 conclusion.",
      uiOutput("v24mfc_legacy"),
      open = FALSE
    ),

    # ---- J. Assistant ----------------------------------------------------
    v24_assistant_card("mfc", V6_24_MF_CHAMPION_PROMPTS,
                       "Ask AEGIS about champion evidence",
                       paste("Answered only from navigation_contract,",
                             "model_rankings and series_signal_quality."))
  )
}
