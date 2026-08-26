"""V6.24-P9B part B - parity map, Highcharts, assistant/download, plan, risks."""
from __future__ import annotations

import csv
from pathlib import Path

OUT = Path(__file__).resolve().parent


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


NAV = "navigation_contract"
TAX = "taxonomy_counts"
BT = "model_backtests_15_models"
ACT = "actuals_normalized"
FO = "forecast_outputs"
RK = "model_rankings"
AC = "accuracy_metrics"
SQ = "series_signal_quality"

# ============================================ 9. parity map (27 elements)
F = ["element_id", "existing_forecasting_element", "current_forecasting_behavior",
     "current_forecasting_files", "v624_current_behavior", "v624_current_files",
     "parity_gap", "recommended_v624_behavior", "v624_governed_artifact_source",
     "implementation_stage", "risk_level", "validation_needed", "notes"]
P = [
 ("E01", "Sidebar navigation",
  "Forecasting group with Viewer / Accuracy / Forecast / TTL; active state via "
  "data-section and custom.js.",
  "ui/sidebar.R",
  "Separate 'V6.24 MVP' group with Overview / Viewer / Forecast / Taxonomy.",
  "ui/sidebar.R",
  "None functionally. Visually there is no cue telling the user which group is "
  "legacy and which is the new one.",
  "Keep both groups. Add a small 'legacy' or 'new' qualifier so coexistence is "
  "explicit rather than confusing.",
  "n/a", "P9H", "LOW",
  "Both groups load; no duplicate data-section values.",
  "Rule 1 and 2: Forecasting is not removed."),
 ("E02", "Overview / landing summary",
  "No dedicated overview. The Viewer opens straight into Selection.",
  "ui/tabs_v6_16_viewer.R",
  "Twelve coverage cards, horizon banner, two tables, aggregation policy and a "
  "loader validation table.",
  "ui/tabs_v6_24_mvp.R, server/v6_24_mvp_server.R",
  "V6.24 is AHEAD here. The owner explicitly wants this kept.",
  "Keep. Rebalance the cards into a hierarchy, fix the token that wraps as "
  "GOVERNED_30_STE..., and move the loader table behind a technical toggle.",
  f"{TAX} GLOBAL and BY_METRIC, {NAV}",
  "P9H", "LOW",
  "Cards still reconcile to 140/125/53/87/15/1 after restyling.",
  "The one area where V6.24 leads; do not regress it."),
 ("E03", "Selection card",
  "Card A with kicker, title, scope pill, lead paragraph, then a two-column "
  "navigator: left rail of fields, right route panel.",
  "ui/tabs_v6_16_viewer.R, R/taxonomy_navigation.R",
  "A single 'Select a series' bar with six dropdowns in one row and a status line.",
  "ui/tabs_v6_24_mvp.R v24_filter_bar()",
  "The primary owner complaint. No card structure, no rail/route split, no "
  "scope pill, no lead text.",
  "Rebuild as a two-column navigator matching Card A: rail on the left, route "
  "panel on the right, scope pill showing 140 operational series.",
  f"{NAV}, {TAX}",
  "P9C", "MEDIUM",
  "140/140 paths still resolve to exactly one series; zero empty options.",
  "Emulate the pattern; do not bind to the V6.18 schema."),
 ("E04", "Progressive filter disclosure",
  "Axes resolved per branch by taxonomy_route_context(); an axis with no "
  "remaining choices is not rendered at all.",
  "R/taxonomy_navigation.R",
  "All six axes always rendered; inapplicable ones show the literal value "
  "NOT_APPLICABLE.",
  "server/v6_24_mvp_server.R make_filter_flow()",
  "Six always-visible controls versus only the ones that apply.",
  "Render an axis only when it has more than one real value for the current "
  "branch. When it resolves to a single conditional token, collapse it to a "
  "read-only context chip instead of a dropdown.",
  NAV,
  "P9C", "MEDIUM",
  "No path can be built that yields zero series; collapsing must never hide a "
  "real choice.",
  "V6.24 already knows which axes are conditional: db_type is NOT_APPLICABLE "
  "for IOPS and UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE for CPU."),
 ("E05", "Breadcrumb / route cards",
  "Chips for the path being built plus OPERATIONAL badge and a six-cell route "
  "metadata grid.",
  "R/taxonomy_navigation.R",
  "One green sentence: 'Selected: <series_id> - path a|b|c'.",
  "server/v6_24_mvp_server.R output$*_status",
  "No chips, no badge, no cards.",
  "Breadcrumb chips from the six filter levels; a status badge from "
  "product_status; a route card grid showing route_path, route_display_label, "
  "granularity, key role, signal quality and champion validity.",
  NAV,
  "P9C", "LOW",
  "Breadcrumb reflects the live selection and clears correctly.",
  "All fields already exist in navigation_contract; nothing new is needed."),
 ("E06", "Dynamic axis labels",
  "The entity axis is labelled Forest, Region or Forest+SKU depending on the "
  "branch.",
  "R/taxonomy_navigation.R",
  "The last axis is always labelled 'Key'.",
  "ui/tabs_v6_24_mvp.R V6_24_FILTER_LABELS",
  "A user selecting a Forest sees a control called Key.",
  "Label the last axis from key_axis_status: ROUTING_VALUE_REGION -> Region, "
  "IDENTIFIER_VALUE_FOREST -> Forest, COMPOSITE_TOKEN_FOREST_SKU -> Forest SKU.",
  f"{NAV}.key_axis_status",
  "P9C", "LOW",
  "Label changes with granularity; Key is never the first axis.",
  "P7 already emits the field; P8 simply does not read it."),
 ("E07", "Route status card",
  "OPERATIONAL badge with 'Prepared route and entity are available'.",
  "R/taxonomy_navigation.R",
  "product_status appears as one row in a flat key/value list.",
  "server/v6_24_mvp_server.R output$v24_vw_identity",
  "No visual status badge.",
  "Green badge for AVAILABLE, amber for AVAILABLE_WITH_CAVEAT, driven by "
  "product_status.",
  f"{NAV}.product_status",
  "P9C", "LOW",
  "Badge colour follows the field, never a hardcoded series list.",
  ""),
 ("E08", "Forecast-only / unavailable messaging",
  "Teal callout explaining that N prepared cases have forecasts but no actuals "
  "and no backtests, so nothing was fabricated.",
  "ui/tabs_v6_16_viewer.R",
  "No equivalent, because every V6.24 series has actuals, backtests and "
  "forecasts.",
  "-",
  "No gap in substance; the V6.24 cohort has no forecast-only population.",
  "Do not invent a forecast-only callout. Reuse the same calm tone for the "
  "no-signal explanation instead.",
  SQ,
  "P9C", "LOW",
  "140/140 are viewer and forecast visible, so the callout would be empty.",
  "Adding it would be inventing a state the data does not have."),
 ("E09", "Backtest configuration card",
  "Card B with kicker, title, '15 verified models' pill, availability banner and "
  "grouped controls.",
  "ui/tabs_v6_16_viewer.R",
  "A bare model dropdown above the chart.",
  "ui/tabs_v6_24_mvp.R",
  "No card, no pill, no availability banner, no grouped controls.",
  "Rebuild Card B with the same structure, driven by V6.24 readiness fields.",
  f"{BT}, {RK}, {NAV}",
  "P9D", "MEDIUM",
  "Configuration filters existing rows only; no accuracy is recomputed.",
  ""),
 ("E10", "Horizon selector",
  "radioButtons 5/10/15/20/25/30 plus struck-through disabled chips for 35/45 "
  "with the note 'Prepared artifact covers 1-30 day horizons.'",
  "ui/tabs_v6_16_viewer.R, R/helpers.R",
  "None. The chart plots every backtest row regardless of horizon.",
  "-",
  "No horizon control at all.",
  "Identical control. Filter model_backtests_15_models on horizon_steps.",
  f"{BT}.horizon_steps (verified present, values 1..30)",
  "P9D", "LOW",
  "Selecting 5 days must return only horizon_steps == 5 rows.",
  "Directly feasible: the column exists with the same semantics."),
 ("E11", "Model family grouping",
  "Four checkbox columns: Growth Baseline, Statistical, Machine Learning, Deep "
  "Learning, ordered by FVP_FAMILY_ORDER.",
  "R/helpers.R, server/server.R",
  "One flat dropdown of 15 models ordered by rank.",
  "server/v6_24_mvp_server.R output$v24_vw_model_sel",
  "No families, no multi-select.",
  "Four family checkbox groups. The V6.24 artifact only carries three coarse "
  "families (Baseline 7 / Challenger 5 / Neural 3), so the four-family display "
  "split must come from the legacy artifact's own model_family classification "
  "for the same 15 model names, or from an explicit documented map.",
  f"{AC}.model_family plus the legacy 4-family classification",
  "P9D", "MEDIUM",
  "All 15 models appear exactly once across the four groups.",
  "REAL MISMATCH FOUND: 3 families in V6.24 vs 4 in the legacy display. The "
  "legacy artifact already classifies the identical 15 names, so no invention "
  "is required."),
 ("E12", "Champion star",
  "fvp_model_label() appends ' \u2605 champion' when is_selected_champion is TRUE.",
  "R/helpers.R",
  "Champion shown in a separate block; suppressed when champion_visible is FALSE.",
  "server/v6_24_mvp_server.R output$v24_vw_champion",
  "No star on the model control itself.",
  "Star on the checkbox label, gated on champion_visible so no-signal series "
  "show no star anywhere.",
  f"{NAV}.champion_visible, {NAV}.champion_model_name, {RK}.is_series_champion",
  "P9D", "MEDIUM",
  "Zero stars rendered for the 15 no-signal series.",
  "Legacy has no champion_visible concept; V6.24 must not inherit an "
  "unconditional star."),
 ("E13", "Analyze Backtest button",
  "The chart is an eventReactive on the click; controls do not trigger a redraw.",
  "ui/tabs_v6_16_viewer.R, server/server.R",
  "Every dropdown change re-renders immediately.",
  "server/v6_24_mvp_server.R",
  "No explicit commit step.",
  "Add Analyze Backtest. The chart renders on click only.",
  "n/a",
  "P9D", "LOW",
  "Changing a control does not redraw until Analyze is pressed.",
  "Matters more once several models can be selected at once."),
 ("E14", "Reset Selection button",
  "Restores default models and horizon.",
  "ui/tabs_v6_16_viewer.R, R/helpers.R fvp_default_models()",
  "None.",
  "-", "No reset.",
  "Add Reset. Default = champion when visible, plus ETS Explicit and a few "
  "comparators, at horizon 5.",
  f"{NAV}.champion_model_name",
  "P9D", "LOW",
  "Reset returns to the documented default set.",
  "For no-signal series the default must not be the suppressed champion."),
 ("E15", "Backtest results chart",
  "fvp_chart(): Highcharts line chart, Actual in reserved blue plus one line per "
  "selected model, title, contextual subtitle, datetime axis, crosshairs.",
  "R/helpers.R",
  "plotly scatter with actual and one model.",
  "server/v6_24_mvp_server.R output$v24_vw_backtest",
  "Wrong library, single model, no title or subtitle context, no crosshair.",
  "Port fvp_chart() to V6.24 accessors. Keep title, subtitle, palette, tooltip "
  "and axis configuration identical.",
  f"{ACT} for the actual line, {BT} for model lines",
  "P9E", "MEDIUM",
  "Chart shows only artifact rows; nothing is generated in Shiny.",
  "THE central migration. Only the two data accessors change."),
 ("E16", "Highcharts legend / export menu",
  "hc_legend(enabled = TRUE) gives click-to-toggle; hc_exporting(enabled = TRUE) "
  "gives the native export menu.",
  "R/helpers.R",
  "Plotly legend; no export menu.",
  "server/v6_24_mvp_server.R",
  "No governed export path from the chart.",
  "Enable both, exactly as fvp_chart does.",
  "n/a",
  "P9E", "LOW",
  "Legend toggles series; export menu is present.",
  "Free once the chart is Highcharts."),
 ("E17", "Download analysis",
  "uiOutput('fvp_download_ui') under the chart, backed by row-level export of "
  "the current selection; artifact_export.R provides a six-format modal.",
  "R/viewer_pilot.R, R/artifact_export.R",
  "None.",
  "-", "No download anywhere in V6.24.",
  "Download the visible selection: actuals, backtests, forecast rows, ranking "
  "and the contract row. CSV first, reusing the modal pattern.",
  f"filtered rows of {ACT}, {BT}, {FO}, {RK}, {NAV}",
  "P9G", "MEDIUM",
  "The downloaded rows match the visible selection exactly.",
  "artifact_export.R exports whole small artifacts; the filtered-selection "
  "pattern is fvp_pilot_download_rows()."),
 ("E18", "Forecast chart",
  "fvf_chart(): Highcharts with actual history, forward forecast and a boundary "
  "marker.",
  "R/helpers.R, R/forecast_pilot.R",
  "plotly: 90 days of history plus 30 forward points.",
  "server/v6_24_mvp_server.R output$v24_fc_chart",
  "Wrong library, no boundary marker.",
  "Port fvf_chart() to forecast_outputs; keep the boundary marker at "
  "train_end_date.",
  f"{ACT} for history, {FO} for the forward line",
  "P9F", "MEDIUM",
  "Exactly 30 forward points; the boundary sits at train_end_date.",
  ""),
 ("E19", "Forecast model selector",
  "Model select plus history control, committed by Analyze.",
  "ui/tabs_v6_16_viewer.R",
  "Flat selectInput over the models present for the series.",
  "server/v6_24_mvp_server.R output$v24_fc_model_sel",
  "No family grouping, no Analyze.",
  "Same grouped control as the Viewer, defaulting to the champion when visible "
  "and to ETS Explicit otherwise.",
  f"{FO}.model_name, {NAV}.champion_visible",
  "P9F", "LOW",
  "All 15 governed models selectable; no legacy names appear.",
  ""),
 ("E20", "Forecast horizon label",
  "Horizon is a control, and the artifact covers 1-30 days.",
  "R/helpers.R",
  "Persistent banner naming GOVERNED_30_STEP_DAILY_FORECAST on all four pages.",
  "ui/tabs_v6_24_mvp.R v24_horizon_banner()",
  "V6.24 is AHEAD. The forward horizon is fixed at 30 and is stated plainly.",
  "Keep the banner. Do not turn the forward horizon into a control: 30 steps is "
  "the proven model capability, not a preference.",
  f"{FO}.forecast_type, {FO}.forecast_step",
  "P9F", "LOW",
  "No page may render '4-year' or '1,440'.",
  "Backtest horizon (1-30) and forward horizon (fixed 30) are different things "
  "and must not be conflated in the UI."),
 ("E21", "Caveat badges",
  "Legacy shows almost no caveats; risk_status exists but high-risk badges are "
  "deliberately not displayed in the Viewer.",
  "R/helpers.R fvp_model_label()",
  "Eleven caveat codes rendered as coloured chips by severity.",
  "server/v6_24_mvp_server.R, R/v6_24_read_only_loader.R",
  "V6.24 is far more transparent, but severity colouring makes ordinary series "
  "look alarming.",
  "Keep every caveat. Re-grade the palette: NO_SIGNAL and "
  "CHAMPION_NOT_MEANINGFUL as informative amber, negative/extreme as neutral "
  "technical notes, and hide STALE_MANIFEST_FLAG_IGNORED from the product view.",
  f"{NAV}.caveat_badge",
  "P9H", "LOW",
  "No caveat is dropped; only the visual weight changes.",
  "87 of 140 series carry at least one badge, so tone matters."),
 ("E22", "No-signal handling",
  "No equivalent concept.",
  "-",
  "Series stays selectable, champion suppressed with an explicit message.",
  "server/v6_24_mvp_server.R output$v24_vw_champion",
  "V6.24 is AHEAD and this is correct behaviour.",
  "Preserve exactly. Never hide the series and never restore the champion.",
  f"{SQ}.signal_quality_status, {NAV}.champion_visible",
  "P9C", "HIGH",
  "Zero no-signal series may show a champion recommendation.",
  "Regression here would undo P6C and P7. Guard it in every stage."),
 ("E23", "Low-confidence handling",
  "No equivalent concept.",
  "-",
  "Badge plus a zero-tail explanation, derived from the flag.",
  "server/v6_24_mvp_server.R",
  "V6.24 is AHEAD.",
  "Preserve, and surface it on the backtest card since it is a backtest-window "
  "property.",
  f"{NAV}.low_confidence_backtest_window_flag",
  "P9D", "MEDIUM",
  "Derived from the field; GBRP267 must never be named in code.",
  ""),
 ("E24", "Accuracy / ranking summary",
  "Dedicated Accuracy page with heatmap and table.",
  "R/helpers.R acc_*",
  "Ranking table inside the Viewer; no accuracy page.",
  "server/v6_24_mvp_server.R output$v24_vw_ranking",
  "No V6.24 accuracy page.",
  "Out of scope for P9C-P9G. Consider a V6.24 accuracy page after P9H.",
  f"{AC}, {RK}",
  "POST-P9H", "LOW",
  "n/a",
  "Deliberately deferred to avoid widening the migration."),
 ("E25", "Taxonomy / availability page",
  "No equivalent.",
  "-",
  "Ten count scopes, caveat counts and the filter option contract.",
  "ui/tabs_v6_24_mvp.R section_v24_taxonomy()",
  "V6.24 is AHEAD but the page reads as an audit.",
  "Keep. Split product-facing counts from technical evidence.",
  TAX,
  "P9H", "LOW",
  "Counts still reconcile to 140.",
  ""),
 ("E26", "LLM Assistant",
  "llm_explain_ui/server per section; four quick prompts; local mock over a "
  "page-keyed evidence pack.",
  "R/llm_explain.R, R/llm_compose.R",
  "Absent.",
  "-", "No assistant on any V6.24 page.",
  "Mount the same panel on the V6.24 Viewer and Forecast. The engine is "
  "page-keyed, so V6.24 needs its own evidence entries, ideally selection-aware.",
  "selected row of NAV plus RK, AC, FO summaries",
  "P9G", "MEDIUM",
  "The assistant must compute nothing and must not invent evidence.",
  "KEY CONSTRAINT: llm_explain_get(page_id) is static per page, not per "
  "selection. Making it selection-aware is a real design decision for P9G."),
 ("E27", "Governance / read-only validation",
  "Read-only by construction; the loader registry never writes.",
  "R/data_loader.R",
  "35 load-time validations, source scan proving no writes, sha256 immutability "
  "check.",
  "R/v6_24_read_only_loader.R, P8 reports",
  "V6.24 is AHEAD.",
  "Keep. Re-run the immutability check at the end of every P9x stage.",
  "all eight governed artifacts",
  "every stage", "HIGH",
  "Artifacts byte-identical before and after each stage.",
  "Rule 8 is non-negotiable."),
]
write("v6_24_p9b_forecasting_to_v624_parity_map.csv", F,
      [dict(zip(F, r)) for r in P])

# ============================================ 11. Highcharts migration study
F = ["aspect", "existing_implementation", "existing_location", "v624_current",
     "v624_target", "reuse_mode", "v624_artifact", "risk", "notes"]
rows = [dict(zip(F, r)) for r in [
    ("Library declaration", "library(highcharter) with the comment 'interactive "
     "forecast charting (Forecast Viewer)'", "R/libraries.R line 11",
     "plotly used in four outputs", "highcharter for all final charts",
     "REUSE", "n/a", "NONE",
     "No new dependency is needed. P8 introduced plotly against an established "
     "convention."),
    ("Chart constructor", "highcharter::highchart() piped through hc_chart, "
     "hc_title, hc_subtitle, hc_xAxis, hc_yAxis, hc_legend, hc_tooltip, "
     "hc_exporting, hc_credits, hc_plotOptions",
     "R/helpers.R fvp_chart() lines 650-670",
     "plotly::plot_ly()", "identical hc_ pipeline",
     "REUSE", "n/a", "LOW", "Copy the pipeline verbatim."),
    ("Chart type and interaction",
     "type='line', zoomType='xy', panning enabled with panKey='shift'",
     "R/helpers.R", "plotly defaults", "same",
     "REUSE", "n/a", "LOW", ""),
    ("Title", "'Backtest Comparison', 15px 600 weight, colour #102a43",
     "R/helpers.R", "none", "same", "REUSE", "n/a", "NONE", ""),
    ("Subtitle", "'{series}  -  horizon {N} days  -  {M} models  -  {min} -> {max}'",
     "R/helpers.R lines 644-648", "none",
     "same, with series_id and the selected horizon_steps",
     "ADAPT", f"{NAV}, {BT}", "LOW",
     "Gives the chart its context; currently missing entirely."),
    ("Axes", "x datetime with crosshair; y titled 'Value' with crosshair",
     "R/helpers.R", "plotly axes without crosshair", "same",
     "REUSE", "n/a", "NONE", ""),
    ("Legend", "hc_legend(enabled = TRUE); Highcharts gives click-to-toggle free",
     "R/helpers.R", "plotly legend", "same",
     "REUSE", "n/a", "NONE",
     "Directly satisfies the owner's 'poder quitar series'."),
    ("Export menu", "hc_exporting(enabled = TRUE)", "R/helpers.R line 667",
     "none", "same", "REUSE", "n/a", "NONE",
     "One line restores the export capability."),
    ("Tooltip", "shared=FALSE, xDateFormat='%Y-%m-%d', valueDecimals=2, plus a "
     "per-series pointFormat carrying model, date, value, horizon, family, risk",
     "R/helpers.R lines 665-666 and 706-714",
     "plotly default hover",
     "same, with family from accuracy_metrics and caveat context",
     "ADAPT", f"{AC}.model_family, {NAV}.caveat_badge", "LOW",
     "Risk status has no V6.24 equivalent; use caveat context instead of "
     "inventing a risk field."),
    ("Actual series", "Reserved blue #10477e, lineWidth 3, circle markers r=3, "
     "custom tooltip",
     "R/helpers.R lines 673-685",
     "plotly line", "same",
     "ADAPT", ACT, "LOW",
     "fvp_actual_series() maps to actuals_normalized (series_date, actual_value)."),
    ("Model series", "One line per selected model, family-ordered for stable "
     "colours, name from fvp_model_label() including the champion star",
     "R/helpers.R lines 687-715",
     "one model at a time", "same, multi-model",
     "ADAPT", BT, "MEDIUM",
     "fvp_forecast_series() maps to model_backtests_15_models filtered on "
     "series_id, model_name and horizon_steps."),
    ("Palette", ".fvp_palette: 13 fixed colours, actual reserved blue",
     "R/helpers.R lines 613-617", "plotly default cycle", "reuse verbatim",
     "REUSE", "n/a", "NONE",
     "13 colours for 15 models means two repeats if all are selected; the "
     "default selection is smaller."),
    ("Data shape", "data.frame(x = datetime_to_timestamp(date), y = round(value,3)) "
     "then list_parse2()",
     "R/helpers.R", "plotly takes the frame directly", "same",
     "REUSE", "n/a", "LOW", "Straightforward transformation."),
    ("Empty state", "fvp_empty_chart(): a calm titled highchart with hidden axes, "
     "used before Analyze is pressed",
     "R/helpers.R lines 599-610", "plotly_empty()", "same",
     "REUSE", "n/a", "NONE", ""),
    ("Update trigger", "eventReactive on the Analyze click",
     "server/server.R", "reactive on every control change",
     "eventReactive on Analyze", "ADAPT", "n/a", "LOW", ""),
    ("Forward chart", "fvf_chart() with history, forward series and a boundary "
     "marker at the last actual",
     "R/helpers.R lines 924-1034", "plotly with 90 days of history",
     "port with a boundary at train_end_date",
     "ADAPT", f"{ACT}, {FO}", "MEDIUM", "Target for P9F."),
    ("Hidden-container behaviour",
     "outputOptions(suspendWhenHidden = FALSE) already used for CSS-toggled "
     "outputs",
     "R/taxonomy_navigation.R line 532",
     "33 un-suspensions added in P8 plus a plotly resize hook",
     "keep the un-suspensions; the resize hook becomes unnecessary",
     "REUSE", "n/a", "LOW",
     "Highcharts reflows on container change more reliably than plotly, so the "
     "resize hook can likely be dropped in P9E. Verify before removing."),
    ("Remaining Plotly", "n/a", "n/a",
     "Four outputs: v24_vw_actuals, v24_vw_backtest, v24_fc_chart, plus "
     "plotly::plotlyOutput in the UI",
     "zero plotly in final charts",
     "REPLACE", "n/a", "MEDIUM",
     "P9E removes the two Viewer charts; P9F removes the Forecast chart. "
     "Verify with a source scan that no plotly call remains."),
]]
write("v6_24_p9b_highcharts_migration_study.csv", F, rows)

# ============================================ 13. assistant reuse
F = ["aspect", "existing_implementation", "location", "reusable", "v624_target",
     "constraint", "stage"]
rows = [dict(zip(F, r)) for r in [
    ("UI function", "llm_explain_ui(id, page_title, button_label, panel_title, "
     "panel_sub, quick_prompts)", "R/llm_explain.R line 200", "YES, as-is",
     "Mount on the V6.24 Viewer and Forecast sections",
     "Fully parameterised; no change needed", "P9G"),
    ("Server function", "llm_explain_server(id, page_id, quick_prompts)",
     "R/llm_explain.R line 745", "YES, as-is",
     "Register llm_v24_viewer and llm_v24_forecast in app_server()",
     "One line each in server/server.R", "P9G"),
    ("Quick prompts", ".LLM_DEFAULT_QUICK_PROMPTS: Summarize the key takeaway / "
     "Explain what changed / Explain the main risk / What should I pay attention "
     "to?", "R/llm_explain.R line 167", "YES, as-is",
     "Use the defaults; they match the owner's screenshot exactly",
     "None", "P9G"),
    ("Evidence lookup", "llm_explain_get(page_id) reads a preloaded response "
     "keyed by page id", "R/llm_explain.R line 77", "PARTIAL",
     "V6.24 needs its own entries",
     "BLOCKING DESIGN POINT: the evidence pack is STATIC PER PAGE, not per "
     "selection. A V6.24 assistant that says nothing about the selected series "
     "would be worse than none.", "P9G"),
    ("Composer", "llm_compose builds a question-adaptive answer from the evidence "
     "pack; deterministic and local", "R/llm_compose.R", "YES, as-is",
     "Reuse unchanged",
     "Local mock only; adding a real model is out of scope", "P9G"),
    ("Thinking animation", "Four-step timed status then the rendered panel",
     "R/llm_explain.R", "YES, as-is", "Reuse", "None", "P9G"),
    ("Explanation download", "Modal offering MD/TXT/HTML and PDF/DOCX when pandoc "
     "is present", "R/llm_explain.R", "YES, as-is", "Reuse", "None", "P9G"),
    ("Disclosure", "'Local mock - governed evidence only - no model or champion "
     "changes.'", "R/llm_explain.R", "YES, as-is", "Reuse verbatim",
     "Must stay: it is an honesty statement, not decoration", "P9G"),
    ("V6.24 evidence content", "n/a", "n/a", "NEW",
     "series_id, route display label, the six axes, champion model and validity "
     "when visible, primary rank metric and value, median WAPE/MAE with "
     "computability status, signal_quality_status, caveat badges, forecast type "
     "and 30-step horizon, forecast window dates, negative and extreme counts, "
     "latest actual date and value",
     "Every item must be READ from an artifact; nothing computed and nothing "
     "invented", "P9G"),
]]
write("v6_24_p9b_assistant_reuse_study.csv", F, rows)

# ============================================ 14. download reuse
F = ["aspect", "existing_implementation", "location", "reusable", "v624_target",
     "format", "stage", "notes"]
rows = [dict(zip(F, r)) for r in [
    ("Whole-artifact download", "register_artifact_downloads() registers "
     "dl_<key>_{csv,md,txt,html,pdf,docx} per governed spec",
     "R/artifact_export.R line 288", "PATTERN",
     "Not the primary V6.24 need", "6 formats", "P9G",
     "Designed for tiny artifacts (<= 15 rows) with a preview cap."),
    ("Format modal", ".artifact_download_modal(spec, caps) with a button per "
     "available format", "R/artifact_export.R line 241", "YES, as-is",
     "Reuse for the V6.24 selection download", "n/a", "P9G",
     "Good UX to reuse rather than rebuild."),
    ("Capability detection", "MD/HTML/TXT always available; PDF/DOCX only when "
     "pandoc and LaTeX are present, otherwise clearly disabled",
     "R/llm_explain.R lines 83-88", "YES, as-is", "Reuse", "n/a", "P9G",
     "Nothing is installed at runtime."),
    ("Verbatim CSV", "file.copy of the canonical CSV, never a re-render",
     "R/artifact_export.R line 299", "PATTERN",
     "V6.24 exports a FILTERED subset, so a writer is needed instead of a copy",
     "CSV", "P9G",
     "The read-only guarantee is that rows are never altered, not that the file "
     "is copied."),
    ("Filtered-selection download", "fvp_pilot_download_rows(metric, scenario, "
     "granularity, series_key, ...) plus uiOutput('fvp_download_ui')",
     "R/viewer_pilot.R line 186", "PATTERN",
     "THE closest match for the V6.24 requirement", "CSV", "P9G",
     "This, not artifact_export, is the right reference for 'download analysis'."),
    ("V6.24 target: actuals", "n/a", "n/a", "NEW",
     "Observed history for the selected series", "CSV",
     "P9G", f"filtered {ACT}"),
    ("V6.24 target: backtests", "n/a", "n/a", "NEW",
     "Backtest rows for the selected series, models and horizon", "CSV",
     "P9G", f"filtered {BT}"),
    ("V6.24 target: forecasts", "n/a", "n/a", "NEW",
     "The 30 forecast rows for the selected series and model", "CSV",
     "P9G", f"filtered {FO}"),
    ("V6.24 target: rankings", "n/a", "n/a", "NEW",
     "The 15 ranking rows for the selected series", "CSV",
     "P9G", f"filtered {RK} joined to {AC}"),
    ("V6.24 target: contract row", "n/a", "n/a", "NEW",
     "The single navigation_contract row with its caveats", "CSV",
     "P9G", f"filtered {NAV}"),
    ("Filename convention", "Artifact key plus extension",
     "R/artifact_export.R", "ADAPT",
     "v6_24_<target>_<metric>_<key>_<model>_<yyyymmdd>.csv", "CSV", "P9G",
     "The owner asked for metric, route, model and date in the name."),
]]
write("v6_24_p9b_download_reuse_study.csv", F, rows)
print("part 2 complete")
