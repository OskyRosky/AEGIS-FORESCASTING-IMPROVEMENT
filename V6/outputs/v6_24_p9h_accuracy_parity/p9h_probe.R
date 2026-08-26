# P9H | Headless probe: accuracy scoped to ONE selected series.
setwd("C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V6/shiny_app")
suppressMessages({
  library(shiny); library(arrow); library(highcharter); library(DT)
  source("R/v6_24_read_only_loader.R"); source("R/v6_24_selection_helpers.R")
  source("R/v6_24_backtest_config_helpers.R"); source("R/v6_24_viz_helpers.R")
  source("R/v6_24_accuracy_helpers.R"); source("R/v6_24_assistant_helpers.R")
})
invisible(capture.output(v6_24_load_all()))

SIG <- "CPU__Consumed__Region__EUR-MSIT"
NOS <- "HDD__Basilisk__NA__Forest__apcp150"

cat("=== A. scoped to ONE series ===\n")
r <- v6_24_acc_rows("MAE", V6_24_GOVERNED_MODELS, SIG)
cat("rows:", nrow(r), "(expect 15 = one per governed model)\n")
cat("distinct series:", length(unique(r$series_id)), "\n")

cat("\n=== B. values COPIED from the artifact ===\n")
ac <- v6_24_tbl("accuracy_metrics")
src <- ac[ac$series_id == SIG & ac$model_name == r$model_name[1], ]
cat("metric_value == artifact mae? ",
    identical(as.numeric(r$metric_value[1]), as.numeric(src$mae)), "\n")

cat("\n=== C. summary is per-series: best / weakest MODEL ===\n")
s <- v6_24_acc_summary(r, "MAE")
cat("series:", s$series_label, "\n")
cat("models:", s$n_models, "| target dates:", s$target_dates, "\n")
cat("best   :", s$best, "=", v6_24_acc_fmt(s$best_value), "\n")
cat("weakest:", s$worst, "=", v6_24_acc_fmt(s$worst_value), "\n")
cat("champion:", s$champion, "| visible:", s$champion_visible, "\n")
cat("excluded:", s$excluded, "| extreme:", s$extreme, "| no_signal:", s$no_signal, "\n")

cat("\n=== D. NO-SIGNAL series gets NO best model ===\n")
rn <- v6_24_acc_rows("MAE", V6_24_GOVERNED_MODELS, NOS)
sn <- v6_24_acc_summary(rn, "MAE")
cat("series:", sn$series_label, "| no_signal:", sn$no_signal, "\n")
cat("best   :", sn$best, "\n")
cat("weakest:", sn$worst, "\n")
cat("best_value is NA (not 0)? ", is.na(sn$best_value), "\n")
cat("names a real model as best? ", sn$best %in% V6_24_GOVERNED_MODELS,
    "<- TRUE would be a BUG\n")

cat("\n=== E. metric switch reorders models ===\n")
for (m in c("MAE","RMSE","WAPE","SMAPE")) {
  rr <- v6_24_acc_rows(m, V6_24_GOVERNED_MODELS, SIG)
  ss <- v6_24_acc_summary(rr, m)
  cat(sprintf("  %-6s best=%-18s (%s)  excluded=%d\n", m, ss$best,
              v6_24_acc_fmt(ss$best_value), ss$excluded))
}

cat("\n=== F. heatmap is models x measures ===\n")
hm <- v6_24_acc_heatmap(r, "MAE")
cat("chart type:", hm$x$hc_opts$chart$type, "\n")
cat("y (models):", length(hm$x$hc_opts$yAxis$categories),
    "| x (measures):", length(hm$x$hc_opts$xAxis$categories), "\n")
cat("measures:", paste(unlist(hm$x$hc_opts$xAxis$categories), collapse=", "), "\n")
cat("cells:", length(hm$x$hc_opts$series[[1]]$data),
    "(expect", length(hm$x$hc_opts$yAxis$categories) *
      length(hm$x$hc_opts$xAxis$categories), ")\n")
cat("exporting:", isTRUE(hm$x$hc_opts$exporting$enabled),
    "| colorAxis:", !is.null(hm$x$hc_opts$colorAxis), "\n")

cat("\n=== G. table is one row per model ===\n")
tb <- v6_24_acc_table(r, "MAE")
cat("rows:", nrow(tb$x$data), "| cols:", paste(names(tb$x$data), collapse=", "), "\n")

cat("\n=== H. assistant, signal-present ===\n")
cfg <- list(metric="MAE", models=V6_24_GOVERNED_MODELS, series_id=SIG,
            label="CPU / EUR-MSIT")
e <- v6_24_accuracy_evidence(cfg, r)
for (p in V6_24_ACCURACY_PROMPTS) {
  a <- v6_24_accuracy_answer(e, p$label, p$intent)
  cat("*", p$label, "->", a$intent, "\n   ", substr(a$lead, 1, 130), "\n")
}

cat("\n=== I. assistant, NO-SIGNAL must refuse a best model ===\n")
en <- v6_24_accuracy_evidence(list(metric="MAE", models=V6_24_GOVERNED_MODELS,
                                   series_id=NOS, label="HDD / apcp150"), rn)
a <- v6_24_accuracy_answer(en, "Which models look strongest?")
cat("lead:", a$lead, "\n")
cat("body:", substr(a$body, 1, 190), "\n")
txt <- tolower(paste(a$lead, a$body))
cat("claims a strongest model? ",
    grepl("is strongest|is the best|has the lowest", txt),
    "<- TRUE would be a BUG\n")

cat("\n=== J. refusals still work ===\n")
for (q in c("Why did demand increase because of a business event?",
            "Should we buy more capacity?")) {
  aa <- v6_24_accuracy_answer(e, q)
  cat("*", substr(q,1,45), "->", aa$intent, "| bounded:", aa$bounded, "\n")
}

cat("\n=== K. intent routing ===\n")
qs <- list(c("Summarize the accuracy view","acc_summary"),
           c("Which models look strongest?","acc_models"),
           c("Where are the largest errors?","acc_worst"),
           c("Explain the heatmap","acc_heatmap"),
           c("Explain the caveats","acc_caveats"),
           c("What should I tell a stakeholder?","acc_stakeholder"),
           c("Why is there no horizon filter?","acc_horizon"),
           c("should we buy more capacity?","unsupported_action"),
           c("what caused the spike?","unsupported_cause"))
bad <- 0L
for (p in qs) {
  g <- v6_24_accuracy_intent(p[[1]]); ok <- identical(g,p[[2]])
  if(!ok) bad <- bad+1L
  cat(sprintf("  [%s] %-40s -> %s\n", if(ok)"OK " else "BAD", substr(p[[1]],1,40), g))
}
cat("\nROUTING MISMATCHES:", bad, "\n")
cat("\nPROBE COMPLETE\n")
