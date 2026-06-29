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
import math
import os
from datetime import date, timedelta

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

# Resources to emit. The multi-resource structure is READY; only HDD has real
# forecast data today, so the list holds a single resource for now. Add
# "CPU"/"SSD"/"IOPS" here (with a supply/demand simulator) to light up the
# binding-constraint logic WITHOUT touching the rest of the pipeline.
RESOURCES = ["HDD"]

# eTTL dotted-projection cap (months past the forecast horizon) so projections
# stay readable on the chart.
ETTL_PROJECTION_CAP_MONTHS = 36

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


def compute_resource_ttl(
    ekey, resource, region, environment, today_date,
    dates, dvals, dmonths, demand_now, growth_per_month, demand_at,
):
    """TTL for one (forest x resource) using the official two-method model.

    Method 1 (Intersection): flat point-in-time supply; first month demand
    reaches it; TTL = days-to-intersection / 30 via linear interpolation.
    Method 2 (eTTL): when no crossing in the horizon, extrapolate linearly from
    the forecast growth rate -> eTTL = (Supply - Demand_now) / GrowthPerMonth.

    Returns a dict: {resource, ttl_months, snapshot, timeseries}.
    """
    n = len(dvals)
    last_off = dmonths[-1]
    seed = seeded_unit(f"{ekey}|{resource}", "ttl")

    # Average monthly demand growth (kept for the KPI / reference).
    growths = [dvals[i] / dvals[i - 1] - 1.0
               for i in range(1, n) if dvals[i - 1] > 0]
    monthly_growth_rate = sum(growths) / len(growths) if growths else 0.0

    supply = None
    method = None
    ttl_months = None
    crossing_date = None
    cross_i = None
    proj_meta: list[tuple] = []   # (month_date, projected_demand) for eTTL

    if seed < 0.18:
        # ---- Method 2: eTTL (ample headroom, no crossing in horizon) --------
        method = "eTTL"
        gpm = growth_per_month
        if gpm <= 1e-9:
            # Demand flat/declining -> no capacity pressure (unbounded TTL).
            headroom = 0.12 + 0.20 * seeded_unit(f"{ekey}|{resource}", "headroom")
            supply = demand_now * (1.0 + headroom)
            ttl_months = None
        else:
            # Target eTTL beyond the forecast horizon, spread for variety.
            target_ettl = last_off + 6 + seeded_unit(f"{ekey}|{resource}", "ettl") \
                * (ETTL_PROJECTION_CAP_MONTHS - 6)
            supply = demand_now + gpm * target_ettl
            ttl_months = (supply - demand_now) / gpm          # doc formula
            crossing_date = today_date + timedelta(days=ttl_months * 30.0)
            # Dotted projection along the idealized demand_now + gpm*k line.
            kmax = min(int(math.ceil(ttl_months)), last_off + ETTL_PROJECTION_CAP_MONTHS)
            for k in range(last_off + 1, kmax + 1):
                val = demand_now + gpm * k
                md = month_floor(today_date + pd.DateOffset(months=k))
                proj_meta.append((md, val))
    else:
        # ---- Method 1: Forecast Intersection (flat supply) ------------------
        method = "intersection"
        norm = (seed - 0.18) / 0.82
        target_T = 2.0 + norm * 28.0                           # 2 .. 30 months
        target_T = min(target_T, max(2.0, last_off - 1))
        supply = demand_at(target_T)                          # flat supply = demand level at target
        for i in range(1, n):
            if dvals[i] >= supply:
                cross_i = i
                break
        if cross_i is None:
            # Never reaches supply within the horizon -> fall back to eTTL-cool.
            method = "eTTL"
            ttl_months = None
        else:
            d0, d1 = dvals[cross_i - 1], dvals[cross_i]
            f = (supply - d0) / (d1 - d0) if d1 > d0 else 0.0
            t0, t1 = dates[cross_i - 1], dates[cross_i]
            span_days = (t1 - t0).days
            crossing_date = t0 + timedelta(days=f * span_days)
            ttl_months = (crossing_date - today_date).days / 30.0

    status = ttl_status(ttl_months)
    util_now = demand_now / supply if supply and supply > 0 else None

    # ---- Timeseries: real forecast months (flat supply) ---------------------
    ts: list[dict] = []
    for i in range(n):
        dval = dvals[i]
        util = dval / supply if supply and supply > 0 else None
        gf = (dvals[i] / dvals[i - 1] - 1.0) if i > 0 and dvals[i - 1] > 0 else None
        is_cross = (method == "intersection" and i == cross_i)
        ts.append({
            "entity_key": ekey, "region": region, "environment": environment,
            "resource": resource,
            "month_date": dates[i].date().isoformat(),
            "demand": round(dval, 4), "supply": round(supply, 4),
            "utilization_pct": round(util * 100.0, 2) if util is not None else "",
            "utilization": round(util, 4) if util is not None else "",
            "growth_factor": round(gf, 6) if gf is not None else "",
            "is_crossover_month": "TRUE" if is_cross else "FALSE",
            "is_crossover": "TRUE" if is_cross else "FALSE",
            "is_projection": "FALSE",
            "data_origin": "demand=forecast_real;supply=simulated_flat",
        })

    # ---- Timeseries: eTTL dotted projection beyond the horizon ---------------
    crossed = False
    for (md, val) in proj_meta:
        util = val / supply if supply and supply > 0 else None
        is_cross = (not crossed and supply is not None and val >= supply)
        if is_cross:
            crossed = True
        ts.append({
            "entity_key": ekey, "region": region, "environment": environment,
            "resource": resource,
            "month_date": md.date().isoformat(),
            "demand": round(val, 4), "supply": round(supply, 4),
            "utilization_pct": round(util * 100.0, 2) if util is not None else "",
            "utilization": round(util, 4) if util is not None else "",
            "growth_factor": "",
            "is_crossover_month": "TRUE" if is_cross else "FALSE",
            "is_crossover": "TRUE" if is_cross else "FALSE",
            "is_projection": "TRUE",
            "data_origin": "demand=eTTL_projection;supply=simulated_flat",
        })

    status_comment = (
        "No capacity pressure (demand flat/declining)" if ttl_months is None
        else f"Baseline TTL: {ttl_months:.2f} mo ({method})"
    )

    snapshot = {
        "entity_key": ekey, "region": region, "environment": environment,
        "resource": resource,
        "snapshot_date": today_date.date().isoformat(),
        "supply_date": today_date.date().isoformat(),
        "supply_now": round(supply, 4), "supply": round(supply, 4),
        "demand_now": round(demand_now, 4),
        "utilization_pct": round(util_now * 100.0, 2) if util_now is not None else "",
        "utilization": round(util_now, 4) if util_now is not None else "",
        "monthly_growth_rate": round(monthly_growth_rate, 6),
        "growth_per_month": round(growth_per_month, 6),
        "months_to_live": round(ttl_months, 2) if ttl_months is not None else "",
        "ttl_months": round(ttl_months, 2) if ttl_months is not None else "",
        "crossover_date": crossing_date.date().isoformat() if crossing_date is not None else "",
        "intersection_date": crossing_date.date().isoformat() if crossing_date is not None else "",
        "method": method,
        "ttl_status": status,
        "status_comment": status_comment,
        "data_origin": f"demand=forecast_real;supply+ttl=simulated;flat_supply;method={method}",
    }

    return {"resource": resource, "ttl_months": ttl_months,
            "snapshot": snapshot, "timeseries": ts}


def main() -> None:
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(os.path.join(OUT_DIR, "logs"), exist_ok=True)

    fc = pd.read_csv(FORECASTS, parse_dates=["date"])
    ent = pd.read_csv(ENTITIES, parse_dates=[
        "first_actual_date", "last_actual_date",
        "first_forecast_date", "last_forecast_date",
    ])

    # Monthly real demand from the FORECAST (future only; supply is point-in-time).
    fc["month_date"] = fc["date"].apply(month_floor)
    fc_m = (fc.groupby(["entity_key", "resource", "month_date"], as_index=False)["forecast_value"]
              .mean().rename(columns={"forecast_value": "demand"}))

    ts_rows: list[dict] = []
    snap_rows: list[dict] = []

    for _, e in ent.iterrows():
        ekey = e["entity_key"]
        region, environment = split_entity(ekey)
        snap_month = month_floor(e["last_actual_date"])

        # Forward forecast demand (real) from the first month after the snapshot.
        fut = fc_m[(fc_m["entity_key"] == ekey) & (fc_m["month_date"] > snap_month)].copy()
        fut = fut.sort_values("month_date").drop_duplicates("month_date")
        if fut.empty:
            continue

        dates = list(fut["month_date"])
        dvals = [float(v) for v in fut["demand"]]
        today_date = dates[0]                  # "today" = first forecast month
        demand_now = dvals[0]
        n = len(dvals)
        dmonths = [(d.year - today_date.year) * 12 + (d.month - today_date.month)
                   for d in dates]
        last_off = dmonths[-1]

        def demand_at(t: float) -> float:
            """Linear interpolation of demand at a (fractional) month offset."""
            if t <= dmonths[0]:
                return dvals[0]
            if t >= dmonths[-1]:
                return dvals[-1]
            for j in range(1, n):
                if dmonths[j] >= t:
                    f = (t - dmonths[j - 1]) / (dmonths[j] - dmonths[j - 1])
                    return dvals[j - 1] + f * (dvals[j] - dvals[j - 1])
            return dvals[-1]

        # GrowthPerMonth from the FORECAST itself (doc Method 2).
        g_off = min(12, last_off) if last_off > 0 else 1
        growth_per_month = (demand_at(g_off) - demand_now) / g_off if g_off > 0 else 0.0

        # Per-resource TTL (multi-resource ready; HDD real only today).
        results = [
            compute_resource_ttl(
                ekey, resource, region, environment, today_date,
                dates, dvals, dmonths, demand_now, growth_per_month, demand_at,
            )
            for resource in RESOURCES
        ]

        # Binding constraint = resource with the SMALLEST TTL (None -> +inf).
        def _ttl_key(r):
            return r["ttl_months"] if r["ttl_months"] is not None else float("inf")
        binding_name = min(results, key=_ttl_key)["resource"]

        for r in results:
            snap = r["snapshot"]
            snap["is_binding"] = "TRUE" if r["resource"] == binding_name else "FALSE"
            snap["constraining_resource_name"] = binding_name
            snap_rows.append(snap)
            ts_rows.extend(r["timeseries"])

    ts_df = pd.DataFrame(ts_rows)
    snap_df = pd.DataFrame(snap_rows)
    ts_df.to_csv(TS_OUT, index=False, quoting=csv.QUOTE_MINIMAL)
    snap_df.to_csv(SNAP_OUT, index=False, quoting=csv.QUOTE_MINIMAL)

    # --- Validation / report ---------------------------------------------------
    band_counts = snap_df["ttl_status"].value_counts().to_dict()
    method_counts = snap_df["method"].value_counts().to_dict()
    report = [
        f"TTL PROTOTYPE generated {date.today().isoformat()}",
        f"series: {snap_df['entity_key'].nunique()}  resources: {len(RESOURCES)}  "
        f"snapshot_rows: {len(snap_df)}  timeseries_rows: {len(ts_df)}",
        f"resources: {RESOURCES}  (multi-resource structure ready; HDD real only)",
        f"supply model: FLAT point-in-time (today); methods: intersection + eTTL",
        f"TTL bands: {band_counts}",
        f"methods: {method_counts}",
        f"no-TTL (no pressure): {(snap_df['months_to_live'] == '').sum()}",
        f"projection rows: {(ts_df['is_projection'] == 'TRUE').sum()}",
        f"DEMAND=real forecast; SUPPLY+TTL=simulated (deterministic, flat).",
        f"outputs: {TS_OUT}",
        f"         {SNAP_OUT}",
    ]
    with open(os.path.join(OUT_DIR, "report.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(report) + "\n")
    print("\n".join(report))


if __name__ == "__main__":
    main()
