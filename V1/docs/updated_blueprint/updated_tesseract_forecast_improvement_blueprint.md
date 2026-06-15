# Blueprint Actualizado — TESSERACT v2 / AEGIS Forecast Improvement Platform

> **Tipo de documento:** Reconstrucción de blueprint dirigida por el repositorio (review-only).
> **Fecha:** 2026-06-12
> **Autor del review:** Principal Forecasting Platform Architect / Project Blueprint Auditor
> **Modo:** Solo revisión. No se modificó código, configs, datos, modelos ni rankings.
> **Raíz del proyecto:** `AEGIS-FORESCASTING-IMPROVEMENT`
> **Blueprint de referencia:** `Blueprint --- TESSERACT v2 Forecast Improvement Platform.pdf`

---

## Nota metodológica (evidencia)

Toda afirmación de estado en este documento está respaldada por artefactos reales encontrados en el
repositorio (configs en `config/`, código en `python/model_lab/`, salidas en `outputs/model_lab/`, y los
dos audits en `outputs/model_lab/audits/`). El `README.md` de la raíz **está desactualizado** (marca casi
todas las etapas como *Pending*); fue descartado como fuente de verdad y reemplazado por la evidencia de
ejecución. La verdad de estado proviene de los outputs y de los audits, no del README.

### Reconciliación de hechos de datos (Stage 3 vs implementación)

Existe una diferencia legítima entre los *hechos de datos crudos de Stage 3* y los *hechos de la ejecución
del baseline de Stage 5*. No es un error; son dos planos distintos:

| Hecho | Stage 3 (fuente cruda) | Implementación Stage 5 (ejecutado) | Evidencia |
|---|---|---|---|
| Entidades | 45 | **39** (subconjunto con historia suficiente) | `full_baseline_summary.csv`, audits |
| Modelos baseline | 16 ModelVersions (fuente) | **7** modelos baseline implementados | `baseline_metrics_by_model.csv` |
| ForecastVersion | 2026-05-01 (Enterprise) | 2026-05-01 (Enterprise) | consistente |
| Tabla métricas | `forecast_substrateBE_hdd_region_metrics` | misma (validación) | `evaluation_source_summary.txt` |
| Ventanas backtesting | — | **454** (de ~468 teóricas; ~14 entidades de historia corta) | `full_baseline_summary.csv`, AUDIT #1 |

> **Observación crítica de evidencia:** la tabla `..._region_metrics` muestra `ModelVersions available:`
> **vacío**. Las "16 ModelVersions del baseline" no se pudieron confirmar desde la tabla de métricas
> inspeccionada; el baseline implementado y ejecutado en el Model Lab usa **7 modelos**. Esta discrepancia
> debe documentarse explícitamente antes de cualquier publicación externa.

---

## A. Resumen del Blueprint Original

El blueprint original define una plataforma de evaluación de forecasting en **9 etapas** cuya tesis central
es: *"TESSERACT actual = Baseline. Framework propuesto = candidato de mejora. Los datos deciden."*

| # | Etapa | Propósito original |
|---|---|---|
| 1 | Project Foundation | Estructura de carpetas, arranque de Shiny, base del repo |
| 2 | Vision & Wireframe | Visión ejecutiva + wireframes (`docs/wireframes/`) |
| 3 | Data Contract | Esquemas de datos fijos (forecasts, actuals, metrics, rankings, run_metadata, recommendations) |
| 4 | Baseline Replication / Evaluation Platform | Reproducir output TESSERACT + plataforma de evaluación (métricas, datasets) |
| 5 | Model Lab | Ejecutar modelos baseline + candidatos, ranking, comparación, torneo |
| 6 | Validation Lab & Governance | Composite score, validación, gobierno, recomendaciones |
| 7 | UI/UX + LLM Insights | UX ejecutivo + narrativas LLM (Ollama / Claude API) |
| 8 | Codebase Improvement | Deliverable G3 de mejora de código |
| 9 | (Cierre / entrega) | Consolidación final |

> **Nota de numeración:** el `README.md` enumera las etapas **0–8**; el blueprint de gobierno las enumera
> **1–9**. En este documento se usa la numeración **1–9** del enunciado. La regla arquitectónica fijada
> durante la implementación (R/Shiny solo presentación, Python todo el procesamiento, `app.R` ≤ 30 líneas)
> **no estaba en el blueprint original** y es una evolución posterior.

---

## B. Estado Actual del Repositorio

### Regla arquitectónica — VERIFICADA Y CUMPLIDA

- **`shiny_app/app.R` tiene 7 líneas** (solo `source()` + `shinyApp()`). Cumple el límite de ≤ 30 líneas y
  la regla de "solo orquestación". El Shiny está modularizado en `ui/`, `server/`, `modules/`, `R/`.
- **Todo el procesamiento, métricas, modelos y rankings viven en `python/`** (`model_lab/`, `evaluation/`,
  `ingestion/`, `transform/`, `utils/`). No se detectó cálculo de métricas en R.

### Inventario de evidencia clave

**`config/` (7 archivos):** `backtesting.yaml`, `execution.yaml`, `multistep_forecasting.yaml`,
`ranking_policy.yaml`, `scoring_definitions.yaml`, `scoring_weights.yaml`, `tournament.yaml`.

- `execution.yaml`: `training_enabled: false`, `dry_run: true` → **triple-gate de ejecución activo**.
- `backtesting.yaml`: walk-forward, horizonte 30 días, ventana expansiva, min 365 train / 30 test.
- `ranking_policy.yaml`: `normalization.method: percentile_rank_within_entity_window`, `policy_status:
  design_only`, `policy_scope: baseline_models_only`, prohíbe explícitamente evaluar challengers.
- **Deriva de configs (confirmada):** `scoring_weights.yaml` usa 6 métricas (wmape/mape/rmse/bias/
  stability/horizon) pero el ranking publicado usa `ranking_metric_weights.csv` (5 métricas, sin stability
  ni horizon). Dos sistemas de pesos divergentes coexisten.

**`python/model_lab/models/` (14 clases registradas):**
- Baseline implementados y ejecutados: `arima_fixed_model`, `ets_current_model`, `linear_regression_model`,
  `fixed_growth_model` (1.5/3/4/6).
- Challengers **solo como placeholders**: `autoarima_model`, `theta_model`, `lightgbm_model`,
  `xgboost_model`, `nbeats_model`, `nhits_model`, `ets_model`.

**`outputs/model_lab/` (evidencia de ejecución):**
- `full_baseline/full_baseline_summary.csv`: **run `full_baseline_20260611_103953` → 454 ventanas, 39
  entidades, 7 modelos, 3,178 jobs planificados = 3,178 ejecutados, 0 fallos, 95,340 filas de forecast.**
- `metrics/` (engine de métricas: wMAPE, MAPE, RMSE, SMAPE, abs bias) — calculado.
- `ranking_policy/`, `ranking_dry_run/`, `baseline_ranking/baseline_ranking_publication.csv` — ranking
  publicado (ETS_Current 64.18 → … → FixedGrowth_6 17.04).
- `metrics_sanity/`, `sanity_review/`, `outlier_drilldown/` — revisión y outliers completados.
- `audits/`: `stage_5_pre_training_audit.md` (AUDIT #1 → **APPROVED WITH CHANGES**) y
  `stage_5_challenger_readiness_audit.md` (AUDIT #2 → **BLOCKED**).
- **Vacíos / no iniciados:** `tournament/`, `dashboard/`, `outputs/governance/`, `outputs/baseline/`.

**`tests/`** está **vacío** — riesgo de regresión sin cobertura automatizada (señalado por ambos audits).

---

## C. Estado Etapa por Etapa

### Etapa 1 — Project Foundation
- **Propósito original:** estructura de repo + arranque de Shiny.
- **Bloques implementados:** estructura de carpetas, `setup.R`, `app.R` (7 líneas), modularización Shiny,
  regla arquitectónica R-presentación / Python-procesamiento.
- **Bloques pendientes:** ninguno.
- **Estado: Done.**

### Etapa 2 — Vision & Wireframe
- **Propósito original:** visión ejecutiva + wireframes.
- **Bloques implementados:** definición de visión (README), estructura `docs/wireframes/`.
- **Bloques pendientes:** `docs/wireframes/` está **vacío** en disco (los wireframes no están versionados como
  artefactos). UX final pertenece a Etapa 8.
- **Estado: Done (con deuda menor de artefactos de wireframe).**

### Etapa 3 — Data Contract
- **Propósito original:** esquemas de datos fijos.
- **Bloques implementados:** contrato de datos confirmado contra fuente real
  (`forecast_substrateBE_hdd_region` + `..._region_metrics`), ForecastVersion 2026-05-01 Enterprise, rangos
  de actuals/forecasts confirmados, inventario de fuentes (`evaluation_source_summary.txt`).
- **Bloques pendientes:** documentar formalmente la discrepancia 45→39 entidades y 16→7 modelos.
- **Estado: Done (Needs Revision menor: discrepancia de conteos por documentar).**

### Etapa 4 — Evaluation Platform (antes "Baseline Replication")
- **Propósito original:** reproducir output TESSERACT + plataforma de evaluación.
- **Bloques implementados:** descubrimiento de fuentes (`discover_evaluation_sources.py`), construcción del
  `evaluation_dataset.csv`, inventario de ventanas de backtest, validación de métricas oficiales contra la
  tabla de métricas, exports de dashboard de evaluación, **fundación de la plataforma de evaluación**.
- **Bloques pendientes:** ninguno para la fundación; el motor de ranking semántico migró a Stage 5.
- **Estado: Done.** *(No regresar trabajo actual a esta etapa: la fundación de evaluación quedó establecida
  aquí; el trabajo de baseline/benchmark/ranking es Stage 5.)*

### Etapa 5 — Model Lab  ← **ETAPA ACTUAL**
- **Propósito original:** ejecutar modelos baseline + candidatos, ranking, torneo, selección de campeón.
- **Bloques implementados:**
  - Generación de ventanas de backtesting (454) + inspección.
  - Construcción de feature dataset + inspección.
  - Model registry (14 modelos) + validación.
  - Controles y contrato de ejecución (triple-gate, manifest, audit append-only).
  - Implementación de 7 modelos baseline.
  - Smoke test, broader smoke test, pilot, **full baseline execution (3,178 jobs, 0 fallos)**.
  - Motor de métricas (wMAPE, MAPE, RMSE, SMAPE, abs bias) + sanity review.
  - Investigación de outliers (drilldown, root causes).
  - Política de ranking + dry run + **publicación de ranking baseline**.
  - Investigación de implementation issue.
  - **AUDIT #1** (pre-training, APPROVED WITH CHANGES) y **AUDIT #2** (challenger readiness, BLOCKED).
- **Bloques pendientes (rediseño de benchmark + challengers):**
  - Rediseño de semántica de benchmark (absolute score vs tournament rank).
  - Modelo de referencia Naive y Seasonal Naive.
  - MASE y RMSSE.
  - Política de forecast no-negativo.
  - Formalización de la jerarquía de agregación.
  - Framework de significancia estadística.
  - Contrato de no-tuning-leakage.
  - Confirmación de audit post-rediseño.
  - Onboarding y ejecución de challengers, torneo, selección de campeón.
- **Estado: Active / Needs Revision** (la capa de forecasting y métricas es válida; la capa de
  ranking/benchmark requiere rediseño antes de challengers).

### Etapa 6 — Validation Lab & Governance
- **Propósito original:** composite score, validación, gobierno, recomendaciones.
- **Bloques implementados:** ninguno (`outputs/governance/` vacío). Existen `scoring_definitions.yaml` y
  `scoring_weights.yaml` como diseño, pero el composite original es inválido según AUDIT #1.
- **Bloques pendientes:** todo. Parte del gobierno (significancia, no-tuning-leakage) se adelantó como
  prerequisito de Stage 5.
- **Estado: Pending.**

### Etapa 7 — UI/UX + LLM Insights
- **Propósito original:** UX ejecutivo + narrativas LLM.
- **Bloques implementados:** estructura Shiny modular base; `outputs/model_lab/dashboard/` vacío.
- **Bloques pendientes:** UX ejecutivo final, integración LLM (Ollama / Claude API).
- **Estado: Pending.**

### Etapa 8 — Codebase Improvement
- **Propósito original:** deliverable G3 de mejora de código.
- **Bloques implementados:** ninguno (`docs/codebase_improvement/` no presente).
- **Bloques pendientes:** todo.
- **Estado: Pending.**

### Etapa 9 — Cierre / Entrega
- **Bloques implementados:** ninguno.
- **Estado: Pending.**

---

## D. Posición Exacta Actual

> ### **Estamos actualmente en la Etapa 5 — Model Lab.**

**Por qué (evidencia):**

1. El trabajo activo es sobre **modelos baseline, ejecución baseline, semántica de benchmark, comparación de
   modelos, validación de ranking y readiness de challengers** — todos dominio explícito de Stage 5.
2. La fundación de la plataforma de evaluación (Stage 4) **ya está establecida** (`evaluation_dataset.csv`,
   inventario de fuentes, validación de métricas oficiales). **No debe devolverse trabajo a Stage 4.**
3. La evidencia de ejecución es de Stage 5: `full_baseline_20260611_103953` (454×7 = 3,178 jobs, 95,340
   filas), ranking publicado, y dos audits de Stage 5 (`stage_5_*`).
4. El bloqueo activo es de Stage 5: **el onboarding de challengers está BLOQUEADO** (AUDIT #2) hasta reparar
   la semántica de benchmark. Las carpetas `tournament/`, `dashboard/`, `governance/` están vacías,
   confirmando que el trabajo de challengers/torneo/gobierno **aún no comenzó**.

**Sub-posición precisa:** dentro de Stage 5, justo **después** de la publicación del ranking baseline y de
AUDIT #2, y **antes** del rediseño de semántica de benchmark. Es decir: en el *gate de remediación previo a
challengers*.

---

## E. Evolución Respecto del Blueprint Original

Cambios significativos introducidos durante la implementación (dirigidos por ejecución y audits):

### E.1 — Evolución de Stage 4
- Stage 4 dejó de ser solo "Baseline Replication" y se consolidó como **fundación de la Evaluation
  Platform**: descubrimiento de fuentes, dataset canónico de evaluación, validación de métricas oficiales
  contra la tabla `..._region_metrics`. La reproducción del baseline propiamente (modelos) migró a Stage 5.

### E.2 — Evolución de Stage 5
- Se expandió de "correr candidatos" a un **framework de ejecución baseline completo y auditable** con
  triple-gate (`training_enabled` + `dry_run` + `NotImplementedError`), manifest con cross-check de jobs, y
  audit logs **append-only** (`*_history.csv`) — corrigiendo el defecto de sobre-escritura detectado en
  AUDIT #1.
- Se introdujo una **política de forecasting multi-step explícita** (`multistep_forecasting.yaml`): nativo
  para estadísticos, recursivo para lineal/ML, directo multi-horizonte para DL, con reglas anti-leakage.

### E.3 — Framework de ejecución baseline
- 7 modelos baseline implementados y ejecutados en 454 ventanas × 39 entidades = 3,178 jobs, 95,340 filas,
  **0 fallos**. Pipeline verificado como leakage-clean por ambos audits.

### E.4 — Rediseño dirigido por audit
- **AUDIT #1 (pre-training):** APPROVED WITH CHANGES. Detectó composite inválido (suma de métricas de escala
  mezcladas), métricas indefinidas (stability/horizon), falta de manejo de actuals cero, y sobre-escritura
  de historia. La mayoría se remedió antes de la ejecución completa.
- **AUDIT #2 (challenger readiness):** **BLOCKED**. Confirmó que forecasting y métricas son válidos pero el
  **benchmark publicado no es válido como referencia fija**.

### E.5 — Rediseño de semántica de benchmark (nuevo, no estaba en el original)
- Se reconoce que **percentile_rank_within_entity_window es cohort-relativo**, no benchmark-relativo:
  agregar challengers re-escala todo y mueve los scores baseline.
- Contradicción rank-vs-accuracy confirmada con evidencia: **FixedGrowth_1_5 domina en TODAS las métricas
  crudas** (wMAPE 4.9% vs ETS 18.2%; RMSE 7,132 vs 19,593) pero se publica **3º**, mientras **ETS_Current**
  (peor MAPE de los 7) se publica **1º**.
- Surge la separación conceptual **Absolute Benchmark Score ≠ Relative Tournament Rank**.

### E.6 — Adiciones de gobierno (adelantadas desde Stage 6)
- **Framework de significancia estadística** (MCB / Nemenyi / Diebold-Mariano) — nuevo requisito.
- **Contrato de no-tuning-leakage / validación anidada** para challengers ML/DL — nuevo requisito crítico.
- **Política de forecast no-negativo** (floor `max(forecast, 0)`) — nuevo requisito (forecasts hasta
  −17.6M detectados).
- **Anclaje de skill absoluto:** Naive / Seasonal Naive + **MASE / RMSSE** — nuevo requisito.

### E.7 — Adiciones a la política de ranking
- Formalización explícita de la **jerarquía de agregación** (window → entity → cross-entity → global) ya
  existe en `ranking_policy.yaml`, pero debe re-derivarse sobre métricas escaladas (no solo percentiles).
- De-colinealización del composite (wMAPE + MAPE + SMAPE = 65% del peso, redundantes).
- Tratamiento de la familia correlacionada `FixedGrowth_*` (4 de 7 modelos) para evitar sesgo de
  composición de cohorte.

---

## F. Blueprint Actualizado de Stage 5 (orden de ejecución)

Leyenda de estado: ✅ Done · 🔄 Active/Next · ⏳ Pending · 🔁 Needs Revision

| # | Bloque | Estado |
|---|---|---|
| 5.1 | Generación de ventanas de backtesting (454) | ✅ |
| 5.2 | Construcción del feature dataset | ✅ |
| 5.3 | Model registry (14 modelos) + validación | ✅ |
| 5.4 | Controles de ejecución (triple-gate) | ✅ |
| 5.5 | Contrato de ejecución + manifest + audit append-only | ✅ |
| 5.6 | Implementación de modelos baseline (7) | ✅ |
| 5.7 | Smoke test | ✅ |
| 5.8 | Broader smoke test | ✅ |
| 5.9 | Pilot execution | ✅ |
| 5.10 | **Full baseline execution** (3,178 jobs, 95,340 filas, 0 fallos) | ✅ |
| 5.11 | Motor de métricas (wMAPE, MAPE, RMSE, SMAPE, abs bias) | ✅ |
| 5.12 | Metrics sanity review | ✅ |
| 5.13 | Outlier investigation (drilldown + root causes) | ✅ |
| 5.14 | Ranking policy (design_only) | ✅ |
| 5.15 | Ranking dry run | ✅ |
| 5.16 | **Baseline ranking publication** | ✅ |
| 5.17 | AUDIT #1 (pre-training) + AUDIT #2 (challenger readiness → BLOCKED) | ✅ |
| **5.18** | **Rediseño de semántica de benchmark** (Absolute Score vs Tournament Rank) | 🔄 **NEXT** |
| 5.19 | Modelo de referencia **Naive** | ⏳ |
| 5.20 | Modelo de referencia **Seasonal Naive** | ⏳ |
| 5.21 | Implementación de **MASE** | ⏳ |
| 5.22 | Implementación de **RMSSE** | ⏳ |
| 5.23 | **Política de forecast no-negativo** (floor uniforme + recálculo baseline) | ⏳ |
| 5.24 | **Formalización de jerarquía de agregación** (sobre métricas escaladas) | ⏳ |
| 5.25 | **Framework de significancia estadística** (MCB / Nemenyi / Diebold-Mariano) | ⏳ |
| 5.26 | **Contrato de no-tuning-leakage** (validación anidada + seeds/determinismo) | ⏳ |
| 5.27 | **Confirmación de audit** post-rediseño (AUDIT #3) | ⏳ |
| 5.28 | **Onboarding de challengers** (AutoARIMA, Theta, LightGBM, XGBoost, NBEATS, NHITS) | ⏳ |
| 5.29 | Ejecución de challengers (sandbox primero) | ⏳ |
| 5.30 | Torneo (cohorte conjunta baseline + challengers) | ⏳ |
| 5.31 | Selección de campeón (con bandas de significancia) | ⏳ |

> **Mapeo a la nomenclatura del plan en español (5.15A–G):**
> 5.15A Ranking Semantics Repair = **5.18** · 5.15B Absolute Benchmark Score = **5.18+5.21+5.22** ·
> 5.15C Non-Negative Forecast Policy = **5.23** · 5.15D Baseline Recalculation = **5.23/5.24** ·
> 5.15E Audit Confirmation = **5.27** · 5.15F Aggregation & Significance = **5.24+5.25** ·
> 5.15G No-Tuning-Leakage Contract = **5.26**.

### Decisiones de diseño obligatorias para 5.18–5.22 (recomendación del review)

- **No publicar `percentile_rank_within_entity_window` como score principal.** Sirve para *tournament rank*
  relativo, no como benchmark estable.
- **Adoptar UNA métrica primaria escalada** (RMSSE si importa el costo de errores grandes; MASE si importa
  el error absoluto) con **denominador naive fijo calculado sobre la porción de entrenamiento** de cada
  ventana (nunca sobre test → evita leakage).
- **NO usar el composite ponderado 40/25/20/15.** Pesos arbitrarios, reintroduce redundancia (wMAPE+SMAPE) y
  mezcla *bias* (dirección) dentro de un score de *accuracy* (magnitud). Publicar wMAPE / SMAPE / RMSE
  normalizado / abs bias / % que supera al naive como **panel de diagnóstico al lado**, no mezclados.
- Un modelo es "mejor" solo si gana en la métrica primaria **y** no empeora en los guardrails (bias, % > naive).

---

## G. Blueprint Completo Actualizado (9 Etapas)

| # | Etapa | Estado | Cambios incorporados |
|---|---|---|---|
| 1 | **Project Foundation** | ✅ Done | + Regla arquitectónica fijada: R/Shiny solo presentación, Python todo el procesamiento, `app.R` ≤ 30 líneas (actual: 7). |
| 2 | **Vision & Wireframe** | ✅ Done | Deuda menor: artefactos de wireframe no versionados en `docs/wireframes/`. |
| 3 | **Data Contract** | ✅ Done | Fuente real confirmada (`..._region` + `..._region_metrics`), ForecastVersion 2026-05-01 Enterprise. Documentar discrepancia 45→39 entidades / 16→7 modelos. |
| 4 | **Evaluation Platform** | ✅ Done | Reconceptualizada: fundación de evaluación (dataset canónico, validación de métricas oficiales). Reproducción de modelos baseline migró a Stage 5. |
| 5 | **Model Lab** | 🔄 **Active / Needs Revision** | Framework de ejecución baseline auditable; pipeline leakage-clean; **benchmark requiere rediseño** (5.18–5.27) antes de challengers (5.28–5.31). |
| 6 | **Validation Lab & Governance** | ⏳ Pending | Adelantos hacia Stage 5: significancia estadística, no-tuning-leakage, política no-negativo. Composite original declarado inválido por AUDIT #1; rediseñar. |
| 7 | **UI/UX + LLM Insights** | ⏳ Pending | Shiny modular base lista; dashboard de presentación y narrativas LLM pendientes. |
| 8 | **Codebase Improvement** | ⏳ Pending | Deliverable G3. Incluir suite de tests (hoy `tests/` vacío) y unificación de configs de scoring. |
| 9 | **Cierre / Entrega** | ⏳ Pending | Consolidación final. |

**Descubrimientos transversales incorporados al blueprint:**
- Triple-gate de ejecución y audit append-only (MLOps).
- Política multi-step + reglas anti-leakage (`multistep_forecasting.yaml`).
- Separación conceptual Absolute Benchmark Score vs Relative Tournament Rank.
- Anclaje de skill absoluto (Naive/Seasonal Naive + MASE/RMSSE).
- Significancia estadística y contrato no-tuning-leakage como gates pre-challenger.
- Deudas técnicas abiertas: `tests/` vacío, deriva entre `scoring_weights.yaml` y `ranking_metric_weights.csv`,
  fingerprinting de reproducibilidad ausente, forecasts negativos sin floor.

---

## H. Recomendación

### Próximo bloque inmediato: **5.18 — Rediseño de Semántica de Benchmark**

### Por qué es el siguiente bloque
1. Es el **único bloqueador formal** para challengers (AUDIT #2 = BLOCKED por C-1 cohort-relativo y C-2
   rank-contradice-accuracy).
2. Todos los bloques posteriores (5.19–5.31) **dependen** de la decisión semántica: MASE/RMSSE necesitan el
   denominador naive (5.19/5.20); la jerarquía de agregación (5.24) debe re-derivarse sobre métricas
   escaladas, no percentiles; el torneo (5.30) requiere un score estable.
3. La capa de forecasting y métricas **ya es válida** (verificado por ambos audits), así que el esfuerzo se
   concentra solo en semántica de ranking + floor de no-negatividad, no en re-arquitectura.

### Criterios de éxito antes de permitir challengers (gate 5.27)

Un AUDIT #3 debe confirmar TODO lo siguiente:

1. **Score absoluto estable (cohort-independiente):** el score baseline de cada modelo **no cambia** al
   agregar/quitar otros modelos. Verificación empírica: el MASE/RMSSE baseline debe ser idéntico antes y
   después de introducir challengers en sandbox.
2. **Métrica primaria escalada** (MASE o RMSSE) con denominador naive **calculado sobre entrenamiento**
   (con test unitario que lo demuestre, evitando leakage en el denominador).
3. **Naive y Seasonal Naive** implementados y ejecutados como referencias; ningún modelo se promueve si no
   supera al seasonal-naive.
4. **Contradicción rank-vs-accuracy reconciliada y documentada:** publicar, junto al rank, la vista de
   accuracy entity-balanced; explicar cualquier divergencia (análisis por segmento volumen/intermitencia).
5. **Floor de no-negatividad aplicado uniformemente a todos los modelos** y **métricas baseline recalculadas**
   tras el floor (5.23).
6. **Jerarquía de agregación documentada** (window→entity→global, central tendency y ponderación explícitas)
   sobre métricas escaladas (5.24).
7. **Significancia estadística publicada** con cada ranking (MCB/Nemenyi); rankings sin bandas de
   confianza no se publican (5.25).
8. **Contrato de no-tuning-leakage firmado** (validación anidada para LightGBM/XGBoost/NBEATS/NHITS) +
   política de seeds/determinismo, **antes** de cualquier ejecución de challenger (5.26).
9. **Deuda técnica mínima cerrada:** unificar las dos configs de scoring en una sola fuente de verdad y
   poblar `tests/` con tests de leakage, horizonte 30 días, no-future-actuals, monotonicidad de
   normalización y determinismo de ranking.

### Veredicto operativo
- **Publicación de benchmark para challengers: BLOQUEADA** hasta completar 5.18–5.27.
- **Ejecución de challengers en sandbox: PERMITIDA** una vez exista el score absoluto (5.18–5.22), porque es
  la forma más barata de validar empíricamente que el score es cohort-estable.
- **No** implementar nuevos modelos challenger productivamente hasta que AUDIT #3 confirme los 9 criterios.

---

*Documento generado en modo solo-revisión. No se modificó código, configs, datos, modelos ni rankings.
Toda afirmación está respaldada por artefactos del repositorio citados en el cuerpo.*
