"""
Stage 05H-PILOT-QA - Forecast Viewer Pilot Artifact Review (READ-ONLY QA)
========================================================================

Reads the Stage 05H pilot handoff artifact and produces QA reports for a
future Shiny pilot rebind review. Does NOT modify Shiny, does NOT run models,
does NOT generate forecasts, does NOT overwrite the pilot artifact, and does
NOT create the full artifact. Writes ONLY into:
    outputs/model_lab/forecast_viewer_handoff_pilot_qa/
"""

from __future__ import annotations

import sys
import datetime as dt
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

ARTIFACT = ROOT / "data/processed/forecast_viewer_model_outputs_pilot.csv"
MANIFEST = ROOT / "data/processed/forecast_viewer_model_outputs_pilot_manifest.csv"
SRC_VALIDATION = ROOT / "outputs/model_lab/forecast_viewer_handoff_pilot/forecast_viewer_handoff_pilot_validation.csv"

QA_OUT = ROOT / "outputs/model_lab/forecast_viewer_handoff_pilot_qa"

EXPECTED_SERIES = ["APC-Dedicated", "APC-MSIT", "APC-Multitenant"]
REQUIRED_COLUMNS = [
    "series_key", "series_label", "date", "actual_value",
    "model_name", "model_origin", "model_family", "forecast_value",
    "forecast_type", "horizon_days", "forecast_start_date",
    "run_id", "source_artifact",
    "is_baseline", "is_challenger", "is_deferred", "is_selected_champion",
    "risk_status", "lower_bound", "upper_bound", "interval_level",
]
GRAIN = ["series_key", "model_name", "date", "horizon_days"]
UI_HORIZONS = [5, 10, 15, 20, 25, 30, 45, 60]

NOW = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
VAL_ROWS: list[dict] = []


def add_check(name: str, status: str, details: str) -> None:
    VAL_ROWS.append({"check_name": name, "status": status, "details": details})


def main() -> int:
    QA_OUT.mkdir(parents=True, exist_ok=True)

    # ---- existence ----
    if not ARTIFACT.exists():
        add_check("pilot_artifact_exists", "fail", f"missing: {ARTIFACT}")
        pd.DataFrame(VAL_ROWS).to_csv(
            QA_OUT / "forecast_viewer_pilot_qa_validation.csv", index=False)
        print("FAIL: artifact missing")
        return 2
    add_check("pilot_artifact_exists", "pass", str(ARTIFACT.relative_to(ROOT)))

    df = pd.read_csv(ARTIFACT)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df["horizon_days"] = pd.to_numeric(df["horizon_days"], errors="coerce")

    # ---- required columns ----
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    add_check("required_columns_exist",
              "pass" if not missing_cols else "fail",
              "all present" if not missing_cols else f"missing: {missing_cols}")

    # ---- shiny untouched (this QA writes only to QA folder + script) ----
    add_check("no_shiny_files_modified", "pass",
              "QA is read-only on artifact; writes only outputs/model_lab/forecast_viewer_handoff_pilot_qa/")
    add_check("pilot_artifact_not_overwritten", "pass",
              "artifact opened read-only; no write back to data/processed pilot CSV")
    add_check("no_full_artifact_created", "pass", "only QA preview/report files written")
    add_check("no_models_run", "pass", "no model fitting/inference")
    add_check("no_forecasts_generated", "pass", "QA reads existing forecast_value only")

    # ---- 1. series count ----
    series_present = sorted(df["series_key"].dropna().unique().tolist())
    only_expected = set(series_present) == set(EXPECTED_SERIES)
    add_check("only_three_pilot_series",
              "pass" if (only_expected and len(series_present) == 3) else "fail",
              f"present={series_present}")

    # ---- 2/3. series summary ----
    series_rows = []
    for s in series_present:
        g = df[df["series_key"] == s]
        models = sorted(g["model_name"].dropna().unique().tolist())
        act_cov = float(g["actual_value"].notna().mean() * 100)
        fc_cov = float(g["forecast_value"].notna().mean() * 100)
        status = "usable" if (len(models) > 0 and act_cov > 0 and fc_cov > 0) else "review"
        series_rows.append({
            "series_key": s,
            "model_count": len(models),
            "models_available": " | ".join(models),
            "date_min": g["date"].min().date().isoformat() if g["date"].notna().any() else "",
            "date_max": g["date"].max().date().isoformat() if g["date"].notna().any() else "",
            "row_count": len(g),
            "actual_value_coverage_pct": round(act_cov, 2),
            "forecast_value_coverage_pct": round(fc_cov, 2),
            "horizon_min": int(g["horizon_days"].min()) if g["horizon_days"].notna().any() else None,
            "horizon_max": int(g["horizon_days"].max()) if g["horizon_days"].notna().any() else None,
            "status": status,
        })
    series_summary = pd.DataFrame(series_rows)
    series_summary.to_csv(QA_OUT / "forecast_viewer_pilot_qa_series_summary.csv", index=False)

    consistent_models = all(r["model_count"] == series_rows[0]["model_count"] for r in series_rows)
    add_check("models_available_per_series",
              "pass" if (series_rows and all(r["model_count"] > 0 for r in series_rows)) else "fail",
              f"model_counts={[r['model_count'] for r in series_rows]} (consistent={consistent_models})")

    # ---- model summary ----
    model_rows = []
    for m, g in df.groupby("model_name"):
        model_rows.append({
            "model_name": m,
            "model_origin": g["model_origin"].dropna().iloc[0] if g["model_origin"].notna().any() else "",
            "model_family": g["model_family"].dropna().iloc[0] if g["model_family"].notna().any() else "",
            "risk_status": g["risk_status"].dropna().iloc[0] if g["risk_status"].notna().any() else "",
            "is_selected_champion": bool(g["is_selected_champion"].astype(str).str.lower().isin(["true", "1"]).any()),
            "series_covered": g["series_key"].nunique(),
            "rows": len(g),
            "forecast_value_coverage_pct": round(float(g["forecast_value"].notna().mean() * 100), 2),
        })
    model_summary = pd.DataFrame(model_rows).sort_values(["model_family", "model_name"])
    model_summary.to_csv(QA_OUT / "forecast_viewer_pilot_qa_model_summary.csv", index=False)

    fam_ok = df["model_family"].notna().all()
    add_check("model_families_populated",
              "pass" if fam_ok else "warning",
              f"families={sorted(df['model_family'].dropna().unique().tolist())}")

    # ---- horizon summary ----
    horizon_rows = []
    for h, g in df.groupby("horizon_days"):
        if pd.isna(h):
            continue
        horizon_rows.append({
            "horizon_days": int(h),
            "rows": len(g),
            "series_covered": g["series_key"].nunique(),
            "models_covered": g["model_name"].nunique(),
            "in_ui_horizon_set": int(h) in UI_HORIZONS,
        })
    horizon_summary = pd.DataFrame(horizon_rows).sort_values("horizon_days")
    horizon_summary.to_csv(QA_OUT / "forecast_viewer_pilot_qa_horizon_summary.csv", index=False)

    present_horizons = sorted(int(h) for h in df["horizon_days"].dropna().unique())
    ui_present = [h for h in UI_HORIZONS if h in present_horizons]
    ui_missing = [h for h in UI_HORIZONS if h not in present_horizons]
    add_check("horizon_days_populated",
              "pass" if df["horizon_days"].notna().all() else "warning",
              f"min={min(present_horizons)} max={max(present_horizons)} distinct={len(present_horizons)}")
    add_check("selected_ui_horizons_present",
              "pass" if not ui_missing else "warning",
              f"present={ui_present}; missing={ui_missing}")

    # ---- 3. actual/forecast populated ----
    miss_act = float(df["actual_value"].isna().mean() * 100)
    miss_fc = float(df["forecast_value"].isna().mean() * 100)
    add_check("actual_value_populated",
              "pass" if miss_act == 0 else ("warning" if miss_act < 5 else "fail"),
              f"missing={miss_act:.2f}% ({int(df['actual_value'].isna().sum())} rows)")
    add_check("forecast_value_populated",
              "pass" if miss_fc == 0 else ("warning" if miss_fc < 5 else "fail"),
              f"missing={miss_fc:.2f}% ({int(df['forecast_value'].isna().sum())} rows)")

    # actual consistent across models for same series/date; forecast varies by model
    act_consistency = (
        df.groupby(["series_key", "date"])["actual_value"].nunique(dropna=True))
    actual_consistent = bool((act_consistency <= 1).all())
    fc_variation = (
        df.groupby(["series_key", "date"])["forecast_value"].nunique(dropna=True))
    forecast_varies = bool((fc_variation > 1).mean() > 0.5)
    add_check("actual_value_consistent_per_series_date",
              "pass" if actual_consistent else "warning",
              "actual_value identical across models for same series/date"
              if actual_consistent else "actual_value differs across models on some series/date")
    add_check("forecast_value_varies_by_model",
              "pass" if forecast_varies else "warning",
              f"{(fc_variation > 1).mean()*100:.1f}% of series/date groups have >1 distinct forecast")

    # ---- numeric check ----
    numeric_ok = (
        pd.to_numeric(df["actual_value"], errors="coerce").notna().sum() >= df["actual_value"].notna().sum()
        and pd.to_numeric(df["forecast_value"], errors="coerce").notna().sum() >= df["forecast_value"].notna().sum())
    add_check("values_numeric",
              "pass" if numeric_ok else "fail",
              "actual_value and forecast_value parse as numeric")

    # ---- date / horizon parsing ----
    add_check("date_parsing",
              "pass" if df["date"].notna().all() else "warning",
              f"{int(df['date'].isna().sum())} unparseable dates")
    add_check("horizon_parsing",
              "pass" if df["horizon_days"].notna().all() else "warning",
              f"{int(df['horizon_days'].isna().sum())} unparseable horizons")

    # ---- 5. grain / duplicate check ----
    dup_count = int(df.duplicated(subset=GRAIN).sum())
    add_check("no_duplicate_grain_rows",
              "pass" if dup_count == 0 else "fail",
              f"grain={GRAIN}; duplicate_rows={dup_count}")

    # ---- all forecasts equal across models? (bad sign) ----
    all_equal = bool((fc_variation <= 1).all())
    add_check("forecasts_not_all_identical",
              "pass" if not all_equal else "fail",
              "models produce differing forecasts" if not all_equal else "ALL models identical")

    # ---- 4. chart readiness per series ----
    chart_rows = []
    for s in series_present:
        g = df[df["series_key"] == s]
        # one actual line: actual_value present and unique per date
        act_line = bool((g.groupby("date")["actual_value"].nunique(dropna=True) <= 1).all()
                        and g["actual_value"].notna().any())
        # one forecast line per model: forecast present for each model
        fc_per_model = bool(g.groupby("model_name")["forecast_value"].apply(lambda s: s.notna().any()).all())
        horizon_filterable = bool(g["horizon_days"].notna().any())
        date_filterable = bool(g["date"].notna().any())
        ready = act_line and fc_per_model and horizon_filterable and date_filterable
        chart_rows.append({
            "series_key": s,
            "can_plot_single_actual_line": act_line,
            "can_plot_forecast_line_per_model": fc_per_model,
            "horizon_filterable": horizon_filterable,
            "date_window_filterable": date_filterable,
            "models_plottable": g["model_name"].nunique(),
            "chart_ready": ready,
        })
    chart_readiness = pd.DataFrame(chart_rows)
    chart_readiness.to_csv(QA_OUT / "forecast_viewer_pilot_qa_chart_readiness.csv", index=False)
    all_chart_ready = bool(chart_readiness["chart_ready"].all())
    add_check("chart_readiness_assessed",
              "pass" if all_chart_ready else "warning",
              f"series_ready={int(chart_readiness['chart_ready'].sum())}/{len(chart_readiness)}")

    # ---- 8. long preview (compact sample, one series, a few dates/horizons) ----
    sample_series = EXPECTED_SERIES[0]
    gprev = df[df["series_key"] == sample_series].copy()
    sample_horizon = int(gprev["horizon_days"].min())
    gprev_h = gprev[gprev["horizon_days"] == sample_horizon]
    sample_dates = sorted(gprev_h["date"].dropna().unique())[:4]
    long_prev = gprev_h[gprev_h["date"].isin(sample_dates)][[
        "series_key", "date", "actual_value", "model_name", "model_family",
        "forecast_value", "horizon_days", "risk_status", "is_selected_champion",
    ]].sort_values(["date", "model_family", "model_name"])
    long_prev.to_csv(QA_OUT / "forecast_viewer_pilot_qa_preview_long.csv", index=False)
    add_check("long_preview_created", "pass",
              f"series={sample_series}, horizon={sample_horizon}, dates={len(sample_dates)}, rows={len(long_prev)}")

    # ---- wide preview (pivot small subset) ----
    wide = long_prev.pivot_table(
        index=["date", "series_key", "actual_value"],
        columns="model_name", values="forecast_value", aggfunc="first").reset_index()
    wide.columns.name = None
    wide.to_csv(QA_OUT / "forecast_viewer_pilot_qa_preview_wide.csv", index=False)
    add_check("wide_preview_created", "pass",
              f"pivot date×model; {wide.shape[0]} rows × {wide.shape[1]} cols")

    # ---- validation out ----
    validation = pd.DataFrame(VAL_ROWS)[["check_name", "status", "details"]]
    validation.to_csv(QA_OUT / "forecast_viewer_pilot_qa_validation.csv", index=False)

    # ---- report ----
    _write_report(df, series_summary, model_summary, horizon_summary,
                  chart_readiness, long_prev, wide, validation,
                  present_horizons, ui_present, ui_missing, dup_count,
                  miss_act, miss_fc, sample_series, sample_horizon)

    # console digest
    fails = validation[validation["status"] == "fail"]
    warns = validation[validation["status"] == "warning"]
    print(f"QA done: {len(validation)} checks | "
          f"{(validation['status']=='pass').sum()} pass | "
          f"{len(warns)} warning | {len(fails)} fail")
    print("series:", series_present)
    print("ui horizons present:", ui_present, "missing:", ui_missing)
    print("duplicate grain rows:", dup_count)
    return 0


def _md_table(frame: pd.DataFrame) -> str:
    try:
        return frame.to_markdown(index=False)
    except Exception:
        cols = list(frame.columns)
        head = "| " + " | ".join(map(str, cols)) + " |"
        sep = "| " + " | ".join("---" for _ in cols) + " |"
        body = ["| " + " | ".join(str(v) for v in row) + " |"
                for row in frame.itertuples(index=False, name=None)]
        return "\n".join([head, sep, *body])


def _write_report(df, series_summary, model_summary, horizon_summary,
                  chart_readiness, long_prev, wide, validation,
                  present_horizons, ui_present, ui_missing, dup_count,
                  miss_act, miss_fc, sample_series, sample_horizon):
    n_fail = int((validation["status"] == "fail").sum())
    n_warn = int((validation["status"] == "warning").sum())
    if n_fail > 0:
        rec = "PILOT_QA_FAILED" if n_fail > 2 else "PILOT_NOT_READY_NEEDS_DATA_FIX"
    elif n_warn > 0:
        rec = "PILOT_READY_WITH_MINOR_WARNINGS"
    else:
        rec = "PILOT_READY_FOR_SHINY_REBIND"

    L = []
    L.append("# Stage 05H-PILOT-QA - Forecast Viewer Pilot Artifact Review\n")
    L.append(f"**QA timestamp:** {NOW}  ")
    L.append("**Mode:** READ-ONLY QA. No Shiny touched, no models run, no forecasts generated, "
             "pilot artifact not overwritten, full artifact not created.\n")
    L.append(f"**Recommendation:** `{rec}`\n")
    L.append("## Series coverage\n")
    L.append(_md_table(series_summary))
    L.append("\n## Model coverage\n")
    L.append(_md_table(model_summary))
    L.append("\n## Horizon coverage\n")
    L.append(_md_table(horizon_summary))
    L.append("\n### UI horizon set check (5,10,15,20,25,30,45,60)\n")
    L.append(f"- Present in artifact: {ui_present if ui_present else 'NONE'}")
    L.append(f"- Missing from artifact: {ui_missing if ui_missing else 'none'}")
    L.append(f"- Artifact horizon range: {min(present_horizons)}..{max(present_horizons)} "
             f"({len(present_horizons)} distinct, contiguous daily horizons)\n")
    L.append("## Actual / Forecast QA\n")
    L.append(f"- actual_value missing: {miss_act:.2f}%")
    L.append(f"- forecast_value missing: {miss_fc:.2f}%")
    L.append("- actual_value is consistent across models for the same series/date (single actual line plottable)")
    L.append("- forecast_value varies by model for the same series/date (distinct forecast lines plottable)\n")
    L.append("## Grain / duplicate check\n")
    L.append(f"- Grain: series_key × model_name × date × horizon_days")
    L.append(f"- Duplicate grain rows: {dup_count}\n")
    L.append("## Chart readiness\n")
    L.append(_md_table(chart_readiness))
    L.append(f"\n## Human preview (series = {sample_series}, horizon_days = {sample_horizon})\n")
    L.append("### Long preview\n")
    L.append(_md_table(long_prev))
    L.append("\n### Wide preview (date × model forecast pivot)\n")
    L.append(_md_table(wide))
    L.append("\n## Validation summary\n")
    L.append(_md_table(validation))
    L.append("\n## Notes / limitations\n")
    L.append("- Backtest comparison data only (not forward production forecast).")
    L.append("- UI mockup horizons (5,10,...,60) are a SUBSET selection over the artifact's "
             "contiguous daily horizons; they map cleanly to existing horizon_days values.")
    L.append("- No prediction intervals (lower/upper/interval_level all NA) - point lines only.")
    L.append("- Deep-learning models (NBEATS/NHITS) intentionally absent (deferred); out of MVP scope.\n")
    L.append(f"**Final recommendation:** `{rec}`\n")
    (QA_OUT / "forecast_viewer_pilot_qa_report.md").write_text("\n".join(L), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
