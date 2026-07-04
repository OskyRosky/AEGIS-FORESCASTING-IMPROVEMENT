"""Create a Model Lab dry-run execution manifest.

This Stage 5.6 script records execution controls and planned training coverage.
It does not call fit(), call predict(), train models, generate forecasts,
calculate metrics, or create rankings.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.load_configs import load_yaml_config
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("create_run_manifest")

EXECUTION_CONFIG = PROJECT_ROOT / "config" / "execution.yaml"
MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
RUNS_DIR = MODEL_LAB_DIR / "runs"
TRAINING_JOB_PLAN = MODEL_LAB_DIR / "training_job_plan.csv"
RUN_MANIFEST_OUTPUT = RUNS_DIR / "run_manifest.csv"
RUN_METADATA_OUTPUT = RUNS_DIR / "run_metadata.csv"
RUN_MANIFEST_HISTORY_OUTPUT = RUNS_DIR / "run_manifest_history.csv"
RUN_METADATA_HISTORY_OUTPUT = RUNS_DIR / "run_metadata_history.csv"


def _require_input_file(path) -> None:
    """Fail fast when a required input is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required input missing: {path}")


def _build_run_id(timestamp: datetime) -> str:
    """Create a deterministic timestamp-based run id."""

    return f"run_{timestamp.strftime('%Y%m%d_%H%M%S')}"


def _append_history(frame: pd.DataFrame, path) -> None:
    """Append rows to a history CSV, creating it with headers when missing."""

    frame.to_csv(path, mode="a", header=not path.exists(), index=False)


def create_run_manifest() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create run manifest and run metadata outputs."""

    logger.info("Stage 5.6 run manifest creation started")
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    _require_input_file(EXECUTION_CONFIG)
    _require_input_file(TRAINING_JOB_PLAN)

    execution_config = load_yaml_config(EXECUTION_CONFIG)
    job_plan = pd.read_csv(TRAINING_JOB_PLAN)
    timestamp = datetime.now()
    run_id = _build_run_id(timestamp)

    manifest = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "run_timestamp": timestamp.isoformat(timespec="seconds"),
                "training_enabled": bool(execution_config["training_enabled"]),
                "dry_run": bool(execution_config["dry_run"]),
                "planned_jobs": len(job_plan),
                "entity_count": job_plan["entity_key"].nunique(),
                "window_count": job_plan[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "model_count": job_plan["model_name"].nunique(),
                "models": ";".join(sorted(job_plan["model_name"].unique())),
                "model_families": ";".join(
                    sorted(job_plan["model_family"].unique())
                ),
                "status": "planned",
            }
        ]
    )
    metadata = pd.DataFrame(
        [
            {
                "run_id": run_id,
                "created_at": timestamp.isoformat(timespec="seconds"),
                "platform_stage": "Stage 5",
                "platform_block": "5.6 Dry-Run Execution Controls & Run Manifest",
                "notes": (
                    "Dry-run manifest only. Training disabled; no model fitting, "
                    "forecast generation, metrics, or rankings were executed."
                ),
            }
        ]
    )

    manifest.to_csv(RUN_MANIFEST_OUTPUT, index=False)
    metadata.to_csv(RUN_METADATA_OUTPUT, index=False)
    _append_history(manifest, RUN_MANIFEST_HISTORY_OUTPUT)
    _append_history(metadata, RUN_METADATA_HISTORY_OUTPUT)

    logger.info("Created %s with %s rows", RUN_MANIFEST_OUTPUT, len(manifest))
    logger.info("Created %s with %s rows", RUN_METADATA_OUTPUT, len(metadata))
    logger.info("Appended %s rows to %s", len(manifest), RUN_MANIFEST_HISTORY_OUTPUT)
    logger.info("Appended %s rows to %s", len(metadata), RUN_METADATA_HISTORY_OUTPUT)
    logger.info("Training enabled: %s", bool(execution_config["training_enabled"]))
    logger.info("Dry run: %s", bool(execution_config["dry_run"]))
    logger.info("Planned jobs: %s", len(job_plan))
    logger.info("Stage 5.6 run manifest creation completed")

    return manifest, metadata


if __name__ == "__main__":
    create_run_manifest()
