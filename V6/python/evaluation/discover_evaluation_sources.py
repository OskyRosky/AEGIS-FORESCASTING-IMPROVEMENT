"""Discover TESSERACT evaluation source tables for historical backtesting.

This Stage 4.2B script profiles known HDD metrics tables to determine whether
they contain precomputed metrics, historical ForecastVersions, and enough
actual/forecast linkage to support Stage 4.3. It performs discovery only.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd
import pyodbc

from ingestion.config import build_connection_string
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("discover_evaluation_sources")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "evaluation"
INVENTORY_OUTPUT = OUTPUT_DIR / "evaluation_source_inventory.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "evaluation_source_summary.txt"

TABLES_TO_INSPECT = [
    "forecast_substrateBE_hdd_region_metrics",
    "forecast_substrateBE_hdd_forest_metrics",
]

METRIC_COLUMN_HINTS = ("mape", "smape", "rmse", "mae", "bias", "accuracy")
DATE_COLUMN_HINTS = ("date", "time", "period", "horizon", "version")
ENTITY_COLUMN_HINTS = ("key", "entity", "region", "forest", "resource")
LINKAGE_COLUMN_HINTS = ("actual", "forecast", "prediction", "value")
FORECAST_VERSION_COLUMNS = ("ForecastVersion", "Forecast_Version")
MODEL_VERSION_COLUMNS = ("ModelVersion", "Model_Version")


@dataclass(frozen=True)
class TableProfile:
    """Container for one table's discovery results."""

    table_name: str
    exists: bool
    row_count: int | None
    columns: list[str]
    forecast_versions: list[str]
    model_versions: list[str]
    date_columns: list[str]
    entity_columns: list[str]
    metric_columns: list[str]
    linkage_columns: list[str]
    has_precomputed_metrics: bool
    has_historical_forecast_versions: bool
    has_actual_forecast_linkage: bool
    useful_for_backtesting: bool
    useful_for_metrics_validation: bool
    sample_rows: pd.DataFrame
    error: str | None = None


def _read_sql(connection: pyodbc.Connection, query: str) -> pd.DataFrame:
    """Read SQL into a DataFrame with a single pandas call site."""

    return pd.read_sql(query, connection)


def _table_columns(connection: pyodbc.Connection, table_name: str) -> list[str]:
    """Return ordered column names for a dbo table."""

    query = """
    SELECT COLUMN_NAME
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_SCHEMA = 'dbo'
      AND TABLE_NAME = ?
    ORDER BY ORDINAL_POSITION;
    """
    rows = connection.cursor().execute(query, table_name).fetchall()
    return [row[0] for row in rows]


def _row_count(connection: pyodbc.Connection, table_name: str) -> int:
    """Return table row count."""

    query = f"SELECT COUNT_BIG(*) FROM [TesseractEarthDW].[dbo].[{table_name}];"
    return int(connection.cursor().execute(query).fetchone()[0])


def _distinct_values(
    connection: pyodbc.Connection, table_name: str, column_name: str, limit: int = 200
) -> list[str]:
    """Return distinct values from a column for discovery summaries."""

    query = f"""
    SELECT DISTINCT TOP ({limit}) CAST([{column_name}] AS varchar(256)) AS value
    FROM [TesseractEarthDW].[dbo].[{table_name}]
    WHERE [{column_name}] IS NOT NULL
    ORDER BY value;
    """
    values = _read_sql(connection, query)["value"].dropna().astype(str).tolist()
    return values


def _top_rows(connection: pyodbc.Connection, table_name: str) -> pd.DataFrame:
    """Retrieve TOP 10 sample rows from a table."""

    query = f"SELECT TOP (10) * FROM [TesseractEarthDW].[dbo].[{table_name}];"
    return _read_sql(connection, query)


def _matching_columns(columns: list[str], hints: tuple[str, ...]) -> list[str]:
    """Find columns whose names contain any hint, case-insensitively."""

    matches = []
    for column in columns:
        lower_column = column.lower()
        if any(hint in lower_column for hint in hints):
            matches.append(column)
    return matches


def _first_existing_column(columns: list[str], candidates: tuple[str, ...]) -> str | None:
    """Return the first candidate column that exists in a table."""

    for candidate in candidates:
        if candidate in columns:
            return candidate
    return None


def _profile_table(connection: pyodbc.Connection, table_name: str) -> TableProfile:
    """Inspect one metrics table and infer its usefulness."""

    try:
        columns = _table_columns(connection, table_name)
        if not columns:
            return TableProfile(
                table_name=table_name,
                exists=False,
                row_count=None,
                columns=[],
                forecast_versions=[],
                model_versions=[],
                date_columns=[],
                entity_columns=[],
                metric_columns=[],
                linkage_columns=[],
                has_precomputed_metrics=False,
                has_historical_forecast_versions=False,
                has_actual_forecast_linkage=False,
                useful_for_backtesting=False,
                useful_for_metrics_validation=False,
                sample_rows=pd.DataFrame(),
                error="Table was not found in dbo schema.",
            )

        row_count = _row_count(connection, table_name)
        forecast_version_column = _first_existing_column(
            columns, FORECAST_VERSION_COLUMNS
        )
        model_version_column = _first_existing_column(columns, MODEL_VERSION_COLUMNS)
        forecast_versions = (
            _distinct_values(connection, table_name, forecast_version_column)
            if forecast_version_column
            else []
        )
        model_versions = (
            _distinct_values(connection, table_name, model_version_column)
            if model_version_column
            else []
        )
        sample_rows = _top_rows(connection, table_name)

        date_columns = _matching_columns(columns, DATE_COLUMN_HINTS)
        entity_columns = _matching_columns(columns, ENTITY_COLUMN_HINTS)
        metric_columns = _matching_columns(columns, METRIC_COLUMN_HINTS)
        linkage_columns = _matching_columns(columns, LINKAGE_COLUMN_HINTS)

        has_precomputed_metrics = bool(metric_columns)
        has_historical_forecast_versions = len(forecast_versions) > 1
        has_actual_forecast_linkage = any(
            column.lower() in {"actual", "actualvalue", "actual_value"}
            or "actual" in column.lower()
            for column in linkage_columns
        ) and any(
            "forecast" in column.lower() or "prediction" in column.lower()
            for column in linkage_columns
        )

        # Metrics tables can validate already-computed metrics. They support
        # reconstructing backtests only if they expose actual/forecast values.
        useful_for_metrics_validation = has_precomputed_metrics and row_count > 0
        useful_for_backtesting = (
            row_count > 0
            and has_historical_forecast_versions
            and bool(entity_columns)
            and bool(date_columns)
            and bool(model_versions)
            and has_actual_forecast_linkage
        )

        return TableProfile(
            table_name=table_name,
            exists=True,
            row_count=row_count,
            columns=columns,
            forecast_versions=forecast_versions,
            model_versions=model_versions,
            date_columns=date_columns,
            entity_columns=entity_columns,
            metric_columns=metric_columns,
            linkage_columns=linkage_columns,
            has_precomputed_metrics=has_precomputed_metrics,
            has_historical_forecast_versions=has_historical_forecast_versions,
            has_actual_forecast_linkage=has_actual_forecast_linkage,
            useful_for_backtesting=useful_for_backtesting,
            useful_for_metrics_validation=useful_for_metrics_validation,
            sample_rows=sample_rows,
        )
    except Exception as exc:
        logger.error("Failed to profile %s: %s", table_name, exc)
        return TableProfile(
            table_name=table_name,
            exists=False,
            row_count=None,
            columns=[],
            forecast_versions=[],
            model_versions=[],
            date_columns=[],
            entity_columns=[],
            metric_columns=[],
            linkage_columns=[],
            has_precomputed_metrics=False,
            has_historical_forecast_versions=False,
            has_actual_forecast_linkage=False,
            useful_for_backtesting=False,
            useful_for_metrics_validation=False,
            sample_rows=pd.DataFrame(),
            error=str(exc),
        )


def _join(values: list[str], limit: int | None = None) -> str:
    """Join values for compact CSV/text output."""

    selected = values if limit is None else values[:limit]
    suffix = "" if limit is None or len(values) <= limit else f";...(+{len(values) - limit})"
    return ";".join(str(value) for value in selected) + suffix


def _inventory_frame(profiles: list[TableProfile]) -> pd.DataFrame:
    """Convert profiles to one inventory row per table."""

    rows = []
    for profile in profiles:
        rows.append(
            {
                "table_name": profile.table_name,
                "exists": profile.exists,
                "row_count": profile.row_count,
                "column_count": len(profile.columns),
                "columns": _join(profile.columns),
                "forecast_version_count": len(profile.forecast_versions),
                "forecast_versions": _join(profile.forecast_versions, limit=25),
                "model_version_count": len(profile.model_versions),
                "model_versions": _join(profile.model_versions, limit=25),
                "date_columns": _join(profile.date_columns),
                "entity_columns": _join(profile.entity_columns),
                "metric_columns": _join(profile.metric_columns),
                "linkage_columns": _join(profile.linkage_columns),
                "has_precomputed_metrics": profile.has_precomputed_metrics,
                "has_historical_forecast_versions": profile.has_historical_forecast_versions,
                "has_actual_forecast_linkage": profile.has_actual_forecast_linkage,
                "useful_for_backtesting": profile.useful_for_backtesting,
                "useful_for_metrics_validation": profile.useful_for_metrics_validation,
                "error": profile.error,
            }
        )
    return pd.DataFrame(rows)


def _recommended_source(profiles: list[TableProfile]) -> str:
    """Choose the best available Stage 4.3 source from discovery results."""

    backtest_sources = [profile for profile in profiles if profile.useful_for_backtesting]
    if backtest_sources:
        return backtest_sources[0].table_name

    validation_sources = [
        profile for profile in profiles if profile.useful_for_metrics_validation
    ]
    if validation_sources:
        return (
            f"{validation_sources[0].table_name} for metrics validation only; "
            "no inspected table currently supports reconstructing raw backtests."
        )

    return "No recommended source identified from inspected tables."


def _write_summary(profiles: list[TableProfile], path: Path) -> None:
    """Write human-readable source discovery findings."""

    recommended_source = _recommended_source(profiles)
    lines = [
        "Stage 4.2B Evaluation Source Discovery",
        "",
        f"Recommended source for Stage 4.3: {recommended_source}",
        "",
    ]

    for profile in profiles:
        lines.extend(
            [
                f"Table: {profile.table_name}",
                f"Exists: {profile.exists}",
                f"Row count: {profile.row_count}",
                f"Columns: {_join(profile.columns)}",
                f"ForecastVersions available: {_join(profile.forecast_versions, limit=25)}",
                f"ModelVersions available: {_join(profile.model_versions, limit=25)}",
                f"Date-related columns: {_join(profile.date_columns)}",
                f"Entity columns: {_join(profile.entity_columns)}",
                f"Metric columns: {_join(profile.metric_columns)}",
                f"Actual/forecast linkage columns: {_join(profile.linkage_columns)}",
                f"Precomputed metrics present: {profile.has_precomputed_metrics}",
                f"Historical ForecastVersions present: {profile.has_historical_forecast_versions}",
                f"Actual/forecast linkage present: {profile.has_actual_forecast_linkage}",
                f"Useful for backtesting: {profile.useful_for_backtesting}",
                f"Useful for metrics validation: {profile.useful_for_metrics_validation}",
            ]
        )
        if profile.error:
            lines.append(f"Error: {profile.error}")

        lines.append("TOP 10 sample rows:")
        if profile.sample_rows.empty:
            lines.append("(no sample rows available)")
        else:
            lines.append(profile.sample_rows.to_string(index=False))
        lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")


def discover_evaluation_sources() -> pd.DataFrame:
    """Profile known evaluation tables and save inventory artifacts."""

    logger.info("Stage 4.2B evaluation source discovery started")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with pyodbc.connect(build_connection_string()) as connection:
        profiles = [_profile_table(connection, table) for table in TABLES_TO_INSPECT]

    inventory = _inventory_frame(profiles)
    inventory.to_csv(INVENTORY_OUTPUT, index=False)
    _write_summary(profiles, SUMMARY_OUTPUT)

    logger.info("Created %s with %s rows", INVENTORY_OUTPUT, len(inventory))
    logger.info("Created %s", SUMMARY_OUTPUT)
    logger.info("Recommended source for Stage 4.3: %s", _recommended_source(profiles))
    logger.info("Stage 4.2B evaluation source discovery completed")

    return inventory


if __name__ == "__main__":
    discover_evaluation_sources()
