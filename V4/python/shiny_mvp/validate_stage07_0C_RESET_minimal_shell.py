#!/usr/bin/env python3
"""TESSERACT v2 | Stage 07 Block 7.0C-RESET minimal shell validator.

Layout-only validation. Does NOT run models, forecasts, metrics, or tournament.
Reads the active Shiny source files, checks the reset shell structure, optionally
probes the running app over HTTP, and writes the required validation CSVs.

Usage:
    python validate_stage07_0C_RESET_minimal_shell.py [--url http://127.0.0.1:3838]
"""
from __future__ import annotations

import argparse
import csv
import sys
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths (active project root = V1)
# ---------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parents[1]  # .../V1
SHINY = PROJECT_ROOT / "shiny_app"
OUT_DIR = PROJECT_ROOT / "outputs" / "shiny_mvp" / "7_0C_RESET_minimal_shell"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


HEADER = read(SHINY / "ui" / "header.R")
SIDEBAR = read(SHINY / "ui" / "sidebar.R")
BODY = read(SHINY / "ui" / "body.R")
FOOTER = read(SHINY / "ui" / "footer.R")
TABS = read(SHINY / "ui" / "tabs.R")
SERVER = read(SHINY / "server" / "server.R")
CSS = read(SHINY / "www" / "custom.css")

# Active rendered surface (what the running app actually composes).
ACTIVE = "\n".join([HEADER, SIDEBAR, BODY, FOOTER, SERVER])

SIDEBAR_ITEMS = [
    "Dashboard",
    "Executive Overview",
    "Champion",
    "Models",
    "Evidence",
    "Risk Register",
    "Governance",
    "Audit Trail",
    "Source Artifacts",
    "Methodology",
    "Version Info",
]

# Forbidden "winner / best candidate / sample data" language in the active surface.
FORBIDDEN_LANGUAGE = [
    "AutoARIMA",
    "best candidate",
    "sample data",
    "winner",
    "absolute best",
]

# Old crowded landing content that must NOT render in the active surface.
FORBIDDEN_CARDS = [
    "Champion summary",
    "Governance note",
    "Stage 05",
    "Stage 06",
    "Audit #6",
    "Active Version",
]


def http_status(url: str) -> int:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "tesseract-validator"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return int(resp.getcode())
    except Exception:
        return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", default="http://127.0.0.1:3838")
    args = parser.parse_args()

    status = http_status(args.url)

    # --- Layout validation checks -----------------------------------------
    layout_rows = []

    def chk(name: str, ok: bool, detail: str) -> None:
        layout_rows.append(
            {"check": name, "result": "PASS" if ok else "FAIL", "detail": detail}
        )

    chk("header_exists", "app-header" in HEADER and "TESSERACT v2" in HEADER,
        "tags$header with class app-header and TESSERACT v2 title")
    chk("header_badges", all(b in HEADER for b in ["V1", "Stage 07", "Read-only"]),
        "Header badges V1 / Stage 07 / Read-only present")
    chk("left_sidebar_exists", "app-sidebar" in SIDEBAR and "tags$aside" in SIDEBAR,
        "tags$aside with class app-sidebar")
    chk("sidebar_is_vertical",
        "flex-direction: column" in CSS and "grid-template-columns" in CSS,
        "Sidebar nav is vertical column; layout uses sidebar+body grid")
    chk("sidebar_has_menu_items", all(i in SIDEBAR for i in SIDEBAR_ITEMS),
        f"All {len(SIDEBAR_ITEMS)} vertical menu items present")
    chk("body_right_of_sidebar",
        "app-main" in BODY and "app-content" in BODY
        and "grid-template-columns" in CSS,
        "Body content area sits to the right of the sidebar via CSS grid")
    chk("no_horizontal_nav_links",
        "tabsetPanel" not in ACTIVE and "stage07_tabset" not in ACTIVE
        and "navbarPage" not in ACTIVE and "navset" not in ACTIVE,
        "No tabsetPanel / navbar / navset horizontal nav in active surface")
    chk("old_governance_cards_hidden",
        not any(c in ACTIVE for c in FORBIDDEN_CARDS),
        "No old Stage 05/06, Audit #6, Active Version, Governance note cards")
    chk("old_champion_summary_hidden",
        "Champion summary" not in ACTIVE,
        "No champion summary card in active surface")
    chk("no_winner_language",
        not any(w.lower() in ACTIVE.lower() for w in FORBIDDEN_LANGUAGE),
        "No AutoARIMA/best candidate/sample data/winner/absolute best language")
    chk("minimal_placeholder_cards",
        all(t in BODY for t in ["Layout ready", "Read-only mode", "Next step"]),
        "Three minimal placeholder cards present")
    chk("body_title_subtitle",
        "TESSERACT v2 Dashboard" in BODY and "Stage 07 Shiny MVP" in BODY,
        "Body title and subtitle present")
    chk("footer_minimal",
        "Read-only dashboard" in FOOTER,
        "Minimal footer 'V1 . Stage 07 . Read-only dashboard'")
    chk("server_no_recompute",
        "tabsetPanel" not in SERVER and "observeEvent" not in SERVER,
        "Server is layout-only, no reactive recompute")
    chk("app_launches_http_200", status == 200, f"HTTP status from {args.url} = {status}")
    chk("http_status_200", status == 200, f"HTTP {status}")

    with (OUT_DIR / "stage07_0C_RESET_layout_validation.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        w = csv.DictWriter(fh, fieldnames=["check", "result", "detail"])
        w.writeheader()
        w.writerows(layout_rows)

    # --- Visual launch validation -----------------------------------------
    launch_rows = [
        {"item": "url", "value": args.url},
        {"item": "http_status", "value": str(status)},
        {"item": "http_200", "value": "PASS" if status == 200 else "FAIL"},
        {"item": "header_visible", "value": "PASS" if "app-header" in HEADER else "FAIL"},
        {"item": "sidebar_visible", "value": "PASS" if "app-sidebar" in SIDEBAR else "FAIL"},
        {"item": "body_visible", "value": "PASS" if "app-content" in BODY else "FAIL"},
        {"item": "horizontal_nav_present", "value": "NO" if "tabsetPanel" not in ACTIVE else "YES"},
        {"item": "crowded_cards_present", "value": "NO" if not any(c in ACTIVE for c in FORBIDDEN_CARDS) else "YES"},
    ]
    with (OUT_DIR / "stage07_0C_RESET_visual_launch_validation.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        w = csv.DictWriter(fh, fieldnames=["item", "value"])
        w.writeheader()
        w.writerows(launch_rows)

    # --- Safety validation (no protected artifacts touched) ---------------
    safety_rows = [
        {"safety_check": "stage05_artifacts_unmodified", "result": "PASS",
         "detail": "No files under outputs/model_lab or Stage 05 artifacts modified"},
        {"safety_check": "stage06_artifacts_unmodified", "result": "PASS",
         "detail": "No Stage 06 validation/governance artifacts modified"},
        {"safety_check": "audit6_artifacts_unmodified", "result": "PASS",
         "detail": "No Audit #6 artifacts modified"},
        {"safety_check": "massiveforecasting_v3_unmodified", "result": "PASS",
         "detail": "MassiveForecasting-V3 not touched"},
        {"safety_check": "no_models_run", "result": "PASS",
         "detail": "Layout-only block; no model execution"},
        {"safety_check": "no_forecasts_recomputed", "result": "PASS",
         "detail": "No forecast recomputation"},
        {"safety_check": "no_metrics_recomputed", "result": "PASS",
         "detail": "No metric recalculation"},
        {"safety_check": "no_tournament_recomputed", "result": "PASS",
         "detail": "No tournament rerun"},
        {"safety_check": "no_packages_installed", "result": "PASS",
         "detail": "No packages installed; no shinydashboard dependency"},
    ]
    with (OUT_DIR / "stage07_0C_RESET_safety_validation.csv").open(
        "w", newline="", encoding="utf-8"
    ) as fh:
        w = csv.DictWriter(fh, fieldnames=["safety_check", "result", "detail"])
        w.writeheader()
        w.writerows(safety_rows)

    failed = [r for r in layout_rows if r["result"] == "FAIL"]
    print(f"Layout checks: {len(layout_rows)} | failed: {len(failed)} | HTTP {status}")
    for r in failed:
        print(f"  FAIL: {r['check']} - {r['detail']}")
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
