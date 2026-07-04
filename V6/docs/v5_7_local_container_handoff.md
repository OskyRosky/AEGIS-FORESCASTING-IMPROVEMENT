# AEGIS V5 — Local Container Handoff (V5.7)

Plain-language handoff of the local Docker MVP.

## 1. What is finished in V5 so far
- **V5.0A–V5.1:** V5 cloned from closed V4; Docker readiness audited; the R-only
  dashboard image `aegis-dashboard:v5.1` built and validated.
- **V5.2:** `docker compose up -d shiny` runs the dashboard.
- **V5.3:** external read-only volume/artifact contract proven (no rebuild needed
  when artifacts change; mounts are read-only).
- **V5.4:** downloads validated in-container — Explanation (MD/PDF/DOCX/HTML/TXT)
  and Governed (CSV verbatim + MD/PDF/DOCX/HTML/TXT). PDF works via baked TinyTeX.
- **V5.5:** a **separate** refresh service (`aegis-refresh:v5.5`) runs
  **validate-only** (no SQL/models/promote/mutation).
- **V5.7 (this):** full internal documentation (README, RUNBOOK, TROUBLESHOOTING,
  demo checklist, command reference, gating note).

## 2. What Oscar can do locally
- Start and view the dashboard.
- Navigate all sections (Models, Forecasting, Governance, Reference).
- Use the 10 assistants and download explanations/artifacts in 5–6 formats.
- Run the smoke test.
- Run the refresh **validate-only** service.

## 3. What Oscar can see in Docker Desktop
- Image `aegis-dashboard:v5.1` (and `aegis-refresh:v5.5`).
- Container `aegis-dashboard-v5-2` running/healthy on port 8080.
- The `refresh` run appears as a short-lived one-shot container when invoked.

## 4. URL
**http://127.0.0.1:8080**

## 5. Command to start the dashboard
```powershell
docker compose up -d shiny
```

## 6. Command to validate refresh
```powershell
docker compose run --rm refresh
```

## 7. What "refresh validate-only" means
It **validates the refresh architecture** — orchestrator present, mounts correct
(`data/processed` read-only, `data/raw` absent), required artifacts present — and
runs the orchestrator's safe `--dry-run`. **It does NOT update data, run SQL, run
models, or promote.** It ends with `V5_5_REFRESH_VALIDATE_OK`.

## 8. What is NOT ready yet
- Real SQL ingestion from the container.
- Model training / recalibration / full pipeline.
- Champion promote.
- Azure / public cloud endpoint.
- Real LLM (assistants are local mock).
- Scheduler / automation.

## 9. What is left for Azure / future
- Choose a **non-interactive** auth strategy for SQL/Azure (device-code /
  service principal / managed identity).
- Move secrets to a secret store (never in image/compose).
- Decide artifact sourcing for a hosted deployment.
- These are future, explicitly-gated stages — not part of V5.

## 10. What V5.8 will validate
V5.8 = **final local Docker closure**: a full pass over the local MVP (dashboard
+ downloads + refresh validate-only + governance invariants + immutability) and
the final closure record. **V5.8 does not enable real SQL/model refresh.**
