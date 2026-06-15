# TESSERACT v2 | body.R | navbar page composition
source("ui/tabs/overview_tab.R")
source("ui/tabs/forecast_overlay_tab.R")
source("ui/tabs/accuracy_tab.R")
source("ui/tabs/models_tab.R")
source("ui/tabs/backtesting_tab.R")
source("ui/tabs/governance_tab.R")
source("ui/tabs/settings_tab.R")

app_ui <- function() {
  page_navbar(
    title = app_header_title(),
    theme = app_theme,
    navbar_options = navbar_options(bg = APP_COLORS$navbar, theme = "dark"),
    fillable = FALSE,
    header = tagList(
      tags$link(rel = "stylesheet", type = "text/css", href = "custom.css"),
      tags$script(src = "custom.js")
    ),
    nav_spacer(),
    run_context_badge(),
    overview_tab(),
    forecast_overlay_tab(),
    accuracy_tab(),
    models_tab(),
    backtesting_tab(),
    governance_tab()
  )
}
