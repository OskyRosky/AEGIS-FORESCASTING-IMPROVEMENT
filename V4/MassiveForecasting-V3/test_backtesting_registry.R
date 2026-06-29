###############################################################################
# tests/test_backtesting_registry.R
#
# Propósito:
#   Smoke-test del backtesting rolling-origin usando el registry.
#   - Corre backtest_rolling_origin() con los 5 modelos oficiales
#   - Verifica filas esperadas en detalle y resumen
#   - Guarda un RDS demo de salida
#
# Se ejecuta con:
#   cd "/Users/sultan/DataScience/MassiveForescastingIncome/V2"
#   Rscript tests/test_backtesting_registry.R
###############################################################################

# ============================
# Resolución de rutas robusta
# ============================
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)

if (length(file_arg) > 0) {
  this_file <- sub("^--file=", "", file_arg[1])
  script_dir <- dirname(normalizePath(this_file))
} else {
  script_dir <- normalizePath(getwd())
}

root_dir <- normalizePath(file.path(script_dir, ".."), winslash = "/", mustWork = TRUE)
app_dir  <- normalizePath(file.path(root_dir, "Scripts_tablas_dashboard"), winslash = "/", mustWork = TRUE)

cat("DEBUG script_dir: ", script_dir, "\n", sep = "")
cat("DEBUG root_dir : ", root_dir, "\n", sep = "")
cat("DEBUG app_dir  : ", app_dir, "\n", sep = "")

stopifnot(dir.exists(app_dir))

# ============================
# Sources necesarios
# ============================
source(file.path(app_dir, "Librerias.R"), local = TRUE)
source(file.path(app_dir, "forecast_models_registry.R"), local = TRUE)
source(file.path(app_dir, "forecast_backtesting.R"), local = TRUE)

cat("✅ Sources cargados correctamente (backtesting)\n")

# ============================
# Serie de prueba (estable)
# ============================
y <- stats::ts(as.numeric(AirPassengers), frequency = 12, start = c(1949, 1))
cat("OK ts length: ", length(y), "\n", sep = "")
cat("OK ts start: ", paste(stats::start(y), collapse = ","), "\n", sep = "")
cat("OK ts freq: ", stats::frequency(y), "\n", sep = "")

# ============================
# Modelos oficiales (5)
# ============================
model_ids <- c("seasonal_naive", "ets", "autoarima", "nnetar", "tslm")

# Parámetros backtest (rápidos pero suficientes)
h <- 12
initial <- 60
step <- 1
seed <- 123

bt <- backtest_rolling_origin(
  y = y,
  model_ids = model_ids,
  h = h,
  initial = initial,
  step = step,
  fixed_window = FALSE,
  metrics = c("sMAPE", "wMAPE", "RMSE", "MAE", "MAPE"),
  mape_variant = "floor",
  rank_by = "sMAPE",
  seed = seed,
  level = 95
)

# ============================
# Validaciones
# ============================
stopifnot(is.list(bt))
stopifnot(!is.null(bt$meta), !is.null(bt$detalle), !is.null(bt$resumen))

cat("Meta n_cuts: ", bt$meta$n_cuts, "\n", sep = "")
cat("Detalle rows: ", nrow(bt$detalle), "\n", sep = "")
cat("Resumen rows: ", nrow(bt$resumen), "\n", sep = "")

# Resumen debe tener 5 modelos (si alguno falla siempre, acá lo detectamos)
if (nrow(bt$resumen) != length(model_ids)) {
  stop(
    "❌ backtesting resumen NO tiene 5 modelos.\n",
    "Esperado: ", length(model_ids), "\n",
    "Obtenido : ", nrow(bt$resumen), "\n",
    "Modelos en resumen: ", paste(bt$resumen$model_id, collapse = ", "),
    call. = FALSE
  )
}

print(bt$resumen)

# ============================
# Guardar demo
# ============================
out_rds <- file.path(root_dir, "tests", "backtest_airpassengers_demo_h12.rds")
saveRDS(bt, out_rds)
cat("OK guardado: ", basename(out_rds), "\n", sep = "")

cat("✅ test_backtesting_registry.R OK\n")