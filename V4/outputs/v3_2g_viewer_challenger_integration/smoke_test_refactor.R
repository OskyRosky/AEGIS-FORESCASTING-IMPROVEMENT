## V3.2G refactor smoke test: families, DL models, no evaluation section.
suppressWarnings(suppressMessages({
  setwd(file.path("shiny_app"))
  source("global.R")
  source(file.path("ui", "header.R"))
  source(file.path("ui", "body.R"))
}))

cat("\n--- FVP family order/labels ---\n")
print(FVP_FAMILY_ORDER)
print(FVP_FAMILY_LABELS)
stopifnot(!"evaluation_challenger" %in% FVP_FAMILY_ORDER)
stopifnot(identical(unname(FVP_FAMILY_LABELS[["lightweight_neural"]]), "Deep Learning"))

cat("\n--- fvp_data families present ---\n")
df <- fvp_data()
fams <- sort(unique(df$model_family))
print(fams)
stopifnot(setequal(fams, c("growth_baseline","statistical","machine_learning","lightweight_neural")))

dl <- sort(unique(df$model_name[df$model_family == "lightweight_neural"]))
cat("Deep Learning models:", paste(dl, collapse=", "), "\n")
stopifnot(setequal(dl, c("SMLP-TCN","NLIN-DLIN_FIXED","FNAR-V2")))

cat("\n--- label has no high-risk badge ---\n")
lbl <- fvp_model_label("SomeModel", FALSE, "high_risk")
cat("label:", lbl, "\n")
stopifnot(!grepl("high risk", lbl))
stopifnot(grepl("champion", fvp_model_label("X", TRUE, "ok")))

cat("\n--- defaults ---\n")
print(fvp_default_models())
stopifnot("SMLP-TCN" %in% fvp_default_models())
stopifnot(!"FastNeuralAR_MLP" %in% fvp_default_models())

cat("\n--- UI builds (sections + sidebar) ---\n")
ui <- app_sections()
sb <- stage07_menu()
models_grp <- Filter(function(g) identical(g$group, "Models"), sb)[[1]]
model_vals <- vapply(models_grp$items, function(i) i$value, character(1))
cat("Models nav:", paste(model_vals, collapse=", "), "\n")
stopifnot(setequal(model_vals, c("universe","tournament","champion")))
stopifnot(!exists("section_evaluation"))

cat("\nALL SMOKE CHECKS PASSED\n")
