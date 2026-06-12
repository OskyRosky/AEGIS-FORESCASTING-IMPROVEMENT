"""Block 5.29B-Fix - Dependency Resolution artifacts.

Probes the installed forecasting backends (real imports + versions), determines
which challengers became sandbox-runnable, and writes the dependency-resolution
artifacts. This script never runs models and never modifies protected outputs.
"""

from __future__ import annotations

import importlib
import importlib.util
from datetime import datetime

from model_lab.run_challenger_sandbox import (
    DEPENDENCY_OPTIONS,
    _first_available_option,
    _module_available,
)
from utils.logger import get_logger
from utils.paths import PROJECT_ROOT

logger = get_logger("challenger_dependency_resolution")

MODEL_LAB_DIR = PROJECT_ROOT / "outputs" / "model_lab"
RESOLUTION_DIR = MODEL_LAB_DIR / "challenger_dependency_resolution"

RUN_ID = "challenger_dependency_resolution"

# Every dependency we attempted to resolve, and the challengers that rely on it.
DEPENDENCY_CONSUMERS: dict[str, list[str]] = {
    "statsmodels": ["ETS Explicit"],
    "statsforecast": ["AutoARIMA (alt)", "Theta (alt)", "ETS Explicit (alt)"],
    "pmdarima": ["AutoARIMA"],
    "darts": ["Theta", "NBEATS (alt)"],
    "lightgbm": ["LightGBM"],
    "xgboost": ["XGBoost"],
    "torch": ["NBEATS", "NHITS"],
    "neuralforecast": ["NHITS", "NBEATS (alt)"],
}

# Installation commands executed during this block (for the audit log).
INSTALL_COMMANDS = [
    "python -m pip install --upgrade pip setuptools wheel",
    "python -m pip install statsmodels statsforecast lightgbm xgboost torch "
    "neuralforecast darts pmdarima  (combined attempt - failed on scipy source "
    "build for statsforecast)",
    "python -m pip install statsmodels lightgbm xgboost pmdarima  (succeeded)",
    "python -m pip install torch  (succeeded)",
    "python -m pip install neuralforecast  (installed legacy 0.1.0 - incompatible)",
    "python -m pip install statsforecast  (failed - scipy source build needs C "
    "compiler not present)",
    "python -m pip install darts  (succeeded)",
    "python -m pip install neuralforecast==1.7.6  (failed - requires ray>=2.2.0 "
    "with no Python 3.14 wheel)",
]


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S")


def _version_of(name: str) -> str:
    if importlib.util.find_spec(name) is None:
        return ""
    try:
        mod = importlib.import_module(name)
        return str(getattr(mod, "__version__", "unknown"))
    except Exception:  # noqa: BLE001
        return "installed_but_import_failed"


def _import_status(name: str) -> tuple[bool, str, str]:
    """Return (available, status, notes)."""
    spec = importlib.util.find_spec(name)
    if spec is None:
        return False, "missing", "package not installed"
    try:
        importlib.import_module(name)
        return True, "available", "import succeeded"
    except Exception as exc:  # noqa: BLE001
        return (
            False,
            "installed_but_broken",
            f"import failed: {type(exc).__name__}: {exc}",
        )


def _build_import_check() -> list[dict]:
    ts = _now()
    rows = []
    for dep in sorted(DEPENDENCY_CONSUMERS):
        available, status, notes = _import_status(dep)
        rows.append(
            {
                "dependency_name": dep,
                "required_by": "; ".join(DEPENDENCY_CONSUMERS[dep]),
                "import_available": available,
                "version_detected": _version_of(dep) if available else "",
                "status": status,
                "notes": notes,
                "created_timestamp": ts,
            }
        )
    return rows


def _model_runnability() -> tuple[list[str], list[str]]:
    runnable, blocked = [], []
    for model in DEPENDENCY_OPTIONS:
        if _first_available_option(model) is not None:
            runnable.append(model)
        else:
            blocked.append(model)
    return runnable, blocked


def _write_csv(path, rows: list[dict], columns: list[str]) -> None:
    import csv

    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def _build_installation_log(import_rows: list[dict]) -> str:
    lines = [
        "# Challenger Dependency Installation Log (Block 5.29B-Fix)",
        "",
        f"Generated: {_now()}",
        "",
        "## Environment",
        "",
        "- Python: 3.14.6 (pythoncore-3.14-64)",
        "- pip: 26.1.2",
        "- Install scope: project interpreter (user-approved).",
        "",
        "## Commands Executed",
        "",
    ]
    for cmd in INSTALL_COMMANDS:
        lines.append(f"- `{cmd}`")
    lines += [
        "",
        "## Packages Installed Successfully",
        "",
        "- statsmodels, pmdarima, lightgbm, xgboost (prebuilt cp314 wheels)",
        "- torch 2.12.0+cpu",
        "- darts 0.44.1 (+ scikit-learn, scipy 1.17.1, statsmodels, xarray, shap)",
        "",
        "## Packages Failed / Unresolved",
        "",
        "- **statsforecast**: build aborted - its dependency resolution pulled "
        "scipy 1.15.3 as a source tarball, which needs a C/Fortran compiler "
        "(MSVC) that is not installed. Optional: AutoARIMA/ETS/Theta are covered "
        "by pmdarima / statsmodels / darts respectively.",
        "- **neuralforecast (modern)**: 1.7.6 requires `ray>=2.2.0`, which has no "
        "Python 3.14 wheel. Pip backtracked to the legacy 0.1.0, which is "
        "incompatible with the installed pytorch-lightning 2.6.5 "
        "(`pytorch_lightning.utilities.distributed` removed). NHITS depends only "
        "on neuralforecast, so it remains blocked.",
        "",
        "## Important Warnings",
        "",
        "- Console-script shims were installed to a Scripts dir not on PATH "
        "(cosmetic; imports unaffected).",
        "- hyperopt emits a `pkg_resources` deprecation warning (cosmetic).",
        "",
        "## Final Import Status",
        "",
        "| dependency | available | version | status |",
        "| --- | --- | --- | --- |",
    ]
    for r in import_rows:
        lines.append(
            f"| {r['dependency_name']} | {r['import_available']} | "
            f"{r['version_detected'] or '-'} | {r['status']} |"
        )
    return "\n".join(lines) + "\n"


def _build_report(
    import_rows: list[dict], runnable: list[str], blocked: list[str]
) -> str:
    avail = [r["dependency_name"] for r in import_rows if r["import_available"]]
    missing = [r["dependency_name"] for r in import_rows if not r["import_available"]]
    proceed = len(runnable) > 0
    lines = [
        "# Challenger Dependency Resolution Report (Block 5.29B-Fix)",
        "",
        f"Generated: {_now()}",
        "",
        "## Installation Outcome",
        "",
        f"- Dependencies importable: {avail}",
        f"- Dependencies unresolved: {missing}",
        "",
        "## Challengers Now Sandbox-Runnable",
        "",
    ]
    for m in runnable:
        opt = _first_available_option(m)
        lines.append(f"- {m} (backend: {opt})")
    lines += [
        "",
        "## Challengers Still Blocked",
        "",
    ]
    if blocked:
        for m in blocked:
            lines.append(
                f"- {m} (no importable backend; requires one of "
                f"{DEPENDENCY_OPTIONS[m]})"
            )
    else:
        lines.append("- None.")
    lines += [
        "",
        "## Can Sandbox Proceed?",
        "",
        (
            f"Yes - {len(runnable)} of {len(DEPENDENCY_OPTIONS)} challengers can run "
            "in the sandbox. Re-run the sandbox; remaining blocked models stay "
            "documented."
            if proceed
            else "No - no challenger has an importable backend."
        ),
        "",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    logger.info("=== Block 5.29B-Fix - Dependency Resolution ===")
    RESOLUTION_DIR.mkdir(parents=True, exist_ok=True)

    import_rows = _build_import_check()
    _write_csv(
        RESOLUTION_DIR / "dependency_import_check.csv",
        import_rows,
        ["dependency_name", "required_by", "import_available", "version_detected",
         "status", "notes", "created_timestamp"],
    )

    runnable, blocked = _model_runnability()
    ts = _now()
    summary_rows = [
        {
            "run_id": RUN_ID,
            "dependencies_attempted": len(import_rows),
            "dependencies_available": sum(
                1 for r in import_rows if r["import_available"]
            ),
            "dependencies_missing": sum(
                1 for r in import_rows if not r["import_available"]
            ),
            "models_now_sandbox_runnable": len(runnable),
            "models_still_blocked": len(blocked),
            "created_timestamp": ts,
        }
    ]
    _write_csv(
        RESOLUTION_DIR / "dependency_resolution_summary.csv",
        summary_rows,
        ["run_id", "dependencies_attempted", "dependencies_available",
         "dependencies_missing", "models_now_sandbox_runnable",
         "models_still_blocked", "created_timestamp"],
    )

    (RESOLUTION_DIR / "dependency_installation_log.md").write_text(
        _build_installation_log(import_rows), encoding="utf-8"
    )
    (RESOLUTION_DIR / "dependency_resolution_report.md").write_text(
        _build_report(import_rows, runnable, blocked), encoding="utf-8"
    )

    logger.info("Dependencies available: %d / %d", summary_rows[0][
        "dependencies_available"], len(import_rows))
    logger.info("Models now sandbox-runnable: %s", runnable)
    logger.info("Models still blocked: %s", blocked)


if __name__ == "__main__":
    main()
