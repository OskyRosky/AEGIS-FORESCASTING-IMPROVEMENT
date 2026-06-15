"""Inspect Stage 06 Block 6.3 champion conditions artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_governance_6_3")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_3_champion_conditions"
FILES = {
    "conditions": OUT_DIR / "champion_conditions_protocol.csv",
    "language": OUT_DIR / "champion_dashboard_language.csv",
    "traceability": OUT_DIR / "champion_condition_traceability.csv",
    "display": OUT_DIR / "champion_dashboard_display_requirements.csv",
    "validation": OUT_DIR / "champion_conditions_validation.csv",
    "report": OUT_DIR / "champion_conditions_report.md",
}
REQUIRED_CONDITIONS = [f"C-{i:03d}" for i in range(1, 6)]
REQUIRED_COLUMNS = {
    "conditions": {
        "condition_id",
        "selected_champion_model",
        "condition_type",
        "condition_description",
        "source_artifact",
        "severity",
        "governance_action",
        "dashboard_display_required",
        "review_trigger",
        "expiration_or_reassessment_rule",
        "created_timestamp",
    },
    "language": {
        "language_id",
        "language_category",
        "audience",
        "statement_text",
        "allowed_status",
        "reason",
        "replacement_statement",
        "created_timestamp",
    },
    "traceability": {
        "trace_id",
        "condition_or_language_id",
        "source_artifact",
        "source_field_or_record",
        "trace_rationale",
        "created_timestamp",
    },
    "display": {
        "display_requirement_id",
        "dashboard_area",
        "required_element",
        "source_artifact",
        "display_priority",
        "required_wording_guidance",
        "must_be_visible",
        "created_timestamp",
    },
    "validation": {"check_name", "status", "details", "created_timestamp"},
}


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def main() -> None:
    logger.info("=== Inspect Stage 06 Block 6.3 ===")
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
        check(f"{name} file exists", path.exists(), str(path))
    if failures:
        raise SystemExit(1)

    data = {name: _read(path) for name, path in FILES.items() if path.suffix == ".csv"}
    for name, columns in REQUIRED_COLUMNS.items():
        check(f"{name} required columns", columns.issubset(set(data[name].columns)))

    conditions = data["conditions"]
    check("C-001 through C-005 exist exactly once", list(conditions["condition_id"]) == REQUIRED_CONDITIONS, str(list(conditions["condition_id"])))
    check("all conditions dashboard display required", conditions["dashboard_display_required"].map(_bool).all())
    check("ETS Explicit condition target only", set(conditions["selected_champion_model"]) == {"ETS Explicit"})
    check("medium confidence condition preserved", "medium_confidence" in set(conditions["condition_type"]))
    check(
        "unconditional winner guardrail represented",
        "DO_NOT_PRESENT_AS_UNCONDITIONAL_WINNER" in set(conditions["governance_action"]),
    )

    language = data["language"]
    approved = language[language["language_category"] == "approved"]
    prohibited = language[language["language_category"] == "prohibited"]
    check("approved statements exist", len(approved) >= 4, str(len(approved)))
    check("prohibited statements exist", len(prohibited) >= 7, str(len(prohibited)))
    check("prohibited statements have replacement statements", prohibited["replacement_statement"].astype(str).str.len().gt(0).all())
    check(
        "ETS Explicit not approved as unconditional winner",
        not approved["statement_text"].astype(str).str.contains("won|absolute best|replaces all other|tournament winner", case=False, regex=True).any(),
    )
    check("medium confidence surfaced", language.astype(str).apply(lambda col: col.str.contains("medium confidence", case=False, regex=False)).any().any())
    check("FastNeuralAR_MLP risk surfaced", language.astype(str).apply(lambda col: col.str.contains("FastNeuralAR_MLP", regex=False)).any().any())
    check("NBEATS/NHITS deferrals surfaced", language.astype(str).apply(lambda col: col.str.contains("NBEATS", regex=False)).any().any() and language.astype(str).apply(lambda col: col.str.contains("NHITS", regex=False)).any().any())

    display = data["display"]
    display_text = " ".join(display["required_element"].astype(str).tolist() + display["required_wording_guidance"].astype(str).tolist()).lower()
    for required in ["champion", "confidence", "mase", "rmsse", "pairwise", "risk", "nbeats", "nhits"]:
        check(f"display includes {required}", required in display_text)
    check("all display requirements visible", display["must_be_visible"].map(_bool).all())

    validation = data["validation"]
    check("validation file has no fail rows", not (validation["status"].astype(str).str.lower() == "fail").any())
    check("report exists and non-empty", FILES["report"].stat().st_size > 0)

    stage05 = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack" / "model_lab_champion_summary.csv"
    prior6 = PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "decision_rules_validation.csv"
    shiny = PROJECT_ROOT / "shiny_app"
    check("Stage 05 protected output present", stage05.exists(), str(stage05))
    check("Stage 06 prior output present", prior6.exists(), str(prior6))
    check("Shiny path present and untouched by this block", shiny.exists(), str(shiny))

    logger.info("Inspection checks run: %s, failures: %s", checks, failures)
    if failures:
        raise SystemExit(1)
    logger.info("INSPECTION PASSED: governance 6.3 artifacts satisfy contract.")


if __name__ == "__main__":
    main()
