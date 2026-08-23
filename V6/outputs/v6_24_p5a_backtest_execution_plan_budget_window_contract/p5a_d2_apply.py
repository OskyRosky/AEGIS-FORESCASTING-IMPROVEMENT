"""V6.24-P5A-D2 | Apply the owner-approved sparse-observed window policy.

Owner decision D2, approved 2026-08-23: Option B.

  - burn-in only from the oldest side
  - force the latest origin at max_date - 30 when valid
  - require at least 20 REAL OBSERVED target dates inside the 30-day horizon
  - do not fill, resample, interpolate or invent dates
  - prediction_date must equal target_date
  - actual_value must come from actuals_normalized for that series_id + target_date

This recomputes the window contract under the approved rule and measures the delta
against the previous strict-contiguity rule. No models are run.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"

LAGS, HORIZON = 30, 30
BURN_IN_DAYS = LAGS + HORIZON + 4          # 64
MIN_TRAIN_ROWS = LAGS + HORIZON + 5        # 65
MIN_TARGETS = 20                           # D2 Option B: was == HORIZON (30)
ORIGIN_COUNT = 11

ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])

STRICT = pd.read_csv(OUT / "v6_24_p5a_backtest_window_contract.csv", dtype=str)
STRICT["valid_origin_count"] = STRICT["valid_origin_count"].astype(int)
STRICT["target_date_count"] = STRICT["target_date_count"].astype(int)
strict_by_id = STRICT.set_index("series_id")

rows = []
for sid, g in ACT.groupby("series_id"):
    g = g.sort_values("series_date")
    dmin, dmax = g["series_date"].min(), g["series_date"].max()
    n = len(g)
    span = (dmax - dmin).days + 1

    earliest = dmin + pd.Timedelta(days=BURN_IN_DAYS)
    latest = dmax - pd.Timedelta(days=HORIZON)
    burn_rows = int((g["series_date"] < earliest).sum())

    if latest < earliest:
        origins = []
    else:
        span_days = int((latest - earliest).days)
        offsets = sorted({int(round(span_days * i / (ORIGIN_COUNT - 1)))
                          for i in range(ORIGIN_COUNT)})
        origins = [earliest + pd.Timedelta(days=o) for o in offsets]
        # D2: the latest origin is forced, so the newest observations are always
        # the last thing predicted rather than the first thing lost.
        if latest not in origins:
            origins.append(latest)
        origins = sorted(set(origins))

    valid, targets, first_tgt, last_tgt = 0, 0, None, None
    forced_ok = False
    for o in origins:
        ntr = int((g["series_date"] <= o).sum())
        tgt = g["series_date"][(g["series_date"] > o)
                               & (g["series_date"] <= o + pd.Timedelta(days=HORIZON))]
        if ntr >= MIN_TRAIN_ROWS and len(tgt) >= MIN_TARGETS:
            valid += 1
            targets += len(tgt)
            if first_tgt is None:
                first_tgt = tgt.min()
            last_tgt = tgt.max()
            if o == latest:
                forced_ok = True

    m = MAN[MAN["series_id"] == sid].iloc[0]
    prev = strict_by_id.loc[sid]
    preserved = (last_tgt == dmax) if last_tgt is not None else False
    rows.append({
        "metric": m["metric"], "series_id": sid,
        "min_actual_date": str(dmin)[:10], "max_actual_date": str(dmax)[:10],
        "observation_count": n, "calendar_span_days": span,
        "missing_calendar_days": span - n,
        "proposed_burn_in_count": burn_rows, "burn_in_side": "OLDEST_ONLY",
        "policy": "D2_OPTION_B_SPARSE_OBSERVED",
        "min_observed_targets_required": MIN_TARGETS,
        "sampled_origin_count": len(origins),
        "forced_latest_origin": str(latest)[:10] if origins else "NONE",
        "forced_latest_origin_valid": "TRUE" if forced_ok else "FALSE",
        "first_origin_date": str(earliest)[:10],
        "valid_origin_count": valid,
        "first_backtest_target_date": str(first_tgt)[:10] if first_tgt is not None else "NONE",
        "last_backtest_target_date": str(last_tgt)[:10] if last_tgt is not None else "NONE",
        "target_date_count": targets,
        "newest_observation_preserved": "TRUE" if preserved else "FALSE",
        "prev_strict_valid_origins": int(prev["valid_origin_count"]),
        "prev_strict_target_dates": int(prev["target_date_count"]),
        "prev_strict_last_target": prev["last_backtest_target_date"],
        "origins_recovered": valid - int(prev["valid_origin_count"]),
        "target_dates_recovered": targets - int(prev["target_date_count"]),
        "in_p5_workload": "FALSE" if m["metric"] == "HDD" else "TRUE",
        "rule": ("LEFT_BURN_IN_ONLY_NEWEST_PRESERVED" if preserved
                 else "NO_VALID_ORIGIN" if valid == 0
                 else "LEFT_BURN_IN_ONLY_NEWEST_NOT_REACHED"),
        "notes": (f"{valid} valid origins under the approved sparse rule "
                  f"(>= {MIN_TARGETS} observed targets in the 30-day horizon). Burn-in consumes "
                  f"the {burn_rows} OLDEST observations only. "
                  + ("Forced latest origin at max_date-30 is valid, so the last target equals "
                     "the series max date." if forced_ok and preserved else
                     "Forced latest origin did not qualify; the last reachable target is "
                     f"{str(last_tgt)[:10] if last_tgt is not None else 'NONE'}.")
                  + " No dates were filled, resampled or interpolated."),
    })

F = list(rows[0].keys())
with (OUT / "v6_24_p5a_backtest_window_contract_D2_APPROVED.csv").open(
        "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=F)
    w.writeheader()
    w.writerows(rows)
print(f"v6_24_p5a_backtest_window_contract_D2_APPROVED.csv|rows={len(rows)}")

df = pd.DataFrame(rows)
new = df[df["in_p5_workload"] == "TRUE"]
print("\n=== D2 Option B, P5 workload ===")
for m, g in new.groupby("metric"):
    pres = int((g["newest_observation_preserved"] == "TRUE").sum())
    print(f"{m:<5} series={len(g):>3} origins {g['valid_origin_count'].min()}-"
          f"{g['valid_origin_count'].max()} (was {g['prev_strict_valid_origins'].min()}-"
          f"{g['prev_strict_valid_origins'].max()}) | targets={int(g['target_date_count'].sum()):,} "
          f"(was {int(g['prev_strict_target_dates'].sum()):,}) | newest preserved {pres}/{len(g)}")

tot_t = int(new["target_date_count"].sum())
prev_t = int(new["prev_strict_target_dates"].sum())
pres = int((new["newest_observation_preserved"] == "TRUE").sum())
print(f"\nTOTAL targets {prev_t:,} -> {tot_t:,} (+{tot_t - prev_t:,})")
print(f"prediction rows {prev_t * 15:,} -> {tot_t * 15:,}")
print(f"newest observation preserved: {pres} of {len(new)} (was 68)")
print(f"series with zero valid origins: {int((new['valid_origin_count'] == 0).sum())}")
print(f"origin-level fits: {int(new['valid_origin_count'].sum()) * 15:,}")

json.dump({"total_targets": tot_t, "prev_targets": prev_t, "preserved": pres,
           "series": len(new),
           "origin_fits": int(new["valid_origin_count"].sum()) * 15},
          (OUT / "_p5a_d2.json").open("w", encoding="utf-8"), indent=1)
