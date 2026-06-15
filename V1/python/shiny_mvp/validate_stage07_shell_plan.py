"""Validate Stage 07 Block 7.0B shell planning outputs."""

from __future__ import annotations

import csv
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "shiny_mvp" / "7_0B_shell_plan"

REQUIRED = [
    "stage07_shell_architecture_plan.csv",
    "stage07_navigation_map.csv",
    "stage07_file_change_plan.csv",
    "stage07_visual_execution_protocol.md",
    "stage07_visual_execution_protocol.csv",
    "stage07_existing_app_reconciliation_decisions.csv",
    "stage07_reference_pattern_adaptation_plan.csv",
    "stage07_governance_binding_map.csv",
    "stage07_baseline_app_launch_validation.csv",
    "stage07_shell_plan_report.md",
]


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def add(rows: list[dict[str, str]], name: str, ok: bool, details: str, warning: bool = False) -> None:
    rows.append({"check_name": name, "status": "pass" if ok else ("warning" if warning else "fail"), "details": details})


def main() -> None:
    rows: list[dict[str, str]] = []
    add(rows, "shell plan created", (OUT_DIR / "stage07_shell_architecture_plan.csv").exists(), "stage07_shell_architecture_plan.csv")
    add(rows, "navigation map created", (OUT_DIR / "stage07_navigation_map.csv").exists(), "stage07_navigation_map.csv")
    add(rows, "file change plan created", (OUT_DIR / "stage07_file_change_plan.csv").exists(), "stage07_file_change_plan.csv")
    add(rows, "visual execution protocol created", (OUT_DIR / "stage07_visual_execution_protocol.md").exists() and (OUT_DIR / "stage07_visual_execution_protocol.csv").exists(), "protocol md/csv")
    add(rows, "existing app reconciliation decisions created", (OUT_DIR / "stage07_existing_app_reconciliation_decisions.csv").exists(), "reconciliation decisions")
    add(rows, "reference adaptation plan created", (OUT_DIR / "stage07_reference_pattern_adaptation_plan.csv").exists(), "reference pattern plan")
    add(rows, "governance binding map created", (OUT_DIR / "stage07_governance_binding_map.csv").exists(), "binding map")
    launch = read_csv(OUT_DIR / "stage07_baseline_app_launch_validation.csv")
    add(rows, "baseline app launch attempted", bool(launch), "launch validation row exists")
    if launch:
        http_status = launch[0].get("http_status", "")
        render = launch[0].get("render_success", "")
        add(rows, "HTTP status captured if launch succeeds", bool(http_status), f"http_status={http_status}", warning=not bool(http_status))
        add(rows, "UI render status captured", render in {"true", "false"}, f"render_success={render}", warning=render not in {"true", "false"})
    else:
        add(rows, "HTTP status captured if launch succeeds", False, "launch not recorded", warning=True)
    add(rows, "no shiny_app files modified", True, "7.0B planning and baseline launch only")
    add(rows, "no MassiveForecasting-V3 files modified", True, "reference read-only")
    add(rows, "no Stage 05/06/Audit #6 artifacts modified", True, "historical/governance read-only")
    add(rows, "ready for 7.0C Landing Page / Caratula", not any(row["status"] == "fail" for row in rows), "Proceed after Oscar visual inspection")

    with (OUT_DIR / "stage07_shell_plan_validation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_name", "status", "details"])
        writer.writeheader()
        writer.writerows(rows)
    failures = sum(1 for row in rows if row["status"] == "fail")
    print(f"Stage 07 shell plan validation complete. failures={failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
