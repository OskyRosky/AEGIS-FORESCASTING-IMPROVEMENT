# V5.1 — Dockerfile dashboard R-only (Task E)

## Diseño
- **Base:** `rocker/r-ver:4.6.0@sha256:a3c049...` (digest-pinned, Ubuntu noble, R 4.6.0).
- **Locale:** `ENV LANG=C.UTF-8`, `ENV LC_ALL=C.UTF-8`.
- **System deps (apt):** `ca-certificates curl pandoc locales libcurl4-openssl-dev libssl-dev libxml2-dev libuv1 libfontconfig1-dev libfreetype6-dev libpng-dev libjpeg-dev libtiff5-dev libharfbuzz-dev libfribidi-dev fonts-dejavu-core fonts-liberation`.
- **R packages:** 14 paquetes dashboard desde snapshot P3M; gate de build verifica que todos quedaron instalados.
- **TinyTeX:** instalado **no-fatal** (`|| echo TINYTEX_INSTALL_DEFERRED_TO_V5_4`) → PDF tiene su propio gate en V5.4.
- **WORKDIR:** `/app`. **COPY:** `shiny_app/`, `config/`, marcadores de raíz. **NO** se copia data/raw, outputs pesados, Python ni secretos.
- **Mount points:** `mkdir -p /app/outputs /app/data/processed` (volúmenes read-only en runtime).
- **EXPOSE:** 3838 (puerto interno fijo).
- **HEALTHCHECK:** curl a `http://127.0.0.1:3838/`.
- **ENTRYPOINT:** `/usr/local/bin/entrypoint.sh`.

## Principios cumplidos (V5.1)
1. Imagen R-only. 2. Sin Python. 3. Sin torch/darts/lightgbm/xgboost/sklearn. 4. Imagen = código + deps runtime. 5. data/processed = mount externo RO. 6. outputs = mount externo RO. 7. Sin data/raw. 8. Sin secrets. 9. Sin outputs pesados. 10. Entrypoint simple sin port-hunting. 11. Puerto interno 3838. 12. Healthcheck 127.0.0.1:3838. 13. Tag `aegis-dashboard:v5.1`.

## Bug-blocker corregido (cambio de entorno, NO funcional)
- **Síntoma:** al servir la página, `dyn.load` fallaba:
  `unable to load shared object '.../fs/libs/fs.so': libuv.so.1: cannot open shared object file`.
- **Causa:** el paquete `fs` (dep de `bslib`/`sass`) requiere la librería de sistema `libuv.so.1`.
- **Corrección:** se agregó `libuv1` a las dependencias apt (cambio de **entorno/infra**, permitido por la regla 6; no cambia lógica funcional del dashboard).
- **Resultado:** tras rebuild, render sin errores, contenedor `healthy`, `NO_CRITICAL_ERRORS`.

## Confirmaciones de seguridad/alcance
- Sin Python en la imagen (`NO_PYTHON`), sin ML pesado, sin secrets, sin data/raw.
- Sin SQL, sin modelos, sin refresh, sin Azure, sin LLM real (mock/local).
