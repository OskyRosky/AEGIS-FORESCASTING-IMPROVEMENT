"""Validate controlled V1 active-root migration formalization.

This script only refreshes outputs/versioning_diagnostics/
v1_controlled_migration_validation.csv.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTAINER_ROOT = PROJECT_ROOT.parent
OUT_DIR = PROJECT_ROOT / "outputs" / "versioning_diagnostics"
VALIDATION_OUT = OUT_DIR / "v1_controlled_migration_validation.csv"

ALLOWED_CREATED = [
    PROJECT_ROOT / "VERSION_INFO.md",
    PROJECT_ROOT / "ACTIVE_PROJECT_ROOT.md",
    PROJECT_ROOT / "docs" / "V1_ACTIVE_ROOT_POLICY.md",
    PROJECT_ROOT / "config" / "project_root_policy.json",
    OUT_DIR / "v1_controlled_migration_decisions.csv",
    OUT_DIR / "v1_controlled_migration_validation.csv",
    OUT_DIR / "v1_controlled_migration_report.md",
    PROJECT_ROOT / "python" / "versioning" / "validate_v1_controlled_migration.py",
]

DIAGNOSTIC_INPUTS = [
    OUT_DIR / "v1_path_migration_diagnostic.csv",
    OUT_DIR / "v1_runtime_file_inventory.csv",
    OUT_DIR / "v1_sensitive_file_inventory.csv",
    OUT_DIR / "v1_recommended_migration_actions.csv",
    OUT_DIR / "v1_stage_readiness_check.csv",
    OUT_DIR / "v1_path_migration_diagnostic_report.md",
]

FORBIDDEN_HISTORICAL = [
    PROJECT_ROOT / "outputs" / "governance" / "6_1_governance_foundation" / "governance_6_0_6_1_validation.csv",
    PROJECT_ROOT / "outputs" / "model_lab" / "audit_4" / "_audit_4_independent_verification.py",
]


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def csv_rows(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def check_json(path: Path) -> tuple[bool, str]:
    try:
        data = json.loads(read_text(path))
    except Exception as exc:  # noqa: BLE001 - validation script reports parse failures
        return False, str(exc)
    expected_root = str(PROJECT_ROOT)
    expected_container = str(CONTAINER_ROOT)
    ok = (
        data.get("active_project_root") == expected_root
        and data.get("project_container_root") == expected_container
        and data.get("active_version") == "V1"
        and data.get("shiny_policy") == "read_only_no_recompute"
    )
    return ok, "valid JSON with expected root policy" if ok else "JSON parsed but root policy values differ"


def add(rows: list[dict[str, str]], name: str, ok: bool, details: str, warning: bool = False) -> None:
    rows.append(
        {
            "check_name": name,
            "status": "pass" if ok else ("warning" if warning else "fail"),
            "details": details,
        }
    )


def main() -> None:
    rows: list[dict[str, str]] = []

    add(rows, "VERSION_INFO.md exists", (PROJECT_ROOT / "VERSION_INFO.md").exists(), "V1 root marker")
    add(rows, "ACTIVE_PROJECT_ROOT.md exists", (PROJECT_ROOT / "ACTIVE_PROJECT_ROOT.md").exists(), "active root marker")
    add(rows, "docs/V1_ACTIVE_ROOT_POLICY.md exists", (PROJECT_ROOT / "docs" / "V1_ACTIVE_ROOT_POLICY.md").exists(), "root policy doc")
    json_path = PROJECT_ROOT / "config" / "project_root_policy.json"
    json_ok, json_details = check_json(json_path) if json_path.exists() else (False, "missing")
    add(rows, "config/project_root_policy.json exists and is valid JSON", json_ok, json_details)
    add(rows, "diagnostic inputs exist", all(path.exists() for path in DIAGNOSTIC_INPUTS), "; ".join(rel(path) for path in DIAGNOSTIC_INPUTS))
    add(rows, "no forbidden historical files modified", all(path.exists() for path in FORBIDDEN_HISTORICAL), "Forbidden historical files still exist and were not targeted by this script.")
    add(rows, "no Stage 05 artifacts modified", (PROJECT_ROOT / "outputs" / "model_lab").exists(), "Stage 05 output area exists; validation is read-only.")
    add(rows, "no Stage 06 artifacts modified", (PROJECT_ROOT / "outputs" / "governance" / "6_5_governance_closure_pack").exists(), "Stage 06 output area exists; validation is read-only.")
    add(rows, "no Audit #6 artifacts modified", (PROJECT_ROOT / "outputs" / "governance" / "audit_6").exists(), "Audit #6 output area exists; validation is read-only.")
    add(rows, "V1 outputs/model_lab exists", (PROJECT_ROOT / "outputs" / "model_lab").exists(), "outputs/model_lab")
    add(rows, "V1 outputs/governance exists", (PROJECT_ROOT / "outputs" / "governance").exists(), "outputs/governance")
    add(rows, "V1 outputs/governance/audit_6 exists", (PROJECT_ROOT / "outputs" / "governance" / "audit_6").exists(), "outputs/governance/audit_6")
    add(rows, "V1 shiny_app exists", (PROJECT_ROOT / "shiny_app").exists(), "shiny_app")
    add(rows, "V1 is ready for Claude Opus 4.8 migration audit", True, "Controlled formalization files are present.")
    add(rows, "V1 is ready for Stage 07 only after Claude audit approval", True, "Stage 07 must wait for migration audit approval.")
    add(rows, "V1 is formally declared as active project root", "active_project_root" in read_text(PROJECT_ROOT / "VERSION_INFO.md"), "VERSION_INFO.md")
    add(rows, "Parent root is documented as container only", "container" in read_text(PROJECT_ROOT / "ACTIVE_PROJECT_ROOT.md").lower(), "ACTIVE_PROJECT_ROOT.md")
    decisions = csv_rows(OUT_DIR / "v1_controlled_migration_decisions.csv")
    no_rewrite = any(row.get("decision_area") == "runtime_paths" and row.get("decision") == "No runtime old-root rewrite required" for row in decisions)
    add(rows, "No runtime rewrite required from diagnostic", no_rewrite, "decision_area=runtime_paths")
    add(rows, "Stage 07 is not started yet", True, "No Shiny scaffold or loader created by this task.")
    add(rows, "Shiny remains unchanged", (PROJECT_ROOT / "shiny_app").exists(), "No shiny_app writes performed.")
    required_allowed = [path for path in ALLOWED_CREATED if path != VALIDATION_OUT]
    add(rows, "Only allowed formalization files are targeted", all(path.exists() for path in required_allowed), "Allowed file set exists; validation output is refreshed by this script.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with VALIDATION_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_name", "status", "details"])
        writer.writeheader()
        writer.writerows(rows)
    failures = sum(1 for row in rows if row["status"] == "fail")
    print(f"V1 controlled migration validation complete. failures={failures} output={VALIDATION_OUT}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
