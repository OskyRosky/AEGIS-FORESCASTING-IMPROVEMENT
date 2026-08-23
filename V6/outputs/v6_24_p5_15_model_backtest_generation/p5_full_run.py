"""V6.24-P5 | Full 15-model backtest generation for the 90 non-HDD MVP series.

Generates HISTORICAL BACKTEST estimates only. No forward forecasts, no accuracy,
no rankings. Those belong to P6/P7.

Model fitting replicates run_v6_17_viewer_backtests.py exactly. Origin selection
and target emission follow the owner-approved D2 Option B policy: a model still
forecasts 30 steps from each origin, but a row is emitted ONLY when that target
date exists in actuals_normalized. Nothing is filled, resampled or interpolated.

Phase A (12 non-neural models, 10-series batches) runs first and checkpoints, so
a neural failure in Phase B cannot destroy cheap completed work.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import time
import traceback
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.compose import TransformedTargetRegressor
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

warnings.filterwarnings("ignore")

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work"
PILOT_PATH = V6 / "outputs" / "v6_16_five_case_viewer_uiux_lab" / "build_v6_16_pilot_backtest.py"

for sub in ("checkpoints", "logs", "failures", "temp_outputs", "runtime_ledger"):
    (WORK / sub).mkdir(parents=True, exist_ok=True)

LAGS, HORIZON = 30, 30
BURN_IN_DAYS, MIN_TRAIN_ROWS, MIN_TARGETS, ORIGIN_COUNT = 64, 65, 20, 11
RANDOM_SEED = 42
HARD_SEC, SOFT_SEC = 120 * 60, 105 * 60
EXPECTED_MS = 1350

NON_NEURAL = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
              "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
              "LightGBM", "LinearRegression", "XGBoost"]
NEURAL_M = ["FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]

spec = importlib.util.spec_from_file_location("v6_16_pilot", PILOT_PATH)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)
BASELINE, CHALLENGER = pilot.BASELINE_CLASSES, pilot.CHALLENGER_FORECASTERS
FAMILY = {**{m: "Baseline" for m in BASELINE}, **{m: "Challenger" for m in CHALLENGER},
          **{m: "Neural" for m in NEURAL_M}}

T0 = time.time()
RUN_ID = f"P5_FULL_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
progress_log, batch_ledger, exec_ledger, failures = [], [], [], []
done_ms, done_rows = 0, 0
next_milestone = 10


def el_min():
    return (time.time() - T0) / 60


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def progress(pct, metric, model, batch, ckpt):
    e = el_min()
    eta = (e / done_ms * (EXPECTED_MS - done_ms)) if done_ms else 0.0
    progress_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "percent_complete": pct, "elapsed_minutes": round(e, 2),
        "estimated_remaining_minutes": round(eta, 2),
        "completed_model_series": done_ms, "total_model_series": EXPECTED_MS,
        "completed_prediction_rows": done_rows, "current_metric": metric,
        "current_model": model, "current_batch": batch,
        "failures_so_far": len(failures), "latest_checkpoint_path": ckpt})
    print(f"[PROGRESS] P5 {pct}% | elapsed={e:.1f}m | eta={eta:.1f}m | metric={metric} | "
          f"batch={batch} | model_series={done_ms}/{EXPECTED_MS} | rows={done_rows} | "
          f"failures={len(failures)}", flush=True)


# ------------------------------------------------- model fitting, verbatim
def fit_scaled_mlp(x, y, hidden, iters, act):
    reg = Pipeline([("scale", StandardScaler()),
                    ("mlp", MLPRegressor(hidden_layer_sizes=hidden, activation=act,
                                         solver="adam", alpha=1e-3, max_iter=iters,
                                         early_stopping=len(x) >= 20, validation_fraction=0.1,
                                         random_state=RANDOM_SEED))])
    m = TransformedTargetRegressor(regressor=reg, transformer=StandardScaler())
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        m.fit(x, y)
    return m


def fit_fnar_v2_scaled(values):
    t = np.log1p(np.clip(values, 0.0, None))
    x, y = pilot.build_xy(t, LAGS, HORIZON)
    if len(x) < 5:
        raise ValueError(f"insufficient FNAR-V2 training rows ({len(x)})")
    m = fit_scaled_mlp(x, y, (32,), 300, "tanh")
    f = np.log1p(np.clip(values[-LAGS:][::-1].reshape(1, -1), 0.0, None))
    return np.clip(np.expm1(np.asarray(m.predict(f)).ravel()), 0.0, None)


def predict_smlp_scaled(model, values):
    f = np.log1p(np.clip(values[-LAGS:][::-1].reshape(1, -1), 0.0, None))
    return np.clip(np.expm1(np.asarray(model.predict(f)).ravel()), 0.0, None)


def fit_predictions(name, training, gm):
    v = training["value"].to_numpy(dtype=float)
    if name in BASELINE:
        p = pilot._fit_baseline(name, training)
    elif name in CHALLENGER:
        p = np.asarray(CHALLENGER[name](v), dtype=float)
    elif name == "FNAR-V2":
        p = fit_fnar_v2_scaled(v)
    elif name == "SMLP-TCN":
        if gm is None:
            raise ValueError("SMLP-TCN global model is missing")
        p = predict_smlp_scaled(gm, v)
    elif name == "NLIN-DLIN_FIXED":
        p = pilot._fit_neural(name, v, gm)
    else:
        raise ValueError(f"Unexpected model {name}")
    p = np.asarray(p, dtype=float)
    if len(p) != HORIZON or not np.isfinite(p).all():
        raise ValueError(f"{name} produced invalid {len(p)}-row predictions")
    return p


# ------------------------------------------------- inputs and preparation
log("P5 FULL RUN START")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
TARGETS = MAN[MAN["metric"] != "HDD"].copy()
log(f"cohort: {len(MAN)} series | P5 workload: {len(TARGETS)} non-HDD series")


def d2_origins(g):
    dmin, dmax = g["series_date"].min(), g["series_date"].max()
    earliest = dmin + pd.Timedelta(days=BURN_IN_DAYS)
    latest = dmax - pd.Timedelta(days=HORIZON)
    if latest < earliest:
        return [], 0
    span = int((latest - earliest).days)
    offs = sorted({int(round(span * i / (ORIGIN_COUNT - 1))) for i in range(ORIGIN_COUNT)})
    origins = [earliest + pd.Timedelta(days=o) for o in offs]
    if latest not in origins:
        origins.append(latest)
    burn = int((g["series_date"] < earliest).sum())
    valid = [o for o in sorted(set(origins))
             if int((g["series_date"] <= o).sum()) >= MIN_TRAIN_ROWS
             and len(g["series_date"][(g["series_date"] > o)
                                      & (g["series_date"] <= o + pd.Timedelta(days=HORIZON))])
             >= MIN_TARGETS]
    return valid, burn


prep = {}
for _, m in TARGETS.iterrows():
    g = ACT[ACT["series_id"] == m["series_id"]].sort_values("series_date")
    origins, burn = d2_origins(g)
    prep[m["series_id"]] = {
        "series": g[["series_date", "actual_value"]].rename(
            columns={"series_date": "date", "actual_value": "value"}).reset_index(drop=True),
        "origins": origins, "burn_in": burn, "obs": set(g["series_date"]),
        "amap": dict(zip(g["series_date"], g["actual_value"])), "man": m}
log(f"prepared {len(prep)} series | total valid origins "
    f"{sum(len(p['origins']) for p in prep.values())}")

log("building SMLP-TCN pooled global models across all 90 series...")
GLOBALS = {}
mx = max(len(p["origins"]) for p in prep.values())
for i in range(mx):
    px, py = [], []
    for p in prep.values():
        if i >= len(p["origins"]):
            continue
        tr = p["series"][p["series"]["date"] <= p["origins"][i]]
        v = np.log1p(np.clip(tr["value"].to_numpy(dtype=float), 0.0, None))
        x, y = pilot.build_xy(v, LAGS, HORIZON)
        if len(x) >= 5:
            px.append(x)
            py.append(y)
    GLOBALS[i] = fit_scaled_mlp(np.vstack(px), np.vstack(py), (16,), 150, "relu") if px else None
log(f"{len([v for v in GLOBALS.values() if v])} pooled models built ({el_min():.1f}m)")


def run_unit(sid, name):
    """Run one (series, model) unit across all its valid origins."""
    p = prep[sid]
    m = p["man"]
    rows, t0 = [], time.time()
    for oi, origin in enumerate(p["origins"]):
        tr = p["series"][p["series"]["date"] <= origin]
        gm = GLOBALS.get(oi) if name == "SMLP-TCN" else None
        pred = fit_predictions(name, tr, gm)
        for step in range(1, HORIZON + 1):
            td = origin + pd.Timedelta(days=step)
            if td not in p["obs"]:          # D2: only real observed target dates
                continue
            rows.append({
                "cohort_id": m["cohort_id"], "series_id": sid, "metric": m["metric"],
                "db_type": m["db_type"], "scenario": m["scenario"], "segment": m["segment"],
                "granularity": m["granularity"], "key": m["key"],
                "route_path": m["route_path"], "model_name": name,
                "model_family": FAMILY[name], "target_date": td, "prediction_date": td,
                "train_start_date": tr["date"].min(), "train_end_date": origin,
                "horizon_steps": step, "actual_value": float(p["amap"][td]),
                "predicted_value": float(pred[step - 1]),
                "backtest_type": "D2_SPARSE_OBSERVED_BACKTEST",
                "burn_in_count": p["burn_in"],
                "source_actuals_artifact":
                    "processed/v6_24_mvp_cohort/actuals_normalized.parquet",
                "model_run_id": RUN_ID, "source_generation_status": "GENERATED_P5",
                "model_status": "OK", "runtime_seconds": 0.0, "caveat": m["caveat"]})
    rt = round(time.time() - t0, 3)
    for r in rows:
        r["runtime_seconds"] = rt
    return rows, rt


def run_phase(phase, models, batch_size):
    global done_ms, done_rows, next_milestone
    log(f"=== PHASE {phase} START | {len(models)} models | batch size {batch_size} series ===")
    for metric in ("SSD", "CPU", "IOPS"):
        sids = sorted(TARGETS[TARGETS["metric"] == metric]["series_id"])
        for bi in range(0, len(sids), batch_size):
            chunk = sids[bi:bi + batch_size]
            bid = f"{metric}_{phase}_{bi // batch_size + 1:02d}"
            b0, brows, bfail = time.time(), [], 0
            log(f"BATCH START {bid} | {len(chunk)} series x {len(models)} models")
            for sid in chunk:
                for name in models:
                    try:
                        rows, rt = run_unit(sid, name)
                        brows.extend(rows)
                        st, err, n = "OK", "", len(rows)
                    except Exception as exc:
                        st, err, n, rt = "FAILED", f"{type(exc).__name__}: {exc}", 0, 0.0
                        bfail += 1
                        cls = ("PREDICTION_NAN_FAILURE" if "invalid" in str(exc)
                               else "MODEL_RUNTIME_FAILURE")
                        failures.append({
                            "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                            "metric": metric, "series_id": sid, "model_name": name,
                            "failure_class": cls, "error_message": str(exc)[:300],
                            "context_summary":
                                traceback.format_exc().strip().splitlines()[-1][:200],
                            "batch_id": bid,
                            "checkpoint_path":
                                f"data/model_runs/v6_24_p5_work/checkpoints/{bid}.parquet"})
                    done_ms += 1
                    done_rows += n
                    exec_ledger.append({"batch_id": bid, "phase": phase, "metric": metric,
                                        "series_id": sid, "model_name": name,
                                        "model_family": FAMILY[name],
                                        "origins_run": len(prep[sid]["origins"]),
                                        "prediction_rows": n, "model_status": st,
                                        "runtime_seconds": rt, "error_message": err})
                    pct = int(done_ms / EXPECTED_MS * 100)
                    if pct >= next_milestone and next_milestone <= 100:
                        progress(next_milestone, metric, name, bid,
                                 f"data/model_runs/v6_24_p5_work/checkpoints/{bid}.parquet")
                        next_milestone += 10
            ck = WORK / "checkpoints" / f"{bid}.parquet"
            if brows:
                pd.DataFrame(brows).to_parquet(ck, index=False, engine="pyarrow")
            bs = round(time.time() - b0, 2)
            batch_ledger.append({"batch_id": bid, "phase": phase, "metric": metric,
                                 "series_count": len(chunk), "model_count": len(models),
                                 "model_series_runs": len(chunk) * len(models),
                                 "prediction_rows": len(brows), "failures": bfail,
                                 "runtime_seconds": bs,
                                 "checkpoint_path": str(ck.relative_to(V6)).replace("\\", "/")})
            log(f"BATCH END   {bid} | rows={len(brows):,} | failures={bfail} | {bs:.1f}s | "
                f"cumulative {done_ms}/{EXPECTED_MS}")
            if time.time() - T0 > HARD_SEC:
                log("HARD STOP reached; stopping after checkpoint")
                return False
            if time.time() - T0 > SOFT_SEC:
                log(f"SOFT STOP reached at {el_min():.1f}m; stopping cleanly after checkpoint")
                return False
    return True


ok_a = run_phase("A", NON_NEURAL, 10)
ok_b = run_phase("B", NEURAL_M, 5) if ok_a else False
if done_ms >= EXPECTED_MS:
    progress(100, "ALL", "ALL", "COMPLETE", "all checkpoints written")

TOTAL_MIN = round(el_min(), 2)
log(f"GENERATION COMPLETE | {done_ms}/{EXPECTED_MS} model-series | {done_rows:,} rows | "
    f"{TOTAL_MIN}m | {len(failures)} failures")

pd.DataFrame(progress_log).to_csv(OUT / "v6_24_p5_progress_log.csv", index=False)
pd.DataFrame(batch_ledger).to_csv(OUT / "v6_24_p5_batch_runtime_ledger.csv", index=False)
pd.DataFrame(exec_ledger).to_csv(OUT / "v6_24_p5_execution_ledger.csv", index=False)
pd.DataFrame(batch_ledger).to_csv(WORK / "runtime_ledger" / "batch_ledger.csv", index=False)
pd.DataFrame(failures).to_csv(WORK / "failures" / "failure_ledger.csv", index=False)
json.dump({"run_id": RUN_ID, "done_ms": done_ms, "expected_ms": EXPECTED_MS,
           "rows": done_rows, "minutes": TOTAL_MIN, "failures": len(failures),
           "complete": bool(ok_a and ok_b and done_ms == EXPECTED_MS)},
          (OUT / "_p5_run.json").open("w", encoding="utf-8"), indent=1)
log("ledgers written; generation phase done")
