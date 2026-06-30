# V5.1 — Estrategia de pinning R / renv (Task C)

## Estrategia implementada
Se implementó la decisión de V5.0B: **Posit Package Manager (P3M) snapshot fechado**.

- La imagen base `rocker/r-ver:4.6.0` **ya fija** el repo a un snapshot fechado de P3M:
  `https://p3m.dev/cran/__linux__/noble/2026-06-23`
- Ese repo sirve **paquetes binarios** para Ubuntu noble → instalación rápida, sin compilación, **reproducible** (la fecha congela las versiones).
- El `install.packages(...)` del Dockerfile usa ese repo heredado de la base → versiones deterministas.

## Pinning efectivo (doble candado)
1. **Base pinneada por digest:** `sha256:a3c049a16b67a01f893c106a1c8e7c878f739a541bda1fa01e42c3507aa232e9`
2. **Snapshot P3M fechado:** `noble/2026-06-23`
3. **Manifiesto de versiones:** `v5_1_r_dependencies_final.csv` (capturado del contenedor construido)

## Sobre `renv.lock`
- **Decisión: NO se creó `renv.lock`.** El mandato permite "renv.lock **o equivalente**" / "renv.lock **si aplica**".
- El triple candado (digest + snapshot fechado + manifiesto CSV de versiones reales) ofrece **reproducibilidad equivalente** sin el peso/fragilidad de bootstrapear `renv` dentro de la imagen.
- Si en una etapa posterior se requiere `renv.lock` formal, puede generarse desde el manifiesto sin cambiar la imagen.

## Paquetes incluidos (14 dashboard) — versiones reales en la imagen
| Paquete | Versión | Paquete | Versión |
|---|---|---|---|
| shiny | 1.14.0 | jsonlite | 2.0.0 |
| bslib | 0.11.0 | rmarkdown | 2.31 |
| DT | 0.34.0 | tinytex | 0.60 |
| plotly | 4.12.0 | httr | 1.4.8 |
| highcharter | 0.9.5 | pandoc | 0.2.0 |
| dplyr | 1.2.1 | (stats) | base |
| readr | 2.2.0 | (utils) | base |
| tidyr | 1.3.2 | | |
| htmltools | 0.5.9 | | |

Dependencias transitivas (scales, stringr, lubridate, fs, …) las resuelve `install.packages` automáticamente.

## Paquetes excluidos (deliberadamente)
- **Legacy (MassiveForecasting-V3):** forecast, prophet, shinydashboard, reactable, readxl, openxlsx — NO los usa el dashboard activo.
- **ML pesado / puente Python:** torch, keras, xgboost, lightgbm, reticulate — fuera de la imagen dashboard (principio R-only).

## Verificación
- Gate de build: `RUN Rscript -e "... if(length(miss)) stop(...)"` → falla el build si falta algún paquete. **Pasó** (ALL_R_PKGS_OK).
- Inspección runtime: 14/14 presentes; 0 paquetes ML/Python presentes.
