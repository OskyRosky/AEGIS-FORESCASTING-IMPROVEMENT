"""Inspect Stage 5.4 feature dataset outputs.

This helper validates generated feature, metadata, and contract files without
training models, generating forecasts, calculating metrics, or creating
rankings.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_feature_dataset")

FEATURE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "features"
FEATURE_DATASET_INPUT = FEATURE_DIR / "feature_dataset.csv"
FEATURE_METADATA_INPUT = FEATURE_DIR / "feature_metadata.csv"
DATASET_CONTRACT_INPUT = FEATURE_DIR / "dataset_contract.csv"

LAG_COLUMNS = ["lag_1", "lag_7", "lag_14", "lag_30", "lag_60", "lag_90"]
ROLLING_COLUMNS = [
    "rolling_mean_7",
    "rolling_mean_30",
    "rolling_std_7",
    "rolling_std_30",
]
CALENDAR_COLUMNS = [
    "year",
    "month",
    "quarter",
    "day_of_month",
    "day_of_week",
    "week_of_year",
    "is_month_start",
    "is_month_end",
]


def _require_input_file(path) -> None:
    """Fail fast when a feature output is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required feature output missing: {path}")


def inspect_feature_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Inspect generated feature dataset, metadata, and contract."""

    _require_input_file(FEATURE_DATASET_INPUT)
    _require_input_file(FEATURE_METADATA_INPUT)
    _require_input_file(DATASET_CONTRACT_INPUT)

    features = pd.read_csv(FEATURE_DATASET_INPUT, parse_dates=["date"])
    metadata = pd.read_csv(FEATURE_METADATA_INPUT)
    contract = pd.read_csv(DATASET_CONTRACT_INPUT)

    feature_columns = LAG_COLUMNS + ROLLING_COLUMNS + CALENDAR_COLUMNS
    null_counts = features[["entity_key", "date", "target"] + feature_columns].isna().sum()
    lag_coverage = {
        column: int(features[column].notna().sum()) for column in LAG_COLUMNS
    }

    logger.info("Feature dataset rows: %s", len(features))
    logger.info("Entity count: %s", features["entity_key"].nunique())
    logger.info("Date range: %s to %s", features["date"].min(), features["date"].max())
    logger.info("Feature count: %s", len(feature_columns))
    logger.info("Metadata rows: %s", len(metadata))
    logger.info("Dataset contract rows: %s", len(contract))
    logger.info("Null counts: %s", null_counts.to_dict())
    logger.info("Lag coverage: %s", lag_coverage)

    if features["entity_key"].isna().any() or features["date"].isna().any():
        raise ValueError("Feature dataset contains null entity keys or dates.")

    missing_metadata = sorted(set(feature_columns) - set(metadata["feature_name"]))
    if missing_metadata:
        raise ValueError(f"Feature metadata missing rows: {missing_metadata}")

    missing_contract_columns = sorted(set(features.columns) - set(contract["column_name"]))
    if missing_contract_columns:
        raise ValueError(f"Dataset contract missing columns: {missing_contract_columns}")

    logger.info("Stage 5.4 feature dataset inspection passed")
    return features, metadata, contract


if __name__ == "__main__":
    inspect_feature_dataset()
