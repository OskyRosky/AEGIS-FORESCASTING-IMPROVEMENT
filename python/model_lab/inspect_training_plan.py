"""Inspect planned Model Lab training jobs.

This helper reads the Stage 5.5 job plan outputs and reports planning coverage.
It does not call fit(), call predict(), train models, generate forecasts,
calculate metrics, or create rankings.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_training_plan")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
TRAINING_JOB_PLAN_INPUT = MODEL_LAB_DIR / "training_job_plan.csv"
TRAINING_JOB_SUMMARY_INPUT = MODEL_LAB_DIR / "training_job_summary.csv"


def _require_input_file(path) -> None:
    """Fail fast when a training plan output is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required training plan output missing: {path}")


def inspect_training_plan() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Inspect planned training jobs and summary outputs."""

    _require_input_file(TRAINING_JOB_PLAN_INPUT)
    _require_input_file(TRAINING_JOB_SUMMARY_INPUT)

    job_plan = pd.read_csv(TRAINING_JOB_PLAN_INPUT)
    summary = pd.read_csv(TRAINING_JOB_SUMMARY_INPUT)

    logger.info("Total jobs: %s", len(job_plan))
    logger.info("Unique entities: %s", job_plan["entity_key"].nunique())
    logger.info(
        "Unique windows: %s",
        job_plan[["entity_key", "window_id"]].drop_duplicates().shape[0],
    )
    logger.info("Unique models: %s", job_plan["model_name"].nunique())
    logger.info("Jobs by model: %s", job_plan["model_name"].value_counts().to_dict())
    logger.info(
        "Jobs by model family: %s",
        job_plan["model_family"].value_counts().to_dict(),
    )
    logger.info("Train rows min: %s", int(job_plan["train_rows"].min()))
    logger.info("Train rows max: %s", int(job_plan["train_rows"].max()))
    logger.info("Test rows min: %s", int(job_plan["test_rows"].min()))
    logger.info("Test rows max: %s", int(job_plan["test_rows"].max()))
    logger.info("Summary rows: %s", len(summary))

    if not (job_plan["status"] == "planned").all():
        raise ValueError("Training plan contains jobs with non-planned status.")

    logger.info("Stage 5.5 training plan inspection passed")
    return job_plan, summary


if __name__ == "__main__":
    inspect_training_plan()
