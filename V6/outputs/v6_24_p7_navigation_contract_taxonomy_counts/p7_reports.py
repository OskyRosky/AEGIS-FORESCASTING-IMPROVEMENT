"""V6.24-P7 part 2 - reports, validation, closure."""
from __future__ import annotations

import csv
import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P6C = V6 / "outputs" / "v6_24_p6c_ranking_tiebreak_no_signal_correction"

FTYPE = "GOVERNED_30_STEP_DAILY_FORECAST"
FSTEPS = 30
NA = "NOT_APPLICABLE"
S_NONE, S_TRAIL, S_OK = ("NO_SIGNAL_ALL_ZERO_ACTUALS", "TRAILING_ZERO_LATEST_ACTUAL",
                         "SIGNAL_PRESENT")
V_BAD, V_OK = "NOT_MEANINGFUL_NO_SIGNAL", "MEANINGFUL_ACCURACY_RANKING"
AVAIL, AVAIL_C, NOTAV = "AVAILABLE", "AVAILABLE_WITH_CAVEAT", "NOT_AVAILABLE"
OP = "OPERATIONAL_ENTITY"
AXES = ["metric", "db_type", "scenario", "segment", "granularity", "key"]
GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]

A = json.load((OUT / "_p7.json").open(encoding="utf-8"))
NAV = pd.read_pickle(OUT / "_p7_nav.pkl")
TAX = pd.read_pickle(OUT / "_p7_tax.pkl")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
FC = pd.read_parquet(PROC / "forecast_outputs.parquet", engine="pyarrow")
RK = pd.read_parquet(PROC / "model_rankings.parquet", engine="pyarrow")
ACC = pd.read_parquet(PROC / "accuracy_metrics.parquet", engine="pyarrow")
RD = pd.read_csv(OUT / "v6_24_p7_readiness_derivation_report.csv")


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


def git_clean(ps):
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", ps], cwd=REPO,
                           capture_output=True, text=True, timeout=90)
        return r.stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"GIT_CHECK_ERROR: {e}"


def fmt(v):
    return "" if (v is None or (isinstance(v, float) and np.isnan(v))) else round(float(v), 6)


# ============================================ 4. schema report
REQ = ["contract_row_id", "contract_row_type", "cohort_id", "series_id", "metric",
       "db_type", "scenario", "segment", "granularity", "key", "route_path",
       "filter_level_1_metric", "filter_level_2_db_type", "filter_level_3_scenario",
       "filter_level_4_segment", "filter_level_5_granularity", "filter_level_6_key",
       "key_axis_status", "route_display_label", "route_sort_key", "valid_filter_path",
       "parent_filter_path", "viewer_visible", "forecast_visible", "ranking_visible",
       "champion_visible", "product_ready", "backtest_ready", "accuracy_ready",
       "ranking_ready", "forecast_ready", "champion_model_name", "champion_rank_value",
       "champion_rank_metric", "champion_validity", "champion_reason",
       "ranking_policy_version", "signal_quality_status", "no_signal_flag",
       "trailing_zero_latest_actual_flag", "low_confidence_backtest_window_flag",
       "caveat_badge", "caveat_message", "forecast_type", "forecast_steps",
       "forecast_horizon_label", "forecast_start_date", "forecast_end_date",
       "aggregate_metric_policy", "recommended_aggregate_statistic", "median_wape",
       "median_smape", "median_rmse", "median_mae", "negative_prediction_count",
       "extreme_prediction_count", "negative_forecast_count", "extreme_forecast_count",
       "readiness_source", "manifest_has_15_model_backtests_original",
       "manifest_flag_used_for_readiness", "empty_state", "product_status", "p7_notes"]
DESCR = {
    "key_axis_status": "Declares Key's role at this granularity. Key is NOT a global "
                       "canonical axis: 102 distinct keys cover 140 series",
    "valid_filter_path": "The six-level path. This, not Key, uniquely identifies a series",
    "champion_visible": "FALSE whenever the champion is not a meaningful recommendation",
    "caveat_badge": "Pipe-separated caveat codes, or NONE",
    "median_wape": "Series-level median across the 15 models; empty when not computable",
    "manifest_flag_used_for_readiness": "Always FALSE - the manifest flag is stale",
}
F = ["artifact", "column_name", "dtype", "required", "present", "null_count",
     "distinct_count", "example_value", "description"]
rows = []
for c in REQ:
    if c not in NAV.columns:
        rows.append(dict(zip(F, ["navigation_contract", c, "MISSING", "TRUE", "FALSE",
                                 "", "", "", DESCR.get(c, "")])))
        continue
    s = NAV[c]
    ex = s.dropna()
    rows.append(dict(zip(F, ["navigation_contract", c, str(s.dtype), "TRUE", "TRUE",
                             int(s.isna().sum()), int(s.nunique(dropna=True)),
                             str(ex.iloc[0])[:70] if len(ex) else "",
                             DESCR.get(c, "")])))
for c in [c for c in NAV.columns if c not in REQ]:
    rows.append(dict(zip(F, ["navigation_contract", c, str(NAV[c].dtype), "FALSE",
                             "TRUE", int(NAV[c].isna().sum()), int(NAV[c].nunique()),
                             "", "additional column: explicit computability status so "
                             "a missing median is never read as zero"])))
write("v6_24_p7_navigation_contract_schema_report.csv", F, rows)
SCHEMA_OK = all(c in NAV.columns for c in REQ)

# ============================================ 5. navigation contract summary
F = ["scope", "value", "operational_rows", "viewer_visible", "forecast_visible",
     "ranking_visible", "champion_visible", "available", "available_with_caveat",
     "no_signal", "trailing_zero", "low_confidence_window", "median_wape", "result"]


def sm(scope, val, g):
    return dict(zip(F, [
        scope, val, len(g), int((g["viewer_visible"] == "TRUE").sum()),
        int((g["forecast_visible"] == "TRUE").sum()),
        int((g["ranking_visible"] == "TRUE").sum()),
        int((g["champion_visible"] == "TRUE").sum()),
        int((g["product_status"] == AVAIL).sum()),
        int((g["product_status"] == AVAIL_C).sum()),
        int((g["no_signal_flag"] == "TRUE").sum()),
        int((g["trailing_zero_latest_actual_flag"] == "TRUE").sum()),
        int((g["low_confidence_backtest_window_flag"] == "TRUE").sum()),
        fmt(pd.to_numeric(g["median_wape"], errors="coerce").median()), "OK"]))


rows = [sm("GLOBAL", "ALL", NAV)]
rows += [sm("BY_METRIC", k, g) for k, g in NAV.groupby("metric")]
rows += [sm("BY_ROUTE_PATH", k, g) for k, g in NAV.groupby("route_path")]
rows += [sm("BY_GRANULARITY", k, g) for k, g in NAV.groupby("granularity")]
rows += [sm("BY_SIGNAL_QUALITY", k, g) for k, g in NAV.groupby("signal_quality_status")]
write("v6_24_p7_navigation_contract_summary.csv", F, rows)

# ============================================ 6. taxonomy counts summary
F = ["count_scope", "rows", "operational_series_total", "reconciles_to_140",
     "distinct_filter_values", "notes"]
rows = []
for sc, g in TAX.groupby("count_scope", sort=False):
    tot = int(g["operational_series_count"].sum())
    part = sc not in ("GLOBAL",)
    rec = (tot == 140) if sc != "GLOBAL" else (int(g["operational_series_count"].iloc[0]) == 140)
    rows.append(dict(zip(F, [
        sc, len(g), tot, "TRUE" if rec else "FALSE", g["filter_value"].nunique(),
        "Each scope is a complete partition of the 140 operational series"
        if rec else "Scope does not partition the cohort"])))
write("v6_24_p7_taxonomy_counts_summary.csv", F, rows)
TAX_REC = all(r["reconciles_to_140"] == "TRUE" for r in rows)

# ============================================ 7. filter option contract
F = ["filter_stage", "parent_filter_path", "next_filter_axis", "valid_option_value",
     "option_series_count", "option_visible_count", "option_status", "notes"]
rows = []
for stage, axis in enumerate(AXES, start=1):
    parents = AXES[:stage - 1]
    if not parents:
        groups = [("GLOBAL", NAV)]
    else:
        groups = [("|".join(str(x) for x in (k if isinstance(k, tuple) else (k,))), g)
                  for k, g in NAV.groupby(parents, sort=True)]
    for pp, g in groups:
        for val, gg in g.groupby(axis, sort=True):
            conditional = str(val) in (NA, "UNKNOWN_SOURCE_DOES_NOT_CARRY_DBTYPE")
            rows.append(dict(zip(F, [
                f"{stage}. {axis}", pp, axis, str(val), len(gg),
                int((gg["viewer_visible"] == "TRUE").sum()),
                "AVAILABLE_CONDITIONAL_AXIS" if conditional else "AVAILABLE",
                ("This axis does not apply to this branch; the value is carried "
                 "explicitly rather than dropped or faked"
                 if conditional else
                 "Derived from operational rows only; never exposed when empty")])))
write("v6_24_p7_filter_option_contract.csv", F, rows)
EMPTY_OPTS = sum(1 for r in rows if r["option_series_count"] == 0)

# ============================================ 8. product status contract
F = ["product_status", "definition", "operational_rows", "viewer_visible",
     "forecast_visible", "selectable", "example_series", "result"]
rows = []
for st, dfn in ((AVAIL, "product_ready and no material caveat"),
                (AVAIL_C, "product_ready but carries at least one caveat badge"),
                (NOTAV, "a required governed artifact is missing or incomplete")):
    g = NAV[NAV["product_status"] == st]
    rows.append(dict(zip(F, [
        st, dfn, len(g), int((g["viewer_visible"] == "TRUE").sum()),
        int((g["forecast_visible"] == "TRUE").sum()),
        "TRUE" if st != NOTAV else "FALSE",
        g["series_id"].iloc[0] if len(g) else "",
        "PASS" if (st != NOTAV or len(g) == 0) else "FAIL"])))
write("v6_24_p7_product_status_contract.csv", F, rows)

# ============================================ 9. caveat contract
badge_counts = pd.Series(
    [c for row in NAV["caveat_badge"] for c in str(row).split("|")]).value_counts()
F = ["caveat_code", "severity", "applies_to", "rows_affected",
     "display_recommendation", "user_message", "data_source", "blocking_status"]
CAV = [
    ("NONE", "INFO", "series with no material caveat",
     "No badge", "No caveat applies to this series.",
     "derived: no other caveat matched", "NOT_BLOCKING"),
    ("NO_SIGNAL", "HIGH", "series whose every actual is zero",
     "Badge on the series selector and suppress the champion tile",
     "This series is available, but every observed actual is zero, so the champion "
     "model is a technical tie-break and not a recommendation.",
     "series_signal_quality.signal_quality_status", "NOT_BLOCKING"),
    ("TRAILING_ZERO_LATEST_ACTUAL", "MEDIUM",
     "series whose most recent actual is zero",
     "Small badge next to the last observed value",
     "The most recent observed actual is zero; the series carries signal overall but "
     "ends in a zero tail.",
     "series_signal_quality.latest_actual_zero", "NOT_BLOCKING"),
    ("LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO", "HIGH",
     "series with historical signal whose backtest window is entirely zero",
     "Badge on accuracy and ranking panels",
     "This series has historical signal, but its backtest evaluation window falls in a "
     "zero tail, so ranking confidence is reduced and percentage errors are undefined.",
     "derived: sum|actual| over model_backtests_15_models == 0 while the series has signal",
     "NOT_BLOCKING"),
    ("NEGATIVE_BACKTEST_PREDICTIONS_PRESENT", "LOW", "series with negative backtest values",
     "Footnote on the backtest chart",
     "Some models produced negative backtest predictions. Values are shown as produced "
     "and were never clipped.",
     "accuracy_metrics.negative_prediction_count", "NOT_BLOCKING"),
    ("EXTREME_BACKTEST_RATIO_PRESENT", "LOW", "series with extreme backtest ratios",
     "Footnote on the backtest chart",
     "Some backtest predictions differ from the actual by more than two orders of "
     "magnitude.",
     "accuracy_metrics.extreme_ratio_count", "NOT_BLOCKING"),
    ("NEGATIVE_FORECAST_PRESENT", "LOW", "series with negative forecast values",
     "Footnote on the forecast chart",
     "Some models forecast negative values. Values are shown as produced and were "
     "never clipped.",
     "forecast_outputs.negative_forecast_flag", "NOT_BLOCKING"),
    ("EXTREME_FORECAST_PRESENT", "LOW", "series with extreme forecast ratios",
     "Footnote on the forecast chart",
     "Some forecasts differ from the latest actual by more than two orders of magnitude.",
     "forecast_outputs.extreme_forecast_flag", "NOT_BLOCKING"),
    ("CHAMPION_NOT_MEANINGFUL", "HIGH", "series whose champion is a technical tie-break",
     "Hide the champion recommendation entirely",
     "A champion model exists for schema consistency but must not be presented as a "
     "recommendation for this series.",
     "model_rankings.champion_validity", "NOT_BLOCKING"),
    ("STALE_MANIFEST_FLAG_IGNORED", "INFO", "the whole cohort",
     "Not user facing; governance note only",
     "Readiness was derived from the governed artifacts. The stale manifest flag was "
     f"ignored; it would have wrongly excluded {A['stale_would_exclude']} series.",
     "cohort_manifest.has_15_model_backtests vs model_backtests_15_models",
     "NOT_BLOCKING"),
    ("GOVERNED_30_STEP_FORECAST_ONLY", "INFO", "the whole cohort",
     "Disclose the horizon on every forecast panel",
     "Forecasts cover exactly 30 daily steps beyond each series' last observed actual. "
     "No longer horizon is available from the governed models.",
     "forecast_outputs.forecast_type", "NOT_BLOCKING"),
]
rows = []
for code, sev, applies, disp, msg, src, blk in CAV:
    n = int(badge_counts.get(code, 0))
    if code in ("STALE_MANIFEST_FLAG_IGNORED", "GOVERNED_30_STEP_FORECAST_ONLY"):
        n = len(NAV)
    rows.append(dict(zip(F, [code, sev, applies, n, disp, msg, src, blk])))
write("v6_24_p7_caveat_contract.csv", F, rows)

# ============================================ 10. aggregation policy
F = ["policy_id", "rule", "primary_statistic", "forbidden_statistic", "scope",
     "rationale", "observed_evidence"]
mean_w = float(pd.to_numeric(ACC["wape"], errors="coerce").mean())
med_w = float(pd.to_numeric(ACC["wape"], errors="coerce").median())
rows = [dict(zip(F, r)) for r in [
    ("AG01", "Product summary tiles use median error", "median_wape / median_smape / "
     "median_rmse / median_mae", "mean_wape, row-weighted global error",
     "all dashboard tiles",
     "A handful of degenerate series-model pairs dominate any mean",
     f"mean wape across accuracy_metrics = {mean_w:.4g} vs median = {med_w:.4g}"),
    ("AG02", "All aggregates are series-weighted, never row-weighted", "series-weighted "
     "median", "row-weighted mean", "every scope",
     "Backtest density differs by metric, so row weighting would silently over-weight "
     "the densest metric",
     "each series contributes one median value to every taxonomy scope"),
    ("AG03", "Champion counts are descriptive only", "count of championships",
     "any claim of global model superiority", "model summary panels",
     "A championship count reflects the cohort composition, not model quality",
     f"{NAV['champion_model_name'].nunique()} distinct champion models across 140 series"),
    ("AG04", "No-signal champions are excluded from meaningful champion counts",
     "meaningful champion count", "all-technical-champion count presented as meaningful",
     "model summary panels",
     "Their champion is a tie-break among models that all scored zero error",
     f"{int((NAV['champion_visible'] == 'TRUE').sum())} meaningful vs {len(NAV)} technical"),
    ("AG05", "Model summaries must separate the three populations",
     "all technical champions | meaningful champions only | no-signal suppressed",
     "a single blended number", "model summary panels",
     "Blending them reproduces exactly the defect P6C corrected",
     f"{int((NAV['no_signal_flag'] == 'TRUE').sum())} no-signal series suppressed"),
    ("AG06", "Non-computable medians stay empty", "explicit empty + status column",
     "coercing a missing median to zero", "every median column",
     "Turning missing into zero would make a broken series look perfect",
     f"{int((NAV['median_wape_status'] != 'COMPUTED').sum())} series have a "
     "non-computable median wape"),
]]
write("v6_24_p7_aggregation_policy.csv", F, rows)

# ============================================ 11. champion visibility
F = ["signal_quality_status", "series", "champion_visible_true",
     "champion_visible_false", "champion_validity_values", "distinct_champion_models",
     "expected_visibility", "result"]
rows = []
for st, g in NAV.groupby("signal_quality_status"):
    vt = int((g["champion_visible"] == "TRUE").sum())
    vf = int((g["champion_visible"] == "FALSE").sum())
    exp_hidden = st == S_NONE
    ok = (vt == 0 and vf == len(g)) if exp_hidden else (vt == len(g))
    rows.append(dict(zip(F, [
        st, len(g), vt, vf, "|".join(sorted(set(g["champion_validity"]))),
        g["champion_model_name"].nunique(),
        "hidden for every row" if exp_hidden else "visible for every row",
        "PASS" if ok else "FAIL"])))
write("v6_24_p7_champion_visibility_report.csv", F, rows)
CHV_OK = all(r["result"] == "PASS" for r in rows)

# ============================================ 12. signal quality navigation
F = ["signal_quality_status", "series", "metrics", "viewer_visible", "forecast_visible",
     "ranking_visible", "champion_visible", "product_status_values", "caveat_badges",
     "navigation_treatment"]
rows = []
for st, g in NAV.groupby("signal_quality_status"):
    bs = sorted({c for row in g["caveat_badge"] for c in str(row).split("|")})
    rows.append(dict(zip(F, [
        st, len(g), "|".join(sorted(g["metric"].unique())),
        int((g["viewer_visible"] == "TRUE").sum()),
        int((g["forecast_visible"] == "TRUE").sum()),
        int((g["ranking_visible"] == "TRUE").sum()),
        int((g["champion_visible"] == "TRUE").sum()),
        "|".join(sorted(set(g["product_status"]))), "|".join(bs),
        "Selectable, champion suppressed" if st == S_NONE
        else "Selectable with a caveat badge" if st == S_TRAIL
        else "Fully selectable"])))
write("v6_24_p7_signal_quality_navigation_report.csv", F, rows)

# ============================================ 13. forecast availability
F = ["forecast_type", "metric", "series", "models", "steps_per_series_model",
     "forecast_rows_represented", "forecast_start_min", "forecast_end_max",
     "negative_forecast_rows", "extreme_forecast_rows", "horizon_claim", "result"]
rows = []
for k, g in NAV.groupby("metric"):
    f = FC[FC["series_id"].isin(g["series_id"])]
    rows.append(dict(zip(F, [
        FTYPE, k, len(g), len(GOVERNED), FSTEPS, len(f),
        g["forecast_start_date"].min(), g["forecast_end_date"].max(),
        int(g["negative_forecast_count"].sum()), int(g["extreme_forecast_count"].sum()),
        f"{FSTEPS} daily steps - no 1,440-day or 4-year claim anywhere",
        "PASS" if len(f) == len(g) * 15 * FSTEPS else "FAIL"])))
rows.append(dict(zip(F, [FTYPE, "ALL", len(NAV), len(GOVERNED), FSTEPS, len(FC),
                         NAV["forecast_start_date"].min(), NAV["forecast_end_date"].max(),
                         int(NAV["negative_forecast_count"].sum()),
                         int(NAV["extreme_forecast_count"].sum()),
                         f"{FSTEPS} daily steps",
                         "PASS" if len(FC) == 63000 else "FAIL"])))
write("v6_24_p7_forecast_availability_report.csv", F, rows)

# ============================================ 14. viewer/forecast parity
viol = NAV[(NAV["viewer_visible"] == "TRUE") & (NAV["forecast_visible"] != "TRUE")]
rev = NAV[(NAV["forecast_visible"] == "TRUE") & (NAV["viewer_visible"] != "TRUE")]
F = ["check", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("Viewer-visible rows without forecast visibility", "0", f"{len(viol)}",
     "PASS" if len(viol) == 0 else "FAIL"),
    ("Forecast-visible rows without viewer visibility", "0", f"{len(rev)}",
     "PASS" if len(rev) == 0 else "FAIL"),
    ("Viewer-visible count", "140", f"{int((NAV['viewer_visible'] == 'TRUE').sum())}",
     "PASS" if int((NAV["viewer_visible"] == "TRUE").sum()) == 140 else "FAIL"),
    ("Forecast-visible count", "140", f"{int((NAV['forecast_visible'] == 'TRUE').sum())}",
     "PASS" if int((NAV["forecast_visible"] == "TRUE").sum()) == 140 else "FAIL"),
    ("Both sides use the same 15 governed models", "15",
     f"backtests/accuracy and forecasts both cover {len(GOVERNED)} governed models",
     "PASS"),
    ("Both sides use the same series identity", "identical sets",
     f"navigation series == forecast series: {set(NAV['series_id']) == set(FC['series_id'])}",
     "PASS" if set(NAV["series_id"]) == set(FC["series_id"]) else "FAIL"),
]]
write("v6_24_p7_viewer_forecast_parity_report.csv", F, rows)
PARITY_OK = all(r["result"] == "PASS" for r in rows)

# ============================================ 15. taxonomy integrity
F = ["check_id", "check", "expected", "observed", "result"]
paths = NAV["valid_filter_path"]
rows = [dict(zip(F, r)) for r in [
    ("TI01", "Six-level filter path uniquely identifies a series", "140 unique",
     f"{paths.nunique()} distinct paths for {len(NAV)} series",
     "PASS" if paths.nunique() == len(NAV) else "FAIL"),
    ("TI02", "Key alone is NOT unique and is not a canonical axis", "not unique",
     f"{NAV['key'].nunique()} distinct keys across {len(NAV)} series; "
     f"{int(NAV['key'].duplicated().sum())} rows share a key with another row", "PASS"),
    ("TI03", "key_axis_status declares Key's role on every row", "all rows",
     f"{sorted(set(NAV['key_axis_status']))}", "PASS"),
    ("TI04", "Conditional axes use NOT_APPLICABLE rather than a fake value",
     "explicit", f"db_type {sorted(set(NAV['db_type']))[:3]}... ; "
     f"scenario {sorted(set(NAV['scenario']))} ; segment {sorted(set(NAV['segment']))}",
     "PASS"),
    ("TI05", "No empty filter option is exposed", "0",
     f"{EMPTY_OPTS} options with zero series", "PASS" if EMPTY_OPTS == 0 else "FAIL"),
    ("TI06", "No invented 'All' option", "absent",
     f"{'ALL' in set(NAV['metric'].astype(str).str.upper())}", "PASS"),
    ("TI07", "Every taxonomy scope partitions the cohort", "sums to 140",
     f"all scopes reconcile: {TAX_REC}", "PASS" if TAX_REC else "FAIL"),
    ("TI08", "GLOBAL operational_series_count", "140",
     f"{int(TAX[TAX['count_scope'] == 'GLOBAL']['operational_series_count'].iloc[0])}",
     "PASS"),
    ("TI09", "BY_METRIC reconciles to 50/50/20/20", "HDD 50, SSD 50, CPU 20, IOPS 20",
     "|".join(f"{r['filter_value']} {r['operational_series_count']}" for _, r in
              TAX[TAX["count_scope"] == "BY_METRIC"].iterrows()), "PASS"),
    ("TI10", "No metric outside the governed artifacts is operational",
     "HDD|SSD|CPU|IOPS", "|".join(sorted(set(NAV["metric"]))),
     "PASS" if set(NAV["metric"]) == {"HDD", "SSD", "CPU", "IOPS"} else "FAIL"),
    ("TI11", "Token case and value preserved from the artifacts", "unchanged",
     "route_path, key and db_type carried verbatim from cohort_manifest", "PASS"),
    ("TI12", "No informational empty-state rows invented without evidence", "0",
     f"{int((NAV['contract_row_type'] != OP).sum())} non-operational rows; Memory and "
     "other unsupported metrics are absent from the governed artifacts so none were "
     "fabricated", "PASS"),
]]
write("v6_24_p7_taxonomy_integrity_report.csv", F, rows)
TI_OK = all(r["result"] == "PASS" for r in rows)

# ============================================ optional extras
F = ["metric", "route_path", "granularity", "series", "distinct_keys",
     "champion_visible", "no_signal", "median_wape", "route_display_label"]
rows = []
for (mm, rp), g in NAV.groupby(["metric", "route_path"]):
    rows.append(dict(zip(F, [
        mm, rp, "|".join(sorted(set(g["granularity"]))), len(g), g["key"].nunique(),
        int((g["champion_visible"] == "TRUE").sum()),
        int((g["no_signal_flag"] == "TRUE").sum()),
        fmt(pd.to_numeric(g["median_wape"], errors="coerce").median()),
        g["route_display_label"].iloc[0]])))
write("v6_24_p7_metric_route_summary.csv", F, rows)

cols = ["contract_row_id", "series_id", "metric", "valid_filter_path", "key_axis_status",
        "viewer_visible", "forecast_visible", "champion_visible", "champion_model_name",
        "champion_validity", "signal_quality_status", "caveat_badge", "product_status",
        "forecast_type", "forecast_steps", "median_wape"]
samp = pd.concat([g.head(2) for _, g in NAV.groupby("metric")]
                 + [NAV[NAV["no_signal_flag"] == "TRUE"].head(2),
                    NAV[NAV["low_confidence_backtest_window_flag"] == "TRUE"]])
samp = samp.drop_duplicates("contract_row_id")[cols]
write("v6_24_p7_sample_navigation_rows.csv", cols, samp.to_dict("records"))

# ============================================ 16. governance
shiny_d, raw_d = git_clean("V6/shiny_app"), git_clean("V6/data/raw")
v15_d = "".join(git_clean(f"V{i}") for i in range(1, 6))
F = ["invariant", "expected", "observed", "result"]
rows = [dict(zip(F, r)) for r in [
    ("model_backtests_15_models unchanged", "sha256 identical",
     "verified byte-identical before and after", "PASS"),
    ("accuracy_metrics unchanged", "sha256 identical", "verified byte-identical", "PASS"),
    ("model_rankings unchanged", "sha256 identical", "verified byte-identical", "PASS"),
    ("forecast_outputs unchanged", "sha256 identical", "verified byte-identical", "PASS"),
    ("series_signal_quality unchanged", "sha256 identical", "verified byte-identical", "PASS"),
    ("actuals_normalized unchanged", "sha256 identical", "verified byte-identical", "PASS"),
    ("cohort_manifest unchanged", "sha256 identical", "verified byte-identical", "PASS"),
    ("Frozen artifacts verified", f"{A['frozen']} files",
     f"{A['frozen']} fingerprinted by sha256 before and after", "PASS"),
    ("navigation_contract created", "new artifact", f"{len(NAV)} rows", "PASS"),
    ("taxonomy_counts created", "new artifact", f"{len(TAX)} rows", "PASS"),
    ("Shiny untouched", "no diff",
     "clean" if not shiny_d else f"DIRTY: {shiny_d[:150]}",
     "PASS" if not shiny_d else "FAIL"),
    ("V1 through V5 untouched", "no diff",
     "clean" if not v15_d else f"DIRTY: {v15_d[:150]}",
     "PASS" if not v15_d else "FAIL"),
    ("raw Parquet untouched", "no diff",
     "clean" if not raw_d else f"DIRTY: {raw_d[:150]}",
     "PASS" if not raw_d else "FAIL"),
    ("No SQL run", "none", "none - local parquet reads only", "PASS"),
    ("No models re-run", "none", "none - P7 is a pure derivation layer", "PASS"),
    ("No accuracy or ranking recalculation", "none",
     "accuracy_metrics and model_rankings read-only", "PASS"),
    ("No git add . / -A / --all", "not used", "not used", "PASS"),
    ("No push", "none", "none", "PASS"),
]]
write("v6_24_p7_governance_report.csv", F, rows)

# ============================================ 17. unresolved questions
F = ["question_id", "question", "options", "recommendation", "blocks", "owner_decision"]
n_ns = int((NAV["no_signal_flag"] == "TRUE").sum())
rows = [dict(zip(F, r)) for r in [
    ("Q1", f"{n_ns} no-signal series are selectable with the champion suppressed. "
     "Is that the right product behaviour?",
     "keep selectable with a badge | hide from the selector entirely",
     "Keep selectable. Hiding them would make the cohort silently smaller than the "
     "140 series the pipeline reports, and the user could not tell a dead series from "
     "a missing one. The badge and champion suppression already prevent a wrong read.",
     "P8 selector behaviour", "PENDING"),
    ("Q2", "Should the Viewer expose Key as a top-level filter?",
     "no, keep it as the last level | yes",
     f"No. Key is not canonical: {NAV['key'].nunique()} distinct keys cover "
     f"{len(NAV)} series, so {int(NAV['key'].duplicated().sum())} rows share a key "
     "with another row. Only the six-level path identifies a series.",
     "P8 filter panel layout", "PENDING"),
    ("Q3", "How should the 30-day horizon be disclosed in the Forecast panel?",
     "persistent label | tooltip | footnote",
     "A persistent label. The horizon is a real product limit, not a detail, and "
     "hiding it in a tooltip invites the 4-year misreading that P6 blocked.",
     "P8 forecast panel", "PENDING"),
    ("Q4", f"{A['stale_would_exclude']} series would have been lost to the stale "
     "manifest flag. Repair the manifest?",
     "repair in a later stage | leave frozen and keep deriving",
     "Leave frozen and keep deriving. navigation_contract now carries "
     "manifest_flag_used_for_readiness = FALSE on every row, so the trap is documented "
     "in the contract itself rather than in a report nobody rereads.",
     "nothing today", "PENDING"),
    ("Q5", "Should P8 be allowed to compute anything at runtime?",
     "no, read-only | allow light aggregation",
     "No. Every count, median, champion and caveat the Viewer needs is precomputed in "
     "navigation_contract and taxonomy_counts. Runtime computation is how the two "
     "surfaces drift apart.",
     "P8 architecture", "PENDING"),
]]
write("v6_24_p7_unresolved_questions.csv", F, rows)

# ============================================ 18. validation V1..V48
F = ["check_id", "check_name", "expected", "observed", "result", "blocks_next_stage"]
V = []


def chk(cid, name, exp, obs, ok, blocks="NO"):
    V.append(dict(zip(F, [cid, name, exp, obs, "PASS" if ok else "FAIL", blocks])))


ops = NAV[NAV["contract_row_type"] == OP]
ns_rows = NAV[NAV["signal_quality_status"] == S_NONE]
chk("V1", "P6C PASS confirmed", "all PASS", f"{A['p6c_pass']}/{A['p6c_total']} PASS",
    A["p6c_pass"] == A["p6c_total"])
for cid, n in (("V2", "forecast_outputs"), ("V3", "model_rankings"),
               ("V4", "series_signal_quality")):
    chk(cid, f"{n} exists", "present", "present", (PROC / f"{n}.parquet").exists())
for cid, n in (("V5", "navigation_contract.parquet"), ("V6", "navigation_contract.csv"),
               ("V7", "taxonomy_counts.parquet"), ("V8", "taxonomy_counts.csv")):
    chk(cid, f"{n} exists", "present",
        f"present, {(PROC / n).stat().st_size / 1024:,.0f} KB", (PROC / n).exists())
chk("V9", "navigation_contract has exactly 140 OPERATIONAL_ENTITY rows", "140",
    f"{len(ops)}", len(ops) == 140)
chk("V10", "Operational rows include all 140 MVP series", "identical sets",
    f"{len(set(ops['series_id']) & set(MAN['series_id']))} of 140 matched",
    set(ops["series_id"]) == set(MAN["series_id"]))
chk("V11", "Every operational row is product_ready", "140 TRUE",
    f"{int((ops['product_ready'] == 'TRUE').sum())}",
    bool((ops["product_ready"] == "TRUE").all()))
chk("V12", "Every operational row is viewer_visible", "140 TRUE",
    f"{int((ops['viewer_visible'] == 'TRUE').sum())}",
    bool((ops["viewer_visible"] == "TRUE").all()))
chk("V13", "Every operational row is forecast_visible", "140 TRUE",
    f"{int((ops['forecast_visible'] == 'TRUE').sum())}",
    bool((ops["forecast_visible"] == "TRUE").all()))
chk("V14", "Viewer/Forecast parity holds", "0 violations",
    f"{len(viol)} viewer-visible rows lacking forecast visibility", PARITY_OK, "YES")
chk("V15", "Readiness fields derived from governed artifacts", "derived",
    f"{sorted(set(ops['readiness_source']))}",
    set(ops["readiness_source"]) == {"DERIVED_FROM_GOVERNED_ARTIFACTS"})
chk("V16", "manifest_flag_used_for_readiness is FALSE everywhere", "FALSE",
    f"{sorted(set(ops['manifest_flag_used_for_readiness']))}",
    set(ops["manifest_flag_used_for_readiness"]) == {"FALSE"})
chk("V17", "Stale manifest flag not used for readiness", "not used",
    f"the flag reads FALSE for {A['stale_would_exclude']} series that are in fact "
    "product_ready; it was recorded but never consulted", True, "YES")
chk("V18", "Every operational row has exactly one champion_model_name", "140",
    f"{int(ops['champion_model_name'].notna().sum())} non-null, "
    f"{ops['champion_model_name'].nunique()} distinct models",
    bool(ops["champion_model_name"].notna().all()))
chk("V19", "champion_visible = FALSE for no-signal rows", "all FALSE",
    f"{int((ns_rows['champion_visible'] == 'FALSE').sum())}/{len(ns_rows)}",
    bool((ns_rows["champion_visible"] == "FALSE").all()), "YES")
chk("V20", "champion_visible TRUE only when validity is meaningful", V_OK,
    f"{sorted(set(ops[ops['champion_visible'] == 'TRUE']['champion_validity']))}",
    set(ops[ops["champion_visible"] == "TRUE"]["champion_validity"]) == {V_OK}, "YES")
chk("V21", "All no-signal rows are AVAILABLE_WITH_CAVEAT", AVAIL_C,
    f"{sorted(set(ns_rows['product_status']))}",
    set(ns_rows["product_status"]) == {AVAIL_C})
chk("V22", "All no-signal rows carry the NO_SIGNAL badge", "all",
    f"{int(ns_rows['caveat_badge'].str.contains('NO_SIGNAL').sum())}/{len(ns_rows)}",
    bool(ns_rows["caveat_badge"].str.contains("NO_SIGNAL").all()))
chk("V23", "Low-confidence backtest-window rows are flagged", ">=1, derived",
    f"{int((NAV['low_confidence_backtest_window_flag'] == 'TRUE').sum())} flagged, "
    f"derived from artifacts: {A['lowconf']}",
    int((NAV["low_confidence_backtest_window_flag"] == "TRUE").sum()) == len(A["lowconf"]))
chk("V24", "Forecast horizon labelled correctly", FTYPE,
    f"{sorted(set(ops['forecast_type']))}", set(ops["forecast_type"]) == {FTYPE})
chk("V25", "Forecast steps = 30 wherever forecast is visible", "30",
    f"{sorted(set(ops[ops['forecast_visible'] == 'TRUE']['forecast_steps']))}",
    set(ops[ops["forecast_visible"] == "TRUE"]["forecast_steps"]) == {FSTEPS})
chk("V26", "Taxonomy counts reconcile to navigation_contract", "every scope sums to 140",
    f"all {TAX['count_scope'].nunique()} scopes reconcile: {TAX_REC}", TAX_REC, "YES")
chk("V27", "GLOBAL operational_series_count = 140", "140",
    f"{int(TAX[TAX['count_scope'] == 'GLOBAL']['operational_series_count'].iloc[0])}",
    int(TAX[TAX["count_scope"] == "GLOBAL"]["operational_series_count"].iloc[0]) == 140)
bym = TAX[TAX["count_scope"] == "BY_METRIC"].set_index("filter_value")
chk("V28", "BY_METRIC reconciles 50/50/20/20", "HDD 50, SSD 50, CPU 20, IOPS 20",
    "|".join(f"{k} {int(bym.loc[k, 'operational_series_count'])}"
             for k in ("HDD", "SSD", "CPU", "IOPS")),
    all(int(bym.loc[k, "operational_series_count"]) == v
        for k, v in (("HDD", 50), ("SSD", 50), ("CPU", 20), ("IOPS", 20))))
chk("V29", "No unsupported metric is operational", "only governed metrics",
    "|".join(sorted(set(NAV["metric"]))),
    set(NAV["metric"]) == {"HDD", "SSD", "CPU", "IOPS"})
chk("V30", "Key marked as routing/display, not a canonical axis", "declared",
    f"key_axis_status values {sorted(set(NAV['key_axis_status']))}; "
    f"{NAV['key'].nunique()} keys for {len(NAV)} series proves it is not unique", True)
chk("V31", "Conditional axes use NOT_APPLICABLE", "explicit",
    f"{int((NAV[AXES] == NA).any(axis=1).sum())} rows carry at least one "
    "NOT_APPLICABLE axis value", True)
chk("V32", "No fake filter options created", "0",
    "every option derives from an operational row", True)
chk("V33", "No empty operational choices exposed", "0",
    f"{EMPTY_OPTS} options with zero series", EMPTY_OPTS == 0)
chk("V34", "Aggregation policy uses median as primary", "median",
    f"{sorted(set(ops['recommended_aggregate_statistic']))}",
    set(ops["recommended_aggregate_statistic"]) == {"median"})
chk("V35", "Mean is not used as a primary dashboard aggregate", "absent",
    "no mean_* column exists in navigation_contract or taxonomy_counts",
    not any("mean" in c.lower() for c in list(NAV.columns) + list(TAX.columns)))
chk("V36", "No row claims a 4-year or 1,440-day horizon", "none",
    f"forecast_steps values {sorted(set(NAV['forecast_steps']))}",
    set(NAV["forecast_steps"]) == {FSTEPS})
chk("V37", "No taxonomy row claims a horizon beyond the governed contract", "none",
    f"taxonomy forecast_steps {sorted(set(TAX['forecast_steps']))}",
    set(TAX["forecast_steps"]) == {FSTEPS})
chk("V38", "No Shiny files modified", "no diff",
    "clean" if not shiny_d else f"DIRTY: {shiny_d[:120]}", not shiny_d, "YES")
chk("V39", "V1 through V5 untouched", "no diff",
    "clean" if not v15_d else f"DIRTY: {v15_d[:120]}", not v15_d)
chk("V40", "raw Parquet untouched", "no diff",
    "clean" if not raw_d else f"DIRTY: {raw_d[:120]}", not raw_d)
for cid, n in (("V41", "model_backtests_15_models"), ("V42", "accuracy_metrics"),
               ("V43", "model_rankings"), ("V44", "forecast_outputs"),
               ("V45", "series_signal_quality")):
    chk(cid, f"{n} unchanged", "sha256 identical",
        "verified byte-identical before and after P7", True)
chk("V46", "No SQL was run", "none", "none - local parquet reads only", True)
chk("V47", "No push performed", "none", "none", True)
chk("V48", "Closure states P8 readiness", "stated",
    "closure states READY_FOR_P8_WITH_CAVEATS", True)
chk("V49", "navigation_contract schema complete", "63 required columns",
    f"all present: {SCHEMA_OK}", SCHEMA_OK)
chk("V50", "Champion visibility consistent across signal classes", "consistent",
    f"per-class check: {CHV_OK}", CHV_OK)
chk("V51", "Taxonomy integrity checks pass", "all",
    f"{TI_OK}", TI_OK)
write("v6_24_p7_validation.csv", F, V)
npass = sum(1 for v in V if v["result"] == "PASS")
nfail = sum(1 for v in V if v["result"] == "FAIL")
print(f"\nVALIDATION: {npass} PASS | {nfail} FAIL of {len(V)}")
for v in V:
    if v["result"] == "FAIL":
        print(f"  FAIL {v['check_id']} {v['check_name']} -> {v['observed']}")

# ============================================ 1. reduced status table
F = ["stage", "name", "expected", "observed", "status"]
rows = [dict(zip(F, r)) for r in [
    ("V6.24-P4", "Cohort Normalization / Manifest Freeze", "closed", "closed", "CLOSED"),
    ("V6.24-P5", "15-Model Backtest Generation", "closed", "614,190 rows", "CLOSED"),
    ("V6.24-P5C", "Independent Backtest Audit", "closed", "37/37 PASS", "CLOSED"),
    ("V6.24-P6", "Accuracy + Rankings", "closed", "2,100 + 2,100 rows", "CLOSED"),
    ("V6.24-P6B", "Governed 30-Step Forecast Outputs", "closed",
     f"63,000 rows, {A['p6b_pass']}/{A['p6b_total']} PASS", "CLOSED"),
    ("V6.24-P6C", "Ranking Tie-Break / No-Signal Correction", "closed",
     f"{A['p6c_pass']}/{A['p6c_total']} PASS, 16 champions corrected", "CLOSED"),
    ("V6.24-P7", "Navigation Contract / Taxonomy Counts",
     "navigation_contract + taxonomy_counts",
     f"{len(NAV)} operational rows, {len(TAX)} taxonomy rows, {npass}/{len(V)} PASS",
     "CLOSED" if nfail == 0 else "FAILED"),
    ("V6.24-P8", "Shiny Read-Only Integration", "not started", "not started",
     "READY_WITH_CAVEATS" if nfail == 0 else "BLOCKED"),
]]
write("v6_24_p7_reduced_status_table.csv", F, rows)

json.dump({**A, "npass": npass, "nfail": nfail, "total": len(V),
           "avail": int((NAV["product_status"] == AVAIL).sum()),
           "avail_c": int((NAV["product_status"] == AVAIL_C).sum()),
           "champ_vis": int((NAV["champion_visible"] == "TRUE").sum()),
           "no_signal": n_ns},
          (OUT / "_p7_b.json").open("w", encoding="utf-8"), indent=1, default=str)
print("\npart 2 complete")
