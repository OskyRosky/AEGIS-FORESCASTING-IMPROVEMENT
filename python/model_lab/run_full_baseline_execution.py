"""Full baseline production model backtest execution.

This Stage 5.10 script executes only BaselineProduction models across all
planned walk-forward windows. It does not run challengers, calculate metrics,
create rankings, publish tournament outputs, or modify execution.yaml.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.models.model_registry import get_model
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_full_baseline_execution")

TRAINING_JOB_PLAN = PROJECT_ROOT / "outputs" / "model_lab" / "training_job_plan.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
FULL_BASELINE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "full_baseline"
FULL_BASELINE_FORECASTS_OUTPUT = FULL_BASELINE_DIR / "full_baseline_forecasts.csv"
FULL_BASELINE_STATUS_OUTPUT = FULL_BASELINE_DIR / "full_baseline_execution_status.csv"
FULL_BASELINE_SUMMARY_OUTPUT = FULL_BASELINE_DIR / "full_baseline_summary.csv"

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
SUMMARY_COLUMNS = [
    "run_id",
    "windows_executed",
    "entities_executed",
    "models_executed",
    "jobs_planned",
    "jobs_executed",
    "jobs_failed",
    "forecast_rows",
    "created_timestamp",
]


def _require_file(path) -> None:
    """Validate that a required full-baseline input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required full-baseline input missing: {path}")


def _load_baseline_jobs() -> pd.DataFrame:
    """Load all planned baseline production jobs."""

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
    baseline_jobs = jobs[jobs["model_family"] == "BaselineProduction"].copy()
    baseline_jobs = baseline_jobs[baseline_jobs["model_name"].isin(BASELINE_MODELS)]
    unexpected_models = sorted(set(baseline_jobs["model_name"]) - set(BASELINE_MODELS))
    if unexpected_models:
        raise ValueError(f"Unexpected baseline models selected: {unexpected_models}")
    if len(baseline_jobs) != 3178:
        raise ValueError(f"Expected 3178 baseline jobs, found {len(baseline_jobs)}.")
    return baseline_jobs.sort_values(["entity_key", "window_id", "model_name"])


def _load_actuals() -> pd.DataFrame:
    """Load canonical actual rows used for training slices."""

    _require_file(EVALUATION_DATASET)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    if actuals.empty:
        raise ValueError("No actual rows found in evaluation dataset.")
    return actuals.sort_values(["entity_key", "date"])


def _training_slice(actuals_by_entity: dict[str, pd.DataFrame], job: pd.Series) -> pd.DataFrame:
    """Return training actuals strictly bounded by the job train window."""

    entity_actuals = actuals_by_entity.get(job["entity_key"])
    if entity_actuals is None:
        raise ValueError(f"No actuals found for entity {job['entity_key']}")
    mask = (
        (entity_actuals["date"] >= job["train_start_date"])
        & (entity_actuals["date"] <= job["train_end_date"])
    )
    training_data = entity_actuals.loc[mask, ["date", "value"]].sort_values("date")
    if training_data.empty:
        raise ValueError(f"No training actuals found for job {job['job_id']}")
    if training_data["date"].max() > job["train_end_date"]:
        raise ValueError(f"Training leakage detected for job {job['job_id']}")
    return training_data


def _forecast_dates(job: pd.Series) -> pd.DatetimeIndex:
    """Build the 30-day forecast horizon from the job test window."""

    dates = pd.date_range(job["test_start_date"], job["test_end_date"], freq="D")
    if len(dates) != 30:
        raise ValueError(f"Full baseline requires 30 dates for {job['job_id']}.")
    return dates


def _write_outputs(
    forecasts: pd.DataFrame, statuses: pd.DataFrame, summary: pd.DataFrame
) -> None:
    """Write all full baseline outputs."""

    FULL_BASELINE_DIR.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(FULL_BASELINE_FORECASTS_OUTPUT, index=False)
    statuses.to_csv(FULL_BASELINE_STATUS_OUTPUT, index=False)
    summary.to_csv(FULL_BASELINE_SUMMARY_OUTPUT, index=False)
    logger.info(
        "Created %s with %s rows", FULL_BASELINE_FORECASTS_OUTPUT, len(forecasts)
    )
    logger.info("Created %s with %s rows", FULL_BASELINE_STATUS_OUTPUT, len(statuses))
    logger.info("Created %s with %s rows", FULL_BASELINE_SUMMARY_OUTPUT, len(summary))


def run_full_baseline_execution() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute all baseline production jobs with per-job failure handling."""

    logger.info("Stage 5.10 full baseline execution started")
    run_id = f"full_baseline_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    jobs = _load_baseline_jobs()
    actuals = _load_actuals()
    actuals_by_entity = {
        entity_key: group.copy() for entity_key, group in actuals.groupby("entity_key")
    }
    forecast_rows = []
    status_rows = []

    for index, (_, job) in enumerate(jobs.iterrows(), start=1):
        try:
            training_data = _training_slice(actuals_by_entity, job)
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
            message = "Full baseline job completed."
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

        if index % 500 == 0:
            logger.info("Processed %s/%s baseline jobs", index, len(jobs))

    forecasts = pd.DataFrame(forecast_rows, columns=FORECAST_COLUMNS)
    statuses = pd.DataFrame(status_rows, columns=STATUS_COLUMNS)
    completed_jobs = statuses[statuses["status"] == "completed"]
    summary = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "windows_executed": completed_jobs[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "entities_executed": completed_jobs["entity_key"].nunique(),
                "models_executed": completed_jobs["model_name"].nunique(),
                "jobs_planned": len(jobs),
                "jobs_executed": int((statuses["status"] == "completed").sum()),
                "jobs_failed": int((statuses["status"] == "failed").sum()),
                "forecast_rows": len(forecasts),
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )

    _write_outputs(forecasts, statuses, summary)
    logger.info("Stage 5.10 full baseline execution completed")
    return forecasts, statuses, summary


if __name__ == "__main__":
    run_full_baseline_execution()
