###############################################################################
# precompute_bundles.R
#
# Propósito:
#   Pre-calcular bundles de pronóstico (pronos1) para h = 1..18 y guardarlos
#   como RDS. Shiny los consume directamente sin relanzar el engine.
#
# Uso:
#   cd "/Users/sultan/DataScience/MassiveForescastingIncome/V2"
#   Rscript Scripts_tablas_dashboard/precompute_bundles.R
#
#   # Forzar recálculo aunque los RDS ya existan:
#   FORCE_REBUILD=1 Rscript Scripts_tablas_dashboard/precompute_bundles.R
#
# Salida:
#   Scripts_tablas_dashboard/bundles/bundle_pronos1_h01.rds  ...  _h18.rds
#   Scripts_tablas_dashboard/bundles/manifest_pronos1.rds
#
# Parámetros fijos:
#   - model_ids     : todos los modelos del registry
#   - bt_initial=60, bt_step=3, bt_fixed_window=FALSE
#   - rank_by="wMAPE", lambda_stability=0.1
#   - level=95, seed=123
#
# Shiny (cambio mínimo posterior):
#   .bundle_pronos1 <- reactive({
#     readRDS(file.path(bundles_dir, sprintf("bundle_pronos1_h%02d.rds",
#                                            input$horizonte.1)))
#   })
#   input$modelos.1 solo filtra b$backtest$resumen (no relanza el engine).
###############################################################################

options(encoding = "utf-8")
options(scipen  = 999)
options(warn    = 0)

# ===========================================================================
# 1. Resolver rutas (mismo patrón que AI_SAF.R)
# ===========================================================================
args     <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)

if (length(file_arg) > 0) {
  this_file  <- sub("^--file=", "", file_arg[1])
  script_dir <- dirname(normalizePath(this_file, mustWork = TRUE))
} else {
  # Fallback: ejecutado desde RStudio o source()
  script_dir <- normalizePath(getwd(), mustWork = TRUE)
  # Si el wd es la raíz V2, apuntar a Scripts_tablas_dashboard
  if (dir.exists(file.path(script_dir, "Scripts_tablas_dashboard"))) {
    script_dir <- file.path(script_dir, "Scripts_tablas_dashboard")
  }
}

app_dir <- normalizePath(script_dir, mustWork = TRUE)
setwd(app_dir)

cat(sprintf("[precompute] app_dir : %s\n", app_dir))

# Helper para source con rutas absolutas
.src <- function(rel) file.path(app_dir, rel)

# ===========================================================================
# 2. Control de verbosidad y flags de entorno
# ===========================================================================
FORCE_REBUILD <- identical(Sys.getenv("FORCE_REBUILD", "0"), "1")
cat(sprintf("[precompute] FORCE_REBUILD = %s\n", FORCE_REBUILD))

# ===========================================================================
# 3. Source dependencias (mismo orden que AI_SAF.R)
# ===========================================================================
cat("[precompute] Cargando dependencias...\n")

suppressWarnings(suppressMessages({
  source(.src("Librerias.R"))
  source(.src("Parametros.R"))
  source(.src("forecast_models_registry.R"))
  source(.src("forecast_helpers.R"))
  source(.src("forecast_backtesting.R"))
  source(.src("forecast_engine/_10_series_builders.R"))
  source(.src("forecast_engine/_30_engine.R"))
  source(.src("forecast_engine/_20_forecast_runner.R"))
}))

cat("[precompute] Dependencias OK.\n")

# ===========================================================================
# 4. Cargar datos (tabla_2 vía pipeline canónico)
# ===========================================================================
cat("[precompute] Cargando tabla_2...\n")

source(.src("R/05_data_access.R"), local = TRUE)

ds <- get_data(
  prefer               = "rds",
  verbose              = FALSE,
  allow_excel_fallback = TRUE,
  save_fallback_rds    = FALSE
)

# Renombrar mes_cod -> mes.cod si hace falta (mismo mapping que importacion.R)
.rename_cols_if_present <- function(df, mapping) {
  if (is.null(df) || !is.data.frame(df)) return(df)
  nm <- names(df)
  for (from in names(mapping)) {
    to <- mapping[[from]]
    if (from %in% nm && !(to %in% nm)) nm[nm == from] <- to
  }
  names(df) <- nm
  df
}

.map_legacy <- c(
  "mes_cod"              = "mes.cod",
  "var_Ingresos"         = "var.Ingresos",
  "var_acum_12"          = "var.acum_12",
  "var_cum_ano_Ingresos" = "var.cum_ano_Ingresos",
  "Carga_tributaria"     = "Carga tributaria"
)

tabla_2 <- .rename_cols_if_present(ds$monthly_core$tabla_2, .map_legacy)

if (is.null(tabla_2) || !is.data.frame(tabla_2) || nrow(tabla_2) == 0) {
  stop("[precompute] tabla_2 no disponible o vacía. Ejecuta el pipeline primero.", call. = FALSE)
}

cat(sprintf("[precompute] tabla_2 cargada: %d filas, %d cols.\n",
            nrow(tabla_2), ncol(tabla_2)))

# ===========================================================================
# 5. Parámetros fijos del engine
# ===========================================================================
ALL_MODELS <- c("seasonal_naive", "ets", "autoarima", "nnetar", "tslm", "prophet", "xgboost")
H_RANGE    <- 1:18

PARAMS <- list(
  model_ids        = ALL_MODELS,
  level            = 95,
  seed             = 123,
  imputar          = TRUE,
  incluir_ultimo_mes = TRUE,
  millones         = 1e6,
  bt_initial       = 60,
  bt_step          = 3,
  bt_fixed_window  = FALSE,
  rank_by          = "wMAPE",
  lambda_stability = 0.1
)

cat(sprintf("[precompute] Modelos   : %s\n", paste(PARAMS$model_ids, collapse = ", ")))
cat(sprintf("[precompute] h range   : %d-%d\n", min(H_RANGE), max(H_RANGE)))
cat(sprintf("[precompute] bt_initial: %d  bt_step: %d\n", PARAMS$bt_initial, PARAMS$bt_step))

# ===========================================================================
# 6. Directorio de salida
# ===========================================================================
bundles_dir <- file.path(app_dir, "bundles")
if (!dir.exists(bundles_dir)) {
  dir.create(bundles_dir, recursive = TRUE)
  cat(sprintf("[precompute] Directorio creado: %s\n", bundles_dir))
}

# ===========================================================================
# 7. Loop h = 1..18
# ===========================================================================
cat(sprintf("\n[precompute] Iniciando loop h = %d..%d\n", min(H_RANGE), max(H_RANGE)))
cat(rep("-", 60), "\n", sep = "")

results <- vector("list", length(H_RANGE))

for (i in seq_along(H_RANGE)) {
  h        <- H_RANGE[i]
  h_label  <- sprintf("%02d", h)
  out_path <- file.path(bundles_dir, sprintf("bundle_pronos1_h%s.rds", h_label))

  # ---- Skip si ya existe y no se fuerza rebuild ----
  if (!isTRUE(FORCE_REBUILD) && file.exists(out_path)) {
    cat(sprintf("[precompute] h=%02d  SKIP (ya existe, FORCE_REBUILD=0)\n", h))
    results[[i]] <- data.frame(
      h           = h,
      status      = "skipped",
      path        = out_path,
      elapsed_sec = NA_real_,
      error_msg   = NA_character_,
      stringsAsFactors = FALSE
    )
    next
  }

  # ---- Calcular bundle ----
  cat(sprintf("[precompute] h=%02d  Calculando...\n", h))
  t0 <- proc.time()[["elapsed"]]

  bundle <- tryCatch({
    withCallingHandlers(
      run_total_bundle(
        tabla_2          = tabla_2,
        h                = as.integer(h),
        model_ids        = PARAMS$model_ids,
        level            = PARAMS$level,
        seed             = PARAMS$seed,
        imputar          = PARAMS$imputar,
        incluir_ultimo_mes = PARAMS$incluir_ultimo_mes,
        millones         = PARAMS$millones,
        bt_initial       = PARAMS$bt_initial,
        bt_step          = PARAMS$bt_step,
        bt_fixed_window  = PARAMS$bt_fixed_window,
        rank_by          = PARAMS$rank_by,
        lambda_stability = PARAMS$lambda_stability
      ),
      # Capturar warnings (ej. modelos omitidos) sin interrumpir
      warning = function(w) {
        cat(sprintf("[precompute] h=%02d  WARN: %s\n", h, conditionMessage(w)))
        invokeRestart("muffleWarning")
      }
    )
  }, error = function(e) {
    structure(list(message = conditionMessage(e)), class = "precompute_error")
  })

  elapsed <- round(proc.time()[["elapsed"]] - t0, 1)

  # ---- Guardar o registrar error ----
  if (inherits(bundle, "precompute_error")) {
    cat(sprintf("[precompute] h=%02d  ERROR (%.1fs): %s\n", h, elapsed, bundle$message))
    results[[i]] <- data.frame(
      h           = h,
      status      = "error",
      path        = NA_character_,
      elapsed_sec = elapsed,
      error_msg   = bundle$message,
      stringsAsFactors = FALSE
    )
  } else {
    saveRDS(bundle, file = out_path)
    cat(sprintf("[precompute] h=%02d  OK    (%.1fs) -> %s\n", h, elapsed,
                basename(out_path)))
    results[[i]] <- data.frame(
      h           = h,
      status      = "ok",
      path        = out_path,
      elapsed_sec = elapsed,
      error_msg   = NA_character_,
      stringsAsFactors = FALSE
    )
  }
}

# ===========================================================================
# 8. Guardar manifest
# ===========================================================================
results_df <- do.call(rbind, results)

manifest <- list(
  generated_at = Sys.time(),
  model_ids    = PARAMS$model_ids,
  params       = PARAMS,
  h_range      = H_RANGE,
  results      = results_df
)

manifest_path <- file.path(bundles_dir, "manifest_pronos1.rds")
saveRDS(manifest, file = manifest_path)

# ===========================================================================
# 9. Resumen final
# ===========================================================================
cat(rep("-", 60), "\n", sep = "")
cat("[precompute] Resumen:\n")

n_ok      <- sum(results_df$status == "ok")
n_skipped <- sum(results_df$status == "skipped")
n_error   <- sum(results_df$status == "error")

cat(sprintf("  OK      : %d\n", n_ok))
cat(sprintf("  Skipped : %d\n", n_skipped))
cat(sprintf("  Errores : %d\n", n_error))

if (n_ok > 0) {
  total_time <- sum(results_df$elapsed_sec[results_df$status == "ok"], na.rm = TRUE)
  cat(sprintf("  Tiempo total (solo nuevos calculos): %.1f seg\n", total_time))
}

if (n_error > 0) {
  cat("\n  Horizontes con error:\n")
  err_rows <- results_df[results_df$status == "error", ]
  for (j in seq_len(nrow(err_rows))) {
    cat(sprintf("    h=%02d: %s\n", err_rows$h[j], err_rows$error_msg[j]))
  }
}

cat(sprintf("\n[precompute] Manifest guardado en: %s\n", manifest_path))
cat("[precompute] Listo.\n")
