# AEGIS V5 — Command Reference (V5.7)

Run all commands from the **V5 repo root** (where `docker-compose.yml` lives).

## Dashboard
```powershell
docker compose up -d shiny        # start dashboard (http://127.0.0.1:8080)
docker compose ps                 # show service/container state
docker compose logs -f shiny      # follow logs
docker compose restart shiny      # restart dashboard
docker compose down               # stop + remove containers (keeps data/images)
```

## Refresh — VALIDATE-ONLY (one-shot; does NOT update data)
```powershell
docker compose run --rm refresh   # ends with V5_5_REFRESH_VALIDATE_OK
```

## Smoke test
```powershell
powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080
```

## Images
```powershell
docker images                                  # list images
docker image inspect aegis-dashboard:v5.1      # dashboard image details
docker image inspect aegis-refresh:v5.5        # refresh image details
```

## Containers
```powershell
docker ps                         # running containers
docker compose ps                 # compose-managed services
```

## Safety — commands to AVOID (gated / would break governance)
```text
# DO NOT run any of these in V5:
docker compose run --rm refresh ... --execute-staging --allow-execute   # real models/SQL
python python/orchestration/run_daily_refresh_orchestrator.py --promote --allow-promote   # promote
#  ^ no promote, no execute-staging, no real SQL
```
- ❌ No `--promote` / `--allow-promote`.
- ❌ No `--execute-staging` / `--allow-execute`.
- ❌ No real SQL / no ODBC connection / no Entra/MFA.
- ❌ No manual edits to `data/processed` or `data/raw`.
- ❌ No Azure, no scheduler, no real LLM, no refresh button.
- ❌ Avoid `docker system prune -a` (removes images).
