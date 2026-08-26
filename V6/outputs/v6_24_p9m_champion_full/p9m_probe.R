# P9M | Headless probe of the Champion FULL helpers.
setwd("C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V6/shiny_app")
suppressMessages({
  library(shiny); library(arrow); library(highcharter); library(DT)
  source("R/v6_24_read_only_loader.R"); source("R/v6_24_selection_helpers.R")
  source("R/v6_24_backtest_config_helpers.R"); source("R/v6_24_viz_helpers.R")
  source("R/v6_24_accuracy_helpers.R"); source("R/v6_24_models_full_helpers.R")
  source("R/v6_24_assistant_helpers.R")
})
invisible(capture.output(v6_24_load_all()))
SIG <- "CPU__Consumed__Region__EUR-MSIT"
NOS <- "HDD__Basilisk__NA__Forest__apcp150"

cat("=== A. distribution ===\n")
d <- v6_24_mf_champion_distribution()
cat("models leading:", nrow(d), "| counts sum:", sum(d$series_champion_count), "\n")
cat("shares sum to 1?", isTRUE(all.equal(sum(d$share_of_presentable), 1)), "\n")
print(head(d[, c("model_name","series_champion_count","share_of_presentable")], 4),
      row.names = FALSE)

cat("\n=== B. summary ===\n")
s <- v6_24_mf_champion_summary()
for (k in c("n_series","presentable","suppressed","n_leaders","top_model",
            "top_count","evidence_type","ranking_policy","global_champion","counts_sum")) {
  cat(sprintf("  %-18s %s\n", k, s[[k]]))
}
cat("counts_sum == presentable?", s$counts_sum == s$presentable, "\n")
cat("suppressed excluded (sum != 140)?", s$counts_sum != s$n_series, "\n")

cat("\n=== C. selected series, champion PRESENTABLE ===\n")
x <- v6_24_mf_selected_series_champion(SIG)
cat("label:", x$label, "\n")
cat("presentable:", x$presentable, "| champion:", x$champion_model,
    "| rank:", x$champion_rank, "\n")
cat("ranked by:", x$rank_metric, "=", v6_24_acc_fmt(x$rank_value, 6), "\n")
cat("validity:", x$validity, "| policy:", x$ranking_policy, "\n")

cat("\n=== D. selected series, champion SUPPRESSED ===\n")
y <- v6_24_mf_selected_series_champion(NOS)
cat("label:", y$label, "\n")
cat("presentable:", y$presentable, "<- must be FALSE\n")
cat("signal:", y$signal_quality, "| no_signal:", y$no_signal,
    "| all_zero:", y$all_zero, "\n")
cat("tie-break name still returned:", y$champion_model, "\n")
cat("validity:", y$validity, "\n")

cat("\n=== E. per-series ranking ===\n")
r1 <- v6_24_mf_selected_series_ranking(SIG, 5L)
cat("rows:", nrow(r1), "(expect 5) | top:", r1$model_name[1],
    "rank", r1$rank_within_series[1], "\n")
cat("top is the champion?", r1$model_name[1] == x$champion_model, "\n")
r2 <- v6_24_mf_selected_series_ranking(NOS, 5L)
cat("no-signal rows:", nrow(r2), "| top:", r2$model_name[1], "\n")

cat("\n=== F. policy summary ===\n")
p <- v6_24_mf_champion_policy_summary()
cat("policy:", p$policy, "| primary metrics:",
    paste(p$primary_metrics, collapse=", "), "\n")
cat("presentable:", p$n_presentable, "| suppressed:", p$n_suppressed, "\n")
print(p$validity)

cat("\n=== G. legacy facts ===\n")
L <- v6_24_mf_legacy_champion_facts()
cat("ETS Explicit rows:", L$ets_rows_v624, "| presentable:",
    L$ets_presentable_v624, "| suppressed:", L$ets_suppressed_v624, "\n")
cat("consistent (rows = presentable + suppressed)?",
    L$ets_rows_v624 == L$ets_presentable_v624 + L$ets_suppressed_v624, "\n")

cat("\n=== H. assistant, PRESENTABLE selection ===\n")
e1 <- v6_24_mc_evidence(x)
for (pp in V6_24_MF_CHAMPION_PROMPTS) {
  a <- v6_24_mc_answer(e1, pp$label, pp$intent)
  cat("*", pp$label, "->", a$intent, "\n   ", substr(a$lead, 1, 130), "\n")
  h <- v6_24_mf_validate_no_global_claims(c(a$lead, a$body, a$bullets))
  if (length(h)) cat("   !! FORBIDDEN:", paste(h, collapse=", "), "\n")
}

cat("\n=== I. assistant, SUPPRESSED selection must refuse winner language ===\n")
e2 <- v6_24_mc_evidence(y)
a <- v6_24_mc_answer(e2, "What is the champion for this selected series?")
cat("lead:", a$lead, "\n")
cat("body:", substr(a$body, 1, 210), "\n")
txt <- tolower(paste(a$lead, a$body))
# Check for ASSERTIVE winner language, not the mere presence of the words: the
# correct answer says "must not be read as best, recommended or a winner",
# which a naive scan flags while it is in fact the denial we want.
assertive <- grepl(paste0(
  "\\bis the best\\b|\\bthe winner is\\b|\\bwe recommend\\b|",
  "\\bis recommended\\b|\\brecommended model is\\b|\\bbest model is\\b"), txt)
cat("asserts best/winner/recommended? ", assertive, "<- TRUE would be a BUG\n")
cat("explicitly denies it? ",
    grepl("must not be read as best", txt), "\n")
cat("says no presentable champion? ",
    grepl("no presentable champion", txt), "\n")

cat("\n=== J. refusals ===\n")
for (q in c("Why did demand increase because of a business event?",
            "Should we buy more capacity?")) {
  aa <- v6_24_mc_answer(e1, q)
  cat("*", substr(q,1,42), "->", aa$intent, "| bounded:", aa$bounded, "\n")
}

cat("\n=== K. intent routing ===\n")
qs <- list(c("Summarize Champion FULL","mc_summary"),
           c("Which model leads the most series?","mc_leads"),
           c("What is the champion for this selected series?","mc_selected"),
           c("Why is there no global champion?","mc_no_global"),
           c("Why are no-signal series suppressed?","mc_no_signal"),
           c("What changed from the old HDD Champion page?","mc_changed"),
           c("What should I tell a stakeholder?","mc_stakeholder"),
           c("should we buy more capacity?","unsupported_action"))
bad <- 0L
for (pp in qs) {
  g <- v6_24_mc_intent(pp[[1]]); okk <- identical(g, pp[[2]])
  if (!okk) bad <- bad + 1L
  cat(sprintf("  [%s] %-46s -> %s\n", if(okk)"OK " else "BAD",
              substr(pp[[1]],1,46), g))
}
cat("\nROUTING MISMATCHES:", bad, "\n")
cat("\nPROBE COMPLETE\n")
