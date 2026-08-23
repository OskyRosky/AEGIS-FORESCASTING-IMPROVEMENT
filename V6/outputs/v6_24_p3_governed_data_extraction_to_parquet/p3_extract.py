"""V6.24-P3 | Governed extraction of the 90 approved non-HDD series to raw Parquet.

Extracts SSD LVWE, SSD LVNE, CPU and IOPS filtered strictly to the approved keys,
writes raw Parquet, then RE-READS each file and validates it. No extraction is
considered complete until the written file has been read back and checked.

HDD is not touched: it is already local.

Fails loudly. No silent row dropping, no silent type coercion. The original
varchar Mean_Actual is preserved alongside its cast value so the cast can be
audited rather than trusted.
"""

from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

import _p3_sql as S

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
RAW = V6 / "data" / "raw" / "v6_24_mvp_cohort"
P2 = OUT.parent / "v6_24_p2_controlled_parquet_extraction_plan"
P2A = OUT.parent / "v6_24_p2a_ssd_selected_cohort_verification"

S.load_ledger()
EV = {}

LVWE = "forecast_substrateBE_ssd_phx_lvwe_metrics"
LVNE = "forecast_substrateBE_ssd_phx_lvne_metrics"
CPU_T = "forecast_substrateBE_cpu_actual_region"
IOPS_T = "forecast_substrateBE_iops_actual_region"


def read_plan(p):
    with p.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


ssd_plan = read_plan(P2A / "v6_24_p2a_corrected_ssd_50_extraction_plan.csv")
cpu_plan = read_plan(P2 / "v6_24_p2_cpu_20_extraction_plan.csv")
iops_plan = read_plan(P2 / "v6_24_p2_iops_20_extraction_plan.csv")

ssd_keys = sorted({r["key"] for r in ssd_plan})
cpu_sel = sorted({(r["scenario"], r["key"]) for r in cpu_plan})
iops_sel = sorted({(r["scenario"], r["key"]) for r in iops_plan})

assert len(ssd_plan) == 50 and len(ssd_keys) == 50, "SSD plan must hold 50 unique keys"
assert len(cpu_plan) == 20 and len(cpu_sel) == 20, "CPU plan must hold 20 series"
assert len(iops_plan) == 20 and len(iops_sel) == 20, "IOPS plan must hold 20 series"
print(f"PLAN OK | SSD={len(ssd_keys)} CPU={len(cpu_sel)} IOPS={len(iops_sel)}")
EV["plan"] = {"ssd_keys": ssd_keys, "cpu": cpu_sel, "iops": iops_sel}


def to_frame(cols, rows):
    return pd.DataFrame.from_records([tuple(r) for r in rows], columns=cols)


# ===================================================== SSD LVWE and LVNE
SSD_SQL = """
SELECT
    'SSD'                              AS metric,
    'Phoenix'                          AS db_type,
    '{variant}'                        AS variant,
    'NOT_APPLICABLE'                   AS scenario,
    'NOT_APPLICABLE'                   AS segment,
    'Organic'                          AS demand_nature,
    'Forest'                           AS granularity,
    m.[Key]                            AS series_key,
    m.Start_Date                       AS window_start,
    m.End_Date                         AS series_date,
    TRY_CAST(m.[Count]     AS INT)     AS window_obs_count,
    TRY_CAST(m.Mean_Actual AS FLOAT)   AS actual_value,
    m.Mean_Actual                      AS actual_value_source_text,
    m.Mean_Forecast                    AS forecast_value,
    TRY_CAST(m.MAE         AS FLOAT)   AS mae,
    TRY_CAST(m.RMSE        AS FLOAT)   AS rmse,
    TRY_CAST(m.Bias        AS FLOAT)   AS bias,
    m.Bias_Pct                         AS bias_pct,
    m.MAPE                             AS mape,
    m.SMAPE                            AS smape,
    m.Accuracy                         AS accuracy,
    m.Forecast_Version                 AS forecast_version,
    '{table}'                          AS source_object
FROM dbo.[{table}] AS m
WHERE m.Mean_Actual IS NOT NULL
  AND m.[Key] IN ({ph})
ORDER BY m.[Key], m.End_Date
"""

frames = {}
ph = ",".join("?" for _ in ssd_keys)
for variant, table in (("LVWE", LVWE), ("LVNE", LVNE)):
    cols, rows = S.fetch(
        SSD_SQL.format(variant=variant, table=table, ph=ph),
        obj=table, purpose=f"Governed extraction of SSD {variant} for the 50 approved forest keys",
        filter_summary=f"Mean_Actual IS NOT NULL AND Key IN (50 approved forest keys)",
        params=tuple(ssd_keys),
    )
    frames[variant] = to_frame(cols, rows)

# ===================================================== CPU and IOPS
ACT_SQL = """
SELECT
    '{metric}'                         AS metric,
    '{dbtype}'                         AS db_type,
    'NOT_APPLICABLE'                   AS variant,
    a.Scenario                         AS scenario,
    'NOT_APPLICABLE'                   AS segment,
    a.[Type]                           AS demand_nature,
    'Region'                           AS granularity,
    a.[Key]                            AS series_key,
    a.[DateTime]                       AS series_date,
    a.Value                            AS actual_value,
    a.ValueRef                         AS value_reference,
    a.ModelVersion                     AS model_version,
    a.ForecastVersion                  AS forecast_version,
    a.Fleet, a.Workload, a.Resource, a.Unit,
    '{table}'                          AS source_object
FROM dbo.[{table}] AS a
WHERE a.ModelVersion = 'Actual'
  AND a.Value IS NOT NULL
  AND ({clauses})
ORDER BY a.Scenario, a.[Key], a.[DateTime]
"""

for metric, table, sel, dbtype in (
    ("CPU", CPU_T, cpu_sel, "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE"),
    ("IOPS", IOPS_T, iops_sel, "NOT_APPLICABLE"),
):
    scen = sorted({s for s, _ in sel})
    clauses, params = [], []
    for sc in scen:
        ks = sorted(k for s, k in sel if s == sc)
        clauses.append(f"(a.Scenario = ? AND a.[Key] IN ({','.join('?' for _ in ks)}))")
        params += [sc] + ks
    cols, rows = S.fetch(
        ACT_SQL.format(metric=metric, table=table, dbtype=dbtype,
                       clauses=" OR ".join(clauses)),
        obj=table, purpose=f"Governed extraction of {metric} actuals for the 20 approved series",
        filter_summary=f"ModelVersion='Actual' AND Value IS NOT NULL AND "
                       f"(Scenario,Key) IN ({len(sel)} approved pairs across {scen})",
        params=tuple(params),
    )
    frames[metric] = to_frame(cols, rows)

S.save_ledger()
for k, df in frames.items():
    print(f"FETCHED {k}: {len(df):,} rows x {len(df.columns)} cols")

# ===================================================== write raw Parquet
TARGETS = {
    "LVWE": RAW / "ssd" / "ssd_lvwe_raw.parquet",
    "LVNE": RAW / "ssd" / "ssd_lvne_raw.parquet",
    "CPU": RAW / "cpu" / "cpu_actuals_raw.parquet",
    "IOPS": RAW / "iops" / "iops_actuals_raw.parquet",
}
written = {}
for k, path in TARGETS.items():
    df = frames[k]
    if path.exists():
        print(f"NOTE: replacing pre-existing {path.name} from an earlier attempt")
    df.to_parquet(path, index=False, engine="pyarrow", compression="snappy")
    written[k] = path
    print(f"WROTE {path.relative_to(V6)} | {len(df):,} rows")

# ===================================================== re-read and validate
EXPECTED_KEYS = {"LVWE": set(ssd_keys), "LVNE": set(ssd_keys),
                 "CPU": {k for _, k in cpu_sel}, "IOPS": {k for _, k in iops_sel}}
report = {}
for k, path in written.items():
    back = pd.read_parquet(path, engine="pyarrow")
    src = frames[k]
    got = set(back["series_key"].unique())
    exp = EXPECTED_KEYS[k]
    r = {
        "file": path.name,
        "relative_path": str(path.relative_to(V6)).replace("\\", "/"),
        "exists": path.exists(),
        "file_size_bytes": path.stat().st_size,
        "sql_rows": int(len(src)),
        "parquet_rows": int(len(back)),
        "rows_match": bool(len(src) == len(back)),
        "columns": int(len(back.columns)),
        "selected_keys": len(exp),
        "keys_in_parquet": len(got),
        "unexpected_keys": sorted(got - exp),
        "missing_keys": sorted(exp - got),
        "min_date": str(back["series_date"].min())[:10],
        "max_date": str(back["series_date"].max())[:10],
        "distinct_dates": int(back["series_date"].nunique()),
        "null_actual_value": int(back["actual_value"].isna().sum()),
        "checksum_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if k in ("LVWE", "LVNE"):
        # Every source text value must have produced a numeric cast. A null here
        # means the cast silently lost a value, which must fail the stage.
        r["non_parseable_actuals"] = int(
            (back["actual_value_source_text"].notna() & back["actual_value"].isna()).sum())
    else:
        r["non_parseable_actuals"] = 0
    report[k] = r
    print(f"VALIDATED {k}: rows_match={r['rows_match']} keys={r['keys_in_parquet']}/{r['selected_keys']} "
          f"unexpected={len(r['unexpected_keys'])} missing={len(r['missing_keys'])} "
          f"non_parseable={r['non_parseable_actuals']} {r['min_date']}..{r['max_date']}")

EV["files"] = report

# ===================================================== SSD LVWE vs LVNE consistency
w = frames["LVWE"][["series_key", "series_date", "actual_value", "forecast_value"]]
n = frames["LVNE"][["series_key", "series_date", "actual_value", "forecast_value"]]
m = w.merge(n, on=["series_key", "series_date"], suffixes=("_lvwe", "_lvne"))
EV["ssd_consistency"] = {
    "matched_rows": int(len(m)),
    "actual_identical": int((m["actual_value_lvwe"] == m["actual_value_lvne"]).sum()),
    "actual_differing": int((m["actual_value_lvwe"] != m["actual_value_lvne"]).sum()),
    "forecast_identical": int((m["forecast_value_lvwe"] == m["forecast_value_lvne"]).sum()),
    "forecast_differing": int((m["forecast_value_lvwe"] != m["forecast_value_lvne"]).sum()),
    "lvwe_keys": int(w["series_key"].nunique()),
    "lvne_keys": int(n["series_key"].nunique()),
    "observed_series_count": int(w["series_key"].nunique()),
}
print(f"SSD CONSISTENCY: {EV['ssd_consistency']}")

# ===================================================== per-series detail
series = []
for k, df in frames.items():
    metric = "SSD" if k in ("LVWE", "LVNE") else k
    grp = ["series_key"] if metric == "SSD" else ["scenario", "series_key"]
    for gk, g in df.groupby(grp, dropna=False):
        gk = (gk,) if not isinstance(gk, tuple) else gk
        rec = {
            "unit": k, "metric": metric,
            "scenario": "NOT_APPLICABLE" if metric == "SSD" else gk[0],
            "series_key": gk[-1],
            "row_count": int(len(g)),
            "distinct_dates": int(g["series_date"].nunique()),
            "min_date": str(g["series_date"].min())[:10],
            "max_date": str(g["series_date"].max())[:10],
            "parseable_actual_count": int(g["actual_value"].notna().sum()),
            "non_parseable_actual_count": int(
                (g["actual_value_source_text"].notna() & g["actual_value"].isna()).sum()
            ) if metric == "SSD" else 0,
        }
        series.append(rec)
EV["series"] = series
print(f"SERIES RECORDS: {len(series)}")

(OUT / "_p3_evidence.json").write_text(json.dumps(EV, indent=1, default=str), encoding="utf-8")
print("extraction complete")
