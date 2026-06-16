# TESSERACT v2 | header.R | dashboard shell header (Block 7.0C)

# Shared safe icon helper (fontawesome with graceful fallbacks).
tess_icon <- function(name, fallback = "circle") {
  out <- tryCatch(shiny::icon(name), error = function(e) NULL)
  if (!is.null(out)) return(out)
  out2 <- tryCatch(shiny::icon(fallback), error = function(e) NULL)
  if (!is.null(out2)) out2 else tags$span(class = "sidebar-bullet", "\u2022")
}

app_header <- function() {
  tags$header(
    class = "app-header",
    tags$div(
      class = "app-header-brand",
      tags$span(class = "app-header-logo", tess_icon("chart-line")),
      tags$span(class = "app-header-title", "TESSERACT v2"),
      tags$span(class = "app-header-subtitle", "Forecast Improvement Platform")
    ),
    tags$div(
      class = "app-header-actions",
      tags$div(
        class = "app-header-badges",
        tags$span(class = "hdr-badge hdr-badge-version", "V1"),
        tags$span(class = "hdr-badge hdr-badge-stage", "Stage 07"),
        tags$span(class = "hdr-badge hdr-badge-readonly", "Read-only")
      ),
      tags$div(
        class = "app-header-tools",
        tags$button(
          id = "hdr-help-btn", class = "hdr-tool-btn", type = "button",
          title = "Help / About", tess_icon("circle-question")
        ),
        tags$a(
          class = "hdr-tool-btn", href = "mailto:oscarau@microsoft.com",
          title = "Comments & suggestions", tess_icon("comment")
        ),
        tags$button(
          id = "hdr-theme-btn", class = "hdr-tool-btn", type = "button",
          title = "Toggle light / dark mode", tess_icon("moon")
        )
      )
    )
  )
}
