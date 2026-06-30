# AEGIS Forecast Improvement Platform — Handoff V1 → V5

> **Para pegar al inicio del chat V5 (empaquetado / Docker).**
> Documento de contexto completo del proyecto: objetivo, qué se hizo en cada versión (V1–V4), invariantes de gobernanza que NUNCA se rompen, y la estructura propuesta para V5.
> Orquestación: Oscar + ChatGPT dirigen a Claude Opus. Claude implementa; ChatGPT/Oscar supervisan que se respeten las reglas de abajo.

---

## 0. Objetivo del proyecto (qué es AEGIS y para qué existe)

**AEGIS Forecast Improvement Platform** (interno "Goal #3", Substrate Platform CR) es una plataforma de **mejora del proceso de forecasting** de la capacidad de Substrate Backend (Tesseract / TesseractEarthDW).

- **Problema de negocio:** el proceso actual de forecasting se apoya en un puñado de modelos fijos elegidos uno por uno. AEGIS propone una forma **basada en evidencia**: comparar un **universo más amplio de modelos** bajo las mismas reglas, sobre el mismo histórico y con las mismas métricas, y **dejar que los datos decidan** cuál pronostica mejor — sin auto-promover nada.
- **Naturaleza:** dashboard **R Shiny de solo lectura** sobre artefactos **gobernados** (CSV ya calculados por un "Model Lab" en Python). El dashboard **nunca** descarga, limpia, entrena, recalcula ni escribe; solo **lee y muestra**.
- **Datos reales:** SQL Azure `tesseractearth.database.windows.net` → DB `TesseractEarthDW`, tabla `dbo.forecast_substrateBE_hdd_region` (Scenario=Enterprise, ValueType=Forecast-Mean), vía VPN + Entra ID interactivo (MFA manual). Recurso modelado actual = **HDD**.
- **Alcance actual de datos:** 45 entidades (region-environment), histórico de actuals 2019-07-01 → 2026-04-27, forecasts 2026-04-28 → 2030-04-25, ForecastVersion 2026-05-01.

### Stack técnico
- **R 4.6.0** (`C:\Program Files\R\R-4.6.0\bin\x64\Rscript.exe`, no en PATH). Paquetes: shiny, bslib, DT, plotly, highcharter (0.9.5), dplyr, readr, tidyr, htmltools, jsonlite. (pandoc 3.10 + TinyTeX instalados a nivel usuario para exportar PDF/DOCX.)
- **Python 3.14.6** (sistema, sin .venv; usar `PYTHONPATH=<root>\python`). numpy, pandas, sklearn, lightgbm, xgboost, torch (CPU), darts, statsmodels, pyodbc 5.3.0 + ODBC Driver 18.
- **Arranque dashboard:** `scripts\start_shiny.ps1 -PreferredPort <port> -LogDir <rel> -LogPrefix <p>` (lanzar con `powershell -NoProfile -ExecutionPolicy Bypass -File ...`).

### Versionado (carpetas hermanas, cada una raíz independiente y aislada)
`AEGIS-FORESCASTING-IMPROVEMENT/` contiene `V1/ V2/ V3/ V4/` (+ `BACKUP/`). Cada versión tiene su propio `data/`, `outputs/`, `python/`, `shiny_app/`, `config/`, y marcadores de raíz (`ACTIVE_PROJECT_ROOT.md`, `VERSION_INFO.md`, `config/project_root_policy.json`). El dashboard resuelve su raíz subiendo hasta el `ACTIVE_PROJECT_ROOT.md` más cercano, así que **se lanza desde su propia carpeta**.

---

## 1. V1 — Núcleo gobernado + primer build del dashboard (BASE)

**Rol:** primera versión real del codebase. Aquí nació el **pipeline gobernado** (Model Lab en Python) y el **primer Shiny MVP** página por página.

- **Stages 0–6 (Python / Model Lab):** fundación del proyecto, contrato de datos (6 esquemas CSV), replicación del baseline desde SQL, plataforma de evaluación (métricas), Model Lab (modelos candidatos), validación y gobernanza. Estado heredado: **Stage 05 cerrado, Stage 06 aprobado, Audit #6 aprobado**.
- **Resultado de gobernanza (el "campeón"):** tras un **torneo round-robin** (todos-contra-todos, 78 = C(13,2) comparaciones pairwise) sobre **13 modelos puntuados**, se seleccionó **campeón = ETS Explicit** (`CHAMPION_SELECTED_WITH_CONDITIONS`, confianza media, **mediana MASE 6.90 / RMSSE 1.86**). NO se auto-promueve; queda **congelado**.
- **Stage 07 — Shiny MVP:** se construyó el loader de solo lectura (`R/data_loader.R`, registro de ~27–33 artefactos gobernados) y todas las páginas: Home, Overview, Models (Universe/Tournament/Champion), Forecasting (Viewer/Accuracy/Forecast/TTL), Governance (Risks/Audit), Reference (Artifacts/Methodology/Version).
- **Prototipo TTL ("Months-to-Live"):** demanda = forecast real; **supply + TTL = SIMULADOS** y etiquetados "Prototype · simulated supply" (los datos reales de supply existen en vistas SQL pero aún no están gobernados). Gauge tipo velocímetro + heatmap + tabla.
- **Intervalos de pronóstico:** se generaron por **residuales relativos** (scale-invariant) calibrados a horizontes 1–30, niveles 80% y 95%.
- **Prototipo LLM (referencia):** V1 tenía un prototipo Ollama en `server.R` (`.build_prompt_pronos1` + `ollama_generate` + botón narrativa) — semilla del futuro V4.

**Estado:** V1 **congelado**. No se toca jamás.

---

## 2. V2 — Consolidación + pulido del dashboard página por página

**Rol:** copia controlada completa de V1 (robocopy, 2026-06-23, .venv excluido). Aquí se **declutteró y maduró el dashboard** y se completó la capa de intervalos.

- **Re-branding:** plataforma renombrada a **"AEGIS"** (se conservan refs al sistema upstream "TESSERACT v2" y a la tabla SQL real como linaje factual). Texto Home cambia el sistema a "AX".
- **Header "Last update":** indicador estilo Power BI junto al título (lee `run_metadata.csv run_timestamp`).
- **Declutter masivo (Oscar: "más fluido, no tan lleno"):** todas las páginas pasaron a **colapsables** (`home_collapse`), se quitaron muros de KPIs, se removieron páginas redundantes (Comparison, Conditions, Downloads), se quitó jerga interna visible ("Stage 07", "block", "Shiny MVP", etc.).
- **Tournament — iteraciones de visual (clave):** diagnóstico → League View (round-robin) → flow/bracket (rechazado) → **Evidence Tree / dendrograma** (aprobado) agrupando los 13 modelos por evidencia neta (net = better − worse), con bloque "Tournament outcome" (campeón ETS Explicit 8/0/4, net +8). **Regla de oro:** nunca fabricar scores ni un bracket de eliminación falso; el torneo es round-robin real.
- **Champion:** se separó **campeón global gobernado (ETS Explicit)** del **líder local más frecuente por serie (Theta, 8 series)** — el conteo local es **solo diagnóstico**, no decide el campeón.
- **Intervalos 60 días:** nuevo backtest a 60d + recalibración 80% (k=1.5, holdout cov ~0.80); en la página Forecast se muestra **solo 80%** (95% queda en artefacto, no se dibuja). Selectores Forecast = **Next 30 / 60 / 180 días**.
- **TTL realineado a spec oficial:** supply **plano** point-in-time; **todas** las series obtienen un TTL (intersección o eTTL). Seam de proveedor `ttl_provider.R` mock|api (API stub inactivo, listo para datos reales).

**Estado:** V2 **congelado**.

---

## 3. V3 — Metodología + evaluación de modelos + refresh diario (VERSIÓN "CORE" CERRADA)

**Rol:** copia controlada de V2 (2026-06-25). Aquí se cerró el **núcleo metodológico y operativo**. Oscar **sacó la capa LLM de V3** y la movió a V4 (demasiadas consecuencias: proveedor, secrets, costo de tokens, privacidad).

- **V3.1 — Metodología y arquitectura:** documento de proyecto (16 secciones) + **diagrama de arquitectura** (productor Python vs consumidor Shiny read-only) cableado en la página Methodology como imagen + PDF embebido.
- **V3.2 — Reemplazo/evaluación del modelo Deep Learning** (el viejo `FastNeuralAR_MLP` rendía pésimo, MASE ~740, colapso recursivo + 55 forecasts negativos):
  - Diagnóstico (V3.2A), harness experimental (V3.2B), dry-run con **gate de runtime** (V3.2C), **backtest gobernado completo** 39 series × 12 ventanas × h1-30 con presupuesto de tiempo (V3.2D), paquete de decisión (V3.2E).
  - **Resultado:** 6 challengers evaluados; **mejor DL = SMLP-TCN (18.78, 2.72× el campeón)**, mejor ML = ENET-RIDGE (19.33). **NINGUNO** vence a ETS Explicit (6.90). **Campeón sin cambios. Cero promociones.** Todos quedan como "challengers documentados".
  - **Modelos PROHIBIDOS (nunca ejecutar):** **NBEATS, NHITS** (diferidos por runtime/dependencia) y **FastNeuralAR_MLP original** (retirado por alto riesgo).
  - Familia DL final expuesta = 3 modelos (SMLP-TCN, NLIN-DLIN_FIXED, FNAR-V2).
- **V3.3 — Job de refresh diario gobernado (~10 AM):** orquestador `python/orchestration/run_daily_refresh_orchestrator.py` con modos `--dry-run / --validate / --execute-staging / --promote` (promote requiere `--allow-promote`). **Staging → 32 gates de validación → promote vía robocopy + backup_pre_promote + rollback** (nunca swap/rename por locks de OneDrive). `run_metadata.csv` se promueve **al final** (la fecha "Last Update" solo avanza si TODO pasó). Champion congelado como gate; guardia de modelos prohibidos.
- **Cierre:** **V3 MVP CLOSED (2026-06-29)** — validación final 32/32 checks PASS. Universo canónico **15 modelos** (4 Growth + 5 Statistical + 3 ML + 3 DL frozen-reuse), campeón ETS Explicit.

**Estado:** V3 **cerrado**. Dashboard vive en **puerto 3838**, lee `V3/data/processed`.

> **Diferido a backlog/Azure (NO hecho, NO empezar sin orden):** scheduler real (Task Scheduler), VPN auto-login, email/MFA automático, gap detector, notificaciones 10am/6pm.

---

## 4. V4 — Capa de explicación con IA / LLM (AEGIS Explanation Assistant) — MVP LOCAL CERRADO

**Rol:** copia controlada del V3 cerrado (2026-06-29). Objetivo: **añadir una capa de explicación con LLM ENCIMA del core cerrado**. Vive en **puerto 3839**, lee `V4/data/processed`.

### Regla de gobernanza del LLM (oficial, refinada)
> "Shiny no calcula ni modifica artifacts productivos; solo puede construir *evidence packs* temporales de lectura para explicaciones LLM on-demand."
El LLM **EXPLICA**, **nunca decide**. El botón nunca entrena, nunca corre SQL, nunca muta `data/processed`, nunca promueve campeón, nunca recalcula gobernanza. El LLM **nunca ve datos crudos**, solo un evidence pack gobernado y minimizado.

### Fases ejecutadas (todas cerradas, local-first; Azure quedó GATED)
- **V4.0** Baseline formal del clon de V3.
- **V4.1** Diseño LLM (4 botones iniciales → luego 10 secciones).
- **V4.2** **Evidence pack builder** (`python/llm_explanation/build_evidence_pack.py`): lee solo CSV gobernados, **minimiza datos** (ej. de 65 095 filas de forecast solo embebe 5 muestra), sanea lenguaje prohibido, documenta qué NO pasa.
- **V4.3** Insights deterministas (sin LLM, tarjetas/resúmenes desde el evidence pack; hash idéntico entre corridas).
- **V4.4** **Mock provider local** (`llm_client.py` MockLLMClient — determinista, sin LLM real/Azure/red). Narrativas con formato estable: Executive summary / What the evidence says / Why it matters / Sources used / Limitations.
- **V4.5** **Prompt contract** (esquema de salida estable, política de lenguaje prohibido, reglas de validación, rendering contract para Shiny).
- **V4.6 / 6R / 6R2** **Módulo Shiny on-demand** (`shiny_app/R/llm_explain.R` + `R/llm_compose.R`): asistente al **final** de cada sección, caja de pregunta + quick-prompts + botón "Generate explanation", barra de "pensando", respuesta en párrafos, trazabilidad colapsada. **Nivel A** = composición determinista por intención de pregunta desde el evidence pack en runtime (sin LLM real). (Nivel B Ollama = solo plan; Azure = V4.9 gated.)
- **V4.7 / 7B / 7C** **Descargas multi-formato gobernadas** (MD/PDF/DOCX/HTML/TXT vía pandoc+TinyTeX) para las explicaciones, **+ descargas verbatim de los 8 artefactos gobernados** (CSV canónico intacto). Cobertura del asistente expandida a **10 secciones**: Universe, Tournament, Champion, Forecast Viewer, Accuracy, Forecast, TTL, Risks, Audit, Reference Artifacts.
- **V4.8** **Validación local final** → **V4 LOCAL MVP CLOSED + READY FOR DEMO** (33/33 PASS). V4.8R = pulido UI (cache-buster, guías por sección, versión de app = "V4", historial de versiones V1→V5 en Methodology).

### Correcciones de texto recientes (2026-06-30)
- **Overview ("evidence base"):** corregido a **15 modelos gobernados** + **horizontes 30 / 60 / 180 días** (era 13 / "1–30").
- **Tournament legacy:** se mantiene en **13** (su dendrograma/scoreboard/pairwise se renderizan **dinámicamente desde el dato real** de 13 filas; poner 15 ahí exigiría inventar 2 modelos = violación de gobernanza). Etiquetado claramente como **artefacto histórico cerrado**; el ranking vigente de **15** es la vista autoritativa.

**Estado:** V4 **MVP local cerrado**. Azure OpenAI (V4.9) **no** se hizo (GATED).

---

## 5. INVARIANTES DE GOBERNANZA — NUNCA romper (válidos para V5)

1. **Campeón CONGELADO = ETS Explicit** (`CHAMPION_SELECTED_WITH_CONDITIONS`, MASE 6.90 / RMSSE 1.86). Sin auto-promoción jamás.
2. **15 modelos** = universo gobernado vigente (vista autoritativa). **13 modelos / 78 pairwise** = subconjunto del torneo legacy (artefacto cerrado, dato real — NO inflar a 15).
3. **Horizontes de pronóstico: 30 / 60 / 180 días** (selector Forecast). Intervalos calibrados 1–30/1–60, se muestra solo 80%.
4. **Modelos PROHIBIDOS (nunca ejecutar / nunca en producción):** NBEATS, NHITS, FastNeuralAR_MLP (original). No nombrarlos en texto user-facing de guía.
5. **Shiny = solo lectura.** Nunca descarga, limpia, entrena, recalcula, ni escribe `data/processed`. **El LLM explica, nunca decide**, nunca ve datos crudos.
6. **No fabricar datos ni matemáticas falsas.** Si una cifra es data-driven (ej. `nrow`), no se "etiqueta" un número distinto: o coincide con el dato o se reformula con honestidad. Oscar rechaza texto inexacto.
7. **No tocar V1 / V2 / V3** al trabajar en V4/V5. Cada versión es raíz independiente.
8. **Topología de puertos/datos (CRÍTICO):** 3838 = V3 (lee `V3/data/processed`); 3839 = V4 (lee `V4/data/processed`). Son **independientes**; refrescar uno NO actualiza el otro.
9. **No automatizar** login/VPN/MFA/email/scheduler/Azure sin autorización explícita por fase. Oscar hace el login/MFA manualmente.
10. **Backups se conservan** (no limpiar). Cada fase = backend gobernado + **resultado visible** (la visibilidad da confianza).

---

## 6. V5 — EMPAQUETADO / DOCKER (lo que viene)

**Objetivo de V5:** hacer AEGIS **portátil, reproducible y compartible internamente** vía **contenedor Docker**, **sin cambiar nada del forecasting ni de la gobernanza**. V5 = *packaging + deployment*, no nuevos modelos.

### 6.1 Estructura propuesta de V5
- **Base:** copia controlada del V4 cerrado (mismo patrón que V3→V4): robocopy `/E` excluyendo `.venv / __pycache__ / *.pyc`; actualizar los 3 marcadores de raíz a V5; parity check de archivos; V1–V4 intactos.
- **Artefactos de contenedor (nuevos en V5):**
  - `Dockerfile` — imagen con R 4.6 + paquetes fijados (shiny, bslib, DT, plotly, highcharter, dplyr, readr, tidyr, jsonlite) y, si se incluye exportación, pandoc + TinyTeX. (Python solo si se quiere el pipeline dentro; para un demo de **solo-dashboard** basta R.)
  - `docker-compose.yml` — servicio del dashboard, mapeo de puerto (ej. 3838:3838), montaje de `data/processed` y `outputs` (read-only), variables de entorno.
  - `.dockerignore` — excluir `.venv`, `data/raw`, logs, backups, transcripts.
  - `entrypoint` / script de arranque que invoca `start_shiny.ps1`-equivalente para Linux (`Rscript -e "shiny::runApp('shiny_app', host='0.0.0.0', port=3838)"`).
  - Fijado de versiones de paquetes R (renv lockfile o pak/Posit Package Manager con fecha) para **reproducibilidad**.
- **Datos:** decidir política — (a) hornear un **snapshot gobernado** de `data/processed` dentro de la imagen para demo offline, o (b) montar `data/processed` como volumen read-only. **Nunca** meter `data/raw` ni credenciales en la imagen.
- **LLM:** mantener **provider = mock** dentro del contenedor para el MVP (determinista, sin red). Azure OpenAI sigue **gated** (V5.x opcional, con Managed Identity solo si se hostea en Azure).
- **Docs de cierre V5** (mismo estilo que V4): `outputs/v5_*/` con `*_validation.csv`, `*_closure_summary.md`, reporte de build, smoke test del contenedor.

### 6.2 Roadmap oficial de V5 (10 stages — cada uno con autorización + resultado visible + token de cierre)

> Principio: **V5 = última versión local/containerizada (empaquetado), NO una versión para features.** Parte de V4 cerrado, no reabre V1–V4, preserva Shiny como consumidor read-only de artefactos gobernados. Azure, scheduler real y LLM real quedan fuera de V5 (fase futura separada, gated).

- **V5.0A — Baseline Clone from V4**
  - Objetivo: crear la carpeta V5 como copia controlada de V4 cerrado (robocopy `/E`, excluir `.venv / __pycache__ / *.pyc`), actualizar los 3 marcadores de raíz a V5, parity check, V1–V4 intactos. Aún NO hay Docker.
  - Validación: V5 arranca local · HTTP 200 · 10 asistentes visibles · champion = ETS Explicit · scope 15 modelos · sin mutación de datos · V1/V2/V3/V4 intactos.
  - Cierre: `V5_0A_BASELINE_CLONE_COMPLETED`

- **V5.0B — Docker Readiness Audit + Reproducibility Decisions** *(gate técnico real, no solo audit)*
  - Bloques obligatorios: (1) inventario dependencias R · (2) inventario dependencias Python · (3) inventario dependencias de sistema · (4) **estrategia de pinning R** (`renv.lock` o snapshot fechado de Posit Package Manager) · (5) **decisión de imagen base** (`rocker/r-ver` vs `rocker/shiny`; confirmar disponibilidad de R 4.6.0; **fijar por digest `@sha256`**, no solo por tag) · (6) **estrategia pandoc/TeX** (TinyTeX vs texlive mínimo; impacto en tamaño) · (7) **locale/UTF-8/fonts** (`LANG=C.UTF-8`, `LC_ALL=C.UTF-8`, `fontconfig`) · (8) **path audit Windows/OneDrive** (`C:\Users\...`, backslashes, `ACTIVE_PROJECT_ROOT.md`, `VERSION_INFO.md`, `project_root_policy.json`) · (9) **build context audit** (`.dockerignore` agresivo: excluir `data/raw`, `BACKUP`, `outputs` pesados, `.git`, transcripts, `?nocache=` artifacts, cache de `www/`) · (10) plan de HEALTHCHECK · (11) plan de entrypoint · (12) estrategia de volúmenes · (13) feasibility del refresh service · (14) **assessment de auth/SQL/ODBC**.
  - Entregables: `outputs/v5_0_docker_readiness/` → `v5_0_readiness_report.md`, `v5_0_r_dependencies.csv`, `v5_0_python_dependencies.csv`, `v5_0_system_dependencies.csv`, `v5_0_path_audit.csv`, `v5_0_volume_plan.md`, `v5_0_compose_architecture.md`, `v5_0_refresh_service_plan.md`, `v5_0_docker_risk_register.csv`, `v5_0_validation.csv`, `v5_0_closure_summary.md`.
  - Cierre: `V5_0B_DOCKER_READINESS_COMPLETED`

- **V5.1 — Dockerfile Dashboard Image** *(dashboard-first, decisiones de V5.0B ya tomadas)*
  - Imagen base definida (por digest) · R pineado · locale definido · pandoc/TeX decidido o diferido explícito · **entrypoint simple** (`Rscript -e "shiny::runApp('shiny_app', host='0.0.0.0', port=3838)"` — NO portar el port-hunting de PowerShell) · **HEALTHCHECK** (`curl 127.0.0.1:3838`). Imagen del dashboard **solo-R** (Python NO va aquí; se reserva para el refresh service).
  - Archivos: `Dockerfile`, `.dockerignore`, `docker/entrypoint.sh`, `docker/README.md`.
  - Validación: `docker build` OK · `docker run` OK · HTTP 200 · dashboard carga · logs sin errores críticos · mock assistant funciona.
  - Cierre: `V5_1_DOCKERFILE_DASHBOARD_COMPLETED`

- **V5.2 — Docker Compose Shiny Service**
  - `docker-compose.yml` con servicio `shiny`, puerto fijo (`3839:3838`), `data/` y `outputs/` como mounts `:ro`, config reproducible.
  - Validación: `docker compose up shiny` · HTTP 200 · 10 asistentes · downloads básicos · comportamiento V4 preservado.
  - Cierre: `V5_2_DOCKER_COMPOSE_SHINY_COMPLETED`

- **V5.3 — External Volumes / Artifact Mounts** *(decisión arquitectónica central)*
  - Imagen = **código + dependencias estables**; `data/processed`, `outputs`, `logs`, secretos = **fuera** de la imagen. Idea: *image = app estable; data/outputs = artefactos actualizables; refresh = job separado; Shiny = consumidor read-only.*
  - Entregables: `outputs/v5_3_volume_artifacts/` → `v5_3_volume_contract.md`, `v5_3_volume_mapping.csv`, `v5_3_artifact_mount_check.csv`, `v5_3_no_rebuild_data_update_test.md`, `v5_3_validation.csv`, `v5_3_closure_summary.md`.
  - Validación: cambiar un artifact montado se refleja **sin rebuild** · el contenedor no depende de `C:\Users\...` · `data/raw` no entra en la imagen · secretos no entran en la imagen.
  - Cierre: `V5_3_VOLUME_ARTIFACT_MOUNTS_COMPLETED`

- **V5.4 — Dockerized Downloads Validation** *(gate duro)*
  - Validar MD/PDF/DOCX/HTML/TXT (explanations) + governed downloads (CSV verbatim + formatos renderizados) dentro de Linux (pandoc + TeX). **Si PDF/DOCX falla: no se toca lógica funcional, solo capa de sistema/export; no se avanza a cierre final hasta resolver o documentar downgrade explícito.**
  - Cierre: `V5_4_DOCKER_DOWNLOADS_VALIDATED`

- **V5.5 — Refresh Service Dry-Run / Validate** *(servicio separado, sin SQL real)*
  - Servicio `refresh` (imagen con Python) corre `run_daily_refresh_orchestrator.py --dry-run` / `--validate`. **No** meter el refresh dentro de Shiny; **no** botón "Update data" en el dashboard para el MVP. Sub-fases: V5.5A command/dry-run · V5.5B validate mode · V5.5C path validation dentro del contenedor.
  - No hacer todavía: SQL real · Entra/VPN · promote · mutación de `data/processed` · scheduler.
  - Cierre: `V5_5_REFRESH_SERVICE_DRY_RUN_COMPLETED`

- **V5.6 — Controlled Refresh in Container [DEFERRED / GATED]**
  - Status por defecto: `V5_6_CONTROLLED_REFRESH_DEFERRED_GATED`. Razón **técnica** (no solo gobernanza): el auth actual depende de **Entra Interactive + MFA**, incompatible con un contenedor headless. Refresh real requeriría rediseñar auth a **device-code / service principal / managed identity** → decisión arquitectónica futura. **No bloquea el cierre de V5.**
  - Si algún día se autoriza: `V5_6_CONTROLLED_REFRESH_IN_CONTAINER_COMPLETED`.

- **V5.7 — Docker Runbook / Internal Documentation**
  - Cómo correr/parar el contenedor, mapear puertos, montar artefactos, validar salud, ejecutar refresh dry-run, y **qué NO hace V5**.
  - Entregables: `docker/README.md`, `docker/RUNBOOK.md`, `docker/TROUBLESHOOTING.md`, `outputs/v5_7_documentation/v5_7_internal_deployment_guide.md`, `v5_7_validation.csv`, `v5_7_closure_summary.md`.
  - Cierre: `V5_7_DOCKER_DOCUMENTATION_COMPLETED`

- **V5.8 — Final Docker Closure Validation**
  - Checklist final (no agrega features): build PASS · compose up shiny PASS · HTTP 200 · 10 asistentes · downloads + governed downloads · `data/processed` y `outputs` montados · `data/raw` NO en imagen · secretos NO en imagen · refresh dry-run/validate PASS · champion = ETS Explicit · scope 15 modelos · modelos prohibidos ausentes · V1/V2/V3/V4 intactos · sin Azure · sin LLM real · sin scheduler.
  - Estados finales: `V5_DOCKER_LOCAL_MVP_CLOSED` · `V5_READY_FOR_CONTAINER_DEMO` · `V5_DOCKER_PACKAGE_COMPLETED`.

### 6.3 Afinaciones de ingeniería (incorporar en V5.0B/V5.1)
1. **Separar imagen dashboard (solo-R) de imagen refresh (Python).** La imagen que la gente corre en el demo NO debe arrastrar torch/darts/lightgbm/xgboost. Multi-stage o dos Dockerfiles.
2. **Pin por digest, no solo por tag** (`rocker/r-ver@sha256:...`) para reproducibilidad real (un tag puede re-publicarse; el digest es inmutable).
3. **Smoke-test reutilizable + tagging de imagen.** Un único script de smoke (HTTP 200 + 10 asistentes + champion ETS Explicit + 15-model + no-write) corrido igual en V5.1/V5.2/V5.4/V5.8; convención de tags `aegis-dashboard:v5.x`. El cierre V5.8 = correr el smoke una vez más.
4. **Definition-of-done explícito por stage.** Cada stage con 2–3 criterios binarios pasa/no-pasa (los de las validaciones) para que Claude tenga un gate objetivo y no "avance por sentir".

### 6.4 Reglas para Claude Opus en V5 (resumen operativo)
- Trabajar **solo dentro de V5**; no tocar V1–V4. Una fase a la vez, con **autorización explícita** y **resultado visible** por fase.
- **No** cambiar modelos, métricas, campeón, ni texto de gobernanza. **No** fabricar datos. Mantener el dashboard read-only y el LLM en mock.
- **No** meter secretos/credenciales/`data/raw` en la imagen. **No** automatizar VPN/MFA/email/scheduler.
- Validar cada fase con build + smoke + `*_validation.csv` y dejar `*_closure_summary.md`. Conservar backups.
- Verificación de UI con evidencia clara (HTTP 200 + grep del HTML o Playwright); bump del cache-buster CSS tras cambios de estilo.

---

## 7. Estado actual (punto de partida para V5)
- **V4 MVP local CERRADO y listo para demo** (puerto 3839). Overview = 15 modelos + 30/60/180. Tournament legacy = 13 (artefacto histórico etiquetado).
- **V3 cerrado** (puerto 3838). V1, V2 congelados.
- **Próximo paso:** crear **V5** como clone controlado de V4 y arrancar el **empaquetado Docker** (V5.0 → V5.1 …), respetando todos los invariantes de la Sección 5.

---

*Fin del handoff. Pegar este documento al inicio del chat V5 para alinear a Claude Opus con todo el contexto V1→V4 y el plan de empaquetado.*
