# ============================================================================
# Stage 07 - Block 7.11-DIAG | Forecast Data Coverage & Multi-Model Diagnosis
# READ-ONLY. Does not modify any data, model, or Shiny file.
# Inspects forecast-related artifacts to determine whether a multi-model-per-
# series Forecast Viewer is supportable with existing data.
# ============================================================================

suppressWarnings(suppressMessages({
  library(readr); library(dplyr); library(tidyr)
}))

ROOT <- "C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V1"
OUT  <- file.path(ROOT, "outputs/shiny_mvp/7_11_DIAG_forecast_data_coverage")
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)

# Candidate forecast/model artifacts to inspect (relative to ROOT).
candidates <- c(
  "data/processed/forecasts.csv",
  "data/processed/actuals.csv",
  "data/processed/forecast_comparison.csv",
  "data/processed/entities.csv",
  "data/processed/run_metadata.csv",
  "data/sample/metrics.csv",
  "data/sample/recommendations.csv",
  "outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv",
  "outputs/model_lab/tournament_engine/tournament_preliminary_standings.csv",
  "outputs/model_lab/tournament_engine/tournament_model_scorecard.csv",
  "outputs/model_lab/tournament_engine/tournament_pairwise_evidence.csv",
  "outputs/model_lab/tournament_engine/tournament_entity_model_scores.csv",
  "outputs/model_lab/challenger_metrics/challenger_metrics_by_model_diagnostic.csv",
  "outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv",
  "outputs/model_lab/challenger_metrics/challenger_scoring_forecasts.csv",
  "outputs/model_lab/challenger_aggregation_significance/challenger_aggregation_by_model.csv",
  "outputs/model_lab/challenger_official_execution/challenger_official_forecasts.csv",
  "outputs/model_lab/forecasts/baseline_forecasts.csv",
  "outputs/model_lab/full_baseline/full_baseline_forecasts.csv",
  "outputs/model_lab/benchmark_reference/naive_benchmark_forecasts.csv",
  "outputs/model_lab/seasonal_benchmark/seasonal_naive_forecasts.csv",
  "outputs/model_lab/non_negative_policy/non_negative_forecasts.csv",
  "outputs/model_lab/baseline_pilot/baseline_pilot_forecasts.csv",
  "outputs/model_lab/challenger_sandbox/challenger_sandbox_forecasts.csv",
  "outputs/model_lab/contracts/forecast_output_schema.csv"
)

read_safe <- function(p) {
  tryCatch(suppressWarnings(suppressMessages(
    readr::read_csv(p, show_col_types = FALSE, progress = FALSE,
                    guess_max = 5000))),
    error = function(e) NULL)
}

# Column-name helpers (artifacts use varied naming).
pick <- function(cols, opts) { hit <- opts[opts %in% cols]; if (length(hit)) hit[1] else NA_character_ }
ENTITY_COLS <- c("entity_key","entity","entity_id","series","series_id","series_key","id")
MODEL_COLS  <- c("model_name","model","model_version","model_id","method","algorithm","model_label")
DATE_COLS   <- c("target_date","forecast_date","date","ds","period","timestamp")
FVAL_COLS   <- c("forecast_value","forecast","yhat","prediction","predicted","value_forecast","point_forecast")
AVAL_COLS   <- c("actual_value","actual","y","value_actual","truth")

# ---- 1. Inventory + schema summary ----------------------------------------
inv  <- list(); sch <- list(); mm_flag <- list()

for (rel in candidates) {
  p <- file.path(ROOT, rel)
  if (!file.exists(p)) {
    inv[[length(inv)+1]] <- data.frame(artifact = rel, exists = FALSE,
      n_rows = NA, n_cols = NA, entity_col = NA, model_col = NA,
      date_col = NA, forecast_col = NA, actual_col = NA,
      n_entities = NA, n_models = NA, multimodel_per_entity = NA,
      stringsAsFactors = FALSE)
    next
  }
  df <- read_safe(p)
  if (is.null(df)) {
    inv[[length(inv)+1]] <- data.frame(artifact = rel, exists = TRUE,
      n_rows = NA, n_cols = NA, entity_col = NA, model_col = NA,
      date_col = NA, forecast_col = NA, actual_col = NA,
      n_entities = NA, n_models = NA, multimodel_per_entity = NA,
      stringsAsFactors = FALSE)
    next
  }
  cols <- names(df)
  ec <- pick(cols, ENTITY_COLS); mc <- pick(cols, MODEL_COLS)
  dc <- pick(cols, DATE_COLS);   fc <- pick(cols, FVAL_COLS); ac <- pick(cols, AVAL_COLS)

  n_ent <- if (!is.na(ec)) length(unique(trimws(as.character(df[[ec]])))) else NA
  n_mod <- if (!is.na(mc)) length(unique(trimws(as.character(df[[mc]])))) else NA

  # multimodel test: does any entity have >1 distinct model?
  mm <- NA
  max_models_one_entity <- NA
  if (!is.na(ec) && !is.na(mc)) {
    g <- df %>% mutate(.e = trimws(as.character(.data[[ec]])),
                       .m = trimws(as.character(.data[[mc]]))) %>%
      group_by(.e) %>% summarise(nm = n_distinct(.m), .groups = "drop")
    max_models_one_entity <- max(g$nm)
    mm <- any(g$nm > 1)
  }

  inv[[length(inv)+1]] <- data.frame(artifact = rel, exists = TRUE,
    n_rows = nrow(df), n_cols = ncol(df),
    entity_col = ifelse(is.na(ec),"",ec), model_col = ifelse(is.na(mc),"",mc),
    date_col = ifelse(is.na(dc),"",dc), forecast_col = ifelse(is.na(fc),"",fc),
    actual_col = ifelse(is.na(ac),"",ac),
    n_entities = n_ent, n_models = n_mod,
    multimodel_per_entity = mm, stringsAsFactors = FALSE)

  # schema rows
  for (cn in cols) {
    v <- df[[cn]]
    sch[[length(sch)+1]] <- data.frame(
      artifact = rel, column = cn, r_type = class(v)[1],
      n_distinct = length(unique(v)),
      example = ifelse(nrow(df) > 0, as.character(v[1]), NA),
      stringsAsFactors = FALSE)
  }

  # multimodel candidate flag (has entity+model+date+forecast and >1 model/entity)
  is_fv_shape <- (!is.na(ec) && !is.na(mc) && !is.na(dc) && !is.na(fc))
  mm_flag[[length(mm_flag)+1]] <- data.frame(
    artifact = rel,
    has_entity = !is.na(ec), has_model = !is.na(mc),
    has_date = !is.na(dc), has_forecast = !is.na(fc), has_actual = !is.na(ac),
    forecast_viewer_shape = is_fv_shape,
    multimodel_per_entity = ifelse(is.na(mm), FALSE, mm),
    max_models_one_entity = ifelse(is.na(max_models_one_entity), NA, max_models_one_entity),
    n_entities = n_ent, n_models = n_mod,
    stringsAsFactors = FALSE)
}

inventory <- do.call(rbind, inv)
schema    <- do.call(rbind, sch)
mmflags   <- do.call(rbind, mm_flag)

write.csv(inventory, file.path(OUT, "stage07_11_DIAG_forecast_artifact_inventory.csv"), row.names = FALSE)
write.csv(schema,    file.path(OUT, "stage07_11_DIAG_forecast_schema_summary.csv"), row.names = FALSE)
write.csv(mmflags,   file.path(OUT, "stage07_11_DIAG_data_gap_matrix.csv"), row.names = FALSE)

cat("=== INVENTORY (existing) ===\n")
print(inventory[inventory$exists == TRUE,
      c("artifact","n_rows","entity_col","model_col","date_col","forecast_col",
        "n_entities","n_models","multimodel_per_entity")], row.names = FALSE)

cat("\n=== FORECAST-VIEWER SHAPE CANDIDATES (entity x model x date x forecast) ===\n")
cand_mm <- mmflags[mmflags$forecast_viewer_shape == TRUE, ]
print(cand_mm[, c("artifact","multimodel_per_entity","max_models_one_entity",
                  "n_entities","n_models")], row.names = FALSE)

# ---- 2. models per entity for forecasts.csv -------------------------------
fpath <- file.path(ROOT, "data/processed/forecasts.csv")
fc <- read_safe(fpath)
if (!is.null(fc)) {
  ec <- pick(names(fc), ENTITY_COLS); mc <- pick(names(fc), MODEL_COLS)
  dc <- pick(names(fc), DATE_COLS)
  fc$.e <- trimws(as.character(fc[[ec]]))
  fc$.m <- trimws(as.character(fc[[mc]]))
  fc$.d <- suppressWarnings(as.Date(fc[[dc]]))
  mpe <- fc %>%
    group_by(.e) %>% summarise(
      model_count = n_distinct(.m),
      models_available = paste(sort(unique(.m)), collapse = " | "),
      forecast_points = n(),
      min_date = as.character(min(.d, na.rm = TRUE)),
      max_date = as.character(max(.d, na.rm = TRUE)),
      .groups = "drop") %>% rename(entity = .e)
  write.csv(mpe, file.path(OUT, "stage07_11_DIAG_models_per_entity_forecasts.csv"), row.names = FALSE)
  cat("\n=== forecasts.csv : models per entity ===\n")
  cat("entities:", nrow(mpe), " | max models/entity:", max(mpe$model_count),
      " | any multimodel:", any(mpe$model_count > 1), "\n")
}

# ---- 3. models per entity for forecast_comparison.csv ---------------------
cmp <- read_safe(file.path(ROOT, "data/processed/forecast_comparison.csv"))
if (!is.null(cmp) && ncol(cmp) > 1 && nrow(cmp) > 0) {
  ec <- pick(names(cmp), ENTITY_COLS); mc <- pick(names(cmp), MODEL_COLS)
  if (!is.na(ec) && !is.na(mc)) {
    cpe <- cmp %>% mutate(.e = trimws(as.character(.data[[ec]])),
                          .m = trimws(as.character(.data[[mc]]))) %>%
      group_by(.e) %>% summarise(model_count = n_distinct(.m),
        models_available = paste(sort(unique(.m)), collapse = " | "),
        rows = n(), .groups = "drop") %>% rename(entity = .e)
    write.csv(cpe, file.path(OUT, "stage07_11_DIAG_models_per_entity_forecast_comparison.csv"), row.names = FALSE)
  } else {
    write.csv(data.frame(note = "forecast_comparison.csv present but lacks entity/model columns",
                         ncol = ncol(cmp), nrow = nrow(cmp), cols = paste(names(cmp), collapse=",")),
              file.path(OUT, "stage07_11_DIAG_models_per_entity_forecast_comparison.csv"), row.names = FALSE)
  }
} else {
  write.csv(data.frame(note = "forecast_comparison.csv empty or single-column (not usable)",
                       ncol = ifelse(is.null(cmp),0,ncol(cmp)),
                       nrow = ifelse(is.null(cmp),0,nrow(cmp))),
            file.path(OUT, "stage07_11_DIAG_models_per_entity_forecast_comparison.csv"), row.names = FALSE)
  cat("\n=== forecast_comparison.csv : EMPTY / not usable ===\n")
}

# ---- 4. representative series coverage across multimodel candidate ---------
# Pick the best multimodel artifact (forecast_viewer_shape & multimodel).
best <- cand_mm[cand_mm$multimodel_per_entity == TRUE, ]
best <- best[order(-best$max_models_one_entity), ]
rep_targets <- c("APC-Dedicated","APC-MSIT","APC-Multitenant","AUS-Go Local","BRA-Go Local")

cov_rows <- list()
best_artifact <- if (nrow(best) > 0) best$artifact[1] else NA
if (!is.na(best_artifact)) {
  bdf <- read_safe(file.path(ROOT, best_artifact))
  ec <- pick(names(bdf), ENTITY_COLS); mc <- pick(names(bdf), MODEL_COLS)
  dc <- pick(names(bdf), DATE_COLS);   fc <- pick(names(bdf), FVAL_COLS); ac <- pick(names(bdf), AVAL_COLS)
  bdf <- bdf %>% mutate(.e = trimws(as.character(.data[[ec]])),
                        .m = trimws(as.character(.data[[mc]])))
  ents_avail <- sort(unique(bdf$.e))
  # map representative targets to closest available
  chosen <- intersect(rep_targets, ents_avail)
  if (length(chosen) < 4) chosen <- unique(c(chosen, head(ents_avail, 5)))[1:min(5,length(ents_avail))]
  for (e in chosen) {
    sub <- bdf %>% filter(.e == e)
    dts <- if (!is.na(dc)) suppressWarnings(as.Date(sub[[dc]])) else as.Date(NA)
    cov_rows[[length(cov_rows)+1]] <- data.frame(
      source_artifact = best_artifact, entity = e,
      model_count = dplyr::n_distinct(sub$.m),
      models_available = paste(sort(unique(sub$.m)), collapse = " | "),
      actual_points = if (!is.na(ac)) sum(!is.na(sub[[ac]])) else NA,
      forecast_points = if (!is.na(fc)) sum(!is.na(sub[[fc]])) else nrow(sub),
      min_date = ifelse(all(is.na(dts)), NA, as.character(min(dts, na.rm=TRUE))),
      max_date = ifelse(all(is.na(dts)), NA, as.character(max(dts, na.rm=TRUE))),
      stringsAsFactors = FALSE)
  }
}
if (length(cov_rows) == 0) {
  # fall back to forecasts.csv (final single-model) to show honest coverage
  if (!is.null(fc <- read_safe(fpath))) {
    ec <- pick(names(fc), ENTITY_COLS); mc <- pick(names(fc), MODEL_COLS); dc <- pick(names(fc), DATE_COLS)
    fc$.e <- trimws(as.character(fc[[ec]])); fc$.m <- trimws(as.character(fc[[mc]]))
    fcx <- fc
    ents_avail <- sort(unique(fcx$.e))
    chosen <- intersect(rep_targets, ents_avail); if (length(chosen) < 4) chosen <- head(ents_avail, 5)
    for (e in chosen) {
      sub <- fcx %>% filter(.e == e); dts <- suppressWarnings(as.Date(sub[[dc]]))
      cov_rows[[length(cov_rows)+1]] <- data.frame(
        source_artifact = "data/processed/forecasts.csv", entity = e,
        model_count = dplyr::n_distinct(sub$.m),
        models_available = paste(sort(unique(sub$.m)), collapse = " | "),
        actual_points = NA, forecast_points = nrow(sub),
        min_date = as.character(min(dts, na.rm=TRUE)), max_date = as.character(max(dts, na.rm=TRUE)),
        stringsAsFactors = FALSE)
    }
  }
}
coverage <- do.call(rbind, cov_rows)
write.csv(coverage, file.path(OUT, "stage07_11_DIAG_representative_series_coverage.csv"), row.names = FALSE)
cat("\n=== REPRESENTATIVE SERIES COVERAGE (best artifact:", best_artifact, ") ===\n")
print(coverage, row.names = FALSE)

# ---- 5. required forecast viewer schema -----------------------------------
req <- data.frame(
  column = c("entity_key","entity_label","model_name","model_origin","model_family",
             "forecast_date","target_date","actual_value","forecast_value","horizon_days",
             "run_id","source_artifact"),
  type = c("string","string","string","string","string",
           "date","date","double","double","integer","string","string"),
  required = c(TRUE,FALSE,TRUE,FALSE,FALSE,TRUE,TRUE,FALSE,TRUE,FALSE,FALSE,TRUE),
  description = c(
    "Stable entity/series key (join key)",
    "Human-readable series label",
    "Model identifier (multiple rows per entity)",
    "baseline | challenger | benchmark",
    "statistical | ml | deep_learning | naive",
    "Date the forecast was issued (origin)",
    "Date being forecast",
    "Observed actual at target_date (NA for pure-future)",
    "Forecast point value",
    "target_date - forecast_date in days",
    "Run/execution identifier for provenance",
    "Originating governed artifact path"),
  stringsAsFactors = FALSE)
write.csv(req, file.path(OUT, "stage07_11_DIAG_required_forecast_viewer_schema.csv"), row.names = FALSE)

# ---- 6. search results (all forecast-ish files, read-only listing) ---------
all_files <- list.files(ROOT, recursive = TRUE, full.names = TRUE, pattern = "\\.(csv|rds|parquet)$")
key <- "forecast|prediction|backtest|fitted|actual|comparison|model_output|challenger|baseline|tournament"
sel <- all_files[grepl(key, basename(all_files), ignore.case = TRUE)]
sr <- data.frame(path = gsub(paste0("^", gsub("([\\\\])","\\\\\\1",ROOT), "[\\\\/]"), "", sel),
                 size_kb = round(file.info(sel)$size/1024, 1), stringsAsFactors = FALSE)
write.csv(sr, file.path(OUT, "stage07_11_DIAG_artifact_search_results.csv"), row.names = FALSE)

cat("\nDIAG_DONE\n")
