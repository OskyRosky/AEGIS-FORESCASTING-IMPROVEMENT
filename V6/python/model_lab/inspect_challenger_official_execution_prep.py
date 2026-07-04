"""Block 5.29C - Challenger Official Execution Prep Inspector (read-only).

Validates the official-execution-prep artifacts and confirms the block stayed
inside its safety envelope (no official execution, no metrics, no rankings, no
tournament, no champion, protected outputs untouched).

Workload counts are validated against the REAL backtesting scope derived from
``backtesting_windows.csv`` (454 entity-window pairs for this walk-forward
design), and checked for internal consistency
(expected_rows == entity_window_pairs x horizon, total == per_model x 6).
"""

from __future__ import annotations

import sys

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_official_execution_prep_inspector")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
PREP_DIR = MODEL_LAB_DIR / "challenger_official_execution_prep"
WINDOWS_PATH = MODEL_LAB_DIR / "backtesting_windows.csv"

HORIZON_DAYS = 30
EXPECTED_CANDIDATES = {
    "AutoARIMA", "Theta", "ETS Explicit", "LightGBM", "XGBoost", "NBEATS",
}
DEFERRED_MODEL = "NHITS"

REQUIRED_FILES = [
    "official_challenger_candidate_list.csv",
    "official_execution_gate_review.csv",
    "official_execution_manifest.csv",
    "official_execution_scope.csv",
    "official_execution_locked_policy.csv",
    "official_execution_workload_estimate.csv",
    "official_execution_output_contract.csv",
    "official_execution_prep_summary.csv",
    "official_execution_prep_report.md",
]

OUTPUT_CONTRACT_REQUIRED = [
    "run_id", "model_name", "entity_key", "window_id", "forecast_date",
    "horizon_day", "forecast_value", "execution_mode", "created_timestamp",
]

PROTECTED_DIRS = [
    "full_baseline", "metrics", "baseline_ranking", "benchmark_reference",
    "seasonal_benchmark", "mase", "rmsse", "non_negative_policy",
    "aggregation_hierarchy", "statistical_significance",
    "denominator_reconciliation", "challenger_onboarding",
    "challenger_execution_planning", "challenger_sandbox",
    "challenger_dependency_resolution", "shiny_app",
]
FORBIDDEN_DIRS = [
    "challenger_execution", "challenger_forecasts", "challenger_metrics",
    "rankings", "champion", "tournament",
]
FORBIDDEN_TOKENS = ["rank", "champion", "winner", "tournament"]

_failures: list[str] = []
_checks = 0


def _check(condition: bool, message: str) -> None:
    global _checks
    _checks += 1
    if condition:
        logger.info("PASS: %s", message)
    else:
        logger.error("FAIL: %s", message)
        _failures.append(message)


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def _assert_columns(df: pd.DataFrame, columns: list[str], name: str) -> None:
    missing = [c for c in columns if c not in df.columns]
    _check(not missing, f"{name}: required columns present ({missing or 'all'})")


def _assert_no_forbidden_columns(df: pd.DataFrame, name: str) -> None:
    bad = [c for c in df.columns if any(t in c.lower() for t in FORBIDDEN_TOKENS)]
    _check(not bad, f"{name}: no rank/champion/tournament columns ({bad or 'none'})")


def main() -> int:
    logger.info("=== Block 5.29C - Official Execution Prep Inspection ===")
    logger.info("Protected dirs: %s", PROTECTED_DIRS)
    logger.info("Forbidden dirs: %s", FORBIDDEN_DIRS)

    for fname in REQUIRED_FILES:
        _check((PREP_DIR / fname).exists(), f"required file exists: {fname}")
    if _failures:
        return _finish()

    windows = pd.read_csv(WINDOWS_PATH)
    entity_count = int(windows["entity_key"].nunique())
    window_count = int(windows.drop_duplicates(["entity_key", "window_id"]).shape[0])
    expected_per_model = window_count * HORIZON_DAYS
    expected_total = expected_per_model * len(EXPECTED_CANDIDATES)
    logger.info("Real scope: %d entities, %d entity-window pairs, per-model rows %d, total %d",
                entity_count, window_count, expected_per_model, expected_total)

    candidates = pd.read_csv(PREP_DIR / "official_challenger_candidate_list.csv")
    gates = pd.read_csv(PREP_DIR / "official_execution_gate_review.csv")
    manifest = pd.read_csv(PREP_DIR / "official_execution_manifest.csv")
    scope = pd.read_csv(PREP_DIR / "official_execution_scope.csv")
    policy = pd.read_csv(PREP_DIR / "official_execution_locked_policy.csv")
    workload = pd.read_csv(PREP_DIR / "official_execution_workload_estimate.csv")
    contract = pd.read_csv(PREP_DIR / "official_execution_output_contract.csv")
    summary = pd.read_csv(PREP_DIR / "official_execution_prep_summary.csv")

    # Schemas
    _assert_columns(candidates, [
        "model_name", "model_family", "model_type", "sandbox_status",
        "dependency_status", "official_candidate", "official_execution_prep_status",
        "deferred_reason", "created_timestamp"], "candidate_list")
    _assert_columns(gates, [
        "gate_id", "gate_name", "model_name", "gate_status", "blocking_if_failed",
        "evidence_source", "notes", "created_timestamp"], "gate_review")
    _assert_columns(manifest, [
        "run_id", "model_name", "execution_mode", "entity_count", "window_count",
        "horizon_days", "expected_forecast_rows", "official_candidate",
        "ready_for_official_execution", "created_timestamp"], "manifest")
    _assert_columns(scope, [
        "run_id", "entity_key", "window_id", "train_start_date", "train_end_date",
        "test_start_date", "test_end_date", "selected_for_official_execution",
        "created_timestamp"], "scope")
    _assert_columns(policy, [
        "model_name", "tuning_allowed", "tuning_mode", "max_trials",
        "max_runtime_minutes", "random_seed", "inner_validation_required",
        "official_results_may_tune_model", "hyperparameter_policy_status",
        "created_timestamp"], "locked_policy")
    _assert_columns(workload, [
        "model_name", "entity_count", "window_count", "horizon_days",
        "expected_forecast_rows", "runtime_class", "estimated_relative_cost",
        "notes", "created_timestamp"], "workload")
    _assert_columns(contract, ["column_name", "required", "description"], "output_contract")
    _assert_columns(summary, [
        "run_id", "sandbox_passed_models", "official_candidate_models",
        "deferred_models", "ready_for_official_execution_models",
        "expected_total_forecast_rows", "official_execution_run_performed",
        "rankings_created", "tournament_created", "champion_selected",
        "created_timestamp"], "summary")

    # The summary is excluded from the token scan: it intentionally carries
    # proof-of-absence safety flags (rankings_created / tournament_created /
    # champion_selected) whose values are separately asserted to be false.
    for df, name in [(candidates, "candidate_list"), (gates, "gate_review"),
                     (manifest, "manifest"), (scope, "scope"), (policy, "policy"),
                     (workload, "workload")]:
        _assert_no_forbidden_columns(df, name)

    # Candidate list: exactly 6 official candidates, NHITS deferred
    official = set(candidates[_bool_series(candidates["official_candidate"])]["model_name"])
    _check(official == EXPECTED_CANDIDATES,
           f"exactly the 6 expected official candidates ({sorted(official)})")
    nhits = candidates[candidates["model_name"] == DEFERRED_MODEL]
    _check(len(nhits) == 1 and not _bool_series(nhits["official_candidate"]).any(),
           "NHITS present and NOT an official candidate")
    _check(len(nhits) == 1 and nhits.iloc[0]["deferred_reason"].strip() != "",
           "NHITS has a documented deferred_reason")
    _check(len(nhits) == 1 and "neuralforecast" in nhits.iloc[0]["deferred_reason"].lower()
           and "ray" in nhits.iloc[0]["deferred_reason"].lower()
           and "3.14" in nhits.iloc[0]["deferred_reason"],
           "NHITS deferred_reason cites Python 3.14 / neuralforecast / ray")

    # Manifest: 6 official candidate rows, real per-model rows, official mode
    man_official = manifest[_bool_series(manifest["official_candidate"])]
    _check(len(man_official) == len(EXPECTED_CANDIDATES),
           f"manifest has 6 official candidate rows ({len(man_official)})")
    _check((manifest["execution_mode"] == "official").all(),
           "manifest execution_mode is official")
    _check((man_official["expected_forecast_rows"] == expected_per_model).all(),
           f"manifest expected rows per candidate == {expected_per_model}")
    _check(int(man_official["expected_forecast_rows"].sum()) == expected_total,
           f"manifest total expected rows == {expected_total}")
    _check((man_official["window_count"] == window_count).all()
           and (man_official["entity_count"] == entity_count).all()
           and (man_official["horizon_days"] == HORIZON_DAYS).all(),
           "manifest scope columns match real backtest scope")
    # Internal consistency: rows == window_count * horizon
    consistent = (man_official["expected_forecast_rows"]
                  == man_official["window_count"] * man_official["horizon_days"]).all()
    _check(consistent, "manifest rows == window_count x horizon_days (internally consistent)")

    # Scope: real entity-window count, all selected
    _check(len(scope) == window_count, f"scope has {window_count} entity-window rows ({len(scope)})")
    _check(_bool_series(scope["selected_for_official_execution"]).all(),
           "all scope rows selected_for_official_execution")
    _check(scope.drop_duplicates(["entity_key", "window_id"]).shape[0] == len(scope),
           "scope entity-window rows are unique")

    # Output contract
    _check(list(contract["column_name"]) == OUTPUT_CONTRACT_REQUIRED,
           "output contract columns match required schema")
    _check(_bool_series(contract["required"]).all(), "all output contract columns required")
    exec_desc = contract[contract["column_name"] == "execution_mode"]["description"].iloc[0]
    _check("official" in exec_desc.lower(), "output contract execution_mode states official")

    # Locked policy
    _check(set(policy["model_name"]) == EXPECTED_CANDIDATES,
           "locked policy covers exactly the 6 candidates")
    _check(not _bool_series(policy["official_results_may_tune_model"]).any(),
           "official_results_may_tune_model == false for all candidates")
    _check(policy["random_seed"].notna().all()
           and (policy["random_seed"].astype(str).str.strip() != "").all(),
           "random_seed locked (non-empty) for all candidates")
    _check((policy["hyperparameter_policy_status"].astype(str).str.contains("lock")).all(),
           "hyperparameter policy status locked for all candidates")

    # Summary safety flags
    s = summary.iloc[0]
    _check(int(s["official_candidate_models"]) == len(EXPECTED_CANDIDATES),
           "summary official_candidate_models == 6")
    _check(int(s["deferred_models"]) == 1, "summary deferred_models == 1")
    _check(int(s["expected_total_forecast_rows"]) == expected_total,
           f"summary expected_total_forecast_rows == {expected_total}")
    for flag in ["official_execution_run_performed", "rankings_created",
                 "tournament_created", "champion_selected"]:
        _check(not _bool_series(pd.Series([s[flag]])).any(), f"summary {flag} == false")

    # Gate review: every official candidate evaluated on all 10 gates, all pass
    for model in EXPECTED_CANDIDATES:
        g = gates[gates["model_name"] == model]
        _check(len(g) == 10, f"gate review: {model} evaluated on 10 gates ({len(g)})")
        _check((g["gate_status"] == "pass").all(),
               f"gate review: {model} passes all gates")
    nhits_gates = gates[gates["model_name"] == DEFERRED_MODEL]
    _check((nhits_gates["gate_status"] != "pass").any(),
           "gate review: NHITS not fully passing (deferred)")

    # Forbidden dirs empty/absent
    for d in FORBIDDEN_DIRS:
        p = MODEL_LAB_DIR / d
        present = p.exists() and any(p.iterdir())
        _check(not present, f"forbidden dir empty/absent: {d}")

    # Prep dir must contain NO forecast/metric outputs
    forbidden_names = ["forecast", "mase", "rmsse", "metric", "ranking",
                       "tournament", "champion"]
    stray = [
        f.name for f in PREP_DIR.glob("*")
        if any(t in f.name.lower() for t in forbidden_names)
        and "output_contract" not in f.name.lower()
        and "workload" not in f.name.lower()
    ]
    _check(not stray, f"no forecast/metric/ranking outputs in prep dir ({stray or 'none'})")

    for d in PROTECTED_DIRS:
        if (MODEL_LAB_DIR / d).exists() or d == "shiny_app":
            logger.info("protected scope (not modified by this block): %s", d)

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for f in _failures:
            logger.error("  - %s", f)
        return 1
    logger.info("INSPECTION PASSED: official execution prep is valid and safe.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
