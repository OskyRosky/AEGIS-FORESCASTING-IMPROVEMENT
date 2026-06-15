# Decisions Log - Benchmark Semantics

## Block 5.18 - Benchmark Semantics Redesign

Fecha: 2026-06-12

Estado: aprobado para diseno

### Decision 1: Metrica primaria

`MASE` queda aprobada como metrica primaria del benchmark.

Razon: `MASE` permite comparar accuracy contra un naive lag-1 absoluto por entidad y ventana, sin depender de la cohorte de modelos participantes.

### Decision 2: Denominador

El denominador de `MASE` debe ser el MAE de un naive lag-1 calculado solo sobre el training slice de cada ventana.

Restricciones:

- Nunca calcular el denominador sobre test.
- Nunca usar Drift como denominador.
- Aplicar floor / epsilon para denominadores cero o cercanos a cero.

### Decision 3: Agregacion

La agregacion primaria queda definida como:

- mediana de `MASE` por entidad;
- luego mediana entre entidades.

Razon: reduce sensibilidad a outliers y evita que entidades con mas ventanas o mayor escala dominen el benchmark.

### Decision 4: Guardrail

`RMSSE` queda definido como guardrail, no como metrica primaria.

Falla de guardrail: `RMSSE` materialmente peor que el runner-up por mas de `1.5x`.

### Decision 5: Diagnosticos

`wMAPE`, `SMAPE`, `abs_bias` y `pct_beating_naive` quedan autorizadas solo como diagnosticos.

No deben usarse para el benchmark score absoluto.

### Decision 6: Deprecacion de percentiles relativos

`percentile_rank_within_entity_window` queda deprecado como benchmark score porque al agregar challengers cambia la escala de los baselines existentes.

Puede permitirse mas adelante solo como parte de `Tournament Rank`, explicitamente limitado a comparacion dentro de cohorte.

### Decision 7: Separacion conceptual

`Absolute Benchmark Score` y `Tournament Rank` quedan separados.

El benchmark score debe ser estable ante nuevos challengers. El tournament rank puede ser relativo, pero debe declararse como ranking de cohorte y no reemplaza al score absoluto.

### Referencia normativa

Ver `docs/benchmark_semantics/benchmark_semantics_v1.md`.
