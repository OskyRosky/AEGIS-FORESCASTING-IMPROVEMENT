# AEGIS V5 — Docker (README)

AEGIS V5 is the **local / containerized MVP** of the AEGIS Forecast Improvement
Platform. It runs a **read-only** Shiny dashboard from governed artifacts using
Docker Desktop + Docker Compose.

> V5 is packaging & local deployment only. It does **not** ingest SQL, run
> models, promote a champion, connect to Azure, use a real LLM, or schedule
> anything. The champion is frozen = **ETS Explicit** (15 governed models,
> horizons 30 / 60 / 180).

## Services

| Service | Image | Role |
|---------|-------|------|
| `shiny` | `aegis-dashboard:v5.1` | Read-only dashboard on port 8080 → 3838 |
| `refresh` | `aegis-refresh:v5.5` | Separate, one-shot, **validate-only** service (profile `refresh`) |

## Requirements
- Docker Desktop running (Linux engine).
- Docker Compose v2 (`docker compose`).
- This V5 repo folder open locally (run commands from the V5 root).

## Start the dashboard
```powershell
docker compose up -d shiny
```
Open: **http://127.0.0.1:8080**

## Logs
```powershell
docker compose logs -f shiny
```

## Restart
```powershell
docker compose restart shiny
```

## Stop
```powershell
docker compose down
```

## Smoke test (health/invariants)
```powershell
powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080
```

## Refresh — VALIDATE-ONLY (one-shot)
```powershell
docker compose run --rm refresh
```
⚠️ **`refresh` validate-only does NOT update data.** It only validates the
architecture (paths, mounts, contracts) and runs the orchestrator's safe
`--dry-run`. Ends with `V5_5_REFRESH_VALIDATE_OK`.

## What is GATED (not available in V5)
Real SQL ingestion · model training · champion promote · Azure · scheduler ·
real LLM · a refresh button in the dashboard. See `docker/RUNBOOK.md` and
`docs/v5_7_v5_6_gating_note.md`.

## More docs
- `docker/RUNBOOK.md` — full operations runbook.
- `docker/TROUBLESHOOTING.md` — common problems & safe fixes.
- `docker/LOCAL_DEMO_CHECKLIST.md` — pre-demo checklist.
- `docs/v5_7_command_reference.md` — quick command reference.
