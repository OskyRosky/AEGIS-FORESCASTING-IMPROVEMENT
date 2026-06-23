# Audit #4 — Official Challenger Results Readiness Audit

**Platform:** TESSERACT v2 / AEGIS Forecast Improvement Platform
**Stage:** Stage 5 — Model Lab
**Gate audited:** Readiness to proceed to **5.30 — Tournament Engine**
**Reviewer:** Independent senior audit reviewer (Claude Opus 4.8)
**Audit type:** Read-only verification (no model outputs modified, no reruns, no metric recalculation except independent spot-checks)
**Generated:** 2026-06-13T18:00:00

---

## 1. Executive Verdict

**APPROVE_WITH_CONDITIONS_TO_PROCEED_TO_5.30_TOURNAMENT_ENGINE**

The official challenger forecasts, metrics, denominator policy, non-negative scoring, aggregation hierarchy, and pairwise significance evidence are **correct, internally consistent, leakage-safe, and ready** to be carried into the Tournament Engine. Every headline figure asserted by the upstream blocks (5.29D-Recovery, 5.29E, 5.29F) was **independently reproduced** by this audit from the raw artifacts and matched to full precision.

There are **0 blockers** and **0 major integrity findings**. Two advisories and one minor finding are documented; none compromise the integrity of the challenger result set or block 5.30. The single substantive concern — FastNeuralAR_MLP's extreme error — is **transparently flagged, isolated, and does not contaminate any other model's metrics, aggregation, or significance evidence**.

---

## 2. Reviewed Artifacts

**Model-set re-scope:** `model_set_rescope_decision.csv`, `current_official_challenger_set.csv`, `onboarding_addendum.csv`, `execution_planning_addendum.csv`, `official_execution_prep_addendum.csv`, `fast_neural_policy.md`, `model_set_rescope_report.md`

**Official execution:** `challenger_official_forecasts.csv`, `challenger_official_execution_status.csv`, `challenger_official_model_summary.csv`, `challenger_official_contract_validation.csv`, `challenger_official_execution_summary.csv`, `challenger_official_execution_manifest_final.csv`, `challenger_official_execution_report.md`

**Execution recovery:** `partial_output_inventory.csv`, `fast_neural_sandbox_status.csv`, `fast_neural_official_status.csv`, `recovery_summary.csv`, `recovery_report.md`

**Metrics:** `challenger_scoring_forecasts.csv`, `challenger_actual_forecast_join.csv`, `challenger_metrics_entity_window.csv`, `challenger_negative_forecast_impact.csv`, `challenger_metrics_by_model_diagnostic.csv`, `challenger_metrics_validation.csv`, `challenger_metrics_summary.csv`

**Aggregation/significance:** `challenger_canonical_entity_window_scores.csv`, `challenger_aggregation_by_entity_model.csv`, `challenger_aggregation_by_model.csv`, `challenger_pairwise_significance.csv`, `challenger_model_significance_summary.csv`, `challenger_family_summary.csv`, `challenger_outlier_risk_review.csv`, `challenger_tournament_input_manifest.csv`, `challenger_aggregation_significance_validation.csv`, `challenger_aggregation_significance_summary.csv`, `challenger_aggregation_significance_report.md`

**Denominator policy & config:** `training_only_denominators.csv`, `denominator_reconciliation_report.md`, `config/scoring_definitions.yaml`, `config/ranking_policy.yaml`

**Baseline reference (read-only, not modified):** `aggregation_hierarchy/aggregation_policy.md`-adjacent artifacts, `statistical_significance/significance_policy.md`-adjacent artifacts.

Independent verification harness: `outputs/model_lab/audit_4/_audit_4_independent_verification.py`.

---

## 3. Row-Count Reconciliation

| Quantity | Expected | Independently Observed | Status |
| --- | ---: | ---: | --- |
| Official forecast rows | 81,720 | 81,720 | PASS |
| Rows per model (×6) | 13,620 | 13,620 each | PASS |
| Entity-windows | 454 | 454 (39 entities × ≤12 windows) | PASS |
| Horizon days per entity-window | 30 | 1..30 | PASS |
| Actual-forecast join rows | 81,720 | 81,720 | PASS |
| Missing actuals | 0 | 0 | PASS |
| Metric rows | 2,724 | 2,724 (454 × 6) | PASS |
| Negative raw forecast rows | 306 | 306 | PASS |
| Canonical entity-window scores | 2,724 | 2,724 | PASS |
| Entity/model aggregation rows | 234 | 234 (39 × 6) | PASS |
| Model aggregation rows | 6 | 6 | PASS |
| Pairwise comparisons | 15 | 15 | PASS |
| Supported / inconclusive | 12 / 3 | 12 / 3 | PASS |
| Risk flags | 4 | 4 | PASS |

---

## 4. Model-Set Validation

- Final official set = exactly the **6** required models: AutoARIMA, Theta, ETS Explicit, LightGBM, XGBoost, FastNeuralAR_MLP.
- **NBEATS** → `deferred_runtime_impractical`; **NHITS** → `deferred_dependency_blocked`. Both deferral rows, reasons, and history are **preserved** (no silent deletion/rewrite) across every re-scope addendum.
- **FastNeuralAR_MLP** is documented (`fast_neural_policy.md`) as an NNETAR-style lightweight neural (sklearn `MLPRegressor`) replacement with explicit leakage controls (train on `date <= train_end_date`, recursive forecast, no future actuals), fixed pre-registered hyperparameters (hidden `(32,)`, relu, adam, max_iter 300, seed 42), and a dependency footprint suited to MVP/container/Azure automation.
- Re-scope justification (runtime impracticality of NBEATS; Python 3.14/neuralforecast/ray block for NHITS) is coherent and matches the MVP automation profile.

**Result: PASS (A1–A6).**

---

## 5. Forecast Validation

Independently from `challenger_official_forecasts.csv`:

- 81,720 rows; **only** the 6 final models; **0 NBEATS rows; 0 NHITS rows**.
- `execution_mode` = `official` (single value).
- `horizon_day` ∈ 1..30 (30 distinct); `forecast_value` has **0 nulls, 0 infinities**.
- **0 duplicate** rows on (run_id, model_name, entity_key, window_id, horizon_day).
- 39 distinct entities, window_id 1..12, 454 entity-windows.
- **Leakage-safe:** every `forecast_date` is strictly after the entity-window `train_end_date` (0 violating rows); forecast dates span 2025-05-03 … 2026-04-27.
- Raw forecasts preserved (306 raw negatives retained unmodified in `forecast_value`).

**Result: PASS (B1–B12).**

> Note (F-015, MINOR): the pre-recovery `partial_output_inventory.csv` records NBEATS partial rows (900 in the forecasts path, 960 in the checkpoint) that were correctly **excluded**. The final forecast and metric files independently contain **0** NBEATS rows. 5.30 must consume only the final `challenger_official_forecasts.csv` (never the `_checkpoint_*` / partial artifacts).

---

## 6. Metrics Validation

- Join = 81,720 rows, **0 missing actuals**.
- Metric table = 2,724 rows (454 per model); all seven metrics present: **MASE, RMSSE, wMAPE, MAPE, SMAPE, RMSE, Bias**.
- **0 NaN / 0 Inf** in MASE and RMSSE (and all other metrics).
- No NBEATS/NHITS in metrics; FastNeuralAR_MLP included.
- **Official scoring uses `adjusted_forecast_value` (non-negative), not raw `forecast_value`.** Independent MASE/RMSSE recomputation on 5 random entity-windows using `adjusted_forecast_value` matched stored values to full precision (e.g., FastNeuralAR_MLP DEU-Go Local w2: MASE 1207.6156 = stored; AutoARIMA NAM-Multitenant w3: MASE 13.0527 = stored).

**Result: PASS (C1–C8).**

---

## 7. Denominator Policy Validation

- MASE denominator = `training_only_lag1_naive_mae`; RMSSE denominator = `training_only_lag1_naive_mse`; both loaded from `training_only_denominators.csv` (454 entity-windows).
- **Training-only:** `denominator_observations = training_observations − 1` for all rows (lag-1 absolute/squared first differences over training actuals); **no test actuals** enter the denominator (confirmed by construction and by the leakage check in §5).
- `config/scoring_definitions.yaml` and `config/ranking_policy.yaml` set `never_use_test: true`, `block_519_naive_forecasts_allowed_as_denominator: false`, and `seasonal_naive_allowed_as_denominator: false` — i.e., the corrected 5.27A/5.27B policy is respected and neither the 5.19 naive forecast nor a seasonal naive is used as a denominator.

**Result: PASS (D1–D7).**

---

## 8. Non-Negative Scoring Validation

- `adjusted_forecast_value = max(forecast_value, 0)` — **0** rows violate this identity.
- `negative_forecast_flag` true count = **306**, matching raw `forecast_value < 0` exactly; adjusted negatives = 0.
- Raw forecasts preserved in both the forecast and scoring files; **no raw file overwritten**.
- Adjustment documented per model in `challenger_negative_forecast_impact.csv` (AutoARIMA 115, ETS 133, FastNeuralAR_MLP 55, XGBoost 3, LightGBM 0, Theta 0 = 306).

**Result: PASS (E1–E6).**

---

## 9. Aggregation Validation

- Canonical 2,724 → entity/model 234 (39 × 6) → model 6.
- **Two-stage equal-entity-weighted hierarchy** independently reproduced: median MASE across windows per entity, then median across the 39 entity medians. All six stored `official_median_mase` values matched exactly (AutoARIMA 8.08853, Theta 10.64229, ETS Explicit 6.90114, LightGBM 16.04104, XGBoost 14.54763, FastNeuralAR_MLP 739.92189).
- Equal entity weighting confirmed — entities with more windows do **not** dominate because stage-1 collapses each entity to a single median first.
- **No ranking columns; no winner/champion/best-model language** (report is explicitly diagnostic-only).

**Result: PASS (F1–F7).**

---

## 10. Significance Validation

- 15 pairwise comparisons; each paired across **all 39 entities** on entity-level median MASE.
- **10,000 bootstrap iterations**, deterministic **seed 20260612**, exact **paired sign test**, **Benjamini-Hochberg** correction across all 15 comparisons, **practical threshold 0.02** (verified single-valued).
- BH adjusted p ≥ raw sign-test p for all rows (monotonicity sanity check passed).
- **12 supported_difference / 3 inconclusive** — these are **evidence labels only**, not rankings, and no champion/tournament decision is made (`tournament_created` / `champion_selected` = False).

**Result: PASS (G1–G10).**

---

## 11. FastNeuralAR_MLP Risk Assessment

FastNeuralAR_MLP ran successfully across all 454 entity-windows (124s, no failures) and is leakage-safe, but its error is **orders of magnitude worse** than every other challenger:

| Signal | FastNeuralAR_MLP | Other 5 challengers (range) |
| --- | ---: | --- |
| Official median MASE | 739.92 | 6.90 – 16.04 |
| Official median RMSSE | 164.62 | 1.86 – 4.06 |
| Median wMAPE | 0.861 | 0.0088 – 0.0206 |
| Median SMAPE | 1.481 | 0.0087 – 0.0208 |
| Median signed bias | ≈ −17,657 | small relative to scale |

**Assessment of likely cause.** The combination of (a) very large *negative* bias, (b) SMAPE ≈ 1.48 (near the 2.0 ceiling), and (c) MASE ~50–100× the statistical/ML models points to a **probable scale/normalization or recursive-collapse implementation issue** (the MLP appears to systematically forecast far below the true level), **not** a marginal "the model is simply a bit weaker" outcome and **not** a denominator artifact (denominators are shared, training-only, and independently validated; the same denominators yield sensible MASE for the other five models). It is **not** classifiable as a metrics/aggregation/leakage defect — those pipelines are correct.

**Disposition.** The behavior is **flagged, not hidden** (`challenger_outlier_risk_review.csv` raises `extremely_high_mase` and `extremely_high_rmsse` at risk_level `high`; the 5.29F report calls it out explicitly for this audit). There is **no evidence of implementation invalidity** that meets the bar for removal, and removing it is **not** recommended. The recommendation is to **carry the high-risk flag into 5.30 and investigate the model's feature scaling / recursive forecasting before it is ever treated as a viable contender or champion.** Its presence does not distort any other model's evidence (paired comparisons isolate it).

**Result: included & properly flagged — ADVISORY (F-014); checklist H2/H4 = WARNING, non-blocking.**

---

## 12. Tournament-Readiness Assessment

- `challenger_tournament_input_manifest.csv` exists, lists the **6 final challengers**, and contains **metadata only** (model_origin, model_family, metrics/aggregation/significance availability, `eligible_for_tournament_consideration`, exclusion_reason).
- **No tournament scores and no rank columns** (independent column scan = none).
- The `eligible_for_tournament_consideration` boolean (all True) is an **eligibility gate, not a ranking** (F-016, ADVISORY).
- The manifest, the validated forecasts, metrics, aggregation, and significance evidence collectively form a **clean, audit-approved input set** for 5.30.

**Result: PASS (I1–I6) — ready as 5.30 input.**

---

## 13. Scope / Safety

- **No** rankings, tournament outputs, winners, or champions were created (all corresponding flags False across status/summary CSVs; no such files exist).
- Challenger metrics live only under `challenger_metrics/`; aggregation/significance only under `challenger_aggregation_significance/`.
- Baseline outputs, Shiny, and other protected outputs were **not** modified by the upstream blocks or by this audit.
- This audit wrote **only** under `outputs/model_lab/audit_4/`.

**Result: PASS (J1–J8).**

---

## 14. Blockers

**None.** No forecast, metric, denominator, aggregation, or significance integrity defect was found.

---

## 15. Non-Blocking Findings

| ID | Severity | Summary |
| --- | --- | --- |
| F-014 | ADVISORY | FastNeuralAR_MLP extreme MASE/RMSSE — probable scale/implementation issue; flagged and isolated; investigate before treating as a contender; do not remove. |
| F-015 | MINOR | Pre-recovery NBEATS partial rows existed in inventory but are absent from final outputs; ensure 5.30 reads only final forecasts, never checkpoint/partial files. |
| F-016 | ADVISORY | Tournament manifest's `eligible_for_tournament_consideration` is metadata/eligibility, not a ranking; acceptable. |

---

## 16. Recommendations

1. **Proceed to 5.30** using `challenger_tournament_input_manifest.csv` plus the validated metrics/aggregation/significance set; never ingest `_checkpoint_*` or partial NBEATS artifacts.
2. **Propagate the FastNeuralAR_MLP `high` risk flag** into the Tournament Engine and gate it from champion eligibility until a scale/implementation review is completed.
3. **Open a follow-up investigation** into FastNeuralAR_MLP feature scaling / recursive-forecast collapse (suspected root cause of the ~740 MASE); keep raw and adjusted forecasts as evidence.
4. Keep all challenger evidence **diagnostic-only** until 5.30 formally introduces ranking semantics within-cohort.

---

## 17. Final Decision

**APPROVE_WITH_CONDITIONS_TO_PROCEED_TO_5.30_TOURNAMENT_ENGINE**

Conditions (documentation/operational, non-blocking):
- Carry the FastNeuralAR_MLP high-risk flag forward and investigate its error before treating it as a viable contender/champion.
- Ensure 5.30 consumes only the final, audited forecast/metric/manifest artifacts.

**Recommended next step:** `PROCEED_TO_5.30_TOURNAMENT_ENGINE`
