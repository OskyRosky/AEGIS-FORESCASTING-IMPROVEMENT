# =============================================================================
# V3.2G | Append evaluated challengers (V3.2D/V3.2E) into the Forecast Viewer
# =============================================================================
# Purpose: surface the 6 evaluated challenger candidates inside the Forecast
# Viewer (and Accuracy page, which shares the artifact) as HISTORICAL BACKTEST
# lines only. This script maps the candidate backtest outputs into the Viewer
# contract and appends them to data/processed/forecast_viewer_model_outputs.csv.
#
# GOVERNANCE GUARDRAILS (reaffirmed):
#   * Backtest visualization ONLY. No future forecasts generated.
#   * No change to forecasts.csv, intervals, champion (ETS Explicit stays),
#     promotion/governance (0 promoted), or any model run.
#   * is_challenger = TRUE, is_selected_champion = FALSE for all appended rows.
#   * Idempotent: removes any prior evaluation_challenger rows before appending.
#   * Backs up the original artifact before writing.
# =============================================================================

suppressWarnings(suppressMessages({
  library(readr)
}))

# ---- Resolve paths (script lives in V3/outputs/v3_2g_.../) -------------------
args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args[grepl("^--file=", args)])
script_dir <- if (length(file_arg)) dirname(normalizePath(file_arg)) else getwd()
v3_root <- normalizePath(file.path(script_dir, "..", ".."))

viewer_csv <- file.path(v3_root, "data", "processed",
                        "forecast_viewer_model_outputs.csv")
cand_csv   <- file.path(v3_root, "outputs", "v3_2b_model_candidates",
                        "candidate_outputs", "full_candidate_outputs.csv")
log_dir    <- file.path(script_dir, "logs")
dir.create(log_dir, showWarnings = FALSE, recursive = TRUE)

stopifnot(file.exists(viewer_csv), file.exists(cand_csv))

ts <- format(Sys.time(), "%Y%m%d_%H%M%S")
log_lines <- character(0)
log <- function(...) {
  msg <- paste0("[", format(Sys.time(), "%H:%M:%S"), "] ", paste0(..., collapse = ""))
  log_lines[[length(log_lines) + 1L]] <<- msg
  cat(msg, "\n")
}

log("V3.2G append starting. v3_root = ", v3_root)

# ---- Read everything as character to preserve exact numeric text ------------
viewer <- read_csv(viewer_csv, col_types = cols(.default = col_character()),
                   progress = FALSE)
cand   <- read_csv(cand_csv,   col_types = cols(.default = col_character()),
                   progress = FALSE)

viewer_cols <- names(viewer)
log("Viewer artifact columns: ", paste(viewer_cols, collapse = ", "))
log("Viewer rows (original): ", nrow(viewer))
log("Candidate rows (raw): ", nrow(cand))

# ---- Backup the original artifact (reversibility) ---------------------------
backup_path <- file.path(log_dir,
                         paste0("forecast_viewer_model_outputs_BACKUP_", ts, ".csv"))
file.copy(viewer_csv, backup_path, overwrite = FALSE)
log("Backup written: ", backup_path)

# ---- Idempotency: drop any previously appended challenger rows --------------
CHALLENGER_FAMILY <- "evaluation_challenger"
if ("model_family" %in% names(viewer)) {
  before <- nrow(viewer)
  viewer <- viewer[viewer$model_family != CHALLENGER_FAMILY, , drop = FALSE]
  removed <- before - nrow(viewer)
  if (removed > 0) log("Removed ", removed, " pre-existing challenger rows (idempotent rerun).")
}

# ---- Keep only valid candidate forecast rows --------------------------------
keep <- !is.na(cand$forecast_value) & nzchar(trimws(cand$forecast_value)) &
        !is.na(cand$actual_value)   & nzchar(trimws(cand$actual_value))   &
        (is.na(cand$status) | tolower(trimws(cand$status)) == "ok")
cand <- cand[keep, , drop = FALSE]
log("Candidate rows kept (valid): ", nrow(cand))

# ---- Map candidate rows into the Viewer contract ----------------------------
n <- nrow(cand)
mapped <- data.frame(
  series_key           = cand$series_key,
  series_label         = cand$series_key,
  date                 = cand$forecast_date,
  actual_value         = cand$actual_value,
  model_name           = cand$candidate_id,          # short code (ENET-RIDGE, ...)
  model_origin         = "challenger",
  model_family         = CHALLENGER_FAMILY,
  forecast_value       = cand$forecast_value,
  forecast_type        = "backtest",
  horizon_days         = cand$horizon,
  forecast_start_date  = cand$forecast_origin,
  run_id               = "v3_2d_e_evaluation",
  source_artifact      = "outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv",
  is_baseline          = "False",
  is_challenger        = "True",
  is_deferred          = "False",
  is_selected_champion = "False",
  risk_status          = "ok",
  lower_bound          = NA_character_,
  upper_bound          = NA_character_,
  interval_level       = NA_character_,
  stringsAsFactors     = FALSE,
  check.names          = FALSE
)

# Align to the exact viewer column order (defensive).
missing_in_map <- setdiff(viewer_cols, names(mapped))
if (length(missing_in_map)) {
  for (mc in missing_in_map) mapped[[mc]] <- NA_character_
}
mapped <- mapped[, viewer_cols, drop = FALSE]

log("Mapped challenger rows: ", nrow(mapped))
log("Challenger models: ",
    paste(sort(unique(mapped$model_name)), collapse = ", "))
log("Challenger series count: ", length(unique(mapped$series_key)))

# ---- Append and write -------------------------------------------------------
combined <- rbind(viewer, mapped)
log("Combined total rows: ", nrow(combined))

write_csv(combined, viewer_csv, na = "")
log("Wrote updated artifact: ", viewer_csv)

# ---- Validation summary -----------------------------------------------------
check <- read_csv(viewer_csv, col_types = cols(.default = col_character()),
                  progress = FALSE)
fam_tab <- as.data.frame(table(check$model_family), stringsAsFactors = FALSE)
names(fam_tab) <- c("model_family", "rows")
log("Post-write family counts:")
for (i in seq_len(nrow(fam_tab))) {
  log("  ", fam_tab$model_family[i], " = ", fam_tab$rows[i])
}

ch <- check[check$model_family == CHALLENGER_FAMILY, , drop = FALSE]
log("Challenger rows in artifact: ", nrow(ch))
log("Champion rows untouched (is_selected_champion=True count): ",
    sum(check$is_selected_champion == "True", na.rm = TRUE))

# Write validation CSV
val <- data.frame(
  check = c("challenger_models", "challenger_series", "challenger_rows",
            "total_rows", "champion_rows", "backup_exists"),
  value = c(length(unique(ch$model_name)),
            length(unique(ch$series_key)),
            nrow(ch),
            nrow(check),
            sum(check$is_selected_champion == "True", na.rm = TRUE),
            as.integer(file.exists(backup_path))),
  stringsAsFactors = FALSE
)
write_csv(val, file.path(script_dir, "v3_2g_validation.csv"))

writeLines(log_lines, file.path(log_dir, paste0("append_run_", ts, ".log")))
log("V3.2G append complete.")
