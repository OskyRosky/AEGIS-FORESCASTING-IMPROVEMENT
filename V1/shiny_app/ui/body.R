# TESSERACT v2 | body.R | governed left-sidebar page composition
source("ui/sidebar.R")
source("ui/tabs.R")
source("ui/footer.R")

app_ui <- function() {
  page_fillable(
    theme = app_theme,
    fillable = FALSE,
    tags$link(rel = "stylesheet", type = "text/css", href = "custom.css"),
    tags$script(src = "custom.js"),
    div(
      class = "tess-app",
      app_header(),
      div(
        class = "app-main",
        app_sidebar(),
        tags$main(
          class = "app-content",
          stage07_tabset()
        )
      ),
      app_footer()
    )
  )
}
