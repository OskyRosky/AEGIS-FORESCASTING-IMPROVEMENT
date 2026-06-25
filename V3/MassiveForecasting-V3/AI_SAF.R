###############################################################################
# AI_SAF.R
#
# Massive Forecasting Income — Shiny App Runner
#
# Objetivo:
#   Levantar la app Shiny consumiendo datasets canónicos (RDS) por defecto.
#   La app NO cocina datos en runtime; eso se hace vía pipeline.
#
# Cómo correr (modo normal):
#   cd "/Users/sultan/DataScience/MassiveForescastingIncome/V2"
#   Rscript AI_SAF.R
#
# Modo mantenimiento (pipeline, sin Shiny):
#   RUN_PIPELINE=1 Rscript AI_SAF.R
#
# Verbose (solo si querés ver detalles):
#   APP_VERBOSE=1 Rscript AI_SAF.R
###############################################################################

#######################
# Opciones generales  #
#######################
options(encoding = "utf-8")
options(scipen = 999)
options(warn = 0)

##########################
# Verbosidad (control)   #
##########################
APP_VERBOSE <- identical(Sys.getenv("APP_VERBOSE", "0"), "1")

.vmsg <- function(...) {
  if (isTRUE(APP_VERBOSE)) message(...)
}

##########################
# Helper: source "limpio"#
##########################
.source_quiet <- function(file, envir = parent.frame()) {
  suppressWarnings(
    suppressMessages(
      source(file, local = envir)
    )
  )
}

.source_maybe_quiet <- function(file, envir = parent.frame()) {
  if (isTRUE(APP_VERBOSE)) {
    source(file, local = envir)
  } else {
    .source_quiet(file, envir = envir)
  }
}

##########################
# Resolver working dir   #
##########################
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)

if (length(file_arg) > 0) {
  this_file <- sub("^--file=", "", file_arg[1])
  base_dir  <- dirname(normalizePath(this_file))
} else {
  base_dir <- getwd()
  .vmsg("ℹ️  No se detectó --file=. Usando getwd() como base_dir: ", base_dir)
}

app_dir <- file.path(base_dir, "Scripts_tablas_dashboard")
if (!dir.exists(app_dir)) {
  stop(
    "No existe el directorio esperado: ", app_dir,
    "\nAsegurate de correr desde V2 o ejecutar: Rscript AI_SAF.R desde la carpeta V2.",
    call. = FALSE
  )
}

# Mantengo el setwd (tu regla), pero además blindo los source con rutas absolutas.
setwd(app_dir)
.vmsg("📁 Working dir: ", normalizePath(getwd()))

# Helper para source absoluto (no depende del setwd si algún script lo cambia)
.src <- function(rel_path) file.path(app_dir, rel_path)

##########################
# Librerías y parámetros #
##########################
.source_maybe_quiet(.src("Librerias.R"))
.source_maybe_quiet(.src("Parametros.R"))

##########################
# Forecasting (Fase 3)   #
# IMPORTANTE: antes de UI/Server
##########################
# ✅ ORDEN ROBUSTO:
#   1) registry (run_model_forecast)
#   2) helpers  (utilidades compartidas)
#   3) backtesting (usa registry + helpers)
#   4) engine + runners (usan todo lo anterior)

.source_maybe_quiet(.src("forecast_models_registry.R"))   # run_model_forecast()
.source_maybe_quiet(.src("forecast_helpers.R"))           # helpers (si aplica)
.source_maybe_quiet(.src("forecast_backtesting.R"))       # backtest_rolling_origin()

.source_maybe_quiet(.src("forecast_engine/_10_series_builders.R"))
.source_maybe_quiet(.src("forecast_engine/_30_engine.R"))
.source_maybe_quiet(.src("forecast_engine/_20_forecast_runner.R"))

##########################
# Modo mantenimiento     #
##########################
run_pipeline <- identical(Sys.getenv("RUN_PIPELINE", "0"), "1")

if (run_pipeline) {

  .vmsg("🛠️ RUN_PIPELINE=1 -> ejecutando pipeline (validación + rebuild RDS) ...")

  .source_maybe_quiet(.src("R/01_validate_inputs.R"))
  validate_inputs(verbose = APP_VERBOSE)

  .source_maybe_quiet(.src("R/04_build_datasets.R"))
  build_and_save_canonic(verbose = APP_VERBOSE)

  if (isTRUE(APP_VERBOSE)) {
    .vmsg("✅ Pipeline completado. (RDS actualizado en exports/)")
  } else {
    cat("✅ Pipeline: OK\n")
  }

  q("no", status = 0)
}

##########################
# Datos para la app      #
##########################
.source_maybe_quiet(.src("importacion.R"))

##########################
# UI y Server (Shiny)    #
##########################
.source_maybe_quiet(.src("header.R"))
.source_maybe_quiet(.src("sider.R"))
.source_maybe_quiet(.src("body.R"))
.source_maybe_quiet(.src("ui.R"))
.source_maybe_quiet(.src("server.R"))

##########################
# Levantar Shiny         #
##########################
HOST <- Sys.getenv("SHINY_HOST", "127.0.0.1")

port_raw <- Sys.getenv("SHINY_PORT", "7702")
PORT <- suppressWarnings(as.integer(port_raw))
if (is.na(PORT) || PORT <= 0) {
  PORT <- 7702L
  .vmsg("⚠️  SHINY_PORT inválido (", port_raw, "). Usando PORT=", PORT)
}

.vmsg("🚀 Shiny en: http://", HOST, ":", PORT)

if (isTRUE(APP_VERBOSE)) {
  shiny::runApp(
    launch.browser = identical(Sys.getenv("SHINY_LAUNCH_BROWSER", "1"), "1"),
    port = PORT,
    host = HOST
  )
} else {
  suppressWarnings(
    suppressMessages(
      shiny::runApp(
        launch.browser = identical(Sys.getenv("SHINY_LAUNCH_BROWSER", "1"), "1"),
        port = PORT,
        host = HOST
      )
    )
  )
}