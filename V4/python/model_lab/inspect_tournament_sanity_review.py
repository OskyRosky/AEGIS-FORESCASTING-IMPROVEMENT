"""Block 5.30A - Tournament Sanity Review Inspector."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_tournament_sanity_review")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "tournament_sanity_review"

REQUIRED_FILES = [
    "tournament_sanity_checklist.csv",
    "tournament_preliminary_standings_review.csv",
    "tournament_pairwise_sanity_review.csv",
    "tournament_risk_sanity_review.csv",
    "tournament_candidate_readiness_for_5_31.csv",
    "tournament_sanity_findings.csv",
    "tournament_sanity_summary.csv",
    "tournament_sanity_review_report.md",
]
BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}
CHALLENGER_MODELS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
}
FORBIDDEN_CHAMPION_PATHS = [
    MODEL_LAB_DIR / "champion",
    MODEL_LAB_DIR / "challenger_champion",
    MODEL_LAB_DIR / "final_champion",
]
PROTECTED_PATHS = [
    MODEL_LAB_DIR / "tournament_engine",
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "non_negative_policy",
    MODEL_LAB_DIR / "aggregation_hierarchy",
    MODEL_LAB_DIR / "statistical_significance",
    MODEL_LAB_DIR / "challenger_official_execution",
    MODEL_LAB_DIR / "challenger_metrics",
    MODEL_LAB_DIR / "challenger_aggregation_significance",
    MODEL_LAB_DIR / "audit_4",
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


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def _path_has_files(path: Path) -> bool:
    return path.exists() and any(path.iterdir()) if path.is_dir() else path.exists()


def main() -> int:
    logger.info("=== Block 5.30A - Tournament Sanity Review Inspection ===")
    for filename in REQUIRED_FILES:
        _check((OUTPUT_DIR / filename).exists(), f"required sanity review file exists: {filename}")
    if _failures:
        return _finish()

    checklist = pd.read_csv(OUTPUT_DIR / "tournament_sanity_checklist.csv")
    standings = pd.read_csv(OUTPUT_DIR / "tournament_preliminary_standings_review.csv")
    pairwise = pd.read_csv(OUTPUT_DIR / "tournament_pairwise_sanity_review.csv")
    risk = pd.read_csv(OUTPUT_DIR / "tournament_risk_sanity_review.csv")
    candidates = pd.read_csv(OUTPUT_DIR / "tournament_candidate_readiness_for_5_31.csv")
    findings = pd.read_csv(OUTPUT_DIR / "tournament_sanity_findings.csv")
    summary = pd.read_csv(OUTPUT_DIR / "tournament_sanity_summary.csv")

    _check(len(standings) == 13, "13 scored models reviewed in preliminary standings")
    _check(set(standings[standings["model_origin"] == "baseline"]["model_name"]) == BASELINE_MODELS, "7 baseline models reviewed")
    _check(set(standings[standings["model_origin"] == "challenger"]["model_name"]) == CHALLENGER_MODELS, "6 challenger models reviewed")
    _check(len(pairwise) == 78, "pairwise comparisons reviewed = 78")
    _check(len(risk) > 0, "risk flags reviewed")
    fast = candidates[candidates["model_name"] == "FastNeuralAR_MLP"]
    _check(
        len(fast) == 1 and _bool_series(fast["requires_manual_review"]).iloc[0],
        "FastNeuralAR_MLP flagged for manual review",
    )
    _check("NBEATS" not in set(standings["model_name"]), "NBEATS not scored")
    _check("NHITS" not in set(standings["model_name"]), "NHITS not scored")
    _check("NBEATS" in set(risk["model_name"]), "NBEATS exclusion reviewed in risk register")
    _check("NHITS" in set(risk["model_name"]), "NHITS deferral reviewed in risk register")
    _check(not _bool_series(summary["champion_selected"]).any(), "champion_selected = false")
    _check(not _bool_series(summary["winner_selected"]).any(), "winner_selected = false")
    _check(_bool_series(summary["ready_for_5_31_champion_decision"]).all(), "ready_for_5_31_champion_decision = true")
    _check(int(summary.iloc[0]["blockers"]) == 0, "no blockers")
    _check(int(summary.iloc[0]["major_findings"]) == 0, "no major findings")
    _check(not (checklist["status"] == "FAIL").any(), "sanity checklist has no FAIL rows")
    _check(not (pairwise["sanity_review_status"] == "FAIL").any(), "pairwise sanity review has no FAIL rows")

    for path in FORBIDDEN_CHAMPION_PATHS:
        _check(not _path_has_files(path), f"no champion artifact created: {path.name}")
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
    logger.info("INSPECTION PASSED: tournament sanity review satisfies Block 5.30A contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
