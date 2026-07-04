# AEGIS V5.5 — Refresh Validate-Only Output

Run: `docker compose run --rm refresh` → exit code **0**.

```
================================================================================
AEGIS V5.5 REFRESH VALIDATE-ONLY | NO_SQL | NO_MODELS | NO_PROMOTE | NO_MUTATION
================================================================================
timestamp: 2026-07-03T19:45:01Z
app_root : /app
------------------------------------------------------------
  [PASS] orchestrator_present: True
  [PASS] data_processed_present: True
  [PASS] data_processed_read_only: READONLY
  [PASS] data_raw_absent: absent
  [PASS] required_artifacts_present: 5/5
  [PASS] pyodbc_absent: absent
  [PASS] no_sql_azure_env: none
  [PASS] dangerous_flags_documented: ['--execute-staging','--allow-execute','--promote','--allow-promote']
  [PASS] orchestrator_dry_run_safe: OK
  [PASS] data_processed_unchanged: a2c95a6f46d54c7e9a7b51696c9fe1a3
  [PASS] data_raw_unchanged: MISSING
  [PASS] v5_5_output_dir_writable: True
------------------------------------------------------------
RESULT: ALL_PASS
VALIDATE_ONLY | NO_SQL | NO_MODELS | NO_PROMOTE | NO_MUTATION
V5_5_REFRESH_VALIDATE_OK
```

Notes:
- `data_processed_unchanged` uses the container-side content hash
  (`a2c95a...`, name+size digest) before/after the dry-run — identical.
- `data_raw_unchanged: MISSING == MISSING` because `data/raw` is intentionally
  not mounted into the refresh container (absent before and after) — consistent
  with "no data/raw mount".
- The report JSON is written to
  `outputs/v5_5_refresh_service_validate/v5_5_refresh_validate_report.json`.
- No SQL/ODBC/Entra/MFA/model/promote was attempted at any point.
