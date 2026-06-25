###############################################################################
# body.R
#
# Propósito (UI ONLY):
#   Definir la estructura visual (dashboardBody / tabItems / tabItem).
#
# Reglas:
#   - NO cocina datos.
#   - NO calcula.
#   - NO carga archivos.
#   - Solo define UI y consume objetos ya en memoria.
#
# Dependencias esperadas en memoria:
#   - Ingresos, Ingresos_mensual, Impuestos, Estacionalidad, etc.
#   - Ano_actual (si no existe, se infiere con Sys.Date()).
#
# Buenas prácticas:
#   - Toda lógica reactiva vive en server.R.
#   - Este archivo debe ser estable aunque cambie el pipeline.
#
# Nota:
#   - Cambios aquí afectan navegación del dashboard.
###############################################################################

# ============================================================================
# UI GLOBAL VARS
# - Ano_actual se usa para títulos. Si no existe, se infiere.
# ============================================================================
if (!exists("Ano_actual")) {
  Ano_actual <- format(Sys.Date(), "%Y")
}

# ============================================================================
# DASHBOARD BODY
# ============================================================================
body <- dashboardBody(
  tags$head(
    tags$script(HTML("
      Shiny.addCustomMessageHandler('toggle-dark-mode', function(message) {
        if (message.active) {
          document.body.classList.add('dark-mode');
        } else {
          document.body.classList.remove('dark-mode');
        }
      });
    ")),
    tags$style(HTML("

      /* ── Header y sidebar modo claro ─────────────────────────────── */
      .skin-blue .main-header .navbar       { background-color: #0ea5e9; }
      .skin-blue .main-header .logo         { background-color: #0ea5e9; }
      .skin-blue .main-sidebar,
      .skin-blue .left-side                 { background-color: #111827; }
      .skin-blue .main-sidebar .sidebar .sidebar-menu > li > a { color: #e5e7eb; }

      /* ── Hover y active del sidebar ──────────────────────────────── */
      .skin-blue .main-sidebar .sidebar .sidebar-menu > li.active > a,
      .skin-blue .main-sidebar .sidebar .sidebar-menu > li > a:hover {
        background-color: #0c4a6e;
        color: #ffffff;
        border-radius: 4px;
        margin: 4px 8px;
      }

      /* ── Mini-sidebar al colapsar ────────────────────────────────── */
      .sidebar-collapse .main-sidebar                                        { width: 60px !important; transform: none !important; }
      .sidebar-collapse .left-side                                           { width: 60px !important; }
      .sidebar-collapse .content-wrapper,
      .sidebar-collapse .main-footer                                         { margin-left: 60px !important; }
      .sidebar-collapse .sidebar-menu > li > a                               { text-align: center !important; padding: 12px 0 !important; display: flex !important; flex-direction: column !important; align-items: center !important; }
      .sidebar-collapse .sidebar-menu > li > a > span                        { display: none !important; }
      .sidebar-collapse .sidebar-menu > li > a > i                           { margin-right: 0 !important; font-size: 18px !important; display: block !important; }
      .sidebar-collapse .sidebar-menu > li.treeview > a > .fa.fa-angle-left  { display: none !important; }

    ")),
    tags$style(HTML("

      /* ── Dark mode general ───────────────────────────────────────── */
      body.dark-mode                                   { background-color: #0f172a; color: #e5e7eb; }
      body.dark-mode .skin-blue .main-header .navbar   { background-color: #111827; }
      body.dark-mode .skin-blue .main-header .logo     { background-color: #111827; }
      body.dark-mode .main-sidebar,
      body.dark-mode .left-side                        { background-color: #020617; }
      body.dark-mode .content-wrapper,
      body.dark-mode .right-side                       { background-color: #0f172a; }
      body.dark-mode .box                              { background-color: #020617; border-color: #1f2937; }
      body.dark-mode .box-header,
      body.dark-mode .box-title,
      body.dark-mode .box-body                         { color: #e5e7eb; }
      body.dark-mode .app-footer                       { background-color: #020617; border-top-color: #1f2937; color: #9ca3af; }

      /* ── Footer modo claro ───────────────────────────────────────── */
      .app-footer {
        position:         fixed;
        bottom:           0;
        left:             0;
        right:            0;
        height:           26px;
        padding:          4px 18px;
        background-color: #f9fafb;
        border-top:       1px solid #e5e7eb;
        color:            #6b7280;
        font-size:        11px;
        z-index:          1000;
      }
      .content-wrapper { padding-bottom: 40px; }

    "))
  ),
  tabItems(

    # ########################################################################
    # TAB: inicio  -----------------------------------------------------------
    # ########################################################################
    tabItem(
      tabName = "inicio",

      # -- Encabezados -------------------------------------------------------
      h1("Análisis de los ingresos nacionales", align = "center"),
      br(),
      h2(
        paste(
          "Fecha de actualización: el",
          substr(Sys.Date(), 9, 10), "-",
          substr(Sys.Date(), 6, 7), "-",
          substr(Sys.Date(), 1, 4),
          ", a las", substr(Sys.time(), 12, 20)
        )
      ),

      br(), br(),

      # -- Contenido ---------------------------------------------------------
      box(
        imageOutput("picture.ingresos", height = "auto")
      )
    ),

    # ########################################################################
    # TAB: defi  -------------------------------------------------------------
    # ########################################################################
    tabItem(
      tabName = "defi",

      # -- Encabezados -------------------------------------------------------
      h1("Definición de ciertos términos presente en el presente Dashboard.", align = "center"),
      br(), br(),

      # -- Tabla -------------------------------------------------------------
      box(
        reactableOutput("conceptos.1")
      )
    ),

    # ########################################################################
    # TAB: alertas  ----------------------------------------------------------
    # Indicadores del ingreso
    # ########################################################################
    tabItem(
      tabName = "alertas",

      # -- Encabezados -------------------------------------------------------
      h1(paste0("Indicadores del ingreso ", Ano_actual, "."), align = "center"),
      br(), br(),
      h2("Importante: los siguientes indicadores son referentes a los ingresos corrientes."),
      br(), br(),

      # -- Indicador 1 -------------------------------------------------------
      h2(paste0("Recaudación acumulada ", Ano_actual, ".")),
      br(),
      fluidRow(
        box(
          title = paste0("Recaudación acumulada al ", Sys.Date()),
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          valueBoxOutput("index1")
        )
      ),

      # -- Indicador 2 -------------------------------------------------------
      h2(paste0("Carga tributaria ", Ano_actual, ".")),
      br(),
      fluidRow(
        box(
          title = paste0("Carga tributaria al ", Sys.Date()),
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          valueBoxOutput("index2")
        )
      ),

      # -- Indicador 3 -------------------------------------------------------
      h2(paste0("Ejecución ", Ano_actual, ".")),
      br(),
      fluidRow(
        box(
          title = paste0("Ejecución al ", Sys.Date()),
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          valueBoxOutput("index3")
        )
      ),

      # -- Indicador 4 -------------------------------------------------------
      h2(paste0("Variación porcentual interanual ", Ano_actual, ".")),
      br(),
      fluidRow(
        box(
          title = paste0("Variación al ", Sys.Date()),
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          valueBoxOutput("index4")
        )
      ),

      # -- Indicador 5 -------------------------------------------------------
      h2(paste0("Variación porcentual acumulada ", Ano_actual, ".")),
      br(),
      fluidRow(
        box(
          title = paste0("Variación porcentual acumulada al ", Sys.Date()),
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          valueBoxOutput("index5")
        )
      ),

      br(),
      # -- Indicador 6 -------------------------------------------------------
      h2(paste0("Variación acumulada al mes ", Ano_actual, ".")),
      br(),
      fluidRow(
        box(
          title = paste0("Variación acumulada al mes ", Sys.Date()),
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          valueBoxOutput("index6")
        )
      ),

      br(), br(),
      h2("Para ver los valores en términos compatirvos en el tiempo, ir a la sección de evolución mensual.")
    ),

    # ########################################################################
    # TAB: HC1  --------------------------------------------------------------
    # Evolución anual del presupuesto
    # ########################################################################


    
    tabItem(
      tabName = "HC1",

      # -- Encabezados -------------------------------------------------------
      h1("Evolución anual del presupuesto: actual, inicial, ajustado e ingresos", align = "center"),
      br(), br(),
      h2(
        "Importante: no se poseen los datos del presupuesto ajustado, de forma anual, del 2007 al 2012, por lo que se este se visualiza a partir
               del 2013 en adelante."
      ),

      # -- Gráfico principal -------------------------------------------------
      fluidRow(
        box(
          title = "Evolución Anual de Ingresos",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HCIA_1", height = "500px")
        )
      ),

      br(), br()
    ),

    # ########################################################################
    # TAB: HC2  --------------------------------------------------------------
    # Evolución mensual (múltiples gráficos)
    # ########################################################################
    tabItem(
      tabName = "HC2",

      # -- Encabezados -------------------------------------------------------
      h1("Evolución del ingreso mensual.", align = "center"),
      br(),

      # -- Gráfico 1: Ingresos mensuales -------------------------------------
      h2("Ingresos mensuales"),
      br(), br(),
      fluidRow(
        box(
          title = "Ingresos Mensuales — Serie Histórica",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HCIM_1", height = "500px")
        )
      ),

      # -- Gráfico 2: Variaciones --------------------------------------------
      h2("Variaciones"),
      br(), br(),
      fluidRow(
        box(
          title = "Comparativo Mensual por Año",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HCIM_2", height = "500px")
        )
      ),

      br(), br(),

      # -- Gráfico 3: Recaudación acumulada ----------------------------------
      h2("Recaudación acumulada"),
      br(),
      fluidRow(
        box(
          title = "Variación Interanual Mensual",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HCIM_3", height = "500px")
        )
      ),

      br(), br(),

      # -- Gráfico 4: Carga tributaria ---------------------------------------
      h2("Carga tributaria"),
      br(),
      fluidRow(
        box(
          title = "Acumulado Mensual",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HCIM_4", height = "500px")
        )
      ),

      br(), br(),

      # -- Gráfico 5: Ejecución mensual --------------------------------------
      h2("Ejecución  mensual"),
      br(),
      fluidRow(
        box(
          title = "Ingresos Mensuales — Detalle",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HCIM_5", height = "500px")
        )
      )
    ),

    # ########################################################################
    # TAB: HC5  --------------------------------------------------------------
    # Impuestos (selección simple)
    # ########################################################################
    tabItem(
      tabName = "HC5",

      # -- Encabezados -------------------------------------------------------
      h1("Prueba de las elecciones de los impuestos", align = "left"),
      br(),
      h2("Selecione los impuestos a partir del impuesto: 'Impuestos a los ingresos y Utilidades-ISR'"),
      br(),

      # -- INPUT: selector de variable (solo columnas válidas) ---------------
      {
        Impuestos_UI <- Impuestos %>%
          dplyr::select(-dplyr::any_of(c("Año", "mes.cod", "mes", "cod_fuentefinanciacion_3")))

        impuestos_raw   <- names(Impuestos_UI)
        impuestos_label <- gsub("_", " ", impuestos_raw)

        selectInput(
          inputId  = "variable",
          label    = "Variables:",
          choices  = setNames(impuestos_raw, impuestos_label),
          selected = if ("Impuesto_a_los_Ingresos_y_Utilidades_ISR" %in% impuestos_raw)
            "Impuesto_a_los_Ingresos_y_Utilidades_ISR"
          else
            impuestos_raw[1]
        )
      },
      br(),

      # -- OUTPUT: gráfico series --------------------------------------------
      h3("Visualización del impuesto en el tiempo"),
      br(), br(),
      fluidRow(
        box(
          title = "Ingresos por Impuesto",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HC_I", height = "500px")
        )
      ),

      # -- OUTPUT: gráfico variación -----------------------------------------
      h3("Visualización de la variación del impuesto en el tiempo"),
      fluidRow(
        box(
          title = "Variación por Impuesto",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HC_VI", height = "500px")
        )
      )
    ),

    # ########################################################################
    # TAB: HC4  --------------------------------------------------------------
    # Avanzado (selección múltiple jerárquica)
    # ########################################################################
    tabItem(
      tabName = "HC4",

      # -- Encabezados -------------------------------------------------------
      h1("Prueba de las elecciones múltiples", align = "center"),

      # -- INPUTS: filtros jerárquicos ---------------------------------------
      selectInput(
        inputId = "f_clase",
        label = "Clase:",
        choices = c(unique(as.character(Ingresos_mensual$clase))),
        selected = "INGRESOS CORRIENTES"
      ),

      selectInput(
        inputId = "f_subclase",
        label = "Subclase:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subclase))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_grupo",
        label = "Grupo:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$grupo))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_subgrupo",
        label = "Subgrupo:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subgrupo))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_partida",
        label = "Partida:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$partida))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_subpartida",
        label = "Subpartida:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subpartida))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_renglon",
        label = "Renglon:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$renglon))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_subrenglon",
        label = "Subrenglon:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subrenglon))),
        selected = "Todo"
      ),

      br(),

      # -- Acción -------------------------------------------------------------
      actionButton("select_2", "Seleccionar"),

      # -- OUTPUT: evolución --------------------------------------------------
      h3("Visualización del gráfico de evolución"),
      fluidRow(
        box(
          title = "Ingresos Avanzado — Serie",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HC_P", height = "500px")
        )
      ),

      # -- OUTPUT: variación --------------------------------------------------
      h3("Visualización de la variación en el tiempo"),
      fluidRow(
        box(
          title = "Variación Avanzado",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("HC_VP", height = "500px")
        )
      )
    ),

# ########################################################################
# TAB: pronos1  -----------------------------------------------------------
# Proyecciones: Total (Nuevo Mundo Fase 3)
# Outputs:
#   - forecast1     (gráfico ganador + bandas)
#   - quality1      (quality card)
#   - GoF.1         (ranking table compacta)
# ########################################################################
tabItem(
  tabName = "pronos1",

  h1("Proyección del Ingreso Mensual Total",
     align = "center",
     style = "font-weight: bold; font-size: 2.4em; margin-bottom: 0.2em;"),
  br(), br(),

  sliderInput(
    "horizonte.1",
    "Meses a pronosticar:",
    min = 1, max = 18, value = 12
  ),
  br(),

  checkboxGroupInput(
    inputId  = "modelos.1",
    label    = "Modelos a comparar:",
    choices  = list(
      "Seasonal Naive (Baseline)"  = "seasonal_naive",
      "ETS"                        = "ets",
      "AutoARIMA"                  = "autoarima",
      "NNETAR"                     = "nnetar",
      "Regresión (trend + season)" = "tslm",
      "Prophet (Meta) — lento"     = "prophet",
      "XGBoost (lag features) — lento" = "xgboost"
    ),
    selected = c("seasonal_naive", "ets", "autoarima", "nnetar", "tslm"),
    inline   = FALSE
  ),
  br(),

  p("Configure los parámetros y presione Seleccionar para ver los resultados.",
    style = "color: #555; font-style: italic; margin-bottom: 8px;"),
  actionButton("select_1", "Seleccionar",
               style = "background-color: #2196F3; color: black; font-weight: bold;"),
  br(),

  h3("Resumen de calidad (quality card)"),
  fluidRow(
    box(
      title = "Modelo Ganador — Quality Card",
      status = "primary",
      solidHeader = TRUE,
      collapsible = TRUE,
      width = 12,
      uiOutput("quality1")
    )
  ),
  br(),

  h3("Ranking de modelos (backtesting rolling-origin)"),
  fluidRow(
    box(
      title = "Bondad de Ajuste — Backtesting",
      status = "primary",
      solidHeader = TRUE,
      collapsible = TRUE,
      width = 12,
      reactableOutput("GoF.1")
    )
  ),
  br(),

  hr(),

  h3(icon("robot"), " Narrativa ejecutiva del pronóstico"),
  fluidRow(
    box(
      title = "Narrativa Ejecutiva con IA",
      status = "primary",
      solidHeader = TRUE,
      collapsible = TRUE,
      width = 12,
      actionButton("btn_narrativa_1", label = tagList(icon("magic"), " Generar narrativa con IA"),
                   class = "btn btn-primary"),
      br(), br(),
      uiOutput("narrativa_pronos1")
    )
  ),
  br(),

  h3("Visualización y proyección (modelo ganador + bandas)"),
  fluidRow(
    box(
      title = "Visualización del Pronóstico",
      status = "primary",
      solidHeader = TRUE,
      collapsible = TRUE,
      width = 12,
      highchartOutput("forecast1")
    )
  ),
  br(),

  h3("Valores pronosticados — modelo ganador"),
  fluidRow(
    box(
      title = "Tabla de Pronóstico — Modelo Ganador",
      status = "primary",
      solidHeader = TRUE,
      collapsible = TRUE,
      width = 12,
      reactableOutput("tabla.forecast1")
    )
  ),

  hr(),

  # -- Consulta de pronóstico por modelo -------------------------------------
  h3("Consultar pronóstico por modelo"),
  selectInput(
    inputId  = "modelo_consulta_1",
    label    = "Modelo:",
    choices  = list(
      "Seasonal Naive (Baseline)"      = "seasonal_naive",
      "ETS"                            = "ets",
      "AutoARIMA"                      = "autoarima",
      "NNETAR"                         = "nnetar",
      "Regresión (trend + season)"     = "tslm",
      "Prophet (Meta) — lento"         = "prophet",
      "XGBoost (lag features) — lento" = "xgboost"
    ),
    selected = "ets"
  ),
  p("Seleccione un modelo y presione el botón para ver sus valores pronosticados.",
    style = "color: #555; font-style: italic; margin-bottom: 8px;"),
  actionButton("ver_modelo_1", "Ver pronóstico",
               style = "background-color: #2196F3; color: black; font-weight: bold;"),
  br(), br(),
  fluidRow(
    box(
      title = "Consulta por Modelo",
      status = "primary",
      solidHeader = TRUE,
      collapsible = TRUE,
      width = 12,
      reactableOutput("tabla.modelo_consulta_1")
    )
  )
),

    # ########################################################################
    # TAB: pronos3  -----------------------------------------------------------
    # Proyecciones: Impuestos
    # ########################################################################
    tabItem(
      tabName = "pronos3",

      # -- Encabezados -------------------------------------------------------
      h1("Proyección del Ingreso Mensual según Impuestos",
         align = "center",
         style = "font-weight: bold; font-size: 2.4em; margin-bottom: 0.2em;"),
      br(),
      h2("Seleccione los impuestos a partir del impuesto: 'Impuestos a los ingresos y Utilidades-ISR'"),
      br(),

      # -- INPUT: selector variable2 -----------------------------------------
      {
        Impuestos_UI_pronos <- Impuestos %>%
          dplyr::select(-dplyr::any_of(c(
            "Año",
            "mes.cod",
            "mes",
            "cod_fuentefinanciacion_3",
            "Fecha"
          )))

        impuestos_raw   <- names(Impuestos_UI_pronos)
        impuestos_label <- gsub("_", " ", impuestos_raw)

        selectInput(
          inputId  = "variable2",
          label    = "Variables:",
          choices  = setNames(impuestos_raw, impuestos_label),
          selected = if ("Impuesto_a_los_Ingresos_y_Utilidades_ISR" %in% impuestos_raw)
            "Impuesto_a_los_Ingresos_y_Utilidades_ISR"
          else
            impuestos_raw[1]
        )
      },

      # -- INPUT: horizonte --------------------------------------------------
      sliderInput(
        "horizonte.3",
        "Meses a pronosticar:",
        min = 1, max = 18, value = 12
      ),
      br(),

      p("Configure los parámetros y presione Seleccionar para ver los resultados.",
        style = "color: #555; font-style: italic; margin-bottom: 8px;"),
      actionButton("select_pronos3", "Seleccionar",
                   style = "background-color: #2196F3; color: black; font-weight: bold;"),
      br(),

      # -- OUTPUT: gráfico forecast ------------------------------------------
      h3("Visualización mensual del ingreso por impuesto"),
      fluidRow(
        box(
          title = "Visualización del Pronóstico por Impuesto",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("forecast3")
        )
      ),

      # -- OUTPUT: GoF --------------------------------------------------------
      h3("Estadísticos de bondad y ajuste"),
      fluidRow(
        box(
          title = "Bondad de Ajuste — 4 Modelos",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          reactableOutput("GoF.3")
        )
      ),

      br(),

      hr(),

      h3(icon("robot"), " Narrativa ejecutiva del pronóstico"),
      fluidRow(
        box(
          title = "Narrativa Ejecutiva con IA",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          tags$p("Presione Seleccionar primero, luego genere la narrativa.",
                 style = "color: #555; font-style: italic;"),
          actionButton("btn_narrativa_3",
                       label = tagList(icon("magic"), " Generar narrativa con IA"),
                       class = "btn btn-primary"),
          br(), br(),
          uiOutput("narrativa_pronos3")
        )
      ),

      br(),

      hr(),

      # -- Consulta de pronóstico por modelo ---------------------------------
      h3("Consultar pronóstico por modelo"),
      selectInput(
        inputId  = "modelo_ver_3",
        label    = "Modelo:",
        choices  = list(
          "ARIMA"     = "arima",
          "ETS"       = "ets",
          "AutoARIMA" = "autoarima",
          "Regresión" = "regresion"
        ),
        selected = "ets"
      ),
      p("Seleccione un modelo y presione el botón para ver sus valores pronosticados.",
        style = "color: #555; font-style: italic; margin-bottom: 8px;"),
      actionButton("ver_modelo_3", "Ver pronóstico",
                   style = "background-color: #2196F3; color: black; font-weight: bold;"),
      br(), br(),
      fluidRow(
        box(
          title = "Consulta por Modelo",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          reactableOutput("tabla.modelo_ver_3")
        )
      )
    ),

    # ########################################################################
    # TAB: pronos4  -----------------------------------------------------------
    # Proyecciones: Avanzado
    # ########################################################################
    tabItem(
      tabName = "pronos4",

      # -- Encabezados -------------------------------------------------------
      h1("Proyección del Ingreso Mensual — Avanzado",
         align = "center",
         style = "font-weight: bold; font-size: 2.4em; margin-bottom: 0.2em;"),
      br(),

      # -- INPUTS: filtros jerárquicos ---------------------------------------
      selectInput(
        inputId = "f_clase_2",
        label = "Clase:",
        choices = c(unique(as.character(Ingresos_mensual$clase))),
        selected = "INGRESOS CORRIENTES"
      ),

      selectInput(
        inputId = "f_subclase_2",
        label = "Subclase:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subclase))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_grupo_2",
        label = "Grupo:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$grupo))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_subgrupo_2",
        label = "Subgrupo:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subgrupo))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_partida_2",
        label = "Partida:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$partida))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_subpartida_2",
        label = "Subpartida:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subpartida))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_renglon_2",
        label = "Renglon:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$renglon))),
        selected = "Todo"
      ),

      selectInput(
        inputId = "f_subrenglon_2",
        label = "Subrenglon:",
        choices = c("Todo", unique(as.character(Ingresos_mensual$subrenglon))),
        selected = "Todo"
      ),

      br(),

      # -- Acción -------------------------------------------------------------
      p("Configure los parámetros y presione Seleccionar para ver los resultados.",
        style = "color: #555; font-style: italic; margin-bottom: 8px;"),
      actionButton("select_3", "Seleccionar",
                   style = "background-color: #2196F3; color: black; font-weight: bold;"),

      # -- INPUT: horizonte --------------------------------------------------
      sliderInput(
        "horizonte.4",
        "Meses a pronosticar:",
        min = 1, max = 18, value = 12
      ),
      br(),

      # -- OUTPUT: gráfico forecast ------------------------------------------
      h3("Visualización mensuales del ingreso"),
      fluidRow(
        box(
          title = "Visualización del Pronóstico Avanzado",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("forecast4")
        )
      ),

      # -- OUTPUT: GoF --------------------------------------------------------
      h3("Estadísticos de bondad y de ajuste"),
      fluidRow(
        box(
          title = "Bondad de Ajuste — 4 Modelos",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          reactableOutput("GoF.4")
        )
      ),

      br(),

      hr(),

      h3(icon("robot"), " Narrativa ejecutiva del pronóstico"),
      fluidRow(
        box(
          title = "Narrativa Ejecutiva con IA",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          tags$p("Presione Seleccionar primero, luego genere la narrativa.",
                 style = "color: #555; font-style: italic;"),
          actionButton("btn_narrativa_4",
                       label = tagList(icon("magic"), " Generar narrativa con IA"),
                       class = "btn btn-primary"),
          br(), br(),
          uiOutput("narrativa_pronos4")
        )
      ),

      br(),

      hr(),

      # -- Consulta de pronóstico por modelo ---------------------------------
      h3("Consultar pronóstico por modelo"),
      selectInput(
        inputId  = "modelo_ver_4",
        label    = "Modelo:",
        choices  = list(
          "ARIMA"     = "arima",
          "ETS"       = "ets",
          "AutoARIMA" = "autoarima",
          "Regresión" = "tslm"
        ),
        selected = "ets"
      ),
      p("Seleccione un modelo y presione el botón para ver sus valores pronosticados.",
        style = "color: #555; font-style: italic; margin-bottom: 8px;"),
      actionButton("ver_modelo_4", "Ver pronóstico",
                   style = "background-color: #2196F3; color: black; font-weight: bold;"),
      br(), br(),
      fluidRow(
        box(
          title = "Consulta por Modelo",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          reactableOutput("tabla.modelo_ver_4")
        )
      )
    ),

    # ########################################################################
    # TAB: SI1  ---------------------------------------------------------------
    # Estacionalidad general
    # ########################################################################
    tabItem(
      tabName = "SI1",

      h1(paste0("Estacionalidad general"), align = "center"),
      br(), br(),
      h2("Las siguientes estacionalidades se llevan a cabo mediante el cálculo del ingresos general o total."),
      br(), br(),

      # -- OUTPUT: Estacionalidad 1 ------------------------------------------
      h3(paste0("Estacionalidad mensual - parámetro")),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Mensual",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_1")
        )
      ),

      # -- OUTPUT: Estacionalidad 2 ------------------------------------------
      h3(paste0("Estacionalidad acumulada - parámetro"), align = "center"),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Acumulada",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_2")
        )
      ),

      # -- OUTPUT: Estacionalidad 3 ------------------------------------------
      h3(paste0("Estacionalidad mensual GC")),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Mensual GC",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_3")
        )
      )
    ),

    # ########################################################################
    # TAB: SI2  ---------------------------------------------------------------
    # Estacionalidad según ingreso tributario
    # ########################################################################
    tabItem(
      tabName = "SI2",

      h1(paste0("Estacional según el Ingreso tributario"), align = "center"),

      # -- OUTPUT: IT_1 -------------------------------------------------------
      h2(paste0("Estacionalidad mensual del Ingreso Tributario - parámetro"), align = "center"),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Ingresos Tributarios",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_IT_1")
        )
      ),

      # -- OUTPUT: IT_2 -------------------------------------------------------
      h2(paste0("Estacionalidad acumulada del Ingreso Tributario - parámetro"), align = "center"),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Tributaria Acumulada",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_IT_2")
        )
      ),

      # -- OUTPUT: IT_3 -------------------------------------------------------
      h2(paste0("Estacionalidad mensual del Ingreso Tributario - GC"), align = "center"),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Tributaria Mensual GC",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_IT_3")
        )
      )
    ),

    # ########################################################################
    # TAB: SI3  ---------------------------------------------------------------
    # Estacionalidad según impuestos
    # ########################################################################
    tabItem(
      tabName = "SI3",

      h1(paste0("Estacional según impuestos"), align = "center"),
      br(),
      h2("Seleccione los impuestos a partir del impuesto: 'Impuestos a los ingresos y Utilidades-ISR' "),
      br(),

      # -- INPUT: selector variable5 -----------------------------------------
      {
        Impuestos_UI_SI3 <- Impuestos %>%
          dplyr::select(-dplyr::any_of(c(
            "Año",
            "mes.cod",
            "mes",
            "cod_fuentefinanciacion_3",
            "Fecha"
          )))

        impuestos_raw   <- names(Impuestos_UI_SI3)
        impuestos_label <- gsub("_", " ", impuestos_raw)

        selectInput(
          inputId  = "variable5",
          label    = "Variables:",
          choices  = setNames(impuestos_raw, impuestos_label),
          selected = if ("Impuesto_a_los_Ingresos_y_Utilidades_ISR" %in% impuestos_raw)
            "Impuesto_a_los_Ingresos_y_Utilidades_ISR"
          else
            impuestos_raw[1]
        )
      },

      # -- OUTPUTS ------------------------------------------------------------
      h2(paste0("Evolución del impuesto"), align = "center"),
      fluidRow(
        box(
          title = "Estacionalidad por Impuesto",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_Impuestos_1")
        )
      ),

      h2(paste0("Estacionalidad mensual de los impuestos - parámetro"), align = "center"),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Impuestos Acumulada",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_Impuestos_2")
        )
      ),

      h2(paste0("Estacionalidad acumulada del impuesto - parámetro"), align = "center"),
      br(),
      fluidRow(
        box(
          title = "Estacionalidad Impuestos Mensual GC",
          status = "primary",
          solidHeader = TRUE,
          collapsible = TRUE,
          width = 12,
          highchartOutput("Estacionalidad_Impuestos_3")
        )
      )
    ),

    # ########################################################################
    # TAB: download  ----------------------------------------------------------
    # Descarga de archivos
    # ########################################################################
    tabItem(
      tabName = "download",

      h1("Descargar achivo de datos.", align = "center"),
      br(), br(),

      # -- Acciones: descargas ------------------------------------------------
      h2("Descarga archivo de los ingresos."),
      actionButton("show2", "Descargar archivo"),
      br(), br(),
      h2("Descarga información de los impuestos."),
      actionButton("show1", "Descargar archivo")
    )

  ),

  tags$div(
    class = "app-footer",
    tags$span("MassiveForecastingIncome v2.0  |  Datos: 2007 - 2024  |  CGR Costa Rica"),
    tags$span(paste0("Actualizado: ", format(Sys.Date(), "%B %Y")),
              style = "float: right;")
  )
)