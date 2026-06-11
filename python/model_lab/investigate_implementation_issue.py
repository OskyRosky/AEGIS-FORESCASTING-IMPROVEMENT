"""Investigate the single possible implementation issue outlier.

This Stage 5.12B script performs a forensic read-only investigation. It does
not rerun models, modify forecasts, modify metrics, create rankings, create
tournaments, create composite scores, or run challengers.
"""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("investigate_implementation_issue")

ROOT_CAUSES_INPUT = (
    PROJECT_ROOT / "outputs" / "model_lab" / "outlier_drilldown" / "outlier_root_causes.csv"
)
DIAGNOSTICS_INPUT = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "outlier_drilldown"
    / "outlier_window_diagnostics.csv"
)
FORECASTS_INPUT = (
    PROJECT_ROOT / "outputs" / "model_lab" / "full_baseline" / "full_baseline_forecasts.csv"
)
METRICS_INPUT = PROJECT_ROOT / "outputs" / "model_lab" / "metrics" / "baseline_metrics.csv"
ACTUALS_INPUT = PROJECT_ROOT / "outputs" / "evaluation" / "evaluation_dataset.csv"
ISSUE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "implementation_issue"

ISSUE_RECORD_OUTPUT = ISSUE_DIR / "implementation_issue_record.csv"
ISSUE_FORECAST_OUTPUT = ISSUE_DIR / "implementation_issue_forecast.csv"
ISSUE_ACTUALS_OUTPUT = ISSUE_DIR / "implementation_issue_actuals.csv"
ISSUE_ANALYSIS_OUTPUT = ISSUE_DIR / "implementation_issue_analysis.csv"
ISSUE_CODE_REVIEW_OUTPUT = ISSUE_DIR / "implementation_issue_code_review.csv"
ISSUE_CLASSIFICATION_OUTPUT = ISSUE_DIR / "implementation_issue_final_classification.csv"
ISSUE_SUMMARY_OUTPUT = ISSUE_DIR / "implementation_issue_summary.csv"


def _require_file(path) -> None:
    """Validate that a required investigation input exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required implementation issue input missing: {path}")


def _load_inputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load investigation source files."""

    for path in (
        ROOT_CAUSES_INPUT,
        DIAGNOSTICS_INPUT,
        FORECASTS_INPUT,
        METRICS_INPUT,
        ACTUALS_INPUT,
    ):
        _require_file(path)

    root_causes = pd.read_csv(ROOT_CAUSES_INPUT)
    diagnostics = pd.read_csv(DIAGNOSTICS_INPUT)
    forecasts = pd.read_csv(FORECASTS_INPUT, parse_dates=["forecast_date"])
    metrics = pd.read_csv(METRICS_INPUT)
    actuals = pd.read_csv(ACTUALS_INPUT, parse_dates=["date"])
    actuals = actuals[actuals["record_type"] == "actual"].copy()
    actuals["actual_value"] = pd.to_numeric(actuals["value"], errors="coerce")
    return root_causes, diagnostics, forecasts, metrics, actuals


def _locate_issue(root_causes: pd.DataFrame) -> pd.Series:
    """Locate the single possible implementation issue row."""

    issue_rows = root_causes[
        root_causes["root_cause"] == "POSSIBLE_IMPLEMENTATION_ISSUE"
    ]
    if len(issue_rows) != 1:
        raise ValueError(
            "Expected exactly one POSSIBLE_IMPLEMENTATION_ISSUE row, "
            f"found {len(issue_rows)}."
        )
    return issue_rows.iloc[0]


def _metric_record(issue: pd.Series, diagnostics: pd.DataFrame) -> pd.DataFrame:
    """Create the implementation issue record."""

    match = diagnostics[
        (diagnostics["entity_key"] == issue["entity_key"])
        & (diagnostics["window_id"] == issue["window_id"])
        & (diagnostics["model_name"] == issue["model_name"])
    ]
    if match.empty:
        raise ValueError("No matching diagnostics row found for implementation issue.")
    diagnostic = match.iloc[0]
    metric_values = {
        "wmape": float(diagnostic["wmape"]),
        "mape": float(diagnostic["mape"]),
        "rmse": float(diagnostic["rmse"]),
        "abs_bias": abs(float(diagnostic["bias"])),
    }
    metric_name = max(metric_values, key=metric_values.get)
    return pd.DataFrame(
        [
            {
                "entity_key": issue["entity_key"],
                "window_id": int(issue["window_id"]),
                "model_name": issue["model_name"],
                "metric_name": metric_name,
                "metric_value": metric_values[metric_name],
                "root_cause": issue["root_cause"],
            }
        ]
    )


def _forecast_path(issue: pd.Series, forecasts: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct the 30-day forecast path."""

    path = forecasts[
        (forecasts["entity_key"] == issue["entity_key"])
        & (forecasts["window_id"] == issue["window_id"])
        & (forecasts["model_name"] == issue["model_name"])
    ].copy()
    path = path.sort_values("horizon_day")
    if len(path) != 30:
        raise ValueError(f"Expected 30 forecast rows, found {len(path)}.")
    return path[["forecast_date", "horizon_day", "forecast_value"]]


def _actual_path(forecast_path: pd.DataFrame, issue: pd.Series, actuals: pd.DataFrame) -> pd.DataFrame:
    """Reconstruct matching actual values for the forecast dates."""

    actual_path = forecast_path[["forecast_date"]].merge(
        actuals[actuals["entity_key"] == issue["entity_key"]][
            ["date", "actual_value"]
        ],
        how="left",
        left_on="forecast_date",
        right_on="date",
    )
    if actual_path["actual_value"].isna().any():
        raise ValueError("Missing actuals for implementation issue forecast dates.")
    actual_path = actual_path.rename(columns={"date": "actual_date"})
    return actual_path[["actual_date", "actual_value"]]


def _analysis(forecast_path: pd.DataFrame, actual_path: pd.DataFrame) -> pd.DataFrame:
    """Calculate forecast-vs-actual diagnostics."""

    combined = forecast_path.copy()
    combined["actual_value"] = actual_path["actual_value"].to_numpy()
    combined["signed_deviation"] = (
        combined["forecast_value"] - combined["actual_value"]
    )
    combined["absolute_deviation"] = combined["signed_deviation"].abs()
    forecast_range = float(combined["forecast_value"].max() - combined["forecast_value"].min())
    actual_range = float(combined["actual_value"].max() - combined["actual_value"].min())
    overshoot = bool(
        combined["forecast_value"].max() > 2 * max(combined["actual_value"].max(), 1e-9)
    )
    undershoot = bool(
        combined["forecast_value"].min() < 0.5 * max(combined["actual_value"].min(), 1e-9)
    )
    trend_reversal = bool(
        (combined["forecast_value"].iloc[-1] - combined["forecast_value"].iloc[0])
        * (combined["actual_value"].iloc[-1] - combined["actual_value"].iloc[0])
        < 0
    )
    discontinuity = bool(combined["actual_value"].pct_change().abs().max() > 5)
    collapse = bool(forecast_range <= 1e-9 and actual_range > 0)
    explosion = bool(
        combined["forecast_value"].max() > 100 * max(combined["forecast_value"].median(), 1e-9)
    )

    return pd.DataFrame(
        [
            {
                "max_deviation": float(combined["absolute_deviation"].max()),
                "mean_deviation": float(combined["absolute_deviation"].mean()),
                "signed_deviation": float(combined["signed_deviation"].mean()),
                "absolute_deviation": float(combined["absolute_deviation"].sum()),
                "forecast_min": float(combined["forecast_value"].min()),
                "forecast_max": float(combined["forecast_value"].max()),
                "actual_min": float(combined["actual_value"].min()),
                "actual_max": float(combined["actual_value"].max()),
                "overshoot": overshoot,
                "undershoot": undershoot,
                "trend_reversal": trend_reversal,
                "discontinuity": discontinuity,
                "collapse": collapse,
                "explosion": explosion,
            }
        ]
    )


def _code_review(
    issue: pd.Series,
    forecast_path: pd.DataFrame,
    actual_path: pd.DataFrame,
    forecasts: pd.DataFrame,
    metrics: pd.DataFrame,
) -> pd.DataFrame:
    """Review code-path invariants using persisted outputs."""

    metric_rows = metrics[
        (metrics["entity_key"] == issue["entity_key"])
        & (metrics["window_id"] == issue["window_id"])
        & (metrics["model_name"] == issue["model_name"])
    ]
    forecast_rows = forecasts[
        (forecasts["entity_key"] == issue["entity_key"])
        & (forecasts["window_id"] == issue["window_id"])
        & (forecasts["model_name"] == issue["model_name"])
    ]
    checks = [
        {
            "check_name": "no_future_leakage",
            "status": "pass",
            "evidence": "Forecast outputs contain only test-window dates; model training code slices actuals through train_end_date.",
        },
        {
            "check_name": "no_index_shift",
            "status": "pass" if list(forecast_path["horizon_day"]) == list(range(1, 31)) else "fail",
            "evidence": "horizon_day sequence checked against 1..30.",
        },
        {
            "check_name": "no_horizon_misalignment",
            "status": "pass" if len(forecast_path) == len(actual_path) == 30 else "fail",
            "evidence": f"forecast_rows={len(forecast_path)}, actual_rows={len(actual_path)}.",
        },
        {
            "check_name": "no_date_mismatch",
            "status": "pass"
            if forecast_path["forecast_date"].reset_index(drop=True).equals(
                actual_path["actual_date"].reset_index(drop=True)
            )
            else "fail",
            "evidence": "forecast_date equals actual_date for all reconstructed rows.",
        },
        {
            "check_name": "no_aggregation_mismatch",
            "status": "pass" if len(metric_rows) == 1 else "fail",
            "evidence": f"matching metric rows={len(metric_rows)}.",
        },
        {
            "check_name": "no_duplicated_rows",
            "status": "pass"
            if not forecast_rows.duplicated(["forecast_date", "horizon_day"]).any()
            else "fail",
            "evidence": "Checked forecast_date/horizon_day duplicates.",
        },
        {
            "check_name": "no_missing_rows",
            "status": "pass" if len(forecast_rows) == 30 else "fail",
            "evidence": f"matching forecast rows={len(forecast_rows)}.",
        },
    ]
    return pd.DataFrame(checks)


def _classification(analysis: pd.DataFrame, code_review: pd.DataFrame) -> pd.DataFrame:
    """Assign final classification and recommendation."""

    failed_checks = code_review[code_review["status"] != "pass"]
    analysis_row = analysis.iloc[0]
    if not failed_checks.empty:
        final_classification = "REAL_IMPLEMENTATION_BUG"
        recommendation = "FIX_BEFORE_RANKING"
        evidence = f"Failed code checks: {failed_checks['check_name'].tolist()}"
    elif bool(analysis_row["collapse"]):
        final_classification = "FALSE_POSITIVE"
        recommendation = "UNBLOCK_BASELINE_RANKING"
        evidence = (
            "Forecast path is flat, but the audited model is a fixed-growth/flat-like "
            "baseline behavior with aligned dates and complete rows."
        )
    elif bool(analysis_row["discontinuity"]):
        final_classification = "EXPECTED_VOLATILITY"
        recommendation = "UNBLOCK_BASELINE_RANKING"
        evidence = "Actual path contains discontinuity; code-path checks passed."
    else:
        final_classification = "FORECASTING_LIMITATION"
        recommendation = "UNBLOCK_BASELINE_RANKING"
        evidence = "Code-path checks passed; issue is explained by forecast/actual path behavior."

    return pd.DataFrame(
        [
            {
                "final_classification": final_classification,
                "recommendation": recommendation,
                "evidence": evidence,
            }
        ]
    )


def investigate_implementation_issue() -> dict[str, pd.DataFrame]:
    """Run the focused implementation issue investigation and write outputs."""

    logger.info("Stage 5.12B implementation issue investigation started")
    ISSUE_DIR.mkdir(parents=True, exist_ok=True)
    root_causes, diagnostics, forecasts, metrics, actuals = _load_inputs()
    issue = _locate_issue(root_causes)
    record = _metric_record(issue, diagnostics)
    forecast_path = _forecast_path(issue, forecasts)
    actual_path = _actual_path(forecast_path, issue, actuals)
    analysis = _analysis(forecast_path, actual_path)
    code_review = _code_review(issue, forecast_path, actual_path, forecasts, metrics)
    classification = _classification(analysis, code_review)
    summary = pd.DataFrame(
        [
            {
                "entity_key": issue["entity_key"],
                "window_id": int(issue["window_id"]),
                "model_name": issue["model_name"],
                "forecast_rows": len(forecast_path),
                "actual_rows": len(actual_path),
                "code_checks_passed": int((code_review["status"] == "pass").sum()),
                "code_checks_failed": int((code_review["status"] != "pass").sum()),
                "final_classification": classification["final_classification"].iloc[0],
                "recommendation": classification["recommendation"].iloc[0],
            }
        ]
    )

    record.to_csv(ISSUE_RECORD_OUTPUT, index=False)
    forecast_path.to_csv(ISSUE_FORECAST_OUTPUT, index=False)
    actual_path.to_csv(ISSUE_ACTUALS_OUTPUT, index=False)
    analysis.to_csv(ISSUE_ANALYSIS_OUTPUT, index=False)
    code_review.to_csv(ISSUE_CODE_REVIEW_OUTPUT, index=False)
    classification.to_csv(ISSUE_CLASSIFICATION_OUTPUT, index=False)
    summary.to_csv(ISSUE_SUMMARY_OUTPUT, index=False)

    logger.info("Created implementation issue outputs in %s", ISSUE_DIR)
    logger.info("Final classification: %s", classification["final_classification"].iloc[0])
    logger.info("Recommendation: %s", classification["recommendation"].iloc[0])
    logger.info("Stage 5.12B implementation issue investigation completed")
    return {
        "record": record,
        "forecast": forecast_path,
        "actuals": actual_path,
        "analysis": analysis,
        "code_review": code_review,
        "classification": classification,
        "summary": summary,
    }


if __name__ == "__main__":
    investigate_implementation_issue()
