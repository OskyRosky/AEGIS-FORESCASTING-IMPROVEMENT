# AEGIS V5 — Docker TROUBLESHOOTING

For each problem: **symptom → probable cause → diagnostic → safe fix → what NOT to do.**
All commands run from the **V5 repo root**.

---

## 1. Docker Desktop is not running
- **Symptom:** `error during connect ... dockerDesktopLinuxEngine ... cannot find the file`.
- **Cause:** Docker daemon/engine is off.
- **Diagnostic:** `docker version`
- **Fix:** Start Docker Desktop; wait for the Linux engine, then retry.
- **Do NOT:** run commands assuming success; do not reinstall Docker.

## 2. Port 8080 already in use
- **Symptom:** `bind: address already in use` on `up`.
- **Cause:** another process/container holds 8080.
- **Diagnostic:** `(Get-NetTCPConnection -LocalPort 8080 -State Listen).OwningProcess`
- **Fix:** stop the other listener, OR edit `docker-compose.yml` port to `"8081:3838"` and open http://127.0.0.1:8081.
- **Do NOT:** change the internal port 3838.

## 3. Container not healthy
- **Symptom:** `docker compose ps` shows `starting`/`unhealthy`.
- **Cause:** first render still loading (Inter font download / warmup).
- **Diagnostic:** `docker compose logs --tail 30 shiny`
- **Fix:** wait ~30–60 s; the healthcheck curls 127.0.0.1:3838. Re-check `ps`.
- **Do NOT:** rebuild the image to "fix" a warmup delay.

## 4. Dashboard does not load
- **Symptom:** browser can’t reach http://127.0.0.1:8080.
- **Cause:** container down, or wrong URL/port.
- **Diagnostic:** `docker compose ps`; `Invoke-WebRequest http://127.0.0.1:8080 -UseBasicParsing`
- **Fix:** `docker compose up -d shiny`; confirm 8080 mapping in `ps`.
- **Do NOT:** edit shiny_app code.

## 5. Smoke test fails
- **Symptom:** `SMOKE_TEST_FAILED`.
- **Cause:** dashboard not fully up, or mounts missing.
- **Diagnostic:** rerun after `ps` shows healthy; read the failed row.
- **Fix:** ensure `up -d shiny` from V5 root; re-run smoke.
- **Do NOT:** modify the smoke script to force a pass.

## 6. 10 assistants not visible
- **Symptom:** fewer than 10 "Generate explanation" in HTML.
- **Cause:** `outputs` mount missing → mock LLM JSON not found.
- **Diagnostic:** `docker exec aegis-dashboard-v5-2 ls /app/outputs/v4_4_mock_provider`
- **Fix:** run compose from V5 root so `./outputs` resolves; recreate.
- **Do NOT:** hardcode assistant content.

## 7. PDF / DOCX download fails
- **Symptom:** PDF/DOCX not produced.
- **Cause:** LaTeX/pandoc missing (should be baked since V5.4).
- **Diagnostic:** `docker exec aegis-dashboard-v5-2 sh -lc "which pdflatex pandoc"`
- **Fix:** confirm image is the V5.4 rebuild (`aegis-dashboard:v5.1` = TinyTeX build). MD/TXT/HTML always work.
- **Do NOT:** install LaTeX at runtime; it belongs in the image.

## 8. Refresh validate-only fails
- **Symptom:** `V5_5_REFRESH_VALIDATE_BLOCKER` / exit ≠ 0.
- **Cause:** a mount contract check failed (e.g., data/processed writable, data/raw present, or a required artifact missing).
- **Diagnostic:** read the `[FAIL]` line in the run output.
- **Fix:** run from V5 root; ensure the refresh service mounts (processed :ro, only v5_5 subdir :rw). It must NEVER see SQL/pyodbc.
- **Do NOT:** grant the refresh service write access to productive artifacts or add pyodbc to "make it work".

## 9. Compose says it can't find mounts
- **Symptom:** empty/missing `/app/data/processed` or `/app/outputs`.
- **Cause:** compose run from the wrong directory (relative `./` paths).
- **Diagnostic:** `Get-Location`; `docker compose config` (check resolved source paths).
- **Fix:** `cd` to the V5 root before running compose.
- **Do NOT:** hardcode absolute `C:\Users\...` paths in compose.

## 10. Ran from the wrong folder
- **Symptom:** mounts empty, or "no configuration file".
- **Cause:** not in the V5 root (where `docker-compose.yml` lives).
- **Diagnostic:** `Test-Path docker-compose.yml`
- **Fix:** `cd` into the V5 folder.
- **Do NOT:** copy compose elsewhere.

## 11. OneDrive lock / permissions
- **Symptom:** transient file-in-use / access-denied on host artifacts.
- **Cause:** OneDrive sync holding a file.
- **Diagnostic:** retry the read; check OneDrive sync status.
- **Fix:** wait for sync to settle; reads are safe (mounts are read-only).
- **Do NOT:** force-delete host artifacts.

## 12. Image does not exist
- **Symptom:** `pull access denied` / image not found on `up`.
- **Cause:** `aegis-dashboard:v5.1` / `aegis-refresh:v5.5` not built locally.
- **Diagnostic:** `docker images | Select-String aegis`
- **Fix:** dashboard: `docker compose up -d --build shiny`; refresh: `docker build -f Dockerfile.refresh -t aegis-refresh:v5.5 .`
- **Do NOT:** pull from a registry (these are local images).

## 13. Accidental rebuild
- **Symptom:** long build unexpectedly triggered.
- **Cause:** `--build` used, or image missing.
- **Diagnostic:** `docker images` (check image ID/date).
- **Fix:** if the image already exists, use `docker compose up -d shiny` (no `--build`).
- **Do NOT:** rebuild to "refresh data" — data is a mount, not an image layer.

## 14. data/raw appears by mistake
- **Symptom:** `/app/data/raw` present in a container.
- **Cause:** a stray mount/bake was added.
- **Diagnostic:** `docker exec aegis-dashboard-v5-2 sh -lc "[ -d /app/data/raw ] && echo PRESENT || echo absent"`
- **Fix:** remove any data/raw mount from compose; rebuild only if it was baked.
- **Do NOT:** mount data/raw into the dashboard or refresh service.

## 15. Clean up containers without deleting data
```powershell
docker compose down
```
- Removes containers + the compose network. **Keeps** images and host data.
- **Do NOT:** use `docker system prune -a --volumes` (would remove images).

## 16. Verify there was no mutation
```powershell
# from V5 root; compare against the recorded baselines
Get-ChildItem data\processed -Recurse -File | Measure-Object   # expect 24 files
Get-ChildItem data\raw -Recurse -File | Measure-Object          # expect 6 files
```
- Baselines: `data/processed` = 24 files (hash B0880D33…D61); `data/raw` = 6 files (hash BD44163A…73D).
- **Do NOT:** hand-edit files under `data/processed` or `data/raw`.
