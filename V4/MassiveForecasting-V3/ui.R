###############################################################################
# ui.R
#
# Propósito:
#   Construir el UI del dashboard (shinydashboard) de forma modular:
#     - header  -> header.R
#     - sidebar -> sidebar.R
#     - body    -> body.R
#
# Reproducibilidad / mantenibilidad:
#   - Este archivo NO debería contener lógica compleja ni UI muy extensa.
#   - Solo ensambla componentes y define estilos globales.
###############################################################################

# =========================
# 1) Librerías (UI only)
# =========================
library(shiny)
library(shinydashboard)

# (Opcional) Si usas widgets en el UI:
# library(shinyWidgets)
# library(shinyjs)

# =========================
# 2) Paths / Sourcing
# =========================
# Recomendación: mantener componentes del UI en /R o /modules (según tu estructura).
# Aquí asumimos que están en la misma carpeta o una subcarpeta "components".
source("header.R",  local = TRUE)
source("sider.R", local = TRUE)
source("body.R",    local = TRUE)

# =========================
# 3) Configuración global
# =========================
APP_TITLE <- "Dashboard de Ingresos"
APP_SKIN  <- "blue"   # opciones: "blue", "black", "purple", "green", "red", "yellow"

# =========================
# 4) UI final (orquestación)
# =========================
ui <- dashboardPage(
  skin    = APP_SKIN,
  header  = header,
  sidebar = sidebar,
  body    = body
)
