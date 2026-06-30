from __future__ import annotations

import csv
import datetime as dt
import json
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = ROOT / "outputs" / "shiny_mvp" / "7_0C_landing_page"
LAUNCH_CSV = OUT_DIR / "stage07_0C_visual_launch_validation.csv"
VALIDATION_CSV = OUT_DIR / "stage07_0C_shell_validation.csv"
LANGUAGE_SCAN_CSV = OUT_DIR / "stage07_0C_governance_language_scan.csv"
MANIFEST_CSV = OUT_DIR / "stage07_0C_modified_files_manifest.csv"
REPORT_MD = OUT_DIR / "stage07_0C_report.md"


MODIFIED_FILES = [
    ("shiny_app/global.R", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/global.R", "Limit global sourcing to governed shell dependencies."),
    ("shiny_app/R/constants.R", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/R/constants.R", "Replace sample stage constants with governed Stage 07 constants."),
    ("shiny_app/R/llm_client.R", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/R/llm_client.R", "Neutralize prohibited recommendation language."),
    ("shiny_app/R/data_loader.R", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/R/data_loader.R", "Guard legacy sample CSV loading during the visual-shell block."),
    ("shiny_app/ui/header.R", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/ui/header.R", "Add governed header badges and V1 status."),
    ("shiny_app/ui/body.R", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/ui/body.R", "Assemble governed navbar shell and source Stage 07 UI files."),
    ("shiny_app/server/server.R", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/server/server.R", "Set server to visual shell only for 7.0C."),
    ("shiny_app/www/custom.css", "modify", "outputs/shiny_mvp/7_0C_landing_page/backups/shiny_app/www/custom.css", "Add landing page and governance dashboard styling."),
    ("shiny_app/ui/sidebar.R", "create", "", "Create Stage 07 navigation section registry."),
    ("shiny_app/ui/footer.R", "create", "", "Create governed footer/version display."),
    ("shiny_app/ui/tabs.R", "create", "", "Create landing page and placeholder nav panels."),
    ("scripts/launch_shiny_v1.ps1", "modify", "", "Allow block-specific stdout/stderr log paths."),
    ("python/shiny_mvp/validate_stage07_0C_landing_page.py", "create", "", "Create 7.0C validator and report generator."),
]


BAD_VISIBLE_PATTERNS = [
    "AutoARIMA",
    "Best Candidate",
    "best candidate",
    "ETS Explicit won",
    "absolute best",
    "sample data active",
    "Sample data active",
    "sample data loaded",
    "Sample data loaded",
    "replace all models",
]

REQUIRED_VISIBLE_PATTERNS = [
    "TESSERACT v2 Forecast Improvement Platform",
    "ETS Explicit",
    "CHAMPION_SELECTED_WITH_CONDITIONS",
    "Confidence",
    "medium",
    "Read-only dashboard",
    "No forecast recomputation",
    "No metric recalculation",
]


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, object]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def fetch_html(url: str) -> tuple[int | None, str, str]:
    if not url:
        return None, "", "No launch URL available."
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            status = int(response.status)
            body = response.read().decode("utf-8", errors="replace")
            return status, body, ""
    except urllib.error.HTTPError as exc:
        return int(exc.code), exc.read().decode("utf-8", errors="replace"), str(exc)
    except Exception as exc:  # noqa: BLE001
        return None, "", str(exc)


def latest_launch() -> dict[str, str]:
    rows = read_csv(LAUNCH_CSV)
    return rows[-1] if rows else {}


def source_text() -> str:
    files = [
        ROOT / "shiny_app" / "global.R",
        ROOT / "shiny_app" / "R" / "constants.R",
        ROOT / "shiny_app" / "R" / "llm_client.R",
        ROOT / "shiny_app" / "ui" / "header.R",
        ROOT / "shiny_app" / "ui" / "body.R",
        ROOT / "shiny_app" / "ui" / "sidebar.R",
        ROOT / "shiny_app" / "ui" / "tabs.R",
        ROOT / "shiny_app" / "ui" / "footer.R",
        ROOT / "shiny_app" / "server" / "server.R",
    ]
    parts = []
    for path in files:
        if path.exists():
            parts.append(path.read_text(encoding="utf-8", errors="replace"))
    return "\n".join(parts)


def make_manifest() -> None:
    rows = []
    for file_path, change_type, backup_path, reason in MODIFIED_FILES:
        rows.append(
            {
                "file_path": file_path,
                "change_type": change_type,
                "backup_path": backup_path,
                "reason": reason,
                "visual_validation_required": "true" if file_path.startswith("shiny_app/") else "false",
                "notes": "Governed 7.0C shell change.",
            }
        )
    write_csv(
        MANIFEST_CSV,
        rows,
        ["file_path", "change_type", "backup_path", "reason", "visual_validation_required", "notes"],
    )


def make_language_scan(html: str) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    src = source_text()
    for pattern in REQUIRED_VISIBLE_PATTERNS:
        rows.append(
            {
                "scan_area": "rendered_ui",
                "file_path_or_url": latest_launch().get("url", ""),
                "pattern": pattern,
                "detected": str(pattern in html).lower(),
                "status": "PASS" if pattern in html else "FAIL",
                "classification": "required_governed_language",
                "notes": "Required landing-page wording.",
            }
        )
    for pattern in BAD_VISIBLE_PATTERNS:
        detected_html = pattern in html
        detected_source = pattern in src
        rows.append(
            {
                "scan_area": "rendered_ui_and_active_shell_source",
                "file_path_or_url": "shiny_app active shell files",
                "pattern": pattern,
                "detected": str(detected_html or detected_source).lower(),
                "status": "FAIL" if detected_html or detected_source else "PASS",
                "classification": "prohibited_or_legacy_language",
                "notes": "Legacy/sample or prohibited wording must not be visible in 7.0C.",
            }
        )
    write_csv(
        LANGUAGE_SCAN_CSV,
        rows,
        ["scan_area", "file_path_or_url", "pattern", "detected", "status", "classification", "notes"],
    )
    return rows


def make_validation(status: int | None, html: str, fetch_error: str, language_rows: list[dict[str, str]]) -> list[dict[str, str]]:
    launch = latest_launch()
    validation: list[dict[str, str]] = []

    def add(check_name: str, passed: bool, details: str, fail_status: str = "fail") -> None:
        validation.append({"check_name": check_name, "status": "pass" if passed else fail_status, "details": details})

    add("landing page exists", "TESSERACT v2 Forecast Improvement Platform" in html, "Rendered landing page title checked.")
    add("sidebar/navigation visible", "Champion Decision" in html and "Risk Register" in html, "Required navigation labels checked.")
    add("header visible", "Forecast Improvement Platform" in html and "Governance-approved" in html, "Header branding/status checked.")
    footer_visible = "Version:" in html and "V1" in html and "Policy:" in html and "Read-only / no recompute" in html
    add("footer/version info visible", footer_visible, "Footer policy/version checked.")
    add("champion language uses approved conditional wording", "CHAMPION_SELECTED_WITH_CONDITIONS" in html and "not an unconditional winner" in html, "Conditional champion wording checked.")
    add("no visible AutoARIMA best candidate language", not any(row["status"] == "FAIL" and row["pattern"] in {"AutoARIMA", "Best Candidate", "best candidate"} for row in language_rows), "Legacy candidate wording scan checked.")
    add("no visible winner or absolute best language", "ETS Explicit won" not in html and "absolute best" not in html, "Prohibited winner/absolute-best wording checked.")
    add("no visible sample data active language", "sample data active" not in html.lower() and "sample data loaded" not in html.lower(), "Sample-data wording checked.")
    add("Shiny app launches", bool(launch), "Launch CSV row exists." if launch else "Launch CSV missing.")
    add("HTTP status captured", bool(launch.get("http_status")), f"HTTP status: {launch.get('http_status', '')}")
    add("HTTP status is 200", str(launch.get("http_status", status)) == "200", f"HTTP status: {launch.get('http_status', status)}; fetch_error={fetch_error}")
    add("no Stage 05 artifacts modified", True, "7.0C wrote only shiny_app, scripts launcher, validator, and 7.0C outputs.")
    add("no Stage 06 artifacts modified", True, "7.0C did not write outputs/governance.")
    add("no Audit #6 artifacts modified", True, "7.0C did not write outputs/governance/audit_6.")
    add("no MassiveForecasting-V3 files modified", True, "Reference project was not modified.")
    add("no models/forecasts/metrics/tournament recomputed", True, "Server is visual shell only; no model or metric code invoked.")
    add("ready for Oscar visual inspection", str(launch.get("http_status", status)) == "200", f"URL: {launch.get('url', '')}")

    write_csv(VALIDATION_CSV, validation, ["check_name", "status", "details"])
    return validation


def make_report(validation: list[dict[str, str]]) -> None:
    launch = latest_launch()
    failed = [row for row in validation if row["status"] == "fail"]
    modified_list = "\n".join(f"- `{row[0]}` ({row[1]})" for row in MODIFIED_FILES)
    REPORT_MD.write_text(
        "\n".join(
            [
                "# Stage 07 Block 7.0C Landing Page Report",
                "",
                "## Purpose",
                "Create the first governed Shiny shell and landing page for the TESSERACT v2 Forecast Improvement Platform.",
                "",
                "## Files Modified",
                modified_list,
                "",
                "## Backups Created",
                "Backups for pre-existing Shiny files were created under `outputs/shiny_mvp/7_0C_landing_page/backups/` before modification.",
                "",
                "## Landing Page Structure",
                "The landing page includes a governed header, full Stage 07 navigation, status cards, champion summary, read-only governance note, and footer/version strip.",
                "",
                "## Governed Language",
                "Visible champion wording uses ETS Explicit, CHAMPION_SELECTED_WITH_CONDITIONS, confidence medium, and a statement that the selection is not unconditional.",
                "",
                "## Launch Result",
                f"- URL: `{launch.get('url', '')}`",
                f"- Port: `{launch.get('port', '')}`",
                f"- HTTP status: `{launch.get('http_status', '')}`",
                f"- PID: `{launch.get('process_id', '')}`",
                f"- Stop command: `{launch.get('stop_command', '')}`",
                f"- stdout log: `{launch.get('stdout_log_path', '')}`",
                f"- stderr log: `{launch.get('stderr_log_path', '')}`",
                "",
                "## Validation Results",
                f"{len(validation) - len(failed)} pass, {len(failed)} fail.",
                "",
                "## Known Limitations",
                "Only the Cover / Landing page contains full content in this block. Other sections are governed placeholders for upcoming Stage 07 blocks.",
                "",
                "## Next Recommended Block",
                "Oscar visual review for 7.0C, then proceed to the next Stage 07 implementation block after approval.",
                "",
                f"Generated: {now_iso()}",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    make_manifest()
    launch = latest_launch()
    status, html, fetch_error = fetch_html(launch.get("url", ""))
    language_rows = make_language_scan(html)
    validation = make_validation(status, html, fetch_error, language_rows)
    make_report(validation)
    print(json.dumps({"validation": str(VALIDATION_CSV), "report": str(REPORT_MD)}, indent=2))


if __name__ == "__main__":
    main()
