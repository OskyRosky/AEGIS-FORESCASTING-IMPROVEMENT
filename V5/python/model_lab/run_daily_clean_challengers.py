#!/usr/bin/env python
"""V3.3C-next - Clean daily challenger entrypoint (scope/plan/guard only).

Replaces the DAILY use of the legacy run_challenger_official_execution.py, whose
APPROVED_MODELS hard-codes NBEATS (and wires NHITS). This clean entrypoint ONLY
ever references the allowed challengers from the canonical 15-model universe:

    Statistical : AutoARIMA, ETS Explicit, Theta
    Machine ML  : LightGBM, XGBoost

It NEVER imports or references NBEATS / NHITS / FastNeuralAR_MLP (it does not
import the model registry, which would pull those in). Light modes (scope / plan
/ guard) are stdlib-only; the clean torch-free live-fit (V3.3C-fit) imports its
model libraries lazily only under --execute --allow-execute. It does NOT change
the champion, promote models, or touch productive outputs. All live-fit output
is written to staging only.

The 3 active Deep Learning models (FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN) are NOT
challengers here: they are wired as reuse_frozen_artifact (no live training).

Usage (from V3/python with PYTHONPATH=V3/python):
    python model_lab/run_daily_clean_challengers.py --dry-run
    python model_lab/run_daily_clean_challengers.py --validate-scope
    python model_lab/run_daily_clean_challengers.py --plan
    python model_lab/run_daily_clean_challengers.py --execute --allow-execute --smoke-test
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

from model_lab.run_daily_15_model_refresh import (
    MODELS as CANONICAL_MODELS_TABLE,
    PROHIBITED_LEGACY_LOCATIONS,
    PROHIBITED_MODELS,
    PROHIBITED_VIOLATION_TOKEN,
    prohibited_model_guard,
    STAGING_DIR as EXEC_STAGING_DIR,
    EXEC_STATUS_NOT_READY,
    EXEC_STATUS_CLEAN_FIT_READY,
    EXEC_BLOCKED_TOKEN,
    CLEAN_CHALLENGER_RUN_COMMAND,
)

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # model_lab -> python -> V3
OUTPUT_DIR = (
    PROJECT_ROOT / "outputs" / "v3_3_daily_refresh"
    / "v3_3c_next_clean_challenger_entrypoint"
)

CLEAN_CHALLENGER_OUT = "outputs/model_lab/daily_clean_challengers/clean_challenger_forecasts.csv"
DL_FROZEN_SOURCE = "outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv"
DL_DASHBOARD_ARTIFACT = "data/processed/model_universe_canonical.csv"

SCOPE_VALIDATED_TOKEN = "DAILY_CLEAN_CHALLENGER_SCOPE_VALIDATED"

CANONICAL_MODEL_NAMES = {m["model"] for m in CANONICAL_MODELS_TABLE}

# --------------------------------------------------------------------------
# V3.3C-fit - clean live-fit trainer (staging only; --allow-execute required)
# --------------------------------------------------------------------------
FIT_OUTPUT_DIR = (
    PROJECT_ROOT / "outputs" / "v3_3_daily_refresh" / "v3_3c_fit_clean_challengers"
)
FIT_STAGING_DIR = FIT_OUTPUT_DIR / "staging"
FIT_OUTPUTS_REL = (
    "outputs/v3_3_daily_refresh/v3_3c_fit_clean_challengers/"
    "staging/clean_challenger_fit_outputs.csv"
)

# Clean input contract (same as the baseline production runner).
EVALUATION_DATASET = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
TRAINING_JOB_PLAN = PROJECT_ROOT / "outputs" / "model_lab" / "training_job_plan.csv"

HORIZON_DAYS = 30
RANDOM_SEED = 42

FIT_COMPLETED_TOKEN = "V3_3C_FIT_CLEAN_CHALLENGERS_COMPLETED"
FIT_PARTIAL_TOKEN = "V3_3C_FIT_CLEAN_CHALLENGERS_PARTIAL"
FIT_PATH_NOT_READY = "FIT_PATH_NOT_READY"

# The 5 clean challengers, each mapped to its training_job_plan model_name, its
# clean torch-free forecaster, and its single runtime dependency. NBEATS / NHITS
# / FastNeuralAR_MLP are never referenced. (job_plan calls ETS Explicit "ETS".)
CHALLENGER_FIT_SPEC: list[dict] = [
    dict(model="AutoARIMA", family="Statistical", plan_name="AutoARIMA",
         forecaster="autoarima", dependency="pmdarima"),
    dict(model="ETS Explicit", family="Statistical", plan_name="ETS",
         forecaster="ets", dependency="statsmodels"),
    dict(model="Theta", family="Statistical", plan_name="Theta",
         forecaster="theta", dependency="statsmodels"),
    dict(model="LightGBM", family="Machine learning", plan_name="LightGBM",
         forecaster="lightgbm", dependency="lightgbm"),
    dict(model="XGBoost", family="Machine learning", plan_name="XGBoost",
         forecaster="xgboost", dependency="xgboost"),
]
FIT_PLAN_NAME_TO_SPEC = {s["plan_name"]: s for s in CHALLENGER_FIT_SPEC}

# --------------------------------------------------------------------------
# Allowed clean challengers (NEVER NBEATS / NHITS / FastNeuralAR_MLP)
# --------------------------------------------------------------------------
CLEAN_CHALLENGERS: list[dict] = [
    dict(order=1, model="AutoARIMA", family="Statistical",
         challenger_type="statistical_challenger", action="train",
         notes="Auto-order ARIMA; statistical challenger."),
    dict(order=2, model="ETS Explicit", family="Statistical",
         challenger_type="statistical_challenger", action="train",
         notes="CURRENT CHAMPION (MASE 6.901144); statistical challenger."),
    dict(order=3, model="Theta", family="Statistical",
         challenger_type="statistical_challenger", action="train",
         notes="Theta method; statistical challenger."),
    dict(order=4, model="LightGBM", family="Machine learning",
         challenger_type="ml_challenger", action="train",
         notes="Gradient boosting; ML challenger."),
    dict(order=5, model="XGBoost", family="Machine learning",
         challenger_type="ml_challenger", action="train",
         notes="Gradient boosting; ML challenger."),
]

# --------------------------------------------------------------------------
# Deep Learning reuse wiring (frozen artifacts, NO live training)
# --------------------------------------------------------------------------
DL_REUSE: list[dict] = [
    dict(model="FNAR-V2", family="Deep Learning",
         notes="FastNeuralAR_MLP_v2_direct from the closed V3.2B/D/E candidate study."),
    dict(model="NLIN-DLIN_FIXED", family="Deep Learning",
         notes="NLinear_log_space_fixed from the closed V3.2B/D/E candidate study."),
    dict(model="SMLP-TCN", family="Deep Learning",
         notes="SmallMLPGlobal/SmallTCN from the closed V3.2B/D/E candidate study."),
]


def _clean_challenger_models() -> list[str]:
    return [c["model"] for c in CLEAN_CHALLENGERS]


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


# --------------------------------------------------------------------------
# Artifact writers
# --------------------------------------------------------------------------
def write_clean_challenger_scope(violations: list[str]) -> Path:
    path = OUTPUT_DIR / "clean_challenger_scope.csv"
    header = [
        "model", "family", "challenger_type", "action", "entrypoint",
        "daily_scope_status", "prohibited_model_check",
        "expected_output_artifact", "notes",
    ]
    rows = []
    for c in CLEAN_CHALLENGERS:
        in_canon = c["model"] in CANONICAL_MODEL_NAMES
        check = "CLEAN" if (c["model"] not in PROHIBITED_MODELS and in_canon) else "VIOLATION"
        rows.append([
            c["model"], c["family"], c["challenger_type"], c["action"],
            "python/model_lab/run_daily_clean_challengers.py",
            "active_train", check, CLEAN_CHALLENGER_OUT, c["notes"],
        ])
    _write_csv(path, header, rows)
    return path


def write_dl_reuse_wiring() -> Path:
    path = OUTPUT_DIR / "dl_reuse_wiring.csv"
    header = [
        "model", "family", "action", "frozen_artifact_source",
        "expected_dashboard_artifact", "daily_training_available",
        "reuse_status", "gap_to_daily_training", "notes",
    ]
    rows = []
    for d in DL_REUSE:
        rows.append([
            d["model"], d["family"], "reuse_frozen_artifact", DL_FROZEN_SOURCE,
            DL_DASHBOARD_ARTIFACT, "NO",
            "frozen_closed_candidate_study_v3_2b",
            "No live daily trainer exists; the V3.2B/D/E candidate-study trainer "
            "must be located/rebuilt before these can be daily-trained.",
            d["notes"],
        ])
    _write_csv(path, header, rows)
    return path


def write_prohibited_guard_csv(violations: list[str]) -> Path:
    path = OUTPUT_DIR / "prohibited_model_guard_result.csv"
    header = [
        "prohibited_model", "found_in_active_daily_scope", "found_in_legacy_code",
        "active_scope_status", "action_taken", "notes",
    ]
    rows = []
    for p in PROHIBITED_MODELS:
        found_active = "YES" if p in violations else "NO"
        action = (
            "BLOCKED_RUN_ABORTED" if p in violations
            else "excluded_from_clean_challenger_entrypoint; legacy_runner_not_used_as_daily"
        )
        rows.append([
            p, found_active, "YES", "excluded", action,
            PROHIBITED_LEGACY_LOCATIONS.get(p, ""),
        ])
    _write_csv(path, header, rows)
    return path


def write_daily_runner_plan_updated() -> Path:
    path = OUTPUT_DIR / "daily_runner_plan_updated.csv"
    header = [
        "execution_order", "stage_name", "models_covered", "action",
        "entrypoint_or_source", "output_artifacts", "status", "notes",
    ]
    rows = [
        [
            1, "Baseline generation (growth + baseline statistical/ML)",
            "FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | "
            "ARIMA_Fixed | ETS_Current | LinearRegression",
            "train+generate", "python/model_lab/run_full_baseline_execution.py",
            "outputs/model_lab/full_baseline/full_baseline_forecasts.csv", "READY",
            "Clean runner; 7 of 15; no prohibited models.",
        ],
        [
            2, "Clean statistical + ML challengers",
            "AutoARIMA | ETS Explicit | Theta | LightGBM | XGBoost",
            "train", "python/model_lab/run_daily_clean_challengers.py",
            CLEAN_CHALLENGER_OUT, "READY",
            "Clean entrypoint; excludes NBEATS/NHITS; legacy challenger runner NOT used.",
        ],
        [
            3, "Deep Learning reuse (frozen artifacts)",
            "FNAR-V2 | NLIN-DLIN_FIXED | SMLP-TCN",
            "reuse_frozen_artifact", DL_FROZEN_SOURCE, DL_DASHBOARD_ARTIFACT,
            "FROZEN_REUSE", "No live daily training; reuse closed V3.2B study outputs.",
        ],
        [
            4, "Canonical universe aggregation",
            "all 15 (12 governed + 3 DL)", "aggregate",
            "outputs/v3_2h_model_consistency_fix/build_canonical_universe.R",
            "data/processed/model_universe_canonical.csv", "READY",
            "Aggregates governed scorecard + frozen DL; runs no model.",
        ],
        [
            5, "Tournament + champion decision",
            "12 governed (DL not champion-eligible)", "aggregate+decision",
            "build_tournament_engine.py + build_champion_decision.py",
            "outputs/model_lab/champion_decision/champion_candidate_evaluation.csv",
            "READY", "Champion = ETS Explicit; no promotion in V3.3C-next.",
        ],
        [
            6, "Forecast viewer handoff",
            "all 15 (display)", "handoff",
            "build_forecast_viewer_handoff.py",
            "data/processed/forecast_viewer_model_outputs.csv", "READY",
            "Maps the 15 canonical models for the dashboard viewer.",
        ],
    ]
    _write_csv(path, header, rows)
    return path


# --------------------------------------------------------------------------
# V3.3C-fit - clean torch-free forecasters (lazy imports; never NBEATS/NHITS)
# --------------------------------------------------------------------------
def _make_lag_matrix(values, n_lags: int):
    import numpy as np

    rows_x, rows_y = [], []
    for i in range(n_lags, len(values)):
        rows_x.append(values[i - n_lags:i][::-1])
        rows_y.append(values[i])
    return np.asarray(rows_x, dtype=float), np.asarray(rows_y, dtype=float)


def _recursive_tree_forecast(model, values, n_lags: int):
    import numpy as np

    history = list(np.asarray(values, dtype=float))
    preds: list[float] = []
    for _ in range(HORIZON_DAYS):
        feats = np.asarray(history[-n_lags:][::-1], dtype=float).reshape(1, -1)
        yhat = float(model.predict(feats)[0])
        preds.append(yhat)
        history.append(yhat)
    return np.asarray(preds, dtype=float)


def _forecast_autoarima(values):
    import numpy as np
    import pmdarima as pm

    model = pm.auto_arima(
        values.astype(float), seasonal=False, start_p=0, start_q=0,
        max_p=2, max_q=2, max_order=4, stepwise=True,
        error_action="ignore", suppress_warnings=True, random_state=RANDOM_SEED,
    )
    return np.asarray(model.predict(HORIZON_DAYS), dtype=float)


def _forecast_ets(values):
    import numpy as np
    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    model = ExponentialSmoothing(
        values.astype(float), trend="add", seasonal=None
    ).fit(optimized=True)
    return np.asarray(model.forecast(HORIZON_DAYS), dtype=float)


def _forecast_theta(values):
    """Clean torch-free Theta via statsmodels (no darts/torch dependency)."""
    import numpy as np
    from statsmodels.tsa.forecasting.theta import ThetaModel

    model = ThetaModel(values.astype(float), deseasonalize=False).fit()
    return np.asarray(model.forecast(HORIZON_DAYS), dtype=float)


def _forecast_lightgbm(values):
    import lightgbm as lgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = lgb.LGBMRegressor(
        n_estimators=100, random_state=RANDOM_SEED,
        verbosity=-1, deterministic=True, n_jobs=1,
    )
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags)


def _forecast_xgboost(values):
    import xgboost as xgb

    n_lags = 7
    x, y = _make_lag_matrix(values, n_lags)
    model = xgb.XGBRegressor(
        n_estimators=100, random_state=RANDOM_SEED, verbosity=0, n_jobs=1,
    )
    model.fit(x, y)
    return _recursive_tree_forecast(model, values, n_lags)


_FORECASTERS = {
    "autoarima": _forecast_autoarima,
    "ets": _forecast_ets,
    "theta": _forecast_theta,
    "lightgbm": _forecast_lightgbm,
    "xgboost": _forecast_xgboost,
}


# --------------------------------------------------------------------------
# V3.3C-fit - data loading + smoke-bounded job selection
# --------------------------------------------------------------------------
def _load_fit_inputs():
    """Load challenger jobs and actuals (lazy pandas import)."""
    import pandas as pd

    if not TRAINING_JOB_PLAN.exists():
        raise FileNotFoundError(f"Missing training job plan: {TRAINING_JOB_PLAN}")
    if not EVALUATION_DATASET.exists():
        raise FileNotFoundError(f"Missing evaluation dataset: {EVALUATION_DATASET}")

    plan = pd.read_csv(
        TRAINING_JOB_PLAN,
        parse_dates=["train_start_date", "train_end_date",
                     "test_start_date", "test_end_date"],
    )
    plan_names = list(FIT_PLAN_NAME_TO_SPEC.keys())
    jobs = plan[plan["model_name"].isin(plan_names)].copy()
    jobs = jobs.sort_values(["entity_key", "window_id", "model_name"])

    actuals = pd.read_csv(EVALUATION_DATASET, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals = actuals.sort_values(["entity_key", "date"])
    return jobs, actuals


def _select_fit_jobs(jobs, smoke_test: bool, max_windows):
    """Bound the job set to a safe smoke subset. NEVER the full 454-window set."""
    if smoke_test:
        first_entity = jobs["entity_key"].iloc[0]
        first_window = int(jobs[jobs["entity_key"] == first_entity]["window_id"].min())
        return jobs[(jobs["entity_key"] == first_entity)
                    & (jobs["window_id"] == first_window)].copy()
    if max_windows is not None:
        pairs = jobs[["entity_key", "window_id"]].drop_duplicates().head(int(max_windows))
        return jobs.merge(pairs, on=["entity_key", "window_id"]).copy()
    return jobs.iloc[0:0].copy()  # neither flag -> empty (full run is gated)


def _fit_one_job(spec, job, actuals_by_entity):
    """Fit a single challenger for one job; return (values_list, error)."""
    import pandas as pd

    entity_actuals = actuals_by_entity.get(job["entity_key"])
    if entity_actuals is None:
        return None, f"no actuals for entity {job['entity_key']}"
    mask = ((entity_actuals["date"] >= job["train_start_date"])
            & (entity_actuals["date"] <= job["train_end_date"]))
    training = entity_actuals.loc[mask, ["date", "value"]].sort_values("date")
    if training.empty:
        return None, "empty training slice"
    values = training["value"].to_numpy(dtype=float)
    dates = pd.date_range(job["test_start_date"], job["test_end_date"], freq="D")
    if len(dates) != HORIZON_DAYS:
        return None, f"expected {HORIZON_DAYS} forecast dates, got {len(dates)}"
    forecaster = _FORECASTERS[spec["forecaster"]]
    preds = forecaster(values)
    if len(preds) != len(dates):
        return None, f"forecast length mismatch ({len(preds)} vs {len(dates)})"
    return list(zip(dates, preds)), None


def run_live_fit(allow_execute: bool, smoke_test: bool,
                 max_windows) -> tuple[list[dict], int, str]:
    """Execute the clean live-fit for the 5 challengers on a bounded smoke subset.

    Staging only. Returns (per_model_results, total_rows, mode_label). Invents no
    numbers: any model that cannot fit is reported FIT_PATH_NOT_READY / failed.
    """
    import pandas as pd

    FIT_STAGING_DIR.mkdir(parents=True, exist_ok=True)
    import warnings

    warnings.filterwarnings("ignore")
    mode_label = "smoke_test" if smoke_test else (
        f"max_windows_{max_windows}" if max_windows is not None else "none")
    run_id = f"v3_3c_fit_{datetime.now():%Y%m%d_%H%M%S}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    jobs, actuals = _load_fit_inputs()
    selected = _select_fit_jobs(jobs, smoke_test, max_windows)
    actuals_by_entity = {k: g.copy() for k, g in actuals.groupby("entity_key")}

    forecast_rows: list[dict] = []
    per_model: dict[str, dict] = {
        s["model"]: dict(model=s["model"], family=s["family"], plan_name=s["plan_name"],
                         fit_attempted=False, fit_status=FIT_PATH_NOT_READY,
                         rows_generated=0, error_or_blocker="", notes="")
        for s in CHALLENGER_FIT_SPEC
    }

    for _, job in selected.iterrows():
        spec = FIT_PLAN_NAME_TO_SPEC.get(job["model_name"])
        if spec is None:
            continue
        rec = per_model[spec["model"]]
        rec["fit_attempted"] = True
        try:
            pairs, err = _fit_one_job(spec, job, actuals_by_entity)
            if err:
                rec["fit_status"] = "failed"
                rec["error_or_blocker"] = err
                continue
            for horizon_day, (fdate, fval) in enumerate(pairs, start=1):
                forecast_rows.append(dict(
                    run_id=run_id, model_name=spec["model"], model_family=spec["family"],
                    entity_key=job["entity_key"], window_id=int(job["window_id"]),
                    forecast_date=fdate.date(), horizon_day=horizon_day,
                    forecast_value=float(fval), execution_mode=mode_label,
                    created_timestamp=timestamp,
                ))
            rec["fit_status"] = "SMOKE_PASS" if smoke_test else "FIT_OK"
            rec["rows_generated"] += len(pairs)
            rec["notes"] = f"Fitted via {spec['dependency']} (torch-free clean path)."
        except Exception as exc:  # noqa: BLE001 - capture, never invent results
            rec["fit_status"] = "failed"
            rec["error_or_blocker"] = f"{type(exc).__name__}: {exc}"

    # Write staged forecasts (only if any rows were produced).
    out_path = FIT_STAGING_DIR / "clean_challenger_fit_outputs.csv"
    cols = ["run_id", "model_name", "model_family", "entity_key", "window_id",
            "forecast_date", "horizon_day", "forecast_value", "execution_mode",
            "created_timestamp"]
    pd.DataFrame(forecast_rows, columns=cols).to_csv(out_path, index=False)

    total_rows = len(forecast_rows)
    return list(per_model.values()), total_rows, mode_label


# --------------------------------------------------------------------------
# V3.3C-fit - artifact writers
# --------------------------------------------------------------------------
def _fit_status_to_ready(fit_status: str) -> str:
    if fit_status in ("SMOKE_PASS", "FIT_OK"):
        return "READY_FOR_BENCHMARK_AUTHORIZATION"
    return "NOT_READY"


def write_fit_plan_csv(fit_results: list[dict] | None) -> Path:
    FIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = FIT_OUTPUT_DIR / "clean_challenger_fit_plan.csv"
    res_by_model = {r["model"]: r for r in (fit_results or [])}
    header = [
        "model", "family", "action", "entrypoint", "execution_status",
        "expected_output_artifact", "smoke_test_status", "full_fit_ready_status",
        "notes",
    ]
    rows = []
    for s in CHALLENGER_FIT_SPEC:
        r = res_by_model.get(s["model"], {})
        fit_status = r.get("fit_status", "SMOKE_NOT_RUN")
        smoke = ("SMOKE_PASS" if fit_status in ("SMOKE_PASS", "FIT_OK")
                 else ("SMOKE_FAIL" if fit_status == "failed" else "SMOKE_NOT_RUN"))
        rows.append([
            s["model"], s["family"], "clean_live_fit",
            "python/model_lab/run_daily_clean_challengers.py",
            EXEC_STATUS_CLEAN_FIT_READY if smoke == "SMOKE_PASS" else EXEC_STATUS_NOT_READY,
            FIT_OUTPUTS_REL, smoke, _fit_status_to_ready(fit_status),
            f"Clean torch-free forecaster via {s['dependency']}; no NBEATS/NHITS.",
        ])
    _write_csv(path, header, rows)
    return path


def write_fit_result_csv(fit_results: list[dict] | None) -> Path:
    FIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = FIT_OUTPUT_DIR / "clean_challenger_fit_result.csv"
    res_by_model = {r["model"]: r for r in (fit_results or [])}
    header = [
        "model", "family", "fit_attempted", "fit_status", "rows_generated",
        "output_artifact", "error_or_blocker", "notes",
    ]
    rows = []
    for s in CHALLENGER_FIT_SPEC:
        r = res_by_model.get(s["model"])
        if r is None:
            rows.append([s["model"], s["family"], "FALSE", "SMOKE_NOT_RUN", 0,
                         "", "", "Smoke test not run (no --smoke-test/--max-windows)."])
            continue
        rows.append([
            s["model"], s["family"], "TRUE" if r["fit_attempted"] else "FALSE",
            r["fit_status"], r["rows_generated"],
            FIT_OUTPUTS_REL if r["rows_generated"] > 0 else "",
            r["error_or_blocker"], r["notes"],
        ])
    _write_csv(path, header, rows)
    return path


def write_updated_daily_15_execution_plan() -> Path:
    FIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = FIT_OUTPUT_DIR / "updated_daily_15_model_execution_plan.csv"
    baseline_models = {"FixedGrowth_1_5", "FixedGrowth_3", "FixedGrowth_4",
                       "FixedGrowth_6", "ARIMA_Fixed", "ETS_Current", "LinearRegression"}
    challenger_models = {s["model"] for s in CHALLENGER_FIT_SPEC}
    dl_models = {"FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"}
    header = [
        "model", "family", "daily_action", "execution_path",
        "execution_ready_status", "output_artifact", "notes",
    ]
    rows = []
    for m in CANONICAL_MODELS_TABLE:
        name = m["model"]
        if name in dl_models:
            rows.append([name, m["family"], "reuse_frozen_artifact",
                         "dl_reuse_frozen", "FROZEN_REUSE", DL_FROZEN_SOURCE,
                         "Reuse closed V3.2B candidate-study output; no training."])
        elif name in challenger_models:
            rows.append([name, m["family"], "train",
                         "clean_live_fit (run_daily_clean_challengers.py)",
                         EXEC_STATUS_CLEAN_FIT_READY, FIT_OUTPUTS_REL,
                         "Clean torch-free live-fit (V3.3C-fit); full fit gated behind benchmark auth."])
        elif name in baseline_models:
            action = "generate" if name.startswith("FixedGrowth") else "train"
            rows.append([name, m["family"], action,
                         "baseline_generation (run_full_baseline_execution.py)",
                         "READY_FOR_BENCHMARK_AUTHORIZATION",
                         "outputs/model_lab/full_baseline/full_baseline_forecasts.csv",
                         "Baseline/stat/ML path; heavy full run gated behind benchmark auth."])
        else:
            rows.append([name, m["family"], m["action"], "unmapped",
                         "REVIEW", "", "Unexpected model - review."])
    _write_csv(path, header, rows)
    return path


def write_fit_prohibited_guard_csv(violations: list[str]) -> Path:
    FIT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = FIT_OUTPUT_DIR / "prohibited_model_guard_result.csv"
    header = [
        "prohibited_model", "found_in_active_daily_scope", "found_in_legacy_code",
        "active_scope_status", "action_taken", "notes",
    ]
    rows = []
    for p in PROHIBITED_MODELS:
        found_active = "YES" if p in violations else "NO"
        action = ("BLOCKED_RUN_ABORTED" if p in violations
                  else "excluded_from_clean_live_fit; legacy_runner_not_used; never_imported")
        rows.append([
            p, found_active, "YES", "excluded", action,
            PROHIBITED_LEGACY_LOCATIONS.get(p, ""),
        ])
    _write_csv(path, header, rows)
    return path


# --------------------------------------------------------------------------
# V3.3C-exec - clean challenger staging executor (status reporter)
# --------------------------------------------------------------------------
def execute_clean_challengers(staging_dir: Path | None = None,
                              allow_execute: bool = False) -> list[dict]:
    """Stage the clean challenger execution status into the execution-wiring dir.

    This is the clean daily entrypoint wired into the execution path. It runs the
    shared prohibited-model guard and writes a per-challenger staging-status file.
    The clean torch-free live-fit trainer now EXISTS (V3.3C-fit, smoke-validated);
    the legacy NBEATS challenger runner remains excluded. Each challenger is
    reported as CLEAN_LIVE_FIT_READY (full fit gated behind benchmark auth).
    Returns the per-challenger result rows.
    """
    target_dir = staging_dir or EXEC_STAGING_DIR
    target_dir.mkdir(parents=True, exist_ok=True)

    models = _clean_challenger_models()
    violations = prohibited_model_guard(models)

    results: list[dict] = []
    for c in CLEAN_CHALLENGERS:
        clean = c["model"] not in PROHIBITED_MODELS and c["model"] in CANONICAL_MODEL_NAMES
        results.append(dict(
            model=c["model"], family=c["family"],
            challenger_type=c["challenger_type"], action=c["action"],
            entrypoint="python/model_lab/run_daily_clean_challengers.py",
            prohibited_model_check="CLEAN" if clean else "VIOLATION",
            execution_status=EXEC_STATUS_CLEAN_FIT_READY,
            staging_output="",
            command_when_ready=CLEAN_CHALLENGER_RUN_COMMAND,
            requires_benchmark_auth="YES",
            notes="Clean torch-free live-fit implemented (V3.3C-fit); legacy NBEATS "
                  "challenger runner excluded. Full fit gated behind benchmark auth.",
        ))

    out_path = target_dir / "clean_challenger_execution_status.csv"
    header = [
        "model", "family", "challenger_type", "action", "entrypoint",
        "prohibited_model_check", "execution_status", "staging_output",
        "command_when_ready", "requires_benchmark_auth", "notes",
    ]
    rows = [[
        r["model"], r["family"], r["challenger_type"], r["action"], r["entrypoint"],
        r["prohibited_model_check"], r["execution_status"], r["staging_output"],
        r["command_when_ready"], r["requires_benchmark_auth"], r["notes"],
    ] for r in results]
    _write_csv(out_path, header, rows)

    if violations:  # defensive - should never happen for the clean 5
        results.insert(0, dict(model="__GUARD__", execution_status="ABORTED",
                               notes=f"{PROHIBITED_VIOLATION_TOKEN}: {violations}"))
    return results


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------
def run_dry_run() -> int:
    _ensure_output_dir()
    print("=" * 70)
    print("V3.3C-next  clean-challengers  dry-run  (no training)")
    print("=" * 70)
    print("Allowed challengers the clean entrypoint will operate on:\n")
    print(f"  {'#':>2}  {'MODEL':<14} {'FAMILY':<17} {'CHALLENGER TYPE':<22} ACTION")
    print("  " + "-" * 66)
    for c in CLEAN_CHALLENGERS:
        print(f"  {c['order']:>2}  {c['model']:<14} {c['family']:<17} "
              f"{c['challenger_type']:<22} {c['action']}")

    models = _clean_challenger_models()
    violations = prohibited_model_guard(models)
    scope_path = write_clean_challenger_scope(violations)
    guard_path = write_prohibited_guard_csv(violations)

    print(f"\n  challenger count : {len(models)}")
    print(f"  prohibited check : {'CLEAN' if not violations else 'VIOLATION'}")
    print(f"  wrote {scope_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {guard_path.relative_to(PROJECT_ROOT)}")

    if violations:
        print(f"\n{PROHIBITED_VIOLATION_TOKEN}: {', '.join(violations)}")
        return 2
    if len(models) != 5:
        print("\nDRY_RUN_FAILED: clean challenger scope is not exactly 5 models")
        return 1
    print(f"\n{SCOPE_VALIDATED_TOKEN}")
    return 0


def run_validate_scope() -> int:
    _ensure_output_dir()
    print("=" * 70)
    print("V3.3C-next  clean-challengers  validate-scope")
    print("=" * 70)
    models = _clean_challenger_models()
    checks: list[tuple[str, bool, str]] = []

    checks.append(("clean_challenger_count_5", len(models) == 5, f"count={len(models)}"))
    for required in ("AutoARIMA", "ETS Explicit", "Theta", "LightGBM", "XGBoost"):
        checks.append((f"{required.lower().replace(' ', '_')}_included",
                       required in models, "present" if required in models else "MISSING"))

    in_canon = all(m in CANONICAL_MODEL_NAMES for m in models)
    checks.append(("all_in_canonical_15_universe", in_canon,
                   "ok" if in_canon else "OUT_OF_SCOPE"))

    violations = prohibited_model_guard(models)
    for p in PROHIBITED_MODELS:
        checks.append((f"{p.lower()}_excluded_from_active_scope", p not in violations,
                       "absent" if p not in violations else "PRESENT"))

    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<42} {detail}")

    scope_path = write_clean_challenger_scope(violations)
    guard_path = write_prohibited_guard_csv(violations)
    print(f"\n  wrote {scope_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {guard_path.relative_to(PROJECT_ROOT)}")

    if violations:
        print(f"\n{PROHIBITED_VIOLATION_TOKEN}: {', '.join(violations)}")
        return 2
    if not all(ok for _, ok, _ in checks):
        print("\nVALIDATE_SCOPE_FAILED")
        return 1
    print(f"\n{SCOPE_VALIDATED_TOKEN}")
    return 0


def run_plan() -> int:
    _ensure_output_dir()
    print("=" * 70)
    print("V3.3C-next  clean-challengers  plan  (no execution)")
    print("=" * 70)
    plan_path = write_daily_runner_plan_updated()
    dl_path = write_dl_reuse_wiring()
    scope_path = write_clean_challenger_scope([])

    print("  clean challengers : " + ", ".join(_clean_challenger_models()))
    print("  DL reuse (frozen) : " + ", ".join(d["model"] for d in DL_REUSE))
    print(f"\n  wrote {plan_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {dl_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {scope_path.relative_to(PROJECT_ROOT)}")
    print("\nDAILY_CLEAN_CHALLENGER_PLAN_EMITTED")
    return 0


def run_execute(allow_execute: bool, smoke_test: bool = False,
                max_windows=None) -> int:
    print("=" * 70)
    print("V3.3C-fit  clean-challengers  execute  (clean live-fit; staging only)")
    print("=" * 70)
    if not allow_execute:
        print("Execution is blocked. --execute requires the explicit "
              "--allow-execute flag.")
        print(EXEC_BLOCKED_TOKEN)
        return 3

    # Hard guard before any work.
    models = _clean_challenger_models()
    violations = prohibited_model_guard(models)
    guard_path = write_fit_prohibited_guard_csv(violations)
    print(f"  prohibited guard : {'CLEAN' if not violations else 'VIOLATION'}")
    print(f"  wrote {guard_path.relative_to(PROJECT_ROOT)}")
    if violations:
        print(f"\n{PROHIBITED_VIOLATION_TOKEN}: {', '.join(violations)}")
        return 2

    # Safety: a bounded smoke subset is required; the full run is gated.
    if not smoke_test and max_windows is None:
        print("\n  Full clean live-fit (all entity-windows) is gated behind "
              "benchmark authorization.")
        print("  Re-run with --smoke-test (or --max-windows N) to validate wiring.")
        plan_path = write_fit_plan_csv(None)
        result_path = write_fit_result_csv(None)
        upd_path = write_updated_daily_15_execution_plan()
        for p in (plan_path, result_path, upd_path):
            print(f"  wrote {p.relative_to(PROJECT_ROOT)}")
        print("\nCLEAN_CHALLENGER_FULL_FIT_REQUIRES_BENCHMARK_AUTHORIZATION")
        return 0

    # Bounded clean live-fit (smoke / max-windows). Staging only.
    fit_results, total_rows, mode_label = run_live_fit(
        allow_execute=allow_execute, smoke_test=smoke_test, max_windows=max_windows)

    plan_path = write_fit_plan_csv(fit_results)
    result_path = write_fit_result_csv(fit_results)
    upd_path = write_updated_daily_15_execution_plan()
    out_path = FIT_STAGING_DIR / "clean_challenger_fit_outputs.csv"

    ok = sum(1 for r in fit_results if r["fit_status"] in ("SMOKE_PASS", "FIT_OK"))
    failed = [r["model"] for r in fit_results if r["fit_status"] == "failed"]
    print(f"\n  mode             : {mode_label}")
    print(f"  challengers fit  : {ok}/5 passed")
    if failed:
        print(f"  failed           : {', '.join(failed)}")
    print(f"  forecast rows    : {total_rows}")
    print(f"  wrote {out_path.relative_to(PROJECT_ROOT)}")
    for p in (plan_path, result_path, upd_path):
        print(f"  wrote {p.relative_to(PROJECT_ROOT)}")
    print("  staging only - no promotion to data/processed; no champion change.")

    if ok == 5:
        print(f"\n{FIT_COMPLETED_TOKEN}")
        return 0
    print(f"\n{FIT_PARTIAL_TOKEN}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="V3.3C clean daily challenger entrypoint "
                    "(scope/plan/guard + clean live-fit).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate-scope", action="store_true")
    group.add_argument("--dry-run", action="store_true")
    group.add_argument("--plan", action="store_true")
    group.add_argument("--execute", action="store_true",
                       help="Clean torch-free live-fit (staging only). Requires "
                            "--allow-execute and a bounded subset (--smoke-test or "
                            "--max-windows). Full run gated behind benchmark auth. "
                            "Legacy NBEATS runner excluded.")
    parser.add_argument("--allow-execute", action="store_true",
                        help="Explicit opt-in required by --execute.")
    parser.add_argument("--smoke-test", action="store_true",
                        help="Validate wiring on a single entity-window (no runtime "
                             "measurement, no full 454-window run).")
    parser.add_argument("--max-windows", type=int, default=None,
                        help="Bound the live-fit to the first N entity-windows.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] project_root={PROJECT_ROOT}")
    if args.validate_scope:
        return run_validate_scope()
    if args.dry_run:
        return run_dry_run()
    if args.plan:
        return run_plan()
    if args.execute:
        return run_execute(args.allow_execute, smoke_test=args.smoke_test,
                           max_windows=args.max_windows)
    return 1


if __name__ == "__main__":
    sys.exit(main())
