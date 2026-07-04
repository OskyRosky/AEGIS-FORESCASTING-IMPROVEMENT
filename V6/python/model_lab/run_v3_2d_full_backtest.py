"""V3.2D - Candidate Remediation + Governed Full Backtest.

ISOLATED, READ-ONLY-INPUT, EXPERIMENTAL.

Authorized scope (V3.2D):
  1. Fix NLIN-DLIN to avoid RAW negatives by construction (log-space NLinear + expm1 bounded inverse).
  2. Reformulate LGBM/XGB to a single-model-with-horizon-feature design and RE-RUN the subset runtime
     gate; only include them in the full backtest if they pass (else DEFERRED_NOT_VIABLE_FOR_V3_DAILY_REFRESH).
  3. Run the governed full backtest (39 series, walk-forward windows, h1-30) for the viable candidates.
  4. Compare against the governed ETS Explicit champion + existing baselines (anchors, NOT re-fit).
  5. Emit per-candidate recommendations. NO model promoted.

Governance (honored):
  - V3 only. V1/V2 untouched. Champion/forecasts/intervals/governance unchanged.
  - Inputs READ-ONLY (governed): backtesting_windows.csv + evaluation_dataset.csv (record_type=='actual').
  - The MASE/RMSSE denominator is the GOVERNED training-only lag-1 first-difference MAE/MSE
    (reused verbatim from model_lab.benchmark_denominators) so candidate numbers sit on the SAME axis
    as the governed scorecard (ETS Explicit MASE 6.901 / RMSSE 1.856).
  - ALL outputs ONLY under outputs/v3_2b_model_candidates/. data/processed/ never written. No promotion.

Model universe in the comparison:
  - Existing governed anchors (NOT re-fit): ETS Explicit (champion), AutoARIMA, Theta, ETS_Current,
    ARIMA_Fixed, LinearRegression, FixedGrowth_*, current LightGBM, current XGBoost, current FastNeuralAR_MLP.
  - 3 Deep Learning candidates: FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN.
  - ML challenger candidate(s): ENET-RIDGE (and reformulated LGBM-IMP-v2 / XGB-IMP-v2 if they pass the re-gate).
"""

from __future__ import annotations

import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.exceptions import ConvergenceWarning
from sklearn.linear_model import Ridge
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "python"))

# Reuse the GOVERNED denominator definition verbatim (training-only lag-1 MAE/MSE, epsilon floor).
from model_lab.benchmark_denominators import (  # noqa: E402
    EPSILON,
    compute_training_only_denominators,
    load_actuals,
    load_windows,
)

OUT_ROOT = PROJECT_ROOT / "outputs" / "v3_2b_model_candidates"
DIR_RUNTIME = OUT_ROOT / "runtime_checks"
DIR_CANDOUT = OUT_ROOT / "candidate_outputs"
DIR_METRICS = OUT_ROOT / "metrics"
DIR_LOGS = OUT_ROOT / "logs"

RANDOM_SEED = 42
HORIZON_DAYS = 30
LAGS = 30
TOTAL_GOVERNED_ENTITY_WINDOWS = 454
NOT_VIABLE_PROJECTED_MINUTES = 25.0
RUNTIME_GATE_MINUTES = 30.0

# ---- Runtime control (V3.2D mandatory operating rule) ----
MAX_WALL_CLOCK_BUDGET_MINUTES = 30.0   # hard wall-clock budget for the whole full backtest
CANDIDATE_BUDGET_SAFETY = 2.0          # per-candidate budget = estimate * safety factor
CANDIDATE_BUDGET_MIN_MINUTES = 2.0     # floor for a per-candidate budget
PROGRESS_EVERY = 25                    # emit a progress line every N windows

# Deterministic 5-series subset (same as V3.2C) for the GBM re-gate.
SUBSET_SERIES = ["NAM-Multitenant", "EUR-Multitenant", "LAM-Multitenant", "APC-Dedicated", "NAM-TDF"]
DRY_RUN_WINDOWS_PER_SERIES = 3

# Governed anchor metrics (READ-ONLY reference, from tournament_model_scorecard.csv; NOT re-fit here).
ANCHORS = [
    ("ETS Explicit", "statistical", 6.901143533373399, 1.856193218184295, "champion"),
    ("AutoARIMA", "statistical", 8.088530320808188, 1.8590126984374988, "baseline"),
    ("FixedGrowth_1_5", "growth_baseline", 8.649280961006667, 2.2718379673062783, "baseline"),
    ("ETS_Current", "statistical", 8.65417111153676, 2.273019421267602, "baseline"),
    ("LinearRegression", "machine_learning", 9.49576945571986, 2.7517633206678718, "baseline"),
    ("Theta", "statistical", 10.642289708177191, 2.819225444576951, "baseline"),
    ("ARIMA_Fixed", "statistical", 11.789916350319965, 3.49334506602668, "baseline"),
    ("FixedGrowth_3", "growth_baseline", 12.989045570820014, 3.019316356642247, "baseline"),
    ("XGBoost", "machine_learning", 14.547628304157428, 3.880790199165525, "baseline_current"),
    ("LightGBM", "machine_learning", 16.04104170759398, 4.061386180935608, "baseline_current"),
    ("FixedGrowth_4", "growth_baseline", 16.52907963144241, 4.072356391248675, "baseline"),
    ("FixedGrowth_6", "growth_baseline", 27.01539149184708, 5.083541365063246, "baseline"),
    ("FastNeuralAR_MLP", "lightweight_neural", 739.9218881736479, 164.62241686434226, "under_audit"),
]
CHAMPION_MASE = 6.901143533373399

CONTRACT_COLUMNS = [
    "candidate_id", "model_name", "model_family", "series_key", "forecast_origin",
    "horizon", "forecast_date", "forecast_value", "actual_value", "error",
    "abs_error", "squared_error", "mase", "rmsse", "smape_or_mae_if_available",
    "runtime_seconds", "status", "failure_reason", "guardrail_pass",
    "negative_forecast_count", "notes",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _fmt_mins(seconds: float) -> str:
    return f"{seconds / 60.0:.1f}min"


def _emit_progress(label: str, done: int, total: int, loop_t0: float, final: bool = False) -> None:
    """Unbuffered incremental progress: candidate, windows done/total, elapsed, ETA, status."""
    elapsed = time.perf_counter() - loop_t0
    rate = (elapsed / done) if done > 0 else 0.0
    remaining = rate * (total - done)
    pct = (100.0 * done / total) if total else 0.0
    status = "DONE" if final else "RUNNING"
    print(f"   [progress] {label:18s} {done:4d}/{total:<4d} ({pct:5.1f}%) "
          f"elapsed={_fmt_mins(elapsed)} eta={_fmt_mins(remaining)} status={status}",
          flush=True)


# --------------------------------------------------------------------------- #
# Feature builders (direct multi-horizon, no recursion)
# --------------------------------------------------------------------------- #
def build_xy(values: np.ndarray, lags: int, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    rows_x, rows_y = [], []
    n = len(values)
    for idx in range(lags, n - horizon + 1):
        rows_x.append(values[idx - lags:idx][::-1])
        rows_y.append(values[idx:idx + horizon])
    if not rows_x:
        return np.empty((0, lags)), np.empty((0, horizon))
    return np.asarray(rows_x, dtype=float), np.asarray(rows_y, dtype=float)


def build_xy_horizon_feature(values: np.ndarray, lags: int, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """Single-model design: features = [lags..., horizon_index]; target = value at that horizon."""
    rows_x, rows_y = [], []
    n = len(values)
    for idx in range(lags, n - horizon + 1):
        base = values[idx - lags:idx][::-1]
        for h in range(1, horizon + 1):
            rows_x.append(np.concatenate([base, [float(h)]]))
            rows_y.append(values[idx + h - 1])
    if not rows_x:
        return np.empty((0, lags + 1)), np.empty((0,))
    return np.asarray(rows_x, dtype=float), np.asarray(rows_y, dtype=float)


def last_feats(values: np.ndarray, lags: int) -> np.ndarray:
    return np.asarray(values[-lags:][::-1], dtype=float).reshape(1, -1)


def _clamp(arr: np.ndarray) -> tuple[np.ndarray, int]:
    raw_neg = int((arr < 0).sum())
    return np.clip(arr, 0.0, None), raw_neg


# --------------------------------------------------------------------------- #
# Candidate fit/predict
# --------------------------------------------------------------------------- #
def fit_fnar_v2(values: np.ndarray) -> tuple[np.ndarray, int]:
    t = np.log1p(np.clip(values, 0.0, None))
    X, Y = build_xy(t, LAGS, HORIZON_DAYS)
    if len(X) < 5:
        raise ValueError(f"insufficient rows ({len(X)})")
    mlp = MLPRegressor(hidden_layer_sizes=(32,), activation="relu", solver="adam", alpha=1e-3,
                       max_iter=300, early_stopping=len(X) >= 20, validation_fraction=0.1,
                       random_state=RANDOM_SEED)
    model = Pipeline([("scale", StandardScaler()), ("mlp", mlp)])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(X, Y)
    feats = np.log1p(np.clip(last_feats(values, LAGS), 0.0, None))
    return _clamp(np.expm1(np.asarray(model.predict(feats)).ravel()))


def fit_nlinear_fixed(values: np.ndarray) -> tuple[np.ndarray, int]:
    """NLinear in LOG space: positive target transform + expm1 bounded inverse => no raw negatives."""
    t = np.log1p(np.clip(values, 0.0, None))
    X, Y = build_xy(t, LAGS, HORIZON_DAYS)
    if len(X) < 5:
        raise ValueError(f"insufficient rows ({len(X)})")
    last = X[:, 0].reshape(-1, 1)  # last observed log-value per row (NLinear normalization)
    model = Ridge(alpha=1.0, random_state=RANDOM_SEED)
    model.fit(X - last, Y - last)
    feats = np.log1p(np.clip(last_feats(values, LAGS), 0.0, None))
    f_last = feats[0, 0]
    pred_log = np.asarray(model.predict(feats - f_last)).ravel() + f_last
    return _clamp(np.expm1(pred_log))


def fit_ridge_direct(values: np.ndarray) -> tuple[np.ndarray, int]:
    t = np.log1p(np.clip(values, 0.0, None))
    X, Y = build_xy(t, LAGS, HORIZON_DAYS)
    if len(X) < 5:
        raise ValueError(f"insufficient rows ({len(X)})")
    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0, random_state=RANDOM_SEED))])
    model.fit(X, Y)
    feats = np.log1p(np.clip(last_feats(values, LAGS), 0.0, None))
    return _clamp(np.expm1(np.asarray(model.predict(feats)).ravel()))


def fit_gbm_v2(values: np.ndarray, kind: str) -> tuple[np.ndarray, int]:
    """Reformulated GBM: ONE model with horizon-as-feature (was 30 per-horizon boosters in V3.2C)."""
    t = np.log1p(np.clip(values, 0.0, None))
    X, Y = build_xy_horizon_feature(t, LAGS, HORIZON_DAYS)
    if len(X) < 30:
        raise ValueError(f"insufficient rows ({len(X)})")
    if kind == "lgbm":
        from lightgbm import LGBMRegressor
        model = LGBMRegressor(n_estimators=300, num_leaves=31, learning_rate=0.05,
                              subsample=0.9, colsample_bytree=0.9, random_state=RANDOM_SEED,
                              n_jobs=-1, verbose=-1)
    else:
        from xgboost import XGBRegressor
        model = XGBRegressor(n_estimators=300, max_depth=6, learning_rate=0.05, subsample=0.9,
                             colsample_bytree=0.9, tree_method="hist", random_state=RANDOM_SEED,
                             n_jobs=-1, verbosity=0)
    model.fit(X, Y)
    base = last_feats(values, LAGS)
    base_log = np.log1p(np.clip(base, 0.0, None))
    feats = np.hstack([np.repeat(base_log, HORIZON_DAYS, axis=0),
                       np.arange(1, HORIZON_DAYS + 1).reshape(-1, 1).astype(float)])
    return _clamp(np.expm1(np.asarray(model.predict(feats)).ravel()))


def fit_global_mlp(pooled_X: np.ndarray, pooled_Y: np.ndarray) -> Pipeline:
    mlp = MLPRegressor(hidden_layer_sizes=(16,), activation="relu", solver="adam", alpha=1e-3,
                       max_iter=150, early_stopping=len(pooled_X) >= 20, validation_fraction=0.1,
                       random_state=RANDOM_SEED)
    model = Pipeline([("scale", StandardScaler()), ("mlp", mlp)])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(pooled_X, pooled_Y)
    return model


# --------------------------------------------------------------------------- #
# Data helpers
# --------------------------------------------------------------------------- #
def series_until(actuals_by_entity: dict, entity: str, train_end: pd.Timestamp) -> np.ndarray:
    g = actuals_by_entity.get(entity)
    if g is None:
        return np.empty(0)
    return g[g["date"] <= train_end]["value"].to_numpy(dtype=float)


def test_vals(actuals_by_entity: dict, entity: str, ts: pd.Timestamp, te: pd.Timestamp) -> np.ndarray:
    g = actuals_by_entity.get(entity)
    if g is None:
        return np.empty(0)
    return g[(g["date"] >= ts) & (g["date"] <= te)]["value"].to_numpy(dtype=float)


def window_scores(fc: np.ndarray, act: np.ndarray, denom_mae: float, denom_mse: float) -> dict:
    h = min(len(fc), len(act))
    f, a = fc[:h], act[:h]
    err = f - a
    mae_model = float(np.mean(np.abs(err)))
    rmse_model = float(np.sqrt(np.mean(err ** 2)))
    mase = mae_model / denom_mae if denom_mae > 0 else float("nan")
    rmsse = rmse_model / np.sqrt(denom_mse) if denom_mse > 0 else float("nan")
    denom = np.abs(f) + np.abs(a)
    smape = float(np.mean(np.where(denom > 0, 2.0 * np.abs(err) / denom, 0.0)))
    return {"mase": mase, "rmsse": rmsse, "smape": smape, "bias": float(np.mean(err)),
            "mae_model": mae_model, "h": h}


def run_candidate(cand_id, model_name, family, windows, abe, denom_idx, forecaster, log_rows, contract_rows,
                  global_deadline=None, cand_deadline=None, progress_label=None):
    """Run a per-series candidate over windows; returns (per_window, runtime, raw_neg, stop_status).

    stop_status in {"ok", "CANDIDATE_TIME_BUDGET_EXCEEDED", "TIME_BUDGET_EXCEEDED"}.
    """
    per_window: list[dict] = []
    runtime = 0.0
    raw_neg_total = 0
    stop_status = "ok"
    total_w = len(windows)
    loop_t0 = time.perf_counter()
    note = {"FNAR-V2": "direct_multi_horizon;log1p",
            "NLIN-DLIN_FIXED": "nlinear_log_space;expm1_bounded_inverse",
            "ENET-RIDGE": "ridge_direct;log1p",
            "SMLP-TCN": "global_pooled_mlp;log1p",
            "LGBM-IMP-v2": "single_model_horizon_feature;log1p",
            "XGB-IMP-v2": "single_model_horizon_feature;log1p"}.get(cand_id, "")
    for _i, (_, w) in enumerate(windows.iterrows()):
        now = time.perf_counter()
        if global_deadline is not None and now > global_deadline:
            stop_status = "TIME_BUDGET_EXCEEDED"
            break
        if cand_deadline is not None and now > cand_deadline:
            stop_status = "CANDIDATE_TIME_BUDGET_EXCEEDED"
            break
        if progress_label and total_w and _i > 0 and (_i % PROGRESS_EVERY == 0):
            _emit_progress(progress_label, _i, total_w, loop_t0)
        entity = str(w["entity_key"]); wid = int(w["window_id"])
        te = pd.to_datetime(w["train_end_date"]); ts = pd.to_datetime(w["test_start_date"])
        tend = pd.to_datetime(w["test_end_date"]); origin = te.date().isoformat()
        train = series_until(abe, entity, te); act = test_vals(abe, entity, ts, tend)
        t0 = time.perf_counter()
        try:
            if len(train) < LAGS + HORIZON_DAYS + 5:
                raise ValueError(f"history too short ({len(train)})")
            fc, raw_neg = forecaster(train)
        except Exception as exc:  # noqa: BLE001
            dt = time.perf_counter() - t0; runtime += dt
            log_rows.append({"timestamp": _now(), "candidate_id": cand_id, "series_key": entity,
                             "window_id": wid, "forecast_origin": origin, "status": "failed",
                             "runtime_seconds": round(dt, 4),
                             "message": f"{type(exc).__name__}: {exc}"[:200]})
            continue
        dt = time.perf_counter() - t0; runtime += dt; raw_neg_total += raw_neg
        d = denom_idx.get((entity, wid))
        if d is None:
            continue
        m = window_scores(fc, act, d[0], d[1]); per_window.append(m)
        if contract_rows is not None:
            for hh in range(HORIZON_DAYS):
                a = float(act[hh]) if hh < len(act) else np.nan
                fval = float(fc[hh]); err = (fval - a) if np.isfinite(a) else np.nan
                contract_rows.append({
                    "candidate_id": cand_id, "model_name": model_name, "model_family": family,
                    "series_key": entity, "forecast_origin": origin, "horizon": hh + 1,
                    "forecast_date": (ts + pd.Timedelta(days=hh)).date().isoformat(),
                    "forecast_value": round(fval, 6),
                    "actual_value": (round(a, 6) if np.isfinite(a) else ""),
                    "error": (round(err, 6) if np.isfinite(err) else ""),
                    "abs_error": (round(abs(err), 6) if np.isfinite(err) else ""),
                    "squared_error": (round(err ** 2, 6) if np.isfinite(err) else ""),
                    "mase": round(m["mase"], 6) if np.isfinite(m["mase"]) else "",
                    "rmsse": round(m["rmsse"], 6) if np.isfinite(m["rmsse"]) else "",
                    "smape_or_mae_if_available": round(m["smape"], 6),
                    "runtime_seconds": round(dt, 4), "status": "ok", "failure_reason": "",
                    "guardrail_pass": "", "negative_forecast_count": raw_neg, "notes": note})
        log_rows.append({"timestamp": _now(), "candidate_id": cand_id, "series_key": entity,
                         "window_id": wid, "forecast_origin": origin, "status": "ok",
                         "runtime_seconds": round(dt, 4),
                         "message": f"mase={m['mase']:.3f} rmsse={m['rmsse']:.3f} raw_neg={raw_neg}"})
    if progress_label and total_w:
        _emit_progress(progress_label, len(per_window), total_w, loop_t0, final=(stop_status == "ok"))
    return per_window, runtime, raw_neg_total, stop_status


def run_smlp_global(cand_id, model_name, family, windows, abe, denom_idx, all_series, log_rows, contract_rows,
                    global_deadline=None, cand_deadline=None, progress_label=None):
    """SmallMLPGlobal: pool ALL series at each window_id, fit once, predict each series."""
    per_window: list[dict] = []; runtime = 0.0; raw_neg_total = 0
    stop_status = "ok"
    total_w = len(windows)
    loop_t0 = time.perf_counter()
    cache: dict[int, Pipeline] = {}
    for _i, (_, w) in enumerate(windows.iterrows()):
        now = time.perf_counter()
        if global_deadline is not None and now > global_deadline:
            stop_status = "TIME_BUDGET_EXCEEDED"
            break
        if cand_deadline is not None and now > cand_deadline:
            stop_status = "CANDIDATE_TIME_BUDGET_EXCEEDED"
            break
        if progress_label and total_w and _i > 0 and (_i % PROGRESS_EVERY == 0):
            _emit_progress(progress_label, _i, total_w, loop_t0)
        entity = str(w["entity_key"]); wid = int(w["window_id"])
        te = pd.to_datetime(w["train_end_date"]); ts = pd.to_datetime(w["test_start_date"])
        tend = pd.to_datetime(w["test_end_date"]); origin = te.date().isoformat()
        t0 = time.perf_counter()
        try:
            if wid not in cache:
                Xs, Ys = [], []
                wsub = windows[windows["window_id"] == wid]
                for _, ww in wsub.iterrows():
                    ent = str(ww["entity_key"]); tee = pd.to_datetime(ww["train_end_date"])
                    vv = series_until(abe, ent, tee)
                    if len(vv) < LAGS + HORIZON_DAYS + 5:
                        continue
                    Xi, Yi = build_xy(np.log1p(np.clip(vv, 0.0, None)), LAGS, HORIZON_DAYS)
                    if len(Xi):
                        Xs.append(Xi); Ys.append(Yi)
                if not Xs:
                    raise ValueError("no pooled training data")
                cache[wid] = fit_global_mlp(np.vstack(Xs), np.vstack(Ys))
            train = series_until(abe, entity, te)
            if len(train) < LAGS + HORIZON_DAYS + 5:
                raise ValueError(f"history too short ({len(train)})")
            feats = np.log1p(np.clip(last_feats(train, LAGS), 0.0, None))
            fc, raw_neg = _clamp(np.expm1(np.asarray(cache[wid].predict(feats)).ravel()))
        except Exception as exc:  # noqa: BLE001
            dt = time.perf_counter() - t0; runtime += dt
            log_rows.append({"timestamp": _now(), "candidate_id": cand_id, "series_key": entity,
                             "window_id": wid, "forecast_origin": origin, "status": "failed",
                             "runtime_seconds": round(dt, 4),
                             "message": f"{type(exc).__name__}: {exc}"[:200]})
            continue
        dt = time.perf_counter() - t0; runtime += dt; raw_neg_total += raw_neg
        act = test_vals(abe, entity, ts, tend); d = denom_idx.get((entity, wid))
        if d is None:
            continue
        m = window_scores(fc, act, d[0], d[1]); per_window.append(m)
        if contract_rows is not None:
            for hh in range(HORIZON_DAYS):
                a = float(act[hh]) if hh < len(act) else np.nan
                fval = float(fc[hh]); err = (fval - a) if np.isfinite(a) else np.nan
                contract_rows.append({
                    "candidate_id": cand_id, "model_name": model_name, "model_family": family,
                    "series_key": entity, "forecast_origin": origin, "horizon": hh + 1,
                    "forecast_date": (ts + pd.Timedelta(days=hh)).date().isoformat(),
                    "forecast_value": round(fval, 6),
                    "actual_value": (round(a, 6) if np.isfinite(a) else ""),
                    "error": (round(err, 6) if np.isfinite(err) else ""),
                    "abs_error": (round(abs(err), 6) if np.isfinite(err) else ""),
                    "squared_error": (round(err ** 2, 6) if np.isfinite(err) else ""),
                    "mase": round(m["mase"], 6) if np.isfinite(m["mase"]) else "",
                    "rmsse": round(m["rmsse"], 6) if np.isfinite(m["rmsse"]) else "",
                    "smape_or_mae_if_available": round(m["smape"], 6),
                    "runtime_seconds": round(dt, 4), "status": "ok", "failure_reason": "",
                    "guardrail_pass": "", "negative_forecast_count": raw_neg,
                    "notes": "global_pooled_mlp;log1p"})
        log_rows.append({"timestamp": _now(), "candidate_id": cand_id, "series_key": entity,
                         "window_id": wid, "forecast_origin": origin, "status": "ok",
                         "runtime_seconds": round(dt, 4),
                         "message": f"mase={m['mase']:.3f} rmsse={m['rmsse']:.3f} raw_neg={raw_neg}"})
    if progress_label and total_w:
        _emit_progress(progress_label, len(per_window), total_w, loop_t0, final=(stop_status == "ok"))
    return per_window, runtime, raw_neg_total, stop_status


def aggregate(per_window: list[dict]) -> dict:
    valid = [m for m in per_window if np.isfinite(m["mase"])]
    if not valid:
        return {"median_mase": float("nan"), "mean_mase": float("nan"), "p95_mase": float("nan"),
                "median_rmsse": float("nan"), "mean_smape": float("nan"), "mean_bias": float("nan"),
                "pct_windows_beating_naive": float("nan"), "n_windows": 0}
    mases = np.array([m["mase"] for m in valid]); rmsses = np.array([m["rmsse"] for m in valid])
    return {"median_mase": float(np.median(mases)), "mean_mase": float(np.mean(mases)),
            "p95_mase": float(np.percentile(mases, 95)), "median_rmsse": float(np.median(rmsses)),
            "mean_smape": float(np.mean([m["smape"] for m in valid])),
            "mean_bias": float(np.mean([m["bias"] for m in valid])),
            "pct_windows_beating_naive": float(np.mean(mases < 1.0) * 100.0), "n_windows": len(valid)}


def _median_series(abe: dict) -> np.ndarray:
    arrs = [v["value"].to_numpy(dtype=float) for v in abe.values()]
    arrs.sort(key=len)
    return arrs[len(arrs) // 2] if arrs else np.empty(0)


def _estimate_smlp_minutes(windows, abe, unique_wids: int) -> float:
    """Calibrate one pooled global-MLP fit (largest window_id) and project across unique window_ids."""
    if not unique_wids:
        return 0.0
    wid = int(windows["window_id"].value_counts().idxmax())
    wsub = windows[windows["window_id"] == wid]
    Xs, Ys = [], []
    for _, ww in wsub.iterrows():
        ent = str(ww["entity_key"]); tee = pd.to_datetime(ww["train_end_date"])
        vv = series_until(abe, ent, tee)
        if len(vv) < LAGS + HORIZON_DAYS + 5:
            continue
        Xi, Yi = build_xy(np.log1p(np.clip(vv, 0.0, None)), LAGS, HORIZON_DAYS)
        if len(Xi):
            Xs.append(Xi); Ys.append(Yi)
    if not Xs:
        return 0.0
    t = time.perf_counter()
    fit_global_mlp(np.vstack(Xs), np.vstack(Ys))
    return (time.perf_counter() - t) * unique_wids / 60.0


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    np.random.seed(RANDOM_SEED)
    for d in (DIR_RUNTIME, DIR_CANDOUT, DIR_METRICS, DIR_LOGS):
        d.mkdir(parents=True, exist_ok=True)

    actuals = load_actuals()  # governed loader, record_type=='actual'
    actuals_by_entity = {k: g.sort_values("date").reset_index(drop=True)
                         for k, g in actuals.groupby("entity_key", sort=False)}
    windows = load_windows()  # governed walk-forward windows (454 entity-windows, 39 series)
    all_series = sorted(windows["entity_key"].unique())

    denoms = compute_training_only_denominators(windows, actuals, "v3_2d_full_backtest", _now())
    denom_idx = {(r["entity_key"], int(r["window_id"])):
                 (float(r["mase_denominator_mae"]), float(r["rmsse_denominator_mse"]))
                 for _, r in denoms.iterrows()}

    log_rows: list[dict] = []
    contract_rows: list[dict] = []
    runtime_rows: list[dict] = []
    metric_rows: list[dict] = []
    recs: list[dict] = []

    # ---------- Phase A: NLIN-DLIN remediation verification (raw negatives) ---------- #
    subset_windows = windows[windows["entity_key"].isin(SUBSET_SERIES)].copy()
    subset_windows = (subset_windows.sort_values(["entity_key", "window_id"])
                      .groupby("entity_key").tail(DRY_RUN_WINDOWS_PER_SERIES))
    nlin_before_raw_neg = 27  # recorded from V3.2C subset (level-space NLinear)
    _, _, nlin_after_raw_neg, _ = run_candidate(
        "NLIN-CHECK", "NLinear_log_space", "linear_dl", subset_windows, actuals_by_entity,
        denom_idx, fit_nlinear_fixed, [], None)
    nlin_fixed_ok = nlin_after_raw_neg == 0
    print(f"[NLIN fix] raw_neg before={nlin_before_raw_neg} after={nlin_after_raw_neg} "
          f"=> {'PASS' if nlin_fixed_ok else 'FAIL'}")

    # ---------- Phase B: GBM v2 subset re-gate ---------- #
    gbm_regate = {}
    sub_ew = len(subset_windows)
    for gid, gname, gkind in [("LGBM-IMP-v2", "LightGBM_candidate_improved_v2", "lgbm"),
                              ("XGB-IMP-v2", "XGBoost_candidate_improved_v2", "xgb")]:
        _, rt, neg, _ = run_candidate(gid, gname, "gradient_boosting", subset_windows, actuals_by_entity,
                                      denom_idx, lambda v, k=gkind: fit_gbm_v2(v, k), [], None)
        per_ew = rt / sub_ew if sub_ew else float("nan")
        proj_min = per_ew * TOTAL_GOVERNED_ENTITY_WINDOWS / 60.0
        viable = proj_min < NOT_VIABLE_PROJECTED_MINUTES
        gbm_regate[gid] = {"name": gname, "kind": gkind, "subset_runtime_s": rt,
                           "projected_full_min": proj_min, "viable": viable, "raw_neg": neg}
        runtime_rows.append({
            "candidate_id": gid, "model_name": gname, "model_family": "gradient_boosting",
            "stage": "subset_re_gate", "entity_windows": sub_ew, "runtime_seconds": round(rt, 4),
            "runtime_per_entity_window_seconds": round(per_ew, 4),
            "projected_full_runtime_minutes": round(proj_min, 3),
            "gate_decision": "VIABLE" if viable else "DEFERRED_NOT_VIABLE_FOR_V3_DAILY_REFRESH",
            "status": "ok", "failure_reason": ""})
        print(f"[GBM re-gate {gid}] runtime={rt:.2f}s proj_full={proj_min:.2f}min "
              f"=> {'VIABLE' if viable else 'DEFERRED_NOT_VIABLE'}")

    # ---------- Phase C: governed full backtest for the viable candidate set ---------- #
    full_candidates = [
        ("FNAR-V2", "FastNeuralAR_MLP_v2_direct", "lightweight_neural", "deep_learning", fit_fnar_v2),
        ("NLIN-DLIN_FIXED", "NLinear_log_space_fixed", "linear_dl", "deep_learning", fit_nlinear_fixed),
        ("SMLP-TCN", "SmallMLPGlobal", "lightweight_neural", "deep_learning", None),  # special
        ("ENET-RIDGE", "Ridge_direct_multi_horizon", "linear_ml", "machine_learning", fit_ridge_direct),
    ]
    for gid in ("LGBM-IMP-v2", "XGB-IMP-v2"):
        if gbm_regate[gid]["viable"]:
            kind = gbm_regate[gid]["kind"]
            full_candidates.append((gid, gbm_regate[gid]["name"], "gradient_boosting",
                                    "machine_learning", lambda v, k=kind: fit_gbm_v2(v, k)))

    n_windows = len(windows)
    n_series = int(windows["entity_key"].nunique())
    unique_wids = int(windows["window_id"].nunique())

    # ----- Runtime estimation (single-fit calibration -> per-candidate estimate) ----- #
    med_series = _median_series(actuals_by_entity)
    est_by_cand: dict[str, float] = {}
    for cand_id, _mn, _fam, _rg, forecaster in full_candidates:
        if cand_id in gbm_regate:  # reuse the measured re-gate per-window cost
            per_ew = gbm_regate[cand_id]["subset_runtime_s"] / max(sub_ew, 1)
            est_by_cand[cand_id] = per_ew * n_windows / 60.0
        elif cand_id == "SMLP-TCN":
            est_by_cand[cand_id] = _estimate_smlp_minutes(windows, actuals_by_entity, unique_wids)
        else:
            tcal = time.perf_counter()
            try:
                forecaster(med_series)
            except Exception:  # noqa: BLE001
                pass
            est_by_cand[cand_id] = (time.perf_counter() - tcal) * n_windows / 60.0
    est_total_min = float(sum(est_by_cand.values()))

    # ----- Mandatory time-budget block (printed + persisted) ----- #
    run_start_perf = time.perf_counter()
    run_start_wall = _now()
    global_deadline = run_start_perf + MAX_WALL_CLOCK_BUDGET_MINUTES * 60.0
    total_jobs = int(n_windows * HORIZON_DAYS * len(full_candidates))
    budget_block = {
        "start_time": run_start_wall,
        "candidates_to_run": [c[0] for c in full_candidates],
        "number_of_series": n_series,
        "number_of_windows": n_windows,
        "horizons": int(HORIZON_DAYS),
        "total_jobs": total_jobs,
        "estimated_runtime_by_candidate_min": {k: round(v, 2) for k, v in est_by_cand.items()},
        "estimated_total_runtime_min": round(est_total_min, 2),
        "max_wall_clock_budget_minutes": MAX_WALL_CLOCK_BUDGET_MINUTES,
    }
    print("\n========== V3.2D RUNTIME BUDGET ==========", flush=True)
    for bk, bv in budget_block.items():
        print(f"  {bk}: {bv}", flush=True)
    print("==========================================\n", flush=True)

    # ----- Controlled full-backtest loop (global + per-candidate budgets) ----- #
    overall_status = "COMPLETE"
    budget_events: list[tuple[str, str]] = []
    completed_candidates: list[str] = []
    incomplete_candidates: list[str] = []
    not_started_candidates: list[str] = []

    for cand_id, model_name, family, role_group, forecaster in full_candidates:
        now = time.perf_counter()
        if now >= global_deadline:
            overall_status = "TIME_BUDGET_EXCEEDED"
            not_started_candidates.append(cand_id)
            runtime_rows.append({
                "candidate_id": cand_id, "model_name": model_name, "model_family": family,
                "stage": "full_backtest", "entity_windows": 0, "runtime_seconds": 0.0,
                "runtime_per_entity_window_seconds": 0.0, "projected_full_runtime_minutes": "",
                "gate_decision": "NOT_STARTED_TIME_BUDGET_EXCEEDED", "status": "skipped",
                "failure_reason": "global wall-clock budget exhausted before candidate start"})
            print(f"[full backtest] {cand_id} SKIPPED (global budget exhausted)", flush=True)
            continue
        cand_budget_min = max(est_by_cand[cand_id] * CANDIDATE_BUDGET_SAFETY, CANDIDATE_BUDGET_MIN_MINUTES)
        cand_deadline = min(now + cand_budget_min * 60.0, global_deadline)
        print(f"[full backtest] {cand_id} starting ({n_windows} entity-windows; "
              f"est={est_by_cand[cand_id]:.1f}min budget={cand_budget_min:.1f}min)...", flush=True)
        if cand_id == "SMLP-TCN":
            pw, rt, raw_neg, stop_status = run_smlp_global(
                cand_id, model_name, family, windows, actuals_by_entity, denom_idx, all_series,
                log_rows, contract_rows, global_deadline=global_deadline,
                cand_deadline=cand_deadline, progress_label=cand_id)
        else:
            pw, rt, raw_neg, stop_status = run_candidate(
                cand_id, model_name, family, windows, actuals_by_entity, denom_idx, forecaster,
                log_rows, contract_rows, global_deadline=global_deadline,
                cand_deadline=cand_deadline, progress_label=cand_id)
        agg = aggregate(pw)
        guardrail_pass = bool(raw_neg == 0 and np.isfinite(agg["median_mase"]))
        gate_decision = "VIABLE" if stop_status == "ok" else stop_status
        runtime_rows.append({
            "candidate_id": cand_id, "model_name": model_name, "model_family": family,
            "stage": "full_backtest", "entity_windows": agg["n_windows"], "runtime_seconds": round(rt, 4),
            "runtime_per_entity_window_seconds": round(rt / max(agg["n_windows"], 1), 4),
            "projected_full_runtime_minutes": round(rt / 60.0, 3),
            "gate_decision": gate_decision, "status": "ok" if stop_status == "ok" else "partial",
            "failure_reason": "" if stop_status == "ok" else stop_status})
        metric_rows.append({
            "model_name": model_name, "candidate_id": cand_id, "role": "candidate",
            "model_family": family, "dl_or_ml": role_group,
            "median_mase": round(agg["median_mase"], 6), "mean_mase": round(agg["mean_mase"], 6),
            "p95_mase": round(agg["p95_mase"], 6), "median_rmsse": round(agg["median_rmsse"], 6),
            "mean_smape": round(agg["mean_smape"], 6), "mean_bias": round(agg["mean_bias"], 2),
            "pct_windows_beating_naive": round(agg["pct_windows_beating_naive"], 2),
            "negative_forecast_count": raw_neg, "guardrail_pass": guardrail_pass,
            "n_windows": agg["n_windows"], "runtime_seconds": round(rt, 4),
            "completion_status": stop_status})
        print(f"   {cand_id}: median_MASE={agg['median_mase']:.3f} median_RMSSE={agg['median_rmsse']:.3f} "
              f"raw_neg={raw_neg} runtime={rt:.1f}s n={agg['n_windows']} status={stop_status}", flush=True)
        if stop_status == "ok":
            completed_candidates.append(cand_id)
        else:
            incomplete_candidates.append(cand_id)
            budget_events.append((cand_id, stop_status))
        if stop_status == "TIME_BUDGET_EXCEEDED":
            overall_status = "TIME_BUDGET_EXCEEDED"
            break

    if overall_status == "COMPLETE" and budget_events:
        overall_status = "PARTIAL_CANDIDATE_TIME_BUDGET_EXCEEDED"
    total_wall_min = (time.perf_counter() - run_start_perf) / 60.0
    print(f"\n[budget result] overall_status={overall_status} wall={total_wall_min:.1f}min "
          f"completed={completed_candidates} incomplete={incomplete_candidates} "
          f"not_started={not_started_candidates}", flush=True)

    # ---------- Anchors (governed, NOT re-fit) appended for side-by-side ---------- #
    for name, fam, mase, rmsse, role in ANCHORS:
        metric_rows.append({
            "model_name": name, "candidate_id": "", "role": f"anchor_{role}",
            "model_family": fam, "dl_or_ml": "existing_governed",
            "median_mase": round(mase, 6), "mean_mase": "", "p95_mase": "",
            "median_rmsse": round(rmsse, 6), "mean_smape": "", "mean_bias": "",
            "pct_windows_beating_naive": "", "negative_forecast_count": "", "guardrail_pass": "",
            "n_windows": "", "runtime_seconds": ""})

    # ---------- Recommendations ---------- #
    cand_metrics = {m["candidate_id"]: m for m in metric_rows if m["role"] == "candidate"}

    def recommend(cid: str, m: dict) -> tuple[str, str]:
        mase = m["median_mase"]; gp = m["guardrail_pass"]
        if not gp:
            return "reject", "guardrail fail (raw negatives) - not eligible"
        if mase <= CHAMPION_MASE:
            return "candidate for governance review", f"median MASE {mase:.3f} <= champion {CHAMPION_MASE:.3f}"
        if mase <= 8.65:  # competitive with top baselines (AutoARIMA/ETS_Current band)
            return "candidate for governance review", f"median MASE {mase:.3f} competitive with top baselines"
        if mase <= 16.6:  # within mid-pack baseline band (beats current LGBM/XGB/FixedGrowth_4)
            return "keep as challenger", f"median MASE {mase:.3f} mid-pack; beats current FastNeuralAR massively"
        if mase < 739.0:
            return "keep as challenger", f"median MASE {mase:.3f}; far better than current FastNeuralAR (739.9)"
        return "reject", f"median MASE {mase:.3f} not competitive"

    for cid, m in cand_metrics.items():
        rec, reason = recommend(cid, m)
        if cid in incomplete_candidates:
            rec = "incomplete_partial_re_run_required"
            reason = f"{dict(budget_events).get(cid, 'incomplete')}; metrics from completed windows only"
        recs.append({"candidate_id": cid, "model_name": m["model_name"], "model_family": m["model_family"],
                     "dl_or_ml": m["dl_or_ml"], "median_mase": m["median_mase"],
                     "median_rmsse": m["median_rmsse"], "guardrail_pass": m["guardrail_pass"],
                     "negative_forecast_count": m["negative_forecast_count"],
                     "vs_champion_ratio": round(m["median_mase"] / CHAMPION_MASE, 3),
                     "runtime_seconds": m["runtime_seconds"], "recommendation": rec, "reason": reason})
    for gid in ("LGBM-IMP-v2", "XGB-IMP-v2"):
        if not gbm_regate[gid]["viable"]:
            recs.append({"candidate_id": gid, "model_name": gbm_regate[gid]["name"],
                         "model_family": "gradient_boosting", "dl_or_ml": "machine_learning",
                         "median_mase": "", "median_rmsse": "", "guardrail_pass": "",
                         "negative_forecast_count": gbm_regate[gid]["raw_neg"], "vs_champion_ratio": "",
                         "runtime_seconds": round(gbm_regate[gid]["subset_runtime_s"], 2),
                         "recommendation": "defer",
                         "reason": f"DEFERRED_NOT_VIABLE_FOR_V3_DAILY_REFRESH (proj "
                                   f"{gbm_regate[gid]['projected_full_min']:.1f}min even after reformulation)"})

    # ---------- Write outputs (canonical) ---------- #
    contract_df = pd.DataFrame(contract_rows).reindex(columns=CONTRACT_COLUMNS)
    runtime_df = pd.DataFrame(runtime_rows)
    metrics_df = pd.DataFrame(metric_rows)
    contract_df.to_csv(DIR_CANDOUT / "full_candidate_outputs.csv", index=False)
    runtime_df.to_csv(DIR_RUNTIME / "full_runtime_results.csv", index=False)
    metrics_df.to_csv(DIR_METRICS / "full_backtest_metrics_summary.csv", index=False)
    pd.DataFrame(log_rows).to_csv(DIR_LOGS / "full_backtest_run_log.csv", index=False)
    pd.DataFrame(recs).to_csv(OUT_ROOT / "candidate_recommendations.csv", index=False)

    # Persist a machine-readable summary for the report writer (includes runtime control state).
    summary = {"nlin_before_raw_neg": nlin_before_raw_neg, "nlin_after_raw_neg": int(nlin_after_raw_neg),
               "nlin_fixed_ok": nlin_fixed_ok, "gbm_regate": gbm_regate,
               "champion_mase": CHAMPION_MASE, "n_windows": int(len(windows)),
               "overall_status": overall_status, "total_wall_minutes": round(total_wall_min, 3),
               "budget_block": budget_block, "completed_candidates": completed_candidates,
               "incomplete_candidates": incomplete_candidates,
               "not_started_candidates": not_started_candidates,
               "budget_events": [{"candidate_id": c, "event": e} for c, e in budget_events]}
    with open(OUT_ROOT / "_v3_2d_run_summary.json", "w", encoding="utf-8") as fh:
        import json as _json
        _json.dump(summary, fh, indent=2, default=str)

    # ---------- Partial outputs (only when stopped by a time budget) ---------- #
    if overall_status != "COMPLETE":
        contract_df.to_csv(DIR_CANDOUT / "partial_candidate_outputs.csv", index=False)
        metrics_df.to_csv(DIR_METRICS / "partial_metrics_summary.csv", index=False)
        runtime_df.to_csv(DIR_RUNTIME / "partial_runtime_results.csv", index=False)
        lines = []
        lines.append("# V3.2D PARTIAL REPORT (time-budget stop)")
        lines.append("")
        lines.append(f"- generated: {_now()}")
        lines.append(f"- overall_status: {overall_status}")
        lines.append(f"- wall_clock_minutes: {total_wall_min:.2f} (budget {MAX_WALL_CLOCK_BUDGET_MINUTES})")
        lines.append("")
        lines.append("## Candidates that completed")
        lines.append("")
        if completed_candidates:
            for c in completed_candidates:
                lines.append(f"- {c}")
        else:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Candidates incomplete (partial metrics from completed windows only)")
        lines.append("")
        if incomplete_candidates:
            for c in incomplete_candidates:
                lines.append(f"- {c}: {dict(budget_events).get(c, 'incomplete')}")
        else:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Candidates not started (global budget exhausted)")
        lines.append("")
        if not_started_candidates:
            for c in not_started_candidates:
                lines.append(f"- {c}")
        else:
            lines.append("- (none)")
        lines.append("")
        lines.append("## Why it stopped")
        lines.append("")
        if overall_status == "TIME_BUDGET_EXCEEDED":
            lines.append(f"- Global wall-clock budget of {MAX_WALL_CLOCK_BUDGET_MINUTES} min was reached; "
                         "the run was halted safely and partial outputs were written.")
        else:
            lines.append("- One or more candidates exceeded their per-candidate budget "
                         "(CANDIDATE_TIME_BUDGET_EXCEEDED). The run continued safely with the remaining "
                         "candidates; affected candidates carry partial metrics only.")
        lines.append("")
        lines.append("## Resumability")
        lines.append("")
        lines.append("- Resumable: YES (stateless harness). Re-running V3.2D recomputes from the governed "
                     "inputs. To finish within budget, raise MAX_WALL_CLOCK_BUDGET_MINUTES or run the "
                     "incomplete/not-started candidates in isolation.")
        lines.append("")
        lines.append("## Governance (partial run)")
        lines.append("")
        lines.append("- No champion changed. No forecasts changed. No intervals changed. "
                     "No data/processed changed. No governance decisions changed. No production promotion.")
        (OUT_ROOT / "v3_2d_partial_report.md").write_text("\n".join(lines), encoding="utf-8")
        print(f"\nV3.2D {overall_status}. Partial outputs written -> {OUT_ROOT}", flush=True)
    else:
        print(f"\nV3.2D COMPLETE. contract_rows={len(contract_rows)} wall={total_wall_min:.1f}min "
              f"-> {OUT_ROOT}", flush=True)



if __name__ == "__main__":
    main()
