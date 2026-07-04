############################
#          header          #
############################

header <- shinydashboard::dashboardHeader(

  # 1) Título con ícono
  title = tags$span(
    icon("chart-line"),
    tags$span("Ingresos CGR", style = "font-weight: 600; margin-left: 6px;")
  ),
  titleWidth = 260,

  # 2) Botón dinámico centrado
  tags$li(
    class = "dropdown",
    style = "position: absolute; left: 50%; transform: translateX(-50%); top: 6px; z-index: 999;",
    uiOutput("header_help_button")
  ),

  # 3) Dropdown de comentarios
  dropdownMenu(
    type       = "messages",
    icon       = icon("comment"),
    badgeStatus = NULL,
    messageItem(
      from    = "Comentarios y sugerencias",
      message = "Envíe sus comentarios por correo",
      icon    = icon("envelope"),
      href    = "mailto:oscarau@microsoft.com"
    )
  ),

  # 4) Switch day/night
  tags$li(
    class = "dropdown",
    style = "padding-top: 8px; padding-right: 10px;",
    shinyWidgets::materialSwitch(
      inputId = "dark_mode",
      label   = NULL,
      value   = FALSE,
      status  = "primary",
      right   = TRUE
    )
  )
)
