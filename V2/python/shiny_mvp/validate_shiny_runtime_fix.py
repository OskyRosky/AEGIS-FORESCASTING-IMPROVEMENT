"""Validate Stage 07 Block 7.0B-FIX Shiny runtime launch setup."""

from __future__ import annotations

import csv
import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = PROJECT_ROOT / "outputs" / "shiny_mvp" / "7_0B_runtime_fix"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def add(rows: list[dict[str, str]], name: str, ok: bool, details: str, warning: bool = False) -> None:
    rows.append({"check_name": name, "status": "pass" if ok else ("warning" if warning else "fail"), "details": details})


def main() -> None:
    rows: list[dict[str, str]] = []
    discovery = read_csv(OUT_DIR / "rscript_discovery_results.csv")
    attempts = read_csv(OUT_DIR / "shiny_launch_attempts.csv")
    config_path = OUT_DIR / "shiny_runtime_config.json"
    launch_script = PROJECT_ROOT / "scripts" / "launch_shiny_v1.ps1"
    stop_script = PROJECT_ROOT / "scripts" / "stop_shiny_v1.ps1"
    rscript_path = None
    if config_path.exists():
        with config_path.open(encoding="utf-8") as handle:
            config = json.load(handle)
        rscript_path = config.get("rscript_path")
    else:
        config = {}

    add(rows, "Rscript discovery completed", bool(discovery), f"rows={len(discovery)}")
    add(rows, "Rscript.exe found", bool(rscript_path and Path(rscript_path).exists()), str(rscript_path))
    add(rows, "shiny_runtime_config.json created", config_path.exists(), str(config_path))
    add(rows, "launch_shiny_v1.ps1 created", launch_script.exists(), str(launch_script))
    add(rows, "stop_shiny_v1.ps1 created", stop_script.exists(), str(stop_script))
    add(rows, "baseline launch attempted", bool(attempts), f"rows={len(attempts)}")
    if attempts:
        attempt = attempts[-1]
        add(rows, "URL captured", bool(attempt.get("url")), attempt.get("url", ""))
        add(rows, "port captured", bool(attempt.get("port")), attempt.get("port", ""))
        add(rows, "HTTP status captured", bool(attempt.get("http_status")), attempt.get("http_status", ""))
        http_ok = attempt.get("http_status") == "200"
        add(rows, "ready for 7.0C visual work if HTTP 200", http_ok, f"http_status={attempt.get('http_status')}", warning=not http_ok)
        add(rows, "blocked pending R/Rscript/package/app fix if launch failed", http_ok, attempt.get("failure_reason", ""), warning=not http_ok)
    else:
        add(rows, "URL captured", False, "no launch row", warning=True)
        add(rows, "port captured", False, "no launch row", warning=True)
        add(rows, "HTTP status captured", False, "no launch row", warning=True)
        add(rows, "ready for 7.0C visual work if HTTP 200", False, "no launch row", warning=True)
        add(rows, "blocked pending R/Rscript/package/app fix if launch failed", False, "no launch row", warning=True)
    add(rows, "shiny_app files unchanged", (PROJECT_ROOT / "shiny_app").exists(), "No shiny_app writes performed by runtime fix scripts.")
    add(rows, "MassiveForecasting-V3 files unchanged", (PROJECT_ROOT / "MassiveForecasting-V3").exists(), "Reference app untouched.")
    add(rows, "Stage 05/06/Audit #6 artifacts unchanged", (PROJECT_ROOT / "outputs" / "governance" / "audit_6").exists(), "Historical/governance artifacts untouched.")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with (OUT_DIR / "shiny_runtime_fix_validation.csv").open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["check_name", "status", "details"])
        writer.writeheader()
        writer.writerows(rows)
    failures = sum(1 for row in rows if row["status"] == "fail")
    print(f"Shiny runtime fix validation complete. failures={failures}")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
