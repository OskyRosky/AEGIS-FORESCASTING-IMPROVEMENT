# AEGIS V5.5 — Refresh Image Strategy

## Decision: build a SEPARATE minimal Python image `aegis-refresh:v5.5`

- **Base:** `python:3.12-slim`.
- **Purpose:** run the validate-only wrapper (+ orchestrator `--dry-run`),
  which are **stdlib-only** → **zero pip installs**.
- **Size:** ~180 MB.

## Governance requirements (all met)

| Requirement | Status |
|-------------|--------|
| Do NOT put Python in the dashboard image | met — dashboard stays R-only (`aegis-dashboard:v5.1` unchanged, NO_PYTHON) |
| Separate image | met — `aegis-refresh:v5.5` (own Dockerfile.refresh) |
| No torch / darts / lightgbm / xgboost / sklearn | met — no pip installs at all |
| No pyodbc / ODBC (no SQL in V5.5) | met — `import pyodbc` fails in the image |
| No pandas (validate-only is stdlib) | met — `import pandas` fails |
| No data/raw copied | met — not baked, not mounted |
| No secrets baked | met — 0 secret patterns in history |
| No productive artifacts baked | met — data/processed + outputs are runtime mounts |
| Workdir /app | met |
| Safe validate-only command | met — CMD = refresh_validate_only.py |

## Build context

Uses a dedicated **`Dockerfile.refresh.dockerignore`** so the refresh build can
see `python/` + `scripts/` + `config/` (which the dashboard `.dockerignore`
strips) while still excluding all heavy data, governed outputs, the R app,
backups, and caches. The dashboard `.dockerignore` is **not modified**.

## Copied into the image
`python/`, `scripts/refresh_validate_only.py`, `config/`,
`ACTIVE_PROJECT_ROOT.md`, `VERSION_INFO.md`. Nothing else.

## Future (V5.6+, gated)
Real refresh will require adding `pyodbc` + ODBC Driver 18 + `pandas` (+ an
approved non-interactive auth strategy). Each dependency must be justified and
added only under V5.6 authorization. Not done here.
