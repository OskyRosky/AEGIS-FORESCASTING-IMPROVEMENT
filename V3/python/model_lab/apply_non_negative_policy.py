"""Apply non-negative forecast policy to existing full-baseline forecasts.

This script writes adjusted copies and recalculates adjusted MASE/RMSSE with
the official training-only lag-1 denominators. It does not overwrite baseline
forecasts or previous benchmark/reference forecasts.
"""

from __future__ import annotations

from datetime import datetime
from math import sqrt

import pandas as pd

from model_lab.benchmark_denominators import build_and_write_denominators, load_actuals
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("apply_non_negative_policy")

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

RUN_ID_PREFIX = "non_negative_policy"
EPSILON = 1e-6

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


def _require_file(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required non-negative policy input missing: {path}")


def _load_forecasts() -> pd.DataFrame:
    _require_file(FULL_BASELINE_FORECASTS)
    forecasts = pd.read_csv(FULL_BASELINE_FORECASTS, parse_dates=["forecast_date"])
    required = {
        "entity_key",
        "window_id",
        "model_name",
        "forecast_date",
        "horizon_day",
        "forecast_value",
    }
    missing = required.difference(forecasts.columns)
    if missing:
        raise ValueError(f"full_baseline_forecasts.csv missing columns: {sorted(missing)}")
    forecasts = forecasts.copy()
    forecasts["window_id"] = forecasts["window_id"].astype(int)
    forecasts["horizon_day"] = forecasts["horizon_day"].astype(int)
    forecasts["forecast_value"] = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
    return forecasts.dropna(
        subset=[
            "entity_key",
            "window_id",
            "model_name",
            "forecast_date",
            "horizon_day",
            "forecast_value",
        ]
    )


def _load_previous_metric_medians() -> tuple[float, float]:
    _require_file(MASE_SCORES_INPUT)
    _require_file(RMSSE_SCORES_INPUT)
    mase = pd.read_csv(MASE_SCORES_INPUT)
    rmsse = pd.read_csv(RMSSE_SCORES_INPUT)
    return float(pd.to_numeric(mase["mase"], errors="coerce").median()), float(
        pd.to_numeric(rmsse["rmsse"], errors="coerce").median()
    )


def _actuals_for_forecast_dates() -> pd.DataFrame:
    actuals = load_actuals()
    return actuals[["entity_key", "date", "value"]].rename(
        columns={"date": "forecast_date", "value": "actual_value"}
    )


def _risk_status(rmsse: float) -> str:
    if rmsse < 1.0:
        return "beats_naive"
    if rmsse < 2.0:
        return "acceptable"
    if rmsse < 5.0:
        return "warning"
    return "high_risk"


def _build_adjusted_forecasts(forecasts: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    adjusted = forecasts[
        ["entity_key", "window_id", "model_name", "forecast_date", "horizon_day", "forecast_value"]
    ].copy()
    adjusted = adjusted.rename(columns={"forecast_value": "original_forecast_value"})
    adjusted["adjusted_forecast_value"] = adjusted["original_forecast_value"].clip(lower=0)
    adjusted["was_clipped"] = adjusted["original_forecast_value"] < 0
    adjusted.insert(0, "run_id", run_id)
    adjusted["created_timestamp"] = timestamp
    return adjusted[FORECAST_COLUMNS]


def _build_scoring_frame(
    adjusted: pd.DataFrame, denominators: pd.DataFrame, actuals: pd.DataFrame
) -> pd.DataFrame:
    merged = adjusted.merge(
        actuals,
        on=["entity_key", "forecast_date"],
        how="inner",
        validate="many_to_one",
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
    if merged.empty:
        raise ValueError("No rows after joining adjusted forecasts, actuals, and denominators.")
    merged["model_abs_error_adjusted"] = (
        merged["actual_value"] - merged["adjusted_forecast_value"]
    ).abs()
    merged["model_squared_error_adjusted"] = (
        merged["actual_value"] - merged["adjusted_forecast_value"]
    ) ** 2
    return merged


def _calculate_adjusted_mase(scoring_frame: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    rows = []
    for (entity_key, window_id, model_name), group in scoring_frame.groupby(
        ["entity_key", "window_id", "model_name"], sort=True
    ):
        mae_model = float(group["model_abs_error_adjusted"].mean())
        mae_naive = float(group["mase_denominator_mae"].iloc[0])
        rows.append(
            {
                "run_id": run_id,
                "entity_key": entity_key,
                "window_id": int(window_id),
                "model_name": model_name,
                "forecast_rows": int(len(group)),
                "mase": mae_model / mae_naive,
                "mae_model_adjusted": mae_model,
                "mae_naive": mae_naive,
                "denominator_floored": bool(group["mase_denominator_floored"].iloc[0]),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=MASE_COLUMNS)


def _calculate_adjusted_rmsse(scoring_frame: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    rows = []
    for (entity_key, window_id, model_name), group in scoring_frame.groupby(
        ["entity_key", "window_id", "model_name"], sort=True
    ):
        model_mse = float(group["model_squared_error_adjusted"].mean())
        naive_mse = float(group["rmsse_denominator_mse"].iloc[0])
        rmse_model = sqrt(model_mse)
        rmse_naive = sqrt(naive_mse)
        rmsse = sqrt(model_mse / naive_mse)
        rows.append(
            {
                "run_id": run_id,
                "entity_key": entity_key,
                "window_id": int(window_id),
                "model_name": model_name,
                "forecast_rows": int(len(group)),
                "rmsse": rmsse,
                "rmse_model_adjusted": rmse_model,
                "rmse_naive": rmse_naive,
                "denominator_floored": bool(group["rmsse_denominator_floored"].iloc[0]),
                "risk_status": _risk_status(rmsse),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=RMSSE_COLUMNS)


def _impact_by_model(adjusted: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for model_name, group in adjusted.groupby("model_name", sort=True):
        negative_rows = int(group["was_clipped"].sum())
        rows.append(
            {
                "model_name": model_name,
                "forecast_rows": len(group),
                "negative_forecast_rows": negative_rows,
                "pct_negative_forecast_rows": negative_rows / len(group),
                "min_original_forecast": float(group["original_forecast_value"].min()),
                "min_adjusted_forecast": float(group["adjusted_forecast_value"].min()),
                "max_original_forecast": float(group["original_forecast_value"].max()),
                "max_adjusted_forecast": float(group["adjusted_forecast_value"].max()),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=IMPACT_BY_MODEL_COLUMNS)


def _impact_by_entity(adjusted: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for entity_key, group in adjusted.groupby("entity_key", sort=True):
        negative_rows = int(group["was_clipped"].sum())
        rows.append(
            {
                "entity_key": entity_key,
                "forecast_rows": len(group),
                "negative_forecast_rows": negative_rows,
                "pct_negative_forecast_rows": negative_rows / len(group),
                "min_original_forecast": float(group["original_forecast_value"].min()),
                "min_adjusted_forecast": float(group["adjusted_forecast_value"].min()),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=IMPACT_BY_ENTITY_COLUMNS)


def _summary(adjusted, mase_adjusted, rmsse_adjusted, run_id: str, timestamp: str) -> pd.DataFrame:
    mase_before, rmsse_before = _load_previous_metric_medians()
    negative_rows = int(adjusted["was_clipped"].sum())
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "forecast_rows": len(adjusted),
                "adjusted_forecast_rows": negative_rows,
                "negative_forecast_rows": negative_rows,
                "pct_negative_forecast_rows": negative_rows / len(adjusted),
                "models": adjusted["model_name"].nunique(),
                "entities": adjusted["entity_key"].nunique(),
                "windows": adjusted[["entity_key", "window_id"]].drop_duplicates().shape[0],
                "original_min_forecast": float(adjusted["original_forecast_value"].min()),
                "adjusted_min_forecast": float(adjusted["adjusted_forecast_value"].min()),
                "mase_median_before": mase_before,
                "mase_median_after": float(mase_adjusted["mase"].median()),
                "rmsse_median_before": rmsse_before,
                "rmsse_median_after": float(rmsse_adjusted["rmsse"].median()),
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _write_outputs(adjusted, impact_model, impact_entity, mase_adjusted, rmsse_adjusted, summary) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    adjusted.to_csv(FORECASTS_OUTPUT, index=False)
    impact_model.to_csv(IMPACT_BY_MODEL_OUTPUT, index=False)
    impact_entity.to_csv(IMPACT_BY_ENTITY_OUTPUT, index=False)
    mase_adjusted.to_csv(MASE_OUTPUT, index=False)
    rmsse_adjusted.to_csv(RMSSE_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)


def apply_non_negative_policy() -> tuple[
    pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame
]:
    logger.info("Stage 5.23 non-negative forecast policy started")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    denominators, _ = build_and_write_denominators(
        run_id=f"denominator_reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=timestamp,
    )
    adjusted = _build_adjusted_forecasts(_load_forecasts(), run_id, timestamp)
    scoring_frame = _build_scoring_frame(adjusted, denominators, _actuals_for_forecast_dates())
    mase_adjusted = _calculate_adjusted_mase(scoring_frame, run_id, timestamp)
    rmsse_adjusted = _calculate_adjusted_rmsse(scoring_frame, run_id, timestamp)
    impact_model = _impact_by_model(adjusted, timestamp)
    impact_entity = _impact_by_entity(adjusted, timestamp)
    summary = _summary(adjusted, mase_adjusted, rmsse_adjusted, run_id, timestamp)

    logger.info("Forecast rows: %s", len(adjusted))
    logger.info("Negative forecast rows clipped: %s", int(adjusted["was_clipped"].sum()))
    logger.info("Adjusted MASE rows: %s", len(mase_adjusted))
    logger.info("Adjusted RMSSE rows: %s", len(rmsse_adjusted))
    _write_outputs(adjusted, impact_model, impact_entity, mase_adjusted, rmsse_adjusted, summary)
    logger.info("Stage 5.23 non-negative forecast policy completed")
    return adjusted, impact_model, impact_entity, mase_adjusted, rmsse_adjusted, summary


if __name__ == "__main__":
    apply_non_negative_policy()
