"""
Stage 7 - TTL PROTOTYPE data generator (READ-ONLY on inputs).

Produces two SIMULATED artifacts that mirror the AEGIS/TESSERACT capacity views,
so the Shiny TTL page can show how our forecast improvements feed a Time-To-Live view.

  DEMAND  -> REAL (our forecasts.csv / actuals.csv, resource HDD)
  SUPPLY  -> SIMULATED (deterministic step series per series)
  TTL     -> DERIVED from the crossover of real demand vs simulated supply

Outputs (data/processed/):
  ttl_supply_demand_timeseries.csv   (series x month: demand, supply, utilization, crossover flag)
  ttl_months_to_live_snapshot.csv    (one row per series: months_to_live, crossover_date, ttl_status)

Nothing governed is touched; no champion logic is involved.
"""

from __future__ import annotations

import csv
import hashlib
import os
from datetime import date

import pandas as pd

# --- Paths (script lives in V1/python/shiny_mvp; project root is two levels up) ----
HERE = os.path.dirname(os.path.abspath(__file__))
V1_ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
PROC = os.path.join(V1_ROOT, "data", "processed")
OUT_DIR = os.path.join(V1_ROOT, "outputs", "shiny_mvp", "7_TTL_PROTOTYPE")

FORECASTS = os.path.join(PROC, "forecasts.csv")
ACTUALS = os.path.join(PROC, "actuals.csv")
ENTITIES = os.path.join(PROC, "entities.csv")

TS_OUT = os.path.join(PROC, "ttl_supply_demand_timeseries.csv")
SNAP_OUT = os.path.join(PROC, "ttl_months_to_live_snapshot.csv")

HISTORY_MONTHS = 0           # demand line = forward forecast only (actuals re-baseline late, different scale)
TTL_HORIZON_MONTHS = 60      # cap for "no crossover" search

# TTL color bands (Alert / Warning / Healthy / Cool) - prototype, tunable.
def ttl_status(mtl: float | None) -> str:
    if mtl is None:
        return "Cool"
    if mtl < 3:
        return "Alert"
    if mtl < 6:
        return "Warning"
    if mtl < 12:
        return "Healthy"
    return "Cool"


def split_entity(entity_key: str) -> tuple[str, str]:
    """APC-Dedicated -> ('APC', 'Dedicated'); NAM-ITAR DoD -> ('NAM', 'ITAR DoD')."""
    if "-" in entity_key:
        region, environment = entity_key.split("-", 1)
        return region.strip(), environment.strip()
    return entity_key.strip(), ""


def seeded_unit(entity_key: str, salt: str) -> float:
    """Deterministic float in [0, 1) from a stable hash of the series key."""
    h = hashlib.md5(f"{entity_key}|{salt}".encode("utf-8")).hexdigest()
    return int(h[:8], 16) / 0xFFFFFFFF


def month_floor(ts: pd.Timestamp) -> pd.Timestamp:
    return ts.normalize().replace(day=1)


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "logs"), exist_ok=True)

    fc = pd.read_csv(FORECASTS, parse_dates=["date"])
    ac = pd.read_csv(ACTUALS, parse_dates=["date"])
    ent = pd.read_csv(ENTITIES, parse_dates=[
        "first_actual_date", "last_actual_date",
        "first_forecast_date", "last_forecast_date",
    ])

    # Monthly real demand: forecast (future) and actuals (history), both real.
    fc["month_date"] = fc["date"].apply(month_floor)
    ac["month_date"] = ac["date"].apply(month_floor)
    fc_m = (fc.groupby(["entity_key", "resource", "month_date"], as_index=False)["forecast_value"]
              .mean().rename(columns={"forecast_value": "demand"}))
    ac_m = (ac.groupby(["entity_key", "resource", "month_date"], as_index=False)["actual_value"]
              .mean().rename(columns={"actual_value": "demand"}))

    ts_rows: list[dict] = []
    snap_rows: list[dict] = []

    for _, e in ent.iterrows():
        ekey = e["entity_key"]
        region, environment = split_entity(ekey)
        snap_month = month_floor(e["last_actual_date"])
        resource = "HDD"

        # Real demand series: last HISTORY_MONTHS of actuals + full forecast horizon.
        hist = ac_m[(ac_m["entity_key"] == ekey) & (ac_m["month_date"] <= snap_month)].copy()
        hist = hist.sort_values("month_date").tail(HISTORY_MONTHS)
        fut = fc_m[(fc_m["entity_key"] == ekey) & (fc_m["month_date"] > snap_month)].copy()
        fut = fut.sort_values("month_date")
        demand_series = pd.concat([hist, fut], ignore_index=True)
        if demand_series.empty:
            continue
        demand_series = demand_series.drop_duplicates("month_date").sort_values("month_date")

        # "today" demand = first forecast month (or last available).
        future_only = demand_series[demand_series["month_date"] > snap_month]
        demand_now = float(future_only["demand"].iloc[0]) if not future_only.empty \
            else float(demand_series["demand"].iloc[-1])

        # --- Real demand as ordered arrays (months_from_snap, value) ----------
        dmonths = [
            (m.year - snap_month.year) * 12 + (m.month - snap_month.month)
            for m in demand_series["month_date"]
        ]
        dvals = [float(v) for v in demand_series["demand"]]
        n = len(dvals)

        # Average monthly demand growth from the REAL forecast.
        growths = [dvals[i] / dvals[i - 1] - 1.0
                   for i in range(1, n) if dvals[i - 1] > 0]
        g_d = sum(growths) / len(growths) if growths else 0.0
        g_d_pos = max(g_d, 0.0)

        # --- SIMULATED supply: a STAIRCASE that STARTS ABOVE demand -----------
        # Three logic rules (prototype, deterministic):
        #   1) Headroom => supply > demand at the first month, so any crossover
        #      is always a FUTURE point (to the right), never at t0.
        #   2) Supply grows in visible STEPS (staircase) for EVERY series, like
        #      the AEGIS capacity view (provision capacity in discrete blocks).
        #   3) The supply staircase grows SLOWER than demand, so the demand
        #      curve catches it near a per-series target month (spreads bands).
        step_every = 2                                           # months per step

        # Gentle, ALWAYS-rising supply staircase (so it is visibly stepped, never
        # flat) that still grows slower than demand.
        g_s = max(0.003, g_d_pos * 0.25)
        delta = g_d - g_s                                        # demand net catch-up/mo

        # Per-series target crossover month -> well-spread TTL bands; ~18% Cool.
        # Floor of 4 months keeps every crossover a clear FUTURE point (to the
        # right) with a visible supply staircase before it.
        ttl_seed = seeded_unit(ekey, "ttl")
        if ttl_seed < 0.18:
            target_T = None                                      # Cool: no crossover
        else:
            target_T = 4 + ((ttl_seed - 0.18) / 0.82) * 22       # 4 .. 26 months

        if target_T is None or delta <= 0.0005:
            # Supply keeps up with demand -> no crossover (Cool). Keep a clear,
            # maintained gap and let supply outpace demand.
            target_T = None
            headroom = 0.12 + 0.20 * seeded_unit(ekey, "headroom")   # 12% .. 32%
            g_s = g_d_pos * 1.10 + 0.004                              # outpaces
        else:
            # Headroom chosen so demand erodes it by ~target_T months
            # (t_cross ~= headroom / delta).
            headroom = max(0.05, min(0.45, target_T * delta))

        step_pct = (1.0 + g_s) ** step_every - 1.0               # per-step jump
        supply_base = demand_now * (1.0 + headroom)              # starts above demand
        supply_vals: list[float] = []
        current = supply_base
        for i in range(n):
            if i > 0 and i % step_every == 0:
                current = current * (1.0 + step_pct)
            supply_vals.append(current)

        # --- Crossover: first FUTURE month where demand reaches supply --------
        crossover_date = None
        months_to_live = None
        cross_i = None
        for i in range(n):
            if dvals[i] >= supply_vals[i]:
                cross_i = i
                crossover_date = demand_series["month_date"].iloc[i]
                months_to_live = float(dmonths[i])
                break

        # --- Emit the monthly timeseries rows ---------------------------------
        for i in range(n):
            mdate = demand_series["month_date"].iloc[i]
            dval = dvals[i]
            sval = supply_vals[i]
            util = dval / sval * 100.0 if sval > 0 else None
            gf = (dvals[i] / dvals[i - 1] - 1.0) if i > 0 and dvals[i - 1] > 0 else None
            ts_rows.append({
                "entity_key": ekey,
                "region": region,
                "environment": environment,
                "resource": resource,
                "month_date": mdate.date().isoformat(),
                "demand": round(dval, 4),
                "supply": round(sval, 4),
                "utilization_pct": round(util, 2) if util is not None else "",
                "growth_factor": round(gf, 6) if gf is not None else "",
                "is_crossover_month": "TRUE" if i == cross_i else "FALSE",
                "data_origin": "demand=forecast_real;supply=simulated",
            })

        monthly_growth_rate = g_d
        supply_now = supply_vals[0]
        status = ttl_status(months_to_live)

        snap_rows.append({
            "entity_key": ekey,
            "region": region,
            "environment": environment,
            "resource": resource,
            "snapshot_date": snap_month.date().isoformat(),
            "supply_now": round(supply_now, 4),
            "demand_now": round(demand_now, 4),
            "utilization_pct": round(demand_now / supply_now * 100.0, 2) if supply_now > 0 else "",
            "monthly_growth_rate": round(monthly_growth_rate, 6),
            "months_to_live": round(months_to_live, 2) if months_to_live is not None else "",
            "crossover_date": crossover_date.date().isoformat() if crossover_date is not None else "",
            "ttl_status": status,
            "constraining_resource_name": resource,
            "data_origin": "demand=forecast_real;supply+ttl=simulated",
        })

    ts_df = pd.DataFrame(ts_rows)
    snap_df = pd.DataFrame(snap_rows)
    ts_df.to_csv(TS_OUT, index=False, quoting=csv.QUOTE_MINIMAL)
    snap_df.to_csv(SNAP_OUT, index=False, quoting=csv.QUOTE_MINIMAL)

    # --- Validation / report ---------------------------------------------------
    band_counts = snap_df["ttl_status"].value_counts().to_dict()
    report = [
        f"TTL PROTOTYPE generated {date.today().isoformat()}",
        f"series: {snap_df['entity_key'].nunique()}  timeseries_rows: {len(ts_df)}  snapshot_rows: {len(snap_df)}",
        f"resource: HDD (only resource in forecasts.csv)",
        f"TTL bands: {band_counts}",
        f"with_crossover: {(snap_df['crossover_date'] != '').sum()}  no_crossover(Cool): {(snap_df['crossover_date'] == '').sum()}",
        f"DEMAND=real forecast/actuals; SUPPLY+TTL=simulated (deterministic).",
        f"outputs: {TS_OUT}",
        f"         {SNAP_OUT}",
    ]
    with open(os.path.join(OUT_DIR, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
