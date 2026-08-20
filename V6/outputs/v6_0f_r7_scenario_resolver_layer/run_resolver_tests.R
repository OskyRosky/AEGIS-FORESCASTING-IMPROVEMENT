#!/usr/bin/env Rscript
# V6.0F-R7 - resolver test harness. Read-only against DuckDB + metadata slices.

suppressWarnings(suppressMessages(library(data.table)))
setwd("V6/shiny_app")
source("R/scenario_resolver.R")
OUT <- "../outputs/v6_0f_r7_scenario_resolver_layer"

res <- list()
add <- function(id, desc, input, expected, observed, status, rows = NA, elapsed = NA,
                notes = "") {
  res[[length(res) + 1]] <<- data.table(case_id = id, description = desc, input = input,
    expected = expected, observed = observed, rows_returned = rows,
    elapsed_seconds = if (is.na(elapsed)) NA_real_ else round(elapsed, 4),
    status = status, notes = notes)
}
chk <- function(id, desc, input, expected, observed, rows = NA, elapsed = NA, notes = "") {
  add(id, desc, input, expected, observed,
      if (identical(as.character(expected), as.character(observed))) "PASS" else "FAIL",
      rows, elapsed, notes)
}

cat("storage ready:", sr_storage_ready(), "\n")
cat("duckdb:", sr_paths()$duckdb, "\n\n")

# ---- T1..T2 HDD - EDB forest, uppercase NAMPRD07 --------------------------
for (i in seq_along(c("Enterprise", "Consumer"))) {
  sc <- c("Enterprise", "Consumer")[i]
  f <- fetch_series_preview("HDD - EDB", sc, "Forest", "NAMPRD07", page = "viewer",
                            limit = NULL)
  ok <- f$resolution$status == "AVAILABLE" && f$rows > 0 &&
        f$resolution$expected_mode == "FULL"
  cat(sprintf("T%d HDD - EDB / %-10s / Forest / NAMPRD07  rows=%5d  %.4fs  mode=%s\n",
              i, sc, f$rows, f$elapsed, f$resolution$expected_mode))
  add(sprintf("T%d", i), sprintf("HDD - EDB / %s / Forest / NAMPRD07 / Viewer", sc),
      "key='NAMPRD07'", "AVAILABLE + FULL + rows>0",
      sprintf("%s + %s + rows=%d", f$resolution$status, f$resolution$expected_mode, f$rows),
      if (ok) "PASS" else "FAIL", f$rows, f$elapsed,
      paste("series_type:", paste(unique(f$data$series_type), collapse = "/")))
}

# ---- T3 Basilisk with the lowercase key stored in the data ---------------
f3 <- fetch_series_preview("HDD - Basilisk", "Basilisk", "Forest", "namprd07",
                           page = "viewer", limit = NULL)
cat(sprintf("T3 Basilisk / Forest / 'namprd07'          rows=%5d  %.4fs\n", f3$rows, f3$elapsed))
add("T3", "HDD - Basilisk / Basilisk / Forest / namprd07 / Viewer", "key='namprd07'",
    "AVAILABLE + rows>0", sprintf("%s + rows=%d", f3$resolution$status, f3$rows),
    if (f3$resolution$status == "AVAILABLE" && f3$rows > 0) "PASS" else "FAIL",
    f3$rows, f3$elapsed, "key as physically stored")

# ---- T4 Basilisk with the uppercase key the user will type ---------------
f4 <- fetch_series_preview("HDD - Basilisk", "Basilisk", "Forest", "NAMPRD07",
                           page = "viewer", limit = NULL)
cat(sprintf("T4 Basilisk / Forest / 'NAMPRD07'          rows=%5d  %.4fs\n", f4$rows, f4$elapsed))
add("T4", "HDD - Basilisk / Basilisk / Forest / NAMPRD07 / Viewer", "key='NAMPRD07'",
    sprintf("same row count as T3 (%d)", f3$rows), sprintf("rows=%d", f4$rows),
    if (f4$rows == f3$rows && f4$rows > 0) "PASS" else "FAIL", f4$rows, f4$elapsed,
    "case-insensitive matching proves RB1 is handled")

# ---- T5..T6 SSD-Phoenix forecast ----------------------------------------
for (i in seq_along(c("Low Volume No Efficiency", "Low Volume With Efficiency"))) {
  sc <- c("Low Volume No Efficiency", "Low Volume With Efficiency")[i]
  f <- fetch_series_preview("SSD - Phoenix", sc, "Forest", "NAMPRD07", page = "forecast",
                            limit = NULL)
  ok <- f$resolution$status == "AVAILABLE" && f$rows > 0 &&
        f$resolution$table_name == "forecast_ssd"
  cat(sprintf("T%d SSD / %-26s rows=%5d  %.4fs  tbl=%s\n", i + 4, sc, f$rows, f$elapsed,
              f$resolution$table_name))
  add(sprintf("T%d", i + 4), sprintf("SSD - Phoenix / %s / Forest / NAMPRD07 / Forecast", sc),
      "page='forecast'", "AVAILABLE + forecast_ssd + rows>0",
      sprintf("%s + %s + rows=%d", f$resolution$status, f$resolution$table_name, f$rows),
      if (ok) "PASS" else "FAIL", f$rows, f$elapsed, f$resolution$notes)
}

# ---- T7 HDD region sample key -------------------------------------------
rk <- get_available_keys("HDD - EDB", "Enterprise", "Region")[1]
f7 <- fetch_series_preview("HDD - EDB", "Enterprise", "Region", rk, page = "viewer",
                           limit = NULL)
cat(sprintf("T7 HDD Region / '%s'  rows=%5d  %.4fs\n", rk, f7$rows, f7$elapsed))
add("T7", "HDD - EDB / Enterprise / Region / sample key / Viewer", sprintf("key='%s'", rk),
    "AVAILABLE + FULL + rows>0",
    sprintf("%s + %s + rows=%d", f7$resolution$status, f7$resolution$expected_mode, f7$rows),
    if (f7$resolution$status == "AVAILABLE" && f7$rows > 0) "PASS" else "FAIL",
    f7$rows, f7$elapsed, paste("series_type:", paste(unique(f7$data$series_type), collapse = "/")))

# ---- T8..T11 blocked selections -----------------------------------------
r8 <- resolve_series_query("Memory", "not available", "none", "any", page = "viewer")
cat(sprintf("T8  Memory                -> %s\n", r8$status))
chk("T8", "Memory must be out of scope", "metric='Memory'", "OUT_OF_SCOPE", r8$status,
    notes = r8$notes)

hidden <- setdiff(
  unique(fread(file.path(sr_paths()$meta, "scenario_registry.csv"))[
    metric == "SSD - Phoenix" & status == "NOT_EXPOSED", scenario_ui_label]), NA)
r9 <- resolve_series_query("SSD - Phoenix", hidden[1], "Forest", "NAMPRD07", page = "forecast")
cat(sprintf("T9  SSD hidden '%s' -> %s\n", hidden[1], r9$status))
chk("T9", sprintf("SSD-Phoenix hidden scenario (%d of 24) must not be exposed", length(hidden)),
    sprintf("scenario='%s'", hidden[1]), "NOT_EXPOSED", r9$status,
    notes = sprintf("%d hidden scenarios registered", length(hidden)))

for (m in c("CPU", "IOPS")) {
  r <- resolve_series_query(m, "Consumed", "Region", "any", page = "forecast")
  cat(sprintf("T10 %-5s                -> %s\n", m, r$status))
  chk("T10", sprintf("%s must not resolve in Phase 1", m), sprintf("metric='%s'", m),
      "NOT_AVAILABLE_IN_PHASE1", r$status, notes = r$notes)
}

r11 <- resolve_series_query("SSD - MCDB", "pending definition", "Forest", "any",
                            page = "forecast")
cat(sprintf("T11 SSD - MCDB            -> %s\n", r11$status))
chk("T11", "SSD - MCDB must be blocked by O1", "metric='SSD - MCDB'", "BLOCKED_O1",
    r11$status, notes = r11$notes)

# ---- dropdown behaviour --------------------------------------------------
cat("\n--- dropdowns ---\n")
m <- get_available_metrics()
cat("metrics:", paste(m, collapse = " | "), "\n")
chk("D1", "Memory absent from the metric dropdown", "get_available_metrics()", "FALSE",
    as.character("Memory" %in% m), notes = paste(m, collapse = " | "))
chk("D2", "Only HDD and SSD-Phoenix metrics offered", "get_available_metrics()", "3",
    as.character(length(m)), notes = paste(m, collapse = " | "))

sc <- get_available_scenarios("SSD - Phoenix")
chk("D3", "SSD-Phoenix exposes exactly 2 scenarios", "get_available_scenarios()", "2",
    as.character(length(sc)), notes = paste(sc, collapse = " | "))

g <- get_available_granularities("HDD - EDB", "Enterprise")
chk("D4", "HDD - EDB offers Region and Forest", "get_available_granularities()",
    "Region|Forest", paste(g, collapse = "|"))

k <- get_available_keys("HDD - Basilisk", "Basilisk", "Forest")
chk("D5", "Basilisk keys are scoped and lowercase", "get_available_keys()", "TRUE",
    as.character(any(k == "namprd07")), rows = length(k),
    notes = sprintf("%d keys; sample: %s", length(k), paste(head(k, 3), collapse = ", ")))

v <- get_available_versions("HDD - Basilisk", "Basilisk", "Forest")
cat(sprintf("Basilisk versions: %d single=%s\n", v$count, v$single_version))
chk("D6", "Basilisk reports a single forecast version", "get_available_versions()", "TRUE",
    as.character(v$single_version), rows = v$count, notes = v$note)

v2 <- get_available_versions("HDD - EDB", "Enterprise", "Region")
chk("D7", "HDD - EDB Region reports 3 versions", "get_available_versions()", "3",
    as.character(v2$count), rows = v2$count, notes = v2$note)

mt <- get_available_model_types("HDD - EDB", "Enterprise", "Forest")
cat(sprintf("HDD EDB Forest model families: %s\n", paste(mt$families, collapse = " | ")))
chk("D8", "HDD model types grouped by family", "get_available_model_types()", "TRUE",
    as.character(mt$applies && length(mt$families) > 1),
    rows = length(mt$model_types), notes = paste(mt$families, collapse = " | "))

mtb <- get_available_model_types("HDD - Basilisk", "Basilisk", "Forest")
chk("D9", "Basilisk exposes few model types", "get_available_model_types()", "TRUE",
    as.character(mtb$applies && length(mtb$model_types) <= 3),
    rows = length(mtb$model_types), notes = paste(mtb$model_types, collapse = " | "))

mts <- get_available_model_types("SSD - Phoenix", "Low Volume No Efficiency", "Forest")
chk("D10", "SSD-Phoenix renders no model selector", "get_available_model_types()", "FALSE",
    as.character(mts$applies), notes = mts$note)

chk("D11", "Markers excluded from model types", "available_model_types", "FALSE",
    as.character(any(tolower(trimws(mt$model_types)) %in%
                     c("stubbed", "extrapolated", "fixed_na"))))

# ---- version filter actually narrows the result -------------------------
vv <- get_available_versions("HDD - EDB", "Enterprise", "Region")$versions
a <- fetch_series_count("HDD - EDB", "Enterprise", "Region", rk, page = "forecast")
b <- fetch_series_count("HDD - EDB", "Enterprise", "Region", rk, version = vv[1],
                        page = "forecast")
chk("D12", "Version filter reduces the result set", "version = latest", "TRUE",
    as.character(b$rows < a$rows && b$rows > 0), rows = b$rows,
    notes = sprintf("all versions=%d, one version=%d", a$rows, b$rows))

# ---- model filter keeps the actual series in the Viewer -----------------
one <- mt$model_types[mt$model_types != "Actual"][1]
fm <- fetch_series_preview("HDD - EDB", "Enterprise", "Forest", "NAMPRD07",
                           model_type = one, page = "viewer", limit = NULL)
chk("D13", "Viewer keeps actuals when a model is selected", sprintf("model_type='%s'", one),
    "TRUE", as.character("actual" %in% unique(fm$data$series_type)), rows = fm$rows,
    notes = paste(unique(fm$data$series_type), collapse = "/"))

out <- rbindlist(res)
fwrite(out, file.path(OUT, "resolver_test_results.csv"))
cat(sprintf("\n%d checks: %d PASS, %d FAIL\n", nrow(out), sum(out$status == "PASS"),
            sum(out$status == "FAIL")))
if (any(out$status == "FAIL")) print(out[status == "FAIL", .(case_id, expected, observed)])
cat("RESOLVER_TESTS_DONE\n")
