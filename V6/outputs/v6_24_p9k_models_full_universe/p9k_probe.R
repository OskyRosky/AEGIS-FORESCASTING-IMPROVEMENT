# P9K | Headless probe of the Models FULL Universe helpers.
setwd("C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V6/shiny_app")
suppressMessages({
  library(shiny); library(arrow); library(highcharter); library(DT)
  source("R/v6_24_read_only_loader.R"); source("R/v6_24_selection_helpers.R")
  source("R/v6_24_backtest_config_helpers.R"); source("R/v6_24_viz_helpers.R")
  source("R/v6_24_accuracy_helpers.R"); source("R/v6_24_models_full_helpers.R")
  source("R/v6_24_assistant_helpers.R")
})
invisible(capture.output(v6_24_load_all()))

cat("=== A. model list comes from the ARTIFACT ===\n")
v <- v6_24_mf_validate_model_list()
cat("artifact models:", v$n_artifact, "| registry:", v$n_registry, "\n")
cat("missing:", if (length(v$missing)) paste(v$missing, collapse=", ") else "none", "\n")
cat("extra  :", if (length(v$extra)) paste(v$extra, collapse=", ") else "none", "\n")
cat("exactly 15, none missing, none extra? ", v$ok, "\n")

cat("\n=== B. family map: 4 display + governed 3-valued ===\n")
fm <- v6_24_mf_family_map()
cat("rows:", nrow(fm), "\n")
print(table(fm$display_family))
print(table(fm$governed_family))
cat("\ncross-cutting proof (display vs governed):\n")
x <- fm[fm$model_name %in% c("ETS Explicit","LinearRegression","FNAR-V2"), ]
print(x[, c("model_name","display_family","governed_family")], row.names = FALSE)

cat("\n=== C. universe summary ===\n")
s <- v6_24_mf_universe_summary()
for (k in c("n_models","n_series","n_rows","n_metrics","champion_visible",
            "champion_suppressed","distinct_winners")) {
  cat(sprintf("  %-22s %s\n", k, s[[k]]))
}

cat("\n=== D. universe table: one row per model, medians ===\n")
tb <- v6_24_mf_universe_table()
cat("rows:", nrow(tb), "| cols:", paste(names(tb), collapse=", "), "\n")
print(head(tb[, c("model_name","display_family","median_mae","median_wape",
                  "series_champion_count")], 5), row.names = FALSE)

cat("\n=== E. medians match an INDEPENDENT recomputation ===\n")
ac <- v6_24_tbl("accuracy_metrics")
ok <- TRUE
for (m in head(tb$model_name, 4)) {
  d <- ac[ac$model_name == m, ]
  mine <- tb$median_mae[tb$model_name == m]
  theirs <- median(suppressWarnings(as.numeric(d$mae)), na.rm = TRUE)
  match <- isTRUE(all.equal(mine, theirs))
  if (!match) ok <- FALSE
  cat(sprintf("  %-18s helper=%.4f  recomputed=%.4f  %s\n", m, mine, theirs,
              if (match) "MATCH" else "MISMATCH"))
}
cat("all match? ", ok, "\n")

cat("\n=== F. medians are NOT means ===\n")
m1 <- tb$median_mae[tb$model_name == "LinearRegression"]
mu <- mean(suppressWarnings(as.numeric(ac$mae[ac$model_name=="LinearRegression"])), na.rm=TRUE)
cat(sprintf("  LinearRegression median=%.2f  mean=%.4g  -> helper uses %s\n",
            m1, mu, if (abs(m1-mu) > 1) "MEDIAN" else "MEAN (BUG)"))

cat("\n=== G. champion counts are series-level and gated ===\n")
ch <- v6_24_mf_champion_counts()
cat("models with >=1 series:", nrow(ch), "| total counted:", sum(ch$series_champion_count), "\n")
cat("equals champion_visible (", s$champion_visible, ")? ",
    sum(ch$series_champion_count) == s$champion_visible, "\n")
print(head(ch, 5), row.names = FALSE)
nav <- v6_24_tbl("nav_contract")
cat("ETS Explicit: champion_model_name rows =",
    sum(nav$champion_model_name == "ETS Explicit"),
    "| presentable =", ch$series_champion_count[ch$model_name=="ETS Explicit"], "\n")

cat("\n=== H. forbidden-claim guard ===\n")
bad <- c("ETS Explicit is the champion", "median MASE 6.90", "head-to-head record")
cat("guard on a bad string ->",
    paste(v6_24_mf_validate_no_global_claims(bad), collapse=" | "), "\n")
good <- c("cohort diagnostic medians", "series-level champion count",
          "not a head-to-head tournament")
cat("guard on approved wording ->",
    if (!length(v6_24_mf_validate_no_global_claims(good))) "clean" else "FLAGGED", "\n")

cat("\n=== I. assistant ===\n")
e <- v6_24_mf_evidence()
for (p in V6_24_MF_UNIVERSE_PROMPTS) {
  a <- v6_24_mf_answer(e, p$label, p$intent)
  cat("*", p$label, "->", a$intent, "\n   ", substr(a$lead, 1, 140), "\n")
  hits <- v6_24_mf_validate_no_global_claims(c(a$lead, a$body, a$bullets))
  if (length(hits)) cat("   !! FORBIDDEN:", paste(hits, collapse=", "), "\n")
}

cat("\n=== J. assistant refusals ===\n")
for (q in c("Why did demand increase because of a business event?",
            "Should we buy more capacity?")) {
  a <- v6_24_mf_answer(e, q)
  cat("*", substr(q,1,44), "->", a$intent, "| bounded:", a$bounded, "\n")
}

cat("\n=== K. intent routing ===\n")
qs <- list(c("Summarize the model universe","mf_summary"),
           c("Explain the model families","mf_families"),
           c("Which models look strongest by cohort medians?","mf_strongest"),
           c("Why is this not a tournament?","mf_not_tournament"),
           c("What changed from the old HDD model section?","mf_changed"),
           c("What should I tell a stakeholder?","mf_stakeholder"),
           c("should we buy more capacity?","unsupported_action"))
bad2 <- 0L
for (p in qs) {
  g <- v6_24_mf_intent(p[[1]]); okk <- identical(g,p[[2]])
  if(!okk) bad2 <- bad2+1L
  cat(sprintf("  [%s] %-46s -> %s\n", if(okk)"OK " else "BAD", substr(p[[1]],1,46), g))
}
cat("\nROUTING MISMATCHES:", bad2, "\n")
cat("\nPROBE COMPLETE\n")
