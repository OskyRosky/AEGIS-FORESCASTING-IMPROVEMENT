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
      tess_help_overlay()
    )
  )
}
