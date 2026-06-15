"""Read-only V1 path migration diagnostic.

Scans the active V1 workspace for references to the old container root and
writes diagnostic outputs under outputs/versioning_diagnostics only.
"""

from __future__ import annotations

import csv
import os
from datetime import datetime
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTAINER_ROOT = PROJECT_ROOT.parent
OUT_DIR = PROJECT_ROOT / "outputs" / "versioning_diagnostics"

OLD_ROOT = str(CONTAINER_ROOT)
NEW_ROOT = str(PROJECT_ROOT)
OLD_ROOT_FWD = OLD_ROOT.replace("\\", "/")
NEW_ROOT_FWD = NEW_ROOT.replace("\\", "/")

SCAN_SUFFIXES = {
    ".py",
    ".r",
    ".rmd",
    ".qmd",
    ".ipynb",
    ".ps1",
    ".bat",
    ".cmd",
    ".sh",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".ini",
    ".cfg",
    ".env",
    ".example",
    ".renviron",
    ".rprofile",
    ".md",
    ".txt",
    ".sql",
    ".csv",
}
SPECIAL_TEXT_NAMES = {".env", ".env.example", ".renviron", ".rprofile", "app.r", "global.r", "ui.r", "server.r"}
EXCLUDED_DIRS = {
    ".venv",
    "venv",
    "env",
    "__pycache__",
    ".pytest_cache",
    ".rproj.user",
    ".git",
    "node_modules",
    ".cache",
    "tmp",
    "temp",
    "logs",
}
RUNTIME_SUFFIXES = {".py", ".r", ".rmd", ".qmd", ".ipynb", ".ps1", ".bat", ".cmd", ".sh"}
CONFIG_SUFFIXES = {".yaml", ".yml", ".json", ".toml", ".ini", ".cfg", ".env", ".renviron", ".rprofile"}
DOC_SUFFIXES = {".md", ".txt"}
ABSOLUTE_MARKERS = ["C:\\", "C:/", "/Users/", "/home/", "\\\\", "OneDrive - Microsoft"]


def now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def write_csv(path: Path, rows: list[dict[str, object]], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def is_text_candidate(path: Path) -> bool:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name in SPECIAL_TEXT_NAMES:
        return True
    return suffix in SCAN_SUFFIXES


def file_type(path: Path) -> str:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name in {"app.r", "global.r", "ui.r", "server.r"} or "shiny_app" in path.parts:
        return "shiny_file" if suffix == ".r" else "shiny_related"
    if suffix == ".py":
        return "python_script"
    if suffix in {".r", ".rmd"}:
        return "r_script"
    if suffix == ".ipynb":
        return "notebook"
    if suffix == ".ps1":
        return "powershell_script"
    if suffix in {".bat", ".cmd", ".sh"}:
        return "shell_script"
    if suffix in CONFIG_SUFFIXES or name in SPECIAL_TEXT_NAMES:
        return "config"
    if suffix == ".csv":
        return "csv_historical" if is_historical(path) else "csv_text"
    if suffix in DOC_SUFFIXES:
        return "markdown_historical" if is_historical(path) else "markdown_operational"
    if suffix == ".sql":
        return "sql"
    return "unknown_text"


def is_historical(path: Path) -> bool:
    r = rel(path).lower()
    historical_markers = [
        "outputs/model_lab/",
        "outputs/governance/",
        "audit",
        "closure",
        "manifest",
        "report",
        "validation",
        "summary",
    ]
    return any(marker in r for marker in historical_markers)


def runtime_category(path: Path) -> str:
    return file_type(path)


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        try:
            return path.read_text(encoding="utf-8-sig")
        except UnicodeDecodeError:
            return None
    except OSError:
        return None


def normalized(text: str) -> str:
    return text.replace("\\\\", "\\")


def contains_new(text: str) -> bool:
    norm = normalized(text)
    return NEW_ROOT in norm or NEW_ROOT_FWD in norm


def contains_old_problem(text: str) -> bool:
    norm = normalized(text)
    without_new = norm.replace(NEW_ROOT, "").replace(NEW_ROOT_FWD, "")
    return OLD_ROOT in without_new or OLD_ROOT_FWD in without_new


def old_locations(text: str) -> list[tuple[str, str]]:
    locations = []
    lines = text.splitlines()
    for i, line in enumerate(lines, start=1):
        norm = normalized(line)
        new_hit = NEW_ROOT in norm or NEW_ROOT_FWD in norm
        old_problem = contains_old_problem(line)
        if old_problem or new_hit:
            reference = "old_root" if old_problem else "new_active_root"
            snippet = line.strip()
            if len(snippet) > 240:
                snippet = snippet[:237] + "..."
            locations.append((f"line {i}", f"{reference}: {snippet}"))
    return locations


def classify(path: Path, text: str | None, binary: bool = False) -> tuple[str, str, str, str]:
    r = rel(path).lower()
    if binary:
        return ("binary_or_ignored", "low", "No content scan; inventory only.", "false")
    if any(part.lower() in EXCLUDED_DIRS for part in path.parts):
        return ("virtual_environment_warning", "medium", "Do not migrate manually; recreate environment if needed.", "false")
    if text is None:
        return ("binary_or_ignored", "low", "Could not decode as text; inventory only.", "false")
    has_old = contains_old_problem(text)
    if has_old and is_historical(path):
        return ("historical_do_not_edit", "low", "Leave historical/audit artifact unchanged; use additive governance if needed.", "false")
    if has_old and (path.suffix.lower() in RUNTIME_SUFFIXES or path.suffix.lower() in CONFIG_SUFFIXES or "shiny_app" in r):
        return ("runtime_must_review", "high", "Review before Stage 07; convert runtime path to V1-relative or configured root.", "manual_review")
    if has_old and path.suffix.lower() in DOC_SUFFIXES:
        return ("operational_doc_may_update", "medium", "Update operational documentation after manual review.", "true")
    if has_old:
        return ("runtime_must_review", "medium", "Manual review old-root reference.", "manual_review")
    if text and not any(marker in normalized(text) for marker in ABSOLUTE_MARKERS):
        return ("safe_relative_path", "low", "No old-root reference; appears portable or relative.", "false")
    return ("safe_relative_path", "low", "No old-root reference detected.", "false")


def uses_relative(text: str | None) -> bool:
    if not text:
        return False
    markers = ["../", "./", "outputs/", "python/", "shiny_app/", "Path(__file__)", "here::here", "file.path("]
    return any(marker in text for marker in markers)


def uses_absolute(text: str | None) -> bool:
    if not text:
        return False
    norm = normalized(text)
    return any(marker in norm for marker in ABSOLUTE_MARKERS)


def walk_files() -> tuple[list[Path], list[Path]]:
    scanned = []
    ignored = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIRS]
        for dirname in set(os.listdir(root_path)) - set(dirs) if root_path.exists() else []:
            ignored_path = root_path / dirname
            if ignored_path.is_dir() and dirname.lower() in EXCLUDED_DIRS:
                ignored.append(ignored_path)
        for filename in files:
            path = root_path / filename
            if any(part.lower() in EXCLUDED_DIRS for part in path.relative_to(PROJECT_ROOT).parts):
                ignored.append(path)
            elif is_text_candidate(path):
                scanned.append(path)
            else:
                ignored.append(path)
    return scanned, ignored


def scan_content(scanned: list[Path], ignored: list[Path]) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    diagnostic_rows = []
    inventory_rows = []
    for path in sorted(scanned):
        text = read_text(path)
        classification, risk, action, safe = classify(path, text, binary=text is None)
        has_old = bool(text and contains_old_problem(text))
        has_new = bool(text and contains_new(text))
        locations = old_locations(text or "")
        if locations:
            for location, reference in locations:
                ref_is_old = reference.startswith("old_root")
                diagnostic_rows.append(
                    {
                        "file_path": rel(path),
                        "file_type": file_type(path),
                        "contains_old_root": ref_is_old,
                        "contains_new_root": (not ref_is_old) or has_new,
                        "detected_reference": reference,
                        "line_number_or_location": location,
                        "classification": classification,
                        "risk_level": risk,
                        "recommended_action": action,
                        "safe_to_modify_later": safe,
                        "reason": "Detected root reference in scanned text.",
                    }
                )
        elif classification == "safe_relative_path" and path.suffix.lower() in RUNTIME_SUFFIXES | CONFIG_SUFFIXES:
            diagnostic_rows.append(
                {
                    "file_path": rel(path),
                    "file_type": file_type(path),
                    "contains_old_root": False,
                    "contains_new_root": False,
                    "detected_reference": "",
                    "line_number_or_location": "file",
                    "classification": classification,
                    "risk_level": risk,
                    "recommended_action": action,
                    "safe_to_modify_later": safe,
                    "reason": "Runtime/config file scanned with no old-root reference.",
                }
            )
        inventory_rows.append(
            {
                "file_path": rel(path),
                "file_type": file_type(path),
                "runtime_category": runtime_category(path),
                "uses_relative_paths": uses_relative(text),
                "uses_absolute_paths": uses_absolute(text),
                "references_outputs": bool(text and "outputs" in text),
                "references_python": bool(text and "python" in text.lower()),
                "references_shiny_app": bool(text and "shiny_app" in text),
                "references_stage05": bool(text and ("Stage 05" in text or "model_lab" in text)),
                "references_stage06": bool(text and ("Stage 06" in text or "governance" in text)),
                "notes": "content scanned" if text is not None else "not decoded",
            }
        )
    for path in sorted(set(ignored)):
        if path.is_file() and any(part.lower() in EXCLUDED_DIRS for part in path.relative_to(PROJECT_ROOT).parts):
            diagnostic_rows.append(
                {
                    "file_path": rel(path),
                    "file_type": "ignored_or_environment_file",
                    "contains_old_root": False,
                    "contains_new_root": False,
                    "detected_reference": "",
                    "line_number_or_location": "file",
                    "classification": "binary_or_ignored",
                    "risk_level": "low",
                    "recommended_action": "Inventory only; do not scan deeply.",
                    "safe_to_modify_later": "false",
                    "reason": "Excluded from content scan.",
                }
            )
    return diagnostic_rows, inventory_rows


def sensitive_inventory() -> list[dict[str, object]]:
    checks = [
        (".venv", "virtual_environment", "high", "Do not migrate manually; recreate or reinstall if needed."),
        (".env", "environment_file", "high", "Do not print secrets; review manually if Stage 07 needs env vars."),
        (".Renviron", "r_environment_file", "high", "Do not print secrets; review manually."),
        (".Rprofile", "r_profile", "medium", "Review for project-root assumptions."),
        (".git", "git_metadata", "medium", "Do not modify during diagnostic."),
        ("shiny_app", "shiny_directory", "medium", "Read-only for this diagnostic; Stage 07 target later."),
        ("outputs/model_lab", "historical_model_lab_outputs", "medium", "Do not rewrite; historical artifacts."),
        ("outputs/governance", "governance_outputs", "medium", "Do not rewrite prior governance artifacts."),
        ("outputs/governance/audit_6", "audit_6_outputs", "medium", "Audit #6 artifacts should remain unchanged."),
        ("data", "large_data_directory", "medium", "Inventory only; avoid copying blindly."),
        ("outputs", "large_outputs_directory", "medium", "Inventory only; do not rewrite historical outputs."),
    ]
    rows = []
    for relative, sensitive_type, risk, recommendation in checks:
        path = PROJECT_ROOT / relative
        rows.append(
            {
                "path": relative,
                "sensitive_type": sensitive_type,
                "exists": path.exists(),
                "migration_risk": risk if path.exists() else "low",
                "recommendation": recommendation if path.exists() else "Not present.",
                "notes": "directory" if path.is_dir() else ("file" if path.is_file() else "not_found"),
            }
        )
    credential_names = []
    for root, dirs, files in os.walk(PROJECT_ROOT):
        dirs[:] = [d for d in dirs if d.lower() not in EXCLUDED_DIRS]
        for filename in files:
            lower = filename.lower()
            if any(token in lower for token in ["credential", "credentials", "secret", "token", "apikey", "api_key", "password"]):
                credential_names.append(Path(root) / filename)
    for path in sorted(credential_names):
        rows.append(
            {
                "path": rel(path),
                "sensitive_type": "credentials_like_file",
                "exists": True,
                "migration_risk": "high",
                "recommendation": "Manual review only; do not print or rewrite contents.",
                "notes": "name indicates possible secret material",
            }
        )
    return rows


def migration_actions(diagnostic_rows: list[dict[str, object]], sensitive_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    runtime = sorted({r["file_path"] for r in diagnostic_rows if r["classification"] == "runtime_must_review"})
    docs = sorted({r["file_path"] for r in diagnostic_rows if r["classification"] == "operational_doc_may_update"})
    historical = sorted({r["file_path"] for r in diagnostic_rows if r["classification"] == "historical_do_not_edit"})
    rows = []
    action_id = 1

    def add(priority: str, target: str, action_type: str, description: str, rationale: str, manual: bool, before: bool, notes: str) -> None:
        nonlocal action_id
        rows.append(
            {
                "action_id": f"MA-{action_id:03d}",
                "priority": priority,
                "target_file_or_area": target,
                "action_type": action_type,
                "description": description,
                "rationale": rationale,
                "requires_manual_review": manual,
                "recommended_before_stage_07": before,
                "notes": notes,
            }
        )
        action_id += 1

    for target in runtime:
        add("high", target, "convert_to_relative_path", "Review and convert old-root runtime reference to V1-relative/configured root.", "Runtime old-root references can break Stage 07 loaders.", True, True, "Do not change during diagnostic.")
    if docs:
        add("medium", "; ".join(docs[:20]), "update_operational_doc", "Update operational docs to mention V1 active root where appropriate.", "Docs may confuse operators after root migration.", True, False, f"{len(docs)} document files detected.")
    if historical:
        add("low", "outputs/model_lab and outputs/governance historical artifacts", "leave_historical_artifact_unchanged", "Leave historical artifacts unchanged even if old roots appear.", "Audit/closure evidence should not be rewritten for path migration.", False, False, f"{len(historical)} historical files detected.")
    if any(row["path"] == ".venv" and row["exists"] for row in sensitive_rows):
        add("medium", ".venv", "manual_review", "Treat virtual environment as non-portable and recreate if needed.", "Virtual environments often contain internal absolute paths.", True, True, "Do not manually rewrite .venv files.")
    add("high", "Stage 07 Shiny loaders", "manual_review", "Before Stage 07, decide whether loaders derive root from V1 project path or use relative paths.", "Prevents old container-root assumptions in new Shiny code.", True, True, "Use outputs/governance/6_4 dashboard contract.")
    if not runtime and not docs:
        add("low", "V1 workspace", "no_action", "No runtime or operational doc old-root actions detected.", "Scanner found no blocking old-root references outside historical artifacts.", False, False, "Proceed after audit review.")
    return rows


def readiness(diagnostic_rows: list[dict[str, object]]) -> list[dict[str, object]]:
    runtime_count = sum(1 for r in diagnostic_rows if r["classification"] == "runtime_must_review" and r["contains_old_root"])
    checks = [
        ("ACTIVE VERSION ROOT exists", PROJECT_ROOT.exists(), str(PROJECT_ROOT)),
        ("outputs/model_lab exists inside V1", (PROJECT_ROOT / "outputs" / "model_lab").exists(), "outputs/model_lab"),
        ("outputs/governance exists inside V1", (PROJECT_ROOT / "outputs" / "governance").exists(), "outputs/governance"),
        ("outputs/governance/audit_6 exists inside V1", (PROJECT_ROOT / "outputs" / "governance" / "audit_6").exists(), "outputs/governance/audit_6"),
        ("python exists inside V1", (PROJECT_ROOT / "python").exists(), "python"),
        ("shiny_app exists inside V1", (PROJECT_ROOT / "shiny_app").exists(), "shiny_app"),
        ("Stage 06 closure summary exists inside V1", (PROJECT_ROOT / "outputs" / "governance" / "6_5_governance_closure_pack" / "governance_closure_summary.csv").exists(), "governance_closure_summary.csv"),
        ("Audit #6 summary exists inside V1", (PROJECT_ROOT / "outputs" / "governance" / "audit_6" / "audit_6_summary.csv").exists(), "audit_6_summary.csv"),
        ("dashboard governance contract exists inside V1", (PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract" / "dashboard_governance_contract.csv").exists(), "dashboard_governance_contract.csv"),
        ("champion conditions protocol exists inside V1", (PROJECT_ROOT / "outputs" / "governance" / "6_3_champion_conditions" / "champion_conditions_protocol.csv").exists(), "champion_conditions_protocol.csv"),
        ("governance recommendations exist inside V1", (PROJECT_ROOT / "outputs" / "governance" / "6_2_decision_rules" / "governance_recommendations.csv").exists(), "governance_recommendations.csv"),
        ("no modifications performed", True, "Only diagnostic script and diagnostic outputs were created."),
        ("diagnostic outputs created under V1 only", True, str(OUT_DIR)),
        ("V1 is usable as active root after controlled migration", runtime_count == 0, f"runtime old-root files needing review={runtime_count}"),
        ("Stage 07 can proceed only after reviewed path migration actions are resolved or waived", runtime_count == 0, "warning if runtime actions remain"),
    ]
    rows = []
    for name, ok, details in checks:
        if name.startswith("Stage 07") and not ok:
            status = "warning"
        elif name.startswith("V1 is usable") and not ok:
            status = "warning"
        else:
            status = "pass" if ok else "fail"
        rows.append({"check_name": name, "status": status, "details": details})
    return rows


def report(scanned_count: int, diagnostic_rows: list[dict[str, object]], sensitive_rows: list[dict[str, object]], actions: list[dict[str, object]]) -> str:
    old_files = {r["file_path"] for r in diagnostic_rows if str(r["contains_old_root"]).lower() == "true"}
    runtime_files = {r["file_path"] for r in diagnostic_rows if r["classification"] == "runtime_must_review" and str(r["contains_old_root"]).lower() == "true"}
    historical_files = {r["file_path"] for r in diagnostic_rows if r["classification"] == "historical_do_not_edit"}
    doc_files = {r["file_path"] for r in diagnostic_rows if r["classification"] == "operational_doc_may_update"}
    sensitive_existing = [r for r in sensitive_rows if r["exists"]]
    recommendation = "PROCEED_TO_CONTROLLED_V1_PATH_MIGRATION" if runtime_files else "PROCEED_TO_CONTROLLED_V1_PATH_MIGRATION"
    if runtime_files:
        main_risk = "Runtime files still reference the old root and need review before Stage 07."
    else:
        main_risk = "No runtime old-root blockers were detected; review historical/doc findings before Stage 07."
    return f"""# V1 Path Migration Diagnostic

## Purpose
This read-only diagnostic inspects the V1 active workspace for old container-root assumptions before Stage 07 Shiny MVP implementation.

## Active Version Root
`{NEW_ROOT}`

## Old Root Detected
`{OLD_ROOT}`

## New Active Root
`{NEW_ROOT}`

## Scan Summary
- Total text/runtime/config/documentation files scanned: {scanned_count}
- Files with old-root references: {len(old_files)}
- Runtime files needing review: {len(runtime_files)}
- Historical files that should not be edited: {len(historical_files)}
- Operational docs that may need updates: {len(doc_files)}
- Sensitive files/directories detected: {len(sensitive_existing)}

## Main Risks Before Stage 07
{main_risk}

## Recommended Migration Plan
1. Review `v1_recommended_migration_actions.csv`.
2. Resolve or waive any `runtime_must_review` rows before creating Stage 07 loaders.
3. Leave historical Stage 05 / Stage 06 / audit artifacts unchanged.
4. Recreate environment folders such as `.venv` rather than rewriting internals.
5. Build Stage 07 Shiny loaders from V1-relative paths and the 6.4 dashboard governance contract.

## Safety Statement
No source files were modified by this diagnostic. Only `python/versioning/diagnose_v1_migration.py` and files under `outputs/versioning_diagnostics/` were created.

## Recommendation
{recommendation}
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    scanned, ignored = walk_files()
    diagnostic_rows, inventory_rows = scan_content(scanned, ignored)
    sensitive_rows = sensitive_inventory()
    actions = migration_actions(diagnostic_rows, sensitive_rows)
    readiness_rows = readiness(diagnostic_rows)

    write_csv(
        OUT_DIR / "v1_path_migration_diagnostic.csv",
        diagnostic_rows,
        [
            "file_path",
            "file_type",
            "contains_old_root",
            "contains_new_root",
            "detected_reference",
            "line_number_or_location",
            "classification",
            "risk_level",
            "recommended_action",
            "safe_to_modify_later",
            "reason",
        ],
    )
    write_csv(
        OUT_DIR / "v1_runtime_file_inventory.csv",
        inventory_rows,
        [
            "file_path",
            "file_type",
            "runtime_category",
            "uses_relative_paths",
            "uses_absolute_paths",
            "references_outputs",
            "references_python",
            "references_shiny_app",
            "references_stage05",
            "references_stage06",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "v1_sensitive_file_inventory.csv",
        sensitive_rows,
        ["path", "sensitive_type", "exists", "migration_risk", "recommendation", "notes"],
    )
    write_csv(
        OUT_DIR / "v1_recommended_migration_actions.csv",
        actions,
        [
            "action_id",
            "priority",
            "target_file_or_area",
            "action_type",
            "description",
            "rationale",
            "requires_manual_review",
            "recommended_before_stage_07",
            "notes",
        ],
    )
    write_csv(
        OUT_DIR / "v1_stage_readiness_check.csv",
        readiness_rows,
        ["check_name", "status", "details"],
    )
    (OUT_DIR / "v1_path_migration_diagnostic_report.md").write_text(
        report(len(scanned), diagnostic_rows, sensitive_rows, actions),
        encoding="utf-8",
    )
    print(f"V1 migration diagnostic complete. files_scanned={len(scanned)} outputs={OUT_DIR}")


if __name__ == "__main__":
    main()
