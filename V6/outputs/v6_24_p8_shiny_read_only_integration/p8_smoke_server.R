# V6.24-P8 | reactive server test. Exercises the real server module with
# shiny::testServer so the filter cascade, champion suppression and forecast
# rendering are tested as they actually behave, not merely inspected.
suppressPackageStartupMessages({
  library(shiny); library(bslib); library(DT); library(plotly)
  library(dplyr); library(readr); library(tidyr)
})
setwd(Sys.getenv("V6_SHINY_DIR", "."))
source("global.R")

res <- list()
R <- function(id, label, cond, detail = "") {
  res[[length(res) + 1]] <<- data.frame(
    check_id = id, check = label, observed = as.character(detail),
    result = if (isTRUE(cond)) "PASS" else "FAIL", stringsAsFactors = FALSE)
  cat(sprintf("[%s] %-56s %s\n", if (isTRUE(cond)) "PASS" else "FAIL",
              label, detail))
}

nav <- v6_24_operational()
# Pick representative series from the artifacts, by FIELD, never by name.
pick <- function(pred) {
  s <- nav[pred, , drop = FALSE]
  if (!nrow(s)) NULL else s[1, , drop = FALSE]
}
sig  <- pick(nav$signal_quality_status == V6_24_SIGNAL_PRESENT &
               nav$champion_visible == "TRUE")
nosig <- pick(nav$signal_quality_status == V6_24_NO_SIGNAL)
lowc <- pick(nav$low_confidence_backtest_window_flag == "TRUE")

cat("representative series chosen from artifact fields:\n")
cat("  signal-present :", sig$series_id[1], "\n")
cat("  no-signal      :", nosig$series_id[1], "\n")
cat("  low-confidence :", lowc$series_id[1], "\n\n")

set_path <- function(session, prefix, row) {
  args <- list()
  for (ax in V6_24_FILTER_AXES) {
    args[[paste0(prefix, "_", ax)]] <- as.character(row[[ax]][1])
  }
  do.call(session$setInputs, args)
}

testServer(v6_24_mvp_server, {

  # ---- overview renders
  R("S1", "overview cards render", !is.null(output$v24_ov_cards))
  R("S2", "overview by-metric table renders", !is.null(output$v24_ov_by_metric))
  R("S3", "overview loader table renders", !is.null(output$v24_ov_loader))
  R("S4", "taxonomy scope selector renders", !is.null(output$v24_tx_scope_sel))

  # ---- filter cascade: first axis offers only real metrics
  m_ui <- output$v24_vw_sel_metric
  R("S5", "metric selector renders as first filter", !is.null(m_ui))
  R("S6", "key is NOT the first filter axis",
    identical(V6_24_FILTER_AXES[1], "metric"), V6_24_FILTER_AXES[1])
  R("S7", "key is the last filter axis",
    identical(V6_24_FILTER_AXES[length(V6_24_FILTER_AXES)], "key"))

  # ---- signal-present series: champion shown
  set_path(session, "v24_vw", sig)
  id_html <- paste(as.character(output$v24_vw_identity), collapse = "")
  ch_html <- paste(as.character(output$v24_vw_champion), collapse = "")
  R("S8", "viewer identity shows the selected series",
    grepl(sig$series_id[1], id_html, fixed = TRUE))
  R("S9", "signal-present series shows champion as a recommendation",
    grepl("Champion model", ch_html, fixed = TRUE) &&
      !grepl("not meaningful", ch_html, fixed = TRUE))
  R("S10", "champion model name rendered",
    grepl(as.character(sig$champion_model_name[1]), ch_html, fixed = TRUE),
    sig$champion_model_name[1])
  R("S11", "viewer model selector renders", !is.null(output$v24_vw_model_sel))
  R("S12", "actual history chart renders", !is.null(output$v24_vw_actuals))
  R("S13", "ranking table renders", !is.null(output$v24_vw_ranking))
  st <- paste(as.character(output$v24_vw_status), collapse = "")
  R("S14", "full path resolves to exactly one series",
    grepl("Selected:", st, fixed = TRUE))

  # backtest chart needs a model selection
  session$setInputs(v24_vw_model = as.character(sig$champion_model_name[1]))
  R("S15", "backtest chart renders", !is.null(output$v24_vw_backtest))

  # ---- no-signal series: champion suppressed
  set_path(session, "v24_vw", nosig)
  ch2 <- paste(as.character(output$v24_vw_champion), collapse = "")
  id2 <- paste(as.character(output$v24_vw_identity), collapse = "")
  R("S16", "no-signal series suppresses the champion recommendation",
    grepl("not meaningful", ch2, fixed = TRUE))
  R("S17", "no-signal series labels its champion technical only",
    grepl("not a recommendation", ch2, fixed = TRUE))
  R("S18", "no-signal series carries the NO_SIGNAL badge",
    grepl("NO_SIGNAL", id2, fixed = TRUE))
  R("S19", "no-signal series is still selectable and rendered",
    grepl(nosig$series_id[1], id2, fixed = TRUE))

  # ---- low-confidence series: caveat surfaced
  set_path(session, "v24_vw", lowc)
  id3 <- paste(as.character(output$v24_vw_identity), collapse = "")
  R("S20", "low-confidence series shows its caveat badge",
    grepl("LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO", id3, fixed = TRUE))
  R("S21", "low-confidence caveat message explains the zero tail",
    grepl("zero tail", id3, fixed = TRUE))

  # ---- forecast page
  set_path(session, "v24_fc", sig)
  fid <- paste(as.character(output$v24_fc_identity), collapse = "")
  R("S22", "forecast identity renders", grepl(sig$series_id[1], fid, fixed = TRUE))
  R("S23", "forecast page labels the governed horizon",
    grepl(V6_24_FORECAST_TYPE, fid, fixed = TRUE))
  R("S24", "forecast page shows 30 steps", grepl(">30<", fid))
  R("S25", "forecast model selector renders", !is.null(output$v24_fc_model_sel))
  session$setInputs(v24_fc_model = as.character(sig$champion_model_name[1]))
  R("S26", "forecast chart renders", !is.null(output$v24_fc_chart))
  R("S27", "forecast table renders", !is.null(output$v24_fc_table))

  # ---- taxonomy page
  session$setInputs(v24_tx_scope = "GLOBAL")
  R("S28", "taxonomy table renders for GLOBAL", !is.null(output$v24_tx_table))
  session$setInputs(v24_tx_scope = "BY_METRIC")
  R("S29", "taxonomy table renders for BY_METRIC", !is.null(output$v24_tx_table))
  R("S30", "caveat count table renders", !is.null(output$v24_tx_caveats))
  R("S31", "filter option table renders", !is.null(output$v24_tx_filters))
})

out <- do.call(rbind, res)
np <- sum(out$result == "PASS"); nf <- sum(out$result == "FAIL")
cat(sprintf("\nSERVER: %d PASS | %d FAIL of %d\n", np, nf, nrow(out)))
write.csv(out, file.path(Sys.getenv("V6_P8_OUT", "."),
                         "v6_24_p8_server_raw.csv"), row.names = FALSE)
if (nf == 0) cat("SERVER_TEST_OK\n") else cat("SERVER_TEST_FAILED\n")
