# TESSERACT v2 | sidebar.R | Stage 07 left navigation definition

stage07_sections <- function() {
  list(
    list(id = "cover", title = "Cover / Landing", value = "cover"),
    list(id = "executive", title = "Executive Overview", value = "executive"),
    list(id = "champion", title = "Champion Decision", value = "champion"),
    list(id = "conditions", title = "Champion Conditions", value = "conditions"),
    list(id = "universe", title = "Model Universe", value = "universe"),
    list(id = "tournament", title = "Tournament Evidence", value = "tournament"),
    list(id = "pairwise", title = "Pairwise Evidence", value = "pairwise"),
    list(id = "risk", title = "Risk Register", value = "risk"),
    list(id = "deferred", title = "Deferred Models", value = "deferred"),
    list(id = "actions", title = "Governance Actions", value = "actions"),
    list(id = "audit", title = "Audit Trail", value = "audit"),
    list(id = "sources", title = "Source Artifacts", value = "sources"),
    list(id = "methodology", title = "Methodology / Metric Policy", value = "methodology"),
    list(id = "version", title = "Version Info", value = "version")
  )
}

app_sidebar <- function() {
  tags$aside(
    class = "app-sidebar",
    tags$div(
      class = "sidebar-heading",
      tags$div(class = "sidebar-kicker", "Stage 07"),
      tags$div(class = "sidebar-title", "Dashboard Navigation")
    ),
    tags$nav(
      class = "sidebar-nav",
      lapply(
        stage07_sections(),
        function(section) {
          tags$a(
            href = "#",
            class = paste("sidebar-link", if (identical(section$value, "cover")) "active" else ""),
            `data-section` = section$value,
            section$title
          )
        }
      )
    )
  )
}
