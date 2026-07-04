###############################################################################
# forecast_helpers.R
#
# Propósito:
#   Helpers canónicos para construir series mensuales para Forecasting.
#   Este archivo NO dibuja gráficos ni usa Shiny outputs.
#   Solo construye:
#     - una tabla mensual estándar (Fecha_str, Fecha_ord, Ingresos)
#     - un objeto ts (frecuencia 12) con start dinámico
#
# Reglas fijas del proyecto (ETAPA 1):
#   1) Frecuencia: 12 (mensual)
#   2) Start: dinámico desde la primera observación disponible (YYYY-MM)
#   3) Último mes incompleto: por defecto se elimina (remove_last = TRUE)
#   4) Valores problemáticos (<=0 o NA): imputación por promedio de 4 previos válidos
#   5) Unidad: se controla por parámetro (scale = "colones" o "millones")
###############################################################################

# ============================
# Utils básicos
# ============================

safe_num <- function(x) {
  suppressWarnings(as.numeric(x))
}

assert_has_cols <- function(df, cols, ctx = "dataset") {
  missing <- setdiff(cols, names(df))
  if (length(missing) > 0) {
    stop(paste0("Faltan columnas en ", ctx, ": ", paste(missing, collapse = ", ")))
  }
  invisible(TRUE)
}

# Construye "YYYY-MM" a partir de columnas Año + mes (texto) o Año + mes.cod/mes_cod
make_fecha_str <- function(df) {
  if ("Fecha" %in% names(df)) {
    out <- substr(as.character(df$Fecha), 1, 7)
    return(out)
  }

  # Columna mes código
  month_code_col <- dplyr::case_when(
    "mes_cod" %in% names(df) ~ "mes_cod",
    "mes.cod" %in% names(df) ~ "mes.cod",
    "mes.cod" %in% names(df) ~ "mes.cod",
    TRUE ~ NA_character_
  )

  if (!("Año" %in% names(df))) stop("Falta columna 'Año' para construir Fecha_str.")
  if (is.na(month_code_col)) stop("Falta columna de mes: no existe mes_cod ni mes.cod.")

  sprintf("%04d-%02d", as.integer(df$Año), as.integer(df[[month_code_col]]))
}

# ============================
# Imputación: promedio últimos 4 válidos
# ============================

impute_last4_mean <- function(x) {
  x <- safe_num(x)

  for (i in seq_along(x)) {
    if (is.na(x[i]) || !is.finite(x[i]) || x[i] <= 0) {
      prev <- x[seq_len(i - 1)]
      prev <- prev[is.finite(prev) & !is.na(prev) & prev > 0]

      if (length(prev) == 0) {
        x[i] <- NA_real_      # no inventamos
      } else {
        k <- min(4, length(prev))
        x[i] <- mean(tail(prev, k), na.rm = TRUE)
      }
    }
  }
  x
}

# ============================
# Serie mensual estándar (tabla)
# ============================

prep_serie_mensual_std <- function(df,
                                  value_col = NULL,
                                  remove_last = TRUE,
                                  impute_bad = TRUE) {
  stopifnot(is.data.frame(df))

  # 1) Identificar columna de valores
  if (is.null(value_col)) {
    value_col <- intersect(c("Ingresos", "monto", "Monto"), names(df))[1]
  }
  if (is.na(value_col) || is.null(value_col) || !nzchar(value_col)) {
    stop("No encuentro columna de valores. Pase value_col explícito (ej: 'Ingresos').")
  }
  if (!(value_col %in% names(df))) {
    stop(paste0("value_col='", value_col, "' no existe en el data frame."))
  }

  # 2) Crear Fecha_str canónica (YYYY-MM)
  df <- df %>% dplyr::mutate(Fecha_str = make_fecha_str(.))

  # 3) Agrupar por mes
  out <- df %>%
    dplyr::mutate(.val = safe_num(.data[[value_col]])) %>%
    dplyr::group_by(.data$Fecha_str) %>%
    dplyr::summarise(
      Ingresos = sum(.data$.val, na.rm = TRUE),
      .groups = "drop"
    ) %>%
    dplyr::mutate(
      Fecha_ord = as.Date(paste0(.data$Fecha_str, "-01"))
    ) %>%
    dplyr::arrange(.data$Fecha_ord)

  # 4) (Opcional) eliminar último mes (típicamente incompleto)
  if (isTRUE(remove_last) && nrow(out) > 1) {
    out <- out %>% dplyr::slice(1:(nrow(out) - 1))
  }

  # 5) Imputación de valores problemáticos
  out <- out %>% dplyr::mutate(Ingresos = safe_num(.data$Ingresos))

  if (isTRUE(impute_bad)) {
    out <- out %>% dplyr::mutate(Ingresos = impute_last4_mean(.data$Ingresos))
  }

  # 6) Limpieza final: quedarnos con finitos (NA al inicio pueden quedar)
  out <- out %>% dplyr::mutate(Ingresos = safe_num(.data$Ingresos))

  out
}

# ============================
# Convertir a ts (mensual) con start dinámico
# ============================

to_ts_mensual <- function(serie_df, scale = c("millones", "colones")) {
  scale <- match.arg(scale)
  assert_has_cols(serie_df, c("Fecha_ord", "Ingresos"), ctx = "serie mensual")

  d <- serie_df %>%
    dplyr::filter(is.finite(.data$Ingresos), !is.na(.data$Ingresos)) %>%
    dplyr::arrange(.data$Fecha_ord)

  if (nrow(d) < 24) {
    stop("No hay suficientes observaciones mensuales (mínimo recomendado: 24).")
  }

  y <- safe_num(d$Ingresos)

  if (scale == "millones") {
    y <- y / 1000000
  }

  start_year  <- as.integer(format(d$Fecha_ord[1], "%Y"))
  start_month <- as.integer(format(d$Fecha_ord[1], "%m"))

  stats::ts(y, frequency = 12, start = c(start_year, start_month))
}