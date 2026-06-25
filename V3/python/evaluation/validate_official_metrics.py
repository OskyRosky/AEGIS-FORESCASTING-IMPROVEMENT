"""Validate official TESSERACT metrics CSV exports.

This Stage 4.3 script validates schema, coverage, duplicates, nulls, and metric
sanity for official exported metrics files. It does not calculate new metrics,
create rankings, modify processed datasets, or train models.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT, RAW_DIR


logger = get_logger("validate_official_metrics")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "metrics"
VALIDATION_OUTPUT = OUTPUT_DIR / "official_metrics_validation.csv"
SUMMARY_OUTPUT = OUTPUT_DIR / "official_metrics_validation_summary.txt"

METRICS_FILES = {
    "hdd_region_metrics.csv": RAW_DIR / "hdd_region_metrics.csv",
    "hdd_forest_metrics.csv": RAW_DIR / "hdd_forest_metrics.csv",
    "ssd_phx_lvwe_metrics.csv": RAW_DIR / "ssd_phx_lvwe_metrics.csv",
    "ssd_phx_lvne_metrics.csv": RAW_DIR / "ssd_phx_lvne_metrics.csv",
}

REQUIRED_COLUMNS = [
    "Key",
    "Count",
    "Mean_Actual",
    "Mean_Forecast",
    "MAE",
    "RMSE",
    "Bias",
    "Bias_Pct",
    "MAPE",
    "SMAPE",
    "Accuracy",
    "Forecast_Version",
    "Start_Date",
    "End_Date",
    "Execution_Date",
]

DUPLICATE_GRAIN = ["Key", "Forecast_Version", "Start_Date", "End_Date"]
NON_NEGATIVE_COLUMNS = ["MAPE", "SMAPE", "RMSE", "MAE"]


def _date_min_max(frame: pd.DataFrame, column: str) -> tuple[object, object]:
    """Return min/max for a date-like column."""

    values = pd.to_datetime(frame[column], errors="coerce")
    return values.min(), values.max()


def _count_required_nulls(frame: pd.DataFrame, columns: list[str]) -> dict[str, int]:
    """Count nulls in required columns that are present."""

    return {column: int(frame[column].isna().sum()) for column in columns}


def _metric_sanity_issues(frame: pd.DataFrame, columns: list[str]) -> dict[str, int]:
    """Count sanity violations without recalculating metrics."""

    issues: dict[str, int] = {}

    for column in NON_NEGATIVE_COLUMNS:
        if column in columns:
            issues[f"{column}_negative_count"] = int((frame[column] < 0).sum())

    if "Accuracy" in columns:
        accuracy = frame["Accuracy"].dropna()
        issues["accuracy_out_of_range_count"] = int(
            ((accuracy < 0) | (accuracy > 100)).sum()
        )

    if "Count" in columns:
        issues["count_non_positive_count"] = int((frame["Count"] <= 0).sum())

    return issues


def _validate_file(source_file: str, path) -> dict[str, object]:
    """Validate one official metrics CSV and return a summary row."""

    if not path.exists():
        logger.error("Missing metrics file: %s", path)
        return {
            "source_file": source_file,
            "file_exists": False,
            "row_count": 0,
            "column_count": 0,
            "unique_keys": 0,
            "forecast_versions": "",
            "forecast_version_count": 0,
            "start_date_min": "",
            "start_date_max": "",
            "end_date_min": "",
            "end_date_max": "",
            "missing_required_columns": ";".join(REQUIRED_COLUMNS),
            "null_counts_required_columns": "",
            "duplicate_grain_rows": 0,
            "schema_valid": False,
            "metric_sanity_issue_count": 0,
            "metric_sanity_issues": "file_missing",
            "ready_for_stage_4_4": False,
        }

    frame = pd.read_csv(path)
    columns = list(frame.columns)
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in columns]
    present_required_columns = [
        column for column in REQUIRED_COLUMNS if column in columns
    ]
    null_counts = _count_required_nulls(frame, present_required_columns)

    duplicate_rows = 0
    if all(column in columns for column in DUPLICATE_GRAIN):
        duplicate_rows = int(frame.duplicated(subset=DUPLICATE_GRAIN).sum())

    sanity_issues = _metric_sanity_issues(frame, columns)
    sanity_issue_count = int(sum(sanity_issues.values()))

    start_min, start_max = ("", "")
    if "Start_Date" in columns:
        start_min, start_max = _date_min_max(frame, "Start_Date")

    end_min, end_max = ("", "")
    if "End_Date" in columns:
        end_min, end_max = _date_min_max(frame, "End_Date")

    forecast_versions = []
    if "Forecast_Version" in columns:
        forecast_versions = sorted(
            frame["Forecast_Version"].dropna().astype(str).unique().tolist()
        )

    schema_valid = not missing_columns
    ready_for_stage_4_4 = schema_valid and sanity_issue_count == 0

    logger.info("%s rows: %s", source_file, len(frame))
    logger.info("%s missing required columns: %s", source_file, missing_columns)
    logger.info("%s duplicate grain rows: %s", source_file, duplicate_rows)
    logger.info("%s metric sanity issue count: %s", source_file, sanity_issue_count)

    return {
        "source_file": source_file,
        "file_exists": True,
        "row_count": len(frame),
        "column_count": len(columns),
        "unique_keys": frame["Key"].nunique() if "Key" in columns else 0,
        "forecast_versions": ";".join(forecast_versions),
        "forecast_version_count": len(forecast_versions),
        "start_date_min": start_min,
        "start_date_max": start_max,
        "end_date_min": end_min,
        "end_date_max": end_max,
        "missing_required_columns": ";".join(missing_columns),
        "null_counts_required_columns": ";".join(
            f"{column}={count}" for column, count in null_counts.items()
        ),
        "duplicate_grain_rows": duplicate_rows,
        "schema_valid": schema_valid,
        "metric_sanity_issue_count": sanity_issue_count,
        "metric_sanity_issues": ";".join(
            f"{name}={count}" for name, count in sanity_issues.items()
        ),
        "ready_for_stage_4_4": ready_for_stage_4_4,
    }


def _write_summary(validation: pd.DataFrame) -> None:
    """Write a concise text summary of validation results."""

    all_schema_valid = bool(validation["schema_valid"].all())
    any_metric_sanity_issues = bool(
        (validation["metric_sanity_issue_count"] > 0).any()
    )
    all_ready = bool(validation["ready_for_stage_4_4"].all())

    lines = [
        "Stage 4.3 Official Metrics Validation Summary",
        "",
        f"All files passed schema validation: {all_schema_valid}",
        f"Any metric sanity issues exist: {any_metric_sanity_issues}",
        f"Files ready for Stage 4.4: {all_ready}",
        "",
        "Per-file results:",
    ]

    for _, row in validation.iterrows():
        lines.extend(
            [
                f"- {row['source_file']}",
                f"  rows: {row['row_count']}",
                f"  columns: {row['column_count']}",
                f"  unique Keys: {row['unique_keys']}",
                f"  Forecast_Version values: {row['forecast_versions']}",
                f"  Start_Date range: {row['start_date_min']} to {row['start_date_max']}",
                f"  End_Date range: {row['end_date_min']} to {row['end_date_max']}",
                f"  missing required columns: {row['missing_required_columns']}",
                f"  duplicate grain rows: {row['duplicate_grain_rows']}",
                f"  metric sanity issue count: {row['metric_sanity_issue_count']}",
            ]
        )

    if all_ready:
        recommendation = (
            "Proceed to Stage 4.4 using the official metrics files as validated "
            "baseline inputs."
        )
    else:
        recommendation = (
            "Review schema, duplicate, null, or sanity issues before Stage 4.4."
        )

    lines.extend(["", f"Recommended next step: {recommendation}"])
    SUMMARY_OUTPUT.write_text("\n".join(lines), encoding="utf-8")


def validate_official_metrics() -> pd.DataFrame:
    """Validate all official metrics CSV exports."""

    logger.info("Stage 4.3 official metrics validation started")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    rows = [
        _validate_file(source_file, path)
        for source_file, path in METRICS_FILES.items()
    ]
    validation = pd.DataFrame(rows)
    validation.to_csv(VALIDATION_OUTPUT, index=False)
    _write_summary(validation)

    logger.info("Created %s with %s rows", VALIDATION_OUTPUT, len(validation))
    logger.info("Created %s", SUMMARY_OUTPUT)
    logger.info("Stage 4.3 official metrics validation completed")
    return validation


if __name__ == "__main__":
    validate_official_metrics()
