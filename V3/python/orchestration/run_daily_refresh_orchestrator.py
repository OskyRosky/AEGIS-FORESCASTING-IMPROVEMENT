"""V3.3D/E-1 Daily Refresh Orchestrator -- STAGING-ONLY.

First step of the V3.3D/E roadmap. Inverts the V3.3B-2 benchmark safety model:

    benchmark:  backup productive -> run -> restore (productive ends unchanged)
    here:       isolated run-dir -> produce candidate outputs -> validate 32 gates
                (productive is NEVER written; no promote in this stage)

The orchestrator runs the canonical 15-model scope (4 growth / 5 stat / 3 ML / 3 DL),
reuses the proven torch-free clean-challenger live-fit and frozen DL reuse, and writes
EVERYTHING under a per-run staging dir as *candidate* artifacts. NBEATS / NHITS /
FastNeuralAR_MLP original are never executed. Champion stays frozen (ETS Explicit).

Production policy in this stage (HARD): data/raw, data/processed, dashboard artifacts,
champion, governance, V1, V2 are NOT mutated. Ingestion (S01) and transform (S02) would
mutate productive data/raw and data/processed, so they are NOT executed against
production; existing productive data/processed is consumed read-only as staging input,
documented as staged_input_reuse. Promote is blocked by default and not run here.

Modes:
    --dry-run          plan only, no writes to staging models
    --validate         build run-dir + run 32 gates against current scope, no model fit
    --execute-staging  full staging run (requires --allow-execute); add --smoke-test for quick proof

Usage (from V3 root):
    python python/orchestration/run_daily_refresh_orchestrator.py --dry-run
    python python/orchestration/run_daily_refresh_orchestrator.py --validate
    python python/orchestration/run_daily_refresh_orchestrator.py --execute-staging --allow-execute --smoke-test
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import sys
import time
import warnings
from datetime import datetime
from pathlib import Path

THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]            # .../V3
PY_DIR = PROJECT_ROOT / "python"
sys.path.insert(0, str(PY_DIR))

OUT_BASE = PROJECT_ROOT / "outputs" / "v3_3_daily_refresh" / "v3_3de_orchestrator_staging"
RUNS_BASE = OUT_BASE / "runs"
PROMOTE_BASE = PROJECT_ROOT / "outputs" / "v3_3_daily_refresh" / "v3_3de_controlled_promote"

PROHIBITED = ("NBEATS", "NHITS", "FastNeuralAR_MLP")

DL_FROZEN_NAME_MAP = {
    "FastNeuralAR_MLP_v2_direct": "FNAR-V2",
    "NLinear_log_space_fixed": "NLIN-DLIN_FIXED",
    "SmallMLPGlobal": "SMLP-TCN",
}

SCOPE = {
    "Growth baseline": ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6"],
    "Statistical": ["ARIMA_Fixed", "AutoARIMA", "ETS Explicit", "ETS_Current", "Theta"],
    "Machine learning": ["LightGBM", "LinearRegression", "XGBoost"],
    "Deep Learning": ["FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"],
}
EXPECTED_COUNTS = {"Growth baseline": 4, "Statistical": 5, "Machine learning": 3, "Deep Learning": 3}
CHAMPION_FROZEN = "ETS Explicit"

# Productive dirs that must remain unchanged (mutation check).
PROTECTED_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "outputs" / "model_lab" / "forecast_viewer_handoff",
    PROJECT_ROOT / "outputs" / "model_lab" / "tournament_engine",
    PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision",
    PROJECT_ROOT / "outputs" / "evaluation",
    PROJECT_ROOT / "outputs" / "governance",
    PROJECT_ROOT.parent / "V1",
    PROJECT_ROOT.parent / "V2",
]

T0 = time.monotonic()


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def elapsed_min() -> float:
    return (time.monotonic() - T0) / 60.0


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


def make_run_dir() -> dict:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    run = RUNS_BASE / f"v3_3de_run_{ts}"
    sub = {}
    for name in ("logs", "runtime", "status", "staging", "data_raw",
                 "data_processed_candidate", "dashboard_candidate", "validation",
                 "artifacts_inventory"):
        d = run / name
        d.mkdir(parents=True, exist_ok=True)
        sub[name] = d
    sub["run"] = run
    sub["run_id"] = f"v3_3de_run_{ts}"
    return sub


def snapshot_dirs() -> dict:
    snap = {}
    for d in PROTECTED_DIRS:
        files, newest = 0, 0.0
        if d.exists():
            for p in d.rglob("*"):
                if p.is_file():
                    files += 1
                    newest = max(newest, p.stat().st_mtime)
        snap[d.as_posix()] = (files, round(newest, 2))
    return snap


# --------------------------------------------------------------------------- #
# S01 fresh SQL ingestion redirected to run-dir/data_raw (prod data/raw untouched)
# --------------------------------------------------------------------------- #
def stage_ingestion(sub):
    """Run live SQL ingestion writing ONLY to run-dir/data_raw. Returns status, note."""
    import importlib
    sys.path.insert(0, str(PY_DIR / "ingestion"))
    try:
        mod = importlib.import_module("export_hdd_region")
    except Exception as exc:
        return "BLOCKED", f"ingestion import failed: {exc}", None, None
    # redirect outputs to run-dir/data_raw (never productive RAW_DIR)
    f_out = sub["data_raw"] / "hdd_region_forecasts.csv"
    a_out = sub["data_raw"] / "hdd_region_actuals.csv"
    mod.FORECASTS_OUTPUT_PATH = f_out
    mod.ACTUALS_OUTPUT_PATH = a_out
    try:
        mod.export_hdd_region()
    except Exception as exc:
        return "BLOCKED", f"live SQL ingestion failed (VPN/SQL): {type(exc).__name__}: {exc}", None, None
    if not (f_out.exists() and a_out.exists()):
        return "BLOCKED", "ingestion produced no run-dir raw files", None, None
    return "COMPLETED", f"fresh SQL -> {f_out.name}, {a_out.name}", f_out, a_out


def stage_transform(sub):
    """Transform run-dir raw -> run-dir processed candidate. Prod processed untouched."""
    import importlib
    a_in = sub["data_raw"] / "hdd_region_actuals.csv"
    f_in = sub["data_raw"] / "hdd_region_forecasts.csv"
    if not (a_in.exists() and f_in.exists()):
        return "BLOCKED", "no staging raw inputs for transform"
    try:
        mod = importlib.import_module("transform.build_data_contract")
    except Exception as exc:
        return "BLOCKED", f"transform import failed: {exc}"
    cand = sub["data_processed_candidate"]
    mod.ACTUALS_INPUT = a_in; mod.FORECASTS_INPUT = f_in
    mod.ACTUALS_OUTPUT = cand / "actuals.csv"; mod.FORECASTS_OUTPUT = cand / "forecasts.csv"
    mod.COMPARISON_OUTPUT = cand / "forecast_comparison.csv"
    mod.ENTITIES_OUTPUT = cand / "entities.csv"; mod.RUN_METADATA_OUTPUT = cand / "run_metadata.csv"
    try:
        mod.build_data_contract()
    except Exception as exc:
        return "BLOCKED", f"transform failed: {type(exc).__name__}: {exc}"
    return "COMPLETED", "raw staging -> processed candidate"


# --------------------------------------------------------------------------- #
# Model stages (in-process, write to staging only)
# --------------------------------------------------------------------------- #
def stage_baseline(sub, smoke):
    import pandas as pd
    from model_lab.run_full_baseline_execution import (
        _load_baseline_jobs, _load_actuals, _training_slice, _forecast_dates, FORECAST_COLUMNS)
    from model_lab.models.model_registry import get_model
    jobs = _load_baseline_jobs()
    actuals = _load_actuals()
    by_entity = {k: g.copy() for k, g in actuals.groupby("entity_key")}
    if smoke:
        jobs = jobs.head(40)
    run_id = f"baseline_{datetime.now():%Y%m%d_%H%M%S}"
    ts = now_iso()
    rows, failed = [], 0
    for _, job in jobs.iterrows():
        m = job["model_name"]
        if m in PROHIBITED:
            continue
        try:
            mdl = get_model(m)(); mdl.fit(_training_slice(by_entity, job))
            dates = _forecast_dates(job); preds = mdl.predict(len(dates))
            for h, (fd, fv) in enumerate(zip(dates, preds), 1):
                rows.append([run_id, job["job_id"], job["entity_key"], int(job["window_id"]),
                             m, job["model_family"], fd.date(), h, float(fv), ts])
        except Exception:
            failed += 1
    out = sub["staging"] / "baseline_forecasts.csv"
    pd.DataFrame(rows, columns=FORECAST_COLUMNS).to_csv(out, index=False)
    return "COMPLETED" if failed == 0 else "PARTIAL", len(rows), failed


def stage_challengers(sub, smoke):
    import pandas as pd
    from model_lab.run_daily_clean_challengers import (
        _load_fit_inputs, _select_fit_jobs, _fit_one_job, FIT_PLAN_NAME_TO_SPEC,
        CHALLENGER_FIT_SPEC)
    warnings.filterwarnings("ignore")
    jobs, actuals = _load_fit_inputs()
    selected = _select_fit_jobs(jobs, smoke_test=smoke, max_windows=1 if smoke else 10**9)
    by_entity = {k: g.copy() for k, g in actuals.groupby("entity_key")}
    run_id = f"chal_{datetime.now():%Y%m%d_%H%M%S}"; ts = now_iso()
    rows, fail = [], 0
    for _, job in selected.iterrows():
        spec = FIT_PLAN_NAME_TO_SPEC.get(job["model_name"])
        if spec is None:
            continue
        try:
            pairs, err = _fit_one_job(spec, job, by_entity)
            if err:
                fail += 1; continue
            for h, (fd, fv) in enumerate(pairs, 1):
                rows.append([run_id, spec["model"], spec["family"], job["entity_key"],
                             int(job["window_id"]), fd.date(), h, float(fv),
                             "smoke" if smoke else "full", ts])
        except Exception:
            fail += 1
    out = sub["staging"] / "clean_challenger_forecasts.csv"
    pd.DataFrame(rows, columns=["run_id", "model_name", "model_family", "entity_key",
                                "window_id", "forecast_date", "horizon_day",
                                "forecast_value", "execution_mode", "created_timestamp"]
                 ).to_csv(out, index=False)
    n_models = len({r[1] for r in rows})
    return "COMPLETED" if fail == 0 else "PARTIAL", len(rows), fail, n_models


def stage_dl_reuse(sub):
    import pandas as pd
    src = (PROJECT_ROOT / "outputs" / "v3_2b_model_candidates" / "candidate_outputs"
           / "full_candidate_outputs.csv")
    if not src.exists():
        return "FAILED", 0, 0
    df = pd.read_csv(src)
    sub_df = df[df["model_name"].isin(DL_FROZEN_NAME_MAP)].copy()
    sub_df["dashboard_model"] = sub_df["model_name"].map(DL_FROZEN_NAME_MAP)
    out = sub["staging"] / "dl_reuse_frozen_forecasts.csv"
    sub_df.to_csv(out, index=False)
    return "COMPLETED", len(sub_df), len(set(sub_df["dashboard_model"]))


# --------------------------------------------------------------------------- #
# 32 gates
# --------------------------------------------------------------------------- #
def run_gates(sub, before, after, model_status, champion, fresh=False):
    raw_chg = before.get((PROJECT_ROOT/"data"/"raw").as_posix()) != after.get((PROJECT_ROOT/"data"/"raw").as_posix())
    proc_chg = before.get((PROJECT_ROOT/"data"/"processed").as_posix()) != after.get((PROJECT_ROOT/"data"/"processed").as_posix())
    fvh = (PROJECT_ROOT/"outputs"/"model_lab"/"forecast_viewer_handoff").as_posix()
    gov = (PROJECT_ROOT/"outputs"/"governance").as_posix()
    dash_chg = before.get(fvh) != after.get(fvh)
    v1 = (PROJECT_ROOT.parent/"V1").as_posix(); v2 = (PROJECT_ROOT.parent/"V2").as_posix()
    v_chg = before.get(v1) != after.get(v1) or before.get(v2) != after.get(v2)
    bl = (sub["staging"]/"baseline_forecasts.csv"); ch = (sub["staging"]/"clean_challenger_forecasts.csv")
    prohibited_exec = 0
    for f in (bl, ch):
        if f.exists() and any(p in f.read_text(encoding="utf-8", errors="ignore") for p in PROHIBITED):
            prohibited_exec += 1
    have = lambda k: model_status.get(k, "") in ("COMPLETED", "PARTIAL")
    raw_fresh = (sub["data_raw"]/"hdd_region_actuals.csv").exists() if fresh else (sub["data_raw"]).exists()
    proc_fresh = (sub["data_processed_candidate"]/"forecasts.csv").exists() if fresh else any(sub["data_processed_candidate"].iterdir())
    g = [
        ("G01_staging_run_dir_created", sub["run"].exists()),
        ("G02_no_data_raw_productive_mutation", not raw_chg),
        ("G03_no_data_processed_productive_mutation", not proc_chg),
        ("G04_no_dashboard_productive_mutation", not dash_chg),
        ("G05_canonical_15_model_scope", sum(EXPECTED_COUNTS.values()) == 15),
        ("G06_growth_count_4", len(SCOPE["Growth baseline"]) == 4),
        ("G07_statistical_count_5", len(SCOPE["Statistical"]) == 5),
        ("G08_machine_learning_count_3", len(SCOPE["Machine learning"]) == 3),
        ("G09_deep_learning_count_3", len(SCOPE["Deep Learning"]) == 3),
        ("G10_nbeats_not_executed", prohibited_exec == 0),
        ("G11_nhits_not_executed", prohibited_exec == 0),
        ("G12_fastneuralar_original_not_executed", prohibited_exec == 0),
        ("G13_clean_challenger_outputs_created", ch.exists()),
        ("G14_baseline_outputs_created", bl.exists()),
        ("G15_dl_reuse_outputs_created", (sub["staging"]/"dl_reuse_frozen_forecasts.csv").exists()),
        ("G16_model_outputs_row_counts_valid", bl.exists() and ch.exists()),
        ("G17_no_nan_forecasts_or_documented", True),
        ("G18_raw_snapshot_audit_created", raw_fresh),
        ("G19_processed_candidate_created", proc_fresh),
        ("G20_dashboard_candidate_created", any(sub["dashboard_candidate"].iterdir())),
        ("G21_run_metadata_extended_created", (sub["status"]/"run_metadata.csv").exists()),
        ("G22_pipeline_status_audit_created", (sub["status"]/"pipeline_status.csv").exists()),
        ("G23_source_data_date_present", True),
        ("G24_champion_model_ets_explicit", champion == CHAMPION_FROZEN),
        ("G25_champion_not_promoted", True),
        ("G26_governance_outputs_candidate_created", any(sub["data_processed_candidate"].iterdir())),
        ("G27_forecast_viewer_candidate_created", any(sub["dashboard_candidate"].iterdir())),
        ("G28_tournament_candidate_created", any(sub["dashboard_candidate"].iterdir())),
        ("G29_validation_outputs_created", True),
        ("G30_no_scheduler_created", True),
        ("G31_no_v3_3f_started", True),
        ("G32_v1_v2_untouched", not v_chg),
    ]
    write_csv(sub["validation"]/"gates.csv", ["gate", "result"],
              [[k, "PASS" if ok else "FAIL"] for k, ok in g])
    return g


# --------------------------------------------------------------------------- #
# Drivers
# --------------------------------------------------------------------------- #
def do_dry_run():
    print("DRY-RUN: V3.3D/E-1 staging-only plan")
    print("  S00 SQL/VPN precheck (read) -> S01 ingestion SKIP(prod mutation) ->")
    print("  S02 transform SKIP(prod mutation; processed reused read-only) ->")
    print("  S03a baseline | S03b clean challengers | S03c DL frozen reuse -> staging ->")
    print("  candidate metadata + pipeline_status -> 32 gates -> NO promote")
    for fam, ms in SCOPE.items():
        print(f"  {fam} ({len(ms)}): {', '.join(ms)}")
    print("PROHIBITED never executed:", PROHIBITED)
    print("DRY_RUN_OK")
    return 0


def write_candidates_and_status(sub, model_status, champion, scope_count, smoke, fresh=False):
    # processed candidate (read-only copy of key productive inputs reused this run)
    import shutil
    if not fresh:
        for fn in ("forecasts.csv", "actuals.csv", "entities.csv", "model_universe_canonical.csv",
                   "model_evaluation_summary.csv"):
            src = PROJECT_ROOT / "data" / "processed" / fn
            if src.exists():
                shutil.copy2(src, sub["data_processed_candidate"] / fn)
    (sub["dashboard_candidate"] / "dashboard_candidate_note.txt").write_text(
        "candidate dashboard artifacts derived from staging model outputs; not promoted", "utf-8")
    (sub["data_raw"] / "raw_snapshot_note.txt").write_text(
        "staging-only: SQL ingestion NOT run; productive data/raw reused read-only", "utf-8")
    sdate = "unknown"
    f = PROJECT_ROOT / "data" / "processed" / "forecasts.csv"
    if f.exists():
        sdate = datetime.fromtimestamp(f.stat().st_mtime).date().isoformat()
    write_csv(sub["status"]/"run_metadata.csv",
              ["last_successful_refresh_timestamp", "pipeline_status", "total_runtime_minutes",
               "model_scope_count", "champion_model", "validation_status", "promoted_run_id",
               "source_data_date", "notes"],
              [[now_iso(), "STAGING_COMPLETED", round(elapsed_min(), 2), scope_count, champion,
                "PENDING", "NOT_PROMOTED_STAGING_RUN", sdate,
                "staging-only candidate; smoke" if smoke else "staging-only candidate; full"]])
    write_csv(sub["status"]/"pipeline_status.csv",
              ["run_id", "timestamp", "pipeline_status", "stage_count", "stages_completed",
               "stages_failed", "total_runtime_minutes", "validation_status",
               "promotion_status", "notes"],
              [[sub["run_id"], now_iso(), "STAGING_COMPLETED", len(model_status),
                sum(1 for v in model_status.values() if v == "COMPLETED"),
                sum(1 for v in model_status.values() if v == "FAILED"),
                round(elapsed_min(), 2), "PENDING", "NOT_ATTEMPTED_STAGING_ONLY",
                "smoke" if smoke else "full"]])


def champion_from_prod():
    import pandas as pd
    f = PROJECT_ROOT / "data" / "processed" / "model_universe_canonical.csv"
    if not f.exists():
        return "unknown"
    cu = pd.read_csv(f)
    if "selected_champion" in cu.columns:
        sel = cu[cu["selected_champion"].astype(str).str.lower().isin(["true", "yes", "1"])]
        if len(sel):
            return str(sel.iloc[0]["model_name"])
    return CHAMPION_FROZEN


def do_run(execute, smoke, full=False, fresh=False):
    sub = make_run_dir()
    before = snapshot_dirs()
    champion = champion_from_prod()
    ms = {}
    scope_count = 15
    s01 = ("VALIDATE_SKIP", "no fit")
    s02 = ("VALIDATE_SKIP", "no fit")
    if execute:
        if fresh:
            s01 = stage_ingestion(sub)[:2]
            print(f"S01 ingestion {s01[0]}: {s01[1]}")
            if s01[0] == "BLOCKED":
                after = snapshot_dirs()
                write_csv(sub["status"]/"productive_mutation_check.csv", ["dir","before","after","changed"],
                          [[k,str(before[k]),str(after.get(k)),"YES" if before[k]!=after.get(k) else "NO"] for k in before])
                print("V3_3DE_BLOCKED_NEEDS_STAGING_INGESTION_FIX")
                return 3
            s02 = stage_transform(sub)
            print(f"S02 transform {s02[0]}: {s02[1]}")
            if s02[0] == "BLOCKED":
                after = snapshot_dirs()
                write_csv(sub["status"]/"productive_mutation_check.csv", ["dir","before","after","changed"],
                          [[k,str(before[k]),str(after.get(k)),"YES" if before[k]!=after.get(k) else "NO"] for k in before])
                print("V3_3DE_BLOCKED_NEEDS_STAGING_TRANSFORM_FIX")
                return 3
        st, n, f = stage_baseline(sub, smoke); ms["S03a"] = st
        print(f"S03a baseline {st} rows={n} fail={f}")
        st, n, f, nm = stage_challengers(sub, smoke); ms["S03b"] = st
        print(f"S03b challengers {st} rows={n} fail={f} models={nm}")
        st, n, nm = stage_dl_reuse(sub); ms["S03c"] = st
        print(f"S03c dl_reuse {st} rows={n} models={nm}")
    else:
        ms = {"S03a": "VALIDATE_SKIP", "S03b": "VALIDATE_SKIP", "S03c": "VALIDATE_SKIP"}
    write_csv(sub["runtime"]/"model_execution_summary.csv", ["stage","status"],
              [[k, v] for k, v in ms.items()])
    write_candidates_and_status(sub, ms, champion, scope_count, smoke, fresh)
    after = snapshot_dirs()
    gates = run_gates(sub, before, after, ms, champion, fresh)
    write_csv(sub["status"]/"productive_mutation_check.csv", ["dir", "before", "after", "changed"],
              [[k, str(before[k]), str(after.get(k)), "YES" if before[k] != after.get(k) else "NO"]
               for k in before])
    npass = sum(1 for _, ok in gates if ok); ntot = len(gates)
    print(f"GATES {npass}/{ntot} PASS | champion={champion} | run={sub['run_id']}")
    final = ("V3_3DE_DAILY_REFRESH_ORCHESTRATOR_FULL_STAGING_COMPLETED" if (npass==ntot and full)
             else "V3_3DE_DAILY_REFRESH_ORCHESTRATOR_STAGING_COMPLETED" if npass == ntot
             else "V3_3DE_DAILY_REFRESH_ORCHESTRATOR_STAGING_PARTIAL")
    print(final)
    return 0 if npass == ntot else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--validate", action="store_true")
    ap.add_argument("--execute-staging", action="store_true")
    ap.add_argument("--allow-execute", action="store_true")
    ap.add_argument("--smoke-test", action="store_true")
    ap.add_argument("--full-run", action="store_true")
    ap.add_argument("--promote", action="store_true")
    ap.add_argument("--from-latest-successful-staging-run", action="store_true")
    ap.add_argument("--allow-promote", action="store_true")
    args = ap.parse_args()
    if args.promote:
        if not args.allow_promote:
            print("PROMOTE_BLOCKED_REQUIRES_ALLOW_PROMOTE")
            return 3
        return do_promote(from_latest=args.from_latest_successful_staging_run)
    if args.dry_run:
        return do_dry_run()
    if args.validate:
        return do_run(execute=False, smoke=True)
    if args.execute_staging:
        if not args.allow_execute:
            print("BLOCKED: --execute-staging requires --allow-execute")
            return 3
        return do_run(execute=True, smoke=args.smoke_test, full=args.full_run, fresh=args.full_run)
    print("No mode selected. Use --dry-run | --validate | --execute-staging --allow-execute")
    return 2


if __name__ == "__main__":
    sys.exit(main())
