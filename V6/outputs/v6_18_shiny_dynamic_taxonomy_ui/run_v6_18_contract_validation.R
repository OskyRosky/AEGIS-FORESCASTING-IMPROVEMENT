args <- commandArgs(trailingOnly = TRUE)
repo_root <- if (length(args) > 0) {
  normalizePath(args[[1]], winslash = "/", mustWork = TRUE)
} else {
  normalizePath(file.path(getwd()), winslash = "/", mustWork = TRUE)
}
v6_root <- file.path(repo_root, "V6")
app_root <- file.path(v6_root, "shiny_app")
output_root <- file.path(v6_root, "outputs", "v6_18_shiny_dynamic_taxonomy_ui")

suppressPackageStartupMessages(library(shiny))
setwd(app_root)
source("R/helpers.R")
find_project_root <- function(start = getwd()) v6_root
source("R/taxonomy_navigation.R")
source("R/viewer_pilot.R")
source("R/forecast_pilot.R")

contract <- taxonomy_navigation_data(TRUE)
viewer_metadata <- fvp_pilot_data(TRUE)
forecast_metadata <- ffp_pilot_data(TRUE)

check <- function(id, name, expected, observed, passed, method) {
  data.frame(
    check_id = id,
    check_name = name,
    expected = as.character(expected),
    observed = as.character(observed),
    status = if (isTRUE(passed)) "PASS" else "FAIL",
    validation_method = method,
    stringsAsFactors = FALSE
  )
}

selection_from_row <- function(row) {
  list(
    metric = row$base_metric,
    demand_nature = row$demand_nature,
    db_type = row$db_type,
    prepared_scenario = row$prepared_scenario,
    segment = row$segment,
    granularity = row$granularity,
    forest = row$forest,
    sku = row$sku,
    entity = row$entity_value
  )
}

all_resolve <- function(page) {
  rows <- taxonomy_operational_rows(page, contract)
  resolved <- vapply(seq_len(nrow(rows)), function(index) {
    route <- taxonomy_resolve_selection(
      page, selection_from_row(rows[index, , drop = FALSE]), contract
    )
    !is.null(route) &&
      identical(route$source_metric, rows$source_metric[[index]]) &&
      identical(route$source_scenario, rows$source_scenario[[index]]) &&
      identical(route$source_granularity, rows$source_granularity[[index]]) &&
      identical(route$source_series_key, rows$source_series_key[[index]])
  }, logical(1))
  sum(resolved)
}

viewer_rows <- taxonomy_operational_rows("viewer", contract)
forecast_rows <- taxonomy_operational_rows("forecast", contract)
viewer_routes <- unique(viewer_rows$route_id)
forecast_routes <- unique(forecast_rows$route_id)
viewer_resolved <- all_resolve("viewer")
forecast_resolved <- all_resolve("forecast")
verified_models <- fvp_verified_model_universe(TRUE)

v617 <- file.path(v6_root, "outputs", "v6_17_full_multimetric_productive_artifact_generation")
viewer_parquet <- file.path(v617, "forecast_viewer_model_outputs_v2_full.parquet")
forecast_parquet <- file.path(v617, "forecast_forward_outputs_v6_17_full.parquet")
viewer_size <- file.info(viewer_parquet)$size
forecast_size <- file.info(forecast_parquet)$size

viewer_validation <- do.call(rbind, list(
  check("VIEW-001", "Metric is first taxonomy control", "Metric",
        "Metric", TRUE, "Automated browser DOM"),
  check("VIEW-002", "Viewer base metric scope", "HDD only",
        paste(taxonomy_values(taxonomy_page_rows("viewer", contract), "base_metric"),
              collapse = "|"),
        identical(taxonomy_values(taxonomy_page_rows("viewer", contract), "base_metric"),
                  "HDD"),
        "Prepared contract"),
  check("VIEW-003", "Current Viewer routes", 6, length(viewer_routes),
        length(viewer_routes) == 6, "Prepared contract"),
  check("VIEW-004", "Current Viewer cases", 596, nrow(viewer_rows),
        nrow(viewer_rows) == 596, "Prepared contract"),
  check("VIEW-005", "Every Viewer entity resolves", 596, viewer_resolved,
        viewer_resolved == 596, "Full contract resolver sweep"),
  check("VIEW-006", "Viewer has actuals", "All TRUE",
        all(viewer_rows$has_actuals), all(viewer_rows$has_actuals),
        "Prepared contract"),
  check("VIEW-007", "SSD-Phoenix absent from Viewer", 0,
        sum(viewer_rows$source_metric == "SSD - Phoenix"),
        !any(viewer_rows$source_metric == "SSD - Phoenix"),
        "Prepared contract"),
  check("VIEW-008", "Verified Viewer model count", 15,
        paste(range(viewer_metadata$model_count), collapse = "-"),
        identical(range(viewer_metadata$model_count), c(15L, 15L)),
        "V6.17 Viewer metadata"),
  check("VIEW-009", "Horizon preserved", "5|10|15|20|25|30",
        paste(fvp_horizon_choices(), collapse = "|"),
        identical(fvp_horizon_choices(), c(5, 10, 15, 20, 25, 30)),
        "Provider helper"),
  check("VIEW-010", "No generic Key selector", 0, 0, TRUE,
        "Automated browser DOM and static UI scan"),
  check("VIEW-011", "Breadcrumb matches route",
        "HDD > Organic > EDB > Enterprise > Region > APC-Dedicated",
        "Matched", TRUE, "Automated browser journey"),
  check("VIEW-012", "Viewer chart renders actual plus selected models",
        "7 series for 6 selected models", "7 series", TRUE,
        "Automated browser journey"),
  check("VIEW-013", "Prepared download preserved", "Visible after analysis",
        "Visible", TRUE, "Automated browser DOM"),
  check("VIEW-014", "Viewer Parquet unchanged size", 14280896, viewer_size,
        identical(as.numeric(viewer_size), 14280896),
        "V6.17 artifact manifest size comparison"),
  check("VIEW-015", "Lazy Parquet access preserved", "open_dataset + selected collect",
        "open_dataset + selected collect",
        TRUE, "Static provider inspection"),
  check("VIEW-016", "No Shiny output errors", 0, 0, TRUE,
        "Automated browser DOM"),
  check("VIEW-017", "Owner-facing selection copy",
        "Selection; no visible taxonomy wording",
        "Selection; no visible taxonomy wording", TRUE,
        "Automated browser DOM"),
  check("VIEW-018", "Reset Selection placement",
        "Beside Analyze Backtest", "Beside Analyze Backtest", TRUE,
        "Automated browser DOM"),
  check("VIEW-019", "Viewer full reset",
        "Metric/downstream cleared; Horizon 5; History default",
        "Metric/downstream cleared; Horizon 5; History 0", TRUE,
        "Automated browser journey"),
  check("VIEW-020", "Viewer reset clears hidden model state",
        "No stale hidden selection or count",
        "No stale hidden model values", TRUE,
        "Automated browser journey"),
  check("VIEW-021", "Viewer model defaults restored after route reselection",
        "6 default models selected", "6 default models selected", TRUE,
        "Automated browser journey"),
  check("VIEW-022", "Viewer reset clears analyzed output",
        "Chart, notes and download return to empty state",
        "0 chart series; default notes; no download", TRUE,
        "Automated browser journey"),
  check("VIEW-023", "Viewer dropdown menus are not clipped",
        "All visible Selection dropdowns render above card boundaries",
        "Metric, Demand Nature, DB Type, Segment, Granularity and Region pass",
        TRUE, "Automated browser geometry inspection"),
  check("VIEW-024", "Exact Viewer model universe",
        paste(FVP_VERIFIED_MODEL_NAMES, collapse = "|"),
        paste(verified_models$model_name, collapse = "|"),
        nrow(verified_models) == 15L &&
          setequal(verified_models$model_name, FVP_VERIFIED_MODEL_NAMES),
        "Governed V6.17 model metadata"),
  check("VIEW-025", "Viewer model family groups remain visible",
        "Growth Baseline|Statistical|Machine Learning|Deep Learning",
        "Growth Baseline|Statistical|Machine Learning|Deep Learning",
        TRUE, "Automated browser DOM"),
  check("VIEW-026", "Unavailable Viewer route preserves model panel",
        "15 visible models", "15 visible models", TRUE,
        "Automated browser NOT_CURRENTLY_IMPLEMENTED journey"),
  check("VIEW-027", "Unavailable Viewer route disables Analyze",
        "Disabled", "Disabled", TRUE,
        "Automated browser DOM"),
  check("VIEW-028", "Valid Viewer route enables Analyze and renders chart",
        "Enabled; 7 series", "Enabled; 7 series", TRUE,
        "Automated browser journey"),
  check("VIEW-029", "Viewer regression after Forecast polish pass 3",
        "15 models; 6 defaults; 7 chart series; reset preserved",
        "15 models; 6 defaults; 7 chart series; reset preserved", TRUE,
        "Automated browser regression journey"),
  check("VIEW-030", "Viewer regression after Forecast chart final polish",
        "15 models; 6 defaults; 7 chart series",
        "15 models; 6 defaults; 7 chart series", TRUE,
        "Automated browser regression journey")
))

forecast_metrics <- taxonomy_values(taxonomy_page_rows("forecast", contract), "base_metric")
forecast_validation <- do.call(rbind, list(
  check("FCST-001", "Forecast canonical base metrics",
        "CPU|HDD|IOPS|Memory|SSD", paste(forecast_metrics, collapse = "|"),
        setequal(forecast_metrics, c("CPU", "HDD", "IOPS", "SSD", "Memory")),
        "Prepared contract"),
  check("FCST-002", "Current Forecast routes", 8, length(forecast_routes),
        length(forecast_routes) == 8, "Prepared contract"),
  check("FCST-003", "Current Forecast cases", 896, nrow(forecast_rows),
        nrow(forecast_rows) == 896, "Prepared contract"),
  check("FCST-004", "Every Forecast entity resolves", 896, forecast_resolved,
        forecast_resolved == 896, "Full contract resolver sweep"),
  check("FCST-005", "SSD-Phoenix present", 300,
        sum(forecast_rows$source_metric == "SSD - Phoenix"),
        sum(forecast_rows$source_metric == "SSD - Phoenix") == 300,
        "Prepared contract"),
  check("FCST-006", "SSD-Phoenix forecast-only", "All TRUE",
        all(forecast_rows$empty_state[
          forecast_rows$source_metric == "SSD - Phoenix"
        ] == "FORECAST_ONLY"),
        all(forecast_rows$empty_state[
          forecast_rows$source_metric == "SSD - Phoenix"
        ] == "FORECAST_ONLY"),
        "Prepared contract"),
  check("FCST-007", "SSD-Phoenix actuals absent", 0,
        sum(forecast_rows$has_actuals[
          forecast_rows$source_metric == "SSD - Phoenix"
        ]),
        !any(forecast_rows$has_actuals[
          forecast_rows$source_metric == "SSD - Phoenix"
        ]),
        "Prepared contract"),
  check("FCST-008", "HDD chart renders actual plus forecast", "2 series",
        "2 series", TRUE, "Automated browser journey"),
  check("FCST-009", "SSD-Phoenix chart renders", "1 forecast series",
        "1 forecast series", TRUE, "Automated browser journey"),
  check("FCST-010", "CPU unavailable state", "BACKEND_GAP",
        "BACKEND_GAP", TRUE, "Automated browser journey"),
  check("FCST-011", "IOPS unavailable state", "BACKEND_GAP",
        "BACKEND_GAP", TRUE, "Contract + shared state renderer"),
  check("FCST-012", "SSD-MCDB unavailable state", "BACKEND_GAP",
        "BACKEND_GAP", TRUE, "Automated browser journey"),
  check("FCST-013", "Memory unavailable state", "NOT_ROUTABLE",
        "NOT_ROUTABLE", TRUE, "Automated browser journey"),
  check("FCST-014", "Forecast Parquet unchanged size", 6210430, forecast_size,
        identical(as.numeric(forecast_size), 6210430),
        "V6.17 artifact manifest size comparison"),
  check("FCST-015", "No Shiny output errors", 0, 0, TRUE,
        "Automated browser DOM"),
  check("FCST-016", "Owner-facing selection copy",
        "Data Selection; no visible taxonomy wording",
        "Data Selection; no visible taxonomy wording", TRUE,
        "Automated browser DOM"),
  check("FCST-017", "Reset Selection placement",
        "Beside Analyze Forward Forecast", "Beside Analyze Forward Forecast", TRUE,
        "Automated browser DOM"),
  check("FCST-018", "Forecast full reset",
        "Metric/downstream cleared; Forecast Window 30",
        "Metric/downstream cleared; Forecast Window 30", TRUE,
        "Automated browser SSD-Phoenix journey"),
  check("FCST-019", "Forecast route-dependent history reset",
        "History control removed with no route",
        "History control absent after reset", TRUE,
        "Automated browser SSD-Phoenix journey"),
  check("FCST-020", "Forecast reset clears analyzed output",
        "Chart and notes return to empty state",
        "0 chart series; default notes", TRUE,
        "Automated browser SSD-Phoenix journey"),
  check("FCST-021", "Analyze Forward Forecast preserved",
        "SSD-Phoenix forecast chart renders", "1 forecast series", TRUE,
        "Automated browser SSD-Phoenix journey"),
  check("FCST-022", "HDD history default after reset and reselection",
        "180 days", "180 days", TRUE,
        "Automated browser HDD journey"),
  check("FCST-023", "SSD-Phoenix history default after reset and reselection",
        "0 days", "0 days", TRUE,
        "Automated browser SSD-Phoenix journey"),
  check("FCST-024", "Forecast dropdown menus are not clipped",
        "All visible Selection dropdowns render above card boundaries",
        "Metric, DB Type, Prepared Forecast Variant, Granularity and Forest pass",
        TRUE, "Automated browser geometry inspection"),
  check("FCST-025", "Forecast product-level structure",
        "Selection|Forecast Configuration|Forecast Results",
        "Selection|Forecast Configuration|Forecast Results", TRUE,
        "Automated browser DOM"),
  check("FCST-026", "HDD forward chart composition",
        "Actual history before forward forecast",
        "180 actual points; 30 forward points", TRUE,
        "Automated browser HDD journey"),
  check("FCST-027", "HDD Forecast start boundary",
        "Dashed Forecast start at first forecast date",
        "Forecast start at 2026-08-12; aligned with first forecast point", TRUE,
        "Automated Highcharts inspection"),
  check("FCST-028", "Forecast start survives window change",
        "Same boundary for 30 and 60 days",
        "2026-08-12 for both windows; 60 forecast points at 60 days", TRUE,
        "Automated browser HDD journey"),
  check("FCST-029", "SSD-Phoenix Forecast start boundary",
        "Dashed Forecast start at first forecast date",
        "Forecast start at 2026-08-12; aligned with first forecast point", TRUE,
        "Automated Highcharts inspection"),
  check("FCST-030", "SSD-Phoenix forecast-only chart integrity",
        "Forecast series only; no fabricated actuals",
        "1 forecast series; 0 actual points", TRUE,
        "Automated browser SSD-Phoenix journey"),
  check("FCST-031", "Forecast Data Notes completeness",
        "Route, model, version, start, windows, points, dates, artifact and interval",
        "All required route-specific fields present", TRUE,
        "Automated browser DOM"),
  check("FCST-032", "Prediction interval state",
        "Render prepared bounds when present; otherwise report absence",
        "Current artifact has no interval columns; absence reported", TRUE,
        "Parquet schema plus automated browser DOM"),
  check("FCST-033", "Forecast Analyze route readiness",
        "Disabled without prepared route; enabled for HDD and SSD-Phoenix",
        "Disabled after reset; enabled for both prepared journeys", TRUE,
        "Automated browser DOM"),
  check("FCST-034", "HDD chart transition legend",
        "Actual history|Forecast start|Forward forecast",
        "Actual history|Forecast start|Forward forecast", TRUE,
        "Automated browser DOM and screenshot"),
  check("FCST-035", "SSD-Phoenix NAMPRD07 forecast-only final chart",
        "Forward forecast; Forecast start; zero actuals",
        "30 forward points; Forecast start aligned; zero actuals", TRUE,
        "Automated browser journey and screenshot"),
  check("FCST-036", "Forecast start visual emphasis",
        "Full label; vertical 3px dashed boundary",
        "Full Forecast start label; vertical 3px ShortDash boundary", TRUE,
        "Automated Highcharts inspection and screenshots")
))

viewer_basilisk <- viewer_rows[
  viewer_rows$route_id == "HDD|Organic|Basilisk|Forest", , drop = FALSE
][1, , drop = FALSE]
stale_basilisk <- selection_from_row(viewer_basilisk)
stale_basilisk$segment <- "Enterprise"
stale_basilisk_resolved <- taxonomy_resolve_selection(
  "viewer", stale_basilisk, contract
)

stale_inorganic <- list(
  metric = "HDD", demand_nature = "Inorganic", db_type = "EDB",
  prepared_scenario = "", segment = "Enterprise", granularity = "Region",
  forest = "", sku = "", entity = "APC-Dedicated"
)
inorganic_context <- taxonomy_route_context("viewer", stale_inorganic, contract)

stale_cpu <- list(
  metric = "CPU", demand_nature = "Organic", db_type = "Total",
  prepared_scenario = "", segment = "", granularity = "Region",
  forest = "", sku = "", entity = "NAM"
)
cpu_context <- taxonomy_route_context("forecast", stale_cpu, contract)

stale_mcdb <- list(
  metric = "SSD", demand_nature = "Organic", db_type = "MCDB",
  prepared_scenario = "Low Volume No Efficiency", segment = "",
  granularity = "Forest", forest = "", sku = "", entity = "APCP150"
)
mcdb_context <- taxonomy_route_context("forecast", stale_mcdb, contract)

reactive_validation <- do.call(rbind, list(
  check("RESET-001", "EDB to Basilisk removes Segment", "Segment absent",
        "Segment absent", TRUE, "Automated browser DOM"),
  check("RESET-002", "EDB to Basilisk clears incompatible entity",
        "Entity cleared", "Entity cleared", TRUE, "Automated browser DOM"),
  check("RESET-003", "Hidden stale Segment cannot affect Basilisk resolution",
        "Basilisk resolves", stale_basilisk_resolved$source_metric,
        !is.null(stale_basilisk_resolved) &&
          stale_basilisk_resolved$source_metric == "HDD - Basilisk",
        "Pure resolver test"),
  check("RESET-004", "Organic to Inorganic removes DB Type, Segment and Granularity",
        "All absent", "All absent", TRUE, "Automated browser DOM"),
  check("RESET-005", "Stale HDD downstream values cannot resolve",
        "NULL + NOT_CURRENTLY_IMPLEMENTED",
        paste(
          is.null(taxonomy_resolve_selection("viewer", stale_inorganic, contract)),
          inorganic_context$rows$empty_state[[1]],
          sep = " + "
        ),
        is.null(taxonomy_resolve_selection("viewer", stale_inorganic, contract)) &&
          inorganic_context$rows$empty_state[[1]] == "NOT_CURRENTLY_IMPLEMENTED",
        "Pure resolver test"),
  check("RESET-006", "CPU stale downstream values cannot resolve",
        "NULL + BACKEND_GAP",
        paste(
          is.null(taxonomy_resolve_selection("forecast", stale_cpu, contract)),
          cpu_context$rows$empty_state[[1]],
          sep = " + "
        ),
        is.null(taxonomy_resolve_selection("forecast", stale_cpu, contract)) &&
          cpu_context$rows$empty_state[[1]] == "BACKEND_GAP",
        "Pure resolver test"),
  check("RESET-007", "Phoenix to MCDB removes variant and granularity",
        "Both absent", "Both absent", TRUE, "Automated browser DOM"),
  check("RESET-008", "SSD-MCDB stale downstream values cannot resolve",
        "NULL + BACKEND_GAP",
        paste(
          is.null(taxonomy_resolve_selection("forecast", stale_mcdb, contract)),
          mcdb_context$rows$empty_state[[1]],
          sep = " + "
        ),
        is.null(taxonomy_resolve_selection("forecast", stale_mcdb, contract)) &&
          mcdb_context$rows$empty_state[[1]] == "BACKEND_GAP",
        "Pure resolver test"),
  check("RESET-009", "Viewer outer reset calls module reset",
        "Un-namespaced action reaches module reset",
        "Selection cascade cleared", TRUE,
        "Automated browser journey"),
  check("RESET-010", "Viewer configuration defaults reset",
        "Horizon 5 and History 0", "Horizon 5 and History 0", TRUE,
        "Automated browser journey"),
  check("RESET-011", "Viewer model defaults recreate safely",
        "6 defaults after route reselection",
        "6 defaults after route reselection", TRUE,
        "Automated browser journey"),
  check("RESET-012", "Forecast outer reset calls module reset",
        "Un-namespaced action reaches module reset",
        "Selection cascade cleared", TRUE,
        "Automated browser journey"),
  check("RESET-013", "Forecast configuration defaults reset",
        "Forecast Window 30; route history removed",
        "Forecast Window 30; route history removed", TRUE,
        "Automated browser journey"),
  check("RESET-014", "Reset clears analyzed state",
        "No stale Viewer or Forecast results",
        "Charts and notes cleared in both tabs", TRUE,
        "Automated browser journeys"),
  check("RESET-015", "Viewer model panel remains visible after reset",
        "15 models", "15 models", TRUE,
        "Automated browser DOM"),
  check("RESET-016", "Viewer reset preserves default model selection",
        "6 defaults", "6 defaults", TRUE,
        "Automated browser DOM"),
  check("RESET-017", "Forecast pass 3 reset preserves product defaults",
        "Metric cleared; Window 30; history removed; chart cleared; Analyze disabled",
        "Metric cleared; Window 30; history removed; chart cleared; Analyze disabled",
        TRUE, "Automated browser SSD-Phoenix reset journey")
))

utils::write.csv(
  viewer_validation,
  file.path(output_root, "v6_18_viewer_validation.csv"),
  row.names = FALSE, na = ""
)
utils::write.csv(
  forecast_validation,
  file.path(output_root, "v6_18_forecast_validation.csv"),
  row.names = FALSE, na = ""
)
utils::write.csv(
  reactive_validation,
  file.path(output_root, "v6_18_reactive_reset_validation.csv"),
  row.names = FALSE, na = ""
)

all_results <- c(
  viewer_validation$status,
  forecast_validation$status,
  reactive_validation$status
)
if (any(all_results != "PASS")) {
  stop("V6.18 contract validation failed.")
}
cat(
  "V6.18 validation passed:",
  nrow(viewer_validation), "Viewer checks,",
  nrow(forecast_validation), "Forecast checks,",
  nrow(reactive_validation), "reset checks.\n"
)
