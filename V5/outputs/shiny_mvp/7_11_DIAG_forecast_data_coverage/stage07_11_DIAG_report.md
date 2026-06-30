# Stage 07 · Block 7.11-DIAG — Forecast Data Coverage & Multi-Model Availability

**Type:** READ-ONLY diagnosis. No dashboard, data, model, or governance file was modified.
**Scope root:** `V1` only.
**Question driving this block:** Does the project contain the multi-model forecast data needed
so the Forecast Viewer can let Oscar compare *several* models (baseline / statistical / ML /
deep learning) for the *same* series?

---

## 1. Executive verdict

**PARTIALLY YES.** The multi-model forecast data **does exist**, but **not in the artifact the
dashboard currently reads**.

- The dashboard reads `data/processed/forecasts.csv`, which is a **FINAL / production forecast**
  artifact: **45 entities, exactly 1 model per entity** (16 distinct models globally). This is
  *by design* a single-model deliverable — which is why the Viewer shows only one model per series.
- The **multi-model forecasts live in the Model Lab backtest artifacts**:
  - `outputs/model_lab/full_baseline/full_baseline_forecasts.csv` → **7 baseline models** × 39 entities.
  - `outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv` → **6 challenger models**
    × 39 entities, **with actuals + forecast + error** already joined.
- Combined, **39 of 45 entities have 13 models each**, spanning 4 model families:
  `statistical`, `machine_learning`, `growth_baseline`, `lightweight_neural`.
- **Deep learning (NBEATS / NHITS) is NOT available** — both were deferred in the model universe
  (`deferred_runtime_impractical` / `deferred_dependency_blocked`) and never produced forecasts.

So Oscar's mental model (compare many models per series) is **valid and achievable for 39/45
entities**, but it must be powered by the **Model Lab backtest artifacts**, not by the final
single-model `forecasts.csv`. The comparison is over a **historical backtest window
(2025-05-03 → 2026-04-27)**, not the forward production horizon (2026-04-28 onward).

---

## 2. Forecast artifact inventory (key rows)

| Artifact | Rows | Entity col | Model col | Forecast col | Entities | Models | Multi-model/entity |
|---|---|---|---|---|---|---|---|
| `data/processed/forecasts.csv` | 65 095 | entity_key | model_version | forecast_value | 45 | 16 | **No (1/entity)** |
| `data/processed/forecast_comparison.csv` | **0** | — | — | — | 0 | 0 | Empty / unusable |
| `data/processed/actuals.csv` | 84 537 | entity_key | — | — | 45 | — | n/a |
| `outputs/model_lab/full_baseline/full_baseline_forecasts.csv` | 95 340 | entity_key | model_name | forecast_value | 39 | **7** | **Yes** |
| `outputs/model_lab/challenger_metrics/challenger_actual_forecast_join.csv` | 81 720 | entity_key | model_name | forecast_value (+actual) | 39 | **6** | **Yes** |
| `outputs/model_lab/challenger_metrics/challenger_scoring_forecasts.csv` | 81 720 | entity_key | model_name | forecast_value | 39 | 6 | Yes |
| `outputs/model_lab/challenger_official_execution/challenger_official_forecasts.csv` | 81 720 | entity_key | model_name | forecast_value | 39 | 6 | Yes |
| `outputs/model_lab/baseline_pilot/baseline_pilot_forecasts.csv` | 2 100 | entity_key | model_name | forecast_value | 10 | 7 | Yes (pilot) |
| `outputs/model_lab/challenger_sandbox/challenger_sandbox_forecasts.csv` | 900 | entity_key | model_name | forecast_value | 5 | 6 | Yes (sandbox) |

Full inventory: `stage07_11_DIAG_forecast_artifact_inventory.csv`.
Shape/gap matrix: `stage07_11_DIAG_data_gap_matrix.csv`.

---

## 3. `forecasts.csv` (current dashboard source)

- 65 095 rows · 45 entities · **1 `model_version` per entity** · 16 distinct models globally.
- This is the **final forward forecast** (one chosen model per series). It is **not** a comparison
  artifact, so the Viewer correctly shows a single line per series.

## 4. `forecast_comparison.csv`

- **Empty (0 rows).** It was likely intended as the consolidated comparison source but was never
  populated. **Not usable** as-is.

## 5. Model universe (`model_lab_final_model_universe.csv`)

15 models defined, by origin/family:

- **baseline:** ARIMA_Fixed (statistical), ETS_Current (statistical), LinearRegression (ML),
  FixedGrowth_1_5 / _3 / _4 / _6 (growth_baseline).
- **challenger:** AutoARIMA (statistical), Theta (statistical), **ETS Explicit (statistical — selected_champion)**,
  LightGBM (ML), XGBoost (ML), FastNeuralAR_MLP (lightweight_neural),
  **NBEATS (deep_learning — deferred)**, **NHITS (deep_learning — deferred)**.

---

## 6. Multi-model coverage (consolidated baseline + challenger)

- **39 of 45 entities** have **13 models each** (7 baseline + 6 challenger).
- Families present per entity: `statistical`, `machine_learning`, `growth_baseline`,
  `lightweight_neural`. **`deep_learning` absent everywhere.**
- Backtest window: **2025-05-03 → 2026-04-27**, 360 points per model per entity.
- Challenger forecasts carry **actuals** (so error overlays are possible); baseline forecasts do not
  carry actuals in their file but can be joined to `actuals.csv` by `entity_key` + date.
- **6 entities** (45 − 39) appear only in the final `forecasts.csv` and are **not** in the Model Lab
  multi-model artifacts.

Per-entity detail: `stage07_11_DIAG_models_per_entity_multimodel.csv`.
Representative series (APC-Dedicated, APC-MSIT, APC-Multitenant, AUS-Go Local, BRA-Go Local):
`stage07_11_DIAG_representative_series_coverage.csv` — each shows the full 13-model lineup.

---

## 7. Interpretation — artifact limitation vs conceptual issue

Oscar's concept is **correct**: a multi-model Forecast Viewer is exactly what the Model Lab data
supports. The current blank/single-model experience is an **artifact-binding limitation**, not a
conceptual error:

- The Viewer is pointed at the **final single-model** artifact instead of the **multi-model backtest**
  artifacts.
- Two honest options exist (see recommendation), and both are real and buildable with existing data
  for 39/45 entities and 4 of 5 model families.

---

## 8. Important caveats (must be shown honestly in any future Viewer)

1. **Backtest, not future.** Multi-model data is a historical evaluation window
   (2025-05 → 2026-04), not the forward production horizon. Comparing models = comparing how each
   model performed against known actuals.
2. **39/45 entities only.** Six entities have no multi-model data.
3. **No deep learning.** NBEATS/NHITS were deferred; the Viewer must not imply they exist.
4. **Two distinct artifacts.** Baseline (forecast-only) and challenger (forecast+actual) must be
   unioned and labeled by `model_origin` / `model_family`.

---

## 9. Files produced by this diagnostic (all under `outputs/shiny_mvp/7_11_DIAG_forecast_data_coverage/`)

- `stage07_11_DIAG_inspect.R` (read-only inspector)
- `stage07_11_DIAG_consolidate.R` (read-only consolidator)
- `stage07_11_DIAG_forecast_artifact_inventory.csv`
- `stage07_11_DIAG_forecast_schema_summary.csv`
- `stage07_11_DIAG_data_gap_matrix.csv`
- `stage07_11_DIAG_models_per_entity_forecasts.csv`
- `stage07_11_DIAG_models_per_entity_forecast_comparison.csv`
- `stage07_11_DIAG_models_per_entity_multimodel.csv`
- `stage07_11_DIAG_representative_series_coverage.csv`
- `stage07_11_DIAG_required_forecast_viewer_schema.csv`
- `stage07_11_DIAG_artifact_search_results.csv`
- `stage07_11_DIAG_recommendation.md`
- `stage07_11_DIAG_report.md` (this file)
- `stage07_11_DIAG_validation.csv`
