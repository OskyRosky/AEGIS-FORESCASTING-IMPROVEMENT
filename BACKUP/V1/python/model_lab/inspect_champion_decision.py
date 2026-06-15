"""Block 5.31 - Champion Decision Inspector."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_champion_decision")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "champion_decision"

REQUIRED_FILES = [
    "champion_candidate_evaluation.csv",
    "champion_decision_scorecard.csv",
    "champion_decision_evidence_summary.csv",
    "champion_decision.csv",
    "champion_decision_risk_review.csv",
    "champion_decision_validation.csv",
    "champion_decision_summary.csv",
    "champion_decision_report.md",
]
DECISIONS = {
    "CHAMPION_SELECTED",
    "CHAMPION_SELECTED_WITH_CONDITIONS",
    "NO_CHAMPION_SELECTED",
}
PROTECTED_PATHS = [
    MODEL_LAB_DIR / "tournament_engine",
    MODEL_LAB_DIR / "tournament_sanity_review",
    MODEL_LAB_DIR / "audit_4",
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "non_negative_policy",
    MODEL_LAB_DIR / "aggregation_hierarchy",
    MODEL_LAB_DIR / "statistical_significance",
    MODEL_LAB_DIR / "challenger_official_execution",
    MODEL_LAB_DIR / "challenger_metrics",
    MODEL_LAB_DIR / "challenger_aggregation_significance",
    PROJECT_ROOT / "shiny_app",
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


def _bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> int:
    logger.info("=== Block 5.31 - Champion Decision Inspection ===")
    for filename in REQUIRED_FILES:
        _check((OUTPUT_DIR / filename).exists(), f"required champion decision file exists: {filename}")
    if _failures:
        return _finish()

    candidates = pd.read_csv(OUTPUT_DIR / "champion_candidate_evaluation.csv")
    decision = pd.read_csv(OUTPUT_DIR / "champion_decision.csv")
    risk = pd.read_csv(OUTPUT_DIR / "champion_decision_risk_review.csv")
    validation = pd.read_csv(OUTPUT_DIR / "champion_decision_validation.csv")
    summary = pd.read_csv(OUTPUT_DIR / "champion_decision_summary.csv")

    _check(len(candidates) == 13, "champion_candidate_evaluation has 13 scored models")
    _check("NBEATS" not in set(candidates["model_name"]), "NBEATS absent from scored candidate evaluation")
    _check("NHITS" not in set(candidates["model_name"]), "NHITS absent from scored candidate evaluation")
    _check(len(decision) == 1, "champion_decision.csv has exactly 1 row")
    decision_value = decision.iloc[0]["decision"]
    _check(decision_value in DECISIONS, f"decision is valid: {decision_value}")
    selected = str(decision.iloc[0].get("selected_champion_model", "")).strip()
    if decision_value == "NO_CHAMPION_SELECTED":
        _check(not selected or selected.lower() == "nan", "no selected model when no champion selected")
        _check(bool(str(decision.iloc[0].get("no_champion_reason", "")).strip()), "no-champion reason documented")
    else:
        selected_rows = candidates[candidates["model_name"] == selected]
        _check(len(selected_rows) == 1, "selected champion is in evaluated candidates")
        if len(selected_rows) == 1:
            _check(
                selected_rows.iloc[0]["champion_candidate_status"]
                in {"eligible_candidate", "conditionally_eligible"},
                "selected model is eligible or conditionally eligible",
            )
    fast = candidates[candidates["model_name"] == "FastNeuralAR_MLP"]
    _check(
        len(fast) == 1 and fast.iloc[0]["champion_candidate_status"] == "ineligible_due_to_risk",
        "FastNeuralAR_MLP risk addressed",
    )
    _check("FastNeuralAR_MLP" in set(risk["model_name"]), "FastNeuralAR_MLP in risk review")
    _check("NBEATS" in set(risk["model_name"]), "NBEATS documented in risk review")
    _check("NHITS" in set(risk["model_name"]), "NHITS documented in risk review")
    _check(not (validation["status"] == "fail").any(), "champion_decision_validation has no failed checks")
    _check(_bool(summary.iloc[0]["ready_for_model_lab_closure_pack"]), "ready_for_model_lab_closure_pack = true")

    for path in PROTECTED_PATHS:
        _check(path.exists(), f"protected source path still present: {path}")

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for failure in _failures:
            logger.error("  - %s", failure)
        return 1
    logger.info("INSPECTION PASSED: champion decision satisfies Block 5.31 contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
