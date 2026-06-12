"""Inspect Stage 5.24 aggregation hierarchy outputs."""

from __future__ import annotations

import math
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_aggregation_hierarchy")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
NON_NEGATIVE_DIR = MODEL_LAB_DIR / "non_negative_policy"
MASE_INPUT = NON_NEGATIVE_DIR / "non_negative_mase_scores.csv"
RMSSE_INPUT = NON_NEGATIVE_DIR / "non_negative_rmsse_scores.csv"
WINDOWS_INPUT = MODEL_LAB_DIR / "backtesting_windows.csv"
OUTPUT_DIR = MODEL_LAB_DIR / "aggregation_hierarchy"

CANONICAL_OUTPUT = OUTPUT_DIR / "canonical_entity_window_scores.csv"
ENTITY_MODEL_OUTPUT = OUTPUT_DIR / "aggregation_by_entity_model.csv"
MODEL_OUTPUT = OUTPUT_DIR / "aggregation_by_model.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "aggregation_summary.csv"
POLICY_OUTPUT = OUTPUT_DIR / "aggregation_policy.md"

PROTECTED_OUTPUT_DIRS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "metrics",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "benchmark_reference",
    MODEL_LAB_DIR / "seasonal_benchmark",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "non_negative_policy",
    MODEL_LAB_DIR / "tournament",
    PROJECT_ROOT / "shiny_app",
]

EXPECTED_CANONICAL_ROWS = 3178
EXPECTED_ENTITY_MODEL_ROWS = 273
EXPECTED_MODEL_ROWS = 7
EXPECTED_ENTITIES = 39
EXPECTED_WINDOWS = 454
EXPECTED_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
    "LinearRegression",
}
FORECAST_HORIZON_DAYS = 30
NUMERIC_TOLERANCE = 1e-9

CANONICAL_COLUMNS = [
    "run_id",
    "entity_key",
    "window_id",
    "model_name",
    "forecast_rows",
    "mase",
    "rmsse",
    "mase_beats_naive",
    "rmsse_risk_status",
    "mase_denominator_floored",
    "rmsse_denominator_floored",
    "created_timestamp",
]
ENTITY_MODEL_COLUMNS = [
    "entity_key",
    "model_name",
    "windows",
    "median_mase",
    "mean_mase",
    "p95_mase",
    "median_rmsse",
    "mean_rmsse",
    "p95_rmsse",
    "pct_windows_beating_naive",
    "pct_windows_high_risk",
    "mase_denominator_floored_rows",
    "rmsse_denominator_floored_rows",
    "created_timestamp",
]
MODEL_COLUMNS = [
    "model_name",
    "entities",
    "windows",
    "official_median_mase",
    "diagnostic_mean_mase",
    "diagnostic_p95_mase",
    "official_median_rmsse",
    "diagnostic_mean_rmsse",
    "diagnostic_p95_rmsse",
    "pct_entities_beating_naive",
    "pct_windows_beating_naive",
    "pct_entities_high_risk",
    "pct_windows_high_risk",
    "mase_denominator_floored_rows",
    "rmsse_denominator_floored_rows",
    "created_timestamp",
]
SUMMARY_COLUMNS = [
    "run_id",
    "entity_window_score_rows",
    "entity_model_rows",
    "model_rows",
    "entities",
    "windows",
    "models",
    "official_aggregation_method",
    "primary_metric",
    "guardrail_metric",
    "created_timestamp",
]


def _require_file(path: Path) -> None:
    """Validate that a required output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required aggregation output missing: {path}")


def _assert_columns(frame: pd.DataFrame, expected: list[str], name: str) -> None:
    """Validate expected columns are present."""

    missing = set(expected).difference(frame.columns)
    if missing:
        raise ValueError(f"{name} missing columns: {sorted(missing)}")


def _assert_no_forbidden_columns(frame: pd.DataFrame, name: str) -> None:
    """Validate no ranking/champion/winner columns exist."""

    forbidden_terms = ["rank", "champion", "winner"]
    bad = [
        column
        for column in frame.columns
        if any(term in column.lower() for term in forbidden_terms)
    ]
    if bad:
        raise ValueError(f"{name} contains forbidden columns: {bad}")


def _load_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, str]:
    """Load all aggregation hierarchy outputs."""

    for path in [
        CANONICAL_OUTPUT,
        ENTITY_MODEL_OUTPUT,
        MODEL_OUTPUT,
        SUMMARY_OUTPUT,
        POLICY_OUTPUT,
    ]:
        _require_file(path)
    canonical = pd.read_csv(CANONICAL_OUTPUT, parse_dates=["created_timestamp"])
    entity_model = pd.read_csv(ENTITY_MODEL_OUTPUT, parse_dates=["created_timestamp"])
    by_model = pd.read_csv(MODEL_OUTPUT, parse_dates=["created_timestamp"])
    summary = pd.read_csv(SUMMARY_OUTPUT, parse_dates=["created_timestamp"])
    policy = POLICY_OUTPUT.read_text(encoding="utf-8")

    _assert_columns(canonical, CANONICAL_COLUMNS, "canonical_entity_window_scores.csv")
    _assert_columns(entity_model, ENTITY_MODEL_COLUMNS, "aggregation_by_entity_model.csv")
    _assert_columns(by_model, MODEL_COLUMNS, "aggregation_by_model.csv")
    _assert_columns(summary, SUMMARY_COLUMNS, "aggregation_summary.csv")
    for name, frame in [
        ("canonical_entity_window_scores.csv", canonical),
        ("aggregation_by_entity_model.csv", entity_model),
        ("aggregation_by_model.csv", by_model),
        ("aggregation_summary.csv", summary),
    ]:
        _assert_no_forbidden_columns(frame, name)
    return canonical, entity_model, by_model, summary, policy


def _validate_numeric(frame: pd.DataFrame, columns: list[str], name: str) -> None:
    """Validate numeric columns have no NaN or Inf."""

    for column in columns:
        if frame[column].isna().any():
            raise ValueError(f"{name} contains NaN in {column}.")
        if not frame[column].map(math.isfinite).all():
            raise ValueError(f"{name} contains Inf/non-finite values in {column}.")


def _validate_canonical(canonical: pd.DataFrame) -> None:
    """Validate canonical entity/window/model score table."""

    if len(canonical) != EXPECTED_CANONICAL_ROWS:
        raise ValueError(f"Expected 3178 canonical rows; found {len(canonical)}.")
    if canonical.duplicated(["entity_key", "window_id", "model_name"]).any():
        raise ValueError("Duplicate entity/window/model rows found in canonical scores.")
    if canonical["entity_key"].nunique() != EXPECTED_ENTITIES:
        raise ValueError("Canonical table does not include all 39 entities.")
    if canonical[["entity_key", "window_id"]].drop_duplicates().shape[0] != EXPECTED_WINDOWS:
        raise ValueError("Canonical table does not include all 454 windows.")
    if set(canonical["model_name"].unique()) != EXPECTED_MODELS:
        raise ValueError("Canonical table does not include all 7 baseline models.")
    if not (canonical["forecast_rows"].astype(int) == FORECAST_HORIZON_DAYS).all():
        raise ValueError("Canonical forecast_rows must all be 30.")
    _validate_numeric(canonical, ["mase", "rmsse"], "canonical")

    beats = canonical["mase_beats_naive"].astype(str).str.lower().isin(["true", "1"])
    if not (beats == (canonical["mase"] < 1.0)).all():
        raise ValueError("mase_beats_naive does not match mase < 1.")


def _validate_merge_against_inputs(canonical: pd.DataFrame) -> None:
    """Validate canonical scores correctly merge adjusted MASE and RMSSE."""

    _require_file(MASE_INPUT)
    _require_file(RMSSE_INPUT)
    mase = pd.read_csv(MASE_INPUT)
    rmsse = pd.read_csv(RMSSE_INPUT)
    expected = mase[
        ["entity_key", "window_id", "model_name", "forecast_rows", "mase", "denominator_floored"]
    ].merge(
        rmsse[
            [
                "entity_key",
                "window_id",
                "model_name",
                "rmsse",
                "denominator_floored",
                "risk_status",
            ]
        ],
        on=["entity_key", "window_id", "model_name"],
        how="inner",
        validate="one_to_one",
        suffixes=("_mase", "_rmsse"),
    )
    expected["window_id"] = expected["window_id"].astype(int)
    merged = canonical.merge(
        expected,
        on=["entity_key", "window_id", "model_name"],
        how="left",
        validate="one_to_one",
        suffixes=("", "_expected"),
    )
    if merged["mase_expected"].isna().any():
        raise ValueError("Canonical table contains rows not present in adjusted inputs.")
    if not ((merged["mase"] - merged["mase_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Canonical MASE values do not match adjusted input.")
    if not ((merged["rmsse"] - merged["rmsse_expected"]).abs() < NUMERIC_TOLERANCE).all():
        raise ValueError("Canonical RMSSE values do not match adjusted input.")
    if not (merged["rmsse_risk_status"] == merged["risk_status"]).all():
        raise ValueError("Canonical RMSSE risk statuses do not match adjusted input.")


def _validate_entity_model(canonical: pd.DataFrame, entity_model: pd.DataFrame) -> None:
    """Validate entity/model aggregation."""

    if len(entity_model) != EXPECTED_ENTITY_MODEL_ROWS:
        raise ValueError(f"Expected 273 entity/model rows; found {len(entity_model)}.")
    if entity_model.duplicated(["entity_key", "model_name"]).any():
        raise ValueError("Duplicate entity/model rows found.")
    _validate_numeric(
        entity_model,
        [
            "median_mase",
            "mean_mase",
            "p95_mase",
            "median_rmsse",
            "mean_rmsse",
            "p95_rmsse",
            "pct_windows_beating_naive",
            "pct_windows_high_risk",
        ],
        "entity_model",
    )
    rows = []
    for keys, group in canonical.groupby(["entity_key", "model_name"]):
        rows.append(
            {
                "entity_key": keys[0],
                "model_name": keys[1],
                "windows_expected": group["window_id"].nunique(),
                "median_mase_expected": float(group["mase"].median()),
                "median_rmsse_expected": float(group["rmsse"].median()),
            }
        )
    expected = pd.DataFrame(rows)
    merged = entity_model.merge(expected, on=["entity_key", "model_name"], how="left")
    if merged["median_mase_expected"].isna().any():
        raise ValueError("Entity/model aggregation contains unexpected rows.")
    if not (merged["windows"].astype(int) == merged["windows_expected"]).all():
        raise ValueError("Entity/model windows count mismatch.")
    if not (
        (merged["median_mase"] - merged["median_mase_expected"]).abs()
        < NUMERIC_TOLERANCE
    ).all():
        raise ValueError("Entity/model median MASE mismatch.")
    if not (
        (merged["median_rmsse"] - merged["median_rmsse_expected"]).abs()
        < NUMERIC_TOLERANCE
    ).all():
        raise ValueError("Entity/model median RMSSE mismatch.")


def _validate_model(entity_model: pd.DataFrame, by_model: pd.DataFrame) -> None:
    """Validate model-level official median of entity medians."""

    if len(by_model) != EXPECTED_MODEL_ROWS:
        raise ValueError(f"Expected 7 model rows; found {len(by_model)}.")
    if set(by_model["model_name"]) != EXPECTED_MODELS:
        raise ValueError("Model aggregation does not include all baseline models.")
    _validate_numeric(
        by_model,
        [
            "official_median_mase",
            "diagnostic_mean_mase",
            "diagnostic_p95_mase",
            "official_median_rmsse",
            "diagnostic_mean_rmsse",
            "diagnostic_p95_rmsse",
            "pct_entities_beating_naive",
            "pct_windows_beating_naive",
            "pct_entities_high_risk",
            "pct_windows_high_risk",
        ],
        "by_model",
    )
    rows = []
    for model_name, group in entity_model.groupby("model_name"):
        rows.append(
            {
                "model_name": model_name,
                "entities_expected": group["entity_key"].nunique(),
                "official_median_mase_expected": float(group["median_mase"].median()),
                "official_median_rmsse_expected": float(group["median_rmsse"].median()),
            }
        )
    expected = pd.DataFrame(rows)
    merged = by_model.merge(expected, on="model_name", how="left")
    if merged["official_median_mase_expected"].isna().any():
        raise ValueError("Model aggregation contains unexpected rows.")
    if not (merged["entities"].astype(int) == merged["entities_expected"]).all():
        raise ValueError("Model entities count mismatch.")
    if not (
        (merged["official_median_mase"] - merged["official_median_mase_expected"]).abs()
        < NUMERIC_TOLERANCE
    ).all():
        raise ValueError("official_median_mase is not median of entity medians.")
    if not (
        (merged["official_median_rmsse"] - merged["official_median_rmsse_expected"]).abs()
        < NUMERIC_TOLERANCE
    ).all():
        raise ValueError("official_median_rmsse is not median of entity medians.")


def _validate_summary(
    canonical: pd.DataFrame,
    entity_model: pd.DataFrame,
    by_model: pd.DataFrame,
    summary: pd.DataFrame,
) -> None:
    """Validate summary table."""

    if len(summary) != 1:
        raise ValueError(f"Summary must contain exactly one row; found {len(summary)}.")
    row = summary.iloc[0]
    expected = {
        "entity_window_score_rows": len(canonical),
        "entity_model_rows": len(entity_model),
        "model_rows": len(by_model),
        "entities": canonical["entity_key"].nunique(),
        "windows": canonical[["entity_key", "window_id"]].drop_duplicates().shape[0],
        "models": canonical["model_name"].nunique(),
    }
    for column, value in expected.items():
        if int(row[column]) != int(value):
            raise ValueError(
                f"Summary {column} mismatch: expected {value}, found {row[column]}"
            )
    if row["primary_metric"] != "MASE":
        raise ValueError("Summary primary_metric must be MASE.")
    if row["guardrail_metric"] != "RMSSE":
        raise ValueError("Summary guardrail_metric must be RMSSE.")


def _validate_valid_window_coverage(canonical: pd.DataFrame) -> None:
    """Validate all valid backtesting windows are represented."""

    _require_file(WINDOWS_INPUT)
    windows = pd.read_csv(WINDOWS_INPUT)
    windows = windows[windows["forecast_horizon_days"] == FORECAST_HORIZON_DAYS].copy()
    planned = set(zip(windows["entity_key"], windows["window_id"].astype(int)))
    actual = set(zip(canonical["entity_key"], canonical["window_id"].astype(int)))
    if planned != actual:
        missing = sorted(planned - actual)[:10]
        unexpected = sorted(actual - planned)[:10]
        raise ValueError(
            "Canonical windows do not match valid windows. "
            f"Missing sample: {missing}; unexpected sample: {unexpected}"
        )


def _validate_policy(policy: str) -> None:
    """Validate policy document includes required semantics."""

    required_phrases = [
        "MASE is the primary benchmark metric",
        "RMSSE is guardrail only",
        "equal entity weighting",
        "No champion is selected",
        "No ranking is created",
        "deferred to later blocks",
        "diagnostics only",
    ]
    missing = [phrase for phrase in required_phrases if phrase not in policy]
    if missing:
        raise ValueError(f"Aggregation policy missing phrases: {missing}")


def _log_protected_scope() -> None:
    """Report protected directories to make no-touch validation explicit."""

    for path in PROTECTED_OUTPUT_DIRS:
        if path.exists():
            logger.info("Protected path present and not inspected for writes: %s", path)
        else:
            logger.info("Protected path not present: %s", path)


def inspect_aggregation_hierarchy() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Validate Stage 5.24 aggregation hierarchy outputs."""

    logger.info("Stage 5.24 aggregation hierarchy inspection started")
    canonical, entity_model, by_model, summary, policy = _load_outputs()
    _validate_canonical(canonical)
    _validate_merge_against_inputs(canonical)
    _validate_valid_window_coverage(canonical)
    _validate_entity_model(canonical, entity_model)
    _validate_model(entity_model, by_model)
    _validate_summary(canonical, entity_model, by_model, summary)
    _validate_policy(policy)
    _log_protected_scope()

    logger.info("Output files exist: yes")
    logger.info("Required columns exist: yes")
    logger.info("No NaN or Inf values: yes")
    logger.info("No duplicate entity/window/model rows: yes")
    logger.info("Canonical rows: %s", len(canonical))
    logger.info("Entity/model rows: %s", len(entity_model))
    logger.info("Model rows: %s", len(by_model))
    logger.info("Entities represented: %s", canonical["entity_key"].nunique())
    logger.info(
        "Windows represented: %s",
        canonical[["entity_key", "window_id"]].drop_duplicates().shape[0],
    )
    logger.info("Models represented: %s", canonical["model_name"].nunique())
    logger.info("official_median_mase computed from entity medians: yes")
    logger.info("official_median_rmsse computed from entity medians: yes")
    logger.info("No ranking/champion columns: yes")
    logger.info("No tournament outputs created: yes")
    logger.info("Stage 5.24 aggregation hierarchy inspection completed")
    return canonical, entity_model, by_model, summary


if __name__ == "__main__":
    inspect_aggregation_hierarchy()
