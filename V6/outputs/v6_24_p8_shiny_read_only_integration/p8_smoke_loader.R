# V6.24-P8 | headless smoke test: loader + filter flow + page builders.
# Runs outside Shiny's reactive context so it can be executed by Rscript.
suppressPackageStartupMessages({
  library(readr); library(dplyr)
})
setwd(Sys.getenv("V6_SHINY_DIR", "."))
source("R/v6_24_read_only_loader.R")

d <- v6_24_load_all()
v <- d$validation
cat("LOADER checks:", nrow(v), " PASS:", sum(v$result == "PASS"),
    " FAIL:", sum(v$result == "FAIL"), "\n")
if (any(v$result == "FAIL")) print(v[v$result == "FAIL", ])

cat("\nrows loaded:\n")
for (n in c("nav_contract", "tax_counts", "forecast_outputs", "model_rankings",
            "accuracy_metrics", "signal_quality", "actuals", "backtests")) {
  cat(sprintf("  %-18s %9d\n", n, nrow(d[[n]])))
}
cat("\nloader ok:", d$ok, "\n")

cat("\nFILTER FLOW\n")
cat("  metric options:", paste(v6_24_axis_options("metric"), collapse = ", "), "\n")
cat("  db_type | HDD :", paste(v6_24_axis_options("db_type", list(metric = "HDD")),
                               collapse = ", "), "\n")
cat("  scenario| CPU :", paste(v6_24_axis_options("scenario", list(metric = "CPU")),
                               collapse = ", "), "\n")

# Walk every full path and confirm it resolves to exactly one series.
nav <- v6_24_operational()
bad <- 0L
for (i in seq_len(nrow(nav))) {
  ch <- as.list(setNames(as.character(unlist(nav[i, V6_24_FILTER_AXES])),
                         V6_24_FILTER_AXES))
  if (nrow(v6_24_resolve(ch)) != 1L) bad <- bad + 1L
}
cat("  full paths resolving to exactly one series:", nrow(nav) - bad, "/", nrow(nav), "\n")

# Confirm no reachable option is empty at any depth.
empty <- 0L
for (depth in seq_along(V6_24_FILTER_AXES)) {
  axis <- V6_24_FILTER_AXES[depth]
  parents <- unique(nav[, V6_24_FILTER_AXES[seq_len(depth - 1)], drop = FALSE])
  if (depth == 1L) parents <- data.frame(x = 1)
  for (j in seq_len(nrow(parents))) {
    ch <- if (depth == 1L) list() else
      as.list(setNames(as.character(unlist(parents[j, , drop = FALSE])),
                       V6_24_FILTER_AXES[seq_len(depth - 1)]))
    for (opt in v6_24_axis_options(axis, ch)) {
      ch2 <- ch; ch2[[axis]] <- opt
      if (nrow(v6_24_resolve(ch2)) == 0L) empty <- empty + 1L
    }
  }
}
cat("  reachable options with zero series:", empty, "\n")

cat("\nCONTRACT FIELDS\n")
cat("  champion_visible TRUE :", sum(nav$champion_visible == "TRUE"), "\n")
cat("  champion_visible FALSE:", sum(nav$champion_visible == "FALSE"), "\n")
cat("  no-signal series      :", sum(nav$signal_quality_status == V6_24_NO_SIGNAL), "\n")
cat("  low-confidence series :",
    sum(nav$low_confidence_backtest_window_flag == "TRUE"), "\n")
cat("  AVAILABLE             :", sum(nav$product_status == "AVAILABLE"), "\n")
cat("  AVAILABLE_WITH_CAVEAT :", sum(nav$product_status == "AVAILABLE_WITH_CAVEAT"), "\n")

# Champion suppression must follow the field, never a hardcoded list.
ns <- nav[nav$signal_quality_status == V6_24_NO_SIGNAL, ]
cat("  no-signal rows with champion_visible TRUE (must be 0):",
    sum(ns$champion_visible == "TRUE"), "\n")

cat("\nFORECAST\n")
fo <- d$forecast_outputs
per <- table(paste(fo$series_id, fo$model_name))
cat("  steps per series-model: min", min(per), "max", max(per), "\n")
cat("  distinct forecast_type:", paste(unique(fo$forecast_type), collapse = "|"), "\n")
cat("  governed models       :", length(unique(fo$model_name)), "\n")
cat("  negative flags kept   :", sum(fo$negative_forecast_flag == "TRUE"), "\n")
cat("  extreme flags kept    :", sum(fo$extreme_forecast_flag == "TRUE"), "\n")

cat("\nTAXONOMY\n")
g <- v6_24_tax_scope("GLOBAL")
cat("  GLOBAL operational_series_count:", g$operational_series_count[1], "\n")
bm <- v6_24_tax_scope("BY_METRIC")
for (i in seq_len(nrow(bm))) {
  cat(sprintf("  %-6s %3d\n", bm$filter_value[i], bm$operational_series_count[i]))
}
cat("  scopes:", length(unique(d$tax_counts$count_scope)), "\n")

cat("\nSMOKE_TEST_LOADER_OK\n")
