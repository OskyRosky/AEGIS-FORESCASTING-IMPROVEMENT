"""Current ETS baseline production implementation."""

from __future__ import annotations

import pandas as pd

from model_lab.models.base_model import ForecastModel


class ETSCurrentModel(ForecastModel):
    """Conservative non-seasonal ExponentialSmoothing baseline implementation."""

    model_name = "ETS_Current"
    model_family = "BaselineProduction"

    def __init__(self) -> None:
        self._result = None

    def fit(self, training_data):
        """Fit conservative non-seasonal additive-trend ETS state."""

        self.validate_input(training_data)
        series = _extract_target_series(training_data)
        values = series.to_numpy(dtype=float)
        alpha = 0.8
        beta = 0.2
        level = values[0]
        trend = values[1] - values[0]
        for value in values[1:]:
            previous_level = level
            level = alpha * value + (1 - alpha) * (level + trend)
            trend = beta * (level - previous_level) + (1 - beta) * trend
        self._result = {"level": float(level), "trend": float(trend)}
        return self

    def predict(self, horizon: int, future_data=None):
        """Generate a non-seasonal ETS forecast for the requested horizon."""

        if self._result is None:
            raise RuntimeError("ETS_Current must be fit before predict().")
        if horizon <= 0:
            raise ValueError("horizon must be positive.")
        steps = pd.Series(range(1, horizon + 1), dtype=float)
        return (self._result["level"] + steps * self._result["trend"]).to_numpy()

    def get_model_name(self) -> str:
        return self.model_name

    def get_model_family(self) -> str:
        return self.model_family

    def validate_input(self, data) -> None:
        series = _extract_target_series(data)
        if len(series) < 2:
            raise ValueError("ETS_Current requires at least 2 training observations.")


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
