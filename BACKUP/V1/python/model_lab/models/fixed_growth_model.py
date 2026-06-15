"""Fixed growth baseline production implementations."""

from __future__ import annotations

import numpy as np
import pandas as pd

from model_lab.models.base_model import ForecastModel


class FixedGrowthModel(ForecastModel):
    """Base implementation for current FixedGrowthModel configurations."""

    model_name: str
    model_family = "BaselineProduction"
    growth_rate: float
    growth_horizon_days = 30

    def __init__(self) -> None:
        self._last_observed_value: float | None = None
        self._daily_increment: float | None = None

    def fit(self, training_data):
        """Store the last observed value and fixed daily growth increment."""

        self.validate_input(training_data)
        series = _extract_target_series(training_data)
        self._last_observed_value = float(series.iloc[-1])
        self._daily_increment = (
            self._last_observed_value * self.growth_rate / self.growth_horizon_days
        )
        return self

    def predict(self, horizon: int, future_data=None):
        """Forecast forward with a fixed daily increment."""

        if self._last_observed_value is None or self._daily_increment is None:
            raise RuntimeError(f"{self.model_name} must be fit before predict().")
        if horizon <= 0:
            raise ValueError("horizon must be positive.")
        steps = np.arange(1, horizon + 1, dtype=float)
        return self._last_observed_value + (self._daily_increment * steps)

    def get_model_name(self) -> str:
        return self.model_name

    def get_model_family(self) -> str:
        return self.model_family

    def validate_input(self, data) -> None:
        series = _extract_target_series(data)
        if series.empty:
            raise ValueError(f"{self.model_name} requires training observations.")


class FixedGrowth15Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.015."""

    model_name = "FixedGrowth_1_5"
    growth_rate = 0.015


class FixedGrowth3Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.03."""

    model_name = "FixedGrowth_3"
    growth_rate = 0.03


class FixedGrowth4Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.04."""

    model_name = "FixedGrowth_4"
    growth_rate = 0.04


class FixedGrowth6Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.06."""

    model_name = "FixedGrowth_6"
    growth_rate = 0.06


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
