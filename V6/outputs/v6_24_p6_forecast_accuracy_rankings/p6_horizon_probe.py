"""V6.24-P6 - Forecast horizon capability probe.

Measures, for each of the 15 governed AEGIS models, how many forward steps the
model actually emits when asked to forecast. This produces the durable evidence
behind the P6 forecast horizon contract.

Read-only with respect to processed/. Fits models in memory on ONE real cohort
series and discards them. Writes no forecast artifact.
"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

OUT = Path(__file__).resolve().parent
V6 = OUT.parent.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
LAB = V6 / "outputs" / "v6_16_five_case_viewer_uiux_lab"
sys.path.insert(0, str(LAB))
sys.path.insert(0, str(V6))

from build_v6_16_pilot_backtest import (  # noqa: E402
    BASELINE_CLASSES, CHALLENGER_FORECASTERS, NEURAL_MODELS,
    HORIZON_DAYS, LAGS, _fit_baseline, _fit_neural,
)
from model_lab.run_v3_2c_subset_dry_run import (  # noqa: E402
    build_xy, fit_global_mlp,
)

print(f"registry constants: HORIZON_DAYS={HORIZON_DAYS} LAGS={LAGS}")

ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])
# Use the longest available series so history is never the limiting factor.
sid = ACT.groupby("series_id").size().idxmax()
s = ACT[ACT["series_id"] == sid].sort_values("series_date").reset_index(drop=True)
training = s.rename(columns={"series_date": "date", "actual_value": "value"})[["date", "value"]]
print(f"probe series: {sid} | {len(training)} observations "
      f"{training['date'].min().date()} -> {training['date'].max().date()}")

values = np.log1p(np.clip(training["value"].to_numpy(dtype=float), 0.0, None))
gx, gy = build_xy(values, LAGS, HORIZON_DAYS)
global_model = fit_global_mlp(gx, gy)

REQUESTED = 48 * 30  # the prompt's default assumption: 48 steps x 30 days
rows = []


def probe(name: str, family: str, fn, accepts_horizon: str, note: str) -> None:
    try:
        out = np.asarray(fn(), dtype=float)
        n = int(out.shape[0]) if out.ndim else 0
        rows.append({
            "model_name": name, "model_family": family,
            "call_site_accepts_horizon_argument": accepts_horizon,
            "requested_steps": REQUESTED, "emitted_steps": n,
            "matches_request": "TRUE" if n == REQUESTED else "FALSE",
            "emitted_equals_30": "TRUE" if n == 30 else "FALSE",
            "probe_result": "OK", "error": "",
            "evidence": note,
        })
        print(f"  {name:<20} emitted {n} steps")
    except Exception as e:  # noqa: BLE001 - the failure itself is the evidence
        rows.append({
            "model_name": name, "model_family": family,
            "call_site_accepts_horizon_argument": accepts_horizon,
            "requested_steps": REQUESTED, "emitted_steps": -1,
            "matches_request": "FALSE", "emitted_equals_30": "FALSE",
            "probe_result": "ERROR", "error": f"{type(e).__name__}: {e}"[:300],
            "evidence": note,
        })
        print(f"  {name:<20} ERROR {type(e).__name__}")


print("\nprobing 7 baseline models...")
for n in BASELINE_CLASSES:
    probe(n, "baseline", lambda n=n: _fit_baseline(n, training), "NO",
          "_fit_baseline calls model.predict(HORIZON_DAYS); HORIZON_DAYS is a "
          "module constant, not a parameter")

print("probing 5 challenger models...")
for n, fn in CHALLENGER_FORECASTERS.items():
    # run_daily_clean_challengers signatures take the raw value array only.
    probe(n, "challenger",
          lambda fn=fn: fn(training["value"].to_numpy(dtype=float)), "NO",
          "run_daily_clean_challengers._forecast_* signature is (values) only; the "
          "horizon is the module constant HORIZON_DAYS. A horizon-parameterised "
          "variant exists in model_lab/run_backtest_60d.py but is NOT the governed "
          "import path used by the 15-model registry")

print("probing 3 neural models...")
for n in NEURAL_MODELS:
    probe(n, "neural", lambda n=n: _fit_neural(n, values, global_model), "NO",
          "build_xy(values, LAGS, HORIZON_DAYS) makes 30 the OUTPUT DIMENSION of "
          "the trained network; changing it requires retraining a new architecture")

H = pd.DataFrame(rows)
H.to_csv(OUT / "v6_24_p6_forecast_horizon_probe.csv", index=False)
ok = H[H["probe_result"] == "OK"]
print(f"\nv6_24_p6_forecast_horizon_probe.csv|rows={len(H)}")
print(f"probed OK: {len(ok)}/15 | all emitted exactly 30 steps: "
      f"{(ok['emitted_equals_30'] == 'TRUE').all()}")
print(f"any model reached the requested {REQUESTED} steps: "
      f"{(ok['matches_request'] == 'TRUE').any()}")
print("distinct emitted step counts:", sorted(ok["emitted_steps"].unique().tolist()))
