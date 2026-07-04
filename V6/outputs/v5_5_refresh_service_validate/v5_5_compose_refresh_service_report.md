# AEGIS V5.5 — Compose Refresh Service Report

## Change
Added a second service `refresh` to `docker-compose.yml`. The `shiny` service is
**unchanged** (same image, ports, mounts, restart, healthcheck).

## `refresh` service definition

```yaml
refresh:
  image: aegis-refresh:v5.5
  build:
    context: .
    dockerfile: Dockerfile.refresh
  container_name: aegis-refresh-v5-5
  profiles: ["refresh"]          # NOT started by `up shiny`
  working_dir: /app
  restart: "no"                  # one-shot, no daemon
  volumes:
    - ./data/processed:/app/data/processed:ro
    - ./outputs/v5_5_refresh_service_validate:/app/outputs/v5_5_refresh_service_validate:rw
  # command = CMD in Dockerfile.refresh = python /app/scripts/refresh_validate_only.py
```

## Governance properties (verified via `docker compose config`)
- `shiny` intact; `refresh` added as a separate service.
- `refresh` is behind the **`refresh` profile** → excluded from
  `docker compose up shiny` (default services = `shiny` only; with
  `--profile refresh` = `shiny` + `refresh`).
- **No ports** on refresh.
- **restart: "no"** (one-shot; run via `docker compose run --rm refresh`).
- `data/processed` mounted **read-only**.
- **Only** the V5.5 output subdir is mounted **read-write** (granular) — the
  productive `outputs/` tree is NOT mounted, so refresh cannot mutate it.
- `data/raw` **not mounted**. No `.env`, no secrets, no Azure env vars.

## Run
`docker compose run --rm refresh` → validate-only, exit 0,
`V5_5_REFRESH_VALIDATE_OK`, auto-removed (`--rm`).
