"""V3.2C - Model Candidate Experimental Harness (SUBSET DRY-RUN + RUNTIME GATE).

ISOLATED, READ-ONLY-INPUT, EXPERIMENTAL.

Scope (authorized V3.2C):
  - Implement the isolated candidate harness and run ONLY the deterministic
    5-series subset dry-run with a runtime gate.
  - DO NOT run the full 39-series backtest (separate, later authorization).

Strict governance honored by this script:
  - V3 only. V1/V2 never touched.
  - Champion NOT changed. Forecasts/intervals/governance NOT changed.
  - Inputs read READ-ONLY from governed artifacts:
        outputs/model_lab/challenger_official_execution_prep/official_execution_scope.csv
        outputs/evaluation/evaluation_dataset.csv  (record_type == 'actual')
    (same sources the governed official execution recovery script uses).
  - ALL outputs written ONLY under outputs/v3_2b_model_candidates/.
  - data/processed/ is NEVER written. No model is promoted.

Candidates executed in the subset dry-run (6):
  FNAR-V2     FastNeuralAR_MLP_v2_direct              (direct multi-horizon, log1p, clamp, L2, early-stop)
  NLIN-DLIN   NLinear_or_DLinear_lightweight          (NLinear last-value normalization linear layer, CPU)
  SMLP-TCN    SmallTCN_or_SmallMLPGlobal              (SmallMLPGlobal global pooled tiny net, epoch-capped)
  LGBM-IMP    LightGBM_candidate_improved             (direct multi-horizon, per-horizon boosters)
  XGB-IMP     XGBoost_candidate_improved              (direct multi-horizon, per-horizon boosters)
  ENET-RIDGE  ElasticNet_or_Ridge_direct_multi_horizon(Ridge multi-output direct, fastest)

All point forecasts are clamped to >= 0 (non-negativity guardrail). Raw negative
counts (before clamp) are recorded. Direct multi-horizon design (no recursion) is
the structural fix for the diagnosed recursive-collapse of the current FastNeuralAR_MLP.
"""

from __future__ import annotations

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

# --------------------------------------------------------------------------- #
# Paths (computed from this file: .../V3/python/model_lab/<this>.py -> V3)
# --------------------------------------------------------------------------- #
PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCOPE_PATH = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "challenger_official_execution_prep"
    / "official_execution_scope.csv"
)
EVAL_PATH = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"

OUT_ROOT = PROJECT_ROOT / "outputs" / "v3_2b_model_candidates"
DIR_RUNTIME = OUT_ROOT / "runtime_checks"
DIR_CANDOUT = OUT_ROOT / "candidate_outputs"
DIR_METRICS = OUT_ROOT / "metrics"
DIR_LOGS = OUT_ROOT / "logs"

# --------------------------------------------------------------------------- #
# Constants / gate
# --------------------------------------------------------------------------- #
RANDOM_SEED = 42
HORIZON_DAYS = 30
LAGS = 30
SEASONAL_M = 7  # weekly seasonality for MASE/RMSSE in-sample scale
DRY_RUN_WINDOWS_PER_SERIES = 3  # last N windows used for the runtime gate
TOTAL_GOVERNED_ENTITY_WINDOWS = 454  # full-scale projection denominator (39 series)
RUNTIME_GATE_MINUTES = 30.0
NOT_VIABLE_PROJECTED_MINUTES = 25.0  # "approaching ~30 min" => NOT_VIABLE_FOR_V3_DAILY_REFRESH

# Deterministic 5-series subset: high-scale multitenant (where FastNeuralAR_MLP
# collapsed) + dedicated/well-behaved anchors. All have 12 windows.
SUBSET_SERIES = [
    "NAM-Multitenant",
    "EUR-Multitenant",
    "LAM-Multitenant",
    "APC-Dedicated",
    "NAM-TDF",
]

CANDIDATES = [
    ("FNAR-V2", "FastNeuralAR_MLP_v2_direct", "lightweight_neural"),
    ("NLIN-DLIN", "NLinear_or_DLinear_lightweight", "linear_dl"),
    ("SMLP-TCN", "SmallTCN_or_SmallMLPGlobal", "lightweight_neural"),
    ("LGBM-IMP", "LightGBM_candidate_improved", "gradient_boosting"),
    ("XGB-IMP", "XGBoost_candidate_improved", "gradient_boosting"),
    ("ENET-RIDGE", "ElasticNet_or_Ridge_direct_multi_horizon", "linear_ml"),
]

CONTRACT_COLUMNS = [
    "candidate_id", "model_name", "model_family", "series_key", "forecast_origin",
    "horizon", "forecast_date", "forecast_value", "actual_value", "error",
    "abs_error", "squared_error", "mase", "rmsse", "smape_or_mae_if_available",
    "runtime_seconds", "status", "failure_reason", "guardrail_pass",
    "negative_forecast_count", "notes",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


# --------------------------------------------------------------------------- #
# Data loading (READ-ONLY)
# --------------------------------------------------------------------------- #
def load_scope() -> pd.DataFrame:
    scope = pd.read_csv(SCOPE_PATH)
    sel = scope[
        scope["selected_for_official_execution"].astype(str).str.lower().isin(
            {"true", "1", "yes"}
        )
    ].copy()
    for col in ["train_start_date", "train_end_date", "test_start_date", "test_end_date"]:
        sel[col] = pd.to_datetime(sel[col], errors="raise")
    sel["window_id"] = pd.to_numeric(sel["window_id"], errors="raise").astype(int)
    return sel.sort_values(["entity_key", "window_id"]).reset_index(drop=True)


def load_actuals() -> pd.DataFrame:
    act = pd.read_csv(EVAL_PATH)
    if "record_type" in act.columns:
        act = act[act["record_type"].astype(str).str.lower() == "actual"].copy()
    act["date"] = pd.to_datetime(act["date"], errors="coerce")
    act["value"] = pd.to_numeric(act["value"], errors="coerce")
    act = act.dropna(subset=["entity_key", "date", "value"]).copy()
    return act.sort_values(["entity_key", "date"]).reset_index(drop=True)


def series_until(actuals: pd.DataFrame, entity: str, train_end: pd.Timestamp) -> np.ndarray:
    s = actuals[(actuals["entity_key"] == entity) & (actuals["date"] <= train_end)]
    return s.sort_values("date")["value"].to_numpy(dtype=float)


def test_actuals(
    actuals: pd.DataFrame, entity: str, test_start: pd.Timestamp, test_end: pd.Timestamp
) -> tuple[np.ndarray, np.ndarray]:
    s = actuals[
        (actuals["entity_key"] == entity)
        & (actuals["date"] >= test_start)
        & (actuals["date"] <= test_end)
    ].sort_values("date")
    return s["date"].to_numpy(), s["value"].to_numpy(dtype=float)


# --------------------------------------------------------------------------- #
# Feature builders (direct multi-horizon, NO recursion)
# --------------------------------------------------------------------------- #
def build_xy(values: np.ndarray, lags: int, horizon: int) -> tuple[np.ndarray, np.ndarray]:
    """X = last `lags` values (most-recent-first); Y = next `horizon` values."""
    rows_x, rows_y = [], []
    n = len(values)
    for idx in range(lags, n - horizon + 1):
        rows_x.append(values[idx - lags:idx][::-1])
        rows_y.append(values[idx:idx + horizon])
    if not rows_x:
        return np.empty((0, lags)), np.empty((0, horizon))
    return np.asarray(rows_x, dtype=float), np.asarray(rows_y, dtype=float)


def last_window_feats(values: np.ndarray, lags: int) -> np.ndarray:
    return np.asarray(values[-lags:][::-1], dtype=float).reshape(1, -1)


# --------------------------------------------------------------------------- #
# Candidate fit/predict (return clamped 30-vector + raw negative count)
# --------------------------------------------------------------------------- #
def _clamp(arr: np.ndarray) -> tuple[np.ndarray, int]:
    raw_neg = int((arr < 0).sum())
    return np.clip(arr, 0.0, None), raw_neg


def fit_fnar_v2(values: np.ndarray) -> tuple[np.ndarray, int]:
    v = np.clip(values, 0.0, None)
    t = np.log1p(v)
    X, Y = build_xy(t, LAGS, HORIZON_DAYS)
    if len(X) < 5:
        raise ValueError(f"insufficient training rows ({len(X)})")
    mlp = MLPRegressor(
        hidden_layer_sizes=(32,), activation="relu", solver="adam",
        alpha=1e-3, max_iter=300, early_stopping=len(X) >= 20,
        validation_fraction=0.1, random_state=RANDOM_SEED,
    )
    model = Pipeline([("scale", StandardScaler()), ("mlp", mlp)])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(X, Y)
    feats = np.log1p(np.clip(last_window_feats(values, LAGS), 0.0, None))
    pred = np.expm1(np.asarray(model.predict(feats)).ravel())
    return _clamp(pred)


def fit_nlinear(values: np.ndarray) -> tuple[np.ndarray, int]:
    X, Y = build_xy(values, LAGS, HORIZON_DAYS)
    if len(X) < 5:
        raise ValueError(f"insufficient training rows ({len(X)})")
    last = X[:, 0].reshape(-1, 1)  # most-recent observed value per row
    Xn, Yn = X - last, Y - last
    model = Ridge(alpha=1.0, random_state=RANDOM_SEED)
    model.fit(Xn, Yn)
    feats = last_window_feats(values, LAGS)
    f_last = feats[0, 0]
    pred = np.asarray(model.predict(feats - f_last)).ravel() + f_last
    return _clamp(pred)


def fit_ridge_direct(values: np.ndarray) -> tuple[np.ndarray, int]:
    v = np.clip(values, 0.0, None)
    t = np.log1p(v)
    X, Y = build_xy(t, LAGS, HORIZON_DAYS)
    if len(X) < 5:
        raise ValueError(f"insufficient training rows ({len(X)})")
    model = Pipeline([("scale", StandardScaler()), ("ridge", Ridge(alpha=1.0, random_state=RANDOM_SEED))])
    model.fit(X, Y)
    feats = np.log1p(np.clip(last_window_feats(values, LAGS), 0.0, None))
    pred = np.expm1(np.asarray(model.predict(feats)).ravel())
    return _clamp(pred)


def fit_gbm_direct(values: np.ndarray, kind: str) -> tuple[np.ndarray, int]:
    """Per-horizon direct multi-horizon gradient boosting (LightGBM / XGBoost)."""
    v = np.clip(values, 0.0, None)
    t = np.log1p(v)
    X, Y = build_xy(t, LAGS, HORIZON_DAYS)
    if len(X) < 10:
        raise ValueError(f"insufficient training rows ({len(X)})")
    feats = np.log1p(np.clip(last_window_feats(values, LAGS), 0.0, None))
    preds_t = np.empty(HORIZON_DAYS, dtype=float)
    if kind == "lgbm":
        from lightgbm import LGBMRegressor

        def make():
            return LGBMRegressor(
                n_estimators=200, num_leaves=31, learning_rate=0.05,
                subsample=0.9, colsample_bytree=0.9, random_state=RANDOM_SEED,
                n_jobs=-1, verbose=-1,
            )
    else:
        from xgboost import XGBRegressor

        def make():
            return XGBRegressor(
                n_estimators=200, max_depth=6, learning_rate=0.05,
                subsample=0.9, colsample_bytree=0.9, tree_method="hist",
                random_state=RANDOM_SEED, n_jobs=-1, verbosity=0,
            )

    for h in range(HORIZON_DAYS):
        m = make()
        m.fit(X, Y[:, h])
        preds_t[h] = float(np.asarray(m.predict(feats)).ravel()[0])
    pred = np.expm1(preds_t)
    return _clamp(pred)


# --- SmallMLPGlobal: pooled global tiny net, fit ONCE per window across series --- #
def fit_global_mlp(pooled_X: np.ndarray, pooled_Y: np.ndarray) -> Pipeline:
    mlp = MLPRegressor(
        hidden_layer_sizes=(16,), activation="relu", solver="adam",
        alpha=1e-3, max_iter=150, early_stopping=len(pooled_X) >= 20,
        validation_fraction=0.1, random_state=RANDOM_SEED,
    )
    model = Pipeline([("scale", StandardScaler()), ("mlp", mlp)])
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(pooled_X, pooled_Y)
    return model


def predict_global_mlp(model: Pipeline, values: np.ndarray) -> tuple[np.ndarray, int]:
    feats = np.log1p(np.clip(last_window_feats(values, LAGS), 0.0, None))
    pred = np.expm1(np.asarray(model.predict(feats)).ravel())
    return _clamp(pred)


# --------------------------------------------------------------------------- #
# Metrics (per series/window): seasonal-naive (m=7) in-sample scale
# --------------------------------------------------------------------------- #
def in_sample_scales(train_values: np.ndarray) -> tuple[float, float]:
    if len(train_values) <= SEASONAL_M:
        d = np.diff(train_values)
    else:
        d = train_values[SEASONAL_M:] - train_values[:-SEASONAL_M]
    d = d[np.isfinite(d)]
    mae = float(np.mean(np.abs(d))) if d.size else float("nan")
    rmse = float(np.sqrt(np.mean(d ** 2))) if d.size else float("nan")
    return mae, rmse


def window_metrics(
    fc: np.ndarray, act: np.ndarray, mae_scale: float, rmse_scale: float
) -> dict:
    h = min(len(fc), len(act))
    f, a = fc[:h], act[:h]
    err = f - a
    abs_e = np.abs(err)
    sq_e = err ** 2
    mase = float(np.mean(abs_e) / mae_scale) if mae_scale and np.isfinite(mae_scale) and mae_scale > 0 else float("nan")
    rmsse = float(np.sqrt(np.mean(sq_e)) / rmse_scale) if rmse_scale and np.isfinite(rmse_scale) and rmse_scale > 0 else float("nan")
    denom = np.abs(f) + np.abs(a)
    smape = float(np.mean(np.where(denom > 0, 2.0 * abs_e / denom, 0.0)))
    return {"mase": mase, "rmsse": rmsse, "smape": smape, "bias": float(np.mean(err)), "h_eval": h}


# --------------------------------------------------------------------------- #
# Main
# --------------------------------------------------------------------------- #
def main() -> None:
    np.random.seed(RANDOM_SEED)
    for d in (DIR_RUNTIME, DIR_CANDOUT, DIR_METRICS, DIR_LOGS):
        d.mkdir(parents=True, exist_ok=True)

    scope = load_scope()
    actuals = load_actuals()

    # Build the deterministic dry-run window set: last N windows per subset series.
    dry_windows: list[pd.Series] = []
    for entity in SUBSET_SERIES:
        ent = scope[scope["entity_key"] == entity].sort_values("window_id")
        ent = ent.tail(DRY_RUN_WINDOWS_PER_SERIES)
        for _, row in ent.iterrows():
            dry_windows.append(row)
    subset_entity_windows = len(dry_windows)

    contract_rows: list[dict] = []
    metric_rows: list[dict] = []
    runtime_rows: list[dict] = []
    log_rows: list[dict] = []

    dep_status = {
        "FNAR-V2": "available_sklearn_1.9.0",
        "NLIN-DLIN": "available_sklearn_1.9.0_numpy_2.4.6",
        "SMLP-TCN": "available_sklearn_1.9.0",
        "LGBM-IMP": "available_lightgbm_4.6.0",
        "XGB-IMP": "available_xgboost_3.2.0",
        "ENET-RIDGE": "available_sklearn_1.9.0",
    }

    for cand_id, model_name, family in CANDIDATES:
        cand_runtime = 0.0
        cand_neg = 0
        cand_status = "ok"
        cand_fail = ""
        per_window_metrics: list[dict] = []

        # Group dry windows by window_id for the global model's per-window fit.
        for row in dry_windows:
            entity = str(row["entity_key"])
            window_id = int(row["window_id"])
            train_end = pd.to_datetime(row["train_end_date"])
            test_start = pd.to_datetime(row["test_start_date"])
            test_end = pd.to_datetime(row["test_end_date"])
            origin = train_end.date().isoformat()

            train_vals = series_until(actuals, entity, train_end)
            _, act_vals = test_actuals(actuals, entity, test_start, test_end)

            row_status = "ok"
            row_fail = ""
            t0 = time.perf_counter()
            try:
                if len(train_vals) < LAGS + HORIZON_DAYS + 5:
                    raise ValueError(f"history too short ({len(train_vals)} rows)")
                if cand_id == "FNAR-V2":
                    fc, raw_neg = fit_fnar_v2(train_vals)
                elif cand_id == "NLIN-DLIN":
                    fc, raw_neg = fit_nlinear(train_vals)
                elif cand_id == "ENET-RIDGE":
                    fc, raw_neg = fit_ridge_direct(train_vals)
                elif cand_id == "LGBM-IMP":
                    fc, raw_neg = fit_gbm_direct(train_vals, "lgbm")
                elif cand_id == "XGB-IMP":
                    fc, raw_neg = fit_gbm_direct(train_vals, "xgb")
                elif cand_id == "SMLP-TCN":
                    # Global: pool ALL subset series for this window_id, fit once, cache.
                    fc, raw_neg = _smlp_global(actuals, scope, window_id, entity, train_vals)
                else:
                    raise ValueError(f"unknown candidate {cand_id}")
            except Exception as exc:  # noqa: BLE001 - record, never crash the run
                dt = time.perf_counter() - t0
                cand_runtime += dt
                row_status, row_fail = "failed", f"fit_error: {type(exc).__name__}: {exc}"[:240]
                cand_status, cand_fail = "failed", row_fail
                log_rows.append({
                    "timestamp": _now(), "candidate_id": cand_id, "model_name": model_name,
                    "series_key": entity, "window_id": window_id, "forecast_origin": origin,
                    "status": row_status, "runtime_seconds": round(dt, 4), "message": row_fail,
                })
                continue
            dt = time.perf_counter() - t0
            cand_runtime += dt
            cand_neg += raw_neg

            mae_s, rmse_s = in_sample_scales(train_vals)
            m = window_metrics(fc, act_vals, mae_s, rmse_s)
            per_window_metrics.append(m)

            for hh in range(HORIZON_DAYS):
                fdate = (test_start + pd.Timedelta(days=hh)).date().isoformat()
                a = float(act_vals[hh]) if hh < len(act_vals) else np.nan
                fval = float(fc[hh])
                err = (fval - a) if np.isfinite(a) else np.nan
                contract_rows.append({
                    "candidate_id": cand_id, "model_name": model_name, "model_family": family,
                    "series_key": entity, "forecast_origin": origin, "horizon": hh + 1,
                    "forecast_date": fdate, "forecast_value": round(fval, 6),
                    "actual_value": (round(a, 6) if np.isfinite(a) else ""),
                    "error": (round(err, 6) if np.isfinite(err) else ""),
                    "abs_error": (round(abs(err), 6) if np.isfinite(err) else ""),
                    "squared_error": (round(err ** 2, 6) if np.isfinite(err) else ""),
                    "mase": (round(m["mase"], 6) if np.isfinite(m["mase"]) else ""),
                    "rmsse": (round(m["rmsse"], 6) if np.isfinite(m["rmsse"]) else ""),
                    "smape_or_mae_if_available": round(m["smape"], 6),
                    "runtime_seconds": round(dt, 4), "status": "ok", "failure_reason": "",
                    "guardrail_pass": "", "negative_forecast_count": raw_neg,
                    "notes": "direct_multi_horizon;log1p" if cand_id != "NLIN-DLIN" else "nlinear_lastval_norm",
                })

            log_rows.append({
                "timestamp": _now(), "candidate_id": cand_id, "model_name": model_name,
                "series_key": entity, "window_id": window_id, "forecast_origin": origin,
                "status": "ok", "runtime_seconds": round(dt, 4),
                "message": f"mase={m['mase']:.3f} rmsse={m['rmsse']:.3f} raw_neg={raw_neg} h_eval={m['h_eval']}",
            })

        # ---- candidate aggregate metrics ----
        valid = [m for m in per_window_metrics if np.isfinite(m["mase"])]
        med_mase = float(np.median([m["mase"] for m in valid])) if valid else float("nan")
        med_rmsse = float(np.median([m["rmsse"] for m in valid])) if valid else float("nan")
        mean_smape = float(np.mean([m["smape"] for m in valid])) if valid else float("nan")
        mean_bias = float(np.mean([m["bias"] for m in valid])) if valid else float("nan")

        rt_per_ew = cand_runtime / subset_entity_windows if subset_entity_windows else float("nan")
        projected_full_s = rt_per_ew * TOTAL_GOVERNED_ENTITY_WINDOWS
        projected_full_m = projected_full_s / 60.0
        if cand_status == "failed":
            gate = "FAILED"
        elif projected_full_m >= NOT_VIABLE_PROJECTED_MINUTES:
            gate = "NOT_VIABLE_FOR_V3_DAILY_REFRESH"
        else:
            gate = "VIABLE"
        guardrail_pass = bool(cand_neg == 0 and cand_status == "ok" and np.isfinite(med_mase))

        runtime_rows.append({
            "candidate_id": cand_id, "model_name": model_name, "model_family": family,
            "dependency_status": dep_status[cand_id],
            "subset_entity_windows": subset_entity_windows,
            "subset_runtime_seconds": round(cand_runtime, 4),
            "runtime_per_entity_window_seconds": round(rt_per_ew, 4),
            "total_governed_entity_windows": TOTAL_GOVERNED_ENTITY_WINDOWS,
            "projected_full_runtime_seconds": round(projected_full_s, 2),
            "projected_full_runtime_minutes": round(projected_full_m, 3),
            "runtime_gate_threshold_minutes": RUNTIME_GATE_MINUTES,
            "not_viable_threshold_minutes": NOT_VIABLE_PROJECTED_MINUTES,
            "gate_decision": gate,
            "status": cand_status,
            "failure_reason": cand_fail,
        })
        metric_rows.append({
            "candidate_id": cand_id, "model_name": model_name, "model_family": family,
            "subset_entity_windows": subset_entity_windows,
            "median_mase": (round(med_mase, 6) if np.isfinite(med_mase) else ""),
            "median_rmsse": (round(med_rmsse, 6) if np.isfinite(med_rmsse) else ""),
            "mean_smape": (round(mean_smape, 6) if np.isfinite(mean_smape) else ""),
            "mean_bias": (round(mean_bias, 6) if np.isfinite(mean_bias) else ""),
            "negative_forecast_count": cand_neg,
            "subset_runtime_seconds": round(cand_runtime, 4),
            "projected_full_runtime_minutes": round(projected_full_m, 3),
            "gate_decision": gate,
            "guardrail_pass": guardrail_pass,
            "status": cand_status,
            "failure_reason": cand_fail,
        })
        print(f"[{cand_id:11}] runtime={cand_runtime:7.2f}s proj_full={projected_full_m:6.2f}min "
              f"med_MASE={med_mase if np.isfinite(med_mase) else float('nan'):.3f} "
              f"neg={cand_neg} gate={gate} status={cand_status}")

    # --------------------------------------------------------------------- #
    # Write outputs (ONLY under outputs/v3_2b_model_candidates/)
    # --------------------------------------------------------------------- #
    pd.DataFrame(contract_rows).reindex(columns=CONTRACT_COLUMNS).to_csv(
        DIR_CANDOUT / "subset_candidate_outputs.csv", index=False)
    pd.DataFrame(runtime_rows).to_csv(DIR_RUNTIME / "subset_runtime_results.csv", index=False)
    pd.DataFrame(metric_rows).to_csv(DIR_METRICS / "subset_metrics_summary.csv", index=False)
    pd.DataFrame(log_rows).to_csv(DIR_LOGS / "subset_run_log.csv", index=False)

    total_runtime = sum(r["subset_runtime_seconds"] for r in runtime_rows)
    print(f"\nSUBSET DRY-RUN COMPLETE  total_runtime={total_runtime:.2f}s  "
          f"entity_windows={subset_entity_windows}  candidates={len(CANDIDATES)}")
    print(f"Outputs -> {OUT_ROOT}")


# Cache for the global SmallMLP per window_id (fit once, reused across series).
_GLOBAL_MLP_CACHE: dict[int, Pipeline] = {}


def _smlp_global(
    actuals: pd.DataFrame, scope: pd.DataFrame, window_id: int, entity: str, train_vals: np.ndarray
) -> tuple[np.ndarray, int]:
    """SmallMLPGlobal: pool ALL subset series at this window_id, fit once, predict series."""
    if window_id not in _GLOBAL_MLP_CACHE:
        Xs, Ys = [], []
        for ent in SUBSET_SERIES:
            wr = scope[(scope["entity_key"] == ent) & (scope["window_id"] == window_id)]
            if wr.empty:
                continue
            te = pd.to_datetime(wr.iloc[0]["train_end_date"])
            vv = np.clip(series_until(actuals, ent, te), 0.0, None)
            if len(vv) < LAGS + HORIZON_DAYS + 5:
                continue
            tt = np.log1p(vv)
            Xi, Yi = build_xy(tt, LAGS, HORIZON_DAYS)
            if len(Xi):
                Xs.append(Xi)
                Ys.append(Yi)
        if not Xs:
            raise ValueError("no pooled training data for global MLP")
        _GLOBAL_MLP_CACHE[window_id] = fit_global_mlp(np.vstack(Xs), np.vstack(Ys))
    return predict_global_mlp(_GLOBAL_MLP_CACHE[window_id], train_vals)


if __name__ == "__main__":
    main()
