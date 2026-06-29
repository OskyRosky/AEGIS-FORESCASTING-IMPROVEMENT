###############################################################################
# tests/test_registry_modelos.R
#
# Propósito:
#   Testear el Model Registry (Etapa 3) con 5 modelos oficiales.
#   - Verifica que list_models() contenga EXACTAMENTE los 5 esperados
#   - Verifica que cada modelo:
#       * devuelve mean de largo h
#       * devuelve flags coherentes
#       * nnetar es reproducible con seed
#
# Se ejecuta con:
#   cd "/Users/sultan/DataScience/MassiveForescastingIncome/V2"
#   Rscript tests/test_registry_modelos.R
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
# Sources mínimos necesarios
# ============================
source(file.path(app_dir, "Librerias.R"), local = TRUE)
source(file.path(app_dir, "forecast_models_registry.R"), local = TRUE)

cat("✅ Sources cargados correctamente (registry)\n")

# ============================
# Serie de prueba (simple y estable)
# ============================
y <- stats::ts(as.numeric(AirPassengers), frequency = 12, start = c(1949, 1))
cat("OK ts length: ", length(y), "\n", sep = "")
cat("OK ts start: ", paste(stats::start(y), collapse = ","), "\n", sep = "")
cat("OK ts freq: ", stats::frequency(y), "\n", sep = "")

# ============================
# Validar catálogo EXACTO (5 modelos)
# ============================
expected <- c("seasonal_naive", "ets", "autoarima", "nnetar", "tslm")

models <- list_models()
stopifnot(is.data.frame(models))
stopifnot("model_id" %in% names(models))

got <- sort(unique(as.character(models$model_id)))
exp <- sort(expected)

if (!identical(got, exp)) {
  stop(
    "❌ list_models() NO coincide con el set oficial.\n",
    "Esperado: ", paste(exp, collapse = ", "), "\n",
    "Obtenido : ", paste(got, collapse = ", "),
    call. = FALSE
  )
}

cat("✅ list_models() contiene los 5 modelos oficiales: ", paste(exp, collapse = ", "), "\n", sep = "")

# ============================
# Test por modelo (mean y flags)
# ============================
h <- 12
level <- 95

for (mid in expected) {
  out <- run_model_forecast(
    model_id = mid,
    y_train  = y,
    h        = h,
    level    = level,
    seed     = 123
  )

  stopifnot(is.list(out))
  stopifnot(!is.null(out$mean))
  stopifnot(length(out$mean) == h)

  cat(
    "OK model: ", mid,
    " | mean_len: ", length(out$mean),
    " | supports_intervals: ", out$supports_intervals,
    " | needs_features: ", out$needs_features,
    " | is_stochastic: ", out$is_stochastic,
    " | used_seed: ", ifelse(is.na(out$used_seed), "NA", as.character(out$used_seed)),
    "\n", sep = ""
  )
}

# ============================
# Reproducibilidad específica NNETAR
# ============================
o1 <- run_model_forecast("nnetar", y_train = y, h = h, level = level, seed = 123)$mean
o2 <- run_model_forecast("nnetar", y_train = y, h = h, level = level, seed = 123)$mean
stopifnot(isTRUE(all.equal(as.numeric(o1), as.numeric(o2), tolerance = 1e-8)))
cat("NNETAR reproducible: TRUE\n")

cat("✅ test_registry_modelos.R OK\n")