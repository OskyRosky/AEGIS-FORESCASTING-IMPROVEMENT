"""Block 5.29F - Challenger Aggregation & Significance Inspector."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_challenger_aggregation_significance")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_aggregation_significance"

FINAL_MODELS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
}
EXPECTED_CANONICAL_ROWS = 2724
EXPECTED_MODEL_ROWS = 6
EXPECTED_PAIRWISE_ROWS = 15

REQUIRED_FILES = [
    "challenger_canonical_entity_window_scores.csv",
    "challenger_aggregation_by_entity_model.csv",
    "challenger_aggregation_by_model.csv",
    "challenger_pairwise_significance.csv",
    "challenger_model_significance_summary.csv",
    "challenger_family_summary.csv",
    "challenger_outlier_risk_review.csv",
    "challenger_tournament_input_manifest.csv",
    "challenger_aggregation_significance_validation.csv",
    "challenger_aggregation_significance_summary.csv",
    "challenger_aggregation_significance_report.md",
]
FORBIDDEN_OUTPUT_PATHS = [
    MODEL_LAB_DIR / "challenger_rankings",
    MODEL_LAB_DIR / "challenger_tournament",
    MODEL_LAB_DIR / "challenger_champion",
    MODEL_LAB_DIR / "rankings",
    MODEL_LAB_DIR / "tournament",
    MODEL_LAB_DIR / "champion",
]
PROTECTED_PATHS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "non_negative_policy",
    MODEL_LAB_DIR / "aggregation_hierarchy",
    MODEL_LAB_DIR / "statistical_significance",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "challenger_official_execution",
    MODEL_LAB_DIR / "challenger_metrics",
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


def _ranking_like_columns(*frames: pd.DataFrame) -> list[str]:
    cols = []
    for frame in frames:
        cols.extend(
            [
                c
                for c in frame.columns
                if "rank" in c.lower() or "winner" in c.lower() or "champion" in c.lower()
            ]
        )
    return cols


def main() -> int:
    logger.info("=== Block 5.29F - Challenger Aggregation & Significance Inspection ===")
    for filename in REQUIRED_FILES:
        _check((OUTPUT_DIR / filename).exists(), f"required output exists: {filename}")
    if _failures:
        return _finish()

    canonical = pd.read_csv(OUTPUT_DIR / "challenger_canonical_entity_window_scores.csv")
    entity_model = pd.read_csv(OUTPUT_DIR / "challenger_aggregation_by_entity_model.csv")
    model_agg = pd.read_csv(OUTPUT_DIR / "challenger_aggregation_by_model.csv")
    pairwise = pd.read_csv(OUTPUT_DIR / "challenger_pairwise_significance.csv")
    significance_summary = pd.read_csv(OUTPUT_DIR / "challenger_model_significance_summary.csv")
    family = pd.read_csv(OUTPUT_DIR / "challenger_family_summary.csv")
    risks = pd.read_csv(OUTPUT_DIR / "challenger_outlier_risk_review.csv")
    tournament_manifest = pd.read_csv(OUTPUT_DIR / "challenger_tournament_input_manifest.csv")
    validation = pd.read_csv(OUTPUT_DIR / "challenger_aggregation_significance_validation.csv")
    summary = pd.read_csv(OUTPUT_DIR / "challenger_aggregation_significance_summary.csv")

    models = set(canonical["model_name"])
    _check(len(canonical) == EXPECTED_CANONICAL_ROWS, "canonical rows = 2,724")
    _check(models == FINAL_MODELS, "exactly 6 final challenger models in canonical scores")
    _check("NBEATS" not in models, "NBEATS absent")
    _check("NHITS" not in models, "NHITS absent")
    _check("FastNeuralAR_MLP" in models, "FastNeuralAR_MLP present")
    _check(len(model_agg) == EXPECTED_MODEL_ROWS, "model aggregation has 6 rows")
    _check(len(pairwise) == EXPECTED_PAIRWISE_ROWS, "pairwise significance has 15 rows")
    _check(len(significance_summary) == EXPECTED_MODEL_ROWS, "model significance summary has 6 rows")
    _check(set(tournament_manifest["model_name"]) == FINAL_MODELS, "tournament input manifest has final challengers only")

    ranking_columns = _ranking_like_columns(
        canonical,
        entity_model,
        model_agg,
        pairwise,
        significance_summary,
        family,
        risks,
        tournament_manifest,
    )
    _check(not ranking_columns, f"no ranking/winner/champion columns ({ranking_columns or 'none'})")
    _check(not (validation["status"] == "fail").any(), "validation file has no failed checks")

    row = summary.iloc[0]
    _check(int(row["challenger_models"]) == 6, "summary challenger_models = 6")
    _check(int(row["canonical_rows"]) == EXPECTED_CANONICAL_ROWS, "summary canonical_rows = 2,724")
    _check(int(row["model_aggregation_rows"]) == EXPECTED_MODEL_ROWS, "summary model_aggregation_rows = 6")
    _check(int(row["pairwise_comparisons"]) == EXPECTED_PAIRWISE_ROWS, "summary pairwise_comparisons = 15")
    _check(_bool_series(summary["aggregation_created"]).all(), "aggregation_created = true")
    _check(_bool_series(summary["significance_created"]).all(), "significance_created = true")
    _check(not _bool_series(summary["rankings_created"]).any(), "rankings_created = false")
    _check(not _bool_series(summary["tournament_created"]).any(), "tournament_created = false")
    _check(not _bool_series(summary["champion_selected"]).any(), "champion_selected = false")
    _check(
        len(entity_model.groupby("model_name")["entity_key"].nunique().unique()) == 1,
        "aggregation preserves equal entity weighting",
    )
    _check(
        pairwise["paired_entity_count"].min() == pairwise["paired_entity_count"].max(),
        "significance uses entity-level paired comparisons",
    )
    _check(
        "FastNeuralAR_MLP" in set(risks["model_name"]),
        "FastNeuralAR_MLP included in outlier risk review",
    )

    for path in FORBIDDEN_OUTPUT_PATHS:
        _check(not _path_has_files(path), f"no ranking/tournament/champion output path created: {path.name}")
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
    logger.info("INSPECTION PASSED: challenger aggregation/significance satisfies Block 5.29F contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
