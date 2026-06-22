# ===========================================================================
# TTL DATA PROVIDER  (Phase 0 - API-ready abstraction layer)
# ---------------------------------------------------------------------------
# Single seam between the Shiny TTL page and the TTL data source. Everything
# downstream (gauge, line chart, tables, KPI cards) consumes the CANONICAL
# schema returned here, NEVER the raw CSV columns. When the official Tesseract
# API (POST /api/v1/calculate-ttl) becomes available, only the `api` branch is
# switched on -- no helper / UI / server logic changes.
#
#   getOption("ttl_source")  ->  "mock"  (default, reads local CSV prototype)
#                            ->  "api"   (calls the governed TTL endpoint; stub)
#
# CANONICAL SNAPSHOT schema (one row per forest x resource) -- field names
# mirror the official API response so the mock CSV is a drop-in:
#   forest, region, environment, resource, resource_display,
#   supply_date, supply, demand_now, utilization (0..1),
#   intersection_date (Date or NA), ttl_months (num or NA),
#   method ("intersection" | "eTTL"), ttl_status, is_binding (logical),
#   status_comment
#
# CANONICAL TIMESERIES schema (one row per forest x resource x month):
#   forest, region, environment, resource, resource_display, month_date,
#   demand, supply, utilization (0..1), is_crossover (logical),
#   is_projection (logical), data_origin
#
# Nothing governed is touched; DEMAND is our real forecast, SUPPLY+TTL are
# prototype values until the API is wired.
# ===========================================================================

# Active source (override with options(ttl_source = "api") once enabled).
ttl_data_source <- function() {
  src <- getOption("ttl_source", "mock")
  if (!src %in% c("mock", "api")) "mock" else src
}

# Official endpoints (documented for the future API swap; NOT called yet).
TTL_API_ENDPOINTS <- list(
  npe  = "https://cs-calculate-ttl-func-npe.azurewebsites.net/api/v1/calculate-ttl",
  ppe  = "https://cs-calculate-ttl-func-ppe.azurewebsites.net/api/v1/calculate-ttl",
  prod = "https://cs-calculate-ttl-func-prod.azurewebsites.net/api/v1/calculate-ttl"
)

# Resource slug -> display name (extend when CPU/SSD/IOPS are added).
TTL_RESOURCE_DISPLAY <- list(
  "HDD"      = "HDD",
  "hdd-edb"  = "HDD - EDB",
  "ssd-mcdb" = "SSD - MCDB",
  "cpu"      = "CPU",
  "iops"     = "IOPS"
)

ttl_resource_display <- function(resource) {
  r <- as.character(resource)
  vapply(r, function(x) {
    d <- TTL_RESOURCE_DISPLAY[[x]]
    if (is.null(d)) x else d
  }, character(1))
}

# ---------------------------------------------------------------------------
# Public accessors -- ALL downstream code calls these two functions only.
# ---------------------------------------------------------------------------
ttl_provider_snapshot <- function(source = ttl_data_source()) {
  if (identical(source, "api")) return(.ttl_api_snapshot())
  .ttl_mock_snapshot()
}

ttl_provider_timeseries <- function(source = ttl_data_source()) {
  if (identical(source, "api")) return(.ttl_api_timeseries())
  .ttl_mock_timeseries()
}

# ---------------------------------------------------------------------------
# MOCK source -- normalize the local prototype CSVs to the canonical schema.
# ---------------------------------------------------------------------------
.ttl_mock_snapshot <- function() {
  df <- tryCatch(load_csv_artifact("ttl_months_to_live_snapshot"),
                 error = function(e) data.frame())
  if (!is.data.frame(df) || nrow(df) == 0) return(.ttl_empty_snapshot())

  num <- function(x) suppressWarnings(as.numeric(x))
  has <- function(col) col %in% names(df)

  ttl_months  <- if (has("ttl_months"))  num(df$ttl_months)  else num(df$months_to_live)
  inter_chr   <- if (has("intersection_date")) as.character(df$intersection_date) else as.character(df$crossover_date)
  inter_date  <- suppressWarnings(as.Date(inter_chr))
  supply      <- if (has("supply")) num(df$supply) else num(df$supply_now)
  demand_now  <- if (has("demand_now")) num(df$demand_now) else num(df$demand_now)
  util        <- if (has("utilization")) num(df$utilization)
                 else if (has("utilization_pct")) num(df$utilization_pct) / 100
                 else demand_now / supply
  method      <- if (has("method")) as.character(df$method)
                 else ifelse(is.na(ttl_months) | !nzchar(inter_chr), "eTTL", "intersection")
  status      <- if (has("ttl_status")) as.character(df$ttl_status) else NA_character_
  is_binding  <- if (has("is_binding")) as.logical(df$is_binding) else TRUE
  stmt        <- if (has("status_comment")) as.character(df$status_comment)
                 else paste0("TTL: ",
                             ifelse(is.na(ttl_months), "no crossover in horizon",
                                    paste0(round(ttl_months, 2), " mo")),
                             " (", method, ")")

  data.frame(
    forest           = as.character(df$entity_key),
    region           = if (has("region")) as.character(df$region) else "",
    environment      = if (has("environment")) as.character(df$environment) else "",
    resource         = if (has("resource")) as.character(df$resource) else "HDD",
    resource_display = ttl_resource_display(if (has("resource")) df$resource else "HDD"),
    supply_date      = if (has("supply_date")) as.character(df$supply_date) else as.character(df$snapshot_date),
    supply           = supply,
    demand_now       = demand_now,
    utilization      = util,
    intersection_date = inter_date,
    ttl_months       = ttl_months,
    method           = method,
    ttl_status       = status,
    is_binding       = is_binding,
    status_comment   = stmt,
    monthly_growth_rate = if (has("monthly_growth_rate")) num(df$monthly_growth_rate) else NA_real_,
    growth_per_month    = if (has("growth_per_month")) num(df$growth_per_month) else NA_real_,
    stringsAsFactors = FALSE
  )
}

.ttl_mock_timeseries <- function() {
  df <- tryCatch(load_csv_artifact("ttl_supply_demand_timeseries"),
                 error = function(e) data.frame())
  if (!is.data.frame(df) || nrow(df) == 0) return(.ttl_empty_timeseries())

  num <- function(x) suppressWarnings(as.numeric(x))
  has <- function(col) col %in% names(df)

  supply  <- num(df$supply)
  demand  <- num(df$demand)
  util    <- if (has("utilization")) num(df$utilization)
             else if (has("utilization_pct")) num(df$utilization_pct) / 100
             else demand / supply

  data.frame(
    forest           = as.character(df$entity_key),
    region           = if (has("region")) as.character(df$region) else "",
    environment      = if (has("environment")) as.character(df$environment) else "",
    resource         = if (has("resource")) as.character(df$resource) else "HDD",
    resource_display = ttl_resource_display(if (has("resource")) df$resource else "HDD"),
    month_date       = as.Date(df$month_date),
    demand           = demand,
    supply           = supply,
    utilization      = util,
    is_crossover     = if (has("is_crossover")) as.logical(df$is_crossover)
                       else toupper(as.character(df$is_crossover_month)) == "TRUE",
    is_projection    = if (has("is_projection")) as.logical(df$is_projection) else FALSE,
    data_origin      = if (has("data_origin")) as.character(df$data_origin) else "demand=forecast_real;supply=simulated",
    stringsAsFactors = FALSE
  )
}

# ---------------------------------------------------------------------------
# API source -- STUB. Wiring deferred until access + function key are granted.
# Activation (future):
#   options(ttl_source = "api", ttl_api_env = "prod")
#   Sys.setenv(CALCULATE_TTL_KEY = "<function key>")
# Body per contract: {forest, resource, supplyDate, scenarioDemand, demandMode}
# Auth header: x-functions-key. (What-if ADD/REPLACE also lands here.)
# ---------------------------------------------------------------------------
.ttl_api_not_ready <- function() {
  stop("TTL API source not yet enabled. Set options(ttl_source='mock') ",
       "until /api/v1/calculate-ttl access (function key) is provisioned.",
       call. = FALSE)
}
.ttl_api_snapshot   <- function() .ttl_api_not_ready()
.ttl_api_timeseries <- function() .ttl_api_not_ready()

# ---------------------------------------------------------------------------
# Empty canonical frames (stable columns so downstream never errors).
# ---------------------------------------------------------------------------
.ttl_empty_snapshot <- function() {
  data.frame(
    forest = character(0), region = character(0), environment = character(0),
    resource = character(0), resource_display = character(0),
    supply_date = character(0), supply = numeric(0), demand_now = numeric(0),
    utilization = numeric(0), intersection_date = as.Date(character(0)),
    ttl_months = numeric(0), method = character(0), ttl_status = character(0),
    is_binding = logical(0), status_comment = character(0),
    monthly_growth_rate = numeric(0), growth_per_month = numeric(0),
    stringsAsFactors = FALSE
  )
}

.ttl_empty_timeseries <- function() {
  data.frame(
    forest = character(0), region = character(0), environment = character(0),
    resource = character(0), resource_display = character(0),
    month_date = as.Date(character(0)), demand = numeric(0), supply = numeric(0),
    utilization = numeric(0), is_crossover = logical(0),
    is_projection = logical(0), data_origin = character(0),
    stringsAsFactors = FALSE
  )
}
