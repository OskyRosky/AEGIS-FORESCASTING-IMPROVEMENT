# AEGIS V5.5 — Safe Refresh Command Decision

## Decision
Use a **dedicated V5.5 validate-only wrapper** as the refresh service command,
with the orchestrator's `--dry-run` as an embedded safe sub-proof.

Command (image CMD): `python /app/scripts/refresh_validate_only.py`
One-shot run: `docker compose run --rm refresh`

## Why not the existing modes directly

| Option | Verdict | Reason |
|--------|---------|--------|
| `--dry-run` alone | insufficient | Genuinely safe (pure print), but does not validate mounts/contracts/artifact presence that V5.5 must prove. |
| `--validate` | rejected | Safe re SQL/models/promote, but writes run-dirs under `outputs/v3_3_daily_refresh/` (outside the V5.5 output area, violating rule 12) and pulls pandas. |
| `--execute-staging` / `--promote` | forbidden | Real SQL / models / promote. |

## What the wrapper does (safe by construction)
- Validates: orchestrator present; `data/processed` present **and read-only**
  (write probe must fail); `data/raw` **absent**; required artifacts present;
  V5.5 output dir writable.
- Asserts **no SQL capability**: `import pyodbc` must fail (not installed).
- Asserts **no SQL/Azure/secret env** variables are set.
- Static-scans the orchestrator to confirm the dangerous flags exist and are
  gated (documentation only — never passes them).
- Invokes `--dry-run` (pure print) and asserts `DRY_RUN_OK` + that
  `data/processed` / `data/raw` hashes are unchanged before/after.
- Writes only to `outputs/v5_5_refresh_service_validate/`.
- Prints an explicit banner and, on any failure, exits non-zero with
  `V5_5_REFRESH_VALIDATE_BLOCKER` (rule 30: stop and report, never proceed
  silently).

## Guarantees
NO SQL · NO ODBC/pyodbc · NO Entra/MFA · NO models · NO promote ·
NO mutation of `data/processed` or `data/raw`.
