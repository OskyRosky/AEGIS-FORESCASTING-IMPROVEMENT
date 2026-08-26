# P9G | Headless probe of the evidence builder and composer.
# Runs outside Shiny so a failure is a code failure, not a UI failure.
setwd("C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V6/shiny_app")
suppressMessages({
  library(shiny); library(arrow); library(highcharter)
  source("R/v6_24_read_only_loader.R")
  source("R/v6_24_selection_helpers.R")
  source("R/v6_24_backtest_config_helpers.R")
  source("R/v6_24_viz_helpers.R")
  source("R/v6_24_assistant_helpers.R")
})
invisible(capture.output(v6_24_load_all()))

sig_ok <- "CPU__Consumed__Region__EUR-MSIT"
no_sig <- "HDD__Basilisk__NA__Forest__apcp150"

cat("=== A. evidence for a signal-present series ===\n")
e <- v6_24_evidence(sig_ok, list(series = sig_ok,
                                 models = v6_24_default_models(sig_ok),
                                 horizon = 5L))
cat("groups:", paste(names(e), collapse = ", "), "\n")
cat("final_axis_label:", e$selection$final_axis_label, "\n")
cat("champion_visible:", e$selection$champion_visible,
    "| champion:", e$champion$model, "\n")
cat("obs:", e$signal$observation_count, e$signal$actual_min_date, "->",
    e$signal$actual_max_date, "\n")
cat("bt rows:", e$backtest$rows, "horizon:", e$backtest$horizon,
    e$backtest$date_min, "->", e$backtest$date_max, "\n")
cat("fc steps contract/drawn:", e$forecast$steps_contract, "/",
    e$forecast$steps_drawn, "| model:", e$forecast$model,
    "| is_champ:", e$forecast$model_is_champion, "\n")
cat("caveat codes:", paste(e$caveats$codes, collapse = "|"), "\n")
cat("taxonomy series:", e$taxonomy$series, "\n\n")

show <- function(a) {
  cat("  intent:", a$intent, "| bounded:", a$bounded, "\n")
  cat("  LEAD:", substr(a$lead, 1, 200), "\n")
  if (nzchar(a$body)) cat("  BODY:", substr(a$body, 1, 240), "\n")
  if (length(a$bullets)) cat("  BULLETS:", length(a$bullets), "\n")
  cat("  USED:", paste(a$used, collapse = ","), "\n\n")
}

cat("=== B. quick prompts, signal-present ===\n")
for (p in V6_24_VIEWER_PROMPTS) {
  cat("*", p$label, "\n"); show(v6_24_assistant_answer(e, p$label, p$intent))
}

cat("=== C. no-signal series: winner must be refused ===\n")
e2 <- v6_24_evidence(no_sig, NULL)
a2 <- v6_24_assistant_answer(e2, "Which model is winning?")
show(a2)
txt2 <- tolower(paste(a2$lead, a2$body, paste(a2$bullets, collapse = " ")))
cat("  contains 'winner'/'best' claim? ",
    grepl("is the best|the winner is|recommended model is", txt2), "\n")
cat("  says no winner? ", grepl("no model can be presented as a winner", txt2), "\n\n")

cat("=== D. horizon question ===\n")
a3 <- v6_24_assistant_answer(e, "Is this a 4-year forecast?")
show(a3)
# A naive scan for "4-year" flags the DISCLAIMER, not a claim. Test the two
# things that actually matter: the answer states the governed 30 steps, and it
# explicitly denies a longer horizon.
h_txt <- paste(a3$lead, a3$body)
cat("  states 30 steps? ", grepl("30-step|30 steps|30 daily", h_txt), "\n")
cat("  denies longer horizon? ",
    grepl("no longer governed horizon|never produced|inventing data", h_txt), "\n")
cat("  asserts a long horizon? ",
    grepl("is a 4-year forecast|forecasts 1,?440 days|covers 4 years", h_txt), "\n\n")

cat("=== E. unsupported causal question ===\n")
a4 <- v6_24_assistant_answer(e, "Why did demand increase because of a business event?")
show(a4)

cat("=== F. unsupported action question ===\n")
a5 <- v6_24_assistant_answer(e, "Should we buy more capacity?")
show(a5)

cat("=== G. forecast prompts ===\n")
for (p in V6_24_FORECAST_PROMPTS) {
  cat("*", p$label, "\n"); show(v6_24_assistant_answer(e, p$label, p$intent))
}

cat("=== H. no selection ===\n")
show(v6_24_assistant_answer(NULL, "anything"))

cat("=== I. intent routing table ===\n")
# Each case carries its EXPECTED intent so the probe fails loudly instead of
# printing a table a reader has to check by eye.
qs <- list(
  c("Summarize the selected series", "summary"),
  c("which model is winning?", "champion"),
  c("What is the recommended model?", "champion"),
  c("explain the caveats", "caveats"),
  c("what should I pay attention to?", "attention"),
  c("Is this series safe to interpret?", "risk"),
  c("are there negative or extreme values?", "flags"),
  c("Why is this only a 30-step forecast?", "horizon"),
  c("Is this a 4-year forecast?", "horizon"),
  c("what should I tell a stakeholder?", "stakeholder"),
  c("Summarize the forecast", "forecast"),
  c("Explain the backtest", "backtest"),
  c("Explain the model ranking", "ranking"),
  c("why did demand increase because of a business event?", "unsupported_cause"),
  c("what caused the spike?", "unsupported_cause"),
  c("should we buy more capacity?", "unsupported_action"),
  c("Should I invest in more storage?", "unsupported_action"),
  c("is this production ready?", "unsupported_action"),
  c("how is the weather today?", "unsupported"))
n_bad <- 0L
for (p in qs) {
  got <- v6_24_assistant_intent(p[[1]])
  ok <- identical(got, p[[2]])
  if (!ok) n_bad <- n_bad + 1L
  cat(sprintf("  [%s] %-54s -> %-20s (want %s)\n",
              if (ok) "OK " else "BAD", substr(p[[1]], 1, 54), got, p[[2]]))
}
cat("\nROUTING MISMATCHES:", n_bad, "\n")
cat("\nPROBE COMPLETE\n")
