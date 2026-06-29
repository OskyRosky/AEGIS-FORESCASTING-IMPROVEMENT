# Stage 07 — V2 TTL / Capacity View Layout Cleanup Report

## Objective
Refactor the Forecasting → TTL / Capacity View page so it follows the same
approved collapsible-box layout used in Viewer, Accuracy and Forecast. Layout /
UX only — no data, methodology, TTL, supply, demand, model, forecast or champion
changes. Shiny remains a pure consumer of already-prepared artifacts.

## Scope
- Edited only `shiny_app/ui/tabs.R` (`section_ttl()`).
- No server logic, helpers, CSS or cache changes were required: all server
  output IDs are preserved and the TTL outputs already render eagerly
  (`suspendWhenHidden = FALSE`).

## New layout (six collapsible boxes, existing app collapse pattern)
1. **How to use this TTL / Capacity View** — compact guide, collapsed by default.
2. **TTL Capacity Overview** (open) — prototype/simulated-supply note + the fleet
   KPI cards (Series, Alert, Warning, Healthy, Cool, Soonest crossover) via
   `ttl_summary_cards`.
3. **Set up the TTL view** (open) — controls only: Step 1 Select series, Step 2
   Analyze TTL, plus the note "Demand = real forecast. Supply & TTL = simulated.
   Nothing is written back." No result KPIs, gauge, chart or table.
4. **TTL Results — Selected Series** (open) — result KPI cards (TTL binding,
   constraining resource, utilization today, method) via `ttl_series_kpis`, then
   the Months-to-Live gauge (`ttl_gauge`) and Supply vs Demand crossover
   (`ttl_line`) kept visually together.
5. **Projected Utilization Heatmap** (open) — short description line + the fleet
   heatmap (`ttl_heatmap`).
6. **Time-to-Live Snapshot Table** (collapsed) — short description line + the
   snapshot table (`ttl_table`) + TTL color legend + method note.

## Action-gated behavior
Preserved. The gauge, crossover line and result KPIs still render only after
clicking Analyze TTL (`input$ttl_go`); changing the series does not auto-refresh.

## Chart interactivity
Preserved. No highchart/plotly options changed — crosshair, rectangular zoom,
export/download menu and existing interactivity remain intact (same output IDs
and render functions).

## Text cleanup
User-facing wording uses "Prototype · simulated supply" and an honest
demand-real / supply-simulated explanation. No internal labels (stage07, Shiny
MVP status, blog) are shown.

## Guardrails confirmed
- No data artifacts modified.
- No models/forecasts/backtests run; no TTL/supply/demand recomputation.
- Champion/governance decisions unchanged.
- Viewer, Accuracy, Forecast, Models, Governance and Reference pages untouched.

## Validation
tabs.R parses cleanly (PARSE_OK). Isolated render of `section_ttl()` confirms 6
collapsible boxes, 4 open + 2 collapsed, and all output IDs present. App launched
single clean instance PID 14564 on http://127.0.0.1:3838 — HTTP 200.

## Status
READY_FOR_OSCAR_VISUAL_REVIEW_V2_TTL_CAPACITY_VIEW_LAYOUT
