# TESSERACT v2 | models_tab.R | model tournament navigation panel
models_tab <- function() {
  nav_panel(
    "Models",
    icon = icon("trophy"),
    div(
      class = "container-fluid py-3 px-4",
      uiOutput("models_placeholder")
    )
  )
}
