"""Stage 07 - V2 Model Lab 60-Day Backtest Extension (ISOLATED, governed).

Self-contained walk-forward backtest at forecast_horizon_days = 60. Reproduces the
SAME 13-model roster that produced the governed 30-day backtest
(forecast_viewer_model_outputs.csv), using:
  * the project's own baseline model classes (model_registry) for the 7 baselines, and
  * faithful ports of the inline challenger forecasters from
    run_challenger_official_execution.py + run_challenger_official_execution_recovery.py
    for the 6 challengers (AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost,
    FastNeuralAR_MLP).

Generates REAL residual evidence for horizons 1-60 (no extrapolation).

ISOLATION GUARANTEES (does NOT touch any existing governed artifact):
  - Reads ONLY  outputs/evaluation/evaluation_dataset.csv  (canonical actuals)
  - Writes ONLY under  outputs/model_lab/backtest_60d/
  - Does NOT modify the 30-day artifacts, forecasts.csv,
    forecasts_with_intervals_relative.csv, configs, or any model/champion decision.

Fresh 60-day walk-forward windows step back by 60 days from the latest actual, so
every window's test period lies fully inside observed actuals (each window yields
real residuals for all horizons 1-60).

Usage:
  python -m model_lab.run_backtest_60d [--max-entities N]
"""

from __future__ import annotations

import argparse
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "python"))

from model_lab.models.model_registry import get_model  # noqa: E402

EVAL_PATH = ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
VIEWER_30D = ROOT / "data" / "processed" / "forecast_viewer_model_outputs.csv"
OUT_DIR = ROOT / "outputs" / "model_lab" / "backtest_60d"
FORECASTS_OUT = OUT_DIR / "forecast_viewer_model_outputs_60d.csv"
WINDOWS_OUT = OUT_DIR / "backtest_60d_windows.csv"
SUMMARY_OUT = OUT_DIR / "backtest_60d_summary.csv"
STATUS_OUT = OUT_DIR / "backtest_60d_model_status.csv"

# ---- backtest design (mirrors config/backtesting.yaml but horizon -> 60) ----
HORIZON = 60
N_WINDOWS = 12
MIN_TRAIN = 365
MIN_TEST = 60          # require a full 60-day evaluable test window
EXPANDING = True
RANDOM_SEED = 42

BASELINE_MODELS = [
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
]
CHALLENGER_MODELS = [
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
]
MODEL_FAMILY = {
    "ARIMA_Fixed": "statistical",
    "ETS_Current": "statistical",
    "LinearRegression": "machine_learning",
    "FixedGrowth_1_5": "growth_baseline",
    "FixedGrowth_3": "growth_baseline",
    "FixedGrowth_4": "growth_baseline",
    "FixedGrowth_6": "growth_baseline",
    "AutoARIMA": "statistical",
    "Theta": "statistical",
    "ETS Explicit": "statistical",
    "LightGBM": "machine_learning",
    "XGBoost": "machine_learning",
    "FastNeuralAR_MLP": "lightweight_neural",
}


# ============================ challenger forecasters ============================
# Faithful ports of the governed inline implementations, parameterized on horizon.

def _make_lag_matrix(values: np.ndarray, n_lags: int):
    rows_x, rows_y = [], []
    for i in range(n_lags, len(values)):
        rows_x.append(values[i - n_lags : i][::-1])
        rows_y.append(float(values[i]))
    return np.asarray(rows_x, dtype=float), np.asarray(rows_y, dtype=float)


def _recursive_tree_forecast(model, values: np.ndarray, n_lags: int, horizon: int) -> np.ndarray:
    history = list(values.astype(float))
    preds = []
    for _ in range(horizon):
        feats = np.asarray(history[-n_lags:][::-1], dtype=float).reshape(1, -1)
        yhat = float(model.predict(feats)[0])
        preds.append(yhat)
        history.append(yhat)
    return np.asarray(preds, dtype=float)


def _forecast_autoarima(values: np.ndarray, horizon: int) -> np.ndarray:
    import pmdarima as pm

    model = pm.auto_arima(
        values.astype(float), seasonal=False, start_p=0, start_q=0,
        max_p=2, max_q=2, max_order=4, stepwise=True,
        error_action="ignore", suppress_warnings=True, random_state=RANDOM_SEED,
    )
    return np.asarray(model.predict(horizon), dtype=float)


def _forecast_theta(values: np.ndarray, horizon: int) -> np.ndarray:
    from darts import TimeSeries
    from darts.models import Theta as DartsTheta

    ts = TimeSeries.from_values(values.astype(float))
    model = DartsTheta()
    model.fit(ts)
    return model.predict(horizon).values().flatten().astype(float)


def _forecast_ets(values: np.ndarray, horizon: int) -> np.ndarray:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    model = ExponentialSmoothing(values.astype(float), trend="add", seasonal=None).fit(optimized=True)
    return np.asarray(model.forecast(horizon), dtype=float)


def _forecast_lightgbm(values: np.ndarray, horizon: int) -> np.ndarray:
    import lightgbm as lgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = lgb.LGBMRegressor(
        n_estimators=100, random_state=RANDOM_SEED, verbosity=-1, deterministic=True, n_jobs=1,
    )
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags, horizon)


def _forecast_xgboost(values: np.ndarray, horizon: int) -> np.ndarray:
    import xgboost as xgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = xgb.XGBRegressor(
        n_estimators=100, random_state=RANDOM_SEED, verbosity=0, n_jobs=1,
    )
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags, horizon)


def _forecast_fast_neural(values: np.ndarray, horizon: int) -> np.ndarray:
    from sklearn.exceptions import ConvergenceWarning
    from sklearn.neural_network import MLPRegressor
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler

    if len(values) < 10:
        raise ValueError(f"insufficient training history ({len(values)} rows)")
    n_lags = min(30, max(2, len(values) - 1))
    x, y = _make_lag_matrix(values.astype(float), n_lags)
    if len(y) < 5:
        raise ValueError(f"insufficient lag training rows ({len(y)} rows)")
    early_stopping = len(y) >= 20
    validation_fraction = 0.15 if early_stopping else 0.1
    mlp = MLPRegressor(
        hidden_layer_sizes=(32,), activation="relu", solver="adam", max_iter=300,
        random_state=RANDOM_SEED, early_stopping=early_stopping, validation_fraction=validation_fraction,
    )
    model = Pipeline([("scale", StandardScaler()), ("mlp", mlp)])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(x, y)
    history = list(values.astype(float))
    preds = []
    for _ in range(horizon):
        feats = np.asarray(history[-n_lags:][::-1], dtype=float).reshape(1, -1)
        preds.append(float(model.predict(feats)[0]))
        history.append(preds[-1])
    return np.asarray(preds, dtype=float)


CHALLENGER_FORECASTERS = {
    "AutoARIMA": _forecast_autoarima,
    "Theta": _forecast_theta,
    "ETS Explicit": _forecast_ets,
    "LightGBM": _forecast_lightgbm,
    "XGBoost": _forecast_xgboost,
    "FastNeuralAR_MLP": _forecast_fast_neural,
}


def _forecast_baseline(model_name: str, training_df: pd.DataFrame, horizon: int) -> np.ndarray:
    model = get_model(model_name)()
    model.fit(training_df)
    return np.asarray(model.predict(horizon), dtype=float)


def forecast_one(model_name: str, training_df: pd.DataFrame, horizon: int) -> np.ndarray:
    if model_name in BASELINE_MODELS:
        return _forecast_baseline(model_name, training_df, horizon)
    values = training_df.sort_values("date")["value"].to_numpy(dtype=float)
    return CHALLENGER_FORECASTERS[model_name](values, horizon)


# ============================ windows ============================

def generate_windows(entity_dates: pd.Series) -> list[dict]:
    dates = pd.to_datetime(entity_dates).sort_values().reset_index(drop=True)
    if dates.empty:
        return []
    first_actual = dates.min()
    latest_actual = dates.max()
    date_set = set(dates.dt.normalize())
    windows = []
    for offset in range(N_WINDOWS):
        test_end = latest_actual - pd.Timedelta(days=offset * HORIZON)
        test_start = test_end - pd.Timedelta(days=HORIZON - 1)
        train_start = first_actual
        train_end = test_start - pd.Timedelta(days=1)
        if train_end < train_start:
            continue
        train_obs = int(((dates >= train_start) & (dates <= train_end)).sum())
        test_obs = int(((dates >= test_start) & (dates <= test_end)).sum())
        if train_obs < MIN_TRAIN or test_obs < MIN_TEST:
            continue
        windows.append(
            {
                "window_id": N_WINDOWS - offset,
                "train_start_date": train_start,
                "train_end_date": train_end,
                "test_start_date": test_start,
                "test_end_date": test_end,
                "train_observations": train_obs,
                "test_observations": test_obs,
            }
        )
    return sorted(windows, key=lambda r: r["window_id"])


# ============================ main run ============================

def run(max_entities: int | None = None) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    run_id = f"backtest_60d_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    ts = datetime.now().isoformat(timespec="seconds")

    ev = pd.read_csv(EVAL_PATH, parse_dates=["date"])
    ev = ev[ev["record_type"].astype(str).str.lower() == "actual"].copy()
    ev["value"] = pd.to_numeric(ev["value"], errors="coerce")
    ev = ev.dropna(subset=["entity_key", "date", "value"]).sort_values(["entity_key", "date"])

    eligible = sorted(pd.read_csv(VIEWER_30D, usecols=["series_key"])["series_key"].unique())
    if max_entities:
        eligible = eligible[:max_entities]
    print(f"[run] {run_id} | entities={len(eligible)} | horizon={HORIZON}", flush=True)

    roster = BASELINE_MODELS + CHALLENGER_MODELS
    forecast_rows = []
    window_rows = []
    status_rows = []

    for ei, key in enumerate(eligible, 1):
        g = ev[ev["entity_key"] == key]
        wins = generate_windows(g["date"])
        actual_by_date = dict(zip(g["date"].dt.normalize(), g["value"]))
        ek_t0 = time.time()
        for w in wins:
            window_rows.append({"entity_key": key, **{k: (v.date() if hasattr(v, "date") else v) for k, v in w.items()}})
            train_df = g[g["date"] <= w["train_end_date"]][["date", "value"]]
            test_dates = pd.date_range(w["test_start_date"], w["test_end_date"], freq="D")
            for model_name in roster:
                t0 = time.time()
                try:
                    preds = forecast_one(model_name, train_df, HORIZON)
                    if len(preds) != HORIZON or not np.all(np.isfinite(preds)):
                        raise ValueError(f"bad forecast length/finite ({len(preds)})")
                    for h, (d, fv) in enumerate(zip(test_dates, preds), start=1):
                        forecast_rows.append(
                            {
                                "run_id": run_id,
                                "series_key": key,
                                "model_name": model_name,
                                "model_family": MODEL_FAMILY[model_name],
                                "window_id": w["window_id"],
                                "forecast_start_date": w["test_start_date"].date(),
                                "date": d.date(),
                                "horizon_days": h,
                                "forecast_value": float(fv),
                                "actual_value": (
                                    float(actual_by_date[d.normalize()])
                                    if d.normalize() in actual_by_date else np.nan
                                ),
                                "created_timestamp": ts,
                            }
                        )
                    status_rows.append({"series_key": key, "window_id": w["window_id"], "model_name": model_name,
                                        "status": "completed", "message": "", "runtime_s": round(time.time() - t0, 3)})
                except Exception as exc:  # pragma: no cover
                    status_rows.append({"series_key": key, "window_id": w["window_id"], "model_name": model_name,
                                        "status": "failed", "message": f"{type(exc).__name__}: {exc}",
                                        "runtime_s": round(time.time() - t0, 3)})
        print(f"[{ei}/{len(eligible)}] {key}: {len(wins)} windows in {time.time()-ek_t0:.1f}s "
              f"(elapsed {time.time()-t_start:.0f}s)", flush=True)

    fc = pd.DataFrame(forecast_rows)
    wdf = pd.DataFrame(window_rows)
    sdf = pd.DataFrame(status_rows)
    fc.to_csv(FORECASTS_OUT, index=False)
    wdf.to_csv(WINDOWS_OUT, index=False)
    sdf.to_csv(STATUS_OUT, index=False)

    n_fail = int((sdf["status"] == "failed").sum()) if not sdf.empty else 0
    summary = pd.DataFrame([{
        "run_id": run_id,
        "entities": len(eligible),
        "models": len(roster),
        "windows_total": len(wdf),
        "forecast_rows": len(fc),
        "model_jobs": len(sdf),
        "model_jobs_failed": n_fail,
        "horizon_days": HORIZON,
        "n_windows_config": N_WINDOWS,
        "min_train": MIN_TRAIN,
        "min_test": MIN_TEST,
        "runtime_seconds": round(time.time() - t_start, 1),
        "created_timestamp": ts,
    }])
    summary.to_csv(SUMMARY_OUT, index=False)
    print(f"[done] rows={len(fc)} jobs={len(sdf)} failed={n_fail} "
          f"runtime={time.time()-t_start:.0f}s -> {FORECASTS_OUT}", flush=True)


if __name__ == "__main__":
    warnings.filterwarnings("ignore")
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-entities", type=int, default=None)
    args = ap.parse_args()
    run(max_entities=args.max_entities)
