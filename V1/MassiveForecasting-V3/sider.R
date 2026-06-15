############################
#          sidebar         #
############################

safe_icon <- function(name) {
  tryCatch(icon(name), error = function(e) icon("circle"))
}

sidebar <- dashboardSidebar(
  collapsed = FALSE,
  sidebarMenu(
    id = "sidebar",
    menuItem("Presentacion",   tabName = "inicio",   icon = safe_icon("chalkboard")),
    menuItem("Definicion",     tabName = "defi",     icon = safe_icon("book")),
    menuItem("Indicadores ingreso", icon = safe_icon("tachometer-alt"),
             startExpanded = FALSE,
             menuSubItem("Indicadores", tabName = "alertas", icon = safe_icon("exclamation-triangle"))
    ),

    menuItem("Evolucion ingresos", icon = safe_icon("chart-line"),
             startExpanded = FALSE,
             menuSubItem("Anuales",   tabName = "HC1", icon = safe_icon("chevron-circle-right")),
             menuSubItem("Mensuales", tabName = "HC2", icon = safe_icon("chevron-circle-right")),
             menuSubItem("Impuestos", tabName = "HC5", icon = safe_icon("chevron-circle-right")),
             menuSubItem("Avanzado",  tabName = "HC4", icon = safe_icon("chevron-circle-right"))
    ),

    #   menuItem("Ingresos clasificador", icon = safe_icon("diagnoses"),
    #            startExpanded = FALSE,
    #            menuSubItem("Clase",                   tabName = "IC1", icon = safe_icon("line")),
    #            menuSubItem("Subclase",                tabName = "IC2", icon = safe_icon("line")),
    #            menuSubItem("Grupo",                   tabName = "IC3", icon = safe_icon("line")),
    #            menuSubItem("Subgrupo",                tabName = "IC4", icon = safe_icon("line")),
    #            menuSubItem("Partida",                 tabName = "IC5", icon = safe_icon("line")),
    #            menuSubItem("Subpartida",              tabName = "IC6", icon = safe_icon("line")),
    #            menuSubItem("Renglón",                 tabName = "IC7", icon = safe_icon("line")),
    #            menuSubItem("Subrenglón",              tabName = "IC8", icon = safe_icon("line")),
    #            menuSubItem("Fuente de Financiación",  tabName = "IC9", icon = safe_icon("line"))
    #   ),

    menuItem("Pronósticos", icon = safe_icon("brain"),
             startExpanded = FALSE,
             menuSubItem("Ingresos totales", tabName = "pronos1", icon = safe_icon("chart-bar")),
             #   menuSubItem("Clasificador",   tabName = "pronos2", icon = safe_icon("chart-bar")),
             menuSubItem("Impuestos",        tabName = "pronos3", icon = safe_icon("chart-bar")),
             menuSubItem("Avanzado",         tabName = "pronos4", icon = safe_icon("sliders-h"))
    ),

    menuItem("Estacionalidad", icon = safe_icon("calendar-alt"),
             startExpanded = FALSE,
             menuSubItem("General",               tabName = "SI1", icon = safe_icon("chart-area")),
             menuSubItem("Ingresos tributarios",  tabName = "SI2", icon = safe_icon("chart-area")),
             menuSubItem("Impuestos",             tabName = "SI3", icon = safe_icon("chart-area"))
    ),

    menuItem("Descargar", tabName = "download", icon = safe_icon("download"))
  )
)
