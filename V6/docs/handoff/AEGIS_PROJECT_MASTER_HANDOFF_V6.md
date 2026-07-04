# AEGIS — Documento Maestro de Proyecto y Handoff a V6 (Deployment)

> **Propósito de este documento.** Es el "recordatorio completo" para arrancar
> el chat de **V6**. Con él, cualquier asistente o persona entiende de qué trata
> el proyecto, qué se hizo en cada versión (V1 → V5), cuál es el estado
> congelado actual, qué reglas de gobernanza son inviolables, y **qué es V6: la
> versión final de deployment**, con su roadmap por etapas/bloques y el resultado
> esperado de cada una.
>
> **Fecha de creación:** 2026-07-03 · **Autor del cierre V5:** GitHub Copilot (con Oscar)
> **Estado al crear este doc:** V5 LOCAL DOCKER MVP CLOSED
> (`V5_FINAL_DOCKER_VALIDATION_COMPLETED` / `V5_DOCKER_LOCAL_MVP_CLOSED` /
> `V5_READY_FOR_CONTAINER_DEMO`).

---

## 0. Cómo usar este documento para iniciar V6

1. Pega/adjunta este documento al inicio del chat de V6 (o pídele al asistente
   que lo lea desde `V5/docs/handoff/AEGIS_PROJECT_MASTER_HANDOFF_V6.md`).
2. Recuerda la regla base del proyecto: **cada etapa se autoriza explícitamente,
   se ejecuta, se valida con evidencia visible, y se cierra con un token**. No se
   avanza en silencio; si aparece un blocker, se detiene y se reporta.
3. V6 = **deployment a Azure**. Es la única fase donde se toca la nube. Todo lo
   anterior (V1–V5) queda **congelado** salvo que se autorice lo contrario.

---

## 1. Resumen ejecutivo del proyecto AEGIS

**AEGIS Forecast Improvement Platform** es una plataforma de **mejora de la
metodología de forecasting** para el sistema **TESSERACT v2 / Substrate BE**
(capacidad de infraestructura: HDD, SSD, CPU, etc.). El producto visible es un
**dashboard Shiny (R) de solo lectura** que consume **artefactos gobernados**
(CSVs y resúmenes producidos por un "Model Lab" fuera del dashboard).

Ideas centrales:

- **Separación productor/consumidor.** Un pipeline (Python + SQL) *produce*
  artefactos gobernados; el dashboard Shiny solo los *lee*. El dashboard **nunca**
  entrena modelos, corre SQL, recalcula métricas ni cambia el champion.
- **Champion gobernado y congelado.** El modelo campeón es **ETS Explicit**
  (seleccionado *con condiciones*: median MASE 6.90 / RMSSE 1.86). Se mantiene
  frozen; cualquier refresh solo produce candidatos "for review", nunca
  auto-promueve.
- **Universo de 15 modelos** en 4 familias (Growth baseline / Statistical /
  Machine Learning / Deep Learning), con horizontes de **30 / 60 / 180 días**.
- **Lenguaje de gobernanza.** Se evita prometer/afirmar "winner/best/producción
  lista"; el LLM (cuando existe) **explica** artefactos, **no decide**.

Fuente de datos real: SQL `TesseractEarthDW.dbo.forecast_substrateBE_hdd_region`
(Scenario=Enterprise, ValueType=Forecast-Mean), autenticada con **Entra
ActiveDirectoryInteractive** (requiere VPN + MFA). Esto es clave para V6.

---

## 2. Invariantes de gobernanza (HARD RULES — válidas en todas las versiones)

1. **Champion = ETS Explicit**, frozen. Sin auto-promote. Sin cambiar champion.
2. **15 modelos gobernados**; horizontes **30 / 60 / 180**.
3. **Modelos prohibidos (nunca ejecutar):** `NBEATS`, `NHITS`,
   `FastNeuralAR_MLP` (el original). Los 3 DL activos son challengers renombrados
   (FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN), evaluados en fases cerradas.
4. **Shiny es read-only**: no computa, no entrena, no promueve, no escribe
   artefactos, no corre SQL. No hay botón "Update data".
5. **`data/raw` nunca se monta ni se hornea** en imágenes; no es dependencia del
   dashboard. `data/processed` y `outputs` son de **solo lectura** para el
   dashboard.
6. **El LLM explica, no decide.** Provider seam mock | azure_openai | local; en
   local es **mock/determinista** (sin LLM real, sin red).
7. **No secrets en repo/imagen/compose.** Nada de credenciales hardcodeadas.
8. **V1, V2, V3, V4 están congeladas.** No se modifican salvo autorización
   explícita. Cada versión vive en su propia carpeta raíz aislada.
9. **Regla de proceso:** autorización explícita por etapa → ejecución →
   resultado/evidencia visible → token de cierre. Si hay blocker: detener y
   reportar.

Preferencias de Oscar (recurrentes): hacer **exactamente** lo pedido, no agregar
features/tabs/modelos extra; mostrar solo lo final (no cada experimento);
declutter/UX limpio; validar con evidencia real (no inventar resultados);
trabajar rápido (batch de edits → un restart → él refresca el navegador).

---

## 3. Arquitectura general

```
  TESSERACT v2 / SQL (Substrate BE)                [PRODUCTOR — fuera del dashboard]
        │  ingestion (Python + pyodbc + Entra/MFA + VPN)
        ▼
  data/raw/  (hdd_region_*.csv)                     [NO se monta al dashboard]
        │  transform (build_data_contract)
        ▼
  data/processed/  (forecasts, actuals, entities, run_metadata, viewer, TTL, model-eval, canonical universe)
        │  Model Lab (backtests, tournament, champion decision, governance)  [cerrado en V3.2]
        ▼
  outputs/model_lab + outputs/governance + outputs/v4_4_mock_provider (LLM mock JSON)
        │
        ▼  (SOLO LECTURA)
  Shiny dashboard (R)  ──►  navegador  [CONSUMIDOR read-only]
```

- **Imagen Docker = código + dependencias.** Los artefactos viven **fuera** de la
  imagen y se montan read-only. Cambiar un artefacto en el host se refleja en el
  contenedor **sin rebuild** (probado en V5.3).
- **Refresh** (regenerar artefactos) es un **servicio separado** del dashboard,
  no parte de Shiny.

---

## 4. Historia por versiones (qué se hizo y resultado)

### V1 — Primer build gobernado + Shiny MVP
- Primera codebase gobernada de forecasting (Stages 05/06; Audit #6 "approve with
  conditions"). Loader gobernado read-only (`data_loader.R`), registro de
  artefactos, páginas Home/Overview/Models(Universe/Tournament/Champion)/
  Forecasting(Viewer/Accuracy/Forecast/TTL)/Governance(Risks/Audit)/Reference.
- Prototipo TTL (Months-to-Live) con **supply simulado** (demand real), gauge +
  heatmap + tabla. Intervalos de pronóstico (empíricos, relativos, 80%).
- Rebranding a **AEGIS** (marca de la plataforma; se conservan refs al sistema
  TESSERACT/SQL como fuente real).

### V2 — Copia controlada de V1 + limpieza UX
- Robocopy completo de V1 (2026-06-23). Se re-enraíza automáticamente (root
  markers `ACTIVE_PROJECT_ROOT.md`, `VERSION_INFO.md`, `project_root_policy.json`).
- Declutter página por página (Home/Overview colapsables, Universe/Tournament/
  Champion simplificados, Forecasting con layout de dos cajas guiadas, TTL/
  Governance/Reference layout cleanup). Badge "Last update" estilo Power BI.
- Intervalos extendidos a 60 días (recalibrados a cobertura ~0.80). Todo
  read-only, champion sin cambios.

### V3 — Versión "core" final (metodología + operacional)
Copia controlada de V2 (2026-06-25). **V3 = alcance core final.** Subfases:
- **V3.1** Metodología + documentación + diagrama de arquitectura (imagen + PDF
  embebidos en la página Methodology).
- **V3.2 (A–H, CERRADA)** Reemplazo/evaluación del modelo Deep Learning
  (FastNeuralAR_MLP rendía mal). Harness experimental, dry-run + gate de runtime,
  backtest gobernado completo (budget 60 min), decision package. **Ningún
  candidato supera al champion** → todos quedan "keep as challenger", **sin
  promoción**. Se integraron resultados al dashboard (Models + Forecast Viewer con
  los challengers evaluados). V3.2H fijó el universo canónico de 15 modelos.
- **V3.3 (D/E, CERRADA)** Orquestador de refresh diario **staging-only** →
  **controlled promote** (backup + rollback, robocopy, sin swap por locks de
  OneDrive). 32 gates. `run_metadata.csv` se promueve al final. Refresh manual
  controlado ejecutado varias veces (VPN + Entra Interactive).
- **H Final Validation → V3 MVP CLOSED** (2026-06-29). Scheduler/VPN-auto/email/
  MFA quedaron **diferidos** (backlog/Azure).

### V4 — Capa de explicación LLM (local, mock)
Copia controlada de V3 cerrada (2026-06-29). Objetivo: **AEGIS Explanation
Assistant** — botones que **explican** artefactos gobernados, sin computar/ver
raw/cambiar champion. Fases:
- V4.0 baseline; V4.1 diseño; V4.2 evidence pack builder; V4.3 insights
  determinísticos; V4.4 **mock provider** (sin LLM real); V4.5 prompt contract;
  V4.6/R/R2 panel Shiny on-demand con **motor de composición local determinista**
  (genera respuestas desde el evidence pack por intención de pregunta; nunca
  decide); V4.7/B/C **descargas** (MD/PDF/DOCX/HTML/TXT + CSV verbatim gobernado),
  cobertura de **10 asistentes** en las secciones; V4.8/R final validation →
  **V4 LOCAL MVP CLOSED**.
- Se instaló **pandoc + TinyTeX** a nivel usuario (para PDF/DOCX). Provider real
  Azure OpenAI quedó **V4.9 GATED** (no ejecutado).
- Refresh manual controlado también en V4 (puerto 3839, capa LLM).

### V5 — Empaquetado Docker (MVP local/contenedorizado) — **CERRADA**
Copia controlada de V4 (2026-06-30). **V5 = packaging/deployment local; NO cambia
forecasting/gobernanza.** Etapas:

| Etapa | Token de cierre | Qué se hizo |
|-------|-----------------|-------------|
| V5.0A | V5_0A_BASELINE_CLONE_COMPLETED | Clon controlado de V4 (paridad, hashes) |
| V5.0B | V5_0B_DOCKER_READINESS_REPRODUCIBILITY_COMPLETED | Auditoría de dependencias + 14 decisiones (R-only, TinyTeX, RO mounts, .dockerignore, sin data/raw) |
| V5.1 | V5_1_DOCKERFILE_DASHBOARD_IMAGE_COMPLETED | Imagen R-only `aegis-dashboard:v5.1` (base `rocker/r-ver:4.6.0` pin por digest); smoke 11/11 |
| V5.2 | V5_2_DOCKER_COMPOSE_SHINY_SERVICE_COMPLETED | `docker-compose.yml` servicio `shiny`, `8080:3838`, RO mounts, `restart unless-stopped` |
| V5.3 | V5_3_EXTERNAL_VOLUMES_ARTIFACT_MOUNTS_COMPLETED | Contrato de volúmenes externos: 9/9 required presentes; **reflexión sin rebuild**; RO enforcement; sin `data/raw` |
| V5.4 | V5_4_DOCKERIZED_DOWNLOADS_VALIDATED | Downloads en contenedor: Explanation (MD/PDF/DOCX/HTML/TXT) + Governed (CSV verbatim + MD/PDF/DOCX/HTML/TXT). **Blocker PDF resuelto** horneando TinyTeX (rebuild de la imagen, mismo tag) |
| V5.5 | V5_5_REFRESH_SERVICE_DRY_RUN_VALIDATE_COMPLETED | Servicio **separado** `refresh` (`aegis-refresh:v5.5`, python-slim, sin pyodbc/pandas/ML) en modo **validate-only**; wrapper `scripts/refresh_validate_only.py`; profile `refresh`; sin SQL/modelos/promote/mutación |
| V5.6 | **DEFERRED / GATED** | Refresh **real** en contenedor: bloqueado por **MFA headless** (ActiveDirectoryInteractive) → requiere auth no-interactiva |
| V5.7 | V5_7_DOCKER_RUNBOOK_INTERNAL_DOCS_COMPLETED | Documentación interna: `docker/README.md`, `docker/RUNBOOK.md`, `docker/TROUBLESHOOTING.md`, `docker/LOCAL_DEMO_CHECKLIST.md`, `docs/v5_7_*` |
| V5.8 | **V5_FINAL_DOCKER_VALIDATION_COMPLETED / V5_DOCKER_LOCAL_MVP_CLOSED / V5_READY_FOR_CONTAINER_DEMO** | Validación de cierre end-to-end: 37/37 checks, smoke 11/11, gobernanza intacta, sin mutación |

---

## 5. Estado congelado actual (punto de partida para V6)

- **Imágenes Docker locales:**
  - `aegis-dashboard:v5.1` → id `a799da697173`, ~2.47 GB (R-only + pandoc + TinyTeX). **NO Python.**
  - `aegis-refresh:v5.5` → id `698b1634f78a`, ~180 MB (python:3.12-slim, sin pyodbc/pandas/ML; solo validate-only).
- **Compose:** servicios `shiny` (default) + `refresh` (profile `refresh`, one-shot).
- **Comandos locales validados:**
  - `docker compose up -d shiny` → http://127.0.0.1:8080
  - `docker compose run --rm refresh` → `V5_5_REFRESH_VALIDATE_OK` (no actualiza datos)
  - `powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080`
- **Baselines de datos (no deben cambiar):** `data/processed` = 24 archivos
  (hash agregado `B0880D33…D61`); `data/raw` = 6 archivos (hash `BD44163A…73D`).
- **Contrato de artefactos gobernados** documentado en
  `V5/outputs/v5_3_external_volumes_artifact_mounts/v5_3_volume_contract.md` y el
  manifiesto de runtime (43 entradas; 9 required) — base para V6.
- **Raíces de versión:** `AEGIS-FORESCASTING-IMPROVEMENT/{V1,V2,V3,V4,V5}` +
  `BACKUP/V1`. Cada una auto-enraíza. V6 será una **copia controlada de V5**.

---

## 6. Lo que está GATED / diferido (entra a decisión en V6)

1. **Auth no-interactiva para SQL/Azure.** `ActiveDirectoryInteractive` (MFA) no
   funciona headless. Opciones a decidir: **device-code**, **service principal**
   (secreto/cert en secret store), **managed identity** (cuando esté hospedado en
   Azure). — *Bloqueante para refresh real y para conectar a SQL desde la nube.*
2. **Refresh real end-to-end** (SQL → ingest → transform → models → controlled
   promote). Hoy solo existe validate-only.
3. **Azure deployment** (hosting del dashboard y/o del refresh).
4. **Azure OpenAI (LLM real)** — el V4.9 gated; el seam ya existe (mock ↔ azure_openai).
5. **Scheduler** (10am/6pm) — sin cron/Task Scheduler/GitHub Actions todavía.
6. **Secrets management** (Key Vault / secret store).
7. **Highcharts / highcharter** — licencia comercial de Highcharts → revisión
   legal antes de exponer públicamente.
8. **Fuente Inter (bslib)** se descarga en runtime → bundle offline para entornos
   sin red.

---

## 7. V6 — DEPLOYMENT (Azure): objetivo, principios y roadmap

### 7.1 Objetivo de V6
Llevar el MVP local/contenedorizado (V5) a un **deployment gobernado en Azure**:
hospedar el dashboard read-only de forma segura y reproducible, resolver la
**autenticación no-interactiva**, gestionar **secrets** correctamente, y —de
forma gated y por etapas— habilitar el **refresh real** y opcionalmente el **LLM
real (Azure OpenAI)**. Todo respetando las invariantes de gobernanza.

> **Qué NO es V6:** no reescribe forecasting ni gobernanza; no cambia el champion;
> no agrega botón refresh al dashboard; no promete "producción" hasta pasar sus
> propios gates.

### 7.2 Principios de V6
1. **Copia controlada de V5** como baseline (V6.0A), V1–V5 congeladas.
2. **Autorización explícita por etapa** + resultado visible + token de cierre.
3. **Least privilege**: identidades con el mínimo rol (RBAC), secrets solo en
   **Key Vault** / secret store, nunca en imagen/repo/compose.
4. **Auth no-interactiva primero** (device-code / service principal / **managed
   identity** preferida cuando ya esté hospedado). MFA interactivo no aplica
   headless.
5. **Dashboard sigue read-only**; refresh sigue siendo un servicio separado.
6. **Reproducibilidad**: imágenes pinneadas, IaC (Bicep/Terraform) versionado,
   builds deterministas.
7. **Gated real refresh**: primero validate/dry-run en la nube, luego (con
   autorización) refresh real con staging → gates → controlled promote → rollback.
8. **Costo y seguridad**: revisar SKU/plan, egress, private networking hacia SQL
   (VPN/Private Link), y la licencia de Highcharts antes de exposición externa.

### 7.2b Estrategia ADOPTADA (oficial — Oscar aprobó 2026-07-03)

**Roadmap oficial = el detallado de 11 etapas de este documento** (se descarta la
variante compacta de 8 etapas del briefing CGPT). La granularidad es una
característica de seguridad: separar Identidad / Registry / Deploy / SQL / Refresh
en etapas distintas evita que el agente mezcle en un solo paso algo inofensivo con
algo sensible.

**El roadmap se organiza en DOS TRACKS separados por un GATE DURO:**

```
TRACK A — Consumidor read-only (SEGURO, no toca SQL)
  V6.0A Clone → V6.0B Readiness → V6.1 Identity/RBAC/KeyVault
  → V6.2 ACR/push → V6.3 Dashboard deploy → V6.4 Cloud downloads
        ══════════ GATE DURO: decisión + autorización explícita ══════════
TRACK B — Productor real (SENSIBLE: SQL/auth/refresh/scheduler/LLM)
  V6.5 SQL connectivity → V6.6 Real refresh → V6.7 Scheduler
  → V6.8 Azure OpenAI (opcional) → V6.9 Observability → V6.10 Final closure
```

- **V6 puede CERRARSE en Track A** como "dashboard cloud read-only" (demo), sin
  activar refresh real — igual que V5 cerró sin V5.6. Track B es otra conversación.
- **Nada toca SQL ni auth de producción antes del gate duro (post-V6.4).**

**6 DECISIONES DE ARRANQUE (registradas):**
1. Arranque = **V6.0A Baseline Clone desde V5** (copia controlada + paridad + smoke), NO saltar directo a Azure.
2. Deploy inicial = **dashboard read-only en Azure sin refresh real** (cerrar Track A primero).
3. **Permisos Azure = prerequisito #1 de V6.0B** — confirmar capacidad de crear Container Apps, ACR, Key Vault, Managed Identity, Storage/Azure Files, y (Track B) VNet/Private Link.
4. Endpoint = **privado/interno por defecto** con control de acceso (Entra), hasta autorización contraria (mitiga también exposición de Highcharts).
5. Artifact storage = **Azure Files montado read-only para V6.3** (análogo directo a los mounts de V5); **Blob** para staging/productive del refresh real (Track B).
6. **Azure OpenAI = opcional/gated (V6.8), aislado** — no mezclar LLM real con deploy + refresh real a la vez.

**ESTRATEGIA DE AUTH (se congela en V6.0B, condiciona todo Track B):**
diseñar alrededor de **Managed Identity** (preferida, sin secrets) →
**Service Principal** (fallback, secreto/cert SOLO en Key Vault) →
**device-code** (solo pruebas puntuales) →
**refresh manual local** (fallback operativo, ya probado en V3/V4).
`ActiveDirectoryInteractive + MFA` DESCARTADO para headless.

**Hosting recomendado (a confirmar en V6.0B):** **Azure Container Apps** (separa
dashboard app + refresh job + managed identity + logs + secrets + networking de
forma limpia). App Service for Containers = alternativa para el dashboard, menos
natural para jobs. AKS = demasiado pesado para este MVP.

### 7.3 Roadmap de V6 por etapas (ADOPTADO; cada una se autoriza aparte)

> Nota: los tokens se confirman al iniciar cada etapa. Cada etapa produce
> entregables en `V6/outputs/<etapa>/` + validación + closure summary, igual que
> en V5. Track A = V6.0A–V6.4 (+V6.9 si se cierra ahí); Track B = V6.5–V6.10 tras
> el gate duro.

| Etapa | Nombre | Objetivo / bloques | Resultado esperado (token) |
|-------|--------|--------------------|----------------------------|
| **V6.0A** | Baseline Clone desde V5 | Clonar V5 → V6 (excl. `.venv/__pycache__/...`); actualizar root markers; verificar paridad (tree + hashes); smoke del dashboard local. | `V6_0A_BASELINE_CLONE_COMPLETED` |
| **V6.0B** | Azure Readiness + Decisiones | Inventario de recursos Azure necesarios; elegir **servicio de hosting** (Azure Container Apps recomendado vs App Service for Containers vs AKS); elegir **estrategia de auth** (managed identity preferida); definir manejo de **secrets (Key Vault)**; definir **registry** (ACR); estimar **costos**; revisar **licencia Highcharts**; decidir **sourcing de artefactos** (volumen montado vs producidos por refresh). Solo auditoría + decisiones, sin desplegar. | `V6_0B_AZURE_READINESS_DECISIONS_COMPLETED` |
| **V6.1** | Identidad, RBAC y Secrets | Crear/registrar identidad (managed identity / service principal); asignar **roles mínimos** (ACR pull, Key Vault secrets user, SQL DB reader si aplica); crear **Key Vault**; cargar secrets (sin exponerlos). Sin correr SQL real todavía. | `V6_1_IDENTITY_RBAC_SECRETS_COMPLETED` |
| **V6.2** | Container Registry + Push de imágenes | Crear **ACR**; push de `aegis-dashboard` (y opcional `aegis-refresh`) con tags versionados/digest; validar pull con la identidad. Sin cambiar la lógica de las imágenes. | `V6_2_REGISTRY_IMAGES_PUSHED_COMPLETED` |
| **V6.3** | Deploy del Dashboard (read-only) | Desplegar el dashboard en el servicio elegido, **read-only**, consumiendo artefactos (montados o empaquetados según V6.0B); HTTPS/ingress; healthcheck; **smoke reusable** contra la URL de Azure; confirmar invariantes (champion, 15 modelos, 30/60/180, 10 asistentes). | `V6_3_DASHBOARD_DEPLOYED_COMPLETED` |
| **V6.4** | Downloads en la nube | Validar Explanation + Governed downloads (incl. PDF/DOCX) en el entorno Azure (TinyTeX/pandoc en imagen); firmas %PDF/PK; sin secrets/traceback; sin mutación de artefactos. | `V6_4_CLOUD_DOWNLOADS_VALIDATED` |
| **GATE DURO** V6.4→V6.5 | Track B Authorization Review | Decidir formalmente si se cruza a SQL/auth/refresh real. Revisar permisos, seguridad, costos, networking, Managed Identity, riesgos. **No avanzar a Track B sin autorización explícita.** | `V6_4_TO_V6_5_HARD_GATE_REVIEW_COMPLETED` |
| **V6.5** | Private SQL connectivity (sin refresh real) | Conectividad privada/no-interactiva hacia SQL (Private Link / VNet / VPN, ODBC, MI/SPN) + prueba mínima autorizada (p.ej. `SELECT 1` **solo si se autoriza**). No ingesta full, no modelos, no promote. Reportar si MFA/red bloquea. | `V6_5_PRIVATE_SQL_CONNECTIVITY_VALIDATED` |
| **V6.6** | Refresh real gobernado (GATED) | **Solo si se autoriza y si V6.5 pasó.** Habilitar el pipeline real con auth no-interactiva: staging → 32 gates → **controlled promote** (backup + rollback) → actualizar artefactos que consume el dashboard; **sin auto-cambiar champion**; sin botón en Shiny. | `V6_6_CLOUD_REFRESH_GOVERNED_COMPLETED` |
| **V6.7** | Scheduler / automatización (GATED) | **Solo si se autoriza.** Programar el refresh (Container Apps Job / Logic App / cron gobernado) con preflight de conectividad, notificación y auditoría; nunca auto-promueve sin gates. | `V6_7_SCHEDULER_AUTOMATION_COMPLETED` |
| **V6.8** | LLM real Azure OpenAI (OPCIONAL/GATED) | **Solo si se autoriza.** Cambiar el provider seam mock → azure_openai con **managed identity** (rol "Cognitive Services OpenAI User"), sin secrets en repo; el LLM sigue **explicando, no decidiendo**; fallback a mock. | `V6_8_AZURE_OPENAI_READINESS_COMPLETED` |
| **V6.9** | Observabilidad, costo y hardening | App Insights/Log Analytics, alertas, límites de escala, revisión de costos, WAF/reliability según corresponda; runbook de operación en la nube. | `V6_9_OBSERVABILITY_HARDENING_COMPLETED` |
| **V6.10** | Cierre final de deployment | Validación end-to-end en Azure; documentación de operación; checklist de demo en la nube; declaración de estado. | `V6_FINAL_DEPLOYMENT_VALIDATION_COMPLETED` / `V6_AZURE_DEPLOYMENT_CLOSED` / `V6_READY_FOR_PRODUCTION_REVIEW` |

> **Orden y gating:** V6.0A→V6.4 pueden avanzar como "deploy del consumidor
> read-only" sin tocar SQL. **V6.5 en adelante es la parte sensible** (SQL/auth/
> refresh real/scheduler/LLM real) y cada una requiere autorización explícita. Se
> puede **cerrar V6 como "dashboard desplegado read-only"** (hasta V6.4/V6.9) sin
> activar refresh real, exactamente como V5 cerró sin V5.6.

### 7.4 Formato de cada etapa V6 (igual que V5)
Cada etapa entrega, en `V6/outputs/<etapa>/`:
- `*_preflight_check.csv`, validaciones específicas (`*_validation.csv`),
- logs en `logs/`,
- `*_closure_summary.md` con **tablas obligatorias** (artifacts, validación
  específica, gobernanza, inmutabilidad, riesgos, estado global),
- actualización de `VERSION_INFO.md` (current_status/next_stage) y de la memoria.
- Regla de oro: **evidencia real**, no inventada; si algo falla, blocker + reporte.

---

## 8. Riesgos y decisiones pendientes para arrancar V6

> **Dirección ya adoptada (2026-07-03):** ver §7.2b. Aquí quedan solo las
> confirmaciones finales/insumos que se cierran en V6.0B y el gate duro.

1. **Estrategia de auth** — DIRECCIÓN FIJADA: **Managed Identity primero**,
   Service Principal (Key Vault) como fallback; device-code solo pruebas; manual
   local como fallback operativo. Confirmación final en **V6.0B**.
2. **Servicio de hosting** — DIRECCIÓN FIJADA: **Azure Container Apps**.
   Confirmación final (contra permisos/costo) en **V6.0B**.
3. **Sourcing de artefactos** — DIRECCIÓN FIJADA: **Azure Files read-only para
   V6.3**; Blob para staging/productive del refresh real. Confirmación en **V6.0B**.
4. **Permisos Azure (prerequisito #1)** — confirmar en **V6.0B** que se pueden
   crear Container Apps, ACR, Key Vault, Managed Identity, Storage/Azure Files, y
   (Track B) VNet/Private Link. **Sin esto, Track A no pasa del clone.**
5. **Endpoint privado/interno** por defecto con control de acceso Entra
   (confirmar en **V6.0B/V6.3**).
6. **Conectividad a SQL** (Private Link / VNet / VPN) y si se permite `SELECT 1`
   de prueba. — **Gate duro / V6.5.**
7. **Licencia de Highcharts** antes de exposición externa. — **Legal.**
8. **Costo/SKU** y política de escalado. — **V6.0B / V6.9.**
9. **Datos sensibles**: confirmar que solo salen artefactos gobernados (no raw) y
   que no hay PII/credenciales en downloads.

---

## 9. Checklist para arrancar el chat de V6

- [ ] Adjuntar este documento y confirmar tokens de cierre de V5.
- [ ] Confirmar que V1–V5 quedan congeladas.
- [ ] Autorizar **V6.0A** (baseline clone) con la frase explícita.
- [ ] Tener listo: suscripción Azure, permisos para crear recursos, y decisión
      preliminar de hosting/auth (se afina en V6.0B).
- [ ] Recordar: **no SQL real / no MFA headless / no auto-promote / dashboard
      read-only** hasta pasar los gates correspondientes.

---

## 10. Tokens de cierre esperados de V6 (referencia)

```
V6_0A_BASELINE_CLONE_COMPLETED
V6_0B_AZURE_READINESS_DECISIONS_COMPLETED
V6_1_IDENTITY_RBAC_SECRETS_COMPLETED
V6_2_REGISTRY_IMAGES_PUSHED_COMPLETED
V6_3_DASHBOARD_DEPLOYED_COMPLETED
V6_4_CLOUD_DOWNLOADS_VALIDATED
V6_5_PRIVATE_SQL_CONNECTIVITY_VALIDATED
V6_6_CLOUD_REFRESH_GOVERNED_COMPLETED        (GATED)
V6_7_SCHEDULER_AUTOMATION_COMPLETED          (GATED)
V6_8_AZURE_OPENAI_READINESS_COMPLETED        (OPCIONAL/GATED)
V6_9_OBSERVABILITY_HARDENING_COMPLETED
V6_FINAL_DEPLOYMENT_VALIDATION_COMPLETED / V6_AZURE_DEPLOYMENT_CLOSED / V6_READY_FOR_PRODUCTION_REVIEW
```

**No declarar** "production ready" hasta pasar V6.9/V6.10 y la revisión de
gobernanza/seguridad/costo correspondiente.

---

### Anexo A — Comandos clave heredados de V5 (siguen válidos localmente)
```powershell
docker compose up -d shiny        # dashboard local -> http://127.0.0.1:8080
docker compose logs -f shiny
docker compose restart shiny
docker compose down
docker compose run --rm refresh   # validate-only (NO actualiza datos)
powershell -ExecutionPolicy Bypass -File scripts/docker_smoke_test.ps1 -Url http://127.0.0.1:8080
```

### Anexo B — Rutas de referencia
- Cierre V5.8: `V5/outputs/v5_8_final_docker_closure/v5_8_final_closure_report.md`
- Contrato de volúmenes: `V5/outputs/v5_3_external_volumes_artifact_mounts/v5_3_volume_contract.md`
- Runbook/troubleshooting: `V5/docker/RUNBOOK.md`, `V5/docker/TROUBLESHOOTING.md`
- Gating de refresh real: `V5/docs/v5_7_v5_6_gating_note.md`
- Este documento: `V5/docs/handoff/AEGIS_PROJECT_MASTER_HANDOFF_V6.md`
