#!/usr/bin/env Rscript
# V6.0F-R5b - storage benchmark. Reads R6 Phase 1 artifacts read-only.

suppressWarnings(suppressMessages({
  library(data.table); library(arrow); library(duckdb); library(DBI)
}))

R6  <- "V6/outputs/v6_0f_r6_phase1_governed_extraction"
R5B <- "V6/outputs/v6_0f_r5b_storage_performance_strategy"
BENCH <- file.path(R5B, "bench")
dir.create(BENCH, recursive = TRUE, showWarnings = FALSE)

ART <- c(viewer_hdd = "r6_phase1_viewer_hdd.csv",
         forecast_hdd = "r6_phase1_forecast_hdd.csv",
         forecast_ssd = "r6_phase1_forecast_ssd_phoenix.csv")

res <- list()
add <- function(id, store, metric, scen, gran, key, rows, secs, status, notes = "") {
  res[[length(res) + 1]] <<- data.table(benchmark_id = id, artifact_or_storage = store,
    metric = metric, scenario = scen, granularity = gran, key_value = key,
    rows_returned = rows, elapsed_seconds = round(secs, 3), status = status, notes = notes)
}
tt <- function(expr) { t0 <- Sys.time(); v <- force(expr); list(v = v,
                       s = as.numeric(difftime(Sys.time(), t0, units = "secs"))) }

mb <- function(p) round(sum(file.info(list.files(p, recursive = TRUE, full.names = TRUE))$size,
                           na.rm = TRUE) / 1048576, 2)

cat("=== OPTION A: plain CSV ===\n")
csv_load <- list(); csv_mem <- list()
for (n in names(ART)) {
  gc(FALSE)
  r <- tt(fread(file.path(R6, ART[[n]]), showProgress = FALSE))
  csv_load[[n]] <- r$s
  csv_mem[[n]] <- as.numeric(object.size(r$v)) / 1048576
  cat(sprintf("  %-14s load=%6.2fs  rows=%9s  mem=%7.1f MB\n", n, r$s,
              format(nrow(r$v), big.mark = ","), csv_mem[[n]]))
  assign(paste0("dt_", n), r$v)
}
total_csv_load <- sum(unlist(csv_load))
total_csv_mem  <- sum(unlist(csv_mem))
cat(sprintf("  TOTAL load=%.2fs  mem=%.1f MB\n", total_csv_load, total_csv_mem))

# in-memory filter timings (best case for CSV, after paying the load cost)
f1 <- tt(dt_viewer_hdd[metric == "HDD - EDB" & scenario_ui_label == "Enterprise" &
                       granularity == "Forest" & grepl("NAMPRD07", key)])
add("B1", "CSV in-memory", "HDD - EDB", "Enterprise", "Forest", "NAMPRD07",
    nrow(f1$v), f1$s, "OK", "filter only; excludes the load cost")
f2 <- tt(dt_viewer_hdd[metric == "HDD - EDB" & scenario_ui_label == "Consumer" &
                       granularity == "Forest" & grepl("NAMPRD07", key)])
add("B2", "CSV in-memory", "HDD - EDB", "Consumer", "Forest", "NAMPRD07",
    nrow(f2$v), f2$s, "OK", "filter only")
f3 <- tt(dt_viewer_hdd[metric == "HDD - Basilisk" & granularity == "Forest" &
                       grepl("NAMPRD07", key)])
add("B3", "CSV in-memory", "HDD - Basilisk", "Basilisk", "Forest", "NAMPRD07",
    nrow(f3$v), f3$s, "OK", "filter only")
f4 <- tt(dt_forecast_ssd[scenario_ui_label == "Low Volume No Efficiency" &
                         grepl("NAMPRD07", key)])
add("B4", "CSV in-memory", "SSD - Phoenix", "Low Volume No Efficiency", "Forest", "NAMPRD07",
    nrow(f4$v), f4$s, "OK", "filter only")
f5 <- tt(dt_forecast_ssd[scenario_ui_label == "Low Volume With Efficiency" &
                         grepl("NAMPRD07", key)])
add("B5", "CSV in-memory", "SSD - Phoenix", "Low Volume With Efficiency", "Forest", "NAMPRD07",
    nrow(f5$v), f5$s, "OK", "filter only")
region_key <- dt_viewer_hdd[granularity == "Region", key][1]
f6 <- tt(dt_viewer_hdd[granularity == "Region" & key == region_key])
add("B6", "CSV in-memory", "HDD", "all", "Region", region_key, nrow(f6$v), f6$s, "OK", "filter only")
f7 <- tt(unique(dt_viewer_hdd[, .(metric, scenario_ui_label, granularity)]))
add("B7", "CSV in-memory", "all", "all", "all", "-", nrow(f7$v), f7$s, "OK",
    "scenario dropdown metadata")
f8 <- tt(unique(dt_viewer_hdd[metric == "HDD - EDB" & scenario_ui_label == "Enterprise" &
                              granularity == "Forest", key]))
add("B8", "CSV in-memory", "HDD - EDB", "Enterprise", "Forest", "-", length(f8$v), f8$s, "OK",
    "key dropdown metadata")
for (i in 1:8) add(paste0("B", i), "CSV cold read", "-", "-", "-", "-", NA_integer_,
                   total_csv_load, "OK", "every filter above requires this full load first")

cat("\n=== OPTION B: partitioned CSV ===\n")
PART <- file.path(BENCH, "csv_partitioned"); dir.create(PART, showWarnings = FALSE)
w <- tt({
  for (n in names(ART)) {
    d <- get(paste0("dt_", n))
    gcols <- intersect(c("metric", "scenario_ui_label", "granularity"), names(d))
    for (g in split(d, by = gcols, drop = TRUE)) {
      tag <- paste(gsub("[^A-Za-z0-9]+", "_", unlist(g[1, ..gcols])), collapse = "__")
      fwrite(g, file.path(PART, paste0(n, "__", tag, ".csv")))
    }
  }
})
cat(sprintf("  wrote %d partitions in %.2fs  size=%.1f MB\n",
            length(list.files(PART)), w$s, mb(PART)))
pfile <- list.files(PART, pattern = "viewer_hdd__HDD___EDB__Enterprise__Forest", full.names = TRUE)
if (length(pfile)) {
  r <- tt(fread(pfile[1], showProgress = FALSE))
  d <- tt(r$v[grepl("NAMPRD07", key)])
  add("B1", "CSV partitioned", "HDD - EDB", "Enterprise", "Forest", "NAMPRD07",
      nrow(d$v), r$s + d$s, "OK", "cold read of one partition only")
}

cat("\n=== OPTION C: DuckDB ===\n")
DB <- file.path(BENCH, "r6_phase1.duckdb")
if (file.exists(DB)) file.remove(DB)
con <- dbConnect(duckdb::duckdb(shared_home = FALSE), dbdir = DB)
b <- tt({
  for (n in names(ART)) {
    p <- normalizePath(file.path(R6, ART[[n]]), winslash = "/")
    dbExecute(con, sprintf("CREATE TABLE %s AS SELECT * FROM read_csv_auto('%s')", n, p))
  }
})
cat(sprintf("  built in %.2fs  size=%.1f MB\n", b$s,
            round(file.info(DB)$size / 1048576, 2)))
dbDisconnect(con, shutdown = TRUE)

q <- function(sql) { con <- dbConnect(duckdb::duckdb(shared_home = FALSE), dbdir = DB, read_only = TRUE)
  r <- tt(dbGetQuery(con, sql)); dbDisconnect(con, shutdown = TRUE); r }
r <- q("SELECT * FROM viewer_hdd WHERE metric='HDD - EDB' AND scenario_ui_label='Enterprise' AND granularity='Forest' AND key LIKE '%NAMPRD07%'")
add("B1", "DuckDB", "HDD - EDB", "Enterprise", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "cold connect and query")
r <- q("SELECT * FROM viewer_hdd WHERE metric='HDD - EDB' AND scenario_ui_label='Consumer' AND granularity='Forest' AND key LIKE '%NAMPRD07%'")
add("B2", "DuckDB", "HDD - EDB", "Consumer", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "cold connect and query")
r <- q("SELECT * FROM viewer_hdd WHERE metric='HDD - Basilisk' AND granularity='Forest' AND key LIKE '%NAMPRD07%'")
add("B3", "DuckDB", "HDD - Basilisk", "Basilisk", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "cold connect and query")
r <- q("SELECT * FROM forecast_ssd WHERE scenario_ui_label='Low Volume No Efficiency' AND key LIKE '%NAMPRD07%'")
add("B4", "DuckDB", "SSD - Phoenix", "Low Volume No Efficiency", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "")
r <- q("SELECT * FROM forecast_ssd WHERE scenario_ui_label='Low Volume With Efficiency' AND key LIKE '%NAMPRD07%'")
add("B5", "DuckDB", "SSD - Phoenix", "Low Volume With Efficiency", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "")
r <- q(sprintf("SELECT * FROM viewer_hdd WHERE granularity='Region' AND key='%s'", region_key))
add("B6", "DuckDB", "HDD", "all", "Region", region_key, nrow(r$v), r$s, "OK", "")
r <- q("SELECT DISTINCT metric, scenario_ui_label, granularity FROM viewer_hdd")
add("B7", "DuckDB", "all", "all", "all", "-", nrow(r$v), r$s, "OK", "scenario dropdown metadata")
r <- q("SELECT DISTINCT key FROM viewer_hdd WHERE metric='HDD - EDB' AND scenario_ui_label='Enterprise' AND granularity='Forest'")
add("B8", "DuckDB", "HDD - EDB", "Enterprise", "Forest", "-", nrow(r$v), r$s, "OK", "key dropdown metadata")

cat("\n=== OPTION D: Parquet partitioned ===\n")
PQ <- file.path(BENCH, "parquet"); dir.create(PQ, showWarnings = FALSE)
b <- tt({
  write_dataset(dt_viewer_hdd, file.path(PQ, "viewer_hdd"),
                partitioning = c("metric", "scenario_ui_label", "granularity"), format = "parquet")
  write_dataset(dt_forecast_hdd, file.path(PQ, "forecast_hdd"),
                partitioning = c("metric", "scenario_ui_label", "granularity"), format = "parquet")
  write_dataset(dt_forecast_ssd, file.path(PQ, "forecast_ssd"),
                partitioning = c("scenario_ui_label"), format = "parquet")
})
cat(sprintf("  written in %.2fs  size=%.1f MB\n", b$s, mb(PQ)))

pq <- function(path, expr_fn) { r <- tt({ ds <- open_dataset(path); expr_fn(ds) }); r }
r <- pq(file.path(PQ, "viewer_hdd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::filter(ds, metric == "HDD - EDB", scenario_ui_label == "Enterprise",
                granularity == "Forest", grepl("NAMPRD07", key)))))
add("B1", "Parquet partitioned", "HDD - EDB", "Enterprise", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "lazy scan of one partition")
r <- pq(file.path(PQ, "viewer_hdd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::filter(ds, metric == "HDD - EDB", scenario_ui_label == "Consumer",
                granularity == "Forest", grepl("NAMPRD07", key)))))
add("B2", "Parquet partitioned", "HDD - EDB", "Consumer", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "")
r <- pq(file.path(PQ, "viewer_hdd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::filter(ds, metric == "HDD - Basilisk", granularity == "Forest", grepl("NAMPRD07", key)))))
add("B3", "Parquet partitioned", "HDD - Basilisk", "Basilisk", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "")
r <- pq(file.path(PQ, "forecast_ssd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::filter(ds, scenario_ui_label == "Low Volume No Efficiency", grepl("NAMPRD07", key)))))
add("B4", "Parquet partitioned", "SSD - Phoenix", "Low Volume No Efficiency", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "")
r <- pq(file.path(PQ, "forecast_ssd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::filter(ds, scenario_ui_label == "Low Volume With Efficiency", grepl("NAMPRD07", key)))))
add("B5", "Parquet partitioned", "SSD - Phoenix", "Low Volume With Efficiency", "Forest", "NAMPRD07", nrow(r$v), r$s, "OK", "")
r <- pq(file.path(PQ, "viewer_hdd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::filter(ds, granularity == "Region", key == region_key))))
add("B6", "Parquet partitioned", "HDD", "all", "Region", region_key, nrow(r$v), r$s, "OK", "")
r <- pq(file.path(PQ, "viewer_hdd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::distinct(dplyr::select(ds, metric, scenario_ui_label, granularity)))))
add("B7", "Parquet partitioned", "all", "all", "all", "-", nrow(r$v), r$s, "OK", "scenario dropdown metadata")
r <- pq(file.path(PQ, "viewer_hdd"), function(ds) as.data.frame(dplyr::collect(
  dplyr::distinct(dplyr::select(dplyr::filter(ds, metric == "HDD - EDB",
    scenario_ui_label == "Enterprise", granularity == "Forest"), key)))))
add("B8", "Parquet partitioned", "HDD - EDB", "Enterprise", "Forest", "-", nrow(r$v), r$s, "OK", "key dropdown metadata")

cat("\n=== OPTION E: UI metadata slices ===\n")
META <- file.path(BENCH, "ui_metadata"); dir.create(META, showWarnings = FALSE)
b <- tt({
  fwrite(unique(rbind(
    dt_viewer_hdd[, .(metric, scenario_ui_label, granularity, page = "viewer")],
    dt_forecast_hdd[, .(metric, scenario_ui_label, granularity, page = "forecast")],
    dt_forecast_ssd[, .(metric, scenario_ui_label, granularity = "Forest", page = "forecast")]
  )), file.path(META, "available_scenarios.csv"))
  fwrite(unique(rbind(
    dt_viewer_hdd[, .(metric, scenario_ui_label, granularity, key = as.character(key))],
    dt_forecast_ssd[, .(metric, scenario_ui_label, granularity = "Forest", key = as.character(key))]
  )), file.path(META, "available_keys.csv"))
  fwrite(unique(rbind(
    dt_forecast_hdd[, .(metric, scenario_ui_label, granularity,
                        forecast_version = as.character(forecast_version))],
    dt_forecast_ssd[, .(metric, scenario_ui_label, granularity = "Forest",
                        forecast_version = as.character(forecast_version))]
  )), file.path(META, "available_versions.csv"))
  fwrite(unique(dt_viewer_hdd[, .(metric, scenario_ui_label, granularity, model_type, raw_type)]),
         file.path(META, "available_model_types.csv"))
})
cat(sprintf("  built in %.2fs  size=%.2f MB\n", b$s, mb(META)))
for (f in list.files(META, full.names = TRUE)) {
  r <- tt(fread(f, showProgress = FALSE))
  cat(sprintf("    %-28s rows=%7s  load=%.3fs  %.2f MB\n", basename(f),
              format(nrow(r$v), big.mark = ","), r$s, file.info(f)$size / 1048576))
  add(if (grepl("scenarios", f)) "B7" else if (grepl("keys", f)) "B8" else "B9",
      "UI metadata slice", "-", "-", "-", "-", nrow(r$v), r$s, "OK", basename(f))
}

out <- rbindlist(res)
setnames(out, "key_value", "key")
fwrite(out, file.path(R5B, "benchmark_results.csv"))
cat(sprintf("\nwrote benchmark_results.csv: %d rows\n", nrow(out)))

sizes <- data.table(
  option = c("A CSV plain", "B CSV partitioned", "C DuckDB", "D Parquet partitioned", "E UI metadata"),
  size_mb = c(round(sum(file.info(file.path(R6, ART))$size) / 1048576, 2), mb(PART),
              round(file.info(DB)$size / 1048576, 2), mb(PQ), mb(META)),
  build_seconds = c(NA, NA, NA, NA, NA))
fwrite(sizes, file.path(R5B, "storage_sizes.csv"))
print(sizes)
cat(sprintf("\nCSV cold load total = %.2fs, in-memory footprint = %.1f MB\n",
            total_csv_load, total_csv_mem))
cat("BENCHMARK_DONE\n")
