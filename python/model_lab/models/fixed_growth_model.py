"""Fixed growth baseline production placeholder implementations."""

from __future__ import annotations

from model_lab.models.base_model import ForecastModel


class FixedGrowthModel(ForecastModel):
    """Base placeholder for current FixedGrowthModel configurations."""

    model_name: str
    model_family = "BaselineProduction"
    growth_rate: float

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


class FixedGrowth15Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.015 placeholder."""

    model_name = "FixedGrowth_1_5"
    growth_rate = 0.015


class FixedGrowth3Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.03 placeholder."""

    model_name = "FixedGrowth_3"
    growth_rate = 0.03


class FixedGrowth4Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.04 placeholder."""

    model_name = "FixedGrowth_4"
    growth_rate = 0.04


class FixedGrowth6Model(FixedGrowthModel):
    """FixedGrowthModel with growth_rate=0.06 placeholder."""

    model_name = "FixedGrowth_6"
    growth_rate = 0.06
