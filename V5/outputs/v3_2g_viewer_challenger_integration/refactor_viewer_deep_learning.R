# =============================================================================
# V3.2G (final refactor) | Forecast Viewer -> 4 clean families, Deep Learning
# =============================================================================
# Purpose: simplify the Forecast Viewer artifact to four governed families:
#   growth_baseline, statistical, machine_learning, lightweight_neural.
# The lightweight_neural family is relabeled "Deep Learning" in the UI and now
# exposes ONLY the three final deep-learning challengers selected during the
# codebase review (V3.2D/V3.2E):
#   SMLP-TCN, NLIN-DLIN_FIXED, FNAR-V2
# These are mapped into the lightweight_neural family as HISTORICAL BACKTEST
# lines. The original FastNeuralAR_MLP viewer rows and the standalone
# evaluation_challenger group are removed from the Viewer.
#
# GOVERNANCE GUARDRAILS (reaffirmed):
#   * Backtest visualization ONLY. No future forecasts generated.
#   * No change to forecasts.csv, intervals, champion (ETS Explicit stays),
#     promotion/governance (0 promoted), or any model run.
#   * is_challenger = TRUE, is_selected_champion = FALSE for appended rows.
#   * Idempotent: strips prior challenger/eval rows + FastNeuralAR_MLP first.
#   * Backs up the artifact before writing.
#   * Data preservation: full_candidate_outputs.csv and governed summaries are
#     untouched; dropped ML/DL candidates remain available there.
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

log("V3.2G final refactor starting. v3_root = ", v3_root)

# ---- The three final deep-learning challengers to expose --------------------
DL_KEEP <- c("SMLP-TCN", "NLIN-DLIN_FIXED", "FNAR-V2")
# All six evaluated candidate codes (used to strip any prior appends).
ALL_CANDIDATE_CODES <- c("ENET-RIDGE", "FNAR-V2", "LGBM-IMP-v2",
                         "NLIN-DLIN_FIXED", "SMLP-TCN", "XGB-IMP-v2")
DL_FAMILY <- "lightweight_neural"   # relabeled "Deep Learning" in the UI
LEGACY_DL_MODEL <- "FastNeuralAR_MLP"  # original viewer DL row to remove

# ---- Read everything as character to preserve exact numeric text ------------
viewer <- read_csv(viewer_csv, col_types = cols(.default = col_character()),
                   progress = FALSE)
cand   <- read_csv(cand_csv,   col_types = cols(.default = col_character()),
                   progress = FALSE)

viewer_cols <- names(viewer)
log("Viewer artifact columns: ", paste(viewer_cols, collapse = ", "))
log("Viewer rows (incoming): ", nrow(viewer))
log("Candidate rows (raw): ", nrow(cand))

# ---- Backup the incoming artifact (reversibility) ---------------------------
backup_path <- file.path(log_dir,
                         paste0("forecast_viewer_model_outputs_BACKUP_", ts, ".csv"))
file.copy(viewer_csv, backup_path, overwrite = FALSE)
log("Backup written: ", backup_path)

# ---- Idempotency: strip prior challenger appends, eval group, legacy DL ------
before <- nrow(viewer)
drop_mask <-
  (viewer$model_family == "evaluation_challenger") |
  (viewer$model_name %in% ALL_CANDIDATE_CODES) |
  (viewer$model_name == LEGACY_DL_MODEL)
viewer <- viewer[!drop_mask, , drop = FALSE]
log("Stripped ", before - nrow(viewer),
    " rows (prior eval/challenger rows + ", LEGACY_DL_MODEL, ").")

# ---- Keep only the three final DL candidate forecast rows -------------------
keep <- cand$candidate_id %in% DL_KEEP &
        !is.na(cand$forecast_value) & nzchar(trimws(cand$forecast_value)) &
        !is.na(cand$actual_value)   & nzchar(trimws(cand$actual_value))   &
        (is.na(cand$status) | tolower(trimws(cand$status)) == "ok")
cand <- cand[keep, , drop = FALSE]
log("DL candidate rows kept (valid): ", nrow(cand))
log("DL candidate models kept: ",
    paste(sort(unique(cand$candidate_id)), collapse = ", "))

# ---- Map DL candidate rows into the Viewer contract -------------------------
mapped <- data.frame(
  series_key           = cand$series_key,
  series_label         = cand$series_key,
  date                 = cand$forecast_date,
  actual_value         = cand$actual_value,
  model_name           = cand$candidate_id,          # short code (SMLP-TCN, ...)
  model_origin         = "challenger",
  model_family         = DL_FAMILY,                  # -> "Deep Learning" in UI
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

missing_in_map <- setdiff(viewer_cols, names(mapped))
if (length(missing_in_map)) {
  for (mc in missing_in_map) mapped[[mc]] <- NA_character_
}
mapped <- mapped[, viewer_cols, drop = FALSE]

log("Mapped Deep Learning rows: ", nrow(mapped))
log("Deep Learning series count: ", length(unique(mapped$series_key)))

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

dl <- check[check$model_family == DL_FAMILY, , drop = FALSE]
dl_models <- sort(unique(dl$model_name))
log("Deep Learning family models: ", paste(dl_models, collapse = ", "))
log("Champion rows untouched (is_selected_champion=True count): ",
    sum(check$is_selected_champion == "True", na.rm = TRUE))

# Hard assertions for the final state.
stopifnot(setequal(unique(check$model_family),
                   c("growth_baseline", "statistical",
                     "machine_learning", "lightweight_neural")))
stopifnot(setequal(dl_models, DL_KEEP))
stopifnot(!any(check$model_name == LEGACY_DL_MODEL))

val <- data.frame(
  check = c("families", "deep_learning_models", "deep_learning_series",
            "deep_learning_rows", "total_rows", "champion_rows",
            "legacy_dl_removed", "backup_exists"),
  value = c(paste(sort(unique(check$model_family)), collapse = "|"),
            paste(dl_models, collapse = "|"),
            length(unique(dl$series_key)),
            nrow(dl),
            nrow(check),
            sum(check$is_selected_champion == "True", na.rm = TRUE),
            as.integer(!any(check$model_name == LEGACY_DL_MODEL)),
            as.integer(file.exists(backup_path))),
  stringsAsFactors = FALSE
)
write_csv(val, file.path(script_dir, "v3_2g_refactor_validation.csv"))

writeLines(log_lines, file.path(log_dir, paste0("refactor_run_", ts, ".log")))
log("V3.2G final refactor complete.")
