# V6.24-P8 | headless app smoke test.
# Sources the real app the way app.R does, builds the full UI, and exercises
# the V6.24 page builders. Verifies governed artifacts are byte-identical
# before and after the load.
suppressPackageStartupMessages({
  library(shiny); library(bslib); library(DT); library(plotly)
  library(dplyr); library(readr); library(tidyr)
})
setwd(Sys.getenv("V6_SHINY_DIR", "."))

COHORT <- "../data/processed/v6_24_mvp_cohort"
hash_dir <- function() {
  fs <- list.files(COHORT, full.names = TRUE)
  setNames(vapply(fs, function(f) as.character(tools::md5sum(f)), character(1)),
           basename(fs))
}
before <- hash_dir()
cat("fingerprinted", length(before), "governed artifacts before load\n")

ok <- function(label, cond, detail = "") {
  cat(sprintf("[%s] %-58s %s\n", if (isTRUE(cond)) "PASS" else "FAIL",
              label, detail))
  isTRUE(cond)
}
results <- list()
R <- function(id, label, cond, detail = "") {
  results[[length(results) + 1]] <<- data.frame(
    check_id = id, check = label,
    observed = detail, result = if (isTRUE(cond)) "PASS" else "FAIL",
    stringsAsFactors = FALSE)
  ok(label, cond, detail)
}

cat("\n--- sourcing the app exactly as app.R does ---\n")
src_ok <- tryCatch({
  source("global.R"); source("ui/header.R"); source("ui/body.R")
  source("server/server.R"); TRUE
}, error = function(e) { cat("SOURCE ERROR:", conditionMessage(e), "\n"); FALSE })
R("A1", "app sources without fatal error", src_ok)

cat("\n--- building the full UI ---\n")
ui <- NULL
ui_ok <- tryCatch({ ui <- app_ui(); TRUE },
                  error = function(e) {
                    cat("UI ERROR:", conditionMessage(e), "\n"); FALSE })
R("A2", "app_ui() builds", ui_ok)

html <- if (!is.null(ui)) paste(as.character(ui), collapse = "") else ""
for (s in c("v24_overview", "v24_viewer", "v24_forecast", "v24_taxonomy")) {
  R(paste0("A3_", s), paste("section present in UI:", s),
    grepl(s, html, fixed = TRUE))
}

cat("\n--- V6.24 page builders ---\n")
for (fn in c("section_v24_overview", "section_v24_viewer",
             "section_v24_forecast", "section_v24_taxonomy")) {
  built <- tryCatch({ get(fn)(); TRUE },
                    error = function(e) {
                      cat(fn, "ERROR:", conditionMessage(e), "\n"); FALSE })
  R(paste0("A4_", fn), paste(fn, "builds"), built)
}

cat("\n--- loader ---\n")
d <- v6_24_load_all()
v <- d$validation
R("B1", "loader validation all PASS", all(v$result == "PASS"),
  paste0(sum(v$result == "PASS"), "/", nrow(v)))
R("B2", "nav_contract 140 rows", nrow(d$nav_contract) == 140, nrow(d$nav_contract))
R("B3", "tax_counts 192 rows", nrow(d$tax_counts) == 192, nrow(d$tax_counts))
R("B4", "forecast_outputs 63000 rows", nrow(d$forecast_outputs) == 63000,
  nrow(d$forecast_outputs))
R("B5", "model_rankings 2100 rows", nrow(d$model_rankings) == 2100,
  nrow(d$model_rankings))

cat("\n--- horizon honesty ---\n")
low <- tolower(html)
R("C1", "no '4-year' claim in UI", !grepl("4-year|four-year|4 year", low))
R("C2", "no '1,440' / '1440' horizon claim in UI",
  !grepl("1,440|1440", low))
R("C3", "horizon label present in UI",
  grepl("GOVERNED_30_STEP_DAILY_FORECAST", html, fixed = TRUE))

cat("\n--- read-only source scan ---\n")
srcs <- c(readLines("R/v6_24_read_only_loader.R", warn = FALSE),
          readLines("server/v6_24_mvp_server.R", warn = FALSE),
          readLines("ui/tabs_v6_24_mvp.R", warn = FALSE))
body_txt <- paste(srcs, collapse = "\n")
banned_write <- c("write.csv", "write_csv", "write_parquet", "saveRDS",
                  "file.remove", "unlink(", "writeLines")
found_w <- banned_write[vapply(banned_write,
                               function(p) grepl(p, body_txt, fixed = TRUE),
                               logical(1))]
R("D1", "no write/mutation call in V6.24 code", length(found_w) == 0,
  if (length(found_w)) paste(found_w, collapse = ",") else "none")
banned_compute <- c("lm(", "arima", "forecast(", "auto.arima", "predict(")
found_c <- banned_compute[vapply(banned_compute,
                                 function(p) grepl(p, body_txt, fixed = TRUE),
                                 logical(1))]
R("D2", "no model/forecast call in V6.24 code", length(found_c) == 0,
  if (length(found_c)) paste(found_c, collapse = ",") else "none")
R("D3", "no SQL call in V6.24 code",
  !grepl("DBI::|odbc::|dbConnect|dbGetQuery", body_txt))
# The whole point of P6C/P7 is that suppression is field-driven.
R("D4", "no hardcoded GBRP267 special case",
  !grepl("GBRP267", body_txt, fixed = TRUE))
R("D5", "no hardcoded no-signal series list",
  !grepl("HDD__Basilisk__NA__Forest__apcp150", body_txt, fixed = TRUE))
R("D6", "no mean-based tile in V6.24 code",
  !grepl("mean_wape|mean(", body_txt, fixed = TRUE))

cat("\n--- artifact immutability ---\n")
after <- hash_dir()
same <- identical(before[order(names(before))], after[order(names(after))])
changed <- names(before)[before[names(before)] != after[names(before)]]
R("E1", "governed artifacts byte-identical after load", same,
  if (length(changed)) paste(changed, collapse = ",") else
    paste(length(after), "files unchanged"))

res <- do.call(rbind, results)
np <- sum(res$result == "PASS"); nf <- sum(res$result == "FAIL")
cat(sprintf("\nSMOKE: %d PASS | %d FAIL of %d\n", np, nf, nrow(res)))
write.csv(res, file.path(Sys.getenv("V6_P8_OUT", "."),
                         "v6_24_p8_shiny_smoke_raw.csv"), row.names = FALSE)
if (nf == 0) cat("SMOKE_TEST_APP_OK\n") else cat("SMOKE_TEST_APP_FAILED\n")
