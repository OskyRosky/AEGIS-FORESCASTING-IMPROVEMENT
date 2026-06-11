"""Build the master evaluation dataset for future forecasting stages.

This Stage 4.6 script stacks processed actuals and forecasts into a standardized
evaluation dataset. It does not calculate accuracy metrics, create rankings,
train models, create forecasts, or modify Shiny/raw/processed inputs.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROCESSED_DIR, PROJECT_ROOT


logger = get_logger("build_evaluation_dataset")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "evaluation"
EVALUATION_DATASET_OUTPUT = OUTPUT_DIR / "evaluation_dataset.csv"
METADATA_OUTPUT = OUTPUT_DIR / "evaluation_dataset_metadata.csv"

ACTUALS_INPUT = PROCESSED_DIR / "actuals.csv"
FORECASTS_INPUT = PROCESSED_DIR / "forecasts.csv"

ACTUAL_REQUIRED_COLUMNS = [
    "entity_key",
    "date",
    "actual_value",
    "forecast_version",
    "scenario",
    "resource",
]

FORECAST_REQUIRED_COLUMNS = [
    "entity_key",
    "date",
    "forecast_value",
    "model_version",
    "forecast_version",
    "scenario",
    "resource",
]

OUTPUT_COLUMNS = [
    "entity_key",
    "date",
    "value",
    "record_type",
    "forecast_version",
    "model_version",
    "scenario",
    "resource",
    "horizon_days",
    "horizon_bucket",
]


def _require_input_file(path) -> None:
    """Fail fast when an expected processed input is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required processed input missing: {path}")


def _require_columns(frame: pd.DataFrame, columns: list[str], label: str) -> None:
    """Validate required processed input columns."""

    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"{label} missing required columns: {missing}")


def _horizon_bucket(horizon_days: int) -> str:
    """Classify rows by evaluation horizon."""

    if horizon_days == 0:
        return "actual"
    if horizon_days <= 90:
        return "short"
    if horizon_days <= 365:
        return "medium"
    if horizon_days <= 730:
        return "long"
    return "strategic"


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load processed actuals and forecasts."""

    _require_input_file(ACTUALS_INPUT)
    _require_input_file(FORECASTS_INPUT)

    actuals = pd.read_csv(ACTUALS_INPUT)
    forecasts = pd.read_csv(FORECASTS_INPUT)
    _require_columns(actuals, ACTUAL_REQUIRED_COLUMNS, ACTUALS_INPUT.name)
    _require_columns(forecasts, FORECAST_REQUIRED_COLUMNS, FORECASTS_INPUT.name)

    return actuals, forecasts


def _standardize_actuals(actuals: pd.DataFrame) -> pd.DataFrame:
    """Standardize actual rows to the evaluation dataset schema."""

    standardized = actuals.rename(columns={"actual_value": "value"}).copy()
    standardized["date"] = pd.to_datetime(standardized["date"], errors="raise")
    standardized["record_type"] = "actual"
    standardized["model_version"] = "actual"
    standardized["horizon_days"] = 0
    standardized["horizon_bucket"] = "actual"

    return standardized[OUTPUT_COLUMNS]


def _standardize_forecasts(
    forecasts: pd.DataFrame, latest_actual_dates: pd.Series
) -> pd.DataFrame:
    """Standardize forecast rows and calculate horizon from latest entity actual."""

    standardized = forecasts.rename(columns={"forecast_value": "value"}).copy()
    standardized["date"] = pd.to_datetime(standardized["date"], errors="raise")
    standardized["record_type"] = "forecast"

    standardized = standardized.merge(
        latest_actual_dates.rename("latest_actual_date"),
        left_on="entity_key",
        right_index=True,
        how="left",
    )
    standardized["horizon_days"] = (
        standardized["date"] - standardized["latest_actual_date"]
    ).dt.days
    standardized["horizon_bucket"] = standardized["horizon_days"].map(_horizon_bucket)

    return standardized[OUTPUT_COLUMNS]


def _build_metadata(evaluation_dataset: pd.DataFrame) -> pd.DataFrame:
    """Build one-row metadata for the master evaluation dataset."""

    actual_rows = int((evaluation_dataset["record_type"] == "actual").sum())
    forecast_rows = int((evaluation_dataset["record_type"] == "forecast").sum())
    model_versions = evaluation_dataset.loc[
        evaluation_dataset["record_type"] == "forecast", "model_version"
    ]

    return pd.DataFrame(
        [
            {
                "total_rows": len(evaluation_dataset),
                "actual_rows": actual_rows,
                "forecast_rows": forecast_rows,
                "entity_count": evaluation_dataset["entity_key"].nunique(),
                "model_count": model_versions.nunique(),
                "forecast_version_count": evaluation_dataset[
                    "forecast_version"
                ].nunique(),
                "first_date": evaluation_dataset["date"].min(),
                "last_date": evaluation_dataset["date"].max(),
            }
        ]
    )


def _log_validation(before_rows: int, after_rows: int, dataset: pd.DataFrame) -> None:
    """Log required validation and coverage details."""

    logger.info("Duplicate rows before cleanup: %s", before_rows - dataset.drop_duplicates().shape[0])
    logger.info("Duplicate rows after cleanup: %s", after_rows - dataset.drop_duplicates().shape[0])
    logger.info("Null entity_key count: %s", int(dataset["entity_key"].isna().sum()))
    logger.info("Null date count: %s", int(dataset["date"].isna().sum()))
    logger.info("Actual rows: %s", int((dataset["record_type"] == "actual").sum()))
    logger.info("Forecast rows: %s", int((dataset["record_type"] == "forecast").sum()))
    logger.info("Entities: %s", dataset["entity_key"].nunique())
    logger.info(
        "Model versions: %s",
        dataset.loc[dataset["record_type"] == "forecast", "model_version"].nunique(),
    )
    logger.info("Forecast versions: %s", dataset["forecast_version"].nunique())
    logger.info(
        "Horizon distribution: %s",
        dataset["horizon_bucket"].value_counts().to_dict(),
    )


def build_evaluation_dataset() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Create the master evaluation dataset and metadata outputs."""

    logger.info("Stage 4.6 evaluation dataset build started")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    actuals, forecasts = _load_inputs()
    latest_actual_dates = pd.to_datetime(actuals["date"], errors="raise").groupby(
        actuals["entity_key"]
    ).max()

    standardized_actuals = _standardize_actuals(actuals)
    standardized_forecasts = _standardize_forecasts(forecasts, latest_actual_dates)
    evaluation_dataset = pd.concat(
        [standardized_actuals, standardized_forecasts], ignore_index=True
    )

    before_cleanup_rows = len(evaluation_dataset)
    duplicate_rows_before = int(evaluation_dataset.duplicated().sum())
    logger.info("Duplicate rows before cleanup: %s", duplicate_rows_before)

    evaluation_dataset = evaluation_dataset.drop_duplicates()
    evaluation_dataset = evaluation_dataset.sort_values(["entity_key", "date"])
    duplicate_rows_after = int(evaluation_dataset.duplicated().sum())
    logger.info("Duplicate rows after cleanup: %s", duplicate_rows_after)

    null_entity_keys = int(evaluation_dataset["entity_key"].isna().sum())
    null_dates = int(evaluation_dataset["date"].isna().sum())
    if null_entity_keys or null_dates:
        raise ValueError(
            "Evaluation dataset contains null entity keys or dates: "
            f"entity_key={null_entity_keys}, date={null_dates}"
        )

    metadata = _build_metadata(evaluation_dataset)

    evaluation_dataset.to_csv(EVALUATION_DATASET_OUTPUT, index=False)
    metadata.to_csv(METADATA_OUTPUT, index=False)

    logger.info("Created %s with %s rows", EVALUATION_DATASET_OUTPUT, len(evaluation_dataset))
    logger.info("Created %s with %s rows", METADATA_OUTPUT, len(metadata))
    _log_validation(before_cleanup_rows, len(evaluation_dataset), evaluation_dataset)
    logger.info("Stage 4.6 evaluation dataset build completed")

    return evaluation_dataset, metadata


if __name__ == "__main__":
    build_evaluation_dataset()
