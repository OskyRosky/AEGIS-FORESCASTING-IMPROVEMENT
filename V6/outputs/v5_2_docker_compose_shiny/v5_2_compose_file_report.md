# AEGIS V5.2 — Compose File Report

**Stage:** V5.2 — Docker Compose Shiny Service
**Operative file:** `docker-compose.yml` (V5 repo root)
**Status:** V5_2_DOCKER_COMPOSE_SHINY_SERVICE_COMPLETED

## Purpose

Convert the manual V5.1 `docker run ...` command into a reproducible one-line
local flow:

```
docker compose up -d shiny
```

## Service definition (single service: `shiny`)

| Key | Value | Rationale |
|-----|-------|-----------|
| `image` | `aegis-dashboard:v5.1` | Reuse the V5.1-built, validated R-only image. |
| `build.context` / `build.dockerfile` | `.` / `Dockerfile` | Clean-machine reproducibility: rebuild from the **unmodified** V5.1 Dockerfile if the image is missing. Existing image is reused on `up` (no rebuild observed). |
| `container_name` | `aegis-dashboard-v5-2` | Deterministic name for smoke test / `docker inspect`. |
| `ports` | `8080:3838` | Internal 3838 fixed (Dockerfile/entrypoint). External 8080 recommended; 8080 was free on this host. |
| `working_dir` | `/app` | Matches Dockerfile `WORKDIR /app`. |
| `volumes` | `./data/processed:/app/data/processed:ro`, `./outputs:/app/outputs:ro` | External **read-only** governed artifact mounts, **relative** paths. |
| `restart` | `unless-stopped` | Local-demo convenience. Stop with `docker compose down`. |
| healthcheck | inherited from image | Image `HEALTHCHECK curl http://127.0.0.1:3838/` — not redefined to avoid drift. |

## Deliberately excluded (governance)

- No `refresh` service, no `scheduler`, no `sql`, no `azure`, no `llm` service.
- No `data/raw` mount, no `BACKUP` mount, no `.env`, no `secrets`, no credentials.
- No Python / ML stack. No absolute `C:\Users\...` / OneDrive paths in the source file.
- Top-level `version:` key omitted (obsolete in Compose v2+).

## Reproducibility note

`build:` uses `context: .` + `dockerfile: Dockerfile`. On a machine that does not
yet have `aegis-dashboard:v5.1`, `docker compose up --build shiny` rebuilds the
image from the same V5.1 Dockerfile (no functional change). When the image is
present, `docker compose up -d shiny` reuses it.
