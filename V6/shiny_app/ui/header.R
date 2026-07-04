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
      class = "app-header-left",
      tags$button(
        id = "hdr-collapse-btn", class = "hdr-tool-btn hdr-collapse-btn",
        type = "button", title = "Collapse / expand sidebar",
        `aria-label` = "Toggle sidebar", tess_icon("bars")
      ),
      tags$div(
        class = "app-header-brand",
        tags$span(class = "app-header-logo", tess_icon("chart-line")),
        tags$span(class = "app-header-title", "AEGIS"),
        tags$span(class = "app-header-subtitle", "Forecast Improvement Platform")
      ),
      tags$div(
        class = "app-header-lastupdate",
        title = paste0(
          "Last update: the most recent time Tesseract data was ingested ",
          "and the forecasting models were computed for this release."
        ),
        tess_icon("rotate"),
        tags$span(class = "lastupdate-label", "Last update"),
        tags$span(class = "lastupdate-value", header_last_update())
      )
    ),
    tags$div(
      class = "app-header-center",
      tags$button(
        id = "hdr-guide-btn", class = "hdr-guide-btn", type = "button",
        title = "Open the guide for the current section",
        `aria-label` = "Open section guide",
        tags$span(class = "hdr-guide-label", id = "hdr-guide-label", "Dashboard Guide"),
        tags$span(class = "hdr-guide-icon", id = "hdr-guide-icon", tess_icon("table-columns"))
      )
    ),
    tags$div(
      class = "app-header-actions",
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
