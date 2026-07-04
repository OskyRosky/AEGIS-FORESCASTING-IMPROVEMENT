# AEGIS V5 — Volume Usage Guide

## What lives where

| What | Where | Baked in image? | Mounted? | Access |
|------|-------|-----------------|----------|--------|
| Dashboard code + R dependencies | `aegis-dashboard:v5.1` image | Yes | — | — |
| Governed processed data (CSVs) | `./data/processed` | No | Yes → `/app/data/processed` | **read-only** |
| Governed model_lab / governance / mock LLM JSON | `./outputs` | No | Yes → `/app/outputs` | **read-only** |
| Raw ingestion data | `./data/raw` (host only) | **No** | **No** | not in container |
| Backups / secrets / .env | — | **No** | **No** | not in container |

## Why `data/raw` is not included

`data/raw` is an **ingestion input** for the (out-of-scope) refresh pipeline.
The dashboard is a **read-only consumer of governed artifacts** and never reads
raw data. Keeping it out of the image and out of the container reduces size,
avoids leaking source data, and enforces the read-only consumer boundary.

## Why `outputs` and `data/processed` do not require a rebuild

They are **external bind mounts**, not baked layers. Replacing an artifact file
on the host makes it visible to the running container immediately — proven in
V5.3: an external probe update was reflected inside the container with the image
ID unchanged and no rebuild/restart.

## Everyday commands

```powershell
docker compose up -d shiny        # start  ->  http://127.0.0.1:8080
docker compose logs -f shiny      # logs
docker compose restart shiny      # restart
docker compose down               # stop
```

## If external artifacts change

1. Replace the files under `./data/processed` or `./outputs` on the host
   (this is what the future refresh service will do).
2. The running container serves the new content immediately — **no rebuild**.
3. Optionally `docker compose restart shiny` only if you want to clear the R
   loader's in-memory cache (the loader reads artifacts at app startup).

## What NOT to do

- Do **not** hand-edit files in `data/processed` (governed, read-only).
- Do **not** put secrets, credentials, or `.env` into the image or Compose.
- Do **not** mount `data/raw`.
- Do **not** add a refresh/scheduler service to the dashboard Compose.
- Do **not** rebuild the image just to pick up new artifacts.

## Future refresh validation (V5.5)

A **separate** refresh service (not the dashboard) will regenerate the governed
artifacts under `./data/processed` and `./outputs`. V5.5 will validate that
refresh as a dry-run first; the dashboard will keep consuming the mounts
read-only with no code change. Real refresh remains gated by MFA/headless
(V5.6).
