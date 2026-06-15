"""Block 5.30 - Tournament Engine Inspector."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_tournament_engine")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "tournament_engine"

REQUIRED_FILES = [
    "tournament_model_universe.csv",
    "tournament_entity_model_scores.csv",
    "tournament_model_scorecard.csv",
    "tournament_pairwise_evidence.csv",
    "tournament_model_evidence_summary.csv",
    "tournament_preliminary_standings.csv",
    "tournament_risk_register.csv",
    "tournament_validation.csv",
    "tournament_summary.csv",
    "tournament_engine_report.md",
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
FORBIDDEN_OUTPUT_PATHS = [
    MODEL_LAB_DIR / "challenger_champion",
    MODEL_LAB_DIR / "champion",
    MODEL_LAB_DIR / "final_champion",
]
PROTECTED_PATHS = [
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
    logger.info("=== Block 5.30 - Tournament Engine Inspection ===")
    for filename in REQUIRED_FILES:
        _check((OUTPUT_DIR / filename).exists(), f"required tournament file exists: {filename}")
    if _failures:
        return _finish()

    universe = pd.read_csv(OUTPUT_DIR / "tournament_model_universe.csv")
    entity = pd.read_csv(OUTPUT_DIR / "tournament_entity_model_scores.csv")
    scorecard = pd.read_csv(OUTPUT_DIR / "tournament_model_scorecard.csv")
    pairwise = pd.read_csv(OUTPUT_DIR / "tournament_pairwise_evidence.csv")
    standings = pd.read_csv(OUTPUT_DIR / "tournament_preliminary_standings.csv")
    risk = pd.read_csv(OUTPUT_DIR / "tournament_risk_register.csv")
    validation = pd.read_csv(OUTPUT_DIR / "tournament_validation.csv")
    summary = pd.read_csv(OUTPUT_DIR / "tournament_summary.csv")

    scored_universe = universe[_bool_series(universe["included_in_tournament"])]
    _check(set(scored_universe[scored_universe["model_origin"] == "baseline"]["model_name"]) == BASELINE_MODELS, "model universe includes 7 baseline models")
    _check(set(scored_universe[scored_universe["model_origin"] == "challenger"]["model_name"]) == CHALLENGER_MODELS, "model universe includes 6 challenger models")
    _check("NBEATS" not in set(scorecard["model_name"]), "NBEATS not scored")
    _check("NHITS" not in set(scorecard["model_name"]), "NHITS not scored")
    fast = scorecard[scorecard["model_name"] == "FastNeuralAR_MLP"]
    _check(len(fast) == 1 and _bool_series(fast["audit_risk_flag"]).iloc[0], "FastNeuralAR_MLP scored and flagged")
    _check(len(entity) == 507, "entity/model rows = 507")
    _check(len(scorecard) == 13, "model scorecard rows = 13")
    _check(len(pairwise) == 78, "pairwise evidence rows = 78")
    _check(len(standings) == 13 and "preliminary_position" in standings.columns, "preliminary standings exist")
    _check(not _bool_series(summary["champion_selected"]).any(), "champion_selected = false")
    _check(not _bool_series(summary["winner_selected"]).any(), "winner_selected = false")
    _check(not (validation["status"] == "fail").any(), "tournament_validation has no failed checks")
    _check(_bool_series(summary["ready_for_5_30A_sanity_review"]).all(), "ready_for_5_30A_sanity_review = true")
    _check("FastNeuralAR_MLP" in set(risk["model_name"]), "FastNeuralAR_MLP risk carried forward")
    _check("NBEATS" in set(risk["model_name"]), "NBEATS partial-output warning carried forward")
    _check("NHITS" in set(risk["model_name"]), "NHITS deferral carried forward")

    for path in FORBIDDEN_OUTPUT_PATHS:
        _check(not _path_has_files(path), f"no champion artifact path created: {path.name}")
    for path in PROTECTED_PATHS:
        _check(path.exists(), f"protected path still present: {path}")

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for failure in _failures:
            logger.error("  - %s", failure)
        return 1
    logger.info("INSPECTION PASSED: tournament engine satisfies Block 5.30 contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
