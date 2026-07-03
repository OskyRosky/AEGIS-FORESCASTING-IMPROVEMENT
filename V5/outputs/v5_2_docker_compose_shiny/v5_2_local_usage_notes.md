# AEGIS V5 — Local Usage Notes (Docker Compose)

The AEGIS V5 dashboard now runs locally via Docker Compose. Prerequisites:
**Docker Desktop running** and the folder opened at the **V5** repo root
(where `docker-compose.yml` lives).

## Start the dashboard

```powershell
docker compose up -d shiny
```

Then open in a browser:

```
http://127.0.0.1:8080
```

> If port 8080 is already in use on your machine, edit `docker-compose.yml`
> and change the port mapping to `"8081:3838"`, then open
> `http://127.0.0.1:8081`.

## View logs

```powershell
docker compose logs -f shiny
```

## Stop the dashboard

```powershell
docker compose down
```

## Restart the dashboard

```powershell
docker compose restart shiny
```

## Run the smoke test (validation)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080 -ContainerName aegis-dashboard-v5-2 -ImageName aegis-dashboard:v5.1
```

## Rebuild on a clean machine (only if the image is missing)

```powershell
docker compose up -d --build shiny
```

This rebuilds `aegis-dashboard:v5.1` from the unmodified V5.1 Dockerfile.

## What this service does / does not do

- **Does:** serve the read-only AEGIS Shiny dashboard from governed artifacts
  mounted read-only (`data/processed`, `outputs`).
- **Does NOT:** run SQL, run models, run a refresh, connect to Azure, use a real
  LLM, or write to `data/processed` / `data/raw`. `data/raw` is not mounted.
- Champion is frozen = **ETS Explicit**; 15 governed models; horizons 30 / 60 / 180.
