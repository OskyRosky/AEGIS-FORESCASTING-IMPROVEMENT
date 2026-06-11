"""Build standardized Stage 4.1 data contract CSVs.

This module converts raw TESSERACT HDD Region exports into clean, reusable
processed files for later evaluation and visualization stages. It does not
calculate forecast errors, metrics, rankings, backtests, or model outputs.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROCESSED_DIR, RAW_DIR


logger = get_logger("build_data_contract")

ACTUALS_INPUT = RAW_DIR / "hdd_region_actuals.csv"
FORECASTS_INPUT = RAW_DIR / "hdd_region_forecasts.csv"

ACTUALS_OUTPUT = PROCESSED_DIR / "actuals.csv"
FORECASTS_OUTPUT = PROCESSED_DIR / "forecasts.csv"
COMPARISON_OUTPUT = PROCESSED_DIR / "forecast_comparison.csv"
ENTITIES_OUTPUT = PROCESSED_DIR / "entities.csv"
RUN_METADATA_OUTPUT = PROCESSED_DIR / "run_metadata.csv"

RAW_REQUIRED_COLUMNS = {
    "DateTime",
    "Key",
    "Value",
    "ModelVersion",
    "ForecastVersion",
    "Scenario",
    "Resource",
    "ValueType",
}

ACTUALS_COLUMNS = [
    "entity_key",
    "date",
    "actual_value",
    "forecast_version",
    "scenario",
    "resource",
    "source_file",
]

FORECASTS_COLUMNS = [
    "entity_key",
    "date",
    "forecast_value",
    "model_version",
    "forecast_version",
    "scenario",
    "resource",
    "value_type",
    "source_file",
]

COMPARISON_COLUMNS = [
    "entity_key",
    "date",
    "actual_value",
    "forecast_value",
    "model_version",
    "forecast_version",
    "scenario",
    "resource",
    "value_type",
    "horizon_days",
    "horizon_bucket",
]


def _require_input_file(path: Path) -> None:
    """Fail fast when a required raw input is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required input file does not exist: {path}")


def _require_columns(frame: pd.DataFrame, columns: set[str], label: str) -> None:
    """Validate that the expected TESSERACT raw columns are present."""

    missing_columns = sorted(columns - set(frame.columns))
    if missing_columns:
        raise ValueError(f"{label} is missing required columns: {missing_columns}")


def _to_contract_date(series: pd.Series) -> pd.Series:
    """Normalize raw timestamps to date values for contract joins."""

    return pd.to_datetime(series, errors="raise").dt.date


def _count_duplicates(frame: pd.DataFrame, subset: list[str]) -> int:
    """Count rows duplicated on a contract grain."""

    return int(frame.duplicated(subset=subset).sum())


def _horizon_bucket(horizon_days: int) -> str:
    """Bucket forecast horizon without calculating forecast accuracy metrics."""

    if horizon_days <= 90:
        return "short"
    if horizon_days <= 365:
        return "medium"
    if horizon_days <= 730:
        return "long"
    return "strategic"


def _build_actuals(raw_actuals: pd.DataFrame) -> pd.DataFrame:
    """Create the standardized actuals contract."""

    actuals = raw_actuals.rename(
        columns={
            "Key": "entity_key",
            "DateTime": "date",
            "Value": "actual_value",
            "ForecastVersion": "forecast_version",
        }
    )
    actuals = actuals[
        (actuals["ModelVersion"] == "actual") & (actuals["actual_value"] > 0)
    ].copy()
    actuals["date"] = _to_contract_date(actuals["date"])
    actuals["source_file"] = ACTUALS_INPUT.name

    duplicate_count = _count_duplicates(actuals, ["entity_key", "date"])
    logger.info("Actuals duplicate rows before cleanup: %s", duplicate_count)

    actuals = actuals.drop_duplicates(subset=["entity_key", "date"], keep="first")
    actuals = actuals.sort_values(["entity_key", "date"])
    actuals = actuals[
        [
            "entity_key",
            "date",
            "actual_value",
            "forecast_version",
            "Scenario",
            "Resource",
            "source_file",
        ]
    ].rename(columns={"Scenario": "scenario", "Resource": "resource"})

    logger.info(
        "Actuals duplicate rows after cleanup: %s",
        _count_duplicates(actuals, ["entity_key", "date"]),
    )
    return actuals[ACTUALS_COLUMNS]


def _build_forecasts(raw_forecasts: pd.DataFrame) -> pd.DataFrame:
    """Create the standardized forecasts contract."""

    forecasts = raw_forecasts.rename(
        columns={
            "Key": "entity_key",
            "DateTime": "date",
            "Value": "forecast_value",
            "ModelVersion": "model_version",
            "ForecastVersion": "forecast_version",
            "ValueType": "value_type",
        }
    )
    forecasts = forecasts[
        (forecasts["model_version"] != "actual")
        & (forecasts["value_type"] == "Forecast-Mean")
    ].copy()
    forecasts["date"] = _to_contract_date(forecasts["date"])
    forecasts["source_file"] = FORECASTS_INPUT.name

    duplicate_count = _count_duplicates(
        forecasts, ["entity_key", "date", "model_version"]
    )
    logger.info("Forecast duplicate rows before cleanup: %s", duplicate_count)

    forecasts = forecasts.drop_duplicates(
        subset=["entity_key", "date", "model_version"], keep="first"
    )
    forecasts = forecasts.sort_values(["entity_key", "model_version", "date"])
    forecasts = forecasts[
        [
            "entity_key",
            "date",
            "forecast_value",
            "model_version",
            "forecast_version",
            "Scenario",
            "Resource",
            "value_type",
            "source_file",
        ]
    ].rename(columns={"Scenario": "scenario", "Resource": "resource"})

    logger.info(
        "Forecast duplicate rows after cleanup: %s",
        _count_duplicates(forecasts, ["entity_key", "date", "model_version"]),
    )
    return forecasts[FORECASTS_COLUMNS]


def _build_comparison(actuals: pd.DataFrame, forecasts: pd.DataFrame) -> pd.DataFrame:
    """Create same-date forecast/actual comparison rows for later stages."""

    forecasts_with_horizon = forecasts.copy()
    first_dates = forecasts_with_horizon.groupby(
        ["entity_key", "model_version", "forecast_version"]
    )["date"].transform("min")
    forecasts_with_horizon["horizon_days"] = (
        pd.to_datetime(forecasts_with_horizon["date"])
        - pd.to_datetime(first_dates)
    ).dt.days
    forecasts_with_horizon["horizon_bucket"] = forecasts_with_horizon[
        "horizon_days"
    ].map(_horizon_bucket)

    comparison = forecasts_with_horizon.merge(
        actuals[["entity_key", "date", "actual_value"]],
        on=["entity_key", "date"],
        how="inner",
    )
    comparison = comparison[
        [
            "entity_key",
            "date",
            "actual_value",
            "forecast_value",
            "model_version",
            "forecast_version",
            "scenario",
            "resource",
            "value_type",
            "horizon_days",
            "horizon_bucket",
        ]
    ].sort_values(["entity_key", "model_version", "date"])

    if comparison.empty:
        logger.warning(
            "forecast_comparison.csv has zero rows after same-date join. "
            "This can happen when actuals end before the latest forecast run starts."
        )

    return comparison[COMPARISON_COLUMNS]


def _build_entities(actuals: pd.DataFrame, forecasts: pd.DataFrame) -> pd.DataFrame:
    """Create entity-level raw coverage inventory."""

    actual_summary = actuals.groupby("entity_key").agg(
        first_actual_date=("date", "min"),
        last_actual_date=("date", "max"),
        actual_rows=("date", "size"),
    )
    forecast_summary = forecasts.groupby("entity_key").agg(
        first_forecast_date=("date", "min"),
        last_forecast_date=("date", "max"),
        forecast_rows=("date", "size"),
        model_count=("model_version", "nunique"),
    )

    entities = actual_summary.join(forecast_summary, how="outer").reset_index()
    entities = entities[
        [
            "entity_key",
            "first_actual_date",
            "last_actual_date",
            "first_forecast_date",
            "last_forecast_date",
            "actual_rows",
            "forecast_rows",
            "model_count",
        ]
    ].sort_values("entity_key")

    count_columns = ["actual_rows", "forecast_rows", "model_count"]
    entities[count_columns] = entities[count_columns].fillna(0).astype(int)
    return entities


def _build_run_metadata(
    actuals: pd.DataFrame, forecasts: pd.DataFrame, comparison: pd.DataFrame
) -> pd.DataFrame:
    """Create one-row metadata describing the processed contract build."""

    forecast_versions = sorted(
        set(actuals["forecast_version"].dropna().astype(str))
        | set(forecasts["forecast_version"].dropna().astype(str))
    )
    notes = (
        "Stage 4.1 data contract build. Same-date actual/forecast comparison "
        "only; no errors, metrics, rankings, imputations, or shifted dates."
    )

    return pd.DataFrame(
        [
            {
                "run_timestamp": datetime.now().isoformat(timespec="seconds"),
                "forecast_version": ";".join(forecast_versions),
                "actual_rows": len(actuals),
                "forecast_rows": len(forecasts),
                "comparison_rows": len(comparison),
                "entity_count": actuals["entity_key"].nunique(),
                "model_count": forecasts["model_version"].nunique(),
                "first_actual_date": actuals["date"].min(),
                "last_actual_date": actuals["date"].max(),
                "first_forecast_date": forecasts["date"].min(),
                "last_forecast_date": forecasts["date"].max(),
                "notes": notes,
            }
        ]
    )


def _write_csv(frame: pd.DataFrame, path: Path) -> None:
    """Write a processed contract CSV and validate that it was created."""

    frame.to_csv(path, index=False)
    if not path.exists():
        raise RuntimeError(f"Processed output was not created: {path}")
    logger.info("Created %s with %s rows", path.name, len(frame))


def build_data_contract() -> None:
    """Build all Stage 4.1 processed contract outputs."""

    logger.info("Stage 4.1 data contract build started")
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    _require_input_file(ACTUALS_INPUT)
    _require_input_file(FORECASTS_INPUT)

    raw_actuals = pd.read_csv(ACTUALS_INPUT)
    raw_forecasts = pd.read_csv(FORECASTS_INPUT)
    _require_columns(raw_actuals, RAW_REQUIRED_COLUMNS, ACTUALS_INPUT.name)
    _require_columns(raw_forecasts, RAW_REQUIRED_COLUMNS, FORECASTS_INPUT.name)

    actuals = _build_actuals(raw_actuals)
    forecasts = _build_forecasts(raw_forecasts)
    comparison = _build_comparison(actuals, forecasts)
    entities = _build_entities(actuals, forecasts)
    run_metadata = _build_run_metadata(actuals, forecasts, comparison)

    _write_csv(actuals, ACTUALS_OUTPUT)
    _write_csv(forecasts, FORECASTS_OUTPUT)
    _write_csv(comparison, COMPARISON_OUTPUT)
    _write_csv(entities, ENTITIES_OUTPUT)
    _write_csv(run_metadata, RUN_METADATA_OUTPUT)

    logger.info("Comparison row count: %s", len(comparison))
    logger.info("Stage 4.1 data contract build completed")


if __name__ == "__main__":
    build_data_contract()
