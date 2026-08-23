"""V6.24-P7 - Navigation contract / taxonomy counts / product availability contract.

A read-only derivation layer over the governed processed artifacts. Creates exactly
two new canonical artifacts: navigation_contract and taxonomy_counts.

Readiness is derived from the artifacts themselves, never from the stale
cohort_manifest.has_15_model_backtests flag.
"""
from __future__ import annotations

import csv
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P6C = V6 / "outputs" / "v6_24_p6c_ranking_tiebreak_no_signal_correction"
P6B = V6 / "outputs" / "v6_24_p6b_governed_30_step_forecast_outputs"

POLICY = "P6C_RANKING_POLICY_V2"
FTYPE = "GOVERNED_30_STEP_DAILY_FORECAST"
FSTEPS = 30
NA = "NOT_APPLICABLE"
S_NONE, S_TRAIL, S_OK = ("NO_SIGNAL_ALL_ZERO_ACTUALS", "TRAILING_ZERO_LATEST_ACTUAL",
                         "SIGNAL_PRESENT")
V_BAD, V_OK = "NOT_MEANINGFUL_NO_SIGNAL", "MEANINGFUL_ACCURACY_RANKING"
AVAIL, AVAIL_C = "AVAILABLE", "AVAILABLE_WITH_CAVEAT"
OP = "OPERATIONAL_ENTITY"
NCS = "STRUCTURALLY_NOT_COMPUTABLE"
GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
AXES = ["metric", "db_type", "scenario", "segment", "granularity", "key"]
TS = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def write(name, fields, rows):
    with (OUT / name).open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f"{name}|rows={len(rows)}")


def sha256_file(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def med(s):
    """Median over computable values only. Returns NaN when nothing is computable."""
    v = pd.to_numeric(s, errors="coerce").dropna()
    return float(v.median()) if len(v) else np.nan


# ================================================ preflight
print("P7 START - navigation contract / taxonomy counts")
P6CV = pd.read_csv(P6C / "v6_24_p6c_validation.csv")
P6BV = pd.read_csv(P6B / "v6_24_p6b_validation.csv")
p6c_ok = bool((P6CV["result"] == "PASS").all())
need = {n: (PROC / f"{n}.parquet").exists() for n in
        ("cohort_manifest", "actuals_normalized", "model_backtests_15_models",
         "accuracy_metrics", "model_rankings", "forecast_outputs",
         "series_signal_quality")}

F = ["check_id", "check", "expected", "observed", "result", "blocking_token"]
pf = [dict(zip(F, [
    "PF01", "P6C validation passed", "all PASS",
    f"{int((P6CV['result'] == 'PASS').sum())}/{len(P6CV)} PASS",
    "PASS" if p6c_ok else "FAIL", "V6_24_P7_BLOCKED_P6C_NOT_PASS"]))]
tok = {"forecast_outputs": "V6_24_P7_BLOCKED_FORECAST_OUTPUTS_MISSING",
       "model_rankings": "V6_24_P7_BLOCKED_MODEL_RANKINGS_MISSING",
       "series_signal_quality": "V6_24_P7_BLOCKED_SIGNAL_QUALITY_MISSING"}
for i, (n, ok) in enumerate(need.items(), start=2):
    pf.append(dict(zip(F, [f"PF{i:02d}", f"{n} exists", "present",
                           "present" if ok else "MISSING",
                           "PASS" if ok else "FAIL", tok.get(n, "")])))
pf.append(dict(zip(F, ["PF09", "P6B validation passed", "all PASS",
                       f"{int((P6BV['result'] == 'PASS').sum())}/{len(P6BV)} PASS",
                       "PASS" if bool((P6BV['result'] == 'PASS').all()) else "FAIL", ""])))
write("v6_24_p7_preflight_check.csv", F, pf)
if not p6c_ok or not all(need.values()):
    bad = [r["blocking_token"] for r in pf if r["result"] == "FAIL" and r["blocking_token"]]
    raise SystemExit(f"PREFLIGHT FAILED -> {bad[0] if bad else 'UNKNOWN'}")
print(f"preflight OK | P6C {int((P6CV['result'] == 'PASS').sum())}/{len(P6CV)} PASS")

# ================================================ inputs + frozen fingerprints
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
BT = pd.read_parquet(PROC / "model_backtests_15_models.parquet", engine="pyarrow")
ACC = pd.read_parquet(PROC / "accuracy_metrics.parquet", engine="pyarrow")
RK = pd.read_parquet(PROC / "model_rankings.parquet", engine="pyarrow")
FC = pd.read_parquet(PROC / "forecast_outputs.parquet", engine="pyarrow")
SQ = pd.read_parquet(PROC / "series_signal_quality.parquet", engine="pyarrow")
FC["forecast_date"] = pd.to_datetime(FC["forecast_date"])

FROZEN = ["cohort_manifest", "actuals_normalized", "model_backtests_15_models",
          "accuracy_metrics", "model_rankings", "forecast_outputs",
          "series_signal_quality", "source_forecast_baselines_normalized"]
frozen_before = {p.name: sha256_file(p) for p in PROC.iterdir()
                 if any(p.name.startswith(k) for k in FROZEN)}
print(f"fingerprinted {len(frozen_before)} frozen artifacts by sha256")

# ================================================ readiness, derived
bt_models = BT.groupby("series_id")["model_name"].apply(lambda s: set(s.unique()))
bt_permodel = BT.groupby(["series_id", "model_name"]).size()
acc_models = ACC.groupby("series_id")["model_name"].apply(lambda s: set(s.unique()))
rk_models = RK.groupby("series_id")["model_name"].apply(lambda s: set(s.unique()))
rk_champ = RK[RK["is_series_champion"] == "TRUE"].groupby("series_id").size()
rk_pol = RK.groupby("series_id")["ranking_policy_version"].apply(lambda s: set(s.unique()))
fc_models = FC.groupby("series_id")["model_name"].apply(lambda s: set(s.unique()))
fc_steps = FC.groupby(["series_id", "model_name"]).size()
fc_type = FC.groupby("series_id")["forecast_type"].apply(lambda s: set(s.unique()))
G = set(GOVERNED)
man_flag = dict(zip(MAN["series_id"], MAN["has_15_model_backtests"].astype(str)))

READY = {}
rrows = []
RF = ["series_id", "metric", "backtest_ready", "backtest_evidence", "accuracy_ready",
      "accuracy_evidence", "ranking_ready", "ranking_evidence", "forecast_ready",
      "forecast_evidence", "product_ready", "readiness_source",
      "manifest_has_15_model_backtests_original", "manifest_flag_used_for_readiness",
      "manifest_flag_would_have_excluded"]
for sid in MAN["series_id"]:
    bm = bt_models.get(sid, set())
    b_ok = bm == G and bool(bt_permodel.get(sid, pd.Series(dtype=int)).ge(1).all()) \
        if sid in bt_permodel.index.get_level_values(0) else False
    b_ok = (bm == G) and all(bt_permodel.get((sid, m), 0) >= 1 for m in GOVERNED)
    a_ok = acc_models.get(sid, set()) == G
    r_ok = (rk_models.get(sid, set()) == G and int(rk_champ.get(sid, 0)) == 1
            and rk_pol.get(sid, set()) == {POLICY})
    f_ok = (fc_models.get(sid, set()) == G
            and all(fc_steps.get((sid, m), 0) == FSTEPS for m in GOVERNED)
            and fc_type.get(sid, set()) == {FTYPE})
    p_ok = b_ok and a_ok and r_ok and f_ok
    READY[sid] = dict(backtest=b_ok, accuracy=a_ok, ranking=r_ok, forecast=f_ok,
                      product=p_ok)
    orig = man_flag.get(sid, "MISSING")
    rrows.append(dict(zip(RF, [
        sid, MAN[MAN["series_id"] == sid]["metric"].iloc[0],
        str(b_ok).upper(), f"{len(bm)}/15 models, min rows/model "
        f"{min(bt_permodel.get((sid, m), 0) for m in GOVERNED):,}",
        str(a_ok).upper(), f"{len(acc_models.get(sid, set()))}/15 models",
        str(r_ok).upper(), f"{len(rk_models.get(sid, set()))}/15 models, "
        f"{int(rk_champ.get(sid, 0))} champion, policy "
        f"{'|'.join(sorted(rk_pol.get(sid, set())))}",
        str(f_ok).upper(), f"{len(fc_models.get(sid, set()))}/15 models, "
        f"{FSTEPS} steps each, type {'|'.join(sorted(fc_type.get(sid, set())))}",
        str(p_ok).upper(), "DERIVED_FROM_GOVERNED_ARTIFACTS", orig, "FALSE",
        "TRUE" if orig.upper() == "FALSE" and p_ok else "FALSE"])))
write("v6_24_p7_readiness_derivation_report.csv", RF, rrows)
n_ready = sum(1 for v in READY.values() if v["product"])
n_stale = sum(1 for r in rrows if r["manifest_flag_would_have_excluded"] == "TRUE")
print(f"readiness derived: {n_ready}/140 product_ready | {n_stale} series the stale "
      f"manifest flag would have wrongly excluded")

# ================================================ per-series aggregates
SIG = dict(zip(SQ["series_id"], SQ["signal_quality_status"]))
SQR = {r["series_id"]: r for _, r in SQ.iterrows()}
CH = RK[RK["is_series_champion"] == "TRUE"].set_index("series_id")

# Low-confidence: the series has signal, but its backtest evaluation window is all
# zeros. Derived, never hardcoded.
bt_sum = BT.groupby("series_id")["actual_value"].apply(lambda s: float(s.abs().sum()))
LOWCONF = {sid for sid in MAN["series_id"]
           if bt_sum.get(sid, 0.0) == 0.0 and SIG[sid] != S_NONE}
print(f"low-confidence backtest windows derived: {len(LOWCONF)} series "
      f"{sorted(LOWCONF)}")

accg = {sid: g for sid, g in ACC.groupby("series_id")}
fcg = {sid: g for sid, g in FC.groupby("series_id")}

# ================================================ navigation contract
NAVF = ["contract_row_id", "contract_row_type", "cohort_id", "series_id", "metric",
        "db_type", "scenario", "segment", "granularity", "key", "route_path",
        "filter_level_1_metric", "filter_level_2_db_type", "filter_level_3_scenario",
        "filter_level_4_segment", "filter_level_5_granularity", "filter_level_6_key",
        "key_axis_status", "route_display_label", "route_sort_key", "valid_filter_path",
        "parent_filter_path",
        "viewer_visible", "forecast_visible", "ranking_visible", "champion_visible",
        "product_ready", "backtest_ready", "accuracy_ready", "ranking_ready",
        "forecast_ready",
        "champion_model_name", "champion_rank_value", "champion_rank_metric",
        "champion_validity", "champion_reason", "ranking_policy_version",
        "signal_quality_status", "no_signal_flag", "trailing_zero_latest_actual_flag",
        "low_confidence_backtest_window_flag", "caveat_badge", "caveat_message",
        "forecast_type", "forecast_steps", "forecast_horizon_label",
        "forecast_start_date", "forecast_end_date",
        "aggregate_metric_policy", "recommended_aggregate_statistic",
        "median_wape", "median_smape", "median_rmse", "median_mae",
        "median_wape_status", "median_smape_status",
        "negative_prediction_count", "extreme_prediction_count",
        "negative_forecast_count", "extreme_forecast_count",
        "readiness_source", "manifest_has_15_model_backtests_original",
        "manifest_flag_used_for_readiness", "empty_state", "product_status",
        "p7_notes"]

KEY_AXIS = {
    "Region": "ROUTING_VALUE_REGION",
    "Forest": "IDENTIFIER_VALUE_FOREST",
    "Forest_SKU": "COMPOSITE_TOKEN_FOREST_SKU",
}
nav = []
for i, (_, m) in enumerate(MAN.sort_values(["metric", "db_type", "scenario", "segment",
                                            "granularity", "key"]).iterrows(), start=1):
    sid = m["series_id"]
    r = READY[sid]
    st = SIG[sid]
    sq = SQR[sid]
    ch = CH.loc[sid]
    a = accg[sid]
    f = fcg[sid]
    lvl = [str(m[x]) for x in AXES]
    path = "|".join(lvl)
    parent = "|".join(lvl[:5])
    gran = str(m["granularity"])

    no_sig = st == S_NONE
    trail = st == S_TRAIL
    lowc = sid in LOWCONF
    champ_ok = str(ch["champion_validity"]) == V_OK

    neg_bt = int(a["negative_prediction_count"].sum())
    ext_bt = int(a["extreme_ratio_count"].sum())
    neg_fc = int((f["negative_forecast_flag"] == "TRUE").sum())
    ext_fc = int((f["extreme_forecast_flag"] == "TRUE").sum())

    badges, msgs = [], []
    if no_sig:
        badges.append("NO_SIGNAL")
        msgs.append("This series is available in Viewer and Forecast, but every "
                    "observed actual is zero, so the champion model is a technical "
                    "tie-break and is NOT a meaningful recommendation.")
    if trail:
        badges.append("TRAILING_ZERO_LATEST_ACTUAL")
        msgs.append("The most recent observed actual is zero; recent history is a "
                    "zero tail even though the series carries signal overall.")
    if lowc:
        badges.append("LOW_CONFIDENCE_BACKTEST_WINDOW_ZERO")
        msgs.append("This series has historical signal, but its backtest evaluation "
                    "window falls entirely in a zero tail, so ranking confidence is "
                    "reduced and percentage errors are not computable.")
    if not champ_ok:
        badges.append("CHAMPION_NOT_MEANINGFUL")
    if neg_bt:
        badges.append("NEGATIVE_BACKTEST_PREDICTIONS_PRESENT")
    if ext_bt:
        badges.append("EXTREME_BACKTEST_RATIO_PRESENT")
    if neg_fc:
        badges.append("NEGATIVE_FORECAST_PRESENT")
    if ext_fc:
        badges.append("EXTREME_FORECAST_PRESENT")
    if not badges:
        badges = ["NONE"]
    if not msgs:
        msgs = ["No material caveat for this series."]

    mw, ms = med(a["wape"]), med(a["smape"])
    nav.append(dict(zip(NAVF, [
        f"NAV_{i:04d}", OP, m["cohort_id"], sid, m["metric"], m["db_type"],
        m["scenario"], m["segment"], gran, m["key"], m["route_path"],
        *lvl, KEY_AXIS.get(gran, "ROUTING_OR_IDENTIFIER_VALUE"),
        f"{m['metric']} / {m['route_path']} / {m['key']}",
        f"{m['metric']}|{m['route_path']}|{m['key']}", path, parent,
        str(r["product"]).upper(), str(r["forecast"]).upper(),
        str(r["ranking"]).upper(), str(champ_ok).upper(),
        str(r["product"]).upper(), str(r["backtest"]).upper(),
        str(r["accuracy"]).upper(), str(r["ranking"]).upper(),
        str(r["forecast"]).upper(),
        ch["model_name"], float(ch["primary_rank_value"]),
        ch["primary_rank_metric"], ch["champion_validity"], ch["champion_reason"],
        ch["ranking_policy_version"],
        st, str(no_sig).upper(), str(trail).upper(), str(lowc).upper(),
        "|".join(badges), " ".join(msgs),
        FTYPE, FSTEPS, f"{FSTEPS} daily steps ahead of the last observed actual",
        str(f["forecast_date"].min())[:10], str(f["forecast_date"].max())[:10],
        "MEDIAN_SERIES_WEIGHTED", "median",
        mw, ms, med(a["rmse"]), med(a["mae"]),
        "COMPUTED" if mw == mw else NCS, "COMPUTED" if ms == ms else NCS,
        neg_bt, ext_bt, neg_fc, ext_fc,
        "DERIVED_FROM_GOVERNED_ARTIFACTS", man_flag.get(sid, "MISSING"), "FALSE",
        "NOT_APPLICABLE_OPERATIONAL_ROW",
        AVAIL if badges == ["NONE"] else AVAIL_C,
        "Key is a routing/display value at this granularity, not a globally unique "
        "axis; the six-level filter path is what identifies the series."])))
NAV = pd.DataFrame(nav)
print(f"navigation_contract: {len(NAV)} rows | product_status "
      f"{NAV['product_status'].value_counts().to_dict()}")

# ================================================ taxonomy counts
def block(scope, keys, g, fv):
    ch_models = g[g["champion_visible"] == "TRUE"]["champion_model_name"]
    cav = [c for row in g["caveat_badge"] for c in str(row).split("|") if c != "NONE"]
    return {
        "count_scope": scope,
        "parent_filter_path": fv.get("parent_filter_path", NA),
        "filter_axis": fv.get("filter_axis", NA),
        "filter_value": fv.get("filter_value", NA),
        **{a: fv.get(a, NA) for a in AXES},
        "operational_series_count": len(g),
        "viewer_visible_count": int((g["viewer_visible"] == "TRUE").sum()),
        "forecast_visible_count": int((g["forecast_visible"] == "TRUE").sum()),
        "ranking_visible_count": int((g["ranking_visible"] == "TRUE").sum()),
        "champion_visible_count": int((g["champion_visible"] == "TRUE").sum()),
        "no_signal_count": int((g["no_signal_flag"] == "TRUE").sum()),
        "trailing_zero_count": int((g["trailing_zero_latest_actual_flag"] == "TRUE").sum()),
        "low_confidence_backtest_window_count": int(
            (g["low_confidence_backtest_window_flag"] == "TRUE").sum()),
        "product_ready_count": int((g["product_ready"] == "TRUE").sum()),
        "available_count": int((g["product_status"] == AVAIL).sum()),
        "available_with_caveat_count": int((g["product_status"] == AVAIL_C).sum()),
        "not_available_count": int((~g["product_status"].isin([AVAIL, AVAIL_C])).sum()),
        "forecast_type": FTYPE, "forecast_steps": FSTEPS,
        "governed_model_count": len(GOVERNED),
        "median_wape": med(g["median_wape"]), "median_smape": med(g["median_smape"]),
        "median_rmse": med(g["median_rmse"]), "median_mae": med(g["median_mae"]),
        "champion_model_count_summary": "|".join(
            f"{k}:{v}" for k, v in sorted(ch_models.value_counts().items())) or "NONE",
        "caveat_count_summary": "|".join(
            f"{k}:{v}" for k, v in sorted(pd.Series(cav).value_counts().items()))
        if cav else "NONE",
        "recommended_aggregate_statistic": "median",
        "taxonomy_status": "AVAILABLE" if len(g) else "NOT_AVAILABLE",
        "p7_notes": ("Medians are series-weighted: each series contributes its own "
                     "median once, never one row per backtest row. Not computable "
                     "medians are left empty, never coerced to zero."),
    }


tax = [block("GLOBAL", [], NAV, {})]
SCOPES = [
    ("BY_METRIC", ["metric"]),
    ("BY_METRIC_DB_TYPE", ["metric", "db_type"]),
    ("BY_METRIC_DB_TYPE_SCENARIO", ["metric", "db_type", "scenario"]),
    ("BY_METRIC_DB_TYPE_SCENARIO_SEGMENT", ["metric", "db_type", "scenario", "segment"]),
    ("BY_METRIC_DB_TYPE_SCENARIO_SEGMENT_GRANULARITY",
     ["metric", "db_type", "scenario", "segment", "granularity"]),
    ("BY_FULL_FILTER_PATH", AXES),
]
for scope, keys in SCOPES:
    for k, g in NAV.groupby(keys, sort=True):
        k = k if isinstance(k, tuple) else (k,)
        fv = dict(zip(keys, [str(x) for x in k]))
        fv["filter_axis"] = keys[-1]
        fv["filter_value"] = str(k[-1])
        fv["parent_filter_path"] = "|".join(str(x) for x in k[:-1]) if len(k) > 1 else "GLOBAL"
        tax.append(block(scope, keys, g, fv))
for scope, col in (("BY_ROUTE_PATH", "route_path"),
                   ("BY_SIGNAL_QUALITY", "signal_quality_status"),
                   ("BY_CHAMPION_VALIDITY", "champion_validity")):
    for k, g in NAV.groupby(col, sort=True):
        tax.append(block(scope, [col], g, {
            "filter_axis": col, "filter_value": str(k), "parent_filter_path": "GLOBAL",
            **({"metric": str(g["metric"].iloc[0])} if col == "route_path"
               and g["metric"].nunique() == 1 else {})}))
TAX = pd.DataFrame(tax)
TAX.insert(0, "count_row_id", [f"TAX_{i:04d}" for i in range(1, len(TAX) + 1)])
TAXF = ["count_row_id", "count_scope", "parent_filter_path", "filter_axis",
        "filter_value"] + AXES + [
    "operational_series_count", "viewer_visible_count", "forecast_visible_count",
    "ranking_visible_count", "champion_visible_count", "no_signal_count",
    "trailing_zero_count", "low_confidence_backtest_window_count",
    "product_ready_count", "available_count", "available_with_caveat_count",
    "not_available_count", "forecast_type", "forecast_steps", "governed_model_count",
    "median_wape", "median_smape", "median_rmse", "median_mae",
    "champion_model_count_summary", "caveat_count_summary",
    "recommended_aggregate_statistic", "taxonomy_status", "p7_notes"]
TAX = TAX[TAXF]
print(f"taxonomy_counts: {len(TAX)} rows across "
      f"{TAX['count_scope'].nunique()} scopes")

# ================================================ promotion gate
gl = TAX[TAX["count_scope"] == "GLOBAL"].iloc[0]
bym = TAX[TAX["count_scope"] == "BY_METRIC"].set_index("filter_value")
gate = {
    "140 operational rows": len(NAV[NAV["contract_row_type"] == OP]) == 140,
    "all 140 MVP series present": set(NAV["series_id"]) == set(MAN["series_id"]),
    "every operational row product_ready": bool((NAV["product_ready"] == "TRUE").all()),
    "every operational row viewer_visible": bool((NAV["viewer_visible"] == "TRUE").all()),
    "every operational row forecast_visible": bool((NAV["forecast_visible"] == "TRUE").all()),
    "viewer/forecast parity": len(NAV[(NAV["viewer_visible"] == "TRUE")
                                      & (NAV["forecast_visible"] != "TRUE")]) == 0,
    "manifest flag never used": bool((NAV["manifest_flag_used_for_readiness"] == "FALSE").all()),
    "one champion name per row": bool(NAV["champion_model_name"].notna().all()),
    "no-signal champions hidden": bool(
        (NAV[NAV["signal_quality_status"] == S_NONE]["champion_visible"] == "FALSE").all()),
    "champion_visible only when meaningful": bool(
        (NAV[NAV["champion_visible"] == "TRUE"]["champion_validity"] == V_OK).all()),
    "no-signal rows AVAILABLE_WITH_CAVEAT": bool(
        (NAV[NAV["signal_quality_status"] == S_NONE]["product_status"] == AVAIL_C).all()),
    "no operational row NOT_AVAILABLE": bool(
        NAV["product_status"].isin([AVAIL, AVAIL_C]).all()),
    "forecast type honest": set(NAV["forecast_type"]) == {FTYPE},
    "forecast steps 30": set(NAV["forecast_steps"]) == {FSTEPS},
    "GLOBAL count == 140": int(gl["operational_series_count"]) == 140,
    "BY_METRIC reconciles 50/50/20/20": all(
        int(bym.loc[k, "operational_series_count"]) == v
        for k, v in (("HDD", 50), ("SSD", 50), ("CPU", 20), ("IOPS", 20))),
    "taxonomy sums to navigation": int(
        TAX[TAX["count_scope"] == "BY_METRIC"]["operational_series_count"].sum()) == 140,
    "only governed models as champions": set(NAV["champion_model_name"]) <= set(GOVERNED),
}
print("--- promotion gate ---")
for k, v in gate.items():
    print(f"  [{'OK  ' if v else 'FAIL'}] {k}")
if not all(gate.values()):
    raise SystemExit(f"GATE FAILED: {[k for k, v in gate.items() if not v]}")

NAV.to_parquet(PROC / "navigation_contract.parquet", index=False, engine="pyarrow",
               compression="snappy")
NAV.to_csv(PROC / "navigation_contract.csv", index=False)
TAX.to_parquet(PROC / "taxonomy_counts.parquet", index=False, engine="pyarrow",
               compression="snappy")
TAX.to_csv(PROC / "taxonomy_counts.csv", index=False)
print("PROMOTED navigation_contract + taxonomy_counts (parquet + csv)")

frozen_after = {p.name: sha256_file(p) for p in PROC.iterdir()
                if any(p.name.startswith(k) for k in FROZEN)}
touched = sorted(n for n in frozen_before if frozen_before[n] != frozen_after.get(n))
if touched:
    raise SystemExit(f"V6_24_P7_BLOCKED_GOVERNANCE_VIOLATION: {touched}")
print(f"governance OK | {len(frozen_before)} frozen artifacts byte-identical")

NAV.to_pickle(OUT / "_p7_nav.pkl")
TAX.to_pickle(OUT / "_p7_tax.pkl")
json.dump({"nav_rows": len(NAV), "tax_rows": len(TAX), "ready": n_ready,
           "stale_would_exclude": n_stale, "lowconf": sorted(LOWCONF),
           "frozen": len(frozen_before), "ts": TS,
           "p6c_pass": int((P6CV["result"] == "PASS").sum()), "p6c_total": len(P6CV),
           "p6b_pass": int((P6BV["result"] == "PASS").sum()), "p6b_total": len(P6BV)},
          (OUT / "_p7.json").open("w", encoding="utf-8"), indent=1, default=str)
print("\npart 1 complete")
