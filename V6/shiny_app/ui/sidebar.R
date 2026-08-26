# TESSERACT v2 | sidebar.R | collapsible grouped left navigation (Block 7.0C)
# Structure appropriated from MassiveForecasting-V3/sider.R (menuItem/menuSubItem),
# rebuilt in plain Shiny + CSS/JS (no shinydashboard dependency).

# P9N | Product navigation. The V6.24 experience is now the product-facing
# Forecasting and Models module. The two original groups are kept in this file
# for rollback and history but are marked `hidden` so they are not rendered in
# the sidebar. Their sections, server logic and helper functions are untouched
# and still mounted; they are simply unreachable from the navigation.
stage07_menu <- function() {
  list(
    list(group = "Project", icon = "house", expanded = TRUE, items = list(
      list(value = "home",     label = "Home",     title = "Project Home",       icon = "house", active = TRUE),
      list(value = "overview", label = "Overview", title = "Executive Overview", icon = "gauge-high")
    )),
    list(group = "Models", icon = "cubes", items = list(
      list(value = "v24mf_universe", label = "Universe", title = "Models \u2014 Universe", icon = "layer-group"),
      list(value = "v24mf_ranking",  label = "Ranking Diagnostics", title = "Models \u2014 Ranking Diagnostics", icon = "chart-column"),
      list(value = "v24mf_champion", label = "Champion", title = "Models \u2014 Champion", icon = "trophy")
    )),
    list(group = "Forecasting", icon = "chart-line", items = list(
      list(value = "v24_overview", label = "Overview", title = "Forecasting Overview",            icon = "gauge-high"),
      list(value = "v24_viewer",   label = "Viewer",   title = "Forecasting Series Viewer",       icon = "chart-line"),
      list(value = "v24_accuracy", label = "Accuracy", title = "Forecasting Accuracy Diagnostics", icon = "bullseye"),
      list(value = "v24_forecast", label = "Forecast", title = "Governed 30-Step Forecast",       icon = "arrow-trend-up"),
      # Hidden from the sidebar on request. The section, its server outputs and
      # its helpers are untouched and still mounted; only the link is withheld.
      list(value = "v24_taxonomy", label = "Taxonomy", title = "Taxonomy and Availability",       icon = "sitemap", hidden = TRUE)
    )),
    # Superseded by the Models group above. Retained, not rendered.
    list(group = "Models (legacy)", icon = "trophy", hidden = TRUE, items = list(
      list(value = "universe",   label = "Universe",   title = "Model Universe",            icon = "layer-group"),
      list(value = "tournament", label = "Tournament", title = "Tournament Standings",      icon = "chart-column"),
      list(value = "champion",   label = "Champion",   title = "Champion Decision",         icon = "trophy")
    )),
    # Superseded by the Forecasting group above. Retained, not rendered.
    list(group = "Forecasting (legacy)", icon = "chart-line", hidden = TRUE, items = list(
      list(value = "explorer", label = "Viewer", title = "Forecast Viewer",  icon = "chart-line"),
      list(value = "accuracy", label = "Accuracy", title = "Accuracy Overview",  icon = "bullseye"),
      list(value = "forecast", label = "Forecast", title = "Forward Forecast", icon = "arrow-trend-up"),
      list(value = "ttl",      label = "TTL",      title = "TTL / Capacity View", icon = "hourglass-half", planned = TRUE)
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
  items <- Filter(function(it) !isTRUE(it$hidden), g$items)
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
      lapply(items, function(it) {
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
  groups <- Filter(function(g) !isTRUE(g$hidden), stage07_menu())
  tags$aside(
    class = "app-sidebar",
    tags$nav(
      class = "sidebar-nav",
      lapply(groups, sidebar_group)
    )
  )
}
