"""V6.24-P6B - Governed 30-step forward forecast generation.

Generates forecast_outputs for 140 MVP series x 15 governed models x 30 daily
steps = 63,000 rows, using the identical model execution path as P5 so that
forecasts and backtests remain comparable.

Reads P4/P5/P6 artifacts. Modifies none of them. No SQL. No Shiny.
"""
from __future__ import annotations

import csv
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
WORK = V6 / "data" / "model_runs" / "v6_24_p6b_forecast_work"
P5C = V6 / "outputs" / "v6_24_p5c_independent_backtest_artifact_audit"
PILOT_PATH = V6 / "outputs" / "v6_16_five_case_viewer_uiux_lab" / "build_v6_16_pilot_backtest.py"

for sub in ("checkpoints", "logs", "failures", "runtime_ledger"):
    (WORK / sub).mkdir(parents=True, exist_ok=True)

LAGS, HORIZON = 30, 30
RANDOM_SEED = 42
FORECAST_TYPE = "GOVERNED_30_STEP_DAILY_FORECAST"
SRC_STATUS = "GENERATED_P6B_GOVERNED_30_STEP_FORECAST"
EXPECTED_SERIES, EXPECTED_MODELS = 140, 15
EXPECTED_MS = EXPECTED_SERIES * EXPECTED_MODELS
EXPECTED_ROWS = EXPECTED_MS * HORIZON
NC = "STRUCTURALLY_NOT_COMPUTABLE"

GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
NEURAL_M = ["FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]

spec = importlib.util.spec_from_file_location("v6_16_pilot", PILOT_PATH)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)
BASELINE, CHALLENGER = pilot.BASELINE_CLASSES, pilot.CHALLENGER_FORECASTERS
FAMILY = {**{m: "Baseline" for m in BASELINE}, **{m: "Challenger" for m in CHALLENGER},
          **{m: "Neural" for m in NEURAL_M}}

T0 = time.time()
RUN_ID = f"P6B_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"
failures, exec_ledger, ckpt_ledger, progress_log = [], [], [], []
done_ms = 0


def el_min():
    return (time.time() - T0) / 60


def log(msg):
    print(f"[{datetime.now():%H:%M:%S}] {msg}", flush=True)


def write(path, fields, rows):
    with Path(path).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def progress(pct, metric):
    e = el_min()
    eta = (e / done_ms * (EXPECTED_MS - done_ms)) if done_ms else 0.0
    progress_log.append({
        "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "percent_complete": pct, "elapsed_minutes": round(e, 2),
        "estimated_remaining_minutes": round(eta, 2),
        "completed_model_series": done_ms, "total_model_series": EXPECTED_MS,
        "current_metric": metric, "failures_so_far": len(failures)})
    print(f"[PROGRESS] P6B {pct}% | elapsed={e:.1f}m | eta={eta:.1f}m | metric={metric} | "
          f"model_series={done_ms}/{EXPECTED_MS} | failures={len(failures)}", flush=True)


# ---------------------------------------- model fitting, verbatim from P5
# These wrappers are copied unchanged from p5_full_run.py on purpose. The
# internal np.clip(...,0,None) is part of the model's own inverse log1p
# transform and is already baked into the P5 backtest artifact. Removing it
# here would make P6B forecasts incomparable with P5 backtests and would break
# Viewer = Forecast parity. "Do not clip" in the P6B contract means P6B adds no
# post-hoc clipping of its own.
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


# ---------------------------------------- preflight
log("P6B START - governed 30-step forward forecast generation")
P5CV = pd.read_csv(P5C / "v6_24_p5c_validation.csv")
p5c_ok = bool((P5CV["result"] == "PASS").all())
acc_ok = (PROC / "accuracy_metrics.parquet").exists()
rk_ok = (PROC / "model_rankings.parquet").exists()
fo_existing = [p.name for p in PROC.iterdir() if p.name.startswith("forecast_outputs")]
P6B_OWNED = {"forecast_outputs.parquet", "forecast_outputs.csv"}
fo_unexpected = [n for n in fo_existing if n not in P6B_OWNED]

FROZEN = {"cohort_manifest", "actuals_normalized", "model_backtests_15_models",
          "source_forecast_baselines_normalized", "accuracy_metrics", "model_rankings"}
frozen_before = {p.name: (p.stat().st_mtime, p.stat().st_size) for p in PROC.iterdir()
                 if any(p.name.startswith(k) for k in FROZEN)}

F = ["check_id", "check", "expected", "observed", "result", "blocking_token"]
pf = [dict(zip(F, r)) for r in [
    ("PF01", "P5C independent audit passed", "all PASS",
     f"{int((P5CV['result'] == 'PASS').sum())}/{len(P5CV)} PASS",
     "PASS" if p5c_ok else "FAIL", "V6_24_P6B_BLOCKED_P5C_NOT_PASS"),
    ("PF02", "P6 accuracy_metrics exists", "present",
     "present" if acc_ok else "MISSING", "PASS" if acc_ok else "FAIL",
     "V6_24_P6B_BLOCKED_P6_ANALYTICS_MISSING"),
    ("PF03", "P6 model_rankings exists", "present",
     "present" if rk_ok else "MISSING", "PASS" if rk_ok else "FAIL",
     "V6_24_P6B_BLOCKED_P6_ANALYTICS_MISSING"),
    ("PF04", "Pre-existing forecast_outputs are P6B-owned (idempotent re-run)",
     "0 unexpected",
     f"{len(fo_unexpected)} unexpected; {len(fo_existing)} P6B-owned present",
     "PASS" if not fo_unexpected else "FAIL", "V6_24_P6B_BLOCKED_GOVERNANCE_VIOLATION"),
    ("PF05", "Frozen P4/P5/P6 artifacts tracked before run", "6 artifact families",
     f"{len(frozen_before)} files tracked for mtime+size comparison", "PASS", ""),
    ("PF06", "navigation_contract absent (P7 scope)", "absent",
     "absent" if not (PROC / "navigation_contract.parquet").exists() else "PRESENT",
     "PASS" if not (PROC / "navigation_contract.parquet").exists() else "FAIL",
     "V6_24_P6B_BLOCKED_GOVERNANCE_VIOLATION"),
    ("PF07", "taxonomy_counts absent (P7 scope)", "absent",
     "absent" if not (PROC / "taxonomy_counts.parquet").exists() else "PRESENT",
     "PASS" if not (PROC / "taxonomy_counts.parquet").exists() else "FAIL",
     "V6_24_P6B_BLOCKED_GOVERNANCE_VIOLATION"),
]]
write(OUT / "v6_24_p6b_preflight_check.csv", F, pf)
log(f"v6_24_p6b_preflight_check.csv|rows={len(pf)}")
if not (p5c_ok and acc_ok and rk_ok and not fo_unexpected):
    bad = [r["blocking_token"] for r in pf if r["result"] == "FAIL"]
    raise SystemExit(f"PREFLIGHT FAILED -> {bad[0] if bad else 'UNKNOWN'}")
log(f"preflight OK | P5C {int((P5CV['result'] == 'PASS').sum())}/{len(P5CV)} PASS")

# ---------------------------------------- inputs
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
log(f"cohort {len(MAN)} series | actuals {len(ACT):,} rows")

prep = {}
for _, m in MAN.iterrows():
    g = ACT[ACT["series_id"] == m["series_id"]].sort_values("series_date")
    s = g[["series_date", "actual_value"]].rename(
        columns={"series_date": "date", "actual_value": "value"}).reset_index(drop=True)
    prep[m["series_id"]] = {
        "series": s, "man": m,
        "train_start": s["date"].min(), "train_end": s["date"].max(),
        # Latest observed actual: the anchor for the extreme-ratio rule.
        "latest_actual": float(s["value"].iloc[-1]), "n_obs": len(s)}
log(f"prepared {len(prep)} series | obs min={min(p['n_obs'] for p in prep.values())} "
    f"max={max(p['n_obs'] for p in prep.values())}")

log("building the SMLP-TCN pooled global model across all 140 series (full history)...")
px, py = [], []
for p in prep.values():
    v = np.log1p(np.clip(p["series"]["value"].to_numpy(dtype=float), 0.0, None))
    x, y = pilot.build_xy(v, LAGS, HORIZON)
    if len(x) >= 5:
        px.append(x)
        py.append(y)
GLOBAL_MLP = fit_scaled_mlp(np.vstack(px), np.vstack(py), (16,), 150, "relu") if px else None
log(f"pooled model built from {len(px)} series, {sum(len(a) for a in px):,} windows "
    f"({el_min():.1f}m)")


def run_unit(sid, name):
    """Fit one model on one series' full history and emit exactly 30 forecast rows."""
    p = prep[sid]
    m = p["man"]
    t0 = time.time()
    gm = GLOBAL_MLP if name == "SMLP-TCN" else None
    pred = fit_predictions(name, p["series"], gm)
    la = p["latest_actual"]
    rows = []
    for step in range(1, HORIZON + 1):
        pv = float(pred[step - 1])
        if la == 0:
            ex = NC
        else:
            ratio = abs(pv / la)
            ex = "TRUE" if (ratio > 100 or ratio < 0.01) else "FALSE"
        rows.append({
            "cohort_id": m["cohort_id"], "series_id": sid, "metric": m["metric"],
            "db_type": m["db_type"], "scenario": m["scenario"], "segment": m["segment"],
            "granularity": m["granularity"], "key": m["key"],
            "route_path": m["route_path"], "model_name": name,
            "model_family": FAMILY[name],
            "forecast_date": p["train_end"] + pd.Timedelta(days=step),
            "forecast_step": step, "forecast_horizon_days": step,
            "train_start_date": p["train_start"], "train_end_date": p["train_end"],
            "latest_actual_value": la, "predicted_value": pv,
            "negative_forecast_flag": "TRUE" if pv < 0 else "FALSE",
            "extreme_forecast_flag": ex,
            "forecast_type": FORECAST_TYPE, "source_generation_status": SRC_STATUS,
            "model_run_id": RUN_ID, "model_status": "OK",
            "runtime_seconds": 0.0, "caveat": m["caveat"]})
    rt = round(time.time() - t0, 4)
    for r in rows:
        r["runtime_seconds"] = rt
    return rows, rt


# ---------------------------------------- generation, checkpointed by metric
METRIC_ORDER = ["HDD", "SSD", "CPU", "IOPS"]
all_rows = []
hit = set()
progress(0, "START")

for metric in METRIC_ORDER:
    sids = MAN[MAN["metric"] == metric]["series_id"].tolist()
    log(f"--- {metric}: {len(sids)} series x 15 models = {len(sids) * 15} units")
    mrows, mfail, mt0 = [], 0, time.time()
    for sid in sids:
        for name in GOVERNED:
            try:
                rows, rt = run_unit(sid, name)
                mrows.extend(rows)
                exec_ledger.append({
                    "run_id": RUN_ID, "metric": metric, "series_id": sid,
                    "model_name": name, "model_family": FAMILY[name],
                    "forecast_steps_emitted": len(rows), "model_status": "OK",
                    "runtime_seconds": rt, "error": ""})
            except Exception as e:  # noqa: BLE001 - failures are recorded, never substituted
                mfail += 1
                failures.append({
                    "run_id": RUN_ID, "metric": metric, "series_id": sid,
                    "model_name": name, "error_type": type(e).__name__,
                    "error": str(e)[:400],
                    "traceback": traceback.format_exc()[-800:]})
                exec_ledger.append({
                    "run_id": RUN_ID, "metric": metric, "series_id": sid,
                    "model_name": name, "model_family": FAMILY[name],
                    "forecast_steps_emitted": 0, "model_status": "FAILED",
                    "runtime_seconds": 0.0, "error": f"{type(e).__name__}: {e}"[:200]})
            done_ms += 1
            pct = int(100 * done_ms / EXPECTED_MS)
            for ms in (25, 50, 75, 100):
                if pct >= ms and ms not in hit:
                    hit.add(ms)
                    progress(ms, metric)
    mrt = round(time.time() - mt0, 2)
    cp = WORK / "checkpoints" / f"p6b_checkpoint_{metric}.parquet"
    pd.DataFrame(mrows).to_parquet(cp, index=False, engine="pyarrow", compression="snappy")
    ckpt_ledger.append({
        "metric": metric, "series_count": len(sids), "model_count": len(GOVERNED),
        "expected_rows": len(sids) * len(GOVERNED) * HORIZON, "row_count": len(mrows),
        "failures": mfail, "runtime_seconds": mrt, "checkpoint_path": str(cp)})
    all_rows.extend(mrows)
    log(f"--- {metric} done: {len(mrows):,} rows | {mfail} failures | {mrt:.1f}s "
        f"| checkpoint {cp.name}")

FC = pd.DataFrame(all_rows)
log(f"generation complete: {len(FC):,} rows in {el_min():.2f} min | {len(failures)} failures")

# ---------------------------------------- ledgers (failure ledger always written)
FF = ["run_id", "metric", "series_id", "model_name", "error_type", "error", "traceback"]
write(WORK / "failures" / "p6b_failures.csv", FF, failures)
log(f"failure ledger written ({len(failures)} rows; written even when empty)")

EF = ["run_id", "metric", "series_id", "model_name", "model_family",
      "forecast_steps_emitted", "model_status", "runtime_seconds", "error"]
write(WORK / "runtime_ledger" / "p6b_execution_ledger.csv", EF, exec_ledger)
write(OUT / "v6_24_p6b_forecast_execution_ledger.csv", EF, exec_ledger)
write(WORK / "logs" / "p6b_progress_log.csv", list(progress_log[0]), progress_log)

# ---------------------------------------- promotion gate
sm = FC.groupby(["series_id", "model_name"]).size()
gate = {
    "rows == 63,000": len(FC) == EXPECTED_ROWS,
    "series == 140": FC["series_id"].nunique() == EXPECTED_SERIES,
    "models == 15": FC["model_name"].nunique() == EXPECTED_MODELS,
    "series-model pairs == 2,100": len(sm) == EXPECTED_MS,
    "every pair has exactly 30 steps": bool(sm.eq(HORIZON).all()),
    "forecast_step always 1..30": bool(
        FC.groupby(["series_id", "model_name"])["forecast_step"].apply(
            lambda x: sorted(x) == list(range(1, 31))).all()),
    "forecast_horizon_days == forecast_step": bool(
        (FC["forecast_horizon_days"] == FC["forecast_step"]).all()),
    "forecast_date == train_end + step": bool(
        (pd.to_datetime(FC["forecast_date"])
         == pd.to_datetime(FC["train_end_date"])
         + pd.to_timedelta(FC["forecast_step"], unit="D")).all()),
    "forecast_date > train_end_date": bool(
        (pd.to_datetime(FC["forecast_date"]) > pd.to_datetime(FC["train_end_date"])).all()),
    "all predicted_value finite": bool(np.isfinite(FC["predicted_value"]).all()),
    "only governed model names": set(FC["model_name"]) == set(GOVERNED),
    "forecast_type constant": set(FC["forecast_type"]) == {FORECAST_TYPE},
    "source_generation_status constant": set(FC["source_generation_status"]) == {SRC_STATUS},
    "zero unresolved failures": len(failures) == 0,
    "checkpoints reconcile": sum(c["row_count"] for c in ckpt_ledger) == len(FC),
}
log("--- promotion gate ---")
for k, v in gate.items():
    log(f"  [{'OK  ' if v else 'FAIL'}] {k}")
if not all(gate.values()):
    bad = [k for k, v in gate.items() if not v]
    raise SystemExit(f"GATE FAILED, forecast_outputs NOT promoted: {bad}")

FC.to_parquet(PROC / "forecast_outputs.parquet", index=False, engine="pyarrow",
              compression="snappy")
FC.to_csv(PROC / "forecast_outputs.csv", index=False)
log("PROMOTED forecast_outputs.parquet / .csv")

# ---------------------------------------- governance: frozen artifacts untouched
frozen_after = {p.name: (p.stat().st_mtime, p.stat().st_size) for p in PROC.iterdir()
                if any(p.name.startswith(k) for k in FROZEN)}
touched = sorted(n for n in frozen_before if frozen_before[n] != frozen_after.get(n))
if touched:
    raise SystemExit(f"GOVERNANCE VIOLATION: P6B modified frozen artifacts: {touched}")
log(f"governance OK | {len(frozen_before)} frozen artifacts unmodified")

CF = ["metric", "series_count", "model_count", "expected_rows", "row_count",
      "failures", "runtime_seconds", "reconciles", "checkpoint_path"]
write(OUT / "v6_24_p6b_checkpoint_reconciliation.csv", CF,
      [{**c, "reconciles": "TRUE" if c["row_count"] == c["expected_rows"] else "FALSE"}
       for c in ckpt_ledger])

json.dump({"run_id": RUN_ID, "rows": len(FC), "series": int(FC["series_id"].nunique()),
           "models": int(FC["model_name"].nunique()), "failures": len(failures),
           "runtime_min": round(el_min(), 3),
           "frozen_unmodified": len(frozen_before), "checkpoints": ckpt_ledger,
           "p5c_pass": int((P5CV["result"] == "PASS").sum()), "p5c_total": len(P5CV)},
          (OUT / "_p6b.json").open("w", encoding="utf-8"), indent=1, default=str)
progress(100, "DONE")
log(f"P6B GENERATION COMPLETE | {len(FC):,} rows | {el_min():.2f} min")
