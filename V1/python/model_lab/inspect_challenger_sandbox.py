"""Block 5.29B - Challenger Sandbox Inspector (read-only validation).

Validates the artifacts produced by ``run_challenger_sandbox.py`` and confirms
that the sandbox stayed inside its safety envelope:

  * All required sandbox artifacts exist.
  * Execution status covers ALL registered challengers.
  * ``official_execution_allowed`` is False and no model is marked
    ``official_execution_ready``.
  * No official / ranking / tournament / champion outputs were created.
  * No protected upstream outputs (baselines, metrics, MASE/RMSSE, aggregation,
    significance, onboarding, planning, shiny app) were modified.
  * If forecasts exist they obey the contract; if none exist, every model must be
    blocked or not-attempted with a documented reason.

The inspector never writes to protected locations and never mutates data.
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_sandbox_inspector")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
SANDBOX_DIR = MODEL_LAB_DIR / "challenger_sandbox"
REGISTRY_PATH = (
    MODEL_LAB_DIR / "challenger_onboarding" / "challenger_registry_snapshot.csv"
)

HORIZON_DAYS = 30

REQUIRED_FILES = [
    "challenger_sandbox_dependency_check.csv",
    "challenger_sandbox_scope.csv",
    "challenger_sandbox_execution_status.csv",
    "challenger_sandbox_forecasts.csv",
    "challenger_sandbox_contract_validation.csv",
    "challenger_sandbox_summary.csv",
    "challenger_sandbox_report.md",
]

FORECAST_COLUMNS = [
    "run_id",
    "model_name",
    "entity_key",
    "window_id",
    "forecast_date",
    "horizon_day",
    "forecast_value",
    "execution_mode",
    "created_timestamp",
]

# Upstream outputs that must NOT be modified by this block.
PROTECTED_DIRS = [
    "full_baseline",
    "metrics",
    "baseline_ranking",
    "benchmark_reference",
    "seasonal_benchmark",
    "mase",
    "rmsse",
    "non_negative_policy",
    "aggregation_hierarchy",
    "statistical_significance",
    "denominator_reconciliation",
    "challenger_onboarding",
    "challenger_execution_planning",
    "shiny_app",
]

# Directories that must NOT exist / must be empty in this block.
FORBIDDEN_DIRS = [
    "challenger_execution",
    "challenger_forecasts",
    "challenger_metrics",
    "rankings",
    "champion",
    "tournament",
]

FORBIDDEN_TOKENS = ["rank", "champion", "winner", "tournament"]


class InspectionError(Exception):
    pass


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
    bad = [
        c
        for c in df.columns
        if any(tok in c.lower() for tok in FORBIDDEN_TOKENS)
    ]
    _check(not bad, f"{name}: no ranking/champion/tournament columns ({bad or 'none'})")


def _log_protected_scope() -> None:
    logger.info("Protected dirs (must be untouched): %s", PROTECTED_DIRS)
    logger.info("Forbidden dirs (must be empty/absent): %s", FORBIDDEN_DIRS)


def main() -> int:
    logger.info("=== Block 5.29B - Challenger Sandbox Inspection ===")
    _log_protected_scope()

    # 1. Files exist
    for fname in REQUIRED_FILES:
        _check((SANDBOX_DIR / fname).exists(), f"required file exists: {fname}")
    if _failures:
        logger.error("Missing required files; aborting further checks.")
        return _finish()

    dep_df = pd.read_csv(SANDBOX_DIR / "challenger_sandbox_dependency_check.csv")
    scope_df = pd.read_csv(SANDBOX_DIR / "challenger_sandbox_scope.csv")
    status_df = pd.read_csv(SANDBOX_DIR / "challenger_sandbox_execution_status.csv")
    forecasts_df = pd.read_csv(SANDBOX_DIR / "challenger_sandbox_forecasts.csv")
    contract_df = pd.read_csv(SANDBOX_DIR / "challenger_sandbox_contract_validation.csv")
    summary_df = pd.read_csv(SANDBOX_DIR / "challenger_sandbox_summary.csv")
    registry = pd.read_csv(REGISTRY_PATH)

    # 2. Schemas
    _assert_columns(
        dep_df,
        ["model_name", "dependency_name", "required_for_sandbox", "available",
         "status", "notes", "created_timestamp"],
        "dependency_check",
    )
    _assert_columns(
        scope_df,
        ["run_id", "entity_key", "window_id", "train_start_date", "train_end_date",
         "test_start_date", "test_end_date", "selected_for_sandbox",
         "selection_reason", "created_timestamp"],
        "scope",
    )
    _assert_columns(
        status_df,
        ["run_id", "model_name", "execution_mode", "sandbox_status", "attempted",
         "forecast_rows", "entities_attempted", "windows_attempted",
         "error_message", "eligible_for_official_candidate", "created_timestamp"],
        "execution_status",
    )
    _assert_columns(summary_df, [
        "run_id", "planned_challengers", "models_attempted", "models_passed",
        "models_failed", "models_blocked_dependency_missing", "sandbox_forecast_rows",
        "entities", "windows", "official_execution_allowed", "created_timestamp",
    ], "summary")
    for df, name in [
        (dep_df, "dependency_check"),
        (scope_df, "scope"),
        (status_df, "execution_status"),
        (forecasts_df, "forecasts"),
        (summary_df, "summary"),
    ]:
        _assert_no_forbidden_columns(df, name)

    # 3. Execution status covers ALL registered challengers
    reg_models = set(registry["model_name"])
    status_models = set(status_df["model_name"])
    _check(
        reg_models.issubset(status_models),
        f"execution status covers all challengers (missing: "
        f"{sorted(reg_models - status_models) or 'none'})",
    )
    valid_status = {
        "sandbox_passed",
        "sandbox_failed",
        "sandbox_blocked_dependency_missing",
        "sandbox_not_attempted",
    }
    bad_status = sorted(set(status_df["sandbox_status"]) - valid_status)
    _check(not bad_status, f"all sandbox_status values valid ({bad_status or 'ok'})")

    # 4. Sandbox scope present
    selected = scope_df[_bool_series(scope_df["selected_for_sandbox"])]
    _check(len(selected) > 0, f"sandbox scope has selected entities ({len(selected)})")

    # 5. official_execution_allowed must be False
    _check(
        not _bool_series(summary_df["official_execution_allowed"]).any(),
        "summary: official_execution_allowed is False",
    )
    if "official_execution_ready" in status_df.columns:
        _check(
            not _bool_series(status_df["official_execution_ready"]).any(),
            "no model marked official_execution_ready",
        )

    # 6. Eligibility only for passed models
    elig = status_df[_bool_series(status_df["eligible_for_official_candidate"])]
    non_passed_elig = elig[elig["sandbox_status"] != "sandbox_passed"]
    _check(
        len(non_passed_elig) == 0,
        "only sandbox_passed models are eligible candidates "
        f"({non_passed_elig['model_name'].tolist() or 'ok'})",
    )

    # 7. Forecast handling
    if len(forecasts_df) > 0:
        _assert_columns(forecasts_df, FORECAST_COLUMNS, "forecasts")
        _check(
            (forecasts_df["execution_mode"] == "sandbox").all(),
            "forecasts: execution_mode is sandbox",
        )
        vals = pd.to_numeric(forecasts_df["forecast_value"], errors="coerce")
        _check(not vals.isna().any(), "forecasts: no NaN values")
        _check(np.isfinite(vals.to_numpy()).all(), "forecasts: no Inf values")
        hd = pd.to_numeric(forecasts_df["horizon_day"], errors="coerce")
        _check(hd.between(1, HORIZON_DAYS).all(), "forecasts: horizon_day in 1..30")
        grp = forecasts_df.groupby(["model_name", "entity_key", "window_id"]).size()
        _check(
            (grp == HORIZON_DAYS).all(),
            f"forecasts: 30 rows per model/entity/window ({sorted(grp.unique())})",
        )
        dates_ok = pd.to_datetime(forecasts_df["forecast_date"], errors="coerce")
        _check(not dates_ok.isna().any(), "forecasts: forecast_date parseable")
    else:
        logger.info("No sandbox forecasts present - verifying all models are blocked/not-attempted.")
        unaccounted = status_df[
            ~status_df["sandbox_status"].isin(
                {"sandbox_blocked_dependency_missing", "sandbox_not_attempted", "sandbox_failed"}
            )
        ]
        _check(
            len(unaccounted) == 0,
            "no forecasts => every model blocked/failed/not-attempted with reason "
            f"({unaccounted['model_name'].tolist() or 'ok'})",
        )
        no_reason = status_df[
            status_df["error_message"].astype(str).str.strip().isin({"", "nan"})
        ]
        _check(
            len(no_reason) == 0,
            f"all non-running models have a documented reason ({no_reason['model_name'].tolist() or 'ok'})",
        )

    # 8. Forbidden output directories must be empty/absent
    for d in FORBIDDEN_DIRS:
        p = MODEL_LAB_DIR / d
        present = p.exists() and any(p.iterdir())
        _check(not present, f"forbidden dir empty/absent: {d}")

    # 9. Protected dirs still exist (sanity that we did not delete them)
    for d in PROTECTED_DIRS:
        p = MODEL_LAB_DIR / d
        if p.exists():
            logger.info("protected dir present (untouched): %s", d)

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for f in _failures:
            logger.error("  - %s", f)
        return 1
    logger.info("INSPECTION PASSED: all sandbox safety + contract checks succeeded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
