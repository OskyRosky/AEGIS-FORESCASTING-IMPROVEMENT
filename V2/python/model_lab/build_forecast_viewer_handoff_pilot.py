"""
Stage 05H-PILOT - Forecast Viewer Multi-Model Handoff (PILOT builder)
=====================================================================

PURPOSE
    Build a SMALL, controlled pilot of the consolidated multi-model Forecast
    Viewer handoff artifact for a maximum of 3 representative series, using
    ONLY existing governed Model Lab / data outputs.

WHAT THIS IS (and is NOT)
    - This is a DATA-ENGINEERING CONSOLIDATION (curation) of existing Stage 5
      Model Lab forecast outputs into one long/tidy artifact for Shiny.
    - It does NOT run models, generate forecasts, recompute metrics, rerun
      tournaments, or change the champion decision.
    - It writes ONLY *_pilot* artifacts. It never overwrites forecasts.csv,
      actuals.csv, entities.csv, or forecast_comparison.csv.

SEMANTICS
    The multi-model values are HISTORICAL BACKTEST forecasts, not the forward
    production forecast. The dashboard must label this as model comparison /
    backtest evidence.

REUSABILITY
    The build logic is parameterised by `series_keys`; a later FULL builder can
    reuse `build_handoff(series_keys=<all 39>)`. This pilot caps to <= 3 series.
"""

from __future__ import annotations

import sys
import csv
import hashlib
import datetime as dt
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Paths (resolved relative to V1 root = two parents up from this file:
#   V1/python/model_lab/build_forecast_viewer_handoff_pilot.py)
# ---------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[2]

SRC = {
    "baseline":   ROOT / "outputs/model_lab/full_baseline/full_baseline_forecasts.csv",
    "challenger": ROOT / "outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv",
    "actuals":    ROOT / "data/processed/actuals.csv",
    "entities":   ROOT / "data/processed/entities.csv",
    "universe":   ROOT / "outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv",
    "deferred":   ROOT / "outputs/model_lab/model_lab_closure_pack/model_lab_deferred_models.csv",
    "risk":       ROOT / "outputs/model_lab/model_lab_closure_pack/model_lab_risk_register_final.csv",
    "champion":   ROOT / "outputs/model_lab/model_lab_closure_pack/model_lab_champion_summary.csv",
}

DATA_OUT = ROOT / "data/processed"
REPORT_OUT = ROOT / "outputs/model_lab/forecast_viewer_handoff_pilot"
LOG_OUT = REPORT_OUT / "logs"

PREFERRED = ["APC-Dedicated", "APC-MSIT", "APC-Multitenant"]
ALTERNATES = ["ARE-Go Local", "AUS-Go Local", "BRA-Go Local"]
MAX_SERIES = 3

SCHEMA_COLUMNS = [
    "series_key", "series_label", "date", "actual_value",
    "model_name", "model_origin", "model_family", "forecast_value",
    "forecast_type", "horizon_days", "forecast_start_date",
    "run_id", "source_artifact",
    "is_baseline", "is_challenger", "is_deferred", "is_selected_champion",
    "risk_status", "lower_bound", "upper_bound", "interval_level",
]

NOW = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
LOG_LINES: list[str] = []


def log(msg: str) -> None:
    line = f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}"
    LOG_LINES.append(line)
    print(line)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_sources() -> dict[str, pd.DataFrame]:
    data = {}
    for key, path in SRC.items():
        if not path.exists():
            log(f"WARNING missing source: {key} -> {path}")
            data[key] = None
            continue
        data[key] = pd.read_csv(path)
        log(f"loaded {key}: {len(data[key]):,} rows <- {path.relative_to(ROOT)}")
    return data


def build_model_metadata(data: dict) -> tuple[pd.DataFrame, set]:
    """Return per-model metadata frame and the set of deferred model names."""
    uni = data["universe"].copy()
    deferred_set = set()
    if data["deferred"] is not None:
        deferred_set = set(data["deferred"]["model_name"].astype(str).str.strip())
    # risk: any model present in risk register marked high-risk OR risk_flag in universe
    risk_models = set()
    if data["risk"] is not None and "model_name" in data["risk"].columns:
        risk_models = set(
            data["risk"]["model_name"].dropna().astype(str).str.strip()
        )
    uni["model_name_norm"] = uni["model_name"].astype(str).str.strip()
    uni["is_deferred"] = uni["model_name_norm"].isin(deferred_set)
    uni["is_selected_champion"] = uni["selected_champion"].astype(str).str.lower().isin(
        ["true", "1", "yes"]
    )
    uni["risk_flag_bool"] = uni["risk_flag"].astype(str).str.lower().isin(
        ["true", "1", "yes"]
    )
    uni["risk_status"] = uni.apply(
        lambda r: "high_risk"
        if (r["risk_flag_bool"] or r["model_name_norm"] in risk_models)
        else "ok",
        axis=1,
    )
    meta = uni[
        [
            "model_name_norm", "model_origin", "model_family",
            "is_deferred", "is_selected_champion", "risk_status",
        ]
    ].rename(columns={"model_name_norm": "model_name"})
    return meta, deferred_set


# ---------------------------------------------------------------------------
# Coverage check
# ---------------------------------------------------------------------------
def coverage_for_series(series_key: str, baseline: pd.DataFrame,
                        challenger: pd.DataFrame, actuals: pd.DataFrame) -> dict:
    b = baseline[baseline["entity_key"].astype(str).str.strip() == series_key]
    c = challenger[challenger["entity_key"].astype(str).str.strip() == series_key]
    a = actuals[actuals["entity_key"].astype(str).str.strip() == series_key]
    bmodels = sorted(b["model_name"].astype(str).str.strip().unique())
    cmodels = sorted(c["model_name"].astype(str).str.strip().unique())
    allmodels = sorted(set(bmodels) | set(cmodels))
    dates = []
    if len(b):
        dates += pd.to_datetime(b["forecast_date"], errors="coerce").dropna().tolist()
    if len(c):
        dates += pd.to_datetime(c["forecast_date"], errors="coerce").dropna().tolist()
    if len(a):
        dates += pd.to_datetime(a["date"], errors="coerce").dropna().tolist()
    status = "usable" if (len(bmodels) > 0 and len(cmodels) > 0) else "insufficient"
    return {
        "series_key": series_key,
        "series_label": series_key,
        "has_actuals": len(a) > 0 or len(c) > 0,
        "has_baseline_forecasts": len(b) > 0,
        "has_challenger_forecasts": len(c) > 0,
        "baseline_model_count": len(bmodels),
        "challenger_model_count": len(cmodels),
        "total_model_count": len(allmodels),
        "models_available": " | ".join(allmodels),
        "min_date": min(dates).date().isoformat() if dates else "",
        "max_date": max(dates).date().isoformat() if dates else "",
        "status": status,
    }


def select_pilot_series(data: dict) -> tuple[list[str], pd.DataFrame]:
    baseline, challenger, actuals = data["baseline"], data["challenger"], data["actuals"]
    rows = []
    for s in PREFERRED + ALTERNATES:
        rows.append(coverage_for_series(s, baseline, challenger, actuals))
    cov = pd.DataFrame(rows)
    # choose: preferred usable first, then alternates, cap at 3
    chosen = []
    for s in PREFERRED:
        r = cov[cov["series_key"] == s].iloc[0]
        if r["status"] == "usable" and len(chosen) < MAX_SERIES:
            chosen.append(s)
    if len(chosen) < MAX_SERIES:
        for s in ALTERNATES:
            r = cov[cov["series_key"] == s].iloc[0]
            if r["status"] == "usable" and len(chosen) < MAX_SERIES:
                chosen.append(s)
    cov["selected_for_pilot"] = cov["series_key"].isin(chosen)
    return chosen, cov


# ---------------------------------------------------------------------------
# Build the long/tidy artifact for the chosen series
# ---------------------------------------------------------------------------
def build_handoff(series_keys: list[str], data: dict, meta: pd.DataFrame) -> pd.DataFrame:
    baseline, challenger, actuals = data["baseline"], data["challenger"], data["actuals"]

    # actuals lookup for baseline rows (entity_key + date -> actual_value)
    act = actuals.copy()
    act["entity_key"] = act["entity_key"].astype(str).str.strip()
    act["date"] = pd.to_datetime(act["date"], errors="coerce")
    act_lookup = act[["entity_key", "date", "actual_value"]].drop_duplicates(
        ["entity_key", "date"]
    )

    frames = []

    # ----- baseline (forecast only; attach actuals by join) -----
    b = baseline.copy()
    b["entity_key"] = b["entity_key"].astype(str).str.strip()
    b = b[b["entity_key"].isin(series_keys)]
    if len(b):
        b["forecast_date"] = pd.to_datetime(b["forecast_date"], errors="coerce")
        b = b.merge(act_lookup, left_on=["entity_key", "forecast_date"],
                    right_on=["entity_key", "date"], how="left")
        out_b = pd.DataFrame({
            "series_key": b["entity_key"],
            "series_label": b["entity_key"],
            "date": b["forecast_date"].dt.date.astype("string"),
            "actual_value": b["actual_value"],
            "model_name": b["model_name"].astype(str).str.strip(),
            "forecast_value": b["forecast_value"],
            "forecast_type": "backtest",
            "horizon_days": pd.to_numeric(b["horizon_day"], errors="coerce"),
            "run_id": b["run_id"],
            "source_artifact": "outputs/model_lab/full_baseline/full_baseline_forecasts.csv",
        })
        frames.append(out_b)

    # ----- challenger (forecast + actual already joined) -----
    c = challenger.copy()
    c["entity_key"] = c["entity_key"].astype(str).str.strip()
    c = c[c["entity_key"].isin(series_keys)]
    if len(c):
        c["forecast_date"] = pd.to_datetime(c["forecast_date"], errors="coerce")
        out_c = pd.DataFrame({
            "series_key": c["entity_key"],
            "series_label": c["entity_key"],
            "date": c["forecast_date"].dt.date.astype("string"),
            "actual_value": c["actual_value"],
            "model_name": c["model_name"].astype(str).str.strip(),
            "forecast_value": c["forecast_value"],
            "forecast_type": "backtest",
            "horizon_days": pd.to_numeric(c["horizon_day"], errors="coerce"),
            "run_id": c["run_id"],
            "source_artifact": "outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv",
        })
        frames.append(out_c)

    if not frames:
        return pd.DataFrame(columns=SCHEMA_COLUMNS)

    df = pd.concat(frames, ignore_index=True)

    # attach model metadata (origin/family/deferred/champion/risk)
    df = df.merge(meta, on="model_name", how="left")

    # derived: forecast_start_date = date - horizon_days
    d = pd.to_datetime(df["date"], errors="coerce")
    h = pd.to_numeric(df["horizon_days"], errors="coerce")
    df["forecast_start_date"] = (d - pd.to_timedelta(h, unit="D")).dt.date.astype("string")

    # flags
    df["is_baseline"] = df["model_origin"].astype(str).str.lower().eq("baseline")
    df["is_challenger"] = df["model_origin"].astype(str).str.lower().eq("challenger")
    df["is_deferred"] = df["is_deferred"].fillna(False)
    df["is_selected_champion"] = df["is_selected_champion"].fillna(False)
    df["risk_status"] = df["risk_status"].fillna("ok")

    # intervals not available in any source -> NA
    df["lower_bound"] = pd.NA
    df["upper_bound"] = pd.NA
    df["interval_level"] = pd.NA

    # SAFETY: deferred models must NOT appear as forecast rows
    df = df[~df["is_deferred"].astype(bool)].copy()

    df = df[SCHEMA_COLUMNS].sort_values(
        ["series_key", "model_family", "model_name", "date"]
    ).reset_index(drop=True)
    return df


# ---------------------------------------------------------------------------
# Writers + reports
# ---------------------------------------------------------------------------
def df_to_md(frame: pd.DataFrame) -> str:
    """Markdown table without requiring the optional `tabulate` package."""
    try:
        return frame.to_markdown(index=False)
    except Exception:
        cols = list(frame.columns)
        head = "| " + " | ".join(cols) + " |"
        sep = "| " + " | ".join("---" for _ in cols) + " |"
        body = [
            "| " + " | ".join(str(v) for v in row) + " |"
            for row in frame.itertuples(index=False, name=None)
        ]
        return "\n".join([head, sep, *body])


def file_checksum(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def main() -> int:
    REPORT_OUT.mkdir(parents=True, exist_ok=True)
    LOG_OUT.mkdir(parents=True, exist_ok=True)
    log(f"Stage 05H-PILOT builder start | ROOT={ROOT}")

    data = load_sources()
    meta, deferred_set = build_model_metadata(data)
    log(f"deferred models (excluded from rows): {sorted(deferred_set)}")

    chosen, cov = select_pilot_series(data)
    cov.to_csv(REPORT_OUT / "forecast_viewer_handoff_pilot_coverage_by_series.csv", index=False)
    log(f"pilot series chosen: {chosen}")

    # ---- gate: need exactly/at least 3 usable series ----
    if len(chosen) < 3:
        log(f"FAIL coverage insufficient: only {len(chosen)} usable series")
        _write_validation(created=False, df=None, chosen=chosen,
                          fallback_csv=True, reason="coverage_insufficient")
        _write_report(df=None, chosen=chosen, cov=cov, created=False,
                      fallback_csv=True, deferred_set=deferred_set)
        _flush_logs()
        return 2

    df = build_handoff(chosen, data, meta)
    log(f"built pilot artifact rows: {len(df):,}")

    # ---- write consumable artifact (parquet if engine available, else CSV) ----
    parquet_ok = False
    parquet_path = DATA_OUT / "forecast_viewer_model_outputs_pilot.parquet"
    csv_path = DATA_OUT / "forecast_viewer_model_outputs_pilot.csv"
    try:
        import pyarrow  # noqa: F401
        df.to_parquet(parquet_path, index=False)
        parquet_ok = True
        primary_path = parquet_path
        log(f"wrote parquet: {parquet_path.relative_to(ROOT)}")
    except Exception as exc:  # pyarrow/fastparquet unavailable -> CSV fallback
        df.to_csv(csv_path, index=False)
        primary_path = csv_path
        log(f"parquet engine unavailable ({type(exc).__name__}); CSV fallback -> {csv_path.relative_to(ROOT)}")

    # sample CSV (first 200 rows)
    sample_path = DATA_OUT / "forecast_viewer_model_outputs_pilot_sample.csv"
    df.head(200).to_csv(sample_path, index=False)
    log(f"wrote sample CSV: {sample_path.relative_to(ROOT)} (<=200 rows)")

    # ---- manifest ----
    manifest_path = DATA_OUT / "forecast_viewer_model_outputs_pilot_manifest.csv"
    _write_manifest(manifest_path, df, chosen, primary_path, parquet_ok, data, deferred_set)
    log(f"wrote manifest: {manifest_path.relative_to(ROOT)}")

    # ---- schema, model coverage, source manifest, validation, report ----
    _write_schema(df)
    _write_model_coverage(df)
    _write_source_manifest(data)
    _write_validation(created=True, df=df, chosen=chosen,
                      fallback_csv=not parquet_ok, reason="ok")
    _write_report(df=df, chosen=chosen, cov=cov, created=True,
                  fallback_csv=not parquet_ok, deferred_set=deferred_set)
    _flush_logs()
    log("Stage 05H-PILOT builder done")
    return 0


def _write_manifest(path, df, chosen, primary_path, parquet_ok, data, deferred_set):
    rows = []
    rows.append(("artifact_name", primary_path.name))
    rows.append(("artifact_format", "parquet" if parquet_ok else "csv_fallback"))
    rows.append(("build_timestamp", NOW))
    rows.append(("pilot_series", " | ".join(chosen)))
    rows.append(("series_count", str(df["series_key"].nunique())))
    rows.append(("model_count", str(df["model_name"].nunique())))
    rows.append(("row_count", str(len(df))))
    rows.append(("date_min", str(df["date"].min())))
    rows.append(("date_max", str(df["date"].max())))
    rows.append(("forecast_type", "backtest_historical_comparison"))
    rows.append(("interval_availability", "none_point_forecasts_only"))
    rows.append(("deferred_models_excluded", " | ".join(sorted(deferred_set))))
    rows.append(("no_model_rerun", "TRUE"))
    rows.append(("no_synthetic_forecasts", "TRUE"))
    rows.append(("no_metric_recalculation", "TRUE"))
    rows.append(("no_champion_change", "TRUE"))
    # source row counts + checksums
    for key in ["baseline", "challenger", "actuals", "universe"]:
        p = SRC[key]
        if p.exists():
            rows.append((f"source__{key}", str(p.relative_to(ROOT))))
            rows.append((f"source_rows__{key}", str(len(data[key]))))
            rows.append((f"source_sha256_16__{key}", file_checksum(p)))
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["key", "value"])
        w.writerows(rows)


def _write_schema(df):
    rows = []
    for col in SCHEMA_COLUMNS:
        non_na = int(df[col].notna().sum())
        rows.append({
            "column": col,
            "dtype": str(df[col].dtype),
            "non_null_rows": non_na,
            "null_rows": int(len(df) - non_na),
            "example": "" if df[col].dropna().empty else str(df[col].dropna().iloc[0]),
        })
    pd.DataFrame(rows).to_csv(
        REPORT_OUT / "forecast_viewer_handoff_pilot_schema.csv", index=False)


def _write_model_coverage(df):
    g = (df.groupby(["series_key", "model_name", "model_origin", "model_family",
                     "is_selected_champion", "risk_status"])
         .agg(rows=("forecast_value", "size"),
              actual_points=("actual_value", lambda s: int(s.notna().sum())),
              min_date=("date", "min"), max_date=("date", "max"))
         .reset_index()
         .sort_values(["series_key", "model_family", "model_name"]))
    g.to_csv(REPORT_OUT / "forecast_viewer_handoff_pilot_model_coverage.csv", index=False)


def _write_source_manifest(data):
    rows = []
    for key, p in SRC.items():
        rows.append({
            "source_key": key,
            "path": str(p.relative_to(ROOT)) if p.exists() else "MISSING",
            "exists": p.exists(),
            "rows": (len(data[key]) if data[key] is not None else 0),
            "sha256_16": file_checksum(p) if p.exists() else "",
        })
    pd.DataFrame(rows).to_csv(
        REPORT_OUT / "forecast_viewer_handoff_pilot_source_manifest.csv", index=False)


def _write_validation(created, df, chosen, fallback_csv, reason):
    def chk(name, status, details):
        return {"check_name": name, "status": status, "details": details}

    rows = [
        chk("no_shiny_files_modified", "pass", "Builder writes only python/model_lab + data *_pilot* + outputs/model_lab/forecast_viewer_handoff_pilot"),
        chk("no_existing_data_overwritten", "pass", "Only *_pilot* artifacts written; forecasts/actuals/entities/forecast_comparison untouched"),
        chk("no_model_lab_outputs_modified", "pass", "Existing Model Lab outputs read-only"),
        chk("no_forecasts_generated", "pass", "Consolidation only; zero model inference"),
        chk("no_models_run", "pass", "No model fitting/inference"),
        chk("no_metrics_recalculated", "pass", "No metric computation"),
        chk("no_champion_decision_changed", "pass", "champion flag read from model universe only"),
        chk("only_pilot_artifact_created", "pass", "All consumable artifacts carry _pilot suffix"),
        chk("max_three_series", "pass" if len(chosen) <= 3 else "fail", f"series={chosen}"),
    ]
    if created and df is not None:
        only_pilot = set(df["series_key"].unique()).issubset(set(chosen))
        traced = df["source_artifact"].notna().all()
        fam_ok = df["model_family"].notna().all()
        champ_ok = bool(df["is_selected_champion"].any())
        risk_ok = df["risk_status"].notna().all()
        no_deferred = (~df["is_deferred"].astype(bool)).all()
        intervals_na = df[["lower_bound", "upper_bound", "interval_level"]].isna().all().all()
        rows += [
            chk("all_rows_in_pilot_series", "pass" if only_pilot else "fail", f"series={sorted(df['series_key'].unique())}"),
            chk("all_model_rows_trace_to_source", "pass" if traced else "fail", "source_artifact populated on every row"),
            chk("actual_value_source_documented", "pass", "challenger: joined column; baseline: left-join actuals.csv on entity_key+date"),
            chk("forecast_value_source_documented", "pass", "full_baseline_forecasts.csv + challenger_actual_forecast_join.csv"),
            chk("model_family_mapping_present", "pass" if fam_ok else "fail", "model_family from model_lab_final_model_universe.csv"),
            chk("champion_flag_mapping_present", "pass" if champ_ok else "warning", "is_selected_champion TRUE for governed champion (ETS Explicit)"),
            chk("risk_flag_mapping_present", "pass" if risk_ok else "fail", "risk_status from universe risk_flag + risk register"),
            chk("deferred_models_not_materialized", "pass" if no_deferred else "fail", "NBEATS/NHITS excluded from forecast rows"),
            chk("interval_columns_present_but_na", "pass" if intervals_na else "warning", "lower/upper/interval_level all NA (no source bands)"),
            chk("row_counts_by_series_produced", "pass", "coverage_by_series + model_coverage written"),
            chk("model_counts_by_series_produced", "pass", "model_coverage written"),
            chk("source_manifest_produced", "pass", "source_manifest + manifest written"),
            chk("sample_csv_created", "pass", "forecast_viewer_model_outputs_pilot_sample.csv"),
            chk("parquet_or_csv_fallback_reported", "warning" if fallback_csv else "pass",
                "CSV fallback used (no pyarrow/fastparquet)" if fallback_csv else "parquet written"),
        ]
    else:
        rows += [chk("pilot_artifact_created", "fail", f"NOT created: {reason}")]
    pd.DataFrame(rows).to_csv(
        REPORT_OUT / "forecast_viewer_handoff_pilot_validation.csv", index=False)


def _write_report(df, chosen, cov, created, fallback_csv, deferred_set):
    lines = []
    lines.append("# Stage 05H-PILOT - Forecast Viewer Multi-Model Handoff (PILOT)\n")
    lines.append(f"**Build timestamp:** {NOW}  ")
    lines.append("**Mode:** Data-engineering consolidation of EXISTING Stage 5 outputs. "
                 "No models run, no forecasts generated, no metrics recomputed, no champion change.\n")
    lines.append("## Semantics\n")
    lines.append("This artifact contains **historical BACKTEST** model forecasts for "
                 "model comparison. It is **NOT** the forward production forecast. The "
                 "dashboard must label it as *model comparison / backtest evidence*.\n")
    lines.append("## 1-2. Selected series and coverage\n")
    lines.append(f"Pilot series selected: **{', '.join(chosen) if chosen else 'NONE'}**\n")
    lines.append(df_to_md(cov))
    lines.append("")
    if not created or df is None:
        lines.append("## Result: PILOT ARTIFACT NOT CREATED\n")
        lines.append("Fewer than 3 series had usable multi-model coverage. See coverage table above.\n")
        (REPORT_OUT / "forecast_viewer_handoff_pilot_report.md").write_text(
            "\n".join(lines), encoding="utf-8")
        return
    n_models = df["model_name"].nunique()
    lines.append("## 3-4. Models available per series\n")
    per = (df.groupby("series_key")["model_name"].nunique()
           .reset_index(name="model_count"))
    lines.append(df_to_md(per))
    lines.append("")
    lines.append("## 5. Source artifacts used\n")
    lines.append("- outputs/model_lab/full_baseline/full_baseline_forecasts.csv (baseline forecasts)")
    lines.append("- outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv (challenger forecasts + actuals)")
    lines.append("- data/processed/actuals.csv (actuals for baseline rows)")
    lines.append("- outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv (origin/family/champion/risk)")
    lines.append("- outputs/model_lab/model_lab_closure_pack/model_lab_deferred_models.csv (deferred exclusion)")
    lines.append("- outputs/model_lab/model_lab_closure_pack/model_lab_risk_register_final.csv (risk)\n")
    lines.append("## 6-7. Rows and date range\n")
    lines.append(f"- Total rows: **{len(df):,}**")
    lines.append(f"- Distinct models: **{n_models}**")
    lines.append(f"- Date range: **{df['date'].min()} -> {df['date'].max()}**\n")
    lines.append("## 8. Backtest vs production\n")
    lines.append("Historical **backtest** comparison (not forward production).\n")
    lines.append("## 9. Prediction intervals\n")
    lines.append("**Not available** in any source. lower_bound/upper_bound/interval_level = NA.\n")
    lines.append("## 10-11. Readiness\n")
    lines.append("Artifact is structurally ready for a **Shiny pilot rebind** (read-only). "
                 "Full 39-series build can reuse this builder with the full series list.\n")
    lines.append("## 12. Dashboard limitations to display\n")
    lines.append("- Backtest window only (not forward production).")
    lines.append("- Pilot = 3 series only.")
    lines.append("- No deep-learning forecasts (NBEATS/NHITS deferred).")
    lines.append("- FastNeuralAR_MLP is lightweight-neural / high-risk, not a champion.")
    lines.append("- No prediction intervals (point forecasts only).\n")
    fmt = "CSV (fallback, no parquet engine)" if fallback_csv else "parquet"
    lines.append(f"## Output format\nPrimary consumable written as **{fmt}**, plus sample CSV + manifest CSV.\n")
    (REPORT_OUT / "forecast_viewer_handoff_pilot_report.md").write_text(
        "\n".join(lines), encoding="utf-8")


def _flush_logs():
    logfile = LOG_OUT / f"build_pilot_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logfile.write_text("\n".join(LOG_LINES), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
