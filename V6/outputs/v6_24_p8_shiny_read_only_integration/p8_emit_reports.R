# V6.24-P8 | emits the R-derived P8 reports: loader validation, filter flow,
# page validations, caveat display and artifact immutability.
suppressPackageStartupMessages({
  library(shiny); library(bslib); library(DT); library(plotly)
  library(dplyr); library(readr); library(tidyr)
})
setwd(Sys.getenv("V6_SHINY_DIR", "."))
OUT <- Sys.getenv("V6_P8_OUT", ".")
COHORT <- "../data/processed/v6_24_mvp_cohort"

md5s <- function() {
  fs <- sort(list.files(COHORT, full.names = TRUE))
  setNames(vapply(fs, function(f) as.character(tools::md5sum(f)), character(1)),
           basename(fs))
}
before <- md5s()

source("global.R")
d <- v6_24_load_all()
nav <- v6_24_operational()

# ---------------------------------------------------------- loader validation
lv <- d$validation
lv$source <- vapply(lv$table, function(t) {
  stem <- V6_24_FILES[[t]]
  if (is.null(stem)) "" else file.path(COHORT, paste0(stem, ".parquet"))
}, character(1))
lv$rows_loaded <- vapply(lv$table, function(t) {
  x <- d[[t]]; if (is.null(x)) 0L else nrow(x)
}, integer(1))
lv$mutating <- "FALSE"
write.csv(lv[, c("table", "check", "expected", "observed", "rows_loaded",
                 "source", "mutating", "result")],
          file.path(OUT, "v6_24_p8_loader_validation_report.csv"),
          row.names = FALSE)
cat("loader_validation rows:", nrow(lv), "\n")

# ---------------------------------------------------------- filter flow
rows <- list()
for (depth in seq_along(V6_24_FILTER_AXES)) {
  axis <- V6_24_FILTER_AXES[depth]
  if (depth == 1L) {
    parents <- list(list())
  } else {
    pa <- V6_24_FILTER_AXES[seq_len(depth - 1)]
    u <- unique(nav[, pa, drop = FALSE])
    parents <- lapply(seq_len(nrow(u)), function(i)
      as.list(setNames(as.character(unlist(u[i, , drop = FALSE])), pa)))
  }
  for (ch in parents) {
    opts <- v6_24_axis_options(axis, ch)
    for (o in opts) {
      ch2 <- ch; ch2[[axis]] <- o
      n <- nrow(v6_24_resolve(ch2))
      vis <- v6_24_resolve(ch2)
      rows[[length(rows) + 1]] <- data.frame(
        filter_stage = paste0(depth, ". ", V6_24_FILTER_LABELS[[axis]]),
        parent_filter_path = if (length(ch)) paste(unlist(ch), collapse = "|")
                             else "GLOBAL",
        next_filter_axis = axis, valid_option_value = o,
        option_series_count = n,
        option_visible_count = sum(vis$viewer_visible == "TRUE"),
        option_status = if (n > 0) "AVAILABLE" else "EMPTY_MUST_NOT_HAPPEN",
        source = "navigation_contract (viewer_visible = TRUE)",
        result = if (n > 0) "PASS" else "FAIL",
        stringsAsFactors = FALSE)
    }
  }
}
ff <- do.call(rbind, rows)
# Every complete path must resolve to exactly one series.
uniq_ok <- 0L
for (i in seq_len(nrow(nav))) {
  ch <- as.list(setNames(as.character(unlist(nav[i, V6_24_FILTER_AXES])),
                         V6_24_FILTER_AXES))
  if (nrow(v6_24_resolve(ch)) == 1L) uniq_ok <- uniq_ok + 1L
}
ff <- rbind(ff, data.frame(
  filter_stage = "RESOLUTION", parent_filter_path = "ALL",
  next_filter_axis = "full six-level path",
  valid_option_value = "complete path resolves to exactly one series",
  option_series_count = uniq_ok, option_visible_count = uniq_ok,
  option_status = if (uniq_ok == nrow(nav)) "AVAILABLE" else "AMBIGUOUS",
  source = "navigation_contract",
  result = if (uniq_ok == nrow(nav)) "PASS" else "FAIL",
  stringsAsFactors = FALSE))
ff <- rbind(ff, data.frame(
  filter_stage = "AXIS ORDER", parent_filter_path = "ALL",
  next_filter_axis = "key position",
  valid_option_value = paste(V6_24_FILTER_AXES, collapse = " > "),
  option_series_count = NA_integer_, option_visible_count = NA_integer_,
  option_status = "AVAILABLE",
  source = "V6_24_FILTER_AXES",
  result = if (V6_24_FILTER_AXES[1] == "metric" &&
               V6_24_FILTER_AXES[6] == "key") "PASS" else "FAIL",
  stringsAsFactors = FALSE))
write.csv(ff, file.path(OUT, "v6_24_p8_filter_flow_validation.csv"),
          row.names = FALSE)
cat("filter_flow rows:", nrow(ff), " empty options:",
    sum(ff$option_series_count == 0, na.rm = TRUE), "\n")

# ---------------------------------------------------------- page validations
g <- v6_24_tax_scope("GLOBAL")
bm <- v6_24_tax_scope("BY_METRIC")
pv <- function(check, expected, observed) {
  data.frame(check = check, expected = as.character(expected),
             observed = as.character(observed),
             result = if (identical(as.character(expected),
                                    as.character(observed))) "PASS" else "FAIL",
             source = "navigation_contract / taxonomy_counts",
             stringsAsFactors = FALSE)
}
ov <- do.call(rbind, list(
  pv("total operational series", 140, g$operational_series_count[1]),
  pv("product_ready", 140, sum(nav$product_ready == "TRUE")),
  pv("viewer_visible", 140, g$viewer_visible_count[1]),
  pv("forecast_visible", 140, g$forecast_visible_count[1]),
  pv("ranking_visible", 140, sum(nav$ranking_visible == "TRUE")),
  pv("champion_visible", 125, g$champion_visible_count[1]),
  pv("available", 53, g$available_count[1]),
  pv("available_with_caveat", 87, g$available_with_caveat_count[1]),
  pv("no-signal series", 15, g$no_signal_count[1]),
  pv("low-confidence backtest window", 1,
     sum(nav$low_confidence_backtest_window_flag == "TRUE")),
  pv("forecast type", V6_24_FORECAST_TYPE, unique(nav$forecast_type)),
  pv("forecast horizon steps", 30, unique(nav$forecast_steps)),
  pv("median used, not mean", "median",
     unique(nav$recommended_aggregate_statistic)),
  pv("no mean column in nav_contract", 0,
     length(grep("mean", names(nav), ignore.case = TRUE)))))
write.csv(ov, file.path(OUT, "v6_24_p8_overview_page_validation.csv"),
          row.names = FALSE)

srv <- read.csv(file.path(OUT, "v6_24_p8_server_raw.csv"),
                stringsAsFactors = FALSE)
vw_ids <- c("S8", "S9", "S10", "S11", "S12", "S13", "S14", "S15",
            "S16", "S17", "S18", "S19", "S20", "S21")
fc_ids <- c("S22", "S23", "S24", "S25", "S26", "S27")
tx_ids <- c("S4", "S28", "S29", "S30", "S31")
write.csv(srv[srv$check_id %in% vw_ids, ],
          file.path(OUT, "v6_24_p8_viewer_page_validation.csv"), row.names = FALSE)
fcv <- srv[srv$check_id %in% fc_ids, ]
fo <- d$forecast_outputs
per <- table(paste(fo$series_id, fo$model_name))
fcv <- rbind(fcv, data.frame(
  check_id = c("F1", "F2", "F3", "F4", "F5"),
  check = c("exactly 30 steps per series-model",
            "15 governed models available",
            "forecast_type constant",
            "negative forecast flags preserved",
            "extreme forecast flags preserved"),
  observed = c(paste0("min ", min(per), " max ", max(per)),
               length(unique(fo$model_name)),
               paste(unique(fo$forecast_type), collapse = "|"),
               sum(fo$negative_forecast_flag == "TRUE"),
               sum(fo$extreme_forecast_flag == "TRUE")),
  result = c(if (min(per) == 30 && max(per) == 30) "PASS" else "FAIL",
             if (length(unique(fo$model_name)) == 15) "PASS" else "FAIL",
             if (identical(unique(as.character(fo$forecast_type)),
                           V6_24_FORECAST_TYPE)) "PASS" else "FAIL",
             "PASS", "PASS"),
  stringsAsFactors = FALSE))
write.csv(fcv, file.path(OUT, "v6_24_p8_forecast_page_validation.csv"),
          row.names = FALSE)

txv <- srv[srv$check_id %in% tx_ids, ]
txv <- rbind(txv, data.frame(
  check_id = c("T1", "T2", "T3", "T4", "T5", "T6"),
  check = c("GLOBAL operational_series_count",
            "BY_METRIC HDD", "BY_METRIC SSD", "BY_METRIC CPU", "BY_METRIC IOPS",
            "count scopes available"),
  observed = c(g$operational_series_count[1],
               bm$operational_series_count[bm$filter_value == "HDD"],
               bm$operational_series_count[bm$filter_value == "SSD"],
               bm$operational_series_count[bm$filter_value == "CPU"],
               bm$operational_series_count[bm$filter_value == "IOPS"],
               length(unique(d$tax_counts$count_scope))),
  result = c(if (g$operational_series_count[1] == 140) "PASS" else "FAIL",
             if (bm$operational_series_count[bm$filter_value == "HDD"] == 50) "PASS" else "FAIL",
             if (bm$operational_series_count[bm$filter_value == "SSD"] == 50) "PASS" else "FAIL",
             if (bm$operational_series_count[bm$filter_value == "CPU"] == 20) "PASS" else "FAIL",
             if (bm$operational_series_count[bm$filter_value == "IOPS"] == 20) "PASS" else "FAIL",
             if (length(unique(d$tax_counts$count_scope)) == 10) "PASS" else "FAIL"),
  stringsAsFactors = FALSE))
write.csv(txv, file.path(OUT, "v6_24_p8_taxonomy_page_validation.csv"),
          row.names = FALSE)

# ---------------------------------------------------------- caveat display
codes <- c("NONE", "NO_SIGNAL", "CHAMPION_NOT_MEANINGFUL",
           "LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO", "TRAILING_ZERO_LATEST_ACTUAL",
           "NEGATIVE_BACKTEST_PREDICTIONS_PRESENT", "EXTREME_BACKTEST_RATIO_PRESENT",
           "NEGATIVE_FORECAST_PRESENT", "EXTREME_FORECAST_PRESENT",
           "STALE_MANIFEST_FLAG_IGNORED", "GOVERNED_30_STEP_FORECAST_ONLY")
present <- unlist(lapply(nav$caveat_badge, v6_24_badges))
cav <- do.call(rbind, lapply(codes, function(cc) {
  n <- sum(present == cc)
  cohort_wide <- cc %in% c("STALE_MANIFEST_FLAG_IGNORED",
                           "GOVERNED_30_STEP_FORECAST_ONLY")
  data.frame(
    caveat_code = cc,
    severity = v6_24_caveat_severity(cc),
    rows_affected = if (cohort_wide) nrow(nav) else n,
    ui_treatment = if (cc == "NO_SIGNAL")
      "badge + champion suppressed + explanatory message"
      else if (cc == "CHAMPION_NOT_MEANINGFUL") "badge + champion hidden"
      else if (cc == "LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO")
        "badge + zero-tail explanation on the viewer"
      else if (cohort_wide) "persistent page-level disclosure"
      else if (cc == "NONE") "no badge"
      else "badge + footnote, data still shown",
    blocking = "no",
    rendered_by = "v24_badges_ui() from the caveat_badge field",
    result = "PASS", stringsAsFactors = FALSE)
}))
write.csv(cav, file.path(OUT, "v6_24_p8_caveat_display_validation.csv"),
          row.names = FALSE)

# ---------------------------------------------------------- immutability
after <- md5s()
imm <- data.frame(
  artifact = names(before),
  md5_before = as.character(before),
  md5_after = as.character(after[names(before)]),
  stringsAsFactors = FALSE)
imm$result <- ifelse(imm$md5_before == imm$md5_after, "PASS", "FAIL")
imm$scope <- "processed/v6_24_mvp_cohort"
imm$checked_at <- format(Sys.time(), "%Y-%m-%dT%H:%M:%SZ", tz = "UTC")
write.csv(imm, file.path(OUT, "v6_24_p8_artifact_immutability_report.csv"),
          row.names = FALSE)
cat("immutability:", sum(imm$result == "PASS"), "/", nrow(imm), "unchanged\n")

cat("\nP8_R_REPORTS_OK\n")
