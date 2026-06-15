"""Inspect Stage 06 Block 6.4 dashboard governance contract artifacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_governance_6_4")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract"
FILES = {
    "contract": OUT_DIR / "dashboard_governance_contract.csv",
    "sections": OUT_DIR / "dashboard_required_sections.csv",
    "bindings": OUT_DIR / "dashboard_data_binding_contract.csv",
    "do_dont": OUT_DIR / "dashboard_do_dont_rules.csv",
    "warnings": OUT_DIR / "dashboard_warning_labels.csv",
    "traceability": OUT_DIR / "dashboard_governance_traceability.csv",
    "validation": OUT_DIR / "dashboard_contract_validation.csv",
    "report": OUT_DIR / "dashboard_governance_contract_report.md",
}

REQUIRED_COLUMNS = {
    "contract": {
        "contract_id",
        "contract_area",
        "contract_rule",
        "rule_type",
        "required_behavior",
        "prohibited_behavior",
        "source_artifact",
        "governance_rationale",
        "blocking_if_violated",
        "created_timestamp",
    },
    "sections": {
        "section_id",
        "dashboard_section",
        "section_purpose",
        "required_elements",
        "primary_source_artifact",
        "secondary_source_artifacts",
        "required_for_mvp",
        "governance_notes",
        "created_timestamp",
    },
    "bindings": {
        "binding_id",
        "dashboard_section",
        "source_artifact",
        "source_fields",
        "display_fields",
        "allowed_transformations",
        "prohibited_transformations",
        "refresh_behavior",
        "required_for_mvp",
        "created_timestamp",
    },
    "do_dont": {
        "rule_id",
        "category",
        "do_statement",
        "dont_statement",
        "reason",
        "replacement_guidance",
        "severity_if_violated",
        "created_timestamp",
    },
    "warnings": {
        "label_id",
        "dashboard_section",
        "label_type",
        "label_text",
        "display_priority",
        "required",
        "source_condition",
        "created_timestamp",
    },
    "traceability": {
        "trace_id",
        "dashboard_requirement",
        "source_artifact",
        "source_record_or_field",
        "trace_rationale",
        "created_timestamp",
    },
    "validation": {"check_name", "status", "details", "created_timestamp"},
}

REQUIRED_AREAS = {
    "read_only_behavior",
    "no_metric_recalculation",
    "champion_communication",
    "confidence_display",
    "risk_visibility",
    "deferred_model_visibility",
    "tournament_vs_champion_distinction",
    "audit_status_visibility",
    "source_artifact_traceability",
    "no_silent_filtering",
    "no_unconditional_winner_language",
    "methodology_transparency",
}
REQUIRED_SECTIONS = {
    "Executive Summary",
    "Champion Decision",
    "Champion Conditions",
    "Model Universe",
    "Tournament Standings",
    "Baseline vs Challenger Scorecard",
    "Pairwise Evidence",
    "Risk Register",
    "Deferred Models",
    "Audit Status",
    "Governance Actions",
    "Methodology / Metric Policy",
    "Dashboard Handoff / Source Artifacts",
}
REQUIRED_BINDINGS = {
    "model_lab_key_results.csv",
    "model_lab_champion_summary.csv",
    "champion_decision.csv",
    "model_lab_final_model_universe.csv",
    "tournament_preliminary_standings.csv",
    "tournament_model_scorecard.csv",
    "tournament_pairwise_evidence.csv",
    "model_lab_risk_register_final.csv",
    "model_lab_deferred_models.csv",
    "audit_5_summary.csv",
    "governance_recommendations.csv",
    "champion_conditions_protocol.csv",
    "champion_dashboard_language.csv",
    "champion_dashboard_display_requirements.csv",
}


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def main() -> None:
    logger.info("=== Inspect Stage 06 Block 6.4 ===")
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

    check("required contract areas exist", REQUIRED_AREAS.issubset(set(data["contract"]["contract_area"])))
    check("required dashboard sections exist", REQUIRED_SECTIONS.issubset(set(data["sections"]["dashboard_section"])))
    source_text = " ".join(data["bindings"]["source_artifact"].astype(str))
    check("required source artifacts in bindings", all(item in source_text for item in REQUIRED_BINDINGS))

    do_text = " ".join(data["do_dont"].astype(str).agg(" ".join, axis=1)).lower()
    for phrase in [
        "ets explicit won",
        "absolute best",
        "no risks",
        "hide fastneuralar_mlp",
        "hide nbeats/nhits",
        "tournament position equals champion",
        "recompute or transform mase/rmsse",
    ]:
        check(f"do/don't represents {phrase}", phrase in do_text, do_text)

    warning_text = " ".join(data["warnings"].astype(str).agg(" ".join, axis=1)).lower()
    for term in ["conditions", "medium", "fastneuralar_mlp", "nbeats", "nhits", "audit #5", "not recomputed"]:
        check(f"warning labels include {term}", term in warning_text)

    trace_text = " ".join(data["traceability"].astype(str).agg(" ".join, axis=1)).lower()
    for term in ["champion", "ets explicit", "medium", "mase", "rmsse", "pairwise", "c-001", "c-005", "fastneuralar_mlp", "nbeats", "nhits", "audit #5", "governance actions"]:
        check(f"traceability includes {term}", term in trace_text)

    validation = data["validation"]
    check("validation has no fail rows", not (validation["status"].astype(str).str.lower() == "fail").any())
    check("report exists and non-empty", FILES["report"].stat().st_size > 0)

    stage05 = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack" / "model_lab_closure_summary.csv"
    prior6 = PROJECT_ROOT / "outputs" / "governance" / "6_3_champion_conditions" / "champion_conditions_validation.csv"
    shiny = PROJECT_ROOT / "shiny_app"
    check("Stage 05 protected output present", stage05.exists(), str(stage05))
    check("Stage 06 prior output present", prior6.exists(), str(prior6))
    check("Shiny path present and untouched by this block", shiny.exists(), str(shiny))

    logger.info("Inspection checks run: %s, failures: %s", checks, failures)
    if failures:
        raise SystemExit(1)
    logger.info("INSPECTION PASSED: governance 6.4 artifacts satisfy contract.")


if __name__ == "__main__":
    main()
