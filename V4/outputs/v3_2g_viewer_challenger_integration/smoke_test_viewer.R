# V3.2G smoke test — verify Viewer helpers see the appended challengers.
setwd("c:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V3/shiny_app")
suppressWarnings(suppressMessages(source("global.R")))

cat("=== fvp_data() ===\n")
df <- fvp_data()
cat("rows:", nrow(df), "\n")
cat("families:", paste(sort(unique(df$model_family)), collapse=", "), "\n")
cat("challenger models:",
    paste(sort(unique(df$model_name[df$model_family == "evaluation_challenger"])), collapse=", "), "\n")

cat("\n=== fvp_model_meta('APC-Dedicated') ===\n")
meta <- fvp_model_meta("APC-Dedicated", df)
print(meta[, c("model_name","model_family","is_selected_champion")])

cat("\n=== FVP_FAMILY_ORDER / labels ===\n")
print(FVP_FAMILY_ORDER)
print(FVP_FAMILY_LABELS)

cat("\n=== fvp_forecast_series challenger (ENET-RIDGE, h=5) ===\n")
fs <- fvp_forecast_series("APC-Dedicated", "ENET-RIDGE", 5, 0, df)
cat("rows:", nrow(fs), " range:",
    if (nrow(fs)) paste(min(fs$date), "->", max(fs$date)) else "none", "\n")

cat("\n=== fvp_chart with a challenger selected ===\n")
hc <- tryCatch(
  fvp_chart("APC-Dedicated", c("ETS Explicit", "ENET-RIDGE", "SMLP-TCN"), 5, 0, df),
  error = function(e) { cat("ERROR:", conditionMessage(e), "\n"); NULL })
cat("chart built:", !is.null(hc), " class:", paste(class(hc), collapse="/"), "\n")
cat("n_series in chart:", if (!is.null(hc)) length(hc$x$hc_opts$series) else NA, "\n")

cat("\n=== champion unchanged check ===\n")
cat("champion models (is_selected_champion):",
    paste(sort(unique(df$model_name[df$is_selected_champion %in% c('True', TRUE)])), collapse=", "), "\n")
cat("\nSMOKE TEST DONE\n")
