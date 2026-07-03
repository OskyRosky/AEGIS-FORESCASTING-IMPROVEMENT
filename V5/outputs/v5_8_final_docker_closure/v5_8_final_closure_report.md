# AEGIS V5 — Final Docker Closure Report

**Status:** `V5_FINAL_DOCKER_VALIDATION_COMPLETED` · `V5_DOCKER_LOCAL_MVP_CLOSED` · `V5_READY_FOR_CONTAINER_DEMO`
**Date:** 2026-07-03

## 1. Executive summary
AEGIS V5 is validated and closed as a **local / containerized MVP** (container
demo). The read-only Shiny dashboard runs on Docker via `docker compose up -d
shiny` at http://127.0.0.1:8080, serving governed artifacts mounted read-only.
Downloads (Explanation + Governed, incl. PDF) work in-container. A separate,
one-shot `refresh` service runs **validate-only** — it does not update data.
Governance invariants hold; no mutation occurred. **This is NOT a production /
Azure / real-refresh system.**

## 2. What V5 achieved
- V5.0A–V5.1: R-only dashboard image `aegis-dashboard:v5.1` (reproducible build).
- V5.2: single-command dashboard via Docker Compose.
- V5.3: external read-only volume/artifact contract (no rebuild on artifact change).
- V5.4: in-container downloads validated (MD/PDF/DOCX/HTML/TXT + CSV verbatim).
- V5.5: separated, validate-only refresh service (`aegis-refresh:v5.5`).
- V5.7: full internal documentation (README/RUNBOOK/TROUBLESHOOTING/checklist/handoff/gating/commands).
- V5.8 (this): final closure validation.

## 3. What V5 does
- Serves the governed read-only dashboard locally in Docker.
- Renders explanation & governed downloads (incl. PDF via baked TinyTeX).
- Enforces read-only mounts; `data/raw` is never mounted.
- Provides a safe, separated, validate-only refresh service.

## 4. What V5 does NOT do
No real SQL ingestion · no ODBC/pyodbc connection · no Entra/MFA · no model
training/runner · no full pipeline · no champion promote · no Azure · no
scheduler · no real LLM (assistants are local mock) · no "Update data" button.

## 5. Final architecture
- Docker image = code + dependencies (dashboard is R-only).
- `data/processed` and `outputs` = external **read-only** mounts.
- `data/raw` = not mounted, not baked.
- `shiny` = read-only dashboard; `refresh` = validate-only; real refresh = gated.

## 6. Services
| Service | Image | Port | Restart | Profile | Role |
|---------|-------|------|---------|---------|------|
| `shiny` | `aegis-dashboard:v5.1` | 8080→3838 | unless-stopped | default | read-only dashboard |
| `refresh` | `aegis-refresh:v5.5` | none | "no" | `refresh` | validate-only (one-shot) |

## 7. Images
- `aegis-dashboard:v5.1` — `a799da697173`, ~2.47 GB, R-only + pandoc + TinyTeX.
- `aegis-refresh:v5.5` — `698b1634f78a`, ~180 MB, python-slim, no pyodbc/pandas/ML.

## 8. Volumes
- `./data/processed:/app/data/processed:ro`
- `./outputs:/app/outputs:ro` (shiny)
- refresh: `./data/processed:ro` + only `./outputs/v5_5_refresh_service_validate:rw`
- `data/raw`: never mounted.

## 9. Commands
```powershell
docker compose up -d shiny        # start dashboard -> http://127.0.0.1:8080
docker compose ps                 # state
docker compose logs -f shiny      # logs
docker compose restart shiny      # restart
docker compose down               # stop
docker compose run --rm refresh   # refresh VALIDATE-ONLY (does NOT update data)
powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080
```

## 10. Validation results (V5.8)
- Compose config valid; `shiny` running/healthy; refresh not auto-start.
- Dashboard HTTP 200; smoke **11/11**; 10 assistants; ETS Explicit; 15 models; 30/60/180.
- Downloads: Explanation MD/PDF(%PDF)/DOCX(PK)/HTML/TXT; Governed CSV (verbatim SHA256) + PDF/DOCX. No traceback/secrets.
- Refresh: `V5_5_REFRESH_VALIDATE_OK`, exit 0, NO_SQL/NO_MODELS/NO_PROMOTE/NO_MUTATION.
- Mounts: processed(24 csv)+outputs read-only; data/raw absent; LLM mock JSON present.
- Governance: champion ETS Explicit; 15 models; prohibited (NBEATS/NHITS/FastNeuralAR_MLP) = 0.
- Immutability: data/processed + data/raw + all docker files + both images unchanged; no rebuild.

## 11. Governance status
Champion frozen = **ETS Explicit**; 15 governed models; horizons 30/60/180;
Shiny read-only; LLM mock/deterministic; V1–V4 frozen and untouched.

## 12. Risks carried forward
Real refresh gated (auth strategy needed); Highcharts commercial license (legal
review); Inter font runtime download (offline bundle future). See
`v5_8_final_risk_register.csv`.

## 13. Deferred — V5.6
**V5.6 (controlled refresh in container) is DEFERRED / GATED.** Real refresh
needs a non-interactive auth strategy (device-code / service principal / managed
identity); `ActiveDirectoryInteractive` (MFA) is headless-incompatible. See
`docs/v5_7_v5_6_gating_note.md`.

## 14. Next phase recommendation
Future, explicitly-authorized work (NOT part of V5): decide the non-interactive
auth strategy, move secrets to a secret store, then design a hosted refresh
(V5.6) and/or an Azure deployment as separate phases. None of this is promised
by V5.

## 15. Final status tokens
```
V5_FINAL_DOCKER_VALIDATION_COMPLETED
V5_DOCKER_LOCAL_MVP_CLOSED
V5_READY_FOR_CONTAINER_DEMO
```
NOT declared: production ready · Azure ready · refresh real ready · SQL refresh
ready · automated daily refresh ready · model retraining ready.
