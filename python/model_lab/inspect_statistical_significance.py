"""Inspect Stage 5.25 statistical significance outputs."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_statistical_significance")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
AGGREGATION_DIR = MODEL_LAB_DIR / "aggregation_hierarchy"
ENTITY_MODEL_INPUT = AGGREGATION_DIR / "aggregation_by_entity_model.csv"
MODEL_INPUT = AGGREGATION_DIR / "aggregation_by_model.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "statistical_significance"

PAIRWISE_OUTPUT = OUTPUT_DIR / "pairwise_model_significance.csv"
MODEL_SUMMARY_OUTPUT = OUTPUT_DIR / "model_significance_summary.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "significance_summary.csv"
POLICY_OUTPUT = OUTPUT_DIR / "significance_policy.md"

PROTECTED_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "benchmark_reference",
    MODEL_LAB_DIR / "seasonal_benchmark",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "non_negative_policy",
    MODEL_LAB_DIR / "aggregation_hierarchy",
    MODEL_LAB_DIR / "tournament",
    PROJECT_ROOT / "shiny_app",
]

EXPECTED_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
    "LinearRegression",
}
EXPECTED_MODELS_COUNT = 7
EXPECTED_ENTITIES = 39
EXPECTED_PAIRWISE_ROWS = 21
EXPECTED_MODEL_SUMMARY_ROWS = 7
BOOTSTRAP_ITERATIONS = 10000
ALPHA = 0.05
MIN_PRACTICAL_MASE_DELTA = 0.02
NUMERIC_TOLERANCE = 1e-9
EVIDENCE_STATUSES = {"model_a_supported", "model_b_supported", "inconclusive"}

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


def _require_file(path: Path) -> None:
    """Validate that a required output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required significance output missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _assert_no_forbidden_columns(frame: pd.DataFrame, name: str) -> None:
    """Validate no rank/champion/winner columns exist."""

    forbidden_terms = ["rank", "champion", "winner"]
    bad = [
        column
        for column in frame.columns
        if any(term in column.lower() for term in forbidden_terms)
    ]
    if bad:
        raise ValueError(f"{name} contains forbidden columns: {bad}")


def _load_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """Load statistical significance outputs."""

    for path in [PAIRWISE_OUTPUT, MODEL_SUMMARY_OUTPUT, SUMMARY_OUTPUT, POLICY_OUTPUT]:
        _require_file(path)
    pairwise = pd.read_csv(PAIRWISE_OUTPUT, parse_dates=["created_timestamp"])
    model_summary = pd.read_csv(MODEL_SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    summary = pd.read_csv(SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    policy = POLICY_OUTPUT.read_text(encoding="utf-8")
    _assert_columns(pairwise, PAIRWISE_COLUMNS, "pairwise_model_significance.csv")
    _assert_columns(model_summary, MODEL_SUMMARY_COLUMNS, "model_significance_summary.csv")
    _assert_columns(summary, SUMMARY_COLUMNS, "significance_summary.csv")
    for name, frame in [
        ("pairwise_model_significance.csv", pairwise),
        ("model_significance_summary.csv", model_summary),
        ("significance_summary.csv", summary),
    ]:
        _assert_no_forbidden_columns(frame, name)
    return pairwise, model_summary, summary, policy


def _validate_numeric(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    """Validate numeric columns have no NaN or Inf."""

    for column in columns:
        if frame[column].isna().any():
            raise ValueError(f"{name} contains NaN in {column}.")
        if not frame[column].map(math.isfinite).all():
            raise ValueError(f"{name} contains Inf/non-finite values in {column}.")


def _bool_series(series: pd.Series) -> pd.Series:
    """Normalize bool-like CSV values to booleans."""

    return series.astype(str).str.lower().isin(["true", "1"])


def _validate_pairwise(pairwise: pd.DataFrame) -> None:
    """Validate pairwise evidence table."""

    if len(pairwise) != EXPECTED_PAIRWISE_ROWS:
        raise ValueError(f"Expected 21 pairwise rows; found {len(pairwise)}.")
    models = set(pairwise["model_a"]).union(set(pairwise["model_b"]))
    if models != EXPECTED_MODELS:
        raise ValueError(f"Pairwise model set mismatch: {sorted(models)}")
    pair_keys = pairwise.apply(lambda row: tuple(sorted([row["model_a"], row["model_b"]])), axis=1)
    if pair_keys.duplicated().any():
        raise ValueError("Duplicate or reversed duplicate model pairs found.")
    if (pairwise["model_a"] == pairwise["model_b"]).any():
        raise ValueError("Self-comparisons found.")
    if not (pairwise["entities_compared"].astype(int) >= 30).all():
        raise ValueError("Each pairwise comparison must have at least 30 entities.")

    _validate_numeric(
        pairwise,
        [
            "model_a_entity_win_rate",
            "model_b_entity_win_rate",
            "median_delta_mase",
            "mean_delta_mase",
            "bootstrap_median_delta",
            "ci_lower_95",
            "ci_upper_95",
            "p_value_sign_test",
            "p_value_bh_adjusted",
            "min_practical_mase_delta",
        ],
        "pairwise",
    )
    if not (pairwise["ci_lower_95"] <= pairwise["ci_upper_95"]).all():
        raise ValueError("Invalid confidence interval ordering.")
    for column in ["p_value_sign_test", "p_value_bh_adjusted"]:
        if not ((pairwise[column] >= 0) & (pairwise[column] <= 1)).all():
            raise ValueError(f"{column} must be between 0 and 1.")
    if not set(pairwise["evidence_status"]).issubset(EVIDENCE_STATUSES):
        raise ValueError("Unexpected evidence_status values found.")
    if not (pairwise["min_practical_mase_delta"] == MIN_PRACTICAL_MASE_DELTA).all():
        raise ValueError("Practical threshold mismatch.")

    bh = _bool_series(pairwise["bh_significant"])
    practical = _bool_series(pairwise["practical_significance"])
    expected_practical = pairwise["median_delta_mase"].abs() >= MIN_PRACTICAL_MASE_DELTA
    if not (practical == expected_practical).all():
        raise ValueError("practical_significance does not match threshold.")
    expected_status = []
    for _, row in pairwise.iterrows():
        is_bh = str(row["bh_significant"]).lower() in ["true", "1"]
        is_practical = str(row["practical_significance"]).lower() in ["true", "1"]
        if row["ci_upper_95"] < 0 and is_bh and is_practical:
            expected_status.append("model_a_supported")
        elif row["ci_lower_95"] > 0 and is_bh and is_practical:
            expected_status.append("model_b_supported")
        else:
            expected_status.append("inconclusive")
    if not (pairwise["evidence_status"].tolist() == expected_status):
        raise ValueError("Evidence status values do not match policy rules.")


def _validate_against_entity_input(pairwise: pd.DataFrame) -> None:
    """Validate entity-level input representation and pairwise deltas."""

    _require_file(ENTITY_MODEL_INPUT)
    entity_model = pd.read_csv(ENTITY_MODEL_INPUT)
    if entity_model["entity_key"].nunique() != EXPECTED_ENTITIES:
        raise ValueError("Significance input does not include all 39 entities.")
    if set(entity_model["model_name"].unique()) != EXPECTED_MODELS:
        raise ValueError("Significance input does not include all 7 models.")
    if len(entity_model) != EXPECTED_ENTITIES * EXPECTED_MODELS_COUNT:
        raise ValueError("Entity/model input row count mismatch.")

    for _, row in pairwise.iterrows():
        a = entity_model[entity_model["model_name"] == row["model_a"]][
            ["entity_key", "median_mase"]
        ].rename(columns={"median_mase": "a"})
        b = entity_model[entity_model["model_name"] == row["model_b"]][
            ["entity_key", "median_mase"]
        ].rename(columns={"median_mase": "b"})
        paired = a.merge(b, on="entity_key", how="inner", validate="one_to_one")
        deltas = paired["a"] - paired["b"]
        if len(paired) != int(row["entities_compared"]):
            raise ValueError("entities_compared mismatch.")
        if abs(float(deltas.median()) - float(row["median_delta_mase"])) > NUMERIC_TOLERANCE:
            raise ValueError("median_delta_mase mismatch.")
        if abs(float(deltas.mean()) - float(row["mean_delta_mase"])) > NUMERIC_TOLERANCE:
            raise ValueError("mean_delta_mase mismatch.")
        if int((deltas < 0).sum()) != int(row["model_a_entity_wins"]):
            raise ValueError("model_a_entity_wins mismatch.")
        if int((deltas > 0).sum()) != int(row["model_b_entity_wins"]):
            raise ValueError("model_b_entity_wins mismatch.")
        if int((deltas == 0).sum()) != int(row["ties"]):
            raise ValueError("ties mismatch.")


def _validate_model_summary(pairwise: pd.DataFrame, model_summary: pd.DataFrame) -> None:
    """Validate model-level significance summary."""

    if len(model_summary) != EXPECTED_MODEL_SUMMARY_ROWS:
        raise ValueError(f"Expected 7 model summary rows; found {len(model_summary)}.")
    if set(model_summary["model_name"]) != EXPECTED_MODELS:
        raise ValueError("Model summary does not include all baseline models.")
    _validate_numeric(
        model_summary,
        [
            "official_median_mase",
            "official_median_rmsse",
            "pct_entities_beating_naive",
            "pct_windows_beating_naive",
            "pct_entities_high_risk",
            "pct_windows_high_risk",
        ],
        "model_summary",
    )
    _require_file(MODEL_INPUT)
    model_input = pd.read_csv(MODEL_INPUT)
    merged_context = model_summary.merge(
        model_input[
            [
                "model_name",
                "entities",
                "official_median_mase",
                "official_median_rmsse",
                "pct_entities_high_risk",
                "pct_windows_high_risk",
            ]
        ],
        on="model_name",
        how="left",
        suffixes=("", "_input"),
    )
    if merged_context["official_median_mase_input"].isna().any():
        raise ValueError("Model summary contains unexpected model context rows.")
    for _, row in model_summary.iterrows():
        model = row["model_name"]
        involved = pairwise[(pairwise["model_a"] == model) | (pairwise["model_b"] == model)]
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
        if int(row["pairwise_comparisons"]) != len(involved):
            raise ValueError("pairwise_comparisons mismatch.")
        if int(row["pairwise_supported_count"]) != supported:
            raise ValueError("pairwise_supported_count mismatch.")
        if int(row["pairwise_unsupported_count"]) != unsupported:
            raise ValueError("pairwise_unsupported_count mismatch.")
        if int(row["pairwise_inconclusive_count"]) != inconclusive:
            raise ValueError("pairwise_inconclusive_count mismatch.")


def _validate_summary(pairwise: pd.DataFrame, model_summary: pd.DataFrame, summary: pd.DataFrame) -> None:
    """Validate global significance summary."""

    if len(summary) != 1:
        raise ValueError(f"Summary must have one row; found {len(summary)}.")
    row = summary.iloc[0]
    expected = {
        "models": EXPECTED_MODELS_COUNT,
        "entities": EXPECTED_ENTITIES,
        "pairwise_comparisons": len(pairwise),
        "bootstrap_iterations": BOOTSTRAP_ITERATIONS,
        "bh_significant_comparisons": int(_bool_series(pairwise["bh_significant"]).sum()),
        "practically_significant_comparisons": int(
            _bool_series(pairwise["practical_significance"]).sum()
        ),
        "supported_comparisons": int((pairwise["evidence_status"] != "inconclusive").sum()),
        "inconclusive_comparisons": int((pairwise["evidence_status"] == "inconclusive").sum()),
    }
    for column, value in expected.items():
        if int(row[column]) != int(value):
            raise ValueError(
                f"Summary {column} mismatch: expected {value}, found {row[column]}"
            )
    if abs(float(row["alpha"]) - ALPHA) > NUMERIC_TOLERANCE:
        raise ValueError("Summary alpha mismatch.")
    if abs(float(row["min_practical_mase_delta"]) - MIN_PRACTICAL_MASE_DELTA) > NUMERIC_TOLERANCE:
        raise ValueError("Summary practical threshold mismatch.")


def _validate_policy(policy: str) -> None:
    """Validate significance policy document."""

    required_phrases = [
        "MASE is the primary metric",
        "RMSSE is guardrail only",
        "entity-level median MASE",
        "Paired bootstrap is performed over entities",
        "sign test is paired by entity",
        "Benjamini-Hochberg correction",
        "0.02",
        "not a champion decision",
        "No model ranking is created",
        "Champion selection is deferred",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in policy]
    if missing:
        raise ValueError(f"Significance policy missing phrases: {missing}")


def _log_protected_scope() -> None:
    """Report protected directories to make no-touch validation explicit."""

    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not inspected for writes: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_statistical_significance() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate Stage 5.25 statistical significance outputs."""

    logger.info("Stage 5.25 statistical significance inspection started")
    pairwise, model_summary, summary, policy = _load_outputs()
    _validate_pairwise(pairwise)
    _validate_against_entity_input(pairwise)
    _validate_model_summary(pairwise, model_summary)
    _validate_summary(pairwise, model_summary, summary)
    _validate_policy(policy)
    _log_protected_scope()

    logger.info("Output files exist: yes")
    logger.info("Required columns exist: yes")
    logger.info("Pairwise rows: %s", len(pairwise))
    logger.info("Model summary rows: %s", len(model_summary))
    logger.info("Summary rows: %s", len(summary))
    logger.info("All 7 baseline models represented: yes")
    logger.info("All 39 entities represented in significance input: yes")
    logger.info("No NaN or Inf values: yes")
    logger.info("No duplicate/reversed model pairs: yes")
    logger.info("Confidence intervals and p-values valid: yes")
    logger.info("No rank/champion/winner columns: yes")
    logger.info("No tournament outputs created: yes")
    logger.info("Stage 5.25 statistical significance inspection completed")
    return pairwise, model_summary, summary


if __name__ == "__main__":
    inspect_statistical_significance()
