"""Block 5.29E - Challenger Metrics Inspector.

Read-only validation for challenger metrics artifacts.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_challenger_metrics")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
OUTPUT_DIR = MODEL_LAB_DIR / "challenger_metrics"
OFFICIAL_FORECAST_PATH = (
    MODEL_LAB_DIR / "challenger_official_execution" / "challenger_official_forecasts.csv"
)
DENOMINATOR_PATH = (
    MODEL_LAB_DIR / "denominator_reconciliation" / "training_only_denominators.csv"
)

FINAL_MODELS = {
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
}
EXPECTED_FORECAST_ROWS = 81720
EXPECTED_METRIC_ROWS = 2724
EXPECTED_PER_MODEL_FORECAST_ROWS = 13620
EXPECTED_PER_MODEL_METRIC_ROWS = 454
EXPECTED_HORIZON_DAYS = 30

REQUIRED_FILES = [
    "challenger_scoring_forecasts.csv",
    "challenger_actual_forecast_join.csv",
    "challenger_metrics_entity_window.csv",
    "challenger_negative_forecast_impact.csv",
    "challenger_metrics_by_model_diagnostic.csv",
    "challenger_metrics_validation.csv",
    "challenger_metrics_summary.csv",
    "challenger_metrics_report.md",
]
FORBIDDEN_OUTPUT_PATHS = [
    MODEL_LAB_DIR / "challenger_rankings",
    MODEL_LAB_DIR / "challenger_tournament",
    MODEL_LAB_DIR / "challenger_champion",
    MODEL_LAB_DIR / "tournament",
    MODEL_LAB_DIR / "champion",
]
PROTECTED_PATHS = [
    MODEL_LAB_DIR / "full_baseline",
    MODEL_LAB_DIR / "mase",
    MODEL_LAB_DIR / "rmsse",
    MODEL_LAB_DIR / "non_negative_policy",
    MODEL_LAB_DIR / "aggregation_hierarchy",
    MODEL_LAB_DIR / "statistical_significance",
    MODEL_LAB_DIR / "baseline_ranking",
    MODEL_LAB_DIR / "challenger_official_execution",
    MODEL_LAB_DIR / "challenger_model_set_rescope",
    MODEL_LAB_DIR / "challenger_official_execution_recovery",
    PROJECT_ROOT / "shiny_app",
]

_checks = 0
_failures: list[str] = []


def _check(condition: bool, message: str) -> None:
    global _checks
    _checks += 1
    if condition:
        logger.info("PASS: %s", message)
    else:
        logger.error("FAIL: %s", message)
        _failures.append(message)


def _bool_series(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().isin({"true", "1", "yes"})


def _path_has_files(path: Path) -> bool:
    return path.exists() and any(path.iterdir()) if path.is_dir() else path.exists()


def main() -> int:
    logger.info("=== Block 5.29E - Challenger Metrics Inspection ===")

    for filename in REQUIRED_FILES:
        _check((OUTPUT_DIR / filename).exists(), f"required challenger metrics file exists: {filename}")
    _check(OFFICIAL_FORECAST_PATH.exists(), "official challenger forecast input still exists")
    _check(DENOMINATOR_PATH.exists(), "training_only_denominators.csv exists")
    if _failures:
        return _finish()

    official_forecasts = pd.read_csv(OFFICIAL_FORECAST_PATH)
    scoring = pd.read_csv(OUTPUT_DIR / "challenger_scoring_forecasts.csv")
    joined = pd.read_csv(OUTPUT_DIR / "challenger_actual_forecast_join.csv")
    metrics = pd.read_csv(OUTPUT_DIR / "challenger_metrics_entity_window.csv")
    diagnostic = pd.read_csv(OUTPUT_DIR / "challenger_metrics_by_model_diagnostic.csv")
    validation = pd.read_csv(OUTPUT_DIR / "challenger_metrics_validation.csv")
    summary = pd.read_csv(OUTPUT_DIR / "challenger_metrics_summary.csv")

    _check(set(scoring["model_name"]) == FINAL_MODELS, "scoring forecasts include only final 6 challenger models")
    _check(set(joined["model_name"]) == FINAL_MODELS, "actual join includes only final 6 challenger models")
    _check(set(metrics["model_name"]) == FINAL_MODELS, "metrics include only final 6 challenger models")
    _check("NBEATS" not in set(metrics["model_name"]), "NBEATS excluded from metrics")
    _check("NHITS" not in set(metrics["model_name"]), "NHITS excluded from metrics")

    _check(len(official_forecasts) == EXPECTED_FORECAST_ROWS, "official forecast rows = 81,720")
    _check(len(scoring) == EXPECTED_FORECAST_ROWS, "scoring forecast rows = 81,720")
    _check(len(joined) == EXPECTED_FORECAST_ROWS, "actual join rows = 81,720")
    _check(len(metrics) == EXPECTED_METRIC_ROWS, "metric rows = 2,724")

    metric_counts = metrics.groupby("model_name").size().to_dict()
    _check(
        all(metric_counts.get(model, 0) == EXPECTED_PER_MODEL_METRIC_ROWS for model in FINAL_MODELS),
        "each model has 454 metric rows",
    )
    forecast_counts = scoring.groupby("model_name").size().to_dict()
    _check(
        all(forecast_counts.get(model, 0) == EXPECTED_PER_MODEL_FORECAST_ROWS for model in FINAL_MODELS),
        "each model has 13,620 forecast rows",
    )
    window_counts = scoring.groupby(["model_name", "entity_key", "window_id"]).size()
    _check((window_counts == EXPECTED_HORIZON_DAYS).all(), "forecast rows per model/entity-window = 30")

    _check((scoring["execution_mode"] == "official").all(), "scoring execution_mode = official")
    _check((joined["execution_mode"] == "official").all(), "actual join execution_mode = official")
    _check((metrics["execution_mode"] == "official").all(), "metric execution_mode = official")
    _check(not joined["actual_value"].isna().any(), "no missing actual values")
    _check(not scoring["adjusted_forecast_value"].isna().any(), "no missing adjusted forecast values")

    mase = pd.to_numeric(metrics["mase"], errors="coerce")
    rmsse = pd.to_numeric(metrics["rmsse"], errors="coerce")
    _check(not mase.isna().any(), "no NaN MASE")
    _check(not rmsse.isna().any(), "no NaN RMSSE")
    _check(np.isfinite(mase.to_numpy()).all(), "no Inf MASE")
    _check(np.isfinite(rmsse.to_numpy()).all(), "no Inf RMSSE")
    _check(
        summary.iloc[0]["mase_denominator_source"] == "training_only_lag1_naive_mae"
        and summary.iloc[0]["rmsse_denominator_source"] == "training_only_lag1_naive_mse",
        "denominators loaded from training_only_denominators.csv policy",
    )

    _check(not (validation["status"] == "fail").any(), "challenger_metrics_validation has no failed checks")
    _check(int(summary.iloc[0]["official_models"]) == 6, "summary official_models = 6")
    _check(int(summary.iloc[0]["forecast_rows"]) == EXPECTED_FORECAST_ROWS, "summary forecast_rows = 81,720")
    _check(int(summary.iloc[0]["joined_actual_rows"]) == EXPECTED_FORECAST_ROWS, "summary joined_actual_rows = 81,720")
    _check(int(summary.iloc[0]["metric_rows"]) == EXPECTED_METRIC_ROWS, "summary metric_rows = 2,724")
    _check(_bool_series(summary["metrics_created"]).all(), "metrics_created = true")
    for flag in [
        "aggregation_created",
        "significance_created",
        "rankings_created",
        "tournament_created",
        "champion_selected",
    ]:
        _check(not _bool_series(summary[flag]).any(), f"{flag} = false")

    ranking_like_columns = [
        c
        for frame in [metrics, diagnostic]
        for c in frame.columns
        if "rank" in c.lower() or "winner" in c.lower() or "champion" in c.lower()
    ]
    _check(not ranking_like_columns, f"no ranking/winner/champion columns ({ranking_like_columns or 'none'})")

    for path in FORBIDDEN_OUTPUT_PATHS:
        _check(not _path_has_files(path), f"no ranking/tournament/champion output path created: {path.name}")
    for path in PROTECTED_PATHS:
        _check(path.exists(), f"protected path still present: {path}")

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for failure in _failures:
            logger.error("  - %s", failure)
        return 1
    logger.info("INSPECTION PASSED: challenger metrics satisfy Block 5.29E contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
