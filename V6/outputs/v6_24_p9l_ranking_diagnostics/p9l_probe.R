# P9L | Headless probe of the Ranking Diagnostics helpers.
setwd("C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V6/shiny_app")
suppressMessages({
  library(shiny); library(arrow); library(highcharter); library(DT)
  source("R/v6_24_read_only_loader.R"); source("R/v6_24_selection_helpers.R")
  source("R/v6_24_backtest_config_helpers.R"); source("R/v6_24_viz_helpers.R")
  source("R/v6_24_accuracy_helpers.R"); source("R/v6_24_models_full_helpers.R")
  source("R/v6_24_assistant_helpers.R")
})
invisible(capture.output(v6_24_load_all()))

cat("=== A. metrics offered are governed columns only ===\n")
cat("labels:", paste(V6_24_MF_RANK_METRIC_LABELS, collapse=", "), "\n")
ac <- v6_24_tbl("accuracy_metrics")
cols <- vapply(V6_24_MF_RANK_METRICS, function(m) m$col, character(1))
cat("all columns exist in accuracy_metrics? ", all(cols %in% names(ac)), "\n")
cat("any MASE/RMSSE offered? ",
    any(grepl("mase|rmsse", tolower(V6_24_MF_RANK_METRIC_LABELS))), "<- TRUE would be a BUG\n")

cat("\n=== B. ranking rows: one per model, All family ===\n")
r <- v6_24_mf_ranking_rows("MAE", "All", "metric_asc")
cat("rows:", nrow(r), "(expect 15)\n")
cat("cols:", paste(names(r), collapse=", "), "\n")
print(head(r[, c("diagnostic_position","model_name","median_selected",
                 "series_champion_count")], 5), row.names=FALSE)

cat("\n=== C. medians match an independent recomputation ===\n")
ok <- TRUE
for (m in head(r$model_name, 4)) {
  mine <- r$median_selected[r$model_name==m]
  theirs <- median(suppressWarnings(as.numeric(ac$mae[ac$model_name==m])), na.rm=TRUE)
  eq <- isTRUE(all.equal(mine, theirs)); if (!eq) ok <- FALSE
  cat(sprintf("  %-18s helper=%.4f recomputed=%.4f %s\n", m, mine, theirs,
              if (eq) "MATCH" else "MISMATCH"))
}
cat("all match? ", ok, "\n")

cat("\n=== D. metric switch reorders; no single answer ===\n")
for (mm in c("MAE","RMSE","WAPE","SMAPE")) {
  rr <- v6_24_mf_ranking_rows(mm, "All", "metric_asc")
  s <- v6_24_mf_ranking_summary(rr, mm)
  cat(sprintf("  %-6s lowest median=%-18s | most series led=%-18s | agree=%s\n",
              mm, s$best_median_model, s$most_champ_model, s$agree))
}

cat("\n=== E. family filter ===\n")
for (f in c("All", unname(V6_24_FAMILY_LABEL))) {
  rr <- v6_24_mf_ranking_rows("MAE", f, "metric_asc")
  cat(sprintf("  %-18s rows=%d\n", f, nrow(rr)))
}

cat("\n=== F. sort options change the order ===\n")
for (sb in V6_24_MF_SORT_OPTIONS) {
  rr <- v6_24_mf_ranking_rows("MAE", "All", sb)
  cat(sprintf("  %-12s top3: %s\n", sb,
              paste(head(rr$model_name,3), collapse=" > ")))
}

cat("\n=== G. champion counts sum to presentable series ===\n")
ch <- v6_24_mf_champion_count_rows()
s <- v6_24_mf_universe_summary()
cat("models:", nrow(ch), "| sum:", sum(ch$series_champion_count),
    "| champion_visible:", s$champion_visible, "\n")
cat("sums to presentable? ", sum(ch$series_champion_count)==s$champion_visible, "\n")
cat("no-signal excluded (sum != 140)? ", sum(ch$series_champion_count) != 140, "\n")
cat("share column sums to ~1? ",
    isTRUE(all.equal(sum(r$series_champion_share), 1)), "\n")

cat("\n=== H. metric disagreement is real ===\n")
d <- v6_24_mf_metric_disagreement_rows()
cat("rows:", nrow(d), "\n")
print(head(d[, c("model_name","MAE","RMSE","WAPE","SMAPE","position_spread")], 6),
      row.names=FALSE)
cat("max spread:", max(d$position_spread, na.rm=TRUE),
    "-> metrics disagree? ", max(d$position_spread, na.rm=TRUE) > 0, "\n")

cat("\n=== I. assistant ===\n")
cfg <- list(metric="MAE", family="All", sort_by="metric_asc", stamp="x")
e <- v6_24_mr_evidence(cfg, r)
for (p in V6_24_MF_RANKING_PROMPTS) {
  a <- v6_24_mr_answer(e, p$label, p$intent)
  cat("*", p$label, "->", a$intent, "\n   ", substr(a$lead, 1, 135), "\n")
  hits <- v6_24_mf_validate_no_global_claims(c(a$lead, a$body, a$bullets))
  if (length(hits)) cat("   !! FORBIDDEN:", paste(hits, collapse=", "), "\n")
}

cat("\n=== J. refusals ===\n")
for (q in c("Why did demand increase because of a business event?",
            "Should we buy more capacity?")) {
  a <- v6_24_mr_answer(e, q)
  cat("*", substr(q,1,42), "->", a$intent, "| bounded:", a$bounded, "\n")
}

cat("\n=== K. intent routing ===\n")
qs <- list(c("Summarize the ranking diagnostics","mr_summary"),
           c("Which model has the best diagnostic median?","mr_best"),
           c("Which model leads the most series?","mr_leads"),
           c("Why is this not a tournament?","mr_not_tournament"),
           c("Why is there no global champion?","mr_no_global"),
           c("What changed from the old HDD Tournament?","mr_changed"),
           c("What should I tell a stakeholder?","mr_stakeholder"),
           c("should we buy more capacity?","unsupported_action"))
bad <- 0L
for (p in qs) {
  g <- v6_24_mr_intent(p[[1]]); okk <- identical(g,p[[2]])
  if(!okk) bad <- bad+1L
  cat(sprintf("  [%s] %-44s -> %s\n", if(okk)"OK " else "BAD", substr(p[[1]],1,44), g))
}
cat("\nROUTING MISMATCHES:", bad, "\n")
cat("\nPROBE COMPLETE\n")
