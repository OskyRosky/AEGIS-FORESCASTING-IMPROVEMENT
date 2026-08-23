# V6.24-P0 — Combination Inventory / Artifact Reality Check

`V6_24_P0_COMBINATION_INVENTORY_COMPLETED`

Read-only. No model ran, no SQL was executed, no forecast was generated, nothing
was fabricated. Every number below was measured from a file in `V6/`.

## The honest answer, in one table

| Métrica | Combinaciones | >50 actuals | 15 modelos | Forecast | **Completas** |
|---|---:|---:|---:|---:|---:|
| **HDD** | 596 | **596** | **596** | 596 | **596** |
| **SSD** | 300 | **0** | **0** | 300 | **0** |
| **CPU** | **0** | 0 | 0 | 0 | **0** |
| **IOPS** | **0** | 0 | 0 | 0 | **0** |
| **Total** | 896 | 596 | 596 | 896 | **596** |

**Hoy tenemos 596 combinaciones completas, y todas son HDD.**

CPU e IOPS no tienen ni una sola combinación en el repositorio. No es que estén
incompletas: **no existen como filas de datos**. Aparecen solo como rutas
informativas marcadas `BACKEND_GAP`.

## Por ruta

| Métrica | Ruta | Granularidad | Total | >50 actuals | 15 modelos | Forecast | Completas |
|---|---|---|---:|---:|---:|---:|---:|
| HDD | Basilisk | Forest | 155 | 155 | 155 | 155 | **155** |
| HDD | Basilisk | Region | 47 | 47 | 47 | 47 | **47** |
| HDD | EDB Consumer | Forest | 152 | 152 | 152 | 152 | **152** |
| HDD | EDB Consumer | Region | 45 | 45 | 45 | 45 | **45** |
| HDD | EDB Enterprise | Forest | 152 | 152 | 152 | 152 | **152** |
| HDD | EDB Enterprise | Region | 45 | 45 | 45 | 45 | **45** |
| SSD | Phoenix Low Volume No Efficiency | Forest | 148 | 0 | 0 | 148 | 0 |
| SSD | Phoenix Low Volume With Efficiency | Forest | 152 | 0 | 0 | 152 | 0 |

## El umbral de 50 no elimina nada

Rango medido de observaciones reales: **75 a 360**.

El mínimo es 75 (Basilisk). Con el umbral en 50, **las 596 pasan**. Con 150
habrían caído las 202 de Basilisk. Bajar a 50 fue la decisión correcta.

## Por qué SSD no puede ir al Viewer

El archivo `r6_phase1_forecast_ssd_phoenix.csv` (96.7 MiB) tiene estas columnas:

```
metric, scenario_ui_label, key, forecast_date, forecast_value,
forecast_version, value_type, source_table, extraction_run_id
```

No hay columna de actuals. Nunca se extrajo. La extracción R6 sacó de SQL:

| Archivo | Contenido |
|---|---|
| `r6_phase1_viewer_hdd.csv` | HDD con `series_type = actual` ✓ |
| `r6_phase1_forecast_hdd.csv` | HDD forecast ✓ |
| `r6_phase1_forecast_ssd_phoenix.csv` | SSD **solo forecast** |
| *(no existe)* | SSD viewer/actuals |
| *(no existe)* | CPU |
| *(no existe)* | IOPS |

## Estado real de Shiny

| Página | Expone | Completas | Incompletas expuestas | Resultado |
|---|---:|---:|---:|---|
| Viewer | 596 | 596 | 0 | Alineado |
| Forecast | 894 | 596 | **298** | **No alineado** |

**La paridad Viewer = Forecast no se cumple.** Forecast muestra 298 casos SSD
que el Viewer no puede mostrar. Lo reporto; no lo corrijo en esta etapa.

Selector de métricas hoy: el Viewer solo ofrece HDD; Forecast ofrece HDD, SSD,
CPU, IOPS y Memory (las últimas cuatro terminan en estado de backend gap).

## Qué se necesita de SQL/Tesseract

Las tablas candidatas están documentadas en el propio repositorio
(`v6_0f_r1_tesseract_metric_inventory/tesseract_related_tables_search.csv`).
No las inventé:

| Métrica | Falta | Tablas candidatas | Hallazgo |
|---|---|---|---|
| **SSD-Phoenix** | Actuals + 15 modelos | `forecast_substrateBE_SSD_Phoenix_Organic`, `DemandPlan_SubstrateBE_SSDPhoenixDB_Demand(_Region)` | El forecast ya salió de `forecast_substrateBE_SSD_TotalForecast` |
| **CPU** | Todo | `forecast_substrateBE_cpu`, `..._region`, **`forecast_substrateBE_cpu_actual_region`** | El nombre `_actual_region` sugiere que los actuals **sí existen en SQL** |
| **IOPS** | Todo | `forecast_substrateBE_iops`, **`forecast_substrateBE_iops_actual_region`** | Mismo patrón `_actual_region` |

Ese patrón `_actual_region` en CPU e IOPS es el hallazgo más útil de esta etapa:
sugiere que la data existe en SQL y solo falta extraerla. **No lo puedo afirmar
sin una consulta de metadatos read-only**, que no ejecuté.

Lo desconocido y honesto: para CPU e IOPS no sé aún cuál es la columna de fecha,
la de valor ni la de key. Sus ejes no son los de HDD.

## Cadena de dependencias

```
actuals (>50)  →  15 modelos  →  forecast  →  Viewer + Forecast
```

Sin el primer eslabón no hay nada. Por eso SSD, CPU e IOPS están bloqueados en
el mismo punto: **falta la extracción de actuals**.

## Lo que esto significa para la cohorte de 130-150

- **HDD**: 596 disponibles. Sobran; habría que elegir un subset representativo.
- **SSD**: 0 disponibles. Requiere extracción.
- **CPU**: 0 disponibles. Requiere extracción.
- **IOPS**: 0 disponibles. Requiere extracción.

Una cohorte mixta de las cuatro métricas **no se puede construir hoy con lo
local**. Requiere autorización para leer SQL.

## Siguiente paso propuesto

Una **consulta read-only de metadatos** sobre 6 tablas candidatas, para
confirmar: si existe columna de actuals, su rango de fechas, el conteo de keys y
cuántas combinaciones superarían las 50 observaciones.

Eso convierte el "UNKNOWN" de este inventario en un número real, sin extraer
datos masivos y sin comprometer nada.

## Archivos generados

`v6_24_p0_artifact_inventory.csv` · `v6_24_p0_combination_inventory_by_case.csv`
(896 filas) · `v6_24_p0_summary_by_metric.csv` · `v6_24_p0_summary_by_route.csv`
· `v6_24_p0_summary_by_granularity.csv` · `v6_24_p0_product_complete_candidates.csv`
(596 filas) · `v6_24_p0_incomplete_combinations.csv` (300 filas) ·
`v6_24_p0_shiny_alignment_report.csv` · `v6_24_p0_sql_tesseract_gap_report.csv` ·
`v6_24_p0_validation.csv`
