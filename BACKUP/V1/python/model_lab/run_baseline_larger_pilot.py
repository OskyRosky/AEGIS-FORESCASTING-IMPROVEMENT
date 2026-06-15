"""Larger controlled baseline production model pilot.

This Stage 5.9C script executes the seven BaselineProduction models for the
first ten eligible entities and one most-recent window per entity. It does not
modify execution.yaml, run challengers, calculate metrics, create rankings, or
launch the full baseline run.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.models.model_registry import get_model
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_baseline_larger_pilot")

TRAINING_JOB_PLAN = PROJECT_ROOT / "outputs" / "model_lab" / "training_job_plan.csv"
BACKTESTING_WINDOW_SUMMARY = (
    PROJECT_ROOT / "outputs" / "model_lab" / "backtesting_window_summary.csv"
)
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
PILOT_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "baseline_pilot"
PILOT_FORECASTS_OUTPUT = PILOT_DIR / "baseline_pilot_forecasts.csv"
PILOT_STATUS_OUTPUT = PILOT_DIR / "baseline_pilot_execution_status.csv"
PILOT_SUMMARY_OUTPUT = PILOT_DIR / "baseline_pilot_summary.csv"

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
    "entities_tested",
    "windows_tested",
    "models_tested",
    "jobs_planned",
    "jobs_executed",
    "jobs_failed",
    "forecast_rows",
    "created_timestamp",
]


def _require_file(path) -> None:
    """Validate that a required pilot input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required larger pilot input missing: {path}")


def _load_training_jobs() -> pd.DataFrame:
    """Load planned baseline jobs with parsed window dates."""

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


def _select_entities() -> list[str]:
    """Select the first ten eligible entities from the window summary."""

    _require_file(BACKTESTING_WINDOW_SUMMARY)
    summary = pd.read_csv(BACKTESTING_WINDOW_SUMMARY)
    entities = sorted(summary["entity_key"].dropna().unique())[:10]
    if len(entities) != 10:
        raise ValueError(f"Expected 10 eligible entities, found {len(entities)}.")
    logger.info("Selected larger pilot entities: %s", entities)
    return entities


def _select_pilot_jobs(baseline_jobs: pd.DataFrame) -> pd.DataFrame:
    """Select most-recent window for each selected entity and all baselines."""

    selected_rows = []
    for entity_key in _select_entities():
        entity_jobs = baseline_jobs[baseline_jobs["entity_key"] == entity_key]
        if entity_jobs.empty:
            raise ValueError(f"No baseline jobs found for entity {entity_key}.")

        window_id = int(entity_jobs["window_id"].max())
        window_jobs = entity_jobs[entity_jobs["window_id"] == window_id].copy()
        model_names = set(window_jobs["model_name"])
        if model_names != set(BASELINE_MODELS) or len(window_jobs) != len(BASELINE_MODELS):
            raise ValueError(
                f"Entity {entity_key} window {window_id} does not contain all baselines."
            )
        selected_rows.append(
            window_jobs.set_index("model_name").loc[BASELINE_MODELS].reset_index()
        )
        logger.info("Selected entity/window: %s/%s", entity_key, window_id)

    pilot_jobs = pd.concat(selected_rows, ignore_index=True)
    if len(pilot_jobs) != 70:
        raise ValueError(f"Expected 70 pilot jobs, found {len(pilot_jobs)}.")
    return pilot_jobs


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
        raise ValueError(f"Larger pilot requires 30 dates for {job['job_id']}.")
    return dates


def _write_outputs(
    forecasts: pd.DataFrame, statuses: pd.DataFrame, summary: pd.DataFrame
) -> None:
    """Write all larger pilot outputs."""

    PILOT_DIR.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(PILOT_FORECASTS_OUTPUT, index=False)
    statuses.to_csv(PILOT_STATUS_OUTPUT, index=False)
    summary.to_csv(PILOT_SUMMARY_OUTPUT, index=False)
    logger.info("Created %s with %s rows", PILOT_FORECASTS_OUTPUT, len(forecasts))
    logger.info("Created %s with %s rows", PILOT_STATUS_OUTPUT, len(statuses))
    logger.info("Created %s with %s rows", PILOT_SUMMARY_OUTPUT, len(summary))


def run_baseline_larger_pilot() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Execute the controlled 70-job baseline pilot."""

    logger.info("Stage 5.9C larger baseline pilot started")
    run_id = f"baseline_pilot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    pilot_jobs = _select_pilot_jobs(_load_training_jobs())
    actuals = _load_actuals()
    forecast_rows = []
    status_rows = []

    for _, job in pilot_jobs.iterrows():
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
            message = "Larger baseline pilot job completed."
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
                "entities_tested": pilot_jobs["entity_key"].nunique(),
                "windows_tested": pilot_jobs[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "models_tested": pilot_jobs["model_name"].nunique(),
                "jobs_planned": len(pilot_jobs),
                "jobs_executed": int((statuses["status"] == "completed").sum()),
                "jobs_failed": int((statuses["status"] == "failed").sum()),
                "forecast_rows": len(forecasts),
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )

    _write_outputs(forecasts, statuses, summary)
    logger.info("Stage 5.9C larger baseline pilot completed")
    return forecasts, statuses, summary


if __name__ == "__main__":
    run_baseline_larger_pilot()
