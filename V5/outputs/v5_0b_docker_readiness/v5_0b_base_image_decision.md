# V5.0B — Decisión: Imagen base

**Decisión:** `rocker/r-ver:4.6.0` para la imagen del dashboard, **pin-by-digest**.

**Rechazadas:**
- `rocker/shiny` — trae Shiny Server completo y dependencias que no usamos; más pesada. Nuestro entrypoint usa `shiny::runApp` directo, no Shiny Server.
- `rocker/tidyverse` — incluye paquetes que ya cubrimos selectivamente; innecesariamente grande.
- Construir R desde fuente — costo y tiempo sin beneficio frente a `r-ver`.

**Rationale:** `r-ver` fija una versión exacta de R sobre Debian, ligera, y nos deja instalar solo los 14 paquetes de runtime. Coincide con R 4.6.0 del host.

**Acción requerida (TBD en V5.1):** verificar disponibilidad real del tag `rocker/r-ver:4.6.0` (R 4.6.0 es reciente; si el tag aún no está publicado, usar el patch disponible más cercano o build-from-r-ver). **NO inventar un digest** — obtener el digest real con `docker buildx imagetools inspect` en V5.1 y pinearlo.

**Impacto en V5.1:** `FROM rocker/r-ver:4.6.0@sha256:<digest-verificado>`.
