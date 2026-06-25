###############################################################################
# forecast_engine/_10_series_builders.R
#
# Propósito:
#   Construir la "serie mensual estándar" (contrato Fase 3) para cada componente:
#     - Total    (tabla_2)
#     - Tax      (Impuestos + variable seleccionada)
#     - Advanced (df filtrado por jerarquía)
#
# Contrato de salida (estándar):
#   - df_std: data.frame con:
#       Fecha_ord : Date (primer día del mes)
#       Ingresos  : numeric (en colones, sin escalar)
#   - y_ts_mill: ts mensual en millones (frequency=12), listo para modelar
#
# Reglas acordadas (Fase 3):
#   - Frecuencia: mensual (12)
#   - Último mes: SE INCLUYE (dato cerrado/correcto) [por defecto]
#   - Ceros/negativos/NA: imputación promedio (3 prev + 3 next) con fallback
#   - Unidad oficial de modelado: millones (la ts sale en millones)
###############################################################################

# =========================
# 1) Helpers internos
# =========================
# Nota importante:
# - Este archivo debe mantener UN SOLO .extract_month_dates()
# - El objetivo es tolerar datasets “sucios” (Año/mes con strings, Fecha en formatos mixtos, etc.)
# - Los errores deben ser explícitos y con diagnóstico, para evitar loops en Shiny.

# ---- 1.1: limpieza / coerción -----------------------------------------------

# Limpia a entero: quita todo lo que no sea dígito
.clean_int <- function(x) {
  suppressWarnings(as.integer(gsub("[^0-9]", "", trimws(as.character(x)))))
}

# Constructor robusto de mes:
# (Año, mes) -> Date YYYY-MM-01
# - Valida rango [1900..2100] y mes [1..12]
# - Si algo viene sucio -> NA, para permitir fallback (Fecha_ord / Fecha)
.make_month_date <- function(year, month) {
  yy <- .clean_int(year)
  mm <- .clean_int(month)

  ok <- is.finite(yy) & is.finite(mm) &
    !is.na(yy) & !is.na(mm) &
    mm >= 1 & mm <= 12 &
    yy >= 1900 & yy <= 2100

  out <- rep(NA, length(yy))
  out[ok] <- as.Date(sprintf("%04d-%02d-01", yy[ok], mm[ok]))
  out
}

# Parseo alterno desde columna Fecha (Date/POSIX/character):
# soporta: YYYY-MM, YYYY/MM, YYYYMM, YYYY-MM-DD, etc.
.parse_fecha_to_month <- function(x) {
  # Date / POSIX -> normalizamos al primer día del mes
  if (inherits(x, "Date")) {
    return(as.Date(format(x, "%Y-%m-01")))
  }
  if (inherits(x, "POSIXt")) {
    return(as.Date(format(as.Date(x), "%Y-%m-01")))
  }

  s <- trimws(as.character(x))
  s[s == ""] <- NA_character_

  # normalizar separadores
  s2 <- gsub("\\.", "-", s)
  s2 <- gsub("/", "-", s2)

  # caso YYYYMM (ej 202401) -> 2024-01-01
  is_yyyymm <- grepl("^\\d{6}$", s2)
  if (any(is_yyyymm, na.rm = TRUE)) {
    yy <- substr(s2[is_yyyymm], 1, 4)
    mm <- substr(s2[is_yyyymm], 5, 6)
    s2[is_yyyymm] <- paste0(yy, "-", mm, "-01")
  }

  # caso YYYY-MM o YYYY-M -> + "-01"
  is_yyyymm2 <- grepl("^\\d{4}-\\d{1,2}$", s2)
  if (any(is_yyyymm2, na.rm = TRUE)) {
    s2[is_yyyymm2] <- paste0(s2[is_yyyymm2], "-01")
  }

  # caso YYYY-MM-DD -> forzar día 01 (YYYY-MM-01)
  is_yyyymmdd <- grepl("^\\d{4}-\\d{1,2}-\\d{1,2}$", s2)
  if (any(is_yyyymmdd, na.rm = TRUE)) {
    yy <- sub("^([0-9]{4}).*$", "\\1", s2[is_yyyymmdd])
    mm <- sub("^[0-9]{4}-([0-9]{1,2}).*$", "\\1", s2[is_yyyymmdd])
    mm <- sprintf("%02d", suppressWarnings(as.integer(mm)))
    s2[is_yyyymmdd] <- paste0(yy, "-", mm, "-01")
  }

  suppressWarnings(as.Date(s2))
}

# ---- 1.2: extracción robusta de fecha mensual -------------------------------

# Extrae Fecha_ord mensual con prioridad y fallback:
# 1) (Año, mes.cod) si existe y sirve (ANY no-NA)
# 2) Fecha_ord si existe y sirve (ANY no-NA)
# 3) Fecha si existe y sirve (ANY no-NA)
# Si todo falla: stop con diagnóstico
.extract_month_dates <- function(df) {
  stopifnot(is.data.frame(df))

  # 1) Año + mes.cod (si existe, se intenta primero)
  if (all(c("Año", "mes.cod") %in% names(df))) {
    d <- .make_month_date(df$Año, df$`mes.cod`)
    if (any(!is.na(d))) return(d)
  }

  # 2) Fecha_ord
  if ("Fecha_ord" %in% names(df)) {
    fo <- df$Fecha_ord
    if (!inherits(fo, "Date")) fo <- suppressWarnings(as.Date(fo))
    if (any(!is.na(fo))) return(fo)
  }

  # 3) Fecha
  if ("Fecha" %in% names(df)) {
    fd <- .parse_fecha_to_month(df$Fecha)
    if (any(!is.na(fd))) return(fd)
  }

  # 4) Diagnóstico explícito
  msg <- c(
    "No se pudo inferir Fecha_ord (mensual) de forma válida.",
    "Opciones válidas:",
    "  - Columnas `Año` y `mes.cod` (limpias, 1..12), o",
    "  - `Fecha_ord` (Date o coercible), o",
    "  - `Fecha` parseable (YYYY-MM, YYYY/MM, YYYYMM, YYYY-MM-DD, Date/POSIXt).",
    "",
    "Ejemplo (primeras 10 filas de columnas relevantes):"
  )
  sample <- utils::head(df[, intersect(c("Año","mes.cod","Fecha_ord","Fecha"), names(df)), drop = FALSE], 10)
  stop(paste(c(msg, capture.output(print(sample))), collapse = "\n"), call. = FALSE)
}

# ---- 1.3: imputación / standardización --------------------------------------

# Imputación 3 prev + 3 next con fallback:
# - Aplica para NA y valores <= 0
# - Fallback: usa vecinos disponibles; si no hay, deja NA.
.impute_3x3 <- function(x) {
  x <- as.numeric(x)
  n <- length(x)
  bad <- which(is.na(x) | x <= 0)
  if (length(bad) == 0) return(x)

  for (i in bad) {
    left_idx  <- (i - 3):(i - 1)
    right_idx <- (i + 1):(i + 3)

    left_idx  <- left_idx[left_idx >= 1]
    right_idx <- right_idx[right_idx <= n]

    neigh <- c(x[left_idx], x[right_idx])
    neigh <- neigh[is.finite(neigh) & neigh > 0]

    if (length(neigh) > 0) {
      x[i] <- mean(neigh)
    } else {
      x[i] <- NA_real_
    }
  }

  x
}

# Dado: vector fechas (Date) y vector ingresos (num),
# devuelve df_std mensual colapsado, ordenado y con opción de incluir último mes.
# Robustez:
# - Elimina filas con Fecha_ord NA
# - Falla temprano si se queda sin filas (evita loops “silenciosos”)
.build_df_std <- function(fecha_ord, ingresos, incluir_ultimo_mes = TRUE, ctx = "builder") {
  df <- data.frame(
    Fecha_ord = as.Date(fecha_ord),
    Ingresos  = suppressWarnings(as.numeric(ingresos)),
    stringsAsFactors = FALSE
  )

  # limpiar filas inválidas de fecha
  df <- df[!is.na(df$Fecha_ord), , drop = FALSE]

  if (nrow(df) == 0) {
    stop(paste0(ctx, ": no quedaron filas con Fecha_ord válida luego de limpiar."),
         call. = FALSE)
  }

  df <- df[order(df$Fecha_ord), , drop = FALSE]

  # colapsar por mes (por si hay duplicados)
  df <- stats::aggregate(Ingresos ~ Fecha_ord, data = df, FUN = sum, na.rm = TRUE)
  df <- df[order(df$Fecha_ord), , drop = FALSE]

  if (!isTRUE(incluir_ultimo_mes) && nrow(df) > 1) {
    df <- df[1:(nrow(df) - 1), , drop = FALSE]
  }

  df
}

# Construir ts mensual (en millones) desde df estándar
.to_ts_mill <- function(df_std, millones = 1e6, ctx = "builder") {
  stopifnot(is.data.frame(df_std))
  stopifnot(all(c("Fecha_ord", "Ingresos") %in% names(df_std)))
  stopifnot(inherits(df_std$Fecha_ord, "Date"))

  df_std <- df_std[order(df_std$Fecha_ord), , drop = FALSE]
  y_mill <- as.numeric(df_std$Ingresos) / millones

  start_year  <- as.integer(format(df_std$Fecha_ord[1], "%Y"))
  start_month <- as.integer(format(df_std$Fecha_ord[1], "%m"))

  stats::ts(y_mill, frequency = 12, start = c(start_year, start_month))
}

# =========================
# 2) Builder — TOTAL (tabla_2)
# =========================
# Soporta:
# - tabla_2 con columnas (Año, mes.cod, Ingresos)
# - o tabla_2 con (Fecha, Ingresos)
# - o tabla_2 con (Fecha_ord, Ingresos)

build_series_total <- function(tabla_2,
                               imputar = TRUE,
                               incluir_ultimo_mes = TRUE,
                               millones = 1e6) {

  # ---- Validación básica de entrada -----------------------------------------
  if (missing(tabla_2) || is.null(tabla_2) || !is.data.frame(tabla_2)) {
    stop("build_series_total(): tabla_2 debe ser un data.frame.", call. = FALSE)
  }
  if (!("Ingresos" %in% names(tabla_2))) {
    stop("build_series_total(): falta columna requerida: Ingresos", call. = FALSE)
  }

  # ---- Construcción de df_std -----------------------------------------------
  fecha_ord <- .extract_month_dates(tabla_2)
  df_std <- .build_df_std(
    fecha_ord = fecha_ord,
    ingresos  = tabla_2$Ingresos,
    incluir_ultimo_mes = incluir_ultimo_mes,
    ctx = "build_series_total()"
  )

  # ---- Imputación ------------------------------------------------------------
  if (isTRUE(imputar)) {
    df_std$Ingresos <- .impute_3x3(df_std$Ingresos)
  }

  # ---- Validación de longitud (en el lugar correcto) ------------------------
  if (nrow(df_std) < 24) {
    stop(
      paste0("build_series_total(): Serie demasiado corta. Quedaron ", nrow(df_std),
             " meses. Se requieren al menos 24."),
      call. = FALSE
    )
  }

  # ---- Validación: no dejar NA tras imputación ------------------------------
  if (any(is.na(df_std$Ingresos))) {
    sample <- utils::head(df_std[is.na(df_std$Ingresos), , drop = FALSE], 10)
    stop(
      paste(
        "build_series_total(): quedaron NA en Ingresos luego de imputar.",
        "Ejemplos (primeras filas con NA):",
        paste(capture.output(print(sample)), collapse = "\n"),
        sep = "\n"
      ),
      call. = FALSE
    )
  }

  # ---- ts mensual en millones -----------------------------------------------
  y_ts_mill <- .to_ts_mill(df_std, millones = millones, ctx = "build_series_total()")

  list(
    df_std    = df_std,     # Fecha_ord + Ingresos (colones)
    y_ts_mill = y_ts_mill   # ts mensual en millones
  )
}

# =========================
# 3) Builder — TAX (Impuestos + variable seleccionada)
# =========================
# Espera:
# - Impuestos con (Año, mes.cod) o Fecha/Fecha_ord
# - variable_col numérica

build_series_tax <- function(Impuestos, variable_col,
                             imputar = TRUE,
                             incluir_ultimo_mes = TRUE,
                             millones = 1e6) {

  if (missing(Impuestos) || is.null(Impuestos) || !is.data.frame(Impuestos)) {
    stop("build_series_tax(): Impuestos debe ser un data.frame.", call. = FALSE)
  }
  if (!is.character(variable_col) || length(variable_col) != 1) {
    stop("build_series_tax(): variable_col debe ser un string (nombre de columna).", call. = FALSE)
  }
  if (!(variable_col %in% names(Impuestos))) {
    stop(paste0("build_series_tax(): no existe la columna: ", variable_col), call. = FALSE)
  }

  fecha_ord <- .extract_month_dates(Impuestos)
  ingresos  <- suppressWarnings(as.numeric(Impuestos[[variable_col]]))

  df_std <- .build_df_std(
    fecha_ord = fecha_ord,
    ingresos  = ingresos,
    incluir_ultimo_mes = incluir_ultimo_mes,
    ctx = "build_series_tax()"
  )

  if (isTRUE(imputar)) {
    df_std$Ingresos <- .impute_3x3(df_std$Ingresos)
  }

  if (nrow(df_std) < 24) {
    stop(paste0("build_series_tax(): Serie demasiado corta (", nrow(df_std), " meses)."), call. = FALSE)
  }
  if (any(is.na(df_std$Ingresos))) {
    stop("build_series_tax(): quedaron NA en Ingresos luego de imputar.", call. = FALSE)
  }

  y_ts_mill <- .to_ts_mill(df_std, millones = millones, ctx = "build_series_tax()")

  list(df_std = df_std, y_ts_mill = y_ts_mill)
}

# =========================
# 4) Builder — ADVANCED (df filtrado por jerarquía)
# =========================
# Soporta:
# - fecha por (Año+mes.cod) o (Fecha_ord) o (Fecha)
# - columna de valor flexible (prioridad):
#     Ingresos, ingresos, monto, Monto, MONTO,
#     "Presupuesto a mes.cod" (y variantes)

build_series_advanced <- function(df_filtrado,
                                  imputar = TRUE,
                                  incluir_ultimo_mes = TRUE,
                                  millones = 1e6) {

  if (missing(df_filtrado) || is.null(df_filtrado) || !is.data.frame(df_filtrado)) {
    stop("build_series_advanced(): df_filtrado debe ser un data.frame.", call. = FALSE)
  }

  # detectar columna de valor
  value_candidates <- c(
    "Ingresos", "ingresos", "monto", "Monto", "MONTO",
    "Presupuesto a mes.cod", "Presupuesto a mes.cod.", "Presupuesto_a_mes.cod",
    "Presupuesto a mes.cod "
  )
  value_col <- intersect(value_candidates, names(df_filtrado))[1]

  if (is.na(value_col)) {
    stop(
      "build_series_advanced(): No encuentro columna numérica (Ingresos/monto/Monto/Presupuesto a mes.cod) en df_filtrado.",
      call. = FALSE
    )
  }

  fecha_ord <- .extract_month_dates(df_filtrado)
  ingresos  <- suppressWarnings(as.numeric(df_filtrado[[value_col]]))

  df_std <- .build_df_std(
    fecha_ord = fecha_ord,
    ingresos  = ingresos,
    incluir_ultimo_mes = incluir_ultimo_mes,
    ctx = "build_series_advanced()"
  )

  if (isTRUE(imputar)) {
    df_std$Ingresos <- .impute_3x3(df_std$Ingresos)
  }

  if (nrow(df_std) < 24) {
    stop(paste0("build_series_advanced(): Serie demasiado corta (", nrow(df_std), " meses)."), call. = FALSE)
  }
  if (any(is.na(df_std$Ingresos))) {
    stop("build_series_advanced(): quedaron NA en Ingresos luego de imputar.", call. = FALSE)
  }

  y_ts_mill <- .to_ts_mill(df_std, millones = millones, ctx = "build_series_advanced()")

  list(df_std = df_std, y_ts_mill = y_ts_mill)
}