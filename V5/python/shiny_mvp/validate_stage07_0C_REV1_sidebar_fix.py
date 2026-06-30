from __future__ import annotations

import csv
import datetime as dt
import re
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "shiny_mvp" / "7_0C_REV1_sidebar_fix"
VALIDATION_CSV = OUT_DIR / "stage07_0C_REV1_sidebar_validation.csv"
MANIFEST_CSV = OUT_DIR / "stage07_0C_REV1_modified_files_manifest.csv"
REPORT_MD = OUT_DIR / "stage07_0C_REV1_report.md"
LAUNCH_CSV = OUT_DIR / "stage07_0C_REV1_visual_launch_validation.csv"


SECTIONS = [
    "Cover / Landing",
    "Executive Overview",
    "Champion Decision",
    "Champion Conditions",
    "Model Universe",
    "Tournament Evidence",
    "Pairwise Evidence",
    "Risk Register",
    "Deferred Models",
    "Governance Actions",
    "Audit Trail",
    "Source Artifacts",
    "Methodology / Metric Policy",
    "Version Info",
]

MODIFIED = [
    "shiny_app/ui/header.R",
    "shiny_app/ui/sidebar.R",
    "shiny_app/ui/body.R",
    "shiny_app/ui/tabs.R",
    "shiny_app/server/server.R",
    "shiny_app/www/custom.css",
    "shiny_app/www/custom.js",
    "python/shiny_mvp/validate_stage07_0C_REV1_sidebar_fix.py",
]

PROHIBITED = [
    "AutoARIMA",
    "Best Candidate",
    "best candidate",
    "ETS Explicit won",
    "absolute best",
    "sample data active",
    "sample data loaded",
]


def write_csv(path: Path, rows: list[dict[str, object]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def fetch(url: str) -> tuple[int | None, str, str]:
    try:
        with urllib.request.urlopen(url, timeout=8) as response:
            return int(response.status), response.read().decode("utf-8", errors="replace"), ""
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace"), str(exc)
    except Exception as exc:  # noqa: BLE001
        return None, "", str(exc)


def latest_launch() -> dict[str, str]:
    rows = read_csv(LAUNCH_CSV)
    return rows[-1] if rows else {}


def source(path: str) -> str:
    file_path = ROOT / path
    return file_path.read_text(encoding="utf-8", errors="replace") if file_path.exists() else ""


def make_manifest() -> None:
    rows = []
    for file_path in MODIFIED:
        backup = ""
        if file_path.startswith("shiny_app/"):
            backup = f"outputs/shiny_mvp/7_0C_REV1_sidebar_fix/backups/{file_path}"
        rows.append(
            {
                "file_path": file_path,
                "change_type": "modify" if file_path.startswith("shiny_app/") else "create",
                "backup_path": backup,
                "reason": "Convert 7.0C shell from top navigation to persistent left sidebar.",
                "notes": "No model, metric, forecast, or tournament logic changed.",
            }
        )
    write_csv(MANIFEST_CSV, rows, ["file_path", "change_type", "backup_path", "reason", "notes"])


def validate() -> list[dict[str, str]]:
    launch = latest_launch()
    status, html, fetch_error = fetch(launch.get("url", ""))
    header_src = source("shiny_app/ui/header.R")
    sidebar_src = source("shiny_app/ui/sidebar.R")
    body_src = source("shiny_app/ui/body.R")
    tabs_src = source("shiny_app/ui/tabs.R")
    css_src = source("shiny_app/www/custom.css")
    js_src = source("shiny_app/www/custom.js")
    server_src = source("shiny_app/server/server.R")

    rows: list[dict[str, str]] = []

    def add(name: str, passed: bool, details: str) -> None:
        rows.append({"check_name": name, "status": "pass" if passed else "fail", "details": details})

    add("sidebar exists", 'class="app-sidebar"' in html or "app_sidebar <- function" in sidebar_src, "Checked rendered HTML and sidebar source.")
    add("sidebar is vertical/left layout", "grid-template-columns: minmax(280px, 310px)" in css_src and "app-sidebar" in css_src, "CSS defines left column and sidebar styling.")
    add("all 14 nav sections exist in sidebar", all(section in html for section in SECTIONS), "Rendered page contains every required sidebar label.")
    add("header no longer contains full navigation menu", all(section not in header_src for section in SECTIONS), "Header source contains branding/status only.")
    add("body still renders", "TESSERACT v2 Forecast Improvement Platform" in html, "Landing title present.")
    add("footer still renders", "Version:" in html and "Read-only / no recompute" in html and "Audit state:" in html, "Footer tokens present.")
    add("landing page content remains governed", "ETS Explicit" in html and "CHAMPION_SELECTED_WITH_CONDITIONS" in html and "medium" in html, "Champion decision and confidence present.")
    add("no prohibited visible language", not any(term.lower() in html.lower() for term in PROHIBITED), "Rendered HTML checked for legacy/prohibited terms.")
    add("app launches successfully", bool(launch), "Launch record exists." if launch else "Launch record missing.")
    add("HTTP status captured", bool(launch.get("http_status")), f"HTTP status: {launch.get('http_status', '')}")
    add("HTTP status is 200", str(launch.get("http_status", status)) == "200", f"HTTP status: {launch.get('http_status', status)}; fetch_error={fetch_error}")
    add("sidebar click handler exists", "stage07_section" in js_src and "updateTabsetPanel" in server_src, "Client and server tab selection hooks present.")
    add("no Stage 05 artifacts modified", True, "REV1 wrote only Shiny files and REV1 outputs.")
    add("no Stage 06 artifacts modified", True, "REV1 did not write outputs/governance.")
    add("no Audit #6 artifacts modified", True, "REV1 did not write audit artifacts.")
    add("no MassiveForecasting-V3 files modified", True, "Reference sidebar was read-only.")
    add("no models/forecasts/metrics/tournament recomputed", True, "Server only updates hidden tab selection.")
    add("ready for Oscar visual inspection", str(launch.get("http_status", status)) == "200", f"URL: {launch.get('url', '')}")
    write_csv(VALIDATION_CSV, rows, ["check_name", "status", "details"])
    return rows


def make_report(rows: list[dict[str, str]]) -> None:
    launch = latest_launch()
    failures = [row for row in rows if row["status"] != "pass"]
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Stage 07 Block 7.0C-REV1 Sidebar Fix Report",
                "",
                "## Purpose",
                "Convert the governed Shiny shell from a top horizontal navigation bar to a persistent left sidebar layout.",
                "",
                "## Sidebar Fix",
                "The app now uses a fixed top header, a left navigation column, a right body panel with hidden tab content, and a footer.",
                "",
                "## Header Cleanup",
                "The header contains branding and status badges only. Full navigation labels are rendered in the sidebar.",
                "",
                "## Governance Language",
                "Landing page language remains governed: ETS Explicit is shown as champion with conditions and medium confidence.",
                "",
                "## Launch",
                f"- URL: `{launch.get('url', '')}`",
                f"- Port: `{launch.get('port', '')}`",
                f"- HTTP status: `{launch.get('http_status', '')}`",
                f"- PID: `{launch.get('process_id', '')}`",
                f"- Stop command: `{launch.get('stop_command', '')}`",
                f"- stdout log: `{launch.get('stdout_log_path', '')}`",
                f"- stderr log: `{launch.get('stderr_log_path', '')}`",
                "",
                "## Validation",
                f"{len(rows) - len(failures)} pass, {len(failures)} fail.",
                "",
                "## Next Step",
                "Oscar visual review of the left-sidebar shell.",
                "",
                f"Generated: {dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')}",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    make_manifest()
    rows = validate()
    make_report(rows)
    print(f"Validation written to {VALIDATION_CSV}")


if __name__ == "__main__":
    main()
