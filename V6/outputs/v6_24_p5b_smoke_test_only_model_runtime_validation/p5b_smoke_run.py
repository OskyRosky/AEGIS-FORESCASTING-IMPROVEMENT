"""V6.24-P5B | Smoke test only. 3 series x 15 governed models.

Replicates the reference generator (run_v6_17_viewer_backtests.py) exactly for
model fitting, but applies the owner-approved D2 Option B window policy for
origin selection and target emission.

The critical difference from the reference: a model still forecasts 30 steps
ahead from each origin, but a row is emitted ONLY for target dates that actually
exist in actuals_normalized. Predictions landing on unobserved calendar days are
discarded, never written. Nothing is filled, resampled or interpolated.

SMOKE TEST ONLY. Writes nothing to processed/.
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

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
WORK = V6 / "data" / "model_runs" / "v6_24_p5_work" / "smoke_test"
P5A = OUT.parent / "v6_24_p5a_backtest_execution_plan_budget_window_contract"
PILOT_PATH = V6 / "outputs" / "v6_16_five_case_viewer_uiux_lab" / "build_v6_16_pilot_backtest.py"

WORK.mkdir(parents=True, exist_ok=True)

LAGS, HORIZON = 30, 30
BURN_IN_DAYS = LAGS + HORIZON + 4
MIN_TRAIN_ROWS = LAGS + HORIZON + 5
MIN_TARGETS = 20
ORIGIN_COUNT = 11
RANDOM_SEED = 42
SMOKE_BUDGET_SEC = 15 * 60

GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]

spec = importlib.util.spec_from_file_location("v6_16_pilot", PILOT_PATH)
pilot = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = pilot
spec.loader.exec_module(pilot)
BASELINE, CHALLENGER = pilot.BASELINE_CLASSES, pilot.CHALLENGER_FORECASTERS
NEURAL = tuple(pilot.NEURAL_MODELS)
FAMILY = {**{m: "Baseline" for m in BASELINE},
          **{m: "Challenger" for m in CHALLENGER},
          **{m: "Neural" for m in NEURAL}}
print(f"pilot loaded | {len(BASELINE)} baseline + {len(CHALLENGER)} challenger + "
      f"{len(NEURAL)} neural = {len(BASELINE) + len(CHALLENGER) + len(NEURAL)}", flush=True)

T0 = time.time()
RUN_ID = f"P5B_SMOKE_{datetime.now(timezone.utc):%Y%m%dT%H%M%S}"


def elapsed():
    return time.time() - T0


# ------------------------------------------------- neural, replicated verbatim
def fit_scaled_mlp(x, y, hidden, iters, act):
    reg = Pipeline([("scale", StandardScaler()),
                    ("mlp", MLPRegressor(hidden_layer_sizes=hidden, activation=act,
                                         solver="adam", alpha=1e-3, max_iter=iters,
                                         early_stopping=len(x) >= 20,
                                         validation_fraction=0.1,
                                         random_state=RANDOM_SEED))])
    model = TransformedTargetRegressor(regressor=reg, transformer=StandardScaler())
    with warnings.catch_warnings():
        warnings.filterwarnings("ignore", category=ConvergenceWarning)
        model.fit(x, y)
    return model


def fit_fnar_v2_scaled(values):
    transformed = np.log1p(np.clip(values, 0.0, None))
    x, y = pilot.build_xy(transformed, LAGS, HORIZON)
    if len(x) < 5:
        raise ValueError(f"insufficient FNAR-V2 training rows ({len(x)})")
    model = fit_scaled_mlp(x, y, (32,), 300, "tanh")
    feat = np.log1p(np.clip(values[-LAGS:][::-1].reshape(1, -1), 0.0, None))
    return np.clip(np.expm1(np.asarray(model.predict(feat)).ravel()), 0.0, None)


def predict_smlp_scaled(model, values):
    feat = np.log1p(np.clip(values[-LAGS:][::-1].reshape(1, -1), 0.0, None))
    return np.clip(np.expm1(np.asarray(model.predict(feat)).ravel()), 0.0, None)


def fit_predictions(model_name, training, global_model):
    values = training["value"].to_numpy(dtype=float)
    if model_name in BASELINE:
        pred = pilot._fit_baseline(model_name, training)
    elif model_name in CHALLENGER:
        pred = np.asarray(CHALLENGER[model_name](values), dtype=float)
    elif model_name == "FNAR-V2":
        pred = fit_fnar_v2_scaled(values)
    elif model_name == "SMLP-TCN":
        if global_model is None:
            raise ValueError("SMLP-TCN global model is missing")
        pred = predict_smlp_scaled(global_model, values)
    elif model_name == "NLIN-DLIN_FIXED":
        pred = pilot._fit_neural(model_name, values, global_model)
    else:
        raise ValueError(f"Unexpected model {model_name}")
    pred = np.asarray(pred, dtype=float)
    if len(pred) != HORIZON or not np.isfinite(pred).all():
        raise ValueError(f"{model_name} produced invalid {len(pred)}-row predictions")
    return pred


# ------------------------------------------------- inputs
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
D2 = pd.read_csv(P5A / "v6_24_p5a_backtest_window_contract_D2_APPROVED.csv", dtype=str)

PREFERRED = [("SSD", "SSD__Phoenix__Forest__NAMPRD08"),
             ("CPU", "CPU__Consumed__Region__CHN-Gallatin"),
             ("IOPS", "IOPS__Consumed__Region__APC-Multitenant")]
selection = []
for metric, want in PREFERRED:
    if want in set(MAN["series_id"]):
        sid, reason = want, "PREFERRED_SERIES_PRESENT"
    else:
        sid = MAN[MAN["metric"] == metric]["series_id"].sort_values().iloc[0]
        reason = f"PREFERRED {want} ABSENT; first {metric} series by sort order"
    g = ACT[ACT["series_id"] == sid]
    w = D2[D2["series_id"] == sid].iloc[0]
    selection.append({
        "metric": metric, "series_id": sid, "selection_reason": reason,
        "actual_rows": int(len(g)),
        "min_date": str(g["series_date"].min())[:10],
        "max_date": str(g["series_date"].max())[:10],
        "missing_calendar_days": int(w["missing_calendar_days"]),
        "expected_valid_origins": int(w["valid_origin_count"]),
        "expected_target_dates": int(w["target_date_count"]),
    })
    print(f"  {metric}: {sid} | {len(g)} rows | {w['valid_origin_count']} origins expected",
          flush=True)


# ------------------------------------------------- D2 origins
def d2_origins(g):
    dmin, dmax = g["series_date"].min(), g["series_date"].max()
    earliest = dmin + pd.Timedelta(days=BURN_IN_DAYS)
    latest = dmax - pd.Timedelta(days=HORIZON)
    if latest < earliest:
        return [], 0
    span = int((latest - earliest).days)
    offs = sorted({int(round(span * i / (ORIGIN_COUNT - 1))) for i in range(ORIGIN_COUNT)})
    origins = [earliest + pd.Timedelta(days=o) for o in offs]
    if latest not in origins:          # D2 rule W2: force the latest origin
        origins.append(latest)
    burn = int((g["series_date"] < earliest).sum())
    valid = []
    for o in sorted(set(origins)):
        ntr = int((g["series_date"] <= o).sum())
        tgt = g["series_date"][(g["series_date"] > o)
                               & (g["series_date"] <= o + pd.Timedelta(days=HORIZON))]
        if ntr >= MIN_TRAIN_ROWS and len(tgt) >= MIN_TARGETS:
            valid.append(o)
    return valid, burn


prepared = {}
for s in selection:
    g = ACT[ACT["series_id"] == s["series_id"]].sort_values("series_date")
    origins, burn = d2_origins(g)
    ser = g[["series_date", "actual_value"]].rename(
        columns={"series_date": "date", "actual_value": "value"}).reset_index(drop=True)
    prepared[s["series_id"]] = {
        "series": ser, "origins": origins, "burn_in": burn,
        "obs_dates": set(g["series_date"]),
        "actual_map": dict(zip(g["series_date"], g["actual_value"])),
        "manifest": MAN[MAN["series_id"] == s["series_id"]].iloc[0]}
    s["actual_valid_origins"] = len(origins)
    s["burn_in_count"] = burn
    print(f"  {s['series_id']}: {len(origins)} valid origins, burn-in {burn} oldest rows",
          flush=True)


# ------------------------------------------------- SMLP-TCN pooled global models
def build_globals():
    out = {}
    mx = max(len(p["origins"]) for p in prepared.values())
    for i in range(mx):
        px, py = [], []
        for p in prepared.values():
            if i >= len(p["origins"]):
                continue
            tr = p["series"][p["series"]["date"] <= p["origins"][i]]
            v = np.log1p(np.clip(tr["value"].to_numpy(dtype=float), 0.0, None))
            x, y = pilot.build_xy(v, LAGS, HORIZON)
            if len(x) >= 5:
                px.append(x)
                py.append(y)
        out[i] = fit_scaled_mlp(np.vstack(px), np.vstack(py), (16,), 150, "relu") if px else None
    return out


print("\nbuilding SMLP-TCN pooled global models...", flush=True)
GLOBALS = build_globals()
print(f"  {len([v for v in GLOBALS.values() if v is not None])} pooled models built "
      f"({elapsed():.1f}s elapsed)\n", flush=True)

# ------------------------------------------------- run
rows, failures, ledger = [], [], []
for s in selection:
    sid = s["series_id"]
    p = prepared[sid]
    m = p["manifest"]
    for model_name in GOVERNED:
        t0 = time.time()
        status, emitted, err = "OK", 0, ""
        try:
            if elapsed() > SMOKE_BUDGET_SEC:
                raise TimeoutError(f"smoke budget {SMOKE_BUDGET_SEC}s exceeded")
            for oi, origin in enumerate(p["origins"]):
                tr = p["series"][p["series"]["date"] <= origin]
                gm = GLOBALS.get(oi) if model_name == "SMLP-TCN" else None
                pred = fit_predictions(model_name, tr, gm)
                for step in range(1, HORIZON + 1):
                    tdate = origin + pd.Timedelta(days=step)
                    # D2 rule W4: emit ONLY for real observed target dates.
                    if tdate not in p["obs_dates"]:
                        continue
                    rows.append({
                        "cohort_id": m["cohort_id"], "series_id": sid, "metric": m["metric"],
                        "db_type": m["db_type"], "scenario": m["scenario"],
                        "segment": m["segment"], "granularity": m["granularity"],
                        "key": m["key"], "route_path": m["route_path"],
                        "model_name": model_name, "model_family": FAMILY[model_name],
                        "target_date": tdate, "prediction_date": tdate,
                        "train_start_date": tr["date"].min(), "train_end_date": origin,
                        "horizon_steps": step,
                        "actual_value": float(p["actual_map"][tdate]),
                        "predicted_value": float(pred[step - 1]),
                        "backtest_type": "D2_SPARSE_OBSERVED_SMOKE_TEST",
                        "burn_in_count": p["burn_in"],
                        "source_actuals_artifact":
                            "processed/v6_24_mvp_cohort/actuals_normalized.parquet",
                        "model_run_id": RUN_ID,
                        "source_generation_status": "SMOKE_TEST_ONLY",
                        "model_status": "OK", "runtime_seconds": 0.0,
                        "caveat": m["caveat"],
                    })
                    emitted += 1
        except Exception as exc:
            status, err = "FAILED", f"{type(exc).__name__}: {exc}"
            cls = ("TIME_BUDGET_EXCEEDED" if isinstance(exc, TimeoutError)
                   else "PREDICTION_NAN_FAILURE" if "invalid" in str(exc)
                   else "MODEL_RUNTIME_FAILURE")
            failures.append({
                "timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "metric": s["metric"], "series_id": sid, "model_name": model_name,
                "failure_class": cls, "error_message": str(exc)[:300],
                "context_summary": traceback.format_exc().strip().splitlines()[-1][:200],
                "batch_id": "SMOKE", "checkpoint_path": "data/model_runs/v6_24_p5_work/smoke_test",
            })
        rt = round(time.time() - t0, 3)
        if emitted:
            for r in rows[-emitted:]:
                r["runtime_seconds"] = rt
        ledger.append({"metric": s["metric"], "series_id": sid, "model_name": model_name,
                       "model_family": FAMILY[model_name],
                       "origins_run": len(p["origins"]), "prediction_rows": emitted,
                       "model_status": status, "runtime_seconds": rt, "error_message": err})
        print(f"  {s['metric']:<5} {model_name:<18} {status:<7} rows={emitted:>4} {rt:>7.2f}s",
              flush=True)

TOTAL = round(elapsed(), 1)
BT = pd.DataFrame(rows)
ok = sum(1 for x in ledger if x["model_status"] == "OK")
print(f"\nSMOKE COMPLETE | {len(BT):,} rows | {TOTAL}s | {ok}/{len(ledger)} model-series OK",
      flush=True)

BT.to_parquet(WORK / "smoke_checkpoint.parquet", index=False, engine="pyarrow")
pd.DataFrame(ledger).to_csv(WORK / "smoke_runtime_ledger.csv", index=False)
pd.DataFrame(failures).to_csv(WORK / "smoke_failure_ledger.csv", index=False)
json.dump({"selection": selection, "total_seconds": TOTAL, "run_id": RUN_ID,
           "rows": len(BT), "failures": len(failures)},
          (OUT / "_p5b_run.json").open("w", encoding="utf-8"), indent=1, default=str)
BT.to_pickle(OUT / "_p5b_bt.pkl")
pd.DataFrame(ledger).to_pickle(OUT / "_p5b_ledger.pkl")
pd.DataFrame(failures).to_pickle(OUT / "_p5b_fail.pkl")
print("work artifacts written", flush=True)
