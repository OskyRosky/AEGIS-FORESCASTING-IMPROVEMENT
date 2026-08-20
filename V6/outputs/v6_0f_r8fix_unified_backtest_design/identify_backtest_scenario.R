suppressMessages(library(data.table))
bt <- fread("V6/data/processed/forecast_viewer_model_outputs.csv", showProgress = FALSE)
vw <- fread("V6/outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_viewer_hdd.csv",
            showProgress = FALSE)

b <- unique(bt[, .(key = tolower(series_key), date = as.Date(date), actual_value)])
a <- vw[series_type == "actual" & granularity == "Region",
        .(metric, scenario_ui_label, key = tolower(key),
          date = as.Date(date), value)]

cat("backtest actual points (unique key x date):", nrow(b), "\n")
cat("overlap window:", as.character(max(min(b$date), min(a$date))), "..",
    as.character(min(max(b$date), max(a$date))), "\n\n")

for (s in unique(a[, paste(metric, "|", scenario_ui_label)])) {
  parts <- trimws(strsplit(s, "\\|")[[1]])
  sub <- a[metric == parts[1] & scenario_ui_label == parts[2]]
  j <- merge(b, sub, by = c("key", "date"))
  if (!nrow(j)) { cat(sprintf("%-30s no overlapping rows\n", s)); next }
  d <- abs(j$actual_value - j$value)
  rel <- d / pmax(abs(j$value), 1e-9)
  cat(sprintf("%-30s matched=%6d  exact=%6d (%5.1f%%)  within_1pct=%6d (%5.1f%%)  median_abs_diff=%.4f\n",
              s, nrow(j), sum(d < 1e-6), 100 * mean(d < 1e-6),
              sum(rel < 0.01), 100 * mean(rel < 0.01), median(d)))
}
