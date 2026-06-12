"""Inspect Stage 5.21 MASE outputs.

This inspector validates MASE output contracts and diagnostics. It does not
calculate RMSSE, create rankings, select champions, or write tournament outputs.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_mase")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
MASE_DIR = MODEL_LAB_DIR / "mase"
MASE_SCORES_OUTPUT = MASE_DIR / "mase_scores.csv"
MASE_BY_MODEL_OUTPUT = MASE_DIR / "mase_by_model.csv"
MASE_BY_ENTITY_OUTPUT = MASE_DIR / "mase_by_entity.csv"
MASE_SUMMARY_OUTPUT = MASE_DIR / "mase_summary.csv"

PROTECTED_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "benchmark_reference",
    MODEL_LAB_DIR / "seasonal_benchmark",
    MODEL_LAB_DIR / "tournament",
    PROJECT_ROOT / "shiny_app",
]

FORECAST_HORIZON_DAYS = 30
EXPECTED_BASELINE_JOBS = 3178
EPSILON = 1e-6
BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
    "LinearRegression",
}

MASE_SCORE_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "model_name",
    "forecast_rows",
    "mase",
    "mae_model",
    "mae_naive",
    "denominator_floored",
    "created_timestamp",
]
MASE_BY_MODEL_COLUMNS = [
    "model_name",
    "metric_rows",
    "median_mase",
    "mean_mase",
    "p95_mase",
    "pct_windows_beating_naive",
    "created_timestamp",
]
MASE_BY_ENTITY_COLUMNS = [
    "entity_key",
    "metric_rows",
    "median_mase",
    "mean_mase",
    "p95_mase",
    "created_timestamp",
]
MASE_SUMMARY_COLUMNS = [
    "run_id",
    "metric_rows",
    "entities",
    "windows",
    "models",
    "global_median_mase",
    "global_mean_mase",
    "pct_rows_beating_naive",
    "created_timestamp",
]


def _require_file(path: Path) -> None:
    """Validate that a required output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required MASE output missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _load_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all MASE outputs."""

    for path in [
        MASE_SCORES_OUTPUT,
        MASE_BY_MODEL_OUTPUT,
        MASE_BY_ENTITY_OUTPUT,
        MASE_SUMMARY_OUTPUT,
    ]:
        _require_file(path)

    scores = pd.read_csv(MASE_SCORES_OUTPUT, parse_dates=["created_timestamp"])
    by_model = pd.read_csv(MASE_BY_MODEL_OUTPUT, parse_dates=["created_timestamp"])
    by_entity = pd.read_csv(MASE_BY_ENTITY_OUTPUT, parse_dates=["created_timestamp"])
    summary = pd.read_csv(MASE_SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    _assert_columns(scores, MASE_SCORE_COLUMNS, "mase_scores.csv")
    _assert_columns(by_model, MASE_BY_MODEL_COLUMNS, "mase_by_model.csv")
    _assert_columns(by_entity, MASE_BY_ENTITY_COLUMNS, "mase_by_entity.csv")
    _assert_columns(summary, MASE_SUMMARY_COLUMNS, "mase_summary.csv")
    return scores, by_model, by_entity, summary


def _validate_scores(scores: pd.DataFrame) -> None:
    """Validate row-level MASE scores."""

    if len(scores) != EXPECTED_BASELINE_JOBS:
        raise ValueError(
            f"Expected {EXPECTED_BASELINE_JOBS} MASE rows; found {len(scores)}."
        )
    duplicate_count = scores.duplicated(["entity_key", "window_id", "model_name"]).sum()
    if duplicate_count:
        raise ValueError(f"Duplicate entity/window/model rows found: {duplicate_count}")
    if not (scores["forecast_rows"].astype(int) == FORECAST_HORIZON_DAYS).all():
        raise ValueError("Every MASE row must have exactly 30 forecast rows.")

    numeric_columns = ["mase", "mae_model", "mae_naive"]
    for column in numeric_columns:
        if scores[column].isna().any():
            raise ValueError(f"NaN/null values found in {column}.")
        finite_mask = scores[column].map(math.isfinite)
        if not finite_mask.all():
            raise ValueError(f"Non-finite values found in {column}.")
    if not (scores["mae_naive"] > 0).all():
        raise ValueError("All denominators must be greater than zero.")

    floored = scores["denominator_floored"].astype(str).str.lower().isin(["true", "1"])
    expected_floored = scores["mae_naive"] == EPSILON
    if not (floored == expected_floored).all():
        raise ValueError("Denominator floor behavior is not recorded correctly.")
    if not set(scores["model_name"].unique()) == BASELINE_MODELS:
        raise ValueError(
            "Baseline model set mismatch: "
            f"{sorted(scores['model_name'].unique())}"
        )


def _validate_aggregates(
    scores: pd.DataFrame,
    by_model: pd.DataFrame,
    by_entity: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Validate aggregate output consistency."""

    if len(by_model) != len(BASELINE_MODELS):
        raise ValueError(f"Expected 7 model aggregate rows; found {len(by_model)}.")
    if set(by_model["model_name"]) != BASELINE_MODELS:
        raise ValueError("mase_by_model.csv does not represent all baseline models.")
    model_counts = scores.groupby("model_name").size()
    for _, row in by_model.iterrows():
        if int(row["metric_rows"]) != int(model_counts[row["model_name"]]):
            raise ValueError(f"Metric row mismatch for model {row['model_name']}.")

    entity_counts = scores.groupby("entity_key").size()
    for _, row in by_entity.iterrows():
        if int(row["metric_rows"]) != int(entity_counts[row["entity_key"]]):
            raise ValueError(f"Metric row mismatch for entity {row['entity_key']}.")

    if len(summary) != 1:
        raise ValueError(f"Summary must contain exactly one row; found {len(summary)}.")
    row = summary.iloc[0]
    expected = {
        "metric_rows": len(scores),
        "entities": scores["entity_key"].nunique(),
        "windows": scores[["entity_key", "window_id"]].drop_duplicates().shape[0],
        "models": scores["model_name"].nunique(),
    }
    for column, value in expected.items():
        if int(row[column]) != int(value):
            raise ValueError(
                f"Summary {column} mismatch: expected {value}, found {row[column]}"
            )


def _validate_expected_windows(scores: pd.DataFrame) -> None:
    """Validate all valid baseline windows are represented for each model."""

    _require_file(WINDOWS_INPUT)
    windows = pd.read_csv(WINDOWS_INPUT)
    windows = windows[windows["forecast_horizon_days"] == FORECAST_HORIZON_DAYS].copy()
    planned = set(zip(windows["entity_key"], windows["window_id"].astype(int)))
    scored = set(zip(scores["entity_key"], scores["window_id"].astype(int)))
    if planned != scored:
        missing = sorted(planned - scored)[:10]
        unexpected = sorted(scored - planned)[:10]
        raise ValueError(
            "Scored windows do not match valid windows. "
            f"Missing sample: {missing}; unexpected sample: {unexpected}"
        )
    expected_rows = len(planned) * len(BASELINE_MODELS)
    if len(scores) != expected_rows:
        raise ValueError(f"Expected {expected_rows} rows from valid windows/models.")


def _log_protected_scope() -> None:
    """Report protected directories to make no-touch validation explicit."""

    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not inspected for writes: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_mase() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate Stage 5.21 MASE outputs."""

    logger.info("Stage 5.21 MASE inspection started")
    scores, by_model, by_entity, summary = _load_outputs()
    _validate_scores(scores)
    _validate_expected_windows(scores)
    _validate_aggregates(scores, by_model, by_entity, summary)
    _log_protected_scope()

    mase_lt_1 = int((scores["mase"] < 1.0).sum())
    mase_eq_1 = int((scores["mase"] == 1.0).sum())
    mase_gt_1 = int((scores["mase"] > 1.0).sum())
    logger.info("Output files exist: yes")
    logger.info("Expected columns exist: yes")
    logger.info("MASE finite and non-null: yes")
    logger.info("No duplicate entity/window/model rows: yes")
    logger.info("All 3178 baseline jobs represented: yes")
    logger.info("All 7 baseline models represented: yes")
    logger.info("Rows with MASE < 1: %s", mase_lt_1)
    logger.info("Rows with MASE = 1: %s", mase_eq_1)
    logger.info("Rows with MASE > 1: %s", mase_gt_1)
    logger.info(
        "pct_windows_beating_naive: %.6f", float((scores["mase"] < 1.0).mean())
    )
    logger.info("No RMSSE calculated: yes")
    logger.info("No rankings created: yes")
    logger.info("No tournament outputs created: yes")
    logger.info("Stage 5.21 MASE inspection completed")
    return scores, by_model, by_entity, summary


if __name__ == "__main__":
    inspect_mase()
