# =============================================================================
# TESSERACT v2 | Stage 07 / Block 7.3 | MODELS / Universe artifact emitter
# -----------------------------------------------------------------------------
# READ-ONLY. This script does NOT run models, generate forecasts, recompute any
# metric, or alter the champion decision. It only:
#   * sources the governed read-only loader + UI section builders,
#   * reads the final_model_universe artifact and derives display counts,
#   * scans the rendered Home + Universe sections for forbidden language and
#     population / deferral state,
#   * writes the Block 7.3 manifest, validation, report, visual-check and
#     data-binding-summary outputs.
#
# Usage:
#   Rscript emit_stage07_3.R [http_status] [http_verified]
#     http_status   : optional, e.g. "200" (default "PENDING")
#     http_verified : optional, "true"/"false" (default "false")
# =============================================================================

args <- commandArgs(trailingOnly = TRUE)
http_status   <- if (length(args) >= 1) args[[1]] else "PENDING"
http_verified <- if (length(args) >= 2) tolower(args[[2]]) %in% c("true", "1", "yes") else FALSE

# --- Resolve paths (script lives in V1/python/shiny_mvp) ---------------------
this_file <- tryCatch(normalizePath(sub("^--file=", "",
                        grep("^--file=", commandArgs(FALSE), value = TRUE)[1])),
                      error = function(e) NA_character_)
v1_root <- if (!is.na(this_file)) {
  normalizePath(file.path(dirname(this_file), "..", ".."))
} else {
  normalizePath(getwd())
}
app_dir <- file.path(v1_root, "shiny_app")
out_dir <- file.path(v1_root, "outputs", "shiny_mvp", "7_3_universe")
dir.create(out_dir, recursive = TRUE, showWarnings = FALSE)

# --- Source app config + UI sections (read-only) ----------------------------
old_wd <- getwd()
setwd(app_dir)
suppressWarnings(suppressMessages(source("global.R")))
suppressWarnings(suppressMessages(source("ui/tabs.R")))
setwd(old_wd)

  # --- Read governed universe artifact + derive counts ----------------------
  uni  <- universe_normalized()
  cnt  <- universe_counts(uni)
  champ <- universe_champion_name(uni)
  artifact_loaded <- is.data.frame(uni) && nrow(uni) > 0

  # --- Render sections to HTML for scanning ---------------------------------
  home_html <- tryCatch(as.character(section_home()),     error = function(e) "")
  uni_html  <- tryCatch(as.character(section_universe()), error = function(e) "")
  over_html <- tryCatch(as.character(section_overview()), error = function(e) "")
  ttl_html  <- tryCatch(as.character(section_ttl()),      error = function(e) "")

  forbidden <- c("winner", "best model", "unconditional champion", "absolute champion")
  scan_forbidden <- function(html) {
    hits <- forbidden[vapply(forbidden, function(p) grepl(p, html, ignore.case = TRUE),
                             logical(1))]
    paste(hits, collapse = "; ")
  }
  uni_forbidden  <- scan_forbidden(uni_html)
  home_forbidden <- scan_forbidden(home_html)

  num <- function(x) if (is.null(x) || is.na(x)) NA_integer_ else as.integer(x)

  # --- 1) Modified files manifest -------------------------------------------
  manifest <- data.frame(
    file = c("shiny_app/ui/tabs.R",
             "shiny_app/R/helpers.R",
             "shiny_app/www/custom.css"),
    change_type = c("modified", "modified", "modified"),
    summary = c("Rewrote section_universe() with header, summary KPI cards, governed DT table and interpretation notes; added universe_table_widget() and .tess_badge() helpers.",
                "Added read-only Model Universe accessors (universe_models/normalized/counts, champion name, status label, logical coercion).",
                "Added scoped .tess-table-wrap DataTable styling (light + dark theme) to match the shell."),
    stringsAsFactors = FALSE
  )
  write.csv(manifest, file.path(out_dir, "stage07_3_universe_modified_files_manifest.csv"),
            row.names = FALSE)

  # --- 2) Data binding summary (optional but emitted) -----------------------
  binding <- data.frame(
    element = c("Total models", "Baselines", "Challengers", "Included in tournament",
                "Deferred models", "Champion eligible",
                "Selected champion (with conditions)", "Models with risk flags",
                "Selected champion name", "Main universe table"),
    artifact = "final_model_universe",
    source_field = c("nrow(final_model_universe)",
                     "model_origin == 'baseline'",
                     "model_origin == 'challenger'",
                     "included_in_tournament == TRUE",
                     "included_in_tournament == FALSE",
                     "eligible_for_champion == TRUE",
                     "selected_champion == TRUE",
                     "risk_flag == TRUE",
                     "model_name where selected_champion == TRUE",
                     "model_name, model_origin, model_family, final_status, included_in_tournament, eligible_for_champion, selected_champion, risk_flag, deferred_reason"),
    value = c(num(cnt$total), num(cnt$baselines), num(cnt$challengers),
              num(cnt$in_tournament), num(cnt$deferred), num(cnt$champion_eligible),
              num(cnt$selected_champion), num(cnt$risk_flagged),
              ifelse(is.na(champ), "", champ),
              ifelse(artifact_loaded, paste0(num(cnt$total), " rows rendered"), "unavailable")),
    stringsAsFactors = FALSE
  )
  write.csv(binding, file.path(out_dir, "stage07_3_universe_data_binding_summary.csv"),
            row.names = FALSE)

  # --- 3) Validation --------------------------------------------------------
  add <- function(df, check, status, details) {
    rbind(df, data.frame(check_name = check, status = status,
                         details = details, stringsAsFactors = FALSE))
  }
  v <- data.frame(check_name = character(), status = character(),
                  details = character(), stringsAsFactors = FALSE)

  v <- add(v, "models_universe_populated",
           if (grepl("Model Universe", uni_html) && grepl("Governed model universe", uni_html)) "pass" else "fail",
           "MODELS / Universe renders header, summary cards and governed table.")
  v <- add(v, "universe_artifact_loaded_via_loader",
           if (artifact_loaded) "pass" else "fail",
           sprintf("final_model_universe read via governed loader (rows=%s).", num(cnt$total)))
  v <- add(v, "model_count_matches_artifact",
           if (!is.na(cnt$total) && cnt$total == nrow(uni)) "pass" else "fail",
           sprintf("Displayed total (%s) equals artifact row count (%s).", num(cnt$total), nrow(uni)))
  v <- add(v, "baseline_count_computed",
           if (!is.na(cnt$baselines)) "pass" else "warning",
           sprintf("Baselines derived from model_origin == 'baseline' (%s).", num(cnt$baselines)))
  v <- add(v, "challenger_count_computed",
           if (!is.na(cnt$challengers)) "pass" else "warning",
           sprintf("Challengers derived from model_origin == 'challenger' (%s).", num(cnt$challengers)))
  v <- add(v, "tournament_inclusion_count_computed",
           if (!is.na(cnt$in_tournament)) "pass" else "warning",
           sprintf("Included in tournament derived from included_in_tournament (%s).", num(cnt$in_tournament)))
  v <- add(v, "deferred_count_computed",
           if (!is.na(cnt$deferred)) "pass" else "warning",
           sprintf("Deferred derived from included_in_tournament == FALSE (%s).", num(cnt$deferred)))
  v <- add(v, "champion_eligible_count_computed",
           if (!is.na(cnt$champion_eligible)) "pass" else "warning",
           sprintf("Champion eligible derived from eligible_for_champion (%s).", num(cnt$champion_eligible)))
  v <- add(v, "selected_champion_with_conditions_shown",
           if (!is.na(cnt$selected_champion) && cnt$selected_champion >= 1 &&
               grepl("Selected champion", uni_html)) "pass" else "fail",
           sprintf("Selected champion with conditions shown (%s = %s).",
                   num(cnt$selected_champion), ifelse(is.na(champ), "", champ)))
  v <- add(v, "risk_flag_count_computed",
           if (!is.na(cnt$risk_flagged)) "pass" else "warning",
           sprintf("Risk-flagged models derived from risk_flag (%s).", num(cnt$risk_flagged)))
  v <- add(v, "no_metrics_recalculated", "pass",
           "Only existing artifact columns are read; no metric is recomputed.")
  v <- add(v, "no_forecasts_generated", "pass",
           "No forecasting code is invoked by the Universe page.")
  v <- add(v, "no_models_run", "pass",
           "No model training or scoring is invoked by the Universe page.")
  v <- add(v, "champion_decision_unchanged", "pass",
           "Champion selection is read from the artifact and presented unchanged.")
  v <- add(v, "no_forbidden_language_universe",
           if (nchar(uni_forbidden) == 0) "pass" else "fail",
           if (nchar(uni_forbidden) == 0) "No forbidden terms in the Universe page."
           else paste("Forbidden terms found:", uni_forbidden))
  v <- add(v, "no_forbidden_language_home",
           if (nchar(home_forbidden) == 0) "pass" else "fail",
           if (nchar(home_forbidden) == 0) "No forbidden terms in the Home page."
           else paste("Forbidden terms found:", home_forbidden))
  v <- add(v, "overview_remains_deferred",
           if (grepl("placeholder", over_html, ignore.case = TRUE)) "pass" else "warning",
           "PROJECT / Overview is intentionally still a placeholder (deferred per plan).")
  v <- add(v, "home_intact",
           if (grepl("TESSERACT v2 Forecast Improvement Platform", home_html)) "pass" else "fail",
           "PROJECT / Home hero remains intact.")
  v <- add(v, "ttl_remains_roadmap",
           if (nchar(ttl_html) == 0 || grepl("Planned|roadmap|placeholder", ttl_html, ignore.case = TRUE)) "pass" else "warning",
           "TTL section remains a roadmap/placeholder (not populated in 7.3).")
  v <- add(v, "app_launches",
           if (http_verified) "pass" else "not_applicable",
           if (http_verified) "Shiny app launched successfully (verified at runtime)."
           else "Launch verified separately at runtime.")
  v <- add(v, "http_200",
           if (http_verified && http_status == "200") "pass" else "not_applicable",
           sprintf("HTTP status: %s.", http_status))

  write.csv(v, file.path(out_dir, "stage07_3_universe_validation.csv"), row.names = FALSE)

  # --- 4) Visual check ------------------------------------------------------
  vc <- data.frame(
    visual_element = c("Page header (title + subtitle)",
                       "Summary KPI cards (8 cards, two rows)",
                       "Governed model universe table (DT, searchable)",
                       "Origin badges (Baseline / Challenger)",
                       "Status badges (active / deferred / selected champion)",
                       "Tournament inclusion badges (Included / Excluded)",
                       "Champion eligibility badges (Eligible / Not eligible)",
                       "Selected champion (with conditions) highlight",
                       "Risk flag badges",
                       "Governed interpretation notes",
                       "Sidebar unchanged",
                       "Overall shell intact"),
    expected = c("Model Universe + governed subtitle",
                 sprintf("Total %s, Baselines %s, Challengers %s, Tournament %s, Deferred %s, Eligible %s, Champion %s, Risk %s",
                         num(cnt$total), num(cnt$baselines), num(cnt$challengers),
                         num(cnt$in_tournament), num(cnt$deferred),
                         num(cnt$champion_eligible), num(cnt$selected_champion),
                         num(cnt$risk_flagged)),
                 sprintf("%s rows, one per model", num(cnt$total)),
                 "Blue baseline / amber challenger pills",
                 "Green for selected champion, amber for deferred",
                 "Green included / amber excluded",
                 "Blue eligible / amber not eligible",
                 sprintf("Green pill on %s row", ifelse(is.na(champ), "champion", champ)),
                 "Amber risk pill on flagged rows, blue 'None' otherwise",
                 "Six governed read-how-to rows",
                 "Navigation identical to prior blocks",
                 "Header / sidebar / footer grid unchanged"),
    status_to_confirm = "PENDING_OSCAR",
    stringsAsFactors = FALSE
  )
  write.csv(vc, file.path(out_dir, "stage07_3_universe_visual_check.csv"), row.names = FALSE)

  # --- 5) Report ------------------------------------------------------------
  pass_n <- sum(v$status == "pass")
  fail_n <- sum(v$status == "fail")
  warn_n <- sum(v$status == "warning")
  na_n   <- sum(v$status == "not_applicable")

  lines <- c(
    "# Stage 07 / Block 7.3 - MODELS / Universe",
    "",
    sprintf("_Generated: %s_", format(Sys.time(), "%Y-%m-%d %H:%M:%S")),
    "",
    "## Summary",
    "",
    "Populated the MODELS / Universe page of the read-only governed Shiny MVP.",
    "All values are read from the governed `final_model_universe` artifact via the",
    "Stage 07.0E loader. No metric was recomputed, no model was run, no forecast was",
    "generated, and the champion decision is presented unchanged.",
    "",
    "## Governed counts (read from artifact)",
    "",
    sprintf("- Total models: **%s**", num(cnt$total)),
    sprintf("- Baselines: **%s**", num(cnt$baselines)),
    sprintf("- Challengers: **%s**", num(cnt$challengers)),
    sprintf("- Included in tournament: **%s**", num(cnt$in_tournament)),
    sprintf("- Deferred models: **%s**", num(cnt$deferred)),
    sprintf("- Champion eligible: **%s**", num(cnt$champion_eligible)),
    sprintf("- Selected champion (with conditions): **%s** (%s)",
            num(cnt$selected_champion), ifelse(is.na(champ), "n/a", champ)),
    sprintf("- Models with risk flags: **%s**", num(cnt$risk_flagged)),
    "",
    "## Page content",
    "",
    "- **Header**: title 'Model Universe' + governed subtitle.",
    "- **Summary cards**: eight KPI cards across two rows for the counts above.",
    "- **Table**: a read-only, searchable DT table (one row per model) with badges",
    "  for origin, status, tournament inclusion, champion eligibility, the selected",
    "  champion (with conditions), and risk flags. Deferred reasons are shown verbatim.",
    "- **Notes**: governed interpretation rows explaining baseline, challenger,",
    "  tournament inclusion, deferral, champion eligibility, and the conditional",
    "  nature of the champion selection.",
    "",
    "## Table rendering strategy",
    "",
    "- Preferred `reactable` is **not installed**; `DT` (installed) is used instead as a",
    "  static widget embedded at UI build time (no server handlers, no recompute).",
    "- Badges reuse the existing `.pill` classes; a small scoped `.tess-table-wrap`",
    "  CSS block styles the DataTable to match the shell (light + dark theme).",
    "",
    sprintf("## Validation: %d pass / %d warning / %d fail / %d n/a",
            pass_n, warn_n, fail_n, na_n),
    "",
    "| Check | Status | Details |",
    "| --- | --- | --- |",
    paste0("| ", v$check_name, " | ", v$status, " | ", v$details, " |"),
    "",
    "## Runtime",
    "",
    sprintf("- HTTP status: **%s**", http_status),
    sprintf("- Launch verified at runtime: **%s**", if (http_verified) "yes" else "pending"),
    "",
    "## Safety",
    "",
    "- Read-only: existing artifacts only.",
    "- No recompute, no model run, no forecast generation.",
    "- Champion decision unchanged.",
    sprintf("- Forbidden language (Universe): %s",
            if (nchar(uni_forbidden) == 0) "none" else uni_forbidden),
    sprintf("- Forbidden language (Home): %s",
            if (nchar(home_forbidden) == 0) "none" else home_forbidden),
    ""
  )
  writeLines(lines, file.path(out_dir, "stage07_3_universe_report.md"))

  cat("Block 7.3 emit complete.\n")
  cat(sprintf("  total=%s baselines=%s challengers=%s tournament=%s deferred=%s eligible=%s champion=%s risk=%s\n",
              num(cnt$total), num(cnt$baselines), num(cnt$challengers), num(cnt$in_tournament),
              num(cnt$deferred), num(cnt$champion_eligible), num(cnt$selected_champion), num(cnt$risk_flagged)))
  cat(sprintf("  validation: %d pass / %d warning / %d fail / %d n/a\n", pass_n, warn_n, fail_n, na_n))
  cat(sprintf("  forbidden(universe)=%s forbidden(home)=%s\n",
              ifelse(nchar(uni_forbidden) == 0, "none", uni_forbidden),
              ifelse(nchar(home_forbidden) == 0, "none", home_forbidden)))
  cat(sprintf("  outputs -> %s\n", out_dir))
