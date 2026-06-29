"""Create planned Model Lab training jobs without executing training.

This Stage 5.5 scaffold prepares the orchestration layer that will later run
registered models across walk-forward windows. It does not call fit(), call
predict(), generate forecasts, calculate metrics, or create rankings.
"""

from __future__ import annotations

import pandas as pd

from model_lab.load_configs import load_all_configs
from model_lab.models.model_registry import get_model, list_models
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("training_orchestrator")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
FEATURE_DATASET_INPUT = MODEL_LAB_DIR / "features" / "feature_dataset.csv"
TRAINING_JOB_PLAN_OUTPUT = MODEL_LAB_DIR / "training_job_plan.csv"
TRAINING_JOB_SUMMARY_OUTPUT = MODEL_LAB_DIR / "training_job_summary.csv"

JOB_COLUMNS = [
    "job_id",
    "entity_key",
    "window_id",
    "model_name",
    "model_family",
    "train_start_date",
    "train_end_date",
    "test_start_date",
    "test_end_date",
    "train_rows",
    "test_rows",
    "status",
]


def _require_input_file(path) -> None:
    """Fail fast when an orchestration input is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required orchestration input missing: {path}")


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Load configs, walk-forward windows, and feature dataset."""

    _require_input_file(WINDOWS_INPUT)
    _require_input_file(FEATURE_DATASET_INPUT)

    configs = load_all_configs()
    windows = pd.read_csv(
        WINDOWS_INPUT,
        parse_dates=[
            "train_start_date",
            "train_end_date",
            "test_start_date",
            "test_end_date",
        ],
    )
    features = pd.read_csv(FEATURE_DATASET_INPUT, parse_dates=["date"])
    return windows, features, configs


def _count_rows(features: pd.DataFrame, entity_key: str, start_date, end_date) -> int:
    """Count feature rows for one entity over an inclusive date range."""

    mask = (
        (features["entity_key"] == entity_key)
        & (features["date"] >= start_date)
        & (features["date"] <= end_date)
    )
    return int(mask.sum())


def _build_training_job_plan(
    windows: pd.DataFrame, features: pd.DataFrame
) -> pd.DataFrame:
    """Build one planned job per registered model and backtesting window."""

    rows = []
    job_sequence = 1
    model_names = list_models()

    for _, window in windows.sort_values(["entity_key", "window_id"]).iterrows():
        entity_key = window["entity_key"]
        train_rows = _count_rows(
            features, entity_key, window["train_start_date"], window["train_end_date"]
        )
        test_rows = _count_rows(
            features, entity_key, window["test_start_date"], window["test_end_date"]
        )

        for model_name in model_names:
            model_class = get_model(model_name)
            rows.append(
                {
                    "job_id": f"job_{job_sequence:06d}",
                    "entity_key": entity_key,
                    "window_id": int(window["window_id"]),
                    "model_name": model_name,
                    "model_family": model_class.model_family,
                    "train_start_date": window["train_start_date"].date(),
                    "train_end_date": window["train_end_date"].date(),
                    "test_start_date": window["test_start_date"].date(),
                    "test_end_date": window["test_end_date"].date(),
                    "train_rows": train_rows,
                    "test_rows": test_rows,
                    "status": "planned",
                }
            )
            job_sequence += 1

    return pd.DataFrame(rows, columns=JOB_COLUMNS)


def _build_summary(job_plan: pd.DataFrame) -> pd.DataFrame:
    """Build a one-row training job plan summary."""

    return pd.DataFrame(
        [
            {
                "total_jobs": len(job_plan),
                "entity_count": job_plan["entity_key"].nunique(),
                "window_count": job_plan[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "model_count": job_plan["model_name"].nunique(),
                "models_planned": ";".join(sorted(job_plan["model_name"].unique())),
                "families_planned": ";".join(
                    sorted(job_plan["model_family"].unique())
                ),
                "min_train_rows": int(job_plan["train_rows"].min()),
                "max_train_rows": int(job_plan["train_rows"].max()),
                "min_test_rows": int(job_plan["test_rows"].min()),
                "max_test_rows": int(job_plan["test_rows"].max()),
            }
        ]
    )


def _validate_job_plan(job_plan: pd.DataFrame, windows: pd.DataFrame) -> None:
    """Validate planned jobs without executing models."""

    expected_jobs = len(windows) * len(list_models())
    if len(job_plan) != expected_jobs:
        raise ValueError(f"Expected {expected_jobs} jobs, found {len(job_plan)}")
    if set(job_plan["model_name"].unique()) != set(list_models()):
        raise ValueError("Job plan does not include all registered models.")
    if not (job_plan["status"] == "planned").all():
        raise ValueError("All training jobs must have status='planned'.")
    if (job_plan["train_rows"] <= 0).any() or (job_plan["test_rows"] <= 0).any():
        raise ValueError("Job plan contains non-positive train or test row counts.")


def create_training_job_plan() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create and save planned training jobs and summary outputs."""

    logger.info("Stage 5.5 training orchestration planning started")
    windows, features, configs = _load_inputs()
    logger.info("Loaded config sections: %s", list(configs.keys()))
    logger.info("Backtesting windows loaded: %s", len(windows))
    logger.info("Feature dataset rows loaded: %s", len(features))
    logger.info("Registered models loaded: %s", list_models())

    job_plan = _build_training_job_plan(windows, features)
    _validate_job_plan(job_plan, windows)
    summary = _build_summary(job_plan)

    job_plan.to_csv(TRAINING_JOB_PLAN_OUTPUT, index=False)
    summary.to_csv(TRAINING_JOB_SUMMARY_OUTPUT, index=False)

    logger.info("Created %s with %s rows", TRAINING_JOB_PLAN_OUTPUT, len(job_plan))
    logger.info("Created %s with %s rows", TRAINING_JOB_SUMMARY_OUTPUT, len(summary))
    logger.info("Stage 5.5 training orchestration planning completed")

    return job_plan, summary


if __name__ == "__main__":
    create_training_job_plan()
