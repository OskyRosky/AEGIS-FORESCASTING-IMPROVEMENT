# TESSERACT v2 | sidebar.R | collapsible grouped left navigation (Block 7.0C)
# Structure appropriated from MassiveForecasting-V3/sider.R (menuItem/menuSubItem),
# rebuilt in plain Shiny + CSS/JS (no shinydashboard dependency).

stage07_menu <- function() {
  list(
    list(group = "Project", icon = "house", expanded = TRUE, items = list(
      list(value = "home",     label = "Home",     title = "Project Home",       icon = "house", active = TRUE),
      list(value = "overview", label = "Overview", title = "Executive Overview", icon = "gauge-high")
    )),
    list(group = "Forecasting", icon = "chart-line", items = list(
      list(value = "explorer", label = "Viewer", title = "Forecast Viewer",  icon = "chart-line"),
      list(value = "accuracy", label = "Accuracy", title = "Accuracy Overview",  icon = "bullseye"),
      list(value = "forecast", label = "Forecast", title = "Forward Forecast", icon = "arrow-trend-up"),
      list(value = "ttl",      label = "TTL",      title = "TTL / Capacity View", icon = "hourglass-half", planned = TRUE)
    )),
    list(group = "Models", icon = "trophy", items = list(
      list(value = "universe",   label = "Universe",   title = "Model Universe",            icon = "layer-group"),
      list(value = "tournament", label = "Tournament", title = "Tournament Standings",      icon = "chart-column"),
      list(value = "champion",   label = "Champion",   title = "Champion Decision",         icon = "trophy")
    )),
    list(group = "Governance", icon = "scale-balanced", items = list(
      list(value = "risks",      label = "Risks",      title = "Risk Register",       icon = "triangle-exclamation"),
      list(value = "audit",      label = "Audit",      title = "Audit Trail",         icon = "list-ol")
    )),
    list(group = "Reference", icon = "book", items = list(
      list(value = "artifacts",   label = "Artifacts",   title = "Source Artifacts", icon = "folder-open"),
      list(value = "methodology", label = "Methodology", title = "Methodology",      icon = "book-open"),
      list(value = "version",     label = "Version",     title = "Version Info",     icon = "circle-info")
    ))
  )
}

sidebar_group <- function(g) {
  expanded <- isTRUE(g$expanded)
  tags$div(
    class = paste("sidebar-group", if (expanded) "expanded" else ""),
    tags$button(
      type = "button", class = "sidebar-group-header", title = g$group,
      tags$span(class = "sidebar-group-icon", tess_icon(g$icon)),
      tags$span(class = "sidebar-group-label", g$group),
      tags$span(class = "sidebar-group-caret", tess_icon("chevron-down"))
    ),
    tags$div(
      class = "sidebar-sub",
      lapply(g$items, function(it) {
        tags$a(
          href = "#",
          class = paste("sidebar-sublink",
                        if (isTRUE(it$active)) "active" else "",
                        if (isTRUE(it$planned)) "is-planned" else ""),
          `data-section` = it$value, title = it$title,
          tags$span(class = "sidebar-sublink-icon", tess_icon(it$icon)),
          tags$span(class = "sidebar-sublink-label", it$label)
        )
      })
    )
  )
}

app_sidebar <- function() {
  tags$aside(
    class = "app-sidebar",
    tags$div(
      class = "sidebar-brand",
      tags$span(class = "sidebar-brand-dot"),
      tags$span(class = "sidebar-brand-text", "Navigation")
    ),
    tags$nav(
      class = "sidebar-nav",
      lapply(stage07_menu(), sidebar_group)
    )
  )
}
