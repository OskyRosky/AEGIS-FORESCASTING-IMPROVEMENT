# V5.0B — Plan de entrypoint + healthcheck (propuesta, NO operativo)

## Entrypoint
- **Workdir:** `/app` (raíz del proyecto dentro del contenedor; el resolver relativo encuentra `ACTIVE_PROJECT_ROOT.md` + `outputs/model_lab` + `shiny_app`).
- **Comando (propuesta):**
  ```
  Rscript -e "shiny::runApp('/app/shiny_app', host='0.0.0.0', port=3838, launch.browser=FALSE)"
  ```
- **Sin port-hunting:** a diferencia de `scripts/start_shiny.ps1` (que busca puerto libre 3838..3850 en el host), dentro del contenedor el puerto interno es **fijo 3838**. El mapeo lo hace `docker run -p`.
- `host='0.0.0.0'` (no 127.0.0.1) para exponer fuera del contenedor.

## Puertos
- **Interno:** 3838 (fijo).
- **Externo (host):** evitar 3838/3839/3840 → **colisionan** con V3/V4/V5 locales corriendo en el host. Recomendado mapear a un puerto distinto, p.ej. `-p 8080:3838`. Documentar la colisión.

## Healthcheck (propuesta)
```
HEALTHCHECK --interval=30s --timeout=5s --retries=3 --start-period=30s \
  CMD curl -fsS http://127.0.0.1:3838/ || exit 1
```
- `start-period` 30s cubre el arranque de R + carga de paquetes/global.R.
- Requiere `curl` instalado en la imagen (ver system deps).

> Solo plan. No se crea Dockerfile ni entrypoint operativo en V5.0B.
