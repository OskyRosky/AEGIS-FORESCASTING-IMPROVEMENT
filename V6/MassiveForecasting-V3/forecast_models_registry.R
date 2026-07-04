###############################################################################
# forecast_models_registry.R
#
# Propósito:
#   Model Registry (Etapa 3): un catálogo único de modelos de forecasting
#   para que ni Shiny ni backtesting tengan if/else por modelo.
#
# Contrato estándar de salida (run_model_forecast):
#   list(
#     mean = numeric(h),
#     lower = numeric(h) o NULL,
#     upper = numeric(h) o NULL,
#     model = <objeto entrenado> (o forecast object en baselines),
#     supports_intervals = TRUE/FALSE,
#     needs_features = TRUE/FALSE,
#     is_stochastic = TRUE/FALSE,
#     used_seed = <seed> o NA
#   )
###############################################################################

# ----------------------------
# Utils
# ----------------------------
safe_num <- function(x) suppressWarnings(as.numeric(x))

assert_pkg <- function(pkg) {
  if (!requireNamespace(pkg, quietly = TRUE)) {
    stop(paste0("Falta paquete requerido: ", pkg))
  }
  invisible(TRUE)
}

# Extrae intervalos si existen (forecast::forecast o forecast objects)
extract_intervals <- function(fobj, level = 95) {
  lower <- NULL
  upper <- NULL

  if (!is.null(fobj$lower) && !is.null(fobj$upper)) {
    if (is.matrix(fobj$lower)) {
      coln <- colnames(fobj$lower)
      if (!is.null(coln)) {
        lev_chr <- as.character(level)
        if (lev_chr %in% coln) {
          lower <- safe_num(fobj$lower[, lev_chr])
          upper <- safe_num(fobj$upper[, lev_chr])
        } else {
          lower <- safe_num(fobj$lower[, 1])
          upper <- safe_num(fobj$upper[, 1])
        }
      } else {
        lower <- safe_num(fobj$lower[, 1])
        upper <- safe_num(fobj$upper[, 1])
      }
    } else {
      lower <- safe_num(fobj$lower)
      upper <- safe_num(fobj$upper)
    }
  }

  list(lower = lower, upper = upper)
}

# ----------------------------
# Registry (cache simple)
# ----------------------------
.registry_cache <- NULL

get_model_registry <- function() {
  assert_pkg("forecast")

  if (!is.null(.registry_cache)) return(.registry_cache)

  .registry_cache <<- list(

    # ------------------------
    # Baseline: Seasonal Naive
    # ------------------------
    seasonal_naive = list(
      model_id = "seasonal_naive",
      label_ui = "Seasonal Naive (Baseline)",
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = FALSE,
      seed_default = NA_integer_,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {
        f <- forecast::snaive(y_train, h = h, level = level)
        ints <- extract_intervals(f, level = level)

        list(
          mean = safe_num(f$mean),
          lower = ints$lower,
          upper = ints$upper,
          model = f,                 # baseline devuelve forecast object
          supports_intervals = TRUE
        )
      }
    ),

    # ------------------------
    # ARIMA fijo (el de siempre)
    # ------------------------
    arima = list(
      model_id = "arima",
      label_ui = "ARIMA (1,1,1)(0,1,1)[12]",
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = FALSE,
      seed_default = NA_integer_,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {
        m <- forecast::Arima(y_train, order = c(1, 1, 1), seasonal = c(0, 1, 1))
        f <- forecast::forecast(m, h = h, level = level)
        ints <- extract_intervals(f, level = level)

        list(
          mean = safe_num(f$mean),
          lower = ints$lower,
          upper = ints$upper,
          model = m,
          supports_intervals = TRUE
        )
      }
    ),

    # ------------------------
    # ETS
    # ------------------------
    ets = list(
      model_id = "ets",
      label_ui = "ETS",
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = FALSE,
      seed_default = NA_integer_,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {

        yv <- safe_num(y_train)
        if (any(!is.finite(yv))) stop("ETS: y_train contiene NA/Inf.")

        # Si hay valores <= 0, ETS multiplicativo no aplica -> forzamos additive.only
        additive_only <- any(yv <= 0)

        m <- forecast::ets(y_train, additive.only = additive_only)
        f <- forecast::forecast(m, h = h, level = level)
        ints <- extract_intervals(f, level = level)

        list(
          mean = safe_num(f$mean),
          lower = ints$lower,
          upper = ints$upper,
          model = m,
          supports_intervals = TRUE
        )
      }
    ),

    # ------------------------
    # AutoARIMA
    # ------------------------
    autoarima = list(
      model_id = "autoarima",
      label_ui = "AutoARIMA",
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = FALSE,
      seed_default = NA_integer_,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {
        m <- forecast::auto.arima(y_train)
        f <- forecast::forecast(m, h = h, level = level)
        ints <- extract_intervals(f, level = level)
        list(
          mean = safe_num(f$mean),
          lower = ints$lower,
          upper = ints$upper,
          model = m,
          supports_intervals = TRUE
        )
      }
    ),

    # ------------------------
    # NNETAR (estocástico)
    # ------------------------
    nnetar = list(
      model_id = "nnetar",
      label_ui = "NNETAR",
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = TRUE,
      seed_default = 123L,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {
        if (!is.null(seed) && is.finite(seed)) set.seed(as.integer(seed))
        m <- forecast::nnetar(y_train)
        f <- forecast::forecast(m, h = h, level = level)
        ints <- extract_intervals(f, level = level)
        list(
          mean = safe_num(f$mean),
          lower = ints$lower,
          upper = ints$upper,
          model = m,
          supports_intervals = TRUE
        )
      }
    ),

    # ------------------------
    # TSLM
    # ------------------------
    tslm = list(
      model_id = "tslm",
      label_ui = "Regresión (trend + season)",
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = FALSE,
      seed_default = NA_integer_,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {
        m <- forecast::tslm(y_train ~ trend + season)
        f <- forecast::forecast(m, h = h, level = level)
        ints <- extract_intervals(f, level = level)
        list(
          mean = safe_num(f$mean),
          lower = ints$lower,
          upper = ints$upper,
          model = m,
          supports_intervals = TRUE
        )
      }
    ),

    # ------------------------
    # Prophet (Meta)
    #
    # Notas de implementación:
    #   - Prophet no acepta ts: se reconstruyen fechas desde time(y_train).
    #   - Usa optimizer MAP (default), no MCMC -> determinista, is_stochastic=FALSE.
    #   - interval.width = level/100 mapea al nivel de confianza del proyecto.
    #   - Salida: yhat / yhat_lower / yhat_upper del data.frame de predicción.
    #   - Todo output de Stan se suprime (capture.output + suppressMessages).
    #   - Primer llamado puede ser lento (compilación Stan en caché de disco).
    # ------------------------
    prophet = list(
      model_id = "prophet",
      label_ui = "Prophet (Meta)",
      supports_intervals = TRUE,
      needs_features = FALSE,
      is_stochastic = FALSE,
      seed_default = NA_integer_,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {
        assert_pkg("prophet")

        # ---- 1) ts -> data.frame (ds, y) requerido por Prophet ----
        tt <- stats::time(y_train)
        yr <- floor(tt)
        mo <- pmax(1L, pmin(12L, as.integer(round((tt - yr) * 12) + 1L)))
        df_train <- data.frame(
          ds = as.Date(sprintf("%04d-%02d-01", as.integer(yr), mo)),
          y  = as.numeric(y_train),
          stringsAsFactors = FALSE
        )

        # ---- 2) Ajustar modelo (silenciar Stan + messages) ----
        interval_width <- level / 100

        invisible(utils::capture.output(
          suppressMessages(
            m <- prophet::prophet(df_train, interval.width = interval_width)
          )
        ))

        # ---- 3) Generar fechas futuras y predecir ----
        future_df <- prophet::make_future_dataframe(
          m, periods = h, freq = "month", include_history = FALSE
        )
        pred <- suppressMessages(prophet::predict(m, future_df))

        # ---- 4) Extraer resultados (h filas) ----
        list(
          mean  = safe_num(pred$yhat),
          lower = safe_num(pred$yhat_lower),
          upper = safe_num(pred$yhat_upper),
          model = m,
          supports_intervals = TRUE
        )
      }
    )

    ,

    # ------------------------
    # XGBoost
    #
    # Notas de implementación:
    #   - Features internas (no necesita xreg): lag_1, lag_12, lag_24, mes, trend.
    #   - Predicción recursiva (multi-step): cada pred se usa como lag del siguiente.
    #   - Lags faltantes al inicio de serie corta: imputados con último valor válido.
    #   - nthread=1 -> determinista dentro de workers paralelos (sin race conditions).
    #   - Sin intervalos nativos (supports_intervals=FALSE).
    #   - is_stochastic=TRUE: XGBoost tiene aleatoriedad interna; controlado con seed.
    # ------------------------
    xgboost = list(
      model_id = "xgboost",
      label_ui = "XGBoost (lag features)",
      supports_intervals = FALSE,
      needs_features = FALSE,
      is_stochastic = TRUE,
      seed_default = 123L,
      level_default = 95,
      fit_forecast_fn = function(y_train, h, level = 95, seed = NULL,
                                 xreg_train = NULL, xreg_future = NULL) {
        assert_pkg("xgboost")

        if (!is.null(seed) && is.finite(seed)) set.seed(as.integer(seed))

        y <- as.numeric(y_train)
        n <- length(y)

        # ---- 1) Reconstruir mes desde time(y_train) ----
        tt <- stats::time(y_train)
        yr <- floor(tt)
        mo <- pmax(1L, pmin(12L, as.integer(round((tt - yr) * 12) + 1L)))

        # ---- 2) Construir matriz de features de entrenamiento ----
        lag1  <- c(rep(NA_real_, 1L),  y[seq_len(n - 1L)])
        lag12 <- c(rep(NA_real_, 12L), y[seq_len(n - 12L)])
        lag24 <- c(rep(NA_real_, 24L), y[seq_len(n - 24L)])

        feat_df <- data.frame(
          lag_1  = lag1,
          lag_12 = lag12,
          lag_24 = lag24,
          mes    = as.numeric(mo),
          trend  = as.numeric(seq_len(n)),
          stringsAsFactors = FALSE
        )

        valid  <- stats::complete.cases(feat_df)
        X_train  <- as.matrix(feat_df[valid, , drop = FALSE])
        y_target <- y[valid]

        # ---- 3) Entrenar ----
        dtrain <- xgboost::xgb.DMatrix(data = X_train, label = y_target)

        m <- xgboost::xgb.train(
          params = list(
            objective = "reg:squarederror",
            eta       = 0.1,
            max_depth = 4,
            nthread   = 1L       # determinista en contexto paralelo
          ),
          data    = dtrain,
          nrounds = 100L,
          verbose = 0L
        )

        # ---- 4) Predicción recursiva multi-step ----
        y_ext  <- y
        mo_ext <- mo

        preds <- numeric(h)

        for (i in seq_len(h)) {
          last_mo    <- mo_ext[length(mo_ext)]
          next_mo    <- if (last_mo == 12L) 1L else last_mo + 1L
          next_trend <- as.numeric(n + i)

          ly  <- y_ext[length(y_ext)]
          l12 <- if (length(y_ext) >= 12L) y_ext[length(y_ext) - 11L] else ly
          l24 <- if (length(y_ext) >= 24L) y_ext[length(y_ext) - 23L] else ly

          x_new <- matrix(
            c(ly, l12, l24, as.numeric(next_mo), next_trend),
            nrow = 1L,
            dimnames = list(NULL, c("lag_1", "lag_12", "lag_24", "mes", "trend"))
          )

          pred_i    <- predict(m, xgboost::xgb.DMatrix(data = x_new))
          preds[i]  <- pred_i
          y_ext     <- c(y_ext, pred_i)
          mo_ext    <- c(mo_ext, next_mo)
        }

        list(
          mean  = safe_num(preds),
          lower = NULL,
          upper = NULL,
          model = m,
          supports_intervals = FALSE
        )
      }
    )

    # NOTA para nuevos modelos:
    #   Al agregar una entrada al registry en una sesión activa, invalidar
    #   el caché con: .registry_cache <<- NULL
    #   (el caché se reinicia automáticamente al re-sourcear el archivo)
  )

  .registry_cache
}

# ----------------------------
# Runner estándar (único punto de entrada)
# ----------------------------
run_model_forecast <- function(model_id,
                               y_train,
                               h,
                               level = 95,
                               seed = NULL,
                               xreg_train = NULL,
                               xreg_future = NULL) {
  reg <- get_model_registry()

  if (!(model_id %in% names(reg))) {
    stop(paste0("model_id no existe en registry: ", model_id))
  }

  spec <- reg[[model_id]]

  if (is.null(level) || !is.finite(level)) level <- spec$level_default
  used_seed <- NA_integer_

  if (isTRUE(spec$is_stochastic)) {
    if (is.null(seed) || !is.finite(seed)) seed <- spec$seed_default
    used_seed <- as.integer(seed)
  }

  res <- spec$fit_forecast_fn(
    y_train = y_train,
    h = h,
    level = level,
    seed = if (isTRUE(spec$is_stochastic)) used_seed else NULL,
    xreg_train = xreg_train,
    xreg_future = xreg_future
  )

  out <- list(
    mean = safe_num(res$mean),
    lower = if (!is.null(res$lower)) safe_num(res$lower) else NULL,
    upper = if (!is.null(res$upper)) safe_num(res$upper) else NULL,
    model = res$model,
    supports_intervals = isTRUE(spec$supports_intervals),
    needs_features = isTRUE(spec$needs_features),
    is_stochastic = isTRUE(spec$is_stochastic),
    used_seed = if (isTRUE(spec$is_stochastic)) used_seed else NA_integer_
  )

  if (length(out$mean) != h) {
    stop(paste0("El modelo ", model_id, " no devolvió mean con largo h=", h))
  }

  out
}

# ----------------------------
# Helpers públicos del registry
# ----------------------------
list_models <- function() {
  reg <- get_model_registry()
  data.frame(
    model_id = names(reg),
    label_ui = vapply(reg, function(x) x$label_ui, character(1)),
    supports_intervals = vapply(reg, function(x) isTRUE(x$supports_intervals), logical(1)),
    needs_features = vapply(reg, function(x) isTRUE(x$needs_features), logical(1)),
    is_stochastic = vapply(reg, function(x) isTRUE(x$is_stochastic), logical(1)),
    stringsAsFactors = FALSE
  )
}