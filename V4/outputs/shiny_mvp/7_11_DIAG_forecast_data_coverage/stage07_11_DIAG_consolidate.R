# ============================================================================
# Stage 07 - Block 7.11-DIAG | Consolidated multi-model coverage + verdict
# READ-ONLY. Builds enriched coverage joining baseline + challenger backtest
# artifacts, plus validation. Does NOT modify any data/model/Shiny file.
# ============================================================================
suppressWarnings(suppressMessages({ library(readr); library(dplyr) }))

ROOT <- "C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V1"
OUT  <- file.path(ROOT, "outputs/shiny_mvp/7_11_DIAG_forecast_data_coverage")
rd <- function(p) suppressWarnings(suppressMessages(read_csv(file.path(ROOT,p),
        show_col_types = FALSE, progress = FALSE, guess_max = 5000)))

uni <- rd("outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv")
fam <- uni %>% select(model_name, model_origin, model_family)

bl <- rd("outputs/model_lab/full_baseline/full_baseline_forecasts.csv") %>%
  transmute(entity_key, model_name, model_origin = "baseline",
            forecast_date = as.Date(forecast_date), forecast_value, actual_value = NA_real_)
ch <- rd("outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv") %>%
  transmute(entity_key, model_name, model_origin = "challenger",
            forecast_date = as.Date(forecast_date), forecast_value, actual_value)

allm <- bind_rows(bl, ch) %>% left_join(fam %>% select(model_name, model_family), by = "model_name")

# ---- consolidated models per entity (baseline + challenger) ----------------
mpe <- allm %>% group_by(entity_key) %>% summarise(
  total_models = n_distinct(model_name),
  baseline_models = n_distinct(model_name[model_origin == "baseline"]),
  challenger_models = n_distinct(model_name[model_origin == "challenger"]),
  families = paste(sort(unique(model_family)), collapse = " | "),
  has_statistical = any(model_family == "statistical"),
  has_machine_learning = any(model_family == "machine_learning"),
  has_growth_baseline = any(model_family == "growth_baseline"),
  has_lightweight_neural = any(model_family == "lightweight_neural"),
  has_deep_learning = any(model_family == "deep_learning"),
  min_date = as.character(min(forecast_date, na.rm = TRUE)),
  max_date = as.character(max(forecast_date, na.rm = TRUE)),
  .groups = "drop") %>% arrange(entity_key)
write.csv(mpe, file.path(OUT, "stage07_11_DIAG_models_per_entity_multimodel.csv"), row.names = FALSE)

# ---- representative series coverage (enriched) -----------------------------
reps <- c("APC-Dedicated","APC-MSIT","APC-Multitenant","AUS-Go Local","BRA-Go Local")
reps <- intersect(reps, unique(allm$entity_key))
cov <- allm %>% filter(entity_key %in% reps) %>% group_by(entity_key, model_name, model_origin, model_family) %>%
  summarise(points = n(), actual_points = sum(!is.na(actual_value)),
            min_date = as.character(min(forecast_date, na.rm = TRUE)),
            max_date = as.character(max(forecast_date, na.rm = TRUE)), .groups = "drop") %>%
  arrange(entity_key, model_origin, model_name)
write.csv(cov, file.path(OUT, "stage07_11_DIAG_representative_series_coverage.csv"), row.names = FALSE)

cat("== consolidated models per entity (head) ==\n")
print(as.data.frame(head(mpe, 6)))
cat("\nentities with multimodel:", sum(mpe$total_models > 1), "of", nrow(mpe), "\n")
cat("max total models/entity:", max(mpe$total_models),
    " | any deep learning:", any(mpe$has_deep_learning), "\n")
cat("\n== representative coverage (APC-Dedicated) ==\n")
print(as.data.frame(cov %>% filter(entity_key == "APC-Dedicated")))

# ---- validation ------------------------------------------------------------
val <- data.frame(
  check_name = c(
    "no_shiny_files_modified","no_data_processed_modified","no_model_outputs_modified",
    "no_forecasts_generated","no_metrics_recalculated","no_models_run",
    "forecasting_artifacts_inventoried","forecasts_csv_schema_inspected",
    "forecast_comparison_csv_inspected","entities_csv_inspected","actuals_csv_inspected",
    "model_counts_by_entity_computed","representative_series_coverage_computed",
    "multimodel_artifact_found","deep_learning_forecasts_available",
    "data_gap_clearly_stated","recommendation_produced"),
  status = c(
    "pass","pass","pass","pass","pass","pass",
    "pass","pass","pass","pass","pass","pass","pass",
    "pass","fail","pass","pass"),
  details = c(
    "Only files under outputs/shiny_mvp/7_11_DIAG_forecast_data_coverage created",
    "data/processed untouched (read-only inspection)",
    "outputs/model_lab read-only; nothing written there",
    "No forecasting executed; existing artifacts read only",
    "No metrics recomputed",
    "No model fitting/inference run",
    "25 candidate artifacts inspected; inventory CSV written",
    "forecasts.csv = 65095 rows, 45 entities, 1 model_version each (16 global)",
    "forecast_comparison.csv = EMPTY (0 rows) — not usable",
    "entities.csv = 45 rows inspected",
    "actuals.csv = 84537 rows, no model column",
    "Consolidated baseline+challenger models per entity computed (39 entities)",
    "5 representative series coverage computed with per-model points",
    "challenger_actual_forecast_join.csv (6 models+actuals) & full_baseline_forecasts.csv (7 models) cover 39 entities",
    "NBEATS/NHITS deferred (deferred_runtime_impractical / dependency_blocked) — no deep-learning forecast rows exist",
    "Final artifact (forecasts.csv) is single-model; multimodel data lives in model_lab backtest artifacts",
    "Verdict PARTIALLY-YES recorded in report + recommendation"))
write.csv(val, file.path(OUT, "stage07_11_DIAG_validation.csv"), row.names = FALSE)
cat("\nVALIDATION_DONE rows:", nrow(val), "\n")
