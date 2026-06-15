# TESSERACT v2 | tabs.R | governed Stage 07 tab content

status_card <- function(label, value, detail = NULL, class = "text-bg-primary") {
  div(
    class = "card governance-card h-100",
    div(
      class = "card-body",
      tags$span(class = paste("badge", class, "mb-3"), label),
      h4(class = "fw-bold mb-1", value),
      if (!is.null(detail)) p(class = "text-muted small mb-0", detail)
    )
  )
}

planned_panel <- function(title) {
  div(
    class = "tess-shell py-4",
    div(
      class = "placeholder-panel",
      h3(class = "h5 fw-bold", title),
      p(class = "mb-0 text-muted", "Planned for upcoming Stage 07 block.")
    )
  )
}

cover_landing_tab <- function() {
  nav_panel(
    "Cover / Landing",
    value = "cover",
    div(
      class = "tess-shell py-4",
      div(
        class = "landing-hero mb-4",
        tags$span(class = "status-chip mb-3", "Governance-approved Shiny MVP"),
        h1(class = "display-6 fw-bold mb-2", "TESSERACT v2 Forecast Improvement Platform"),
        p(class = "lead mb-0", "Governed Shiny MVP for forecast improvement review")
      ),
      div(
        class = "row g-3 mb-4",
        div(class = "col-md-3", status_card("Stage 05", "Closed", "Model Lab complete", "text-bg-success")),
        div(class = "col-md-3", status_card("Stage 06", "Approved", "Validation & Governance complete", "text-bg-success")),
        div(class = "col-md-3", status_card("Audit #6", APP_AUDIT_STATE, "Approved with conditions", "text-bg-warning")),
        div(class = "col-md-3", status_card("Active Version", APP_VERSION, "All active work occurs inside V1", "text-bg-primary"))
      ),
      div(
        class = "row g-4",
        div(
          class = "col-lg-6",
          div(
            class = "card governance-card h-100",
            div(
              class = "card-body",
              tags$span(class = "badge text-bg-primary mb-3", "Champion summary"),
              h2(class = "h4 fw-bold", paste("Champion:", APP_CHAMPION)),
              p(class = "mb-2", tags$strong("Decision:"), paste(APP_CHAMPION_DECISION)),
              p(class = "mb-2", tags$strong("Confidence:"), APP_CHAMPION_CONFIDENCE),
              p(class = "mb-0 text-muted", "Selected with conditions; not an unconditional winner.")
            )
          )
        ),
        div(
          class = "col-lg-6",
          div(
            class = "card governance-card h-100",
            div(
              class = "card-body",
              tags$span(class = "badge text-bg-secondary mb-3", "Governance note"),
              tags$ul(
                class = "policy-list mb-3",
                tags$li("Read-only dashboard."),
                tags$li("No forecast recomputation."),
                tags$li("No metric recalculation."),
                tags$li("No model rerun."),
                tags$li("Values must come from governed artifacts.")
              ),
              div(
                class = "alert alert-info mb-0",
                "Next blocks will bind cards and tables to governed artifacts."
              )
            )
          )
        )
      )
    )
  )
}

version_info_tab <- function() {
  nav_panel(
    "Version Info",
    value = "version",
    div(
      class = "tess-shell py-4",
      div(
        class = "card governance-card",
        div(
          class = "card-body",
          h3(class = "h5 fw-bold", "Version and build policy"),
          p(tags$strong("Version:"), APP_VERSION),
          p(tags$strong("Stage:"), APP_STAGE),
          p(tags$strong("Policy:"), APP_POLICY),
          p(tags$strong("Audit state:"), "approved to Stage 07")
        )
      )
    )
  )
}

stage07_nav_items <- function() {
  list(
    cover_landing_tab(),
    nav_panel("Executive Overview", value = "executive", planned_panel("Executive Overview")),
    nav_panel("Champion Decision", value = "champion", planned_panel("Champion Decision")),
    nav_panel("Champion Conditions", value = "conditions", planned_panel("Champion Conditions")),
    nav_panel("Model Universe", value = "universe", planned_panel("Model Universe")),
    nav_panel("Tournament Evidence", value = "tournament", planned_panel("Tournament Evidence")),
    nav_panel("Pairwise Evidence", value = "pairwise", planned_panel("Pairwise Evidence")),
    nav_panel("Risk Register", value = "risk", planned_panel("Risk Register")),
    nav_panel("Deferred Models", value = "deferred", planned_panel("Deferred Models")),
    nav_panel("Governance Actions", value = "actions", planned_panel("Governance Actions")),
    nav_panel("Audit Trail", value = "audit", planned_panel("Audit Trail")),
    nav_panel("Source Artifacts", value = "sources", planned_panel("Source Artifacts")),
    nav_panel("Methodology / Metric Policy", value = "methodology", planned_panel("Methodology / Metric Policy")),
    version_info_tab()
  )
}
