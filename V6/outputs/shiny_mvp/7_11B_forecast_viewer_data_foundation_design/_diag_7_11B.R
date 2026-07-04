# ============================================================================
# Stage 07 - Block 7.11B | Forecast Viewer Data Foundation - DESIGN DIAGNOSIS
# READ-ONLY. Inventories series, model coverage by family, and scans all
# forecast artifacts for confidence/prediction-interval columns.
# Does NOT modify any data, model, governance, or Shiny file.
# ============================================================================
suppressWarnings(suppressMessages({ library(readr); library(dplyr) }))

ROOT <- "C:/Users/oscarau/OneDrive - Microsoft/Desktop/Forecast Generation Codebase Improvement/AEGIS-FORESCASTING-IMPROVEMENT/V1"
OUT  <- file.path(ROOT, "outputs/shiny_mvp/7_11B_forecast_viewer_data_foundation_design")
dir.create(OUT, recursive = TRUE, showWarnings = FALSE)
rd <- function(p) tryCatch(suppressWarnings(suppressMessages(
        read_csv(file.path(ROOT,p), show_col_types = FALSE, progress = FALSE, guess_max = 8000))),
        error = function(e) NULL)

# ---------------------------------------------------------------------------
# Load core sources
# ---------------------------------------------------------------------------
final_fc <- rd("data/processed/forecasts.csv")            # 45 ent, 1 model each (final)
actuals  <- rd("data/processed/actuals.csv")              # 45 ent actuals
entities <- rd("data/processed/entities.csv")             # 45 ent catalog
uni      <- rd("outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv")
baseline <- rd("outputs/model_lab/full_baseline/full_baseline_forecasts.csv")        # 39 ent x 7 baseline
chall    <- rd("outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv") # 39 ent x 6 challenger + actuals

fam <- uni %>% select(model_name, model_origin, model_family,
                      eligible_for_champion, selected_champion, final_status, risk_flag)

# ---------------------------------------------------------------------------
# 1. Series inventory (all 45 entities)
# ---------------------------------------------------------------------------
ents_final     <- unique(trimws(final_fc$entity_key))
ents_actual    <- unique(trimws(actuals$entity_key))
ents_baseline  <- unique(trimws(baseline$entity_key))
ents_chall     <- unique(trimws(chall$entity_key))
all_ents       <- sort(unique(c(ents_final, ents_actual, ents_baseline, ents_chall)))

inv <- lapply(all_ents, function(e) {
  ff <- final_fc %>% filter(trimws(entity_key) == e)
  aa <- actuals  %>% filter(trimws(entity_key) == e)
  bb <- baseline %>% filter(trimws(entity_key) == e)
  cc <- chall    %>% filter(trimws(entity_key) == e)
  models_b <- unique(bb$model_name); models_c <- unique(cc$model_name)
  n_models <- length(unique(c(models_b, models_c)))
  dts <- c()
  if (nrow(ff)) dts <- c(dts, as.Date(ff$date))
  if (nrow(aa)) dts <- c(dts, as.Date(aa$date))
  if (nrow(bb)) dts <- c(dts, as.Date(bb$forecast_date))
  if (nrow(cc)) dts <- c(dts, as.Date(cc$forecast_date))
  data.frame(
    series_key = e, series_label = e,
    source_artifact = paste(c(
      if (nrow(ff)) "forecasts.csv",
      if (nrow(bb)) "full_baseline_forecasts.csv",
      if (nrow(cc)) "challenger_actual_forecast_join.csv"), collapse = " + "),
    has_actuals = nrow(aa) > 0,
    has_final_forecast = nrow(ff) > 0,
    has_baseline_backtest = nrow(bb) > 0,
    has_challenger_backtest = nrow(cc) > 0,
    has_multimodel_coverage = n_models > 1,
    number_of_models_available = n_models,
    date_min = ifelse(length(dts)>0, as.character(min(dts, na.rm=TRUE)), NA),
    date_max = ifelse(length(dts)>0, as.character(max(dts, na.rm=TRUE)), NA),
    stringsAsFactors = FALSE)
})
inventory <- do.call(rbind, inv)
write.csv(inventory, file.path(OUT, "forecast_viewer_series_inventory.csv"), row.names = FALSE)

cat("== SERIES INVENTORY ==\n")
cat("total series:", nrow(inventory),
    "| with multimodel:", sum(inventory$has_multimodel_coverage),
    "| final-only:", sum(!inventory$has_multimodel_coverage), "\n")
cat("series WITHOUT multimodel coverage:\n")
print(inventory$series_key[!inventory$has_multimodel_coverage])

# ---------------------------------------------------------------------------
# 2. Representative MVP series
# ---------------------------------------------------------------------------
pref <- c("APC-Dedicated","APC-MSIT","APC-Multitenant","ARE-Go Local","AUS-Go Local","BRA-Go Local")
avail_mm <- inventory$series_key[inventory$has_multimodel_coverage]
chosen <- intersect(pref, avail_mm)
if (length(chosen) < 5) chosen <- unique(c(chosen, head(sort(avail_mm), 5)))[1:5]
rep_tbl <- inventory %>% filter(series_key %in% chosen) %>%
  mutate(reason = ifelse(series_key %in% pref,
    "Preferred series available with full multi-model backtest coverage",
    "Closest valid alternative with full multi-model backtest coverage"))
write.csv(rep_tbl, file.path(OUT, "forecast_viewer_representative_series_recommendation.csv"), row.names = FALSE)
cat("\n== REPRESENTATIVE MVP SERIES ==\n"); print(rep_tbl$series_key)

# ---------------------------------------------------------------------------
# 3. Model coverage by series (family-classified), for representative series
# ---------------------------------------------------------------------------
bl_long <- baseline %>% transmute(series_key = trimws(entity_key), model_name,
                                  origin = "baseline")
ch_long <- chall %>% transmute(series_key = trimws(entity_key), model_name,
                               origin = "challenger")
cov <- bind_rows(bl_long, ch_long) %>% distinct() %>%
  left_join(fam, by = "model_name")

# Display-family normalization (honest classification)
disp_family <- function(model_family, model_name) {
  dplyr::case_when(
    model_family == "growth_baseline"   ~ "baseline_reference",
    model_family == "statistical"       ~ "statistical",
    model_family == "machine_learning"  ~ "machine_learning",
    model_family == "lightweight_neural"~ "neural_lightweight_high_risk",
    model_family == "deep_learning"     ~ "deep_learning_deferred",
    TRUE ~ model_family)
}
cov <- cov %>% mutate(display_family = disp_family(model_family, model_name))

cov_rep <- cov %>% filter(series_key %in% chosen) %>%
  arrange(series_key, display_family, model_name) %>%
  select(series_key, model_name, model_origin = origin, model_family,
         display_family, eligible_for_champion, selected_champion,
         final_status, risk_flag)
write.csv(cov_rep, file.path(OUT, "forecast_viewer_model_coverage_by_series.csv"), row.names = FALSE)
cat("\n== MODEL COVERAGE (one representative series) ==\n")
print(as.data.frame(cov_rep %>% filter(series_key == chosen[1])))

# ---------------------------------------------------------------------------
# 4. Confidence / prediction interval column scan across ALL forecast artifacts
# ---------------------------------------------------------------------------
search_root <- file.path(ROOT)
all_csv <- list.files(search_root, recursive = TRUE, full.names = TRUE, pattern = "\\.csv$")
# Restrict to forecast-ish files (avoid scanning everything huge)
key <- "forecast|prediction|backtest|fitted|actual|comparison|model_output|challenger|baseline|tournament|scoring|metric"
cand <- all_csv[grepl(key, basename(all_csv), ignore.case = TRUE)]
# skip our own DIAG/design outputs
cand <- cand[!grepl("7_11_DIAG|7_11B_", cand)]

interval_pat <- "(^|_)(lower|upper|lo|hi|low|high|q[0-9]+|p[0-9]+|ci|pi|interval|quantile|conf|band|sd|stderr|se|sigma|variance)($|_)"
int_rows <- list()
for (f in cand) {
  hdr <- tryCatch(suppressWarnings(names(read_csv(f, n_max = 0, show_col_types = FALSE, progress = FALSE))),
                  error = function(e) NULL)
  if (is.null(hdr) || length(hdr) == 0) next
  hits <- hdr[grepl(interval_pat, tolower(hdr))]
  rel <- sub(paste0("^", gsub("([\\\\.])","\\\\\\1", ROOT), "[\\\\/]"), "", f)
  int_rows[[length(int_rows)+1]] <- data.frame(
    artifact = rel,
    has_interval_columns = length(hits) > 0,
    interval_columns = ifelse(length(hits) > 0, paste(hits, collapse = " | "), ""),
    all_columns_sample = paste(head(hdr, 12), collapse = ", "),
    stringsAsFactors = FALSE)
}
intervals <- do.call(rbind, int_rows)
write.csv(intervals, file.path(OUT, "forecast_viewer_interval_availability.csv"), row.names = FALSE)
cat("\n== INTERVAL SCAN ==\n")
cat("artifacts scanned:", nrow(intervals),
    "| with interval-like columns:", sum(intervals$has_interval_columns), "\n")
print(intervals$artifact[intervals$has_interval_columns])

cat("\nDONE_7_11B\n")
