###############################################################################
# server.R
#
# Propósito:
#   Implementar la lógica del servidor (Server Logic) para el Dashboard Shiny.
#   Este archivo contiene la definición de:
#     - server <- function(input, output, session) { ... }
#   y toda la lógica reactiva asociada a:
#     - renderPlot / renderHighchart / renderReactable / renderValueBox
#     - observe / observeEvent
#     - reactive / reactiveVal / eventReactive
#     - descargas (downloadHandler) y cualquier procesamiento mínimo requerido
#       para alimentar visualizaciones (sin sustituir el pipeline de datos).
#
# Alcance:
#   - Cálculo de indicadores (KPIs) y métricas mostradas en valueBoxOutput().
#   - Construcción de series y tablas para gráficos/outputs del UI.
#   - Manejo de inputs de usuario (selectInput, varSelectInput, sliderInput,
#     actionButton, etc.) y su impacto en los outputs.
#   - Reglas de filtrado y segmentación (por clase, subclase, impuesto, etc.).
#
# Diseño:
#   - Separación de responsabilidades:
#       * body.R  -> estructura visual (UI) y navegación
#       * server.R -> lógica reactiva, cálculos y outputs
#       * scripts/pipeline (importacion.R u otros) -> ingestión y preparación
#         canónica de datos
#   - Idealmente, server.R NO debe:
#       * leer archivos desde disco en cada interacción
#       * rehacer transformaciones pesadas dentro de reactives
#       * duplicar lógica que pertenece al pipeline de datos
#
# Dependencias esperadas:
#   - Objetos ya cargados en memoria antes de ejecutar server():
#       * data frames / listas utilizados por el UI (Ingresos, Ingresos_mensual,
#         Impuestos, tablas auxiliares, etc.)
#   - Librerías utilizadas por los outputs (ej. shiny, shinydashboard, highcharter,
#     reactable, dplyr, lubridate, forecast u otras, según aplique).
#   - IDs de outputs definidos en body.R (deben coincidir exactamente).
#
# Buenas prácticas:
#   - Mantener los nombres de outputs consistentes con el UI:
#       output$<id> debe existir para cada *Output("<id>") en body.R.
#   - Evitar imprimir tablas grandes en consola; preferir logs controlados.
#   - Encapsular cálculos reutilizables en funciones internas o helpers.
#   - Proteger contra valores nulos/NA y casos borde (filtros vacíos, etc.).
#
# Notas de mantenimiento:
#   - Si se cambia un tabName, inputId u outputId en body.R,
#     es obligatorio reflejarlo aquí.
#   - Si se agregan nuevos módulos/indicadores, documentar los IDs y la lógica.
###############################################################################

## ============================================================
# Helpers (defensive utilities)
# ============================================================
# Nota:
# - Estos helpers son "puros" (sin side-effects) salvo:
#   * assert_has_cols() -> stop() temprano si falta estructura
#   * to_ts() -> usa validate()/need() porque se ejecuta típicamente dentro
#     de contextos reactivos (Shiny), y así falla de forma controlada en UI.
# - Requieren que dplyr + lubridate estén cargados (vía Librerias.R).
# ============================================================

# ---- Parsing & coercion ------------------------------------------------------

safe_na_num <- function(x) {
  # Coerce to numeric safely; turn non-parsable into NA
  suppressWarnings(as.numeric(x))
}

.safe_as_date <- function(x) {
  # as.Date() puede tirar error (stop). Esto lo vuelve "seguro".
  tryCatch(as.Date(x), error = function(e) rep(NA_Date_, length(x)))
}

safe_parse_date <- function(x) {
  # Accept Date, POSIXct, POSIXt, or character; try multiple formats
  if (inherits(x, "Date")) return(x)
  if (inherits(x, c("POSIXct", "POSIXt"))) return(as.Date(x))

  x <- as.character(x)

  # 1) Try default as.Date() (often handles YYYY-MM-DD)
  out <- suppressWarnings(.safe_as_date(x))

  # 2) Try explicit formats if still all NA
  if (all(is.na(out))) {
    out <- suppressWarnings(.safe_as_date(as.Date(x, format = "%Y-%m-%d")))
  }
  if (all(is.na(out))) {
    out <- suppressWarnings(.safe_as_date(as.Date(x, format = "%d/%m/%Y")))
  }

  out
}

# ---- Month parsing (robust) --------------------------------------------------
# Objetivo:
# - Resolver el caso que te explotó: "character string is not in a standard unambiguous format"
# - Proveer una forma canónica de obtener Fecha_ord mensual (YYYY-MM-01)
#   priorizando (Año, mes.cod), y fallback a Fecha.

.clean_int <- function(x) {
  # Limpia a entero (quita todo lo que no sea dígito)
  suppressWarnings(as.integer(gsub("[^0-9]", "", trimws(as.character(x)))))
}

parse_month_date <- function(year, month) {
  # (Año, mes) -> Date (primer día del mes), robusto
  yy <- .clean_int(year)
  mm <- .clean_int(month)

  ok <- is.finite(yy) & is.finite(mm) & !is.na(yy) & !is.na(mm) &
    mm >= 1 & mm <= 12 & yy >= 1900 & yy <= 2100

  out <- rep(NA_Date_, length(yy))
  out[ok] <- .safe_as_date(sprintf("%04d-%02d-01", yy[ok], mm[ok]))
  out
}

parse_fecha_to_month <- function(x) {
  # x puede ser Date/POSIXct/character
  if (inherits(x, "Date")) {
    return(as.Date(format(x, "%Y-%m-01")))
  }
  if (inherits(x, "POSIXt")) {
    return(as.Date(format(as.Date(x), "%Y-%m-01")))
  }

  s <- trimws(as.character(x))
  s[s == ""] <- NA_character_

  # Normalizar separadores
  s2 <- gsub("\\.", "-", s)
  s2 <- gsub("/", "-", s2)

  # Caso YYYYMM (ej 202401)
  is_yyyymm <- grepl("^\\d{6}$", s2)
  if (any(is_yyyymm, na.rm = TRUE)) {
    yy <- substr(s2[is_yyyymm], 1, 4)
    mm <- substr(s2[is_yyyymm], 5, 6)
    s2[is_yyyymm] <- paste0(yy, "-", mm, "-01")
  }

  # Caso YYYY-MM o YYYY-M (agregamos -01)
  is_yyyymm2 <- grepl("^\\d{4}-\\d{1,2}$", s2)
  if (any(is_yyyymm2, na.rm = TRUE)) {
    s2[is_yyyymm2] <- paste0(s2[is_yyyymm2], "-01")
  }

  # Caso YYYY-MM-DD (forzamos day=01)
  is_yyyymmdd <- grepl("^\\d{4}-\\d{1,2}-\\d{1,2}$", s2)
  if (any(is_yyyymmdd, na.rm = TRUE)) {
    yy <- sub("^([0-9]{4}).*$", "\\1", s2[is_yyyymmdd])
    mm <- sub("^[0-9]{4}-([0-9]{1,2}).*$", "\\1", s2[is_yyyymmdd])
    mm <- sprintf("%02d", as.integer(mm))
    s2[is_yyyymmdd] <- paste0(yy, "-", mm, "-01")
  }

  .safe_as_date(s2)
}

extract_month_dates <- function(df) {
  # Extrae Fecha_ord de forma robusta:
  # 1) Usa Año + mes.cod si existen (fila a fila)
  # 2) Completa faltantes con Fecha si existe
  # 3) Si sigue faltando, error explícito con diagnóstico
  stopifnot(is.data.frame(df))

  out <- rep(NA_Date_, nrow(df))

  # 1) Año + mes.cod (fila a fila)
  if (all(c("Año", "mes.cod") %in% names(df))) {
    out <- parse_month_date(df$Año, df$`mes.cod`)
  }

  # 2) Fallback con Fecha (solo donde falte)
  if ("Fecha" %in% names(df) && any(is.na(out))) {
    fd <- parse_fecha_to_month(df$Fecha)
    out[is.na(out)] <- fd[is.na(out)]
  }

  # 3) Diagnóstico
  if (any(is.na(out))) {
    cols_show <- intersect(c("Año", "mes.cod", "Fecha"), names(df))
    sample <- utils::head(df[, cols_show, drop = FALSE], 10)

    msg <- c(
      "No se pudo construir Fecha_ord (mensual) de forma válida para todas las filas.",
      "Revisá columnas `Año` y `mes.cod` (mes 1..12) o proveé `Fecha` parseable.",
      "Ejemplos (primeras 10 filas):",
      paste(capture.output(print(sample)), collapse = "\n")
    )
    stop(paste(msg, collapse = "\n"), call. = FALSE)
  }

  out
}

# ---- Structural validation ---------------------------------------------------

assert_has_cols <- function(df, cols, ctx = "dataset") {
  missing <- setdiff(cols, names(df))
  if (length(missing) > 0) {
    stop(
      paste0(
        "Missing column(s) in ", ctx, ": ",
        paste(missing, collapse = ", ")
      ),
      call. = FALSE
    )
  }
  invisible(TRUE)
}

# ---- Time series helpers -----------------------------------------------------

# Convert a data.frame with (date, value) to a ts object
to_ts <- function(df, date_col = "date", value_col = "value", freq = 12) {
  assert_has_cols(df, c(date_col, value_col), ctx = "time series frame")

  d <- df %>%
    dplyr::mutate(
      .date  = safe_parse_date(.data[[date_col]]),
      .value = safe_na_num(.data[[value_col]])
    ) %>%
    dplyr::filter(!is.na(.date), !is.na(.value)) %>%
    dplyr::arrange(.date)

  # Shiny-friendly validation (fails "softly" in UI when used inside render*)
  validate(
    need(
      nrow(d) >= max(10, freq * 2),
      paste0(
        "Not enough observations for frequency=", freq,
        ". Need at least ", max(10, freq * 2), " rows."
      )
    )
  )

  # Determine start (year, period) from first date
  start_year <- lubridate::year(d$.date[1])

  if (freq == 1) {
    start <- c(start_year, 1)
  } else if (freq == 4) {
    start <- c(start_year, lubridate::quarter(d$.date[1]))
  } else if (freq == 12) {
    start <- c(start_year, lubridate::month(d$.date[1]))
  } else if (freq == 52) {
    start <- c(start_year, lubridate::isoweek(d$.date[1]))
  } else if (freq == 365) {
    start <- c(start_year, lubridate::yday(d$.date[1]))
  } else {
    # Fallback: assume monthly-like start
    start <- c(start_year, lubridate::month(d$.date[1]))
  }

  stats::ts(d$.value, start = start, frequency = freq)
}

# Map UI selection to ts frequency
freq_from_ui <- function(freq_key) {
  switch(
    freq_key,
    "Daily"     = 365,
    "Weekly"    = 52,
    "Monthly"   = 12,
    "Quarterly" = 4,
    "Yearly"    = 1,
    12
  )
}

# Seasonality period mapping aligned to freq
seasonality_period <- function(season_key, freq) {
  switch(
    season_key,
    "None"      = NA_integer_,
    "ByFreq"    = as.integer(freq),
    "Weekly"    = 52L,
    "Monthly"   = 12L,
    "Quarterly" = 4L,
    "Yearly"    = 1L,
    as.integer(freq)
  )
}

# ---- Aggregations ------------------------------------------------------------

# Robust summarize wrapper (safe sum + na.rm)
safe_summarize_numeric <- function(df, cols) {
  df %>%
    dplyr::summarise(
      dplyr::across(
        dplyr::all_of(cols),
        ~ sum(safe_na_num(.x), na.rm = TRUE),
        .names = "sum_{.col}"
      )
    )
}

  # ========================================================================
  #                          Inicio del server   
  # ========================================================================


server <- function(input, output, session) {

  # ========================================================================
  # Header: botón dinámico según tab activo
  # ========================================================================
  output$header_help_button <- renderUI({
    label_text <- switch(input$sidebar,
      "inicio"   = "Bienvenido",
      "defi"     = "Definiciones",
      "alertas"  = "Indicadores",
      "HC1"      = "Evolución Anual",
      "HC2"      = "Evolución Mensual",
      "HC5"      = "Impuestos",
      "HC4"      = "Vista Avanzada",
      "pronos1"  = "Ingresos Totales",
      "pronos3"  = "Pronóstico Impuestos",
      "pronos4"  = "Pronóstico Avanzado",
      "SI1"      = "Estacionalidad General",
      "SI2"      = "Ingresos Tributarios",
      "SI3"      = "Estacionalidad Impuestos",
      "download" = "Descargar Datos",
      "Bienvenido"
    )

    actionButton(
      inputId = "header_info_btn",
      label   = tagList(
        icon("info-circle"),
        tags$span(label_text, style = "font-size: 15px; font-weight: 600;")
      ),
      class = "btn btn-success",
      style = "padding: 8px 24px; border-radius: 8px;"
    )
  })

  # ========================================================================
  # Header: modal informativo según tab activo
  # ========================================================================
  observeEvent(input$header_info_btn, {
    tab <- input$sidebar

    modal_content <- if (tab == "inicio" || is.null(tab)) {
      modalDialog(
        title     = "Bienvenido al Dashboard de Ingresos",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Bienvenido al Dashboard de Ingresos Fiscales de Costa Rica. Este sistema analiza el comportamiento histórico de los ingresos del gobierno central desde 2007 hasta 2024, utilizando datos oficiales procesados por la Contraloría General de la República. El dashboard permite explorar tendencias, comparar períodos, analizar estacionalidad y consultar pronósticos generados con modelos estadísticos avanzados con backtesting rolling-origin.")
      )
    } else if (tab == "defi") {
      modalDialog(
        title     = "Definiciones y Glosario",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Esta sección presenta el glosario oficial de los conceptos utilizados en el dashboard. Encontrará definiciones de ingresos tributarios, no tributarios, impuestos directos e indirectos, así como las métricas de pronóstico utilizadas como wMAPE, sMAPE, RMSE y MAE. Es el punto de partida recomendado para usuarios que se acercan por primera vez al análisis fiscal.")
      )
    } else if (tab == "alertas") {
      modalDialog(
        title     = "Indicadores de Ingresos",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Panel de indicadores clave de desempeño fiscal. Muestra el resumen ejecutivo del comportamiento de los ingresos: totales acumulados, variación interanual, comparativo contra períodos anteriores y alertas de comportamiento atípico. Diseñado para una lectura rápida del estado actual de la recaudación.")
      )
    } else if (tab %in% c("HC1", "HC2", "HC5", "HC4")) {
      modalDialog(
        title     = "Evolución de Ingresos",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Módulo de análisis histórico de ingresos. Contiene visualizaciones anuales y mensuales del comportamiento de la recaudación desde 2007. Permite identificar tendencias de largo plazo, ciclos económicos, impacto de eventos externos y comparar el desempeño entre años. Incluye vistas por impuesto y análisis avanzado desagregado.")
      )
    } else if (tab %in% c("pronos1", "pronos3", "pronos4")) {
      modalDialog(
        title     = "Motor de Pronósticos",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Motor de pronóstico fiscal basado en 8 modelos estadísticos y de machine learning: Seasonal Naive, ARIMA, ETS, AutoARIMA, NNETAR, TSLM, Prophet y XGBoost. El modelo ganador se selecciona automáticamente mediante backtesting rolling-origin con horizonte de 12 meses. Los resultados están precomputados para garantizar respuesta instantánea.")
      )
    } else if (tab %in% c("SI1", "SI2", "SI3")) {
      modalDialog(
        title     = "Análisis de Estacionalidad",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Análisis de patrones estacionales de los ingresos fiscales. Identifica en qué meses del año se concentra históricamente la recaudación, calcula el peso porcentual de cada mes sobre el total anual y compara el patrón actual contra el promedio histórico. Información clave para la planificación presupuestaria.")
      )
    } else if (tab == "download") {
      modalDialog(
        title     = "Descarga de Datos",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Descarga de los datasets canonizados utilizados en el dashboard. Los archivos están procesados, limpios y listos para análisis externos en R, Excel o cualquier herramienta de análisis de datos. Incluye series mensuales de ingresos totales, por impuesto y clasificación avanzada para el período 2007-2024.")
      )
    } else {
      modalDialog(
        title     = "Bienvenido al Dashboard de Ingresos",
        easyClose = TRUE,
        size      = "m",
        footer    = modalButton("Cerrar"),
        p("Bienvenido al Dashboard de Ingresos Fiscales de Costa Rica. Este sistema analiza el comportamiento histórico de los ingresos del gobierno central desde 2007 hasta 2024, utilizando datos oficiales procesados por la Contraloría General de la República. El dashboard permite explorar tendencias, comparar períodos, analizar estacionalidad y consultar pronósticos generados con modelos estadísticos avanzados con backtesting rolling-origin.")
      )
    }

    showModal(modal_content)
  })

  # ========================================================================
  # Narrativa IA — pronos1
  # ========================================================================

  ollama_generate <- function(
    prompt,
    model = Sys.getenv("OLLAMA_MODEL", "llama3.2:3b"),
    host  = Sys.getenv("OLLAMA_HOST",  "http://localhost:11434")
  ) {
    stopifnot(is.character(prompt), length(prompt) == 1)

    url  <- paste0(host, "/api/generate")
    body <- list(model = model, prompt = prompt, stream = FALSE)

    out  <- httr2::request(url) |>
      httr2::req_body_json(body) |>
      httr2::req_perform() |>
      httr2::resp_body_json()

    out$response
  }

  .safe_ollama_call <- function(prompt) {
    tryCatch(
      ollama_generate(prompt),
      error = function(e) {
        showNotification(
          conditionMessage(e),
          type     = "error",
          duration = 10
        )
        NULL
      }
    )
  }

  .build_prompt_pronos1 <- function(bundle) {
    modelo      <- bundle$winner$label
    wmape       <- round(bundle$winner$metrics$wMAPE_mean, 2)
    score       <- round(bundle$winner$score, 2)
    h           <- length(bundle$forecast_final$mean)
    ultimo_obs  <- round(tail(as.numeric(bundle$y), 1), 1)
    fc_vals     <- round(as.numeric(bundle$forecast_final$mean), 1)
    primeros_3  <- fc_vals[1:3]
    ultimos_3   <- tail(fc_vals, 3)

    paste0(
      "Eres un analista fiscal experto en ingresos del gobierno de Costa Rica. ",
      "Con base en los siguientes datos de pronóstico de ingresos totales, ",
      "redacta un párrafo ejecutivo claro y profesional de máximo 120 palabras.\n\n",
      "Datos del pronóstico:\n",
      "- Modelo ganador: ", modelo, "\n",
      "- wMAPE promedio (error backtesting): ", wmape, "%\n",
      "- Score compuesto: ", score, "\n",
      "- Horizonte de pronóstico: ", h, " meses\n",
      "- Último valor observado (millones CRC): ", ultimo_obs, "\n",
      "- Primeros 3 meses pronosticados (millones CRC): ",
        paste(primeros_3, collapse = ", "), "\n",
      "- Últimos 3 meses del horizonte (millones CRC): ",
        paste(ultimos_3, collapse = ", "), "\n\n",
      "Redacta el párrafo de forma directa, sin bullets, en español formal. ",
      "Menciona el modelo utilizado, el nivel de confianza basado en el wMAPE, ",
      "y la tendencia esperada de los ingresos en el horizonte indicado."
    )
  }

  observeEvent(input$btn_narrativa_1, {
    bundle <- .bundle_pronos1()
    req(bundle)

    showNotification(
      "Generando narrativa con IA, por favor espere...",
      type     = "message",
      duration = 8
    )

    prompt     <- .build_prompt_pronos1(bundle)
    resultado  <- .safe_ollama_call(prompt)

    if (!is.null(resultado)) {
      output$narrativa_pronos1 <- renderUI({
        tags$div(
          resultado,
          style = paste(
            "font-size: 15px;",
            "line-height: 1.7;",
            "padding: 12px;",
            "color: #1e293b;",
            "background: #f8fafc;",
            "border-radius: 8px;"
          )
        )
      })
    } else {
      output$narrativa_pronos1 <- renderUI({
        tags$p(
          "No se pudo conectar con Ollama. Verifique que esté corriendo.",
          style = "color: red;"
        )
      })
    }
  })

  # ========================================================================
  # Dark mode: enviar mensaje al JS handler
  # ========================================================================
  observe({
    session$sendCustomMessage(
      type    = "toggle-dark-mode",
      message = list(active = isTRUE(input$dark_mode))
    )
  })

  # ========================================================================
  # TAB: inicio
  # Análisis de los ingresos nacionales
  # ========================================================================

  # ------------------------------------------------------------------------
  # Definiciones / Conceptos
  # ------------------------------------------------------------------------
  # Output:
  #   - conceptos.1  (reactable)
  #
  # Dependencias esperadas en memoria:
  #   - conceptos : data.frame con definiciones conceptuales
  #
  # Responsabilidad:
  #   - Mostrar tabla de conceptos.
  #   - NO transformar datos.
  # ------------------------------------------------------------------------
  
  output$conceptos.1 <- renderReactable({
    reactable(conceptos)
  })


  # ========================================================================
  # TAB: defi
  # Definición de ciertos términos presente en el Dashboard
  # (UI: tabName = "defi")
  # ========================================================================

  # ------------------------------------------------------------------------
  # Tabla de conceptos (definiciones)
  # ------------------------------------------------------------------------
  # Output (debe existir en body.R):
  #   - reactableOutput("conceptos.1")
  #
  # Dependencias esperadas en memoria:
  #   - conceptos : data.frame con las columnas de definiciones
  #
  # Responsabilidad:
  #   - Renderizar la tabla de conceptos tal cual.
  #   - NO transforma datos.
  # ------------------------------------------------------------------------
  
  output$picture.ingresos <- renderImage({
    list(
      src = file.path("www", "ingresos.png"),
      contentType = "image/png",
      alt = "Ingresos"
    )
  }, deleteFile = FALSE)
  
  # ========================================================================
  # TAB: alertas
  # Indicadores del ingreso
  # (UI: tabName = "alertas")
  # ========================================================================

  # ------------------------------------------------------------------------
  # Helper interno: valueBox robusto
  # - Acepta:
  #   * numeric
  #   * data.frame con columna "Ingresos"
  #   * data.frame sin "Ingresos" -> usa 1ra columna numérica disponible
  # ------------------------------------------------------------------------
  .fmt_valuebox_num <- function(x, acc = 0.1, suffix = "", icon_name = "money",
                               color = "blue", width = 3,
                               big_mark = ".", dec_mark = ",") {

    # Caso A: data.frame (idealmente con columna Ingresos)
    if (is.data.frame(x)) {

      if ("Ingresos" %in% names(x)) {
        x <- x %>%
          dplyr::mutate(
            Ingresos = scales::number(
              suppressWarnings(as.numeric(.data$Ingresos)),
              accuracy = acc,
              big.mark = big_mark,
              decimal.mark = dec_mark
            )
          )

        return(valueBox(
          value = x,
          subtitle = suffix,
          icon = icon(icon_name),
          color = color,
          width = width
        ))
      }

      # Fallback: no existe "Ingresos" -> usar primera columna numérica
      num_cols <- names(x)[vapply(x, function(z) is.numeric(z) || is.integer(z), logical(1))]
      if (length(num_cols) == 0) {
        # Último fallback: intentar convertir primera columna
        v <- suppressWarnings(as.numeric(x[[1]]))
      } else {
        v <- x[[num_cols[1]]]
      }

      v <- scales::number(
        suppressWarnings(as.numeric(v)),
        accuracy = acc,
        big.mark = big_mark,
        decimal.mark = dec_mark
      )

      return(valueBox(
        value = v,
        subtitle = suffix,
        icon = icon(icon_name),
        color = color,
        width = width
      ))
    }

    # Caso B: numeric
    v <- round(suppressWarnings(as.numeric(x)), 1)
    valueBox(
      value = v,
      subtitle = suffix,
      icon = icon(icon_name),
      color = color,
      width = width
    )
  }
  
   # ------------------------------------------------------------------------
  # Indicador 1: Recaudación acumulada
  # Output:
  #   - valueBoxOutput("index1")
  #
  # Dependencias esperadas en memoria:
  #   - indicador.1 (data.frame con columna Ingresos)
  #   - Millones (escala numérica para millones)
  # ------------------------------------------------------------------------
  output$index1 <- renderValueBox({
    ind1 <- round(indicador.1 / Millones, 1)
    .fmt_valuebox_num(
      x = ind1,
      acc = 0.1,
      suffix = "(en millones)",
      icon_name = "money",
      color = "purple",
      width = 3
    )
  })


  # ------------------------------------------------------------------------
  # Indicador 2: Carga tributaria
  # Output:
  #   - valueBoxOutput("index2")
  #
  # Dependencias esperadas en memoria:
  #   - indicador.2 (data.frame con columna Ingresos)
  # ------------------------------------------------------------------------
  output$index2 <- renderValueBox({
    ind2 <- round(indicador.2, 1)
    .fmt_valuebox_num(
      x = ind2,
      acc = 0.1,
      suffix = "(en porcentaje)",
      icon_name = "money",
      color = "green",
      width = 3
    )
  })


  # ------------------------------------------------------------------------
  # Indicador 3: Ejecución
  # Output:
  #   - valueBoxOutput("index3")
  #
  # Dependencias esperadas en memoria:
  #   - indicador.3 (data.frame con columna Ingresos)
  # ------------------------------------------------------------------------
  output$index3 <- renderValueBox({
    ind3 <- round(indicador.3, 1)
    .fmt_valuebox_num(
      x = ind3,
      acc = 0.1,
      suffix = "(en porcentaje)",
      icon_name = "money",
      color = "green",
      width = 3
    )
  })


  # ------------------------------------------------------------------------
  # Indicador 4: Variación porcentual interanual
  # Output:
  #   - valueBoxOutput("index4")
  #
  # Dependencias esperadas en memoria:
  #   - indicador.4 (numeric o data.frame)
  # ------------------------------------------------------------------------
  output$index4 <- renderValueBox({
    ind4 <- round(indicador.4, 1)
    .fmt_valuebox_num(
      x = ind4,
      suffix = "(en porcentaje)",
      icon_name = "money",
      color = "blue",
      width = 3
    )
  })


  # ------------------------------------------------------------------------
  # Indicador 5: Variación porcentual acumulada
  # Output:
  #   - valueBoxOutput("index5")
  #
  # Dependencias esperadas en memoria:
  #   - indicador.5 (numeric o data.frame)
  # ------------------------------------------------------------------------
  output$index5 <- renderValueBox({
    ind5 <- round(indicador.5, 1)
    .fmt_valuebox_num(
      x = ind5,
      suffix = "(en porcentaje)",
      icon_name = "money",
      color = "blue",
      width = 3
    )
  })


  # ------------------------------------------------------------------------
  # Indicador 6: Variación acumulada al mes
  # Output:
  #   - valueBoxOutput("index6")
  #
  # Dependencias esperadas en memoria:
  #   - indicador.6 (numeric o data.frame)
  # ------------------------------------------------------------------------
  output$index6 <- renderValueBox({
    ind6 <- round(indicador.6, 1)
    .fmt_valuebox_num(
      x = ind6,
      suffix = "(en porcentaje)",
      icon_name = "weed",
      color = "green",
      width = 3
    )
  })
  

  
  ###########################################
  #      Evolucion de los presupuestos      #
  ###########################################
  # ========================================================================
  # TAB: HC1  --------------------------------------------------------------
  # Evolución anual del presupuesto: actual, inicial, ajustado e ingresos
  # (UI: tabName = "HC1" | output: HCIA_1)
  # ========================================================================
  #
  # Dependencias esperadas en memoria:
  #   - tabla_1  : data.frame con columnas: Año, Inicial, Actual, Ajustado, Acumulado
  #   - Millones : escalar para convertir colones -> millones (ej. 1000000)
  #
  # Responsabilidad:
  #   - Convertir montos a millones SOLO para visualizar.
  #   - Renderizar gráfico anual con series:
  #       Inicial, Actual, Ajustado, Ingresos acumulados
  # ========================================================================

  # ------------------------------------------------------------------------
  # Helper: base de highchart homogénea para toda la sección HC1/HC2
  # - Mantiene el estilo actual del dashboard
  # - Reduce duplicación de código
  # ------------------------------------------------------------------------
  .hc_base <- function() {
    highchart() %>%
      hc_title(text = "", margin = 20, align = "center",
               style = list(color = "#129", useHTML = TRUE)) %>%
      hc_subtitle(text = "", align = "right",
                  style = list(color = "#634", fontWeight = "bold")) %>%
      hc_credits(enabled = TRUE, text = "") %>%
      hc_legend(align = "left", verticalAlign = "top",
                layout = "vertical", x = 0, y = 100) %>%
      hc_exporting(enabled = TRUE) %>%
      hc_chart(zoomType = "xy")
  }

  # ------------------------------------------------------------------------
  # Helper: asegura columnas mínimas (falla rápido y claro)
  # ------------------------------------------------------------------------
  .assert_cols <- function(df, cols, ctx = "dataset") {
    miss <- setdiff(cols, names(df))
    if (length(miss) > 0) {
      stop(paste0("Faltan columnas en ", ctx, ": ", paste(miss, collapse = ", ")))
    }
    invisible(TRUE)
  }

  output$HCIA_1 <- renderHighchart({

    req(exists("tabla_1"), is.data.frame(tabla_1))
    req(exists("Millones"))

    .assert_cols(tabla_1, c("Año", "Inicial", "Actual", "Ajustado", "Acumulado"), ctx = "tabla_1 (HC1)")

    df_anual <- tabla_1 %>%
      dplyr::mutate(
        Inicial   = round(Inicial  / Millones, 1),
        Actual    = round(Actual   / Millones, 1),
        Ajustado  = round(Ajustado / Millones, 1),
        Acumulado = round(Acumulado / Millones, 1)
      )

    .hc_base() %>%
      hc_tooltip(crosshairs = TRUE, backgroundColor = "#FCFFC5",
                 shared = TRUE, borderWidth = 5) %>%
      hc_xAxis(categories = df_anual$Año, title = list(text = "Años")) %>%
      hc_add_series(name = "Inicial", data = df_anual$Inicial) %>%
      hc_add_series(name = "Actual", data = df_anual$Actual) %>%
      hc_add_series(name = "Ajustado", data = df_anual$Ajustado) %>%
      hc_add_series(name = "Ingresos acumulados", data = df_anual$Acumulado, color = "red") %>%
      hc_yAxis(title = list(text = "Millones de colones"),
               labels = list(format = "{value}"))
  })


  # ========================================================================
  # TAB: HC2  --------------------------------------------------------------
  # Evolución mensual (múltiples gráficos)
  # (UI: tabName = "HC2" | outputs: HCIM_1..HCIM_5)
  # ========================================================================
  #
  # Dependencias esperadas en memoria:
  #   - tabla_2                   : data.frame con Fecha, Ingresos
  #   - tabla_2_var               : data.frame con Fecha, var.Ingresos, var.acum_12, var.cum_ano_Ingresos
  #   - tabla.evo.mensual.1_acum  : data.frame con Fecha, cum_ingresos (colones)
  #   - tabla.evo.mensual.2_acum  : data.frame con Fecha, `Carga tributaria`
  #   - tabla.evo.mensual.3_acum  : data.frame con Fecha, `Ejecucion`
  #   - Millones                  : escalar colones -> millones
  #
  # Responsabilidad:
  #   - Renderizar los gráficos tal cual (NO recalcular pipelines).
  #   - Transformaciones mínimas: redondeo / conversión a millones cuando aplica.
  # ========================================================================

  # ------------------------------------------------------------------------
  # HCIM_1 — Ingresos mensuales (millones)
  # ------------------------------------------------------------------------
  output$HCIM_1 <- renderHighchart({

    req(exists("tabla_2"), is.data.frame(tabla_2))
    req(exists("Millones"))

    .assert_cols(tabla_2, c("Fecha", "Ingresos"), ctx = "tabla_2 (HC2/HCIM_1)")

    df_mensual <- tabla_2 %>%
      dplyr::mutate(Ingresos = round(Ingresos / Millones, 1))

    .hc_base() %>%
      hc_xAxis(categories = df_mensual$Fecha, title = list(text = "Año-mes")) %>%
      hc_add_series(name = "Ingresos", data = df_mensual$Ingresos) %>%
      hc_yAxis(title = list(text = "Millones de colones"),
               labels = list(format = "{value}"))
  })

  # ------------------------------------------------------------------------
  # HCIM_2 — Variaciones (porcentaje)
  # ------------------------------------------------------------------------
  output$HCIM_2 <- renderHighchart({

    req(exists("tabla_2_var"), is.data.frame(tabla_2_var))

    .assert_cols(tabla_2_var,
                 c("Fecha", "var.Ingresos", "var.acum_12", "var.cum_ano_Ingresos"),
                 ctx = "tabla_2_var (HC2/HCIM_2)")

    df_var <- tabla_2_var

    .hc_base() %>%
      hc_xAxis(categories = df_var$Fecha, title = list(text = "Año-mes")) %>%
      hc_add_series(name = "Variación interanual", data = df_var$var.Ingresos) %>%
      hc_add_series(name = "Variación acumulada", data = df_var$var.acum_12) %>%
      hc_add_series(name = "Variación acumulada al mes", data = df_var$var.cum_ano_Ingresos) %>%
      hc_yAxis(title = list(text = "Porcentaje"),
               labels = list(format = "{value}"))
  })

  # ------------------------------------------------------------------------
  # HCIM_3 — Recaudación acumulada (millones)
  # ------------------------------------------------------------------------
  output$HCIM_3 <- renderHighchart({

    req(exists("tabla.evo.mensual.1_acum"), is.data.frame(tabla.evo.mensual.1_acum))

    .assert_cols(tabla.evo.mensual.1_acum, c("Fecha", "cum_ingresos"),
                 ctx = "tabla.evo.mensual.1_acum (HC2/HCIM_3)")

    df_acum <- tabla.evo.mensual.1_acum %>%
      dplyr::mutate(cum_ingresos = round(cum_ingresos / 1000000, 1))

    .hc_base() %>%
      hc_xAxis(categories = df_acum$Fecha, title = list(text = "Año-mes")) %>%
      hc_add_series(name = "Ingresos", data = df_acum$cum_ingresos) %>%
      hc_yAxis(title = list(text = "Millones de colones"),
               labels = list(format = "{value}"))
  })

  # ------------------------------------------------------------------------
  # HCIM_4 — Carga tributaria (% PIB)
  # ------------------------------------------------------------------------
  output$HCIM_4 <- renderHighchart({

    req(exists("tabla.evo.mensual.2_acum"), is.data.frame(tabla.evo.mensual.2_acum))

    .assert_cols(tabla.evo.mensual.2_acum, c("Fecha", "Carga tributaria"),
                 ctx = "tabla.evo.mensual.2_acum (HC2/HCIM_4)")

    df_ct <- tabla.evo.mensual.2_acum

    .hc_base() %>%
      hc_xAxis(categories = df_ct$Fecha, title = list(text = "Año-mes")) %>%
      hc_add_series(name = "Carga tributaria", data = df_ct$`Carga tributaria`) %>%
      hc_yAxis(title = list(text = "Porcentaje del PIB."),
               labels = list(format = "{value}"))
  })

  # ------------------------------------------------------------------------
  # HCIM_5 — Ejecución mensual (%)
  # ------------------------------------------------------------------------
  output$HCIM_5 <- renderHighchart({

    req(exists("tabla.evo.mensual.3_acum"), is.data.frame(tabla.evo.mensual.3_acum))

    .assert_cols(tabla.evo.mensual.3_acum, c("Fecha", "Ejecucion"),
                 ctx = "tabla.evo.mensual.3_acum (HC2/HCIM_5)")

    df_ejec <- tabla.evo.mensual.3_acum

    .hc_base() %>%
      hc_xAxis(categories = df_ejec$Fecha, title = list(text = "Año-mes")) %>%
      hc_add_series(name = "% Ejecución", data = df_ejec$`Ejecucion`) %>%
      hc_yAxis(title = list(text = "Porcentaje de ejecución acumulada al mes"),
               labels = list(format = "{value}"))
  })

  ###################################
  #           Impuestos             # 
  ###################################
# ========================================================================
  # TAB: HC5  --------------------------------------------------------------
  # Impuestos (selección simple)
  # (UI: tabName = "HC5" | outputs: HC_I, HC_VI)
  # ========================================================================

  # Si ya tenés .assert_cols() arriba, podés borrar este bloque.
  .assert_cols <- function(df, cols, ctx = "dataset") {
    miss <- setdiff(cols, names(df))
    if (length(miss) > 0) stop(paste0("Faltan columnas en ", ctx, ": ", paste(miss, collapse = ", ")))
    invisible(TRUE)
  }

  # Helper: arma serie mensual de un impuesto seleccionado (robusto)
  .serie_impuesto <- function(df, var_name) {
    .assert_cols(df, c("Año", "mes.cod", "mes"), ctx = "Impuestos (base)")
    if (!var_name %in% names(df)) stop("La variable seleccionada no existe en Impuestos: ", var_name)

    out <- df %>%
      dplyr::group_by(.data$Año, .data$`mes.cod`, .data$mes) %>%
      dplyr::summarise(
        Ingresos = sum(as.numeric(.data[[var_name]]), na.rm = TRUE),
        .groups = "drop"
      ) %>%
      dplyr::mutate(
        Fecha = paste0(.data$Año, "-", sprintf("%02d", .data$`mes.cod`))
      ) %>%
      dplyr::arrange(.data$Año, .data$`mes.cod`)

    out
  }

  # ------------------------------------------------------------------------
  # HC_I — Serie del impuesto en el tiempo
  # ------------------------------------------------------------------------
  output$HC_I <- renderHighchart({

    req(exists("Impuestos"), is.data.frame(Impuestos))
    req(input$variable)

    Impuesto <- .serie_impuesto(Impuestos, input$variable)

    # recorte final si existe Faltante_mes (mantiene tu lógica)
    if (exists("Faltante_mes") && is.numeric(Faltante_mes) && Faltante_mes >= 0) {
      cut_n <- nrow(Impuesto) - Faltante_mes - 1
      if (cut_n > 0) Impuesto <- Impuesto %>% dplyr::slice(1:cut_n)
    }

    .hc_base() %>%
      hc_xAxis(categories = Impuesto$Fecha, title = list(text = "Año-mes")) %>%
      hc_add_series(name = "Ingresos", data = Impuesto$Ingresos) %>%
      hc_yAxis(title = list(text = "En colones"),
               labels = list(format = "{value}"))
  })

  # ------------------------------------------------------------------------
  # HC_VI — Variaciones del impuesto en el tiempo
  # ------------------------------------------------------------------------
  output$HC_VI <- renderHighchart({

    req(exists("Impuestos"), is.data.frame(Impuestos))
    req(input$variable)

    Impuesto <- .serie_impuesto(Impuestos, input$variable)

    if (exists("Faltante_mes") && is.numeric(Faltante_mes) && Faltante_mes >= 0) {
      cut_n <- nrow(Impuesto) - Faltante_mes
      if (cut_n > 0) Impuesto <- Impuesto %>% dplyr::slice(1:cut_n)
    }

    # Variaciones (en colones)
    Impuesto <- Impuesto %>%
      dplyr::mutate(
        var.Ingresos = round((Ingresos / dplyr::lag(Ingresos, 12) - 1) * 100, 2),
        acum_12      = zoo::rollsum(Ingresos, 12, align = "right", fill = NA),
        var.acum_12  = round((acum_12 / dplyr::lag(acum_12, 12) - 1) * 100, 1)
      )

    # Acumulado anual (en millones, como tu lógica original)
    Millones_local <- 1000000
    Impuesto <- Impuesto %>%
      dplyr::mutate(Ingresos_mill = round(Ingresos / Millones_local, 1)) %>%
      dplyr::group_by(.data$Año) %>%
      dplyr::mutate(cum_ano_Ingresos = cumsum(.data$Ingresos_mill)) %>%
      dplyr::ungroup() %>%
      dplyr::mutate(
        var.cum_ano_Ingresos = round((cum_ano_Ingresos / dplyr::lag(cum_ano_Ingresos, 12) - 1) * 100, 1)
      )

    .hc_base() %>%
      hc_xAxis(categories = Impuesto$Fecha, title = list(text = "Año-mes")) %>%
      hc_add_series(name = "Variación interanual", data = Impuesto$var.Ingresos) %>%
      hc_add_series(name = "Variación acumulada", data = Impuesto$var.acum_12) %>%
      hc_add_series(name = "Variación acumulada al mes", data = Impuesto$var.cum_ano_Ingresos) %>%
      hc_yAxis(title = list(text = "Porcentaje"),
               labels = list(format = "{value}"))
  })

###################################
#           Avanzado              # 
###################################
###################################
#           Avanzado              #
# (UI: tabName = "HC4")           #
###################################

# ------------------------------------------------------------------------
# Helper: convertir mes a número (1-12) de forma tolerante
# - Soporta: 1..12, "01".."12", "Enero", "ene", "febrero", etc.
# ------------------------------------------------------------------------
.mes_to_int <- function(x) {
  if (is.numeric(x)) return(as.integer(x))

  x_chr <- tolower(trimws(as.character(x)))

  # Intento 1: si ya viene como "01" o "1"
  out <- suppressWarnings(as.integer(x_chr))
  if (!all(is.na(out))) return(out)

  # Intento 2: nombres de mes (es)
  map <- c(
    "enero" = 1, "ene" = 1,
    "febrero" = 2, "feb" = 2,
    "marzo" = 3, "mar" = 3,
    "abril" = 4, "abr" = 4,
    "mayo" = 5, "may" = 5,
    "junio" = 6, "jun" = 6,
    "julio" = 7, "jul" = 7,
    "agosto" = 8, "ago" = 8,
    "septiembre" = 9, "setiembre" = 9, "sep" = 9, "set" = 9,
    "octubre" = 10, "oct" = 10,
    "noviembre" = 11, "nov" = 11,
    "diciembre" = 12, "dic" = 12
  )

  out2 <- unname(map[x_chr])
  suppressWarnings(as.integer(out2))
}

# ------------------------------------------------------------------------
# Helper: prepara serie mensual robusta (Fecha_str + Ingresos)
# - Prioridad:
#   1) Si existe Fecha_str -> usar
#   2) Si existe Fecha     -> convertir a string
#   3) Si existe Año + (mes.cod o equivalente) -> construir YYYY-MM
#   4) Si existe Año + mes (texto o num) -> construir YYYY-MM
# ------------------------------------------------------------------------
prep_serie_mensual <- function(df) {
  stopifnot(is.data.frame(df))

  # 1) Detectar columna de valor a sumar (tolerante)
  value_col <- intersect(c("Ingresos", "monto", "Monto"), names(df))[1]
  if (is.na(value_col)) {
    stop("No encuentro columna de valores (Ingresos/monto/Monto) en el dataset filtrado.")
  }

  # 2) Construir Fecha_str
  if ("Fecha_str" %in% names(df)) {

    df <- df %>% dplyr::mutate(Fecha_str = as.character(.data$Fecha_str))

  } else if ("Fecha" %in% names(df)) {

    df <- df %>% dplyr::mutate(Fecha_str = as.character(.data$Fecha))

  } else {

    if (!("Año" %in% names(df))) {
      stop("Faltan columnas para construir Fecha: Año")
    }

    # Buscar columna de mes (primero las “codificadas”, luego alternativas)
    mes_candidates <- c("mes.cod", "mescod", "mes_code", "mes_num", "mesCod", "mesCOD", "Mes.cod",
                       "mes", "Mes")
    mes_col <- intersect(mes_candidates, names(df))[1]

    if (is.na(mes_col)) {
      stop("Faltan columnas para construir Fecha: mes.cod (o equivalente).")
    }

    df <- df %>%
      dplyr::mutate(
        .mes_tmp = .mes_to_int(.data[[mes_col]])
      )

    if (all(is.na(df$.mes_tmp))) {
      stop(paste0("No pude interpretar la columna de mes '", mes_col, "'. Debe ser 1-12 o nombre de mes."))
    }

    df <- df %>%
      dplyr::mutate(
        Fecha_str = paste0(.data$Año, "-", sprintf("%02d", .data$.mes_tmp))
      ) %>%
      dplyr::select(-.data$.mes_tmp)
  }

  # 3) Agregar por mes y ordenar cronológicamente
  out <- df %>%
    dplyr::group_by(.data$Fecha_str) %>%
    dplyr::summarise(
      Ingresos = sum(as.numeric(.data[[value_col]]), na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::filter(is.finite(.data$Ingresos)) %>%
    dplyr::mutate(Fecha_ord = as.Date(paste0(.data$Fecha_str, "-01"))) %>%
    dplyr::arrange(.data$Fecha_ord)

  out
}

# ------------------------------------------------------------------------
# Reactives de filtros (jerárquicos)
# Nota: trabajan sobre Ingresos_mensual (debe existir en memoria)
# ------------------------------------------------------------------------
filtro_clase <- reactive({
  req(exists("Ingresos_mensual"), is.data.frame(Ingresos_mensual))
  Ingresos_mensual %>% dplyr::filter(clase == input$f_clase)
})

filtro_subclase <- reactive({
  if (input$f_subclase == "Todo") filtro_clase()
  else filtro_clase() %>% dplyr::filter(subclase == input$f_subclase)
})

filtro_grupo <- reactive({
  if (input$f_grupo == "Todo") filtro_subclase()
  else filtro_subclase() %>% dplyr::filter(grupo == input$f_grupo)
})

filtro_subgrupo <- reactive({
  if (input$f_subgrupo == "Todo") filtro_grupo()
  else filtro_grupo() %>% dplyr::filter(subgrupo == input$f_subgrupo)
})

filtro_partida <- reactive({
  if (input$f_partida == "Todo") filtro_subgrupo()
  else filtro_subgrupo() %>% dplyr::filter(partida == input$f_partida)
})

filtro_subpartida <- reactive({
  if (input$f_subpartida == "Todo") filtro_partida()
  else filtro_partida() %>% dplyr::filter(subpartida == input$f_subpartida)
})

filtro_renglon <- reactive({
  if (input$f_renglon == "Todo") filtro_subpartida()
  else filtro_subpartida() %>% dplyr::filter(renglon == input$f_renglon)
})

filtro_subrenglon <- reactive({
  if (input$f_subrenglon == "Todo") filtro_renglon()
  else filtro_renglon() %>% dplyr::filter(subrenglon == input$f_subrenglon)
})

# ------------------------------------------------------------------------
# Congelar filtros solo cuando el usuario presiona "Seleccionar"
# ------------------------------------------------------------------------
filtros <- eventReactive(input$select_2, {
  filtro_subrenglon()
})

# ------------------------------------------------------------------------
# Output HC_P: Evolución (millones)
# ------------------------------------------------------------------------
output$HC_P <- renderHighchart({
  df <- filtros()
  req(df)

  serie <- prep_serie_mensual(df)
  req(nrow(serie) > 0)

  Millones <- 1000000
  serie <- serie %>% dplyr::mutate(Ingresos = round(.data$Ingresos / Millones, 1))

  .hc_base() %>%
    hc_xAxis(categories = serie$Fecha_str, title = list(text = "Año-mes")) %>%
    hc_add_series(name = "Ingresos", data = serie$Ingresos) %>%
    hc_yAxis(title = list(text = "Millones de colones"),
             labels = list(format = "{value}"))
})

# ------------------------------------------------------------------------
# Output HC_VP: Variaciones (porcentaje)
# - var.Ingresos: interanual
# - var.acum_12: variación del acumulado 12 meses
# - var.cum_ano_Ingresos: variación del acumulado del año vs 12 meses atrás
# ------------------------------------------------------------------------
output$HC_VP <- renderHighchart({
  df <- filtros()
  req(df)

  serie <- prep_serie_mensual(df)
  req(nrow(serie) > 12)

  # Variaciones sobre colones
  serie <- serie %>%
    dplyr::mutate(
      var.Ingresos = round((Ingresos / dplyr::lag(Ingresos, 12) - 1) * 100, 2),
      acum_12      = zoo::rollsum(Ingresos, 12, align = "right", fill = NA),
      var.acum_12  = round((acum_12 / dplyr::lag(acum_12, 12) - 1) * 100, 1)
    )

  # A millones para acumulado anual (como tu lógica original)
  Millones <- 1000000
  serie <- serie %>% dplyr::mutate(Ingresos = round(.data$Ingresos / Millones, 1))

  serie <- serie %>%
    dplyr::mutate(Año = as.integer(substr(.data$Fecha_str, 1, 4))) %>%
    dplyr::group_by(.data$Año) %>%
    dplyr::mutate(cum_ano_Ingresos = cumsum(.data$Ingresos)) %>%
    dplyr::ungroup() %>%
    dplyr::mutate(
      var.cum_ano_Ingresos = round((cum_ano_Ingresos / dplyr::lag(cum_ano_Ingresos, 12) - 1) * 100, 1)
    )

  .hc_base() %>%
    hc_xAxis(categories = serie$Fecha_str, title = list(text = "Año-mes")) %>%
    hc_add_series(name = "Variación interanual", data = serie$var.Ingresos) %>%
    hc_add_series(name = "Variación acumulada", data = serie$var.acum_12) %>%
    hc_add_series(name = "Variación acumulada al mes", data = serie$var.cum_ano_Ingresos) %>%
    hc_yAxis(title = list(text = "Porcentaje"),
             labels = list(format = "{value}"))
})
  
  ############################################
  #              Pronóstico                  #
  ############################################
# ============================================================
# PRONOSTICO — MODULO 1 (pronos1): TOTAL MENSUAL (Nuevo Mundo)
# Outputs:
#   - forecast1  : ganador + bandas
#   - quality1   : quality card
#   - GoF.1      : ranking table (backtesting)
# Dependencias:
#   - tabla_2 : data.frame (Año, mes.cod, Ingresos)
#   - run_total_bundle() desde forecast_engine/_20_forecast_runner.R
# ============================================================

# Directorio de bundles pre-calculados (relativo a app_dir = Scripts_tablas_dashboard/)
.bundles_dir <- file.path(getwd(), "bundles")

.bundle_pronos1 <- shiny::eventReactive(input$select_1, {
  h <- as.integer(input$horizonte.1)
  req(length(input$modelos.1) > 0)

  path <- file.path(.bundles_dir, sprintf("bundle_pronos1_h%02d.rds", h))

  validate(
    need(file.exists(path),
         paste0("Bundle no encontrado para h=", h,
                ". Ejecuta precompute_bundles.R para generarlo."))
  )

  readRDS(path)
})

# -----------------------------
# (1) Gráfico: histórico + forecast ganador + bandas
# -----------------------------
output$forecast1 <- renderHighchart({
  b <- .bundle_pronos1()

  y <- b$y
  fc <- b$forecast_final

  fr <- stats::frequency(y)
  st <- stats::start(y)
  en <- stats::end(y)

  next_start <- c(en[1], en[2] + 1)
  if (next_start[2] == 13) next_start <- c(next_start[1] + 1, 1)

  f_mean  <- stats::ts(as.numeric(fc$mean),  start = next_start, frequency = fr)
  f_lower <- if (!is.null(fc$lower)) stats::ts(as.numeric(fc$lower), start = next_start, frequency = fr) else NULL
  f_upper <- if (!is.null(fc$upper)) stats::ts(as.numeric(fc$upper), start = next_start, frequency = fr) else NULL

  highcharter::hchart(y, name = "Histórico (millones)") %>%
    highcharter::hc_add_series(f_mean, name = paste0("Forecast ganador: ", b$winner$label), type = "line") %>%
    { if (!is.null(f_lower)) highcharter::hc_add_series(., f_lower, name = "Lower (95%)", type = "line", dashStyle = "Dash", color = "#000000") else . } %>%
    { if (!is.null(f_upper)) highcharter::hc_add_series(., f_upper, name = "Upper (95%)", type = "line", dashStyle = "Dash", color = "#000000") else . } %>%
    highcharter::hc_yAxis(title = list(text = "Millones de colones")) %>%
    highcharter::hc_xAxis(title = list(text = "Año")) %>%
    highcharter::hc_chart(zoomType = "xy")
})

# -----------------------------
# (2) Quality card
# -----------------------------
output$quality1 <- renderUI({
  b <- .bundle_pronos1()
  qc <- b$quality_card

  # Texto ya viene “listo” del engine, y números también
  shiny::tags$div(
    shiny::tags$h4(paste0("Modelo ganador: ", b$winner$label, " (", b$winner$model_id, ")")),
    shiny::tags$p(qc$text),
    shiny::tags$ul(
      shiny::tags$li(paste0("wMAPE (mean): ", qc$wmape_mean)),
      shiny::tags$li(paste0("wMAPE (sd): ", qc$wmape_sd)),
      shiny::tags$li(paste0("Score: ", qc$score))
    )
  )
})

# -----------------------------
# (3) Ranking table (backtesting resumen)
# -----------------------------
output$tabla.forecast1 <- renderReactable({
  b  <- .bundle_pronos1()
  fc <- b$forecast_final
  y  <- b$y
  en <- stats::end(y)
  next_start <- c(en[1], en[2] + 1)
  if (next_start[2] == 13) next_start <- c(next_start[1] + 1, 1)

  h      <- length(fc$mean)
  fechas <- seq(as.Date(paste0(next_start[1], "-", sprintf("%02d", next_start[2]), "-01")),
                by = "month", length.out = h)

  df <- data.frame(
    Fecha          = format(fechas, "%Y-%m"),
    `Valor (mill)` = round(as.numeric(fc$mean), 2),
    check.names    = FALSE
  )
  reactable::reactable(df)
})

# -----------------------------
# (4) Consulta de pronóstico por modelo (on demand)
# -----------------------------
.fc_modelo_consulta_1 <- shiny::eventReactive(input$ver_modelo_1, {
  b   <- .bundle_pronos1()
  h   <- length(b$forecast_final$mean)
  run_model_forecast(input$modelo_consulta_1, y_train = b$y, h = h, level = 95)
})

output$tabla.modelo_consulta_1 <- renderReactable({
  fc  <- .fc_modelo_consulta_1()
  b   <- .bundle_pronos1()

  en <- stats::end(b$y)
  next_start <- c(en[1], en[2] + 1)
  if (next_start[2] == 13) next_start <- c(next_start[1] + 1, 1)

  h      <- length(b$forecast_final$mean)
  fechas <- seq(as.Date(paste0(next_start[1], "-", sprintf("%02d", next_start[2]), "-01")),
                by = "month", length.out = h)

  df <- data.frame(
    Fecha          = format(fechas, "%Y-%m"),
    `Valor (mill)` = round(as.numeric(fc$mean), 2),
    check.names    = FALSE
  )
  reactable::reactable(df)
})

output$GoF.1 <- renderReactable({
  b  <- .bundle_pronos1()
  rs <- b$backtest$resumen

  # Filtrar por modelos seleccionados en el checkbox (Opción B: solo filtra, no relanza engine)
  modelos_sel <- input$modelos.1
  if (length(modelos_sel) > 0) {
    rs <- rs[rs$model_id %in% modelos_sel, , drop = FALSE]
  }

  keep <- intersect(c("rank","model_id","label_ui","wMAPE_mean","wMAPE_sd","score","n_splits"), names(rs))
  rs2  <- rs[, keep, drop = FALSE]

  reactable::reactable(rs2)
})
  
  ##############################################################
  #                          Impuestos                         #
  ##############################################################
  # ============================================================
# ============================================================
# PRONÓSTICOS — PRONOS3 (IMPUESTOS)
# Objetivo:
#   - Construir una serie mensual del impuesto seleccionado
#   - Ajustar 4 modelos (ARIMA, ETS, AUTO.ARIMA, TSLM)
#   - Graficar: observado + fitted + forecast (alineado en tiempo)
#   - Mostrar GoF y tablas de proyección (en millones)
# ============================================================

# ------------------------------
# Helper 1: preparar serie mensual (impuesto seleccionado)
# ------------------------------
prep_impuesto_ts <- function(impuestos_df, col_name) {
  stopifnot(is.data.frame(impuestos_df))
  if (!is.character(col_name) || length(col_name) != 1) {
    stop("col_name debe ser un string con el nombre de la columna del impuesto.")
  }
  if (!col_name %in% names(impuestos_df)) {
    stop("No existe la columna seleccionada en Impuestos: ", col_name)
  }

  needed <- c("Año", "mes.cod", "mes")
  miss <- setdiff(needed, names(impuestos_df))
  if (length(miss) > 0) stop("Impuestos no tiene columnas requeridas: ", paste(miss, collapse = ", "))

  df <- impuestos_df %>%
    dplyr::group_by(.data$Año, .data$`mes.cod`, .data$mes) %>%
    dplyr::summarise(
      Ingresos = sum(.data[[col_name]], na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::mutate(
      Fecha_str = paste0(.data$Año, "-", sprintf("%02d", .data$`mes.cod`)),
      Fecha_ord = as.Date(paste0(.data$Fecha_str, "-01"))
    ) %>%
    dplyr::arrange(.data$Fecha_ord)

  # Si hay meses incompletos al final, normalmente el último se elimina
  if (nrow(df) > 1) df <- dplyr::slice(df, 1:(nrow(df) - 1))

  # Evitar ceros/negativos (tu lógica original) -> para modelos multiplicativos
  df$Ingresos[df$Ingresos <= 0] <- 1000

  # Construir ts con start real (no hardcodear 2007 si no corresponde)
  start_year  <- as.integer(format(df$Fecha_ord[1], "%Y"))
  start_month <- as.integer(format(df$Fecha_ord[1], "%m"))

  ts_y <- stats::ts(as.numeric(df$Ingresos), frequency = 12, start = c(start_year, start_month))

  list(df = df, ts = ts_y)
}

# ------------------------------
# Helper 2: ajustar modelos (impuesto)
# ------------------------------
fit_models_impuesto <- function(y_ts) {
  list(
    arima     = forecast::Arima(y_ts, order = c(1, 1, 1), seasonal = c(0, 1, 1)),
    ets       = forecast::ets(y_ts, model = "MAM", damped = TRUE),
    autoarima = forecast::auto.arima(y_ts),
    regresion = forecast::tslm(y_ts ~ trend + season)
  )
}

# ------------------------------
# Helper 3: pronosticar modelos (impuesto)
# ------------------------------
fc_models_impuesto <- function(models, h, level = 95) {
  list(
    arima     = forecast::forecast(models$arima,     h = h, level = level),
    ets       = forecast::forecast(models$ets,       h = h, level = level),
    autoarima = forecast::forecast(models$autoarima, h = h, level = level),
    regresion = forecast::forecast(models$regresion, h = h, level = level)
  )
}

# ------------------------------
# Helper 4: tabla estándar desde forecast()
# (en millones y con formato CR)
# ------------------------------
tbl_forecast_fc <- function(fc_obj, Millones = 1000000) {
  out <- fc_obj %>%
    as.data.frame() %>%
    dplyr::rename(
      Proyeccion       = `Point Forecast`,
      Limite_inferior  = `Lo 95`,
      Limite_superior  = `Hi 95`
    ) %>%
    dplyr::mutate(
      Proyeccion      = round(.data$Proyeccion / Millones, 1),
      Limite_inferior = round(.data$Limite_inferior / Millones, 1),
      Limite_superior = round(.data$Limite_superior / Millones, 1)
    ) %>%
    dplyr::mutate(
      Proyeccion      = scales::number(.data$Proyeccion,      accuracy = .1, big.mark = ".", decimal.mark = ","),
      Limite_inferior = scales::number(.data$Limite_inferior, accuracy = .1, big.mark = ".", decimal.mark = ","),
      Limite_superior = scales::number(.data$Limite_superior, accuracy = .1, big.mark = ".", decimal.mark = ",")
    ) %>%
    dplyr::rename(
      `Proyección`      = .data$Proyeccion,
      `Límite inferior` = .data$Limite_inferior,
      `Límite superior` = .data$Limite_superior
    )

  out
}

# ============================================================
# Reactivo compartido: modelos + forecasts (1 sola vez por click)
# Reemplaza serie_impuesto_pronos + h3_sel + los 5 fit_models_impuesto
# independientes que había antes.
# ============================================================
datos_pronos3 <- shiny::eventReactive(input$select_pronos3, {
  req(input$variable2)
  obj    <- prep_impuesto_ts(Impuestos, input$variable2)
  y      <- obj$ts
  req(length(y) >= 24)
  h      <- input$horizonte.3
  req(h >= 1)
  models <- fit_models_impuesto(y)
  fc     <- fc_models_impuesto(models, h = h, level = 95)
  list(y = y, h = h, models = models, fc = fc)
})

# ============================================================
# OUTPUT: forecast3 (gráfico)
# ============================================================
output$forecast3 <- renderHighchart({
  d  <- datos_pronos3()
  y  <- d$y
  fc <- d$fc

  st <- stats::start(y)
  fr <- stats::frequency(y)

  fit_arima <- stats::ts(as.numeric(stats::fitted(d$models$arima)),     start = st, frequency = fr)
  fit_ets   <- stats::ts(as.numeric(stats::fitted(d$models$ets)),       start = st, frequency = fr)
  fit_auto  <- stats::ts(as.numeric(stats::fitted(d$models$autoarima)), start = st, frequency = fr)
  fit_reg   <- stats::ts(as.numeric(stats::fitted(d$models$regresion)), start = st, frequency = fr)

  endt <- stats::end(y)
  next_start <- c(endt[1], endt[2] + 1)
  if (next_start[2] == 13) next_start <- c(next_start[1] + 1, 1)

  f_arima <- stats::ts(as.numeric(fc$arima$mean),     start = next_start, frequency = fr)
  f_ets   <- stats::ts(as.numeric(fc$ets$mean),       start = next_start, frequency = fr)
  f_auto  <- stats::ts(as.numeric(fc$autoarima$mean), start = next_start, frequency = fr)
  f_reg   <- stats::ts(as.numeric(fc$regresion$mean), start = next_start, frequency = fr)

  highcharter::hchart(y, name = "Ingresos") %>%
    highcharter::hc_add_series(fit_arima, name = "ARIMA (fit)", type = "line") %>%
    highcharter::hc_add_series(f_arima,   name = "ARIMA (F)",   type = "line") %>%
    highcharter::hc_add_series(fit_ets,   name = "ETS (fit)",   type = "line") %>%
    highcharter::hc_add_series(f_ets,     name = "ETS (F)",     type = "line") %>%
    highcharter::hc_add_series(fit_auto,  name = "AUTO.ARIMA (fit)", type = "line") %>%
    highcharter::hc_add_series(f_auto,    name = "AUTO.ARIMA (F)",   type = "line") %>%
    highcharter::hc_add_series(fit_reg,   name = "Regresión (fit)",  type = "line") %>%
    highcharter::hc_add_series(f_reg,     name = "Regresión (F)",    type = "line") %>%
    highcharter::hc_yAxis(title = list(text = "En colones")) %>%
    highcharter::hc_chart(zoomType = "xy")
})

# ============================================================
# OUTPUT: GoF.3 (tabla bondad)
# ============================================================
output$GoF.3 <- renderReactable({
  d      <- datos_pronos3()
  models <- d$models

  REGRESION  <- round(c(forecast::accuracy(models$regresion)[c(2, 3, 5)], forecast::CV(models$regresion)[c(2, 4)]), 3)
  ETS_MAM    <- round(c(forecast::accuracy(models$ets)[c(2, 3, 5)], models$ets$aic, models$ets$bic), 3)
  ARIMA      <- round(c(forecast::accuracy(models$arima)[c(2, 3, 5)], models$arima$aic, models$arima$bic), 3)
  AUTO_ARIMA <- round(c(forecast::accuracy(models$autoarima)[c(2, 3, 5)], models$autoarima$aic, models$autoarima$bic), 3)

  cuadro <- rbind(
    Medida    = c("RSME", "MAE", "MAPE", "AIC", "BIC"),
    REGRESION,
    ETS_MAM,
    ARIMA,
    AUTO_ARIMA
  )

  colnames(cuadro) <- cuadro[1, ]
  cuadro <- cuadro[-1, ]

  reactable::reactable(cuadro)
})

# ============================================================
# OUTPUTS: tablas pronóstico (3.1 a 3.4)
# ============================================================
output$tabla.forcast.3.1 <- renderReactable({
  d  <- datos_pronos3()
  reactable::reactable(tbl_forecast_fc(d$fc$arima))
})

output$tabla.forcast.3.2 <- renderReactable({
  d  <- datos_pronos3()
  reactable::reactable(tbl_forecast_fc(d$fc$ets))
})

output$tabla.forcast.3.3 <- renderReactable({
  d  <- datos_pronos3()
  reactable::reactable(tbl_forecast_fc(d$fc$autoarima))
})

output$tabla.forcast.3.4 <- renderReactable({
  d  <- datos_pronos3()
  reactable::reactable(tbl_forecast_fc(d$fc$regresion))
})

# ============================================================
# Consulta de pronóstico por modelo (on demand, sin recomputar)
# ============================================================
.fc_ver_pronos3 <- shiny::eventReactive(input$ver_modelo_3, {
  datos_pronos3()$fc[[input$modelo_ver_3]]
})

output$tabla.modelo_ver_3 <- renderReactable({
  reactable::reactable(tbl_forecast_fc(.fc_ver_pronos3()))
})

# ============================================================
# Narrativa IA — pronos3
# ============================================================

.build_prompt_pronos3 <- function(d) {
  rmse_arima     <- round(forecast::accuracy(d$models$arima)[1,     "RMSE"], 2)
  rmse_ets       <- round(forecast::accuracy(d$models$ets)[1,       "RMSE"], 2)
  rmse_autoarima <- round(forecast::accuracy(d$models$autoarima)[1, "RMSE"], 2)
  rmse_regresion <- round(forecast::accuracy(d$models$regresion)[1, "RMSE"], 2)

  rmse_vals <- c(
    "ARIMA"     = rmse_arima,
    "ETS"       = rmse_ets,
    "AutoARIMA" = rmse_autoarima,
    "Regresión" = rmse_regresion
  )

  winner <- names(which.min(rmse_vals))

  fc_mean_winner <- switch(winner,
    "ARIMA"     = d$fc$arima$mean,
    "ETS"       = d$fc$ets$mean,
    "AutoARIMA" = d$fc$autoarima$mean,
    "Regresión" = d$fc$regresion$mean
  )
  primeros_3 <- round(as.numeric(fc_mean_winner), 1)[1:3]

  h          <- d$h
  ultimo_obs <- round(tail(as.numeric(d$y), 1), 1)

  paste0(
    "Eres un analista fiscal experto en ingresos del gobierno de Costa Rica. ",
    "Con base en los siguientes datos de pronóstico del impuesto seleccionado, ",
    "redacta un párrafo ejecutivo claro y profesional de máximo 120 palabras.\n\n",
    "Datos del pronóstico:\n",
    "- Modelo ganador (menor RMSE): ", winner, "\n",
    "- RMSE por modelo: ARIMA=", rmse_arima,
      ", ETS=", rmse_ets,
      ", AutoARIMA=", rmse_autoarima,
      ", Regresión=", rmse_regresion, "\n",
    "- Horizonte de pronóstico: ", h, " meses\n",
    "- Último valor observado (colones): ", ultimo_obs, "\n",
    "- Primeros 3 meses pronosticados (colones): ",
      paste(primeros_3, collapse = ", "), "\n\n",
    "Redacta el párrafo de forma directa, sin bullets, en español formal. ",
    "Menciona el modelo ganador y la tendencia esperada de los ingresos ",
    "en el horizonte indicado."
  )
}

observeEvent(input$btn_narrativa_3, {
  d <- datos_pronos3()
  req(d)

  showNotification(
    "Generando narrativa con IA, por favor espere...",
    type     = "message",
    duration = 8
  )

  prompt    <- .build_prompt_pronos3(d)
  resultado <- .safe_ollama_call(prompt)

  if (!is.null(resultado)) {
    output$narrativa_pronos3 <- renderUI({
      tags$div(
        resultado,
        style = paste(
          "font-size: 15px;",
          "line-height: 1.7;",
          "padding: 12px;",
          "color: #1e293b;",
          "background: #f8fafc;",
          "border-radius: 8px;"
        )
      )
    })
  } else {
    output$narrativa_pronos3 <- renderUI({
      tags$p(
        "No se pudo conectar con Ollama. Verifique que esté corriendo.",
        style = "color: red;"
      )
    })
  }
})

############################################
#   Filtros para el módulo   Avanzado      #
############################################
############################################
#   PRONOS4 — AVANZADO (FILTROS + FORECAST)
############################################
# Este bloque corresponde al TAB:
#   tabName = "pronos4"
#
# Outputs del body:
#   - forecast4
#   - GoF.4
#   - tabla.forcast.4.1 (ARIMA)
#   - tabla.forcast.4.2 (ETS)
#   - tabla.forcast.4.3 (AUTO.ARIMA)
#   - tabla.forcast.4.4 (Regresión / TSLM)
#
# Inputs del body:
#   - f_clase_2, f_subclase_2, f_grupo_2, f_subgrupo_2, f_partida_2,
#     f_subpartida_2, f_renglon_2, f_subrenglon_2
#   - select_3 (actionButton)
#   - horizonte.4 (slider)
############################################

# ============================================================
# (PRE-REQ) Registry de modelos (Etapa 3)
# - Importante: PRONOS4 usará run_model_forecast() para ETS / AutoARIMA / TSLM
# - ARIMA: idealmente también en registry como model_id="arima"
# ============================================================
if (!exists("run_model_forecast")) {
  # Ajustá la ruta si tu archivo está en otra carpeta.
  # Si está en el mismo folder del server/app, esto funciona tal cual.
  try(source("forecast_models_registry.R"), silent = TRUE)
}

# ============================================================
# 0) Helper local (DEFINIDO AQUÍ MISMO)
#    Convierte cualquier df filtrado a una serie mensual estándar
#    que tenga: Fecha_ord (Date), Fecha_str (YYYY-MM), Ingresos (num)
# ============================================================
prep_serie_mensual_forecast <- function(df) {
  stopifnot(is.data.frame(df))

  # A) Columna numérica a sumar
  # Nota: en tu Excel se ve "Presupuesto a mes.cod" (col I).
  value_candidates <- c(
    "Ingresos", "ingresos", "monto", "Monto", "MONTO",
    "Presupuesto a mes.cod", "Presupuesto a mes.cod.", "Presupuesto_a_mes.cod",
    "Presupuesto a mes.cod " # por si trae espacios raros
  )
  value_col <- intersect(value_candidates, names(df))[1]
  if (is.na(value_col)) {
    stop("prep_serie_mensual_forecast(): No encuentro columna numérica (Ingresos/monto/Monto/Presupuesto a mes.cod) en df.")
  }

  # B) Si ya hay fecha (con variantes), usarla
  fecha_col <- intersect(c("Fecha", "fecha", "FECHA", "Fecha_str", "FECHA_STR"), names(df))[1]
  if (!is.na(fecha_col)) {

    out <- df %>%
      dplyr::mutate(
        Fecha_str = substr(as.character(.data[[fecha_col]]), 1, 7),
        Fecha_ord = as.Date(paste0(Fecha_str, "-01"))
      )

  } else {

    # C) Si NO hay fecha, construir con Año + mes
    # En tu Excel: Año + mes.cod + mes
    anio_col <- intersect(c("Año", "ano", "ANO", "year", "Year", "YEAR"), names(df))[1]
    mes_col  <- intersect(c("mes.cod", "mes_cod", "mes", "Mes", "MES", "month", "Month", "MONTH"), names(df))[1]

    miss <- c()
    if (is.na(anio_col)) miss <- c(miss, "Año (o variantes: ano/year)")
    if (is.na(mes_col))  miss <- c(miss, "mes.cod/mes (o variantes)")

    if (length(miss) > 0) {
      stop("prep_serie_mensual_forecast(): Faltan columnas para fecha: ", paste(miss, collapse = " + "))
    }

    out <- df %>%
      dplyr::mutate(
        .anio = as.integer(.data[[anio_col]]),
        .mes  = suppressWarnings(as.integer(.data[[mes_col]])),
        Fecha_str = paste0(.anio, "-", sprintf("%02d", .mes)),
        Fecha_ord = tryCatch(
          as.Date(paste0(.data$Fecha_str, "-01")),
          error = function(e) NA_Date_
        )
      ) %>%
      dplyr::filter(!is.na(.data$Fecha_ord))
  }

  # D) Agregar por mes
  out %>%
    dplyr::group_by(.data$Fecha_str, .data$Fecha_ord) %>%
    dplyr::summarise(
      Ingresos = sum(as.numeric(.data[[value_col]]), na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::arrange(.data$Fecha_ord)
}

# ============================================================
# 1) Filtros jerárquicos (como tu body lo define)
#    Fuente final: filtros_2()
# ============================================================

filtro_clase_2 <- reactive({
  req(Ingresos_mensual, input$f_clase_2)
  dplyr::filter(Ingresos_mensual, .data$clase == input$f_clase_2)
})

filtro_subclase_2 <- reactive({
  req(input$f_subclase_2)
  if (input$f_subclase_2 == "Todo") {
    filtro_clase_2()
  } else {
    dplyr::filter(filtro_clase_2(), .data$subclase == input$f_subclase_2)
  }
})

filtro_grupo_2 <- reactive({
  req(input$f_grupo_2)
  if (input$f_grupo_2 == "Todo") {
    filtro_subclase_2()
  } else {
    dplyr::filter(filtro_subclase_2(), .data$grupo == input$f_grupo_2)
  }
})

filtro_subgrupo_2 <- reactive({
  req(input$f_subgrupo_2)
  if (input$f_subgrupo_2 == "Todo") {
    filtro_grupo_2()
  } else {
    dplyr::filter(filtro_grupo_2(), .data$subgrupo == input$f_subgrupo_2)
  }
})

filtro_partida_2 <- reactive({
  req(input$f_partida_2)
  if (input$f_partida_2 == "Todo") {
    filtro_subgrupo_2()
  } else {
    dplyr::filter(filtro_subgrupo_2(), .data$partida == input$f_partida_2)
  }
})

filtro_subpartida_2 <- reactive({
  req(input$f_subpartida_2)
  if (input$f_subpartida_2 == "Todo") {
    filtro_partida_2()
  } else {
    dplyr::filter(filtro_partida_2(), .data$subpartida == input$f_subpartida_2)
  }
})

filtro_renglon_2 <- reactive({
  req(input$f_renglon_2)
  if (input$f_renglon_2 == "Todo") {
    filtro_subpartida_2()
  } else {
    dplyr::filter(filtro_subpartida_2(), .data$renglon == input$f_renglon_2)
  }
})

filtro_subrenglon_2 <- reactive({
  req(input$f_subrenglon_2)
  if (input$f_subrenglon_2 == "Todo") {
    filtro_renglon_2()
  } else {
    dplyr::filter(filtro_renglon_2(), .data$subrenglon == input$f_subrenglon_2)
  }
})

# Fuente final única
filtros_2 <- reactive({
  df <- filtro_subrenglon_2()
  req(df)
  df
})

# ============================================================
# 2) Serie mensual “sellada” solo cuando el usuario presiona Seleccionar
#    (evita que Shiny intente correr modelos antes de tiempo)
# ============================================================

serie_mensual_4 <- eventReactive(input$select_3, {
  df <- filtros_2()
  req(df)

  serie <- prep_serie_mensual_forecast(df)
  req(nrow(serie) >= 24)  # mínimo razonable para modelos estacionales

  # Tu regla: quitar el último mes si viene incompleto
  if (nrow(serie) > 1) {
    serie <- dplyr::slice(serie, 1:(nrow(serie) - 1))
  }

  serie
})

# ============================================================
# 3) TS en millones (para estabilidad numérica)
# ============================================================

ts_mill_4 <- reactive({
  serie <- serie_mensual_4()
  req(serie)

  Millones <- 1000000
  y <- as.numeric(serie$Ingresos) / Millones

  start_year  <- as.integer(format(serie$Fecha_ord[1], "%Y"))
  start_month <- as.integer(format(serie$Fecha_ord[1], "%m"))

  stats::ts(y, frequency = 12, start = c(start_year, start_month))
})

# ============================================================
# 4) Modelos (4) — exactamente los que pide tu UI
#    ARIMA / ETS / AUTO.ARIMA / Regresión (TSLM)
#
# NOTA:
# - ETS / AUTO.ARIMA / TSLM salen del registry (run_model_forecast)
# - ARIMA:
#     * Ideal: agregar "arima" al registry.
#     * Fallback: ARIMA fijo acá mismo si "arima" no existe en registry.
# ============================================================

models_4 <- reactive({
  y <- ts_mill_4()
  h <- isolate(input$horizonte.4)
  req(h >= 1)

  # -------------------------
  # ARIMA (fijo)
  # -------------------------
  arima_res <- NULL
  arima_model <- NULL

  # Si existe run_model_forecast() y el registry tiene "arima", usarlo
  if (exists("run_model_forecast")) {
    # Try sin romper si no existe en el registry
    arima_res <- try(run_model_forecast("arima", y_train = y, h = h, level = 95), silent = TRUE)
    if (!inherits(arima_res, "try-error") && !is.null(arima_res$model)) {
      arima_model <- arima_res$model
    } else {
      arima_res <- NULL
      arima_model <- NULL
    }
  }

  # Fallback local (tu ARIMA fijo original)
  if (is.null(arima_res)) {
    arima_model <- forecast::Arima(y, order = c(1,1,1), seasonal = c(0,1,1))
    f1 <- forecast::forecast(arima_model, h = h, level = 95)
    arima_res <- list(
      mean  = as.numeric(f1$mean),
      lower = if (!is.null(f1$lower)) as.numeric(f1$lower[, 1]) else NULL,
      upper = if (!is.null(f1$upper)) as.numeric(f1$upper[, 1]) else NULL,
      model = arima_model,
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = FALSE,
      used_seed = NA_integer_
    )
  }

  # -------------------------
  # ETS / AUTOARIMA / TSLM desde registry
  # -------------------------
  if (!exists("run_model_forecast")) {
    stop("PRONOS4: No encuentro run_model_forecast(). Verificá que forecast_models_registry.R se esté source() correctamente.")
  }

  ets_res      <- run_model_forecast("ets",      y_train = y, h = h, level = 95)
  autoarima_res<- run_model_forecast("autoarima", y_train = y, h = h, level = 95)
  tslm_res     <- run_model_forecast("tslm",     y_train = y, h = h, level = 95)

  list(
    y = y,
    h = h,
    arima = arima_res,
    ets = ets_res,
    autoarima = autoarima_res,
    tslm = tslm_res
  )
})

# ============================================================
# 5) Output: gráfico forecast4
# - Alineación correcta de fitted y forecast al eje temporal del ts
# ============================================================

output$forecast4 <- renderHighchart({
  obj <- models_4()
  y <- obj$y
  h <- obj$h

  st <- stats::start(y)
  fr <- stats::frequency(y)

  # fitted alineado (mismo start/frequency)
  fit_arima <- stats::ts(as.numeric(stats::fitted(obj$arima$model)), start = st, frequency = fr)
  fit_ets   <- stats::ts(as.numeric(stats::fitted(obj$ets$model)),   start = st, frequency = fr)
  fit_auto  <- stats::ts(as.numeric(stats::fitted(obj$autoarima$model)), start = st, frequency = fr)
  fit_tslm  <- stats::ts(as.numeric(stats::fitted(obj$tslm$model)),  start = st, frequency = fr)

  # forecast alineado (arranca justo después del último dato observado)
  endt <- stats::end(y)
  next_start <- c(endt[1], endt[2] + 1)
  if (next_start[2] == 13) next_start <- c(next_start[1] + 1, 1)

  f_arima <- stats::ts(as.numeric(obj$arima$mean),     start = next_start, frequency = fr)
  f_ets   <- stats::ts(as.numeric(obj$ets$mean),       start = next_start, frequency = fr)
  f_auto  <- stats::ts(as.numeric(obj$autoarima$mean), start = next_start, frequency = fr)
  f_tslm  <- stats::ts(as.numeric(obj$tslm$mean),      start = next_start, frequency = fr)

  highcharter::hchart(y, name = "Ingresos (millones)") %>%
    highcharter::hc_add_series(fit_arima, name = "ARIMA (fit)", type = "line") %>%
    highcharter::hc_add_series(f_arima,   name = "ARIMA (F)",   type = "line") %>%
    highcharter::hc_add_series(fit_ets,   name = "ETS (fit)", type = "line") %>%
    highcharter::hc_add_series(f_ets,     name = "ETS (F)",   type = "line") %>%
    highcharter::hc_add_series(fit_auto,  name = "AUTO.ARIMA (fit)", type = "line") %>%
    highcharter::hc_add_series(f_auto,    name = "AUTO.ARIMA (F)",   type = "line") %>%
    highcharter::hc_add_series(fit_tslm,  name = "Regresión (fit)",  type = "line") %>%
    highcharter::hc_add_series(f_tslm,    name = "Regresión (F)",    type = "line") %>%
    highcharter::hc_yAxis(title = list(text = "Millones de colones")) %>%
    highcharter::hc_xAxis(title = list(text = "Tiempo")) %>%
    highcharter::hc_tooltip(crosshairs = TRUE, valueDecimals = 1, shared = TRUE, borderWidth = 2) %>%
    highcharter::hc_chart(zoomType = "xy")
})

# ============================================================
# 6) Output: GoF.4 (bondad de ajuste)
# - Se arma con accuracy() del objeto model entrenado
# ============================================================

output$GoF.4 <- renderReactable({
  obj <- models_4()

  .g <- function(m) {
    acc <- forecast::accuracy(m)
    c(
      RMSE = as.numeric(acc[1, "RMSE"]),
      MAE  = as.numeric(acc[1, "MAE"]),
      MAPE = as.numeric(acc[1, "MAPE"]),
      AIC  = suppressWarnings(as.numeric(stats::AIC(m))),
      BIC  = suppressWarnings(as.numeric(stats::BIC(m)))
    )
  }

  cuadro <- rbind(
    ARIMA      = .g(obj$arima$model),
    ETS        = .g(obj$ets$model),
    `AUTO.ARIMA` = .g(obj$autoarima$model),
    REGRESION  = .g(obj$tslm$model)
  )

  cuadro <- round(cuadro, 3)
  cuadro <- data.frame(Medida = rownames(cuadro), cuadro, row.names = NULL, check.names = FALSE)

  reactable::reactable(cuadro)
})

# ============================================================
# 7) Outputs: tablas.forcast.4.1 ... 4.4
# - Construimos una tabla estándar desde (mean/lower/upper) del registry
# - Se muestra en millones (ya viene en millones porque y es ts_mill_4)
# ============================================================

.to_tbl_registry <- function(res) {
  df <- data.frame(
    Proyección = as.numeric(res$mean),
    stringsAsFactors = FALSE
  )

  if (!is.null(res$lower) && !is.null(res$upper)) {
    df$`Límite inferior` <- as.numeric(res$lower)
    df$`Límite superior` <- as.numeric(res$upper)
  } else {
    df$`Límite inferior` <- NA_real_
    df$`Límite superior` <- NA_real_
  }

  df <- df %>%
    dplyr::mutate(
      Proyección        = round(.data$Proyección, 1),
      `Límite inferior` = round(.data$`Límite inferior`, 1),
      `Límite superior` = round(.data$`Límite superior`, 1)
    ) %>%
    dplyr::mutate(
      Proyección        = scales::number(.data$Proyección,        accuracy = .1, big.mark=".", decimal.mark=","),
      `Límite inferior` = scales::number(.data$`Límite inferior`, accuracy = .1, big.mark=".", decimal.mark=","),
      `Límite superior` = scales::number(.data$`Límite superior`, accuracy = .1, big.mark=".", decimal.mark=",")
    )

  df
}

.fc_ver_pronos4 <- shiny::eventReactive(input$ver_modelo_4, {
  models_4()[[input$modelo_ver_4]]
})

output$tabla.modelo_ver_4 <- renderReactable({
  reactable::reactable(.to_tbl_registry(.fc_ver_pronos4()))
})

# ── Narrativa ejecutiva pronos4 ───────────────────────────────────────────────

.build_prompt_pronos4 <- function(obj) {
  rmse_arima     <- round(forecast::accuracy(obj$arima$model)[1, "RMSE"], 2)
  rmse_ets       <- round(forecast::accuracy(obj$ets$model)[1, "RMSE"], 2)
  rmse_autoarima <- round(forecast::accuracy(obj$autoarima$model)[1, "RMSE"], 2)
  rmse_tslm      <- round(forecast::accuracy(obj$tslm$model)[1, "RMSE"], 2)

  rmse_vals <- c(
    "ARIMA"      = rmse_arima,
    "ETS"        = rmse_ets,
    "AutoARIMA"  = rmse_autoarima,
    "Regresión"  = rmse_tslm
  )
  winner <- names(which.min(rmse_vals))

  fc_mean_winner <- switch(winner,
    "ARIMA"     = obj$arima$mean,
    "ETS"       = obj$ets$mean,
    "AutoARIMA" = obj$autoarima$mean,
    "Regresión" = obj$tslm$mean
  )
  primeros_3  <- round(as.numeric(fc_mean_winner), 1)[1:min(3, length(fc_mean_winner))]
  h           <- obj$h
  ultimo_obs  <- round(tail(as.numeric(obj$y), 1), 1)

  rmse_texto <- paste(
    paste0(names(rmse_vals), ": ", rmse_vals),
    collapse = ", "
  )

  paste0(
    "Eres un analista fiscal experto en ingresos del gobierno de Costa Rica. ",
    "Se realizó un análisis avanzado de pronóstico de ingresos con horizonte h=", h, " períodos. ",
    "Se compararon cuatro modelos: ARIMA, ETS, AutoARIMA y Regresión (tslm). ",
    "Los errores RMSE (en millones de colones) fueron: ", rmse_texto, ". ",
    "El modelo con menor RMSE fue '", winner, "'. ",
    "El último valor observado fue ", ultimo_obs, " millones. ",
    "Los primeros valores pronosticados por '", winner, "' son: ",
    paste(primeros_3, collapse = ", "), " millones. ",
    "Redacta en español una narrativa ejecutiva breve (máximo 4 oraciones) que: ",
    "(1) indique cuál modelo ganó y por qué (RMSE más bajo), ",
    "(2) describa la tendencia de los primeros pronósticos respecto al último valor observado, ",
    "(3) mencione cualquier riesgo o consideración relevante para la toma de decisiones fiscales."
  )
}

observeEvent(input$btn_narrativa_4, {
  obj <- tryCatch(models_4(), error = function(e) NULL)
  if (is.null(obj)) {
    showNotification(
      "Primero presione 'Seleccionar' para calcular los modelos.",
      type = "warning", duration = 5
    )
    return()
  }

  showNotification("Generando narrativa con IA...", type = "message", duration = 4)

  prompt <- .build_prompt_pronos4(obj)
  texto  <- .safe_ollama_call(prompt)

  if (is.null(texto)) {
    output$narrativa_pronos4 <- renderUI(
      tags$p("No se pudo conectar con el modelo de IA. Verifique que Ollama esté activo.",
             style = "color: #c0392b; font-style: italic;")
    )
  } else {
    output$narrativa_pronos4 <- renderUI(
      tags$div(
        style = "background:#f0f7ff; border-left:4px solid #2196F3; padding:12px 16px; border-radius:4px; margin-top:8px;",
        tags$p(texto, style = "margin:0; line-height:1.6; color:#1a1a2e;")
      )
    )
  }
})

###############################################################################
###############################################################################
#                                                                             #
#                             Estacionalidad                                  #
#                                                                             #
###############################################################################
###############################################################################

###############################################################################
# TAB SI1 — ESTACIONALIDAD GENERAL
###############################################################################

# ============================================================
# 0) Helper: detectar columnas (Año / mes.cod / mes / valor)
# ============================================================
.pick_col <- function(nms, candidates) {
  hit <- intersect(candidates, nms)
  if (length(hit) == 0) NA_character_ else hit[1]
}

serie_estacionalidad_general <- reactive({
  req(Ingresos_mensual)
  df <- Ingresos_mensual
  nms <- names(df)

  anio_col   <- .pick_col(nms, c("Año","ano","ANO","Anio","anio","year","Year","YEAR"))
  mescod_col <- .pick_col(nms, c("mes.cod","mes_cod","mescod","Mes.cod","MES.COD"))
  mes_col    <- .pick_col(nms, c("mes","Mes","MES","month","Month","MONTH"))
  val_col    <- .pick_col(nms, c("Ingresos","ingresos","MONTO","Monto","monto",
                                 "Presupuesto a mes.cod","Presupuesto a devengado",
                                 "Presupuesto a mes"))

  req(!is.na(anio_col), !is.na(mescod_col), !is.na(mes_col), !is.na(val_col))

  df %>%
    dplyr::group_by(
      Año = .data[[anio_col]],
      mes.cod = .data[[mescod_col]],
      mes = .data[[mes_col]]
    ) %>%
    dplyr::summarise(
      Ingresos = sum(.data[[val_col]], na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::arrange(.data$Año, .data$mes.cod) %>%
    dplyr::mutate(
      Fecha = paste(.data$Año, .data$mes, sep = "-")
    )
})

estacionalidad_general <- reactive({
  df <- serie_estacionalidad_general()
  req(nrow(df) > 0)

  df <- df %>%
    dplyr::group_by(.data$Año) %>%
    dplyr::mutate(
      Total_anual = sum(.data$Ingresos),
      Estacionalidad = dplyr::if_else(.data$Total_anual == 0, NA_real_, .data$Ingresos / .data$Total_anual),
      Estacionalidad_acumulada = cumsum(dplyr::coalesce(.data$Estacionalidad, 0))
    ) %>%
    dplyr::ungroup()

  promedios <- df %>%
    dplyr::group_by(.data$mes, .data$mes.cod) %>%
    dplyr::summarise(
      Estacionalidad_promedio = mean(.data$Estacionalidad, na.rm = TRUE),
      Estacionalidad_acum_prom = mean(.data$Estacionalidad_acumulada, na.rm = TRUE),
      .groups = "drop"
    )

  dplyr::left_join(df, promedios, by = c("mes", "mes.cod")) %>%
    dplyr::arrange(.data$Año, .data$mes.cod)
})

output$Estacionalidad_1 <- renderHighchart({
  df <- estacionalidad_general()
  req(nrow(df) > 0)

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(name="Estacionalidad", data=round(df$Estacionalidad*100, 1)) %>%
    highcharter::hc_add_series(name="Estacionalidad promedio", data=round(df$Estacionalidad_promedio*100, 1)) %>%
    highcharter::hc_yAxis(title=list(text="% del total anual")) %>%
    highcharter::hc_chart(zoomType="xy")
})

output$Estacionalidad_2 <- renderHighchart({
  df <- estacionalidad_general()
  req(nrow(df) > 0)

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(name="Estacionalidad acumulada", data=round(df$Estacionalidad_acumulada*100, 1)) %>%
    highcharter::hc_add_series(name="Estacionalidad acumulada promedio", data=round(df$Estacionalidad_acum_prom*100, 1)) %>%
    highcharter::hc_yAxis(title=list(text="% acumulado")) %>%
    highcharter::hc_chart(zoomType="xy")
})

output$Estacionalidad_3 <- renderHighchart({
  df <- estacionalidad_general()
  req(nrow(df) > 0)

  limite_inf <- 0.8
  limite_sup <- 15.8

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(name="Estacionalidad", data=round(df$Estacionalidad*100, 1)) %>%
    highcharter::hc_add_series(name="Límite inferior", data=rep(limite_inf, nrow(df)), dashStyle="Dash") %>%
    highcharter::hc_add_series(name="Límite superior", data=rep(limite_sup, nrow(df)), dashStyle="Dash") %>%
    highcharter::hc_yAxis(title=list(text="% mensual")) %>%
    highcharter::hc_chart(zoomType="xy")
})
  
###############################################################################
# TAB SI2 — ESTACIONALIDAD INGRESOS TRIBUTARIOS (IT)
# Fuente: data/IT_estacionalidad.xlsx
###############################################################################

# ============================================================
# 1) Cargar IT_estacionalidad.xlsx como data.frame
# ============================================================
IT_Estacionalidad_df <- reactive({
  path_it <- file.path("data", "IT_estacionalidad.xlsx")
  req(file.exists(path_it))

  readxl::read_excel(path_it) %>%
    dplyr::mutate(
      Año = as.integer(.data$Año),
      mes.cod = as.integer(.data$`mes.cod`)
    ) %>%
    dplyr::arrange(.data$Año, .data$`mes.cod`)
})

# ============================================================
# 2) OUTPUT: Estacionalidad mensual (parámetro)
# ============================================================
output$Estacionalidad_IT_1 <- renderHighchart({
  df <- IT_Estacionalidad_df()
  req(df)

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad",
      data = round(df$Estacionalidad * 100, 1)
    ) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad promedio",
      data = round(df$`Estacionalidad promedio` * 100, 1)
    ) %>%
    highcharter::hc_yAxis(title = list(text = "% del total anual")) %>%
    highcharter::hc_chart(zoomType = "xy")
})

# ============================================================
# 3) OUTPUT: Estacionalidad acumulada (parámetro)
# ============================================================
output$Estacionalidad_IT_2 <- renderHighchart({
  df <- IT_Estacionalidad_df()
  req(df)

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad acumulada",
      data = round(df$Estacionalidad_acumulada * 100, 1)
    ) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad acumulada promedio",
      data = round(df$`Estacionalidad acumulada promedio` * 100, 1)
    ) %>%
    highcharter::hc_yAxis(title = list(text = "% acumulado")) %>%
    highcharter::hc_chart(zoomType = "xy")
})

# ============================================================
# 4) OUTPUT: Gráfico de control mensual (GC)
# ============================================================
output$Estacionalidad_IT_3 <- renderHighchart({
  df <- IT_Estacionalidad_df()
  req(df)

  limite_inf <- 0.9
  limite_sup <- 15.6

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad",
      data = round(df$Estacionalidad * 100, 1)
    ) %>%
    highcharter::hc_add_series(
      name = "Límite inferior",
      data = rep(limite_inf, nrow(df)),
      dashStyle = "Dash"
    ) %>%
    highcharter::hc_add_series(
      name = "Límite superior",
      data = rep(limite_sup, nrow(df)),
      dashStyle = "Dash"
    ) %>%
    highcharter::hc_yAxis(title = list(text = "% mensual")) %>%
    highcharter::hc_chart(zoomType = "xy")
}) 
  
###############################################################################
# TAB SI3 — ESTACIONALIDAD SEGÚN IMPUESTOS
###############################################################################

# ============================================================
# 1) Serie mensual del impuesto seleccionado
# ============================================================
serie_impuesto_sel <- reactive({
  req(Impuestos, input$variable5)

  var <- input$variable5
  req(var %in% names(Impuestos))

  Impuestos %>%
    dplyr::group_by(Año, mes.cod, mes) %>%
    dplyr::summarise(
      Ingresos = sum(.data[[var]], na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::arrange(Año, mes.cod) %>%
    dplyr::mutate(
      Fecha = paste(Año, mes, sep = "-")
    )
})

# ============================================================
# 2) Estacionalidades del impuesto seleccionado
# ============================================================
estacionalidad_impuesto_sel <- reactive({
  df <- serie_impuesto_sel()
  req(df)

  df <- df %>%
    dplyr::group_by(Año) %>%
    dplyr::mutate(
      Ingreso_acumulado = cumsum(Ingresos),
      Sumarecaudacion   = sum(Ingresos, na.rm = TRUE),
      Estacionalidad    = dplyr::if_else(Sumarecaudacion == 0, NA_real_, Ingresos / Sumarecaudacion),
      Estacionalidad_acumulada = cumsum(Estacionalidad)
    ) %>%
    dplyr::ungroup() %>%
    dplyr::arrange(Año, mes.cod)

  promedios <- df %>%
    dplyr::group_by(mes, mes.cod) %>%
    dplyr::summarise(
      `Estacionalidad promedio` = mean(Estacionalidad, na.rm = TRUE),
      `Estacionalidad acumulada promedio` = mean(Estacionalidad_acumulada, na.rm = TRUE),
      .groups = "drop"
    )

  dplyr::left_join(df, promedios, by = c("mes", "mes.cod")) %>%
    dplyr::arrange(Año, mes.cod)
})

# ============================================================
# 3) OUTPUT: Evolución del impuesto
# ============================================================
output$Estacionalidad_Impuestos_1 <- renderHighchart({
  df <- serie_impuesto_sel()
  req(df)

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha, title = list(text = "Año-mes")) %>%
    highcharter::hc_add_series(name = "Ingresos", data = df$Ingresos) %>%
    highcharter::hc_yAxis(title = list(text = "Colones")) %>%
    highcharter::hc_chart(zoomType = "xy")
})

# ============================================================
# 4) OUTPUT: Estacionalidad mensual (parámetro)
# ============================================================
output$Estacionalidad_Impuestos_2 <- renderHighchart({
  df <- estacionalidad_impuesto_sel()
  req(df)

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad",
      data = round(df$Estacionalidad * 100, 1)
    ) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad promedio",
      data = round(df$`Estacionalidad promedio` * 100, 1)
    ) %>%
    highcharter::hc_yAxis(title = list(text = "% del total anual")) %>%
    highcharter::hc_chart(zoomType = "xy")
})

# ============================================================
# 5) OUTPUT: Estacionalidad acumulada (parámetro)
# ============================================================
output$Estacionalidad_Impuestos_3 <- renderHighchart({
  df <- estacionalidad_impuesto_sel()
  req(df)

  highcharter::highchart() %>%
    highcharter::hc_xAxis(categories = df$Fecha) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad acumulada",
      data = round(df$Estacionalidad_acumulada * 100, 1)
    ) %>%
    highcharter::hc_add_series(
      name = "Estacionalidad acumulada promedio",
      data = round(df$`Estacionalidad acumulada promedio` * 100, 1)
    ) %>%
    highcharter::hc_yAxis(title = list(text = "% acumulado")) %>%
    highcharter::hc_chart(zoomType = "xy")
})
  
  # Gráfico de control
  
  ###########################################
  #              Descargar archivos         # 
  ###########################################
  
  
  #### ARchivo de los ingresos
  
  observeEvent(input$show2, {
    showModal(modalDialog(
      title = "Descargar archivo de los ingresos en el tiempo ",br(),
      "Seleccione el tipo de archivo de descarga", br(),
      br(),
      downloadButton("download2.1","Archivo .csv"),
      br(),
      br(),
      downloadButton("download2.2","Archivo .txt"),
      footer = modalButton("Cerrar"),
      easyClose = TRUE)
    )
    
  })
  
  
  
  output$download2.1 <- downloadHandler(
    
    
    filename = function() {
      paste("Ingresos-", Sys.Date(), ".csv", sep="")
    },
    
    content = function(file) {
      write.csv(Ingresos_0, file)
    }
  )
  
  output$download2.2 <- downloadHandler(
    
    filename = function() {
      paste("Ingresos-", Sys.Date(), ".txt", sep="")
    },
    content = function(file) {
      write.table(Ingresos_0, file)
    }
  )
  
  
  #### ARchivo de impuestos
  
  observeEvent(input$show1, {
    showModal(modalDialog(
      title = "Descargar archivo de los Impuestos en el tiempo ",br(),
      "Seleccione el tipo de archivo de descarga", br(),
      br(),
      downloadButton("download1","Archivo .csv"),
      br(),
      br(),
      downloadButton("download2","Archivo .txt"),
      footer = modalButton("Cerrar"),
      easyClose = TRUE)
    )
    
  })
  
  output$download1 <- downloadHandler(
    
    
    filename = function() {
      paste("Impuesto-", Sys.Date(), ".csv", sep="")
    },
    
    content = function(file) {
      write.csv(Impuestos, file)
    }
  )
  
  output$download2 <- downloadHandler(
    filename = function() {
      paste("Impuesto-", Sys.Date(), ".txt", sep="")
    },
    content = function(file) {
      write.table(Impuestos, file)
    }
  )
  
  
  
  
}