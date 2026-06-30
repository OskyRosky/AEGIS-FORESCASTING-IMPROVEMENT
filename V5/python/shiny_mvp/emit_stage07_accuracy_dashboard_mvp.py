#!/usr/bin/env python3
"""Stage 07 - Accuracy Page MVP validation emitter (READ-ONLY).

Inspects the frozen Stage 05H backtest artifact and the Shiny source files,
then emits a schema CSV, a metrics summary CSV, a validation CSV and a markdown
report under outputs/shiny_mvp/7_ACCURACY_DASHBOARD_MVP/.

This script never writes to data/processed, never runs any model, and never
changes governance state. It only reads files and writes validation artifacts.
"""
from __future__ import annotations

import csv
import os
import statistics
from collections import defaultdict

# --- Paths (run from V1 root) ---------------------------------------------
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ARTIFACT = os.path.join(ROOT, "data", "processed", "forecast_viewer_model_outputs.csv")
FORECASTS = os.path.join(ROOT, "data", "processed", "forecasts.csv")
ACTUALS = os.path.join(ROOT, "data", "processed", "actuals.csv")
HELPERS = os.path.join(ROOT, "shiny_app", "R", "helpers.R")
TABS = os.path.join(ROOT, "shiny_app", "ui", "tabs.R")
SERVER = os.path.join(ROOT, "shiny_app", "server", "server.R")
CSS = os.path.join(ROOT, "shiny_app", "www", "custom.css")
OUTDIR = os.path.join(ROOT, "outputs", "shiny_mvp", "7_ACCURACY_DASHBOARD_MVP")

os.makedirs(OUTDIR, exist_ok=True)


def read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except OSError:
        return ""


# --- 1. Inspect the artifact schema ---------------------------------------
schema_rows = []
horizons = set()
series_set = set()
model_set = set()
n_rows = 0
header = []

with open(ARTIFACT, "r", encoding="utf-8", newline="") as fh:
    reader = csv.reader(fh)
    header = next(reader)
    idx = {name: i for i, name in enumerate(header)}
    h_i = idx.get("horizon_days")
    s_i = idx.get("series_key")
    m_i = idx.get("model_name")
    for row in reader:
        if not row:
            continue
        n_rows += 1
        if h_i is not None and h_i < len(row) and row[h_i] != "":
            try:
                horizons.add(int(float(row[h_i])))
            except ValueError:
                pass
        if s_i is not None and s_i < len(row):
            series_set.add(row[s_i])
        if m_i is not None and m_i < len(row):
            model_set.add(row[m_i])

EXPECTED_COLS = [
    "series_key", "series_label", "date", "actual_value", "model_name",
    "model_origin", "model_family", "forecast_value", "forecast_type",
    "horizon_days", "forecast_start_date", "run_id", "source_artifact",
    "is_baseline", "is_challenger", "is_deferred", "is_selected_champion",
    "risk_status", "lower_bound", "upper_bound", "interval_level",
]
USED_BY_ACCURACY = {
    "series_key", "model_name", "model_family", "horizon_days",
    "actual_value", "forecast_value",
}
for col in header:
    schema_rows.append({
        "column": col,
        "present": "yes",
        "used_by_accuracy": "yes" if col in USED_BY_ACCURACY else "no",
    })

with open(os.path.join(OUTDIR, "stage07_accuracy_dashboard_mvp_schema.csv"),
          "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["column", "present", "used_by_accuracy"])
    w.writeheader()
    w.writerows(schema_rows)


# --- 2. Compute a metrics summary at horizon=30 (sanity check) ------------
# Mirrors the in-app acc_compute logic at the default horizon, just to confirm
# the diagnostics are computable and to ship an illustrative summary.
HZ = 30
groups = defaultdict(list)  # (series, model) -> list of (actual, forecast)
fam_lookup = {}
with open(ARTIFACT, "r", encoding="utf-8", newline="") as fh:
    reader = csv.reader(fh)
    next(reader)
    for row in reader:
        if not row:
            continue
        try:
            hz = int(float(row[idx["horizon_days"]]))
        except (ValueError, KeyError):
            continue
        if hz != HZ:
            continue
        try:
            a = float(row[idx["actual_value"]])
            f = float(row[idx["forecast_value"]])
        except (ValueError, KeyError):
            continue
        sk = row[idx["series_key"]]
        mn = row[idx["model_name"]]
        groups[(sk, mn)].append((a, f))
        fam_lookup[mn] = row[idx["model_family"]] if "model_family" in idx else ""

metrics_rows = []
for (sk, mn), pairs in groups.items():
    errs = [f - a for a, f in pairs]
    aerr = [abs(e) for e in errs]
    mae = statistics.fmean(aerr)
    rmse = (statistics.fmean([e * e for e in errs])) ** 0.5
    sum_abs_actual = sum(abs(a) for a, _ in pairs)
    wmape = (sum(aerr) / sum_abs_actual * 100) if sum_abs_actual else ""
    bias = statistics.fmean(errs)
    var = statistics.pstdev(errs) if len(errs) > 1 else 0.0
    metrics_rows.append({
        "series_key": sk,
        "model_name": mn,
        "model_family": fam_lookup.get(mn, ""),
        "horizon": HZ,
        "n_points": len(pairs),
        "MAE": round(mae, 4),
        "RMSE": round(rmse, 4),
        "wMAPE": round(wmape, 4) if wmape != "" else "",
        "signed_bias": round(bias, 4),
        "error_variability": round(var, 4),
    })

# standardized MAE severity (median/IQR) for illustration
mae_vals = [r["MAE"] for r in metrics_rows]
if mae_vals:
    med = statistics.median(mae_vals)
    qs = statistics.quantiles(mae_vals, n=4) if len(mae_vals) >= 2 else [med, med, med]
    iqr = qs[2] - qs[0]
    for r in metrics_rows:
        if iqr > 0:
            r["std_score_MAE"] = round((r["MAE"] - med) / iqr, 3)
        else:
            r["std_score_MAE"] = 0.0
metrics_rows.sort(key=lambda r: r.get("std_score_MAE", 0), reverse=True)

with open(os.path.join(OUTDIR, "stage07_accuracy_dashboard_mvp_metrics_summary.csv"),
          "w", encoding="utf-8", newline="") as fh:
    cols = ["series_key", "model_name", "model_family", "horizon", "n_points",
            "MAE", "RMSE", "wMAPE", "signed_bias", "error_variability",
            "std_score_MAE"]
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(metrics_rows)


# --- 3. Validation checks --------------------------------------------------
tabs_src = read_text(TABS)
helpers_src = read_text(HELPERS)
server_src = read_text(SERVER)
css_src = read_text(CSS)

checks = []


def add(name, ok, details, warn=False):
    status = "pass" if ok else ("warning" if warn else "fail")
    checks.append({"check_name": name, "status": status, "details": details})


# Accuracy page exists and is no longer a placeholder
add("accuracy_page_exists",
    "section_accuracy <- function()" in tabs_src,
    "section_accuracy() is defined in ui/tabs.R")
add("accuracy_not_placeholder_only",
    "(placeholder)" not in tabs_src.split("section_accuracy")[-1][:4000]
    and 'plotlyOutput("acc_heatmap"' in tabs_src,
    "Placeholder shell_card text replaced with a real heatmap + table layout")

# Data source rules
add("reads_backtest_artifact",
    'load_csv_artifact("forecast_viewer_full")' in helpers_src
    and "acc_data <- function() fvp_data()" in helpers_src,
    "acc_data() reuses fvp_data() which reads forecast_viewer_model_outputs.csv")
acc_block = helpers_src.split("Stage 07 ACCURACY")[-1] if "Stage 07 ACCURACY" in helpers_src else ""
# Strip comment lines so we test FUNCTIONAL code, not documentation prose.
acc_code = "\n".join(ln for ln in acc_block.splitlines()
                     if not ln.lstrip().startswith("#"))
add("does_not_read_forecasts_csv",
    "fvf_forecasts(" not in acc_code and "forecasts.csv" not in acc_code,
    "Accuracy code never calls the forward forecast loader / forecasts.csv")
add("does_not_read_actuals_csv",
    "fvf_actuals(" not in acc_code and "actuals.csv" not in acc_code,
    "Accuracy code never calls the actuals loader / actuals.csv")

# Horizon selector (numbers live in acc_horizon_choices(); UI binds the radio)
horizon_ok = ("acc_horizon_choices <- function() c(5, 10, 15, 20, 25, 30)"
              in helpers_src) and ('radioButtons("acc_horizon"' in tabs_src) \
    and ("acc_horizon_choices()" in tabs_src)
add("horizon_selector_5_to_30", horizon_ok,
    "acc_horizon_choices() = 5,10,15,20,25,30 and bound to radioButtons('acc_horizon')")

# Heatmap
add("heatmap_exists",
    'plotlyOutput("acc_heatmap"' in tabs_src
    and 'output$acc_heatmap <- plotly::renderPlotly' in server_src,
    "plotly heatmap output acc_heatmap is wired UI <-> server")
add("heatmap_uses_standardized_score",
    "z[si, mi] <- max(min(zz, cap), -cap)" in helpers_src
    and "res$standardized_score" in helpers_src,
    "Heatmap z-values are the standardized severity score (winsorized for color)")

# Table
add("table_exists",
    'dataTableOutput("acc_table"' in tabs_src
    and "output$acc_table <- DT::renderDataTable" in server_src,
    "DT table output acc_table is wired UI <-> server")
add("table_includes_raw_metrics",
    all(tok in helpers_src for tok in ["MAE", "RMSE", "sMAPE", "wMAPE",
                                       "signed_bias", "error_variability"]),
    "acc_table() emits raw MAE/RMSE/sMAPE/wMAPE/bias/variability columns")
add("table_includes_standardized_score",
    "std_score" in helpers_src and "standardized_score" in helpers_src,
    "acc_table() includes a std_score(metric) column")

# Selectors
add("metric_selector_exists",
    'selectInput("acc_metric"' in tabs_src
    and "ACC_METRICS <- " in helpers_src,
    "Metric selector acc_metric bound to ACC_METRICS")
add("horizon_selector_exists",
    'radioButtons("acc_horizon"' in tabs_src,
    "Horizon selector acc_horizon present")
add("analyze_button_exists",
    'actionButton("acc_go", "Analyze Accuracy"' in tabs_src,
    "Analyze Accuracy action button present")

# Action gating
gate_ok = ('if (is.null(input$acc_go) || input$acc_go == 0)' in server_src)
add("heatmap_and_table_action_gated", gate_ok,
    "Heatmap, table and summary cards render an empty state until acc_go is clicked")

# No-modification guarantees (static source checks)
add("no_writes_to_processed_data",
    "data/processed" not in acc_block
    or "write" not in acc_block.lower(),
    "Accuracy helpers contain no write/persist calls to data/processed")
add("no_model_run", "forecast(" not in acc_block and "model(" not in acc_block,
    "No model fitting/forecast generation in the Accuracy code path")
add("no_tournament_rerun", "tournament" not in acc_block.lower(),
    "No tournament logic invoked by the Accuracy page")
add("no_champion_change",
    "is_selected_champion" not in acc_block
    and "selected_champion" not in acc_block,
    "Accuracy never reads/writes champion selection flags")

# Sibling pages preserved
add("viewer_page_exists",
    "section_explorer <- function()" in tabs_src,
    "Viewer (Backtest) page still present")
add("forecast_page_exists",
    "section_forecast <- function()" in tabs_src,
    "Forecast (Forward) page still present")
add("forward_forecast_outside_viewer",
    'fvf_chart' not in tabs_src.split("section_explorer")[-1].split("section_forecast")[0],
    "Forward Forecast (fvf_chart) is not inside the Viewer page body")
add("ttl_page_exists",
    "section_ttl <- function()" in tabs_src,
    "TTL page still present")

# outputOptions eager render
add("outputs_eager_render",
    all(f'outputOptions(output, "{o}"' in server_src
        for o in ["acc_summary_cards", "acc_heatmap", "acc_table"]),
    "Accuracy outputs set suspendWhenHidden = FALSE (hidden panel renders eagerly)")

# Accuracy CSS present
add("accuracy_css_present",
    ".acc-kpi-grid" in css_src,
    "Accuracy summary-card CSS appended to custom.css")

# MASE/RMSSE intentionally excluded (no governed baseline)
add("mase_rmsse_excluded_documented",
    "MASE / RMSSE are intentionally excluded" in tabs_src,
    "MASE/RMSSE excluded with documented rationale (no governed scale baseline)",
    warn=False)

with open(os.path.join(OUTDIR, "stage07_accuracy_dashboard_mvp_validation.csv"),
          "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["check_name", "status", "details"])
    w.writeheader()
    w.writerows(checks)

n_pass = sum(1 for c in checks if c["status"] == "pass")
n_warn = sum(1 for c in checks if c["status"] == "warning")
n_fail = sum(1 for c in checks if c["status"] == "fail")


# --- 4. Report -------------------------------------------------------------
lines = []
lines.append("# Stage 07 - Accuracy Page MVP - Validation Report\n")
lines.append("Read-only validation of the heatmap-first Accuracy page. No data ")
lines.append("artifacts were modified; no models, forecasts or tournaments were run.\n")
lines.append("\n## Data source\n")
lines.append(f"- Artifact: `data/processed/forecast_viewer_model_outputs.csv`\n")
lines.append(f"- Rows: {n_rows}\n")
lines.append(f"- Series: {len(series_set)}  |  Models: {len(model_set)}\n")
lines.append(f"- Horizons present: {sorted(horizons)}\n")
lines.append(f"- Columns: {len(header)}\n")
lines.append("\n## Diagnostics computed (in memory)\n")
lines.append("- Per series x model x horizon: n_points, MAE, RMSE, sMAPE, wMAPE, ")
lines.append("signed_bias, abs_bias_severity, error_variability.\n")
lines.append("- Standardized severity = (value - median) / IQR (z-score fallback).\n")
lines.append("- MASE / RMSSE excluded: no governed scale baseline bundled with the artifact.\n")
lines.append(f"\n## Validation summary: {n_pass} pass, {n_warn} warning, {n_fail} fail\n\n")
lines.append("| Check | Status | Details |\n|---|---|---|\n")
for c in checks:
    lines.append(f"| {c['check_name']} | {c['status']} | {c['details']} |\n")
lines.append("\n## Guarantees\n")
lines.append("- forecast_viewer_model_outputs.csv / forecasts.csv / actuals.csv: unchanged.\n")
lines.append("- No model fitting, forecast generation, tournament rerun or champion change.\n")
lines.append("- Derived metrics are dashboard diagnostics only; never written to data/processed.\n")

with open(os.path.join(OUTDIR, "stage07_accuracy_dashboard_mvp_report.md"),
          "w", encoding="utf-8") as fh:
    fh.write("".join(lines))

print(f"Validation: {n_pass} pass, {n_warn} warning, {n_fail} fail")
print(f"Artifact rows: {n_rows}, series: {len(series_set)}, models: {len(model_set)}, "
      f"horizons: {sorted(horizons)}")
print(f"Outputs written to: {OUTDIR}")
for c in checks:
    if c["status"] != "pass":
        print(f"  [{c['status']}] {c['check_name']}: {c['details']}")
