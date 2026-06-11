"""Publish the Stage 5.15 baseline ranking snapshot.

This script publishes baseline-only ranking artifacts from Stage 5.14 dry-run
outputs. It does not rerun models, recompute forecasts, recompute metrics, run
challengers, create tournament outputs, or select a production champion.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from model_lab.load_configs import load_yaml_config
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("publish_baseline_ranking")

POLICY_CONFIG = PROJECT_ROOT / "config" / "ranking_policy.yaml"
DRY_RUN_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "ranking_dry_run"
DRY_RUN_SCORES = DRY_RUN_DIR / "baseline_ranking_scores.csv"
DRY_RUN_BY_MODEL = DRY_RUN_DIR / "baseline_ranking_by_model.csv"
DRY_RUN_BY_ENTITY = DRY_RUN_DIR / "baseline_ranking_by_entity.csv"
DRY_RUN_SUMMARY = DRY_RUN_DIR / "baseline_ranking_summary.csv"
BASELINE_RANKING_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "baseline_ranking"

PUBLICATION_OUTPUT = BASELINE_RANKING_DIR / "baseline_ranking_publication.csv"
ENTITY_SCORES_OUTPUT = BASELINE_RANKING_DIR / "baseline_ranking_entity_scores.csv"
METADATA_OUTPUT = BASELINE_RANKING_DIR / "baseline_ranking_metadata.csv"
README_OUTPUT = BASELINE_RANKING_DIR / "baseline_ranking_readme.csv"

BASELINE_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
}


def _require_file(path) -> None:
    """Validate that a required publication input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required baseline ranking input missing: {path}")


def publish_baseline_ranking() -> dict[str, pd.DataFrame]:
    """Create baseline ranking publication artifacts."""

    logger.info("Stage 5.15 baseline ranking publication started")
    for path in (
        POLICY_CONFIG,
        DRY_RUN_SCORES,
        DRY_RUN_BY_MODEL,
        DRY_RUN_BY_ENTITY,
        DRY_RUN_SUMMARY,
    ):
        _require_file(path)

    BASELINE_RANKING_DIR.mkdir(parents=True, exist_ok=True)
    policy = load_yaml_config(POLICY_CONFIG)
    scores = pd.read_csv(DRY_RUN_SCORES)
    by_model = pd.read_csv(DRY_RUN_BY_MODEL)
    by_entity = pd.read_csv(DRY_RUN_BY_ENTITY)
    dry_run_summary = pd.read_csv(DRY_RUN_SUMMARY).iloc[0]
    timestamp = datetime.now().isoformat(timespec="seconds")

    if set(by_model["model_name"]) != BASELINE_MODELS:
        raise ValueError("Dry-run model scores do not contain exactly baseline models.")
    if "normalized_mape" not in scores.columns:
        raise ValueError("Dry-run scores must contain normalized_mape for publication.")

    mape_scores = (
        scores.groupby(["entity_key", "model_name"], as_index=False)["normalized_mape"]
        .median()
        .groupby("model_name", as_index=False)["normalized_mape"]
        .mean()
        .rename(columns={"normalized_mape": "mape_score"})
    )

    publication = by_model.rename(
        columns={
            "avg_normalized_wmape": "wmape_score",
            "avg_normalized_smape": "smape_score",
            "avg_normalized_rmse": "rmse_score",
            "avg_normalized_abs_bias": "abs_bias_score",
        }
    ).copy()
    publication = publication.merge(mape_scores, on="model_name", how="left")
    publication["windows_evaluated"] = int(dry_run_summary["windows"])
    publication["publication_timestamp"] = timestamp
    publication = publication[
        [
            "model_name",
            "global_score",
            "entity_count",
            "windows_evaluated",
            "wmape_score",
            "mape_score",
            "rmse_score",
            "smape_score",
            "abs_bias_score",
            "publication_timestamp",
        ]
    ].sort_values(["global_score", "model_name"], ascending=[False, True])

    entity_scores = by_entity.copy()
    entity_scores["publication_timestamp"] = timestamp

    metadata = pd.DataFrame(
        [
            {
                "ranking_policy_name": policy["policy_name"],
                "metrics_used": ";".join(policy["allowed_metrics"]),
                "normalization_method": policy["normalization"]["method"],
                "outlier_method": policy["outlier_handling"][
                    "extreme_outlier_control"
                ],
                "aggregation_method": ";".join(
                    f"{key}={value}" for key, value in policy["aggregation"].items()
                ),
                "tie_break_method": ";".join(policy["tie_breaking"]),
                "creation_timestamp": timestamp,
            }
        ]
    )
    readme = pd.DataFrame(
        [
            {
                "publication_summary": (
                    "Baseline-only evaluation snapshot. No challengers included; "
                    "no tournament performed; scores are normalized using the "
                    "Stage 5.13 policy. Future challengers must be evaluated using "
                    "the identical framework before comparison."
                ),
                "baseline_only_evaluation": True,
                "challengers_included": False,
                "tournament_performed": False,
                "scores_normalized": True,
                "future_challenger_requirement": (
                    "Evaluate challengers with the same metrics, normalization, "
                    "outlier controls, aggregation, and tie-break policy."
                ),
                "creation_timestamp": timestamp,
            }
        ]
    )

    publication.to_csv(PUBLICATION_OUTPUT, index=False)
    entity_scores.to_csv(ENTITY_SCORES_OUTPUT, index=False)
    metadata.to_csv(METADATA_OUTPUT, index=False)
    readme.to_csv(README_OUTPUT, index=False)

    logger.info("Created %s with %s rows", PUBLICATION_OUTPUT, len(publication))
    logger.info("Created %s with %s rows", ENTITY_SCORES_OUTPUT, len(entity_scores))
    logger.info("Created %s with %s rows", METADATA_OUTPUT, len(metadata))
    logger.info("Created %s with %s rows", README_OUTPUT, len(readme))
    logger.info("Stage 5.15 baseline ranking publication completed")
    return {
        "publication": publication,
        "entity_scores": entity_scores,
        "metadata": metadata,
        "readme": readme,
    }


if __name__ == "__main__":
    publish_baseline_ranking()
