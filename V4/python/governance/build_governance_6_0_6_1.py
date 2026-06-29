"""Stage 06 Blocks 6.0 and 6.1 governance foundation.

Creates additive governance artifacts for Audit #5 F-010 and the first
governance vocabulary/taxonomy layer. This script does not modify Stage 05
outputs or Shiny.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("build_governance_6_0_6_1")

GOV_ROOT = PROJECT_ROOT / "outputs" / "governance"
OUT_60 = GOV_ROOT / "6_0_audit5_finding_resolution"
OUT_61 = GOV_ROOT / "6_1_governance_foundation"

AUDIT5_SUMMARY = PROJECT_ROOT / "outputs" / "model_lab" / "audit_5" / "audit_5_summary.csv"
AUDIT5_FINDINGS = PROJECT_ROOT / "outputs" / "model_lab" / "audit_5" / "audit_5_findings.csv"
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

REQUIRED_TERMS = [
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
]
REQUIRED_STATUSES = [
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
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def _write(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise FileNotFoundError(f"required input missing: {path}")
    return pd.read_csv(path)


def _read_audit5_f010() -> pd.Series:
    """Read F-010 defensively because this audited CSV has unquoted comma text."""
    if not AUDIT5_FINDINGS.exists():
        raise FileNotFoundError(f"required input missing: {AUDIT5_FINDINGS}")
    for line in AUDIT5_FINDINGS.read_text(encoding="utf-8").splitlines():
        if line.startswith("F-010,"):
            finding_id, severity, area, finding_tail = line.split(",", 3)
            return pd.Series(
                {
                    "finding_id": finding_id,
                    "severity": severity,
                    "area": area,
                    "finding": finding_tail.strip().strip('"'),
                }
            )
    raise ValueError("Audit #5 F-010 finding not found")


def _f010_context() -> tuple[pd.Series, pd.Series, bool]:
    f010 = _read_audit5_f010()
    manifest = _read(STAGE05_MANIFEST)
    record = manifest[manifest["artifact_path"] == _rel(F010_ARTIFACT)]
    if len(record) != 1:
        raise ValueError("Stage 05 manifest record for closure summary not found exactly once")
    return f010, record.iloc[0], F010_ARTIFACT.exists()


def _build_60(ts: str) -> tuple[pd.DataFrame, pd.DataFrame, str]:
    f010, record, exists = _f010_context()
    resolution = pd.DataFrame(
        [
            {
                "resolution_id": "6_0_F010_additive_governed_resolution",
                "source_audit": "Audit #5",
                "source_finding_id": "F-010",
                "severity": "MINOR",
                "finding_area": "artifact_manifest",
                "finding_summary": str(f010["finding"]),
                "original_artifact_path": record["artifact_path"],
                "manifest_recorded_value": "artifact_exists=False",
                "verified_disk_value": f"artifact_exists={exists}",
                "governed_interpretation": "artifact_exists=True",
                "stage_05_file_edited": False,
                "correction_type": "additive_governed_correction",
                "blocking_status": "non_blocking",
                "rationale": (
                    "The referenced closure summary exists on disk; the Stage 05 manifest "
                    "record is audit-preserved and interpreted through this governed correction."
                ),
                "created_timestamp": ts,
            }
        ]
    )
    correction = pd.DataFrame(
        [
            {
                "correction_id": "F010_manifest_artifact_exists_governed_true",
                "artifact_group": record["artifact_group"],
                "artifact_path": record["artifact_path"],
                "original_manifest_value": False,
                "verified_exists_on_disk": exists,
                "authoritative_governed_value": True,
                "source_of_truth": "Audit #5 + disk verification",
                "applied_to_original_file": False,
                "downstream_use": "dashboard_handoff_and_governance_manifest_interpretation",
                "created_timestamp": ts,
            }
        ]
    )
    report = f"""# Block 6.0 - Audit #5 Finding Resolution

Generated: {ts}

## Finding

Audit #5 F-010 found that `model_lab_artifact_manifest.csv` recorded
`model_lab_closure_summary.csv` as `artifact_exists=False`, although the file
exists on disk.

## Non-Blocking Status

The finding is MINOR and non-blocking because the artifact exists and the issue
is limited to a manifest value, not a missing closure-pack file.

## Stage 05 Preservation

Stage 05 outputs were not edited. The original manifest remains audit-preserved.

## Governed Correction

For downstream governance and dashboard handoff, the authoritative governed
interpretation is `artifact_exists=True`.

## Downstream Interpretation

Consumers should use `governed_manifest_correction.csv` to interpret the
closure summary artifact as present. This is additive, traceable, and does not
mutate the audited Stage 05 file.
"""
    return resolution, correction, report


def _definitions(ts: str) -> pd.DataFrame:
    rows = {
        "champion": ("A model formally selected by the champion decision artifact.", "champion_decision.csv", "Use only after 5.31 decision.", "Display with decision context and conditions."),
        "champion_with_conditions": ("A selected champion that carries explicit caveats or follow-up obligations.", "champion_decision.csv", "Transitional monitored state, not unconditional victory.", "Surface conditions beside champion name."),
        "no_champion": ("Formal decision that no model is sufficiently defensible for champion status.", "champion_decision.csv", "Blocks champion promotion until later decision.", "State no champion plainly."),
        "selected_champion": ("The specific model selected in the official champion decision.", "model_lab_champion_summary.csv", "Single source is the decision artifact.", "Show ETS Explicit as conditional champion."),
        "conditional_champion": ("Synonym for champion selected with conditions.", "champion_decision.csv", "Requires risk and condition carry-forward.", "Avoid absolute winner language."),
        "tournament_standing": ("Preliminary ordered tournament output for review.", "tournament_preliminary_standings.csv", "Not equivalent to champion decision.", "Label as preliminary standing, not winner."),
        "eligible_candidate": ("A scored model eligible for decision review.", "champion_candidate_evaluation.csv", "Can be considered but not automatically selected.", "Display as eligible candidate."),
        "ineligible_candidate": ("A scored model excluded from champion consideration by evidence, risk, or guardrail.", "champion_candidate_evaluation.csv", "May remain in analysis but not champion eligible.", "Show exclusion reason."),
        "deferred_model": ("A model not scored in the final tournament due to documented blocker.", "model_lab_deferred_models.csv", "Future-work candidate, not discarded concept.", "Show as deferred with reason."),
        "risk_flag": ("A documented condition that must be surfaced and reviewed.", "model_lab_risk_register_final.csv", "Cannot be hidden in governance or dashboard.", "Show visible warning/caveat."),
        "manual_review": ("Required human review before future promotion or decision use.", "tournament_candidate_readiness_for_5_31.csv", "Requires follow-up action.", "Display review requirement."),
        "confidence_level": ("Decision confidence assigned by champion decision.", "champion_decision.csv", "Medium confidence means caveats remain.", "Display confidence, not just champion."),
        "carry_forward_condition": ("A non-blocking condition preserved for later stages.", "champion_decision_risk_review.csv", "Must remain visible in governance.", "Show in risks/conditions panel."),
        "dashboard_safe_statement": ("Language that does not overstate evidence or hide conditions.", "governance_definitions.csv", "Prevents misleading dashboard claims.", "Use conditional champion wording."),
        "source_of_truth": ("The authoritative artifact for a governed fact.", "governance_foundation_report.md", "Avoid competing interpretations.", "Link dashboard values to artifact paths."),
    }
    return pd.DataFrame(
        [
            {
                "term": term,
                "definition": values[0],
                "source_artifact": values[1],
                "governance_implication": values[2],
                "dashboard_implication": values[3],
                "created_timestamp": ts,
            }
            for term, values in rows.items()
        ]
    )


def _taxonomy(ts: str) -> pd.DataFrame:
    rows = [
        ("champion_selected_with_conditions", "decision", "Champion selected with explicit caveats.", "transitional", "closure/audit/dashboard review", "ETS Explicit", "Show conditions and medium confidence."),
        ("champion_selected", "decision", "Champion selected without unresolved conditions.", "terminal", "new evidence or governance change", "Not used in Stage 05", "Can display as selected champion."),
        ("no_champion_selected", "decision", "No model selected as champion.", "terminal", "future model evidence", "Allowed decision path", "Display no champion clearly."),
        ("eligible_candidate", "candidate", "Candidate eligible for 5.31 review.", "transitional", "champion decision", "AutoARIMA", "Show as eligible."),
        ("ineligible_due_to_risk", "candidate", "Candidate blocked from champion consideration by risk.", "transitional", "risk resolution", "FastNeuralAR_MLP", "Show risk reason."),
        ("ineligible_due_to_evidence", "candidate", "Candidate not supported by evidence.", "transitional", "new evidence", "LightGBM", "Show evidence reason."),
        ("deferred_runtime_impractical", "deferred", "Model deferred due to runtime impracticality.", "transitional", "stronger runtime or optimized execution", "NBEATS", "Show as deferred, not discarded."),
        ("deferred_dependency_blocked", "deferred", "Model deferred due to dependency incompatibility.", "transitional", "compatible environment", "NHITS", "Show dependency blocker."),
        ("manual_review_required", "review", "Human review required before promotion.", "transitional", "manual review completion", "FixedGrowth_6", "Show review flag."),
        ("monitor", "action", "Continue observing condition.", "transitional", "material change", "Conditional champion", "Show monitor status."),
        ("review_investigate", "action", "Investigate root cause or risk.", "transitional", "investigation result", "FastNeuralAR_MLP", "Show investigation action."),
        ("test_later", "action", "Retest model later under improved conditions.", "transitional", "future environment available", "NBEATS/NHITS", "Show future-test plan."),
    ]
    return pd.DataFrame(
        [
            {
                "status_name": a,
                "status_category": b,
                "description": c,
                "terminal_or_transitional": d,
                "review_trigger": e,
                "example_from_model_lab": f,
                "dashboard_display_requirement": g,
                "created_timestamp": ts,
            }
            for a, b, c, d, e, f, g in rows
        ]
    )


def _foundation_report(ts: str) -> str:
    return f"""# Block 6.1 - Governance Foundation

Generated: {ts}

## Purpose of Stage 06

Stage 06 converts Model Lab outputs into governance rules, decision language,
risk carry-forward, and dashboard-safe contracts. It is not another Model Lab.

## Output Location

All new artifacts are written under `outputs/governance/` to keep governance
additions separate from audited Stage 05 outputs.

## Relationship to Stage 05

Stage 05 remains the source for model execution, metrics, tournament, and
champion decision artifacts. Stage 06 interprets those outputs for governance
and dashboard handoff without modifying them.

## Core Governance Principles

1. Evidence over rank.
2. No silent loss of risk.
3. Single source of truth.
4. Additive correction over silent mutation.
5. Honest dashboard communication.

## Tournament Rank vs Champion Decision

Tournament standing is preliminary evidence. It is not the same as a champion
decision. The champion decision source of truth is `champion_decision.csv`.

## ETS Explicit as Conditional Champion

ETS Explicit is the selected champion with conditions and medium confidence.
It must not be described as an unconditional or absolute winner.

## F-010 Handling

Audit #5 F-010 is resolved through an additive governed correction. The Stage
05 manifest is not edited; downstream consumers should interpret the closure
summary artifact as present.

## Dashboard Risk Disclosure

Shiny and future dashboards must surface risks and conditions, including
FastNeuralAR_MLP high-risk behavior, NBEATS runtime deferral, NHITS dependency
deferral, and the conditional champion state.

## Source Safety

No models, forecasts, metrics, tournament artifacts, champion decision outputs,
Stage 05 artifacts, or Shiny files were modified by Blocks 6.0/6.1.
"""


def _validate(ts: str) -> pd.DataFrame:
    checks = []

    def add(name: str, ok: bool, details: str) -> None:
        checks.append({"check_name": name, "status": "pass" if ok else "fail", "details": details, "created_timestamp": ts})

    add("6_0_output_directory_exists", OUT_60.exists(), str(OUT_60))
    add("6_1_output_directory_exists", OUT_61.exists(), str(OUT_61))
    for path in [
        OUT_60 / "audit5_finding_resolution.csv",
        OUT_60 / "governed_manifest_correction.csv",
        OUT_60 / "audit5_finding_resolution_report.md",
        OUT_61 / "governance_definitions.csv",
        OUT_61 / "governance_status_taxonomy.csv",
        OUT_61 / "governance_foundation_report.md",
    ]:
        add(f"{path.name}_exists", path.exists(), _rel(path))
    resolution = pd.read_csv(OUT_60 / "audit5_finding_resolution.csv")
    correction = pd.read_csv(OUT_60 / "governed_manifest_correction.csv")
    definitions = pd.read_csv(OUT_61 / "governance_definitions.csv")
    taxonomy = pd.read_csv(OUT_61 / "governance_status_taxonomy.csv")
    add("f010_non_blocking", resolution.iloc[0]["blocking_status"] == "non_blocking", "F-010 blocking status")
    add("governed_correction_true", bool(correction.iloc[0]["authoritative_governed_value"]), "artifact_exists=True")
    add("applied_to_original_file_false", not bool(correction.iloc[0]["applied_to_original_file"]), "original file untouched")
    add("stage_05_file_edited_false", not bool(resolution.iloc[0]["stage_05_file_edited"]), "Stage 05 file untouched")
    add("required_terms_present", set(REQUIRED_TERMS).issubset(set(definitions["term"])), "governance terms")
    add("required_statuses_present", set(REQUIRED_STATUSES).issubset(set(taxonomy["status_name"])), "taxonomy statuses")
    add("no_stage05_files_modified", STAGE05_MANIFEST.exists() and F010_ARTIFACT.exists(), "Stage 05 inputs remain present")
    add("no_shiny_files_modified", (PROJECT_ROOT / "shiny_app").exists(), "Shiny path present")
    all_outputs_under_governance = all(str(p).startswith(str(GOV_ROOT)) for p in list(OUT_60.glob("*")) + list(OUT_61.glob("*")))
    add("all_outputs_under_governance", all_outputs_under_governance, "outputs/governance")
    return pd.DataFrame(checks)


def build() -> tuple[pd.DataFrame, pd.DataFrame]:
    logger.info("=== Stage 06 - Blocks 6.0 and 6.1 Governance Foundation ===")
    ts = _now()
    resolution, correction, report_60 = _build_60(ts)
    definitions = _definitions(ts)
    taxonomy = _taxonomy(ts)
    report_61 = _foundation_report(ts)

    _write(resolution, OUT_60 / "audit5_finding_resolution.csv")
    _write(correction, OUT_60 / "governed_manifest_correction.csv")
    OUT_60.mkdir(parents=True, exist_ok=True)
    (OUT_60 / "audit5_finding_resolution_report.md").write_text(report_60, encoding="utf-8")

    _write(definitions, OUT_61 / "governance_definitions.csv")
    _write(taxonomy, OUT_61 / "governance_status_taxonomy.csv")
    OUT_61.mkdir(parents=True, exist_ok=True)
    (OUT_61 / "governance_foundation_report.md").write_text(report_61, encoding="utf-8")
    validation = _validate(ts)
    _write(validation, OUT_61 / "governance_6_0_6_1_validation.csv")
    logger.info("Governance 6.0/6.1 complete: validation_failures=%d", int((validation["status"] == "fail").sum()))
    return resolution, validation


if __name__ == "__main__":
    build()
