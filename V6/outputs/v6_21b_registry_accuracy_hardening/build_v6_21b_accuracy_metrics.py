"""V6.21B | Precompute Accuracy metrics OUTSIDE Shiny.

This is a derived aggregation over already-governed forecast/actual pairs from
the V6.17 productive Viewer artifact. It trains nothing, forecasts nothing and
queries no database.

Correctness constraints (see V6.21B facts F4, F7, F8):

* Grouping key is metric + scenario + granularity + series_key + model_name +
  horizon_days. The route dimensions are grouping dimensions, not passengers:
  197 of the 391 distinct series_key values appear in more than one route and
  are different time series.
* forecast_start_date is NOT part of the key. Aggregating across rolling
  origins is the existing intended semantic and n_points counts them.
* extraction_run_id is NOT part of the key. It is carried as metadata, and the
  builder stops if any group is found to mix runs.

Formulas reproduce helpers.R acc_compute (lines 1184-1236) exactly.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO_ROOT = Path(__file__).resolve().parents[3]
V6_ROOT = REPO_ROOT / "V6"
SOURCE_PARQUET = (
    V6_ROOT
    / "outputs"
    / "v6_17_full_multimetric_productive_artifact_generation"
    / "forecast_viewer_model_outputs_v2_full.parquet"
)
OUT_DIR = V6_ROOT / "outputs" / "v6_21b_registry_accuracy_hardening"
OUT_PARQUET = OUT_DIR / "v6_21b_accuracy_metrics.parquet"
OUT_SUMMARY = OUT_DIR / "v6_21b_accuracy_metrics_summary.csv"

# Route dimensions first: these define which physical series a row belongs to.
ROUTE_DIMS = ["metric", "scenario", "granularity"]
GROUP_KEY = ROUTE_DIMS + ["series_key", "model_name", "horizon_days"]

# Optional extra route dimensions, included only when actually present.
OPTIONAL_DIMS = ["db_type", "demand_nature", "route_id"]

# Carried as group attributes; verified constant within each group.
ATTRIBUTES = [
    "series_label",
    "model_origin",
    "model_family",
    "is_baseline",
    "is_challenger",
    "is_deferred",
    "is_selected_champion",
    "risk_status",
    "extraction_run_id",
]

METRIC_COLUMNS = [
    "MAE",
    "RMSE",
    "sMAPE",
    "wMAPE",
    "signed_bias",
    "abs_bias_severity",
    "error_variability",
]


def compute_metrics(actual: np.ndarray, forecast: np.ndarray) -> dict:
    """Reproduce helpers.R acc_compute for one group of finite pairs."""
    error = forecast - actual
    abs_error = np.abs(error)

    denom = (np.abs(actual) + np.abs(forecast)) / 2.0
    with np.errstate(divide="ignore", invalid="ignore"):
        smape_terms = np.where(denom == 0, np.nan, abs_error / denom)
    smape = np.nan if bool(np.all(np.isnan(smape_terms))) else float(np.nanmean(smape_terms)) * 100.0

    sum_abs_actual = float(np.sum(np.abs(actual)))
    wmape = np.nan if sum_abs_actual == 0 else float(np.sum(abs_error)) / sum_abs_actual * 100.0

    # R stats::sd uses the n-1 denominator; a single point yields exactly 0.
    variability = float(np.std(error, ddof=1)) if error.size > 1 else 0.0

    return {
        "n_points": int(error.size),
        "MAE": float(np.mean(abs_error)),
        "RMSE": float(np.sqrt(np.mean(error**2))),
        "sMAPE": smape,
        "wMAPE": wmape,
        "signed_bias": float(np.mean(error)),
        "abs_bias_severity": float(abs(np.mean(error))),
        "error_variability": variability,
    }


def build(source: Path = SOURCE_PARQUET) -> tuple[pd.DataFrame, int, list[str]]:
    frame = pd.read_parquet(source)

    group_key = list(GROUP_KEY)
    for column in OPTIONAL_DIMS:
        if column in frame.columns:
            group_key.insert(len(ROUTE_DIMS), column)

    frame["actual_value"] = pd.to_numeric(frame["actual_value"], errors="coerce")
    frame["forecast_value"] = pd.to_numeric(frame["forecast_value"], errors="coerce")

    before = len(frame)
    finite = np.isfinite(frame["actual_value"].to_numpy(dtype=float)) & np.isfinite(
        frame["forecast_value"].to_numpy(dtype=float)
    )
    frame = frame.loc[finite].copy()
    dropped = before - len(frame)

    present_attributes = [c for c in ATTRIBUTES if c in frame.columns]
    grouped = frame.groupby(group_key, sort=False, observed=True)

    if "extraction_run_id" in frame.columns:
        offenders = int((grouped["extraction_run_id"].nunique() > 1).sum())
        if offenders:
            raise SystemExit(
                f"STOP: {offenders} groups mix extraction_run_id values. "
                "Aggregation is not safe; report before proceeding."
            )

    records = []
    for keys, chunk in grouped:
        row = dict(zip(group_key, keys if isinstance(keys, tuple) else (keys,)))
        row.update(
            compute_metrics(
                chunk["actual_value"].to_numpy(dtype=float),
                chunk["forecast_value"].to_numpy(dtype=float),
            )
        )
        for attribute in present_attributes:
            row[attribute] = chunk[attribute].iloc[0]
        records.append(row)

    result = pd.DataFrame.from_records(records)

    # Route-qualified display key so the heatmap, table and summary cards never
    # blend two different series that happen to share a series_key.
    result["case_label"] = (
        result["series_key"].astype(str)
        + " \u00b7 "
        + result["metric"].astype(str)
        + " / "
        + result["scenario"].astype(str)
        + " / "
        + result["granularity"].astype(str)
    )
    result["horizon"] = result["horizon_days"]
    return result, dropped, group_key


def summarise(result: pd.DataFrame, dropped: int, group_key: list[str]) -> pd.DataFrame:
    rows: list[dict] = []

    def add(measure: str, value: object, note: str = "") -> None:
        rows.append({"measure": measure, "value": value, "notes": note})

    case_cols = ROUTE_DIMS + ["series_key"]
    add("artifact_rows", len(result), "One row per grouping key.")
    add("grouping_key", " + ".join(group_key), "Route dimensions are grouping dimensions.")
    add("distinct_route_key_cases", result[case_cols].drop_duplicates().shape[0], "Expected 596.")
    add("distinct_series_key_entities", result["series_key"].nunique(), "Expected 391.")
    add("distinct_models", result["model_name"].nunique(), "Expected 15.")
    add("horizons_covered", "|".join(str(h) for h in sorted(result["horizon_days"].unique())), "")
    add("dropped_nonfinite_rows", dropped, "Removed before grouping, exactly as acc_compute does.")

    for metric in METRIC_COLUMNS:
        add(f"na_count_{metric}", int(result[metric].isna().sum()), "")

    if "extraction_run_id" in result.columns:
        for run, chunk in result.groupby("extraction_run_id"):
            prefix = f"n_points[{run}]"
            add(f"{prefix}_groups", len(chunk), "")
            add(f"{prefix}_min", int(chunk["n_points"].min()), "")
            add(f"{prefix}_median", float(chunk["n_points"].median()), "")
            add(f"{prefix}_max", int(chunk["n_points"].max()), "")
            add(
                f"{prefix}_routes",
                chunk[ROUTE_DIMS].drop_duplicates().shape[0],
                "n_points is NOT comparable across runs; see the ranking caveat.",
            )

    return pd.DataFrame(rows)


def main() -> int:
    if not SOURCE_PARQUET.exists():
        raise SystemExit(f"Source artifact missing: {SOURCE_PARQUET}")
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    result, dropped, group_key = build()
    result.to_parquet(OUT_PARQUET, index=False)
    summarise(result, dropped, group_key).to_csv(OUT_SUMMARY, index=False)

    print(f"rows={len(result)}")
    print(f"cases={result[ROUTE_DIMS + ['series_key']].drop_duplicates().shape[0]}")
    print(f"entities={result['series_key'].nunique()}")
    print(f"models={result['model_name'].nunique()}")
    print(f"group_key={'+'.join(group_key)}")
    print(f"dropped_nonfinite={dropped}")
    print(f"parquet={OUT_PARQUET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
