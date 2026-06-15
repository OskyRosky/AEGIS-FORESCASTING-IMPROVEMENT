"""Inspect Stage 5.22 RMSSE guardrail outputs.

This inspector validates RMSSE output contracts and diagnostics. It does not
rank models, select winners, create champions, or write tournament outputs.
"""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_rmsse")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
RMSSE_DIR = MODEL_LAB_DIR / "rmsse"
RMSSE_SCORES_OUTPUT = RMSSE_DIR / "rmsse_scores.csv"
RMSSE_BY_MODEL_OUTPUT = RMSSE_DIR / "rmsse_by_model.csv"
RMSSE_BY_ENTITY_OUTPUT = RMSSE_DIR / "rmsse_by_entity.csv"
RMSSE_SUMMARY_OUTPUT = RMSSE_DIR / "rmsse_guardrail_summary.csv"

PROTECTED_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "benchmark_reference",
    MODEL_LAB_DIR / "seasonal_benchmark",
    MODEL_LAB_DIR / "mase",
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
RISK_STATUSES = {"beats_naive", "acceptable", "warning", "high_risk"}

RMSSE_SCORE_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "model_name",
    "forecast_rows",
    "rmsse",
    "rmse_model",
    "rmse_naive",
    "denominator_floored",
    "risk_status",
    "created_timestamp",
]
RMSSE_BY_MODEL_COLUMNS = [
    "model_name",
    "metric_rows",
    "median_rmsse",
    "mean_rmsse",
    "p95_rmsse",
    "pct_beating_naive",
    "pct_high_risk",
    "created_timestamp",
]
RMSSE_BY_ENTITY_COLUMNS = [
    "entity_key",
    "metric_rows",
    "median_rmsse",
    "mean_rmsse",
    "p95_rmsse",
    "pct_high_risk",
    "created_timestamp",
]
RMSSE_SUMMARY_COLUMNS = [
    "run_id",
    "metric_rows",
    "entities",
    "windows",
    "models",
    "global_median_rmsse",
    "global_mean_rmsse",
    "pct_beating_naive",
    "pct_high_risk",
    "created_timestamp",
]


def _require_file(path: Path) -> None:
    """Validate that a required output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required RMSSE output missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _load_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all RMSSE outputs."""

    for path in [
        RMSSE_SCORES_OUTPUT,
        RMSSE_BY_MODEL_OUTPUT,
        RMSSE_BY_ENTITY_OUTPUT,
        RMSSE_SUMMARY_OUTPUT,
    ]:
        _require_file(path)

    scores = pd.read_csv(RMSSE_SCORES_OUTPUT, parse_dates=["created_timestamp"])
    by_model = pd.read_csv(RMSSE_BY_MODEL_OUTPUT, parse_dates=["created_timestamp"])
    by_entity = pd.read_csv(RMSSE_BY_ENTITY_OUTPUT, parse_dates=["created_timestamp"])
    summary = pd.read_csv(RMSSE_SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    _assert_columns(scores, RMSSE_SCORE_COLUMNS, "rmsse_scores.csv")
    _assert_columns(by_model, RMSSE_BY_MODEL_COLUMNS, "rmsse_by_model.csv")
    _assert_columns(by_entity, RMSSE_BY_ENTITY_COLUMNS, "rmsse_by_entity.csv")
    _assert_columns(summary, RMSSE_SUMMARY_COLUMNS, "rmsse_guardrail_summary.csv")
    return scores, by_model, by_entity, summary


def _expected_risk_status(rmsse: float) -> str:
    """Return expected risk status for a RMSSE value."""

    if rmsse < 1.0:
        return "beats_naive"
    if rmsse < 2.0:
        return "acceptable"
    if rmsse < 5.0:
        return "warning"
    return "high_risk"


def _validate_scores(scores: pd.DataFrame) -> None:
    """Validate row-level RMSSE guardrail scores."""

    if len(scores) != EXPECTED_BASELINE_JOBS:
        raise ValueError(
            f"Expected {EXPECTED_BASELINE_JOBS} RMSSE rows; found {len(scores)}."
        )
    duplicate_count = scores.duplicated(["entity_key", "window_id", "model_name"]).sum()
    if duplicate_count:
        raise ValueError(f"Duplicate entity/window/model rows found: {duplicate_count}")
    if not (scores["forecast_rows"].astype(int) == FORECAST_HORIZON_DAYS).all():
        raise ValueError("Every RMSSE row must have exactly 30 forecast rows.")

    numeric_columns = ["rmsse", "rmse_model", "rmse_naive"]
    for column in numeric_columns:
        if scores[column].isna().any():
            raise ValueError(f"NaN/null values found in {column}.")
        finite_mask = scores[column].map(math.isfinite)
        if not finite_mask.all():
            raise ValueError(f"Non-finite values found in {column}.")
    if not (scores["rmse_naive"] > 0).all():
        raise ValueError("All denominators must be greater than zero.")

    floored = scores["denominator_floored"].astype(str).str.lower().isin(["true", "1"])
    expected_floored = scores["rmse_naive"] == math.sqrt(EPSILON)
    if not (floored == expected_floored).all():
        raise ValueError("Denominator floor behavior is not recorded correctly.")

    if set(scores["model_name"].unique()) != BASELINE_MODELS:
        raise ValueError(
            "Baseline model set mismatch: "
            f"{sorted(scores['model_name'].unique())}"
        )
    if not set(scores["risk_status"].unique()).issubset(RISK_STATUSES):
        raise ValueError("Unexpected risk_status values found.")
    expected_statuses = scores["rmsse"].map(_expected_risk_status)
    if not (scores["risk_status"] == expected_statuses).all():
        raise ValueError("risk_status values do not match RMSSE thresholds.")


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
        raise ValueError("rmsse_by_model.csv does not represent all baseline models.")
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


def inspect_rmsse() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate Stage 5.22 RMSSE guardrail outputs."""

    logger.info("Stage 5.22 RMSSE guardrail inspection started")
    scores, by_model, by_entity, summary = _load_outputs()
    _validate_scores(scores)
    _validate_expected_windows(scores)
    _validate_aggregates(scores, by_model, by_entity, summary)
    _log_protected_scope()

    beats_naive = int((scores["rmsse"] < 1.0).sum())
    acceptable = int(((scores["rmsse"] >= 1.0) & (scores["rmsse"] < 2.0)).sum())
    warning = int(((scores["rmsse"] >= 2.0) & (scores["rmsse"] < 5.0)).sum())
    high_risk = int((scores["rmsse"] >= 5.0).sum())
    logger.info("Output files exist: yes")
    logger.info("Expected columns exist: yes")
    logger.info("RMSSE finite and non-null: yes")
    logger.info("No duplicate entity/window/model rows: yes")
    logger.info("All 3178 baseline jobs represented: yes")
    logger.info("All 7 baseline models represented: yes")
    logger.info("RMSSE < 1: %s", beats_naive)
    logger.info("RMSSE 1-2: %s", acceptable)
    logger.info("RMSSE 2-5: %s", warning)
    logger.info("RMSSE >= 5: %s", high_risk)
    logger.info("pct_beating_naive: %.6f", float((scores["rmsse"] < 1.0).mean()))
    logger.info(
        "pct_high_risk: %.6f",
        float((scores["risk_status"] == "high_risk").mean()),
    )
    logger.info("No rankings created: yes")
    logger.info("No tournament outputs created: yes")
    logger.info("Stage 5.22 RMSSE guardrail inspection completed")
    return scores, by_model, by_entity, summary


if __name__ == "__main__":
    inspect_rmsse()
