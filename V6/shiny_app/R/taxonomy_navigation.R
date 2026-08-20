# V6.18 | Shared, read-only Viewer and Forecast taxonomy navigation.

TAXONOMY_NAV_REL_PATH <- file.path(
  "outputs", "v6_18_shiny_dynamic_taxonomy_ui",
  "v6_18_navigation_contract.csv"
)

.taxonomy_navigation_env <- new.env(parent = emptyenv())

taxonomy_navigation_path <- function(root = find_project_root()) {
  file.path(root, TAXONOMY_NAV_REL_PATH)
}

taxonomy_navigation_data <- function(refresh = FALSE) {
  if (!isTRUE(refresh) &&
      exists("contract", envir = .taxonomy_navigation_env, inherits = FALSE)) {
    return(get("contract", envir = .taxonomy_navigation_env, inherits = FALSE))
  }
  path <- taxonomy_navigation_path()
  if (!file.exists(path)) {
    stop("V6.18 navigation contract is missing: ", path)
  }
  contract <- utils::read.csv(
    path, stringsAsFactors = FALSE, check.names = FALSE, na.strings = character()
  )
  required <- c(
    "contract_row_type", "route_id", "base_metric", "display_label",
    "demand_nature", "db_type", "prepared_scenario", "segment",
    "granularity", "entity_label", "forest", "sku", "entity_value",
    "source_metric", "source_scenario", "source_granularity",
    "source_series_key", "viewer_visible", "forecast_visible",
    "viewer_eligible", "forecast_eligible", "has_actuals",
    "serving_status", "support_status", "empty_state", "traceability", "notes"
  )
  missing <- setdiff(required, names(contract))
  if (length(missing) > 0) {
    stop("V6.18 navigation contract is missing columns: ",
         paste(missing, collapse = ", "))
  }
  logical_columns <- c(
    "viewer_visible", "forecast_visible", "viewer_eligible",
    "forecast_eligible", "has_actuals"
  )
  for (column in logical_columns) {
    contract[[column]] <- .tess_as_logical(contract[[column]])
    if (anyNA(contract[[column]])) {
      stop("V6.18 navigation contract contains invalid ", column, " values.")
    }
  }
  assign("contract", contract, envir = .taxonomy_navigation_env)
  contract
}

taxonomy_page_column <- function(page, suffix) {
  if (!page %in% c("viewer", "forecast")) {
    stop("Unknown taxonomy page: ", page)
  }
  paste0(page, "_", suffix)
}

taxonomy_page_rows <- function(page, contract = taxonomy_navigation_data()) {
  visible <- taxonomy_page_column(page, "visible")
  contract[contract[[visible]], , drop = FALSE]
}

taxonomy_operational_rows <- function(page, contract = taxonomy_navigation_data()) {
  eligible <- taxonomy_page_column(page, "eligible")
  contract[
    contract$contract_row_type == "OPERATIONAL_ENTITY" & contract[[eligible]],
    , drop = FALSE
  ]
}

taxonomy_values <- function(rows, column) {
  values <- unique(rows[[column]])
  values <- values[!is.na(values) & nzchar(values)]
  sort(values)
}

# V6.23-P0 | Viewer scope counts derived from the shared contract, never
# hardcoded. Distinguishes the three numbers the header must not conflate:
#   backtest      cases carrying actuals and the 15 governed model backtests
#   forecast_only cases visible in the selector but with no actuals
#   total         everything the Viewer selector exposes
taxonomy_viewer_scope <- function(contract = taxonomy_navigation_data()) {
  rows <- taxonomy_page_rows("viewer", contract)
  rows <- rows[rows$contract_row_type == "OPERATIONAL_ENTITY", , drop = FALSE]
  backtest <- sum(rows$viewer_eligible)
  list(
    total = nrow(rows),
    backtest = backtest,
    forecast_only = nrow(rows) - backtest,
    routes = length(unique(rows$route_id)),
    backtest_routes = length(unique(rows$route_id[rows$viewer_eligible]))
  )
}

taxonomy_filter <- function(rows, column, value) {
  if (is.null(value) || length(value) == 0 || is.na(value) || !nzchar(value)) {
    return(rows[0, , drop = FALSE])
  }
  rows[rows[[column]] == value, , drop = FALSE]
}

taxonomy_valid_value <- function(value, choices) {
  if (is.null(value) || length(value) == 0 || is.na(value) || !value %in% choices) {
    return("")
  }
  value
}

taxonomy_route_context <- function(page, selection,
                                   contract = taxonomy_navigation_data()) {
  rows <- taxonomy_page_rows(page, contract)
  metric <- taxonomy_valid_value(selection$metric, taxonomy_values(rows, "base_metric"))
  if (!nzchar(metric)) {
    return(list(rows = rows[0, , drop = FALSE], selection = list(metric = "")))
  }
  rows <- taxonomy_filter(rows, "base_metric", metric)
  clean <- list(metric = metric)

  axis <- function(column, value) {
    choices <- taxonomy_values(rows, column)
    if (length(choices) == 0) return("")
    selected <- taxonomy_valid_value(value, choices)
    if (nzchar(selected)) {
      rows <<- taxonomy_filter(rows, column, selected)
    } else {
      rows <<- rows[0, , drop = FALSE]
    }
    selected
  }

  if (metric == "HDD") {
    clean$demand_nature <- axis("demand_nature", selection$demand_nature)
    if (!nzchar(clean$demand_nature)) {
      return(list(rows = rows, selection = clean))
    }
    if (clean$demand_nature == "Inorganic") {
      return(list(rows = rows, selection = clean))
    }
    clean$db_type <- axis("db_type", selection$db_type)
    if (!nzchar(clean$db_type)) {
      return(list(rows = rows, selection = clean))
    }
    if (clean$db_type == "EDB") {
      clean$segment <- axis("segment", selection$segment)
      if (!nzchar(clean$segment)) {
        return(list(rows = rows, selection = clean))
      }
    }
  } else if (metric == "SSD") {
    clean$db_type <- axis("db_type", selection$db_type)
    if (!nzchar(clean$db_type)) {
      return(list(rows = rows, selection = clean))
    }
    if (clean$db_type == "MCDB") {
      return(list(rows = rows, selection = clean))
    }
    clean$prepared_scenario <- axis(
      "prepared_scenario", selection$prepared_scenario
    )
    if (!nzchar(clean$prepared_scenario)) {
      return(list(rows = rows, selection = clean))
    }
  } else {
    return(list(rows = rows, selection = clean))
  }

  clean$granularity <- axis("granularity", selection$granularity)
  if (!nzchar(clean$granularity)) {
    return(list(rows = rows, selection = clean))
  }

  if (clean$granularity == "Forest_SKU") {
    clean$forest <- axis("forest", selection$forest)
    if (!nzchar(clean$forest)) {
      return(list(rows = rows, selection = clean))
    }
    clean$sku <- axis("sku", selection$sku)
  } else {
    clean$entity <- axis("entity_value", selection$entity)
  }
  list(rows = rows, selection = clean)
}

taxonomy_resolve_selection <- function(page, selection,
                                       contract = taxonomy_navigation_data()) {
  context <- taxonomy_route_context(page, selection, contract)
  rows <- context$rows
  operational <- rows[rows$contract_row_type == "OPERATIONAL_ENTITY", , drop = FALSE]
  if (nrow(operational) != 1) return(NULL)
  as.list(operational[1, , drop = FALSE])
}

taxonomy_selection_input <- function(input) {
  list(
    metric = input$metric,
    demand_nature = input$demand_nature,
    db_type = input$db_type,
    prepared_scenario = input$prepared_scenario,
    segment = input$segment,
    granularity = input$granularity,
    forest = input$forest,
    sku = input$sku,
    entity = input$entity
  )
}

taxonomy_control <- function(input_id, label, choices, selected = "",
                             hint = NULL, searchable = FALSE) {
  choices <- stats::setNames(choices, choices)
  choices <- c("Select..." = "", choices)
  control <- if (searchable) {
    selectizeInput(
      input_id, NULL, choices = choices, selected = selected, width = "100%",
      options = list(
        placeholder = paste("Search", tolower(label)),
        maxOptions = 400,
        create = FALSE
      )
    )
  } else {
    selectInput(
      input_id, NULL, choices = choices, selected = selected, width = "100%"
    )
  }
  tags$div(
    class = "fvtn-field",
    tags$label(class = "fvtn-label", label),
    control,
    if (!is.null(hint)) tags$p(class = "fvtn-hint", hint)
  )
}

taxonomy_navigation_ui <- function(id) {
  ns <- NS(id)
  tags$div(
    class = "fvtn-navigator",
    tags$div(
      class = "fvtn-rail",
      tags$div(class = "fvtn-panel-title", "Selection"),
      uiOutput(ns("controls"))
    ),
    tags$div(
      class = "fvtn-route-panel",
      uiOutput(ns("breadcrumb")),
      uiOutput(ns("route_state")),
      uiOutput(ns("route_metadata"))
    )
  )
}

taxonomy_navigation_server <- function(id, page) {
  moduleServer(id, function(input, output, session) {
    contract <- taxonomy_navigation_data()
    page_rows <- taxonomy_page_rows(page, contract)
    operational <- taxonomy_operational_rows(page, contract)
    metric_order <- c("HDD", "SSD", "CPU", "IOPS", "Memory")
    metrics <- taxonomy_values(page_rows, "base_metric")
    metrics <- metric_order[metric_order %in% metrics]
    default_metric <- if (length(metrics) > 0) metrics[[1]] else ""
    state <- reactiveValues(
      metric = default_metric,
      demand_nature = "",
      db_type = "",
      prepared_scenario = "",
      segment = "",
      granularity = "",
      forest = "",
      sku = "",
      entity = ""
    )

    output$controls <- renderUI({
      selection <- reactiveValuesToList(state)
      metric <- taxonomy_valid_value(selection$metric, metrics)
      controls <- list(
        taxonomy_control(
          session$ns("metric"), "Metric", metrics, metric,
          if (page == "viewer") {
            "Only actual-bearing prepared Viewer routes are selectable."
          } else {
            "Canonical base metric; unsupported branches stop with an explicit state."
          }
        )
      )
      if (!nzchar(metric)) return(tagList(controls))

      rows <- taxonomy_filter(page_rows, "base_metric", metric)
      add_control <- function(column, input_name, label, hint = NULL,
                              searchable = FALSE) {
        choices <- taxonomy_values(rows, column)
        selected <- taxonomy_valid_value(selection[[input_name]], choices)
        controls[[length(controls) + 1L]] <<- taxonomy_control(
          session$ns(input_name), label, choices, selected, hint, searchable
        )
        if (nzchar(selected)) {
          rows <<- taxonomy_filter(rows, column, selected)
        } else {
          rows <<- rows[0, , drop = FALSE]
        }
        selected
      }

      if (metric == "HDD") {
        demand <- add_control(
          "demand_nature", "demand_nature", "Demand Nature",
          "DB Type and Segment appear only where the selected branch uses them."
        )
        if (!nzchar(demand) || demand == "Inorganic") {
          return(tagList(controls))
        }
        db_type <- add_control("db_type", "db_type", "DB Type")
        if (!nzchar(db_type)) {
          return(tagList(controls))
        }
        if (db_type == "EDB") {
          segment <- add_control("segment", "segment", "Segment")
          if (!nzchar(segment)) {
            return(tagList(controls))
          }
        }
      } else if (metric == "SSD") {
        db_type <- add_control("db_type", "db_type", "DB Type")
        if (!nzchar(db_type) || db_type == "MCDB") {
          return(tagList(controls))
        }
        variant <- add_control(
          "prepared_scenario", "prepared_scenario", "Prepared Forecast Variant",
          paste(
            "Compatibility field preserved verbatim; canonical",
            "Organic/Inorganic mapping is a BACKEND_GAP."
          )
        )
        if (!nzchar(variant)) {
          return(tagList(controls))
        }
      } else {
        return(tagList(controls))
      }

      grain <- add_control("granularity", "granularity", "Granularity")
      if (nzchar(grain) && grain == "Forest_SKU") {
        forest <- add_control(
          "forest", "forest", "Forest", "Observed Forest values only.", TRUE
        )
        if (nzchar(forest)) {
          add_control("sku", "sku", "SKU", "Observed Forest x SKU pairs only.", TRUE)
        }
      } else if (nzchar(grain)) {
        label <- if (grain == "Region") "Region" else "Forest"
        add_control(
          "entity_value", "entity", label,
          paste(length(taxonomy_values(rows, "entity_value")), "prepared values on route."),
          TRUE
        )
      }
      tagList(controls)
    })

    clear_state <- function(ids) {
      for (input_id in ids) {
        state[[input_id]] <- ""
      }
    }
    reset_selection <- function() {
      state$metric <- ""
      clear_state(c(
        "demand_nature", "db_type", "prepared_scenario", "segment",
        "granularity", "forest", "sku", "entity"
      ))
    }

    observeEvent(input$metric, {
      value <- input$metric
      if (is.null(value) || identical(value, state$metric)) return()
      state$metric <- value
      clear_state(c(
        "demand_nature", "db_type", "prepared_scenario", "segment",
        "granularity", "forest", "sku", "entity"
      ))
    }, ignoreInit = FALSE)
    observeEvent(input$demand_nature, {
      value <- input$demand_nature
      if (is.null(value) || identical(value, state$demand_nature)) return()
      state$demand_nature <- value
      clear_state(c(
        "db_type", "prepared_scenario", "segment", "granularity",
        "forest", "sku", "entity"
      ))
    }, ignoreInit = FALSE)
    observeEvent(input$db_type, {
      value <- input$db_type
      if (is.null(value) || identical(value, state$db_type)) return()
      state$db_type <- value
      clear_state(c(
        "prepared_scenario", "segment", "granularity", "forest", "sku", "entity"
      ))
    }, ignoreInit = FALSE)
    observeEvent(input$prepared_scenario, {
      value <- input$prepared_scenario
      if (is.null(value) || identical(value, state$prepared_scenario)) return()
      state$prepared_scenario <- value
      clear_state(c("granularity", "forest", "sku", "entity"))
    }, ignoreInit = FALSE)
    observeEvent(input$segment, {
      value <- input$segment
      if (is.null(value) || identical(value, state$segment)) return()
      state$segment <- value
      clear_state(c("granularity", "forest", "sku", "entity"))
    }, ignoreInit = FALSE)
    observeEvent(input$granularity, {
      value <- input$granularity
      if (is.null(value) || identical(value, state$granularity)) return()
      state$granularity <- value
      clear_state(c("forest", "sku", "entity"))
    }, ignoreInit = FALSE)
    observeEvent(input$forest, {
      value <- input$forest
      if (is.null(value) || identical(value, state$forest)) return()
      state$forest <- value
      clear_state(c("sku", "entity"))
    }, ignoreInit = FALSE)
    observeEvent(input$sku, {
      value <- input$sku
      if (is.null(value) || identical(value, state$sku)) return()
      state$sku <- value
    }, ignoreInit = FALSE)
    observeEvent(input$entity, {
      value <- input$entity
      if (is.null(value) || identical(value, state$entity)) return()
      state$entity <- value
    }, ignoreInit = FALSE)

    selection <- reactive(reactiveValuesToList(state))
    resolved <- reactive(taxonomy_resolve_selection(page, selection(), contract))

    breadcrumb_values <- reactive({
      context <- taxonomy_route_context(page, selection(), contract)
      clean <- context$selection
      values <- unlist(clean[c(
        "metric", "demand_nature", "db_type", "prepared_scenario",
        "segment", "granularity", "forest", "sku", "entity"
      )], use.names = FALSE)
      values[!is.na(values) & nzchar(values)]
    })

    output$breadcrumb <- renderUI({
      values <- breadcrumb_values()
      if (length(values) == 0) {
        return(tags$div(class = "fvtn-breadcrumb is-empty", "Select a Metric"))
      }
      pieces <- lapply(seq_along(values), function(index) {
        tagList(
          if (index > 1) tags$span(class = "fvtn-separator", "\u203a"),
          tags$span(class = "fvtn-crumb", values[[index]])
        )
      })
      tags$div(class = "fvtn-breadcrumb", pieces)
    })

    output$route_state <- renderUI({
      route <- resolved()
      if (!is.null(route)) {
        status <- if (identical(route$empty_state, "FORECAST_ONLY")) {
          "FORECAST_ONLY"
        } else {
          "OPERATIONAL"
        }
        return(tags$div(
          class = paste("fvtn-state", tolower(status)),
          tags$span(class = "fvtn-state-code", status),
          if (status == "FORECAST_ONLY") {
            "Prepared forward forecast is available; actuals are not available."
          } else {
            "Prepared route and entity are available."
          }
        ))
      }
      context <- taxonomy_route_context(page, selection(), contract)
      info <- context$rows[
        context$rows$contract_row_type == "INFORMATIONAL_ROUTE", , drop = FALSE
      ]
      if (nrow(info) > 0) {
        state <- info$empty_state[[1]]
        return(tags$div(
          class = "fvtn-state is-gap",
          tags$span(class = "fvtn-state-code", state),
          info$notes[[1]]
        ))
      }
      tags$div(
        class = "fvtn-state is-waiting",
        tags$span(class = "fvtn-state-code", "SELECT_ROUTE"),
        "Complete the visible selection controls. Hidden dimensions do not apply."
      )
    })

    output$route_metadata <- renderUI({
      route <- resolved()
      if (is.null(route)) return(NULL)
      card <- function(label, value) {
        tags$div(
          class = "fvtn-meta-card",
          tags$span(class = "fvtn-meta-label", label),
          tags$span(class = "fvtn-meta-value", value)
        )
      }
      tagList(
        tags$div(
          class = "fvtn-meta-grid",
          card("Route", route$route_id),
          card("Display label", route$display_label),
          card("Entity type", route$entity_label),
          card("Serving status", route$serving_status),
          card("Support", route$support_status),
          card("Actuals", if (isTRUE(route$has_actuals)) "Available" else "Not available")
        ),
        if (nzchar(route$notes)) tags$p(class = "fvtn-route-note", route$notes)
      )
    })

    outputOptions(output, "controls", suspendWhenHidden = FALSE)
    outputOptions(output, "breadcrumb", suspendWhenHidden = FALSE)
    outputOptions(output, "route_state", suspendWhenHidden = FALSE)
    outputOptions(output, "route_metadata", suspendWhenHidden = FALSE)

    list(
      selection = selection,
      resolved = resolved,
      reset = reset_selection,
      operational_rows = function() operational
    )
  })
}
