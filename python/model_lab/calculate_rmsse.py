"""Calculate RMSSE guardrail diagnostics for existing full-baseline forecasts.

RMSSE uses the official training-only lag-1 naive MSE denominator by
entity/window. It does not use test-horizon naive forecast errors.
"""

from __future__ import annotations

from datetime import datetime
from math import sqrt

import pandas as pd

from model_lab.benchmark_denominators import (
    build_and_write_denominators,
    load_actuals,
    load_windows,
)
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("calculate_rmsse")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
FULL_BASELINE_FORECASTS = MODEL_LAB_DIR / "full_baseline" / "full_baseline_forecasts.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "rmsse"
RMSSE_SCORES_OUTPUT = OUTPUT_DIR / "rmsse_scores.csv"
RMSSE_BY_MODEL_OUTPUT = OUTPUT_DIR / "rmsse_by_model.csv"
RMSSE_BY_ENTITY_OUTPUT = OUTPUT_DIR / "rmsse_by_entity.csv"
RMSSE_SUMMARY_OUTPUT = OUTPUT_DIR / "rmsse_guardrail_summary.csv"

RUN_ID_PREFIX = "rmsse"
BASELINE_MODELS = [
    "ARIMA_Fixed",
    "ETS_Current",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
    "LinearRegression",
]

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


def _require_file(path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required RMSSE input missing: {path}")


def _load_baseline_forecasts() -> pd.DataFrame:
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
    forecasts["forecast_value"] = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
    return forecasts.dropna(
        subset=["entity_key", "window_id", "model_name", "forecast_date", "forecast_value"]
    )


def _actuals_for_forecast_dates() -> pd.DataFrame:
    actuals = load_actuals()
    return actuals[["entity_key", "date", "value"]].rename(
        columns={"date": "forecast_date", "value": "actual_value"}
    )


def _build_scoring_frame(
    forecasts: pd.DataFrame, denominators: pd.DataFrame, actuals: pd.DataFrame
) -> pd.DataFrame:
    merged = forecasts.merge(
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
                "rmsse_denominator_mse",
                "rmsse_denominator_floored",
            ]
        ],
        on=["entity_key", "window_id"],
        how="inner",
        validate="many_to_one",
    )
    if merged.empty:
        raise ValueError("No rows available after joining forecasts, actuals, and denominators.")
    merged["model_squared_error"] = (merged["actual_value"] - merged["forecast_value"]) ** 2
    return merged


def _risk_status(rmsse: float) -> str:
    if rmsse < 1.0:
        return "beats_naive"
    if rmsse < 2.0:
        return "acceptable"
    if rmsse < 5.0:
        return "warning"
    return "high_risk"


def _calculate_scores(scoring_frame: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    rows = []
    for (entity_key, window_id, model_name), group in scoring_frame.groupby(
        ["entity_key", "window_id", "model_name"], sort=True
    ):
        model_mse = float(group["model_squared_error"].mean())
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
                "rmse_model": rmse_model,
                "rmse_naive": rmse_naive,
                "denominator_floored": bool(group["rmsse_denominator_floored"].iloc[0]),
                "risk_status": _risk_status(rmsse),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=RMSSE_SCORE_COLUMNS)


def _aggregate_by_model(scores: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for model_name, group in scores.groupby("model_name", sort=True):
        rows.append(
            {
                "model_name": model_name,
                "metric_rows": len(group),
                "median_rmsse": float(group["rmsse"].median()),
                "mean_rmsse": float(group["rmsse"].mean()),
                "p95_rmsse": float(group["rmsse"].quantile(0.95)),
                "pct_beating_naive": float((group["rmsse"] < 1.0).mean()),
                "pct_high_risk": float((group["risk_status"] == "high_risk").mean()),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=RMSSE_BY_MODEL_COLUMNS)


def _aggregate_by_entity(scores: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    rows = []
    for entity_key, group in scores.groupby("entity_key", sort=True):
        rows.append(
            {
                "entity_key": entity_key,
                "metric_rows": len(group),
                "median_rmsse": float(group["rmsse"].median()),
                "mean_rmsse": float(group["rmsse"].mean()),
                "p95_rmsse": float(group["rmsse"].quantile(0.95)),
                "pct_high_risk": float((group["risk_status"] == "high_risk").mean()),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=RMSSE_BY_ENTITY_COLUMNS)


def _create_summary(scores: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "metric_rows": len(scores),
                "entities": scores["entity_key"].nunique(),
                "windows": scores[["entity_key", "window_id"]].drop_duplicates().shape[0],
                "models": scores["model_name"].nunique(),
                "global_median_rmsse": float(scores["rmsse"].median()),
                "global_mean_rmsse": float(scores["rmsse"].mean()),
                "pct_beating_naive": float((scores["rmsse"] < 1.0).mean()),
                "pct_high_risk": float((scores["risk_status"] == "high_risk").mean()),
                "created_timestamp": timestamp,
            }
        ],
        columns=RMSSE_SUMMARY_COLUMNS,
    )


def _write_outputs(scores, by_model, by_entity, summary) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scores.to_csv(RMSSE_SCORES_OUTPUT, index=False)
    by_model.to_csv(RMSSE_BY_MODEL_OUTPUT, index=False)
    by_entity.to_csv(RMSSE_BY_ENTITY_OUTPUT, index=False)
    summary.to_csv(RMSSE_SUMMARY_OUTPUT, index=False)


def calculate_rmsse() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    logger.info("Stage 5.22 RMSSE calculation started with training-only denominator")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    denominators, _ = build_and_write_denominators(
        run_id=f"denominator_reconciliation_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        timestamp=timestamp,
    )
    forecasts = _load_baseline_forecasts()
    actuals = _actuals_for_forecast_dates()
    valid_windows = load_windows()
    expected_jobs = len(valid_windows) * len(BASELINE_MODELS)

    scoring_frame = _build_scoring_frame(forecasts, denominators, actuals)
    scores = _calculate_scores(scoring_frame, run_id, timestamp)
    by_model = _aggregate_by_model(scores, timestamp)
    by_entity = _aggregate_by_entity(scores, timestamp)
    summary = _create_summary(scores, run_id, timestamp)

    logger.info("Expected baseline jobs: %s", expected_jobs)
    logger.info("RMSSE metric rows: %s", len(scores))
    logger.info("Training-only denominator rows: %s", len(denominators))
    logger.info("RMSSE < 1: %s", int((scores["rmsse"] < 1.0).sum()))
    logger.info("RMSSE 1-2: %s", int(((scores["rmsse"] >= 1.0) & (scores["rmsse"] < 2.0)).sum()))
    logger.info("RMSSE 2-5: %s", int(((scores["rmsse"] >= 2.0) & (scores["rmsse"] < 5.0)).sum()))
    logger.info("RMSSE >= 5: %s", int((scores["rmsse"] >= 5.0).sum()))
    _write_outputs(scores, by_model, by_entity, summary)
    logger.info("Stage 5.22 RMSSE calculation completed")
    return scores, by_model, by_entity, summary


if __name__ == "__main__":
    calculate_rmsse()
