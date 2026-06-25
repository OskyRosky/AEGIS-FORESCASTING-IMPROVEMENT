# Stage 07 — V2 Model Lab 60-Day Backtest Extension

**Status: `60-day interval artifact created and ready for Oscar review`**
(Equivalentemente: el backtest a 60 días se completó con éxito Y el artifact de intervalos 80% 1–60 fue generado.)

Fecha de ejecución: 2026-06-25 · Active root: `V2` · Tarea Python Model Lab (NO Shiny).

---

## 1. Qué se hizo (y qué NO se tocó)

Se generó **evidencia real de residuos para horizontes 31–60** mediante un backtest nuevo,
aislado y gobernado, y luego se construyó un **artifact candidato de intervalos relativos 80% para
días 1–60**. No se extrapoló: cada banda de los días 31–60 se calibró con residuos observados de un
backtest walk-forward real a 60 días.

### Reglas respetadas (verificado)
- ✅ Shiny **no** tocado (ningún archivo bajo `shiny_app/` modificado; no se relanzó la app).
- ✅ Artifact de 30 días **intacto**: `forecasts.csv`, `forecasts_with_intervals_relative.csv`,
  `forecast_viewer_model_outputs.csv` sin modificar (verificado: existen, mismo tamaño).
- ✅ `forecasts.csv` **no** modificado.
- ✅ `forecasts_with_intervals_relative.csv` (30d) **no** modificado.
- ✅ Champion decision **sin cambios** (no se evaluó ni alteró selección).
- ✅ Viewer / Accuracy / TTL / Models / Governance / Reference **no** tocados.
- ✅ **95% NO** generado ni preparado (el artifact contiene solo nivel 80; columnas 95 ausentes).
- ✅ `config/backtesting.yaml` **no** sobrescrito (horizonte 60 parametrizado en el harness aislado).
- ✅ `forecast_value` **idéntico** al de producción (verificado: `FV_UNCHANGED = True`).

### Archivos nuevos (todos aislados)
| Tipo | Ruta |
|---|---|
| Harness backtest 60d | `python/model_lab/run_backtest_60d.py` |
| Builder intervalos 60d | `python/model_lab/build_interval_calibration_relative_60d.py` |
| Backtest crudo (residuos 1–60) | `outputs/model_lab/backtest_60d/forecast_viewer_model_outputs_60d.csv` |
| Ventanas / status / summary | `outputs/model_lab/backtest_60d/backtest_60d_*.csv` |
| **Artifact candidato** | `data/processed/forecasts_with_intervals_relative_60d.csv` |
| Diagnósticos | `outputs/shiny_mvp/7_V2_MODEL_LAB_60D_BACKTEST_EXTENSION/stage07_v2_model_lab_60d_*.csv` |

---

## 2. Backtest a 60 días — evidencia real

Walk-forward con ventanas **frescas no solapadas** (paso de 60 días hacia atrás desde el último
actual), de modo que cada ventana cae completamente dentro de los actuals observados → **todos los
horizontes 1–60 son evaluables, sin truncamiento**.

- Roster reproducido: **los mismos 13 modelos** del backtest gobernado de 30 días
  (7 baselines vía las clases del proyecto + 6 challengers portados fielmente de las
  implementaciones inline gobernadas: AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost,
  FastNeuralAR_MLP). `RANDOM_SEED = 42`.
- 39 series elegibles · hasta 12 ventanas/serie · **5,642 jobs modelo · 0 fallos** · ~10 min.
- **338,520 filas**, horizontes 1–60, `actual_value` no-nulo en **100%** (toda banda 31–60 tiene
  residuo real detrás).
- Magnitud de residuo relativo absoluto (mediana) **crece de forma realista** con el horizonte:

| bucket | 1–7 | 8–14 | 15–30 | 31–45 | 46–60 |
|---|---|---|---|---|---|
| mediana \|rel. resid.\| | 0.4% | 1.0% | 2.0% | 3.2% | 4.1% |

Sin explosión ni valores degenerados → evidencia apta para calibrar bandas más anchas a horizontes
largos.

---

## 3. Artifact de intervalos 80% (1–60)

- `data/processed/forecasts_with_intervals_relative_60d.csv` — **65,095 filas in = out**,
  columnas originales preservadas, `forecast_value` sin cambios.
- Método idéntico al gobernado de 30 días: cuantiles empíricos de residuo **relativo** (q10/q90)
  por `entity_key × horizon_bucket`, con winsorización (clip_low = −0.95, clip_high = p99) y
  exclusión de denominadores near-zero. Buckets extendidos: `1_7, 8_14, 15_30, **31_45, 46_60**`.
- `interval_available = TRUE` solo en días **1–60 con calibración válida**;
  `FALSE` después con razón **`outside_calibrated_horizon_1_60`** (62,395 filas).
- **2,700 bandas** disponibles = **45 series × 60 días** (todas las series de producción cubiertas
  para 1–60). Monotonicidad OK, **0 lowers negativos**, 0 clamps.

### Cobertura out-of-sample 80% (holdout temporal: 3 cutoffs más recientes)
| scope | 1–7 | 8–14 | 15–30 | 31–45 | 46–60 | **global** |
|---|---|---|---|---|---|---|
| cobertura 80% | 0.768 | 0.727 | 0.737 | 0.730 | **0.712** | **0.731** |

**Lectura honesta:** la cobertura empírica (~73%) queda **por debajo del 80% nominal** → las bandas
están algo **subdispersas** (un poco angostas). Pero el hallazgo central para esta decisión es que
**la cobertura se mantiene estable al extender a 31–60**: 46–60 (71.2%) está apenas ~5.6 pts por
debajo de 1–7 (76.8%). La extensión a 60 días **no degrada materialmente** la calidad de cobertura
respecto de los horizontes cortos; el déficit ~7 pts es una propiedad pre-existente del método, no un
artefacto de los días largos.

### Ancho relativo de banda 80% — crece de forma sensata
| bucket | 1–7 | 8–14 | 15–30 | 31–45 | 46–60 |
|---|---|---|---|---|---|
| mediana ancho/forecast | 0.073 | 0.137 | 0.204 | 0.273 | 0.395 |

Mediana global 0.204; p95 = 3.32 (colas dominadas por pocas series con escala muy volátil).

### Outliers / fallbacks
- **Fallback de recurso (HDD):** exactamente las **6 series actuals-only** sin backtest propio
  (AUT/CHL/DNK/EUR/IDN/MYS-Go Local), 60 filas c/u — usan el grano de recurso, no se inventan bandas.
  Las 39 series restantes usan su propio grano `entity_key × bucket` (2,340 filas).
- **Anomalías de escala punto-vs-backtest:** `APC-Dedicated`, `POL-Go Local` (marcadas en
  `forecast_point_scale_anomaly`; sus bandas existen pero conviene revisarlas).
- Bandas anchas (>2× forecast): 235 filas (8.7% de las disponibles), concentradas en horizontes
  largos de series volátiles — esperable, no inventado.

---

## 4. Recomendación para revisión de Oscar

1. El backtest 60d y el artifact 80% 1–60 son **reproducibles y aislados**; ningún artefacto de
   producción fue alterado.
2. La cobertura 80% **se mantiene razonable y estable** hasta el día 60, con la salvedad de un
   **sub-cobertura sistémico (~73% vs 80%)** que ya existía en horizontes cortos — decisión de Oscar
   si se acepta tal cual o se ajusta (p.ej. ampliar a q05/q95 o recalibrar) **antes** de cualquier
   uso en Shiny.
3. Próximo paso sugerido (NO ejecutado, requiere autorización explícita): wiring del artifact 60d en
   Shiny. **No se realizó ningún cambio en Shiny en esta etapa.**

---

**Final status: `60-day interval artifact created and ready for Oscar review`**
