# Semantica de Benchmark v1

## Proposito

Este documento fija la semantica de benchmark para TESSERACT v2 / AEGIS Forecast Improvement Platform despues de AUDIT #2. El objetivo es separar el score absoluto de benchmark de cualquier ranking relativo de torneo, para que la incorporacion de challengers no reescale ni reinterprete los resultados ya publicados de los baselines.

## Problema corregido

La metrica `percentile_rank_within_entity_window` queda deprecada como benchmark score porque es relativa a la cohorte evaluada. Si se agregan challengers, los percentiles de todos los modelos existentes pueden cambiar aunque sus errores crudos no hayan cambiado.

AUDIT #2 tambien confirmo una contradiccion material: `FixedGrowth_1_5` dominaba las metricas crudas de accuracy, pero no quedaba primero bajo el score publicado. Por tanto, el benchmark debe usar una metrica absoluta de accuracy como criterio primario.

## Decision bloqueada

- Metrica primaria de benchmark: `MASE`.
- Metrica guardrail: `RMSSE`.
- Metricas diagnosticas: `wMAPE`, `SMAPE`, `abs_bias`, `pct_beating_naive`.
- `Absolute Benchmark Score` y `Tournament Rank` son conceptos separados.

## Definicion de MASE

`MASE` se define como el error absoluto medio del modelo dividido por el MAE de un naive lag-1 calculado exclusivamente sobre el training slice de la ventana evaluada.

Reglas obligatorias:

- El denominador se calcula por entidad y ventana usando solo la porcion de entrenamiento.
- El denominador nunca se calcula sobre test.
- El denominador oficial es el MAE in-sample de un naive lag-1 sobre la serie de entrenamiento: `mean(abs(y_train[t] - y_train[t-1]))`.
- Los forecasts lag-1 naive generados en Block 5.19 son benchmark/reference forecasts, pero no son el denominador oficial de `MASE`.
- El modelo Drift puede competir como benchmark contestant, pero nunca puede ser el denominador.
- El denominador corresponde al naive lag-1, no a un modelo entrenado ni a un ranking previo.
- Se aplica un floor / epsilon al denominador para evitar divisiones por cero o denominadores cercanos a cero.
- Un denominador flooreado debe quedar registrado como condicion diagnostica cuando se implemente el calculo.

## Definicion de RMSSE Guardrail

`RMSSE` usa el mismo principio de aislamiento temporal que `MASE`. Su denominador oficial es el MSE in-sample de un naive lag-1 sobre el training slice:

`mean((y_train[t] - y_train[t-1])^2)`

Reglas obligatorias:

- El denominador de `RMSSE` se calcula por entidad y ventana usando solo actuals con fecha `<= train_end_date`.
- Nunca se usan actuals del test horizon para el denominador.
- Nunca se usan forecasts naive de Block 5.19, seasonal naive, Drift ni tablas de metricas previas como denominador.
- Se aplica floor / epsilon al MSE del denominador cuando sea cero o cercano a cero.

## Agregacion del benchmark

La agregacion primaria de `MASE` es robusta y equitativa:

1. Calcular `MASE` por entidad y ventana.
2. Agregar por entidad usando la mediana de sus ventanas.
3. Agregar globalmente usando la mediana entre entidades.

Esta regla evita que una entidad de escala alta o una ventana extrema domine el score global.

## Guardrail RMSSE

`RMSSE` es guardrail solamente. No reemplaza a `MASE` como metrica primaria ni participa en el score absoluto salvo para detectar degradaciones severas.

Regla de falla:

- Un modelo falla el guardrail si su `RMSSE` es materialmente peor que el runner-up por mas de `1.5x`.

La implementacion posterior debe definir de forma explicita el conjunto elegible para runner-up y registrar cualquier falla como condicion de seleccion, no como recalculo de `MASE`.

## Diagnosticos

Las siguientes metricas quedan autorizadas solo como diagnosticos:

- `wMAPE`
- `SMAPE`
- `abs_bias`
- `pct_beating_naive`

Estas metricas pueden explicar comportamiento, sesgo, sensibilidad a ceros o comparacion contra naive, pero no deben convertirse en benchmark score primario ni en normalizacion de ranking absoluto.

## Separacion entre benchmark score y torneo

`Absolute Benchmark Score`:

- Debe ser estable ante la incorporacion de nuevos challengers.
- Debe basarse en `MASE` absoluto con denominador naive lag-1 fijo por entidad/ventana.
- Debe poder compararse entre ejecuciones siempre que el dataset, ventanas y definicion de denominador sean equivalentes.

`Tournament Rank`:

- Puede existir en una fase posterior.
- Solo es valido para comparacion dentro de una cohorte especifica.
- No debe publicarse como sustituto del benchmark score absoluto.
- Si usa percentiles u ordenamientos relativos, debe declararse como ranking de cohorte.

## Deprecaciones

- `percentile_rank_within_entity_window` queda deprecado como benchmark score.
- Los rankings basados en normalizacion relativa pueden mantenerse solo como `Tournament Rank` posterior.
- Las metricas diagnosticas no deben usarse como criterio primario de seleccion.

## Alcance de este bloque

Block 5.18 es solo diseno. No implementa calculos de `MASE` o `RMSSE`, no recalcula metricas, no modifica forecasts, no ejecuta modelos y no genera rankings ni salidas de torneo.
