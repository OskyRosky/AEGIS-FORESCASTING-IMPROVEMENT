"""Validate Model Lab execution controls and dry-run manifest.

This Stage 5.6 validation confirms training is disabled and dry-run mode is
active. It does not call fit(), call predict(), train models, generate
forecasts, calculate metrics, or create rankings.
"""

from __future__ import annotations

import pandas as pd

from model_lab.load_configs import load_yaml_config
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("validate_execution_controls")

EXECUTION_CONFIG = PROJECT_ROOT / "config" / "execution.yaml"
MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
RUNS_DIR = MODEL_LAB_DIR / "runs"
TRAINING_JOB_PLAN = MODEL_LAB_DIR / "training_job_plan.csv"
RUN_MANIFEST = RUNS_DIR / "run_manifest.csv"
RUN_METADATA = RUNS_DIR / "run_metadata.csv"


def _require_file(path) -> None:
    """Validate that a required file exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")


def validate_execution_controls() -> None:
    """Validate Stage 5.6 dry-run execution controls."""

    logger.info("Stage 5.6 execution control validation started")

    for path in (EXECUTION_CONFIG, TRAINING_JOB_PLAN, RUN_MANIFEST, RUN_METADATA):
        _require_file(path)
        logger.info("Found file: %s", path)

    execution_config = load_yaml_config(EXECUTION_CONFIG)
    if execution_config.get("training_enabled") is not False:
        raise ValueError("training_enabled must be false for Stage 5.6.")
    if execution_config.get("dry_run") is not True:
        raise ValueError("dry_run must be true for Stage 5.6.")

    manifest = pd.read_csv(RUN_MANIFEST)
    if manifest.empty:
        raise ValueError("run_manifest.csv is empty.")
    manifest_row = manifest.iloc[0]

    if bool(manifest_row["training_enabled"]) is not False:
        raise ValueError("Manifest training_enabled must be false.")
    if bool(manifest_row["dry_run"]) is not True:
        raise ValueError("Manifest dry_run must be true.")
    if manifest_row["status"] != "planned":
        raise ValueError("Manifest status must be planned.")

    job_plan = pd.read_csv(TRAINING_JOB_PLAN)
    if int(manifest_row["planned_jobs"]) != len(job_plan):
        raise ValueError("Manifest planned_jobs does not match training job plan.")

    logger.info("Training enabled: %s", execution_config["training_enabled"])
    logger.info("Dry run: %s", execution_config["dry_run"])
    logger.info("Manifest run_id: %s", manifest_row["run_id"])
    logger.info("Planned jobs: %s", int(manifest_row["planned_jobs"]))
    logger.info("Stage 5.6 execution control validation passed")


if __name__ == "__main__":
    validate_execution_controls()
