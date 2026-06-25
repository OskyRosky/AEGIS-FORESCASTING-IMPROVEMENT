"""Block 5.29D-Recovery inspector.

Read-only validation for the official model-set re-scope and recovery outputs.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_official_execution_recovery_inspector")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
RESCOPE_DIR = MODEL_LAB_DIR / "challenger_model_set_rescope"
RECOVERY_DIR = MODEL_LAB_DIR / "challenger_official_execution_recovery"
OFFICIAL_DIR = MODEL_LAB_DIR / "challenger_official_execution"
SHINY_DIR = PROJECT_ROOT / "shiny_app"

FINAL_MODELS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
}
EXPECTED_TOTAL_ROWS = 81720
EXPECTED_PER_MODEL_ROWS = 13620
HORIZON_DAYS = 30

RESCOPE_FILES = [
    "model_set_rescope_decision.csv",
    "current_official_challenger_set.csv",
    "onboarding_addendum.csv",
    "execution_planning_addendum.csv",
    "official_execution_prep_addendum.csv",
    "fast_neural_policy.md",
    "model_set_rescope_report.md",
]
RECOVERY_FILES = [
    "partial_output_inventory.csv",
    "fast_neural_sandbox_status.csv",
    "fast_neural_official_status.csv",
    "recovery_summary.csv",
    "recovery_report.md",
]
OFFICIAL_FILES = [
    "challenger_official_forecasts.csv",
    "challenger_official_execution_status.csv",
    "challenger_official_model_summary.csv",
    "challenger_official_contract_validation.csv",
    "challenger_official_execution_summary.csv",
    "challenger_official_execution_manifest_final.csv",
    "challenger_official_execution_report.md",
]
FORBIDDEN_OUTPUT_PATHS = [
    MODEL_LAB_DIR / "challenger_metrics",
    MODEL_LAB_DIR / "challenger_rankings",
    MODEL_LAB_DIR / "challenger_tournament",
    MODEL_LAB_DIR / "challenger_champion",
    MODEL_LAB_DIR / "tournament",
    MODEL_LAB_DIR / "champion",
]
PROTECTED_OUTPUT_PATHS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "baseline_ranking",
    PROJECT_ROOT / "outputs" / "metrics",
    SHINY_DIR,
]

_checks = 0
_failures: list[str] = []


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


def _path_has_files(path: Path) -> bool:
    return path.exists() and any(path.iterdir()) if path.is_dir() else path.exists()


def main() -> int:
    logger.info("=== Block 5.29D-Recovery Inspection ===")

    for filename in RESCOPE_FILES:
        _check((RESCOPE_DIR / filename).exists(), f"model-set rescope artifact exists: {filename}")
    for filename in RECOVERY_FILES:
        _check((RECOVERY_DIR / filename).exists(), f"recovery artifact exists: {filename}")
    for filename in OFFICIAL_FILES:
        _check((OFFICIAL_DIR / filename).exists(), f"final official artifact exists: {filename}")
    if _failures:
        return _finish()

    current_set = pd.read_csv(RESCOPE_DIR / "current_official_challenger_set.csv")
    onboarding = pd.read_csv(RESCOPE_DIR / "onboarding_addendum.csv")
    decision = pd.read_csv(RESCOPE_DIR / "model_set_rescope_decision.csv")
    forecasts = pd.read_csv(OFFICIAL_DIR / "challenger_official_forecasts.csv")
    status = pd.read_csv(OFFICIAL_DIR / "challenger_official_execution_status.csv")
    model_summary = pd.read_csv(OFFICIAL_DIR / "challenger_official_model_summary.csv")
    contract = pd.read_csv(OFFICIAL_DIR / "challenger_official_contract_validation.csv")
    summary = pd.read_csv(OFFICIAL_DIR / "challenger_official_execution_summary.csv")
    recovery_summary = pd.read_csv(RECOVERY_DIR / "recovery_summary.csv")
    sandbox = pd.read_csv(RECOVERY_DIR / "fast_neural_sandbox_status.csv")
    official_fast = pd.read_csv(RECOVERY_DIR / "fast_neural_official_status.csv")

    official_rows = current_set[_bool_series(current_set["official_candidate"])]
    deferred_rows = current_set[_bool_series(current_set["deferred"])]
    _check(len(official_rows) == 6, "current official challenger set has 6 official candidates")
    _check(len(deferred_rows) == 2, "current official challenger set has 2 deferred models")
    _check(set(official_rows["model_name"]) == FINAL_MODELS, "official candidates equal final six-model set")
    _check({"NBEATS", "NHITS"}.issubset(set(deferred_rows["model_name"])), "NBEATS and NHITS are deferred")

    fast_onboarding = onboarding[onboarding["model_name"] == "FastNeuralAR_MLP"]
    _check(len(fast_onboarding) == 1, "FastNeuralAR_MLP documented in onboarding addendum")
    _check(
        len(fast_onboarding) == 1
        and fast_onboarding.iloc[0]["onboarding_status"] == "added_lightweight_neural",
        "FastNeuralAR_MLP onboarding status is added_lightweight_neural",
    )
    decision_text = " ".join(str(value) for value in decision.to_numpy().flatten())
    _check(
        "deferred_runtime_impractical" in decision_text,
        "NBEATS decision records deferred_runtime_impractical",
    )
    _check(
        "deferred_dependency_blocked" in decision_text,
        "NHITS decision records deferred_dependency_blocked",
    )

    forecast_models = set(forecasts["model_name"].dropna())
    _check(forecast_models == FINAL_MODELS, "final forecast file includes only the six final models")
    _check("FastNeuralAR_MLP" in forecast_models, "FastNeuralAR_MLP appears in final forecasts")
    _check("NBEATS" not in forecast_models, "NBEATS does not appear in final forecasts")
    _check("NHITS" not in forecast_models, "NHITS does not appear in final forecasts")
    _check(len(forecasts) == EXPECTED_TOTAL_ROWS, "final row count is 81,720")

    per_model = forecasts.groupby("model_name").size().to_dict()
    bad_model_counts = {
        model: per_model.get(model, 0)
        for model in FINAL_MODELS
        if per_model.get(model, 0) != EXPECTED_PER_MODEL_ROWS
    }
    _check(not bad_model_counts, "per final model row count is 13,620")
    _check((forecasts["execution_mode"] == "official").all(), "execution_mode is official")

    values = pd.to_numeric(forecasts["forecast_value"], errors="coerce")
    _check(not values.isna().any(), "no NaN forecast_value")
    _check(np.isfinite(values.to_numpy()).all(), "no Inf forecast_value")
    horizon = pd.to_numeric(forecasts["horizon_day"], errors="coerce")
    _check(horizon.between(1, HORIZON_DAYS).all(), "horizon_day is 1..30")
    dupes = forecasts.duplicated(["run_id", "model_name", "entity_key", "window_id", "horizon_day"])
    _check(not dupes.any(), "no duplicate run_id/model/entity_key/window_id/horizon_day rows")
    grouped = forecasts.groupby(["model_name", "entity_key", "window_id"]).size()
    _check((grouped == HORIZON_DAYS).all(), "30 rows per model/entity-window")

    _check(not (contract["status"] == "fail").any(), "official contract validation has no failed checks")
    summary_row = summary.iloc[0]
    recovery_row = recovery_summary.iloc[0]
    for flag in ["metrics_created", "rankings_created", "tournament_created", "champion_selected"]:
        _check(not _bool_series(summary[flag]).any(), f"official summary {flag} = false")
        _check(not _bool_series(recovery_summary[flag]).any(), f"recovery summary {flag} = false")
    _check(int(summary_row["official_candidate_models"]) == 6, "official summary candidate models = 6")
    _check(int(summary_row["models_deferred"]) == 2, "official summary deferred models = 2")
    _check(int(summary_row["actual_total_forecast_rows"]) == EXPECTED_TOTAL_ROWS, "official summary actual rows = 81,720")
    _check(int(recovery_row["final_official_models"]) == 6, "recovery summary final official models = 6")
    _check(int(recovery_row["deferred_models"]) == 2, "recovery summary deferred models = 2")

    _check(sandbox.iloc[0]["sandbox_status"] == "sandbox_passed", "FastNeuralAR_MLP sandbox passed")
    _check(official_fast.iloc[0]["official_status"] == "official_passed", "FastNeuralAR_MLP official execution passed")
    _check(int(official_fast.iloc[0]["forecast_rows"]) == EXPECTED_PER_MODEL_ROWS, "FastNeuralAR_MLP official rows = 13,620")

    status_models = set(status["model_name"].dropna())
    _check(FINAL_MODELS.union({"NBEATS", "NHITS"}).issubset(status_models), "status includes final models plus deferred NBEATS/NHITS")
    _check(
        (model_summary.set_index("model_name").loc["NBEATS", "official_model_status"] == "deferred_runtime_impractical"),
        "model summary marks NBEATS deferred_runtime_impractical",
    )
    _check(
        (model_summary.set_index("model_name").loc["NHITS", "official_model_status"] == "deferred_dependency_blocked"),
        "model summary marks NHITS deferred_dependency_blocked",
    )

    for path in FORBIDDEN_OUTPUT_PATHS:
        _check(not _path_has_files(path), f"no forbidden metrics/ranking/tournament/champion output path created: {path.name}")
    for path in PROTECTED_OUTPUT_PATHS:
        _check(path.exists(), f"protected output path still present: {path}")

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for failure in _failures:
            logger.error("  - %s", failure)
        return 1
    logger.info("INSPECTION PASSED: Block 5.29D-Recovery artifacts satisfy the re-scoped official contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
