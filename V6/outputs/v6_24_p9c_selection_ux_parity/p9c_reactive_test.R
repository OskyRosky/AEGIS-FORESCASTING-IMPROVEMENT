# V6.24-P9C | reactive validation of the progressive selection.
suppressPackageStartupMessages({
  library(shiny); library(bslib); library(DT); library(plotly)
  library(dplyr); library(readr); library(tidyr)
})
setwd(Sys.getenv("V6_SHINY_DIR", "."))
source("global.R")

res <- list()
R <- function(id, label, cond, detail = "") {
  res[[length(res) + 1]] <<- data.frame(
    check_id = id, check = label, observed = as.character(detail),
    result = if (isTRUE(cond)) "PASS" else "FAIL", stringsAsFactors = FALSE)
  cat(sprintf("[%s] %-58s %s\n", if (isTRUE(cond)) "PASS" else "FAIL",
              label, detail))
}

nav <- v6_24_operational()

# ---- pure helper checks (no reactive context needed)
p0 <- v6_24_selection_plan(list())
R("H1", "metric is the only open control before any choice",
  p0$plan$metric$state == "CHOICE" &&
    all(vapply(V6_24_FILTER_AXES[-1], function(a) p0$plan[[a]]$state == "LOCKED",
               logical(1))),
  paste(vapply(V6_24_FILTER_AXES, function(a) p0$plan[[a]]$state, character(1)),
        collapse = "/"))
R("H2", "metric offers exactly the governed metrics",
  identical(sort(p0$plan$metric$values), c("CPU", "HDD", "IOPS", "SSD")),
  paste(p0$plan$metric$values, collapse = ","))

# HDD: db_type discriminates (Basilisk/EDB); scenario is a single NA token
ph <- v6_24_selection_plan(list(metric = "HDD"))
R("H3", "HDD opens DB Type as a real choice",
  ph$plan$db_type$state == "CHOICE" &&
    identical(sort(ph$plan$db_type$values), c("Basilisk", "EDB")),
  paste(ph$plan$db_type$values, collapse = ","))

# IOPS: db_type is NOT_APPLICABLE -> must be CONTEXT, not a dropdown
pi <- v6_24_selection_plan(list(metric = "IOPS"))
R("H4", "IOPS shows DB Type as context, not a dropdown",
  pi$plan$db_type$state == "CONTEXT" && isTRUE(pi$plan$db_type$conditional),
  paste0(pi$plan$db_type$state, " / ", pi$plan$db_type$selected))
R("H5", "IOPS auto-resolves past the non-discriminating axis to Scenario",
  pi$plan$scenario$state == "CHOICE",
  paste0(pi$plan$scenario$state, " with ",
         length(pi$plan$scenario$values), " values"))

# CPU: db_type is UNKNOWN_SOURCE... -> context
pc <- v6_24_selection_plan(list(metric = "CPU"))
R("H6", "CPU shows the unknown-source DB Type as context",
  pc$plan$db_type$state == "CONTEXT" && isTRUE(pc$plan$db_type$conditional),
  pc$plan$db_type$selected)

# SSD: single db_type Phoenix -> context but NOT conditional
ps <- v6_24_selection_plan(list(metric = "SSD"))
R("H7", "SSD states its single real DB Type as context",
  ps$plan$db_type$state == "CONTEXT" && !isTRUE(ps$plan$db_type$conditional),
  ps$plan$db_type$selected)

# ---- dynamic final label
lbl_cases <- list(
  list(sel = list(metric = "HDD", db_type = "Basilisk", granularity = "Forest"),
       want = "Forest"),
  list(sel = list(metric = "HDD", db_type = "Basilisk", granularity = "Region"),
       want = "Region"),
  list(sel = list(metric = "SSD"), want = "Forest"),
  list(sel = list(metric = "CPU"), want = "Region"),
  list(sel = list(metric = "IOPS"), want = "Region")
)
lbl_ok <- TRUE
for (cse in lbl_cases) {
  sp <- v6_24_selection_plan(cse$sel)
  got <- sp$plan$key$label
  ok <- identical(got, cse$want)
  lbl_ok <- lbl_ok && ok
  R(paste0("L_", paste(unlist(cse$sel), collapse = "_")),
    paste("final label for", paste(unlist(cse$sel), collapse = "/")),
    ok, paste0("expected ", cse$want, ", got ", got))
}
R("L0", "final axis is never labelled 'Key'",
  !any(vapply(lbl_cases, function(c) {
    identical(v6_24_selection_plan(c$sel)$plan$key$label, "Key") }, logical(1))),
  "no case yields the raw word Key")

# ---- every complete path still resolves to exactly one series
bad <- 0L
for (i in seq_len(nrow(nav))) {
  ch <- as.list(setNames(as.character(unlist(nav[i, V6_24_FILTER_AXES])),
                         V6_24_FILTER_AXES))
  if (is.null(v6_24_resolve_one(ch))) bad <- bad + 1L
}
R("C1", "every complete path resolves to exactly one series",
  bad == 0L, paste0(nrow(nav) - bad, "/", nrow(nav)))

# ---- no reachable option is empty
empty <- 0L
walk <- function(chosen, depth) {
  if (depth > length(V6_24_FILTER_AXES)) return(invisible())
  sp <- v6_24_selection_plan(chosen)
  a <- V6_24_FILTER_AXES[[depth]]
  st <- sp$plan[[a]]
  if (is.null(st) || st$state == "LOCKED") return(invisible())
  if (st$state == "CONTEXT") return(walk(chosen, depth + 1L))
  for (v in st$values) {
    ch2 <- chosen; ch2[[a]] <- v
    if (nrow(v6_24_selection_plan(ch2)$rows) == 0L) empty <<- empty + 1L
    walk(ch2, depth + 1L)
  }
}
walk(list(), 1L)
R("C2", "no reachable option yields zero series", empty == 0L,
  paste(empty, "empty options"))

# ---- no-signal / low-confidence context comes from fields
ns <- nav[nav$signal_quality_status == V6_24_NO_SIGNAL, ][1, ]
lc <- nav[nav$low_confidence_backtest_window_flag == "TRUE", ][1, ]
n1 <- paste(as.character(v6_24_context_notes(ns)), collapse = "")
n2 <- paste(as.character(v6_24_context_notes(lc)), collapse = "")
R("N1", "no-signal series gets the champion-not-a-recommendation note",
  grepl("not a recommendation", n1, fixed = TRUE), ns$series_id[1])
R("N2", "low-confidence series gets the moderate accuracy note",
  grepl("low confidence", n2, fixed = TRUE), lc$series_id[1])
R("N3", "route cards render for a resolved row",
  grepl("v24-rgrid", paste(as.character(v6_24_route_cards(ns)), collapse = ""),
        fixed = TRUE), "grid present")
R("N4", "demand nature is read, not hardcoded",
  nzchar(v6_24_demand_nature(as.character(ns$series_id[1]))),
  v6_24_demand_nature(as.character(ns$series_id[1])))

# ---- source hygiene
src <- paste(c(readLines("R/v6_24_selection_helpers.R", warn = FALSE),
               readLines("server/v6_24_mvp_server.R", warn = FALSE),
               readLines("ui/tabs_v6_24_mvp.R", warn = FALSE)), collapse = "\n")
# `.` crosses newlines in R's TRE, so the scan must be line by line.
srclines <- c(readLines("R/v6_24_selection_helpers.R", warn = FALSE),
              readLines("server/v6_24_mvp_server.R", warn = FALSE),
              readLines("ui/tabs_v6_24_mvp.R", warn = FALSE))
code <- srclines[!grepl("^\\s*#", srclines)]
rp <- code[grepl("route_path", code, fixed = TRUE)]
bad_rp <- rp[grepl("strsplit", rp, fixed = TRUE) | grepl("[[", rp, fixed = TRUE)]
R("S1", "no route_path positional parsing", length(bad_rp) == 0,
  if (length(bad_rp)) paste(bad_rp, collapse = " | ")
  else paste(length(rp), "route_path uses, all whole-field reads"))
R("S2", "no hardcoded no-signal series", !grepl("apcp150", src, fixed = TRUE))
R("S3", "no hardcoded GBRP267", !grepl("GBRP267", src, fixed = TRUE))
R("S4", "no write call", !any(vapply(
  c("write.csv", "write_csv", "write_parquet", "saveRDS", "unlink("),
  function(p) grepl(p, src, fixed = TRUE), logical(1))))
R("S5", "no SQL", !grepl("DBI::|odbc::|dbConnect", src))

# ---- reactive server checks
testServer(v6_24_mvp_server, {
  R("T1", "selection rail renders", !is.null(output$v24_sel_controls))
  R("T2", "breadcrumb renders", !is.null(output$v24_sel_breadcrumb))
  R("T3", "route state renders", !is.null(output$v24_sel_state))
  R("T4", "shared selection mirror renders", !is.null(output$v24_shared_selection))

  bc0 <- paste(as.character(output$v24_sel_breadcrumb), collapse = "")
  R("T5", "breadcrumb starts empty with a prompt",
    grepl("Select a Metric", bc0, fixed = TRUE))

  # choose a full HDD Basilisk Forest path
  row <- nav[nav$metric == "HDD" & nav$db_type == "Basilisk" &
               nav$granularity == "Forest", ][1, ]
  session$setInputs(v24_sel_metric = "HDD")
  ctl <- paste(as.character(output$v24_sel_controls), collapse = "")
  R("T6", "downstream controls appear after choosing Metric",
    grepl("v24_sel_db_type", ctl, fixed = TRUE))
  R("T7", "axes below the first unchosen level stay hidden",
    !grepl("v24_sel_scenario", ctl, fixed = TRUE) &&
      !grepl("v24_sel_key", ctl, fixed = TRUE),
    "Scenario and the final axis are not rendered until DB Type is chosen")

  session$setInputs(v24_sel_db_type = "Basilisk")
  ctl_b <- paste(as.character(output$v24_sel_controls), collapse = "")
  R("T7b", "Scenario is shown as context for HDD Basilisk, not as a dropdown",
    !grepl("v24_sel_scenario", ctl_b, fixed = TRUE) &&
      grepl("does not apply", ctl_b, fixed = TRUE),
    "rendered as a context chip")
  session$setInputs(v24_sel_granularity = "Forest")
  session$setInputs(v24_sel_key = as.character(row$key[1]))
  st <- paste(as.character(output$v24_sel_state), collapse = "")
  cd <- paste(as.character(output$v24_sel_cards), collapse = "")
  bc <- paste(as.character(output$v24_sel_breadcrumb), collapse = "")
  R("T8", "complete path resolves and renders route cards",
    grepl("v24-rgrid", cd, fixed = TRUE), as.character(row$series_id[1]))
  R("T9", "product status badge renders",
    grepl("AVAILABLE", st), "status present")
  R("T10", "breadcrumb shows the built path",
    grepl(as.character(row$key[1]), bc, fixed = TRUE))
  R("T11", "final crumb is labelled Forest, not Key",
    grepl("Forest", bc, fixed = TRUE) && !grepl(">Key<", bc))

  sh <- paste(as.character(output$v24_shared_selection), collapse = "")
  R("T12", "Forecast page mirrors the same selected series",
    grepl(as.character(row$series_id[1]), sh, fixed = TRUE),
    "shared reactive")

  vw <- paste(as.character(output$v24_vw_identity), collapse = "")
  R("T13", "Viewer identity uses the shared selection",
    grepl(as.character(row$series_id[1]), vw, fixed = TRUE))
  fc <- paste(as.character(output$v24_fc_identity), collapse = "")
  R("T14", "Forecast identity uses the SAME shared selection",
    grepl(as.character(row$series_id[1]), fc, fixed = TRUE))

  # changing the parent must clear downstream
  session$setInputs(v24_sel_metric = "CPU")
  bc2 <- paste(as.character(output$v24_sel_breadcrumb), collapse = "")
  R("T15", "changing Metric clears the downstream key",
    !grepl(as.character(row$key[1]), bc2, fixed = TRUE),
    "old key gone from breadcrumb")
  ctl2 <- paste(as.character(output$v24_sel_controls), collapse = "")
  R("T16", "CPU shows the unknown-source DB Type as context",
    grepl("not carried by the source", ctl2, fixed = TRUE))
})

out <- do.call(rbind, res)
np <- sum(out$result == "PASS"); nf <- sum(out$result == "FAIL")
cat(sprintf("\nP9C REACTIVE: %d PASS | %d FAIL of %d\n", np, nf, nrow(out)))
write.csv(out, file.path(Sys.getenv("V6_P9C_OUT", "."),
                         "_p9c_reactive_raw.csv"), row.names = FALSE)
if (nf == 0) cat("P9C_REACTIVE_OK\n") else cat("P9C_REACTIVE_FAILED\n")

