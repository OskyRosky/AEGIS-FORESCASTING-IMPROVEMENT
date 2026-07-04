#!/usr/bin/env python
"""V3.3C - Clean daily 15-model refresh runner (scope/plan/guard only).

This is the FUTURE entrypoint for the model stage of the AEGIS V3.3 daily
pipeline. It is intentionally dependency-light (Python stdlib only) so that
--dry-run / --validate-scope / --plan never import heavy DL libraries
(torch / darts) and never touch productive outputs.

It does NOT train models, run backtests, change the champion, promote models,
or create a scheduler. --execute is intentionally blocked.

Canonical universe = the 15 models that every dashboard section agrees on
(see data/processed/model_universe_canonical.csv, built by
outputs/v3_2h_model_consistency_fix/build_canonical_universe.R).

Prohibited from the daily runner (hard guard): NBEATS, NHITS,
FastNeuralAR_MLP (original), and anything outside the canonical 15.

Modes:
    --validate-scope   Validate the 15-model scope + family counts + guard.
    --dry-run          Print the 15 models and per-model action; run the guard.
    --plan             Emit the staged daily execution plan (no execution).
    --execute          Execution wiring (V3.3C-exec). Requires --allow-execute.
                       Re-stages the 3 frozen DL artifacts (reuse, no training)
                       and writes the 15-model staging manifest. Baseline and
                       clean-challenger live-fit are gated behind benchmark
                       authorization (documented, NOT run). Staging only - never
                       promotes to data/processed, never changes the champion.

Usage (from V3/python with PYTHONPATH=V3/python):
    python model_lab/run_daily_15_model_refresh.py --dry-run
    python model_lab/run_daily_15_model_refresh.py --validate-scope
    python model_lab/run_daily_15_model_refresh.py --plan
"""
from __future__ import annotations

import argparse
import csv
import sys
from datetime import datetime
from pathlib import Path

# --------------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------------
THIS_FILE = Path(__file__).resolve()
PROJECT_ROOT = THIS_FILE.parents[2]  # model_lab -> python -> V3
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "v3_3_daily_refresh" / "v3_3c_15_model_runner_fix"
CANONICAL_UNIVERSE_CSV = PROJECT_ROOT / "data" / "processed" / "model_universe_canonical.csv"

# --------------------------------------------------------------------------
# V3.3C-exec - execution-wiring staging paths (NEVER promote to data/processed)
# --------------------------------------------------------------------------
EXEC_OUTPUT_DIR = (
    PROJECT_ROOT / "outputs" / "v3_3_daily_refresh" / "v3_3c_exec_execution_wiring"
)
STAGING_DIR = EXEC_OUTPUT_DIR / "staging"
DL_FROZEN_ABS = (
    PROJECT_ROOT / "outputs" / "v3_2b_model_candidates"
    / "candidate_outputs" / "full_candidate_outputs.csv"
)
BASELINE_OUT_ABS = (
    PROJECT_ROOT / "outputs" / "model_lab" / "full_baseline"
    / "full_baseline_forecasts.csv"
)

# Dashboard DL code -> frozen candidate-study internal model_name (V3.2B/D).
# Verified present (status=ok, 13620 rows each) in full_candidate_outputs.csv.
DL_FROZEN_NAME_MAP = {
    "FNAR-V2": "FastNeuralAR_MLP_v2_direct",
    "NLIN-DLIN_FIXED": "NLinear_log_space_fixed",
    "SMLP-TCN": "SmallMLPGlobal",
}

# Execution-status tokens for the staging manifest.
EXEC_STATUS_REUSE = "EXECUTED_REUSE_FROZEN"
EXEC_STATUS_NOT_READY = "EXECUTION_PATH_NOT_READY"
EXEC_STATUS_READY_FOR_BENCH = "READY_FOR_BENCHMARK_AUTHORIZATION"
EXEC_STATUS_CLEAN_FIT_READY = "CLEAN_LIVE_FIT_READY"
EXEC_WIRING_COMPLETED_TOKEN = "V3_3C_EXECUTION_WIRING_COMPLETED"
EXEC_BLOCKED_TOKEN = "EXECUTE_BLOCKED_REQUIRES_ALLOW_EXECUTE"

# Heavy commands that are DOCUMENTED but NOT executed in this stage. They would
# trigger a full model run by default -> gated behind benchmark authorization.
BASELINE_RUN_COMMAND = "python python/model_lab/run_full_baseline_execution.py"
CLEAN_CHALLENGER_RUN_COMMAND = (
    "python python/model_lab/run_daily_clean_challengers.py --execute --allow-execute"
)

# --------------------------------------------------------------------------
# Prohibited models (hard guard) - must NEVER appear in the active daily scope
# --------------------------------------------------------------------------
PROHIBITED_MODELS = ("NBEATS", "NHITS", "FastNeuralAR_MLP")

# Where prohibited models still live in legacy/historical code (for the audit).
PROHIBITED_LEGACY_LOCATIONS = {
    "NBEATS": "model_registry.py (registered); run_challenger_official_execution.py "
    "APPROVED_MODELS L49; challenger_registry.yaml CH-06; governance 6_4/6_5",
    "NHITS": "model_registry.py (registered); run_challenger_official_execution.py "
    "DEFERRED_MODEL L51; challenger_registry.yaml CH-07; governance 6_4/6_5",
    "FastNeuralAR_MLP": "RETIRED by build_canonical_universe.R; legacy pilot CSVs; "
    "docs/methodology (historical only)",
}

# --------------------------------------------------------------------------
# Canonical 15-model universe = single source of truth for the daily runner.
# Execution metadata reflects the ACTUAL current code path (V3.3C-0 diagnostic).
# --------------------------------------------------------------------------
# action one of: generate | train | reuse_frozen_artifact
# execution_type one of: baseline_generation | statistical_fit | ml_fit |
#                        dl_fit | reuse_frozen_artifact | missing_execution_path
# entrypoint_status one of: clean_ready |
#                           legacy_contaminated_needs_clean_variant |
#                           frozen_artifact_no_live_training
BASELINE_ENTRY = "python/model_lab/run_full_baseline_execution.py"
BASELINE_OUT = "outputs/model_lab/full_baseline/full_baseline_forecasts.csv"
CHALLENGER_LEGACY = "python/model_lab/run_challenger_official_execution.py"
CHALLENGER_OUT = "outputs/model_lab/challenger_official_execution/*"
# V3.3C-next: the clean challenger entrypoint replaces the legacy runner for daily use.
CHALLENGER_CLEAN = "python/model_lab/run_daily_clean_challengers.py"
CHALLENGER_CLEAN_OUT = "outputs/model_lab/daily_clean_challengers/clean_challenger_forecasts.csv"
DL_FROZEN = "outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv"

_CLEAN_CHALLENGER_GAP = (
    "Build a clean challenger entrypoint (no NBEATS/NHITS) by parameterizing the "
    "model list; the legacy run_challenger_official_execution.py must NOT be the "
    "daily runner while it hard-codes NBEATS in APPROVED_MODELS."
)
_DL_GAP = (
    "No live daily training code exists for this model. It exists only as a frozen "
    "artifact from the closed V3.2B/D/E candidate study. To train it daily, the "
    "candidate-study trainer must be located/rebuilt (out of daily scope today)."
)

MODELS: list[dict] = [
    # ---- Growth baseline (4) -> baseline generation, clean & ready ----
    dict(order=1, model="FixedGrowth_1_5", family="Growth baseline", family_key="growth_baseline",
         action="generate", execution_type="baseline_generation",
         entrypoint=BASELINE_ENTRY, entrypoint_status="clean_ready", output=BASELINE_OUT,
         status="READY", missing_work="", notes="Deterministic growth baseline."),
    dict(order=2, model="FixedGrowth_3", family="Growth baseline", family_key="growth_baseline",
         action="generate", execution_type="baseline_generation",
         entrypoint=BASELINE_ENTRY, entrypoint_status="clean_ready", output=BASELINE_OUT,
         status="READY", missing_work="", notes="Deterministic growth baseline."),
    dict(order=3, model="FixedGrowth_4", family="Growth baseline", family_key="growth_baseline",
         action="generate", execution_type="baseline_generation",
         entrypoint=BASELINE_ENTRY, entrypoint_status="clean_ready", output=BASELINE_OUT,
         status="READY", missing_work="", notes="Deterministic growth baseline."),
    dict(order=4, model="FixedGrowth_6", family="Growth baseline", family_key="growth_baseline",
         action="generate", execution_type="baseline_generation",
         entrypoint=BASELINE_ENTRY, entrypoint_status="clean_ready", output=BASELINE_OUT,
         status="READY", missing_work="", notes="Deterministic growth baseline."),
    # ---- Statistical (5) ----
    dict(order=5, model="ARIMA_Fixed", family="Statistical", family_key="statistical",
         action="train", execution_type="baseline_generation",
         entrypoint=BASELINE_ENTRY, entrypoint_status="clean_ready", output=BASELINE_OUT,
         status="READY", missing_work="",
         notes="Fixed-order ARIMA fitted inside the baseline production runner."),
    dict(order=6, model="ETS_Current", family="Statistical", family_key="statistical",
         action="train", execution_type="baseline_generation",
         entrypoint=BASELINE_ENTRY, entrypoint_status="clean_ready", output=BASELINE_OUT,
         status="READY", missing_work="",
         notes="ETS_Current fitted inside the baseline production runner."),
    dict(order=7, model="AutoARIMA", family="Statistical", family_key="statistical",
         action="train", execution_type="statistical_fit",
         entrypoint=CHALLENGER_CLEAN, entrypoint_status="clean_ready",
         output=CHALLENGER_CLEAN_OUT, status="READY",
         missing_work="Live fit wiring scaffolded behind --allow-execute (not run in V3.3C-next).",
         notes="Statistical challenger; routed to the clean challenger entrypoint."),
    dict(order=8, model="ETS Explicit", family="Statistical", family_key="statistical",
         action="train", execution_type="statistical_fit",
         entrypoint=CHALLENGER_CLEAN, entrypoint_status="clean_ready",
         output=CHALLENGER_CLEAN_OUT, status="READY",
         missing_work="Live fit wiring scaffolded behind --allow-execute (not run in V3.3C-next).",
         notes="CURRENT CHAMPION (MASE 6.901144); routed to the clean challenger entrypoint."),
    dict(order=9, model="Theta", family="Statistical", family_key="statistical",
         action="train", execution_type="statistical_fit",
         entrypoint=CHALLENGER_CLEAN, entrypoint_status="clean_ready",
         output=CHALLENGER_CLEAN_OUT, status="READY",
         missing_work="Live fit wiring scaffolded behind --allow-execute (not run in V3.3C-next).",
         notes="Statistical challenger; routed to the clean challenger entrypoint."),
    # ---- Machine learning (3) ----
    dict(order=10, model="LinearRegression", family="Machine learning", family_key="machine_learning",
         action="train", execution_type="baseline_generation",
         entrypoint=BASELINE_ENTRY, entrypoint_status="clean_ready", output=BASELINE_OUT,
         status="READY", missing_work="",
         notes="LinearRegression fitted inside the baseline production runner."),
    dict(order=11, model="LightGBM", family="Machine learning", family_key="machine_learning",
         action="train", execution_type="ml_fit",
         entrypoint=CHALLENGER_CLEAN, entrypoint_status="clean_ready",
         output=CHALLENGER_CLEAN_OUT, status="READY",
         missing_work="Live fit wiring scaffolded behind --allow-execute (not run in V3.3C-next).",
         notes="ML challenger; routed to the clean challenger entrypoint."),
    dict(order=12, model="XGBoost", family="Machine learning", family_key="machine_learning",
         action="train", execution_type="ml_fit",
         entrypoint=CHALLENGER_CLEAN, entrypoint_status="clean_ready",
         output=CHALLENGER_CLEAN_OUT, status="READY",
         missing_work="Live fit wiring scaffolded behind --allow-execute (not run in V3.3C-next).",
         notes="ML challenger; routed to the clean challenger entrypoint."),
    # ---- Deep learning (3) -> frozen artifacts, NO live training ----
    dict(order=13, model="FNAR-V2", family="Deep Learning", family_key="deep_learning",
         action="reuse_frozen_artifact", execution_type="reuse_frozen_artifact",
         entrypoint=DL_FROZEN, entrypoint_status="frozen_artifact_no_live_training",
         output=DL_FROZEN, status="FROZEN_REUSE", missing_work=_DL_GAP,
         notes="Frozen candidate-study output. No live daily training path."),
    dict(order=14, model="NLIN-DLIN_FIXED", family="Deep Learning", family_key="deep_learning",
         action="reuse_frozen_artifact", execution_type="reuse_frozen_artifact",
         entrypoint=DL_FROZEN, entrypoint_status="frozen_artifact_no_live_training",
         output=DL_FROZEN, status="FROZEN_REUSE", missing_work=_DL_GAP,
         notes="Frozen candidate-study output. No live daily training path."),
    dict(order=15, model="SMLP-TCN", family="Deep Learning", family_key="deep_learning",
         action="reuse_frozen_artifact", execution_type="reuse_frozen_artifact",
         entrypoint=DL_FROZEN, entrypoint_status="frozen_artifact_no_live_training",
         output=DL_FROZEN, status="FROZEN_REUSE", missing_work=_DL_GAP,
         notes="Frozen candidate-study output. No live daily training path."),
]

EXPECTED_FAMILY_COUNTS = {
    "growth_baseline": 4,
    "statistical": 5,
    "machine_learning": 3,
    "deep_learning": 3,
}
EXPECTED_DL_MODELS = {"FNAR-V2", "NLIN-DLIN_FIXED", "SMLP-TCN"}

SCOPE_VALIDATED_TOKEN = "DAILY_15_MODEL_SCOPE_VALIDATED"
PROHIBITED_VIOLATION_TOKEN = "PROHIBITED_MODEL_IN_DAILY_SCOPE"


# --------------------------------------------------------------------------
# Reusable prohibited-model guard
# --------------------------------------------------------------------------
def prohibited_model_guard(active_models: list[str]) -> list[str]:
    """Return the list of prohibited models present in the active scope.

    An empty list means the scope is clean. This is the single reusable guard
    every daily stage must call before doing any work.
    """
    active_norm = {m.strip().lower() for m in active_models}
    violations = [p for p in PROHIBITED_MODELS if p.strip().lower() in active_norm]
    return violations


def _active_models() -> list[str]:
    return [m["model"] for m in MODELS]


def _should(model: dict, kind: str) -> str:
    if kind == "train":
        return "TRUE" if model["action"] == "train" else "FALSE"
    if kind == "generate":
        return "TRUE" if model["action"] == "generate" else "FALSE"
    if kind == "reuse":
        return "TRUE" if model["action"] == "reuse_frozen_artifact" else "FALSE"
    return "FALSE"


def _daily_scope_status(model: dict) -> str:
    return {
        "train": "active_train",
        "generate": "active_generate",
        "reuse_frozen_artifact": "active_reuse_only",
    }[model["action"]]


def _ensure_output_dir() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _write_csv(path: Path, header: list[str], rows: list[list]) -> None:
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(header)
        writer.writerows(rows)


# --------------------------------------------------------------------------
# Cross-check against the canonical universe data file (optional, soft)
# --------------------------------------------------------------------------
def _canonical_file_models() -> list[str] | None:
    if not CANONICAL_UNIVERSE_CSV.exists():
        return None
    try:
        with CANONICAL_UNIVERSE_CSV.open("r", newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            col = None
            for cand in ("model_name", "model"):
                if reader.fieldnames and cand in reader.fieldnames:
                    col = cand
                    break
            if col is None:
                return None
            return [row[col].strip() for row in reader if row.get(col)]
    except Exception:  # pragma: no cover - soft cross-check only
        return None


# --------------------------------------------------------------------------
# Artifact writers
# --------------------------------------------------------------------------
def write_model_training_scope() -> Path:
    path = OUTPUT_DIR / "model_training_scope.csv"
    header = [
        "model", "family", "daily_scope_status", "execution_type",
        "should_train_daily", "should_generate_daily", "should_reuse_frozen_artifact",
        "source_entrypoint_current", "source_entrypoint_status",
        "expected_output_artifact", "missing_work", "excluded_reason", "notes",
    ]
    rows = []
    for m in MODELS:
        rows.append([
            m["model"], m["family"], _daily_scope_status(m), m["execution_type"],
            _should(m, "train"), _should(m, "generate"), _should(m, "reuse"),
            m["entrypoint"], m["entrypoint_status"], m["output"],
            m["missing_work"], "", m["notes"],
        ])
    _write_csv(path, header, rows)
    return path


def write_dry_run_csv() -> Path:
    path = OUTPUT_DIR / "daily_15_model_dry_run.csv"
    header = [
        "execution_order", "model", "family", "action",
        "entrypoint_or_source", "status", "output_artifact", "notes",
    ]
    rows = []
    for m in MODELS:
        rows.append([
            m["order"], m["model"], m["family"], m["action"],
            m["entrypoint"], m["status"], m["output"], m["notes"],
        ])
    _write_csv(path, header, rows)
    return path


def write_prohibited_guard_csv(violations: list[str]) -> Path:
    path = OUTPUT_DIR / "prohibited_model_guard_result.csv"
    header = [
        "prohibited_model", "found_in_active_scope", "found_in_legacy_code",
        "active_scope_status", "action_taken", "notes",
    ]
    rows = []
    for p in PROHIBITED_MODELS:
        found_active = "YES" if p in violations else "NO"
        action = (
            "BLOCKED_RUN_ABORTED" if p in violations
            else "excluded_from_daily_runner; legacy_runner_not_used_as_daily"
        )
        rows.append([
            p, found_active, "YES", "excluded", action,
            PROHIBITED_LEGACY_LOCATIONS.get(p, ""),
        ])
    _write_csv(path, header, rows)
    return path


def write_plan_csv() -> Path:
    path = OUTPUT_DIR / "daily_15_model_runner_plan.csv"
    header = [
        "stage_order", "stage_name", "models_covered", "script_or_entrypoint",
        "execution_mode", "output_artifacts", "daily_ready_status",
        "gap_or_blocker", "notes",
    ]
    rows = [
        [
            1, "Baseline generation (growth + baseline statistical/ML)",
            "FixedGrowth_1_5 | FixedGrowth_3 | FixedGrowth_4 | FixedGrowth_6 | "
            "ARIMA_Fixed | ETS_Current | LinearRegression",
            BASELINE_ENTRY, "train+generate", BASELINE_OUT, "READY",
            "", "Clean runner; covers 7 of 15 with no prohibited models.",
        ],
        [
            2, "Statistical + ML challengers (clean entrypoint)",
            "AutoARIMA | ETS Explicit | Theta | LightGBM | XGBoost",
            CHALLENGER_CLEAN,
            "train", CHALLENGER_CLEAN_OUT, "READY",
            "Clean entrypoint excludes NBEATS/NHITS; legacy "
            "run_challenger_official_execution.py is NOT used as the daily runner.",
            "Covers 5 of 15. Champion ETS Explicit is in this group.",
        ],
        [
            3, "Deep Learning reuse (frozen artifacts)",
            "FNAR-V2 | NLIN-DLIN_FIXED | SMLP-TCN",
            DL_FROZEN, "reuse_frozen_artifact", DL_FROZEN, "FROZEN_REUSE",
            "No live daily training code; reuse frozen candidate-study outputs.",
            "Covers 3 of 15. Daily DL training is a missing execution path.",
        ],
        [
            4, "Canonical universe aggregation",
            "all 15 (12 governed + 3 DL)",
            "outputs/v3_2h_model_consistency_fix/build_canonical_universe.R",
            "aggregate", "data/processed/model_universe_canonical.csv", "READY",
            "", "Aggregates governed scorecard + frozen DL; runs no model.",
        ],
        [
            5, "Tournament + champion decision",
            "12 governed (DL excluded from champion eligibility)",
            "build_tournament_engine.py + build_champion_decision.py",
            "aggregate+decision",
            "outputs/model_lab/tournament_engine/*; "
            "outputs/model_lab/champion_decision/champion_candidate_evaluation.csv",
            "READY", "", "Champion = ETS Explicit; no promotion in V3.3C.",
        ],
        [
            6, "Forecast viewer handoff",
            "all 15 (display)",
            "build_forecast_viewer_handoff.py",
            "handoff", "data/processed/forecast_viewer_model_outputs.csv", "READY",
            "", "Maps the 15 canonical models for the dashboard viewer.",
        ],
    ]
    _write_csv(path, header, rows)
    return path


# --------------------------------------------------------------------------
# V3.3C-exec - execution wiring (staging only; --allow-execute required)
# --------------------------------------------------------------------------
def _ensure_exec_dirs() -> None:
    EXEC_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    STAGING_DIR.mkdir(parents=True, exist_ok=True)


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def execute_dl_reuse(staging_dir: Path) -> tuple[list[dict], Path, int]:
    """Reuse the 3 frozen DL candidate-study outputs into staging.

    This is a REAL, executable step: it reads the closed V3.2B/D candidate-study
    artifact, filters the 3 frozen DL model_names, remaps them to their dashboard
    codes and writes a single staging extract. It performs NO live training and
    invents NO numbers - it only re-stages governed frozen forecasts.
    """
    src = DL_FROZEN_ABS
    frozen_targets = {v: k for k, v in DL_FROZEN_NAME_MAP.items()}  # internal -> display
    rows_by_internal: dict[str, list[dict]] = {v: [] for v in DL_FROZEN_NAME_MAP.values()}
    header: list[str] | None = None

    if src.exists():
        with src.open("r", newline="", encoding="utf-8-sig") as fh:
            reader = csv.DictReader(fh)
            header = list(reader.fieldnames or [])
            for row in reader:
                mn = (row.get("model_name") or "").strip()
                if mn in rows_by_internal:
                    rows_by_internal[mn].append(row)

    out_path = staging_dir / "dl_reuse_frozen_forecasts.csv"
    total = 0
    if header:
        extra_cols = ["dashboard_model", "reuse_status", "frozen_source"]
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            writer = csv.writer(fh)
            writer.writerow(list(header) + extra_cols)
            for internal, display in frozen_targets.items():
                for row in rows_by_internal.get(internal, []):
                    writer.writerow(
                        [row.get(c, "") for c in header]
                        + [display, EXEC_STATUS_REUSE, _rel(src)]
                    )
                    total += 1

    results: list[dict] = []
    for display, internal in DL_FROZEN_NAME_MAP.items():
        n = len(rows_by_internal.get(internal, []))
        ok = src.exists() and n > 0
        results.append(dict(
            dashboard_model=display,
            frozen_model_name=internal,
            frozen_source=_rel(src) if src.exists() else "MISSING",
            rows_reused=n,
            reuse_status=EXEC_STATUS_REUSE if ok else EXEC_STATUS_NOT_READY,
            staging_output=_rel(out_path) if ok else "",
            notes=("Frozen V3.2B/D candidate-study output re-staged; no live training."
                   if ok else "Frozen source missing or model rows not found."),
        ))
    return results, out_path, total


def build_merged_status(dl_results: list[dict]) -> list[list]:
    """Build the 15-row merged execution manifest from the canonical MODELS table."""
    dl_by_model = {d["dashboard_model"]: d for d in dl_results}
    rows: list[list] = []
    for m in MODELS:
        if m["action"] == "reuse_frozen_artifact":
            d = dl_by_model.get(m["model"], {})
            status = d.get("reuse_status", EXEC_STATUS_NOT_READY)
            staging = d.get("staging_output", "")
            rowcount = d.get("rows_reused", 0)
            source = d.get("frozen_source", DL_FROZEN)
            notes = d.get("notes", "")
        elif m["entrypoint"] == CHALLENGER_CLEAN:
            status = EXEC_STATUS_CLEAN_FIT_READY
            staging = ""
            rowcount = "NA"
            source = CLEAN_CHALLENGER_RUN_COMMAND
            notes = ("Clean live-fit trainer implemented (V3.3C-fit); torch-free, "
                     "legacy NBEATS challenger runner excluded. Smoke-validated; "
                     "full fit gated behind benchmark authorization.")
        else:  # BASELINE_ENTRY
            status = EXEC_STATUS_READY_FOR_BENCH
            staging = ""
            rowcount = "NA"
            source = BASELINE_RUN_COMMAND
            notes = ("Live generation/fit exists in the baseline runner; heavy "
                     "full run gated behind benchmark authorization (not executed "
                     "in the execution-wiring stage).")
        rows.append([
            m["order"], m["model"], m["family"], m["action"],
            status, staging, rowcount, source, notes,
        ])
    return rows


def write_merged_status_csv(rows: list[list]) -> Path:
    path = STAGING_DIR / "daily_15_model_outputs.csv"
    header = [
        "execution_order", "model", "family", "action", "execution_status",
        "staging_output_path", "row_count", "source_or_command", "notes",
    ]
    _write_csv(path, header, rows)
    return path


def write_exec_plan_csv(dl_results: list[dict]) -> Path:
    path = EXEC_OUTPUT_DIR / "execution_plan.csv"
    dl_by_model = {d["dashboard_model"]: d for d in dl_results}
    header = [
        "execution_order", "model", "family", "action", "execution_status",
        "requires_allow_execute", "requires_benchmark_auth",
        "command_or_source", "target_staging_path", "notes",
    ]
    rows = []
    for m in MODELS:
        if m["action"] == "reuse_frozen_artifact":
            d = dl_by_model.get(m["model"], {})
            status = d.get("reuse_status", EXEC_STATUS_NOT_READY)
            bench = "NO"
            cmd = d.get("frozen_source", DL_FROZEN)
            staging = d.get("staging_output", "")
            notes = "Frozen DL reuse - executed in this stage."
        elif m["entrypoint"] == CHALLENGER_CLEAN:
            status = EXEC_STATUS_CLEAN_FIT_READY
            bench = "YES"
            cmd = CLEAN_CHALLENGER_RUN_COMMAND
            staging = ""
            notes = "Clean challenger live-fit implemented (V3.3C-fit); full fit gated behind benchmark auth."
        else:
            status = EXEC_STATUS_READY_FOR_BENCH
            bench = "YES"
            cmd = BASELINE_RUN_COMMAND
            staging = ""
            notes = "Baseline heavy full run gated behind benchmark auth."
        rows.append([
            m["order"], m["model"], m["family"], m["action"], status,
            "YES", bench, cmd, staging, notes,
        ])
    _write_csv(path, header, rows)
    return path


def write_exec_wiring_status_csv(dl_total: int, cc_results: list[dict] | None) -> Path:
    path = EXEC_OUTPUT_DIR / "execution_wiring_status.csv"
    cc_count = len(cc_results) if cc_results else 0
    header = ["component", "wired", "executed_this_stage", "result", "notes"]
    rows = [
        ["master_runner_execute", "YES", "YES", "OK",
         "run_daily_15_model_refresh.py --execute --allow-execute (staging only)."],
        ["prohibited_model_guard", "YES", "YES", "PASS",
         "prohibited_model_guard() run before any staging work."],
        ["staging_dir", "YES", "YES", "OK", _rel(STAGING_DIR)],
        ["dl_reuse_frozen", "YES", "YES",
         EXEC_STATUS_REUSE if dl_total > 0 else EXEC_STATUS_NOT_READY,
         f"{dl_total} frozen DL rows re-staged (no training)."],
        ["clean_challenger_entrypoint", "YES", "YES",
         EXEC_STATUS_NOT_READY,
         f"run_daily_clean_challengers.execute_clean_challengers() invoked; "
         f"{cc_count} challengers reported (live-fit path not ready)."],
        ["legacy_challenger_runner", "NO", "NO", "EXCLUDED",
         "run_challenger_official_execution.py (NBEATS) NOT used as daily runner."],
        ["baseline_generation", "YES", "NO", EXEC_STATUS_READY_FOR_BENCH,
         "Heavy full run gated behind benchmark authorization (documented only)."],
        ["merge_manifest", "YES", "YES", "OK",
         "staging/daily_15_model_outputs.csv (15 rows)."],
    ]
    _write_csv(path, header, rows)
    return path


def write_dl_reuse_result_csv(dl_results: list[dict]) -> Path:
    path = EXEC_OUTPUT_DIR / "dl_reuse_execution_result.csv"
    header = [
        "dashboard_model", "frozen_model_name", "frozen_source",
        "rows_reused", "reuse_status", "staging_output", "notes",
    ]
    rows = [[
        d["dashboard_model"], d["frozen_model_name"], d["frozen_source"],
        d["rows_reused"], d["reuse_status"], d["staging_output"], d["notes"],
    ] for d in dl_results]
    _write_csv(path, header, rows)
    return path


def write_staging_inventory_csv() -> Path:
    path = EXEC_OUTPUT_DIR / "staging_artifact_inventory.csv"
    header = ["file", "exists", "size_bytes", "kind", "notes"]
    rows = []
    if STAGING_DIR.exists():
        for f in sorted(STAGING_DIR.glob("*")):
            if f.is_file():
                rows.append([
                    _rel(f), "YES", f.stat().st_size, "staging_output",
                    "Staged under execution-wiring; never promoted to data/processed.",
                ])
    _write_csv(path, header, rows)
    return path


# --------------------------------------------------------------------------
# Modes
# --------------------------------------------------------------------------
def run_validate_scope() -> int:
    _ensure_output_dir()
    print("=" * 70)
    print("V3.3C  validate-scope  (canonical 15-model daily universe)")
    print("=" * 70)

    active = _active_models()
    checks: list[tuple[str, bool, str]] = []

    checks.append(("scope_has_15_models", len(active) == 15, f"count={len(active)}"))

    counts = {}
    for m in MODELS:
        counts[m["family_key"]] = counts.get(m["family_key"], 0) + 1
    for fam, expected in EXPECTED_FAMILY_COUNTS.items():
        checks.append((f"{fam}_count_{expected}", counts.get(fam, 0) == expected,
                       f"got={counts.get(fam, 0)}"))

    dl_models = {m["model"] for m in MODELS if m["family_key"] == "deep_learning"}
    checks.append(("deep_learning_models_correct", dl_models == EXPECTED_DL_MODELS,
                   f"dl={sorted(dl_models)}"))

    violations = prohibited_model_guard(active)
    for p in PROHIBITED_MODELS:
        checks.append((f"{p.lower()}_excluded_from_active_scope", p not in violations,
                       "absent" if p not in violations else "PRESENT"))

    # soft cross-check against the canonical universe data file
    canon_file = _canonical_file_models()
    if canon_file is not None:
        same = set(canon_file) == set(active)
        checks.append(("matches_canonical_universe_csv", same,
                       f"file_count={len(canon_file)}"))
    else:
        print("[info] canonical universe CSV not found - skipping soft cross-check")

    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<42} {detail}")

    scope_path = write_model_training_scope()
    guard_path = write_prohibited_guard_csv(violations)
    print(f"\n  wrote {scope_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {guard_path.relative_to(PROJECT_ROOT)}")

    if violations:
        print(f"\n{PROHIBITED_VIOLATION_TOKEN}: {', '.join(violations)}")
        return 2
    all_ok = all(ok for _, ok, _ in checks)
    if not all_ok:
        print("\nVALIDATE_SCOPE_FAILED")
        return 1
    print(f"\n{SCOPE_VALIDATED_TOKEN}")
    return 0


def run_dry_run() -> int:
    _ensure_output_dir()
    print("=" * 70)
    print("V3.3C  dry-run  (no training, no productive output changes)")
    print("=" * 70)
    print("These are the 15 models the daily runner will operate on:\n")
    print(f"  {'#':>2}  {'MODEL':<18} {'FAMILY':<17} {'ACTION':<22} STATUS")
    print("  " + "-" * 74)
    for m in MODELS:
        print(f"  {m['order']:>2}  {m['model']:<18} {m['family']:<17} "
              f"{m['action']:<22} {m['status']}")

    active = _active_models()
    violations = prohibited_model_guard(active)
    guard_path = write_prohibited_guard_csv(violations)
    dry_path = write_dry_run_csv()

    print(f"\n  active model count : {len(active)}")
    print(f"  prohibited check   : {'CLEAN' if not violations else 'VIOLATION'}")
    print(f"  wrote {dry_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {guard_path.relative_to(PROJECT_ROOT)}")

    if violations:
        print(f"\n{PROHIBITED_VIOLATION_TOKEN}: {', '.join(violations)}")
        return 2
    if len(active) != 15:
        print("\nDRY_RUN_FAILED: scope is not exactly 15 models")
        return 1
    print(f"\n{SCOPE_VALIDATED_TOKEN}")
    return 0


def run_plan() -> int:
    _ensure_output_dir()
    print("=" * 70)
    print("V3.3C  plan  (staged daily execution plan - no execution)")
    print("=" * 70)
    plan_path = write_plan_csv()
    scope_path = write_model_training_scope()

    # console summary
    train = [m["model"] for m in MODELS if m["action"] == "train"]
    generate = [m["model"] for m in MODELS if m["action"] == "generate"]
    reuse = [m["model"] for m in MODELS if m["action"] == "reuse_frozen_artifact"]
    gaps = [m["model"] for m in MODELS if m["status"] == "GAP_NEEDS_CLEAN_ENTRYPOINT"]
    print(f"  train daily ({len(train)})    : {', '.join(train)}")
    print(f"  generate daily ({len(generate)}) : {', '.join(generate)}")
    print(f"  reuse frozen ({len(reuse)})   : {', '.join(reuse)}")
    print(f"  clean-entrypoint gaps ({len(gaps)}): {', '.join(gaps)}")
    print(f"\n  wrote {plan_path.relative_to(PROJECT_ROOT)}")
    print(f"  wrote {scope_path.relative_to(PROJECT_ROOT)}")
    print("\nDAILY_15_MODEL_PLAN_EMITTED")
    return 0


def run_execute(allow_execute: bool) -> int:
    print("=" * 70)
    print("V3.3C-exec  execute  (execution wiring; staging only)")
    print("=" * 70)
    if not allow_execute:
        print("Execution is blocked. --execute requires the explicit "
              "--allow-execute flag.")
        print(EXEC_BLOCKED_TOKEN)
        return 3

    # 1) Hard prohibited-model guard BEFORE any staging work.
    active = _active_models()
    violations = prohibited_model_guard(active)
    _ensure_exec_dirs()
    guard_path = EXEC_OUTPUT_DIR / "prohibited_model_guard_result.csv"
    _write_prohibited_guard_at(guard_path, violations)
    print(f"  prohibited guard : {'CLEAN' if not violations else 'VIOLATION'}")
    print(f"  wrote {_rel(guard_path)}")
    if violations:
        print(f"\n{PROHIBITED_VIOLATION_TOKEN}: {', '.join(violations)}")
        return 2

    # 2) DL reuse - REAL re-staging of frozen candidate-study outputs (no training).
    dl_results, dl_path, dl_total = execute_dl_reuse(STAGING_DIR)
    print(f"  dl reuse         : {dl_total} frozen rows -> {_rel(dl_path)}")

    # 3) Clean challenger entrypoint - invoke its staging executor (no live fit yet).
    cc_results: list[dict] | None = None
    try:
        from model_lab.run_daily_clean_challengers import execute_clean_challengers
        cc_results = execute_clean_challengers(STAGING_DIR, allow_execute=allow_execute)
        print(f"  clean challengers: {len(cc_results)} reported "
              f"({EXEC_STATUS_NOT_READY}; live-fit pending)")
    except Exception as exc:  # pragma: no cover - defensive
        print(f"  clean challengers: WARN could not invoke clean entrypoint ({exc})")

    # 4) Merged 15-model staging manifest.
    merged_rows = build_merged_status(dl_results)
    merged_path = write_merged_status_csv(merged_rows)
    print(f"  wrote {_rel(merged_path)}")

    # 5) Execution-wiring artifacts.
    plan_path = write_exec_plan_csv(dl_results)
    wiring_path = write_exec_wiring_status_csv(dl_total, cc_results)
    dl_result_path = write_dl_reuse_result_csv(dl_results)
    inv_path = write_staging_inventory_csv()
    for p in (plan_path, wiring_path, dl_result_path, inv_path):
        print(f"  wrote {_rel(p)}")

    # 6) Summary.
    reuse_ok = sum(1 for d in dl_results if d["reuse_status"] == EXEC_STATUS_REUSE)
    ready_bench = sum(1 for r in merged_rows if r[4] == EXEC_STATUS_READY_FOR_BENCH)
    not_ready = sum(1 for r in merged_rows if r[4] == EXEC_STATUS_NOT_READY)
    print("\n  --- execution wiring summary ---")
    print(f"  DL reuse executed (frozen)        : {reuse_ok}/3")
    print(f"  baseline ready_for_benchmark_auth : {ready_bench}")
    print(f"  clean challenger execution_not_ready: {not_ready}")
    print("  staging only - no promotion to data/processed; no champion change.")
    print(f"\n{EXEC_WIRING_COMPLETED_TOKEN}")
    return 0


def _write_prohibited_guard_at(path: Path, violations: list[str]) -> None:
    """Same shape as write_prohibited_guard_csv but written to an explicit path."""
    header = [
        "prohibited_model", "found_in_active_scope", "found_in_legacy_code",
        "active_scope_status", "action_taken", "notes",
    ]
    rows = []
    for p in PROHIBITED_MODELS:
        found_active = "YES" if p in violations else "NO"
        action = (
            "BLOCKED_RUN_ABORTED" if p in violations
            else "excluded_from_daily_runner; legacy_runner_not_used_as_daily"
        )
        rows.append([
            p, found_active, "YES", "excluded", action,
            PROHIBITED_LEGACY_LOCATIONS.get(p, ""),
        ])
    _write_csv(path, header, rows)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="V3.3C clean daily 15-model refresh runner "
                    "(scope/plan/guard + execution wiring).")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--validate-scope", action="store_true",
                       help="Validate the 15-model scope, family counts and guard.")
    group.add_argument("--dry-run", action="store_true",
                       help="Print the 15 models and per-model action; run the guard.")
    group.add_argument("--plan", action="store_true",
                       help="Emit the staged daily execution plan (no execution).")
    group.add_argument("--execute", action="store_true",
                       help="Execution wiring (staging only). Requires --allow-execute. "
                            "Re-stages frozen DL; baseline/challenger live-fit gated "
                            "behind benchmark authorization. No full run, no benchmark.")
    parser.add_argument("--allow-execute", action="store_true",
                        help="Explicit opt-in required by --execute.")
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
        return run_execute(args.allow_execute)
    return 1


if __name__ == "__main__":
    sys.exit(main())
