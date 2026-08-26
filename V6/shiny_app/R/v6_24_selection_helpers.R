# TESSERACT v2 | v6_24_selection_helpers.R
# V6.24-P9C | Progressive selection for the V6.24 MVP section.
#
# CONTRACT
#   Every option, label, chip and card on this page is READ from
#   navigation_contract. Nothing is computed, nothing is hardcoded, and
#   route_path is never parsed by position - SSD carries "Phoenix" in the slot
#   where HDD carries "Organic", so positional parsing would produce wrong
#   controls.
#
#   The axis order is fixed: metric first, the operational key last. The key is
#   NOT a canonical axis (102 distinct keys cover 140 series), so it can never
#   be an entry point.

# Conditional tokens: values that mean "this axis does not apply to this
# branch". They are real values in the contract and must be shown, but as
# static context rather than as a dropdown choice the user has to make.
V6_24_CONDITIONAL_TOKENS <- c(
  "NOT_APPLICABLE",
  "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE"
)

# Friendly wording for those tokens, so the selection card does not show raw
# artifact jargon to a product user.
V6_24_CONDITIONAL_WORDING <- c(
  NOT_APPLICABLE = "does not apply to this route",
  UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE = "not carried by the source"
)

# Default axis labels. The final axis label is resolved dynamically.
V6_24_AXIS_LABEL <- c(
  metric = "Metric", db_type = "DB Type", scenario = "Scenario",
  segment = "Segment", granularity = "Granularity", key = "Operational Key"
)

# Short hints, mirroring the tone of the legacy Selection rail.
V6_24_AXIS_HINT <- c(
  metric = "Only metrics with a governed MVP cohort are selectable.",
  db_type = "Appears only where the selected branch uses it.",
  scenario = "Appears only where the selected branch uses it.",
  segment = "Appears only where the selected branch uses it.",
  granularity = "Determines what the final selection represents.",
  key = "Routing or identifier value for the selected granularity."
)

#' Dynamic label for the final axis.
#'
#' Derived from key_axis_status, which P7 emits per row. Never inferred from
#' the key value itself and never from route_path position.
v6_24_final_axis_label <- function(rows) {
  if (is.null(rows) || !nrow(rows) || !"key_axis_status" %in% names(rows)) {
    return(list(label = "Operational Key", basis = "DEFAULT_NO_ROWS"))
  }
  st <- unique(as.character(rows$key_axis_status))
  st <- st[!is.na(st) & nzchar(st)]
  if (length(st) != 1) {
    # Mixed granularities still in scope: stay neutral rather than guess.
    return(list(label = "Operational Key",
                basis = paste0("MIXED:", paste(st, collapse = "|"))))
  }
  lbl <- switch(
    st,
    ROUTING_VALUE_REGION = "Region",
    IDENTIFIER_VALUE_FOREST = "Forest",
    COMPOSITE_TOKEN_FOREST_SKU = "Forest / SKU",
    "Operational Key")
  list(label = lbl, basis = st)
}

#' Distinct values of one axis within a set of contract rows.
v6_24_axis_values <- function(rows, axis) {
  if (is.null(rows) || !nrow(rows) || !axis %in% names(rows)) return(character(0))
  v <- unique(as.character(rows[[axis]]))
  sort(v[!is.na(v) & nzchar(v)])
}

#' Narrow contract rows by the choices made so far.
v6_24_narrow <- function(rows, chosen, upto = NULL) {
  axes <- V6_24_FILTER_AXES
  if (!is.null(upto)) axes <- axes[seq_len(match(upto, axes) - 1L)]
  for (a in axes) {
    v <- chosen[[a]]
    if (is.null(v) || !nzchar(v) || !a %in% names(rows)) next
    rows <- rows[as.character(rows[[a]]) == v, , drop = FALSE]
  }
  rows
}

#' Resolve the whole axis chain into a render plan.
#'
#' For each axis, given the choices already made, decide whether it is:
#'   CHOICE  - more than one real value remains, so ask the user
#'   CONTEXT - exactly one value remains, so state it instead of asking
#'   LOCKED  - a parent has not been chosen yet, so it is not shown at all
#'
#' This is what makes the selection progressive: an axis that cannot
#' discriminate never becomes a control the user has to think about.
v6_24_selection_plan <- function(chosen, rows = v6_24_operational()) {
  plan <- list()
  cur <- rows
  parent_open <- TRUE

  for (i in seq_along(V6_24_FILTER_AXES)) {
    axis <- V6_24_FILTER_AXES[[i]]
    vals <- v6_24_axis_values(cur, axis)
    chosen_val <- chosen[[axis]]
    chosen_val <- if (is.null(chosen_val)) "" else as.character(chosen_val)

    lbl <- if (axis == "key") v6_24_final_axis_label(cur)$label
           else V6_24_AXIS_LABEL[[axis]]

    if (!parent_open) {
      plan[[axis]] <- list(axis = axis, label = lbl, state = "LOCKED",
                           values = vals, selected = "", n = length(vals))
      next
    }
    if (length(vals) == 0) {
      plan[[axis]] <- list(axis = axis, label = lbl, state = "LOCKED",
                           values = vals, selected = "", n = 0)
      parent_open <- FALSE
      next
    }
    if (length(vals) == 1) {
      # Only one possibility: state it, do not ask.
      only <- vals[[1]]
      plan[[axis]] <- list(
        axis = axis, label = lbl, state = "CONTEXT", values = vals,
        selected = only, n = 1,
        conditional = only %in% V6_24_CONDITIONAL_TOKENS)
      cur <- v6_24_narrow(cur, stats::setNames(list(only), axis))
      next
    }
    # A real choice.
    sel <- if (nzchar(chosen_val) && chosen_val %in% vals) chosen_val else ""
    plan[[axis]] <- list(axis = axis, label = lbl, state = "CHOICE",
                         values = vals, selected = sel, n = length(vals),
                         conditional = FALSE)
    if (nzchar(sel)) {
      cur <- v6_24_narrow(cur, stats::setNames(list(sel), axis))
    } else {
      parent_open <- FALSE
    }
  }
  list(plan = plan, rows = cur)
}

#' The effective selection, including axes auto-resolved as CONTEXT.
v6_24_effective_selection <- function(chosen, rows = v6_24_operational()) {
  sp <- v6_24_selection_plan(chosen, rows)
  out <- list()
  for (a in V6_24_FILTER_AXES) {
    st <- sp$plan[[a]]
    out[[a]] <- if (!is.null(st) && nzchar(st$selected)) st$selected else ""
  }
  out
}

#' Resolve to a single operational row, or NULL when the path is incomplete
#' or still ambiguous. Detail panels must only render when this returns a row.
v6_24_resolve_one <- function(chosen, rows = v6_24_operational()) {
  sp <- v6_24_selection_plan(chosen, rows)
  if (nrow(sp$rows) == 1L) sp$rows[1, , drop = FALSE] else NULL
}

#' Demand nature for a series, read from actuals_normalized.
#'
#' It is constant "Organic" across the current 140-series cohort, so it must
#' never become a dropdown. Read rather than hardcoded so it stays true if the
#' cohort ever changes.
v6_24_demand_nature <- function(series_id) {
  a <- v6_24_tbl("actuals")
  if (!nrow(a) || !"demand_nature" %in% names(a) || is.null(series_id)) return("")
  g <- a[as.character(a$series_id) == series_id, , drop = FALSE]
  if (!nrow(g)) return("")
  v <- unique(as.character(g$demand_nature))
  if (length(v) == 1) v else paste(v, collapse = " | ")
}

# ---------------------------------------------------------------------
# Tag builders. Presentation only.
# ---------------------------------------------------------------------

#' Breadcrumb chips for the path being built.
v6_24_breadcrumb <- function(plan) {
  pieces <- list()
  for (a in V6_24_FILTER_AXES) {
    st <- plan[[a]]
    if (is.null(st) || !nzchar(st$selected)) next
    val <- st$selected
    cls <- "v24-crumb"
    if (isTRUE(st$conditional)) {
      cls <- paste(cls, "is-context")
      val <- V6_24_CONDITIONAL_WORDING[[val]]
      if (is.null(val) || is.na(val)) val <- st$selected
    }
    pieces[[length(pieces) + 1]] <- shiny::tags$span(
      class = cls, shiny::tags$em(class = "v24-crumb-k", st$label), val)
  }
  if (!length(pieces)) {
    return(shiny::tags$div(class = "v24-breadcrumb is-empty", "Select a Metric"))
  }
  shiny::tags$div(class = "v24-breadcrumb", pieces)
}

#' Status badge from product_status. Colour follows the field, never a list.
v6_24_status_badge <- function(status) {
  cls <- if (identical(status, "AVAILABLE")) "v24-rbadge is-ok" else "v24-rbadge is-caveat"
  msg <- if (identical(status, "AVAILABLE"))
    "Prepared route and entity are available."
  else "Available, with context you should read before interpreting."
  shiny::tags$div(class = cls,
                  shiny::tags$strong(status),
                  shiny::tags$span(msg))
}

#' One route metadata cell.
v6_24_rcell <- function(k, v) {
  shiny::tags$div(class = "v24-rcell",
                  shiny::tags$div(class = "v24-rcell-k", k),
                  shiny::tags$div(class = "v24-rcell-v", v))
}

#' Route metadata card grid for a resolved row.
v6_24_route_cards <- function(row) {
  fl <- v6_24_final_axis_label(row)
  dn <- v6_24_demand_nature(as.character(row$series_id[1]))
  shiny::tags$div(
    class = "v24-rgrid",
    v6_24_rcell("Route", as.character(row$route_path[1])),
    v6_24_rcell("Display label", as.character(row$route_display_label[1])),
    v6_24_rcell("Entity type", fl$label),
    v6_24_rcell(fl$label, as.character(row$key[1])),
    v6_24_rcell("Granularity", as.character(row$granularity[1])),
    v6_24_rcell("Demand nature", if (nzchar(dn)) dn else "not carried"),
    v6_24_rcell("Series ID", as.character(row$series_id[1])),
    v6_24_rcell("Signal quality", as.character(row$signal_quality_status[1])),
    v6_24_rcell("Viewer", as.character(row$viewer_visible[1])),
    v6_24_rcell("Forecast", as.character(row$forecast_visible[1])),
    v6_24_rcell("Champion shown", as.character(row$champion_visible[1])),
    v6_24_rcell("Forecast horizon",
                paste0(row$forecast_steps[1], " daily steps"))
  )
}

#' Context notes that must be read before interpreting the series.
#' Every branch reads a FIELD; no series is ever named in code.
v6_24_context_notes <- function(row) {
  notes <- list()
  if (identical(as.character(row$champion_visible[1]), "FALSE")) {
    notes[[length(notes) + 1]] <- shiny::tags$div(
      class = "v24-note-card is-attention",
      shiny::tags$strong("Champion is not a recommendation for this series."),
      shiny::tags$p(paste(
        "Every observed actual is zero, so the top-ranked model is a technical",
        "tie-break only. The series stays fully available in Viewer and",
        "Forecast.")))
  }
  if (identical(as.character(row$low_confidence_backtest_window_flag[1]), "TRUE")) {
    notes[[length(notes) + 1]] <- shiny::tags$div(
      class = "v24-note-card is-moderate",
      shiny::tags$strong("Accuracy for this series is low confidence."),
      shiny::tags$p(paste(
        "The series carries real history, but its backtest evaluation window",
        "falls in a zero tail, so percentage errors are not computable and the",
        "ranking is less informative.")))
  }
  if (identical(as.character(row$trailing_zero_latest_actual_flag[1]), "TRUE")) {
    notes[[length(notes) + 1]] <- shiny::tags$div(
      class = "v24-note-card is-soft",
      shiny::tags$strong("The most recent observed value is zero."),
      shiny::tags$p("The series carries signal overall but ends in a zero tail."))
  }
  if (!length(notes)) return(NULL)
  shiny::tags$div(class = "v24-notes", notes)
}
