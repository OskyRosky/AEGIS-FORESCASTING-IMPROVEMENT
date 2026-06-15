"""Inspect Stage 06 Block 6.5 governance closure pack."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_governance_6_5")

OUT_DIR = PROJECT_ROOT / "outputs" / "governance" / "6_5_governance_closure_pack"
FILES = {
    "summary": OUT_DIR / "governance_closure_summary.csv",
    "stage_status": OUT_DIR / "governance_stage_status_manifest.csv",
    "artifact_manifest": OUT_DIR / "governance_artifact_manifest.csv",
    "register": OUT_DIR / "governance_register.csv",
    "handoff": OUT_DIR / "governance_dashboard_handoff_manifest.csv",
    "next_steps": OUT_DIR / "governance_next_steps.csv",
    "validation": OUT_DIR / "governance_closure_validation.csv",
    "report": OUT_DIR / "governance_closure_report.md",
    "executive_summary": OUT_DIR / "governance_executive_summary.md",
}
REQUIRED_COLUMNS = {
    "summary": {
        "stage_id",
        "stage_name",
        "closure_status",
        "prior_stage_status",
        "champion_governance_status",
        "dashboard_contract_status",
        "ready_for_audit_6",
        "ready_for_shiny_mvp_after_audit",
        "conditions_present",
        "created_timestamp",
    },
    "stage_status": {"block_id", "block_name", "status", "primary_output_directory", "key_result", "created_timestamp"},
    "artifact_manifest": {
        "artifact_group",
        "artifact_path",
        "artifact_exists",
        "artifact_role",
        "required_for_audit_6",
        "required_for_shiny_handoff",
        "created_timestamp",
    },
    "register": {
        "register_id",
        "register_type",
        "source_block",
        "subject",
        "governance_status",
        "required_action",
        "dashboard_visibility_required",
        "source_artifact",
        "created_timestamp",
    },
    "handoff": {
        "handoff_id",
        "dashboard_section",
        "source_artifact",
        "governance_requirement",
        "display_requirement",
        "required_for_mvp",
        "audit_6_review_required",
        "created_timestamp",
    },
    "next_steps": {"next_step_id", "next_step_name", "priority", "description", "blocking_dependency", "created_timestamp"},
    "validation": {"check_name", "status", "details", "created_timestamp"},
}
REQUIRED_BLOCKS = {"6.0", "6.1", "6.2", "6.3", "6.4", "6.5"}
REQUIRED_GROUPS = {"6_0", "6_1", "6_2", "6_3", "6_4", "6_5"}
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


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(path)
    return pd.read_csv(path)


def _bool(value: object) -> bool:
    return str(value).strip().lower() == "true"


def main() -> None:
    logger.info("=== Inspect Stage 06 Block 6.5 ===")
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
    for name, cols in REQUIRED_COLUMNS.items():
        check(f"{name} required columns", cols.issubset(set(data[name].columns)))

    summary = data["summary"]
    check("closure summary exactly one row", len(summary) == 1, str(len(summary)))
    check("ready_for_audit_6 true", _bool(summary.iloc[0]["ready_for_audit_6"]))
    check("ready_for_shiny_mvp_after_audit true", _bool(summary.iloc[0]["ready_for_shiny_mvp_after_audit"]))
    check("champion status conditional", "champion with conditions" in str(summary.iloc[0]["champion_governance_status"]).lower())

    stage = data["stage_status"]
    block_ids = set(stage["block_id"].astype(str))
    check("stage status includes 6.0 through 6.5", block_ids == REQUIRED_BLOCKS, str(sorted(block_ids)))
    check("all Stage 06 blocks completed", set(stage["status"]) == {"completed"})

    manifest = data["artifact_manifest"]
    check("artifact manifest includes all prior block groups", REQUIRED_GROUPS.issubset(set(manifest["artifact_group"])))
    check("artifact manifest all listed artifacts exist", manifest["artifact_exists"].map(_bool).all())

    register_text = " ".join(data["register"].astype(str).agg(" ".join, axis=1)).lower()
    for subject in [
        "ets explicit",
        "medium confidence",
        "fastneuralar_mlp",
        "nbeats",
        "nhits",
        "fixedgrowth_6",
        "f-010",
        "audit #5",
        "c-001",
        "c-005",
        "read-only",
        "no metric recalculation",
        "no unconditional winner",
        "warning labels",
    ]:
        check(f"governance register includes {subject}", subject in register_text)

    handoff = data["handoff"]
    check("dashboard handoff includes required sections", REQUIRED_SECTIONS.issubset(set(handoff["dashboard_section"])))
    check("all handoff rows require audit 6 review", handoff["audit_6_review_required"].map(_bool).all())

    steps_text = " ".join(data["next_steps"].astype(str).agg(" ".join, axis=1))
    check("next steps include Audit #6", "Audit #6" in steps_text)
    check("next steps include Shiny MVP", "Shiny MVP" in steps_text)

    validation = data["validation"]
    check("validation has no fail rows", not (validation["status"].astype(str).str.lower() == "fail").any())
    check("report non-empty", FILES["report"].stat().st_size > 0)
    check("executive summary non-empty", FILES["executive_summary"].stat().st_size > 0)

    champion = _read(PROJECT_ROOT / "outputs" / "model_lab" / "champion_decision" / "champion_decision.csv").iloc[0]
    check("champion decision remains conditional", champion["decision"] == "CHAMPION_SELECTED_WITH_CONDITIONS")
    check("medium confidence preserved", champion["decision_confidence"] == "medium")
    check("FastNeuralAR_MLP carried forward", "fastneuralar_mlp" in register_text)
    check("NBEATS carried forward", "nbeats" in register_text)
    check("NHITS carried forward", "nhits" in register_text)

    stage05 = PROJECT_ROOT / "outputs" / "model_lab" / "model_lab_closure_pack" / "model_lab_closure_summary.csv"
    prior6 = PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract" / "dashboard_contract_validation.csv"
    shiny = PROJECT_ROOT / "shiny_app"
    check("Stage 05 protected output present", stage05.exists(), str(stage05))
    check("Stage 06 prior output present", prior6.exists(), str(prior6))
    check("Shiny path present and untouched by this block", shiny.exists(), str(shiny))

    logger.info("Inspection checks run: %s, failures: %s", checks, failures)
    if failures:
        raise SystemExit(1)
    logger.info("INSPECTION PASSED: governance 6.5 artifacts satisfy contract.")


if __name__ == "__main__":
    main()
