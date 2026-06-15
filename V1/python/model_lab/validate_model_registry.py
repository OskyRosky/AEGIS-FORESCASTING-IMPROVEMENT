"""Validate the Stage 5.3 Model Lab model registry and interface layer.

This script checks registration, inheritance, required methods, and metadata.
It does not train models, generate forecasts, calculate metrics, or create
rankings.
"""

from __future__ import annotations

from model_lab.models.base_model import ForecastModel
from model_lab.models.model_metadata import get_model_metadata
from model_lab.models.model_registry import get_model, list_model_families, list_models
from utils.logger import get_logger


logger = get_logger("validate_model_registry")

EXPECTED_MODELS = {
    "ARIMA_Fixed": "BaselineProduction",
    "ETS_Current": "BaselineProduction",
    "LinearRegression": "BaselineProduction",
    "FixedGrowth_1_5": "BaselineProduction",
    "FixedGrowth_3": "BaselineProduction",
    "FixedGrowth_4": "BaselineProduction",
    "FixedGrowth_6": "BaselineProduction",
    "AutoARIMA": "Statistical",
    "Theta": "Statistical",
    "ETS": "Statistical",
    "LightGBM": "MachineLearning",
    "XGBoost": "MachineLearning",
    "NBEATS": "DeepLearning",
    "NHITS": "DeepLearning",
}
REQUIRED_METHODS = [
    "fit",
    "predict",
    "get_model_name",
    "get_model_family",
    "validate_input",
]
METADATA_REQUIRED_FIELDS = [
    "model_name",
    "model_family",
    "description",
    "supports_multivariate",
    "supports_exogenous",
    "supports_probabilistic_forecasts",
]


def _validate_registry() -> None:
    """Validate registered model names, families, and inheritance."""

    registered_models = list_models()
    logger.info("Registered models: %s", registered_models)

    missing_models = sorted(set(EXPECTED_MODELS) - set(registered_models))
    unexpected_models = sorted(set(registered_models) - set(EXPECTED_MODELS))
    if missing_models or unexpected_models:
        raise ValueError(
            f"Registry mismatch. missing={missing_models}, unexpected={unexpected_models}"
        )

    for model_name, expected_family in EXPECTED_MODELS.items():
        model_class = get_model(model_name)
        if not issubclass(model_class, ForecastModel):
            raise TypeError(f"{model_name} does not inherit ForecastModel.")
        if model_class.model_family != expected_family:
            raise ValueError(
                f"{model_name} family mismatch: "
                f"{model_class.model_family} != {expected_family}"
            )

        instance = model_class()
        for method_name in REQUIRED_METHODS:
            method = getattr(instance, method_name, None)
            if not callable(method):
                raise ValueError(f"{model_name} missing method: {method_name}")

    logger.info("Registered model families: %s", list_model_families())


def _validate_metadata() -> None:
    """Validate model metadata coverage and required fields."""

    metadata = get_model_metadata()
    metadata_by_name = {row["model_name"]: row for row in metadata}

    missing_metadata = sorted(set(EXPECTED_MODELS) - set(metadata_by_name))
    if missing_metadata:
        raise ValueError(f"Missing metadata for models: {missing_metadata}")

    for model_name, expected_family in EXPECTED_MODELS.items():
        row = metadata_by_name[model_name]
        missing_fields = [
            field for field in METADATA_REQUIRED_FIELDS if field not in row
        ]
        if missing_fields:
            raise ValueError(f"{model_name} metadata missing fields: {missing_fields}")
        if row["model_family"] != expected_family:
            raise ValueError(
                f"{model_name} metadata family mismatch: "
                f"{row['model_family']} != {expected_family}"
            )

    logger.info("Metadata rows: %s", len(metadata))


def validate_model_registry() -> None:
    """Run all Stage 5.3 model registry validation checks."""

    logger.info("Stage 5.3 model registry validation started")
    _validate_registry()
    _validate_metadata()
    logger.info("Stage 5.3 model registry validation passed")


if __name__ == "__main__":
    validate_model_registry()
