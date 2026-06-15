"""XGBoost placeholder implementation."""

from __future__ import annotations

from model_lab.models.base_model import ForecastModel


class XGBoostModel(ForecastModel):
    """XGBoost model placeholder."""

    model_name = "XGBoost"
    model_family = "MachineLearning"

    def fit(self, training_data):
        raise NotImplementedError("Training not implemented yet.")

    def predict(self, horizon: int, future_data=None):
        raise NotImplementedError("Forecast generation not implemented yet.")

    def get_model_name(self) -> str:
        return self.model_name

    def get_model_family(self) -> str:
        return self.model_family

    def validate_input(self, data) -> None:
        raise NotImplementedError("Input validation not implemented yet.")
