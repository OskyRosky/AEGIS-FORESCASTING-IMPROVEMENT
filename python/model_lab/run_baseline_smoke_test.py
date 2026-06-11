"""Controlled baseline production model smoke test.

This Stage 5.9A script executes exactly one entity/window across the seven
BaselineProduction models. It does not modify execution.yaml, run challengers,
calculate metrics, create rankings, or publish tournament outputs.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.models.model_registry import get_model
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_baseline_smoke_test")

TRAINING_JOB_PLAN = PROJECT_ROOT / "outputs" / "model_lab" / "training_job_plan.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
SMOKE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "smoke_test"
SMOKE_FORECASTS_OUTPUT = SMOKE_DIR / "smoke_forecasts.csv"
SMOKE_STATUS_OUTPUT = SMOKE_DIR / "smoke_execution_status.csv"
SMOKE_SUMMARY_OUTPUT = SMOKE_DIR / "smoke_summary.csv"

BASELINE_MODELS = [
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
]
FORECAST_COLUMNS = [
    "run_id",
    "job_id",
    "entity_key",
    "window_id",
    "model_name",
    "model_family",
    "forecast_date",
    "horizon_day",
    "forecast_value",
    "created_timestamp",
]
STATUS_COLUMNS = [
    "run_id",
    "job_id",
    "entity_key",
    "window_id",
    "model_name",
    "status",
    "message",
    "created_timestamp",
]


def _require_file(path) -> None:
    """Validate that a required smoke-test input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required smoke-test input missing: {path}")


def _load_training_jobs() -> pd.DataFrame:
    """Load and filter planned baseline jobs."""

    _require_file(TRAINING_JOB_PLAN)
    jobs = pd.read_csv(
        TRAINING_JOB_PLAN,
        parse_dates=[
            "train_start_date",
            "train_end_date",
            "test_start_date",
            "test_end_date",
        ],
    )
    baseline_jobs = jobs[jobs["model_name"].isin(BASELINE_MODELS)].copy()
    if baseline_jobs.empty:
        raise ValueError("No baseline jobs found in training_job_plan.csv.")
    return baseline_jobs


def _select_smoke_jobs(baseline_jobs: pd.DataFrame) -> pd.DataFrame:
    """Select one entity/window containing all seven baseline models."""

    grouped = baseline_jobs.groupby(["entity_key", "window_id"], sort=True)
    for (entity_key, window_id), group in grouped:
        model_names = set(group["model_name"])
        if model_names == set(BASELINE_MODELS) and len(group) == len(BASELINE_MODELS):
            logger.info("Selected smoke entity/window: %s/%s", entity_key, window_id)
            return (
                group.set_index("model_name")
                .loc[BASELINE_MODELS]
                .reset_index()
                .copy()
            )

    raise ValueError("Could not find one entity/window with all seven baseline jobs.")


def _load_actuals() -> pd.DataFrame:
    """Load canonical actual rows used for training slices."""

    _require_file(EVALUATION_DATASET)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    if actuals.empty:
        raise ValueError("No actual rows found in evaluation dataset.")
    return actuals


def _training_slice(actuals: pd.DataFrame, job: pd.Series) -> pd.DataFrame:
    """Return training actuals strictly bounded by the job train window."""

    mask = (
        (actuals["entity_key"] == job["entity_key"])
        & (actuals["date"] >= job["train_start_date"])
        & (actuals["date"] <= job["train_end_date"])
    )
    training_data = actuals.loc[mask, ["date", "value"]].sort_values("date")
    if training_data.empty:
        raise ValueError(f"No training actuals found for job {job['job_id']}")
    if training_data["date"].max() > job["train_end_date"]:
        raise ValueError(f"Training leakage detected for job {job['job_id']}")
    return training_data


def _forecast_dates(job: pd.Series) -> pd.DatetimeIndex:
    """Build the 30-day forecast horizon from the job test window."""

    dates = pd.date_range(job["test_start_date"], job["test_end_date"], freq="D")
    if len(dates) != 30:
        raise ValueError(f"Smoke test requires 30 forecast dates for {job['job_id']}.")
    return dates


def _write_outputs(
    forecasts: pd.DataFrame, statuses: pd.DataFrame, summary: pd.DataFrame
) -> None:
    """Write all smoke-test outputs."""

    SMOKE_DIR.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(SMOKE_FORECASTS_OUTPUT, index=False)
    statuses.to_csv(SMOKE_STATUS_OUTPUT, index=False)
    summary.to_csv(SMOKE_SUMMARY_OUTPUT, index=False)
    logger.info("Created %s with %s rows", SMOKE_FORECASTS_OUTPUT, len(forecasts))
    logger.info("Created %s with %s rows", SMOKE_STATUS_OUTPUT, len(statuses))
    logger.info("Created %s with %s rows", SMOKE_SUMMARY_OUTPUT, len(summary))


def run_baseline_smoke_test() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute the controlled seven-job baseline smoke test."""

    logger.info("Stage 5.9A baseline smoke test started")
    run_id = f"smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    smoke_jobs = _select_smoke_jobs(_load_training_jobs())
    actuals = _load_actuals()
    forecast_rows = []
    status_rows = []

    for _, job in smoke_jobs.iterrows():
        try:
            training_data = _training_slice(actuals, job)
            model = get_model(job["model_name"])()
            model.fit(training_data)
            dates = _forecast_dates(job)
            predictions = model.predict(len(dates))

            if len(predictions) != len(dates):
                raise ValueError(f"Forecast length mismatch for job {job['job_id']}.")

            for horizon_day, (forecast_date, forecast_value) in enumerate(
                zip(dates, predictions), start=1
            ):
                forecast_rows.append(
                    {
                        "run_id": run_id,
                        "job_id": job["job_id"],
                        "entity_key": job["entity_key"],
                        "window_id": int(job["window_id"]),
                        "model_name": job["model_name"],
                        "model_family": job["model_family"],
                        "forecast_date": forecast_date.date(),
                        "horizon_day": horizon_day,
                        "forecast_value": float(forecast_value),
                        "created_timestamp": timestamp,
                    }
                )
            status = "completed"
            message = "Smoke test job completed."
        except Exception as exc:  # pragma: no cover - operational status path
            status = "failed"
            message = f"{type(exc).__name__}: {exc}"

        status_rows.append(
            {
                "run_id": run_id,
                "job_id": job["job_id"],
                "entity_key": job["entity_key"],
                "window_id": int(job["window_id"]),
                "model_name": job["model_name"],
                "status": status,
                "message": message,
                "created_timestamp": timestamp,
            }
        )

    forecasts = pd.DataFrame(forecast_rows, columns=FORECAST_COLUMNS)
    statuses = pd.DataFrame(status_rows, columns=STATUS_COLUMNS)
    summary = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "entity_key": smoke_jobs["entity_key"].iloc[0],
                "window_id": int(smoke_jobs["window_id"].iloc[0]),
                "jobs_planned": len(smoke_jobs),
                "jobs_executed": int((statuses["status"] == "completed").sum()),
                "jobs_failed": int((statuses["status"] == "failed").sum()),
                "forecast_rows": len(forecasts),
                "models": ";".join(BASELINE_MODELS),
                "created_timestamp": timestamp,
            }
        ]
    )

    _write_outputs(forecasts, statuses, summary)
    logger.info("Stage 5.9A baseline smoke test completed")
    return forecasts, statuses, summary


if __name__ == "__main__":
    run_baseline_smoke_test()
