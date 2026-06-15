# TESSERACT v2 | accuracy_tab.R | accuracy navigation panel
accuracy_tab <- function() {
  nav_panel(
    "Accuracy",
    icon = icon("bullseye"),
    div(
      class = "container-fluid py-3 px-4",
      uiOutput("accuracy_placeholder")
    )
  )
}
