suppressMessages(library(data.table))
bt <- fread("V6/data/processed/forecast_viewer_model_outputs.csv", showProgress = FALSE)
vw <- fread("V6/outputs/v6_0f_r6_phase1_governed_extraction/r6_phase1_viewer_hdd.csv",
            showProgress = FALSE)

bt_keys <- sort(unique(bt$series_key))
cat("backtest series:", length(bt_keys), "\n")

cat("\n--- overlap of the 39 backtest series against each Tesseract combination ---\n")
combos <- unique(vw[, .(metric, scenario_ui_label, granularity)])
for (i in seq_len(nrow(combos))) {
  k <- unique(vw[metric == combos$metric[i] &
                 scenario_ui_label == combos$scenario_ui_label[i] &
                 granularity == combos$granularity[i], key])
  hit <- sum(tolower(bt_keys) %in% tolower(k))
  cat(sprintf("%-15s %-11s %-7s keys=%4d  matched %2d/%d backtest series\n",
              combos$metric[i], combos$scenario_ui_label[i], combos$granularity[i],
              length(k), hit, length(bt_keys)))
}

cat("\n--- actual points available per combination (input for new backtests) ---\n")
a <- vw[series_type == "actual",
        .(actual_rows = .N, keys = uniqueN(key),
          first = min(date), last = max(date)),
        by = .(metric, scenario_ui_label, granularity)]
setorder(a, metric, scenario_ui_label, granularity)
print(a)
cat("\ntotal actual rows:", sum(a$actual_rows), " total key-combos:", sum(a$keys), "\n")

cat("\n--- current artifact shape ---\n")
cat("rows per model:", nrow(bt) / uniqueN(bt$model_name), "\n")
cat("origins:", uniqueN(bt$forecast_start_date), " horizons:", uniqueN(bt$horizon_days), "\n")
cat("rows per series per model:", round(nrow(bt) / uniqueN(bt$series_key) /
                                        uniqueN(bt$model_name), 1), "\n")
