# V3.3B — Runtime Benchmark Report

**Run ID:** v3_3b_runtime_benchmark
**Date:** 2026-06-26
**Status token:** `V3_3B_RUNTIME_BENCHMARK_PARTIAL`
**Wall clock:** ~23 min (well within 150-min hard budget)

---

## 1. Objective
Measure the real per-stage and total runtime of the daily refresh pipeline (S00–S14) on the local Windows PC, confirm unattended auth, and determine feasibility for a 10:00 AM daily run — without permanently disturbing the consistent V3.2H dashboard state.

## 2. Method
- Full reversible **state backup** taken before any mutation (data/raw, data/processed, model_lab compute dirs, dashboard, governance, challenger dirs).
- Each stage run by its real entrypoint, logged to `logs/S##_*.log` with start/end timestamps and exit codes.
- Productive state **restored from backup** after measuring, preserving V3.2H consistency.

## 3. Scope correction (applied mid-run, per user direction)
The active daily universe is the **15-model V3.2H canonical set**. The heavy deep-learning models **NBEATS** and **NHITS** are **NOT** in daily scope (too expensive). The legacy script `run_challenger_official_execution.py` uses `APPROVED_MODELS = [AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, NBEATS]` + `DEFERRED_MODEL = NHITS` — it does **not** match the active universe. Its run is therefore reclassified as a **legacy heavy probe**, not part of the daily pipeline.

## 4. Three runtime buckets (the key separation)

### 4a. Current daily pipeline runtime (MEASURED)
S00–S08 in-scope stages = **145.6 s ≈ 2.43 min** (reusing frozen challenger artifacts).

### 4b. Legacy heavy challenger probe runtime
S03b `run_challenger_official_execution.py` = **17.0 min and did NOT complete** (still training NBEATS on CPU/torch when stopped). Proof the legacy heavy DL path is unsuitable for daily refresh.

### 4c. Excluded / deferred heavy DL models
**NBEATS, NHITS** — excluded from daily scope. Not to appear in the active daily refresh plan.

## 5. IMPORTANT caveat on 4a
The 2.43-min daily figure **reuses frozen challenger artifacts** (`challenger_actual_forecast_join.csv`, challenger metrics). It does **NOT** include regenerating the **active DL challengers (FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN)** nor the LightGBM/XGBoost challenger forecasts for the 15-model universe. The **true** daily runtime with full active-universe challenger regeneration is **UNMEASURED** and must be measured in V3.3C with a correctly-scoped entrypoint.

## 6. Per-stage results
See `runtime/stage_runtime_summary.csv`. All in-scope stages S00–S08 PASS (exit 0). S03b STOPPED_NOT_IN_SCOPE. S09 ENTRYPOINT_NOT_CONFIRMED. S10 COVERED_BY_S04_S07_S08. S11–S14 NOT_IMPLEMENTED (build in V3.3E/F/H).

## 7. Auth / VPN / SQL
Unattended local execution **CONFIRMED**: ActiveDirectoryInteractive token cached, **no interactive prompt**, SELECT 1 OK in 30.8 s over VPN. See `status/auth_sql_precheck_result.csv`.

## 8. forecast_comparison.csv = 0 rows
**Expected data drift — NOT a transform bug.** Fresh actuals end 2026-04-27, but the latest forecast version is 2026-05-01, so the same-date join yields 0 rows. The transform correctly warns and continues. Will recur on real daily data when actuals lag the newest forecast version; the dashboard comparison panel should handle empty gracefully (note for V3.3C/E).

## 9. Champion behavior
Champion = **ETS Explicit** (MASE 6.901144), **unchanged** after benchmark rerun (deterministic on frozen inputs). No daily auto-apply guardrails exist yet — build in V3.3F. See `status/champion_behavior_observation.csv`.

## 10. Last Update
Currently sourced from `run_metadata.csv` (S02 Transform) → advances even if downstream fails. Recommend a true end-of-pipeline **seal (S11)** in V3.3E. See `status/last_update_observation.csv`.

## 11. Entrypoint for the 15-model universe
**Does NOT exist.** Baseline models come from `run_full_baseline_execution.py`; the statistical/ML challengers come from the legacy `run_challenger_official_execution.py` (which wrongly includes NBEATS); the active DL models (FNAR-V2, NLIN-DLIN_FIXED, SMLP-TCN) come from a separate `candidate_evaluation` path. **No single runner produces exactly the 15-model daily universe → REQUIREMENT for V3.3C.**

## 12. State integrity
Backup created (95 files / 169.2 MB + challenger dirs), all mutations restored, key files verified back to pre-benchmark timestamps (run_metadata 6/10, canonical 6/26 V3.2H). No orphaned processes (python.exe count = 0).

## 13. Constraints honored
No V1/V2 edits; no scheduler; no pipeline-script modifications (logging wrappers only); no V3.3C/V4 start; clean stop with partial outputs.

## 14. Validation
See `v3_3b_validation.csv` — 27 checks: 24 PASS, 3 FAIL (the 3 FAILs are deliberate gaps that define V3.3C/E/F work: no unified 15-model entrypoint, Last Update not sealed, no champion guardrails).

## 15. Conclusion
- Daily pipeline (frozen-challenger reuse) is **fast (~2.4 min)** and runs **unattended**.
- The **dominant runtime risk is challenger regeneration**, and the **legacy heavy path (NBEATS/NHITS) is unsuitable** (17 min, incomplete).
- The true daily cost depends on regenerating **only** the active 15-model universe (incl. FNAR-V2/NLIN-DLIN_FIXED/SMLP-TCN) — **not yet measurable** because no correctly-scoped entrypoint exists.

## 16. Hand-off to V3.3C (requirements)
1. Build/confirm a single **15-model-universe** execution entrypoint (excludes NBEATS/NHITS).
2. Measure true daily runtime with active DL challenger regeneration.
3. Parameterize frozen-data assumptions (e.g., 3178/6356 job counts) for fresh daily data.
4. Decide refresh cadence for active DL models (daily vs weekly) based on their measured cost.
