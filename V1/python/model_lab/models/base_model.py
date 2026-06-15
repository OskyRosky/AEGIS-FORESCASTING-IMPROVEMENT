"""Abstract forecasting model interface for the Model Lab.

All future forecasting implementations must inherit from ForecastModel and
provide the same API contract for fitting, prediction, metadata, and input
validation.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ForecastModel(ABC):
    """Common interface for every forecasting model implementation."""

    model_name: str
    model_family: str

    @abstractmethod
    def fit(self, training_data):
        """Fit a forecasting model to training data."""

    @abstractmethod
    def predict(self, horizon: int, future_data=None):
        """Generate forecasts for a requested horizon."""

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the model name used by the registry."""

    @abstractmethod
    def get_model_family(self) -> str:
        """Return the model family used for grouping and reporting."""

    @abstractmethod
    def validate_input(self, data) -> None:
        """Validate model-specific input requirements."""
