# AEGIS V5.0B — Docker Readiness Audit + Reproducibility Decisions

**Stage:** V5.0B (gate técnico + decision log)
**Scope:** Auditoría de reproducibilidad y decisiones de empaquetado. **NO** construye Docker. **NO** modifica funcionalmente la app. **NO** crea Dockerfile operativo.
**Active root:** `...\AEGIS-FORESCASTING-IMPROVEMENT\V5`
**Based on:** V5.0A baseline clone (CLOSED — `V5_0A_BASELINE_CLONE_COMPLETED`)
**Closure token (al cierre):** `V5_0B_DOCKER_READINESS_REPRODUCIBILITY_COMPLETED`

---

## 0. Resumen ejecutivo

V5.0B confirma que el **dashboard AEGIS es empaquetable como imagen R-only ligera**, con datos montados read-only, sin secretos en código y sin necesidad del stack pesado de ML/Python. Todos los inventarios (R, Python, sistema), la auditoría de paths y la auditoría de secretos se completaron sobre evidencia real del árbol V5. Se registran 12 decisiones técnicas y 7 riesgos. **No se construyó ninguna imagen ni Dockerfile operativo.**

Conclusiones clave:
1. **Imagen dashboard = solo R** (sin Python, sin torch/darts/lightgbm/xgboost). El dashboard usa 14 paquetes R de runtime (todos instalados).
2. **Refresh = imagen separada y diferida a V5.5**; el refresh real queda **gated a V5.6** porque `ActiveDirectoryInteractive` (MFA con navegador) es incompatible con un contenedor headless.
3. **Sin secretos**: no hay passwords, ni `.env`, ni tokens. La conexión SQL usa Entra ID Interactive (sin credenciales en código).
4. **`outputs/` (1255 MB) y `data/` (155 MB) NO van en la imagen** — se montan read-only. El código real son ~3 MB.
5. `shiny_app/` está **limpio de paths absolutos**; el resolver de raíz es relativo y self-rooting (compatible con `/app` en contenedor).

---

## 1. Inventario de dependencias R (Task A)

Detalle completo en `v5_0b_r_dependencies.csv`. R version objetivo: **4.6.0**.

**Dashboard activo (`shiny_app/`, 42 archivos R/Rmd) — CRÍTICAS, todas instaladas:**
`shiny` 1.13.0, `bslib` 0.11.0, `DT` 0.34.0, `plotly` 4.12.0, `highcharter` 0.9.5, `dplyr` 1.2.1, `readr` 2.2.0, `tidyr` 1.3.2, `htmltools` 0.5.9, `jsonlite` 2.0.0, `rmarkdown` 2.31, `tinytex` 0.59, `pandoc` 0.2.0, `httr` 1.4.8.
Helpers/transitivas instaladas: `commonmark` 2.0.0, `httr2` 1.2.3, `lubridate` 1.9.5, `scales` 1.4.0, `stringr` 1.6.0, `zoo` 1.8-15.
Base R (no instalar, vienen con R): `stats`, `utils`.

**Legacy `MassiveForecasting-V3/` (folder histórico bundleado, NO es el dashboard que corre en :3840) — NO instaladas, EXCLUIR de la imagen:**
`forecast`, `openxlsx`, `plyr`, `prophet`, `RcppRoll`, `reactable`, `readxl`, `shinydashboard`, `shinyjs`, `shinyWidgets`, `xgboost`.
Estas aparecen referenciadas en el viejo dashboard de ingresos CR; al no estar instaladas confirma que **no participan en el runtime gobernado de V5**.

> Falso positivo descartado: `pkg::` (placeholder de documentación) y `stats`/`utils` (base R).

## 2. Inventario de dependencias Python (Task O)

Detalle en `v5_0b_python_dependencies.csv`. `python/requirements.txt` declara solo: **pandas, pyodbc, python-dotenv** (refresh-core). 166 archivos `.py` escaneados.

- **Refresh-core (servicio de refresh, diferido):** pandas, pyodbc, python-dotenv + driver ODBC 18.
- **Model-lab (pesado, congelado/no requerido en V5.1–V5.5):** numpy, scikit-learn, statistics. Histórico de entrenamiento ya ejecutado; el campeón está FROZEN.
- **El dashboard NO usa Python.** La capa de explicación LLM en runtime es R determinista (`llm_compose.R`/`llm_explain.R`), no Python.

## 3. Inventario de dependencias de sistema (Task E)

Detalle en `v5_0b_system_dependencies.csv`.

| Componente | Necesario en imagen dashboard | Motivo |
|---|---|---|
| R 4.6.0 runtime | Sí | Ejecutar Shiny |
| libcurl / openssl | Sí | `httr`/`httr2` (seam LLM mock + descargas) |
| pandoc | Sí | Export HTML/DOCX vía `rmarkdown` |
| TinyTeX / TeX | Sí (o diferir export PDF) | Export PDF de artefactos |
| fontconfig + fuentes (DejaVu/Liberation) | Sí | Render de PDF/DOCX |
| locales UTF-8 | Sí | `LANG/LC_ALL=C.UTF-8` |
| ODBC Driver 18 | **No** (solo refresh) | Conexión SQL del servicio de refresh |

## 4. Auditoría de paths (Task H)

Detalle en `v5_0b_path_audit.csv`. Solo **4 hits** de paths absolutos en código runtime (excluyendo outputs/docs/BACKUP/notebooks):
- `config/project_root_policy.json` (2): marcadores cosméticos, **no** los lee el resolver (`find_project_root` es relativo). No bloquea.
- `python/model_lab/build_interval_calibration.py` (1) y `python/versioning/diagnose_v1_migration.py` (1): scripts dev one-off, no runtime del dashboard ni del refresh-core. No bloquea; recomendación: parametrizar por env en V5.5.
- **`shiny_app/` = 0 paths absolutos.** Runtime limpio y compatible con workdir `/app`.

## 5. Auditoría de seguridad / secretos (Task P)

Detalle en `v5_0b_security_secrets_audit.csv`. **Sin hallazgos de credenciales.**
- `password_kw`: **none**. `bearer_token`: **none**. `.env`: **no existen**.
- `ingestion/config.py` declara textualmente: *"The connection string uses Microsoft Entra ID authentication only. No passwords, secrets, or user credentials are stored in code."* Auth = `ActiveDirectoryInteractive`, `Encrypt=yes`, `TrustServerCertificate=no`.
- Host SQL (`tesseractearth.database.windows.net`) aparece como **nombre de host** (no es credencial) en config + docs/outputs de linaje.
- `api_key` (1 hit) en `versioning/diagnose_v1_migration.py` es un **escáner de nombres de archivo sospechosos** (herramienta de seguridad), no un secreto.
- `azure_openai` (9 hits): referencias de **diseño gated** (contrato de prompt), proveedor real no construido.

Conclusión: **ningún secreto debe entrar a la imagen**; el servicio de refresh tomará la config de conexión vía env/mount, nunca baked.

## 6. Comportamiento de escritura (Task J)

`shiny_app/` solo escribe a: el `file` de `downloadHandler` (destino temporal de descarga) y `tempfile()`/`tempdir()`. `file.copy` en `artifact_export.R:304` copia el CSV canónico **al destino de descarga** (no muta la fuente). **No escribe a `data/processed`.**
→ Volumen de datos montable **read-only**; el contenedor solo necesita un `/tmp` escribible.

## 7. Tamaño de contexto de build

Detalle en `v5_0b_docker_context_size_estimate.csv`. Total V5 = **1414 MB**: `outputs` 1255 MB (89%), `data` 155 MB, `python` 1.8 MB, `shiny_app` 0.9 MB, resto <0.5 MB.
→ `.dockerignore` es **obligatorio** (ver `v5_0b_dockerignore_plan.md`). Imagen de código real ≈ 3 MB + capas de R.

## 8. Decisiones (resumen)

Ver `v5_0b_decision_log.csv` y los `*_decision.md`. 12 decisiones registradas; las 5 más críticas:
1. Dashboard image = **rocker/r-ver:4.6.0**, R-only, pin-by-digest (digest a verificar en V5.1).
2. Pinning R = **Posit Public Package Manager (PPM) snapshot fechado** + `renv.lock` como registro.
3. Datos = **mount read-only** (no baked); `/tmp` escribible.
4. Entrypoint = `Rscript -e shiny::runApp(..., host='0.0.0.0', port=3838)` (sin port-hunting); puerto interno 3838.
5. Refresh real = **diferido V5.5, gated V5.6** (MFA interactivo incompatible con headless).

## 9. Riesgos

Ver `v5_0b_risk_register.csv`. Top: (R1) disponibilidad del tag `r-ver:4.6.0`; (R2) MFA interactivo vs contenedor headless; (R6) licencia Highcharts (highcharter) para uso comercial — **flag legal a revisar**.

## 10. Estado y siguiente paso

V5.0B **completo como gate técnico + decision log**. No se construyó Docker. **No avanzar a V5.1 sin autorización explícita de Oscar.**
