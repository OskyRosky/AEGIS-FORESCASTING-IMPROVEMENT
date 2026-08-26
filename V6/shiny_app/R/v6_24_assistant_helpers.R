# TESSERACT v2 | v6_24_assistant_helpers.R
# V6.24-P9G | Evidence-aware assistant for the V6.24 MVP.
#
# CONTRACT
#   This assistant answers ONLY from the governed artifacts and the current
#   Shiny selection. It does not call any LLM, it does not reach any network,
#   it does not recompute a metric, it does not rank, it does not forecast.
#   Every number it prints was read from an artifact column.
#
#   WHY IT IS NOT THE EXISTING ASSISTANT
#   R/llm_explain.R serves precomputed mock responses indexed by PAGE ID
#   (llm_explain_get(page_id)) from outputs/v4_4_mock_provider. There is no
#   parameter through which a selected series could enter, and its composer
#   .comp_answer(resp, question) narrates that fixed response object. Mounting
#   it under V6.24 would produce a panel that LOOKS like it explains the
#   selected series while actually reciting page-level text. That is the exact
#   failure P9B warned about, so V6.24 gets its own evidence builder and its
#   own deterministic composer. The UI pattern and CSS are reused; the engine
#   is not.
#
#   GOVERNANCE INVARIANTS
#   - champion language is gated on champion_visible, never on a model name
#   - the forecast horizon is read from the artifact, never asserted
#   - a question without supporting evidence gets an explicit refusal
#   - caveats are surfaced, never softened or dropped

V6_24_ASSISTANT_NO_EVIDENCE <-
  "I do not have evidence for that in the current V6.24 artifacts."

V6_24_ASSISTANT_ENGINE <- "V6_24_LOCAL_DETERMINISTIC_EVIDENCE_V1"

# ------------------------------------------------------------------ utilities

.v24a_chr <- function(x, default = "") {
  if (is.null(x) || !length(x)) return(default)
  v <- as.character(x[[1]])
  if (is.na(v) || !nzchar(v)) default else v
}

.v24a_num <- function(x) {
  if (is.null(x) || !length(x)) return(NA_real_)
  suppressWarnings(as.numeric(x[[1]]))
}

.v24a_int <- function(x) {
  v <- .v24a_num(x)
  if (is.na(v)) NA_integer_ else as.integer(v)
}

.v24a_is_true <- function(x) identical(toupper(.v24a_chr(x)), "TRUE")

#' Format a number for prose. Never rounds a value to zero that is not zero.
.v24a_fmt <- function(x, digits = 4) {
  if (is.null(x) || !length(x) || is.na(x)) return("not available")
  v <- suppressWarnings(as.numeric(x))
  if (is.na(v)) return("not available")
  if (v != 0 && abs(v) < 10^(-digits)) return(format(v, scientific = TRUE, digits = 3))
  format(round(v, digits), big.mark = ",", trim = TRUE, scientific = FALSE)
}

.v24a_date <- function(x) {
  if (is.null(x) || !length(x)) return("not available")
  d <- try(v6_24_as_date(x), silent = TRUE)
  if (inherits(d, "try-error") || all(is.na(d))) return("not available")
  format(d[[1]], "%Y-%m-%d")
}

# ------------------------------------------------------- evidence context A-F

#' Build the evidence context for the current selection.
#'
#' Every field is read from a governed artifact. Nothing is defaulted to zero:
#' a value the artifacts do not carry is reported as NA and rendered as
#' "not available", so the assistant can say so instead of guessing.
#'
#' @param series_id selected operational series
#' @param cfg applied backtest configuration from P9D, or NULL if Analyze
#'   Backtest has not been clicked
#' @param fc_model model currently chosen on the Forecast page, or NULL
v6_24_evidence <- function(series_id, cfg = NULL, fc_model = NULL) {
  if (is.null(series_id) || !nzchar(series_id)) return(NULL)
  r <- v6_24_nav_row(series_id)
  if (is.null(r)) return(NULL)

  # ---- A. selection ------------------------------------------------------
  sel <- list(
    series_id = series_id,
    route_display_label = .v24a_chr(r$route_display_label),
    route_path = .v24a_chr(r$route_path),
    metric = .v24a_chr(r$metric),
    db_type = .v24a_chr(r$db_type),
    scenario = .v24a_chr(r$scenario),
    segment = .v24a_chr(r$segment),
    granularity = .v24a_chr(r$granularity),
    key = .v24a_chr(r$key),
    key_axis_status = .v24a_chr(r$key_axis_status),
    # v6_24_final_axis_label() takes the contract ROWS and returns
    # list(label=, basis=). Passing a series_id would silently fall through to
    # its "no rows" default and print the wrong axis name.
    final_axis_label = tryCatch(v6_24_final_axis_label(r)$label,
                                error = function(e) "Operational Key"),
    product_status = .v24a_chr(r$product_status),
    product_ready = .v24a_is_true(r$product_ready),
    viewer_visible = .v24a_is_true(r$viewer_visible),
    forecast_visible = .v24a_is_true(r$forecast_visible),
    ranking_visible = .v24a_is_true(r$ranking_visible),
    champion_visible = .v24a_is_true(r$champion_visible))

  # ---- B. signal ---------------------------------------------------------
  sq <- v6_24_tbl("signal_quality")
  srow <- if (!is.null(sq) && nrow(sq))
    sq[as.character(sq$series_id) == series_id, , drop = FALSE] else NULL
  has_s <- !is.null(srow) && nrow(srow) > 0
  sig <- list(
    signal_quality_status = .v24a_chr(r$signal_quality_status),
    no_signal = .v24a_is_true(r$no_signal_flag),
    trailing_zero = .v24a_is_true(r$trailing_zero_latest_actual_flag),
    low_confidence_window = .v24a_is_true(r$low_confidence_backtest_window_flag),
    observation_count = if (has_s) .v24a_int(srow$n_actual_rows) else NA_integer_,
    nonzero_count = if (has_s) .v24a_int(srow$nonzero_actual_count) else NA_integer_,
    zero_count = if (has_s) .v24a_int(srow$zero_actual_count) else NA_integer_,
    actual_min_date = if (has_s) .v24a_date(srow$min_actual_date) else "not available",
    actual_max_date = if (has_s) .v24a_date(srow$max_actual_date) else "not available",
    latest_actual_value = if (has_s) .v24a_num(srow$latest_actual_value) else NA_real_,
    latest_actual_zero = if (has_s) .v24a_is_true(srow$latest_actual_zero) else FALSE)

  # ---- C. backtest -------------------------------------------------------
  applied <- !is.null(cfg)
  bt <- list(applied = applied, horizon = NA_integer_, models = character(0),
             rows = NA_integer_, date_min = "not available",
             date_max = "not available", ranking = NULL)
  if (applied) {
    b <- v6_24_backtest_rows(cfg$series, cfg$models, cfg$horizon)
    bt$horizon <- as.integer(cfg$horizon)
    bt$models <- as.character(cfg$models)
    bt$rows <- nrow(b)
    if (nrow(b)) {
      d <- v6_24_as_date(b$target_date)
      bt$date_min <- format(min(d, na.rm = TRUE), "%Y-%m-%d")
      bt$date_max <- format(max(d, na.rm = TRUE), "%Y-%m-%d")
    }
  }

  # ---- ranking / accuracy (read, never recomputed) -----------------------
  rk <- v6_24_tbl("model_rankings")
  rk <- rk[as.character(rk$series_id) == series_id, , drop = FALSE]
  ac <- v6_24_tbl("accuracy_metrics")
  ac <- ac[as.character(ac$series_id) == series_id, , drop = FALSE]
  rank_tbl <- NULL
  if (nrow(rk)) {
    j <- merge(rk, ac[, c("model_name", "mae", "rmse", "wape", "smape",
                          "wape_status")],
               by = "model_name", all.x = TRUE)
    j <- j[order(as.integer(j$rank_within_series)), , drop = FALSE]
    rank_tbl <- j
  }
  bt$ranking <- rank_tbl

  champ <- list(
    model = .v24a_chr(r$champion_model_name),
    visible = sel$champion_visible,
    validity = .v24a_chr(r$champion_validity),
    reason = .v24a_chr(r$champion_reason),
    rank_metric = .v24a_chr(r$champion_rank_metric),
    rank_value = .v24a_num(r$champion_rank_value),
    median_wape = .v24a_num(r$median_wape),
    median_wape_status = .v24a_chr(r$median_wape_status),
    median_mae = .v24a_num(r$median_mae),
    median_rmse = .v24a_num(r$median_rmse),
    ranking_policy = .v24a_chr(r$ranking_policy_version),
    negative_backtest_rows = .v24a_int(r$negative_prediction_count),
    extreme_backtest_rows = .v24a_int(r$extreme_prediction_count))

  # ---- D. forecast -------------------------------------------------------
  fo <- v6_24_tbl("forecast_outputs")
  fo <- fo[as.character(fo$series_id) == series_id, , drop = FALSE]
  models_avail <- sort(unique(as.character(fo$model_name)))
  chosen <- if (!is.null(fc_model) && nzchar(fc_model)) fc_model else
    if (sel$champion_visible && champ$model %in% models_avail) champ$model else
      if (V6_24_REFERENCE_MODEL %in% models_avail) V6_24_REFERENCE_MODEL else
        if (length(models_avail)) models_avail[[1]] else ""
  frow <- fo[as.character(fo$model_name) == chosen, , drop = FALSE]
  if (nrow(frow)) frow <- frow[order(as.integer(frow$forecast_step)), , drop = FALSE]
  fc <- list(
    forecast_type = .v24a_chr(r$forecast_type),
    steps_contract = .v24a_int(r$forecast_steps),
    steps_drawn = nrow(frow),
    horizon_label = .v24a_chr(r$forecast_horizon_label),
    model = chosen,
    models_available = models_avail,
    model_is_champion = sel$champion_visible && identical(chosen, champ$model),
    start_date = .v24a_chr(r$forecast_start_date),
    end_date = .v24a_chr(r$forecast_end_date),
    min = if (nrow(frow)) min(frow$predicted_value, na.rm = TRUE) else NA_real_,
    max = if (nrow(frow)) max(frow$predicted_value, na.rm = TRUE) else NA_real_,
    last = if (nrow(frow)) frow$predicted_value[[nrow(frow)]] else NA_real_,
    negative_rows = .v24a_int(r$negative_forecast_count),
    extreme_rows = .v24a_int(r$extreme_forecast_count))

  # ---- E. caveats --------------------------------------------------------
  codes <- tryCatch(v6_24_badges(.v24a_chr(r$caveat_badge)),
                    error = function(e) character(0))
  cav <- list(
    badge = .v24a_chr(r$caveat_badge),
    message = .v24a_chr(r$caveat_message),
    codes = codes,
    severities = vapply(codes, function(c)
      tryCatch(v6_24_caveat_severity(c), error = function(e) "info"),
      character(1), USE.NAMES = FALSE),
    blocking = FALSE)  # P7 recorded every MVP caveat as non-blocking

  # ---- F. taxonomy -------------------------------------------------------
  tx <- v6_24_tbl("tax_counts")
  mrow <- tx[as.character(tx$count_scope) == "BY_METRIC" &
               as.character(tx$filter_value) == sel$metric, , drop = FALSE]
  taxo <- if (nrow(mrow)) list(
    metric = sel$metric,
    series = .v24a_int(mrow$operational_series_count),
    viewer = .v24a_int(mrow$viewer_visible_count),
    forecast = .v24a_int(mrow$forecast_visible_count),
    champion = .v24a_int(mrow$champion_visible_count),
    no_signal = .v24a_int(mrow$no_signal_count),
    available = .v24a_int(mrow$available_count),
    with_caveat = .v24a_int(mrow$available_with_caveat_count),
    median_wape = .v24a_num(mrow$median_wape)) else NULL

  list(selection = sel, signal = sig, backtest = bt, champion = champ,
       forecast = fc, caveats = cav, taxonomy = taxo,
       engine = V6_24_ASSISTANT_ENGINE)
}

# ------------------------------------------------------------ intent routing

#' Map a free-text question to an evidence category.
#'
#' Deliberately conservative: anything that does not match a category the
#' artifacts can answer falls through to "unsupported", which triggers the
#' explicit refusal rather than a plausible-sounding guess.
v6_24_assistant_intent <- function(question) {
  q <- tolower(trimws(if (is.null(question)) "" else question))
  if (!nzchar(q)) return("summary")

  # ORDER MATTERS. Supported phrasings that LOOK like refusals are matched
  # first. "What should I pay attention to?" and "What should I tell a
  # stakeholder?" both contain "should i", and "Why is this only a 30-step
  # forecast?" begins with "why is" - all three are answerable from the
  # artifacts, and all three are required quick prompts, so they must not fall
  # into the unsupported guards below.
  if (grepl("attention|watch|focus|look at|notice|careful|aware", q))
    return("attention")
  if (grepl("stakeholder|explain to|tell (a|my|the)|non.?technical|exec", q))
    return("stakeholder")
  if (grepl(paste0("4.?year|1,?440|four year|longer horizon|extend the ",
                   "forecast|30.?step|how far ahead|how far out"), q))
    return("horizon")

  # Causal questions about the DATA are refused: the artifacts carry no driver,
  # no event and no root cause. Scoped to movement/attribution wording so it
  # cannot swallow a methodological "why is this only ..." question.
  if (grepl(paste0("root cause|because of|business event|promotion|marketing|",
                   "outage|incident|\\bcaused\\b|\\bdriver\\b|",
                   "why did .*(increase|decrease|drop|rise|fall|spike|change)|",
                   "why is .*(up|down|higher|lower|increasing|decreasing)|",
                   "what caused|demand increase"), q))
    return("unsupported_cause")

  # Action / approval questions are refused: no capacity, cost or sign-off
  # field exists. Scoped to an actual verb so "should I pay attention" cannot
  # match.
  if (grepl(paste0("should (i|we) (buy|invest|provision|purchase|order|",
                   "decommission|scale|approve|deploy|migrate|act)|",
                   "recommend an action|capacity plan|production ready|",
                   "go live|sign off|business decision"), q))
    return("unsupported_action")

  if (grepl("horizon|how long", q)) return("horizon")
  if (grepl("champion|winner|winning|\\bbest\\b|which model|recommended model", q))
    return("champion")
  if (grepl("caveat|warning|flag|badge|limitation", q)) return("caveats")
  if (grepl("negative|extreme|outlier", q)) return("flags")
  if (grepl("risk|danger|concern|safe|trust|reliable|interpret", q)) return("risk")
  if (grepl("forecast|predict|future|ahead", q)) return("forecast")
  if (grepl("backtest|estimate|history window", q)) return("backtest")
  if (grepl("rank|compare|model|accuracy|wape|smape|rmse|\\bmae\\b", q))
    return("ranking")
  if (grepl("signal|zero|empty|no data", q)) return("signal")
  if (grepl("coverage|taxonomy|how many series|cohort", q)) return("coverage")
  if (grepl("summar|takeaway|overview|what is this|describe", q)) return("summary")
  "unsupported"
}

# --------------------------------------------------------------- composition

.v24a_champion_sentence <- function(e) {
  ch <- e$champion
  if (!isTRUE(ch$visible)) {
    return(paste0(
      "No model can be presented as a winner for this series. ",
      "champion_visible is FALSE (", ch$validity, "), so the top-ranked name ",
      "is a technical tie-break, not a recommendation. ",
      if (nzchar(ch$reason)) paste0("Recorded reason: ", ch$reason, ".") else ""))
  }
  paste0(
    "The champion is ", ch$model, ", ranked by ", ch$rank_metric,
    " = ", .v24a_fmt(ch$rank_value, 6), " under policy ", ch$ranking_policy,
    ". Champion validity is ", ch$validity, ".")
}

.v24a_caveat_lines <- function(e) {
  cav <- e$caveats
  if (!length(cav$codes)) return("No caveat code is recorded for this series.")
  paste0(
    vapply(seq_along(cav$codes), function(i) {
      paste0(cav$codes[[i]], " (", cav$severities[[i]], ")")
    }, character(1)),
    collapse = "; ")
}

#' Compose an evidence-grounded answer.
#'
#' Returns a list the UI renders: a lead sentence, body paragraphs, optional
#' bullets, the caveat line, the artifacts consulted, and a `bounded` flag that
#' marks a refusal. No branch may invent a value; each one prints fields that
#' v6_24_evidence() read from an artifact.
v6_24_assistant_answer <- function(e, question = "", intent = NULL) {
  if (is.null(e)) {
    return(list(
      lead = "No series is selected yet.",
      body = paste("Complete the selection path in the Selection card and I",
                   "will explain the governed evidence for that series."),
      bullets = character(0), caveats = "", used = character(0),
      bounded = TRUE, intent = "no_selection"))
  }
  if (is.null(intent)) intent <- v6_24_assistant_intent(question)
  sel <- e$selection; sig <- e$signal; bt <- e$backtest
  ch <- e$champion; fc <- e$forecast

  used <- character(0)
  bullets <- character(0)
  lead <- ""
  body <- ""

  if (intent %in% c("unsupported", "unsupported_cause", "unsupported_action")) {
    lead <- V6_24_ASSISTANT_NO_EVIDENCE
    body <- switch(
      intent,
      unsupported_cause = paste(
        "The V6.24 artifacts record observed values, backtest estimates,",
        "accuracy, rankings, forecasts and caveats. They carry no drivers, no",
        "business events and no causal attribution, so I cannot say why a",
        "series moved. I can describe what the evidence shows instead."),
      unsupported_action = paste(
        "The artifacts do not carry capacity, cost or approval information, so",
        "I cannot recommend an action or declare production readiness. I can",
        "tell you what the governed accuracy, ranking and caveat fields say."),
      paste("I can only answer from the governed V6.24 artifacts for the",
            "selected series: selection, signal quality, backtest, ranking,",
            "champion, forecast, caveats and taxonomy counts."))
    return(list(lead = lead, body = body, bullets = character(0),
                caveats = .v24a_caveat_lines(e), used = "none",
                bounded = TRUE, intent = intent))
  }

  if (intent == "summary") {
    used <- c("navigation_contract", "series_signal_quality", "actuals_normalized")
    lead <- paste0(sel$route_display_label, " \u2014 ", sel$product_status, ".")
    body <- paste0(
      "This is series ", sel$series_id, ", a ", sel$metric,
      " series at ", sel$granularity, " granularity, reached through ",
      sel$route_path, ". Its ", sel$final_axis_label, " is ", sel$key,
      " (", sel$key_axis_status, "). Signal quality is ",
      sig$signal_quality_status, ", with ",
      if (is.na(sig$observation_count)) "an unrecorded number of" else
        format(sig$observation_count, big.mark = ","),
      " observed points from ", sig$actual_min_date, " to ",
      sig$actual_max_date, ".")
    bullets <- c(
      paste0("Latest observed actual: ", .v24a_fmt(sig$latest_actual_value)),
      paste0("Visible in Viewer / Forecast / Ranking: ",
             sel$viewer_visible, " / ", sel$forecast_visible, " / ",
             sel$ranking_visible),
      .v24a_champion_sentence(e))
    if (isTRUE(sig$no_signal)) {
      bullets <- c(bullets, paste(
        "Every observed actual is zero, so accuracy and ranking for this",
        "series are technical artefacts rather than product signal."))
    }
  } else if (intent == "champion") {
    used <- c("navigation_contract", "model_rankings", "accuracy_metrics")
    lead <- .v24a_champion_sentence(e)
    if (isTRUE(ch$visible)) {
      body <- paste0(
        "Ranking is read from model_rankings under ", ch$ranking_policy,
        "; Shiny does not rank anything. Median WAPE for this series is ",
        if (identical(ch$median_wape_status, "COMPUTED"))
          .v24a_fmt(ch$median_wape, 6) else
            paste0("not computable (", ch$median_wape_status, ")"),
        " and median MAE is ", .v24a_fmt(ch$median_mae, 6),
        ". Medians are used deliberately: the mean of WAPE across this cohort",
        " is distorted by near-zero denominators.")
      if (!is.null(bt$ranking) && nrow(bt$ranking) >= 3) {
        top <- utils::head(bt$ranking, 3)
        bullets <- vapply(seq_len(nrow(top)), function(i) paste0(
          "Rank ", top$rank_within_series[i], ": ", top$model_name[i],
          " (", top$primary_rank_metric[i], " = ",
          .v24a_fmt(top$primary_rank_value[i], 6), ")"), character(1))
      }
    } else {
      body <- paste(
        "I will not name a winner for this series. The ranking still exists",
        "and is shown in the table for technical inspection, but presenting it",
        "as a recommendation would be misleading when there is no signal to",
        "discriminate between models.")
    }
  } else if (intent == "backtest") {
    used <- c("model_backtests_15_models", "navigation_contract")
    if (!isTRUE(bt$applied)) {
      lead <- "No backtest has been applied yet."
      body <- paste("Choose a horizon and models in the Backtest Configuration",
                    "card and click Analyze Backtest. I will then describe the",
                    "rows that were actually drawn.")
    } else {
      lead <- paste0("The applied backtest compares ", length(bt$models),
                     " model", if (length(bt$models) == 1) "" else "s",
                     " at horizon ", bt$horizon, " days.")
      body <- paste0(
        "That configuration selects ", format(bt$rows, big.mark = ","),
        " prepared rows from model_backtests_15_models, spanning ",
        bt$date_min, " to ", bt$date_max,
        ". Horizon filtering uses equality on horizon_steps, so every point",
        " compares models at the same forecast distance rather than mixing",
        " step 1 with step 30. Nothing here is recomputed.")
      bullets <- c(paste0("Models: ", paste(bt$models, collapse = ", ")),
                   paste0("Negative backtest predictions recorded: ",
                          ch$negative_backtest_rows),
                   paste0("Extreme backtest predictions recorded: ",
                          ch$extreme_backtest_rows))
    }
  } else if (intent == "ranking") {
    used <- c("model_rankings", "accuracy_metrics")
    lead <- paste0("Ranking for this series is read from model_rankings under ",
                   ch$ranking_policy, ".")
    if (!is.null(bt$ranking) && nrow(bt$ranking)) {
      top <- utils::head(bt$ranking, 5)
      body <- paste0(
        "All ", nrow(bt$ranking), " governed models are ranked for this series.",
        " The primary metric is ", .v24a_chr(top$primary_rank_metric[1]),
        ". WAPE is reported only where wape_status is COMPUTED; where it is",
        " not, the table says so rather than printing a substitute number.")
      bullets <- vapply(seq_len(nrow(top)), function(i) paste0(
        "Rank ", top$rank_within_series[i], ": ", top$model_name[i],
        " \u2014 MAE ", .v24a_fmt(top$mae[i], 6), ", RMSE ",
        .v24a_fmt(top$rmse[i], 6)), character(1))
      if (!isTRUE(ch$visible)) {
        bullets <- c(bullets, paste(
          "This order is a technical tie-break only: champion_visible is",
          "FALSE for this series."))
      }
    } else {
      body <- "No ranking rows are present for this series."
    }
  } else if (intent == "forecast") {
    used <- c("forecast_outputs", "navigation_contract")
    lead <- paste0("The governed forecast is ", fc$steps_contract,
                   " daily steps, ", fc$start_date, " to ", fc$end_date, ".")
    body <- paste0(
      "It is produced by ", fc$model,
      if (isTRUE(fc$model_is_champion)) ", the champion for this series"
      else if (isTRUE(sel$champion_visible))
        paste0(" (the champion is ", ch$model, ")")
      else ", shown as a technical reference rather than a winner",
      ". Values are read verbatim from forecast_outputs and are never clipped:",
      " the forecast ranges from ", .v24a_fmt(fc$min), " to ",
      .v24a_fmt(fc$max), ", ending at ", .v24a_fmt(fc$last), ".")
    bullets <- c(
      paste0("Forecast type: ", fc$forecast_type),
      paste0("Negative forecast rows: ", fc$negative_rows,
             " \u00b7 extreme forecast rows: ", fc$extreme_rows))
  } else if (intent == "horizon") {
    used <- c("forecast_outputs", "navigation_contract")
    lead <- paste0("This is a ", fc$steps_contract,
                   "-step daily forecast. There is no longer governed horizon.")
    body <- paste0(
      "The 15 governed models were probed on real series and every one of them",
      " emits exactly ", fc$steps_contract, " steps. A longer horizon was not",
      " shortened for display - it was never produced, so claiming a 4-year or",
      " 1,440-day forecast would be inventing data. The forecast window is ",
      fc$start_date, " to ", fc$end_date, ", and ", fc$steps_drawn,
      " rows are drawn for ", fc$model, ".")
    bullets <- c(paste0("forecast_type: ", fc$forecast_type),
                 paste0("horizon label: ", fc$horizon_label))
  } else if (intent == "caveats") {
    used <- c("navigation_contract")
    n_c <- length(e$caveats$codes)
    lead <- if (n_c)
      paste0("This series carries ", n_c, " caveat code",
             if (n_c == 1) "" else "s", ", recorded as informational.")
    else "No caveat code is recorded for this series."
    # caveat_badge and caveat_message are separate contract fields: a series can
    # carry a code while the contract still judges it non-material. Frame the
    # message as that judgement instead of printing it flat after a count,
    # which reads as a contradiction.
    body <- paste0(
      "Caveats in this product are informational, not blocking: the series is",
      " still shown, and product_status is ", sel$product_status, ".",
      if (nzchar(e$caveats$message))
        paste0(" The contract's own assessment of materiality reads: \"",
               e$caveats$message, "\"")
      else "",
      " They exist so a number is read with the right amount of confidence,",
      " not to hide it.")
    if (length(e$caveats$codes)) {
      bullets <- vapply(seq_along(e$caveats$codes), function(i) paste0(
        e$caveats$codes[[i]], " \u2014 severity ", e$caveats$severities[[i]],
        ", non-blocking"), character(1))
    }
  } else if (intent == "flags") {
    used <- c("navigation_contract", "forecast_outputs")
    lead <- paste0("Negative forecast rows: ", fc$negative_rows,
                   ". Extreme forecast rows: ", fc$extreme_rows, ".")
    body <- paste0(
      "Backtest predictions carry their own counters: ",
      ch$negative_backtest_rows, " negative and ", ch$extreme_backtest_rows,
      " extreme. These values are flagged and displayed exactly as the model",
      " produced them. Nothing is clipped to zero, because clipping would make",
      " a model look better than it is.")
  } else if (intent == "risk") {
    used <- c("navigation_contract", "series_signal_quality")
    safe <- !isTRUE(sig$no_signal) && isTRUE(sel$champion_visible)
    lead <- if (safe)
      "This series is interpretable, with the caveats noted below."
    else
      "Interpret this series with care - the evidence does not support a confident reading."
    body <- paste0(
      "Signal quality is ", sig$signal_quality_status,
      ", product status is ", sel$product_status, ", and champion_visible is ",
      sel$champion_visible, ". ",
      if (isTRUE(sig$no_signal))
        paste("Every observed actual is zero, so error metrics compare one",
              "flat line with another and cannot separate the models.")
      else if (isTRUE(sig$low_confidence_window))
        paste("The backtest window for this series is flagged low confidence,",
              "so the accuracy figures rest on a weak evaluation period.")
      else
        "The backtest window carries no low-confidence flag.")
    bullets <- c(paste0("Trailing zero on the latest actual: ", sig$trailing_zero),
                 paste0("Low-confidence backtest window: ", sig$low_confidence_window),
                 paste0("Caveats: ", .v24a_caveat_lines(e)))
  } else if (intent == "signal") {
    used <- c("series_signal_quality")
    lead <- paste0("Signal quality is ", sig$signal_quality_status, ".")
    body <- paste0(
      "The series has ",
      if (is.na(sig$observation_count)) "an unrecorded number of"
      else format(sig$observation_count, big.mark = ","),
      " observed points, of which ",
      if (is.na(sig$nonzero_count)) "an unrecorded number" else sig$nonzero_count,
      " are non-zero, covering ", sig$actual_min_date, " to ",
      sig$actual_max_date, ". ",
      if (isTRUE(sig$no_signal))
        paste("Because every value is zero, this series has no signal to model.",
              "It is kept visible so its emptiness is auditable, not hidden.")
      else "The series carries real variation.")
  } else if (intent == "attention") {
    used <- c("navigation_contract", "series_signal_quality", "forecast_outputs")
    lead <- "Three things are worth checking on this series."
    pts <- character(0)
    pts <- c(pts, if (isTRUE(sig$no_signal))
      "Every actual is zero: no model comparison here is meaningful."
      else paste0("Signal quality is ", sig$signal_quality_status, "."))
    pts <- c(pts, if (isTRUE(sel$champion_visible))
      paste0("The champion is ", ch$model, ", validity ", ch$validity, ".")
      else "No champion may be presented for this series.")
    pts <- c(pts, if (!is.na(fc$negative_rows) && fc$negative_rows > 0)
      paste0(fc$negative_rows, " forecast rows are negative and are shown unclipped.")
      else "No negative forecast rows are recorded.")
    bullets <- pts
    body <- paste0("Caveats recorded: ", .v24a_caveat_lines(e),
                   ". All are informational rather than blocking.")
  } else if (intent == "stakeholder") {
    used <- c("navigation_contract", "forecast_outputs", "model_rankings")
    lead <- if (isTRUE(sel$champion_visible))
      paste0("For ", sel$route_display_label, ", the recommended model is ",
             ch$model, ", with a ", fc$steps_contract, "-day forecast from ",
             fc$start_date, " to ", fc$end_date, ".")
    else
      paste0("For ", sel$route_display_label,
             ", I would not present a recommended model.")
    body <- if (isTRUE(sel$champion_visible))
      paste0("Say that the figure is a governed ", fc$steps_contract,
             "-day forecast, that the model was selected by measured backtest",
             " accuracy rather than preference, and that the horizon is short",
             " by design because that is what the models actually produce. ",
             if (length(e$caveats$codes))
               paste0("Mention the caveat: ", .v24a_caveat_lines(e), ".")
             else "")
    else
      paste("Explain that this series has no usable signal, so any model",
            "ranking is a formality. Presenting a winner would imply a",
            "confidence the data does not support.")
  } else if (intent == "coverage") {
    used <- c("taxonomy_counts")
    if (is.null(e$taxonomy)) {
      lead <- V6_24_ASSISTANT_NO_EVIDENCE
      body <- "No taxonomy row is recorded for this metric."
    } else {
      tx <- e$taxonomy
      lead <- paste0("The ", tx$metric, " cohort holds ", tx$series,
                     " operational series.")
      body <- paste0(
        "Of those, ", tx$viewer, " are visible in the Viewer, ", tx$forecast,
        " in Forecast and ", tx$champion, " carry a presentable champion. ",
        tx$no_signal, " have no signal, and ", tx$with_caveat,
        " are available with a caveat. Median WAPE for the metric is ",
        .v24a_fmt(tx$median_wape), " - a median, because the mean is",
        " unusable on this cohort.")
    }
  } else {
    lead <- V6_24_ASSISTANT_NO_EVIDENCE
    body <- "I can answer from the governed evidence for the selected series."
  }

  list(lead = lead, body = body, bullets = bullets,
       caveats = .v24a_caveat_lines(e), used = used,
       bounded = FALSE, intent = intent)
}

# ------------------------------------------------------------- quick prompts

V6_24_VIEWER_PROMPTS <- list(
  list(id = "qp_summary",   label = "Summarize the selected series", intent = "summary"),
  list(id = "qp_champion",  label = "Explain the champion",          intent = "champion"),
  list(id = "qp_backtest",  label = "Explain the backtest",          intent = "backtest"),
  list(id = "qp_ranking",   label = "Explain the model ranking",     intent = "ranking"),
  list(id = "qp_caveats",   label = "Explain the caveats",           intent = "caveats"),
  list(id = "qp_attention", label = "What should I pay attention to?", intent = "attention"),
  list(id = "qp_safe",      label = "Is this series safe to interpret?", intent = "risk")
)

V6_24_FORECAST_PROMPTS <- list(
  list(id = "fqp_summary", label = "Summarize the forecast",        intent = "forecast"),
  list(id = "fqp_model",   label = "What is the recommended model?", intent = "champion"),
  list(id = "fqp_risk",    label = "What is the main forecast risk?", intent = "risk"),
  list(id = "fqp_flags",   label = "Are there negative or extreme values?", intent = "flags"),
  list(id = "fqp_horizon", label = "Why is this only a 30-step forecast?", intent = "horizon"),
  list(id = "fqp_stake",   label = "What should I tell a stakeholder?", intent = "stakeholder")
)

# ------------------------------------------------- P9H | accuracy assistant

V6_24_ACCURACY_PROMPTS <- list(
  list(id = "aqp_summary",  label = "Summarize the accuracy view",   intent = "acc_summary"),
  list(id = "aqp_takeaway", label = "What is the main takeaway?",     intent = "acc_summary"),
  list(id = "aqp_strong",   label = "Which models look strongest?",   intent = "acc_models"),
  list(id = "aqp_worst",    label = "Where are the largest errors?",  intent = "acc_worst"),
  list(id = "aqp_heatmap",  label = "Explain the heatmap",            intent = "acc_heatmap"),
  list(id = "aqp_caveats",  label = "Explain the caveats",            intent = "acc_caveats"),
  list(id = "aqp_stake",    label = "What should I tell a stakeholder?", intent = "acc_stakeholder")
)

#' Evidence context for the Accuracy page of ONE selected series.
#'
#' Built from the APPLIED accuracy request, so the assistant describes what the
#' user is actually looking at rather than the pending controls. Every figure
#' is read from accuracy_metrics; nothing is recomputed.
v6_24_accuracy_evidence <- function(cfg, rows) {
  if (is.null(cfg) || is.null(rows) || !nrow(rows)) return(NULL)
  s <- v6_24_acc_summary(rows, cfg$metric)
  ok <- rows[is.finite(rows$metric_value), , drop = FALSE]
  ranked <- NULL
  if (nrow(ok) && !isTRUE(s$no_signal)) {
    o <- order(ok$metric_value)
    ranked <- stats::setNames(ok$metric_value[o], as.character(ok$model_name[o]))
  }
  list(
    metric = cfg$metric,
    series_label = s$series_label,
    models_selected = cfg$models,
    n_models = s$n_models,
    n_rows = s$n_rows,
    target_dates = s$target_dates,
    best = s$best, best_value = s$best_value,
    worst = s$worst, worst_value = s$worst_value,
    ranked = ranked,
    no_signal = s$no_signal,
    champion = s$champion, champion_visible = s$champion_visible,
    excluded = s$excluded, extreme = s$extreme,
    severity_method = s$severity_method,
    window_note = V6_24_ACC_WINDOW_NOTE,
    engine = V6_24_ASSISTANT_ENGINE)
}

#' Route an Accuracy question. Falls back to the shared refusal categories so a
#' causal or action question is rejected here exactly as it is elsewhere.
v6_24_accuracy_intent <- function(question) {
  q <- tolower(trimws(if (is.null(question)) "" else question))
  if (!nzchar(q)) return("acc_summary")
  if (grepl("stakeholder|explain to|tell (a|my|the)|non.?technical|exec", q))
    return("acc_stakeholder")
  if (grepl("heatmap|colou?r|severity|standardi", q)) return("acc_heatmap")
  if (grepl("worst|largest error|biggest error|where.*(error|fail)|pocket", q))
    return("acc_worst")
  if (grepl("strongest|best model|which model|stable|top model|rank", q))
    return("acc_models")
  if (grepl("caveat|not computable|excluded|extreme|warning|limitation", q))
    return("acc_caveats")
  if (grepl("horizon|30.?step|5 day|per horizon", q)) return("acc_horizon")
  if (grepl("summar|takeaway|overview|what is this|describe|main", q))
    return("acc_summary")
  # Anything else reuses the general router, which owns the refusals.
  gen <- v6_24_assistant_intent(question)
  if (gen %in% c("unsupported", "unsupported_cause", "unsupported_action"))
    return(gen)
  "acc_summary"
}


#' Compose an Accuracy answer for the selected series.
#'
#' Every branch prints values the evidence builder read from accuracy_metrics.
#' Two gates are enforced here as they are everywhere else in V6.24: a no-signal
#' series gets no "best model", and a causal or action question is refused.
v6_24_accuracy_answer <- function(e, question = "", intent = NULL) {
  if (is.null(e)) {
    return(list(
      lead = "No accuracy analysis has been run yet.",
      body = paste("Select a series in the Viewer, then choose a metric and",
                   "click Analyze Accuracy. I will describe exactly the model",
                   "rows that were analyzed for that series."),
      bullets = character(0), caveats = "", used = character(0),
      bounded = TRUE, intent = "no_analysis"))
  }
  if (is.null(intent)) intent <- v6_24_accuracy_intent(question)

  cav <- paste0(
    e$excluded, " of ", e$n_rows, " model rows have no computable ", e$metric,
    "; ", e$extreme, " carry an extreme magnitude (>= 1e6)",
    if (isTRUE(e$no_signal)) "; series has no signal" else "")
  used <- c("accuracy_metrics", "navigation_contract")
  bullets <- character(0)

  if (intent %in% c("unsupported", "unsupported_cause", "unsupported_action")) {
    a <- v6_24_assistant_answer(
      list(selection = list(product_status = ""),
           caveats = list(codes = character(0)), champion = list(),
           signal = list(), backtest = list(), forecast = list(),
           taxonomy = NULL), question, intent)
    a$caveats <- cav; a$used <- "none"
    return(a)
  }

  # Ranked list of models, best-first. Empty when the series has no signal.
  rank_lines <- function(n = 3) {
    if (is.null(e$ranked) || !length(e$ranked)) return(character(0))
    k <- utils::head(e$ranked, n)
    vapply(seq_along(k), function(i) paste0(
      i, ". ", names(k)[i], " \u2014 ", e$metric, " ",
      v6_24_acc_fmt(k[[i]])), character(1))
  }

  no_signal_body <- paste0(
    "Every observed actual for this series is zero. An error of zero here only ",
    "means the model predicted zero against zero, which is a degenerate ",
    "identity rather than accuracy, so no model is presented as best. The rows ",
    "stay visible for technical inspection and are badged 'no signal'.")

  if (intent == "acc_summary") {
    lead <- if (isTRUE(e$no_signal))
      paste0("Accuracy for ", e$series_label,
             " cannot be interpreted: the series has no signal.")
    else
      paste0("On ", e$series_label, ", ", e$best, " has the lowest ", e$metric,
             " at ", v6_24_acc_fmt(e$best_value), ".")
    body <- if (isTRUE(e$no_signal)) no_signal_body else paste0(
      e$n_models, " governed models were compared over ", e$target_dates,
      " evaluated target dates. ", e$window_note,
      " The weakest is ", e$worst, " at ", v6_24_acc_fmt(e$worst_value),
      ". Every value is read from accuracy_metrics; nothing is recomputed here.")
    bullets <- rank_lines(3)
    if (nzchar(e$champion)) {
      bullets <- c(bullets, if (isTRUE(e$champion_visible))
        paste0("Governed champion for this series: ", e$champion,
               " (chosen by the ranking policy, not by this page)")
        else paste0("Champion is not presentable for this series (", e$champion,
                    " is a technical tie-break only)"))
    }
  } else if (intent == "acc_models") {
    lead <- if (isTRUE(e$no_signal))
      "No model can be called strongest on this series."
    else paste0(e$best, " is strongest on ", e$metric, " for this series.")
    body <- if (isTRUE(e$no_signal)) no_signal_body else paste0(
      "This is a per-series ordering by one metric, not a champion decision. ",
      "Champion selection is read from model_rankings under the governed ",
      "ranking policy and may use a different primary metric. Switching the ",
      "metric above can reorder these models: a model can be strong on MAE and ",
      "weak on WAPE, which is exactly what the heatmap is for.")
    bullets <- rank_lines(5)
  } else if (intent == "acc_worst") {
    lead <- if (isTRUE(e$no_signal))
      "No meaningful error ranking exists for this series."
    else paste0("The largest ", e$metric, " on this series is ", e$worst,
                " at ", v6_24_acc_fmt(e$worst_value), ".")
    body <- if (isTRUE(e$no_signal)) no_signal_body else paste0(
      "The table below is ordered best-first, so the weakest models are at the ",
      "bottom. ", e$extreme, " row(s) carry a magnitude at or above 1e6; those ",
      "are flagged rather than hidden, because a value that large usually means ",
      "the model failed on a near-zero denominator rather than being slightly ",
      "off.")
  } else if (intent == "acc_heatmap") {
    lead <- "Colour is a display-only severity score, not a governed metric."
    body <- paste0(
      "Each row is a governed model and each column a governed measure. ",
      "Severity is (value - median) / IQR computed WITHIN each column, using ",
      "the ", e$severity_method, " branch, then capped at +/-3 so one extreme ",
      "cell cannot flatten the rest. It is standardized per column because MAE ",
      "and SMAPE do not share a scale. The raw value is always in the tooltip ",
      "and the table; the colour never feeds a ranking or a champion decision.")
    bullets <- c(
      "Rows: the governed models you selected, best-first by the chosen metric",
      "Columns: every governed measure the artifact carries",
      "Red = worse than the other models of this series on that measure",
      "Grey = the artifact recorded that measure as not computable")
  } else if (intent == "acc_caveats") {
    lead <- if (isTRUE(e$no_signal))
      "This series has no signal, which is the caveat that matters here."
    else if (e$excluded > 0)
      paste0(e$excluded, " of ", e$n_rows, " model rows have no computable ",
             e$metric, ".")
    else if (e$extreme > 0)
      paste0("Every model row has a computable ", e$metric, ", but ", e$extreme,
             " carry an extreme magnitude.")
    else paste0("No caveat applies to the analyzed ", e$metric, " rows.")
    body <- paste0(
      if (isTRUE(e$no_signal)) paste0(no_signal_body, " ") else "",
      if (e$excluded > 0) paste0(
        "A non-computable value is not a zero and not missing data: the ",
        "artifact recorded it as STRUCTURALLY_NOT_COMPUTABLE, which happens ",
        "when the denominator of a ratio metric is zero across the evaluation ",
        "window. Those rows are excluded from the best and weakest cards and ",
        "drawn as grey cells. ")
      else paste0(e$metric, " is defined for every model row here. Ratio ",
                  "metrics such as WAPE and MAPE do carry non-computable rows ",
                  "on parts of this cohort; switch the metric to see them. "),
      if (e$extreme > 0) paste0(
        e$extreme, " row(s) reach the 1e6 extreme threshold and are shown in ",
        "scientific notation, flagged rather than hidden.")
      else "No row reaches the 1e6 extreme threshold.")
  } else if (intent == "acc_horizon") {
    lead <- "Accuracy here is not sliced by horizon."
    body <- paste0(
      e$window_note, " The Viewer backtest chart does filter by horizon, ",
      "because model_backtests_15_models carries horizon_steps per row. ",
      "accuracy_metrics does not, so offering a 5/10/15/20/25/30 accuracy ",
      "filter would show six identical result sets. The page discloses the ",
      "window instead of pretending to filter it.")
  } else if (intent == "acc_stakeholder") {
    lead <- if (isTRUE(e$no_signal))
      paste0("For ", e$series_label, ", I would not quote an accuracy figure.")
    else paste0("For ", e$series_label, ", ", e$best,
                " gives the lowest ", e$metric, " at ",
                v6_24_acc_fmt(e$best_value), ".")
    body <- if (isTRUE(e$no_signal)) paste0(
      "Explain that this series has no usable signal - every observed value is ",
      "zero - so any accuracy number is an artefact of comparing zero with ",
      "zero. Presenting a model as accurate here would imply a confidence the ",
      "data does not support.")
    else paste0(
      "Say the figure comes from a frozen backtest evaluation over ",
      e$target_dates, " target dates, that lower is better, and that it is a ",
      "diagnostic rather than a ranking decision. ",
      if (e$excluded > 0) paste0("Mention that ", e$excluded,
        " model row(s) could not produce a computable ", e$metric,
        " and were excluded rather than counted as zero. ") else "",
      "Avoid quoting an average across series: this cohort's mean is distorted ",
      "by extreme values, which is why medians are used throughout AEGIS.")
    bullets <- rank_lines(3)
  } else {
    lead <- V6_24_ASSISTANT_NO_EVIDENCE
    body <- "I can answer from the analyzed accuracy rows for this series."
    used <- "none"
  }

  list(lead = lead, body = body, bullets = bullets,
       caveats = cav, used = used, bounded = FALSE, intent = intent)
}


# ------------------------------------------ P9K | Models FULL Universe assistant

V6_24_MF_UNIVERSE_PROMPTS <- list(
  list(id = "mfq_summary", label = "Summarize the model universe",  intent = "mf_summary"),
  list(id = "mfq_family",  label = "Explain the model families",    intent = "mf_families"),
  list(id = "mfq_strong",  label = "Which models look strongest by cohort medians?", intent = "mf_strongest"),
  list(id = "mfq_nottour", label = "Why is this not a tournament?", intent = "mf_not_tournament"),
  list(id = "mfq_changed", label = "What changed from the old HDD model section?", intent = "mf_changed"),
  list(id = "mfq_stake",   label = "What should I tell a stakeholder?", intent = "mf_stakeholder")
)

#' Evidence context for the Models FULL Universe page.
#'
#' Read-only. Wraps the helper outputs so the composer never touches an artifact
#' directly and can never introduce a metric the artifact does not carry.
v6_24_mf_evidence <- function() {
  s <- v6_24_mf_universe_summary()
  tb <- v6_24_mf_universe_table()
  ch <- v6_24_mf_champion_counts()
  list(summary = s, table = tb, champions = ch,
       legacy = V6_24_MF_LEGACY_SCOPE, engine = V6_24_ASSISTANT_ENGINE)
}

v6_24_mf_intent <- function(question) {
  q <- tolower(trimws(if (is.null(question)) "" else question))
  if (!nzchar(q)) return("mf_summary")
  if (grepl("stakeholder|explain to|tell (a|my|the)|non.?technical|exec", q))
    return("mf_stakeholder")
  if (grepl("tournament|pairwise|head.?to.?head|bootstrap|mase|rmsse", q))
    return("mf_not_tournament")
  if (grepl("chang|old|legacy|hdd|before|previous", q)) return("mf_changed")
  if (grepl("famil|group|baseline|challenger|neural|statistical|deep", q))
    return("mf_families")
  if (grepl("strong|best|lowest|median|compare|rank|winner|champion", q))
    return("mf_strongest")
  if (grepl("summar|overview|what is this|describe|universe|how many", q))
    return("mf_summary")
  gen <- v6_24_assistant_intent(question)
  if (gen %in% c("unsupported", "unsupported_cause", "unsupported_action"))
    return(gen)
  "mf_summary"
}

#' Compose a Models FULL Universe answer.
#'
#' Hard rule enforced by construction: no branch names a global champion, a
#' tournament result, MASE or RMSSE as current V6.24 evidence. Where the legacy
#' scope is described, it is explicitly framed as the previous section.
v6_24_mf_answer <- function(e, question = "", intent = NULL) {
  if (is.null(e) || is.null(e$summary)) {
    return(list(lead = "The model universe is not loaded.",
                body = "The governed artifacts could not be read.",
                bullets = character(0), caveats = "", used = character(0),
                bounded = TRUE, intent = "no_data"))
  }
  if (is.null(intent)) intent <- v6_24_mf_intent(question)
  s <- e$summary; tb <- e$table
  used <- c("accuracy_metrics", "navigation_contract")
  bullets <- character(0)
  cav <- paste0(s$champion_suppressed,
                " series have no presentable champion; medians exclude rows the ",
                "artifact recorded as not computable")

  if (intent %in% c("unsupported", "unsupported_cause", "unsupported_action")) {
    a <- v6_24_assistant_answer(
      list(selection = list(product_status = ""),
           caveats = list(codes = character(0)), champion = list(),
           signal = list(), backtest = list(), forecast = list(),
           taxonomy = NULL), question, intent)
    a$caveats <- cav; a$used <- "none"
    return(a)
  }

  top <- function(n = 3) {
    if (is.null(tb) || !nrow(tb)) return(character(0))
    k <- utils::head(tb, n)
    vapply(seq_len(nrow(k)), function(i) paste0(
      k$model_name[i], " \u2014 median MAE ", v6_24_acc_fmt(k$median_mae[i]),
      ", median WAPE ", v6_24_acc_fmt(k$median_wape[i]),
      ", leads ", k$series_champion_count[i], " series"), character(1))
  }

  if (intent == "mf_summary") {
    lead <- paste0("The governed V6.24 universe is ", s$n_models,
                   " models evaluated on ", s$n_series, " operational series.")
    body <- paste0(
      "That produces ", format(s$n_rows, big.mark = ","),
      " model-series accuracy rows across ", s$n_metrics,
      " measures. Of the ", s$n_series, " series, ", s$champion_visible,
      " have a champion that may be presented and ", s$champion_suppressed,
      " do not, because every observed actual for those series is zero. ",
      s$distinct_winners, " different models lead at least one series, so no ",
      "single model describes the cohort.")
    bullets <- top(3)
  } else if (intent == "mf_families") {
    lead <- "Two classifications apply, and they do not agree."
    body <- paste0(
      "The artifact carries a three-valued model_family: Baseline, Challenger ",
      "and Neural. The four families shown on this page - Growth Baseline, ",
      "Statistical, Machine Learning, Deep Learning - are a display grouping ",
      "only. The partitions cut across each other: ETS Explicit is a Challenger ",
      "shown under Statistical, and LinearRegression is a Baseline shown under ",
      "Machine Learning. The display grouping is for reading the list; the ",
      "governed family is the one recorded in the artifact.")
  } else if (intent == "mf_strongest") {
    lead <- if (nrow(tb))
      paste0("By cohort median MAE, ", tb$model_name[1], " is lowest at ",
             v6_24_acc_fmt(tb$median_mae[1]), ".")
    else "No accuracy rows are available."
    body <- paste0(
      "This is a diagnostic median over the artifact, not a governed ranking ",
      "and not a winner. Median MAE and median WAPE do not produce the same ",
      "order, and per-series ranking is decided separately in model_rankings. ",
      "Medians are used because the cohort mean is distorted by extreme values.")
    bullets <- top(5)
  } else if (intent == "mf_not_tournament") {
    lead <- "V6.24 carries no head-to-head evidence, so this page makes no such claim."
    body <- paste0(
      "The previous model section ranked models with a paired bootstrap ",
      "procedure and reported supported-better and supported-worse records. ",
      "That evidence does not exist for this cohort: there is no pairwise ",
      "artifact, and the two metrics it used are not carried by ",
      "accuracy_metrics. Computing either inside the dashboard is not ",
      "permitted, so the page shows what the artifacts do contain - cohort ",
      "medians and per-series championship counts - and says plainly that this ",
      "is a description, not a competition.")
    bullets <- c(
      paste0("Absent from V6.24: ",
             paste(e$legacy$absent_in_v624, collapse = ", ")),
      "Present instead: per-series rankings and cohort diagnostic medians")
  } else if (intent == "mf_changed") {
    lead <- paste0("The scope grew from ", e$legacy$models, " models on ",
                   e$legacy$entities, " entities to ", s$n_models,
                   " models on ", s$n_series, " series.")
    body <- paste0(
      "The previous section covered ", e$legacy$metric,
      ". The V6.24 cohort spans four metrics. Only ", e$legacy$overlap,
      " models appear in both: the earlier work carried ", e$legacy$legacy_only,
      ", which V6.24 does not, and V6.24 adds ",
      paste(e$legacy$v624_only, collapse = ", "),
      ", which were never part of that earlier comparison. The measures also ",
      "changed, so figures from the two are not comparable.")
  } else if (intent == "mf_stakeholder") {
    lead <- paste0("AEGIS now compares ", s$n_models,
                   " models across ", s$n_series,
                   " operational series in four metric families.")
    body <- paste0(
      "Say that every model is scored on the same governed backtest, that the ",
      "comparison here is diagnostic rather than a competition, and that the ",
      "best model is chosen per series rather than once for everything - ",
      s$distinct_winners, " different models lead at least one series. ",
      "Mention that ", s$champion_suppressed,
      " series carry no usable signal and are excluded from any recommendation. ",
      "Avoid quoting an average across series: the cohort mean is distorted by ",
      "extreme values, which is why medians are used.")
    bullets <- top(3)
  } else {
    lead <- V6_24_ASSISTANT_NO_EVIDENCE
    body <- "I can answer from the governed model universe artifacts."
    used <- "none"
  }

  list(lead = lead, body = body, bullets = bullets,
       caveats = cav, used = used, bounded = FALSE, intent = intent)
}

# --------------------------------------- P9L | Models FULL Ranking assistant

V6_24_MF_RANKING_PROMPTS <- list(
  list(id = "mrq_summary", label = "Summarize the ranking diagnostics",  intent = "mr_summary"),
  list(id = "mrq_best",    label = "Which model has the best diagnostic median?", intent = "mr_best"),
  list(id = "mrq_leads",   label = "Which model leads the most series?", intent = "mr_leads"),
  list(id = "mrq_nottour", label = "Why is this not a tournament?",      intent = "mr_not_tournament"),
  list(id = "mrq_nochamp", label = "Why is there no global champion?",   intent = "mr_no_global"),
  list(id = "mrq_changed", label = "What changed from the old HDD Tournament?", intent = "mr_changed"),
  list(id = "mrq_stake",   label = "What should I tell a stakeholder?",  intent = "mr_stakeholder")
)

#' Evidence context for the Ranking Diagnostics page.
v6_24_mr_evidence <- function(cfg, rows) {
  if (is.null(cfg) || is.null(rows) || !nrow(rows)) return(NULL)
  s <- v6_24_mf_ranking_summary(rows, cfg$metric)
  dis <- v6_24_mf_metric_disagreement_rows()
  list(cfg = cfg, summary = s, rows = rows, disagreement = dis,
       legacy = V6_24_MF_LEGACY_SCOPE, engine = V6_24_ASSISTANT_ENGINE)
}

v6_24_mr_intent <- function(question) {
  q <- tolower(trimws(if (is.null(question)) "" else question))
  if (!nzchar(q)) return("mr_summary")
  if (grepl("stakeholder|explain to|tell (a|my|the)|non.?technical|exec", q))
    return("mr_stakeholder")
  # ORDER MATTERS. "What changed from the old HDD Tournament?" contains the word
  # tournament but is asking about the change, so the comparison check must run
  # before the tournament check. "Why is this not a tournament?" carries none of
  # these words and still falls through correctly.
  if (grepl("chang|\\bold\\b|legacy|\\bhdd\\b|before|previous|earlier", q))
    return("mr_changed")
  if (grepl("global champion|one champion|overall champion|no champion", q))
    return("mr_no_global")
  if (grepl("tournament|pairwise|head.?to.?head|bootstrap|p.?value|mase|rmsse", q))
    return("mr_not_tournament")
  if (grepl("lead|most series|champion count|wins most", q)) return("mr_leads")
  if (grepl("best|lowest|strong|median|compare|order|position", q))
    return("mr_best")
  if (grepl("summar|overview|what is this|describe|takeaway", q))
    return("mr_summary")
  gen <- v6_24_assistant_intent(question)
  if (gen %in% c("unsupported", "unsupported_cause", "unsupported_action"))
    return(gen)
  "mr_summary"
}

#' Compose a Ranking Diagnostics answer.
#'
#' The two headline models - best diagnostic median and most series led - are
#' reported separately and never merged into a winner. When they differ, the
#' answer says so explicitly, because that disagreement is the finding.
v6_24_mr_answer <- function(e, question = "", intent = NULL) {
  if (is.null(e)) {
    return(list(
      lead = "No diagnostic comparison has been run yet.",
      body = paste("Choose a measure and click Analyze Ranking Diagnostics.",
                   "I will then describe exactly the rows that were compared."),
      bullets = character(0), caveats = "", used = character(0),
      bounded = TRUE, intent = "no_analysis"))
  }
  if (is.null(intent)) intent <- v6_24_mr_intent(question)
  s <- e$summary; rows <- e$rows
  used <- c("accuracy_metrics", "navigation_contract")
  bullets <- character(0)
  cav <- paste0(s$champion_suppressed,
                " no-signal series excluded from champion counts; ",
                s$noncomputable, " model-series rows have no computable ",
                s$metric)

  if (intent %in% c("unsupported", "unsupported_cause", "unsupported_action")) {
    a <- v6_24_assistant_answer(
      list(selection = list(product_status = ""),
           caveats = list(codes = character(0)), champion = list(),
           signal = list(), backtest = list(), forecast = list(),
           taxonomy = NULL), question, intent)
    a$caveats <- cav; a$used <- "none"
    return(a)
  }

  topn <- function(n = 3) {
    if (is.null(rows) || !nrow(rows)) return(character(0))
    k <- utils::head(rows, n)
    vapply(seq_len(nrow(k)), function(i) paste0(
      "Position ", k$diagnostic_position[i], ": ", k$model_name[i],
      " \u2014 median ", s$metric, " ", v6_24_acc_fmt(k$median_selected[i]),
      ", leads ", k$series_champion_count[i], " series"), character(1))
  }

  disagree_line <- if (isTRUE(s$agree))
    paste0("On this measure the lowest median and the most series led are the ",
           "same model, ", s$best_median_model,
           ". That agreement does not hold for every measure.")
  else
    paste0("The lowest median is ", s$best_median_model,
           " while the most series are led by ", s$most_champ_model,
           " with ", s$most_champ_count,
           ". Those are different models, which is why neither is called a winner.")

  if (intent == "mr_summary") {
    lead <- paste0("Across ", s$models_shown, " models and ", s$n_series,
                   " series, compared on ", s$metric, ".")
    body <- paste0(
      disagree_line,
      " All values are cohort medians read from the artifact; nothing is ",
      "recomputed and no ordering here is an official rank.")
    bullets <- topn(3)
  } else if (intent == "mr_best") {
    lead <- if (nzchar(s$best_median_model) && s$best_median_model != "\u2014")
      paste0(s$best_median_model, " has the lowest diagnostic median ",
             s$metric, " at ", v6_24_acc_fmt(s$best_median_value), ".")
    else paste0("No computable ", s$metric, " median is available.")
    body <- paste0(
      "A diagnostic median is the middle of that model's per-series error ",
      "across the cohort. It is not a selection and not a champion: the ",
      "governed per-series ranking decides which model leads each series, and ",
      "changing the measure above can reorder this list.")
    bullets <- topn(5)
  } else if (intent == "mr_leads") {
    lead <- paste0(s$most_champ_model, " leads the most series, ",
                   s$most_champ_count, " of ", s$champion_visible,
                   " with a presentable champion.")
    body <- paste0(
      "This is a series-level count, not a cohort-wide decision. The ",
      s$champion_suppressed, " no-signal series are excluded, because a model ",
      "predicting zero against an all-zero series scores a perfect error there ",
      "without having modelled anything. ", disagree_line)
  } else if (intent == "mr_not_tournament") {
    lead <- "V6.24 holds no head-to-head evidence, so this page compares medians instead."
    body <- paste0(
      "The earlier model section ran a paired statistical procedure and could ",
      "report that one model beat another with stated confidence. That ",
      "evidence has no successor artifact for this cohort, and the two measures ",
      "it ranked on are not carried by accuracy_metrics. Producing either ",
      "inside the dashboard is not permitted, so the page reports what the ",
      "artifacts do contain and labels the ordering a diagnostic position ",
      "rather than a rank.")
    bullets <- c(paste0("Absent from V6.24: ",
                        paste(e$legacy$absent_in_v624, collapse = ", ")),
                 "Present instead: cohort medians and per-series champion counts")
  } else if (intent == "mr_no_global") {
    lead <- "No cohort-wide model decision exists in V6.24 to report."
    body <- paste0(
      "Champion selection in V6.24 is recorded per series in the governed ",
      "contract, and ", nrow(v6_24_mf_champion_counts()),
      " different models lead at least one series. There is no artifact that ",
      "names one model for the whole cohort, and deriving one here would be ",
      "inventing a decision that was never made. ", disagree_line)
  } else if (intent == "mr_changed") {
    lead <- paste0("The scope grew from ", e$legacy$models, " models on ",
                   e$legacy$entities, " entities to ", s$n_models,
                   " models on ", s$n_series, " series.")
    body <- paste0(
      "The earlier comparison covered ", e$legacy$metric,
      " and ranked models with a paired statistical procedure. This cohort ",
      "spans four metrics, only ", e$legacy$overlap,
      " models appear in both, and the measures changed as well, so figures ",
      "from the two are not comparable. What this page can report is cohort ",
      "medians and how many series each model leads.")
  } else if (intent == "mr_stakeholder") {
    lead <- paste0("On ", s$metric, ", ", s$best_median_model,
                   " has the lowest cohort median; ", s$most_champ_model,
                   " leads the most series.")
    body <- paste0(
      "Say that these are diagnostics rather than a competition, that the best ",
      "model is chosen per series rather than once for everything, and that ",
      "the two headlines above often point at different models. Mention that ",
      s$champion_suppressed, " series carry no usable signal and are excluded. ",
      "Avoid quoting an average across series: the cohort mean is distorted by ",
      "extreme values, which is why medians are used throughout.")
    bullets <- topn(3)
  } else {
    lead <- V6_24_ASSISTANT_NO_EVIDENCE
    body <- "I can answer from the analyzed diagnostic rows."
    used <- "none"
  }

  list(lead = lead, body = body, bullets = bullets,
       caveats = cav, used = used, bounded = FALSE, intent = intent)
}

# -------------------------------------- P9M | Models FULL Champion assistant

V6_24_MF_CHAMPION_PROMPTS <- list(
  list(id = "mcq_summary", label = "Summarize the Champion page",       intent = "mc_summary"),
  list(id = "mcq_leads",   label = "Which model leads the most series?",  intent = "mc_leads"),
  list(id = "mcq_sel",     label = "What is the champion for this selected series?", intent = "mc_selected"),
  list(id = "mcq_noglob",  label = "Why is there no global champion?",    intent = "mc_no_global"),
  list(id = "mcq_nosig",   label = "Why are no-signal series suppressed?", intent = "mc_no_signal"),
  list(id = "mcq_changed", label = "What changed from the old HDD Champion page?", intent = "mc_changed"),
  list(id = "mcq_stake",   label = "What should I tell a stakeholder?",   intent = "mc_stakeholder")
)

#' Evidence context for Champion FULL. `sel` is the selected series champion
#' object, or NULL when nothing is selected.
v6_24_mc_evidence <- function(sel = NULL) {
  list(summary = v6_24_mf_champion_summary(),
       distribution = v6_24_mf_champion_distribution(),
       policy = v6_24_mf_champion_policy_summary(),
       legacy = v6_24_mf_legacy_champion_facts(),
       selected = sel,
       engine = V6_24_ASSISTANT_ENGINE)
}

v6_24_mc_intent <- function(question) {
  q <- tolower(trimws(if (is.null(question)) "" else question))
  if (!nzchar(q)) return("mc_summary")
  if (grepl("stakeholder|explain to|tell (a|my|the)|non.?technical|exec", q))
    return("mc_stakeholder")
  # ORDER MATTERS. This guard runs before the comparison rule below. That rule
  # matches the bare token "hdd" so it can catch "what changed from the old HDD
  # Champion page", which also means a forward-looking question such as "what
  # will HDD be next quarter" would otherwise be answered with the legacy
  # comparison. This page carries champion evidence only and no forecast value,
  # so forward-looking questions are declined and redirected.
  if (grepl(paste0("what will|whats going to|what is going to|will .* be\\b|",
                   "next (week|month|quarter|year)|predict|forecast|",
                   "future|going forward|how much will|expected value"), q))
    return("mc_out_of_scope")
  # Comparison questions run before the tournament/global guards so a question
  # about the change is not swallowed by them.
  if (grepl("chang|\\bold\\b|legacy|\\bhdd\\b|before|previous|earlier", q))
    return("mc_changed")
  if (grepl("no.?signal|suppress|zero|all.?zero|why.*excluded", q))
    return("mc_no_signal")
  if (grepl("this series|selected series|current series|this selection", q))
    return("mc_selected")
  if (grepl("global|overall|one champion|whole cohort|tournament|pairwise", q))
    return("mc_no_global")
  if (grepl("lead|most series|distribution|how many series", q)) return("mc_leads")
  if (grepl("polic|tie.?break|rank", q)) return("mc_policy")
  if (grepl("summar|overview|what is this|describe|champion", q))
    return("mc_summary")
  gen <- v6_24_assistant_intent(question)
  if (gen %in% c("unsupported", "unsupported_cause", "unsupported_action"))
    return(gen)
  "mc_summary"
}

#' Compose a Champion FULL answer.
#'
#' Two hard gates enforced by construction: no branch names a global champion,
#' and any branch touching a selected series checks `presentable` before using
#' champion language at all.
v6_24_mc_answer <- function(e, question = "", intent = NULL) {
  if (is.null(e) || is.null(e$summary)) {
    return(list(lead = "Champion evidence is not loaded.",
                body = "The governed artifacts could not be read.",
                bullets = character(0), caveats = "", used = character(0),
                bounded = TRUE, intent = "no_data"))
  }
  if (is.null(intent)) intent <- v6_24_mc_intent(question)
  s <- e$summary; d <- e$distribution; sel <- e$selected
  used <- c("navigation_contract", "model_rankings")
  bullets <- character(0)
  cav <- paste0(s$suppressed, " of ", s$n_series,
                " series have no presentable champion; champion evidence is ",
                "per series and no cohort-wide decision exists")

  if (intent %in% c("unsupported", "unsupported_cause", "unsupported_action")) {
    a <- v6_24_assistant_answer(
      list(selection = list(product_status = ""),
           caveats = list(codes = character(0)), champion = list(),
           signal = list(), backtest = list(), forecast = list(),
           taxonomy = NULL), question, intent)
    a$caveats <- cav; a$used <- "none"
    return(a)
  }

  topn <- function(n = 3) {
    if (is.null(d) || !nrow(d)) return(character(0))
    k <- utils::head(d, n)
    vapply(seq_len(nrow(k)), function(i) paste0(
      k$model_name[i], " leads ", k$series_champion_count[i], " series (",
      format(round(100 * k$share_of_presentable[i], 1), nsmall = 1),
      "% of presentable)"), character(1))
  }

  if (intent == "mc_out_of_scope") {
    return(list(
      lead = "This page does not carry forecast values.",
      body = paste0(
        "This page reports which model leads each series in the governed ",
        "backtest evidence. It holds no future value for any metric, so a ",
        "question about what a series will do next cannot be answered from ",
        "it. Open Forecasting \u2192 Forecast for the governed 30-step daily ",
        "forecast of the selected series, and read the champion here only as ",
        "the model that led that series in backtest."),
      bullets = character(0), caveats = cav, used = "none",
      bounded = TRUE, intent = intent))
  }

  if (intent == "mc_summary") {
    lead <- paste0("Champion evidence in V6.24 is recorded per series: ",
                   s$presentable, " of ", s$n_series,
                   " series have a presentable champion.")
    body <- paste0(
      s$n_leaders, " different models lead at least one series, and no model ",
      "describes the cohort. The remaining ", s$suppressed,
      " series carry no presentable champion because every observed actual is ",
      "zero. Champion visibility is governed by ", s$ranking_policy,
      " and is read from the contract, never derived here.")
    bullets <- topn(3)
  } else if (intent == "mc_leads") {
    lead <- paste0(s$top_model, " leads the most series: ", s$top_count,
                   " of ", s$presentable, " presentable series.")
    body <- paste0(
      "This is a series-level count, not a cohort-wide decision. ",
      s$n_leaders, " models lead at least one series, and the counts sum to ",
      s$counts_sum, " because the ", s$suppressed,
      " no-signal series are excluded rather than assigned to anyone.")
    bullets <- topn(5)
  } else if (intent == "mc_selected") {
    if (is.null(sel)) {
      lead <- "No series is selected."
      body <- paste("Choose a series in Forecasting - Viewer, or use the selector",
                    "on this page, and I will describe its champion evidence.")
    } else if (isTRUE(sel$presentable)) {
      lead <- paste0("For ", sel$label, ", the series-level champion is ",
                     sel$champion_model, ".")
      body <- paste0(
        "It is ranked ", if (is.na(sel$champion_rank)) "-" else sel$champion_rank,
        " within this series by ", sel$rank_metric, " = ",
        v6_24_acc_fmt(sel$rank_value, 6), ", under ", sel$ranking_policy,
        ". Validity is ", sel$validity,
        ". This applies to this series only; other series are led by other ",
        "models, and V6.24 defines no cohort-wide champion.")
    } else {
      lead <- paste0("For ", sel$label, ", there is no presentable champion.")
      body <- paste0(
        "Signal quality is ", sel$signal_quality,
        ", so champion_visible is FALSE. Every observed actual for this series ",
        "is zero, which means a model predicting zero scores a perfect error ",
        "without having modelled anything. The contract still records ",
        sel$champion_model, " from the internal tie-break, but it is a ",
        "reference only and must not be read as best, recommended or a winner.")
    }
  } else if (intent == "mc_no_global") {
    lead <- "V6.24 does not define a champion for the whole cohort."
    body <- paste0(
      "Champion is recorded per series in the governed contract, and ",
      s$n_leaders, " different models lead at least one series. No artifact ",
      "names one model for everything, and deriving one here would be ",
      "inventing a decision that was never made. There is also no head-to-head ",
      "evidence in V6.24 that could support such a decision.")
    bullets <- topn(3)
  } else if (intent == "mc_no_signal") {
    lead <- paste0(s$suppressed, " series carry no presentable champion.")
    body <- paste0(
      "Every observed actual in those series is zero. A model that predicts ",
      "zero then scores an error of exactly zero, which looks perfect but ",
      "reflects a degenerate identity rather than accuracy. The governed ",
      "contract sets champion_visible to FALSE for them, so they are excluded ",
      "from the distribution and never contribute to any model's count. They ",
      "stay visible in the product so their emptiness is auditable.")
  } else if (intent == "mc_policy") {
    lead <- paste0("Champion selection follows ", s$ranking_policy, ".")
    body <- paste0(
      "Models are ranked within each series by a primary error metric where ",
      "lower is better, with a tie-break for cases where the metrics cannot ",
      "separate them. The champion_visible gate then decides whether the result ",
      "may be presented. Cohort medians shown on other pages summarise the ",
      "same artifact but do not select the per-series champion.")
  } else if (intent == "mc_changed") {
    L <- e$legacy
    lead <- paste0("The previous Champion page named one model for ",
                   L$legacy_entities, " HDD entities; V6.24 records a champion ",
                   "per series across ", s$n_series, ".")
    body <- paste0(
      "That earlier decision selected ", L$legacy_model,
      " with conditions, and it is historical. On the V6.24 cohort ",
      L$legacy_model, " is the presentable champion on ",
      L$ets_presentable_v624, " of ", L$presentable_total,
      " series. It appears on ", L$ets_rows_v624,
      " contract rows, but ", L$ets_suppressed_v624,
      " of those are no-signal series where the tie-break assigns it and the ",
      "champion is suppressed. Restating the earlier sentence as a current ",
      "conclusion would contradict this cohort.")
  } else if (intent == "mc_stakeholder") {
    lead <- paste0("AEGIS picks the best model per series, not once for ",
                   "everything: ", s$n_leaders, " models lead at least one of ",
                   "the ", s$presentable, " series with a presentable champion.")
    body <- paste0(
      "Say that ", s$top_model, " leads most often, with ", s$top_count,
      " series, but that this is a count rather than a cohort-wide selection. ",
      "Mention that ", s$suppressed,
      " series carry no usable signal and are deliberately excluded from any ",
      "recommendation. Avoid describing any single model as the champion of ",
      "the platform - the evidence does not support that statement.")
    bullets <- topn(3)
  } else {
    lead <- V6_24_ASSISTANT_NO_EVIDENCE
    body <- "I can answer from the governed champion evidence."
    used <- "none"
  }

  list(lead = lead, body = body, bullets = bullets,
       caveats = cav, used = used, bounded = FALSE, intent = intent)
}
