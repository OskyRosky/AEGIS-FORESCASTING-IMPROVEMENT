import importlib
import importlib.util

mods = [
    "statsmodels", "pmdarima", "lightgbm", "xgboost", "torch", "darts",
    "neuralforecast", "statsforecast", "numpy", "pandas", "scipy", "sklearn",
]
for m in mods:
    spec = importlib.util.find_spec(m)
    if spec is None:
        print(f"{m}: MISSING")
        continue
    try:
        mod = importlib.import_module(m)
        print(f"{m}: OK {getattr(mod, '__version__', '?')}")
    except Exception as e:  # noqa: BLE001
        print(f"{m}: IMPORT_ERROR {type(e).__name__}: {e}")

# Probe modern neuralforecast API
try:
    from neuralforecast import NeuralForecast  # noqa: F401
    from neuralforecast.models import NHITS, NBEATS  # noqa: F401

    print("neuralforecast_modern_api: OK")
except Exception as e:  # noqa: BLE001
    print(f"neuralforecast_modern_api: FAIL {type(e).__name__}: {e}")

# Probe darts NBEATS + Theta
try:
    from darts.models import NBEATSModel, Theta  # noqa: F401

    print("darts_models: OK")
except Exception as e:  # noqa: BLE001
    print(f"darts_models: FAIL {type(e).__name__}: {e}")
