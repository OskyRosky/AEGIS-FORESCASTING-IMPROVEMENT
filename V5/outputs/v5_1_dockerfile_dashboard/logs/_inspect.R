# V5.1 image inspection helper (run inside container via bind mount)
req <- c("shiny","bslib","DT","plotly","highcharter","dplyr","readr","tidyr",
         "htmltools","jsonlite","rmarkdown","tinytex","httr","pandoc")
cat("=== REQUIRED DASHBOARD PACKAGES ===\n")
inst <- rownames(installed.packages())
for (x in req) {
  ok <- x %in% inst
  ver <- if (ok) as.character(packageVersion(x)) else "MISSING"
  cat(sprintf("%-12s %s %s\n", x, ifelse(ok,"OK","MISSING"), ver))
}
cat("=== HEAVY/PYTHON-BRIDGE PACKAGES (must be absent) ===\n")
bad <- c("torch","keras","tensorflow","xgboost","lightgbm","reticulate","prophet","forecast")
hit <- bad[bad %in% inst]
cat(if (length(hit)) paste("HEAVY_PRESENT:", paste(hit, collapse=",")) else "NO_HEAVY_ML_OR_PYTHON_BRIDGE", "\n")
cat("=== R VERSION ===\n"); cat(R.version.string, "\n")
