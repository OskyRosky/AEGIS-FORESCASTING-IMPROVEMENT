# TESSERACT v2 | backtesting_tab.R | backtesting navigation panel
backtesting_tab <- function() {
  nav_panel(
    "Backtesting",
    icon = icon("rotate"),
    div(
      class = "container-fluid py-3 px-4",
      uiOutput("backtesting_placeholder")
    )
  )
}
