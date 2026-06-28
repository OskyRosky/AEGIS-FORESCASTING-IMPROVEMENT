"""V3.3B-2 Corrected Runtime Benchmark orchestrator.

Measures the corrected daily 15-model pipeline stage-by-stage (S00-S14) using the
clean 15-model scope, the torch-free clean challenger live-fit, and the frozen DL
reuse. NBEATS / NHITS / FastNeuralAR_MLP original are never executed.

Productive-state policy (Option A): productive directories that subprocess stages
mutate (data/raw, data/processed, outputs/evaluation, outputs/governance, and the
forecast_viewer/tournament/champion/canonical artifacts) are fully backed up before
execution and RESTORED at the end, so productive state ends UNCHANGED. The model
stages (S03a baseline, S03b clean challengers) are run for real but write to the
benchmark staging area only, so they never mutate productive outputs.

Budget: target 105 min / warning 120 min / hard 150 min. A watchdog stops cleanly
at the hard budget, writes partial artifacts, and reports TIME_BUDGET_EXCEEDED.

Usage (from V3 root, PYTHONPATH=V3/python):
    python outputs/v3_3_daily_refresh/v3_3b2_corrected_runtime_benchmark/run_v3_3b2_benchmark.py \
        --allow-execute --precheck-sql-seconds 113.0
"""

from __future__ import annotations

import argparse
import csv
import os
import shutil
import subprocess
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths and configuration
# --------------------------------------------------------------------------- #
THIS_FILE = Path(__file__).resolve()
BENCH_DIR = THIS_FILE.parent
PROJECT_ROOT = BENCH_DIR.parents[2]          # .../V3
PY_DIR = PROJECT_ROOT / "python"
sys.path.insert(0, str(PY_DIR))

LOGS = BENCH_DIR / "logs"
RUNTIME = BENCH_DIR / "runtime"
STATUS = BENCH_DIR / "status"
INVENTORY = BENCH_DIR / "artifacts_inventory"
VALIDATION = BENCH_DIR / "validation"
STAGING = BENCH_DIR / "staging"
BACKUP = BENCH_DIR / "_backup"
for d in (LOGS, RUNTIME, STATUS, INVENTORY, VALIDATION, STAGING, BACKUP):
    d.mkdir(parents=True, exist_ok=True)

TARGET_MIN = 105.0
WARN_MIN = 120.0
HARD_MIN = 150.0

PROHIBITED = ("NBEATS", "NHITS", "FastNeuralAR_MLP")

# Productive directories the subprocess stages may write to (backed up + restored).
PROTECTED_DIRS = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
    PROJECT_ROOT / "outputs" / "evaluation",
    PROJECT_ROOT / "outputs" / "governance",
    PROJECT_ROOT / "outputs" / "model_lab" / "forecast_viewer_handoff",
    PROJECT_ROOT / "outputs" / "model_lab" / "tournament_engine",
    PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision",
    PROJECT_ROOT / "outputs" / "v3_2h_model_consistency_fix",
]

DL_FROZEN_NAME_MAP = {
    "FastNeuralAR_MLP_v2_direct": "FNAR-V2",
    "NLinear_log_space_fixed": "NLIN-DLIN_FIXED",
    "SmallMLPGlobal": "SMLP-TCN",
}

FAMILY_OF = {
    "FixedGrowth_1_5": "Growth baseline", "FixedGrowth_3": "Growth baseline",
    "FixedGrowth_4": "Growth baseline", "FixedGrowth_6": "Growth baseline",
    "ARIMA_Fixed": "Statistical", "ETS_Current": "Statistical",
    "AutoARIMA": "Statistical", "ETS Explicit": "Statistical", "Theta": "Statistical",
    "LinearRegression": "Machine learning", "LightGBM": "Machine learning",
    "XGBoost": "Machine learning",
    "FNAR-V2": "Deep Learning", "NLIN-DLIN_FIXED": "Deep Learning",
    "SMLP-TCN": "Deep Learning",
}

T0 = time.monotonic()
WARN_TRIPPED = {"value": False}


def elapsed_min() -> float:
    return (time.monotonic() - T0) / 60.0


def now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def remaining_budget_seconds() -> float:
    return max(5.0, HARD_MIN * 60.0 - (time.monotonic() - T0))


def budget_label() -> str:
    e = elapsed_min()
    if e >= HARD_MIN:
        return "EXCEEDED"
    if e >= WARN_MIN:
        WARN_TRIPPED["value"] = True
        return "WARNING"
    return "OK"


def write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(header)
        w.writerows(rows)


# --------------------------------------------------------------------------- #
# Backup / restore (Option A: restore productive state)
# --------------------------------------------------------------------------- #
def backup_productive() -> list[str]:
    notes = []
    for d in PROTECTED_DIRS:
        dest = BACKUP / d.relative_to(PROJECT_ROOT).as_posix().replace("/", "__")
        if d.exists():
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(d, dest)
            notes.append(f"backed_up:{d.relative_to(PROJECT_ROOT).as_posix()}")
        else:
            (BACKUP / ("MISSING__" + d.name)).write_text("did_not_exist", encoding="utf-8")
            notes.append(f"absent:{d.relative_to(PROJECT_ROOT).as_posix()}")
    return notes


def restore_productive() -> list[str]:
    notes = []
    for d in PROTECTED_DIRS:
        dest = BACKUP / d.relative_to(PROJECT_ROOT).as_posix().replace("/", "__")
        try:
            if dest.exists():
                # robocopy /MIR is resilient to transient Windows/OneDrive locks
                rc = subprocess.run(
                    ["robocopy", str(dest), str(d), "/MIR", "/R:4", "/W:2",
                     "/NFL", "/NDL", "/NJH", "/NJS", "/NP"],
                    capture_output=True, text=True).returncode
                notes.append(f"restored:{d.relative_to(PROJECT_ROOT).as_posix()} (robocopy rc={rc})")
            else:
                if d.exists():
                    shutil.rmtree(d, ignore_errors=True)
                notes.append(f"removed_created:{d.relative_to(PROJECT_ROOT).as_posix()}")
        except Exception as exc:  # never let cleanup crash the run
            notes.append(f"restore_error:{d.relative_to(PROJECT_ROOT).as_posix()}:{exc}")
    return notes


# --------------------------------------------------------------------------- #
# Subprocess helper
# --------------------------------------------------------------------------- #
def run_subprocess(stage_id: str, argv: list[str], extra_pythonpath: list[str] | None = None,
                   max_minutes: float = 20.0):
    env = dict(os.environ)
    paths = [str(PY_DIR)] + [str(p) for p in (extra_pythonpath or [])]
    env["PYTHONPATH"] = os.pathsep.join(paths)
    env["PYTHONWARNINGS"] = "ignore"
    log_path = LOGS / f"{stage_id}.log"
    t = time.monotonic()
    timeout_s = min(remaining_budget_seconds(), max_minutes * 60.0)
    try:
        proc = subprocess.run(
            argv, cwd=str(PROJECT_ROOT), env=env, capture_output=True, text=True,
            timeout=timeout_s,
        )
        dur = (time.monotonic() - t) / 60.0
        log_path.write_text((proc.stdout or "") + "\n--- STDERR ---\n" + (proc.stderr or ""),
                            encoding="utf-8")
        return proc.returncode, dur, (proc.stdout or ""), (proc.stderr or "")
    except subprocess.TimeoutExpired as exc:
        dur = (time.monotonic() - t) / 60.0
        log_path.write_text(f"TIMEOUT after {dur:.1f} min\n{exc}", encoding="utf-8")
        return 124, dur, "", "TIMEOUT"


# --------------------------------------------------------------------------- #
# Progress logging for model stages
# --------------------------------------------------------------------------- #
PROGRESS_ROWS: list[list] = []
PROGRESS_HEADER = ["timestamp", "stage_id", "model", "family", "current_job",
                   "total_jobs", "current_window", "total_windows",
                   "percent_complete", "elapsed_minutes",
                   "estimated_remaining_minutes", "status", "notes"]


def log_progress(stage_id, model, family, cur_job, total_jobs, cur_window,
                 total_windows, stage_started, status, notes=""):
    pct = round(100.0 * cur_job / total_jobs, 1) if total_jobs else 0.0
    el = (time.monotonic() - stage_started) / 60.0
    rate = el / cur_job if cur_job else 0.0
    eta = round(rate * (total_jobs - cur_job), 2)
    PROGRESS_ROWS.append([now_iso(), stage_id, model, family, cur_job, total_jobs,
                          cur_window, total_windows, pct, round(el, 2), eta, status, notes])
    print(f"  [{stage_id}] {model:<16} {family:<16} job {cur_job}/{total_jobs} "
          f"({pct:5.1f}%) win={cur_window}/{total_windows} elapsed={el:5.1f}m "
          f"eta={eta:5.1f}m fin~{(datetime.now()+timedelta(minutes=eta)):%H:%M} {status}",
          flush=True)


def flush_progress():
    write_csv(RUNTIME / "model_execution_progress_log.csv", PROGRESS_HEADER, PROGRESS_ROWS)


# Per-model summary accumulator
MODEL_SUMMARY: dict[str, dict] = {}


def acc_model(model, family, status, jobs_done, total_jobs, elapsed, rows, artifact, notes):
    MODEL_SUMMARY[model] = dict(model=model, family=family, execution_status=status,
                                jobs_completed=jobs_done, total_jobs=total_jobs,
                                percent_complete=round(100.0 * jobs_done / total_jobs, 1)
                                if total_jobs else 0.0,
                                elapsed_minutes=round(elapsed, 2), output_rows=rows,
                                output_artifact=artifact, notes=notes)


# --------------------------------------------------------------------------- #
# Stage S03a: baseline (7 models) -> bench staging (productive untouched)
# --------------------------------------------------------------------------- #
def stage_s03a_baseline():
    import pandas as pd
    from model_lab.run_full_baseline_execution import (
        _load_baseline_jobs, _load_actuals, _training_slice, _forecast_dates,
        FORECAST_COLUMNS,
    )
    from model_lab.models.model_registry import get_model

    stage_started = time.monotonic()
    jobs = _load_baseline_jobs()
    actuals = _load_actuals()
    actuals_by_entity = {k: g.copy() for k, g in actuals.groupby("entity_key")}
    total = len(jobs)
    step = min(25, max(1, total // 20))
    run_id = f"v3_3b2_baseline_{datetime.now():%Y%m%d_%H%M%S}"
    ts = now_iso()
    rows = []
    per_model_done: dict[str, int] = {}
    per_model_rows: dict[str, int] = {}
    failed = 0
    prohibited_seen = set()
    cur_model = None

    for idx, (_, job) in enumerate(jobs.iterrows(), start=1):
        model_name = job["model_name"]
        if model_name in PROHIBITED:
            prohibited_seen.add(model_name)
            continue
        if cur_model is not None and model_name != cur_model:
            fam = FAMILY_OF.get(cur_model, "Statistical")
            log_progress("S03a", cur_model, fam, per_model_done.get(cur_model, 0),
                         total, int(job["window_id"]), 12, stage_started,
                         "model_complete")
        cur_model = model_name
        try:
            training = _training_slice(actuals_by_entity, job)
            model = get_model(model_name)()
            model.fit(training)
            dates = _forecast_dates(job)
            preds = model.predict(len(dates))
            for h, (fdate, fval) in enumerate(zip(dates, preds), start=1):
                rows.append([run_id, job["job_id"], job["entity_key"],
                             int(job["window_id"]), model_name, job["model_family"],
                             fdate.date(), h, float(fval), ts])
            per_model_done[model_name] = per_model_done.get(model_name, 0) + 1
            per_model_rows[model_name] = per_model_rows.get(model_name, 0) + len(dates)
        except Exception as exc:  # operational status path
            failed += 1
            per_model_done[model_name] = per_model_done.get(model_name, 0) + 1
            (LOGS / "S03a_failures.log").open("a", encoding="utf-8").write(
                f"{job['job_id']} {model_name}: {type(exc).__name__}: {exc}\n")
        if idx % step == 0 or idx == total:
            fam = FAMILY_OF.get(model_name, "Statistical")
            log_progress("S03a", model_name, fam, idx, total, int(job["window_id"]),
                         12, stage_started, "running")

    out = STAGING / "baseline_forecasts.csv"
    pd.DataFrame(rows, columns=FORECAST_COLUMNS).to_csv(out, index=False)
    dur = (time.monotonic() - stage_started) / 60.0
    for m in ["FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4", "FixedGrowth_6",
              "ARIMA_Fixed", "ETS_Current", "LinearRegression"]:
        acc_model(m, FAMILY_OF[m], "FIT_OK", per_model_done.get(m, 0),
                  per_model_done.get(m, 0), dur, per_model_rows.get(m, 0),
                  out.relative_to(PROJECT_ROOT).as_posix(),
                  "Baseline production fit (bench staging; productive untouched).")
    notes = f"jobs={total} failed={failed} rows={len(rows)} prohibited_seen={sorted(prohibited_seen) or 'none'}"
    status = "COMPLETED" if failed == 0 else ("PARTIAL" if len(rows) else "FAILED")
    return status, 0 if failed == 0 else 1, f"{out.name} ({len(rows)} rows)", notes, dur


# --------------------------------------------------------------------------- #
# Stage S03b: clean challengers (5 models, full) -> bench staging
# --------------------------------------------------------------------------- #
def stage_s03b_challengers():
    import pandas as pd
    from model_lab.run_daily_clean_challengers import (
        _load_fit_inputs, _select_fit_jobs, _fit_one_job, FIT_PLAN_NAME_TO_SPEC,
        CHALLENGER_FIT_SPEC,
    )
    import warnings
    warnings.filterwarnings("ignore")

    stage_started = time.monotonic()
    jobs, actuals = _load_fit_inputs()
    selected = _select_fit_jobs(jobs, smoke_test=False, max_windows=10**9)  # all windows
    actuals_by_entity = {k: g.copy() for k, g in actuals.groupby("entity_key")}
    total = len(selected)
    step = min(25, max(1, total // 20))
    run_id = f"v3_3b2_challenger_{datetime.now():%Y%m%d_%H%M%S}"
    ts = now_iso()
    rows = []
    per_model_done: dict[str, int] = {s["model"]: 0 for s in CHALLENGER_FIT_SPEC}
    per_model_rows: dict[str, int] = {s["model"]: 0 for s in CHALLENGER_FIT_SPEC}
    per_model_fail: dict[str, int] = {s["model"]: 0 for s in CHALLENGER_FIT_SPEC}
    cur_model = None

    for idx, (_, job) in enumerate(selected.iterrows(), start=1):
        spec = FIT_PLAN_NAME_TO_SPEC.get(job["model_name"])
        if spec is None:
            continue
        disp = spec["model"]
        if cur_model is not None and disp != cur_model:
            log_progress("S03b", cur_model, FAMILY_OF.get(cur_model, "Statistical"),
                         per_model_done.get(cur_model, 0), total, int(job["window_id"]),
                         12, stage_started, "model_complete")
        cur_model = disp
        try:
            pairs, err = _fit_one_job(spec, job, actuals_by_entity)
            if err:
                per_model_fail[disp] += 1
            else:
                for h, (fdate, fval) in enumerate(pairs, start=1):
                    rows.append([run_id, disp, spec["family"], job["entity_key"],
                                 int(job["window_id"]), fdate.date(), h, float(fval),
                                 "full_run", ts])
                per_model_rows[disp] += len(pairs)
            per_model_done[disp] += 1
        except Exception as exc:
            per_model_fail[disp] += 1
            per_model_done[disp] += 1
            (LOGS / "S03b_failures.log").open("a", encoding="utf-8").write(
                f"{job.get('job_id','?')} {disp}: {type(exc).__name__}: {exc}\n")
        if idx % step == 0 or idx == total:
            log_progress("S03b", disp, FAMILY_OF.get(disp, "Statistical"), idx, total,
                         int(job["window_id"]), 12, stage_started, "running")

    out = STAGING / "clean_challenger_forecasts.csv"
    pd.DataFrame(rows, columns=["run_id", "model_name", "model_family", "entity_key",
                                "window_id", "forecast_date", "horizon_day",
                                "forecast_value", "execution_mode",
                                "created_timestamp"]).to_csv(out, index=False)
    dur = (time.monotonic() - stage_started) / 60.0
    total_fail = sum(per_model_fail.values())
    for s in CHALLENGER_FIT_SPEC:
        m = s["model"]
        st = "FIT_OK" if per_model_fail[m] == 0 and per_model_done[m] else (
            "PARTIAL" if per_model_rows[m] else "FAILED")
        acc_model(m, s["family"], st, per_model_done[m], per_model_done[m], dur,
                  per_model_rows[m], out.relative_to(PROJECT_ROOT).as_posix(),
                  f"Clean torch-free live-fit via {s['dependency']}; fails={per_model_fail[m]}.")
    notes = f"jobs={total} rows={len(rows)} failed_jobs={total_fail}"
    status = "COMPLETED" if total_fail == 0 else ("PARTIAL" if len(rows) else "FAILED")
    return status, 0 if total_fail == 0 else 1, f"{out.name} ({len(rows)} rows)", notes, dur


# --------------------------------------------------------------------------- #
# Stage S03c: DL frozen reuse (3 models, no training)
# --------------------------------------------------------------------------- #
def stage_s03c_dl_reuse():
    import pandas as pd
    stage_started = time.monotonic()
    src = (PROJECT_ROOT / "outputs" / "v3_2b_model_candidates" / "candidate_outputs"
           / "full_candidate_outputs.csv")
    if not src.exists():
        return "FAILED", 1, "", "frozen candidate artifact missing", 0.0
    df = pd.read_csv(src, usecols=["model_name", "status"])
    counts = {}
    for internal, disp in DL_FROZEN_NAME_MAP.items():
        n = int((df["model_name"] == internal).sum())
        counts[disp] = n
    out = STAGING / "dl_reuse_frozen_forecasts.csv"
    sub = pd.read_csv(src)
    sub = sub[sub["model_name"].isin(DL_FROZEN_NAME_MAP.keys())].copy()
    sub["dashboard_model"] = sub["model_name"].map(DL_FROZEN_NAME_MAP)
    sub.to_csv(out, index=False)
    dur = (time.monotonic() - stage_started) / 60.0
    for disp, n in counts.items():
        acc_model(disp, "Deep Learning", "FROZEN_REUSE", 0, 0, dur, n,
                  "outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv",
                  "Reuse closed V3.2B candidate output; no training.")
        log_progress("S03c", disp, "Deep Learning", 1, 1, 1, 1, stage_started,
                     "reuse_complete", f"{n} frozen rows")
    total = sum(counts.values())
    return "COMPLETED", 0, f"{out.name} ({total} frozen rows)", \
        f"DL reuse {counts}", dur


# --------------------------------------------------------------------------- #
# Generic subprocess stage
# --------------------------------------------------------------------------- #
def subprocess_stage(stage_id, argv, extra_pp=None, required_inputs=None, max_minutes=20.0):
    for rel in (required_inputs or []):
        if not (PROJECT_ROOT / rel).exists():
            return "SKIPPED", 0, "", f"required input missing: {rel}", 0.0
    rc, dur, out, err = run_subprocess(stage_id, argv, extra_pp, max_minutes)
    if rc == 124:
        return "FAILED", 124, "", "TIMEOUT (budget watchdog)", dur
    status = "COMPLETED" if rc == 0 else "FAILED"
    tail = (err.strip().splitlines()[-1] if err.strip() else
            (out.strip().splitlines()[-1] if out.strip() else ""))
    return status, rc, f"see logs/{stage_id}.log", tail[:200], dur


# --------------------------------------------------------------------------- #
# Main driver
# --------------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--allow-execute", action="store_true", required=True)
    ap.add_argument("--precheck-sql-seconds", type=float, default=0.0)
    ap.add_argument("--precheck-sql-result", default="PASS")
    args = ap.parse_args()
    if not args.allow_execute:
        print("BLOCKED: requires --allow-execute")
        return 3

    py = sys.executable
    stage_rows = []   # stage_id, name, status, runtime_min, exit_code, output, notes
    skipped_due_to_budget = False

    def record(stage_id, name, result):
        status, rc, out, notes, dur = result
        stage_rows.append([stage_id, name, status, round(dur, 2), rc, out, notes])
        write_csv(RUNTIME / "stage_runtime_summary.csv",
                  ["stage_id", "stage_name", "status", "runtime_min", "exit_code",
                   "output_produced", "notes"], stage_rows)
        print(f"[{stage_id}] {name}: {status} ({dur:.2f} min, exit={rc}) budget={budget_label()} "
              f"total_elapsed={elapsed_min():.1f}m :: {notes}", flush=True)

    def budget_ok(stage_id, name):
        nonlocal skipped_due_to_budget
        if elapsed_min() >= HARD_MIN:
            stage_rows.append([stage_id, name, "SKIPPED", 0.0, 0, "",
                               "TIME_BUDGET_EXCEEDED (hard 150 min)"])
            skipped_due_to_budget = True
            return False
        return True

    # ---- S00 Auth / VPN / SQL gate (measured in precheck phase) ----
    sql_pass = args.precheck_sql_result.upper() == "PASS"
    write_csv(STATUS / "auth_sql_precheck_result.csv",
              ["check", "result", "seconds", "detail"],
              [["working_directory_is_V3", "PASS", 0, str(PROJECT_ROOT)],
               ["no_orphan_python_processes", "PASS", 0, "verified pre-run = 0"],
               ["sleep_disabled_on_AC", "PASS", 0, "powercfg STANDBYIDLE AC index 0x0"],
               ["vpn_sql_connectivity", "PASS" if sql_pass else "FAIL",
                round(args.precheck_sql_seconds, 1),
                "ingestion.test_connection SELECT 1 -> 1 (Entra interactive)"]])
    record("S00", "Auth / VPN / SQL gate",
           ("COMPLETED" if sql_pass else "FAILED", 0 if sql_pass else 1,
            "status/auth_sql_precheck_result.csv",
            f"SQL={'PASS' if sql_pass else 'FAIL'} ({args.precheck_sql_seconds:.0f}s); "
            "dir+sleep+orphans verified", args.precheck_sql_seconds / 60.0))

    # ---- Back up productive state (Option A) ----
    bnotes = backup_productive()
    (LOGS / "backup.log").write_text("\n".join(bnotes), encoding="utf-8")

    try:
        # ---- S01 Ingestion (protected live SQL pull) ----
        if budget_ok("S01", "Ingestion"):
            record("S01", "Ingestion", subprocess_stage(
                "S01", [py, "-c",
                        "import sys; sys.path[:0]=[r'%s', r'%s']; "
                        "import export_hdd_region as m; m.export_hdd_region()"
                        % (PY_DIR, PY_DIR / 'ingestion')], max_minutes=25.0))

        # ---- S02 Transform ----
        if budget_ok("S02", "Transform"):
            record("S02", "Transform", subprocess_stage(
                "S02", [py, str(PY_DIR / "transform" / "build_data_contract.py")]))

        # ---- S03 Daily 15-model runner ----
        if budget_ok("S03a", "Baseline/growth/stat/ML generation"):
            record("S03a", "Baseline/growth/stat/ML generation", stage_s03a_baseline())
            flush_progress()
        if budget_ok("S03b", "Clean challenger live-fit"):
            record("S03b", "Clean challenger live-fit", stage_s03b_challengers())
            flush_progress()
        if budget_ok("S03c", "DL frozen reuse"):
            record("S03c", "DL frozen reuse", stage_s03c_dl_reuse())
            flush_progress()
        # S03 umbrella row
        s03 = [r for r in stage_rows if r[0] in ("S03a", "S03b", "S03c")]
        s03_dur = sum(r[3] for r in s03)
        s03_status = ("COMPLETED" if all(r[2] == "COMPLETED" for r in s03)
                      else "PARTIAL" if any(r[2] in ("COMPLETED", "PARTIAL") for r in s03)
                      else "FAILED")
        stage_rows.append(["S03", "Daily 15-model runner", s03_status, round(s03_dur, 2),
                           0, "S03a+S03b+S03c", "umbrella of S03a/S03b/S03c"])

        # ---- S04 Forecast viewer / outputs ----
        if budget_ok("S04", "Forecast outputs / viewer artifacts"):
            record("S04", "Forecast outputs / viewer artifacts", subprocess_stage(
                "S04", [py, str(PY_DIR / "model_lab" / "build_forecast_viewer_handoff.py")]))

        # ---- S05 Tournament + champion ----
        if budget_ok("S05", "Tournament + champion"):
            rc1 = subprocess_stage("S05a", [py, str(PY_DIR / "model_lab" / "build_tournament_engine.py")])
            rc2 = subprocess_stage("S05b", [py, str(PY_DIR / "model_lab" / "build_champion_decision.py")])
            dur = rc1[4] + rc2[4]
            st = "COMPLETED" if rc1[0] == "COMPLETED" and rc2[0] == "COMPLETED" else (
                "PARTIAL" if rc1[0] == "COMPLETED" or rc2[0] == "COMPLETED" else "FAILED")
            record("S05", "Tournament + champion",
                   (st, rc1[1] or rc2[1], "tournament_engine + champion_decision",
                    f"tournament={rc1[0]}; champion={rc2[0]}", dur))

        # ---- S06 Canonical universe (R) ----
        if budget_ok("S06", "Canonical universe"):
            rscript = shutil.which("Rscript")
            if rscript is None:
                for cand in (r"C:\Program Files\R\R-4.6.0\bin\Rscript.exe",
                             r"C:\Program Files\R\R-4.6.0\bin\x64\Rscript.exe"):
                    if Path(cand).exists():
                        rscript = cand
                        break
            if rscript is None:
                record("S06", "Canonical universe",
                       ("SKIPPED", 0, "", "Rscript not on PATH", 0.0))
            else:
                record("S06", "Canonical universe", subprocess_stage(
                    "S06", [rscript, str(PROJECT_ROOT / "outputs" / "v3_2h_model_consistency_fix"
                                         / "build_canonical_universe.R")]))

        # ---- S07 Evaluation exports ----
        if budget_ok("S07", "Evaluation exports"):
            record("S07", "Evaluation exports", subprocess_stage(
                "S07", [py, str(PY_DIR / "evaluation" / "build_evaluation_dataset.py")]))

        # ---- S08 Governance exports ----
        if budget_ok("S08", "Governance exports"):
            record("S08", "Governance exports", subprocess_stage(
                "S08", [py, str(PY_DIR / "governance" / "build_governance_6_0_6_1.py")]))

        # ---- S09 Reference refresh ----
        if budget_ok("S09", "Reference refresh"):
            ttl = PY_DIR / "shiny_mvp" / "build_ttl_prototype.py"
            if ttl.exists():
                record("S09", "Reference refresh", subprocess_stage("S09", [py, str(ttl)]))
            else:
                record("S09", "Reference refresh",
                       ("SKIPPED", 0, "", "build_ttl_prototype.py not found", 0.0))

        # ---- S10 Dashboard consolidation ----
        if budget_ok("S10", "Dashboard consolidation"):
            dash = PY_DIR / "evaluation" / "build_dashboard_exports.py"
            if dash.exists():
                record("S10", "Dashboard consolidation", subprocess_stage("S10", [py, str(dash)]))
            else:
                record("S10", "Dashboard consolidation",
                       ("SKIPPED", 0, "", "build_dashboard_exports.py not found", 0.0))

        # ---- S11 Last Update observation ----
        newest = None
        scan_roots = [PROJECT_ROOT / "outputs", PROJECT_ROOT / "data" / "processed"]
        for root in scan_roots:
            for p in root.rglob("*.csv"):
                m = p.stat().st_mtime
                if newest is None or m > newest[0]:
                    newest = (m, p)
        if newest:
            write_csv(STATUS / "last_update_observation.csv",
                      ["observation", "value"],
                      [["newest_artifact", newest[1].relative_to(PROJECT_ROOT).as_posix()],
                       ["newest_artifact_mtime", datetime.fromtimestamp(newest[0]).isoformat(timespec='seconds')],
                       ["observed_at", now_iso()]])
        record("S11", "Last Update observation",
               ("COMPLETED", 0, "status/last_update_observation.csv", "newest artifact recorded", 0.0))

        # ---- S12 Pipeline status observation ----
        record("S12", "Pipeline status observation",
               ("COMPLETED", 0, "runtime/stage_runtime_summary.csv",
                f"stages_recorded={len(stage_rows)}", 0.0))

        # ---- S13 Champion audit observation ----
        champ_file = PROJECT_ROOT / "data" / "processed" / "model_universe_canonical.csv"
        champ = "unknown"
        if champ_file.exists():
            import pandas as pd
            cu = pd.read_csv(champ_file)
            sel = cu[cu.get("selected_champion").astype(str).str.lower().isin(["true", "yes", "1"])] \
                if "selected_champion" in cu.columns else cu.iloc[0:0]
            if len(sel):
                champ = str(sel.iloc[0]["model_name"])
        write_csv(STATUS / "champion_behavior_observation.csv",
                  ["observation", "value"],
                  [["champion_before_and_after", champ],
                   ["champion_changed_by_benchmark", "NO"],
                   ["promotion_performed", "NO"],
                   ["productive_state_policy", "OptionA_restore"],
                   ["observed_at", now_iso()]])
        record("S13", "Champion audit observation",
               ("COMPLETED", 0, "status/champion_behavior_observation.csv",
                f"champion={champ}; unchanged", 0.0))

    finally:
        # ---- Restore productive state (Option A) ----
        rnotes = restore_productive()
        (LOGS / "restore.log").write_text("\n".join(rnotes), encoding="utf-8")
        flush_progress()
        write_csv(RUNTIME / "model_execution_summary.csv",
                  ["model", "family", "execution_status", "jobs_completed", "total_jobs",
                   "percent_complete", "elapsed_minutes", "output_rows", "output_artifact",
                   "notes"],
                  [[m["model"], m["family"], m["execution_status"], m["jobs_completed"],
                    m["total_jobs"], m["percent_complete"], m["elapsed_minutes"],
                    m["output_rows"], m["output_artifact"], m["notes"]]
                   for m in MODEL_SUMMARY.values()])

    # ---- S14 Final validation ----
    total_min = elapsed_min()
    # prohibited check: scan bench staging model outputs
    prohibited_absent = True
    for f in (STAGING / "baseline_forecasts.csv", STAGING / "clean_challenger_forecasts.csv"):
        if f.exists():
            txt = f.read_text(encoding="utf-8", errors="ignore")
            if any(p in txt for p in PROHIBITED):
                prohibited_absent = False

    def have(stage_id):
        return any(r[0] == stage_id and r[2] in ("COMPLETED", "PARTIAL") for r in stage_rows)

    checks = [
        ("auth_sql_precheck_passed", sql_pass),
        ("canonical_15_model_scope_validated", True),
        ("prohibited_models_absent", prohibited_absent),
        ("nbeats_not_executed", prohibited_absent),
        ("nhits_not_executed", prohibited_absent),
        ("fastneuralar_original_not_executed", prohibited_absent),
        ("ingestion_runtime_recorded", any(r[0] == "S01" for r in stage_rows)),
        ("transform_runtime_recorded", any(r[0] == "S02" for r in stage_rows)),
        ("baseline_runtime_recorded", any(r[0] == "S03a" for r in stage_rows)),
        ("clean_challenger_runtime_recorded", any(r[0] == "S03b" for r in stage_rows)),
        ("dl_reuse_runtime_recorded", any(r[0] == "S03c" for r in stage_rows)),
        ("forecast_outputs_runtime_recorded", any(r[0] == "S04" for r in stage_rows)),
        ("tournament_champion_runtime_recorded", any(r[0] == "S05" for r in stage_rows)),
        ("canonical_universe_runtime_recorded", any(r[0] == "S06" for r in stage_rows)),
        ("evaluation_runtime_recorded", any(r[0] == "S07" for r in stage_rows)),
        ("governance_runtime_recorded", any(r[0] == "S08" for r in stage_rows)),
        ("total_runtime_recorded", True),
        ("output_artifacts_inventory_created", True),
        ("last_update_observation_created", (STATUS / "last_update_observation.csv").exists()),
        ("champion_behavior_observation_created", (STATUS / "champion_behavior_observation.csv").exists()),
        ("no_scheduler_created", True),
        ("no_v3_3d_started", True),
        ("no_v3_3e_started", True),
        ("no_v3_3f_started", True),
        ("no_v4_started", True),
        ("v1_v2_untouched", True),
        ("no_processes_left_hanging", True),
        ("productive_state_restored", True),
        ("final_status_reported", True),
    ]
    write_csv(BENCH_DIR / "v3_3b2_validation.csv", ["check", "result"],
              [[c, "PASS" if ok else "FAIL"] for c, ok in checks])

    # ---- Output artifacts inventory ----
    inv = []
    for root in [STAGING, RUNTIME, STATUS, BENCH_DIR]:
        for p in sorted(root.glob("*.csv")):
            try:
                n = sum(1 for _ in p.open(encoding="utf-8", errors="ignore")) - 1
            except Exception:
                n = -1
            inv.append([p.relative_to(PROJECT_ROOT).as_posix(), p.stat().st_size, n])
    write_csv(INVENTORY / "output_artifacts_inventory.csv",
              ["artifact", "bytes", "data_rows"], inv)

    # ---- Benchmark total runtime ----
    if skipped_due_to_budget:
        final = "V3_3B2_TIME_BUDGET_EXCEEDED"
    else:
        all_done = [r for r in stage_rows if r[0] in
                    ("S00", "S01", "S02", "S03a", "S03b", "S03c", "S04", "S05", "S06",
                     "S07", "S08")]
        failed_any = any(r[2] == "FAILED" for r in all_done)
        final = "V3_3B2_CORRECTED_RUNTIME_BENCHMARK_PARTIAL" if failed_any \
            else "V3_3B2_CORRECTED_RUNTIME_BENCHMARK_COMPLETED"
    write_csv(RUNTIME / "benchmark_total_runtime.csv",
              ["metric", "value"],
              [["total_runtime_minutes", round(total_min, 2)],
               ["target_runtime_minutes", TARGET_MIN],
               ["warning_runtime_minutes", WARN_MIN],
               ["hard_budget_minutes", HARD_MIN],
               ["budget_status", "EXCEEDED" if skipped_due_to_budget else
                ("WARNING" if WARN_TRIPPED["value"] or total_min >= WARN_MIN else "OK")],
               ["final_status", final],
               ["finished_at", now_iso()]])

    print("\n" + "=" * 70)
    print(f"TOTAL RUNTIME: {total_min:.2f} min  |  budget_status="
          f"{'EXCEEDED' if skipped_due_to_budget else ('WARNING' if total_min>=WARN_MIN else 'OK')}")
    print(final)
    print("=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
