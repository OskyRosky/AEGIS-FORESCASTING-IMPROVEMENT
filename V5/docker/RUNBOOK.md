# AEGIS V5 — Docker RUNBOOK

## 1. Executive summary
AEGIS V5 is the **local, containerized MVP** of the AEGIS Forecast Improvement
Platform. A single read-only Shiny dashboard is served from Docker, consuming
governed artifacts mounted read-only. A second, separate service (`refresh`)
exists only to **validate the refresh architecture** — it does not update data.
Real refresh (SQL ingestion + models + promote) is **gated** (see §15).
Champion is frozen = **ETS Explicit**; 15 governed models; horizons 30/60/180.

## 2. Architecture overview
- **Docker image = code + dependencies** (the dashboard image is R-only).
- **`data/processed`** = external **read-only** mount (governed CSVs).
- **`outputs`** = external **read-only** mount (model_lab / governance / mock LLM JSON).
- **`data/raw`** = **not mounted, not baked** (not a runtime dependency).
- **`shiny`** = read-only dashboard.
- **`refresh`** = separate **validate-only** service (profile `refresh`).
- **real refresh** = **gated** (headless MFA incompatible; needs auth strategy).

```
Host (V5 repo)                     Container (aegis-dashboard:v5.1)
  ./data/processed  ── :ro ──►  /app/data/processed   (read-only)
  ./outputs         ── :ro ──►  /app/outputs          (read-only)
  ./data/raw        ── (not mounted) ─►  absent
  shiny_app + R deps  baked in image      port 3838 ─► host 8080
```

## 3. Local services

| Service | Image | Port | Restart | Profile | Role |
|---------|-------|------|---------|---------|------|
| `shiny` | `aegis-dashboard:v5.1` | 8080→3838 | unless-stopped | (default) | read-only dashboard |
| `refresh` | `aegis-refresh:v5.5` | none | "no" (one-shot) | `refresh` | validate-only |

## 4. Docker images
- `aegis-dashboard:v5.1` — R-only (shiny/bslib/DT/plotly/highcharter + pandoc +
  TinyTeX for PDF export). NO Python. ~2.47 GB.
- `aegis-refresh:v5.5` — python:3.12-slim, **no pyodbc / no pandas / no ML**.
  ~180 MB. Runs the validate-only wrapper only.

## 5. Volume / mount contract
- `data/processed` and `outputs` are read-only mounts (never baked).
- Writing to either from inside the container fails (`Read-only file system`).
- `data/raw` is never mounted. No `.env`, no secrets, no `BACKUP`.
- Changing an artifact on the host is reflected live in the container **without
  a rebuild** (validated in V5.3). Rebuild only for code/dependency changes.

## 6. Local startup
```powershell
docker compose up -d shiny
docker compose ps
```
Open **http://127.0.0.1:8080**.

## 7. Local validation
```powershell
powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080
```
Expected: `SMOKE_TEST_PASSED` (HTTP 200, 10 assistants, ETS Explicit, 15 models,
30/60/180, NO_PYTHON, NO_RAW, no secrets, healthy).

## 8. Downloads validation
Both families work in the container (validated in V5.4):
- **Explanation**: MD / PDF / DOCX / HTML / TXT.
- **Governed**: CSV (verbatim) + MD / PDF / DOCX / HTML / TXT.
PDF uses the baked TinyTeX; exports are written to the container `/tmp` only —
they never mutate the read-only mounts.

## 9. Refresh validate-only
```powershell
docker compose run --rm refresh
```
Expected tail: `V5_5_REFRESH_VALIDATE_OK` (exit 0). It validates orchestrator
presence, read-only mounts, `data/raw` absence, artifact presence, and runs the
orchestrator's safe `--dry-run`. **It does not update data.**

## 10. What V5 does
- Serves the governed read-only dashboard locally via Docker.
- Renders explanation & governed downloads (incl. PDF) in-container.
- Proves the external volume/artifact contract and mount read-only enforcement.
- Provides a separated, safe, validate-only refresh service.

## 11. What V5 does NOT do
- ❌ No real SQL ingestion / no SQL connection.
- ❌ No Entra Interactive / MFA.
- ❌ No model training / no model runner / no full pipeline.
- ❌ No champion promote.
- ❌ No Azure / no cloud deployment.
- ❌ No real LLM (assistants are local mock, read-only).
- ❌ No scheduler / cron / Task Scheduler / GitHub Actions.
- ❌ No "Update data" button in the dashboard.

## 12. Governance invariants
- Champion frozen = **ETS Explicit** (MASE 6.90 / RMSSE 1.86).
- 15 governed models; horizons 30 / 60 / 180.
- Shiny is read-only; it never computes, trains, promotes, or writes artifacts.
- `data/processed` and `data/raw` are never mutated by the container.
- V1 / V2 / V3 / V4 are frozen and untouched.

## 13. Troubleshooting
See `docker/TROUBLESHOOTING.md`.

## 14. Stop / restart / cleanup
```powershell
docker compose restart shiny     # restart dashboard
docker compose down              # stop + remove containers (data/images kept)
docker compose ps                # check state
```
`docker compose down` does NOT delete images or host data.

## 15. Future phases
- **V5.6 — Controlled refresh in container: DEFERRED / GATED.** Real refresh
  needs SQL + a **non-interactive** auth strategy (device-code / service
  principal / managed identity). `ActiveDirectoryInteractive` (MFA) does not
  work headless. See `docs/v5_7_v5_6_gating_note.md`.
- **V5.8 — Final Docker closure**: closes the **local Docker MVP**. It does NOT
  turn on real SQL ingestion or automatic model recalibration.

## 16. Deployment readiness notes
- Image builds are reproducible (pinned base + build-time gates).
- For a future Azure deployment: choose a non-interactive auth strategy, move
  secrets to a secret store (never image/compose), and decide artifact sourcing
  (mounted volume vs produced by a hosted refresh). None of this is done in V5.

## 17. Handoff to V5.8
V5.8 will validate the full local Docker MVP end-to-end (dashboard + downloads +
refresh validate-only + governance invariants) and produce the final closure.
It is **local Docker closure**, not a real SQL/model refresh system.
