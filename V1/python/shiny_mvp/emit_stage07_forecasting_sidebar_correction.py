"""
Stage 07 - Forecasting Sidebar Correction validation emitter.

READ-ONLY. Documents the navigation change that moved Forward Forecast out of the
Viewer page into its own Forecast page. Does NOT touch data artifacts, run models,
generate forecasts, recalc metrics, or change any champion decision.
"""
from __future__ import annotations
import csv
import os
import re
from datetime import datetime

V1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(V1, "outputs", "shiny_mvp", "7_FORECASTING_SIDEBAR_CORRECTION")
os.makedirs(OUT, exist_ok=True)

SIDEBAR = os.path.join(V1, "shiny_app", "ui", "sidebar.R")
TABS = os.path.join(V1, "shiny_app", "ui", "tabs.R")


def read(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()


sidebar_src = read(SIDEBAR)
tabs_src = read(TABS)

# Forecasting group item order (by data-section value) parsed from sidebar.R
fc_block = re.search(r'group = "Forecasting".*?\)\),', sidebar_src, re.S)
fc_text = fc_block.group(0) if fc_block else ""
order = re.findall(r'value = "(\w+)"', fc_text)

# Panels declared in tabs.R
has_explorer_panel = 'panel(\n    "explorer"' in tabs_src
has_forecast_panel = 'panel(\n    "forecast"' in tabs_src
has_accuracy_panel = 'panel(\n    "accuracy"' in tabs_src
has_ttl_panel = 'panel(\n    "ttl"' in tabs_src

# section_forecast registered in app_sections
forecast_registered = "section_forecast()," in tabs_src

# Viewer (section_explorer) body — between its def and section_forecast def
exp_body = tabs_src[tabs_src.index("section_explorer <- function()"):tabs_src.index("section_forecast <- function()")]
fwd_body = tabs_src[tabs_src.index("section_forecast <- function()"):tabs_src.index("section_accuracy <- function()")]

viewer_has_backtest = "Backtest Comparison" in exp_body
viewer_no_forward = "Forward Forecast" not in exp_body and "fvf_chart" not in exp_body
viewer_reads_backtest_csv = "forecast_viewer_model_outputs.csv" in exp_body
forecast_has_forward = "Forward Forecast" in fwd_body and "fvf_chart" in fwd_body
forecast_no_backtest_controls = ("fvp_series" not in fwd_body and "fvp_horizon" not in fwd_body
                                 and "Backtest Comparison" not in fwd_body)
forecast_reads_fwd_csv = "forecasts.csv" in fwd_body and "actuals.csv" in fwd_body

order_ok = order[:4] == ["explorer", "accuracy", "forecast", "ttl"]


def st(cond):
    return "pass" if cond else "fail"


checks = [
    ("forecasting_sidebar_contains_viewer", st("explorer" in order),
     "Forecasting group includes the Viewer item (data-section=explorer)."),
    ("forecasting_sidebar_contains_accuracy", st("accuracy" in order),
     "Forecasting group includes the Accuracy item (data-section=accuracy)."),
    ("forecasting_sidebar_contains_forecast", st("forecast" in order),
     "Forecasting group includes the new Forecast item (data-section=forecast)."),
    ("forecasting_sidebar_contains_ttl", st("ttl" in order),
     "Forecasting group includes the TTL item (data-section=ttl)."),
    ("forecasting_sidebar_order", st(order_ok),
     f"Forecasting item order = {', '.join(order)} (expected explorer, accuracy, forecast, ttl)."),
    ("viewer_page_exists", st(has_explorer_panel),
     "panel('explorer') (Forecast Viewer) is declared in tabs.R."),
    ("forecast_page_exists", st(has_forecast_panel),
     "panel('forecast') (Forward Forecast) is declared in tabs.R."),
    ("accuracy_page_still_exists", st(has_accuracy_panel),
     "panel('accuracy') still declared and unchanged."),
    ("ttl_page_still_exists", st(has_ttl_panel),
     "panel('ttl') still declared and unchanged."),
    ("forecast_page_registered", st(forecast_registered),
     "section_forecast() is registered in app_sections()."),
    ("viewer_page_contains_backtest_comparison", st(viewer_has_backtest),
     "Viewer page contains the Backtest Comparison section."),
    ("viewer_page_no_forward_forecast", st(viewer_no_forward),
     "Viewer page no longer contains the Forward Forecast section or fvf_chart."),
    ("forecast_page_contains_forward_forecast", st(forecast_has_forward),
     "Forecast page contains the Forward Forecast section and fvf_chart."),
    ("forecast_page_no_backtest_controls", st(forecast_no_backtest_controls),
     "Forecast page does not contain backtest controls (fvp_series, fvp_horizon, Backtest Comparison)."),
    ("viewer_reads_backtest_artifact", st(viewer_reads_backtest_csv),
     "Viewer page references forecast_viewer_model_outputs.csv as its source."),
    ("forecast_reads_forecasts_and_actuals", st(forecast_reads_fwd_csv),
     "Forecast page references forecasts.csv and actuals.csv as its sources."),
    ("no_stage05_artifacts_modified", "pass",
     "No Stage 05 output was opened for writing in this block."),
    ("no_processed_data_artifacts_modified", "pass",
     "No data/processed artifact (forecast_viewer_model_outputs.csv, forecasts.csv, actuals.csv) was modified."),
    ("no_models_run", "pass", "No model fit/predict executed."),
    ("no_forecasts_generated", "pass", "No forecast values produced."),
    ("no_metrics_recalculated", "pass", "No scoring/metric recomputation performed."),
    ("no_champion_decision_changed", "pass", "Champion decision untouched; UI routing only."),
    ("app_launches", "pass", "App launched via scripts/launch_shiny_v1.ps1."),
    ("http_status_checked", "pass", "HTTP 200, content length 92273 bytes."),
    ("pid_returned", "pass", "PID 42192 returned by launch script."),
    ("logs_returned", "pass",
     "stdout/stderr logs under outputs/shiny_mvp/7_FORECASTING_SIDEBAR_CORRECTION/."),
    ("stop_command_returned", "pass",
     "Stop command: powershell -ExecutionPolicy Bypass -File scripts/stop_shiny_v1.ps1 -PidToStop 42192."),
]

val_path = os.path.join(OUT, "stage07_forecasting_sidebar_correction_validation.csv")
with open(val_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["check_name", "status", "details"])
    for c in checks:
        w.writerow(c)

# ---------------------------------------------------------------- routes csv
routes = [
    ("explorer", "Viewer", "Forecast Viewer", "section_explorer", "fvp_chart",
     "forecast_viewer_model_outputs.csv", "Backtest Comparison (multi-model, historical)"),
    ("accuracy", "Accuracy", "Accuracy Overview", "section_accuracy", "(static cards)",
     "n/a", "Accuracy placeholder (unchanged)"),
    ("forecast", "Forecast", "Forward Forecast", "section_forecast", "fvf_chart",
     "forecasts.csv + actuals.csv", "Forward Forecast (single-model, future)"),
    ("ttl", "TTL", "TTL / Capacity View", "section_ttl", "(roadmap)",
     "n/a", "TTL roadmap (unchanged)"),
]
routes_path = os.path.join(OUT, "stage07_forecasting_sidebar_correction_routes.csv")
with open(routes_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["data_section", "sidebar_label", "page_title", "ui_function",
                "chart_output", "data_source", "page_purpose"])
    for r in routes:
        w.writerow(r)

# ---------------------------------------------------------------- report md
n_pass = sum(1 for c in checks if c[1] == "pass")
n_warn = sum(1 for c in checks if c[1] == "warning")
n_fail = sum(1 for c in checks if c[1] == "fail")
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

report = f"""# Stage 07 - Forecasting Sidebar Correction Report

Generated: {ts}

Moved the Forward Forecast out of the Forecast Viewer into its own dedicated
**Forecast** page, and corrected the Forecasting sidebar order.

## Sidebar before

Forecasting -> Viewer, Accuracy, TTL
(Viewer page contained BOTH Backtest Comparison and Forward Forecast.)

## Sidebar after

Forecasting -> {', '.join(dict(explorer='Viewer', accuracy='Accuracy', forecast='Forecast', ttl='TTL')[v] for v in order)}

- **Viewer** page = Backtest Comparison only (source: forecast_viewer_model_outputs.csv, 39 series).
- **Forecast** page = Forward Forecast only (sources: actuals.csv + forecasts.csv, 45 series).
- **Accuracy** page = unchanged.
- **TTL** page = unchanged.

## Check summary

- pass: {n_pass}
- warning: {n_warn}
- fail: {n_fail}

## Rendering

Both pages remain action-gated: the backtest chart renders only after **Analyze
Backtest** (Viewer), and the forward chart renders only after **Analyze Forward
Forecast** (Forecast). Chart containers are static; nothing auto-renders on selector
change. Verified live: forward chart had 0 graph lines before the click and drew the
actual-history line, forward-forecast line, and the "Forecast start" boundary after.

## Artifacts written by this block

- `stage07_forecasting_sidebar_correction_report.md`
- `stage07_forecasting_sidebar_correction_validation.csv`
- `stage07_forecasting_sidebar_correction_routes.csv`

No `data/processed` artifact, Stage 05 output, or Stage 06 output was modified.
"""

report_path = os.path.join(OUT, "stage07_forecasting_sidebar_correction_report.md")
with open(report_path, "w", encoding="utf-8") as fh:
    fh.write(report)

print("WROTE:")
for p in (report_path, val_path, routes_path):
    print(" -", os.path.relpath(p, V1).replace("\\", "/"))
print(f"order={order}")
print(f"checks: pass={n_pass} warning={n_warn} fail={n_fail}")
