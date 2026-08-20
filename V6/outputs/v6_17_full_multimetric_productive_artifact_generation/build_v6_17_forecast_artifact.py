"""Assemble the full locally available V6.17 forward Forecast artifact."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd


THIS_FILE = Path(__file__).resolve()
OUTPUT_DIR = THIS_FILE.parent
V6_ROOT = THIS_FILE.parents[2]
R6_VIEWER = (
    V6_ROOT
    / "outputs"
    / "v6_0f_r6_phase1_governed_extraction"
    / "r6_phase1_viewer_hdd.csv"
)
R6_FORECAST_HDD = (
    V6_ROOT
    / "outputs"
    / "v6_0f_r6_phase1_governed_extraction"
    / "r6_phase1_forecast_hdd.csv"
)
R6_FORECAST_SSD = (
    V6_ROOT
    / "outputs"
    / "v6_0f_r6_phase1_governed_extraction"
    / "r6_phase1_forecast_ssd_phoenix.csv"
)
OUTPUT_PATH = OUTPUT_DIR / "forecast_forward_outputs_v6_17_full.csv"
SUMMARY_PATH = OUTPUT_DIR / "forecast_forward_outputs_v6_17_summary.json"

OUTPUT_COLUMNS = [
    "metric",
    "scenario",
    "granularity",
    "series_key",
    "date",
    "record_type",
    "value",
    "model_name",
    "forecast_version",
    "has_actuals",
    "forecast_only",
    "value_type",
    "source_table",
    "source_artifact",
    "extraction_run_id",
]


def latest_rows(
    frame: pd.DataFrame, grain: list[str], version_column: str
) -> pd.DataFrame:
    frame = frame.copy()
    frame[version_column] = pd.to_datetime(
        frame[version_column], format="mixed", errors="raise"
    )
    latest = frame.groupby(grain)[version_column].transform("max")
    return frame[frame[version_column].eq(latest)].copy()


def actual_rows() -> tuple[pd.DataFrame, int]:
    viewer = pd.read_csv(R6_VIEWER)
    actual = viewer[
        viewer["series_type"].astype(str).str.casefold().eq("actual")
    ].copy()
    actual["date"] = pd.to_datetime(actual["date"], format="mixed", errors="raise")
    actual["value"] = pd.to_numeric(actual["value"], errors="raise")
    grain = ["metric", "scenario_ui_label", "granularity", "key", "date"]
    revisions = actual.groupby(grain, as_index=False).agg(
        value=("value", "median"),
        value_min=("value", "min"),
        value_max=("value", "max"),
        source_table=("source_table", "first"),
        extraction_run_id=("extraction_run_id", "first"),
    )
    conflicts = int(
        (
            ~np.isclose(
                revisions["value_min"],
                revisions["value_max"],
                rtol=0,
                atol=1e-9,
            )
        ).sum()
    )
    lineage = actual["extraction_run_id"].dropna().astype(str).unique()
    if len(lineage) != 1:
        raise ValueError(f"Expected one Viewer extraction_run_id, found {lineage}")
    rows = pd.DataFrame(
        {
            "metric": revisions["metric"],
            "scenario": revisions["scenario_ui_label"],
            "granularity": revisions["granularity"],
            "series_key": revisions["key"],
            "date": revisions["date"].dt.date.astype(str),
            "record_type": "actual",
            "value": revisions["value"],
            "model_name": "",
            "forecast_version": "",
            "has_actuals": True,
            "forecast_only": False,
            "value_type": "Actual",
            "source_table": revisions["source_table"],
            "source_artifact": (
                "V6/outputs/v6_0f_r6_phase1_governed_extraction/"
                "r6_phase1_viewer_hdd.csv"
            ),
            "extraction_run_id": revisions["extraction_run_id"],
        }
    )
    return rows.reindex(columns=OUTPUT_COLUMNS), conflicts


def hdd_forecast_rows() -> pd.DataFrame:
    source = pd.read_csv(R6_FORECAST_HDD)
    grain = ["metric", "scenario_ui_label", "granularity", "key"]
    rows = latest_rows(source, grain, "forecast_version")
    if rows.duplicated(grain + ["forecast_date"]).any():
        raise ValueError("Latest HDD Forecast rows duplicate required date grain")
    return pd.DataFrame(
        {
            "metric": rows["metric"],
            "scenario": rows["scenario_ui_label"],
            "granularity": rows["granularity"],
            "series_key": rows["key"],
            "date": pd.to_datetime(
                rows["forecast_date"], format="mixed", errors="raise"
            ).dt.date.astype(str),
            "record_type": "forecast",
            "value": pd.to_numeric(rows["forecast_value"], errors="raise"),
            "model_name": rows["model_type"].astype(str),
            "forecast_version": rows["forecast_version"].dt.date.astype(str),
            "has_actuals": True,
            "forecast_only": False,
            "value_type": rows["raw_type"].astype(str),
            "source_table": rows["source_table"].astype(str),
            "source_artifact": (
                "V6/outputs/v6_0f_r6_phase1_governed_extraction/"
                "r6_phase1_forecast_hdd.csv"
            ),
            "extraction_run_id": rows["extraction_run_id"].astype(str),
        }
    ).reindex(columns=OUTPUT_COLUMNS)


def ssd_forecast_rows() -> pd.DataFrame:
    source = pd.read_csv(R6_FORECAST_SSD)
    source["granularity"] = "Forest"
    grain = ["metric", "scenario_ui_label", "granularity", "key"]
    rows = latest_rows(source, grain, "forecast_version")
    if rows.duplicated(grain + ["forecast_date"]).any():
        raise ValueError("Latest SSD Forecast rows duplicate required date grain")
    return pd.DataFrame(
        {
            "metric": rows["metric"],
            "scenario": rows["scenario_ui_label"],
            "granularity": rows["granularity"],
            "series_key": rows["key"],
            "date": pd.to_datetime(
                rows["forecast_date"], format="mixed", errors="raise"
            ).dt.date.astype(str),
            "record_type": "forecast",
            "value": pd.to_numeric(rows["forecast_value"], errors="raise"),
            "model_name": "Governed Phoenix source forecast",
            "forecast_version": rows["forecast_version"].dt.date.astype(str),
            "has_actuals": False,
            "forecast_only": True,
            "value_type": rows["value_type"].astype(str),
            "source_table": rows["source_table"].astype(str),
            "source_artifact": (
                "V6/outputs/v6_0f_r6_phase1_governed_extraction/"
                "r6_phase1_forecast_ssd_phoenix.csv"
            ),
            "extraction_run_id": rows["extraction_run_id"].astype(str),
        }
    ).reindex(columns=OUTPUT_COLUMNS)


def main() -> None:
    started = pd.Timestamp.now(tz="UTC")
    actual, conflicts = actual_rows()
    hdd = hdd_forecast_rows()
    ssd = ssd_forecast_rows()
    full = pd.concat([actual, hdd, ssd], ignore_index=True)
    grain = [
        "metric", "scenario", "granularity", "series_key", "date", "record_type"
    ]
    if full.duplicated(grain).any():
        raise ValueError("Full Forecast artifact duplicates required row grain")
    if full[["metric", "scenario", "granularity", "series_key", "date",
             "record_type", "value", "has_actuals", "forecast_only"]].isna().any().any():
        raise ValueError("Full Forecast artifact contains null required values")
    combinations = full[
        ["metric", "scenario", "granularity", "series_key"]
    ].drop_duplicates()
    if len(combinations) != 896:
        raise ValueError(f"Expected 896 Forecast key-combinations, found {len(combinations)}")
    if (full["metric"].eq("SSD - Phoenix") & full["record_type"].eq("actual")).any():
        raise ValueError("SSD-Phoenix actual rows are forbidden")
    full.to_csv(OUTPUT_PATH, index=False)
    summary = {
        "status": "PASS",
        "rows": len(full),
        "actual_rows": int(full["record_type"].eq("actual").sum()),
        "forecast_rows": int(full["record_type"].eq("forecast").sum()),
        "key_combinations": len(combinations),
        "viewer_actual_revision_conflicts_reconciled": conflicts,
        "reconciliation": "median of observed governed revisions at key/date grain",
        "metrics": sorted(full["metric"].unique().tolist()),
        "completed_at": pd.Timestamp.now(tz="UTC").isoformat(),
        "runtime_seconds": round(
            (pd.Timestamp.now(tz="UTC") - started).total_seconds(), 3
        ),
        "models_run": False,
        "tesseract_accessed": False,
        "cpu_iops_fabricated": False,
    }
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
