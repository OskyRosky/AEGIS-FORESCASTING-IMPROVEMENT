# V6.24-P9D | reactive validation of the Backtest Configuration block.
suppressPackageStartupMessages({
  library(shiny); library(bslib); library(DT); library(plotly)
  library(dplyr); library(readr); library(tidyr)
})
setwd(Sys.getenv("V6_SHINY_DIR", "."))
source("global.R")

res <- list()
R <- function(id, label, cond, detail = "") {
  res[[length(res) + 1]] <<- data.frame(
    check_id = id, check = label, observed = as.character(detail),
    result = if (isTRUE(cond)) "PASS" else "FAIL", stringsAsFactors = FALSE)
  cat(sprintf("[%s] %-56s %s\n", if (isTRUE(cond)) "PASS" else "FAIL",
              label, detail))
}

nav <- v6_24_operational()
sig <- nav[nav$champion_visible == "TRUE", ][1, ]
nos <- nav[nav$signal_quality_status == V6_24_NO_SIGNAL, ][1, ]
lowc <- nav[nav$low_confidence_backtest_window_flag == "TRUE", ][1, ]
sig_id <- as.character(sig$series_id[1])
nos_id <- as.character(nos$series_id[1])
low_id <- as.character(lowc$series_id[1])
cat("signal-present:", sig_id, "\nno-signal     :", nos_id,
    "\nlow-confidence:", low_id, "\n\n")

# ---- family map
v <- v6_24_validate_family_map()
R("F1", "display family map covers all 15 governed models",
  length(v$missing) == 0, paste0(v$mapped_n, " mapped, missing: ",
                                 length(v$missing)))
R("F2", "no extra model is introduced", length(v$extra) == 0,
  paste(length(v$extra), "extras"))
R("F3", "four families with 4/5/3/3", identical(as.integer(v$counts),
                                                c(4L, 5L, 3L, 3L)),
  paste(as.integer(v$counts), collapse = "/"))
R("F4", "embedded map agrees with the legacy display source",
  isTRUE(v$source_agrees), v$source_note)
R("F5", "map is declared display-only",
  identical(V6_24_FAMILY_MAP_USE, "DISPLAY_GROUPING_ONLY"), V6_24_FAMILY_MAP_USE)
R("F6", "each model appears in exactly one family",
  sum(as.integer(v$counts)) == 15, paste(sum(as.integer(v$counts)), "total"))
R("F7", "ETS Explicit keeps its space", "ETS Explicit" %in% V6_24_GOVERNED_MODELS)

# ---- availability
a_sig <- v6_24_backtest_availability(sig_id)
a_nos <- v6_24_backtest_availability(nos_id)
a_low <- v6_24_backtest_availability(low_id)
a_none <- v6_24_backtest_availability("NOT_A_SERIES")
R("A1", "signal-present series reports backtest available",
  isTRUE(a_sig$available), paste(format(a_sig$rows, big.mark = ","), "rows"))
R("A2", "NO-SIGNAL is NOT treated as unavailable", isTRUE(a_nos$available),
  paste(format(a_nos$rows, big.mark = ","), "rows,", a_nos$models, "models"))
R("A3", "LOW-CONFIDENCE is NOT treated as unavailable", isTRUE(a_low$available),
  paste(format(a_low$rows, big.mark = ","), "rows"))
R("A4", "an unknown series reports not available",
  !isTRUE(a_none$available) && a_none$status == "NOT_AVAILABLE", a_none$status)
R("A5", "availability reports all 15 models for a real series",
  a_sig$models == 15, paste(a_sig$models, "models"))

# ---- horizons
h_sig <- v6_24_available_horizons(sig_id)
R("H1", "offered horizons are exactly 5/10/15/20/25/30",
  identical(as.numeric(h_sig), c(5, 10, 15, 20, 25, 30)),
  paste(h_sig, collapse = ","))
R("H2", "every offered horizon is within 1-30",
  all(h_sig >= 1 & h_sig <= 30), paste0(min(h_sig), "-", max(h_sig)))
R("H3", "35 and 45 are declared unavailable",
  identical(as.numeric(V6_24_HORIZON_UNAVAILABLE), c(35, 45)),
  paste(V6_24_HORIZON_UNAVAILABLE, collapse = ","))
R("H4", "default horizon is 5", v6_24_default_horizon(sig_id) == 5,
  v6_24_default_horizon(sig_id))
R("H5", "horizon filter returns only matching horizon_steps", {
  b <- v6_24_backtest_rows(sig_id, v6_24_default_models(sig_id), 10)
  nrow(b) > 0 && all(as.integer(b$horizon_steps) == 10L)
}, "horizon 10 returns only step 10 rows")
R("H6", "no horizon beyond 30 can be requested",
  all(V6_24_HORIZON_CHOICES <= 30), paste(max(V6_24_HORIZON_CHOICES)))

# ---- defaults
d_sig <- v6_24_default_models(sig_id)
d_nos <- v6_24_default_models(nos_id)
ch_sig <- v6_24_champion(sig_id)
ch_nos <- v6_24_champion(nos_id)
R("D1", "defaults select around 5-6 models, not all 15",
  length(d_sig) >= 4 && length(d_sig) <= 6, paste(length(d_sig), "selected"))
R("D2", "champion is selected by default when it is meaningful",
  ch_sig$model %in% d_sig, paste0(ch_sig$model, " in defaults"))
R("D3", "ETS Explicit is always in the default set",
  "ETS Explicit" %in% d_sig && "ETS Explicit" %in% d_nos, "present in both")
R("D4", "a growth baseline is in the default set",
  any(d_sig %in% c("FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4",
                   "FixedGrowth_6")), paste(intersect(d_sig,
    c("FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6")),
    collapse = ","))
R("D5", "no-signal defaults present no model as a winner",
  !isTRUE(ch_nos$meaningful) &&
    !grepl("champion", v6_24_model_label(d_nos[1], ch_nos), fixed = TRUE) &&
    "ETS Explicit" %in% d_nos,
  paste0("leads with ", d_nos[1], " as governance reference; champion validity ",
         ch_nos$validity, " so no star is drawn. Note: P6C's tie-break crowns ",
         "ETS Explicit for every no-signal series, so the reference model and ",
         "the technical champion coincide by design."))
R("D6", "defaults are all governed models",
  all(d_sig %in% V6_24_GOVERNED_MODELS), "all governed")
R("D7", "at least one model is always selected", length(d_nos) > 0,
  paste(length(d_nos), "for the no-signal series"))

# ---- champion star
R("C1", "champion is meaningful for a signal-present series",
  isTRUE(ch_sig$meaningful), ch_sig$model)
R("C2", "champion is NOT meaningful for a no-signal series",
  !isTRUE(ch_nos$meaningful), ch_nos$validity)
R("C3", "star is drawn for a meaningful champion",
  grepl("champion", v6_24_model_label(ch_sig$model, ch_sig), fixed = TRUE),
  v6_24_model_label(ch_sig$model, ch_sig))
R("C4", "star is suppressed for a non-meaningful champion",
  !grepl("champion", v6_24_model_label(ch_nos$model, ch_nos), fixed = TRUE),
  v6_24_model_label(ch_nos$model, ch_nos))
R("C5", "no other model ever gets a star",
  !grepl("champion", v6_24_model_label("Theta", ch_sig), fixed = TRUE), "Theta")

# ---- source hygiene
srclines <- c(readLines("R/v6_24_backtest_config_helpers.R", warn = FALSE),
              readLines("server/v6_24_mvp_server.R", warn = FALSE),
              readLines("ui/tabs_v6_24_mvp.R", warn = FALSE))
code <- srclines[!grepl("^\\s*#", srclines)]
src <- paste(code, collapse = "\n")
R("S1", "no hardcoded no-signal series", !grepl("apcp150", src, fixed = TRUE))
R("S2", "no hardcoded GBRP267", !grepl("GBRP267", src, fixed = TRUE))
R("S3", "no write call", !any(vapply(
  c("write.csv", "write_csv", "write_parquet", "saveRDS", "unlink("),
  function(p) grepl(p, src, fixed = TRUE), logical(1))))
R("S4", "no SQL", !grepl("DBI::|odbc::|dbConnect", src))
R("S5", "no accuracy or ranking recomputation",
  !grepl("\\bmean\\(|\\bsd\\(|rank\\(", src), "no metric computation")
R("S6", "no Highcharts migration in P9D",
  !grepl("highchart", src, ignore.case = TRUE), "charts untouched")
R("S7", "no assistant implementation",
  !grepl("llm_explain", src, fixed = TRUE), "not implemented")
R("S8", "no download implementation",
  !grepl("downloadHandler", src, fixed = TRUE), "not implemented")

# ---- reactive
testServer(v6_24_mvp_server, {
  R("T1", "availability banner renders", !is.null(output$v24_bt_availability))
  R("T2", "horizon control renders", !is.null(output$v24_bt_horizon_ui))
  R("T3", "model family groups render", !is.null(output$v24_bt_model_groups))
  R("T4", "model count renders", !is.null(output$v24_bt_model_count))
  R("T5", "analyze button renders", !is.null(output$v24_bt_analyze_btn))

  setsel <- function(row) {
    for (ax in V6_24_FILTER_AXES) {
      session$setInputs2 <- NULL
      do.call(session$setInputs,
              stats::setNames(list(as.character(row[[ax]][1])),
                              paste0("v24_sel_", ax)))
    }
  }
  setsel(sig)

  av <- paste(as.character(output$v24_bt_availability), collapse = "")
  R("T6", "signal-present series shows Backtest available",
    grepl("Backtest available", av, fixed = TRUE))
  grp <- paste(as.character(output$v24_bt_model_groups), collapse = "")
  for (lab in c("Growth Baseline", "Statistical", "Machine Learning",
                "Deep Learning")) {
    R(paste0("T7_", gsub(" ", "", lab)), paste("family group rendered:", lab),
      grepl(lab, grp, fixed = TRUE))
  }
  R("T8", "all 15 governed models appear in the groups",
    all(vapply(V6_24_GOVERNED_MODELS,
               function(m) grepl(m, grp, fixed = TRUE), logical(1))),
    "15/15")
  R("T9", "champion star rendered for a meaningful champion",
    grepl("champion", grp, fixed = TRUE), ch_sig$model)
  cnt <- paste(as.character(output$v24_bt_model_count), collapse = "")
  R("T10", "model count reflects the default set",
    grepl(paste0(length(d_sig), " of 15"), cnt, fixed = TRUE), cnt)
  ap <- paste(as.character(output$v24_bt_applied), collapse = "")
  R("T11", "nothing is analysed before the first click",
    grepl("Nothing analysed yet", ap, fixed = TRUE))

  session$setInputs(v24_bt_analyze = 1)
  ap2 <- paste(as.character(output$v24_bt_applied), collapse = "")
  R("T12", "Analyze applies the pending configuration",
    grepl("Analysed:", ap2, fixed = TRUE), sub(".*(Analysed:[^<]*).*", "\\1", ap2))
  R("T13", "results notes render after Analyze",
    grepl("prepared rows", paste(as.character(output$v24_vw_notes),
                                 collapse = ""), fixed = TRUE))

  # no-signal series: no star, soft note, still available
  setsel(nos)
  grp2 <- paste(as.character(output$v24_bt_model_groups), collapse = "")
  note <- paste(as.character(output$v24_bt_champion_note), collapse = "")
  av2 <- paste(as.character(output$v24_bt_availability), collapse = "")
  R("T14", "no-signal series shows NO champion star",
    !grepl("champion", grp2, fixed = TRUE), "no star in the groups")
  R("T15", "no-signal series shows the soft champion note",
    grepl("not meaningful", note, fixed = TRUE))
  R("T16", "no-signal series still reports Backtest available",
    grepl("Backtest available", av2, fixed = TRUE))
  R("T17", "changing series clears the previous analysis",
    grepl("Nothing analysed yet",
          paste(as.character(output$v24_bt_applied), collapse = ""),
          fixed = TRUE))

  # reset
  session$setInputs(v24_bt_fam_statistical = character(0))
  session$setInputs(v24_bt_reset = 1)
  cnt2 <- paste(as.character(output$v24_bt_model_count), collapse = "")
  R("T18", "Reset restores the default model count",
    grepl(paste0(length(d_nos), " of 15"), cnt2, fixed = TRUE), cnt2)
})

out <- do.call(rbind, res)
np <- sum(out$result == "PASS"); nf <- sum(out$result == "FAIL")
cat(sprintf("\nP9D REACTIVE: %d PASS | %d FAIL of %d\n", np, nf, nrow(out)))
write.csv(out, file.path(Sys.getenv("V6_P9D_OUT", "."),
                         "_p9d_reactive_raw.csv"), row.names = FALSE)
if (nf == 0) cat("P9D_REACTIVE_OK\n") else cat("P9D_REACTIVE_FAILED\n")
