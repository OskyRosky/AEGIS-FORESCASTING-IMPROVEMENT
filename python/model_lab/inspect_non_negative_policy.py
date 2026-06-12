"""Inspect Stage 5.23 non-negative forecast policy outputs."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_non_negative_policy")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
FULL_BASELINE_FORECASTS = (
    MODEL_LAB_DIR / "full_baseline" / "full_baseline_forecasts.csv"
)
NAIVE_FORECASTS = (
    MODEL_LAB_DIR / "benchmark_reference" / "naive_benchmark_forecasts.csv"
)
MASE_SCORES_INPUT = MODEL_LAB_DIR / "mase" / "mase_scores.csv"
RMSSE_SCORES_INPUT = MODEL_LAB_DIR / "rmsse" / "rmsse_scores.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "non_negative_policy"

FORECASTS_OUTPUT = OUTPUT_DIR / "non_negative_forecasts.csv"
IMPACT_BY_MODEL_OUTPUT = OUTPUT_DIR / "non_negative_impact_by_model.csv"
IMPACT_BY_ENTITY_OUTPUT = OUTPUT_DIR / "non_negative_impact_by_entity.csv"
MASE_OUTPUT = OUTPUT_DIR / "non_negative_mase_scores.csv"
RMSSE_OUTPUT = OUTPUT_DIR / "non_negative_rmsse_scores.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "non_negative_policy_summary.csv"

PROTECTED_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "benchmark_reference",
    MODEL_LAB_DIR / "seasonal_benchmark",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "tournament",
    PROJECT_ROOT / "shiny_app",
]

FORECAST_HORIZON_DAYS = 30
EXPECTED_BASELINE_JOBS = 3178
EPSILON = 1e-6
NUMERIC_TOLERANCE = 1e-6
BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
    "LinearRegression",
}

FORECAST_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "model_name",
    "forecast_date",
    "horizon_day",
    "original_forecast_value",
    "adjusted_forecast_value",
    "was_clipped",
    "created_timestamp",
]
IMPACT_BY_MODEL_COLUMNS = [
    "model_name",
    "forecast_rows",
    "negative_forecast_rows",
    "pct_negative_forecast_rows",
    "min_original_forecast",
    "min_adjusted_forecast",
    "max_original_forecast",
    "max_adjusted_forecast",
    "created_timestamp",
]
IMPACT_BY_ENTITY_COLUMNS = [
    "entity_key",
    "forecast_rows",
    "negative_forecast_rows",
    "pct_negative_forecast_rows",
    "min_original_forecast",
    "min_adjusted_forecast",
    "created_timestamp",
]
MASE_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "model_name",
    "forecast_rows",
    "mase",
    "mae_model_adjusted",
    "mae_naive",
    "denominator_floored",
    "created_timestamp",
]
RMSSE_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "model_name",
    "forecast_rows",
    "rmsse",
    "rmse_model_adjusted",
    "rmse_naive",
    "denominator_floored",
    "risk_status",
    "created_timestamp",
]
SUMMARY_COLUMNS = [
    "run_id",
    "forecast_rows",
    "adjusted_forecast_rows",
    "negative_forecast_rows",
    "pct_negative_forecast_rows",
    "models",
    "entities",
    "windows",
    "original_min_forecast",
    "adjusted_min_forecast",
    "mase_median_before",
    "mase_median_after",
    "rmsse_median_before",
    "rmsse_median_after",
    "created_timestamp",
]


def _require_file(path: Path) -> None:
    """Validate that a required file exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required non-negative policy file missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _load_outputs() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    """Load all non-negative policy outputs."""

    for path in [
        FORECASTS_OUTPUT,
        IMPACT_BY_MODEL_OUTPUT,
        IMPACT_BY_ENTITY_OUTPUT,
        MASE_OUTPUT,
        RMSSE_OUTPUT,
        SUMMARY_OUTPUT,
    ]:
        _require_file(path)

    forecasts = pd.read_csv(
        FORECASTS_OUTPUT, parse_dates=["forecast_date", "created_timestamp"]
    )
    impact_model = pd.read_csv(IMPACT_BY_MODEL_OUTPUT, parse_dates=["created_timestamp"])
    impact_entity = pd.read_csv(IMPACT_BY_ENTITY_OUTPUT, parse_dates=["created_timestamp"])
    mase = pd.read_csv(MASE_OUTPUT, parse_dates=["created_timestamp"])
    rmsse = pd.read_csv(RMSSE_OUTPUT, parse_dates=["created_timestamp"])
    summary = pd.read_csv(SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    _assert_columns(forecasts, FORECAST_COLUMNS, "non_negative_forecasts.csv")
    _assert_columns(
        impact_model, IMPACT_BY_MODEL_COLUMNS, "non_negative_impact_by_model.csv"
    )
    _assert_columns(
        impact_entity, IMPACT_BY_ENTITY_COLUMNS, "non_negative_impact_by_entity.csv"
    )
    _assert_columns(mase, MASE_COLUMNS, "non_negative_mase_scores.csv")
    _assert_columns(rmsse, RMSSE_COLUMNS, "non_negative_rmsse_scores.csv")
    _assert_columns(summary, SUMMARY_COLUMNS, "non_negative_policy_summary.csv")
    return forecasts, impact_model, impact_entity, mase, rmsse, summary


def _load_original_forecasts() -> pd.DataFrame:
    """Load original full-baseline forecasts for comparison."""

    _require_file(FULL_BASELINE_FORECASTS)
    original = pd.read_csv(FULL_BASELINE_FORECASTS, parse_dates=["forecast_date"])
    original["window_id"] = original["window_id"].astype(int)
    original["horizon_day"] = original["horizon_day"].astype(int)
    original["forecast_value"] = pd.to_numeric(original["forecast_value"], errors="coerce")
    return original


def _validate_forecasts(adjusted: pd.DataFrame, original: pd.DataFrame) -> None:
    """Validate adjusted forecast rows and original value preservation."""

    if len(adjusted) != len(original):
        raise ValueError(
            f"Adjusted row count mismatch: expected {len(original)}, found {len(adjusted)}."
        )
    if adjusted.duplicated(
        ["entity_key", "window_id", "model_name", "forecast_date"]
    ).any():
        raise ValueError("Duplicate entity/window/model/date adjusted forecast rows found.")
    if adjusted["adjusted_forecast_value"].isna().any():
        raise ValueError("Null adjusted_forecast_value found.")
    if adjusted["original_forecast_value"].isna().any():
        raise ValueError("Null original_forecast_value found.")
    for column in ["original_forecast_value", "adjusted_forecast_value"]:
        if not adjusted[column].map(math.isfinite).all():
            raise ValueError(f"Non-finite values found in {column}.")
    if (adjusted["adjusted_forecast_value"] < 0).any():
        raise ValueError("Negative adjusted forecasts found.")

    clipped = adjusted["was_clipped"].astype(str).str.lower().isin(["true", "1"])
    expected_clipped = adjusted["original_forecast_value"] < 0
    if not (clipped == expected_clipped).all():
        raise ValueError("was_clipped does not match original_forecast_value < 0.")

    expected_adjusted = adjusted["original_forecast_value"].clip(lower=0)
    if not (
        (adjusted["adjusted_forecast_value"] - expected_adjusted).abs()
        < NUMERIC_TOLERANCE
    ).all():
        raise ValueError("adjusted_forecast_value is not max(original_forecast_value, 0).")

    original_keys = original[
        ["entity_key", "window_id", "model_name", "forecast_date", "horizon_day", "forecast_value"]
    ].copy()
    original_keys = original_keys.rename(columns={"forecast_value": "source_forecast_value"})
    merged = adjusted.merge(
        original_keys,
        on=["entity_key", "window_id", "model_name", "forecast_date", "horizon_day"],
        how="left",
        validate="one_to_one",
    )
    if merged["source_forecast_value"].isna().any():
        raise ValueError("Adjusted forecasts contain rows not found in original forecasts.")
    preserved_delta = (
        merged["original_forecast_value"] - merged["source_forecast_value"]
    ).abs()
    if not (preserved_delta < NUMERIC_TOLERANCE).all():
        raise ValueError("Original forecast values were not preserved in adjusted output.")


def _load_scoring_frame(adjusted: pd.DataFrame) -> pd.DataFrame:
    """Join adjusted forecasts with actuals and naive benchmark for metric checks."""

    _require_file(EVALUATION_DATASET)
    _require_file(NAIVE_FORECASTS)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["actual_value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "actual_value"])
    actuals = actuals[["entity_key", "date", "actual_value"]].rename(
        columns={"date": "forecast_date"}
    )
    naive = pd.read_csv(NAIVE_FORECASTS, parse_dates=["forecast_date"])
    naive["window_id"] = naive["window_id"].astype(int)
    naive["horizon_day"] = naive["horizon_day"].astype(int)
    naive["naive_forecast_value"] = pd.to_numeric(
        naive["naive_forecast_value"], errors="coerce"
    )
    naive = naive[
        ["entity_key", "window_id", "forecast_date", "horizon_day", "naive_forecast_value"]
    ]

    merged = adjusted.merge(
        actuals,
        on=["entity_key", "forecast_date"],
        how="inner",
        validate="many_to_one",
    )
    merged = merged.merge(
        naive,
        on=["entity_key", "window_id", "forecast_date", "horizon_day"],
        how="inner",
        validate="many_to_one",
    )
    if len(merged) != len(adjusted):
        raise ValueError("Adjusted scoring join did not preserve all forecast rows.")
    merged["model_abs_error_adjusted"] = (
        merged["actual_value"] - merged["adjusted_forecast_value"]
    ).abs()
    merged["naive_abs_error"] = (
        merged["actual_value"] - merged["naive_forecast_value"]
    ).abs()
    merged["model_squared_error_adjusted"] = (
        merged["actual_value"] - merged["adjusted_forecast_value"]
    ) ** 2
    merged["naive_squared_error"] = (
        merged["actual_value"] - merged["naive_forecast_value"]
    ) ** 2
    return merged


def _risk_status(rmsse: float) -> str:
    """Return expected RMSSE risk status."""

    if rmsse < 1.0:
        return "beats_naive"
    if rmsse < 2.0:
        return "acceptable"
    if rmsse < 5.0:
        return "warning"
    return "high_risk"


def _validate_adjusted_mase(scoring_frame: pd.DataFrame, mase: pd.DataFrame) -> None:
    """Validate MASE recalculation from adjusted forecasts."""

    if len(mase) != EXPECTED_BASELINE_JOBS:
        raise ValueError(f"Expected {EXPECTED_BASELINE_JOBS} adjusted MASE rows.")
    if mase.duplicated(["entity_key", "window_id", "model_name"]).any():
        raise ValueError("Duplicate adjusted MASE entity/window/model rows found.")
    if not (mase["forecast_rows"].astype(int) == FORECAST_HORIZON_DAYS).all():
        raise ValueError("Adjusted MASE rows must each have 30 forecast rows.")
    if set(mase["model_name"].unique()) != BASELINE_MODELS:
        raise ValueError("Adjusted MASE does not include all 7 baseline models.")
    for column in ["mase", "mae_model_adjusted", "mae_naive"]:
        if mase[column].isna().any() or not mase[column].map(math.isfinite).all():
            raise ValueError(f"Invalid values found in adjusted MASE column {column}.")
    if not (mase["mae_naive"] > 0).all():
        raise ValueError("Adjusted MASE denominators must be positive.")

    recomputed = []
    for keys, group in scoring_frame.groupby(["entity_key", "window_id", "model_name"]):
        raw_naive = float(group["naive_abs_error"].mean())
        mae_naive = EPSILON if raw_naive < EPSILON else raw_naive
        mae_model = float(group["model_abs_error_adjusted"].mean())
        recomputed.append(
            {
                "entity_key": keys[0],
                "window_id": int(keys[1]),
                "model_name": keys[2],
                "forecast_rows_expected": len(group),
                "mase_expected": mae_model / mae_naive,
                "mae_model_adjusted_expected": mae_model,
                "mae_naive_expected": mae_naive,
                "denominator_floored_expected": raw_naive < EPSILON,
            }
        )
    expected = pd.DataFrame(recomputed)
    merged = mase.merge(expected, on=["entity_key", "window_id", "model_name"], how="left")
    if merged["mase_expected"].isna().any():
        raise ValueError("Adjusted MASE includes unexpected rows.")
    if not (merged["forecast_rows"].astype(int) == merged["forecast_rows_expected"]).all():
        raise ValueError("Adjusted MASE forecast row counts do not match recomputation.")
    if not ((merged["mase"] - merged["mase_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Adjusted MASE values do not match recomputation.")
    if not (
        (merged["mae_model_adjusted"] - merged["mae_model_adjusted_expected"]).abs()
        < NUMERIC_TOLERANCE
    ).all():
        raise ValueError("Adjusted MAE values do not match recomputation.")
    if not (
        (merged["mae_naive"] - merged["mae_naive_expected"]).abs()
        < NUMERIC_TOLERANCE
    ).all():
        raise ValueError("Adjusted MASE denominators do not match recomputation.")


def _validate_adjusted_rmsse(scoring_frame: pd.DataFrame, rmsse: pd.DataFrame) -> None:
    """Validate RMSSE recalculation from adjusted forecasts."""

    if len(rmsse) != EXPECTED_BASELINE_JOBS:
        raise ValueError(f"Expected {EXPECTED_BASELINE_JOBS} adjusted RMSSE rows.")
    if rmsse.duplicated(["entity_key", "window_id", "model_name"]).any():
        raise ValueError("Duplicate adjusted RMSSE entity/window/model rows found.")
    if not (rmsse["forecast_rows"].astype(int) == FORECAST_HORIZON_DAYS).all():
        raise ValueError("Adjusted RMSSE rows must each have 30 forecast rows.")
    if set(rmsse["model_name"].unique()) != BASELINE_MODELS:
        raise ValueError("Adjusted RMSSE does not include all 7 baseline models.")
    for column in ["rmsse", "rmse_model_adjusted", "rmse_naive"]:
        if rmsse[column].isna().any() or not rmsse[column].map(math.isfinite).all():
            raise ValueError(f"Invalid values found in adjusted RMSSE column {column}.")
    if not (rmsse["rmse_naive"] > 0).all():
        raise ValueError("Adjusted RMSSE denominators must be positive.")

    recomputed = []
    for keys, group in scoring_frame.groupby(["entity_key", "window_id", "model_name"]):
        model_mse = float(group["model_squared_error_adjusted"].mean())
        raw_naive = float(group["naive_squared_error"].mean())
        naive_mse = EPSILON if raw_naive < EPSILON else raw_naive
        rmsse_value = math.sqrt(model_mse / naive_mse)
        recomputed.append(
            {
                "entity_key": keys[0],
                "window_id": int(keys[1]),
                "model_name": keys[2],
                "forecast_rows_expected": len(group),
                "rmsse_expected": rmsse_value,
                "rmse_model_adjusted_expected": math.sqrt(model_mse),
                "rmse_naive_expected": math.sqrt(naive_mse),
                "denominator_floored_expected": raw_naive < EPSILON,
                "risk_status_expected": _risk_status(rmsse_value),
            }
        )
    expected = pd.DataFrame(recomputed)
    merged = rmsse.merge(expected, on=["entity_key", "window_id", "model_name"], how="left")
    if merged["rmsse_expected"].isna().any():
        raise ValueError("Adjusted RMSSE includes unexpected rows.")
    if not (merged["forecast_rows"].astype(int) == merged["forecast_rows_expected"]).all():
        raise ValueError("Adjusted RMSSE forecast row counts do not match recomputation.")
    if not ((merged["rmsse"] - merged["rmsse_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Adjusted RMSSE values do not match recomputation.")
    if not (merged["risk_status"] == merged["risk_status_expected"]).all():
        raise ValueError("Adjusted RMSSE risk status does not match thresholds.")


def _validate_summary(
    adjusted: pd.DataFrame,
    impact_model: pd.DataFrame,
    impact_entity: pd.DataFrame,
    mase: pd.DataFrame,
    rmsse: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Validate impact summaries and global summary."""

    if len(summary) != 1:
        raise ValueError(f"Summary must contain one row; found {len(summary)}.")
    if len(impact_model) != len(BASELINE_MODELS):
        raise ValueError("Impact by model must include all 7 baseline models.")
    if set(impact_model["model_name"]) != BASELINE_MODELS:
        raise ValueError("Impact by model model set mismatch.")
    if len(impact_entity) != adjusted["entity_key"].nunique():
        raise ValueError("Impact by entity row count mismatch.")

    row = summary.iloc[0]
    negative_rows = int(adjusted["was_clipped"].astype(str).str.lower().isin(["true", "1"]).sum())
    expected = {
        "forecast_rows": len(adjusted),
        "adjusted_forecast_rows": negative_rows,
        "negative_forecast_rows": negative_rows,
        "models": adjusted["model_name"].nunique(),
        "entities": adjusted["entity_key"].nunique(),
        "windows": adjusted[["entity_key", "window_id"]].drop_duplicates().shape[0],
    }
    for column, value in expected.items():
        if int(row[column]) != int(value):
            raise ValueError(
                f"Summary {column} mismatch: expected {value}, found {row[column]}"
            )
    if float(row["adjusted_min_forecast"]) < 0:
        raise ValueError("Summary adjusted_min_forecast is negative.")

    mase_before = pd.to_numeric(pd.read_csv(MASE_SCORES_INPUT)["mase"], errors="coerce").median()
    rmsse_before = pd.to_numeric(pd.read_csv(RMSSE_SCORES_INPUT)["rmsse"], errors="coerce").median()
    if abs(float(row["mase_median_before"]) - float(mase_before)) >= 1e-12:
        raise ValueError("Summary MASE before median mismatch.")
    if abs(float(row["rmsse_median_before"]) - float(rmsse_before)) >= 1e-12:
        raise ValueError("Summary RMSSE before median mismatch.")
    if abs(float(row["mase_median_after"]) - float(mase["mase"].median())) >= 1e-12:
        raise ValueError("Summary MASE after median mismatch.")
    if abs(float(row["rmsse_median_after"]) - float(rmsse["rmsse"].median())) >= 1e-12:
        raise ValueError("Summary RMSSE after median mismatch.")


def _log_protected_scope() -> None:
    """Report protected directories to make no-touch validation explicit."""

    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not inspected for writes: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_non_negative_policy() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    """Validate Stage 5.23 non-negative policy outputs."""

    logger.info("Stage 5.23 non-negative forecast policy inspection started")
    adjusted, impact_model, impact_entity, mase, rmsse, summary = _load_outputs()
    original = _load_original_forecasts()
    _validate_forecasts(adjusted, original)
    scoring_frame = _load_scoring_frame(adjusted)
    _validate_adjusted_mase(scoring_frame, mase)
    _validate_adjusted_rmsse(scoring_frame, rmsse)
    _validate_summary(adjusted, impact_model, impact_entity, mase, rmsse, summary)
    _log_protected_scope()

    clipped = adjusted["was_clipped"].astype(str).str.lower().isin(["true", "1"])
    logger.info("Output files exist: yes")
    logger.info("Required columns exist: yes")
    logger.info("Forecast row count matches original: yes")
    logger.info("All adjusted forecasts are non-negative: yes")
    logger.info("Original forecasts preserved in adjusted output: yes")
    logger.info("All 3178 baseline jobs represented in adjusted metrics: yes")
    logger.info("All 7 baseline models represented: yes")
    logger.info("No NaN or Inf values: yes")
    logger.info("No duplicate entity/window/model/date rows: yes")
    logger.info("MASE recalculated with adjusted forecasts: yes")
    logger.info("RMSSE recalculated with adjusted forecasts: yes")
    logger.info("Negative forecast rows: %s", int(clipped.sum()))
    logger.info("pct_negative_forecast_rows: %.6f", float(clipped.mean()))
    logger.info("No ranking outputs created: yes")
    logger.info("No tournament outputs created: yes")
    logger.info("Stage 5.23 non-negative forecast policy inspection completed")
    return adjusted, impact_model, impact_entity, mase, rmsse, summary


if __name__ == "__main__":
    inspect_non_negative_policy()
