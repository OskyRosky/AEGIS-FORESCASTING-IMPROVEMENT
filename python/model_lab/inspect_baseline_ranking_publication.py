"""Inspect Stage 5.15 baseline ranking publication artifacts."""

from __future__ import annotations

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_baseline_ranking_publication")

BASELINE_RANKING_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "baseline_ranking"
PUBLICATION = BASELINE_RANKING_DIR / "baseline_ranking_publication.csv"
ENTITY_SCORES = BASELINE_RANKING_DIR / "baseline_ranking_entity_scores.csv"
METADATA = BASELINE_RANKING_DIR / "baseline_ranking_metadata.csv"
README = BASELINE_RANKING_DIR / "baseline_ranking_readme.csv"
TOURNAMENT_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "tournament"

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
    "global_score",
    "wmape_score",
    "mape_score",
    "rmse_score",
    "smape_score",
    "abs_bias_score",
]


def _require_file(path) -> None:
    """Validate that a required publication artifact exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required baseline ranking artifact missing: {path}")


def inspect_baseline_ranking_publication() -> dict[str, pd.DataFrame]:
    """Validate baseline ranking publication artifacts."""

    for path in (PUBLICATION, ENTITY_SCORES, METADATA, README):
        _require_file(path)

    publication = pd.read_csv(PUBLICATION)
    entity_scores = pd.read_csv(ENTITY_SCORES)
    metadata = pd.read_csv(METADATA)
    readme = pd.read_csv(README)

    if set(publication["model_name"]) != BASELINE_MODELS:
        raise ValueError("Publication does not contain exactly the 7 baseline models.")
    if publication["model_name"].duplicated().any():
        raise ValueError("Duplicate model rows found in publication.")
    challenger_models = set(publication["model_name"]) - BASELINE_MODELS
    if challenger_models:
        raise ValueError(f"Challenger models found: {sorted(challenger_models)}")
    for column in SCORE_COLUMNS:
        values = pd.to_numeric(publication[column], errors="coerce")
        if values.isna().any():
            raise ValueError(f"{column} contains NaN values.")
        if not np.isfinite(values.to_numpy(dtype=float)).all():
            raise ValueError(f"{column} contains non-finite values.")
    if metadata.empty or readme.empty:
        raise ValueError("Metadata/readme publication artifacts must not be empty.")
    if TOURNAMENT_DIR.exists() and any(TOURNAMENT_DIR.iterdir()):
        raise ValueError("Tournament outputs exist; publication must not create them.")

    logger.info("Publication model rows: %s", len(publication))
    logger.info("Entity score rows: %s", len(entity_scores))
    logger.info("Metadata rows: %s", len(metadata))
    logger.info("Readme rows: %s", len(readme))
    logger.info("Baseline models: %s", sorted(publication["model_name"].unique()))
    logger.info("Stage 5.15 baseline ranking publication inspection passed")
    return {
        "publication": publication,
        "entity_scores": entity_scores,
        "metadata": metadata,
        "readme": readme,
    }


if __name__ == "__main__":
    inspect_baseline_ranking_publication()
