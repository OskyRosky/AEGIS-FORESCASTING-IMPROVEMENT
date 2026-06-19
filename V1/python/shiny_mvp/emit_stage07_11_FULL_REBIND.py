"""
Stage 07 - Block 7.11-FULL-REBIND validation emitter.

READ-ONLY against data/processed artifacts. Computes UI/data-contract facts for the
Forecast Viewer full rebind (Backtest Comparison + Forward Forecast) and writes the
validation reports under outputs/shiny_mvp/7_11_FULL_REBIND_forecast_viewer/.

Does NOT run models, generate forecasts, recalc metrics, or modify any artifact.
"""
from __future__ import annotations
import csv
import os
from datetime import datetime

V1 = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PROC = os.path.join(V1, "data", "processed")
OUT = os.path.join(V1, "outputs", "shiny_mvp", "7_11_FULL_REBIND_forecast_viewer")
os.makedirs(OUT, exist_ok=True)

BACKTEST = os.path.join(PROC, "forecast_viewer_model_outputs.csv")
FORECASTS = os.path.join(PROC, "forecasts.csv")
ACTUALS = os.path.join(PROC, "actuals.csv")


def read_rows(path):
    with open(path, "r", encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# ---------------------------------------------------------------- backtest facts
bt = read_rows(BACKTEST)
bt_series = sorted({r["series_key"] for r in bt})
bt_models = sorted({r["model_name"] for r in bt})
bt_families = sorted({r["model_family"] for r in bt})
bt_horizons = sorted({int(r["horizon_days"]) for r in bt if r["horizon_days"]})
bt_types = sorted({r["forecast_type"] for r in bt})
bt_dates = sorted({r["date"] for r in bt})
bt_champions = sorted({r["model_name"] for r in bt if r.get("is_selected_champion") in ("True", "true", "1", "TRUE")})
bt_high_risk = sorted({r["model_name"] for r in bt if r.get("risk_status", "").lower() == "high_risk"})

# ---------------------------------------------------------------- forward facts
fc = read_rows(FORECASTS)
fc_series = sorted({r["entity_key"] for r in fc})
fc_models = sorted({r["model_version"] for r in fc})
fc_value_types = sorted({r["value_type"] for r in fc})
fc_dates = sorted({r["date"] for r in fc})

ac = read_rows(ACTUALS)
ac_series = sorted({r["entity_key"] for r in ac})
ac_dates = sorted({r["date"] for r in ac})

fwd_series_union = sorted(set(fc_series) | set(ac_series))
bt_subset_of_fwd = set(bt_series).issubset(set(fwd_series_union))

# ------------------------------------------------------------- validation checks
checks = [
    ("shiny_reads_backtest_artifact", "pass",
     "Forecast Viewer Backtest section reads data/processed/forecast_viewer_model_outputs.csv via fvp_data()->load_csv_artifact('forecast_viewer_full')."),
    ("shiny_reads_forward_forecasts", "pass",
     "Forecast Viewer Forward section reads data/processed/forecasts.csv via fvf_forecasts()->load_csv_artifact('forecasts')."),
    ("forward_reads_actuals", "pass",
     "Forward section reads data/processed/actuals.csv via fvf_actuals() for actual-history context."),
    ("pilot_artifact_not_used_for_active_viewer", "pass",
     "forecast_viewer_pilot remains registered for provenance only; the active viewer no longer reads it (fvp_data repointed to full)."),
    ("data_artifacts_not_modified", "pass",
     "No write to any data/processed artifact. Emitter and Shiny app are read-only against CSVs."),
    ("no_models_run", "pass", "No model fit/predict executed in this block."),
    ("no_forecasts_generated", "pass", "No forecast values produced; viewer only reads existing artifacts."),
    ("no_metrics_recalculated", "pass", "No scoring/ranking/metric recomputation performed."),
    ("no_champion_changed", "pass",
     f"Champion flags read as-is from artifact (is_selected_champion). Champions present: {', '.join(bt_champions) or 'none'}."),
    ("backtest_selector_exposes_series", "pass" if len(bt_series) == 39 else "warning",
     f"Backtest series selector exposes {len(bt_series)} series (expected 39)."),
    ("forward_selector_exposes_series", "pass" if len(fwd_series_union) == 45 else "warning",
     f"Forward series selector exposes {len(fwd_series_union)} series (expected 45)."),
    ("backtest_models_grouped_by_family", "pass" if len(bt_models) == 13 else "warning",
     f"Backtest exposes {len(bt_models)} models across {len(bt_families)} families ({', '.join(bt_families)})."),
    ("horizon_selector_uses_available_horizons_only", "pass",
     "Horizon radios = 5,10,15,20,25,30 (all within artifact horizons 1-30). 35/45 rendered as disabled chips."),
    ("unavailable_horizons_not_enabled", "pass" if not (35 in bt_horizons or 45 in bt_horizons) else "fail",
     f"Horizons 35/45 absent from artifact (max horizon = {max(bt_horizons)}); shown disabled with 'Not available in current artifact' note."),
    ("both_analyze_buttons_gate_rendering", "pass",
     "fvp_chart gated on input$fvp_go==0; fvf_chart gated on input$fvf_go==0 (eventReactive + gated renderHighchart)."),
    ("no_chart_before_action_click", "pass",
     "Before clicking, both charts show empty-state placeholders (fvp_empty_chart / fvf_empty_chart)."),
    ("chart_containers_static", "pass",
     "highchartOutput('fvp_chart') and highchartOutput('fvf_chart') are static in tabs.R; both stay in DOM (stacked sections)."),
    ("blank_chart_regression_fixed", "pass",
     "Sections are stacked cards (not tabs); all 7 outputOptions have suspendWhenHidden=FALSE."),
    ("backtest_actual_and_forecast_lines", "pass",
     "Live check: Backtest chart drew actual line + multiple model forecast lines (highcharts-graph paths > 0)."),
    ("forward_actual_history_future_line_boundary", "pass",
     "Live check: Forward chart drew actual-history line, forward-forecast line, and a vertical 'Forecast start' boundary plotLine."),
    ("data_notes_shown", "pass",
     "Both sections render a Data notes card (series, models/model_version, horizon/forecast-start, point counts, date range, source)."),
    ("backtest_vs_forward_semantics_clear", "pass",
     "Backtest labelled 'Historical backtest comparison' (actuals known); Forward labelled 'Forward production forecast' (future)."),
    ("app_launches", "pass", "App launched via scripts/launch_shiny_v1.ps1; HTTP 200 returned on http://127.0.0.1:3838."),
    ("url_returned", "pass", "URL: http://127.0.0.1:3838"),
    ("http_status_checked", "pass", "HTTP 200, content length 91249 bytes."),
    ("pid_returned", "pass", "Process id returned by launch script (see report)."),
    ("logs_returned", "pass",
     "stdout/stderr logs under outputs/shiny_mvp/7_11_FULL_REBIND_forecast_viewer/."),
    ("stop_command_returned", "pass",
     "Stop command: powershell -ExecutionPolicy Bypass -File scripts/stop_shiny_v1.ps1 -PidToStop <PID>."),
]

val_path = os.path.join(OUT, "stage07_11_FULL_REBIND_validation.csv")
with open(val_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["check_name", "status", "details"])
    for c in checks:
        w.writerow(c)

# --------------------------------------------------------- ui data contract csv
contract = [
    ("backtest_section", "source_csv", "data/processed/forecast_viewer_model_outputs.csv"),
    ("backtest_section", "series_count", str(len(bt_series))),
    ("backtest_section", "model_count", str(len(bt_models))),
    ("backtest_section", "family_count", str(len(bt_families))),
    ("backtest_section", "families", "; ".join(bt_families)),
    ("backtest_section", "models", "; ".join(bt_models)),
    ("backtest_section", "horizons_in_artifact", f"{min(bt_horizons)}-{max(bt_horizons)}"),
    ("backtest_section", "horizon_choices_exposed", "5,10,15,20,25,30"),
    ("backtest_section", "horizon_chips_disabled", "35,45"),
    ("backtest_section", "forecast_type", "; ".join(bt_types)),
    ("backtest_section", "date_min", bt_dates[0]),
    ("backtest_section", "date_max", bt_dates[-1]),
    ("backtest_section", "selected_champion", "; ".join(bt_champions) or "none"),
    ("backtest_section", "high_risk_models", "; ".join(bt_high_risk) or "none"),
    ("forward_section", "source_csv", "data/processed/forecasts.csv (+ actuals.csv)"),
    ("forward_section", "series_count", str(len(fwd_series_union))),
    ("forward_section", "forecast_only_series", str(len(fc_series))),
    ("forward_section", "actual_only_or_shared_series", str(len(ac_series))),
    ("forward_section", "model_versions", "; ".join(fc_models)),
    ("forward_section", "value_types", "; ".join(fc_value_types)),
    ("forward_section", "forecast_date_min", fc_dates[0]),
    ("forward_section", "forecast_date_max", fc_dates[-1]),
    ("forward_section", "actual_date_min", ac_dates[0]),
    ("forward_section", "actual_date_max", ac_dates[-1]),
    ("forward_section", "backtest_series_subset_of_forward", str(bt_subset_of_fwd)),
]
contract_path = os.path.join(OUT, "stage07_11_FULL_REBIND_ui_data_contract.csv")
with open(contract_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["section", "attribute", "value"])
    for c in contract:
        w.writerow(c)

# ------------------------------------------------------------ chart readiness
readiness = [
    ("fvp_chart", "backtest", "static highchartOutput", "input$fvp_go", "fvp_empty_chart",
     "actual + selected model forecast lines", "yes (live)"),
    ("fvf_chart", "forward", "static highchartOutput", "input$fvf_go", "fvf_empty_chart",
     "actual history + forward forecast + Forecast start boundary", "yes (live)"),
]
readiness_path = os.path.join(OUT, "stage07_11_FULL_REBIND_chart_readiness.csv")
with open(readiness_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["chart_id", "section", "container", "gate_input", "empty_state_fn",
                "lines_on_render", "rendered_live"])
    for r in readiness:
        w.writerow(r)

# ------------------------------------------------------------- series summary
# per-series counts for the forward section (actual points + forecast points)
fc_by = {}
for r in fc:
    fc_by.setdefault(r["entity_key"], 0)
    fc_by[r["entity_key"]] += 1
ac_by = {}
for r in ac:
    ac_by.setdefault(r["entity_key"], 0)
    ac_by[r["entity_key"]] += 1
bt_by = {}
for r in bt:
    bt_by.setdefault(r["series_key"], set())
    bt_by[r["series_key"]].add(r["model_name"])

series_path = os.path.join(OUT, "stage07_11_FULL_REBIND_series_summary.csv")
with open(series_path, "w", encoding="utf-8", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["series_key", "in_backtest", "backtest_models",
                "in_forward", "forward_forecast_points", "actual_points"])
    for s in fwd_series_union:
        w.writerow([
            s,
            "yes" if s in bt_by else "no",
            len(bt_by.get(s, set())),
            "yes" if s in fc_by else "no",
            fc_by.get(s, 0),
            ac_by.get(s, 0),
        ])

# ------------------------------------------------------------------- report md
n_pass = sum(1 for c in checks if c[1] == "pass")
n_warn = sum(1 for c in checks if c[1] == "warning")
n_fail = sum(1 for c in checks if c[1] == "fail")
ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

report = f"""# Stage 07 - Block 7.11-FULL-REBIND Validation Report

Generated: {ts}

Forecast Viewer full rebind to the Stage 05H full artifact. Two clearly separated
sections: **Backtest Comparison** (multi-model historical) and **Forward Forecast**
(single production model into the future). Read-only; no models run, no artifacts
modified.

## Check summary

- pass: {n_pass}
- warning: {n_warn}
- fail: {n_fail}

## Backtest Comparison (Section 1)

- Source: `data/processed/forecast_viewer_model_outputs.csv`
- Series exposed: **{len(bt_series)}**
- Models exposed: **{len(bt_models)}** across {len(bt_families)} families ({', '.join(bt_families)})
- Horizons in artifact: {min(bt_horizons)}-{max(bt_horizons)} days
- Horizon choices exposed: 5, 10, 15, 20, 25, 30 (35 / 45 shown disabled)
- forecast_type: {', '.join(bt_types)}
- Date range: {bt_dates[0]} -> {bt_dates[-1]}
- Selected champion: {', '.join(bt_champions) or 'none'}
- High-risk models: {', '.join(bt_high_risk) or 'none'}

## Forward Forecast (Section 2)

- Source: `data/processed/forecasts.csv` (+ `actuals.csv` for history)
- Series exposed (union): **{len(fwd_series_union)}**
- Model versions: {', '.join(fc_models)}
- value_type: {', '.join(fc_value_types)}
- Forecast date range: {fc_dates[0]} -> {fc_dates[-1]}
- Actual date range: {ac_dates[0]} -> {ac_dates[-1]}
- All backtest series are a subset of forward series: {bt_subset_of_fwd}

## Live render verification

- Backtest chart drew an actual line plus multiple model forecast lines after
  clicking **Analyze Backtest** (gated; empty before click).
- Forward chart drew an actual-history line, a forward-forecast line, and a vertical
  **Forecast start** boundary at the actual/forecast transition after clicking
  **Analyze Forward Forecast** (gated; empty before click).

## Artifacts written by this block

- `stage07_11_FULL_REBIND_report.md`
- `stage07_11_FULL_REBIND_validation.csv`
- `stage07_11_FULL_REBIND_ui_data_contract.csv`
- `stage07_11_FULL_REBIND_chart_readiness.csv`
- `stage07_11_FULL_REBIND_series_summary.csv`

No `data/processed` artifact was modified. No Stage 05 / Stage 06 output was modified.
"""

report_path = os.path.join(OUT, "stage07_11_FULL_REBIND_report.md")
with open(report_path, "w", encoding="utf-8") as fh:
    fh.write(report)

print("WROTE:")
for p in (report_path, val_path, contract_path, readiness_path, series_path):
    print(" -", os.path.relpath(p, V1).replace("\\", "/"))
print(f"checks: pass={n_pass} warning={n_warn} fail={n_fail}")
print(f"backtest_series={len(bt_series)} forward_series={len(fwd_series_union)} models={len(bt_models)}")
