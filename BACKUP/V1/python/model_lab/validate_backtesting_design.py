"""Validate Stage 5.1 Model Lab backtesting design inputs.

This script validates configuration files, output folders, and the master
evaluation dataset contract. It does not train models, generate forecasts,
calculate metrics, or create rankings.
"""

from __future__ import annotations

import pandas as pd

from model_lab.load_configs import (
    BACKTESTING_CONFIG,
    SCORING_WEIGHTS_CONFIG,
    TOURNAMENT_CONFIG,
    load_all_configs,
)
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("validate_backtesting_design")

EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
MODEL_LAB_DIRS = [
    PROJECT_ROOT / "outputs" / "model_lab",
    PROJECT_ROOT / "outputs" / "model_lab" / "forecasts",
    PROJECT_ROOT / "outputs" / "model_lab" / "metrics",
    PROJECT_ROOT / "outputs" / "model_lab" / "rankings",
    PROJECT_ROOT / "outputs" / "model_lab" / "tournament",
    PROJECT_ROOT / "outputs" / "model_lab" / "dashboard",
]
REQUIRED_EVALUATION_COLUMNS = ["entity_key", "date", "value", "record_type"]


def _require_file(path) -> None:
    """Validate that a required file exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required file missing: {path}")


def _require_directory(path) -> None:
    """Validate that a required directory exists."""

    if not path.exists() or not path.is_dir():
        raise FileNotFoundError(f"Required directory missing: {path}")


def _validate_configs() -> None:
    """Validate config file existence and YAML loading."""

    for path in (BACKTESTING_CONFIG, SCORING_WEIGHTS_CONFIG, TOURNAMENT_CONFIG):
        _require_file(path)
        logger.info("Found config: %s", path)

    configs = load_all_configs()
    logger.info("Loaded config sections: %s", list(configs.keys()))
    logger.info("Backtesting config: %s", configs["backtesting"])
    logger.info("Scoring weights config: %s", configs["scoring_weights"])
    logger.info("Tournament config: %s", configs["tournament"])


def _validate_model_lab_dirs() -> None:
    """Validate Model Lab output folder structure."""

    for directory in MODEL_LAB_DIRS:
        _require_directory(directory)
        logger.info("Found Model Lab directory: %s", directory)


def _validate_evaluation_dataset() -> pd.DataFrame:
    """Validate the evaluation dataset contract."""

    _require_file(EVALUATION_DATASET)
    header = pd.read_csv(EVALUATION_DATASET, nrows=0)
    missing_columns = [
        column
        for column in REQUIRED_EVALUATION_COLUMNS
        if column not in header.columns
    ]
    if missing_columns:
        raise ValueError(
            f"Evaluation dataset missing required columns: {missing_columns}"
        )

    dataset = pd.read_csv(EVALUATION_DATASET, usecols=REQUIRED_EVALUATION_COLUMNS)
    logger.info("Evaluation dataset recognized: %s", EVALUATION_DATASET)
    logger.info("Evaluation dataset rows: %s", len(dataset))
    logger.info("Evaluation dataset entities: %s", dataset["entity_key"].nunique())
    logger.info(
        "Evaluation dataset record types: %s",
        sorted(dataset["record_type"].dropna().unique().tolist()),
    )
    return dataset


def validate_backtesting_design() -> None:
    """Run all Stage 5.1 validation checks."""

    logger.info("Stage 5.1 backtesting design validation started")
    _validate_configs()
    _validate_model_lab_dirs()
    _validate_evaluation_dataset()
    logger.info("Stage 5.1 backtesting design validation passed")


if __name__ == "__main__":
    validate_backtesting_design()
