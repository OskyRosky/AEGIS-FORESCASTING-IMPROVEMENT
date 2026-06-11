"""Fixed ARIMA baseline production implementation."""

from __future__ import annotations

import pandas as pd

from model_lab.models.base_model import ForecastModel


class ARIMAFixedModel(ForecastModel):
    """ARIMA(p=0,d=2,q=0) reproduction baseline production model."""

    model_name = "ARIMA_Fixed"
    model_family = "BaselineProduction"
    order = (0, 2, 0)

    def __init__(self) -> None:
        self._result = None

    def fit(self, training_data):
        """Fit fixed-order ARIMA reproduction state to a univariate series."""

        self.validate_input(training_data)
        series = _extract_target_series(training_data)
        values = series.to_numpy(dtype=float)
        self._result = {
            "last_value": float(values[-1]),
            "last_first_difference": float(values[-1] - values[-2]),
        }
        return self

    def predict(self, horizon: int, future_data=None):
        """Generate a fixed-order ARIMA forecast for the requested horizon."""

        if self._result is None:
            raise RuntimeError("ARIMA_Fixed must be fit before predict().")
        if horizon <= 0:
            raise ValueError("horizon must be positive.")
        steps = pd.Series(range(1, horizon + 1), dtype=float)
        return (
            self._result["last_value"]
            + (steps * self._result["last_first_difference"])
        ).to_numpy()

    def get_model_name(self) -> str:
        return self.model_name

    def get_model_family(self) -> str:
        return self.model_family

    def validate_input(self, data) -> None:
        series = _extract_target_series(data)
        if len(series) < 3:
            raise ValueError("ARIMA_Fixed requires at least 3 training observations.")


def _extract_target_series(data) -> pd.Series:
    """Extract a clean numeric target series from supported training inputs."""

    if isinstance(data, pd.Series):
        series = data.copy()
    elif isinstance(data, pd.DataFrame):
        target_column = "target" if "target" in data.columns else "value"
        if target_column not in data.columns:
            raise ValueError("Training data must include target or value column.")
        series = data.sort_values("date")[target_column] if "date" in data else data[target_column]
    else:
        series = pd.Series(data)

    series = pd.to_numeric(series, errors="coerce").dropna()
    if series.empty:
        raise ValueError("Training data contains no numeric target values.")
    return series.reset_index(drop=True)
