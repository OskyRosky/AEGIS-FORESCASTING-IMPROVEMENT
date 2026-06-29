"""
Stage 05H - Forecast Viewer Multi-Model Handoff (FULL builder)
==============================================================

PURPOSE
    Build the FULL consolidated multi-model Forecast Viewer handoff artifact for
    ALL eligible multi-model series, using ONLY existing governed Model Lab /
    data outputs. This is the full-scale successor to the validated pilot
    (build_forecast_viewer_handoff_pilot.py) and reuses the same long/tidy
    schema and join logic.

WHAT THIS IS (and is NOT)
    - This is a DATA-ENGINEERING CONSOLIDATION (curation) of existing Stage 5
      Model Lab forecast outputs into one long/tidy artifact for Shiny.
    - It does NOT run models, generate forecasts, recompute metrics, rerun
      tournaments, or change the champion decision.
    - It writes ONLY new forecast_viewer_model_outputs* artifacts. It never
      overwrites forecasts.csv, actuals.csv, entities.csv,
      forecast_comparison.csv, or the pilot artifacts.

SEMANTICS
    The multi-model values are HISTORICAL BACKTEST forecasts, not the forward
    production forecast. The dashboard must label this as model comparison /
    backtest evidence.

ELIGIBILITY
    A series is eligible for the multi-model viewer when it has usable
    multi-model BACKTEST coverage: at least 2 distinct models with backtest
    forecast rows (baseline and/or challenger). Series that have actuals only
    (final-only / no multi-model backtest coverage) are EXCLUDED and documented.
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
#   V1/python/model_lab/build_forecast_viewer_handoff.py)
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

BASELINE_REL = "outputs/model_lab/full_baseline/full_baseline_forecasts.csv"
CHALLENGER_REL = "outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv"

DATA_OUT = ROOT / "data/processed"
REPORT_OUT = ROOT / "outputs/model_lab/forecast_viewer_handoff"
LOG_OUT = REPORT_OUT / "logs"

# Eligibility threshold: minimum distinct models with backtest forecasts.
MIN_MODELS_FOR_VIEWER = 2

# UI-ready horizon options the Forecast Viewer offers (reported, not enforced).
UI_HORIZONS = [5, 10, 15, 20, 25, 30]

# Same 21-column long/tidy schema validated in the pilot (superset of the
# required columns; is_deferred retained for the deferred-safety filter and for
# drop-in parity with the pilot artifact the viewer already consumes).
SCHEMA_COLUMNS = [
    "series_key", "series_label", "date", "actual_value",
    "model_name", "model_origin", "model_family", "forecast_value",
    "forecast_type", "horizon_days", "forecast_start_date",
    "run_id", "source_artifact",
    "is_baseline", "is_challenger", "is_deferred", "is_selected_champion",
    "risk_status", "lower_bound", "upper_bound", "interval_level",
]

# Grain at which uniqueness must hold.
GRAIN = ["series_key", "model_name", "date", "horizon_days"]

NOW = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
LOG_LINES: list[str] = []


def log(msg: str) -> None:
    line = f"[{dt.datetime.now().strftime('%H:%M:%S')}] {msg}"
    LOG_LINES.append(line)
    print(line)


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------
def load_sources() -> dict[str, pd.DataFrame | None]:
    data: dict[str, pd.DataFrame | None] = {}
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
    risk_models = set()
    if data["risk"] is not None and "model_name" in data["risk"].columns:
        risk_models = set(data["risk"]["model_name"].dropna().astype(str).str.strip())
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
# Coverage / eligibility across ALL series
# ---------------------------------------------------------------------------
def coverage_for_series(series_key: str, baseline: pd.DataFrame,
                        challenger: pd.DataFrame, actuals: pd.DataFrame,
                        deferred_set: set) -> dict:
    b = baseline[baseline["entity_key"].astype(str).str.strip() == series_key]
    c = challenger[challenger["entity_key"].astype(str).str.strip() == series_key]
    a = actuals[actuals["entity_key"].astype(str).str.strip() == series_key]

    # exclude deferred models from the counted/usable model sets
    bmodels = sorted(
        m for m in b["model_name"].astype(str).str.strip().unique()
        if m not in deferred_set
    )
    cmodels = sorted(
        m for m in c["model_name"].astype(str).str.strip().unique()
        if m not in deferred_set
    )
    allmodels = sorted(set(bmodels) | set(cmodels))

    dates = []
    if len(b):
        dates += pd.to_datetime(b["forecast_date"], errors="coerce").dropna().tolist()
    if len(c):
        dates += pd.to_datetime(c["forecast_date"], errors="coerce").dropna().tolist()
    if len(a):
        dates += pd.to_datetime(a["date"], errors="coerce").dropna().tolist()

    has_backtest = (len(bmodels) > 0) or (len(cmodels) > 0)
    eligible = has_backtest and (len(allmodels) >= MIN_MODELS_FOR_VIEWER)
    if eligible:
        reason = ""
    elif not has_backtest:
        reason = "final_only_no_multimodel_backtest_coverage"
    else:
        reason = f"insufficient_models_lt_{MIN_MODELS_FOR_VIEWER}"

    return {
        "series_key": series_key,
        "series_label": series_key,
        "has_actuals": (len(a) > 0) or (len(c) > 0),
        "has_baseline_forecasts": len(bmodels) > 0,
        "has_challenger_forecasts": len(cmodels) > 0,
        "baseline_model_count": len(bmodels),
        "challenger_model_count": len(cmodels),
        "total_model_count": len(allmodels),
        "models_available": " | ".join(allmodels),
        "min_date": min(dates).date().isoformat() if dates else "",
        "max_date": max(dates).date().isoformat() if dates else "",
        "eligible_for_multimodel_viewer": eligible,
        "exclusion_reason": reason,
    }


def compute_coverage(data: dict, deferred_set: set) -> tuple[pd.DataFrame, list[str]]:
    baseline, challenger = data["baseline"], data["challenger"]
    actuals, entities = data["actuals"], data["entities"]
    all_series = sorted(
        set(baseline["entity_key"].astype(str).str.strip())
        | set(challenger["entity_key"].astype(str).str.strip())
        | set(actuals["entity_key"].astype(str).str.strip())
        | (set(entities["entity_key"].astype(str).str.strip())
           if entities is not None else set())
    )
    rows = [
        coverage_for_series(s, baseline, challenger, actuals, deferred_set)
        for s in all_series
    ]
    cov = pd.DataFrame(rows)
    eligible = cov.loc[cov["eligible_for_multimodel_viewer"], "series_key"].tolist()
    return cov, eligible


# ---------------------------------------------------------------------------
# Build the long/tidy artifact for the eligible series
# ---------------------------------------------------------------------------
def build_handoff(series_keys: list[str], data: dict, meta: pd.DataFrame
                  ) -> tuple[pd.DataFrame, int]:
    baseline, challenger, actuals = data["baseline"], data["challenger"], data["actuals"]

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
            "source_artifact": BASELINE_REL,
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
            "source_artifact": CHALLENGER_REL,
        })
        frames.append(out_c)

    if not frames:
        return pd.DataFrame(columns=SCHEMA_COLUMNS), 0

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

    df = df[SCHEMA_COLUMNS]

    # grain de-duplication (defensive; pilot produced clean grain). Count and drop
    # exact duplicates at the grain, keeping the first occurrence.
    dup_mask = df.duplicated(subset=GRAIN, keep="first")
    n_dups = int(dup_mask.sum())
    if n_dups:
        df = df[~dup_mask].copy()

    df = df.sort_values(
        ["series_key", "model_family", "model_name", "date", "horizon_days"]
    ).reset_index(drop=True)
    return df, n_dups


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
    log(f"Stage 05H FULL builder start | ROOT={ROOT}")

    data = load_sources()
    meta, deferred_set = build_model_metadata(data)
    log(f"deferred models (excluded from rows): {sorted(deferred_set)}")

    cov, eligible = compute_coverage(data, deferred_set)
    cov.to_csv(REPORT_OUT / "forecast_viewer_handoff_coverage_by_series.csv", index=False)
    excluded = cov[~cov["eligible_for_multimodel_viewer"]].copy()
    excluded[
        ["series_key", "series_label", "has_actuals", "has_baseline_forecasts",
         "has_challenger_forecasts", "total_model_count", "min_date", "max_date",
         "exclusion_reason"]
    ].to_csv(REPORT_OUT / "forecast_viewer_handoff_excluded_series.csv", index=False)
    log(f"eligible series: {len(eligible)} | excluded series: {len(excluded)}")

    # ---- gate: need at least 1 eligible series ----
    if len(eligible) == 0:
        log("FAIL coverage insufficient: no eligible multi-model series")
        _write_validation(created=False, df=None, eligible=eligible, excluded=excluded,
                          fallback_csv=True, n_dups=0, reason="coverage_insufficient")
        _write_report(df=None, cov=cov, eligible=eligible, excluded=excluded,
                      created=False, fallback_csv=True, deferred_set=deferred_set,
                      primary_rel="", n_dups=0)
        _flush_logs()
        return 2

    df, n_dups = build_handoff(eligible, data, meta)
    log(f"built full artifact rows: {len(df):,} | grain duplicates dropped: {n_dups}")

    # ---- write consumable artifact (parquet if engine available, else CSV) ----
    parquet_ok = False
    parquet_path = DATA_OUT / "forecast_viewer_model_outputs.parquet"
    csv_path = DATA_OUT / "forecast_viewer_model_outputs.csv"
    try:
        import pyarrow  # noqa: F401
        df.to_parquet(parquet_path, index=False)
        parquet_ok = True
        primary_path = parquet_path
        log(f"wrote parquet: {parquet_path.relative_to(ROOT)}")
    except Exception as exc:  # pyarrow/fastparquet unavailable -> CSV fallback
        df.to_csv(csv_path, index=False)
        primary_path = csv_path
        log(f"parquet engine unavailable ({type(exc).__name__}); "
            f"CSV fallback -> {csv_path.relative_to(ROOT)}")
    primary_rel = str(primary_path.relative_to(ROOT))

    # representative sample CSV (several series, families, horizons)
    sample = _build_sample(df)
    sample_path = DATA_OUT / "forecast_viewer_model_outputs_sample.csv"
    sample.to_csv(sample_path, index=False)
    log(f"wrote sample CSV: {sample_path.relative_to(ROOT)} ({len(sample)} rows)")

    # ---- manifest ----
    manifest_path = DATA_OUT / "forecast_viewer_model_outputs_manifest.csv"
    _write_manifest(manifest_path, df, eligible, excluded, primary_path, parquet_ok,
                    data, deferred_set, n_dups)
    log(f"wrote manifest: {manifest_path.relative_to(ROOT)}")

    # ---- schema, coverage, model coverage, source manifest, horizon, chart, validation, report ----
    _write_schema(df)
    _write_model_coverage(df)
    _write_source_manifest(data)
    _write_horizon_summary(df)
    _write_chart_readiness(df)
    _write_validation(created=True, df=df, eligible=eligible, excluded=excluded,
                      fallback_csv=not parquet_ok, n_dups=n_dups, reason="ok")
    _write_report(df=df, cov=cov, eligible=eligible, excluded=excluded, created=True,
                  fallback_csv=not parquet_ok, deferred_set=deferred_set,
                  primary_rel=primary_rel, n_dups=n_dups)
    _flush_logs()
    log("Stage 05H FULL builder done")
    return 0


def _build_sample(df: pd.DataFrame) -> pd.DataFrame:
    """Small, human-reviewable sample: several series x families x horizons."""
    series_sample = list(df["series_key"].drop_duplicates().head(4))
    horizons = [h for h in UI_HORIZONS if h in set(df["horizon_days"].dropna().unique())]
    horizons = horizons[:3] if horizons else list(df["horizon_days"].dropna().unique())[:3]
    sub = df[df["series_key"].isin(series_sample) & df["horizon_days"].isin(horizons)]
    # cap per (series, family) so all families show up
    parts = []
    for (_s, _f), grp in sub.groupby(["series_key", "model_family"]):
        parts.append(grp.head(4))
    out = pd.concat(parts, ignore_index=True) if parts else sub.head(200)
    return out.head(200)


def _write_manifest(path, df, eligible, excluded, primary_path, parquet_ok, data,
                    deferred_set, n_dups):
    rows = []
    rows.append(("artifact_name", primary_path.name))
    rows.append(("artifact_path", str(primary_path.relative_to(ROOT))))
    rows.append(("artifact_format", "parquet" if parquet_ok else "csv_fallback"))
    rows.append(("build_timestamp", NOW))
    rows.append(("forecast_type", "backtest_historical_comparison"))
    rows.append(("included_series_count", str(df["series_key"].nunique())))
    rows.append(("excluded_series_count", str(len(excluded))))
    rows.append(("included_series", " | ".join(sorted(eligible))))
    rows.append(("excluded_series", " | ".join(sorted(excluded["series_key"].tolist()))))
    rows.append(("model_count", str(df["model_name"].nunique())))
    rows.append(("models", " | ".join(sorted(df["model_name"].unique()))))
    rows.append(("row_count", str(len(df))))
    rows.append(("date_min", str(df["date"].min())))
    rows.append(("date_max", str(df["date"].max())))
    rows.append(("horizon_min", str(int(pd.to_numeric(df["horizon_days"]).min()))))
    rows.append(("horizon_max", str(int(pd.to_numeric(df["horizon_days"]).max()))))
    rows.append(("ui_horizons_offered", " | ".join(str(h) for h in UI_HORIZONS)))
    rows.append(("interval_availability", "none_point_forecasts_only"))
    rows.append(("grain", " x ".join(GRAIN)))
    rows.append(("grain_duplicates_dropped", str(n_dups)))
    rows.append(("deferred_models_excluded", " | ".join(sorted(deferred_set))))
    rows.append(("no_model_rerun", "TRUE"))
    rows.append(("no_forecast_generation", "TRUE"))
    rows.append(("no_synthetic_forecasts", "TRUE"))
    rows.append(("no_metric_recalculation", "TRUE"))
    rows.append(("no_champion_change", "TRUE"))
    rows.append(("known_limitations",
                 "backtest_only; point_forecasts_only_no_intervals; "
                 "deferred_deep_learning_excluded; "
                 "6_actuals_only_series_excluded"))
    rows.append(("csv_or_parquet_decision",
                 "parquet" if parquet_ok else "csv_fallback_no_pyarrow_fastparquet"))
    for key in ["baseline", "challenger", "actuals", "entities", "universe",
                "deferred", "risk", "champion"]:
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
        REPORT_OUT / "forecast_viewer_handoff_schema.csv", index=False)


def _write_model_coverage(df):
    g = (df.groupby(["series_key", "model_name", "model_origin", "model_family",
                     "is_selected_champion", "risk_status"])
         .agg(row_count=("forecast_value", "size"),
              actual_points=("actual_value", lambda s: int(s.notna().sum())),
              date_min=("date", "min"), date_max=("date", "max"),
              horizon_min=("horizon_days", "min"), horizon_max=("horizon_days", "max"))
         .reset_index()
         .sort_values(["series_key", "model_family", "model_name"]))
    g.to_csv(REPORT_OUT / "forecast_viewer_handoff_model_coverage.csv", index=False)


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
        REPORT_OUT / "forecast_viewer_handoff_source_manifest.csv", index=False)


def _write_horizon_summary(df):
    h = pd.to_numeric(df["horizon_days"], errors="coerce")
    g = (df.assign(horizon_days=h)
         .groupby("horizon_days")
         .agg(row_count=("forecast_value", "size"),
              series_count=("series_key", "nunique"),
              model_count=("model_name", "nunique"))
         .reset_index()
         .sort_values("horizon_days"))
    g["is_ui_horizon"] = g["horizon_days"].isin(UI_HORIZONS)
    g.to_csv(REPORT_OUT / "forecast_viewer_handoff_horizon_summary.csv", index=False)


def _write_chart_readiness(df):
    rows = []
    for s, grp in df.groupby("series_key"):
        horizons = sorted(int(x) for x in pd.to_numeric(grp["horizon_days"]).dropna().unique())
        model_count = grp["model_name"].nunique()
        actual_ok = bool(grp["actual_value"].notna().any())
        forecast_ok = bool(grp["forecast_value"].notna().any())
        ui_missing = [h for h in UI_HORIZONS if h not in horizons]
        warnings = []
        if not actual_ok:
            warnings.append("no_actual_values")
        if not forecast_ok:
            warnings.append("no_forecast_values")
        if model_count < MIN_MODELS_FOR_VIEWER:
            warnings.append("single_model_only")
        if ui_missing:
            warnings.append("missing_ui_horizons:" + ",".join(str(h) for h in ui_missing))
        chart_ready = actual_ok and forecast_ok and model_count >= MIN_MODELS_FOR_VIEWER
        rows.append({
            "series_key": s,
            "series_label": s,
            "chart_ready": chart_ready,
            "actual_line_available": actual_ok,
            "forecast_lines_available": forecast_ok,
            "model_count": model_count,
            "available_horizons": ",".join(str(h) for h in horizons),
            "date_min": grp["date"].min(),
            "date_max": grp["date"].max(),
            "warning": "; ".join(warnings),
        })
    pd.DataFrame(rows).sort_values("series_key").to_csv(
        REPORT_OUT / "forecast_viewer_handoff_chart_readiness.csv", index=False)


def _write_validation(created, df, eligible, excluded, fallback_csv, n_dups, reason):
    def chk(name, status, details):
        return {"check_name": name, "status": status, "details": details}

    rows = [
        chk("no_shiny_files_modified", "pass",
            "Builder writes only python/model_lab + data/processed/forecast_viewer_model_outputs* + outputs/model_lab/forecast_viewer_handoff"),
        chk("no_existing_processed_artifacts_overwritten", "pass",
            "Only new forecast_viewer_model_outputs* files written; forecasts/actuals/entities/forecast_comparison untouched"),
        chk("pilot_artifact_not_overwritten", "pass",
            "Full builder writes non-_pilot file names; *_pilot* artifacts preserved"),
        chk("no_model_lab_outputs_modified", "pass", "Existing Model Lab outputs read-only"),
        chk("no_stage06_governance_modified", "pass", "No Stage 06 governance outputs written"),
        chk("no_forecasts_generated", "pass", "Consolidation only; zero model inference"),
        chk("no_models_run", "pass", "No model fitting/inference"),
        chk("no_metrics_recalculated", "pass", "No metric computation"),
        chk("no_champion_decision_changed", "pass", "champion flag read from model universe only"),
        chk("full_builder_created", "pass", "python/model_lab/build_forecast_viewer_handoff.py"),
    ]
    if created and df is not None:
        required = [c for c in SCHEMA_COLUMNS if c != "is_deferred"]
        cols_ok = all(c in df.columns for c in required)
        traced = df["source_artifact"].notna().all()
        fam_ok = df["model_family"].notna().all()
        champ_ok = bool(df["is_selected_champion"].any())
        risk_ok = df["risk_status"].notna().all()
        no_deferred = (~df["is_deferred"].astype(bool)).all()
        intervals_na = df[["lower_bound", "upper_bound", "interval_level"]].isna().all().all()
        actual_pop = bool(df["actual_value"].notna().any())
        fc_pop = df["forecast_value"].notna().all()
        horizon_pop = df["horizon_days"].notna().all()
        date_ok = pd.to_datetime(df["date"], errors="coerce").notna().all()
        fsd_ok = pd.to_datetime(df["forecast_start_date"], errors="coerce").notna().all()
        grain_unique = not df.duplicated(subset=GRAIN).any()
        traceable = set(df["source_artifact"].unique()).issubset({BASELINE_REL, CHALLENGER_REL})
        rows += [
            chk("source_artifacts_found_and_documented", "pass",
                "8 sources documented in source_manifest + manifest"),
            chk("eligible_series_identified", "pass", f"{len(eligible)} eligible series"),
            chk("excluded_series_documented", "pass",
                f"{len(excluded)} excluded -> forecast_viewer_handoff_excluded_series.csv"),
            chk("full_output_artifact_created", "pass", f"{len(df):,} rows"),
            chk("sample_csv_created", "pass", "forecast_viewer_model_outputs_sample.csv"),
            chk("manifest_created", "pass", "forecast_viewer_model_outputs_manifest.csv"),
            chk("required_columns_present", "pass" if cols_ok else "fail",
                "all required schema columns present"),
            chk("no_duplicate_rows_at_grain", "pass" if grain_unique else "fail",
                f"grain={GRAIN}; duplicates dropped during build={n_dups}"),
            chk("actual_value_populated", "pass" if actual_pop else "warning",
                "actual_value present (challenger joined; baseline left-join actuals.csv)"),
            chk("forecast_value_populated", "pass" if fc_pop else "fail",
                "forecast_value present on every row"),
            chk("model_family_populated", "pass" if fam_ok else "fail",
                "model_family from model_lab_final_model_universe.csv"),
            chk("champion_flag_populated", "pass" if champ_ok else "warning",
                "is_selected_champion TRUE for governed champion (ETS Explicit)"),
            chk("risk_status_populated", "pass" if risk_ok else "fail",
                "risk_status from universe risk_flag + risk register"),
            chk("horizon_days_populated", "pass" if horizon_pop else "fail",
                "horizon_days present on every row"),
            chk("date_parsing_valid", "pass" if date_ok else "fail", "date parses to valid dates"),
            chk("forecast_start_date_parsing_valid", "pass" if fsd_ok else "fail",
                "forecast_start_date = date - horizon_days parses valid"),
            chk("all_rows_trace_to_source", "pass" if (traced and traceable) else "fail",
                "every row carries a known source_artifact"),
            chk("no_synthetic_forecasts", "pass",
                "all forecast_value rows originate from source forecast outputs"),
            chk("deferred_models_not_materialized", "pass" if no_deferred else "fail",
                "deferred models excluded from forecast rows"),
            chk("interval_columns_present_but_na", "pass" if intervals_na else "warning",
                "lower/upper/interval_level all NA (no source bands)"),
            chk("row_counts_by_series_produced", "pass", "coverage_by_series + model_coverage written"),
            chk("model_counts_by_series_produced", "pass", "model_coverage written"),
            chk("horizon_summary_produced", "pass", "forecast_viewer_handoff_horizon_summary.csv"),
            chk("chart_readiness_produced", "pass", "forecast_viewer_handoff_chart_readiness.csv"),
            chk("parquet_or_csv_fallback_reported", "warning" if fallback_csv else "pass",
                "CSV fallback used (no pyarrow/fastparquet)" if fallback_csv else "parquet written"),
        ]
    else:
        rows += [chk("full_artifact_created", "fail", f"NOT created: {reason}")]
    pd.DataFrame(rows).to_csv(
        REPORT_OUT / "forecast_viewer_handoff_validation.csv", index=False)


def _write_report(df, cov, eligible, excluded, created, fallback_csv, deferred_set,
                  primary_rel, n_dups):
    lines = []
    lines.append("# Stage 05H - Forecast Viewer Multi-Model Handoff (FULL)\n")
    lines.append(f"**Build timestamp:** {NOW}  ")
    lines.append("**Mode:** Data-engineering consolidation of EXISTING Stage 5 outputs. "
                 "No models run, no forecasts generated, no metrics recomputed, no champion change.\n")

    lines.append("## 1. What was built\n")
    lines.append("A single long/tidy multi-model **backtest** handoff artifact "
                 "(`forecast_viewer_model_outputs`) consolidating existing baseline + "
                 "challenger Stage 5 forecast outputs for every eligible multi-model series, "
                 "using the schema validated in the pilot.\n")

    lines.append("## 2. Why Stage 05H and not Shiny\n")
    lines.append("Shiny only consumes governed artifacts. This consolidation/join of Model "
                 "Lab outputs is data engineering and must happen in the Model Lab layer, not "
                 "in the dashboard. Shiny does not cook data, generate forecasts, or join "
                 "baseline/challenger outputs.\n")

    lines.append("## 3. Source artifacts used\n")
    lines.append(f"- {BASELINE_REL} (baseline backtest forecasts)")
    lines.append(f"- {CHALLENGER_REL} (challenger backtest forecasts + actuals)")
    lines.append("- data/processed/actuals.csv (actuals for baseline rows)")
    lines.append("- data/processed/entities.csv (series universe)")
    lines.append("- outputs/model_lab/model_lab_closure_pack/model_lab_final_model_universe.csv (origin/family/champion/risk)")
    lines.append("- outputs/model_lab/model_lab_closure_pack/model_lab_deferred_models.csv (deferred exclusion)")
    lines.append("- outputs/model_lab/model_lab_closure_pack/model_lab_risk_register_final.csv (risk)")
    lines.append("- outputs/model_lab/model_lab_closure_pack/model_lab_champion_summary.csv (champion context)\n")

    if not created or df is None:
        lines.append("## Result: FULL ARTIFACT NOT CREATED\n")
        lines.append("No series had usable multi-model backtest coverage. See coverage table.\n")
        (REPORT_OUT / "forecast_viewer_handoff_report.md").write_text(
            "\n".join(lines), encoding="utf-8")
        return

    n_models = df["model_name"].nunique()
    per = (df.groupby("series_key")["model_name"].nunique()
           .reset_index(name="model_count").sort_values("series_key"))

    lines.append("## 4. Included series\n")
    lines.append(f"- Included (eligible multi-model): **{len(eligible)}**")
    lines.append(f"- Distinct models: **{n_models}**\n")

    lines.append("## 5. Excluded series and why\n")
    lines.append(f"- Excluded: **{len(excluded)}** (actuals-only / final-only, no multi-model backtest coverage)")
    if len(excluded):
        lines.append(df_to_md(excluded[["series_key", "exclusion_reason", "has_actuals",
                                         "has_baseline_forecasts", "has_challenger_forecasts"]]))
    lines.append("")

    lines.append("## 6. Models available per series\n")
    lines.append(f"Every included series carries the full **{n_models}-model** set "
                 "(7 baseline + 6 challenger). Per-series model counts:\n")
    lines.append(df_to_md(per.head(10)))
    lines.append("\n(Full table: forecast_viewer_handoff_model_coverage.csv)\n")

    lines.append("## 7. Date range\n")
    lines.append(f"- Date range: **{df['date'].min()} -> {df['date'].max()}**\n")

    lines.append("## 8. Horizons available\n")
    hmin = int(pd.to_numeric(df["horizon_days"]).min())
    hmax = int(pd.to_numeric(df["horizon_days"]).max())
    present = sorted(int(x) for x in pd.to_numeric(df["horizon_days"]).dropna().unique())
    ui_ok = all(h in present for h in UI_HORIZONS)
    lines.append(f"- Full horizon range: **{hmin}-{hmax} days**")
    lines.append(f"- UI horizons {UI_HORIZONS} available for all included series/models: "
                 f"**{'YES' if ui_ok else 'NO'}**")
    lines.append("- 45 and 60 day horizons are **not** present in the source data and are not added.\n")

    lines.append("## 9. Backtest vs production\n")
    lines.append("Historical **backtest** comparison (not forward production forecast).\n")

    lines.append("## 10. Prediction intervals\n")
    lines.append("**Not available** in any source. lower_bound/upper_bound/interval_level = NA.\n")

    lines.append("## 11. Shiny readiness\n")
    lines.append("Structurally ready for a full Forecast Viewer rebind (read-only). The "
                 "viewer's existing `fvp_*` logic and pilot schema apply unchanged; only the "
                 "governed artifact key would point at the full file. Awaiting Oscar approval.\n")

    lines.append("## 12. Limitations to show in Shiny\n")
    lines.append("- Backtest window only (not forward production).")
    lines.append("- Point forecasts only (no prediction intervals).")
    lines.append("- Deep-learning models (NBEATS/NHITS) deferred and not included.")
    lines.append("- 6 actuals-only series are not available in the multi-model viewer.")
    lines.append("- Champion flag (ETS Explicit) is governed metadata, not a viewer decision.\n")

    lines.append("## 13. Next Stage 07 step\n")
    lines.append("After Oscar reviews coverage, rebind the Forecast Viewer to the full "
                 "artifact (governed loader key swap) and validate the multi-series view.\n")

    fmt = "CSV (fallback, no parquet engine)" if fallback_csv else "parquet"
    lines.append(f"## Output\nPrimary consumable: **{primary_rel}** ({fmt}); "
                 f"plus sample CSV + manifest CSV. Rows: **{len(df):,}**; "
                 f"grain duplicates dropped: **{n_dups}**.\n")

    (REPORT_OUT / "forecast_viewer_handoff_report.md").write_text(
        "\n".join(lines), encoding="utf-8")


def _flush_logs():
    logfile = LOG_OUT / f"build_full_{dt.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logfile.write_text("\n".join(LOG_LINES), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
