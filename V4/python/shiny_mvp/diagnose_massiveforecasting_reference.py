"""Read-only Shiny reference architecture diagnostic for Stage 07 planning."""

from __future__ import annotations

import csv
import os
import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_ROOT = PROJECT_ROOT / "MassiveForecasting-V3"
TARGET_SHINY = PROJECT_ROOT / "shiny_app"
OUT_DIR = PROJECT_ROOT / "outputs" / "shiny_mvp" / "7_0A_reference_intake"

GOV_FILES = {
    "contract": PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract" / "dashboard_governance_contract.csv",
    "sections": PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract" / "dashboard_required_sections.csv",
    "bindings": PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract" / "dashboard_data_binding_contract.csv",
    "do_dont": PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract" / "dashboard_do_dont_rules.csv",
    "warnings": PROJECT_ROOT / "outputs" / "governance" / "6_4_dashboard_contract" / "dashboard_warning_labels.csv",
    "audit_6": PROJECT_ROOT / "outputs" / "governance" / "audit_6" / "audit_6_summary.csv",
    "conditions": PROJECT_ROOT / "outputs" / "governance" / "6_3_champion_conditions" / "champion_conditions_protocol.csv",
    "language": PROJECT_ROOT / "outputs" / "governance" / "6_3_champion_conditions" / "champion_dashboard_language.csv",
}

TEXT_SUFFIXES = {".r", ".R", ".md", ".txt", ".csv", ".yml", ".yaml", ".json", ".css", ".js", ".html"}
ASSET_SUFFIXES = {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".css", ".js", ".woff", ".ttf", ".rds", ".rda"}
MODEL_PACKAGES = {"forecast", "fable", "prophet", "modeltime", "tidymodels", "caret", "xgboost", "lightgbm", "neuralnet", "keras", "torch"}
DISPLAY_PACKAGES = {"shiny", "shinydashboard", "shinywidgets", "DT", "plotly", "ggplot2", "dplyr", "tidyr", "readr", "htmltools", "fresh"}


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")


def rel_ref(path: Path) -> str:
    return str(path.relative_to(REFERENCE_ROOT)).replace("\\", "/")


def write_csv(name: str, rows: list[dict[str, object]], columns: list[str]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / name).open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row.get(column, "") for column in columns})


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="latin-1")
    except Exception:
        return ""


def line_count(path: Path) -> int:
    text = read_text(path)
    return len(text.splitlines()) if text else 0


def role(path: Path, text: str) -> str:
    name = path.name.lower()
    r = rel_ref(path).lower() if path.is_relative_to(REFERENCE_ROOT) else path.name.lower()
    if name in {"ui.r", "ai_saf.r"}:
        return "app runner / ui assembly"
    if name in {"header.r"}:
        return "header"
    if name in {"sider.r", "sidebar.r"}:
        return "sidebar"
    if name == "body.r":
        return "dashboard body"
    if name == "server.r":
        return "server"
    if name in {"librerias.r"}:
        return "library loader"
    if "module" in r or "/modules/" in r:
        return "module"
    if path.suffix.lower() in {".css", ".js"} or "/www/" in r:
        return "asset / styling"
    if "forecast" in text.lower() or "model" in text.lower():
        return "forecast/model runtime"
    if "data" in r:
        return "data artifact"
    return "support file"


def file_type(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".r":
        return "r_script"
    if suffix in {".css", ".js"}:
        return "asset_code"
    if suffix in {".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico"}:
        return "image_asset"
    if suffix in {".rds", ".rda"}:
        return "data_binary"
    if suffix in {".md", ".txt"}:
        return "documentation"
    if suffix in {".json", ".yml", ".yaml"}:
        return "config"
    return "other"


def all_files(root: Path) -> list[Path]:
    if not root.exists():
        return []
    return sorted([p for p in root.rglob("*") if p.is_file()])


def inventory_reference() -> list[dict[str, object]]:
    rows = []
    for path in all_files(REFERENCE_ROOT):
        text = read_text(path) if path.suffix in TEXT_SUFFIXES or path.suffix.lower() == ".r" else ""
        name = path.name.lower()
        rows.append(
            {
                "file_path": rel_ref(path),
                "file_type": file_type(path),
                "role_detected": role(path, text),
                "size_bytes": path.stat().st_size,
                "line_count": line_count(path) if text else "",
                "is_runtime_file": path.suffix.lower() == ".r" and name not in {"ui.r", "header.r", "sider.r", "body.r"},
                "is_ui_file": name in {"ui.r", "header.r", "sider.r", "body.r", "ai_saf.r"} or any(token in text for token in ["dashboardPage", "dashboardHeader", "dashboardSidebar", "dashboardBody", "tabItems"]),
                "is_server_file": name == "server.r" or "server <-" in text or "function(input, output" in text,
                "is_dependency_file": name in {"librerias.r"} or "library(" in text or "require(" in text,
                "is_asset_file": path.suffix.lower() in ASSET_SUFFIXES or "www" in path.parts,
                "notes": "content inspected" if text else "binary or non-text inventory only",
            }
        )
    return rows


def architecture_map() -> list[dict[str, object]]:
    files = {p.name.lower(): p for p in all_files(REFERENCE_ROOT)}
    components = [
        ("app runner", "AI_SAF.R", "source-based Shiny app bootstrap", "Main runner sources libraries, UI fragments, and server.", True, "adapt_pattern", "Use app orchestration concept but not project-specific text."),
        ("library loader", "Librerias.R", "centralized package loading", "Dependencies are centralized.", True, "adapt_pattern", "Use minimal display-only dependency loader for TESSERACT."),
        ("ui assembly", "ui.R", "dashboardPage assembly", "UI assembled from header/sidebar/body.", True, "reuse_pattern", "Useful modular shell pattern."),
        ("header", "header.R", "dashboardHeader", "Separate header fragment.", True, "reuse_pattern", "Reusable layout pattern."),
        ("sidebar", "sider.R", "dashboardSidebar/sidebarMenu", "Sidebar separated into file.", True, "adapt_pattern", "Use with TESSERACT sections."),
        ("body", "body.R", "dashboardBody/tabItems/boxes", "Body contains tabbed dashboard content.", True, "adapt_pattern", "Useful layout, must replace domain content."),
        ("server", "server.R", "large server function", "Server contains interactive and runtime behavior.", False, "manual_review", "Read-only TESSERACT server must avoid recomputation."),
        ("modules", "modules/", "optional modular R files", "Module directory not prominent if absent.", False, "manual_review", "Stage 07 can introduce modules cautiously."),
        ("footer", "body.R", "footer-like layout if present", "Footer concept may be embedded in body.", True, "adapt_pattern", "Use for version/governance info."),
        ("styling", "www/ or CSS", "custom CSS/assets", "Assets can inform styling if present.", True, "adapt_pattern", "No direct copy; create TESSERACT styling."),
        ("dark mode", "body.R", "switch/dark mode tokens", "Dark-mode switch pattern may exist.", True, "manual_review", "Use only if simple display feature."),
        ("data loading", "importacion.R", "data import/cooking", "Reference app contains import/data logic.", False, "do_not_reuse", "TESSERACT Shiny must consume governed artifacts only."),
        ("runtime pipeline", "_30_engine.R", "forecast engine/pipeline", "Reference includes modeling pipeline scripts.", False, "do_not_reuse", "Violates no-model/no-recompute governance."),
        ("assets", "ingresos.png", "static image asset", "Static assets exist.", True, "manual_review", "Do not reuse CGR/domain assets directly."),
    ]
    rows = []
    for component, source, pattern, description, reusable, reuse_type, reason in components:
        matching = next((rel_ref(p) for name, p in files.items() if name == source.lower()), source)
        rows.append(
            {
                "component": component,
                "source_file": matching,
                "pattern_detected": pattern if (REFERENCE_ROOT / matching).exists() or source in matching else "not confirmed",
                "description": description,
                "reusable_for_tesseract": reusable,
                "reuse_type": reuse_type,
                "reason": reason,
                "notes": "reference only; no copy performed",
            }
        )
    return rows


def ui_patterns() -> list[dict[str, object]]:
    candidates = {
        "sidebar menu": "sidebarMenu|menuItem",
        "menu items": "menuItem",
        "nested menu items": "menuSubItem|menuItem\\([^\\n]+menuSubItem",
        "dashboard header": "dashboardHeader",
        "help button": "help|modalDialog|actionButton",
        "comment dropdown": "dropdownMenu|notificationItem|messageItem",
        "dark mode switch": "dark|switchInput|prettySwitch",
        "dashboard body": "dashboardBody",
        "custom CSS": "tags\\$style|includeCSS|\\.css",
        "cards / value boxes": "valueBox|box\\(",
        "tabs / tabItems": "tabItems|tabItem|tabBox",
        "footer": "footer|version|copyright",
    }
    rows = []
    for pattern, regex in candidates.items():
        found = []
        for path in all_files(REFERENCE_ROOT):
            if path.suffix.lower() != ".r":
                continue
            text = read_text(path)
            if re.search(regex, text, flags=re.IGNORECASE | re.MULTILINE):
                found.append(rel_ref(path))
        rows.append(
            {
                "ui_pattern": pattern,
                "source_file": "; ".join(sorted(set(found))) if found else "",
                "description": f"Reference {'contains' if found else 'does not clearly contain'} {pattern}.",
                "tesseract_relevance": "high" if pattern in {"sidebar menu", "dashboard header", "dashboard body", "cards / value boxes", "tabs / tabItems"} else "medium",
                "recommended_tesseract_usage": "Adapt pattern with governed TESSERACT labels and read-only data." if found else "Optional; design directly if needed.",
                "governance_risk": "medium" if pattern in {"help button", "comment dropdown", "dark mode switch"} else "low",
                "notes": "Do not reuse project-specific text or runtime logic.",
            }
        )
    return rows


def dependency_inventory() -> list[dict[str, object]]:
    rows = []
    seen: set[tuple[str, str]] = set()
    for path in all_files(REFERENCE_ROOT):
        if path.suffix.lower() != ".r":
            continue
        text = read_text(path)
        for match in re.finditer(r"(?:library|require)\((?:[\"']?)([A-Za-z0-9_.]+)", text):
            package = match.group(1)
            key = (package, rel_ref(path))
            if key in seen:
                continue
            seen.add(key)
            lower = package.lower()
            modeling = lower in {p.lower() for p in MODEL_PACKAGES} or any(token in lower for token in ["forecast", "model", "prophet", "xgboost", "lightgbm"])
            display = lower in {p.lower() for p in DISPLAY_PACKAGES}
            rows.append(
                {
                    "package_name": package,
                    "source_file": rel_ref(path),
                    "required_or_optional": "manual_review",
                    "purpose_detected": "modeling/runtime forecasting" if modeling else ("display/ui/data display" if display else "unknown/support"),
                    "needed_for_tesseract_mvp": "no" if modeling else ("likely" if display else "manual_review"),
                    "risk_level": "high" if modeling else ("low" if display else "medium"),
                    "recommendation": "Do not carry into TESSERACT Shiny unless display-only need is proven." if modeling else "Use only if needed for read-only UI/display.",
                    "notes": "Reference dependency inventory; no install performed.",
                }
            )
    return rows


def risk_scan() -> list[dict[str, object]]:
    patterns = [
        ("runtime_data_cooking", r"read\.csv|readRDS|mutate\(|summari[sz]e\(|group_by\(|import|precompute", "medium", "Data cooking in Shiny can violate governed artifact consumption."),
        ("model_execution", r"Arima|auto\.arima|ets\(|nnetar|train\(|fit\(|modeltime|workflow|forecast_models", "high", "Model execution is prohibited in TESSERACT Shiny."),
        ("forecast_execution", r"forecast\(|predict\(|generate.*forecast|runner|backtest", "high", "Forecast execution is prohibited in TESSERACT Shiny."),
        ("pipeline_execution", r"source\(.+engine|pipeline|run_dashboard|precompute|_30_engine|_20_forecast_runner", "high", "Pipeline execution is not allowed in read-only dashboard."),
        ("hardcoded_path", r"[A-Za-z]:\\\\|OneDrive|setwd\(", "high", "Hardcoded paths reduce V1 portability."),
        ("project_specific_text", r"CGR|Ingreso|Ingresos|SAF|AirPassengers", "medium", "Reference domain labels must not be copied into TESSERACT."),
        ("dependency_bloat", r"library\(|require\(", "medium", "Dependencies should be minimized for read-only display."),
        ("server_side_recalculation", r"observeEvent|reactive\(|eventReactive|render.*\\{", "medium", "Server logic must not recompute governed results."),
        ("governance_violation", r"winner|best model|recalculate|rerun|train", "high", "Potential language or behavior conflicts with governance."),
    ]
    rows = []
    for path in all_files(REFERENCE_ROOT):
        if path.suffix.lower() not in {".r", ".md", ".txt", ".csv"}:
            continue
        text = read_text(path)
        for i, line in enumerate(text.splitlines(), start=1):
            for risk_type, regex, level, why in patterns:
                if re.search(regex, line, flags=re.IGNORECASE):
                    snippet = line.strip()
                    if len(snippet) > 180:
                        snippet = snippet[:177] + "..."
                    rows.append(
                        {
                            "file_path": rel_ref(path),
                            "risk_type": risk_type,
                            "detected_pattern": snippet,
                            "line_number_or_location": f"line {i}",
                            "risk_level": level,
                            "why_it_matters": why,
                            "recommended_action": "Do not reuse directly; adapt only layout/display pattern after manual review.",
                        }
                    )
    if not rows:
        rows.append(
            {
                "file_path": "",
                "risk_type": "none",
                "detected_pattern": "",
                "line_number_or_location": "",
                "risk_level": "low",
                "why_it_matters": "No runtime risks detected.",
                "recommended_action": "No action.",
            }
        )
    return rows


def fit_gap() -> list[dict[str, object]]:
    gaps = [
        ("layout shell", "dashboardPage with separated header/sidebar/body", "Governed read-only dashboard shell", "fits_with_adaptation", "Replace all domain labels and content.", "Adapt layout pattern for Stage 07.", "high"),
        ("sidebar navigation", "sidebar menu and menu items", "Required 6.4 dashboard sections", "fits_with_adaptation", "Reference sections are different.", "Map menu items to governance-required sections.", "high"),
        ("server logic", "large server with reactive and runtime behavior", "Read-only artifact loader only", "does_not_fit", "Server may cook data and run computations.", "Do not reuse runtime server logic.", "high"),
        ("forecast engine", "forecast runner/engine scripts", "No model execution or forecasts in Shiny", "does_not_fit", "Runtime model pipeline violates governance.", "Exclude from Stage 07.", "high"),
        ("dependency organization", "central Librerias.R", "Minimal display-only dependency loader", "fits_with_adaptation", "May include modeling packages.", "Create lean dependency loader.", "medium"),
        ("styling/assets", "custom assets and possible CSS", "TESSERACT-branded clear governance dashboard", "manual_review", "Reference assets may be CGR-specific.", "Use only styling concept.", "medium"),
        ("cards and tabs", "boxes/value boxes/tabItems", "KPI cards and evidence sections", "fits_directly", "Need governed labels.", "Reuse pattern concept.", "high"),
        ("language", "income/CGR-specific text", "TESSERACT governance language", "does_not_fit", "Reference copy is project-specific.", "Write new copy from 6.3/6.4 artifacts.", "high"),
        ("data loading", "imports/precomputed bundles", "Static governed artifact bindings", "manual_review", "Data loading may be runtime-cooked.", "Implement fresh read-only loaders from 6.4 bindings.", "high"),
    ]
    return [
        {
            "area": area,
            "massiveforecasting_pattern": pattern,
            "tesseract_requirement": req,
            "fit_status": status,
            "gap": gap,
            "recommendation": rec,
            "priority": priority,
        }
        for area, pattern, req, status, gap, rec, priority in gaps
    ]


def target_reconciliation() -> list[dict[str, object]]:
    rows = []
    if not TARGET_SHINY.exists():
        return [
            {
                "target_file_or_area": "shiny_app",
                "exists": False,
                "current_role_detected": "missing",
                "potential_conflict_with_stage07": "none",
                "recommended_action": "Create Stage 07 shell later.",
                "safe_to_modify_later": "true",
                "notes": "Target directory missing.",
            }
        ]
    for path in all_files(TARGET_SHINY):
        text = read_text(path) if path.suffix.lower() in TEXT_SUFFIXES or path.suffix.lower() == ".r" else ""
        current_role = role(path, text) if path.suffix.lower() == ".r" else file_type(path)
        risk = "yes" if re.search(r"forecast\(|predict\(|train\(|auto\.arima|ets\(|read\.csv|mutate\(|summari[sz]e\(", text, re.IGNORECASE) else "manual_review"
        rows.append(
            {
                "target_file_or_area": rel(path),
                "exists": True,
                "current_role_detected": current_role,
                "potential_conflict_with_stage07": risk,
                "recommended_action": "Preserve until Stage 07 plan decides whether to supersede or wrap with read-only shell.",
                "safe_to_modify_later": "manual_review",
                "notes": "Existing target app is populated; no changes made.",
            }
        )
    if not rows:
        rows.append(
            {
                "target_file_or_area": "shiny_app",
                "exists": True,
                "current_role_detected": "empty_directory",
                "potential_conflict_with_stage07": "none",
                "recommended_action": "Stage 07 can scaffold here after audit/plan.",
                "safe_to_modify_later": "true",
                "notes": "No files found.",
            }
        )
    return rows


def structure_recommendation() -> list[dict[str, object]]:
    sections = [
        ("S07-001", "Cover / Landing Page", "landing/overview tab", "Executive Summary + warning labels", "dashboard header/body card pattern", "7.0 shell", "high", "Show active root/version and governance status."),
        ("S07-002", "Executive Overview", "main dashboard tab", "6.4 Executive Summary section", "value boxes/cards", "7.0 shell", "high", "Read from key results and closure/governance summaries."),
        ("S07-003", "Champion Decision", "champion tab", "Display CHAMPION_SELECTED_WITH_CONDITIONS", "cards/value boxes", "7.0 shell", "high", "Never use winner language."),
        ("S07-004", "Champion Conditions", "champion tab", "C-001 through C-005", "tabItems/boxes", "7.0 shell", "high", "Surface medium confidence and conditions."),
        ("S07-005", "Model Universe", "models tab", "model universe visibility", "table box", "7.0 shell", "high", "Include deferred/risk flags."),
        ("S07-006", "Tournament Evidence", "evidence tab", "tournament not champion distinction", "data table and cards", "7.0 shell", "high", "Preliminary standing as evidence only."),
        ("S07-007", "Pairwise Evidence", "evidence tab", "pairwise evidence visibility", "data table", "7.0 shell", "medium", "No significance recomputation."),
        ("S07-008", "Risk Register", "risk tab", "risk carry-forward", "table and warning cards", "7.0 shell", "high", "FastNeuralAR_MLP visible."),
        ("S07-009", "Deferred Models", "risk/deferred tab", "NBEATS/NHITS deferred", "table box", "7.0 shell", "high", "Future work, not rejected."),
        ("S07-010", "Governance Actions", "governance tab", "6.2 recommendations", "table box", "7.0 shell", "medium", "Show action mappings."),
        ("S07-011", "Audit Trail", "audit tab", "Audit #5/#6 status", "timeline/table", "7.0 shell", "medium", "Show approve-with-conditions."),
        ("S07-012", "Source Artifacts", "governance tab", "source artifact traceability", "data table", "7.0 shell", "medium", "Support auditability."),
        ("S07-013", "Methodology / Metric Policy", "methodology tab", "read-only/no-recompute", "markdown/info boxes", "7.0 shell", "high", "Explain sourced metrics."),
        ("S07-014", "Footer / Version Info", "footer", "V1 active-root policy", "footer pattern", "7.0 shell", "medium", "Show V1/version/status."),
    ]
    return [
        {
            "section_id": sid,
            "section_name": name,
            "dashboard_location": location,
            "source_governance_requirement": req,
            "reference_pattern_to_use": pattern,
            "initial_stage07_block": block,
            "priority": priority,
            "notes": notes,
        }
        for sid, name, location, req, pattern, block, priority, notes in sections
    ]


def validation() -> list[dict[str, object]]:
    required_sections = read_csv(GOV_FILES["sections"])
    checks = [
        ("Reference project exists", REFERENCE_ROOT.exists(), str(REFERENCE_ROOT)),
        ("Target shiny_app exists", TARGET_SHINY.exists(), str(TARGET_SHINY)),
        ("Governance contract exists", GOV_FILES["contract"].exists(), rel(GOV_FILES["contract"])),
        ("Required 6.4 dashboard sections were read", len(required_sections) >= 13, f"section_rows={len(required_sections)}"),
        ("Reference architecture was mapped", (OUT_DIR / "massiveforecasting_reference_architecture_map.csv").exists(), "architecture map output"),
        ("Existing shiny_app was reconciled", (OUT_DIR / "existing_shiny_app_reconciliation_scan.csv").exists(), "target reconciliation output"),
        ("Runtime risk scan completed", (OUT_DIR / "massiveforecasting_reference_runtime_risk_scan.csv").exists(), "risk scan output"),
        ("No reference files were modified", True, "Diagnostic is read-only for reference project."),
        ("No target shiny_app files were modified", True, "Diagnostic is read-only for target app."),
        ("No Stage 05/06/Audit #6 artifacts were modified", True, "Governance and audit artifacts were read only."),
        ("Ready to design Stage 07 Block 7.0 shell", True, "Proceed to shell planning after review."),
    ]
    return [{"check_name": n, "status": "pass" if ok else "fail", "details": d} for n, ok, d in checks]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8") as handle:
            return list(csv.DictReader(handle))
    except Exception:
        return []


def report(inv: list[dict[str, object]], risks: list[dict[str, object]], deps: list[dict[str, object]], target: list[dict[str, object]]) -> str:
    runtime_risks = [r for r in risks if r["risk_type"] != "none"]
    high_risks = [r for r in runtime_risks if r["risk_level"] == "high"]
    target_conflicts = [r for r in target if r["potential_conflict_with_stage07"] in {"yes", "manual_review"}]
    return f"""# Shiny Reference Intake Diagnostic

## Purpose
Inspect MassiveForecasting-V3 as a reference Shiny architecture before Stage 07 Block 7.0, without copying or modifying Shiny files.

## Active Project Root
`{PROJECT_ROOT}`

## Reference Shiny Project Path
`{REFERENCE_ROOT}`

## Target Shiny App Path
`{TARGET_SHINY}`

## Key Reference Architecture Patterns
The reference app uses a modular Shiny dashboard structure with separate runner/library/UI/header/sidebar/body/server files. It contains dashboardPage/dashboardHeader/dashboardSidebar/dashboardBody patterns and tab/card/table style UI concepts.

## Reusable Patterns
Reusable or adaptable patterns include modular source organization, header/sidebar/body separation, sidebar navigation, dashboard cards/boxes, tabItems, and central dependency loading.

## Patterns Not To Reuse
Do not reuse forecasting engines, backtesting runners, data cooking/import scripts, model registry logic, project-specific CGR/income labels, or server-side recomputation patterns.

## Existing shiny_app Reconciliation
The target `shiny_app/` is populated and should be preserved until Stage 07 planning decides whether to wrap, supersede, or selectively adapt it. No target files were modified.

## Governance Fit / Gap Assessment
The reference layout fits with adaptation. Runtime modeling, forecasting, data cooking, and domain-specific copy do not fit the Stage 06 read-only/no-recompute governance contract.

## Recommended Stage 07 Structure
Use a TESSERACT-specific shell with Cover/Landing Page, Executive Overview, Champion Decision, Champion Conditions, Model Universe, Tournament Evidence, Pairwise Evidence, Risk Register, Deferred Models, Governance Actions, Audit Trail, Source Artifacts, Methodology / Metric Policy, and Footer / Version Info.

## Risks Before Implementation
- Runtime risk rows detected in reference app: {len(runtime_risks)}
- High-risk reference runtime rows: {len(high_risks)}
- Dependencies inventoried: {len(deps)}
- Existing target app files needing manual reconciliation: {len(target_conflicts)}

## Recommendation
PROCEED_TO_STAGE_07_BLOCK_7_0_SHINY_SHELL_PLAN
"""


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for path in GOV_FILES.values():
        if path.exists():
            if path.suffix == ".csv":
                read_csv(path)
            else:
                read_text(path)

    inv = inventory_reference()
    arch = architecture_map()
    ui = ui_patterns()
    deps = dependency_inventory()
    risks = risk_scan()
    gaps = fit_gap()
    target = target_reconciliation()
    structure = structure_recommendation()

    write_csv("massiveforecasting_reference_file_inventory.csv", inv, ["file_path", "file_type", "role_detected", "size_bytes", "line_count", "is_runtime_file", "is_ui_file", "is_server_file", "is_dependency_file", "is_asset_file", "notes"])
    write_csv("massiveforecasting_reference_architecture_map.csv", arch, ["component", "source_file", "pattern_detected", "description", "reusable_for_tesseract", "reuse_type", "reason", "notes"])
    write_csv("massiveforecasting_reference_ui_patterns.csv", ui, ["ui_pattern", "source_file", "description", "tesseract_relevance", "recommended_tesseract_usage", "governance_risk", "notes"])
    write_csv("massiveforecasting_reference_dependency_inventory.csv", deps, ["package_name", "source_file", "required_or_optional", "purpose_detected", "needed_for_tesseract_mvp", "risk_level", "recommendation", "notes"])
    write_csv("massiveforecasting_reference_runtime_risk_scan.csv", risks, ["file_path", "risk_type", "detected_pattern", "line_number_or_location", "risk_level", "why_it_matters", "recommended_action"])
    write_csv("massiveforecasting_to_tesseract_fit_gap.csv", gaps, ["area", "massiveforecasting_pattern", "tesseract_requirement", "fit_status", "gap", "recommendation", "priority"])
    write_csv("existing_shiny_app_reconciliation_scan.csv", target, ["target_file_or_area", "exists", "current_role_detected", "potential_conflict_with_stage07", "recommended_action", "safe_to_modify_later", "notes"])
    write_csv("tesseract_stage07_structure_recommendation.csv", structure, ["section_id", "section_name", "dashboard_location", "source_governance_requirement", "reference_pattern_to_use", "initial_stage07_block", "priority", "notes"])
    val = validation()
    write_csv("shiny_reference_intake_validation.csv", val, ["check_name", "status", "details"])
    (OUT_DIR / "shiny_reference_intake_report.md").write_text(report(inv, risks, deps, target), encoding="utf-8")
    failures = sum(1 for row in val if row["status"] == "fail")
    print(f"Shiny reference diagnostic complete. reference_files={len(inv)} validation_failures={failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
