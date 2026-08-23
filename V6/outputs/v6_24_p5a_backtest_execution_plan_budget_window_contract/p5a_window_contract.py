"""V6.24-P5A | Backtest window contract computed from the real cohort dates.

Mirrors the reference implementation in run_v6_17_viewer_backtests.py exactly:

    LAGS = 30, HORIZON_DAYS = 30
    first_origin = min_date + (LAGS + HORIZON_DAYS + 4) days   -> 64-day left burn-in
    last_origin  = max_date - HORIZON_DAYS days
    training     = rows with date <= origin
    test         = rows with origin < date <= origin + HORIZON_DAYS

    valid origin requires  len(training) >= LAGS + HORIZON_DAYS + 5  (65 rows)
                     and   len(test) == HORIZON_DAYS                 (exactly 30 rows)

The second condition is a real hazard: it demands a daily-contiguous test window.
Series with date gaps lose origins. This script measures that per series rather
than assuming it.

Planning only. No models are fitted.
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
ORIGIN_COUNT = 11                          # reference policy: 11 sampled origins per series

ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])


def sampled_origins(dmin, dmax, count):
    """Reproduce origin_dates() from run_v6_17_viewer_backtests.py.

    Origins are evenly spaced between the burn-in boundary and max_date - HORIZON.
    The final origin is exactly max_date - HORIZON, which is what guarantees the
    last target date equals the series max date: the newest observation is never
    burned, it is the last thing predicted.
    """
    earliest = dmin + pd.Timedelta(days=BURN_IN_DAYS)
    latest = dmax - pd.Timedelta(days=HORIZON)
    if latest < earliest:
        return [], earliest, latest
    span = int((latest - earliest).days)
    offsets = sorted(set(int(round(x)) for x in
                         [span * i / (count - 1) for i in range(count)]))
    return [earliest + pd.Timedelta(days=o) for o in offsets], earliest, latest


rows = []
for sid, g in ACT.groupby("series_id"):
    g = g.sort_values("series_date")
    dmin, dmax = g["series_date"].min(), g["series_date"].max()
    n = len(g)
    span = (dmax - dmin).days + 1

    origins, first_origin, last_origin = sampled_origins(dmin, dmax, ORIGIN_COUNT)
    burn_rows = int((g["series_date"] < first_origin).sum())

    valid, first_tgt, last_tgt = 0, None, None
    for o in origins:
        ntr = int((g["series_date"] <= o).sum())
        nte = int(((g["series_date"] > o)
                   & (g["series_date"] <= o + pd.Timedelta(days=HORIZON))).sum())
        if ntr >= MIN_TRAIN_ROWS and nte == HORIZON:
            valid += 1
            if first_tgt is None:
                first_tgt = o + pd.Timedelta(days=1)
            last_tgt = o + pd.Timedelta(days=HORIZON)

    gaps = span - n
    m = MAN[MAN["series_id"] == sid].iloc[0]
    if valid == 0:
        rule = "SERIES_TOO_SHORT_OR_TOO_GAPPY_AFTER_BURN_IN"
        note = (f"No valid origin among the {len(origins)} sampled. Span {span} days with {n} "
                f"observations ({gaps} missing calendar days). A valid origin needs "
                f"{MIN_TRAIN_ROWS} training rows and a daily-contiguous {HORIZON}-day test "
                f"window.")
    else:
        preserved = last_tgt == dmax
        rule = "LEFT_BURN_IN_ONLY_NEWEST_PRESERVED" if preserved \
            else "LEFT_BURN_IN_ONLY_LAST_WINDOW_GAPPY"
        note = (f"{valid} of {len(origins)} sampled origins valid. Burn-in consumes the "
                f"{burn_rows} OLDEST observations only. "
                + ("Last target equals the series max date: no newest observation is discarded."
                   if preserved else
                   f"Last valid target {str(last_tgt)[:10]} falls short of the series max "
                   f"{str(dmax)[:10]} because the final {HORIZON}-day window is not "
                   f"daily-contiguous. This is a GAP effect, not tail trimming."))

    rows.append({
        "metric": m["metric"], "series_id": sid,
        "min_actual_date": str(dmin)[:10], "max_actual_date": str(dmax)[:10],
        "observation_count": n, "calendar_span_days": span, "missing_calendar_days": gaps,
        "proposed_burn_in_count": burn_rows,
        "burn_in_side": "OLDEST_ONLY",
        "sampled_origin_count": len(origins),
        "first_origin_date": str(first_origin)[:10],
        "last_origin_date": str(last_origin)[:10],
        "valid_origin_count": valid,
        "first_backtest_target_date": str(first_tgt)[:10] if first_tgt is not None else "NONE",
        "last_backtest_target_date": str(last_tgt)[:10] if last_tgt is not None else "NONE",
        "target_date_count": valid * HORIZON,
        "newest_observation_preserved": "TRUE" if (last_tgt == dmax) else "FALSE",
        "in_p5_workload": "FALSE" if m["metric"] == "HDD" else "TRUE",
        "rule": rule, "notes": note,
    })

F = list(rows[0].keys())
with (OUT / "v6_24_p5a_backtest_window_contract.csv").open("w", newline="",
                                                           encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=F)
    w.writeheader()
    w.writerows(rows)
print(f"v6_24_p5a_backtest_window_contract.csv|rows={len(rows)}")

df = pd.DataFrame(rows)
print("\n=== per metric ===")
for m, g in df.groupby("metric"):
    print(f"{m:<5} series={len(g):>3} obs {g['observation_count'].min()}-{g['observation_count'].max()} "
          f"span {g['calendar_span_days'].min()}-{g['calendar_span_days'].max()}d "
          f"gaps {g['missing_calendar_days'].min()}-{g['missing_calendar_days'].max()} "
          f"origins {g['valid_origin_count'].min()}-{g['valid_origin_count'].max()} "
          f"targets={int(g['target_date_count'].sum()):,}")

new = df[df["in_p5_workload"] == "TRUE"]
blocked = new[new["valid_origin_count"] == 0]
print(f"\nP5 workload series: {len(new)}")
print(f"  with zero valid origins: {len(blocked)}")
if len(blocked):
    print("  affected metrics:", blocked["metric"].value_counts().to_dict())
    print(blocked[["metric", "series_id", "observation_count", "calendar_span_days",
                   "missing_calendar_days"]].head(6).to_string(index=False))
print(f"  newest observation preserved: "
      f"{int((new['newest_observation_preserved'] == 'TRUE').sum())} of {len(new)}")
print(f"  total prediction rows if all run: "
      f"{int(new['target_date_count'].sum()) * 15:,} (targets x 15 models)")

json.dump({"per_series": rows}, (OUT / "_p5a_window.json").open("w", encoding="utf-8"),
          indent=1, default=str)
