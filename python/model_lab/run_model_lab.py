"""Guarded Model Lab execution entry point.

This Stage 5.7 entry point enforces execution controls before any future model
execution path can run. It does not call fit(), call predict(), train models,
generate forecasts, calculate metrics, or create rankings.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.load_configs import load_yaml_config
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("run_model_lab")

EXECUTION_CONFIG = PROJECT_ROOT / "config" / "execution.yaml"
MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
RUNS_DIR = MODEL_LAB_DIR / "runs"
TRAINING_JOB_PLAN = MODEL_LAB_DIR / "training_job_plan.csv"
RUN_MANIFEST = RUNS_DIR / "run_manifest.csv"
EXECUTION_AUDIT_OUTPUT = RUNS_DIR / "execution_audit.csv"

AUDIT_COLUMNS = [
    "run_id",
    "execution_timestamp",
    "training_enabled",
    "dry_run",
    "planned_jobs",
    "executed_jobs",
    "skipped_jobs",
    "status",
    "message",
]


def _require_file(path) -> None:
    """Validate that a required input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required execution input missing: {path}")


def _load_inputs() -> tuple[dict, pd.DataFrame, pd.Series]:
    """Load execution controls, planned jobs, and latest run manifest row."""

    for path in (EXECUTION_CONFIG, TRAINING_JOB_PLAN, RUN_MANIFEST):
        _require_file(path)
        logger.info("Found file: %s", path)

    execution_config = load_yaml_config(EXECUTION_CONFIG)
    job_plan = pd.read_csv(TRAINING_JOB_PLAN)
    manifest = pd.read_csv(RUN_MANIFEST)

    if manifest.empty:
        raise ValueError("run_manifest.csv is empty.")
    if job_plan.empty:
        raise ValueError("training_job_plan.csv is empty.")

    return execution_config, job_plan, manifest.iloc[0]


def _write_execution_audit(
    *,
    run_id: str,
    training_enabled: bool,
    dry_run: bool,
    planned_jobs: int,
    executed_jobs: int,
    skipped_jobs: int,
    status: str,
    message: str,
) -> pd.DataFrame:
    """Persist one execution audit row."""

    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    audit = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "execution_timestamp": datetime.now().isoformat(timespec="seconds"),
                "training_enabled": training_enabled,
                "dry_run": dry_run,
                "planned_jobs": planned_jobs,
                "executed_jobs": executed_jobs,
                "skipped_jobs": skipped_jobs,
                "status": status,
                "message": message,
            }
        ],
        columns=AUDIT_COLUMNS,
    )
    audit.to_csv(EXECUTION_AUDIT_OUTPUT, index=False)
    logger.info("Created %s with %s rows", EXECUTION_AUDIT_OUTPUT, len(audit))
    logger.info("Execution audit status: %s", status)
    logger.info("Executed jobs: %s", executed_jobs)
    logger.info("Skipped jobs: %s", skipped_jobs)
    return audit


def run_model_lab() -> pd.DataFrame:
    """Apply execution gates and write an audit without executing models."""

    logger.info("Stage 5.7 guarded Model Lab execution started")
    execution_config, job_plan, manifest_row = _load_inputs()

    training_enabled = bool(execution_config.get("training_enabled", False))
    dry_run = bool(execution_config.get("dry_run", True))
    planned_jobs = len(job_plan)
    manifest_planned_jobs = int(manifest_row["planned_jobs"])

    if manifest_planned_jobs != planned_jobs:
        raise ValueError("Manifest planned_jobs does not match training job plan.")

    logger.info("Training enabled: %s", training_enabled)
    logger.info("Dry run: %s", dry_run)
    logger.info("Planned jobs: %s", planned_jobs)

    if not training_enabled:
        message = "Training disabled by execution.yaml. No jobs executed."
        logger.info(message)
        audit = _write_execution_audit(
            run_id=str(manifest_row["run_id"]),
            training_enabled=training_enabled,
            dry_run=dry_run,
            planned_jobs=planned_jobs,
            executed_jobs=0,
            skipped_jobs=planned_jobs,
            status="blocked_by_config",
            message=message,
        )
        logger.info("Stage 5.7 guarded Model Lab execution completed")
        return audit

    if dry_run:
        message = "Dry-run mode enabled by execution.yaml. No jobs executed."
        logger.info(message)
        audit = _write_execution_audit(
            run_id=str(manifest_row["run_id"]),
            training_enabled=training_enabled,
            dry_run=dry_run,
            planned_jobs=planned_jobs,
            executed_jobs=0,
            skipped_jobs=planned_jobs,
            status="dry_run_only",
            message=message,
        )
        logger.info("Stage 5.7 guarded Model Lab execution completed")
        return audit

    message = "Real model execution is not implemented yet."
    _write_execution_audit(
        run_id=str(manifest_row["run_id"]),
        training_enabled=training_enabled,
        dry_run=dry_run,
        planned_jobs=planned_jobs,
        executed_jobs=0,
        skipped_jobs=planned_jobs,
        status="execution_not_implemented",
        message=message,
    )
    raise NotImplementedError(message)


if __name__ == "__main__":
    run_model_lab()
