"""Training-only benchmark denominator utilities.

The official MASE/RMSSE denominators are in-sample lag-1 naive errors computed
from actual observations through each window's train_end_date only.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.paths import PROJECT_ROOT


MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "denominator_reconciliation"
DENOMINATORS_OUTPUT = OUTPUT_DIR / "training_only_denominators.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "denominator_reconciliation_summary.csv"
REPORT_OUTPUT = OUTPUT_DIR / "denominator_reconciliation_report.md"

EPSILON = 1e-6
FORECAST_HORIZON_DAYS = 30

DENOMINATOR_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "training_start_date",
    "train_end_date",
    "training_observations",
    "denominator_observations",
    "mase_denominator_mae_raw",
    "mase_denominator_mae",
    "mase_denominator_floored",
    "rmsse_denominator_mse_raw",
    "rmsse_denominator_mse",
    "rmsse_denominator_floored",
    "created_timestamp",
]
SUMMARY_COLUMNS = [
    "run_id",
    "entities",
    "windows",
    "denominator_rows",
    "epsilon",
    "mase_denominator_floored_rows",
    "rmsse_denominator_floored_rows",
    "min_mase_denominator",
    "median_mase_denominator",
    "mean_mase_denominator",
    "min_rmsse_denominator",
    "median_rmsse_denominator",
    "mean_rmsse_denominator",
    "created_timestamp",
]


def require_file(path: Path) -> None:
    """Fail fast when a required input file is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required denominator input missing: {path}")


def load_actuals(path: Path = EVALUATION_DATASET) -> pd.DataFrame:
    """Load actual observations only."""

    require_file(path)
    actuals = pd.read_csv(path, parse_dates=["date"])
    required = {"entity_key", "date", "value", "record_type"}
    missing = required.difference(actuals.columns)
    if missing:
        raise ValueError(f"evaluation_dataset.csv missing columns: {sorted(missing)}")
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "value"])
    if actuals.duplicated(["entity_key", "date"]).any():
        raise ValueError("Duplicate actual rows found for entity/date.")
    return actuals.sort_values(["entity_key", "date"]).reset_index(drop=True)


def load_windows(path: Path = WINDOWS_INPUT) -> pd.DataFrame:
    """Load valid 30-day backtesting windows."""

    require_file(path)
    windows = pd.read_csv(
        path,
        parse_dates=["train_start_date", "train_end_date", "test_start_date", "test_end_date"],
    )
    required = {
        "entity_key",
        "window_id",
        "train_start_date",
        "train_end_date",
        "forecast_horizon_days",
    }
    missing = required.difference(windows.columns)
    if missing:
        raise ValueError(f"backtesting_windows.csv missing columns: {sorted(missing)}")
    windows = windows[windows["forecast_horizon_days"] == FORECAST_HORIZON_DAYS].copy()
    windows["window_id"] = windows["window_id"].astype(int)
    return windows.sort_values(["entity_key", "window_id"]).reset_index(drop=True)


def _floor(value: float) -> tuple[float, bool]:
    """Apply denominator epsilon floor."""

    if pd.isna(value) or value < EPSILON:
        return EPSILON, True
    return float(value), False


def compute_training_only_denominators(
    windows: pd.DataFrame,
    actuals: pd.DataFrame,
    run_id: str,
    created_timestamp: str,
) -> pd.DataFrame:
    """Compute training-only lag-1 denominators for each entity/window."""

    actuals_by_entity = {
        entity_key: group.sort_values("date").reset_index(drop=True)
        for entity_key, group in actuals.groupby("entity_key", sort=False)
    }
    rows = []
    for _, window in windows.iterrows():
        entity_key = window["entity_key"]
        entity_actuals = actuals_by_entity.get(entity_key)
        if entity_actuals is None:
            training = pd.DataFrame(columns=["date", "value"])
        else:
            training = entity_actuals[
                (entity_actuals["date"] >= window["train_start_date"])
                & (entity_actuals["date"] <= window["train_end_date"])
            ].sort_values("date")

        training_observations = len(training)
        if training_observations < 2:
            denominator_observations = 0
            raw_mae = float("nan")
            raw_mse = float("nan")
        else:
            diffs = training["value"].diff().dropna()
            denominator_observations = len(diffs)
            raw_mae = float(diffs.abs().mean())
            raw_mse = float((diffs**2).mean())

        mase_denominator, mase_floored = _floor(raw_mae)
        rmsse_denominator, rmsse_floored = _floor(raw_mse)
        rows.append(
            {
                "run_id": run_id,
                "entity_key": entity_key,
                "window_id": int(window["window_id"]),
                "training_start_date": window["train_start_date"].date(),
                "train_end_date": window["train_end_date"].date(),
                "training_observations": int(training_observations),
                "denominator_observations": int(denominator_observations),
                "mase_denominator_mae_raw": raw_mae,
                "mase_denominator_mae": mase_denominator,
                "mase_denominator_floored": bool(mase_floored),
                "rmsse_denominator_mse_raw": raw_mse,
                "rmsse_denominator_mse": rmsse_denominator,
                "rmsse_denominator_floored": bool(rmsse_floored),
                "created_timestamp": created_timestamp,
            }
        )
    return pd.DataFrame(rows, columns=DENOMINATOR_COLUMNS)


def denominator_summary(denominators: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    """Create denominator reconciliation summary."""

    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "entities": denominators["entity_key"].nunique(),
                "windows": denominators[["entity_key", "window_id"]].drop_duplicates().shape[0],
                "denominator_rows": len(denominators),
                "epsilon": EPSILON,
                "mase_denominator_floored_rows": int(denominators["mase_denominator_floored"].sum()),
                "rmsse_denominator_floored_rows": int(denominators["rmsse_denominator_floored"].sum()),
                "min_mase_denominator": float(denominators["mase_denominator_mae"].min()),
                "median_mase_denominator": float(denominators["mase_denominator_mae"].median()),
                "mean_mase_denominator": float(denominators["mase_denominator_mae"].mean()),
                "min_rmsse_denominator": float(denominators["rmsse_denominator_mse"].min()),
                "median_rmsse_denominator": float(denominators["rmsse_denominator_mse"].median()),
                "mean_rmsse_denominator": float(denominators["rmsse_denominator_mse"].mean()),
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def write_denominator_outputs(denominators: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    """Write denominator detail and summary outputs."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    denominators.to_csv(DENOMINATORS_OUTPUT, index=False)
    summary = denominator_summary(denominators, run_id, timestamp)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    return summary


def build_and_write_denominators(
    run_id: str | None = None,
    timestamp: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load inputs, compute denominators, and write reconciliation outputs."""

    if run_id is None:
        run_id = f"denominator_reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if timestamp is None:
        timestamp = datetime.now().isoformat(timespec="seconds")
    denominators = compute_training_only_denominators(
        load_windows(), load_actuals(), run_id, timestamp
    )
    summary = write_denominator_outputs(denominators, run_id, timestamp)
    return denominators, summary
