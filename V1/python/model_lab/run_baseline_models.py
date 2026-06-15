"""Guarded baseline production model execution runner.

This Stage 5.9 runner executes only BaselineProduction models when execution
controls allow it. With the current default controls it writes skipped status
rows and does not call fit(), call predict(), train models, generate forecasts,
calculate metrics, or create rankings.
"""

from __future__ import annotations

import os
from datetime import datetime

import pandas as pd

from model_lab.load_configs import load_yaml_config
from model_lab.models.model_registry import get_model
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_baseline_models")

EXECUTION_CONFIG = PROJECT_ROOT / "config" / "execution.yaml"
MULTISTEP_CONFIG = PROJECT_ROOT / "config" / "multistep_forecasting.yaml"
TRAINING_JOB_PLAN = PROJECT_ROOT / "outputs" / "model_lab" / "training_job_plan.csv"
RUN_MANIFEST = PROJECT_ROOT / "outputs" / "model_lab" / "runs" / "run_manifest.csv"
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
FORECASTS_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "forecasts"
BASELINE_FORECASTS_OUTPUT = FORECASTS_DIR / "baseline_forecasts.csv"
BASELINE_STATUS_OUTPUT = FORECASTS_DIR / "baseline_execution_status.csv"

BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}
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
    """Validate that a required runner input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required baseline runner input missing: {path}")


def _load_inputs() -> tuple[dict, dict, pd.DataFrame, pd.Series]:
    """Load execution controls, strategy config, baseline jobs, and manifest."""

    for path in (EXECUTION_CONFIG, MULTISTEP_CONFIG, TRAINING_JOB_PLAN, RUN_MANIFEST):
        _require_file(path)
        logger.info("Found file: %s", path)

    execution_config = load_yaml_config(EXECUTION_CONFIG)
    multistep_config = load_yaml_config(MULTISTEP_CONFIG)
    job_plan = pd.read_csv(
        TRAINING_JOB_PLAN,
        parse_dates=[
            "train_start_date",
            "train_end_date",
            "test_start_date",
            "test_end_date",
        ],
    )
    manifest = pd.read_csv(RUN_MANIFEST)
    if manifest.empty:
        raise ValueError("run_manifest.csv is empty.")

    baseline_jobs = job_plan[job_plan["model_name"].isin(BASELINE_MODELS)].copy()
    if baseline_jobs.empty:
        raise ValueError("No baseline production jobs found in training job plan.")

    unexpected_models = sorted(set(baseline_jobs["model_name"]) - BASELINE_MODELS)
    if unexpected_models:
        raise ValueError(f"Unexpected baseline runner models: {unexpected_models}")

    return execution_config, multistep_config, baseline_jobs, manifest.iloc[0]


def _write_outputs(forecasts: pd.DataFrame, statuses: pd.DataFrame) -> None:
    """Write baseline forecast and execution status outputs."""

    FORECASTS_DIR.mkdir(parents=True, exist_ok=True)
    forecasts.to_csv(BASELINE_FORECASTS_OUTPUT, index=False)
    statuses.to_csv(BASELINE_STATUS_OUTPUT, index=False)
    logger.info("Created %s with %s rows", BASELINE_FORECASTS_OUTPUT, len(forecasts))
    logger.info("Created %s with %s rows", BASELINE_STATUS_OUTPUT, len(statuses))


def _build_status_rows(
    jobs: pd.DataFrame, run_id: str, status: str, message: str
) -> pd.DataFrame:
    """Build one status row per baseline job."""

    timestamp = datetime.now().isoformat(timespec="seconds")
    rows = [
        {
            "run_id": run_id,
            "job_id": row["job_id"],
            "entity_key": row["entity_key"],
            "window_id": int(row["window_id"]),
            "model_name": row["model_name"],
            "status": status,
            "message": message,
            "created_timestamp": timestamp,
        }
        for _, row in jobs.iterrows()
    ]
    return pd.DataFrame(rows, columns=STATUS_COLUMNS)


def _validate_linear_regression_strategy(multistep_config: dict) -> None:
    """Ensure LinearRegression is governed by recursive no-future-actual strategy."""

    strategy = multistep_config["strategies"]["linear_and_ml_models"]
    if strategy.get("strategy") != "recursive":
        raise ValueError("LinearRegression requires recursive multistep strategy.")
    if strategy.get("allow_actuals_inside_forecast_horizon") is not False:
        raise ValueError("LinearRegression must not use actuals inside forecast horizon.")


def _load_actuals() -> pd.DataFrame:
    """Load canonical actuals for baseline model training windows."""

    _require_file(EVALUATION_DATASET)
    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    if actuals.empty:
        raise ValueError("No actual rows found in evaluation dataset.")
    return actuals


def _training_slice(actuals: pd.DataFrame, job: pd.Series) -> pd.DataFrame:
    """Return one entity's train-window actuals."""

    mask = (
        (actuals["entity_key"] == job["entity_key"])
        & (actuals["date"] >= job["train_start_date"])
        & (actuals["date"] <= job["train_end_date"])
    )
    training_data = actuals.loc[mask, ["date", "value"]].sort_values("date")
    if training_data.empty:
        raise ValueError(f"No training actuals found for job {job['job_id']}")
    return training_data


def _forecast_dates(job: pd.Series) -> pd.DatetimeIndex:
    """Build forecast dates from a job's test window."""

    return pd.date_range(job["test_start_date"], job["test_end_date"], freq="D")


def _execute_smoke_jobs(
    jobs: pd.DataFrame, run_id: str, multistep_config: dict
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Execute an explicit limited smoke test for baseline models only."""

    _validate_linear_regression_strategy(multistep_config)
    actuals = _load_actuals()
    max_jobs = int(os.environ.get("BASELINE_MAX_JOBS", "3"))
    smoke_jobs = jobs.sort_values(["entity_key", "window_id", "model_name"]).head(
        max_jobs
    )
    timestamp = datetime.now().isoformat(timespec="seconds")
    forecast_rows = []
    status_rows = []

    for _, job in smoke_jobs.iterrows():
        try:
            training_data = _training_slice(actuals, job)
            model_class = get_model(job["model_name"])
            model = model_class()
            model.fit(training_data)
            dates = _forecast_dates(job)
            predictions = model.predict(len(dates))
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
            message = "Baseline smoke test job completed."
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

    skipped_jobs = jobs[~jobs["job_id"].isin(set(smoke_jobs["job_id"]))]
    if not skipped_jobs.empty:
        skipped_status = _build_status_rows(
            skipped_jobs,
            run_id,
            "skipped",
            "Skipped by explicit limited smoke test mode.",
        )
        status_rows.extend(skipped_status.to_dict("records"))

    return (
        pd.DataFrame(forecast_rows, columns=FORECAST_COLUMNS),
        pd.DataFrame(status_rows, columns=STATUS_COLUMNS),
    )


def run_baseline_models() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run or safely skip baseline production jobs according to execution controls."""

    logger.info("Stage 5.9 baseline production runner started")
    execution_config, multistep_config, baseline_jobs, manifest_row = _load_inputs()
    run_id = str(manifest_row["run_id"])
    training_enabled = bool(execution_config.get("training_enabled", False))
    dry_run = bool(execution_config.get("dry_run", True))
    logger.info("Baseline jobs loaded: %s", len(baseline_jobs))
    logger.info("Training enabled: %s", training_enabled)
    logger.info("Dry run: %s", dry_run)

    if not training_enabled:
        forecasts = pd.DataFrame(columns=FORECAST_COLUMNS)
        statuses = _build_status_rows(
            baseline_jobs,
            run_id,
            "blocked_by_config",
            "Training disabled by execution.yaml. No baseline jobs executed.",
        )
        _write_outputs(forecasts, statuses)
        logger.info("Stage 5.9 baseline production runner blocked by config")
        return forecasts, statuses

    if dry_run:
        forecasts = pd.DataFrame(columns=FORECAST_COLUMNS)
        statuses = _build_status_rows(
            baseline_jobs,
            run_id,
            "dry_run_only",
            "Dry-run mode enabled by execution.yaml. No baseline jobs executed.",
        )
        _write_outputs(forecasts, statuses)
        logger.info("Stage 5.9 baseline production runner completed dry-run only")
        return forecasts, statuses

    if os.environ.get("BASELINE_SMOKE_TEST") != "true":
        raise NotImplementedError(
            "Full baseline execution is not enabled. Set BASELINE_SMOKE_TEST=true "
            "for explicit limited smoke test mode."
        )

    forecasts, statuses = _execute_smoke_jobs(baseline_jobs, run_id, multistep_config)
    _write_outputs(forecasts, statuses)
    logger.info("Stage 5.9 baseline production smoke test completed")
    return forecasts, statuses


if __name__ == "__main__":
    run_baseline_models()
