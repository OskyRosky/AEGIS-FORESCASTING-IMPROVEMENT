# TESSERACT v2 | governance_tab.R | governance navigation panel
governance_tab <- function() {
  nav_panel(
    "Governance",
    icon = icon("shield"),
    div(
      class = "container-fluid py-3 px-4",
      uiOutput("governance_placeholder")
    )
  )
}
