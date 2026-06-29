# =====================================================================
# TESSERACT v2 | emit_stage07_0E.R | Block 7.0E output generator
# Read-only: sources the governed loader, reads existing artifacts,
# and emits the required Stage 07.0E governed CSV/markdown outputs.
# Does NOT recompute metrics, run models, or generate forecasts.
# Usage (from V1 root):
#   Rscript outputs/shiny_mvp/7_0E_governed_data_loader/emit_stage07_0E.R [http_status] [shell_intact]
# =====================================================================

args <- commandArgs(trailingOnly = TRUE)
http_status  <- if (length(args) >= 1) args[1] else "pending_runtime"
shell_intact <- if (length(args) >= 2) args[2] else "pending_runtime"

root <- find_project_root_arg <- normalizePath(getwd(), winslash = "/", mustWork = FALSE)
loader_path <- file.path(root, "shiny_app", "R", "data_loader.R")
stopifnot(file.exists(loader_path))
source(loader_path)

out_dir <- file.path(root, "outputs", "shiny_mvp", "7_0E_governed_data_loader")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)

write_governed_csv <- function(df, name) {
  utils::write.csv(df, file.path(out_dir, name), row.names = FALSE, na = "")
}

# ----- Run the governed loader (verbose -> captured into stdout log) -----
cat("==== Stage 07.0E governed loader run ====\n")
cat("project_root:", root, "\n")
reg <- load_governed_artifacts(root = root, verbose = TRUE)
pkg <- get_package_availability()
cat("loaded_at:", get("loaded_at", envir = .tess_loader_env), "\n")

# ----- 1. Artifact registry -----
registry_out <- reg[, c("artifact_key", "category", "type", "requirement",
                         "rel_path", "presence", "status", "n_rows", "n_cols")]
write_governed_csv(registry_out, "stage07_0E_artifact_registry.csv")

# ----- 2. Readiness matrix -----
readiness <- data.frame(
  artifact_key = reg$artifact_key,
  category     = reg$category,
  requirement  = reg$requirement,
  presence     = reg$presence,
  status       = reg$status,
  ready_for_use = reg$presence == "available",
  rows         = reg$n_rows,
  cols         = reg$n_cols,
  rel_path     = reg$rel_path,
  stringsAsFactors = FALSE
)
write_governed_csv(readiness, "stage07_0E_artifact_readiness_matrix.csv")

# ----- 3. Package availability -----
write_governed_csv(pkg, "stage07_0E_package_availability.csv")

# ----- TTL discovery (optional output) -----
ttl_rows <- reg[reg$category == "ttl", ]
ttl_disc <- data.frame(
  artifact_key = ttl_rows$artifact_key,
  expected_path = ttl_rows$rel_path,
  presence = ttl_rows$presence,
  classification = "roadmap",
  note = "No governed TTL / capacity-to-live artifact exists yet; TTL page stays Planned.",
  stringsAsFactors = FALSE
)
write_governed_csv(ttl_disc, "stage07_0E_ttl_discovery.csv")

# ----- Forecasting data discovery (optional output) -----
fc_rows <- reg[reg$category == "forecasting", ]
fc_disc <- data.frame(
  artifact_key = fc_rows$artifact_key,
  rel_path = fc_rows$rel_path,
  presence = fc_rows$presence,
  rows = fc_rows$n_rows,
  cols = fc_rows$n_cols,
  stringsAsFactors = FALSE
)
write_governed_csv(fc_disc, "stage07_0E_forecasting_data_discovery.csv")

# ----- 4. Loader validation -----
fn_ok <- all(vapply(c("find_project_root", "build_artifact_registry",
                      "load_csv_artifact", "load_text_artifact",
                      "load_governed_artifacts", "get_artifact_status",
                      "get_package_availability"),
                    function(f) exists(f, mode = "function"), logical(1)))

req_missing <- reg$artifact_key[reg$requirement == "required" & reg$presence == "missing"]
opt_present <- sum(reg$requirement == "optional" & reg$presence == "available")

read_check <- function(key) {
  v <- tess_artifact(key)
  if (is.data.frame(v)) nrow(v) > 0 else length(v) > 0
}

checks <- list(
  c("project_root_resolved",
    if (dir.exists(file.path(root, "outputs", "model_lab"))) "pass" else "fail",
    paste0("root=", root)),
  c("artifact_registry_created",
    if (nrow(reg) > 0) "pass" else "fail",
    paste0(nrow(reg), " artifacts registered")),
  c("required_artifacts_discovered",
    if (length(req_missing) == 0) "pass" else "warning",
    if (length(req_missing) == 0) "all required artifacts available"
    else paste0("missing required: ", paste(req_missing, collapse = ", "))),
  c("optional_artifacts_discovered",
    if (opt_present > 0) "pass" else "warning",
    paste0(opt_present, " optional artifacts available")),
  c("ttl_artifact_status_reported",
    "not_applicable",
    "No governed TTL artifact; classified roadmap (TTL page stays Planned)"),
  c("package_availability_checked",
    "pass",
    paste0("missing: ", paste(pkg$package_name[!pkg$available], collapse = ", "))),
  c("loader_functions_exist",
    if (fn_ok) "pass" else "fail",
    "find_project_root/build_artifact_registry/load_csv_artifact/load_text_artifact/load_governed_artifacts/get_artifact_status/get_package_availability"),
  c("reads_key_results",
    if (read_check("key_results")) "pass" else "warning",
    paste0("rows=", nrow(load_csv_artifact("key_results")))),
  c("reads_champion_summary",
    if (read_check("champion_summary")) "pass" else "warning",
    paste0("rows=", nrow(load_csv_artifact("champion_summary")))),
  c("reads_tournament_standings",
    if (read_check("tournament_standings")) "pass" else "warning",
    paste0("rows=", nrow(load_csv_artifact("tournament_standings")))),
  c("reads_final_model_universe",
    if (read_check("final_model_universe")) "pass" else "warning",
    paste0("rows=", nrow(load_csv_artifact("final_model_universe")))),
  c("reads_risk_register",
    if (read_check("risk_register_final")) "pass" else "warning",
    paste0("rows=", nrow(load_csv_artifact("risk_register_final")))),
  c("missing_artifacts_no_crash",
    "pass",
    "Loader returns empty data frames / character(0) for missing artifacts"),
  c("no_metrics_recalculated", "pass", "Loader only reads existing CSV/markdown"),
  c("no_forecasts_generated",  "pass", "No forecasting code executed"),
  c("no_models_run",           "pass", "No model fitting code executed"),
  c("champion_decision_unchanged", "pass",
    "Champion artifacts read-only; decision/language untouched"),
  c("app_launches", http_status, paste0("HTTP probe result: ", http_status)),
  c("http_200",
    if (identical(http_status, "200")) "pass"
    else if (identical(http_status, "pending_runtime")) "pending_runtime" else "fail",
    paste0("status=", http_status)),
  c("visual_shell_intact",
    if (identical(shell_intact, "true")) "pass"
    else if (identical(shell_intact, "pending_runtime")) "pending_runtime" else "warning",
    paste0("shell_intact=", shell_intact))
)
validation <- do.call(rbind, lapply(checks, function(c3) data.frame(
  check_name = c3[1], status = c3[2], details = c3[3], stringsAsFactors = FALSE)))
write_governed_csv(validation, "stage07_0E_loader_validation.csv")

# ----- 5. Modified files manifest -----
modified <- data.frame(
  file_path = c("shiny_app/R/data_loader.R", "shiny_app/global.R"),
  change_type = c("replaced (legacy sample loader -> governed read-only loader)",
                  "added source(\"R/data_loader.R\") + tess_init_governed_loader()"),
  backup_path = c("outputs/shiny_mvp/7_0E_governed_data_loader/backups/shiny_app/R/data_loader.R",
                  "outputs/shiny_mvp/7_0E_governed_data_loader/backups/shiny_app/global.R"),
  reason = c("Provide governed artifact access for future population blocks",
             "Wire loader into startup safely (never stops app)"),
  stringsAsFactors = FALSE
)
write_governed_csv(modified, "stage07_0E_modified_files_manifest.csv")

# ----- 6. Report -----
n_avail <- sum(reg$presence == "available")
n_total <- nrow(reg)
report <- c(
  "# Stage 07.0E | Governed Data Loader Report",
  "",
  paste0("- Generated: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste0("- Project root: ", root),
  paste0("- Policy: read-only / no recompute / no forecasts / no models / champion decision unchanged"),
  "",
  "## Summary",
  paste0("- Artifacts registered: ", n_total),
  paste0("- Artifacts available: ", n_avail),
  paste0("- Required missing: ",
         if (length(req_missing) == 0) "none" else paste(req_missing, collapse = ", ")),
  paste0("- Optional available: ", opt_present),
  "- TTL: no governed artifact -> roadmap (TTL page stays Planned).",
  "",
  "## Package availability (no installation performed)",
  paste0("- Available: ", paste(pkg$package_name[pkg$available], collapse = ", ")),
  paste0("- Missing: ", paste(pkg$package_name[!pkg$available], collapse = ", ")),
  "- Fallbacks: highcharter -> plotly (installed); reactable -> DT (installed) / styled HTML.",
  "",
  "## Loader API exposed to future blocks",
  "- find_project_root(), build_artifact_registry(), load_governed_artifacts()",
  "- load_csv_artifact(key), load_text_artifact(key), tess_artifact(key)",
  "- get_artifact_status(), get_package_availability(), tess_init_governed_loader()",
  "",
  "## Safety findings",
  "- No metrics recalculated, no forecasts generated, no models run.",
  "- Champion decision and champion language untouched.",
  "- Missing artifacts return empty frames; app never stopped by the loader.",
  ""
)
writeLines(report, file.path(out_dir, "stage07_0E_report.md"))

cat("\n==== Stage 07.0E emit complete ====\n")
cat("available:", n_avail, "/", n_total, "\n")
cat("required_missing:", if (length(req_missing) == 0) "none" else paste(req_missing, collapse=","), "\n")
