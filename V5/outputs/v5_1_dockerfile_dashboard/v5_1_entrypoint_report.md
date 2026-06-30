# V5.1 — Entrypoint (Task F)

## Archivo: `docker/entrypoint.sh`
```sh
#!/usr/bin/env bash
set -euo pipefail
exec Rscript -e "shiny::runApp('/app/shiny_app', host = '0.0.0.0', port = 3838)"
```

## Requisitos cumplidos
1. **chmod +x** aplicado en el Dockerfile (con `sed -i 's/\r$//'` para normalizar CRLF de host Windows).
2. **Sin port-hunting** — puerto interno fijo 3838.
3. Sin PowerShell. 4. Sin robocopy. 5. Sin SQL. 6. Sin refresh. 7. Sin modelos.

## Notas de correctitud
- `runApp('/app/shiny_app', ...)` fija el working dir al directorio de la app, por lo que los `source()` relativos de `app.R`/`global.R` y el **data loader gobernado read-only** resuelven correctamente.
- Con `outputs/` y `data/processed` montados en `/app`, `find_project_root()` detecta la raíz `/app` (requiere `outputs/model_lab` + `shiny_app`), y el loader lee los artefactos gobernados.
- `set -euo pipefail` + `exec` → señales correctas y fallo temprano.
