#!/usr/bin/env python3
# =====================================================================
# AEGIS V5.5 | scripts/refresh_validate_only.py
# ---------------------------------------------------------------------
# VALIDATE-ONLY refresh wrapper for the separated Docker "refresh" service.
# It proves the refresh ARCHITECTURE (paths, mounts, contracts, safe flag)
# WITHOUT doing any real refresh work:
#   - NO SQL, NO ODBC/pyodbc connection, NO Entra/MFA
#   - NO model training / model runner
#   - NO promote
#   - NO mutation of data/processed or data/raw
#   - writes ONLY to outputs/v5_5_refresh_service_validate/ (or stdout)
#
# It also invokes the existing orchestrator's SAFE `--dry-run` mode
# (do_dry_run() = pure print, no SQL/models/writes) as a sub-proof that a
# governed safe mode exists and runs in the container. It NEVER runs
# --validate / --execute-staging / --promote.
#
# If anything unsafe is detected or attempted, it STOPS and reports a
# BLOCKER (non-zero exit) instead of proceeding silently.
# =====================================================================
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

APP = Path("/app") if Path("/app/shiny_app").exists() else Path(__file__).resolve().parents[1]
ORCH = APP / "python" / "orchestration" / "run_daily_refresh_orchestrator.py"
DATA_PROCESSED = APP / "data" / "processed"
DATA_RAW = APP / "data" / "raw"
OUT_DIR = APP / "outputs" / "v5_5_refresh_service_validate"

REQUIRED_ARTIFACTS = [
    "data/processed/forecasts.csv",
    "data/processed/actuals.csv",
    "data/processed/entities.csv",
    "data/processed/run_metadata.csv",
    "data/processed/model_universe_canonical.csv",
]

DANGEROUS_FLAGS = ["--execute-staging", "--allow-execute", "--promote", "--allow-promote"]
SQL_ENV_KEYS = ["SQL", "ODBC", "AZURE", "ENTRA", "MSSQL", "DB_PASSWORD", "CALCULATE_TTL_KEY",
                "OPENAI", "PYODBC"]

results = []


def add(check, expected, observed, ok, evidence=""):
    results.append({"check": check, "expected": expected, "observed": str(observed),
                    "status": "PASS" if ok else "FAIL", "evidence": evidence})
    return ok


def dir_hash(p: Path) -> str:
    if not p.exists():
        return "MISSING"
    h = hashlib.sha256()
    for f in sorted(p.rglob("*")):
        if f.is_file():
            h.update(f.name.encode())
            h.update(str(f.stat().st_size).encode())
    return h.hexdigest()[:32]


def main() -> int:
    banner = "AEGIS V5.5 REFRESH VALIDATE-ONLY | NO_SQL | NO_MODELS | NO_PROMOTE | NO_MUTATION"
    print("=" * len(banner))
    print(banner)
    print("=" * len(banner))
    print(f"timestamp: {datetime.now(timezone.utc).isoformat()}")
    print(f"app_root : {APP}")

    all_ok = True

    # 1) orchestrator present
    all_ok &= add("orchestrator_present", "exists", ORCH.exists(),
                  ORCH.exists(), str(ORCH))

    # 2) data/processed present + READ-ONLY (write attempt must fail)
    proc_exists = DATA_PROCESSED.exists()
    add("data_processed_present", "exists", proc_exists, proc_exists, str(DATA_PROCESSED))
    ro_ok = False
    if proc_exists:
        probe = DATA_PROCESSED / "_v5_5_write_probe.tmp"
        try:
            probe.write_text("x")
            probe.unlink(missing_ok=True)
            ro_ok = False  # write succeeded -> NOT read-only -> unsafe
        except Exception:
            ro_ok = True   # write blocked -> read-only -> safe
    all_ok &= add("data_processed_read_only", "write blocked", "READONLY" if ro_ok else "WRITABLE",
                  ro_ok, "attempted write to mount")

    # 3) data/raw NOT present in container
    raw_absent = not DATA_RAW.exists()
    all_ok &= add("data_raw_absent", "absent", "absent" if raw_absent else "PRESENT",
                  raw_absent, str(DATA_RAW))

    # 4) required artifacts readable
    missing = [a for a in REQUIRED_ARTIFACTS if not (APP / a).exists()]
    all_ok &= add("required_artifacts_present", "all present",
                  f"{len(REQUIRED_ARTIFACTS)-len(missing)}/{len(REQUIRED_ARTIFACTS)}",
                  not missing, f"missing={missing}")

    # 5) NO SQL capability: pyodbc must NOT be importable in the refresh image
    pyodbc_absent = False
    try:
        import pyodbc  # noqa: F401
        pyodbc_absent = False
    except Exception:
        pyodbc_absent = True
    all_ok &= add("pyodbc_absent", "not installed (no SQL capability)",
                  "absent" if pyodbc_absent else "PRESENT", pyodbc_absent,
                  "import pyodbc")

    # 6) NO SQL/Azure/secret env vars set
    hot = sorted({k for k in os.environ for s in SQL_ENV_KEYS if s in k.upper()})
    all_ok &= add("no_sql_azure_env", "none", hot or "none", not hot, "env scan")

    # 7) dangerous flags are documented/gated in the orchestrator (static scan only)
    flags_found = []
    if ORCH.exists():
        txt = ORCH.read_text(encoding="utf-8", errors="ignore")
        flags_found = [f for f in DANGEROUS_FLAGS if f in txt]
    add("dangerous_flags_documented", "present + gated", flags_found, bool(flags_found),
        "static scan; wrapper never passes them")

    # 8) capture data baselines BEFORE the safe dry-run
    proc_before = dir_hash(DATA_PROCESSED)
    raw_before = dir_hash(DATA_RAW)

    # 9) invoke the orchestrator SAFE --dry-run (pure print; no SQL/models/writes)
    dry_ok = False
    dry_out = ""
    if ORCH.exists():
        try:
            env = dict(os.environ)
            env["PYTHONPATH"] = str(APP / "python")
            cp = subprocess.run([sys.executable, str(ORCH), "--dry-run"],
                                capture_output=True, text=True, timeout=120, env=env)
            dry_out = (cp.stdout or "") + (cp.stderr or "")
            dry_ok = (cp.returncode == 0 and "DRY_RUN_OK" in dry_out
                      and "PROHIBITED never executed" in dry_out)
        except Exception as exc:
            dry_out = f"ERROR: {exc}"
            dry_ok = False
    all_ok &= add("orchestrator_dry_run_safe", "DRY_RUN_OK (no SQL/models)",
                  "OK" if dry_ok else "FAIL", dry_ok, "subprocess --dry-run")

    # 10) prove the dry-run did NOT mutate data
    proc_after = dir_hash(DATA_PROCESSED)
    raw_after = dir_hash(DATA_RAW)
    all_ok &= add("data_processed_unchanged", proc_before, proc_after,
                  proc_before == proc_after, "hash before==after")
    all_ok &= add("data_raw_unchanged", raw_before, raw_after,
                  raw_before == raw_after, "hash before==after")

    # 11) output dir writable (granular V5.5 area only)
    out_ok = False
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "_write_ok.tmp").write_text("ok")
        (OUT_DIR / "_write_ok.tmp").unlink(missing_ok=True)
        out_ok = True
    except Exception:
        out_ok = False
    add("v5_5_output_dir_writable", "writable", out_ok, out_ok, str(OUT_DIR))

    # --- report ---
    payload = {
        "stage": "V5.5",
        "mode": "validate_only",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "no_sql": True, "no_models": True, "no_promote": True, "no_mutation": True,
        "all_pass": all_ok,
        "checks": results,
        "dry_run_tail": dry_out.strip().splitlines()[-6:] if dry_out else [],
    }
    try:
        OUT_DIR.mkdir(parents=True, exist_ok=True)
        (OUT_DIR / "v5_5_refresh_validate_report.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"WARN: could not write report: {exc}")

    print("-" * 60)
    for r in results:
        print(f"  [{r['status']}] {r['check']}: {r['observed']}")
    print("-" * 60)
    print(f"RESULT: {'ALL_PASS' if all_ok else 'HAS_FAIL'}")
    print("VALIDATE_ONLY | NO_SQL | NO_MODELS | NO_PROMOTE | NO_MUTATION")
    if not all_ok:
        print("V5_5_REFRESH_VALIDATE_BLOCKER")
        return 1
    print("V5_5_REFRESH_VALIDATE_OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
