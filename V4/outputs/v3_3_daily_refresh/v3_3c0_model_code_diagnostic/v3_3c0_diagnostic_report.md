# V3.3C-0 — Model Training Code Diagnostic

**Status:** `V3_3C0_MODEL_CODE_DIAGNOSTIC_COMPLETED`
**Mode:** READ-ONLY diagnosis. No code modified, no models run, no backtests, no data/processed touched, no champion/forecast/interval change, no scheduler, V1/V2 untouched.
**Scope authorized:** *"Aquí solo queremos que nos diga dónde está el problema y qué código hay que tocar."*

---

## 1. Executive summary

The canonical **15-model universe** is **not** produced by a single training runner. It is an **aggregation of two live runners plus one frozen study**:

- **7 growth-baseline/baseline models** → trained by `run_full_baseline_execution.py` (clean, no prohibited models).
- **5 statistical/ML challengers** → trained by `run_challenger_official_execution.py` — **but this runner also fits `NBEATS`** (and wires `NHITS` as deferred). **This is the exact bug that caused NBEATS to run during V3.3B.**
- **3 Deep Learning models** (FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN) → **have no live training code**. They exist only as **frozen outputs of the closed V3.2B/D/E candidate study** (`outputs/v3_2b_model_candidates/candidate_outputs/full_candidate_outputs.csv`). `build_canonical_universe.R` merely aggregates them.

**Therefore: a "clean 15-model daily runner" does not exist, and only 12 of the 15 models are live-trainable with current code.** The other 3 (DL) must be reused as frozen evidence.

The single line to fix is `APPROVED_MODELS` in [python/model_lab/run_challenger_official_execution.py](python/model_lab/run_challenger_official_execution.py#L49) (remove `"NBEATS"`) plus the `DEFERRED_MODEL = "NHITS"` wiring on [line 51](python/model_lab/run_challenger_official_execution.py#L51).

---

## 2. Why V3.3B became partial

V3.3B ran a legacy probe (S03b) that invoked `run_challenger_official_execution.py`. Its `APPROVED_MODELS` list includes `"NBEATS"` — a heavy torch/CPU deep-learning model. NBEATS did not complete within the 17-minute probe and was stopped at a checkpoint. NBEATS, NHITS and the original FastNeuralAR_MLP are **out of daily scope**, so the stage was marked `STOPPED_NOT_IN_SCOPE` and V3.3B closed as **partial**.

Root cause = the official challenger runner has a prohibited model hard-coded into its execution list.

---

## 3. Current model universe expected (canonical 15)

| Family | Models | Live-trainable? | Source |
|---|---|---|---|
| Growth baseline (4) | FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6 | YES | `run_full_baseline_execution.py` |
| Statistical (5) | ARIMA_Fixed, AutoARIMA, ETS Explicit (**champion**), ETS_Current, Theta | YES | baseline + challenger runners |
| Machine learning (3) | LightGBM, LinearRegression, XGBoost | YES | baseline + challenger runners |
| Deep Learning (3) | FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN | **NO (frozen)** | V3.2B candidate study (frozen CSV) |

Champion = **ETS Explicit**, MASE 6.901144 (unchanged).
**Prohibited from daily runner:** NBEATS, NHITS, FastNeuralAR_MLP (original), legacy Evaluation Challengers, anything outside the 15.

---

## 4. Code locations inspected

- `python/model_lab/` (runners, planners, builders, `models/` subdir)
- `python/model_lab/models/` — model classes + `model_registry.py` + `validate_model_registry.py`
- `python/governance/` — build_governance_6_0/6_1/6_2/6_4/6_5
- `config/` — challenger_registry.yaml, multistep_forecasting.yaml, tournament.yaml
- `outputs/v3_2h_model_consistency_fix/build_canonical_universe.R`
- `outputs/v3_2b_model_candidates/` — candidate_registry.csv, candidate_recommendations.csv, candidate_outputs
- `shiny_app/ui/tabs.R` — DL challenger display references
- `outputs/v3_2g_viewer_challenger_integration/` — viewer handoff narrative

---

## 5. Model-to-code map summary

See [model_to_code_map.csv](outputs/v3_3_daily_refresh/v3_3c0_model_code_diagnostic/model_to_code_map.csv). Key facts:

- The 12 governed models each map to a class in `python/model_lab/models/*.py` and are registered in `model_registry.py` (14 classes total, incl. NBEATS/NHITS).
- The 3 DL active models map to **no Python class** — only to rows in the frozen candidate CSV.
- `model_registry.py` does **not** contain FNAR-V2/NLIN-DLIN_FIXED/SMLP-TCN.

## 6. Script-to-model map summary

See [script_to_models_map.csv](outputs/v3_3_daily_refresh/v3_3c0_model_code_diagnostic/script_to_models_map.csv).

- `run_full_baseline_execution.py` — **clean**, daily-safe (7 baseline models).
- `run_challenger_official_execution.py` — daily-capable **only if** NBEATS/NHITS removed.
- `training_orchestrator.py`, `build_challenger_execution_plan.py`, `build_challenger_onboarding.py` — planners/metadata (no execution).
- `build_tournament_engine.py`, `build_champion_decision.py`, `build_forecast_viewer_handoff.py`, `build_canonical_universe.R` — aggregators/decision (no training).

## 7. Prohibited model findings

See [prohibited_model_references.csv](outputs/v3_3_daily_refresh/v3_3c0_model_code_diagnostic/prohibited_model_references.csv). Classified by `is_execution_path`:

- **EXECUTION PATH (must fix):** `run_challenger_official_execution.py` APPROVED_MODELS NBEATS (L49), DEFERRED NHITS (L51), dependency map (L140); `model_registry.py` registration of NBEATS/NHITS (L18-19, L67-68).
- **PLANNING/METADATA (filter for daily):** training_orchestrator.py, build_challenger_execution_plan.py (L53-54), config/multistep_forecasting.yaml (L30-31), config/challenger_registry.yaml (CH-06/CH-07, already `official_execution_ready=false`).
- **GOVERNANCE/DASHBOARD (KEEP as historical):** build_governance_6_4.py, build_governance_6_5.py (deferred-status records), docs methodology.
- **RETIRED (already enforced):** FastNeuralAR_MLP — filtered out by `build_canonical_universe.R`.

---

## 8. Current runner gap

There is no orchestrator that:
1. runs the baseline runner,
2. runs the challenger runner **with a prohibited-model-free list**,
3. reuses the 3 frozen DL artifacts,
4. re-aggregates the canonical universe,
5. and **fails fast** if any prohibited model appears.

---

## 9. Which code MUST be corrected in V3.3C

1. **[python/model_lab/run_challenger_official_execution.py](python/model_lab/run_challenger_official_execution.py#L43)** — remove `"NBEATS"` from `APPROVED_MODELS` and remove the `DEFERRED_MODEL = "NHITS"` wiring (and the NBEATS dependency entry at L140). *(Recommend a parameterized daily variant rather than editing the V3.2 close-out script in place.)*
2. **New V3.3C daily orchestrator** — single entrypoint driving baseline + clean challenger + DL reuse + canonical aggregation, with a hard guard that **raises if NBEATS/NHITS/FastNeuralAR appears** in the resolved model list.
3. **Daily model-list filter** at the planner level (`training_orchestrator.py` / `build_challenger_execution_plan.py`) so daily plans never enumerate prohibited models.

## 10. Which references can remain historical/legacy

- `config/challenger_registry.yaml` CH-06/CH-07 (already `official_execution_ready=false`).
- `python/governance/build_governance_6_4.py` / `build_governance_6_5.py` deferred-status records.
- `python/model_lab/models/nbeats_model.py` / `nhits_model.py` class files (keep — V3 close-out history; just don't request them).
- Docs/methodology + legacy pilot CSV references to FastNeuralAR_MLP.
- `build_canonical_universe.R` FastNeuralAR_MLP retirement filter (keep — it enforces correct exclusion).

## 11. Which references must be removed from ACTIVE EXECUTION

- `NBEATS` from `APPROVED_MODELS` (execution).
- `NHITS` `DEFERRED_MODEL` wiring (execution).
- NBEATS/NHITS from daily planning lists (training_orchestrator, build_challenger_execution_plan, multistep_forecasting.yaml daily path).

---

## 12. Recommended implementation plan for the 15-model daily runner (V3.3C)

1. Create `python/model_lab/run_daily_model_refresh.py` (new; does not edit V3.2 scripts):
   - `DAILY_BASELINE = [FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6, ARIMA_Fixed, ETS_Current, LinearRegression]`
   - `DAILY_CHALLENGERS = [AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost]`
   - `DAILY_DL_FROZEN = [FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN]` (reused, not trained)
   - `PROHIBITED = {NBEATS, NHITS, FastNeuralAR_MLP}` → assert intersection is empty before any run.
2. Call the baseline runner, then a parameterized clean challenger run (list passed in, no NBEATS).
3. Carry the 3 frozen DL rows forward; re-run `build_tournament_engine` → `build_champion_decision` → `build_canonical_universe.R` → viewer handoff.
4. **Dry-run mode** that prints "these are the 15 models I will run" and **exits non-zero** if any prohibited model is present (V3.3C-0 step 5 / user requirement).

## 13. Risks / caveats

- The 3 DL models are **frozen**; daily runs cannot retrain them. If the business wants live DL, the closed candidate-study code must first be located/rebuilt (separate, out of daily scope).
- Editing `run_challenger_official_execution.py` in place risks disturbing V3.2 close-out reproducibility — prefer a new daily variant.
- `model_registry.py` keeps NBEATS/NHITS registered; the guard must operate on the **resolved daily list**, not the registry.
- Confidence on viewer-handoff exact model set is MEDIUM (not deeply traced in this read-only pass).

## 14. Recommended next step

Authorize **V3.3C — Runner Fix**: build the new daily orchestrator + dry-run guard described in §12. Do **not** start it without explicit authorization.
