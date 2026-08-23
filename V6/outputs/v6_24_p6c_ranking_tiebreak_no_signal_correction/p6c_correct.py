"""V6.24-P6C - Ranking tie-break / no-signal series correction.

Recomputes model_rankings from accuracy_metrics only, fixing the P6 defect where
metric AVAILABILITY was used as an ordering level instead of accuracy.

Modifies exactly two canonical artifacts: model_rankings (overwrite) and
series_signal_quality (new). Everything else is verified frozen.
"""
from __future__ import annotations

import csv
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
V6 = OUT.parents[1]
REPO = V6.parent
PROC = V6 / "data" / "processed" / "v6_24_mvp_cohort"
P6B = V6 / "outputs" / "v6_24_p6b_governed_30_step_forecast_outputs"

POLICY = "P6C_RANKING_POLICY_V2"
TOL = 1e-12
NC = "STRUCTURALLY_NOT_COMPUTABLE"
S_NONE, S_TRAIL, S_OK = ("NO_SIGNAL_ALL_ZERO_ACTUALS", "TRAILING_ZERO_LATEST_ACTUAL",
                         "SIGNAL_PRESENT")
V_BAD, V_OK = "NOT_MEANINGFUL_NO_SIGNAL", "MEANINGFUL_ACCURACY_RANKING"
R_BAD = "NO_SIGNAL_ALL_ZERO_ACTUALS_TECHNICAL_TIE_BREAK"
R_OK = "LOWEST_VALID_ERROR_BY_P6C_POLICY"

GOVERNED = ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
            "ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta",
            "LightGBM", "LinearRegression", "XGBoost",
            "FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"]
PROHIBITED = ["NBEATS", "NHITS", "FastNeuralAR_MLP"]
# Deterministic tie-break, applied ONLY after every numeric metric has tied.
TIEBREAK = ["ETS Explicit", "ARIMA_Fixed", "AutoARIMA", "ETS_Current", "Theta",
            "LinearRegression", "LightGBM", "XGBoost", "FixedGrowth_3",
            "FixedGrowth_4", "FixedGrowth_6", "FixedGrowth_1_5",
            "NLIN-DLIN_FIXED", "SMLP-TCN", "FNAR-V2"]
TB_IDX = {m: i for i, m in enumerate(TIEBREAK)}

# Metric sequences. Lower is better for every entry.
CASE1 = ["wape", "smape", "rmse", "mae", "median_absolute_error",
         "negative_prediction_count", "extreme_ratio_count"]
CASE2 = ["mae", "rmse", "median_absolute_error", "smape",
         "negative_prediction_count", "extreme_ratio_count"]
STATUS_OF = {"wape": "wape_status", "smape": "smape_status", "mape": "mape_status"}

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
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def content_hash(df: pd.DataFrame) -> str:
    """Order-independent hash of the frame's content."""
    s = df.sort_index(axis=1)
    s = s.sort_values(list(s.columns)).reset_index(drop=True)
    return hashlib.sha256(s.to_csv(index=False).encode("utf-8")).hexdigest()


def git_clean(pathspec):
    try:
        r = subprocess.run(["git", "status", "--porcelain", "--", pathspec],
                           cwd=REPO, capture_output=True, text=True, timeout=90)
        return r.stdout.strip()
    except Exception as e:  # noqa: BLE001
        return f"GIT_CHECK_ERROR: {e}"


# ================================================ preflight
print("P6C START - ranking tie-break / no-signal correction")
P6BV = pd.read_csv(P6B / "v6_24_p6b_validation.csv")
p6b_ok = bool((P6BV["result"] == "PASS").all())
acc_p = PROC / "accuracy_metrics.parquet"
rk_p = PROC / "model_rankings.parquet"

F = ["check_id", "check", "expected", "observed", "result", "blocking_token"]
pf = [dict(zip(F, r)) for r in [
    ("PF01", "P6B validation passed", "all PASS",
     f"{int((P6BV['result'] == 'PASS').sum())}/{len(P6BV)} PASS",
     "PASS" if p6b_ok else "FAIL", "V6_24_P6C_BLOCKED_P6B_NOT_PASS"),
    ("PF02", "accuracy_metrics exists", "present",
     "present" if acc_p.exists() else "MISSING",
     "PASS" if acc_p.exists() else "FAIL",
     "V6_24_P6C_BLOCKED_ACCURACY_METRICS_MISSING"),
    ("PF03", "model_rankings exists", "present",
     "present" if rk_p.exists() else "MISSING",
     "PASS" if rk_p.exists() else "FAIL",
     "V6_24_P6C_BLOCKED_MODEL_RANKINGS_MISSING"),
    ("PF04", "navigation_contract absent", "absent",
     "absent" if not (PROC / "navigation_contract.parquet").exists() else "PRESENT",
     "PASS" if not (PROC / "navigation_contract.parquet").exists() else "FAIL",
     "V6_24_P6C_BLOCKED_SCOPE_VIOLATION"),
    ("PF05", "taxonomy_counts absent", "absent",
     "absent" if not (PROC / "taxonomy_counts.parquet").exists() else "PRESENT",
     "PASS" if not (PROC / "taxonomy_counts.parquet").exists() else "FAIL",
     "V6_24_P6C_BLOCKED_SCOPE_VIOLATION"),
]]
write("v6_24_p6c_preflight_check.csv", F, pf)
if not (p6b_ok and acc_p.exists() and rk_p.exists()):
    bad = [r["blocking_token"] for r in pf if r["result"] == "FAIL"]
    raise SystemExit(f"PREFLIGHT FAILED -> {bad[0]}")
print(f"preflight OK | P6B {int((P6BV['result'] == 'PASS').sum())}/{len(P6BV)} PASS")

# ================================================ inputs + frozen fingerprints
ACT = pd.read_parquet(PROC / "actuals_normalized.parquet", engine="pyarrow")
ACC = pd.read_parquet(acc_p, engine="pyarrow")
OLD = pd.read_parquet(rk_p, engine="pyarrow")
MAN = pd.read_parquet(PROC / "cohort_manifest.parquet", engine="pyarrow")
ACT["series_date"] = pd.to_datetime(ACT["series_date"])

# model_rankings is the ONLY canonical artifact P6C may overwrite.
FROZEN = ["cohort_manifest", "actuals_normalized", "model_backtests_15_models",
          "source_forecast_baselines_normalized", "accuracy_metrics", "forecast_outputs"]
frozen_before = {p.name: (p.stat().st_size, sha256_file(p)) for p in PROC.iterdir()
                 if any(p.name.startswith(k) for k in FROZEN)}
print(f"fingerprinted {len(frozen_before)} frozen artifacts by size + sha256")

# ================================================ snapshot the pre-P6C rankings
OLD.to_parquet(OUT / "v6_24_p6c_original_model_rankings_snapshot.parquet",
               index=False, engine="pyarrow", compression="snappy")
OLD.to_csv(OUT / "v6_24_p6c_original_model_rankings_snapshot.csv", index=False)
HF = ["artifact", "path", "rows", "columns", "file_sha256", "content_sha256",
      "captured_at", "note"]
write("v6_24_p6c_original_model_rankings_hash.csv", HF, [dict(zip(HF, [
    "model_rankings (pre-P6C)", str(rk_p), len(OLD), len(OLD.columns),
    sha256_file(rk_p), content_hash(OLD), TS,
    "Immutable audit snapshot taken BEFORE the canonical artifact was overwritten"]))])
print("snapshot + hash of the pre-P6C rankings captured")

# ================================================ signal quality from actuals
rows = []
for sid, g in ACT.groupby("series_id"):
    g = g.sort_values("series_date")
    v = g["actual_value"].to_numpy(dtype=float)
    sab = float(np.abs(v).sum())
    latest = float(v[-1])
    allz = sab <= TOL
    latz = abs(latest) <= TOL
    status = S_NONE if allz else (S_TRAIL if latz else S_OK)
    rows.append({
        "cohort_id": g["cohort_id"].iloc[0], "series_id": sid,
        "metric": g["metric"].iloc[0], "db_type": g["db_type"].iloc[0],
        "scenario": g["scenario"].iloc[0], "segment": g["segment"].iloc[0],
        "granularity": g["granularity"].iloc[0], "key": g["key"].iloc[0],
        "route_path": g["route_path"].iloc[0],
        "n_actual_rows": int(len(v)),
        "min_actual_date": str(g["series_date"].min())[:10],
        "max_actual_date": str(g["series_date"].max())[:10],
        "sum_abs_actual": sab, "mean_actual": float(v.mean()),
        "max_abs_actual": float(np.abs(v).max()), "latest_actual_value": latest,
        "all_actuals_zero": "TRUE" if allz else "FALSE",
        "latest_actual_zero": "TRUE" if latz else "FALSE",
        "nonzero_actual_count": int((np.abs(v) > TOL).sum()),
        "zero_actual_count": int((np.abs(v) <= TOL).sum()),
        "signal_quality_status": status,
        "zero_tolerance": TOL,
        "derived_from": "processed/v6_24_mvp_cohort/actuals_normalized.parquet",
    })
SQ = pd.DataFrame(rows)
SQ.to_parquet(PROC / "series_signal_quality.parquet", index=False, engine="pyarrow",
              compression="snappy")
SQ.to_csv(PROC / "series_signal_quality.csv", index=False)
SIG = dict(zip(SQ["series_id"], SQ["signal_quality_status"]))
counts = SQ["signal_quality_status"].value_counts().to_dict()
print(f"signal quality derived: {counts}")

SF = ["signal_quality_status", "series_count", "metrics_affected",
      "accuracy_rows_affected", "min_sum_abs_actual", "max_sum_abs_actual",
      "ranking_treatment", "viewer_treatment"]
srows = []
for st in (S_NONE, S_TRAIL, S_OK):
    g = SQ[SQ["signal_quality_status"] == st]
    if not len(g):
        continue
    srows.append(dict(zip(SF, [
        st, len(g), "|".join(sorted(g["metric"].unique())),
        int(len(ACC[ACC["series_id"].isin(g["series_id"])])),
        f"{g['sum_abs_actual'].min():.6g}", f"{g['sum_abs_actual'].max():.6g}",
        "MAE as primary (WAPE structurally undefined)" if st == S_NONE
        else "WAPE as primary when computable for all 15 models",
        "Suppress champion as a recommendation" if st == S_NONE
        else "Champion is a meaningful recommendation"])))
write("v6_24_p6c_signal_quality_summary.csv", SF, srows)

NSF = ["series_id", "metric", "db_type", "scenario", "granularity", "key",
       "n_actual_rows", "min_actual_date", "max_actual_date", "sum_abs_actual",
       "max_abs_actual", "latest_actual_value", "nonzero_actual_count",
       "signal_quality_status", "note"]
write("v6_24_p6c_no_signal_series_detail.csv", NSF, [
    {**{k: r[k] for k in NSF if k != "note"},
     "note": "Every observation is zero within tolerance 1e-12; WAPE and MAPE are "
             "structurally undefined and a champion is a technical tie-break only"}
    for _, r in SQ[SQ["signal_quality_status"] == S_NONE].iterrows()])

# ================================================ corrected ranking
def computable(g, m):
    """A metric is usable for a series only if it is computable for ALL 15 models."""
    if m in STATUS_OF:
        if not (g[STATUS_OF[m]] == "COMPUTED").all():
            return False
    return bool(np.isfinite(g[m].to_numpy(dtype=float)).all())


def discriminating(g, m):
    """A constant metric carries no ranking information, even when computable."""
    return g[m].astype(float).nunique() > 1


new_rows, delta_rows, policy_rows = [], [], []
old_champ = dict(zip(OLD[OLD["is_series_champion"] == "TRUE"]["series_id"],
                     OLD[OLD["is_series_champion"] == "TRUE"]["model_name"]))
old_pm = dict(zip(OLD[OLD["is_series_champion"] == "TRUE"]["series_id"],
                  OLD[OLD["is_series_champion"] == "TRUE"]["primary_rank_metric"]))
old_pv = dict(zip(OLD[OLD["is_series_champion"] == "TRUE"]["series_id"],
                  OLD[OLD["is_series_champion"] == "TRUE"]["primary_rank_value"]))

for sid, g in ACC.groupby("series_id"):
    g = g.copy()
    st = SIG[sid]
    seq = CASE2 if st == S_NONE else CASE1
    # THE FIX: the metric sequence is resolved ONCE PER SERIES, using only metrics
    # computable for all 15 models. P6 resolved it per model, which let a model win
    # merely because its metric happened to be computable.
    usable = [m for m in seq if computable(g, m)]
    if not usable:
        usable = ["rmse"]
    primary = next((m for m in usable if discriminating(g, m)), usable[0])
    p_i = usable.index(primary)
    sort_keys = usable[p_i:]

    g["_tb"] = g["model_name"].map(TB_IDX)
    g = g.sort_values(sort_keys + ["_tb"], ascending=True).reset_index(drop=True)

    def stat(r, m):
        return r[STATUS_OF[m]] if m in STATUS_OF else "COMPUTED"

    sec = sort_keys[1] if len(sort_keys) > 1 else ""
    ter = sort_keys[2] if len(sort_keys) > 2 else ""
    for i, r in g.iterrows():
        champ = i == 0
        new_rows.append({
            "cohort_id": r["cohort_id"], "series_id": sid, "metric": r["metric"],
            "db_type": r["db_type"], "scenario": r["scenario"], "segment": r["segment"],
            "granularity": r["granularity"], "key": r["key"],
            "route_path": r["route_path"], "model_name": r["model_name"],
            "primary_rank_metric": primary,
            "primary_rank_value": float(r[primary]),
            "primary_rank_status": stat(r, primary),
            "secondary_rank_metric": sec,
            "secondary_rank_value": float(r[sec]) if sec else np.nan,
            "secondary_rank_status": stat(r, sec) if sec else "NOT_APPLICABLE",
            "tertiary_rank_metric": ter,
            "tertiary_rank_value": float(r[ter]) if ter else np.nan,
            "tertiary_rank_status": stat(r, ter) if ter else "NOT_APPLICABLE",
            "rank_within_series": i + 1,
            "is_series_champion": "TRUE" if champ else "FALSE",
            "champion_validity": (V_BAD if st == S_NONE else V_OK) if champ else "NOT_CHAMPION",
            "champion_reason": (R_BAD if st == S_NONE else R_OK) if champ else "NOT_CHAMPION",
            "signal_quality_status": st,
            "n_backtest_rows": int(r["n_backtest_rows"]),
            "negative_prediction_count": int(r["negative_prediction_count"]),
            "extreme_ratio_count": int(r["extreme_ratio_count"]),
            "source_generation_status": r["source_generation_status"],
            "ranking_policy_version": POLICY,
            "caveat": r["caveat"],
            "model_family": r["model_family"],
        })

    ch = g.iloc[0]
    prev, cur = old_champ[sid], ch["model_name"]
    changed = prev != cur
    if changed or st == S_NONE:
        prev_mae = float(g[g["model_name"] == prev]["mae"].iloc[0])
        delta_rows.append({
            "series_id": sid, "metric": ch["metric"],
            "previous_champion": prev, "corrected_champion": cur,
            "champion_changed": "TRUE" if changed else "FALSE",
            "previous_champion_validity": "NOT_RECORDED_BY_P6",
            "corrected_champion_validity": V_BAD if st == S_NONE else V_OK,
            "signal_quality_status": st,
            "previous_primary_rank_metric": old_pm[sid],
            "corrected_primary_rank_metric": primary,
            "previous_primary_rank_value": round(float(old_pv[sid]), 9),
            "corrected_primary_rank_value": round(float(ch[primary]), 9),
            "previous_champion_mae": round(prev_mae, 9),
            "corrected_champion_mae": round(float(ch["mae"]), 9),
            "mae_improvement": round(prev_mae - float(ch["mae"]), 9),
            "reason_for_change": (
                "P6 ranked metric AVAILABILITY above accuracy: it preferred a model with a "
                f"computable smape over models with lower {primary}. P6C resolves the metric "
                "sequence once per series, so only comparable numbers are compared."
                if changed else
                "Champion unchanged; validity flag added because the series has no signal")})

CORR = pd.DataFrame(new_rows)
n_changed = sum(1 for d in delta_rows if d["champion_changed"] == "TRUE")
print(f"corrected rankings: {len(CORR)} rows | {n_changed} champions changed")

# ================================================ promotion gate
champs = CORR[CORR["is_series_champion"] == "TRUE"]
gate = {
    "2,100 rows": len(CORR) == 2100,
    "140 series": CORR["series_id"].nunique() == 140,
    "15 models": CORR["model_name"].nunique() == 15,
    "2,100 series-model pairs": CORR.groupby(["series_id", "model_name"]).ngroups == 2100,
    "each series has all 15 models": bool(
        CORR.groupby("series_id")["model_name"].nunique().eq(15).all()),
    "ranks 1..15 complete per series": bool(
        CORR.groupby("series_id")["rank_within_series"].apply(
            lambda x: sorted(x) == list(range(1, 16))).all()),
    "exactly one champion per series": len(champs) == 140 and bool(
        champs.groupby("series_id").size().eq(1).all()),
    "only governed models": set(CORR["model_name"]) == set(GOVERNED),
    "no prohibited models": not any(m in set(CORR["model_name"]) for m in PROHIBITED),
    "policy version stamped": set(CORR["ranking_policy_version"]) == {POLICY},
    "no-signal use mae as primary": bool(
        (CORR[CORR["signal_quality_status"] == S_NONE]["primary_rank_metric"] == "mae").all()),
    "no-signal champions flagged not meaningful": bool(
        (champs[champs["signal_quality_status"] == S_NONE]["champion_validity"]
         == V_BAD).all()),
    "signal champions flagged meaningful": bool(
        (champs[champs["signal_quality_status"] != S_NONE]["champion_validity"]
         == V_OK).all()),
}
print("--- promotion gate ---")
for k, v in gate.items():
    print(f"  [{'OK  ' if v else 'FAIL'}] {k}")
if not all(gate.values()):
    raise SystemExit(f"GATE FAILED: {[k for k, v in gate.items() if not v]}")

CORR.to_parquet(rk_p, index=False, engine="pyarrow", compression="snappy")
CORR.to_csv(PROC / "model_rankings.csv", index=False)
print("PROMOTED corrected model_rankings.parquet / .csv")

write("v6_24_p6c_corrected_model_rankings_hash.csv", HF, [dict(zip(HF, [
    "model_rankings (post-P6C)", str(rk_p), len(CORR), len(CORR.columns),
    sha256_file(rk_p), content_hash(CORR), TS,
    f"Canonical artifact rewritten under {POLICY}"]))])

DF = ["series_id", "metric", "previous_champion", "corrected_champion",
      "champion_changed", "previous_champion_validity", "corrected_champion_validity",
      "signal_quality_status", "previous_primary_rank_metric",
      "corrected_primary_rank_metric", "previous_primary_rank_value",
      "corrected_primary_rank_value", "previous_champion_mae",
      "corrected_champion_mae", "mae_improvement", "reason_for_change"]
write("v6_24_p6c_ranking_delta.csv", DF, delta_rows)

# ================================================ governance re-fingerprint
frozen_after = {p.name: (p.stat().st_size, sha256_file(p)) for p in PROC.iterdir()
                if any(p.name.startswith(k) for k in FROZEN)}
touched = sorted(n for n in frozen_before if frozen_before[n] != frozen_after.get(n))
if touched:
    raise SystemExit(f"V6_24_P6C_BLOCKED_GOVERNANCE_VIOLATION: {touched}")
print(f"governance OK | {len(frozen_before)} frozen artifacts byte-identical")

json.dump({"policy": POLICY, "rows": len(CORR), "changed": n_changed,
           "counts": counts, "frozen_verified": len(frozen_before),
           "p6b_pass": int((P6BV["result"] == "PASS").sum()), "p6b_total": len(P6BV),
           "ts": TS},
          (OUT / "_p6c.json").open("w", encoding="utf-8"), indent=1, default=str)
CORR.to_pickle(OUT / "_p6c_corr.pkl")
OLD.to_pickle(OUT / "_p6c_old.pkl")
SQ.to_pickle(OUT / "_p6c_sq.pkl")
print("\npart 1 complete")
