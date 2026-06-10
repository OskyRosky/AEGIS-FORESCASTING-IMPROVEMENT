# TESSERACT v2 | data_loader.R | sample CSV loading
source("R/constants.R")
source("R/helpers.R")
source("R/plots.R")
source("R/cards.R")
source("R/tables.R")
source("R/llm_client.R")

safe_read <- function(filename) {
  path <- file.path(DATA_PATH, filename)
  if (!file.exists(path)) {
    return(NULL)
  }

  tryCatch(
    read_csv(path, show_col_types = FALSE),
    error = function(e) NULL
  )
}

forecasts <- safe_read("forecasts.csv")
actuals <- safe_read("actuals.csv")
metrics <- safe_read("metrics.csv")
rankings <- safe_read("rankings.csv")
run_meta <- safe_read("run_metadata.csv")
recommendations <- safe_read("recommendations.csv")
