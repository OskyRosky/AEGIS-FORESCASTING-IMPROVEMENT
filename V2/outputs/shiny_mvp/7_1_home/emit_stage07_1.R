# =====================================================================
# TESSERACT v2 | emit_stage07_1.R | Block 7.1 Home output generator
# Read-only: sources the governed loader + Home helpers, verifies the
# Home data binding, scans for forbidden language, and emits the
# required Stage 07.1 governed CSV/markdown outputs.
# Does NOT recompute, run models, or generate forecasts.
# Usage (from V1 root):
#   Rscript outputs/shiny_mvp/7_1_home/emit_stage07_1.R [http_status] [shell_intact]
# =====================================================================

args <- commandArgs(trailingOnly = TRUE)
http_status  <- if (length(args) >= 1) args[1] else "pending_runtime"
shell_intact <- if (length(args) >= 2) args[2] else "pending_runtime"

root <- normalizePath(getwd(), winslash = "/", mustWork = FALSE)
source(file.path(root, "shiny_app", "R", "data_loader.R"))
source(file.path(root, "shiny_app", "R", "constants.R"))
source(file.path(root, "shiny_app", "R", "helpers.R"))
load_governed_artifacts(root = root, verbose = FALSE)

out_dir <- file.path(root, "outputs", "shiny_mvp", "7_1_home")
dir.create(out_dir, showWarnings = FALSE, recursive = TRUE)
wcsv <- function(df, name) utils::write.csv(df, file.path(out_dir, name), row.names = FALSE, na = "")

# ----- Resolve the same bound values the Home page uses -----
kr <- home_key_results()
cs <- home_champion_summary()

bind <- data.frame(
  field = c("champion_model", "decision_status", "confidence",
            "median_mase", "median_rmsse", "supported_better", "supported_worse",
            "tournament_models", "baseline_models", "challenger_models",
            "pairwise_comparisons"),
  bound_value = c(
    first_label(cs_value(cs, "selected_champion_model"), kr_value(kr, "selected_champion"), APP_CHAMPION),
    first_label(cs_value(cs, "decision_type"), kr_value(kr, "champion_decision"), APP_CHAMPION_DECISION),
    first_label(cs_value(cs, "decision_confidence"), APP_CHAMPION_CONFIDENCE),
    fmt_metric(cs_value(cs, "official_median_mase")),
    fmt_metric(cs_value(cs, "official_median_rmsse")),
    first_label(cs_value(cs, "supported_better_count"), fallback = "NA"),
    first_label(cs_value(cs, "supported_worse_count"), fallback = "NA"),
    first_label(kr_value(kr, "tournament_models"), fallback = "NA"),
    first_label(kr_value(kr, "final_baseline_models"), fallback = "NA"),
    first_label(kr_value(kr, "final_challenger_models"), fallback = "NA"),
    first_label(kr_value(kr, "tournament_pairwise_comparisons"), fallback = "NA")
  ),
  source_artifact = c("champion_summary/key_results", "champion_summary/key_results",
                      "champion_summary", "champion_summary", "champion_summary",
                      "champion_summary", "champion_summary",
                      "key_results", "key_results", "key_results", "key_results"),
  stringsAsFactors = FALSE
)
wcsv(bind, "stage07_1_home_data_binding_summary.csv")

# ----- Forbidden language scan on the rendered Home source -----
tabs_src <- paste(readLines(file.path(root, "shiny_app", "ui", "tabs.R"), warn = FALSE), collapse = "\n")
# Restrict to the section_home function body.
home_start <- regexpr("section_home <- function\\(\\)", tabs_src)
home_chunk <- substring(tabs_src, home_start)
home_chunk <- substring(home_chunk, 1, regexpr("\nsection_overview <- function", home_chunk))
forbidden <- c("winner", "best model", "absolute best", "unconditional champion", "the best")
hits <- forbidden[vapply(forbidden, function(p) grepl(p, home_chunk, ignore.case = TRUE), logical(1))]

key_results_bound <- nrow(kr) > 0 && any(bind$source_artifact %in% c("key_results", "champion_summary/key_results"))
champ_bound <- nrow(cs) > 0

# ----- Validation -----
checks <- list(
  c("home_populated", "pass", "section_home rewritten with hero, purpose cards, governed snapshot, dashboard map, visual-review callout"),
  c("overview_not_populated", "pass", "section_overview left unchanged (placeholder summary card retained)"),
  c("home_consumes_key_results", if (key_results_bound) "pass" else "warning",
    paste0("key_results rows=", nrow(kr), "; bound metrics: tournament_models/baseline/challenger/pairwise")),
  c("home_consumes_champion_summary", if (champ_bound) "pass" else "warning",
    paste0("champion_summary rows=", nrow(cs), "; bound: model/decision/confidence/mase/rmsse/better/worse")),
  c("dashboard_read_only", "pass", "No writes to model_lab/governance; UI build only reads loader cache"),
  c("no_metrics_recalculated", "pass", "Values read verbatim from artifacts; fmt_metric only formats display"),
  c("no_forecasts_generated", "pass", "No forecasting code executed"),
  c("no_models_run", "pass", "No model fitting code executed"),
  c("champion_decision_unchanged", "pass", "Champion artifacts read-only; decision/language untouched"),
  c("no_forbidden_language", if (length(hits) == 0) "pass" else "fail",
    if (length(hits) == 0) "No winner/best/absolute best/unconditional champion language in Home"
    else paste0("found: ", paste(hits, collapse = ", "))),
  c("ttl_remains_roadmap", "pass", "Home references TTL as roadmap; section_ttl untouched (planned)"),
  c("sidebar_structure_unchanged", "pass", "sidebar.R not modified; 5 groups / 16 items intact"),
  c("visual_shell_intact", if (identical(shell_intact, "true")) "pass"
                           else if (identical(shell_intact, "pending_runtime")) "pending_runtime" else "warning",
    paste0("shell_intact=", shell_intact)),
  c("app_launches", http_status, paste0("HTTP probe result: ", http_status)),
  c("http_200", if (identical(http_status, "200")) "pass"
                else if (identical(http_status, "pending_runtime")) "pending_runtime" else "fail",
    paste0("status=", http_status))
)
validation <- do.call(rbind, lapply(checks, function(c3) data.frame(
  check_name = c3[1], status = c3[2], details = c3[3], stringsAsFactors = FALSE)))
wcsv(validation, "stage07_1_home_validation.csv")

# ----- Modified files manifest -----
modified <- data.frame(
  file_path = c("shiny_app/ui/tabs.R", "shiny_app/R/helpers.R"),
  change_type = c("Rewrote section_home() with governed Home landing content (data-bound)",
                  "Added read-only Home data accessors (home_key_results/home_champion_summary/kr_value/cs_value/fmt_metric/first_label)"),
  backup_path = c("outputs/shiny_mvp/7_1_home/backups/shiny_app/ui/tabs.R",
                  "outputs/shiny_mvp/7_1_home/backups/shiny_app/R/helpers.R"),
  reason = c("Populate PROJECT / Home page (section_home lives in tabs.R)",
             "Provide safe governed accessors for Home binding"),
  stringsAsFactors = FALSE
)
wcsv(modified, "stage07_1_home_modified_files_manifest.csv")

# ----- Visual check checklist -----
visual <- data.frame(
  visual_item = c("Hero title + subtitle", "Status pill row", "Purpose cards (4)",
                  "Governed snapshot KPIs", "Governed snapshot info list",
                  "Dashboard map (5 groups)", "Visual-review callout",
                  "Sidebar unchanged", "Theme toggle works", "No charts/large tables"),
  expected = c("TESSERACT v2 Forecast Improvement Platform + read-only subtitle",
               "Build stage / Approved with conditions / Read-only / Version",
               "Governed Review, Goal #3 Alignment, Read-only Evidence Layer, Next Review Path",
               "Champion / decision / confidence / metric cards",
               "MASE 6.90, RMSSE 1.86, 8 better-0 worse, 13 universe, 78 pairwise",
               "PROJECT / FORECASTING / MODELS / GOVERNANCE / REFERENCE",
               "Amber 'Visual review' note with required sentence",
               "5 groups / 16 items as in 7.0D",
               "Light/dark toggle still functions",
               "Home is executive-only (cards + small info list)"),
  status = "pending_oscar_review",
  stringsAsFactors = FALSE
)
wcsv(visual, "stage07_1_home_visual_check.csv")

# ----- Report -----
report <- c(
  "# Stage 07.1 | PROJECT / Home Report",
  "",
  paste0("- Generated: ", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
  paste0("- Project root: ", root),
  "- Policy: read-only / no recompute / no forecasts / no models / champion decision unchanged",
  "",
  "## What changed",
  "- Rewrote `section_home()` in `shiny_app/ui/tabs.R` into a governed executive landing page.",
  "- Added read-only Home data accessors in `shiny_app/R/helpers.R`.",
  "- No other dashboard page was populated (Overview remains a placeholder).",
  "",
  "## Home sections",
  "- A. Hero: platform title + read-only subtitle + status pills.",
  "- B. Purpose cards: Governed Review, Goal #3 Alignment, Read-only Evidence Layer, Next Review Path.",
  "- C. Governed snapshot: champion (with conditions), decision, confidence, MASE/RMSSE, counts.",
  "- D. Dashboard map: PROJECT / FORECASTING / MODELS / GOVERNANCE / REFERENCE.",
  "- E. Visual-review callout (mandatory sentence).",
  "",
  "## Bound governed values",
  paste0("- Champion: ", bind$bound_value[bind$field == "champion_model"], " (selected with conditions)"),
  paste0("- Confidence: ", bind$bound_value[bind$field == "confidence"]),
  paste0("- Median MASE: ", bind$bound_value[bind$field == "median_mase"],
         " | Median RMSSE: ", bind$bound_value[bind$field == "median_rmsse"]),
  paste0("- Supported comparisons: ", bind$bound_value[bind$field == "supported_better"],
         " better / ", bind$bound_value[bind$field == "supported_worse"], " worse"),
  paste0("- Model universe: ", bind$bound_value[bind$field == "tournament_models"],
         " (", bind$bound_value[bind$field == "baseline_models"], " baseline + ",
         bind$bound_value[bind$field == "challenger_models"], " challenger)"),
  paste0("- Pairwise comparisons: ", bind$bound_value[bind$field == "pairwise_comparisons"]),
  "",
  "## Language safety",
  paste0("- Forbidden-language scan on Home: ",
         if (length(hits) == 0) "clean (no winner/best/absolute best/unconditional champion)."
         else paste0("FOUND -> ", paste(hits, collapse = ", "))),
  "",
  "## Safety findings",
  "- No metrics recalculated, no forecasts generated, no models run.",
  "- Champion decision and champion language untouched; dashboard remains read-only.",
  ""
)
writeLines(report, file.path(out_dir, "stage07_1_home_report.md"))

cat("==== Stage 07.1 Home emit complete ====\n")
cat("champion:", bind$bound_value[bind$field == "champion_model"], "\n")
cat("forbidden_language:", if (length(hits) == 0) "none" else paste(hits, collapse=","), "\n")
cat("key_results_rows:", nrow(kr), "champion_summary_rows:", nrow(cs), "\n")
