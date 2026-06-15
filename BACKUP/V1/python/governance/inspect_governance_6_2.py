"""Inspect Stage 06 Block 6.2 decision rules artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_governance_6_2")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules"

FILES = {
    "decision_action_framework": OUT_DIR / "decision_action_framework.csv",
    "risk_to_action_mapping": OUT_DIR / "risk_to_action_mapping.csv",
    "model_recommendation_rules": OUT_DIR / "model_recommendation_rules.csv",
    "governance_recommendations": OUT_DIR / "governance_recommendations.csv",
    "decision_rule_traceability": OUT_DIR / "decision_rule_traceability.csv",
    "decision_rules_validation": OUT_DIR / "decision_rules_validation.csv",
    "decision_rules_report": OUT_DIR / "decision_rules_report.md",
}

REQUIRED_ACTIONS = {
    "KEEP",
    "KEEP_WITH_CONDITIONS",
    "MONITOR",
    "REVIEW",
    "REVIEW_INVESTIGATE",
    "TEST_LATER",
    "DEFER",
    "EXCLUDE_FROM_CHAMPION_CONSIDERATION",
    "SURFACE_ON_DASHBOARD",
    "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER",
}
REQUIRED_RISKS = [f"R-{i:03d}" for i in range(1, 8)]
REQUIRED_MODELS = {
    "ARIMA_Fixed",
    "ETS_Current",
    "LinearRegression",
    "FixedGrowth_1_5",
    "FixedGrowth_3",
    "FixedGrowth_4",
    "FixedGrowth_6",
    "AutoARIMA",
    "Theta",
    "ETS Explicit",
    "LightGBM",
    "XGBoost",
    "FastNeuralAR_MLP",
    "NBEATS",
    "NHITS",
}

REQUIRED_COLUMNS = {
    "decision_action_framework": {
        "action_id",
        "action_name",
        "action_category",
        "definition",
        "trigger_conditions",
        "required_evidence",
        "governance_treatment",
        "dashboard_treatment",
        "manual_review_required",
        "terminal_or_transitional",
        "created_timestamp",
    },
    "risk_to_action_mapping": {
        "risk_id",
        "source_artifact",
        "risk_type",
        "model_name",
        "risk_description",
        "risk_level",
        "assigned_primary_action",
        "assigned_secondary_action",
        "action_rationale",
        "dashboard_carry_forward",
        "future_work_required",
        "review_trigger",
        "created_timestamp",
    },
    "model_recommendation_rules": {
        "rule_id",
        "rule_name",
        "applies_to",
        "input_condition",
        "required_evidence",
        "recommendation_action",
        "blocking_status",
        "manual_review_required",
        "dashboard_requirement",
        "created_timestamp",
    },
    "governance_recommendations": {
        "model_name",
        "model_origin",
        "model_family",
        "final_status",
        "selected_champion",
        "risk_flag",
        "eligible_for_champion",
        "governance_primary_action",
        "governance_secondary_action",
        "recommendation_summary",
        "dashboard_requirement",
        "future_review_trigger",
        "created_timestamp",
    },
    "decision_rule_traceability": {
        "trace_id",
        "output_artifact",
        "record_key",
        "source_artifact",
        "source_record_or_field",
        "trace_rationale",
        "created_timestamp",
    },
    "decision_rules_validation": {
        "check_name",
        "status",
        "details",
        "created_timestamp",
    },
}


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _bool_value(value: object) -> bool:
    return str(value).strip().lower() == "true"


def main() -> None:
    logger.info("=== Inspect Stage 06 Block 6.2 ===")
    checks = 0
    failures = 0

    def check(name: str, ok: bool, details: str = "") -> None:
        nonlocal checks, failures
        checks += 1
        if ok:
            logger.info("PASS: %s%s", name, f" - {details}" if details else "")
        else:
            failures += 1
            logger.error("FAIL: %s%s", name, f" - {details}" if details else "")

    check("output directory exists", OUT_DIR.exists(), str(OUT_DIR))
    for name, path in FILES.items():
        check(f"{name} exists", path.exists(), str(path))

    if failures:
        raise SystemExit(1)

    data = {name: _read(path) for name, path in FILES.items() if path.suffix == ".csv"}

    for name, columns in REQUIRED_COLUMNS.items():
        check(f"{name} required columns", columns.issubset(set(data[name].columns)))

    actions = set(data["decision_action_framework"]["action_name"])
    check("required actions exist", REQUIRED_ACTIONS.issubset(actions), str(sorted(actions)))

    risks = data["risk_to_action_mapping"]
    risk_ids = list(risks["risk_id"])
    check("R-001 through R-007 present exactly once", risk_ids == REQUIRED_RISKS, str(risk_ids))

    recs = data["governance_recommendations"]
    check("governance recommendations has exactly 15 models", len(recs) == 15, str(len(recs)))
    check("required model set present", set(recs["model_name"]) == REQUIRED_MODELS, str(sorted(recs["model_name"])))

    rec_by_model = recs.set_index("model_name")
    check(
        "ETS Explicit KEEP_WITH_CONDITIONS + MONITOR",
        rec_by_model.loc["ETS Explicit", "governance_primary_action"] == "KEEP_WITH_CONDITIONS"
        and rec_by_model.loc["ETS Explicit", "governance_secondary_action"] == "MONITOR",
    )
    check(
        "FastNeuralAR_MLP review/investigate and not champion eligible",
        rec_by_model.loc["FastNeuralAR_MLP", "governance_primary_action"] == "REVIEW_INVESTIGATE"
        and rec_by_model.loc["FastNeuralAR_MLP", "governance_secondary_action"] == "EXCLUDE_FROM_CHAMPION_CONSIDERATION"
        and not _bool_value(rec_by_model.loc["FastNeuralAR_MLP", "eligible_for_champion"]),
    )
    check(
        "NBEATS TEST_LATER / DEFER",
        rec_by_model.loc["NBEATS", "governance_primary_action"] == "TEST_LATER"
        and rec_by_model.loc["NBEATS", "governance_secondary_action"] == "DEFER",
    )
    check(
        "NHITS TEST_LATER / DEFER",
        rec_by_model.loc["NHITS", "governance_primary_action"] == "TEST_LATER"
        and rec_by_model.loc["NHITS", "governance_secondary_action"] == "DEFER",
    )
    check(
        "FixedGrowth_6 REVIEW / MONITOR",
        rec_by_model.loc["FixedGrowth_6", "governance_primary_action"] == "REVIEW"
        and rec_by_model.loc["FixedGrowth_6", "governance_secondary_action"] == "MONITOR",
    )

    validation = data["decision_rules_validation"]
    check("validation has no fail rows", not (validation["status"].astype(str).str.lower() == "fail").any())
    check("report exists and non-empty", FILES["decision_rules_report"].stat().st_size > 0)

    stage05_manifest = (
        PROJECT_ROOT
        / "outputs"
        / "model_lab"
        / "model_lab_closure_pack"
        / "model_lab_artifact_manifest.csv"
    )
    shiny = PROJECT_ROOT / "shiny_app"
    check("Stage 05 protected outputs present", stage05_manifest.exists(), str(stage05_manifest))
    check("Shiny path present and untouched by this block", shiny.exists(), str(shiny))

    logger.info("Inspection checks run: %s, failures: %s", checks, failures)
    if failures:
        raise SystemExit(1)
    logger.info("INSPECTION PASSED: governance 6.2 artifacts satisfy contract.")


if __name__ == "__main__":
    main()
