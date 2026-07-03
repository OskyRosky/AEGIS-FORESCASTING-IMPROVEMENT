# AEGIS V5.3 — Volume / Artifact Contract

This contract is the reference for V5.4, V5.5, V5.7 and V5.8.

## Contract

| Layer | Content | Location | Access | Rebuild on change? |
|-------|---------|----------|--------|--------------------|
| **Image** | dashboard code + R deps (shiny_app, config, R packages, pandoc, TinyTeX) | baked into `aegis-dashboard:v5.1` | n/a | code/dep change → rebuild image |
| **Volume: data/processed** | governed processed CSVs (forecasts, actuals, viewer, TTL, model-eval, canonical universe) | host `./data/processed` → container `/app/data/processed` | **read-only** | **NO** — artifact change reflects live |
| **Volume: outputs** | governed model_lab + governance + mock LLM JSON | host `./outputs` → container `/app/outputs` | **read-only** | **NO** — artifact change reflects live |
| **NOT mounted / NOT baked** | `data/raw`, `BACKUP`, `.env`, secrets | host only (raw); absent elsewhere | none in container | n/a |

## Governance guarantees (proven in V5.3)

1. Image has **no baked artifacts** — `data/` and `outputs/` content live outside the image.
2. `data/processed` and `outputs` are consumed from **external read-only mounts**.
3. All **required** loader artifacts are present in the container (9/9).
4. `data/raw` is **not mounted and not baked**; not a runtime dependency.
5. Mounts are **read-only** from the container (writes → `Read-only file system`).
6. An external change to a mounted probe is **reflected in the container without
   rebuild, without image-ID change, and without restart**.
7. No `refresh` service, no scheduler, no SQL/Azure/LLM service.
8. Shiny is a **read-only consumer**; there is no "Update data" button.

## Separation of concerns

- **Updating artifacts** = replace files under `./data/processed` or `./outputs`
  on the host → the running container sees them immediately (no rebuild).
- **Updating the app** (code/deps) = rebuild `aegis-dashboard:v5.1` from the
  unmodified Dockerfile.
- **Producing artifacts** (SQL → ingest → transform → model → govern) = the
  future, separate refresh service (V5.5/V5.6), **not** part of the dashboard.
