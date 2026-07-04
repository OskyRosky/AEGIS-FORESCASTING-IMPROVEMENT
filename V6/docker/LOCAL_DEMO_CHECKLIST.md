# AEGIS V5 — Local Demo Checklist

Run through this before showing the project. All commands from the **V5 repo root**.

| # | Check | Expected result | Command / Location | Status |
|---|-------|-----------------|--------------------|--------|
| 1 | Docker Desktop open | Linux engine running | Docker Desktop app / `docker version` | [ ] |
| 2 | Dashboard image present | `aegis-dashboard:v5.1` | `docker images \| Select-String aegis` | [ ] |
| 3 | Refresh image present | `aegis-refresh:v5.5` | `docker images \| Select-String aegis` | [ ] |
| 4 | Start dashboard | container created + starting | `docker compose up -d shiny` | [ ] |
| 5 | Container healthy | `running (healthy)` | `docker compose ps` / Docker Desktop → Containers | [ ] |
| 6 | Open dashboard | page loads, HTTP 200 | http://127.0.0.1:8080 | [ ] |
| 7 | Home / Overview | loads, AEGIS branding | dashboard nav | [ ] |
| 8 | Models (Universe/Tournament/Champion) | champion = ETS Explicit, 15 models | Models group | [ ] |
| 9 | Forecasting (Viewer/Accuracy/Forecast/TTL) | 30 / 60 / 180 horizons | Forecasting group | [ ] |
| 10 | Governance (Risks/Audit) | loads governed tables | Governance group | [ ] |
| 11 | Reference / Artifacts | governed downloads visible | Reference → Artifacts | [ ] |
| 12 | 10 assistants | "Generate explanation" ×10 | each section end | [ ] |
| 13 | Downloads | MD/PDF/DOCX/HTML/TXT (+CSV governed) download OK | assistant + artifact modals | [ ] |
| 14 | Smoke test | `SMOKE_TEST_PASSED` | `powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080` | [ ] |
| 15 | Refresh validate-only | `V5_5_REFRESH_VALIDATE_OK` | `docker compose run --rm refresh` | [ ] |
| 16 | Refresh did NOT update data | data/processed unchanged (24 files) | `Get-ChildItem data\processed -File \| Measure-Object` | [ ] |
| 17 | No real SQL | refresh has no pyodbc; no SQL attempted | run output banner `NO_SQL` | [ ] |
| 18 | No Azure | no Azure env/service | `docker compose config` (no AZURE_*) | [ ] |
| 19 | No scheduler | no cron/Task Scheduler/Actions | n/a (none created) | [ ] |
| 20 | Ready for V5.8 | all above green | this checklist complete | [ ] |

**Talking points (do NOT overclaim):**
- "This is the **local Docker MVP**. The dashboard is read-only and reads
  governed artifacts."
- "The refresh service is **validate-only** — it checks the architecture; it
  does **not** update data, run SQL, run models, or promote."
- "Real refresh + Azure are **future, gated** work (need a non-interactive auth
  strategy)."
