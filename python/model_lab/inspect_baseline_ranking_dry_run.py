"""Inspect Stage 5.14 baseline ranking dry-run outputs."""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_baseline_ranking_dry_run")

DRY_RUN_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "ranking_dry_run"
SCORES = DRY_RUN_DIR / "baseline_ranking_scores.csv"
BY_ENTITY = DRY_RUN_DIR / "baseline_ranking_by_entity.csv"
BY_MODEL = DRY_RUN_DIR / "baseline_ranking_by_model.csv"
DISTRIBUTION = DRY_RUN_DIR / "baseline_ranking_distribution.csv"
SUMMARY = DRY_RUN_DIR / "baseline_ranking_summary.csv"
FLAGS = DRY_RUN_DIR / "baseline_ranking_flags.csv"

BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}
SCORE_COLUMNS = [
    "normalized_wmape",
    "normalized_mape",
    "normalized_rmse",
    "normalized_smape",
    "normalized_abs_bias",
    "diagnostic_composite_score",
]


def _require_file(path) -> None:
    """Validate that a required dry-run output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required ranking dry-run output missing: {path}")


def inspect_baseline_ranking_dry_run() -> dict[str, pd.DataFrame]:
    """Inspect ranking dry-run outputs and validate score integrity."""

    for path in (SCORES, BY_ENTITY, BY_MODEL, DISTRIBUTION, SUMMARY, FLAGS):
        _require_file(path)

    scores = pd.read_csv(SCORES)
    by_entity = pd.read_csv(BY_ENTITY)
    by_model = pd.read_csv(BY_MODEL)
    distribution = pd.read_csv(DISTRIBUTION)
    summary = pd.read_csv(SUMMARY)
    flags = pd.read_csv(FLAGS)
    row = summary.iloc[0]

    if int(row["metric_rows_processed"]) != 3178:
        raise ValueError("Dry run did not process all 3178 metric rows.")
    if len(scores) != 3178:
        raise ValueError(f"Expected 3178 score rows, found {len(scores)}.")
    if set(scores["model_name"]) != BASELINE_MODELS:
        raise ValueError("Dry run score output does not contain all baseline models.")
    if scores.duplicated(["entity_key", "window_id", "model_name"]).any():
        raise ValueError("Duplicate ranking dry-run score rows detected.")
    for column in SCORE_COLUMNS:
        values = pd.to_numeric(scores[column], errors="coerce")
        if values.isna().any():
            raise ValueError(f"{column} contains NaN values.")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{column} contains non-finite values.")
    if abs(float(row["weights_sum"]) - 1.0) > 1e-9:
        raise ValueError("Ranking dry-run weights do not sum to 1.0.")
    if bool(row["winner_selected"]):
        raise ValueError("Dry run must not select a winner.")
    if bool(row["tournament_created"]):
        raise ValueError("Dry run must not create tournament outputs.")
    if len(by_model) != 7:
        raise ValueError("Expected 7 model-level dry-run rows.")
    if len(by_entity) != 273:
        raise ValueError(f"Expected 273 entity/model rows, found {len(by_entity)}.")

    logger.info("Score rows: %s", len(scores))
    logger.info("Entity/model rows: %s", len(by_entity))
    logger.info("Model rows: %s", len(by_model))
    logger.info("Distribution rows: %s", len(distribution))
    logger.info("Flags: %s", len(flags))
    logger.info("Models represented: %s", sorted(scores["model_name"].unique()))
    logger.info("Score min/max: %.6f / %.6f", scores["diagnostic_composite_score"].min(), scores["diagnostic_composite_score"].max())
    logger.info("Stage 5.14 baseline ranking dry-run inspection passed")
    return {
        "scores": scores,
        "by_entity": by_entity,
        "by_model": by_model,
        "distribution": distribution,
        "summary": summary,
        "flags": flags,
    }


if __name__ == "__main__":
    inspect_baseline_ranking_dry_run()
