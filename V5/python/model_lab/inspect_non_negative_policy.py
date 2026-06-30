"""Inspect Stage 5.23 non-negative forecast policy outputs."""

from __future__ import annotations

import math

import pandas as pd

from model_lab.benchmark_denominators import DENOMINATORS_OUTPUT, EPSILON, load_actuals
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_non_negative_policy")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
FULL_BASELINE_FORECASTS = MODEL_LAB_DIR / "full_baseline" / "full_baseline_forecasts.csv"
MASE_SCORES_INPUT = MODEL_LAB_DIR / "mase" / "mase_scores.csv"
RMSSE_SCORES_INPUT = MODEL_LAB_DIR / "rmsse" / "rmsse_scores.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "non_negative_policy"

FORECASTS_OUTPUT = OUTPUT_DIR / "non_negative_forecasts.csv"
IMPACT_BY_MODEL_OUTPUT = OUTPUT_DIR / "non_negative_impact_by_model.csv"
IMPACT_BY_ENTITY_OUTPUT = OUTPUT_DIR / "non_negative_impact_by_entity.csv"
MASE_OUTPUT = OUTPUT_DIR / "non_negative_mase_scores.csv"
RMSSE_OUTPUT = OUTPUT_DIR / "non_negative_rmsse_scores.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "non_negative_policy_summary.csv"

EXPECTED_BASELINE_JOBS = 3178
FORECAST_HORIZON_DAYS = 30
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


def _require_file(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required non-negative policy file missing: {path}")


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.lower().isin(["true", "1"])


def _validate_forecasts(adjusted: pd.DataFrame, original: pd.DataFrame) -> None:
    if len(adjusted) != len(original):
        raise ValueError("Adjusted row count does not match original forecasts.")
    if adjusted.duplicated(["entity_key", "window_id", "model_name", "forecast_date"]).any():
        raise ValueError("Duplicate adjusted forecast rows found.")
    for column in ["original_forecast_value", "adjusted_forecast_value"]:
        if adjusted[column].isna().any() or not adjusted[column].map(math.isfinite).all():
            raise ValueError(f"Invalid values in {column}.")
    if (adjusted["adjusted_forecast_value"] < 0).any():
        raise ValueError("Negative adjusted forecasts found.")
    clipped = _bool_series(adjusted["was_clipped"])
    if not (clipped == (adjusted["original_forecast_value"] < 0)).all():
        raise ValueError("was_clipped flag mismatch.")
    expected_adjusted = adjusted["original_forecast_value"].clip(lower=0)
    if not ((adjusted["adjusted_forecast_value"] - expected_adjusted).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("adjusted_forecast_value is not max(original, 0).")

    source = original[
        ["entity_key", "window_id", "model_name", "forecast_date", "horizon_day", "forecast_value"]
    ].rename(columns={"forecast_value": "source_forecast_value"})
    merged = adjusted.merge(
        source,
        on=["entity_key", "window_id", "model_name", "forecast_date", "horizon_day"],
        how="left",
        validate="one_to_one",
    )
    if merged["source_forecast_value"].isna().any():
        raise ValueError("Adjusted output contains rows not present in original forecasts.")
    if not ((merged["original_forecast_value"] - merged["source_forecast_value"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Original forecast values not preserved in adjusted output.")


def _scoring_frame(adjusted: pd.DataFrame, denominators: pd.DataFrame) -> pd.DataFrame:
    actuals = load_actuals()[["entity_key", "date", "value"]].rename(
        columns={"date": "forecast_date", "value": "actual_value"}
    )
    merged = adjusted.merge(
        actuals, on=["entity_key", "forecast_date"], how="inner", validate="many_to_one"
    )
    merged = merged.merge(
        denominators[
            [
                "entity_key",
                "window_id",
                "mase_denominator_mae",
                "mase_denominator_floored",
                "rmsse_denominator_mse",
                "rmsse_denominator_floored",
            ]
        ],
        on=["entity_key", "window_id"],
        how="inner",
        validate="many_to_one",
    )
    if len(merged) != len(adjusted):
        raise ValueError("Scoring join did not preserve all adjusted rows.")
    merged["ae"] = (merged["actual_value"] - merged["adjusted_forecast_value"]).abs()
    merged["se"] = (merged["actual_value"] - merged["adjusted_forecast_value"]) ** 2
    return merged


def _validate_mase(scoring: pd.DataFrame, mase: pd.DataFrame) -> None:
    if len(mase) != EXPECTED_BASELINE_JOBS:
        raise ValueError("Adjusted MASE row count mismatch.")
    if set(mase["model_name"].unique()) != BASELINE_MODELS:
        raise ValueError("Adjusted MASE model set mismatch.")
    if not (mase["forecast_rows"].astype(int) == FORECAST_HORIZON_DAYS).all():
        raise ValueError("Adjusted MASE forecast_rows must be 30.")
    rows = []
    for keys, group in scoring.groupby(["entity_key", "window_id", "model_name"]):
        mae_model = float(group["ae"].mean())
        mae_naive = float(group["mase_denominator_mae"].iloc[0])
        rows.append(
            {
                "entity_key": keys[0],
                "window_id": int(keys[1]),
                "model_name": keys[2],
                "mase_expected": mae_model / mae_naive,
                "mae_model_expected": mae_model,
                "mae_naive_expected": mae_naive,
            }
        )
    expected = pd.DataFrame(rows)
    merged = mase.merge(expected, on=["entity_key", "window_id", "model_name"])
    if not ((merged["mase"] - merged["mase_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Adjusted MASE does not match training-only recomputation.")
    if not ((merged["mae_naive"] - merged["mae_naive_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Adjusted MASE denominator mismatch.")


def _risk_status(value: float) -> str:
    if value < 1.0:
        return "beats_naive"
    if value < 2.0:
        return "acceptable"
    if value < 5.0:
        return "warning"
    return "high_risk"


def _validate_rmsse(scoring: pd.DataFrame, rmsse: pd.DataFrame) -> None:
    if len(rmsse) != EXPECTED_BASELINE_JOBS:
        raise ValueError("Adjusted RMSSE row count mismatch.")
    if set(rmsse["model_name"].unique()) != BASELINE_MODELS:
        raise ValueError("Adjusted RMSSE model set mismatch.")
    if not (rmsse["forecast_rows"].astype(int) == FORECAST_HORIZON_DAYS).all():
        raise ValueError("Adjusted RMSSE forecast_rows must be 30.")
    rows = []
    for keys, group in scoring.groupby(["entity_key", "window_id", "model_name"]):
        model_mse = float(group["se"].mean())
        naive_mse = float(group["rmsse_denominator_mse"].iloc[0])
        rmsse_value = math.sqrt(model_mse / naive_mse)
        rows.append(
            {
                "entity_key": keys[0],
                "window_id": int(keys[1]),
                "model_name": keys[2],
                "rmsse_expected": rmsse_value,
                "rmse_naive_expected": math.sqrt(naive_mse),
                "risk_status_expected": _risk_status(rmsse_value),
            }
        )
    expected = pd.DataFrame(rows)
    merged = rmsse.merge(expected, on=["entity_key", "window_id", "model_name"])
    if not ((merged["rmsse"] - merged["rmsse_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Adjusted RMSSE does not match training-only recomputation.")
    if not ((merged["rmse_naive"] - merged["rmse_naive_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Adjusted RMSSE denominator mismatch.")
    if not (merged["risk_status"] == merged["risk_status_expected"]).all():
        raise ValueError("Adjusted RMSSE risk status mismatch.")


def inspect_non_negative_policy() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger.info("Stage 5.23 non-negative forecast policy inspection started")
    for path in [
        FORECASTS_OUTPUT,
        IMPACT_BY_MODEL_OUTPUT,
        IMPACT_BY_ENTITY_OUTPUT,
        MASE_OUTPUT,
        RMSSE_OUTPUT,
        SUMMARY_OUTPUT,
        DENOMINATORS_OUTPUT,
    ]:
        _require_file(path)
    adjusted = pd.read_csv(FORECASTS_OUTPUT, parse_dates=["forecast_date", "created_timestamp"])
    impact_model = pd.read_csv(IMPACT_BY_MODEL_OUTPUT)
    impact_entity = pd.read_csv(IMPACT_BY_ENTITY_OUTPUT)
    mase = pd.read_csv(MASE_OUTPUT)
    rmsse = pd.read_csv(RMSSE_OUTPUT)
    summary = pd.read_csv(SUMMARY_OUTPUT)
    denominators = pd.read_csv(DENOMINATORS_OUTPUT)
    original = pd.read_csv(FULL_BASELINE_FORECASTS, parse_dates=["forecast_date"])
    original["window_id"] = original["window_id"].astype(int)
    original["horizon_day"] = original["horizon_day"].astype(int)
    original["forecast_value"] = pd.to_numeric(original["forecast_value"], errors="coerce")

    _validate_forecasts(adjusted, original)
    scoring = _scoring_frame(adjusted, denominators)
    _validate_mase(scoring, mase)
    _validate_rmsse(scoring, rmsse)
    if len(summary) != 1:
        raise ValueError("Summary must have one row.")
    if int(summary.iloc[0]["forecast_rows"]) != len(adjusted):
        raise ValueError("Summary forecast_rows mismatch.")
    if int(summary.iloc[0]["negative_forecast_rows"]) != int(_bool_series(adjusted["was_clipped"]).sum()):
        raise ValueError("Summary negative_forecast_rows mismatch.")

    logger.info("Forecast row count matches original: yes")
    logger.info("All adjusted forecasts are non-negative: yes")
    logger.info("MASE recalculated with training-only adjusted forecasts: yes")
    logger.info("RMSSE recalculated with training-only adjusted forecasts: yes")
    logger.info("Negative forecast rows: %s", int(_bool_series(adjusted["was_clipped"]).sum()))
    return adjusted, impact_model, impact_entity, mase, rmsse, summary


if __name__ == "__main__":
    inspect_non_negative_policy()
