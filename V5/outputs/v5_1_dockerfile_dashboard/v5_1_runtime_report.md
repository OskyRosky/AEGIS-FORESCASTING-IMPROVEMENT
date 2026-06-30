# V5.1 — Runtime report (Tasks I, J, K, L)

## Comando de run (exacto)
```
docker run -d --rm -p 8080:3838 --name aegis-dashboard-v5-1 `
  -v "<V5>\outputs:/app/outputs:ro" `
  -v "<V5>\data\processed:/app/data/processed:ro" `
  aegis-dashboard:v5.1
```
- Puerto interno **3838** → externo **8080**.
- `outputs` y `data/processed` montados **read-only** (`:ro`).
- `data/raw` **NO** se montó (no es necesario para el dashboard).

## Validación runtime
| Check | Esperado | Observado | Estado |
|---|---|---|---|
| HTTP 200 en :8080 | 200 | 200 | PASS |
| Dashboard carga | UI renderizada | len=303385 | PASS |
| 10 assistants | >=10 | 10 "Generate explanation" | PASS |
| Champion ETS Explicit | presente | found | PASS |
| Scope 15 modelos | presente | found | PASS |
| Horizontes 30/60/180 | presentes | 30,60,180 | PASS |
| Healthcheck | healthy | healthy | PASS |
| Logs sin errores críticos | none | NO_CRITICAL_ERRORS | PASS |
| Mutación data/processed | none | write bloqueado (RO), sin archivo en host | PASS |
| Mutación data/raw | none | no montado/horneado | PASS |
| V1/V2/V3/V4 | intactos | solo V5 modificado | PASS |

## Bug-blocker (Task — detener y reportar)
- Primer run: error `fs.so: libuv.so.1` → render fallaba. **Se detuvo y se reportó la causa**, se agregó `libuv1` (fix de entorno), rebuild, re-run → healthy. Documentado en `v5_1_dockerfile_report.md` y risk R7.

## PDF/DOCX (Task K)
- `pandoc` instalado (apt) → DOCX/HTML/MD/TXT/CSV operativos.
- `tinytex` instalado → PDF disponible; la **validación funcional completa de descargas (PDF/DOCX)** tiene su **propio gate en V5.4**.
- No fue blocker de V5.1: el dashboard carga y opera; descargas no rompen la app.
- Nota menor (R8): bslib descarga la fuente Google "Inter" en runtime (cache, no-fatal); bundling offline queda como hardening futuro.

## Inspección de imagen (Task L)
- Sin `.env`, sin `*.pem`/`*.key`, sin archivos `*secret*`, sin env de secretos.
- Sin Python runtime (`NO_PYTHON`), sin ML pesado, sin `reticulate`.
- Sin `data/raw` horneado. Sin secretos en `docker history`.

## Logs
- `logs/v5_1_docker_run.log` — id de contenedor.
- `logs/v5_1_container_logs.log` — logs de arranque.
