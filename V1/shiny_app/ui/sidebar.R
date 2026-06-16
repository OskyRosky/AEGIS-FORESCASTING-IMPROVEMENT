# TESSERACT v2 | sidebar.R | collapsible grouped left navigation (Block 7.0C)
# Structure appropriated from MassiveForecasting-V3/sider.R (menuItem/menuSubItem),
# rebuilt in plain Shiny + CSS/JS (no shinydashboard dependency).

stage07_menu <- function() {
  list(
    list(group = "Overview", icon = "gauge-high", expanded = TRUE, items = list(
      list(value = "dashboard", title = "Dashboard",          icon = "table-columns", active = TRUE),
      list(value = "executive", title = "Executive Overview", icon = "chart-line")
    )),
    list(group = "Champion & Models", icon = "trophy", items = list(
      list(value = "champion",   title = "Champion",            icon = "trophy"),
      list(value = "conditions", title = "Champion Conditions", icon = "list-check"),
      list(value = "universe",   title = "Model Universe",      icon = "layer-group")
    )),
    list(group = "Evidence", icon = "clipboard-check", items = list(
      list(value = "tournament", title = "Tournament Evidence", icon = "chart-column"),
      list(value = "pairwise",   title = "Pairwise Evidence",   icon = "code-compare"),
      list(value = "risk",       title = "Risk Register",       icon = "triangle-exclamation")
    )),
    list(group = "Governance", icon = "scale-balanced", items = list(
      list(value = "actions", title = "Governance Actions", icon = "gavel"),
      list(value = "audit",   title = "Audit Trail",        icon = "list-ol")
    )),
    list(group = "Reference", icon = "book", items = list(
      list(value = "sources",     title = "Source Artifacts", icon = "folder-open"),
      list(value = "methodology", title = "Methodology",      icon = "book-open"),
      list(value = "version",     title = "Version Info",     icon = "circle-info")
    ))
  )
}

sidebar_group <- function(g) {
  expanded <- isTRUE(g$expanded)
  tags$div(
    class = paste("sidebar-group", if (expanded) "expanded" else ""),
    tags$button(
      type = "button", class = "sidebar-group-header",
      tags$span(class = "sidebar-group-icon", tess_icon(g$icon)),
      tags$span(class = "sidebar-group-label", g$group),
      tags$span(class = "sidebar-group-caret", tess_icon("chevron-down"))
    ),
    tags$div(
      class = "sidebar-sub",
      lapply(g$items, function(it) {
        tags$a(
          href = "#",
          class = paste("sidebar-sublink", if (isTRUE(it$active)) "active" else ""),
          `data-section` = it$value,
          tags$span(class = "sidebar-sublink-icon", tess_icon(it$icon)),
          tags$span(class = "sidebar-sublink-label", it$title)
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
