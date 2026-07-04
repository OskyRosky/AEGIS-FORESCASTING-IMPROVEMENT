# AEGIS V5 — Local Usage Notes (dashboard + refresh validate-only)

## Dashboard (unchanged from V5.4)

```powershell
docker compose up -d shiny        # start  ->  http://127.0.0.1:8080
docker compose logs -f shiny      # logs
docker compose restart shiny      # restart
docker compose down               # stop
```

The `refresh` service does **NOT** start with `docker compose up -d shiny`
(it is behind the `refresh` profile).

## Refresh — VALIDATE-ONLY (new in V5.5)

One-shot, explicit:

```powershell
docker compose run --rm refresh
```

Expected output ends with:

```
VALIDATE_ONLY | NO_SQL | NO_MODELS | NO_PROMOTE | NO_MUTATION
V5_5_REFRESH_VALIDATE_OK
```

### What `refresh` does / does NOT do

- **Does:** validate architecture — orchestrator present, mounts correct
  (`data/processed` read-only, `data/raw` absent), required artifacts present,
  and that the orchestrator's safe `--dry-run` runs with no side effects.
- **Does NOT:** update data · run SQL · connect ODBC/Entra/MFA · run models ·
  promote · mutate `data/processed` or `data/raw`.

### Rules
- This does **not** refresh data. Real refresh is gated (see
  `v5_5_refresh_real_gating.md`).
- No secrets, no `.env`, no Azure, no scheduler.
- Never add a refresh button to the dashboard; Shiny stays read-only.

## Build the refresh image (only if missing)

```powershell
docker build -f Dockerfile.refresh -t aegis-refresh:v5.5 .
```
