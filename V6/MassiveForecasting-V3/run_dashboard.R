###############################################################################
# Scripts_tablas_dashboard/run_dashboard.R
#
# Lanzador del dashboard (wrapper) que delega al runner oficial: AI_SAF.R
# - No depende del working directory
# - No asume app.R
# - Evita hacks como sys.frame()
#
# Uso:
#   cd "/Users/sultan/DataScience/MassiveForescastingIncome/V2"
#   Rscript Scripts_tablas_dashboard/run_dashboard.R
###############################################################################

suppressWarnings(suppressMessages({
  library(shiny)
}))

# ---------------------------
# Detectar ruta del script (Rscript --file=)
# ---------------------------
args <- commandArgs(trailingOnly = FALSE)
file_arg <- grep("^--file=", args, value = TRUE)

if (length(file_arg) > 0) {
  this_file <- sub("^--file=", "", file_arg[1])
  script_dir <- dirname(normalizePath(this_file, winslash = "/", mustWork = TRUE))
} else {
  # Fallback raro: ejecución sin --file=
  script_dir <- normalizePath(getwd(), winslash = "/", mustWork = TRUE)
}

# Root del proyecto: V2/
root_dir <- normalizePath(file.path(script_dir, ".."), winslash = "/", mustWork = TRUE)

# Runner oficial
ai_saf <- file.path(root_dir, "AI_SAF.R")

message("RUN DEBUG script_dir: ", script_dir)
message("RUN DEBUG root_dir  : ", root_dir)
message("RUN DEBUG ai_saf    : ", ai_saf)

if (!file.exists(ai_saf)) {
  stop("No se encontró AI_SAF.R en: ", ai_saf, call. = FALSE)
}

# Delegar TODO al runner oficial
source(ai_saf, local = TRUE)