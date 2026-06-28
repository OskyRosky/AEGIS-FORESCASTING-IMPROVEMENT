#!/usr/bin/env Rscript
# =====================================================================
# V3.2H  MODEL CONSISTENCY FIX  ---  Canonical model-universe builder
# ---------------------------------------------------------------------
# Produces a SINGLE canonical definition of the CURRENT model universe
# (15 models / 4 families) that every Models page (Universe, Tournament,
# Champion) and the Forecast Viewer can agree on.
#
# It DOES NOT run any model, backtest, or tournament. It only AGGREGATES
# metrics that already exist in closed governed / candidate artifacts:
#   * 12 governed models  -> tournament_model_scorecard.csv (medians ready)
#   * 3 deep-learning      -> full_candidate_outputs.csv (median over series)
#
# The original FastNeuralAR_MLP (high-risk, MASE 739.9) is RETIRED from the
# active universe. The "lightweight_neural" family label is dropped in favour
# of "Deep Learning". The champion (ETS Explicit, MASE 6.901) is UNCHANGED.
#
# Outputs:
#   data/processed/model_universe_canonical.csv          (15 rows)
#   outputs/v3_2h_model_consistency_fix/v3_2h_data_checks.csv
# =====================================================================

suppressWarnings(suppressMessages({
  options(stringsAsFactors = FALSE)
}))

# ---- locate V3 project root (this script lives in outputs/v3_2h_.../) ----
args <- commandArgs(trailingOnly = FALSE)
file_arg <- sub("^--file=", "", args[grep("^--file=", args)])
if (length(file_arg) == 0) file_arg <- "."
root <- normalizePath(file.path(dirname(file_arg), "..", ".."), winslash = "/", mustWork = FALSE)
if (!dir.exists(file.path(root, "data"))) {
  # fallback: assume current working dir is V3 root
  root <- normalizePath(getwd(), winslash = "/", mustWork = FALSE)
}
cat(sprintf("[v3.2h] project root: %s\n", root))

p_scorecard <- file.path(root, "outputs/model_lab/tournament_engine/tournament_model_scorecard.csv")
p_universe  <- file.path(root, "outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv")
p_candid    <- file.path(root, "outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv")
p_out       <- file.path(root, "data/processed/model_universe_canonical.csv")
p_checks    <- file.path(root, "outputs/v3_2h_model_consistency_fix/v3_2h_data_checks.csv")

stopifnot(file.exists(p_scorecard), file.exists(p_universe), file.exists(p_candid))

scorecard <- read.csv(p_scorecard, check.names = FALSE)
universe  <- read.csv(p_universe,  check.names = FALSE)
candid    <- read.csv(p_candid,    check.names = FALSE)

# ---------------------------------------------------------------------
# 1. The 12 governed models = active tournament models MINUS FastNeuralAR_MLP
# ---------------------------------------------------------------------
gov <- universe[as.character(universe$included_in_tournament) %in% c("True", "TRUE", "true") &
                  universe$model_name != "FastNeuralAR_MLP", , drop = FALSE]
stopifnot(nrow(gov) == 12)

# attach official medians from the scorecard
sc <- scorecard[, c("model_name", "official_median_mase", "official_median_rmsse",
                    "risk_status")]
gov <- merge(gov, sc, by = "model_name", all.x = TRUE, sort = FALSE)

gov_out <- data.frame(
  model_name            = gov$model_name,
  model_origin          = gov$model_origin,
  model_family          = gov$model_family,
  final_status          = gov$final_status,
  included_in_tournament = TRUE,
  eligible_for_champion = as.character(gov$eligible_for_champion) %in% c("True","TRUE","true"),
  selected_champion     = as.character(gov$selected_champion) %in% c("True","TRUE","true"),
  deferred_reason       = "",
  risk_flag             = FALSE,
  median_mase           = as.numeric(gov$official_median_mase),
  median_rmsse          = as.numeric(gov$official_median_rmsse),
  evidence_source       = "governed_tournament",
  stringsAsFactors = FALSE
)

# ---------------------------------------------------------------------
# 2. The 3 deep-learning challengers (median over series from candidates)
# ---------------------------------------------------------------------
dl_ids <- c("SMLP-TCN", "NLIN-DLIN_FIXED", "FNAR-V2")
dl_rows <- lapply(dl_ids, function(id) {
  sub <- candid[candid$candidate_id == id, , drop = FALSE]
  stopifnot(nrow(sub) > 0)
  # one MASE / RMSSE value per series_key (constant within series), then median
  per_series <- aggregate(cbind(mase, rmsse) ~ series_key, data = sub,
                          FUN = function(x) x[1])
  data.frame(
    model_name            = id,
    model_origin          = "challenger",
    model_family          = "deep_learning",
    final_status          = "active_evaluation_model",
    included_in_tournament = TRUE,
    eligible_for_champion = FALSE,
    selected_champion     = FALSE,
    deferred_reason       = "",
    risk_flag             = FALSE,
    median_mase           = stats::median(per_series$mase, na.rm = TRUE),
    median_rmsse          = stats::median(per_series$rmsse, na.rm = TRUE),
    evidence_source       = "candidate_evaluation",
    stringsAsFactors = FALSE
  )
})
dl_out <- do.call(rbind, dl_rows)

# ---------------------------------------------------------------------
# 3. Combine + family labels + ranking order
# ---------------------------------------------------------------------
canon <- rbind(gov_out, dl_out)

fam_lab <- c(
  growth_baseline  = "Growth baseline",
  statistical      = "Statistical",
  machine_learning = "Machine learning",
  deep_learning    = "Deep Learning"
)
canon$family_label <- unname(fam_lab[canon$model_family])

# order by family then median MASE (champion stays inside statistical block)
fam_rank <- c(statistical = 1, growth_baseline = 2, machine_learning = 3, deep_learning = 4)
canon <- canon[order(fam_rank[canon$model_family], canon$median_mase), , drop = FALSE]
rownames(canon) <- NULL

dir.create(dirname(p_out), showWarnings = FALSE, recursive = TRUE)
write.csv(canon, p_out, row.names = FALSE)
cat(sprintf("[v3.2h] wrote canonical universe: %s (%d rows)\n", p_out, nrow(canon)))
print(canon[, c("model_name", "model_family", "model_origin", "median_mase",
                "median_rmsse", "evidence_source")])

# ---------------------------------------------------------------------
# 4. Data-level checks
# ---------------------------------------------------------------------
fam_counts <- table(canon$model_family)
dl_models  <- sort(canon$model_name[canon$model_family == "deep_learning"])
champ      <- canon$model_name[canon$selected_champion %in% TRUE]

chk <- function(name, pass, detail = "") {
  data.frame(check = name, pass = isTRUE(pass), detail = detail, stringsAsFactors = FALSE)
}
checks <- rbind(
  chk("canonical_model_universe_has_15_models", nrow(canon) == 15, paste("rows =", nrow(canon))),
  chk("growth_baseline_count_4", unname(fam_counts["growth_baseline"]) == 4,
      paste("count =", unname(fam_counts["growth_baseline"]))),
  chk("statistical_count_5", unname(fam_counts["statistical"]) == 5,
      paste("count =", unname(fam_counts["statistical"]))),
  chk("machine_learning_count_3", unname(fam_counts["machine_learning"]) == 3,
      paste("count =", unname(fam_counts["machine_learning"]))),
  chk("deep_learning_count_3", unname(fam_counts["deep_learning"]) == 3,
      paste("count =", unname(fam_counts["deep_learning"]))),
  chk("deep_learning_models_correct",
      identical(dl_models, sort(c("SMLP-TCN", "NLIN-DLIN_FIXED", "FNAR-V2"))),
      paste(dl_models, collapse = "; ")),
  chk("fastneuralar_original_not_active",
      !("FastNeuralAR_MLP" %in% canon$model_name), "FastNeuralAR_MLP retired"),
  chk("lightweight_neural_not_in_canonical",
      !("lightweight_neural" %in% canon$model_family), "family dropped"),
  chk("no_champion_change", identical(champ, "ETS Explicit"),
      paste("champion =", paste(champ, collapse = "; "))),
  chk("champion_mase_unchanged_6_901",
      isTRUE(abs(canon$median_mase[canon$model_name == "ETS Explicit"] - 6.901143533) < 1e-3),
      sprintf("mase = %.6f", canon$median_mase[canon$model_name == "ETS Explicit"])),
  chk("all_models_have_median_mase", all(is.finite(canon$median_mase)), ""),
  chk("all_models_have_median_rmsse", all(is.finite(canon$median_rmsse)), "")
)

dir.create(dirname(p_checks), showWarnings = FALSE, recursive = TRUE)
write.csv(checks, p_checks, row.names = FALSE)
cat("\n[v3.2h] data checks:\n")
print(checks)
if (!all(checks$pass)) stop("[v3.2h] DATA CHECKS FAILED")
cat("\n[v3.2h] ALL DATA CHECKS PASSED\n")
