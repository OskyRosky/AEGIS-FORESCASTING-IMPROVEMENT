###############################################################################
# forecast_engine/_20_forecast_runner.R
#
# Propósito (Fase 3):
#   Runner liviano por componente.
#   - Construye la serie estándar (builders)
#   - Llama al engine (run_engine) que hace:
#       backtesting -> winner -> forecast_final -> quality_card
#   - Devuelve el bundle FINAL (contrato Fase 3)
#
# Dependencias esperadas (sourcear ANTES de USARLO):
#   - forecast_engine/_10_series_builders.R  -> build_series_total(), etc.
#   - forecast_engine/_30_engine.R           -> run_engine()
###############################################################################

# =========================
# TOTAL
# =========================
run_total_bundle <- function(tabla_2,
                             h,
                             model_ids = c("seasonal_naive", "ets", "autoarima", "nnetar", "tslm",
                                           "prophet", "xgboost"),
                             level = 95,
                             seed = 123,
                             imputar = TRUE,
                             incluir_ultimo_mes = TRUE,
                             millones = 1e6,
                             bt_initial = 60,
                             bt_step = 1,
                             bt_fixed_window = FALSE,
                             rank_by = c("wMAPE", "sMAPE"),
                             lambda_stability = 0.1) {

  rank_by <- match.arg(rank_by)

  # ---------
  # Validar dependencias (builders + engine)
  # ---------
  if (!exists("build_series_total")) {
    stop("run_total_bundle(): No existe build_series_total(). Sourcea forecast_engine/_10_series_builders.R antes.")
  }
  if (!exists("run_engine")) {
    stop("run_total_bundle(): No existe run_engine(). Sourcea forecast_engine/_30_engine.R antes.")
  }

  # ---------
  # 1) Serie canónica (df_std en colones + y_ts_mill en millones)
  # ---------
  series_obj <- build_series_total(
    tabla_2 = tabla_2,
    imputar = imputar,
    incluir_ultimo_mes = incluir_ultimo_mes,
    millones = millones
  )

  # ---------
  # 2) Engine (bundle final)
  # ---------
  bundle <- run_engine(
    y_ts = series_obj$y_ts_mill,
    df_std = series_obj$df_std,
    model_ids = model_ids,
    h = as.integer(h),
    level = level,
    seed = seed,
    bt_initial = as.integer(bt_initial),
    bt_step = as.integer(bt_step),
    bt_fixed_window = isTRUE(bt_fixed_window),
    rank_by = rank_by,
    lambda_stability = lambda_stability
  )

  bundle
}

# =========================
# TAX / ADVANCED
# (los habilitamos cuando implementemos sus builders)
# =========================

# run_tax_bundle <- function(...) { ... }
# run_advanced_bundle <- function(...) { ... }