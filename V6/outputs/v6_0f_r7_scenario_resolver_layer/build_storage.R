#!/usr/bin/env Rscript
# V6.0F-R7 - build the production storage layer from the R6 Phase 1 artifacts.
# Derivation only: no Tesseract access, no edits to the R6 CSV files.

suppressWarnings(suppressMessages({
  library(data.table); library(duckdb); library(DBI)
}))

R6   <- "V6/outputs/v6_0f_r6_phase1_governed_extraction"
R1   <- "V6/outputs/v6_0f_r1_tesseract_metric_inventory"
STORE <- "V6/data/storage"
META  <- file.path(STORE, "ui_metadata")
dir.create(META, recursive = TRUE, showWarnings = FALSE)

viewer   <- fread(file.path(R6, "r6_phase1_viewer_hdd.csv"), showProgress = FALSE)
fcst_hdd <- fread(file.path(R6, "r6_phase1_forecast_hdd.csv"), showProgress = FALSE)
fcst_ssd <- fread(file.path(R6, "r6_phase1_forecast_ssd_phoenix.csv"), showProgress = FALSE)

# ---------------------------------------------------------------- DuckDB
DB <- file.path(STORE, "r6_phase1.duckdb")
if (file.exists(DB)) file.remove(DB)
SRC_CSV <- c(viewer_hdd = "r6_phase1_viewer_hdd.csv",
             forecast_hdd = "r6_phase1_forecast_hdd.csv",
             forecast_ssd = "r6_phase1_forecast_ssd_phoenix.csv")
con <- dbConnect(duckdb::duckdb(shared_home = FALSE), dbdir = DB)
for (n in names(SRC_CSV)) {
  p <- normalizePath(file.path(R6, SRC_CSV[[n]]), winslash = "/")
  # forecast_ssd has no granularity column; it is Forest-only by contract
  extra <- if (n == "forecast_ssd") ", 'Forest' AS granularity" else ""
  # key_lower is materialised at CREATE time: an UPDATE afterwards bloats the file
  dbExecute(con, sprintf(
    "CREATE TABLE %s AS SELECT *%s, lower(key) AS key_lower FROM read_csv_auto('%s')",
    n, extra, p))
  cat(sprintf("  table %-14s %9s rows\n", n,
              format(dbGetQuery(con, sprintf("SELECT COUNT(*) n FROM %s", n))$n, big.mark = ",")))
}
dbExecute(con, "CHECKPOINT")
dbDisconnect(con, shutdown = TRUE)
cat(sprintf("DuckDB built: %.2f MB\n", file.info(DB)$size / 1048576))

# ---------------------------------------------------------------- model families (R3 rules)
family_of <- function(x) {
  v <- trimws(x); lo <- tolower(v)
  fifelse(lo == "actual", "Actual",
  fifelse(lo %in% c("stubbed", "extrapolated", "fixed_na", "none", ""), "Marker",
  fifelse(grepl("_Ensemble", v, fixed = TRUE) | grepl("(0.5,0.5)", v, fixed = TRUE), "Ensemble",
  fifelse(startsWith(v, "FixedGrowth"), "Fixed growth baseline",
  fifelse(startsWith(v, "Fixed_") | v == "fixed_seasonal", "Fixed rate baseline",
          "Statistical model")))))
}

# ---------------------------------------------------------------- scenario registry
ssd_all <- fread(file.path(R1, "tesseract_scenario_values.csv"), showProgress = FALSE)
ssd_all <- unique(trimws(ssd_all[table_name == "forecast_substrateBE_SSD_TotalForecast",
                                 scenario_value]))
ssd_exposed <- c("Low Volume No Efficiency", "Low Volume With Efficiency")
ssd_hidden  <- setdiff(ssd_all, ssd_exposed)

avail <- unique(rbind(
  viewer[, .(metric, scenario_ui_label, granularity)],
  fcst_ssd[, .(metric, scenario_ui_label, granularity = "Forest")]
))
avail[, `:=`(
  status         = "AVAILABLE",
  viewer_status  = fifelse(startsWith(metric, "HDD"), "FULL", "FORECAST_ONLY"),
  forecast_status = "FULL",
  badge          = fifelse(startsWith(metric, "HDD"), "GREEN", "AMBER"),
  viewer_table   = fifelse(startsWith(metric, "HDD"), "viewer_hdd", NA_character_),
  forecast_table = fifelse(startsWith(metric, "HDD"), "forecast_hdd", "forecast_ssd"),
  has_actuals    = startsWith(metric, "HDD"),
  has_forecast   = TRUE,
  reason         = "Extracted and validated in R6 Phase 1"
)]

blocked <- rbindlist(list(
  data.table(metric = "Memory", scenario_ui_label = "not available", granularity = "none",
             status = "OUT_OF_SCOPE", viewer_status = "OUT_OF_SCOPE",
             forecast_status = "OUT_OF_SCOPE", badge = "GREY",
             viewer_table = NA_character_, forecast_table = NA_character_,
             has_actuals = FALSE, has_forecast = FALSE,
             reason = "No populated forecast source in Tesseract (D1)"),
  data.table(metric = "SSD - Phoenix", scenario_ui_label = ssd_hidden, granularity = "Forest",
             status = "NOT_EXPOSED", viewer_status = "NOT_EXPOSED",
             forecast_status = "NOT_EXPOSED", badge = "GREY",
             viewer_table = NA_character_, forecast_table = NA_character_,
             has_actuals = FALSE, has_forecast = TRUE,
             reason = "Documented in R1 but not exposed in the first release (D2)"),
  data.table(metric = c("CPU", "CPU Failover", "IOPS", "IOPS Failover"),
             scenario_ui_label = c("Consumed", "Failover", "Consumed", "Failover"),
             granularity = "Region and Forest",
             status = "NOT_AVAILABLE_IN_PHASE1", viewer_status = "FORECAST_ONLY",
             forecast_status = "FULL", badge = "AMBER",
             viewer_table = NA_character_, forecast_table = NA_character_,
             has_actuals = FALSE, has_forecast = TRUE,
             reason = "Scheduled for R6 Phase 2; not extracted yet"),
  data.table(metric = "SSD - MCDB", scenario_ui_label = "pending definition",
             granularity = "Forest", status = "BLOCKED_O1", viewer_status = "NOT_EXPOSED",
             forecast_status = "NOT_EXPOSED", badge = "GREY",
             viewer_table = NA_character_, forecast_table = NA_character_,
             has_actuals = FALSE, has_forecast = TRUE,
             reason = "Scenario mapping ambiguous; blocked by O1")
))

registry <- rbind(avail, blocked, fill = TRUE)
fwrite(registry, file.path(META, "scenario_registry.csv"))
cat(sprintf("scenario_registry.csv: %d rows (%d AVAILABLE)\n",
            nrow(registry), sum(registry$status == "AVAILABLE")))

fwrite(registry[status == "AVAILABLE",
                .(metric, scenario_ui_label, granularity, viewer_status, forecast_status,
                  badge, has_actuals, has_forecast)],
       file.path(META, "available_scenarios.csv"))

# ---------------------------------------------------------------- keys
keys <- unique(rbind(
  viewer[, .(metric, scenario_ui_label, granularity, key = as.character(key))],
  fcst_ssd[, .(metric, scenario_ui_label, granularity = "Forest", key = as.character(key))]
))
keys[, key_lower := tolower(key)]
setorder(keys, metric, scenario_ui_label, granularity, key)
fwrite(keys, file.path(META, "available_keys.csv"))
cat(sprintf("available_keys.csv: %d rows\n", nrow(keys)))

# ---------------------------------------------------------------- versions
vers <- unique(rbind(
  fcst_hdd[, .(metric, scenario_ui_label, granularity,
               forecast_version = as.character(forecast_version), page = "forecast")],
  fcst_ssd[, .(metric, scenario_ui_label, granularity = "Forest",
               forecast_version = as.character(forecast_version), page = "forecast")]
))
vers[, version_count := .N, by = .(metric, scenario_ui_label, granularity)]
vers[, single_version := version_count == 1L]
setorder(vers, metric, scenario_ui_label, granularity, -forecast_version)
fwrite(vers, file.path(META, "available_versions.csv"))
cat(sprintf("available_versions.csv: %d rows\n", nrow(vers)))

# ---------------------------------------------------------------- model types
mt <- unique(viewer[, .(metric, scenario_ui_label, granularity,
                        model_type, raw_type = as.character(raw_type))])
mt[, model_family := family_of(model_type)]
# 'actual' is a series type, not a selectable model; markers are not models either
mt <- mt[!model_family %in% c("Marker", "Actual")]
setorder(mt, metric, scenario_ui_label, granularity, model_family, model_type)
fwrite(mt, file.path(META, "available_model_types.csv"))
cat(sprintf("available_model_types.csv: %d rows\n", nrow(mt)))

cat("\nSTORAGE_BUILD_DONE\n")
for (f in list.files(META, full.names = TRUE))
  cat(sprintf("  %-30s %7.1f KB\n", basename(f), file.info(f)$size / 1024))
