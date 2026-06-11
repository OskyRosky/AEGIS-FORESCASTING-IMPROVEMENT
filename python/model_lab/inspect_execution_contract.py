"""Inspect and validate Stage 5.8 execution contract documents."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_execution_contract")

CONTRACTS_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "contracts"

CONTRACT_FILES = {
    "execution_contract": CONTRACTS_DIR / "execution_contract.csv",
    "output_artifacts": CONTRACTS_DIR / "output_artifacts.csv",
    "job_status_codes": CONTRACTS_DIR / "job_status_codes.csv",
    "model_output_schema": CONTRACTS_DIR / "model_output_schema.csv",
    "forecast_output_schema": CONTRACTS_DIR / "forecast_output_schema.csv",
    "metrics_output_schema": CONTRACTS_DIR / "metrics_output_schema.csv",
    "tournament_output_schema": CONTRACTS_DIR / "tournament_output_schema.csv",
}

EXPECTED_STATUSES = {
    "planned",
    "running",
    "completed",
    "failed",
    "skipped",
    "blocked_by_config",
    "dry_run_only",
    "execution_not_implemented",
}
EXPECTED_FORECAST_FIELDS = {
    "run_id",
    "job_id",
    "entity_key",
    "model_name",
    "forecast_version",
    "forecast_date",
    "horizon_day",
    "forecast_value",
    "created_timestamp",
}
EXPECTED_METRIC_FIELDS = {
    "run_id",
    "job_id",
    "entity_key",
    "model_name",
    "window_id",
    "wmape",
    "mape",
    "rmse",
    "smape",
    "bias",
    "stability_score",
    "horizon_score",
    "composite_score",
    "created_timestamp",
}
EXPECTED_TOURNAMENT_FIELDS = {
    "run_id",
    "entity_key",
    "model_name",
    "rank",
    "composite_score",
    "tournament_winner",
    "created_timestamp",
}
EXPECTED_ARTIFACT_TYPES = {
    "model_object",
    "training_log",
    "forecast_output",
    "metrics_output",
    "error_log",
}
EXPECTED_ERROR_FIELDS = {
    "run_id",
    "job_id",
    "entity_key",
    "model_name",
    "error_timestamp",
    "error_type",
    "error_message",
    "stack_trace_available",
}
EXPECTED_LOGGING_FIELDS = {
    "timestamp",
    "run_id",
    "job_id",
    "entity_key",
    "model_name",
    "status",
    "message",
}


def _read_contract(name: str, path) -> pd.DataFrame:
    """Read one required contract file."""

    if not path.exists():
        raise FileNotFoundError(f"Required contract file missing: {path}")

    frame = pd.read_csv(path)
    if frame.empty:
        raise ValueError(f"Contract file is empty: {path}")

    logger.info("%s: %s rows", name, len(frame))
    return frame


def _validate_schema_fields(
    frame: pd.DataFrame, expected_fields: set[str], schema_name: str
) -> None:
    """Validate that a schema file contains all required field names."""

    actual_fields = set(frame["field_name"])
    missing_fields = sorted(expected_fields - actual_fields)
    if missing_fields:
        raise ValueError(f"{schema_name} missing fields: {missing_fields}")

    logger.info("%s fields validated: %s", schema_name, sorted(expected_fields))


def inspect_execution_contract() -> dict[str, pd.DataFrame]:
    """Inspect all contract files and validate required coverage."""

    logger.info("Stage 5.8 execution contract inspection started")
    contracts = {
        name: _read_contract(name, path) for name, path in CONTRACT_FILES.items()
    }

    statuses = set(contracts["job_status_codes"]["status"])
    missing_statuses = sorted(EXPECTED_STATUSES - statuses)
    if missing_statuses:
        raise ValueError(f"Missing job status codes: {missing_statuses}")
    logger.info("Status codes validated: %s", sorted(EXPECTED_STATUSES))

    artifact_types = set(contracts["output_artifacts"]["artifact_type"])
    missing_artifacts = sorted(EXPECTED_ARTIFACT_TYPES - artifact_types)
    if missing_artifacts:
        raise ValueError(f"Missing artifact types: {missing_artifacts}")
    logger.info("Artifact types validated: %s", sorted(EXPECTED_ARTIFACT_TYPES))

    _validate_schema_fields(
        contracts["forecast_output_schema"],
        EXPECTED_FORECAST_FIELDS,
        "forecast_output_schema",
    )
    _validate_schema_fields(
        contracts["metrics_output_schema"],
        EXPECTED_METRIC_FIELDS,
        "metrics_output_schema",
    )
    _validate_schema_fields(
        contracts["tournament_output_schema"],
        EXPECTED_TOURNAMENT_FIELDS,
        "tournament_output_schema",
    )
    _validate_schema_fields(
        contracts["model_output_schema"],
        EXPECTED_ERROR_FIELDS,
        "model_output_schema error contract",
    )
    _validate_schema_fields(
        contracts["model_output_schema"],
        EXPECTED_LOGGING_FIELDS,
        "model_output_schema logging contract",
    )

    logger.info("Stage 5.8 execution contract inspection passed")
    return contracts


if __name__ == "__main__":
    inspect_execution_contract()
