# AEGIS V5.5 — Refresh Code Audit Report

## Scope
Audited the existing refresh/orchestration code **statically** (no productive
execution) to classify what is safe for the V5.5 validate-only service.

## Orchestrator: `python/orchestration/run_daily_refresh_orchestrator.py`

Argparse modes and their dispatch (main → line ~560):

| Flag | Dispatch | SQL | Auth | Models | Mutation | Promote | Safe for V5.5 |
|------|----------|-----|------|--------|----------|---------|---------------|
| `--dry-run` | `do_dry_run()` | no | no | no | no (print only) | no | **YES** |
| `--validate` | `do_run(execute=False, smoke=True)` | no | no | no (VALIDATE_SKIP) | writes run-dir **outside V5.5** | no | partial (rejected) |
| `--execute-staging --allow-execute` | `do_run(execute=True)` | **live SQL** (S01) | **Entra/MFA** | **runs models** | staging writes | no | **NO** |
| `--promote --allow-promote` | `do_promote()` | no | no | no | **mutates data/processed** | **PROMOTE** | **NO** |

### Key findings
1. **Module import is side-effect-free.** All heavy imports (`pandas`,
   `pyodbc` via `export_hdd_region`, `model_registry`) are **lazy**, inside
   functions. Importing the orchestrator does not open SQL or load models.
2. **`--dry-run` is genuinely safe** — `do_dry_run()` only prints the plan and
   `DRY_RUN_OK`. No writes, no SQL, no models. Used as the V5.5 sub-proof.
3. **`--validate` is safe re SQL/models/promote/productive-mutation** but it
   creates run directories under `outputs/v3_3_daily_refresh/...` (outside the
   V5.5 output area) and imports pandas → **not used in V5.5**.
4. **SQL entry point** = `stage_ingestion` → `export_hdd_region.export_hdd_region()`
   → `pyodbc` + ODBC Driver 18 + `ActiveDirectoryInteractive` (Entra/MFA).
   Only reachable via `--execute-staging --allow-execute` → **never run**.
5. **Model entry points** = `stage_baseline`/`stage_challengers` →
   `model_registry.get_model` (top-imports prohibited models). Only via
   `--execute-staging` → **never run**.
6. **Promote** = `do_promote` robocopies candidate → `data/processed` and writes
   `run_metadata` → **never run**.

## V5.5 decision
Because the only fully side-effect-free existing mode (`--dry-run`) does not
also validate mounts/contracts, a dedicated **stdlib-only validate-only
wrapper** (`scripts/refresh_validate_only.py`) was created (Task C Preference 2).
It validates architecture + mounts + contracts and invokes `--dry-run` as a
safe sub-proof. It NEVER imports the SQL/model modules and NEVER passes the
dangerous flags. The refresh image contains **no pyodbc / no pandas / no ML**,
so SQL is impossible by construction.
