"""V6.24-P3 | Data quality probe on the written raw Parquet.

Two anomalies surfaced during validation and must be measured, not glossed over:

1. The LVWE/LVNE merge produced 6,650 rows from 6,550 and 6,600 row inputs,
   which is only possible if (series_key, series_date) is not unique.
2. CPU and IOPS reported 10 distinct keys for 20 selected series, implying the
   same keys are reused across both scenarios.

No SQL. Reads only the Parquet files already written.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"

FILES = {
    "LVWE": RAW / "ssd" / "ssd_lvwe_raw.parquet",
    "LVNE": RAW / "ssd" / "ssd_lvne_raw.parquet",
    "CPU": RAW / "cpu" / "cpu_actuals_raw.parquet",
    "IOPS": RAW / "iops" / "iops_actuals_raw.parquet",
}
Q = {}

for tag, path in FILES.items():
    df = pd.read_parquet(path, engine="pyarrow")
    grain = (["series_key", "series_date"] if tag in ("LVWE", "LVNE")
             else ["scenario", "series_key", "series_date"])
    dup = df.duplicated(subset=grain, keep=False)
    ndup = int(dup.sum())
    Q[tag] = {
        "rows": int(len(df)),
        "grain": "+".join(grain),
        "duplicate_grain_rows": ndup,
        "distinct_grain": int(df[grain].drop_duplicates().shape[0]),
        "distinct_keys": int(df["series_key"].nunique()),
        "distinct_scenarios": sorted(df["scenario"].unique().tolist()),
        "series_count": int(df[["scenario", "series_key"]].drop_duplicates().shape[0]),
    }
    print(f"\n=== {tag} ===")
    print(f"  rows={Q[tag]['rows']:,} grain={Q[tag]['grain']} "
          f"distinct_grain={Q[tag]['distinct_grain']:,} duplicate_rows={ndup:,}")
    print(f"  distinct_keys={Q[tag]['distinct_keys']} "
          f"scenarios={Q[tag]['distinct_scenarios']} series={Q[tag]['series_count']}")

    if ndup:
        d = df[dup].sort_values(grain)
        ex = d.head(4)
        cols = [c for c in ("series_key", "window_start", "series_date", "window_obs_count",
                            "actual_value", "forecast_value", "forecast_version",
                            "scenario", "model_version") if c in ex.columns]
        print(f"  --- example duplicate rows ---")
        for _, r in ex[cols].iterrows():
            print("    " + " | ".join(f"{c}={r[c]}" for c in cols))
        # Do duplicated rows carry identical measures, or genuinely different ones?
        val = "actual_value"
        agg = d.groupby(grain)[val].nunique()
        Q[tag]["dup_groups"] = int(len(agg))
        Q[tag]["dup_groups_with_same_value"] = int((agg == 1).sum())
        Q[tag]["dup_groups_with_different_value"] = int((agg > 1).sum())
        print(f"  duplicate groups={len(agg)} "
              f"same_{val}={int((agg == 1).sum())} different_{val}={int((agg > 1).sum())}")
        if "window_start" in df.columns:
            ws = d.groupby(grain)["window_start"].nunique()
            Q[tag]["dup_groups_with_different_window_start"] = int((ws > 1).sum())
            print(f"  duplicate groups with a different window_start={int((ws > 1).sum())}")

# Per-key row and date profile for SSD
for tag in ("LVWE", "LVNE"):
    df = pd.read_parquet(FILES[tag], engine="pyarrow")
    g = df.groupby("series_key").agg(rows=("series_date", "size"),
                                     dates=("series_date", "nunique"))
    Q[tag]["rows_per_key"] = [int(g["rows"].min()), int(g["rows"].max())]
    Q[tag]["dates_per_key"] = [int(g["dates"].min()), int(g["dates"].max())]
    Q[tag]["keys_with_rows_gt_dates"] = int((g["rows"] > g["dates"]).sum())
    print(f"\n{tag} per-key: rows {Q[tag]['rows_per_key']} dates {Q[tag]['dates_per_key']} "
          f"keys_where_rows_exceed_dates={Q[tag]['keys_with_rows_gt_dates']}")

# CPU / IOPS scenario x key structure
for tag in ("CPU", "IOPS"):
    df = pd.read_parquet(FILES[tag], engine="pyarrow")
    pairs = df[["scenario", "series_key"]].drop_duplicates()
    per = pairs.groupby("series_key").size()
    Q[tag]["keys_in_both_scenarios"] = int((per == 2).sum())
    Q[tag]["keys_in_one_scenario"] = int((per == 1).sum())
    print(f"\n{tag}: {len(pairs)} series over {pairs['series_key'].nunique()} keys | "
          f"keys in both scenarios={Q[tag]['keys_in_both_scenarios']}, "
          f"in one only={Q[tag]['keys_in_one_scenario']}")

(OUT / "_p3_quality.json").write_text(json.dumps(Q, indent=1, default=str), encoding="utf-8")
print("\nquality probe complete")
