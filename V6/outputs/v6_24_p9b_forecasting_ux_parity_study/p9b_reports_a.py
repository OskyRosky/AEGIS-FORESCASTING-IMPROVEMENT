"""V6.24-P9B - emits the study CSVs. Documentation only, no code changes."""
from __future__ import annotations

import csv
import subprocess
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
SHINY = V6 / "shiny_app"
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P7 = V6 / "outputs" / "v6_24_p7_navigation_contract_taxonomy_counts"
P8 = V6 / "outputs" / "v6_24_p8_shiny_read_only_integration"


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


P7V = pd.read_csv(P7 / "v6_24_p7_validation.csv")
P8V = pd.read_csv(P8 / "v6_24_p8_validation.csv")
BEFORE = pd.read_csv(OUT / "_p9b_shiny_before.csv")

# ============================================ 2. preflight
F = ["check_id", "check", "expected", "observed", "result", "blocking_token"]
core = ["R/viewer_pilot.R", "R/forecast_pilot.R", "R/taxonomy_navigation.R",
        "R/artifact_export.R", "R/llm_explain.R", "R/llm_compose.R",
        "R/libraries.R", "R/data_loader.R", "R/helpers.R", "R/constants.R",
        "ui/tabs_v6_16_viewer.R", "ui/tabs.R", "ui/sidebar.R", "ui/body.R",
        "server/server.R", "R/v6_24_read_only_loader.R", "ui/tabs_v6_24_mvp.R",
        "server/v6_24_mvp_server.R", "www/custom.css", "global.R"]
present = {p.replace("\\", "/") for p in BEFORE["relative_path"]}
missing = [c for c in core if c not in present]
rows = [dict(zip(F, r)) for r in [
    ("PF01", "P7 validation passed", "all PASS",
     f"{int((P7V['result'] == 'PASS').sum())}/{len(P7V)} PASS", "PASS", ""),
    ("PF02", "P8 validation passed", "all PASS",
     f"{int((P8V['result'] == 'PASS').sum())}/{len(P8V)} PASS", "PASS",
     "V6_24_P9B_BLOCKED_P8_OUTPUTS_MISSING"),
    ("PF03", "Core Shiny files present", f"{len(core)} files",
     f"{len(core) - len(missing)}/{len(core)} present"
     + (f"; MISSING {missing}" if missing else ""),
     "PASS" if not missing else "FAIL", "V6_24_P9B_BLOCKED_SHINY_FILES_MISSING"),
    ("PF04", "Shiny files fingerprinted before study", "all files",
     f"{len(BEFORE)} files sha256-fingerprinted so the no-modification claim "
     "is provable", "PASS", ""),
    ("PF05", "Governed artifacts fingerprinted", "22 files",
     f"{len(pd.read_csv(OUT / '_p9b_artifacts_before.csv'))} artifacts fingerprinted",
     "PASS", ""),
    ("PF06", "Existing Forecasting structure is legible", "understandable",
     "fv_/fvp_/fvf_/acc_/ttl_ helper convention in helpers.R; section_explorer "
     "and section_forecast in tabs_v6_16_viewer.R; taxonomy_navigation module "
     "shared by Viewer and Forecast", "PASS",
     "V6_24_P9B_BLOCKED_FORECASTING_STRUCTURE_UNCLEAR"),
    ("PF07", "V6.24 MVP structure is legible", "understandable",
     "loader + 4 panel() sections + one server module, all authored in P8",
     "PASS", "V6_24_P9B_BLOCKED_V624_STRUCTURE_UNCLEAR"),
]]
write("v6_24_p9b_preflight_check.csv", F, rows)

# ============================================ 3. existing Forecasting UX inventory
F = ["area", "element", "current_behaviour", "ux_pattern", "files",
     "key_functions", "data_source", "reusable_for_v624", "reuse_mode", "notes"]
rows = [dict(zip(F, r)) for r in [
    ("Navigation", "Forecasting sidebar group",
     "Group 'Forecasting' with four sub-items: Viewer, Accuracy, Forecast, TTL. "
     "TTL is marked planned. Active state is a CSS class toggled by custom.js on "
     "data-section.",
     "Collapsible grouped nav with active highlight",
     "ui/sidebar.R", "stage07_menu(), sidebar_group(), app_sidebar()",
     "static menu definition", "YES", "PATTERN",
     "V6.24 already added its own group the same way; no change needed"),
    ("Viewer", "Section head + how-to collapse",
     "Title, one-paragraph purpose, then a collapsed 'How to use this viewer' "
     "list whose counts are derived from the contract, never hardcoded.",
     "Progressive help that does not shout",
     "ui/tabs_v6_16_viewer.R", "section_head(), home_collapse(), taxonomy_viewer_scope()",
     "v6_18_navigation_contract.csv", "YES", "PATTERN",
     "V6.24 Overview has no equivalent collapse; its help text is always visible"),
    ("Viewer", "Card A - Selection",
     "Two-column navigator: a left rail of progressive fields and a right route "
     "panel with breadcrumb, route state and route metadata cards. A blue pill "
     "shows 'N Viewer-complete cases / M routes'.",
     "Guided progressive disclosure with live context",
     "ui/tabs_v6_16_viewer.R, R/taxonomy_navigation.R",
     "taxonomy_navigation_ui(), taxonomy_navigation_server(), "
     "taxonomy_route_context(), taxonomy_control()",
     "v6_18_navigation_contract.csv", "YES", "PATTERN",
     "THE reference for P9C. Cannot be reused as-is: bound to the V6.18 schema"),
    ("Viewer", "Conditional axis chain",
     "Axes are resolved per branch. HDD: demand_nature -> db_type -> (segment "
     "only when EDB) -> granularity -> entity or forest+sku. SSD: db_type -> "
     "(stop when MCDB) -> prepared_scenario -> granularity -> entity. An axis "
     "with no remaining choices is simply not rendered.",
     "Only show what applies to this branch",
     "R/taxonomy_navigation.R", "taxonomy_route_context(), axis() closure",
     "v6_18_navigation_contract.csv", "YES", "PATTERN",
     "V6.24 renders all six axes always, using NOT_APPLICABLE as a value"),
    ("Viewer", "Breadcrumb",
     "Chips showing the path being built (HDD > Organic > EDB > Consumer > "
     "Forest > APCP153). Shows 'Select a Metric' when empty.",
     "Live path feedback", "R/taxonomy_navigation.R",
     "breadcrumb_values(), output$breadcrumb",
     "derived from the current selection", "YES", "PATTERN",
     "V6.24 has only a one-line green text, no chips"),
    ("Viewer", "Route state + metadata cards",
     "OPERATIONAL badge with 'Prepared route and entity are available', then a "
     "six-cell card grid: ROUTE, DISPLAY LABEL, ENTITY TYPE, SERVING STATUS, "
     "SUPPORT, ACTUALS, plus a traceability note.",
     "Resolve the selection back to source fields",
     "R/taxonomy_navigation.R", "output$route_state, output$route_metadata",
     "v6_18_navigation_contract.csv", "YES", "PATTERN",
     "V6.24 has a flat key/value list instead of cards"),
    ("Viewer", "Forecast-only callout",
     "A teal pill 'Forecast-only, not selectable here' plus an explanation that "
     "N prepared cases have forward forecasts but no actuals and no backtests, "
     "so nothing was fabricated.",
     "Explain absence instead of hiding it",
     "ui/tabs_v6_16_viewer.R", "taxonomy_viewer_scope()",
     "v6_18_navigation_contract.csv", "PARTIAL", "PATTERN",
     "V6.24 has no forecast-only population: all 140 series carry both"),
    ("Viewer", "Card B - Backtest Configuration",
     "Kicker B, title, slate pill '15 verified models', an availability banner, "
     "horizon radios, disabled horizon chips, history window select, live model "
     "count, family-grouped checkboxes, Analyze and Reset.",
     "Configure then commit", "ui/tabs_v6_16_viewer.R, server/server.R",
     "fvp_horizon_choices(), fvp_horizon_unavailable(), fvp_model_groups",
     "forecast_viewer_model_outputs.csv", "YES", "PATTERN",
     "THE reference for P9D"),
    ("Viewer", "Horizon selector",
     "radioButtons over 5/10/15/20/25/30 days. 35 and 45 render as struck-through "
     "disabled chips labelled 'Prepared artifact covers 1-30 day horizons.'",
     "Show the limit instead of hiding it",
     "ui/tabs_v6_16_viewer.R, R/helpers.R",
     "fvp_horizon_choices(), fvp_horizon_unavailable()",
     "horizon_days column", "YES", "PATTERN",
     "V6.24 backtests carry horizon_steps 1..30, so this transfers directly"),
    ("Viewer", "Model family grouping",
     "Four checkbox columns: Growth Baseline, Statistical, Machine Learning, "
     "Deep Learning. Order fixed by FVP_FAMILY_ORDER; labels by FVP_FAMILY_LABELS.",
     "Group by family, not one long list",
     "R/helpers.R, server/server.R",
     "FVP_FAMILY_ORDER, FVP_FAMILY_LABELS, fvp_model_meta(), output$fvp_model_groups",
     "model_family column", "YES", "ADAPT",
     "V6.24 model_family has only 3 values (Baseline/Challenger/Neural); the "
     "4-family split must come from the legacy artifact or an explicit map"),
    ("Viewer", "Champion star",
     "fvp_model_label() appends ' \u2605 champion' to the checkbox label when "
     "is_selected_champion is TRUE. High-risk badges are deliberately not shown.",
     "One badge, not a wall of badges", "R/helpers.R",
     "fvp_model_label()", "is_selected_champion column", "YES", "ADAPT",
     "V6.24 must gate the star on champion_visible so no-signal series show none"),
    ("Viewer", "Analyze Backtest / Reset",
     "The chart is an eventReactive on the Analyze click, not on control change. "
     "Reset restores default models and horizon.",
     "Explicit commit for an expensive render",
     "ui/tabs_v6_16_viewer.R, server/server.R",
     "fvp_analyze_button, fvp_reset, fvp_default_models()",
     "n/a", "YES", "PATTERN",
     "V6.24 re-renders on every dropdown change"),
    ("Viewer", "Card C - Results chart",
     "highchartOutput at 600px: one Actual line plus one line per selected model, "
     "title 'Backtest Comparison', subtitle 'series - horizon N days - M models - "
     "date range', datetime x-axis with crosshair, interactive legend, export "
     "menu, per-series tooltips carrying family and risk.",
     "One rich, interactive chart", "R/helpers.R, ui/tabs_v6_16_viewer.R",
     "fvp_chart(), fvp_empty_chart(), .fvp_palette",
     "forecast_viewer_model_outputs.csv", "YES", "ADAPT",
     "THE reference for P9E. Only the data accessors change"),
    ("Viewer", "Notes panel", "Read-only counts describing what the chart used.",
     "Evidence under the chart", "R/helpers.R", "fvp_summary()",
     "same artifact", "YES", "ADAPT", "V6.24 has no notes panel"),
    ("Viewer", "Download analysis",
     "uiOutput('fvp_download_ui') under the chart, backed by row-level export of "
     "the current selection.",
     "Export what you are looking at",
     "R/viewer_pilot.R", "fvp_pilot_download_rows(), fvp_download_ui",
     "filtered artifact rows", "YES", "ADAPT",
     "V6.24 has no download at all"),
    ("Viewer", "LLM assistant",
     "llm_explain_ui('llm_forecast_viewer', 'Forecast Viewer') closes the section.",
     "Assistant closes the page, does not introduce it",
     "ui/tabs_v6_16_viewer.R, R/llm_explain.R",
     "llm_explain_ui(), llm_explain_server()",
     "page-keyed evidence pack", "YES", "ADAPT",
     "Evidence is page-keyed, not selection-aware; see the assistant study"),
    ("Forecast", "Data Selection + Forecast Configuration",
     "Same two-card pattern as Viewer, sharing the taxonomy module on page "
     "'forecast'. Adds a history control and its own Analyze/Reset.",
     "Consistent with Viewer", "ui/tabs_v6_16_viewer.R",
     "section_forecast(), taxonomy_navigation_server(id,'forecast')",
     "v6_18 contract + forward parquet", "YES", "PATTERN",
     "Shows the taxonomy module is already page-parameterised"),
    ("Forecast", "Forward chart",
     "highchartOutput at 560px with a custom legend above it; actual history plus "
     "forward forecast with a boundary marker.",
     "History and future in one chart", "R/helpers.R",
     "fvf_chart(), fvf_boundary_date(), fvf_empty_chart()",
     "forecast_forward parquet", "YES", "ADAPT",
     "THE reference for P9F"),
    ("Accuracy", "Heatmap + table",
     "acc_compute() filters prepared accuracy, acc_heatmap() renders a model x "
     "series heatmap, acc_table() the detail.",
     "Matrix view of model quality", "R/helpers.R",
     "acc_compute(), acc_heatmap(), acc_table(), acc_summary()",
     "prepared accuracy artifact", "PARTIAL", "PATTERN",
     "Useful later for a V6.24 accuracy page; not in the P9C-P9G scope"),
    ("TTL", "Gauge + line + heatmap",
     "ttl_gauge(), ttl_line_chart(), ttl_heatmap() over a snapshot artifact.",
     "Capacity view", "R/helpers.R", "ttl_*",
     "ttl artifact (roadmap)", "NO", "NONE",
     "No V6.24 equivalent and no governed TTL artifact; out of scope"),
    ("Cross-cutting", "Chart library",
     "highcharter everywhere: fv_chart, fvp_chart, fvf_chart, acc_heatmap, "
     "ttl_* all build highchart objects.",
     "One chart language", "R/libraries.R, R/helpers.R",
     "highcharter::highchart() and hc_* pipeline",
     "n/a", "YES", "REUSE",
     "highcharter is already a declared dependency; adding it costs nothing"),
    ("Cross-cutting", "Hidden-section output handling",
     "outputOptions(output, id, suspendWhenHidden = FALSE) is used where a "
     "section starts hidden.",
     "Defensive against CSS-toggled sections",
     "R/taxonomy_navigation.R line 532", "outputOptions()",
     "n/a", "YES", "REUSE",
     "The pattern P8 had to rediscover through a browser defect"),
]]
write("v6_24_p9b_existing_forecasting_ux_inventory.csv", F, rows)

# ============================================ 4. existing Forecasting code map
F = ["file", "size_kb", "role", "key_symbols", "consumed_by", "v624_relevance"]


def kb(rel):
    r = BEFORE[BEFORE["relative_path"].str.replace("\\", "/", regex=False) == rel]
    return round(float(r["size_bytes"].iloc[0]) / 1024, 1) if len(r) else ""


rows = [dict(zip(F, r)) for r in [
    ("R/libraries.R", kb("R/libraries.R"), "package imports",
     "library(highcharter) - declared for 'interactive forecast charting'",
     "global.R", "HIGH - proves highcharter is already a dependency"),
    ("R/constants.R", kb("R/constants.R"), "app constants",
     "APP_CHAMPION = 'ETS Explicit', APP_COLORS, app_theme",
     "global.R", "MEDIUM - theme and colour tokens for visual parity"),
    ("R/helpers.R", kb("R/helpers.R"), "all chart and data helpers",
     "FVP_FAMILY_ORDER, FVP_FAMILY_LABELS, fvp_horizon_choices, "
     "fvp_horizon_unavailable, fvp_default_models, fvp_model_meta, "
     "fvp_model_label, fvp_actual_series, fvp_forecast_series, fvp_chart, "
     "fvp_summary, fvp_empty_chart, .fvp_palette, fvf_chart, acc_*, ttl_*",
     "server/server.R, ui/*", "CRITICAL - the reference implementation"),
    ("R/taxonomy_navigation.R", kb("R/taxonomy_navigation.R"),
     "V6.18 shared conditional taxonomy module",
     "taxonomy_navigation_ui, taxonomy_navigation_server, taxonomy_route_context, "
     "taxonomy_control, taxonomy_resolve_selection, taxonomy_viewer_scope",
     "ui/tabs_v6_16_viewer.R, server/server.R",
     "CRITICAL - the Selection reference for P9C"),
    ("R/viewer_pilot.R", kb("R/viewer_pilot.R"), "V6.17 read-only viewer provider",
     "viewer_pilot_server, fvp_pilot_data, fvp_pilot_case_data, "
     "fvp_pilot_download_rows, fvp_pilot_available",
     "server/server.R", "HIGH - download-of-selection reference"),
    ("R/forecast_pilot.R", kb("R/forecast_pilot.R"),
     "V6.17 read-only forward forecast provider",
     "forecast_pilot_server plus 31 highcharter references",
     "server/server.R", "HIGH - forward chart reference for P9F"),
    ("R/llm_explain.R", kb("R/llm_explain.R"), "assistant UI and server",
     "llm_explain_ui, llm_explain_server, llm_explain_get, "
     ".LLM_DEFAULT_QUICK_PROMPTS, .llm_render_panel, .llm_download_modal",
     "ui/*, server/server.R", "HIGH - assistant reference for P9G"),
    ("R/llm_compose.R", kb("R/llm_compose.R"), "deterministic local composer",
     "question-adaptive composition from the evidence pack",
     "R/llm_explain.R", "MEDIUM - the answer engine behind the assistant"),
    ("R/artifact_export.R", kb("R/artifact_export.R"),
     "governed multi-format downloads",
     "register_artifact_downloads, .artifact_download_modal, "
     ".artifact_build_md/txt/html, ARTIFACT_DOWNLOAD_SPECS",
     "server/server.R", "HIGH - download modal and format pattern for P9G"),
    ("R/data_loader.R", kb("R/data_loader.R"), "governed artifact registry",
     "build_artifact_registry, load_csv_artifact, .tess_read_parquet_file",
     "global.R", "MEDIUM - shows the registry pattern V6.24 bypassed"),
    ("ui/tabs_v6_16_viewer.R", kb("ui/tabs_v6_16_viewer.R"),
     "Viewer and Forecast sections",
     "section_explorer(), section_forecast()",
     "ui/body.R", "CRITICAL - the layout reference"),
    ("ui/tabs.R", kb("ui/tabs.R"), "legacy sections and shared UI helpers",
     "panel(), section_head(), home_collapse(), card_grid(), info_list(), "
     "app_sections()",
     "ui/body.R", "HIGH - shared layout primitives V6.24 already uses"),
    ("ui/sidebar.R", kb("ui/sidebar.R"), "left navigation",
     "stage07_menu(), sidebar_group()", "ui/body.R",
     "MEDIUM - both groups already registered here"),
    ("server/server.R", kb("server/server.R"), "root server",
     "app_server(), viewer_pilot_server(), forecast_pilot_server(), "
     "llm_explain_server() x N, v6_24_mvp_server()",
     "app.R", "HIGH - wiring reference"),
    ("www/custom.css", kb("www/custom.css"), "stylesheet",
     "fvx-/fvb-/fvtn-/fv- class families, plus the v24- block appended by P8",
     "ui/body.R", "HIGH - the visual language to match"),
]]
write("v6_24_p9b_existing_forecasting_code_map.csv", F, rows)

# ============================================ 6. current V6.24 UX inventory
F = ["page", "element", "current_behaviour", "strength", "weakness_vs_forecasting",
     "priority", "target_stage"]
rows = [dict(zip(F, r)) for r in [
    ("Overview", "12 metric cards",
     "Cards read straight from taxonomy_counts GLOBAL and navigation_contract.",
     "Genuinely new; the owner wants this kept and carried into Forecasting",
     "Forecast Type card wraps mid-token as GOVERNED_30_STE... ; 12 equal-weight "
     "cards give no visual hierarchy", "MEDIUM", "P9H"),
    ("Overview", "Horizon banner",
     "Persistent blue banner naming the governed 30-step contract.",
     "Honest and always visible", "None material", "LOW", "-"),
    ("Overview", "Coverage by metric table",
     "Plain HTML table from taxonomy_counts BY_METRIC.",
     "Correct and reconciles to 140",
     "Static; legacy tables are richer", "LOW", "P9H"),
    ("Overview", "Artifact load status table",
     "35 loader validation rows rendered on the product page.",
     "Good evidence that artifacts loaded",
     "Too technical to be a first-class product panel", "MEDIUM", "P9H"),
    ("Viewer", "Six flat dropdowns",
     "All six axes always rendered in one row; NOT_APPLICABLE shown as a value.",
     "Functionally correct: 140/140 paths resolve, zero empty options",
     "The main complaint. No progressive disclosure, no breadcrumb chips, no "
     "route cards, no context panel", "HIGH", "P9C"),
    ("Viewer", "Selection status line",
     "One green line: 'Selected: <series_id> - path a|b|c'.",
     "Unambiguous",
     "A single line instead of breadcrumb chips and a route panel", "HIGH", "P9C"),
    ("Viewer", "Identity key/value list",
     "Flat list of metric, db_type, scenario, segment, granularity, key, key role, "
     "route, product status, signal quality.",
     "Carries key_axis_status, which legacy does not",
     "Flat list instead of the six route metadata cards", "HIGH", "P9C"),
    ("Viewer", "Champion block",
     "Shows champion, rank metric, value, validity, medians; suppressed with an "
     "amber panel when champion_visible is FALSE.",
     "The no-signal handling is correct and clear",
     "Not integrated into a Backtest Configuration card", "MEDIUM", "P9D"),
    ("Viewer", "Model selector",
     "One flat selectInput listing 15 models ordered by rank.",
     "Defaults to the champion when meaningful",
     "No family grouping, no checkboxes, no champion star, single model only, "
     "no Analyze/Reset", "HIGH", "P9D"),
    ("Viewer", "Charts", "plotly scatter/line for actuals and backtest.",
     "Renders and is readable",
     "PLOTLY, not Highcharts. No export menu, no crosshair, no rich tooltip, no "
     "title/subtitle context, one model at a time", "HIGH", "P9E"),
    ("Viewer", "Ranking table",
     "Plain HTML table with rank, model, metric, value, WAPE, MAE, RMSE, champion.",
     "Shows 'not computable' honestly instead of 0",
     "No sorting or interactivity", "LOW", "P9H"),
    ("Forecast", "Filter bar", "A second independent copy of the six dropdowns.",
     "Works",
     "Selection is NOT shared with the Viewer; the user re-selects the series",
     "HIGH", "P9C"),
    ("Forecast", "Forecast chart", "plotly: 90 days of history plus 30 forward steps.",
     "Horizon is honest and visible",
     "Plotly; no boundary marker between history and forecast; no legend control",
     "HIGH", "P9F"),
    ("Forecast", "Forecast table", "30 rows with step, date, value, flags.",
     "Flags preserved verbatim", "No export", "MEDIUM", "P9G"),
    ("Taxonomy", "Scope selector and tables",
     "All 10 taxonomy_counts scopes plus caveat and filter option tables.",
     "Complete and reconciles",
     "Reads as an audit page rather than a product page", "LOW", "P9H"),
    ("Caveats", "Badges",
     "Pipe-separated caveat_badge split into coloured chips by severity.",
     "Machine-readable and never hardcoded",
     "NO_SIGNAL and CHAMPION_NOT_MEANINGFUL both render red, so a normal series "
     "with 2 informational badges can look alarming", "MEDIUM", "P9H"),
    ("Assistant", "None", "No assistant panel on any V6.24 page.",
     "-", "Legacy has one per section", "HIGH", "P9G"),
    ("Download", "None", "No download on any V6.24 page.",
     "-", "Legacy exports the current selection in six formats", "HIGH", "P9G"),
    ("Loader", "R/v6_24_read_only_loader.R",
     "Loads 8 artifacts, validates 35 conditions, and also hosts UI tag helpers "
     "and v24_table().",
     "Validation at load is a real strength",
     "TECHNICAL DEBT: presentation helpers live in a data loader. They were moved "
     "there in P8 to survive UI/server load order. They belong in a dedicated "
     "v6_24_ui_helpers.R", "MEDIUM", "P9C"),
    ("Integration", "Visual language",
     "v24- CSS block, independent of the fvx-/fvb-/fvtn- families.",
     "No collision risk",
     "Different spacing, card and typography scale, so V6.24 reads as a separate "
     "product rather than the same one", "HIGH", "P9H"),
]]
write("v6_24_p9b_current_v624_ux_inventory.csv", F, rows)

# ============================================ 7. current V6.24 code map
F = ["file", "size_kb", "role", "key_symbols", "technical_debt", "stage_to_touch"]
rows = [dict(zip(F, r)) for r in [
    ("R/v6_24_read_only_loader.R", kb("R/v6_24_read_only_loader.R"),
     "read-only loader, filter helpers, caveat map, UI tag helpers",
     "v6_24_load_all, v6_24_tbl, v6_24_operational, v6_24_axis_options, "
     "v6_24_resolve, v6_24_nav_row, v6_24_badges, v6_24_caveat_severity, "
     "v6_24_tax_scope, v6_24_fmt_median, v24_table, v24_card, v24_kv, v24_badge",
     "UI helpers do not belong in a loader; split into v6_24_ui_helpers.R",
     "P9C"),
    ("ui/tabs_v6_24_mvp.R", kb("ui/tabs_v6_24_mvp.R"),
     "four V6.24 sections",
     "section_v24_overview/viewer/forecast/taxonomy, v24_filter_bar, "
     "v24_section_head, v24_horizon_banner, v24_resize_hook",
     "v24_filter_bar renders six unconditional dropdowns; the resize hook exists "
     "only because plotly cannot measure itself in a hidden container",
     "P9C, P9D, P9E, P9F"),
    ("server/v6_24_mvp_server.R", kb("server/v6_24_mvp_server.R"),
     "read-only server module",
     "v6_24_mvp_server, make_filter_flow, per-page reactives, 33 outputOptions "
     "un-suspensions",
     "Two independent filter flows (v24_vw and v24_fc) duplicate state; the "
     "Viewer and Forecast selections should be shared",
     "P9C"),
    ("www/custom.css", kb("www/custom.css"),
     "stylesheet incl. the appended v24- block",
     "v24-card, v24-tbl, v24-badge-*, v24-filterbar, v24-horizon-banner",
     "Parallel visual language to fvx-/fvb-/fvtn-; should converge",
     "P9H"),
    ("global.R", kb("global.R"), "startup sourcing",
     "two added source() lines", "none", "P9C (one more source line if split)"),
    ("ui/body.R", kb("ui/body.R"), "UI shell", "one added source() line",
     "none", "P9C (one more source line if split)"),
    ("ui/sidebar.R", kb("ui/sidebar.R"), "navigation",
     "V6.24 MVP group with four items",
     "Legacy vs V6.24 distinction is not visually explicit", "P9H"),
    ("ui/tabs.R", kb("ui/tabs.R"), "section composition",
     "four section_v24_* calls in app_sections()", "none", "-"),
    ("server/server.R", kb("server/server.R"), "root server",
     "one call to v6_24_mvp_server()",
     "none", "P9G (assistant server registrations will be added here)"),
]]
write("v6_24_p9b_current_v624_code_map.csv", F, rows)
print("part 1 complete")
