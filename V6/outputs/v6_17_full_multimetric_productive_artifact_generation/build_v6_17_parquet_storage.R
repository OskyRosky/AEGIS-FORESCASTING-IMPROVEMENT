args <- commandArgs(trailingOnly = TRUE)
if (length(args) != 1L) stop("Usage: build_v6_17_parquet_storage.R <output_dir>")

output_dir <- normalizePath(args[[1]], winslash = "/", mustWork = TRUE)
inputs <- c(
  forecast_viewer_model_outputs_v2_full =
    file.path(output_dir, "forecast_viewer_model_outputs_v2_full.csv"),
  forecast_forward_outputs_v6_17_full =
    file.path(output_dir, "forecast_forward_outputs_v6_17_full.csv")
)

for (name in names(inputs)) {
  input <- inputs[[name]]
  if (!file.exists(input)) stop("Missing full CSV: ", input)
  output <- file.path(output_dir, paste0(name, ".parquet"))
  table <- arrow::read_csv_arrow(input, as_data_frame = FALSE)
  arrow::write_parquet(table, output, compression = "zstd")
  observed <- arrow::read_parquet(output, as_data_frame = FALSE)$num_rows
  if (observed != table$num_rows) {
    stop("Parquet row mismatch for ", name, ": ", observed, " / ", table$num_rows)
  }
  cat(name, "rows=", observed, "path=", output, "\n")
  rm(table)
  gc()
}
