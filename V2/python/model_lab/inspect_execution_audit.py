"""Inspect the Stage 5.7 Model Lab execution audit output."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_execution_audit")

EXECUTION_AUDIT = PROJECT_ROOT / "outputs" / "model_lab" / "runs" / "execution_audit.csv"

AUDIT_FIELDS = [
    "run_id",
    "training_enabled",
    "dry_run",
    "planned_jobs",
    "executed_jobs",
    "skipped_jobs",
    "status",
    "message",
]


def inspect_execution_audit() -> pd.DataFrame:
    """Read and log the latest execution audit row."""

    if not EXECUTION_AUDIT.exists():
        raise FileNotFoundError(f"Required execution audit missing: {EXECUTION_AUDIT}")

    audit = pd.read_csv(EXECUTION_AUDIT)
    if audit.empty:
        raise ValueError("execution_audit.csv is empty.")

    latest = audit.iloc[-1]
    for field in AUDIT_FIELDS:
        if field not in audit.columns:
            raise ValueError(f"execution_audit.csv missing field: {field}")
        logger.info("%s: %s", field, latest[field])

    return audit


if __name__ == "__main__":
    inspect_execution_audit()
