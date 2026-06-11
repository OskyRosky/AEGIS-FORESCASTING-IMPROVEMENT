"""Inspect Stage 5.12B implementation issue investigation outputs."""

from __future__ import annotations

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT


logger = get_logger("inspect_implementation_issue")

ISSUE_DIR = PROJECT_ROOT / "outputs" / "model_lab" / "implementation_issue"
ISSUE_RECORD = ISSUE_DIR / "implementation_issue_record.csv"
ISSUE_FORECAST = ISSUE_DIR / "implementation_issue_forecast.csv"
ISSUE_ACTUALS = ISSUE_DIR / "implementation_issue_actuals.csv"
ISSUE_ANALYSIS = ISSUE_DIR / "implementation_issue_analysis.csv"
ISSUE_CODE_REVIEW = ISSUE_DIR / "implementation_issue_code_review.csv"
ISSUE_CLASSIFICATION = ISSUE_DIR / "implementation_issue_final_classification.csv"
ISSUE_SUMMARY = ISSUE_DIR / "implementation_issue_summary.csv"


def _require_file(path) -> None:
    """Validate that a required investigation output exists."""

    if not path.exists():
        raise FileNotFoundError(f"Required implementation issue output missing: {path}")


def inspect_implementation_issue() -> dict[str, pd.DataFrame]:
    """Inspect implementation issue outputs and validate evidence coverage."""

    for path in (
        ISSUE_RECORD,
        ISSUE_FORECAST,
        ISSUE_ACTUALS,
        ISSUE_ANALYSIS,
        ISSUE_CODE_REVIEW,
        ISSUE_CLASSIFICATION,
        ISSUE_SUMMARY,
    ):
        _require_file(path)

    record = pd.read_csv(ISSUE_RECORD)
    forecast = pd.read_csv(ISSUE_FORECAST)
    actuals = pd.read_csv(ISSUE_ACTUALS)
    analysis = pd.read_csv(ISSUE_ANALYSIS)
    code_review = pd.read_csv(ISSUE_CODE_REVIEW)
    classification = pd.read_csv(ISSUE_CLASSIFICATION)
    summary = pd.read_csv(ISSUE_SUMMARY)

    if len(record) != 1:
        raise ValueError("Expected exactly one implementation issue record.")
    if len(forecast) != 30:
        raise ValueError(f"Expected 30 forecast rows, found {len(forecast)}.")
    if len(actuals) != 30:
        raise ValueError(f"Expected 30 actual rows, found {len(actuals)}.")
    if (code_review["status"] != "pass").any():
        failed = code_review[code_review["status"] != "pass"]
        raise ValueError(f"Code review failed checks: {failed.to_dict('records')}")

    row = summary.iloc[0]
    final = classification.iloc[0]
    logger.info("Entity: %s", row["entity_key"])
    logger.info("Window: %s", int(row["window_id"]))
    logger.info("Model: %s", row["model_name"])
    logger.info("Forecast rows: %s", len(forecast))
    logger.info("Actual rows: %s", len(actuals))
    logger.info("Code checks passed: %s", int(row["code_checks_passed"]))
    logger.info("Code checks failed: %s", int(row["code_checks_failed"]))
    logger.info("Final classification: %s", final["final_classification"])
    logger.info("Recommendation: %s", final["recommendation"])
    logger.info("Stage 5.12B implementation issue inspection passed")
    return {
        "record": record,
        "forecast": forecast,
        "actuals": actuals,
        "analysis": analysis,
        "code_review": code_review,
        "classification": classification,
        "summary": summary,
    }


if __name__ == "__main__":
    inspect_implementation_issue()
