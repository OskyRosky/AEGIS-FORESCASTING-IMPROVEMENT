# TESSERACT v2 | v6_24_models_full_helpers.R
# V6.24-P9K | Models FULL - Universe.
#
# CONTRACT
#   Everything here is READ from the governed V6.24 artifacts. This file does
#   not compute a tournament, does not compute pairwise evidence, does not
#   select a global champion, and does not recompute any accuracy metric.
#
#   The ONLY derived values are cohort medians over accuracy_metrics, which are
#   labelled COHORT_DIAGNOSTIC_MEDIAN everywhere they surface. They are a
#   description of the artifact, not a governed ranking.
#
# WHY THIS IS NOT THE LEGACY MODELS SECTION (P9J findings, measured)
#   legacy Models  : 13 models x  39 entities x HDD only
#   V6.24 universe : 15 models x 140 series   x CPU + HDD + IOPS + SSD
#   Only 12 models overlap. The legacy tournament carried FastNeuralAR_MLP,
#   which does not exist in V6.24; V6.24 carries FNAR-V2, NLIN-DLIN_FIXED and
#   SMLP-TCN, which never entered that tournament.
#
#   Four things the legacy pages rely on have NO successor artifact in V6.24:
#   MASE, RMSSE, pairwise bootstrap evidence, and a global champion decision.
#   None of them may be shown here as current V6.24 evidence.

V6_24_MF_MEDIAN_STAMP <- "COHORT_DIAGNOSTIC_MEDIAN"

# Legacy scope, kept only so the page can state honestly what changed. These are
# facts about the OLD artifacts, never presented as current evidence.
V6_24_MF_LEGACY_SCOPE <- list(
  models = 13L, entities = 39L, metric = "HDD only",
  overlap = 12L,
  legacy_only = "FastNeuralAR_MLP",
  v624_only = c("FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"),
  absent_in_v624 = c("MASE", "RMSSE", "pairwise bootstrap evidence",
                     "a global champion decision"))

#' The governed model list, read from the artifact rather than declared.
#'
#' V6_24_GOVERNED_MODELS (P9D) is the registry spelling. This function returns
#' the models the ARTIFACT actually carries, so a mismatch surfaces instead of
#' being papered over by a hardcoded vector.
v6_24_mf_model_list <- function() {
  ac <- v6_24_tbl("accuracy_metrics")
  if (is.null(ac) || !nrow(ac)) return(character(0))
  present <- unique(as.character(ac$model_name))
  ordered <- V6_24_GOVERNED_MODELS[V6_24_GOVERNED_MODELS %in% present]
  extra <- setdiff(present, V6_24_GOVERNED_MODELS)
  c(ordered, sort(extra))
}

#' Reconcile the registry list against the artifact.
#'
#' Returns the counts the validation report needs: how many governed models the
#' artifact carries, which are missing, and which extra names appear.
v6_24_mf_validate_model_list <- function() {
  present <- v6_24_mf_model_list()
  list(
    n_artifact = length(present),
    n_registry = length(V6_24_GOVERNED_MODELS),
    missing = setdiff(V6_24_GOVERNED_MODELS, present),
    extra = setdiff(present, V6_24_GOVERNED_MODELS),
    ok = length(present) == length(V6_24_GOVERNED_MODELS) &&
      !length(setdiff(V6_24_GOVERNED_MODELS, present)))
}

#' Family map for display, plus the governed 3-valued family from the artifact.
#'
#' The four display families come from V6_24_DISPLAY_FAMILY (P9D), which is
#' stamped DISPLAY_GROUPING_ONLY: the governed model_family is 3-valued
#' (Baseline / Challenger / Neural) and its partition CUTS ACROSS the display
#' one - ETS Explicit is a Challenger shown under Statistical, LinearRegression
#' is a Baseline shown under Machine Learning. Both are surfaced so the display
#' grouping is never mistaken for methodology.
v6_24_mf_family_map <- function() {
  ac <- v6_24_tbl("accuracy_metrics")
  gov <- if (!is.null(ac) && nrow(ac)) {
    g <- unique(ac[, c("model_name", "model_family")])
    stats::setNames(as.character(g$model_family), as.character(g$model_name))
  } else character(0)
  models <- v6_24_mf_model_list()
  data.frame(
    model_name = models,
    display_family_key = unname(V6_24_DISPLAY_FAMILY[models]),
    display_family = unname(vapply(models, function(m) {
      k <- V6_24_DISPLAY_FAMILY[[m]]
      if (is.null(k)) "\u2014" else unname(V6_24_FAMILY_LABEL[[k]])
    }, character(1))),
    governed_family = unname(ifelse(models %in% names(gov), gov[models], "\u2014")),
    stringsAsFactors = FALSE)
}

#' Series-level champion counts. NOT a global champion.
#'
#' Counts how many series each model leads, gated on champion_visible so the 15
#' no-signal series - where the P6C tie-break crowns a model against all-zero
#' actuals - never inflate a model's count.
v6_24_mf_champion_counts <- function() {
  nav <- v6_24_tbl("nav_contract")
  if (is.null(nav) || !nrow(nav)) return(data.frame())
  vis <- nav[toupper(as.character(nav$champion_visible)) == "TRUE", , drop = FALSE]
  if (!nrow(vis)) return(data.frame())
  tb <- as.data.frame(table(as.character(vis$champion_model_name)),
                      stringsAsFactors = FALSE)
  names(tb) <- c("model_name", "series_champion_count")
  tb[order(-tb$series_champion_count), , drop = FALSE]
}

#' Headline counts for the universe cards. Every number is read or counted from
#' an artifact; none is a ranking.
v6_24_mf_universe_summary <- function() {
  ac <- v6_24_tbl("accuracy_metrics")
  nav <- v6_24_tbl("nav_contract")
  vis <- if (!is.null(nav) && nrow(nav))
    sum(toupper(as.character(nav$champion_visible)) == "TRUE") else NA_integer_
  metrics <- c("MAE", "RMSE", "WAPE", "SMAPE", "MAPE",
               "Median absolute error", "Signed bias")
  # Deliberately reads ONLY accuracy_metrics and navigation_contract - the two
  # sources the page names on screen. It does not touch model_backtests_15_models
  # at all, so no accuracy figure here can have come from a backtest row.
  list(
    n_models = length(v6_24_mf_model_list()),
    n_series = if (!is.null(nav)) nrow(nav) else NA_integer_,
    n_rows = if (!is.null(ac)) nrow(ac) else NA_integer_,
    n_metrics = length(metrics),
    metrics = metrics,
    champion_visible = vis,
    champion_suppressed = if (!is.null(nav) && nrow(nav)) nrow(nav) - vis else NA_integer_,
    distinct_winners = nrow(v6_24_mf_champion_counts()),
    metrics_source = "accuracy_metrics",
    champion_source = "navigation_contract",
    median_stamp = V6_24_MF_MEDIAN_STAMP)
}

#' One row per governed model: coverage, cohort diagnostic medians, and the
#' series-level champion count.
#'
#' MEDIANS, NEVER MEANS. On this cohort the mean is unusable: LinearRegression
#' has a mean MAE of 5.86e21 against a median of 870. Rows whose metric the
#' artifact declared STRUCTURALLY_NOT_COMPUTABLE are excluded from that metric's
#' median rather than treated as zero, and the excluded count is reported.
v6_24_mf_universe_table <- function() {
  ac <- v6_24_tbl("accuracy_metrics")
  if (is.null(ac) || !nrow(ac)) return(data.frame())
  models <- v6_24_mf_model_list()
  fam <- v6_24_mf_family_map()
  ch <- v6_24_mf_champion_counts()

  med <- function(d, col, status_col = NULL) {
    v <- suppressWarnings(as.numeric(d[[col]]))
    if (!is.null(status_col) && status_col %in% names(d)) {
      v[as.character(d[[status_col]]) != "COMPUTED"] <- NA_real_
    }
    v <- v[is.finite(v)]
    if (!length(v)) return(NA_real_)
    stats::median(v)
  }

  rows <- lapply(models, function(m) {
    d <- ac[as.character(ac$model_name) == m, , drop = FALSE]
    f <- fam[fam$model_name == m, , drop = FALSE]
    cc <- ch$series_champion_count[ch$model_name == m]
    nc <- sum(as.character(d$wape_status) != "COMPUTED")
    ext <- sum(is.finite(suppressWarnings(as.numeric(d$mae))) &
                 abs(suppressWarnings(as.numeric(d$mae))) >= 1e6)
    data.frame(
      model_name = m,
      display_family = if (nrow(f)) f$display_family[1] else "\u2014",
      governed_family = if (nrow(f)) f$governed_family[1] else "\u2014",
      accuracy_rows = nrow(d),
      series_covered = length(unique(as.character(d$series_id))),
      median_mae = med(d, "mae"),
      median_rmse = med(d, "rmse"),
      median_wape = med(d, "wape", "wape_status"),
      median_smape = med(d, "smape", "smape_status"),
      noncomputable_wape = nc,
      extreme_mae_rows = ext,
      series_champion_count = if (length(cc)) as.integer(cc[1]) else 0L,
      stringsAsFactors = FALSE)
  })
  out <- do.call(rbind, rows)
  # Ordered by median MAE for readability only. This is NOT a standing and NOT
  # a governed ranking; the page says so next to the table.
  out[order(out$median_mae, na.last = TRUE), , drop = FALSE]
}

#' Guard: scan rendered text for claims V6.24 cannot support.
#'
#' CONTEXT-AWARE BY NECESSITY. A naive substring scan flags the page's own
#' disclaimers - "this is not a head-to-head tournament" and "Absent from
#' V6.24: MASE, RMSSE" both contain forbidden terms while asserting the exact
#' opposite. So the guard first drops any sentence that carries a denial or
#' absence marker, then scans what remains. What is left is assertive text, and
#' a forbidden term surviving there is a real regression.
V6_24_MF_FORBIDDEN <- c(
  "\\bMASE\\b", "\\bRMSSE\\b", "global champion", "tournament winner",
  "head-to-head", "pairwise evidence", "bootstrap support",
  "is the champion")

# A sentence carrying any of these is describing an absence, not making a claim.
V6_24_MF_DENIAL <- paste0(
  "\\bnot\\b|\\bno\\b|\\bnone\\b|\\bnever\\b|\\bcannot\\b|\\bwithout\\b|",
  "\\babsent\\b|\\bdoes not\\b|\\bdo not\\b|\\bis not\\b|\\bare not\\b|",
  "\\bcarries no\\b|\\bhas no\\b|\\bexcept\\b|\\bunlike\\b|\\bprevious\\b|",
  "\\bearlier\\b|\\blegacy\\b|\\bformer\\b|\\binstead\\b|\\bwould be\\b")

v6_24_mf_validate_no_global_claims <- function(txt) {
  if (is.null(txt) || !length(txt)) return(character(0))
  s <- paste(txt, collapse = " . ")
  # Split on sentence-ending punctuation only. A colon must NOT split, because
  # it introduces a list that belongs to the clause before it - splitting
  # "Absent from V6.24: MASE, RMSSE" would strip the denial from its own list
  # and then flag the list as a claim.
  parts <- unlist(strsplit(s, "(?<=[.!?;])\\s+", perl = TRUE))
  parts <- parts[nzchar(trimws(parts))]
  assertive <- parts[!grepl(V6_24_MF_DENIAL, parts, ignore.case = TRUE)]
  if (!length(assertive)) return(character(0))
  a <- paste(assertive, collapse = " ")
  found <- character(0)
  for (p in V6_24_MF_FORBIDDEN) {
    if (grepl(p, a, ignore.case = TRUE)) found <- c(found, p)
  }
  found
}

# ============================================================================
# V6.24-P9L | Ranking Diagnostics.
#
# This is the honest replacement for the legacy Tournament page. It compares
# models across the cohort using medians the artifact supports, and it never
# produces a winner.
#
# WHAT IT DELIBERATELY DOES NOT DO
#   - no pairwise comparison, no bootstrap interval, no p-value
#   - no MASE, no RMSSE (neither exists in V6.24)
#   - no official global rank; the ordering is a diagnostic_position
#   - no global champion
# Each of those needs a governed offline computation, and P9J established that
# none of them has a successor artifact for the 140-series cohort.
# ============================================================================

# Metrics the ranking page may offer, each tied to a governed column and to the
# status column that says whether the value may be read.
V6_24_MF_RANK_METRICS <- list(
  list(label = "MAE",                   col = "mae",   status = NULL),
  list(label = "RMSE",                  col = "rmse",  status = NULL),
  list(label = "WAPE",                  col = "wape",  status = "wape_status"),
  list(label = "SMAPE",                 col = "smape", status = "smape_status"),
  list(label = "MAPE",                  col = "mape",  status = "mape_status"),
  list(label = "Median absolute error", col = "median_absolute_error", status = NULL)
)
V6_24_MF_RANK_METRIC_LABELS <-
  vapply(V6_24_MF_RANK_METRICS, function(m) m$label, character(1))

V6_24_MF_SORT_OPTIONS <- c(
  "Diagnostic median, lowest first"       = "metric_asc",
  "Series-level champion count, highest first" = "champ_desc",
  "Non-computable rows, fewest first"     = "noncomp_asc",
  "Extreme-magnitude rows, fewest first"  = "extreme_asc"
)

v6_24_mf_rank_metric_def <- function(label) {
  for (m in V6_24_MF_RANK_METRICS) if (identical(m$label, label)) return(m)
  V6_24_MF_RANK_METRICS[[1]]
}

#' Cohort diagnostic rows, one per governed model.
#'
#' MEDIANS ONLY. Rows the artifact marked as not computable are excluded from
#' that metric median rather than treated as zero, and the count of excluded
#' rows travels with the result so the page can disclose it.
#'
#' @param primary_metric one of V6_24_MF_RANK_METRIC_LABELS
#' @param family_filter "All" or one of V6_24_FAMILY_LABEL
#' @param sort_by one of V6_24_MF_SORT_OPTIONS
v6_24_mf_ranking_rows <- function(primary_metric = "MAE",
                                  family_filter = "All",
                                  sort_by = "metric_asc") {
  ac <- v6_24_tbl("accuracy_metrics")
  if (is.null(ac) || !nrow(ac)) return(data.frame())
  base <- v6_24_mf_universe_table()
  if (!nrow(base)) return(data.frame())

  def <- v6_24_mf_rank_metric_def(primary_metric)
  med_for <- function(m) {
    d <- ac[as.character(ac$model_name) == m, , drop = FALSE]
    v <- suppressWarnings(as.numeric(d[[def$col]]))
    if (!is.null(def$status) && def$status %in% names(d)) {
      v[as.character(d[[def$status]]) != "COMPUTED"] <- NA_real_
    }
    v <- v[is.finite(v)]
    if (!length(v)) return(c(NA_real_, nrow(d)))
    c(stats::median(v), nrow(d) - length(v))
  }
  mm <- t(vapply(base$model_name, med_for, numeric(2)))
  base$median_selected <- mm[, 1]
  base$selected_excluded <- as.integer(mm[, 2])

  vis <- v6_24_mf_universe_summary()$champion_visible
  base$series_champion_share <- if (is.finite(vis) && vis > 0)
    base$series_champion_count / vis else NA_real_

  if (!identical(family_filter, "All")) {
    base <- base[base$display_family == family_filter, , drop = FALSE]
  }
  if (!nrow(base)) return(base)

  ord <- switch(
    sort_by,
    champ_desc  = order(-base$series_champion_count, base$median_selected,
                        na.last = TRUE),
    noncomp_asc = order(base$selected_excluded, base$median_selected,
                        na.last = TRUE),
    extreme_asc = order(base$extreme_mae_rows, base$median_selected,
                        na.last = TRUE),
    order(base$median_selected, na.last = TRUE))
  base <- base[ord, , drop = FALSE]
  # diagnostic_position, NOT rank: it describes where a row sits under the
  # current sort, and it changes when the metric or the sort changes.
  base$diagnostic_position <- seq_len(nrow(base))
  base
}

#' Headline values for the ranking cards.
#'
#' "Best diagnostic median" and "most series-level champions" are two different
#' models more often than not, which is precisely the point: neither is a winner.
v6_24_mf_ranking_summary <- function(rows, primary_metric = "MAE") {
  s <- v6_24_mf_universe_summary()
  base <- list(
    n_models = s$n_models, n_series = s$n_series,
    metric = primary_metric,
    best_median_model = "\u2014", best_median_value = NA_real_,
    most_champ_model = "\u2014", most_champ_count = NA_integer_,
    champion_visible = s$champion_visible,
    champion_suppressed = s$champion_suppressed,
    noncomputable = NA_integer_, models_shown = 0L,
    evidence_type = "Diagnostic only",
    agree = NA)
  if (is.null(rows) || !nrow(rows)) return(base)
  ok <- rows[is.finite(rows$median_selected), , drop = FALSE]
  if (nrow(ok)) {
    bi <- which.min(ok$median_selected)
    base$best_median_model <- as.character(ok$model_name[bi])
    base$best_median_value <- ok$median_selected[bi]
  }
  ci <- which.max(rows$series_champion_count)
  base$most_champ_model <- as.character(rows$model_name[ci])
  base$most_champ_count <- as.integer(rows$series_champion_count[ci])
  base$noncomputable <- sum(rows$selected_excluded, na.rm = TRUE)
  base$models_shown <- nrow(rows)
  base$agree <- identical(base$best_median_model, base$most_champ_model)
  base
}

#' Champion count rows for the chart. Series-level, gated, never global.
v6_24_mf_champion_count_rows <- function() {
  ch <- v6_24_mf_champion_counts()
  if (!nrow(ch)) return(ch)
  fm <- v6_24_mf_family_map()
  ch$display_family <- vapply(as.character(ch$model_name), function(m) {
    k <- fm$display_family[fm$model_name == m]
    if (!length(k)) "\u2014" else k[1]
  }, character(1), USE.NAMES = FALSE)
  ch
}

#' Where the metrics disagree.
#'
#' Gives each model its position under every available metric. If the metrics
#' agreed, every row would be identical; they do not, and the spread column
#' makes that visible. This is the evidence that a single "standing" would be
#' misleading.
v6_24_mf_metric_disagreement_rows <- function() {
  ac <- v6_24_tbl("accuracy_metrics")
  if (is.null(ac) || !nrow(ac)) return(data.frame())
  models <- v6_24_mf_model_list()
  pos <- list()
  for (m in V6_24_MF_RANK_METRICS) {
    med <- vapply(models, function(mn) {
      d <- ac[as.character(ac$model_name) == mn, , drop = FALSE]
      v <- suppressWarnings(as.numeric(d[[m$col]]))
      if (!is.null(m$status) && m$status %in% names(d)) {
        v[as.character(d[[m$status]]) != "COMPUTED"] <- NA_real_
      }
      v <- v[is.finite(v)]
      if (!length(v)) NA_real_ else stats::median(v)
    }, numeric(1))
    pos[[m$label]] <- rank(med, na.last = "keep", ties.method = "min")
  }
  out <- data.frame(model_name = models, stringsAsFactors = FALSE)
  for (nm in names(pos)) out[[nm]] <- as.integer(pos[[nm]])
  pm <- as.matrix(out[, names(pos), drop = FALSE])
  out$best_position <- apply(pm, 1, function(r) suppressWarnings(min(r, na.rm = TRUE)))
  out$worst_position <- apply(pm, 1, function(r) suppressWarnings(max(r, na.rm = TRUE)))
  out$position_spread <- out$worst_position - out$best_position
  out[order(-out$position_spread, out$best_position), , drop = FALSE]
}

# ============================================================================
# V6.24-P9M | Champion FULL.
#
# Champion in V6.24 is a PER-SERIES fact recorded in navigation_contract and
# gated by champion_visible. There is no global champion artifact, and none is
# derived here.
#
# THE GATE THAT MATTERS
#   15 of the 140 series have all-zero observed actuals. A model predicting
#   zero against zero scores a perfect error there without having modelled
#   anything, so the governed contract sets champion_visible = FALSE for them.
#   Those series still carry a champion_model_name from the P6C tie-break, but
#   it must never be presented as a winner. Every function below honours that.
# ============================================================================

#' Series-level champion distribution: one row per model that leads >= 1 series.
#'
#' Gated on champion_visible, so the counts sum to the presentable total and
#' never to 140.
v6_24_mf_champion_distribution <- function() {
  ch <- v6_24_mf_champion_count_rows()
  if (!nrow(ch)) return(ch)
  tb <- v6_24_mf_universe_table()
  vis <- v6_24_mf_universe_summary()$champion_visible
  ch$share_of_presentable <- if (is.finite(vis) && vis > 0)
    ch$series_champion_count / vis else NA_real_
  idx <- match(ch$model_name, tb$model_name)
  ch$governed_family <- tb$governed_family[idx]
  ch$median_mae <- tb$median_mae[idx]
  ch$median_rmse <- tb$median_rmse[idx]
  ch$median_wape <- tb$median_wape[idx]
  ch$median_smape <- tb$median_smape[idx]
  ch[order(-ch$series_champion_count, ch$median_mae), , drop = FALSE]
}

#' Headline counts for the Champion cards. Every value is read or counted.
v6_24_mf_champion_summary <- function() {
  s <- v6_24_mf_universe_summary()
  d <- v6_24_mf_champion_distribution()
  nav <- v6_24_tbl("nav_contract")
  pol <- if (!is.null(nav) && nrow(nav) &&
             "ranking_policy_version" %in% names(nav))
    as.character(nav$ranking_policy_version[1]) else "not recorded"
  list(
    n_series = s$n_series,
    presentable = s$champion_visible,
    suppressed = s$champion_suppressed,
    n_leaders = nrow(d),
    top_model = if (nrow(d)) as.character(d$model_name[1]) else "\u2014",
    top_count = if (nrow(d)) as.integer(d$series_champion_count[1]) else NA_integer_,
    top_share = if (nrow(d)) d$share_of_presentable[1] else NA_real_,
    evidence_type = "Series-level only",
    ranking_policy = pol,
    global_champion = "Not defined in V6.24",
    counts_sum = if (nrow(d)) sum(d$series_champion_count) else 0L)
}

#' Champion facts for ONE series, straight from navigation_contract.
#'
#' `presentable` is the only gate the UI may use. When it is FALSE the model
#' name is still returned so the page can show it as an internal tie-break, but
#' it is never a recommendation.
v6_24_mf_selected_series_champion <- function(series_id) {
  if (is.null(series_id) || !nzchar(series_id)) return(NULL)
  r <- v6_24_nav_row(series_id)
  if (is.null(r)) return(NULL)
  ch <- as.character(r$champion_model_name[1])
  vis <- identical(toupper(as.character(r$champion_visible[1])), "TRUE")
  sq <- v6_24_tbl("signal_quality")
  srow <- if (!is.null(sq) && nrow(sq))
    sq[as.character(sq$series_id) == series_id, , drop = FALSE] else NULL
  rk <- v6_24_tbl("model_rankings")
  rkr <- rk[as.character(rk$series_id) == series_id &
              as.character(rk$model_name) == ch, , drop = FALSE]
  fam <- V6_24_DISPLAY_FAMILY[[ch]]
  list(
    series_id = series_id,
    label = as.character(r$route_display_label[1]),
    metric = as.character(r$metric[1]),
    route = as.character(r$route_path[1]),
    product_status = as.character(r$product_status[1]),
    signal_quality = as.character(r$signal_quality_status[1]),
    no_signal = identical(toupper(as.character(r$no_signal_flag[1])), "TRUE"),
    all_zero = if (!is.null(srow) && nrow(srow))
      identical(toupper(as.character(srow$all_actuals_zero[1])), "TRUE") else NA,
    presentable = vis,
    champion_model = ch,
    champion_family = if (is.null(fam)) "\u2014" else unname(V6_24_FAMILY_LABEL[[fam]]),
    champion_rank = if (nrow(rkr))
      suppressWarnings(as.integer(rkr$rank_within_series[1])) else NA_integer_,
    rank_metric = as.character(r$champion_rank_metric[1]),
    rank_value = suppressWarnings(as.numeric(r$champion_rank_value[1])),
    validity = as.character(r$champion_validity[1]),
    reason = as.character(r$champion_reason[1]),
    caveat_badge = as.character(r$caveat_badge[1]),
    caveat_message = as.character(r$caveat_message[1]),
    ranking_policy = as.character(r$ranking_policy_version[1]))
}

#' Per-series ranking rows, best first. This is a ranking WITHIN one series.
v6_24_mf_selected_series_ranking <- function(series_id, top_n = 5L) {
  if (is.null(series_id) || !nzchar(series_id)) return(data.frame())
  rk <- v6_24_tbl("model_rankings")
  d <- rk[as.character(rk$series_id) == series_id, , drop = FALSE]
  if (!nrow(d)) return(data.frame())
  ac <- v6_24_tbl("accuracy_metrics")
  a <- ac[as.character(ac$series_id) == series_id, , drop = FALSE]
  j <- merge(d, a[, c("model_name", "mae", "rmse", "wape", "smape",
                      "wape_status", "smape_status")],
             by = "model_name", all.x = TRUE)
  j <- j[order(suppressWarnings(as.integer(j$rank_within_series))), , drop = FALSE]
  if (is.finite(top_n) && top_n > 0 && nrow(j) > top_n) {
    j <- j[seq_len(top_n), , drop = FALSE]
  }
  j$display_family <- vapply(as.character(j$model_name), function(m) {
    k <- V6_24_DISPLAY_FAMILY[[m]]
    if (is.null(k)) "\u2014" else unname(V6_24_FAMILY_LABEL[[k]])
  }, character(1), USE.NAMES = FALSE)
  j
}

#' What the ranking policy does, described from recorded fields only.
v6_24_mf_champion_policy_summary <- function() {
  nav <- v6_24_tbl("nav_contract")
  rk <- v6_24_tbl("model_rankings")
  pol <- if (!is.null(nav) && nrow(nav)) as.character(nav$ranking_policy_version[1])
         else "not recorded"
  metrics <- if (!is.null(rk) && nrow(rk))
    sort(unique(as.character(rk$primary_rank_metric))) else character(0)
  validity <- if (!is.null(nav) && nrow(nav))
    table(as.character(nav$champion_validity)) else table(character(0))
  list(policy = pol, primary_metrics = metrics,
       validity = validity,
       n_presentable = sum(toupper(as.character(nav$champion_visible)) == "TRUE"),
       n_suppressed = sum(toupper(as.character(nav$champion_visible)) != "TRUE"))
}

#' Facts about the previous Champion page, for the clearly-labelled history
#' block. These describe the OLD work and are never current evidence.
v6_24_mf_legacy_champion_facts <- function() {
  nav <- v6_24_tbl("nav_contract")
  vis <- nav[toupper(as.character(nav$champion_visible)) == "TRUE", , drop = FALSE]
  ets_all <- sum(as.character(nav$champion_model_name) == "ETS Explicit")
  ets_vis <- sum(as.character(vis$champion_model_name) == "ETS Explicit")
  list(
    legacy_model = "ETS Explicit",
    legacy_entities = V6_24_MF_LEGACY_SCOPE$entities,
    legacy_models = V6_24_MF_LEGACY_SCOPE$models,
    ets_rows_v624 = as.integer(ets_all),
    ets_presentable_v624 = as.integer(ets_vis),
    ets_suppressed_v624 = as.integer(ets_all - ets_vis),
    presentable_total = nrow(vis))
}
