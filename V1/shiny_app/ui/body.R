# TESSERACT v2 | body.R | governed navbar page composition
source("ui/sidebar.R")
source("ui/tabs.R")
source("ui/footer.R")

app_ui <- function() {
  do.call(
    page_navbar,
    c(
      list(
        title = app_header_title(),
        theme = app_theme,
        navbar_options = navbar_options(bg = APP_COLORS$navbar, theme = "dark"),
        fillable = FALSE,
        header = tagList(
          tags$link(rel = "stylesheet", type = "text/css", href = "custom.css"),
          tags$script(src = "custom.js")
        ),
        nav_spacer(),
        run_context_badge()
      ),
      stage07_nav_items(),
      list(footer = app_footer())
    )
  )
}
