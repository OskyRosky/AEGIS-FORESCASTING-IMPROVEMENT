"""Central registry for supported Model Lab forecasting models."""

from __future__ import annotations

from model_lab.models.autoarima_model import AutoARIMAModel
from model_lab.models.base_model import ForecastModel
from model_lab.models.ets_model import ETSModel
from model_lab.models.lightgbm_model import LightGBMModel
from model_lab.models.nbeats_model import NBEATSModel
from model_lab.models.nhits_model import NHITSModel
from model_lab.models.theta_model import ThetaModel
from model_lab.models.xgboost_model import XGBoostModel


MODEL_REGISTRY: dict[str, type[ForecastModel]] = {}


def register_model(model_class: type[ForecastModel]) -> None:
    """Register a ForecastModel implementation by model_name."""

    if not issubclass(model_class, ForecastModel):
        raise TypeError("Registered model must inherit ForecastModel.")
    MODEL_REGISTRY[model_class.model_name] = model_class


def get_model(model_name: str) -> type[ForecastModel]:
    """Return a registered model class by name."""

    if model_name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {model_name}")
    return MODEL_REGISTRY[model_name]


def list_models() -> list[str]:
    """Return registered model names."""

    return sorted(MODEL_REGISTRY.keys())


def list_model_families() -> list[str]:
    """Return registered model families."""

    return sorted({model.model_family for model in MODEL_REGISTRY.values()})


for candidate_model in (
    AutoARIMAModel,
    ThetaModel,
    ETSModel,
    LightGBMModel,
    XGBoostModel,
    NBEATSModel,
    NHITSModel,
):
    register_model(candidate_model)
