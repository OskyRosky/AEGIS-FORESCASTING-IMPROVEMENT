"""Central metadata for supported Model Lab forecasting candidates."""

from __future__ import annotations


MODEL_METADATA = [
    {
        "model_name": "ARIMA_Fixed",
        "model_family": "BaselineProduction",
        "description": (
            "Fixed ARIMA configuration matching current AD notebook logic, "
            "ARIMA(p=0,d=2,q=0)."
        ),
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "ETS_Current",
        "model_family": "BaselineProduction",
        "description": "Current ExponentialSmoothing baseline implementation.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "LinearRegression",
        "model_family": "BaselineProduction",
        "description": "Current LinearRegressionModel with lags=30.",
        "supports_multivariate": True,
        "supports_exogenous": True,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "FixedGrowth_1_5",
        "model_family": "BaselineProduction",
        "description": "FixedGrowthModel with growth_rate=0.015.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "FixedGrowth_3",
        "model_family": "BaselineProduction",
        "description": "FixedGrowthModel with growth_rate=0.03.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "FixedGrowth_4",
        "model_family": "BaselineProduction",
        "description": "FixedGrowthModel with growth_rate=0.04.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "FixedGrowth_6",
        "model_family": "BaselineProduction",
        "description": "FixedGrowthModel with growth_rate=0.06.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "AutoARIMA",
        "model_family": "Statistical",
        "description": "Automatic ARIMA-style statistical forecasting model.",
        "supports_multivariate": False,
        "supports_exogenous": True,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "Theta",
        "model_family": "Statistical",
        "description": "Theta method statistical forecasting model.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "ETS",
        "model_family": "Statistical",
        "description": "Error-trend-seasonality statistical forecasting model.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "LightGBM",
        "model_family": "MachineLearning",
        "description": "Gradient boosted tree forecasting model using LightGBM.",
        "supports_multivariate": True,
        "supports_exogenous": True,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "XGBoost",
        "model_family": "MachineLearning",
        "description": "Gradient boosted tree forecasting model using XGBoost.",
        "supports_multivariate": True,
        "supports_exogenous": True,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "NBEATS",
        "model_family": "DeepLearning",
        "description": "Neural basis expansion forecasting model.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
    {
        "model_name": "NHITS",
        "model_family": "DeepLearning",
        "description": "Neural hierarchical interpolation forecasting model.",
        "supports_multivariate": False,
        "supports_exogenous": False,
        "supports_probabilistic_forecasts": False,
    },
]


def get_model_metadata() -> list[dict]:
    """Return model metadata rows."""

    return MODEL_METADATA
