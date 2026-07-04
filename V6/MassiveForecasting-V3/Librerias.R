###############################################################################
# Librerias.R
#
# Propósito:
#   Punto único de carga de dependencias para toda la app/pipeline.
#
# Contrato:
#   - Paquetes requeridos: stop() claro si falta alguno.
#   - Paquetes opcionales (ML/paralelo): warning() si falta; la app sigue
#     funcionando. El error aparece solo al usar el modelo/feature en cuestión.
#   - Silencioso por defecto.
#   - APP_VERBOSE=1 muestra mensajes de intención.
#
# Paquetes opcionales y cuándo se necesitan:
#   future, furrr  -> backtest_rolling_origin(..., parallel = TRUE)
#   prophet        -> run_model_forecast("prophet", ...)
#   xgboost        -> run_model_forecast("xgboost", ...)
#
# Instalación de opcionales:
#   install.packages(c("future", "furrr", "prophet", "xgboost"))
###############################################################################

APP_VERBOSE <- identical(Sys.getenv("APP_VERBOSE", "0"), "1")

.required_pkgs <- c(
  # I/O & data
  "readxl", "readr", "data.table",

  # Data wrangling
  "dplyr", "tidyr", "janitor", "stringi",

  # Shiny + UI
  "shiny", "shinydashboard", "shinyWidgets", "DT", "htmltools",

  # Viz & tables
  "highcharter", "viridisLite", "scales", "gt", "reactable", "formattable",
  "sunburstR", "d3r",

  # Time series / utils
  "forecast", "RcppRoll",

  # Assets
  "png"
)

# Paquetes opcionales: no bloquean el arranque si faltan.
# Se acceden vía :: en el código (no se hace library() aquí).
.optional_pkgs <- c(
  "future",   # paralelización del backtesting
  "furrr",    # paralelización del backtesting
  "prophet",  # modelo Prophet (Meta)
  "xgboost"   # modelo XGBoost
)

.msg <- function(...) if (isTRUE(APP_VERBOSE)) message(...)

.load_pkg <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop(
      "❌ Falta el paquete: '", pkg, "'.\n",
      "Instalalo con:\n  install.packages(\"", pkg, "\")\n",
      call. = FALSE
    )
  }
  # Cargar y silenciar TODO lo que normalmente "habla"
  suppressMessages(
    suppressPackageStartupMessages(
      library(pkg, character.only = TRUE, quietly = TRUE, warn.conflicts = FALSE)
    )
  )
  invisible(TRUE)
}

.check_optional_pkg <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    warning(
      "⚠️  Paquete opcional no disponible: '", pkg, "'. ",
      "Instálalo con: install.packages(\"", pkg, "\")",
      call. = FALSE, immediate. = TRUE
    )
    return(invisible(FALSE))
  }
  invisible(TRUE)
}

.msg("📦 Cargando librerías (APP_VERBOSE=1)...")
invisible(lapply(.required_pkgs, .load_pkg))
.msg("✅ Librerías cargadas: ", length(.required_pkgs))

.msg("🔍 Verificando paquetes opcionales (APP_VERBOSE=1)...")
invisible(lapply(.optional_pkgs, .check_optional_pkg))
.msg("✅ Verificación opcionales completada.")