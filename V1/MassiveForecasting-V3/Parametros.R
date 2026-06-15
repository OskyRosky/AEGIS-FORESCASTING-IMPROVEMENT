###############################################################################
# Parametros.R
#
# Propósito:
#   Parámetros globales (datos + dashboard) en un solo lugar.
#   Este archivo define tanto variables legacy (usadas por el dashboard viejo)
#   como aliases "nuevos" (en mayúscula) para ir estandarizando sin romper nada.
#
# Nota:
#   - Evitamos hardcodes de paths; por defecto:
#       DATA_DIR="data"
#       EXPORTS_DIR="exports"
#       RDS_PATH="exports/datasets_canonic.rds"
###############################################################################

# Verbosidad (si lo necesitás en el futuro)
APP_VERBOSE <- identical(Sys.getenv("APP_VERBOSE", "0"), "1")

# -------------------------------
# Paths (centralizados)
# -------------------------------
DATA_DIR    <- Sys.getenv("DATA_DIR", "data")
EXPORTS_DIR <- Sys.getenv("EXPORTS_DIR", "exports")
RDS_PATH    <- file.path(EXPORTS_DIR, "datasets_canonic.rds")

# -------------------------------
# Millones
# -------------------------------
Millones <- 1000000

# -------------------------------
# Delimitación años análisis
# -------------------------------
Anos_analisis <- 2007

# -------------------------------
# Fechas de referencia (LEGACY)
# -------------------------------
Ano_actual   <- as.numeric(substr(Sys.Date(), 1, 4))
Ano_pasado_1 <- Ano_actual - 1
Ano_pasado_2 <- Ano_actual - 2

mes_actual <- as.numeric(substr(Sys.Date(), 6, 7))   # 1..12
Mes_actual <- substr(Sys.Date(), 6, 7)               # "01".."12"

Faltante_mes <- 12 - mes_actual

# -------------------------------
# Aliases "nuevos" (ESTÁNDAR)
# -------------------------------
ANO_ACTUAL      <- Ano_actual
ANO_PASADO_1    <- Ano_pasado_1
ANO_PASADO_2    <- Ano_pasado_2
MES_ACTUAL      <- mes_actual
MES_ACTUAL_STR  <- Mes_actual
FALTANTE_MES    <- Faltante_mes