"""Build pairwise statistical significance evidence for benchmark models.

This Stage 5.25 script creates statistical evidence only. It does not rank
models, select winners, create champions, run models, or write tournament
outputs.
"""

from __future__ import annotations

from datetime import datetime
from itertools import combinations
from math import comb

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("build_statistical_significance")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
AGGREGATION_DIR = MODEL_LAB_DIR / "aggregation_hierarchy"
CANONICAL_INPUT = AGGREGATION_DIR / "canonical_entity_window_scores.csv"
ENTITY_MODEL_INPUT = AGGREGATION_DIR / "aggregation_by_entity_model.csv"
MODEL_INPUT = AGGREGATION_DIR / "aggregation_by_model.csv"
POLICY_INPUT = AGGREGATION_DIR / "aggregation_policy.md"
OUTPUT_DIR = MODEL_LAB_DIR / "statistical_significance"

PAIRWISE_OUTPUT = OUTPUT_DIR / "pairwise_model_significance.csv"
MODEL_SUMMARY_OUTPUT = OUTPUT_DIR / "model_significance_summary.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "significance_summary.csv"
POLICY_OUTPUT = OUTPUT_DIR / "significance_policy.md"

RUN_ID_PREFIX = "statistical_significance"
BOOTSTRAP_ITERATIONS = 10000
BOOTSTRAP_SEED = 20260612
ALPHA = 0.05
MIN_PRACTICAL_MASE_DELTA = 0.02

PAIRWISE_COLUMNS = [
    "run_id",
    "model_a",
    "model_b",
    "entities_compared",
    "ties",
    "model_a_entity_wins",
    "model_b_entity_wins",
    "model_a_entity_win_rate",
    "model_b_entity_win_rate",
    "median_delta_mase",
    "mean_delta_mase",
    "bootstrap_median_delta",
    "ci_lower_95",
    "ci_upper_95",
    "p_value_sign_test",
    "p_value_bh_adjusted",
    "bh_significant",
    "min_practical_mase_delta",
    "practical_significance",
    "evidence_status",
    "created_timestamp",
]
MODEL_SUMMARY_COLUMNS = [
    "model_name",
    "entities",
    "official_median_mase",
    "official_median_rmsse",
    "pairwise_comparisons",
    "pairwise_supported_count",
    "pairwise_unsupported_count",
    "pairwise_inconclusive_count",
    "pct_entities_beating_naive",
    "pct_windows_beating_naive",
    "pct_entities_high_risk",
    "pct_windows_high_risk",
    "created_timestamp",
]
SUMMARY_COLUMNS = [
    "run_id",
    "models",
    "entities",
    "pairwise_comparisons",
    "bootstrap_iterations",
    "alpha",
    "min_practical_mase_delta",
    "bh_significant_comparisons",
    "practically_significant_comparisons",
    "supported_comparisons",
    "inconclusive_comparisons",
    "created_timestamp",
]


def _require_file(path) -> None:
    """Validate that a required input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required significance input missing: {path}")


def _load_entity_model() -> pd.DataFrame:
    """Load entity-level official comparison units."""

    _require_file(ENTITY_MODEL_INPUT)
    data = pd.read_csv(ENTITY_MODEL_INPUT)
    required = {"entity_key", "model_name", "median_mase"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"aggregation_by_entity_model.csv missing columns: {sorted(missing)}")
    data = data.copy()
    data["median_mase"] = pd.to_numeric(data["median_mase"], errors="coerce")
    if data["median_mase"].isna().any():
        raise ValueError("NaN median_mase values found in entity/model input.")
    return data


def _load_model_context() -> pd.DataFrame:
    """Load model-level MASE and RMSSE context from aggregation hierarchy."""

    _require_file(MODEL_INPUT)
    data = pd.read_csv(MODEL_INPUT)
    required = {
        "model_name",
        "entities",
        "official_median_mase",
        "official_median_rmsse",
        "pct_entities_beating_naive",
        "pct_windows_beating_naive",
        "pct_entities_high_risk",
        "pct_windows_high_risk",
    }
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"aggregation_by_model.csv missing columns: {sorted(missing)}")
    return data.copy()


def _validate_source_files() -> None:
    """Validate non-tabular inputs exist for traceability."""

    _require_file(CANONICAL_INPUT)
    _require_file(POLICY_INPUT)


def _sign_test_p_value(model_a_wins: int, model_b_wins: int) -> float:
    """Two-sided exact binomial sign-test p-value for p=0.5."""

    n = model_a_wins + model_b_wins
    if n == 0:
        return 1.0
    k = min(model_a_wins, model_b_wins)
    tail = sum(comb(n, i) for i in range(k + 1)) / (2**n)
    return min(1.0, 2.0 * tail)


def _apply_bh(p_values: list[float], alpha: float) -> tuple[list[float], list[bool]]:
    """Apply Benjamini-Hochberg correction to a list of p-values."""

    m = len(p_values)
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * m
    running_min = 1.0
    for rank_from_end, (idx, p_value) in enumerate(reversed(indexed), start=1):
        rank = m - rank_from_end + 1
        value = min(running_min, p_value * m / rank)
        running_min = value
        adjusted[idx] = min(1.0, value)
    significant = [value <= alpha for value in adjusted]
    return adjusted, significant


def _pairwise_rows(
    entity_model: pd.DataFrame, run_id: str, timestamp: str
) -> pd.DataFrame:
    """Create unordered pairwise statistical evidence rows."""

    models = sorted(entity_model["model_name"].unique())
    rng = np.random.default_rng(BOOTSTRAP_SEED)
    rows = []

    for model_a, model_b in combinations(models, 2):
        a = entity_model[entity_model["model_name"] == model_a][
            ["entity_key", "median_mase"]
        ].rename(columns={"median_mase": "median_mase_a"})
        b = entity_model[entity_model["model_name"] == model_b][
            ["entity_key", "median_mase"]
        ].rename(columns={"median_mase": "median_mase_b"})
        paired = a.merge(b, on="entity_key", how="inner", validate="one_to_one")
        deltas = (paired["median_mase_a"] - paired["median_mase_b"]).to_numpy()
        entities = len(deltas)
        if entities == 0:
            raise ValueError(f"No paired entities for {model_a} vs {model_b}.")

        sample_indices = rng.integers(0, entities, size=(BOOTSTRAP_ITERATIONS, entities))
        bootstrap_medians = np.median(deltas[sample_indices], axis=1)
        model_a_wins = int((deltas < 0).sum())
        model_b_wins = int((deltas > 0).sum())
        ties = int((deltas == 0).sum())
        p_value = _sign_test_p_value(model_a_wins, model_b_wins)
        median_delta = float(np.median(deltas))

        rows.append(
            {
                "run_id": run_id,
                "model_a": model_a,
                "model_b": model_b,
                "entities_compared": entities,
                "ties": ties,
                "model_a_entity_wins": model_a_wins,
                "model_b_entity_wins": model_b_wins,
                "model_a_entity_win_rate": model_a_wins / entities,
                "model_b_entity_win_rate": model_b_wins / entities,
                "median_delta_mase": median_delta,
                "mean_delta_mase": float(np.mean(deltas)),
                "bootstrap_median_delta": float(np.median(bootstrap_medians)),
                "ci_lower_95": float(np.quantile(bootstrap_medians, 0.025)),
                "ci_upper_95": float(np.quantile(bootstrap_medians, 0.975)),
                "p_value_sign_test": p_value,
                "p_value_bh_adjusted": 1.0,
                "bh_significant": False,
                "min_practical_mase_delta": MIN_PRACTICAL_MASE_DELTA,
                "practical_significance": abs(median_delta)
                >= MIN_PRACTICAL_MASE_DELTA,
                "evidence_status": "inconclusive",
                "created_timestamp": timestamp,
            }
        )

    pairwise = pd.DataFrame(rows, columns=PAIRWISE_COLUMNS)
    adjusted, significant = _apply_bh(pairwise["p_value_sign_test"].tolist(), ALPHA)
    pairwise["p_value_bh_adjusted"] = adjusted
    pairwise["bh_significant"] = significant

    pairwise["evidence_status"] = pairwise.apply(_evidence_status, axis=1)
    return pairwise


def _evidence_status(row: pd.Series) -> str:
    """Classify pairwise evidence without selecting winners."""

    if (
        row["ci_upper_95"] < 0
        and bool(row["bh_significant"])
        and bool(row["practical_significance"])
    ):
        return "model_a_supported"
    if (
        row["ci_lower_95"] > 0
        and bool(row["bh_significant"])
        and bool(row["practical_significance"])
    ):
        return "model_b_supported"
    return "inconclusive"


def _model_summary(
    pairwise: pd.DataFrame, model_context: pd.DataFrame, timestamp: str
) -> pd.DataFrame:
    """Create model-level pairwise evidence counts without ranking."""

    rows = []
    for _, context in model_context.sort_values("model_name").iterrows():
        model = context["model_name"]
        involved = pairwise[
            (pairwise["model_a"] == model) | (pairwise["model_b"] == model)
        ]
        supported = int(
            (
                ((involved["model_a"] == model) & (involved["evidence_status"] == "model_a_supported"))
                | ((involved["model_b"] == model) & (involved["evidence_status"] == "model_b_supported"))
            ).sum()
        )
        unsupported = int(
            (
                ((involved["model_a"] == model) & (involved["evidence_status"] == "model_b_supported"))
                | ((involved["model_b"] == model) & (involved["evidence_status"] == "model_a_supported"))
            ).sum()
        )
        inconclusive = int((involved["evidence_status"] == "inconclusive").sum())
        rows.append(
            {
                "model_name": model,
                "entities": int(context["entities"]),
                "official_median_mase": float(context["official_median_mase"]),
                "official_median_rmsse": float(context["official_median_rmsse"]),
                "pairwise_comparisons": len(involved),
                "pairwise_supported_count": supported,
                "pairwise_unsupported_count": unsupported,
                "pairwise_inconclusive_count": inconclusive,
                "pct_entities_beating_naive": float(context["pct_entities_beating_naive"]),
                "pct_windows_beating_naive": float(context["pct_windows_beating_naive"]),
                "pct_entities_high_risk": float(context["pct_entities_high_risk"]),
                "pct_windows_high_risk": float(context["pct_windows_high_risk"]),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=MODEL_SUMMARY_COLUMNS)


def _summary(
    pairwise: pd.DataFrame,
    entity_model: pd.DataFrame,
    run_id: str,
    timestamp: str,
) -> pd.DataFrame:
    """Create global significance summary."""

    supported = int((pairwise["evidence_status"] != "inconclusive").sum())
    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "models": entity_model["model_name"].nunique(),
                "entities": entity_model["entity_key"].nunique(),
                "pairwise_comparisons": len(pairwise),
                "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
                "alpha": ALPHA,
                "min_practical_mase_delta": MIN_PRACTICAL_MASE_DELTA,
                "bh_significant_comparisons": int(pairwise["bh_significant"].sum()),
                "practically_significant_comparisons": int(
                    pairwise["practical_significance"].sum()
                ),
                "supported_comparisons": supported,
                "inconclusive_comparisons": int(
                    (pairwise["evidence_status"] == "inconclusive").sum()
                ),
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _policy_markdown(timestamp: str) -> str:
    """Return significance policy documentation."""

    return f"""# Statistical Significance Policy - Stage 5.25

Created timestamp: {timestamp}

## Metrics

- MASE is the primary metric.
- RMSSE is guardrail only.
- RMSSE context is included in model summaries, but RMSSE is not used to determine statistical significance.

## Comparison Unit

Significance testing uses entity-level median MASE from `aggregation_by_entity_model.csv`.
Raw forecast rows are not used as the official significance unit, so entities with more windows do not dominate the evidence.

## Methods

- Paired bootstrap is performed over entities.
- The bootstrap uses 10,000 iterations and deterministic seed `20260612`.
- The sign test is paired by entity and ignores exact ties in the binomial denominator.
- Benjamini-Hochberg correction is applied across the 21 pairwise sign-test p-values.
- The practical threshold is `0.02` MASE.

## Evidence Scope

Pairwise support is not a champion decision. No model ranking is created in this block. Champion selection is deferred to later blocks.
"""


def _write_outputs(
    pairwise: pd.DataFrame,
    model_summary: pd.DataFrame,
    summary: pd.DataFrame,
    policy_text: str,
) -> None:
    """Write statistical significance outputs only."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    pairwise.to_csv(PAIRWISE_OUTPUT, index=False)
    model_summary.to_csv(MODEL_SUMMARY_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    POLICY_OUTPUT.write_text(policy_text, encoding="utf-8")
    logger.info("Created %s with %s rows", PAIRWISE_OUTPUT, len(pairwise))
    logger.info("Created %s with %s rows", MODEL_SUMMARY_OUTPUT, len(model_summary))
    logger.info("Created %s with %s rows", SUMMARY_OUTPUT, len(summary))
    logger.info("Created %s", POLICY_OUTPUT)


def build_statistical_significance() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build pairwise statistical significance evidence."""

    logger.info("Stage 5.25 statistical significance build started")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")
    _validate_source_files()
    entity_model = _load_entity_model()
    model_context = _load_model_context()

    pairwise = _pairwise_rows(entity_model, run_id, timestamp)
    model_summary = _model_summary(pairwise, model_context, timestamp)
    summary = _summary(pairwise, entity_model, run_id, timestamp)

    logger.info("Models: %s", entity_model["model_name"].nunique())
    logger.info("Entities: %s", entity_model["entity_key"].nunique())
    logger.info("Pairwise comparisons: %s", len(pairwise))
    logger.info("BH significant comparisons: %s", int(pairwise["bh_significant"].sum()))
    logger.info(
        "Practically significant comparisons: %s",
        int(pairwise["practical_significance"].sum()),
    )
    logger.info(
        "Supported comparisons: %s",
        int((pairwise["evidence_status"] != "inconclusive").sum()),
    )
    logger.info("No rankings, champions, winners, or tournament outputs created.")

    _write_outputs(pairwise, model_summary, summary, _policy_markdown(timestamp))
    logger.info("Stage 5.25 statistical significance build completed")
    return pairwise, model_summary, summary


if __name__ == "__main__":
    build_statistical_significance()
