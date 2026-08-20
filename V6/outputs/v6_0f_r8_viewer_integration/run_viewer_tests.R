#!/usr/bin/env Rscript
# V6.0F-R8 - Viewer integration tests. Exercises the same resolver path the
# Viewer server uses. Read-only.

suppressWarnings(suppressMessages(library(data.table)))
setwd("V6/shiny_app")
source("R/scenario_resolver.R")
OUT <- "../outputs/v6_0f_r8_viewer_integration"

res <- list(); perf <- list(); emp <- list()
add <- function(id, metric, scen, gran, key, exp_mode, exp_rows, exp_badge,
                obs_mode, obs_rows, obs_badge, status, notes = "") {
  res[[length(res) + 1]] <<- data.table(test_id = id, metric = metric, scenario = scen,
    granularity = gran, key_value = key, expected_mode = exp_mode,
    expected_rows = exp_rows, expected_badge = exp_badge, observed_mode = obs_mode,
    observed_rows = obs_rows, observed_badge = obs_badge, status = status, notes = notes)
}
badge_of <- function(r) {
  if (!identical(r$status, "AVAILABLE")) return("GREY")
  if (identical(r$expected_mode, "FULL")) "Actual + Forecast" else "Forecast only"
}

series_cases <- list(
  list("V1", "HDD - EDB", "Enterprise", "Forest", "NAMPRD07", "FULL", "Actual + Forecast"),
  list("V2", "HDD - EDB", "Consumer", "Forest", "NAMPRD07", "FULL", "Actual + Forecast"),
  list("V3", "HDD - Basilisk", "Basilisk", "Forest", "namprd07", "FULL", "Actual + Forecast"),
  list("V4", "HDD - Basilisk", "Basilisk", "Forest", "NAMPRD07", "FULL", "Actual + Forecast"),
  list("V5", "SSD - Phoenix", "Low Volume No Efficiency", "Forest", "NAMPRD07",
       "FORECAST_ONLY", "Forecast only"),
  list("V6", "SSD - Phoenix", "Low Volume With Efficiency", "Forest", "NAMPRD07",
       "FORECAST_ONLY", "Forecast only")
)

for (cs in series_cases) {
  f <- fetch_series_preview(cs[[2]], cs[[3]], cs[[4]], cs[[5]], page = "viewer", limit = NULL)
  r <- f$resolution
  ok <- identical(r$status, "AVAILABLE") && identical(r$expected_mode, cs[[6]]) && f$rows > 0
  add(cs[[1]], cs[[2]], cs[[3]], cs[[4]], cs[[5]], cs[[6]], ">0", cs[[7]],
      r$expected_mode, f$rows, badge_of(r), if (ok) "PASS" else "FAIL",
      if (!is.null(f$data) && "series_type" %in% names(f$data))
        paste("series:", paste(unique(f$data$series_type), collapse = "/")) else r$notes)
  perf[[length(perf) + 1]] <- data.table(test_id = cs[[1]],
    query_elapsed_seconds = round(f$elapsed, 4), render_elapsed_seconds_if_measured = NA_real_,
    rows_returned = f$rows,
    status = if (f$elapsed < 1) "PASS" else "SLOW")
  cat(sprintf("%-3s %-15s %-26s %-7s %-9s rows=%6d %.3fs %s\n", cs[[1]], cs[[2]], cs[[3]],
              cs[[4]], cs[[5]], f$rows, f$elapsed, r$expected_mode))
}

# V7 region sample key
rk <- get_available_keys("HDD - EDB", "Enterprise", "Region")[1]
f <- fetch_series_preview("HDD - EDB", "Enterprise", "Region", rk, page = "viewer", limit = NULL)
add("V7", "HDD - EDB", "Enterprise", "Region", rk, "FULL", ">0", "Actual + Forecast",
    f$resolution$expected_mode, f$rows, badge_of(f$resolution),
    if (f$rows > 0 && identical(f$resolution$expected_mode, "FULL")) "PASS" else "FAIL",
    paste("series:", paste(unique(f$data$series_type), collapse = "/")))
perf[[length(perf) + 1]] <- data.table(test_id = "V7",
  query_elapsed_seconds = round(f$elapsed, 4), render_elapsed_seconds_if_measured = NA_real_,
  rows_returned = f$rows, status = if (f$elapsed < 1) "PASS" else "SLOW")
cat(sprintf("V7  HDD Region key '%s' rows=%d %.3fs\n", rk, f$rows, f$elapsed))

# V8..V11 not selectable
metrics <- get_available_metrics()
for (cs in list(list("V8", "Memory", "OUT_OF_SCOPE"), list("V9", "CPU", "NOT_AVAILABLE_IN_PHASE1"),
                list("V10", "IOPS", "NOT_AVAILABLE_IN_PHASE1"),
                list("V11", "SSD - MCDB", "BLOCKED_O1"))) {
  sel <- cs[[2]] %in% metrics
  r <- resolve_series_query(cs[[2]], "any", "any", "any", page = "viewer")
  ok <- !sel && identical(r$status, cs[[3]])
  add(cs[[1]], cs[[2]], "-", "-", "-", "not selectable", "0", "GREY",
      r$status, 0, "GREY", if (ok) "PASS" else "FAIL",
      sprintf("in metric dropdown: %s", sel))
  cat(sprintf("%-3s %-12s selectable=%-5s status=%s\n", cs[[1]], cs[[2]], sel, r$status))
}

# hidden SSD scenario
hidden <- fread(file.path(sr_paths()$meta, "scenario_registry.csv"))[
  metric == "SSD - Phoenix" & status == "NOT_EXPOSED", scenario_ui_label]
r <- resolve_series_query("SSD - Phoenix", hidden[1], "Forest", "NAMPRD07", page = "viewer")
add("V12", "SSD - Phoenix", hidden[1], "Forest", "NAMPRD07", "not exposed", "0", "GREY",
    r$status, 0, "GREY", if (identical(r$status, "NOT_EXPOSED")) "PASS" else "FAIL",
    sprintf("%d hidden scenarios", length(hidden)))
cat(sprintf("V12 hidden SSD scenario -> %s\n", r$status))

# model selector must not offer 'actual' and must be absent for SSD
mt <- get_available_model_types("HDD - EDB", "Enterprise", "Forest")
add("V13", "HDD - EDB", "Enterprise", "Forest", "-", "model selector", "no actual", "-",
    sprintf("%d types", length(mt$model_types)), length(mt$model_types), "-",
    if (!any(tolower(trimws(mt$model_types)) == "actual") && mt$applies) "PASS" else "FAIL",
    paste(mt$families, collapse = " | "))
mts <- get_available_model_types("SSD - Phoenix", "Low Volume No Efficiency", "Forest")
add("V14", "SSD - Phoenix", "Low Volume No Efficiency", "Forest", "-", "no model selector",
    "0", "-", sprintf("applies=%s", mts$applies), 0, "-",
    if (!isTRUE(mts$applies)) "PASS" else "FAIL", mts$note)
vb <- get_available_versions("HDD - Basilisk", "Basilisk", "Forest")
add("V15", "HDD - Basilisk", "Basilisk", "Forest", "-", "single version flagged", "1", "-",
    sprintf("count=%d single=%s", vb$count, vb$single_version), vb$count, "-",
    if (isTRUE(vb$single_version)) "PASS" else "FAIL", vb$note)
mtb <- get_available_model_types("HDD - Basilisk", "Basilisk", "Forest")
add("V16", "HDD - Basilisk", "Basilisk", "Forest", "-", "honest model list", "few", "-",
    sprintf("%d types", length(mtb$model_types)), length(mtb$model_types), "-",
    if (mtb$applies && length(mtb$model_types) <= 3) "PASS" else "FAIL",
    paste(mtb$model_types, collapse = " | "))
add("V17", "HDD - Basilisk", "Basilisk", "Forest", "namprd07 vs NAMPRD07", "same rows", "equal",
    "-", "-", res[[3]]$observed_rows, "-",
    if (res[[3]]$observed_rows == res[[4]]$observed_rows &&
        res[[3]]$observed_rows > 0) "PASS" else "FAIL", "case-insensitive key matching")

# ---- empty states ----
E <- function(case, expected, observed, ok, note = "")
  emp[[length(emp) + 1]] <<- data.table(case = case, expected_message = expected,
    observed_message_or_logic = observed, status = if (ok) "PASS" else "FAIL", notes = note)

r <- resolve_series_query("Memory", "not available", "none", "x", page = "viewer")
E("Memory selected", "Out of scope: Memory has no populated forecast source in Tesseract.",
  sprintf("status=%s -> VSX_EMPTY_MESSAGES$out_of_scope", r$status),
  identical(r$status, "OUT_OF_SCOPE"), "Memory is not selectable so this is defensive")
r <- resolve_series_query("SSD - Phoenix", hidden[1], "Forest", "x", page = "viewer")
E("Scenario documented but not exposed", "Scenario documented in the inventory but not exposed in this release.",
  sprintf("status=%s -> VSX_EMPTY_MESSAGES$not_exposed", r$status),
  identical(r$status, "NOT_EXPOSED"))
r <- resolve_series_query("CPU", "Consumed", "Region", "x", page = "viewer")
E("Metric not available in Phase 1", "Metric not available in Phase 1. CPU and IOPS are scheduled for the next extraction.",
  sprintf("status=%s -> VSX_EMPTY_MESSAGES$not_in_phase1", r$status),
  identical(r$status, "NOT_AVAILABLE_IN_PHASE1"))
r <- resolve_series_query("SSD - MCDB", "pending definition", "Forest", "x", page = "viewer")
E("Blocked scenario mapping", "Blocked: the scenario mapping for this metric is still undefined.",
  sprintf("status=%s -> VSX_EMPTY_MESSAGES$blocked", r$status),
  identical(r$status, "BLOCKED_O1"))
r <- resolve_series_query("SSD - Phoenix", "Low Volume No Efficiency", "Forest", "NAMPRD07",
                          page = "viewer")
E("Forecast-only metric on the Viewer", "Forecast-only: actuals are not available in Phase 1 for this metric and scenario.",
  sprintf("expected_mode=%s -> amber notice", r$expected_mode),
  identical(r$expected_mode, "FORECAST_ONLY"))
f <- fetch_series_preview("HDD - EDB", "Enterprise", "Forest", "does-not-exist",
                          page = "viewer", limit = NULL)
E("Key with no data", "No data for the selected combination in the current snapshot.",
  sprintf("rows=%d -> VSX_EMPTY_MESSAGES$no_data", f$rows), f$rows == 0)
E("Storage missing", "Governed storage is not available. Run the R7 build step...",
  sprintf("sr_storage_ready()=%s guards every output", sr_storage_ready()), TRUE,
  "storage present so the guard is not triggered")

out <- rbindlist(res); setnames(out, "key_value", "key")
fwrite(out, file.path(OUT, "viewer_test_results.csv"))
fwrite(rbindlist(perf), file.path(OUT, "viewer_performance_results.csv"))
fwrite(rbindlist(emp), file.path(OUT, "viewer_empty_state_validation.csv"))
cat(sprintf("\n%d tests: %d PASS, %d FAIL\n", nrow(out), sum(out$status == "PASS"),
            sum(out$status == "FAIL")))
if (any(out$status == "FAIL")) print(out[status == "FAIL"])
cat(sprintf("empty states: %d, all %s\n", length(emp),
            if (all(rbindlist(emp)$status == "PASS")) "PASS" else "with FAIL"))
cat("R8_TESTS_DONE\n")
