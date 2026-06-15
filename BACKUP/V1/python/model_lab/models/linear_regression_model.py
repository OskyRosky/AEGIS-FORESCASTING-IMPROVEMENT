"""Linear regression baseline production implementation."""

from __future__ import annotations

import numpy as np
import pandas as pd

from model_lab.models.base_model import ForecastModel


class LinearRegressionModel(ForecastModel):
    """Current LinearRegressionModel with lags=30 and recursive prediction."""

    model_name = "LinearRegression"
    model_family = "BaselineProduction"
    lags = 30

    def __init__(self) -> None:
        self._coefficients = None
        self._history: list[float] = []

    def fit(self, training_data):
        """Fit linear regression on lagged target values using least squares."""

        self.validate_input(training_data)
        series = _extract_target_series(training_data)
        values = series.to_numpy(dtype=float)
        features = []
        targets = []
        for index in range(self.lags, len(values)):
            features.append(values[index - self.lags : index])
            targets.append(values[index])

        feature_matrix = np.asarray(features)
        design_matrix = np.column_stack(
            [np.ones(len(feature_matrix)), feature_matrix]
        )
        self._coefficients = np.linalg.lstsq(
            design_matrix, np.asarray(targets), rcond=None
        )[0]
        self._history = values.tolist()
        return self

    def predict(self, horizon: int, future_data=None):
        """Recursively predict without using future actuals."""

        if self._coefficients is None:
            raise RuntimeError("LinearRegression must be fit before predict().")
        if horizon <= 0:
            raise ValueError("horizon must be positive.")

        history = list(self._history)
        predictions = []
        for _ in range(horizon):
            lag_values = np.asarray(history[-self.lags:], dtype=float)
            features = np.concatenate([[1.0], lag_values])
            prediction = float(features @ self._coefficients)
            predictions.append(prediction)
            history.append(prediction)

        return np.asarray(predictions)

    def get_model_name(self) -> str:
        return self.model_name

    def get_model_family(self) -> str:
        return self.model_family

    def validate_input(self, data) -> None:
        series = _extract_target_series(data)
        if len(series) <= self.lags:
            raise ValueError(
                f"LinearRegression requires more than {self.lags} observations."
            )


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
