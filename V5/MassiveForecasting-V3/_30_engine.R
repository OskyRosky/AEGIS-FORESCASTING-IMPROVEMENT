###############################################################################
# forecast_engine/_30_engine.R
#
# Propósito (Fase 3):
#   Motor único (engine) que produce el bundle final para Shiny:
#     - Backtesting rolling-origin (evidencia)
#     - Selección defendible del winner (error + estabilidad)
#     - Forecast final del winner (mean / lower / upper)
#     - Quality card (resumen humano + métricas clave)
#
# Principio:
#   Shiny NO cocina -> Shiny solo consume este bundle.
#
# Dependencias (deben estar sourceadas antes):
#   - forecast_models_registry.R   -> run_model_forecast()
#   - forecast_backtesting.R       -> backtest_rolling_origin()
###############################################################################

# Utils locales (no asumimos nada)
.safe_num <- function(x) suppressWarnings(as.numeric(x))

# Normaliza bandas (lower/upper) a vector length = h
# Soporta: NULL, vector, ts, matrix/data.frame (toma 1ra columna)
.pick_band <- function(x, h, name = "band") {
  if (is.null(x)) return(NULL)

  if (inherits(x, "ts")) x <- as.numeric(x)

  if (is.matrix(x) || is.data.frame(x)) {
    v <- suppressWarnings(as.numeric(x[, 1]))
  } else {
    v <- suppressWarnings(as.numeric(x))
  }

  if (length(v) != h) {
    stop(
      paste0("run_engine(): '", name, "' tiene largo ", length(v),
             " pero se esperaba h=", h, "."),
      call. = FALSE
    )
  }
  v
}

# -----------------------------
# Score: error promedio + lambda * volatilidad
# rank_by: "wMAPE" o "sMAPE"
# -----------------------------
.calc_scores_and_rank <- function(resumen_bt,
                                  rank_by = c("wMAPE", "sMAPE"),
                                  lambda_stability = 0.1) {

  rank_by <- match.arg(rank_by)

  if (!is.data.frame(resumen_bt) || nrow(resumen_bt) == 0) {
    stop("_calc_scores_and_rank(): resumen_bt inválido/vacío.")
  }

  if (rank_by == "wMAPE") {
    mean_col <- "wMAPE_mean"
    sd_col   <- "wMAPE_sd"
  } else {
    mean_col <- "sMAPE_mean"
    sd_col   <- "sMAPE_sd"
  }

  if (!(mean_col %in% names(resumen_bt)) || !(sd_col %in% names(resumen_bt))) {
    stop("_calc_scores_and_rank(): columnas requeridas no existen en resumen: ",
         mean_col, " / ", sd_col)
  }

  df <- resumen_bt
  df$score <- .safe_num(df[[mean_col]]) + as.numeric(lambda_stability) * .safe_num(df[[sd_col]])

  df <- df[order(df$score), , drop = FALSE]
  df$rank <- seq_len(nrow(df))

  list(
    ranking = df,
    score_cols = list(mean_col = mean_col, sd_col = sd_col)
  )
}

# -----------------------------
# Quality Card (simple y útil)
# -----------------------------
.build_quality_card <- function(winner_row,
                                rank_by = c("wMAPE", "sMAPE"),
                                lambda_stability = 0.1,
                                label = NULL) {
  rank_by <- match.arg(rank_by)

  if (rank_by == "wMAPE") {
    mean_v <- .safe_num(winner_row[["wMAPE_mean"]])
    sd_v   <- .safe_num(winner_row[["wMAPE_sd"]])
    metric_name <- "wMAPE"
  } else {
    mean_v <- .safe_num(winner_row[["sMAPE_mean"]])
    sd_v   <- .safe_num(winner_row[["sMAPE_sd"]])
    metric_name <- "sMAPE"
  }

  score_v  <- .safe_num(winner_row[["score"]])
  n_splits <- .safe_num(winner_row[["n_splits"]])

  if (is.null(label) || !nzchar(label)) label <- "Modelo ganador"

  txt <- paste0(
    label, " | ",
    metric_name, " promedio=", round(mean_v, 2),
    " | estabilidad(sd)=", round(sd_v, 2),
    " | score=", round(score_v, 2),
    " (λ=", lambda_stability, ")",
    " | splits=", n_splits
  )

  list(
    text = txt,
    metric = metric_name,
    mean = mean_v,
    sd = sd_v,
    score = score_v,
    n_splits = n_splits,
    lambda = lambda_stability
  )
}

# -----------------------------
# Engine principal
# -----------------------------
run_engine <- function(y_ts,
                       df_std = NULL,
                       model_ids,
                       h,
                       level = 95,
                       seed = 123,
                       bt_initial = 60,
                       bt_step = 1,
                       bt_fixed_window = FALSE,
                       rank_by = c("wMAPE", "sMAPE"),
                       lambda_stability = 0.1) {

  # ---------
  # Validaciones
  # ---------
  if (!exists("run_model_forecast")) {
    stop("run_engine(): No existe run_model_forecast(). Sourcea forecast_models_registry.R antes.")
  }
  if (!exists("backtest_rolling_origin")) {
    stop("run_engine(): No existe backtest_rolling_origin(). Sourcea forecast_backtesting.R antes.")
  }

  if (missing(y_ts) || is.null(y_ts) || !is.ts(y_ts)) stop("run_engine(): y_ts debe ser ts.")
  if (stats::frequency(y_ts) != 12) stop("run_engine(): y_ts debe ser mensual (frequency=12).")

  if (missing(h) || is.null(h) || !is.numeric(h) || length(h) != 1 || is.na(h) || h < 1) {
    stop("run_engine(): h inválido.")
  }
  h <- as.integer(h)

  if (missing(model_ids) || is.null(model_ids) || length(model_ids) == 0) {
    stop("run_engine(): model_ids vacío.")
  }
  model_ids <- as.character(model_ids)

  rank_by <- match.arg(rank_by)

  # ---------
  # 1) Backtesting (evidencia)
  #    OJO: forecast_backtesting.R usa rank_metric (no rank_by)
  # ---------
  bt <- backtest_rolling_origin(
    y = y_ts,
    model_ids = model_ids,
    h = h,
    initial = as.integer(bt_initial),
    step = as.integer(bt_step),
    fixed_window = isTRUE(bt_fixed_window),
    rank_metric = rank_by,
    lambda = lambda_stability,
    seed = as.integer(seed),
    level = level
  )

  # ---------
  # 1b) Avisar modelos omitidos
  # ---------
  skipped <- setdiff(model_ids, unique(bt$resumen$model_id))
  if (length(skipped) > 0) {
    warning(
      "run_engine(): ", length(skipped), " modelo(s) omitido(s) del ranking ",
      "(paquete no instalado o fallo en todos los cortes): ",
      paste(skipped, collapse = ", "),
      call. = FALSE
    )
  }

  # ---------
  # 2) Ranking + winner (score)
  # ---------
  scored <- .calc_scores_and_rank(
    resumen_bt = bt$resumen,
    rank_by = rank_by,
    lambda_stability = lambda_stability
  )

  ranking_tbl     <- scored$ranking
  winner_row      <- ranking_tbl[1, , drop = FALSE]
  winner_model_id <- as.character(winner_row$model_id)

  # Label UI del winner (si existe)
  label_ui <- try({
    reg <- get_model_registry()
    if (!is.null(reg[[winner_model_id]]$label_ui)) reg[[winner_model_id]]$label_ui else winner_model_id
  }, silent = TRUE)
  if (inherits(label_ui, "try-error")) label_ui <- winner_model_id

  # ---------
  # 3) Forecast final (solo winner)
  # ---------
  fc <- run_model_forecast(
    model_id = winner_model_id,
    y_train = y_ts,
    h = h,
    level = level,
    seed = seed
  )

  mean_v <- .safe_num(fc$mean)
  if (length(mean_v) != h) {
    stop(
      paste0("run_engine(): fc$mean tiene largo ", length(mean_v),
             " pero se esperaba h=", h, "."),
      call. = FALSE
    )
  }

  # Normalización robusta: lower/upper pueden venir como vector o matriz
  lower_v <- .pick_band(fc$lower, h, "lower")
  upper_v <- .pick_band(fc$upper, h, "upper")

  forecast_final <- list(
    mean  = mean_v,
    lower = lower_v,
    upper = upper_v
  )

  # ---------
  # 4) Quality card
  # ---------
  qc <- .build_quality_card(
    winner_row = as.list(winner_row),
    rank_by = rank_by,
    lambda_stability = lambda_stability,
    label = as.character(label_ui)
  )

  # ---------
  # 5) Bundle final (contrato Fase 3)
  # ---------
  bundle <- list(
    y = y_ts,
    df_std = df_std,
    backtest = list(
      meta = bt$meta,
      resumen = bt$resumen,
      detalle = bt$detalle
    ),
    winner = list(
      model_id = winner_model_id,
      label = as.character(label_ui),
      rank_by = rank_by,
      score = .safe_num(winner_row$score),
      metrics = list(
        wMAPE_mean = .safe_num(winner_row$wMAPE_mean),
        wMAPE_sd   = .safe_num(winner_row$wMAPE_sd),
        sMAPE_mean = .safe_num(winner_row$sMAPE_mean),
        sMAPE_sd   = .safe_num(winner_row$sMAPE_sd),
        RMSE_mean  = .safe_num(winner_row$RMSE_mean),
        RMSE_sd    = .safe_num(winner_row$RMSE_sd),
        MAE_mean   = .safe_num(winner_row$MAE_mean),
        MAE_sd     = .safe_num(winner_row$MAE_sd),
        MAPE_mean  = .safe_num(winner_row$MAPE_mean),
        MAPE_sd    = .safe_num(winner_row$MAPE_sd),
        n_splits   = .safe_num(winner_row$n_splits)
      )
    ),
    ranking_table  = ranking_tbl,
    forecast_final = forecast_final,
    quality_card   = qc
  )

  bundle
}