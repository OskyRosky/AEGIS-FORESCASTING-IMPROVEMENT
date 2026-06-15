###############################################################################
# importacion.R  (V2 - final)
#
# Propósito:
#   Adaptador único de datos para el dashboard.
#   - Usa por defecto el artefacto canónico: exports/datasets_canonic.rds
#   - Si falla y está permitido, hace fallback a Excel (en memoria).
#
# Diseño:
#   - NO cocina datos en runtime.
#   - NO imprime nada en modo normal.
#   - Expone variables "legacy" para no romper server.R / ui.R / body.R.
#
# Control:
#   - APP_VERBOSE=1  -> mensajes informativos
###############################################################################

# ------------------------------------------------------------------
# Verbosidad (control por ENV)
# ------------------------------------------------------------------
APP_VERBOSE <- identical(Sys.getenv("APP_VERBOSE", "0"), "1")

.vmsg <- function(...) {
  if (isTRUE(APP_VERBOSE)) message(...)
}

# ------------------------------------------------------------------
# Data access (canónico)
# ------------------------------------------------------------------
# get_data() vive aquí
source("R/05_data_access.R", local = TRUE)

# Permitir o no fallback a Excel (diseño explícito)
allow_excel_fallback <- TRUE

# Solo cargamos loaders si hay posibilidad real de fallback
if (isTRUE(allow_excel_fallback)) {
  if (!exists("load_data", mode = "function")) {
    source("R/02_load_data.R", local = TRUE)
  }
  if (!exists("clean_standardize", mode = "function")) {
    source("R/03_clean_standardize.R", local = TRUE)
  }
}

# ------------------------------------------------------------------
# Carga de datasets canónicos
# ------------------------------------------------------------------
ds <- get_data(
  prefer = "rds",
  verbose = APP_VERBOSE,                 # mudo en normal
  allow_excel_fallback = allow_excel_fallback,
  save_fallback_rds = FALSE
)

# ------------------------------------------------------------------
# Helpers: renombre canónico -> legacy
# ------------------------------------------------------------------
.rename_cols_if_present <- function(df, mapping) {
  if (is.null(df) || !is.data.frame(df)) return(df)

  nm <- names(df)
  for (from in names(mapping)) {
    to <- mapping[[from]]
    if (from %in% nm && !(to %in% nm)) {
      nm[nm == from] <- to
    }
  }
  names(df) <- nm
  df
}

# Mapeo clave: lo que 03_clean_standardize estandariza a "_" y el server espera con "."
.map_legacy <- c(
  "mes_cod"              = "mes.cod",
  "var_Ingresos"         = "var.Ingresos",
  "var_acum_12"          = "var.acum_12",
  "var_cum_ano_Ingresos" = "var.cum_ano_Ingresos",
  "Carga_tributaria"     = "Carga tributaria"
)

# ------------------------------------------------------------------
# 1) Glosario
# ------------------------------------------------------------------
conceptos <- ds$glossary

# ------------------------------------------------------------------
# 2) Core mensual (renombrado a legacy)
# ------------------------------------------------------------------
Estacionalidad    <- .rename_cols_if_present(ds$monthly_core$estacionalidad,     .map_legacy)
IT_Estacionalidad <- .rename_cols_if_present(ds$monthly_core$it_estacionalidad, .map_legacy)

tabla_2     <- .rename_cols_if_present(ds$monthly_core$tabla_2,     .map_legacy)
tabla_2_var <- .rename_cols_if_present(ds$monthly_core$tabla_2_var, .map_legacy)

tabla.evo.mensual.1_acum <- .rename_cols_if_present(ds$monthly_core$evo_mensual_1_acum, .map_legacy)
tabla.evo.mensual.2_acum <- .rename_cols_if_present(ds$monthly_core$evo_mensual_2_acum, .map_legacy)
tabla.evo.mensual.3_acum <- .rename_cols_if_present(ds$monthly_core$evo_mensual_3_acum, .map_legacy)

Impuestos <- .rename_cols_if_present(ds$monthly_core$impuestos, .map_legacy)

# ------------------------------------------------------------------
# 3) Jerárquicos / ingresos
# ------------------------------------------------------------------
Ingresos         <- ds$hierarchical$ingresos_anual
Ingresos_0       <- ds$hierarchical$ingresos_anual_s0
Ingresos_mensual <- ds$hierarchical$ingresos_mensual

# ------------------------------------------------------------------
# 4) Indicadores (legacy real: server.R usa ind1$Ingresos, ind4$`var.Ingresos`, etc.)
# ------------------------------------------------------------------
.kpi_value <- function(name) {
  val <- ds$kpis$value[ds$kpis$indicator == name]
  if (length(val) == 0) return(NA_real_)
  as.numeric(val[[1]])
}

indicador.1 <- data.frame(Ingresos = .kpi_value("indicador_1"))
indicador.2 <- data.frame(Ingresos = .kpi_value("indicador_2"))
indicador.3 <- data.frame(Ingresos = .kpi_value("indicador_3"))
indicador.4 <- data.frame(`var.Ingresos` = .kpi_value("indicador_4"))
indicador.5 <- data.frame(`var.acum_12`  = .kpi_value("indicador_5"))
indicador.6 <- data.frame(`var.cum_ano_Ingresos` = .kpi_value("indicador_6"))

# ------------------------------------------------------------------
# 5) tabla_1 (excepción temporal fuera del canónico)
# ------------------------------------------------------------------
tabla_1_path <- file.path("data", "tabla_1.xlsx")

if (file.exists(tabla_1_path)) {
  tabla_1 <- readxl::read_excel(tabla_1_path)
} else {
  tabla_1 <- NULL
  .vmsg("⚠️ tabla_1.xlsx no existe en data/. tabla_1 se deja como NULL.")
}

.vmsg("✅ importacion.R: variables legacy cargadas.")