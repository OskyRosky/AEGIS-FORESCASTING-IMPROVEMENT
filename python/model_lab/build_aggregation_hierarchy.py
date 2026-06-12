"""Build official benchmark aggregation hierarchy.

This Stage 5.24 script creates aggregation-ready score tables only. It does not
rank models, select winners, create champions, or write tournament outputs.
"""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("build_aggregation_hierarchy")

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

RUN_ID_PREFIX = "aggregation_hierarchy"
FORECAST_HORIZON_DAYS = 30
PRIMARY_METRIC = "MASE"
GUARDRAIL_METRIC = "RMSSE"
AGGREGATION_METHOD = "median_across_windows_per_entity_model_then_median_across_entities_per_model"

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


def _require_file(path) -> None:
    """Validate that a required input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required aggregation input missing: {path}")


def _load_mase() -> pd.DataFrame:
    """Load adjusted MASE scores from non-negative policy outputs."""

    _require_file(MASE_INPUT)
    mase = pd.read_csv(MASE_INPUT)
    required = {
        "entity_key",
        "window_id",
        "model_name",
        "forecast_rows",
        "mase",
        "denominator_floored",
    }
    missing = required.difference(mase.columns)
    if missing:
        raise ValueError(f"non_negative_mase_scores.csv missing columns: {sorted(missing)}")
    mase = mase.copy()
    mase["window_id"] = mase["window_id"].astype(int)
    mase["forecast_rows"] = mase["forecast_rows"].astype(int)
    mase["mase"] = pd.to_numeric(mase["mase"], errors="coerce")
    return mase[
        [
            "entity_key",
            "window_id",
            "model_name",
            "forecast_rows",
            "mase",
            "denominator_floored",
        ]
    ].rename(columns={"denominator_floored": "mase_denominator_floored"})


def _load_rmsse() -> pd.DataFrame:
    """Load adjusted RMSSE scores from non-negative policy outputs."""

    _require_file(RMSSE_INPUT)
    rmsse = pd.read_csv(RMSSE_INPUT)
    required = {
        "entity_key",
        "window_id",
        "model_name",
        "forecast_rows",
        "rmsse",
        "denominator_floored",
        "risk_status",
    }
    missing = required.difference(rmsse.columns)
    if missing:
        raise ValueError(
            f"non_negative_rmsse_scores.csv missing columns: {sorted(missing)}"
        )
    rmsse = rmsse.copy()
    rmsse["window_id"] = rmsse["window_id"].astype(int)
    rmsse["forecast_rows"] = rmsse["forecast_rows"].astype(int)
    rmsse["rmsse"] = pd.to_numeric(rmsse["rmsse"], errors="coerce")
    return rmsse[
        [
            "entity_key",
            "window_id",
            "model_name",
            "forecast_rows",
            "rmsse",
            "denominator_floored",
            "risk_status",
        ]
    ].rename(
        columns={
            "forecast_rows": "rmsse_forecast_rows",
            "denominator_floored": "rmsse_denominator_floored",
            "risk_status": "rmsse_risk_status",
        }
    )


def _load_valid_windows() -> pd.DataFrame:
    """Load valid backtesting windows for coverage validation."""

    _require_file(WINDOWS_INPUT)
    windows = pd.read_csv(WINDOWS_INPUT)
    required = {"entity_key", "window_id", "forecast_horizon_days"}
    missing = required.difference(windows.columns)
    if missing:
        raise ValueError(f"backtesting_windows.csv missing columns: {sorted(missing)}")
    windows = windows[windows["forecast_horizon_days"] == FORECAST_HORIZON_DAYS].copy()
    windows["window_id"] = windows["window_id"].astype(int)
    return windows[["entity_key", "window_id"]].drop_duplicates()


def _bool_series(series: pd.Series) -> pd.Series:
    """Normalize bool-like CSV values to booleans."""

    return series.astype(str).str.lower().isin(["true", "1"])


def _build_canonical(mase: pd.DataFrame, rmsse: pd.DataFrame, run_id: str, timestamp: str) -> pd.DataFrame:
    """Merge adjusted MASE and RMSSE into canonical entity/window/model scores."""

    merged = mase.merge(
        rmsse,
        on=["entity_key", "window_id", "model_name"],
        how="inner",
        validate="one_to_one",
    )
    if merged.empty:
        raise ValueError("No canonical rows after merging MASE and RMSSE.")
    if not (merged["forecast_rows"] == merged["rmsse_forecast_rows"]).all():
        raise ValueError("MASE/RMSSE forecast row counts do not match.")

    merged["run_id"] = run_id
    merged["mase_beats_naive"] = merged["mase"] < 1.0
    merged["mase_denominator_floored"] = _bool_series(
        merged["mase_denominator_floored"]
    )
    merged["rmsse_denominator_floored"] = _bool_series(
        merged["rmsse_denominator_floored"]
    )
    merged["created_timestamp"] = timestamp
    return merged[CANONICAL_COLUMNS].sort_values(
        ["entity_key", "window_id", "model_name"]
    )


def _aggregate_entity_model(canonical: pd.DataFrame, timestamp: str) -> pd.DataFrame:
    """Aggregate by entity/model across windows."""

    rows = []
    for (entity_key, model_name), group in canonical.groupby(
        ["entity_key", "model_name"], sort=True
    ):
        rows.append(
            {
                "entity_key": entity_key,
                "model_name": model_name,
                "windows": group["window_id"].nunique(),
                "median_mase": float(group["mase"].median()),
                "mean_mase": float(group["mase"].mean()),
                "p95_mase": float(group["mase"].quantile(0.95)),
                "median_rmsse": float(group["rmsse"].median()),
                "mean_rmsse": float(group["rmsse"].mean()),
                "p95_rmsse": float(group["rmsse"].quantile(0.95)),
                "pct_windows_beating_naive": float(group["mase_beats_naive"].mean()),
                "pct_windows_high_risk": float(
                    (group["rmsse_risk_status"] == "high_risk").mean()
                ),
                "mase_denominator_floored_rows": int(
                    group["mase_denominator_floored"].sum()
                ),
                "rmsse_denominator_floored_rows": int(
                    group["rmsse_denominator_floored"].sum()
                ),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=ENTITY_MODEL_COLUMNS)


def _aggregate_model(
    canonical: pd.DataFrame, entity_model: pd.DataFrame, timestamp: str
) -> pd.DataFrame:
    """Aggregate to model-level official scores with equal entity weighting."""

    rows = []
    for model_name, entity_group in entity_model.groupby("model_name", sort=True):
        window_group = canonical[canonical["model_name"] == model_name]
        rows.append(
            {
                "model_name": model_name,
                "entities": entity_group["entity_key"].nunique(),
                "windows": window_group[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "official_median_mase": float(entity_group["median_mase"].median()),
                "diagnostic_mean_mase": float(window_group["mase"].mean()),
                "diagnostic_p95_mase": float(window_group["mase"].quantile(0.95)),
                "official_median_rmsse": float(entity_group["median_rmsse"].median()),
                "diagnostic_mean_rmsse": float(window_group["rmsse"].mean()),
                "diagnostic_p95_rmsse": float(window_group["rmsse"].quantile(0.95)),
                "pct_entities_beating_naive": float(
                    (entity_group["median_mase"] < 1.0).mean()
                ),
                "pct_windows_beating_naive": float(window_group["mase_beats_naive"].mean()),
                "pct_entities_high_risk": float(
                    (entity_group["pct_windows_high_risk"] > 0).mean()
                ),
                "pct_windows_high_risk": float(
                    (window_group["rmsse_risk_status"] == "high_risk").mean()
                ),
                "mase_denominator_floored_rows": int(
                    window_group["mase_denominator_floored"].sum()
                ),
                "rmsse_denominator_floored_rows": int(
                    window_group["rmsse_denominator_floored"].sum()
                ),
                "created_timestamp": timestamp,
            }
        )
    return pd.DataFrame(rows, columns=MODEL_COLUMNS)


def _create_summary(
    canonical: pd.DataFrame,
    entity_model: pd.DataFrame,
    by_model: pd.DataFrame,
    run_id: str,
    timestamp: str,
) -> pd.DataFrame:
    """Create aggregation hierarchy summary."""

    return pd.DataFrame(
        [
            {
                "run_id": run_id,
                "entity_window_score_rows": len(canonical),
                "entity_model_rows": len(entity_model),
                "model_rows": len(by_model),
                "entities": canonical["entity_key"].nunique(),
                "windows": canonical[["entity_key", "window_id"]]
                .drop_duplicates()
                .shape[0],
                "models": canonical["model_name"].nunique(),
                "official_aggregation_method": AGGREGATION_METHOD,
                "primary_metric": PRIMARY_METRIC,
                "guardrail_metric": GUARDRAIL_METRIC,
                "created_timestamp": timestamp,
            }
        ],
        columns=SUMMARY_COLUMNS,
    )


def _policy_markdown(timestamp: str) -> str:
    """Return official aggregation policy documentation."""

    return f"""# Aggregation Policy - Stage 5.24

Created timestamp: {timestamp}

## Official Metrics

- MASE is the primary benchmark metric.
- RMSSE is guardrail only.
- Official scores use non-negative adjusted forecasts from Block 5.23.

## Official Model Score

The official model MASE is calculated with equal entity weighting:

1. For each entity/model, calculate the median MASE across that entity's windows.
2. For each model, calculate the median of those entity/model median MASE values across entities.

This is recorded as `official_median_mase`.

## RMSSE Guardrail Aggregation

RMSSE follows the same hierarchy:

1. For each entity/model, calculate the median RMSSE across that entity's windows.
2. For each model, calculate the median of those entity/model median RMSSE values across entities.

This is recorded as `official_median_rmsse`, but RMSSE remains a guardrail metric only.

## Diagnostics

Row-level means and p95 values are diagnostics only. They are not official model scores.

## Weighting Policy

Equal entity weighting is enforced. Entities with more windows do not dominate the global model score.

## Deferred Decisions

No champion is selected in this block. No ranking is created in this block. Final winner selection is deferred to later blocks.
"""


def _write_outputs(
    canonical: pd.DataFrame,
    entity_model: pd.DataFrame,
    by_model: pd.DataFrame,
    summary: pd.DataFrame,
    policy_text: str,
) -> None:
    """Write aggregation hierarchy outputs only."""

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    canonical.to_csv(CANONICAL_OUTPUT, index=False)
    entity_model.to_csv(ENTITY_MODEL_OUTPUT, index=False)
    by_model.to_csv(MODEL_OUTPUT, index=False)
    summary.to_csv(SUMMARY_OUTPUT, index=False)
    POLICY_OUTPUT.write_text(policy_text, encoding="utf-8")
    logger.info("Created %s with %s rows", CANONICAL_OUTPUT, len(canonical))
    logger.info("Created %s with %s rows", ENTITY_MODEL_OUTPUT, len(entity_model))
    logger.info("Created %s with %s rows", MODEL_OUTPUT, len(by_model))
    logger.info("Created %s with %s rows", SUMMARY_OUTPUT, len(summary))
    logger.info("Created %s", POLICY_OUTPUT)


def build_aggregation_hierarchy() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build official aggregation hierarchy tables."""

    logger.info("Stage 5.24 aggregation hierarchy build started")
    run_id = f"{RUN_ID_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    timestamp = datetime.now().isoformat(timespec="seconds")

    mase = _load_mase()
    rmsse = _load_rmsse()
    valid_windows = _load_valid_windows()
    canonical = _build_canonical(mase, rmsse, run_id, timestamp)
    entity_model = _aggregate_entity_model(canonical, timestamp)
    by_model = _aggregate_model(canonical, entity_model, timestamp)
    summary = _create_summary(canonical, entity_model, by_model, run_id, timestamp)

    expected_rows = len(valid_windows) * canonical["model_name"].nunique()
    logger.info("Canonical entity-window score rows: %s", len(canonical))
    logger.info("Expected canonical rows: %s", expected_rows)
    logger.info("Entity/model rows: %s", len(entity_model))
    logger.info("Model rows: %s", len(by_model))
    logger.info("Official aggregation: %s", AGGREGATION_METHOD)
    logger.info("No rankings, champions, winners, or tournament outputs created.")

    _write_outputs(
        canonical,
        entity_model,
        by_model,
        summary,
        _policy_markdown(timestamp),
    )
    logger.info("Stage 5.24 aggregation hierarchy build completed")
    return canonical, entity_model, by_model, summary


if __name__ == "__main__":
    build_aggregation_hierarchy()
