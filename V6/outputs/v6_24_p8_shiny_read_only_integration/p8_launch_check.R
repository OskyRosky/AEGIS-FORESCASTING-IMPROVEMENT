# V6.24-P8 | live app launch check. Starts the real Shiny app on a local port,
# issues an HTTP request against it, then shuts it down. Proves the app boots
# and serves, rather than only that its objects construct.
suppressPackageStartupMessages({ library(shiny); library(later) })
setwd(Sys.getenv("V6_SHINY_DIR", "."))

port <- 7824L
status <- NULL
bytes <- 0L
hit_v24 <- FALSE

later::later(function() {
  res <- tryCatch({
    con <- url(sprintf("http://127.0.0.1:%d", port), open = "rb")
    on.exit(try(close(con), silent = TRUE), add = TRUE)
    raw <- readBin(con, "raw", 400000L)
    txt <- rawToChar(raw[raw != as.raw(0)])
    list(ok = TRUE, n = length(raw), txt = txt)
  }, error = function(e) list(ok = FALSE, n = 0L, txt = ""))
  status <<- res$ok
  bytes <<- res$n
  hit_v24 <<- grepl("v24_overview", res$txt, fixed = TRUE)
  shiny::stopApp()
}, delay = 8)

cat("starting app on port", port, "...\n")
tryCatch(
  shiny::runApp(".", port = port, host = "127.0.0.1", launch.browser = FALSE,
                quiet = TRUE),
  error = function(e) cat("RUNAPP_ERROR:", conditionMessage(e), "\n"))

cat("served_ok:", isTRUE(status), "\n")
cat("bytes_received:", bytes, "\n")
cat("v24_section_in_served_html:", hit_v24, "\n")
if (isTRUE(status) && bytes > 0) cat("APP_LAUNCH_OK\n") else cat("APP_LAUNCH_FAILED\n")
