setwd("V6/shiny_app")
source("R/scenario_resolver.R")

cat("storage ready:", sr_storage_ready(), "\n")
cat("wal files:", paste(list.files(dirname(sr_paths()$duckdb), pattern = "wal|tmp",
                                   all.files = TRUE), collapse = " | "), "\n")

t0 <- Sys.time()
r <- resolve_series_query("HDD - Basilisk", "Basilisk", "Region", "apc-Dedicated",
                          page = "viewer")
cat("resolve:", r$status, r$table_name, r$expected_mode,
    sprintf("%.3fs", as.numeric(difftime(Sys.time(), t0, units = "secs"))), "\n")

t0 <- Sys.time()
f <- fetch_series_preview("HDD - Basilisk", "Basilisk", "Region", "apc-Dedicated",
                          page = "viewer", limit = NULL)
cat("fetch rows:", f$rows, sprintf("%.3fs", f$elapsed), "\n")
str(head(f$data, 2))

v <- get_available_versions("HDD - Basilisk", "Basilisk", "Region")
cat("versions:", v$count, "applies:", v$applies, "\n")
m <- get_available_model_types("HDD - Basilisk", "Basilisk", "Region")
cat("model applies:", m$applies, "types:", length(m$model_types), "\n")
cat("by_family class:", class(m$by_family), "names:",
    paste(names(m$by_family), collapse = " | "), "\n")
cat("DONE\n")
