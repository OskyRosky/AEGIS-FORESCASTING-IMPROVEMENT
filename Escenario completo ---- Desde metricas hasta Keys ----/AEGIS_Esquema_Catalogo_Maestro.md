# AEGIS — Esquema de trabajo para el Catálogo Maestro

**Objetivo:** construir, contra datos reales de TesseractEarthDW, la tabla maestra
`Metric | DB Type | Granularity | Region | Key`, con `Source Table` como anexo final.

**Método:** árbol por niveles. Cada nivel se abre en dos etapas — primero el *universo*
(qué valores existen), después el *cruce* (qué combinaciones existen de verdad, y con
cuántas filas). El universo sin el cruce miente: dice que algo es posible cuando puede
que no exista ni una fila. El cruce es lo que cierra el nivel.

---

## Decisiones ya fijadas

| Decisión | Valor |
|---|---|
| Fuente de verdad | Tablas `forecast_*` / `substrateBE_*` en TesseractEarthDW |
| Scenario | **No es eje.** Se pliega dentro de Metric (`CPU` y `CPU Failover` = 2 métricas) |
| Fuera de alcance | Decommission Plan, Inorganic Demand |
| Ejes finales | Metric → DB Type → Granularity → Region → Key |
| Source Table | Se anexa al final, no guía la construcción |

---

## Decisión pendiente — se resuelve en E1

**¿Los conteos son sobre todas las filas o sobre una sola `ForecastVersion`?**

Importa mucho. Si contamos todo el histórico, una métrica con 20 versiones publicadas
se ve 20 veces más grande que una con 1, y el árbol queda deformado por frecuencia de
publicación en vez de por cobertura real.

Propuesta: reportar **dos conteos en cada etapa** — filas totales y filas de la última
`ForecastVersion` — y usar el segundo para decidir si una combinación existe o no.
Confirmar al ver el resultado de E1.

---

## Las etapas

### E0 — Inventario estructural ✅ entregado
`AEGIS_Catalog_Phase1_Discovery.sql`

**Pregunta:** ¿dónde vive cada eje — en una columna o en el nombre de la tabla?

**Por qué va primero:** hay dos poblaciones de tablas y se catalogan distinto.
Las que tienen columna `Metric` se recorren con `SELECT DISTINCT`. Las que no
(`forecast_substrateBE_iops`, `forecast_substrateBE_hdd_region`) llevan la métrica y a
veces la granularidad codificadas en el nombre, y hay que mapearlas a mano validando
caso por caso. Mezclarlas es donde se pierde la certeza.

**Cierra cuando:** tenemos Q1.1, Q1.3 y Q1.5 pegados, y toda tabla del inventario está
asignada a una de las dos poblaciones.

---

### E1 — Universo de Metrics
**Pregunta:** ¿cuáles son *todas* las métricas?

**Salida:** `Metric | RowsTotal | RowsLastVersion | #TablasDondeAparece`

**Fuentes que se unen:** el `DISTINCT` que genera Q1.4, más el mapeo manual de las
tablas sin columna Metric (E0/Q1.5).

**Cierra cuando:** la lista está cerrada y cada métrica del slicer del dashboard
(HDD-Basilisk, HDD-EDB, CPU, CPU Failover, IOPS, IOPS Failover, SSD-Phoenix, SSD-MCDB,
Memory, + lo que haya bajo el scroll) queda **confirmada o refutada** contra datos.
Las que aparezcan en la base y no en el slicer también se anotan: esas son las que te
faltaban en el análisis de forecast accuracy.

---

### E2 — Universo de DB Types
**Pregunta:** ¿qué DB Types existen en toda la base, sin importar la métrica?

**Salida:** `DBType | RowsTotal | #TablasDondeAparece`

**Ojo con la normalización:** el Excel usa `Phoenix`, `NonPhoenix`, `Total (phx y nonphx)`,
`MCDB(Total)`, `PHX(Organic)`. La base casi seguro usa otras etiquetas. En esta etapa
listamos **crudo**, sin limpiar. La normalización se decide en E3, con el cruce a la vista.

---

### E3 — Cruce Metric × DB Type
**Pregunta:** ¿qué DB Types tiene cada métrica, y hasta dónde llega cada una?

**Salida:** matriz `Metric × DBType` con conteo en cada celda; celda vacía = no existe.

**Lo que esperamos ver (a confirmar):** CPU se abre en Phoenix / NonPhoenix / Total.
IOPS no se abre (`N/A`). SSD se abre en MCDB / Phoenix. HDD probablemente se abre en
Basilisk / EDB — pero ojo: en el slicer eso vive *dentro del nombre de la métrica*
(`HDD - EDB`), no como DB Type separado. **Esa es la ambigüedad principal de E3** y hay
que resolverla explícitamente: o `HDD-EDB` es una métrica, o es Metric=HDD + DBType=EDB.
No pueden ser las dos cosas en la tabla maestra.

---

### E4 — Universo de Granularities
**Pregunta:** ¿cuántas granularidades hay realmente?

**Salida:** `Granularity | #Tablas | RowsTotal`

**Hipótesis:** solo dos, `Forest` y `Region`. Se valida buscando si existe algún nivel
adicional (DAG, Geo, SKU) — `SubstrateBE_Ssd_MCDB_ForecastForestSKU` sugiere que SKU
podría ser un tercer nivel, o un atributo dentro de Forest. Hay que verlo.

---

### E5 — Cruce Metric × DB Type × Granularity
**Pregunta:** para cada combinación viva de E3, ¿qué granularidades tiene?

**Salida:** el árbol con tres niveles y conteo por hoja.

**Cierra cuando:** cada rama tiene 1 o 2 granularidades y sabemos por qué. Si una rama
tiene solo Forest y otra solo Region, eso es un hallazgo, no un error — hay que anotarlo.

---

### E6 — Universo de Regions
**Pregunta:** ¿cuáles son todas las regiones, y cuántas hay?

**Salida:** `Region | RowsTotal | #Forests`

**Nota:** `Region` aparece dos veces en el modelo y hay que no confundirlas. Es un
**valor de granularidad** (una tabla es "de región") y a la vez un **valor de dimensión**
(APC, EUR, NAM...). En la tabla maestra la columna `Region` es la segunda.

---

### E7 — Cruce Metric × DB Type × Granularity × Region
**Pregunta:** ¿qué regiones existen en cada rama?

**Salida:** el árbol con cuatro niveles y conteo por hoja.

**Cierra cuando:** sabemos si todas las ramas cubren todas las regiones o si hay huecos.
Los huecos son señal — o de que la métrica no aplica ahí, o de que falta data.

---

### E8 — Keys
**Pregunta:** ¿qué es la Key en cada rama, y cuántas hay?

**El punto estructural de toda esta fase:** la Key **no significa lo mismo en las dos
granularidades**. En granularidad Forest, la Key es el forest (`APCPRD04`, como en tu
slicer). En granularidad Region, la Key es la región misma. Es decir, la Key es la hoja
del árbol — el identificador de la entidad más fina que existe en esa rama.

Esto probablemente explica el bug del slicer de Key en el dashboard: `Dim_Key_Values`
está mezclando keys de forest con keys de region, y por eso no filtra limpio contra
las fact tables.

**Salida:** `Metric | DBType | Granularity | Region | Key | Rows` — la tabla maestra.

**Cierra cuando:** el conteo total de keys por rama cuadra con el conteo de filas de E7.

---

### E9 — Anexo Source Table
Se le pega a la tabla maestra la tabla física de origen de cada rama. Va al final a
propósito: si lo hiciéramos antes, el nombre de la tabla nos estaría dictando el
catálogo en vez de al revés.

---

### E10 — Verificación cruzada
Tres contrastes contra la tabla maestra ya cerrada:

1. **vs. slicer del dashboard** — ¿alguna métrica en la base que no está en el slicer, o al revés?
2. **vs. Excel de Sue/Xinmei** — reconciliar el eje `Scenario` que ellos tienen separado y nosotros plegamos.
3. **vs. tu análisis previo de forecast accuracy** — cuáles de las 4 combinaciones que habías estipulado están en la maestra, y cuántas faltaban.

El entregable final es la tabla maestra + una lista explícita de discrepancias. Las
discrepancias no se esconden: son el valor de todo este ejercicio.

---

## Regla de operación

Ninguna etapa arranca sin el resultado de la anterior pegado y validado. Si un
resultado contradice una hipótesis, gana el resultado y se corrige el esquema — no se
fuerza el dato para que calce.

**Siguiente paso:** correr E0 (Q1.1, Q1.3, Q1.5) en SSMS.
