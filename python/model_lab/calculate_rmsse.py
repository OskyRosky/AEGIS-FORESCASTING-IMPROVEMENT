"""Calculate RMSSE guardrail diagnostics for existing full-baseline forecasts.

This Stage 5.22 script calculates RMSSE only as a risk guardrail. It does not
rank models, select winners, create champions, or write tournament outputs.
"""

from __future__ import annotations

from datetime import datetime
from math import sqrt

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("calculate_rmsse")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
FULL_BASELINE_FORECASTS = (
    MODEL_LAB_DIR / "full_baseline" / "full_baseline_forecasts.csv"
)
NAIVE_FORECASTS = (
    MODEL_LAB_DIR / "benchmark_reference" / "naive_benchmark_forecasts.csv"
)
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "rmsse"
RMSSE_SCORES_OUTPUT = OUTPUT_DIR / "rmsse_scores.csv"
RMSSE_BY_MODEL_OUTPUT = OUTPUT_DIR / "rmsse_by_model.csv"
RMSSE_BY_ENTITY_OUTPUT = OUTPUT_DIR / "rmsse_by_entity.csv"
RMSSE_SUMMARY_OUTPUT = OUTPUT_DIR / "rmsse_guardrail_summary.csv"

RUN_ID_PREFIX = "rmsse"
FORECAST_HORIZON_DAYS = 30
EPSILON = 1e-6
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
    """Validate that a required input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required RMSSE input missing: {path}")


def _load_baseline_forecasts() -> pd.DataFrame:
    """Load existing full baseline forecasts."""

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
        raise ValueError(
            f"full_baseline_forecasts.csv missing columns: {sorted(missing)}"
        )
    forecasts = forecasts.copy()
    forecasts["window_id"] = forecasts["window_id"].astype(int)
    forecasts["forecast_value"] = pd.to_numeric(
        forecasts["forecast_value"], errors="coerce"
    )
    forecasts = forecasts.dropna(
        subset=["entity_key", "window_id", "model_name", "forecast_date", "forecast_value"]
    )
    return forecasts


def _load_naive_forecasts() -> pd.DataFrame:
    """Load lag-1 naive benchmark forecasts from Block 5.19."""

    _require_file(NAIVE_FORECASTS)
    naive = pd.read_csv(NAIVE_FORECASTS, parse_dates=["forecast_date"])
    required = {
        "entity_key",
        "window_id",
        "forecast_date",
        "horizon_day",
        "naive_forecast_value",
    }
    missing = required.difference(naive.columns)
    if missing:
        raise ValueError(f"naive_benchmark_forecasts.csv missing columns: {sorted(missing)}")
    naive = naive.copy()
    naive["window_id"] = naive["window_id"].astype(int)
    naive["naive_forecast_value"] = pd.to_numeric(
        naive["naive_forecast_value"], errors="coerce"
    )
    naive = naive.dropna(
        subset=["entity_key", "window_id", "forecast_date", "naive_forecast_value"]
    )
    return naive[
        ["entity_key", "window_id", "forecast_date", "horizon_day", "naive_forecast_value"]
    ]


def _load_actuals() -> pd.DataFrame:
    """Load actual values from the evaluation dataset."""

    _require_file(EVALUATION_DATASET)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    required = {"entity_key", "date", "value", "record_type"}
    missing = required.difference(actuals.columns)
    if missing:
        raise ValueError(f"evaluation_dataset.csv missing columns: {sorted(missing)}")
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["actual_value"] = pd.to_numeric(actuals["value"], errors="coerce")
    actuals = actuals.dropna(subset=["entity_key", "date", "actual_value"])
    if actuals.duplicated(["entity_key", "date"]).any():
        raise ValueError("Duplicate actual rows found for entity/date.")
    return actuals[["entity_key", "date", "actual_value"]].rename(
        columns={"date": "forecast_date"}
    )


def _load_valid_windows() -> pd.DataFrame:
    """Load valid backtesting windows used to count expected baseline jobs."""

    _require_file(WINDOWS_INPUT)
    windows = pd.read_csv(WINDOWS_INPUT)
    required = {"entity_key", "window_id", "forecast_horizon_days"}
    missing = required.difference(windows.columns)
    if missing:
        raise ValueError(f"backtesting_windows.csv missing columns: {sorted(missing)}")
    windows = windows[windows["forecast_horizon_days"] == FORECAST_HORIZON_DAYS].copy()
    windows["window_id"] = windows["window_id"].astype(int)
    return windows[["entity_key", "window_id"]].drop_duplicates()


def _build_scoring_frame(
    forecasts: pd.DataFrame, naive: pd.DataFrame, actuals: pd.DataFrame
) -> pd.DataFrame:
    """Join model forecasts, naive forecasts, and actuals by entity/window/date."""

    merged = forecasts.merge(
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
    if merged.empty:
        raise ValueError("No rows available after joining forecasts, naive, and actuals.")
    merged["model_squared_error"] = (
        merged["actual_value"] - merged["forecast_value"]
    ) ** 2
    merged["naive_squared_error"] = (
        merged["actual_value"] - merged["naive_forecast_value"]
    ) ** 2
    return merged


def _risk_status(rmsse: float) -> str:
    """Classify RMSSE risk without ranking or elimination."""

    if rmsse < 1.0:
        return "beats_naive"
    if rmsse < 2.0:
        return "acceptable"
    if rmsse < 5.0:
        return "warning"
    return "high_risk"


def _calculate_scores(
    scoring_frame: pd.DataFrame, run_id: str, timestamp: str
) -> pd.DataFrame:
    """Calculate RMSSE per entity/window/model."""

    grouped = scoring_frame.groupby(["entity_key", "window_id", "model_name"], sort=True)
    rows = []
    for (entity_key, window_id, model_name), group in grouped:
        forecast_rows = len(group)
        model_mse = float(group["model_squared_error"].mean())
        raw_naive_mse = float(group["naive_squared_error"].mean())
        denominator_floored = raw_naive_mse < EPSILON
        naive_mse = EPSILON if denominator_floored else raw_naive_mse
        rmse_model = sqrt(model_mse)
        rmse_naive = sqrt(naive_mse)
        rmsse = sqrt(model_mse / naive_mse)
        rows.append(
            {
                "run_id": run_id,
                "entity_key": entity_key,
                "window_id": int(window_id),
                "model_name": model_name,
                "forecast_rows": int(forecast_rows),
                "rmsse": rmsse,
                "rmse_model": rmse_model,
                "rmse_naive": rmse_naive,
                "denominator_floored": bool(denominator_floored),
                "risk_status": _risk_status(rmsse),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=RMSSE_SCORE_COLUMNS)


def _aggregate_by_model(scores: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    """Create model-level RMSSE guardrail diagnostics without rankings."""

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
    """Create entity-level RMSSE guardrail diagnostics without rankings."""

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
    """Create global RMSSE guardrail summary."""

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


def _write_outputs(
    scores: pd.DataFrame,
    by_model: pd.DataFrame,
    by_entity: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Write RMSSE guardrail outputs only."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    scores.to_csv(RMSSE_SCORES_OUTPUT, index=False)
    by_model.to_csv(RMSSE_BY_MODEL_OUTPUT, index=False)
    by_entity.to_csv(RMSSE_BY_ENTITY_OUTPUT, index=False)
    summary.to_csv(RMSSE_SUMMARY_OUTPUT, index=False)
    logger.info("Created %s with %s rows", RMSSE_SCORES_OUTPUT, len(scores))
    logger.info("Created %s with %s rows", RMSSE_BY_MODEL_OUTPUT, len(by_model))
    logger.info("Created %s with %s rows", RMSSE_BY_ENTITY_OUTPUT, len(by_entity))
    logger.info("Created %s with %s rows", RMSSE_SUMMARY_OUTPUT, len(summary))


def calculate_rmsse() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Calculate RMSSE guardrail diagnostics for all existing baseline jobs."""

    logger.info("Stage 5.22 RMSSE guardrail calculation started")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    forecasts = _load_baseline_forecasts()
    naive = _load_naive_forecasts()
    actuals = _load_actuals()
    valid_windows = _load_valid_windows()
    expected_jobs = len(valid_windows) * len(BASELINE_MODELS)

    scoring_frame = _build_scoring_frame(forecasts, naive, actuals)
    scores = _calculate_scores(scoring_frame, run_id, timestamp)
    by_model = _aggregate_by_model(scores, timestamp)
    by_entity = _aggregate_by_entity(scores, timestamp)
    summary = _create_summary(scores, run_id, timestamp)

    beats_naive = int((scores["rmsse"] < 1.0).sum())
    acceptable = int(((scores["rmsse"] >= 1.0) & (scores["rmsse"] < 2.0)).sum())
    warning = int(((scores["rmsse"] >= 2.0) & (scores["rmsse"] < 5.0)).sum())
    high_risk = int((scores["rmsse"] >= 5.0).sum())
    logger.info("Expected baseline jobs: %s", expected_jobs)
    logger.info("RMSSE metric rows: %s", len(scores))
    logger.info("RMSSE < 1: %s", beats_naive)
    logger.info("RMSSE 1-2: %s", acceptable)
    logger.info("RMSSE 2-5: %s", warning)
    logger.info("RMSSE >= 5: %s", high_risk)
    logger.info("pct_beating_naive: %.6f", float((scores["rmsse"] < 1.0).mean()))
    logger.info(
        "pct_high_risk: %.6f",
        float((scores["risk_status"] == "high_risk").mean()),
    )
    logger.info("RMSSE guardrail is diagnostic only; no ranking or winners created.")

    _write_outputs(scores, by_model, by_entity, summary)
    logger.info("Stage 5.22 RMSSE guardrail calculation completed")
    return scores, by_model, by_entity, summary


if __name__ == "__main__":
    calculate_rmsse()
