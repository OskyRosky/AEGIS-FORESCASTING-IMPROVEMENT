"""Generate unified baseline metrics and rankings from official metrics exports.

This Stage 4.4 script normalizes official TESSERACT metrics CSVs and creates
baseline ranking outputs from already-computed official metrics. It does not
calculate new forecast metrics, train models, create forecasts, modify Shiny, or
change raw/processed datasets.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT, RAW_DIR


logger = get_logger("generate_baseline_metrics")

OUTPUT_DIR = PROJECT_ROOT / "outputs" / "metrics"
BASELINE_METRICS_OUTPUT = OUTPUT_DIR / "baseline_metrics.csv"
BASELINE_RANKINGS_OUTPUT = OUTPUT_DIR / "baseline_rankings.csv"

RAW_METRICS_FILES = [
    RAW_DIR / "hdd_region_metrics.csv",
    RAW_DIR / "hdd_forest_metrics.csv",
    RAW_DIR / "ssd_phx_lvwe_metrics.csv",
    RAW_DIR / "ssd_phx_lvne_metrics.csv",
]

BASELINE_COLUMNS = [
    "Key",
    "Forecast_Version",
    "Start_Date",
    "End_Date",
    "MAE",
    "RMSE",
    "Bias",
    "Bias_Pct",
    "MAPE",
    "SMAPE",
    "Accuracy",
    "source_file",
    "horizon_days",
    "horizon_bucket",
]

REQUIRED_COLUMNS = [
    "Key",
    "Forecast_Version",
    "Start_Date",
    "End_Date",
    "MAE",
    "RMSE",
    "Bias",
    "Bias_Pct",
    "MAPE",
    "SMAPE",
    "Accuracy",
]


def _require_input_file(path) -> None:
    """Fail fast when a required official metrics export is missing."""

    if not path.exists():
        raise FileNotFoundError(f"Required official metrics file missing: {path}")


def _require_columns(frame: pd.DataFrame, source_file: str) -> None:
    """Validate the normalized baseline source columns."""

    missing = [column for column in REQUIRED_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"{source_file} missing required columns: {missing}")


def _horizon_bucket(horizon_days: int) -> str:
    """Classify official metric rows by Start_Date to End_Date horizon."""

    if horizon_days <= 90:
        return "short"
    if horizon_days <= 365:
        return "medium"
    if horizon_days <= 730:
        return "long"
    return "strategic"


def _read_metrics_file(path) -> pd.DataFrame:
    """Read and normalize one official metrics CSV."""

    _require_input_file(path)
    frame = pd.read_csv(path)
    _require_columns(frame, path.name)

    normalized = frame[REQUIRED_COLUMNS].copy()
    normalized["source_file"] = path.name
    normalized["Start_Date"] = pd.to_datetime(normalized["Start_Date"], errors="raise")
    normalized["End_Date"] = pd.to_datetime(normalized["End_Date"], errors="raise")
    normalized["horizon_days"] = (
        normalized["End_Date"] - normalized["Start_Date"]
    ).dt.days
    normalized["horizon_bucket"] = normalized["horizon_days"].map(_horizon_bucket)

    return normalized[BASELINE_COLUMNS]


def _build_baseline_metrics() -> pd.DataFrame:
    """Build one unified baseline metrics DataFrame from all official exports."""

    frames = [_read_metrics_file(path) for path in RAW_METRICS_FILES]
    baseline = pd.concat(frames, ignore_index=True)
    baseline = baseline.sort_values(
        ["source_file", "Key", "Forecast_Version", "Start_Date", "End_Date"]
    )
    return baseline


def _build_rankings(baseline: pd.DataFrame) -> pd.DataFrame:
    """Rank Key and Forecast_Version groups using official baseline metrics."""

    rankings = (
        baseline.groupby(["Key", "Forecast_Version"], as_index=False)
        .agg(
            avg_mape=("MAPE", "mean"),
            avg_smape=("SMAPE", "mean"),
            avg_rmse=("RMSE", "mean"),
            avg_accuracy=("Accuracy", "mean"),
        )
        .sort_values(["avg_mape", "avg_accuracy"], ascending=[True, False])
    )

    rankings["model_rank_mape"] = rankings["avg_mape"].rank(
        method="dense", ascending=True
    ).astype(int)
    rankings["model_rank_accuracy"] = rankings["avg_accuracy"].rank(
        method="dense", ascending=False
    ).astype(int)

    return rankings[
        [
            "Key",
            "Forecast_Version",
            "model_rank_mape",
            "model_rank_accuracy",
            "avg_mape",
            "avg_smape",
            "avg_rmse",
            "avg_accuracy",
        ]
    ].sort_values(["model_rank_mape", "model_rank_accuracy", "Key"])


def _log_summary(baseline: pd.DataFrame, rankings: pd.DataFrame) -> None:
    """Log output coverage and top-ranked baseline groups."""

    logger.info("baseline_metrics.csv row count: %s", len(baseline))
    logger.info("baseline_metrics.csv unique Keys: %s", baseline["Key"].nunique())
    logger.info(
        "baseline_metrics.csv unique Forecast_Versions: %s",
        baseline["Forecast_Version"].nunique(),
    )
    logger.info(
        "Horizon bucket distribution: %s",
        baseline["horizon_bucket"].value_counts().to_dict(),
    )

    logger.info("Top 5 ranked baseline groups by MAPE:")
    for _, row in rankings.sort_values("model_rank_mape").head(5).iterrows():
        logger.info(
            "rank=%s Key=%s Forecast_Version=%s avg_mape=%.4f avg_accuracy=%.4f",
            row["model_rank_mape"],
            row["Key"],
            row["Forecast_Version"],
            row["avg_mape"],
            row["avg_accuracy"],
        )

    logger.info("Top 5 ranked baseline groups by Accuracy:")
    for _, row in rankings.sort_values("model_rank_accuracy").head(5).iterrows():
        logger.info(
            "rank=%s Key=%s Forecast_Version=%s avg_accuracy=%.4f avg_mape=%.4f",
            row["model_rank_accuracy"],
            row["Key"],
            row["Forecast_Version"],
            row["avg_accuracy"],
            row["avg_mape"],
        )


def generate_baseline_metrics() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Generate baseline metrics and ranking CSV outputs."""

    logger.info("Stage 4.4 baseline metrics generation started")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    baseline = _build_baseline_metrics()
    rankings = _build_rankings(baseline)

    baseline.to_csv(BASELINE_METRICS_OUTPUT, index=False)
    rankings.to_csv(BASELINE_RANKINGS_OUTPUT, index=False)

    logger.info("Created %s", BASELINE_METRICS_OUTPUT)
    logger.info("Created %s", BASELINE_RANKINGS_OUTPUT)
    _log_summary(baseline, rankings)
    logger.info("Stage 4.4 baseline metrics generation completed")

    return baseline, rankings


if __name__ == "__main__":
    generate_baseline_metrics()
