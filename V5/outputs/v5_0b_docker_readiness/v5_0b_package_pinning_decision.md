# V5.0B — Decisión: Pinning de paquetes R (reproducibilidad)

**Decisión:** **Posit Public Package Manager (PPM) snapshot fechado** como repositorio primario de instalación + **`renv.lock`** como registro de versiones exactas.

**Rechazadas:**
- CRAN latest sin fecha — no reproducible; las versiones cambian con el tiempo.
- Solo `renv` con compilación desde fuente — más lento (compila todo), mayor superficie de fallo de build.

**Rationale:** PPM con URL fechada (p.ej. `https://packagemanager.posit.co/cran/__linux__/<distro>/<YYYY-MM-DD>`) entrega **binarios deterministas** rápidos sobre `r-ver`/Debian, congelando el universo de paquetes a una fecha. `renv.lock` documenta las versiones exactas (las del inventario: shiny 1.13.0, bslib 0.11.0, DT 0.34.0, plotly 4.12.0, highcharter 0.9.5, etc.) para auditoría y reproducción.

**Impacto en V5.1:**
- `options(repos = c(PPM = "https://packagemanager.posit.co/cran/__linux__/<distro>/<snapshot-date>"))` antes del install.
- Generar `renv.lock` desde el host (R 4.6.0) y commitearlo en V5.
- La fecha de snapshot debe ser compatible con R 4.6.0 (validar en V5.1).
