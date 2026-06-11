"""Build standardized forecasting feature datasets for the Model Lab.

This Stage 5.4 script creates reproducible lag, rolling, and calendar features
from historical actuals only. It does not train models, generate forecasts,
calculate metrics, or create rankings.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("build_feature_dataset")

EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
FEATURE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "features"
FEATURE_DATASET_OUTPUT = FEATURE_DIR / "feature_dataset.csv"
FEATURE_METADATA_OUTPUT = FEATURE_DIR / "feature_metadata.csv"
DATASET_CONTRACT_OUTPUT = FEATURE_DIR / "dataset_contract.csv"

LAG_FEATURES = [1, 7, 14, 30, 60, 90]
ROLLING_WINDOWS = [7, 30]
CALENDAR_FEATURES = [
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
    """Fail fast when the evaluation dataset is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required input missing: {path}")


def _load_actuals() -> pd.DataFrame:
    """Load historical actuals from the evaluation dataset."""

    _require_input_file(EVALUATION_DATASET)
    dataset = pd.read_csv(EVALUATION_DATASET)
    required_columns = ["entity_key", "date", "value", "record_type"]
    missing_columns = [column for column in required_columns if column not in dataset]
    if missing_columns:
        raise ValueError(f"Evaluation dataset missing columns: {missing_columns}")

    actuals = dataset[dataset["record_type"] == "actual"].copy()
    actuals["date"] = pd.to_datetime(actuals["date"], errors="raise")
    actuals = actuals[["entity_key", "date", "value"]].rename(
        columns={"value": "target"}
    )
    return actuals.sort_values(["entity_key", "date"])


def _add_lag_features(features: pd.DataFrame) -> pd.DataFrame:
    """Add entity-local lag features."""

    for lag in LAG_FEATURES:
        features[f"lag_{lag}"] = features.groupby("entity_key")["target"].shift(lag)
    return features


def _add_rolling_features(features: pd.DataFrame) -> pd.DataFrame:
    """Add entity-local rolling features using prior observations only."""

    shifted_target = features.groupby("entity_key")["target"].shift(1)
    for window in ROLLING_WINDOWS:
        grouped_shifted = shifted_target.groupby(features["entity_key"])
        features[f"rolling_mean_{window}"] = grouped_shifted.transform(
            lambda series: series.rolling(window=window, min_periods=window).mean()
        )
        features[f"rolling_std_{window}"] = grouped_shifted.transform(
            lambda series: series.rolling(window=window, min_periods=window).std()
        )
    return features


def _add_calendar_features(features: pd.DataFrame) -> pd.DataFrame:
    """Add deterministic calendar features."""

    features["year"] = features["date"].dt.year
    features["month"] = features["date"].dt.month
    features["quarter"] = features["date"].dt.quarter
    features["day_of_month"] = features["date"].dt.day
    features["day_of_week"] = features["date"].dt.dayofweek
    features["week_of_year"] = features["date"].dt.isocalendar().week.astype(int)
    features["is_month_start"] = features["date"].dt.is_month_start.astype(int)
    features["is_month_end"] = features["date"].dt.is_month_end.astype(int)
    return features


def _build_feature_metadata() -> pd.DataFrame:
    """Create feature metadata for model compatibility and documentation."""

    rows = []
    for lag in LAG_FEATURES:
        rows.append(
            {
                "feature_name": f"lag_{lag}",
                "feature_type": "lag",
                "description": f"Target value from {lag} day(s) before the row date.",
            }
        )

    for window in ROLLING_WINDOWS:
        rows.extend(
            [
                {
                    "feature_name": f"rolling_mean_{window}",
                    "feature_type": "rolling",
                    "description": (
                        f"Mean target over the prior {window} observations, "
                        "excluding the current row."
                    ),
                },
                {
                    "feature_name": f"rolling_std_{window}",
                    "feature_type": "rolling",
                    "description": (
                        f"Target standard deviation over the prior {window} "
                        "observations, excluding the current row."
                    ),
                },
            ]
        )

    for feature in CALENDAR_FEATURES:
        rows.append(
            {
                "feature_name": feature,
                "feature_type": "calendar",
                "description": f"Calendar-derived feature: {feature}.",
            }
        )

    return pd.DataFrame(rows)


def _build_dataset_contract(feature_dataset: pd.DataFrame) -> pd.DataFrame:
    """Create a dataset contract for downstream model consumers."""

    descriptions = {
        "entity_key": "Unique forecasting entity identifier.",
        "date": "Daily observation date.",
        "target": "Historical actual target value.",
    }
    rows = []
    for column in feature_dataset.columns:
        rows.append(
            {
                "column_name": column,
                "data_type": str(feature_dataset[column].dtype),
                "required": column in {"entity_key", "date", "target"},
                "description": descriptions.get(column, f"Feature column: {column}."),
            }
        )
    return pd.DataFrame(rows)


def build_feature_dataset() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build feature dataset, metadata, and dataset contract outputs."""

    logger.info("Stage 5.4 feature dataset build started")
    FEATURE_DIR.mkdir(parents=True, exist_ok=True)

    features = _load_actuals()
    features = _add_lag_features(features)
    features = _add_rolling_features(features)
    features = _add_calendar_features(features)
    features = features.sort_values(["entity_key", "date"])

    feature_metadata = _build_feature_metadata()
    dataset_contract = _build_dataset_contract(features)

    features.to_csv(FEATURE_DATASET_OUTPUT, index=False)
    feature_metadata.to_csv(FEATURE_METADATA_OUTPUT, index=False)
    dataset_contract.to_csv(DATASET_CONTRACT_OUTPUT, index=False)

    logger.info("Created %s with %s rows", FEATURE_DATASET_OUTPUT, len(features))
    logger.info("Created %s with %s rows", FEATURE_METADATA_OUTPUT, len(feature_metadata))
    logger.info("Created %s with %s rows", DATASET_CONTRACT_OUTPUT, len(dataset_contract))
    logger.info("Entities: %s", features["entity_key"].nunique())
    logger.info("Date range: %s to %s", features["date"].min(), features["date"].max())
    logger.info("Stage 5.4 feature dataset build completed")

    return features, feature_metadata, dataset_contract


if __name__ == "__main__":
    build_feature_dataset()
