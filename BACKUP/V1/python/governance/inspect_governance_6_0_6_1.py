"""Inspector for Stage 06 Blocks 6.0 and 6.1 governance artifacts."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("inspect_governance_6_0_6_1")

GOV_ROOT = PROJECT_ROOT / "outputs" / "governance"
OUT_60 = GOV_ROOT / "6_0_audit5_finding_resolution"
OUT_61 = GOV_ROOT / "6_1_governance_foundation"
STAGE05_MANIFEST = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "model_lab_closure_pack"
    / "model_lab_artifact_manifest.csv"
)
F010_ARTIFACT = (
    PROJECT_ROOT
    / "outputs"
    / "model_lab"
    / "model_lab_closure_pack"
    / "model_lab_closure_summary.csv"
)

REQUIRED_FILES = [
    OUT_60 / "audit5_finding_resolution.csv",
    OUT_60 / "governed_manifest_correction.csv",
    OUT_60 / "audit5_finding_resolution_report.md",
    OUT_61 / "governance_definitions.csv",
    OUT_61 / "governance_status_taxonomy.csv",
    OUT_61 / "governance_foundation_report.md",
    OUT_61 / "governance_6_0_6_1_validation.csv",
]
REQUIRED_RESOLUTION_COLUMNS = {
    "resolution_id",
    "source_audit",
    "source_finding_id",
    "severity",
    "finding_area",
    "finding_summary",
    "original_artifact_path",
    "manifest_recorded_value",
    "verified_disk_value",
    "governed_interpretation",
    "stage_05_file_edited",
    "correction_type",
    "blocking_status",
    "rationale",
    "created_timestamp",
}
REQUIRED_CORRECTION_COLUMNS = {
    "correction_id",
    "artifact_group",
    "artifact_path",
    "original_manifest_value",
    "verified_exists_on_disk",
    "authoritative_governed_value",
    "source_of_truth",
    "applied_to_original_file",
    "downstream_use",
    "created_timestamp",
}
REQUIRED_TERMS = {
    "champion",
    "champion_with_conditions",
    "no_champion",
    "selected_champion",
    "conditional_champion",
    "tournament_standing",
    "eligible_candidate",
    "ineligible_candidate",
    "deferred_model",
    "risk_flag",
    "manual_review",
    "confidence_level",
    "carry_forward_condition",
    "dashboard_safe_statement",
    "source_of_truth",
}
REQUIRED_STATUSES = {
    "champion_selected_with_conditions",
    "champion_selected",
    "no_champion_selected",
    "eligible_candidate",
    "ineligible_due_to_risk",
    "ineligible_due_to_evidence",
    "deferred_runtime_impractical",
    "deferred_dependency_blocked",
    "manual_review_required",
    "monitor",
    "review_investigate",
    "test_later",
}

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


def _bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def _nonempty(path: Path) -> bool:
    return path.exists() and path.stat().st_size > 0


def main() -> int:
    logger.info("=== Inspect Stage 06 Blocks 6.0 and 6.1 ===")
    for path in REQUIRED_FILES:
        _check(path.exists(), f"required file exists: {path.name}")
    if _failures:
        return _finish()

    resolution = pd.read_csv(OUT_60 / "audit5_finding_resolution.csv")
    correction = pd.read_csv(OUT_60 / "governed_manifest_correction.csv")
    definitions = pd.read_csv(OUT_61 / "governance_definitions.csv")
    taxonomy = pd.read_csv(OUT_61 / "governance_status_taxonomy.csv")
    validation = pd.read_csv(OUT_61 / "governance_6_0_6_1_validation.csv")

    _check(REQUIRED_RESOLUTION_COLUMNS.issubset(resolution.columns), "resolution CSV has required columns")
    _check(REQUIRED_CORRECTION_COLUMNS.issubset(correction.columns), "correction CSV has required columns")
    _check(len(resolution) == 1 and len(correction) == 1, "6.0 correction artifacts have one row each")
    r = resolution.iloc[0]
    c = correction.iloc[0]
    _check(r["source_finding_id"] == "F-010", "F-010 recorded")
    _check(r["severity"] == "MINOR", "F-010 severity MINOR")
    _check(r["blocking_status"] == "non_blocking", "F-010 non-blocking")
    _check(r["governed_interpretation"] == "artifact_exists=True", "governed interpretation true")
    _check(not _bool(r["stage_05_file_edited"]), "stage_05_file_edited=false")
    _check(_bool(c["authoritative_governed_value"]), "authoritative governed value true")
    _check(_bool(c["verified_exists_on_disk"]), "verified disk value true")
    _check(not _bool(c["applied_to_original_file"]), "applied_to_original_file=false")
    _check(F010_ARTIFACT.exists(), "closure summary exists on disk")
    manifest = pd.read_csv(STAGE05_MANIFEST)
    manifest_row = manifest[manifest["artifact_path"] == c["artifact_path"]]
    _check(len(manifest_row) == 1 and not _bool(manifest_row.iloc[0]["artifact_exists"]), "original Stage 05 manifest remains audit-preserved as false")
    _check(REQUIRED_TERMS.issubset(set(definitions["term"])), "required governance terms present")
    _check(REQUIRED_STATUSES.issubset(set(taxonomy["status_name"])), "required governance statuses present")
    _check(_nonempty(OUT_60 / "audit5_finding_resolution_report.md"), "6.0 report non-empty")
    _check(_nonempty(OUT_61 / "governance_foundation_report.md"), "6.1 report non-empty")
    _check(not (validation["status"] == "fail").any(), "builder validation has no failed checks")
    _check((PROJECT_ROOT / "outputs" / "model_lab").exists(), "Stage 05 protected outputs present")
    _check((PROJECT_ROOT / "shiny_app").exists(), "Shiny path present and untouched")

    return _finish()


def _finish() -> int:
    logger.info("Inspection checks run: %d, failures: %d", _checks, len(_failures))
    if _failures:
        logger.error("INSPECTION FAILED:")
        for failure in _failures:
            logger.error("  - %s", failure)
        return 1
    logger.info("INSPECTION PASSED: governance 6.0/6.1 artifacts satisfy contract.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
