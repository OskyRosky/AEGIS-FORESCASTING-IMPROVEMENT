#!/usr/bin/env Rscript
# =====================================================================
# V3.2H  MODEL CONSISTENCY FIX  ---  Full validation
# Loads the governed Shiny environment, renders the three Models pages,
# and writes outputs/v3_2h_model_consistency_fix/v3_2h_validation.csv
# Usage: Rscript validate_v3_2h.R <http_status>
# =====================================================================
suppressWarnings(suppressMessages(options(stringsAsFactors = FALSE)))

args <- commandArgs(trailingOnly = TRUE)
http_status <- if (length(args) >= 1) args[[1]] else "unknown"

# ---- locate root + enter shiny_app working dir ----
sa <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", sa[grep("^--file=", sa)])
if (length(file_arg) == 0) file_arg <- "."
root <- normalizePath(file.path(dirname(file_arg), "..", ".."), winslash = "/", mustWork = FALSE)
if (!dir.exists(file.path(root, "shiny_app"))) root <- normalizePath(getwd(), winslash = "/", mustWork = FALSE)
cat(sprintf("[v3.2h] root: %s\n", root))

canon_path <- file.path(root, "data/processed/model_universe_canonical.csv")
canon_mtime <- if (file.exists(canon_path)) file.info(canon_path)$mtime else Sys.time()

old_wd <- getwd()
setwd(file.path(root, "shiny_app"))
suppressWarnings(suppressMessages({
  source("global.R")
  source("ui/header.R")
  source("ui/body.R")
}))

as_html <- function(x) paste(as.character(x), collapse = "\n")
sec_uni  <- tryCatch(as_html(section_universe()),  error = function(e) paste("ERROR:", conditionMessage(e)))
sec_tour <- tryCatch(as_html(section_tournament()), error = function(e) paste("ERROR:", conditionMessage(e)))
sec_champ<- tryCatch(as_html(section_champion()),   error = function(e) paste("ERROR:", conditionMessage(e)))

# canonical universe (single source of truth)
uni <- tryCatch(universe_normalized(), error = function(e) data.frame())
fam <- if (is.data.frame(uni) && "model_family" %in% names(uni)) table(uni$model_family) else integer(0)
dl_models <- if (is.data.frame(uni)) sort(uni$model_name[uni$model_family == "deep_learning"]) else character(0)
champ <- if (is.data.frame(uni)) uni$model_name[uni$selected_champion %in% TRUE] else character(0)
vis <- if (is.data.frame(uni) && "included_in_tournament" %in% names(uni))
  uni[uni$included_in_tournament %in% TRUE, , drop = FALSE] else uni

# forecast viewer families
fv <- tryCatch(load_csv_artifact("forecast_viewer_full"), error = function(e) data.frame())
fv_fams <- if (is.data.frame(fv) && "model_family" %in% names(fv)) length(unique(fv$model_family)) else NA_integer_

# mtime-based "untouched" checks: files NOT written after the canonical artifact
older_than_canon <- function(path) {
  if (!file.exists(path)) return(TRUE)  # absent -> certainly not changed by us
  isTRUE(file.info(path)$mtime <= canon_mtime + 2)
}
tree_max_mtime <- function(dir) {
  if (!dir.exists(dir)) return(as.POSIXct(0, origin = "1970-01-01"))
  fs <- list.files(dir, recursive = TRUE, full.names = TRUE, all.files = TRUE)
  if (length(fs) == 0) return(as.POSIXct(0, origin = "1970-01-01"))
  max(file.info(fs)$mtime, na.rm = TRUE)
}
v1_dir <- file.path(root, "..", "V1")
v2_dir <- file.path(root, "..", "V2")
v1_untouched <- tree_max_mtime(v1_dir) <= canon_mtime + 2
v2_untouched <- tree_max_mtime(v2_dir) <= canon_mtime + 2

# governance / forecasts / intervals unchanged (mtime older than canonical)
gov_files <- list.files(file.path(root, "outputs/governance"), recursive = TRUE, full.names = TRUE)
gov_unchanged <- length(gov_files) == 0 || all(file.info(gov_files)$mtime <= canon_mtime + 2)

no_v33 <- !dir.exists(file.path(root, "..", "V3.3")) &&
  length(list.files(file.path(root, "outputs"), pattern = "v3_3", ignore.case = TRUE)) == 0
no_v4  <- !dir.exists(file.path(root, "..", "V4")) &&
  length(list.files(file.path(root, "outputs"), pattern = "^v4", ignore.case = TRUE)) == 0

stderr_log <- file.path(root, "outputs/v3_2h_model_consistency_fix/logs/v3_2h_app_stderr.log")
listening <- file.exists(stderr_log) &&
  any(grepl("Listening on http", readLines(stderr_log, warn = FALSE)))

has <- function(html, pat) isTRUE(grepl(pat, html, fixed = TRUE))
ci_absent <- function(html, pat) !isTRUE(grepl(pat, html, ignore.case = TRUE))

chk <- function(name, pass, detail = "") {
  data.frame(check = name, pass = isTRUE(pass), detail = as.character(detail),
             stringsAsFactors = FALSE)
}

checks <- rbind(
  chk("canonical_model_universe_has_15_models", is.data.frame(uni) && nrow(uni) == 15,
      paste("rows =", if (is.data.frame(uni)) nrow(uni) else NA)),
  chk("growth_baseline_count_4", isTRUE(unname(fam["growth_baseline"]) == 4),
      paste("count =", unname(fam["growth_baseline"]))),
  chk("statistical_count_5", isTRUE(unname(fam["statistical"]) == 5),
      paste("count =", unname(fam["statistical"]))),
  chk("machine_learning_count_3", isTRUE(unname(fam["machine_learning"]) == 3),
      paste("count =", unname(fam["machine_learning"]))),
  chk("deep_learning_count_3", isTRUE(unname(fam["deep_learning"]) == 3),
      paste("count =", unname(fam["deep_learning"]))),
  chk("deep_learning_models_correct",
      identical(dl_models, sort(c("SMLP-TCN", "NLIN-DLIN_FIXED", "FNAR-V2"))),
      paste(dl_models, collapse = "; ")),
  chk("fastneuralar_original_not_active",
      is.data.frame(uni) && !("FastNeuralAR_MLP" %in% uni$model_name), "retired"),
  chk("lightweight_neural_not_user_facing",
      identical(unname(FVP_FAMILY_LABELS["lightweight_neural"]), "Deep Learning") &&
        ci_absent(sec_uni, "lightweight neural"),
      paste0("label=", unname(FVP_FAMILY_LABELS["lightweight_neural"]),
             "; universe_html_clean=", ci_absent(sec_uni, "lightweight neural"))),
  chk("universe_page_uses_15_models", is.data.frame(vis) && nrow(vis) == 15,
      paste("visible =", if (is.data.frame(vis)) nrow(vis) else NA)),
  chk("governed_model_table_uses_15_or_is_relabelled",
      has(sec_uni, "Current model universe (15 models)"), "relabelled table heading present"),
  chk("tournament_page_no_incorrect_13_model_claim",
      has(sec_tour, "Current model ranking (15 models)") &&
        has(sec_tour, "About the legacy 13-model tournament"),
      "15-model ranking present; 13-model evidence labelled legacy"),
  chk("tournament_pairwise_count_correct_or_labelled_legacy",
      has(sec_tour, "Legacy head-to-head evidence details (78 comparisons)"), "labelled legacy"),
  chk("evidence_tree_correct_or_labelled_legacy",
      has(sec_tour, "Legacy tournament evidence tree (13 models)"), "labelled legacy"),
  chk("league_view_correct_or_labelled_legacy",
      has(sec_tour, "Legacy tournament league view (13 models)"), "labelled legacy"),
  chk("champion_series_diagnostics_correct_or_labelled_legacy",
      has(sec_champ, "lead 0 individual series"), "scope note present"),
  chk("leadership_chart_includes_15_or_is_labelled_legacy",
      has(sec_champ, "Leadership count by model") && has(sec_champ, "lead 0 individual series"),
      "leadership chart present + DL 0-series scope note"),
  chk("forecast_viewer_still_has_4_families", isTRUE(fv_fams == 4),
      paste("families =", fv_fams)),
  chk("no_forecasts_csv_change", older_than_canon(file.path(root, "data/processed/forecasts.csv")),
      "forecasts.csv not modified by V3.2H"),
  chk("no_intervals_change",
      older_than_canon(file.path(root, "data/processed/forecasts_with_intervals_relative.csv")) &&
        older_than_canon(file.path(root, "data/processed/forecasts_with_intervals_relative_60d_calibrated.csv")),
      "interval artifacts not modified by V3.2H"),
  chk("no_champion_change",
      identical(as.character(champ), "ETS Explicit") &&
        isTRUE(abs(uni$median_mase[uni$model_name == "ETS Explicit"] - 6.901143533) < 1e-3),
      sprintf("champion=%s mase=%.4f", paste(champ, collapse = ";"),
              uni$median_mase[uni$model_name == "ETS Explicit"])),
  chk("no_governance_change", gov_unchanged, "governance artifacts unchanged"),
  chk("shiny_runs_locally", listening, "Listening on http found in stderr log"),
  chk("http_200", identical(as.character(http_status), "200"),
      paste("status =", http_status)),
  chk("v1_untouched", v1_untouched, "no V1 file newer than canonical"),
  chk("v2_untouched", v2_untouched, "no V2 file newer than canonical"),
  chk("v3_3_not_started", no_v33, "no V3.3 dir / outputs"),
  chk("v4_not_started", no_v4, "no V4 dir / outputs")
)

setwd(old_wd)
out_path <- file.path(root, "outputs/v3_2h_model_consistency_fix/v3_2h_validation.csv")
write.csv(checks, out_path, row.names = FALSE)

cat("\n[v3.2h] validation results:\n")
print(checks, right = FALSE)
cat(sprintf("\n[v3.2h] %d/%d checks passed\n", sum(checks$pass), nrow(checks)))
if (all(checks$pass)) cat("[v3.2h] STATUS: V3_2H_MODEL_CONSISTENCY_FIX_COMPLETED\n") else
  cat("[v3.2h] STATUS: FAILED -> ", paste(checks$check[!checks$pass], collapse = ", "), "\n")
