"""Create the Stage 5.8 real execution design contract.

This design-only script documents the required execution, artifact, status,
schema, error, and logging contracts for future Model Lab runs. It does not
call fit(), call predict(), train models, generate forecasts, calculate
metrics, or create rankings.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("design_execution_contract")

CONTRACTS_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "contracts"

EXECUTION_CONTRACT_OUTPUT = CONTRACTS_DIR / "execution_contract.csv"
OUTPUT_ARTIFACTS_OUTPUT = CONTRACTS_DIR / "output_artifacts.csv"
JOB_STATUS_CODES_OUTPUT = CONTRACTS_DIR / "job_status_codes.csv"
MODEL_OUTPUT_SCHEMA_OUTPUT = CONTRACTS_DIR / "model_output_schema.csv"
FORECAST_OUTPUT_SCHEMA_OUTPUT = CONTRACTS_DIR / "forecast_output_schema.csv"
METRICS_OUTPUT_SCHEMA_OUTPUT = CONTRACTS_DIR / "metrics_output_schema.csv"
TOURNAMENT_OUTPUT_SCHEMA_OUTPUT = CONTRACTS_DIR / "tournament_output_schema.csv"


def _schema_row(
    field_name: str,
    data_type: str,
    required: bool,
    description: str,
    example: str = "",
) -> dict:
    """Build a standard schema row."""

    return {
        "field_name": field_name,
        "data_type": data_type,
        "required": required,
        "description": description,
        "example": example,
    }


def _write_csv(path, rows: list[dict]) -> pd.DataFrame:
    """Write rows to a contract CSV and return the DataFrame."""

    frame = pd.DataFrame(rows)
    frame.to_csv(path, index=False)
    logger.info("Created %s with %s rows", path, len(frame))
    return frame


def _build_execution_contract() -> list[dict]:
    """Define cross-cutting execution, error, and logging requirements."""

    return [
        {
            "contract_area": "execution_gate",
            "requirement": "Execution must load config/execution.yaml before any job starts.",
            "required": True,
            "notes": "training_enabled and dry_run are authoritative controls.",
        },
        {
            "contract_area": "execution_gate",
            "requirement": "If training_enabled is false, execute zero jobs.",
            "required": True,
            "notes": "Write execution audit with status blocked_by_config.",
        },
        {
            "contract_area": "execution_gate",
            "requirement": "If dry_run is true, execute zero jobs.",
            "required": True,
            "notes": "Write execution audit with status dry_run_only.",
        },
        {
            "contract_area": "execution_gate",
            "requirement": "Real execution is allowed only when training_enabled is true and dry_run is false.",
            "required": True,
            "notes": "Future implementation must still pass all preflight validations.",
        },
        {
            "contract_area": "job_inputs",
            "requirement": "Each executable job must originate from training_job_plan.csv.",
            "required": True,
            "notes": "Ad hoc jobs outside the planned job catalog are not allowed.",
        },
        {
            "contract_area": "job_inputs",
            "requirement": "Each job must reference one run_id, job_id, entity_key, model_name, and window_id.",
            "required": True,
            "notes": "These fields define output lineage.",
        },
        {
            "contract_area": "artifact_layout",
            "requirement": "Model Lab artifacts must be written under outputs/model_lab/artifacts/run_id/model_name/entity_key/window_id/.",
            "required": True,
            "notes": "No artifacts should be written outside the Model Lab artifact root.",
        },
        {
            "contract_area": "error_handling",
            "requirement": "Errors must capture run_id, job_id, entity_key, model_name, error_timestamp, error_type, error_message, and stack_trace_available.",
            "required": True,
            "notes": "A failed job must not stop unrelated jobs unless a platform-level failure is detected.",
        },
        {
            "contract_area": "logging",
            "requirement": "Execution logs must capture timestamp, run_id, job_id, entity_key, model_name, status, and message.",
            "required": True,
            "notes": "Logs must be sufficient to reconstruct job-level execution history.",
        },
        {
            "contract_area": "outputs",
            "requirement": "Forecast, metrics, and tournament outputs must follow their documented schemas.",
            "required": True,
            "notes": "Schema additions require a new forecast_version or contract update.",
        },
    ]


def _build_output_artifacts() -> list[dict]:
    """Define future artifact types and layout."""

    artifact_root = "outputs/model_lab/artifacts/{run_id}/{model_name}/{entity_key}/{window_id}/"
    return [
        {
            "artifact_type": "model_object",
            "artifact_root": artifact_root,
            "required": False,
            "description": "Serialized fitted model object for one job.",
        },
        {
            "artifact_type": "training_log",
            "artifact_root": artifact_root,
            "required": True,
            "description": "Job-level training log for traceability.",
        },
        {
            "artifact_type": "forecast_output",
            "artifact_root": artifact_root,
            "required": True,
            "description": "Forecast rows following forecast_output_schema.csv.",
        },
        {
            "artifact_type": "metrics_output",
            "artifact_root": artifact_root,
            "required": True,
            "description": "Metric rows following metrics_output_schema.csv.",
        },
        {
            "artifact_type": "error_log",
            "artifact_root": artifact_root,
            "required": True,
            "description": "Error details for failed jobs using the error handling contract.",
        },
    ]


def _build_job_status_codes() -> list[dict]:
    """Define standard Model Lab job statuses."""

    descriptions = {
        "planned": "Job exists in the training plan but has not started.",
        "running": "Job execution has started and has not reached a terminal state.",
        "completed": "Job completed all required execution and output steps.",
        "failed": "Job execution failed and error details were recorded.",
        "skipped": "Job was intentionally skipped by scheduler or policy.",
        "blocked_by_config": "Execution was blocked because training_enabled is false.",
        "dry_run_only": "Execution was skipped because dry_run is true.",
        "execution_not_implemented": "Execution was requested but real execution is not implemented.",
    }
    return [
        {
            "status": status,
            "terminal": status
            in {
                "completed",
                "failed",
                "skipped",
                "blocked_by_config",
                "dry_run_only",
                "execution_not_implemented",
            },
            "description": description,
        }
        for status, description in descriptions.items()
    ]


def _build_model_output_schema() -> list[dict]:
    """Define model artifact, error, and logging schema fields."""

    return [
        _schema_row("run_id", "string", True, "Unique Model Lab run identifier."),
        _schema_row("job_id", "string", True, "Unique planned job identifier."),
        _schema_row("entity_key", "string", True, "Forecast entity for the job."),
        _schema_row("model_name", "string", True, "Registered model name."),
        _schema_row("window_id", "integer", True, "Walk-forward window identifier."),
        _schema_row("artifact_type", "string", True, "One documented artifact type."),
        _schema_row("artifact_path", "string", True, "Relative path to the produced artifact."),
        _schema_row("status", "string", True, "Standard job status code."),
        _schema_row("created_timestamp", "datetime", True, "Artifact creation timestamp."),
        _schema_row("error_timestamp", "datetime", False, "Timestamp for a job error."),
        _schema_row("error_type", "string", False, "Error class or category."),
        _schema_row("error_message", "string", False, "Human-readable error message."),
        _schema_row("stack_trace_available", "boolean", False, "Whether stack trace details exist."),
        _schema_row("timestamp", "datetime", False, "Required logging timestamp field."),
        _schema_row("message", "string", False, "Required logging message field."),
    ]


def _build_forecast_output_schema() -> list[dict]:
    """Define future forecast output schema."""

    return [
        _schema_row("run_id", "string", True, "Unique Model Lab run identifier."),
        _schema_row("job_id", "string", True, "Unique planned job identifier."),
        _schema_row("entity_key", "string", True, "Forecast entity for the job."),
        _schema_row("model_name", "string", True, "Registered model name."),
        _schema_row("forecast_version", "string", True, "Forecast schema or generation version."),
        _schema_row("forecast_date", "date", True, "Date being forecast."),
        _schema_row("horizon_day", "integer", True, "Forecast horizon day number."),
        _schema_row("forecast_value", "float", True, "Forecasted target value."),
        _schema_row("created_timestamp", "datetime", True, "Forecast row creation timestamp."),
    ]


def _build_metrics_output_schema() -> list[dict]:
    """Define future metrics output schema."""

    return [
        _schema_row("run_id", "string", True, "Unique Model Lab run identifier."),
        _schema_row("job_id", "string", True, "Unique planned job identifier."),
        _schema_row("entity_key", "string", True, "Forecast entity for the job."),
        _schema_row("model_name", "string", True, "Registered model name."),
        _schema_row("window_id", "integer", True, "Walk-forward window identifier."),
        _schema_row("wmape", "float", True, "Weighted mean absolute percentage error."),
        _schema_row("mape", "float", True, "Mean absolute percentage error."),
        _schema_row("rmse", "float", True, "Root mean squared error."),
        _schema_row("smape", "float", True, "Symmetric mean absolute percentage error."),
        _schema_row("bias", "float", True, "Forecast bias."),
        _schema_row("stability_score", "float", True, "Window-to-window stability score."),
        _schema_row("horizon_score", "float", True, "Forecast horizon quality score."),
        _schema_row("composite_score", "float", True, "Tournament-ready composite score."),
        _schema_row("created_timestamp", "datetime", True, "Metric row creation timestamp."),
    ]


def _build_tournament_output_schema() -> list[dict]:
    """Define future tournament output schema."""

    return [
        _schema_row("run_id", "string", True, "Unique Model Lab run identifier."),
        _schema_row("entity_key", "string", True, "Forecast entity being ranked."),
        _schema_row("model_name", "string", True, "Registered model name."),
        _schema_row("rank", "integer", True, "Model rank for the entity."),
        _schema_row("composite_score", "float", True, "Final ranking score."),
        _schema_row("tournament_winner", "boolean", True, "Whether the model won for the entity."),
        _schema_row("created_timestamp", "datetime", True, "Tournament row creation timestamp."),
    ]


def design_execution_contract() -> dict[str, pd.DataFrame]:
    """Create all Stage 5.8 execution contract documents."""

    logger.info("Stage 5.8 execution contract design started")
    CONTRACTS_DIR.mkdir(parents=True, exist_ok=True)

    outputs = {
        "execution_contract": _write_csv(
            EXECUTION_CONTRACT_OUTPUT, _build_execution_contract()
        ),
        "output_artifacts": _write_csv(
            OUTPUT_ARTIFACTS_OUTPUT, _build_output_artifacts()
        ),
        "job_status_codes": _write_csv(
            JOB_STATUS_CODES_OUTPUT, _build_job_status_codes()
        ),
        "model_output_schema": _write_csv(
            MODEL_OUTPUT_SCHEMA_OUTPUT, _build_model_output_schema()
        ),
        "forecast_output_schema": _write_csv(
            FORECAST_OUTPUT_SCHEMA_OUTPUT, _build_forecast_output_schema()
        ),
        "metrics_output_schema": _write_csv(
            METRICS_OUTPUT_SCHEMA_OUTPUT, _build_metrics_output_schema()
        ),
        "tournament_output_schema": _write_csv(
            TOURNAMENT_OUTPUT_SCHEMA_OUTPUT, _build_tournament_output_schema()
        ),
    }

    logger.info("Stage 5.8 execution contract design completed")
    return outputs


if __name__ == "__main__":
    design_execution_contract()
