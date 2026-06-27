# V3.2H — Model Consistency Fix

**Status:** `V3_2H_MODEL_CONSISTENCY_FIX_COMPLETED`
**Scope:** Data + narrative consistency fix only. No V3.3, no V4. Champion unchanged.

---

## 1. Executive summary

Before V3.2H, the Models pages mixed two incompatible views: the **legacy 13-model
governed tournament** (presented as if it were the current universe) alongside the
**new 15-model universe** shown in the Forecast Viewer. The fix introduces a single
**canonical 15-model universe** definition that the Universe, Tournament and Champion
pages now share, and clearly **labels the 13-model bootstrap tournament as legacy
governed evidence**. No model was re-run, no backtest recomputed, no champion changed.

## 2. Root cause

- The Universe page read `final_model_universe` (13 in-tournament models, including the
  retired high-risk `FastNeuralAR_MLP` under the old "lightweight_neural" family).
- The Tournament page derived "13 models / 78 pairwise" from the governed scorecard and
  pairwise artifacts and presented them as the current standings.
- The Champion series diagnostics read the 13-model `tournament_entity_model_scores`.
- The 3 deep-learning challengers (and the ML challengers) were evaluated **separately**
  in the closed V3.2D/V3.2E candidate study and never entered the bootstrap pairwise
  tournament — so the two populations were never reconciled into one definition.

## 3. Canonical model universe (15 models, 4 families)

| Family | Count | Models |
|---|---|---|
| Growth baseline | 4 | FixedGrowth_1_5, FixedGrowth_3, FixedGrowth_4, FixedGrowth_6 |
| Statistical | 5 | ARIMA_Fixed, AutoARIMA, **ETS Explicit** (champion), ETS_Current, Theta |
| Machine learning | 3 | LightGBM, LinearRegression, XGBoost |
| Deep Learning | 3 | SMLP-TCN, NLIN-DLIN_FIXED, FNAR-V2 |

- Built by aggregating **already-computed** medians: 12 governed models from
  `tournament_model_scorecard.csv`, and 3 deep-learning challengers from the closed
  `full_candidate_outputs.csv` (median over series). No model runs, no backtests.
- The original high-risk `FastNeuralAR_MLP` (MASE 739.9) is **retired**; the
  "lightweight_neural" family label is dropped in favour of **Deep Learning**.
- Champion **ETS Explicit, median MASE 6.901 — unchanged**.

## 4. Files created

- `data/processed/model_universe_canonical.csv` — the single canonical 15-model universe
  (model, family, origin, median MASE/RMSSE, champion flags, evidence_source).
- `outputs/v3_2h_model_consistency_fix/build_canonical_universe.R` — generator (read-only
  aggregation; hard data assertions).
- `outputs/v3_2h_model_consistency_fix/validate_v3_2h.R` — full validation (renders all
  three Models pages + governance/runtime checks).
- `outputs/v3_2h_model_consistency_fix/v3_2h_data_checks.csv` — data-level checks.
- `outputs/v3_2h_model_consistency_fix/v3_2h_validation.csv` — full 27-check validation.
- `outputs/v3_2h_model_consistency_fix/v3_2h_report.md` — this report.

## 5. Files modified

- `shiny_app/R/data_loader.R` — registered `model_universe_canonical` artifact; corrected
  viewer comment to 15 models.
- `shiny_app/R/helpers.R` — `universe_models()` now reads the canonical artifact (falls
  back to legacy only if absent); `universe_normalized()` coerces the new
  `median_mase`/`median_rmsse`/`family_label`/`evidence_source` columns; viewer comment
  corrected to 15 models.
- `shiny_app/ui/tabs.R`:
  - **Universe:** 15-model intro; Deep Learning family metadata; "Current model universe
    (15 models)" table with median MASE + evidence source; risk-flag explainer swapped for
    evidence-source explainer; removed the legacy "Full evaluated model universe
    (challengers)" island.
  - **Tournament:** "How to read this tournament" moved first; new "Current model universe"
    summary + "Current model ranking (15 models)" table; the 13-model evidence tree, league
    view and 78-comparison pairwise table relabelled and wrapped under an explicit
    "About the legacy 13-model tournament" banner.
  - **Champion:** new "What is the Champion" plain-language explainer first; series-level
    diagnostic now carries an explicit scope note that the 3 Deep Learning challengers lead
    0 individual series.
  - **Overview:** evidence-base text scoped to "13 governed tournament models".
- `new helper` `universe_canonical_ranking_table_ui()` in `tabs.R`.

## 6. Universe page fixes

- Reads the canonical artifact → **15 models / 4 families**, Deep Learning = 3.
- No `FastNeuralAR_MLP`, no "Lightweight neural" wording, no stale risk flag.
- Family cards and the current-universe table show median MASE and evidence source
  (Governed tournament vs Candidate evaluation). The challenger "island" section is gone.

## 7. Tournament page fixes

- Current view = **15 models / 4 families**; "How to read" is first.
- New **Current model ranking (15 models)** by median MASE/RMSSE with evidence source.
- The governed bootstrap tournament (13 models / 78 pairwise — evidence tree, league view,
  head-to-head details) is preserved exactly and **labelled legacy** with a clear
  explanation that the 3 DL + ML challengers were evaluated separately.

## 8. Champion page fixes

- New **"What is the Champion"** explainer first (selected governed model over the 15-model
  universe; aggregate evidence; under conditions; not best in every series).
- Comparison vs current challengers retained (no promotion; champion unchanged).
- Series-level diagnostics carry an explicit scope note: the 3 Deep Learning challengers
  (median MASE ≈ 18–80) lead **0** individual series, so the local leaders are unaffected.

## 9. Forecast Viewer confirmation

- Still **4 families**, 15 distinct models; Deep Learning shows the 3 final challengers.
- Unchanged by V3.2H (already correct from V3.2G).

## 10. Sections recalculated vs labelled legacy

- **Recalculated (from existing medians):** Universe (15), Tournament current ranking (15).
- **Labelled legacy (not safely recomputable):** 13-model evidence tree, league view, and
  the 78-comparison pairwise bootstrap — these require re-running tournament statistics and
  are out of scope (no recompute / no backtests).

## 11. Validation

- `v3_2h_validation.csv`: **27/27 checks passed**, including all family counts, retirement
  of FastNeuralAR_MLP, no user-facing "Lightweight neural", 15-model Universe/Tournament,
  legacy labelling, 4-family Viewer, no forecasts/intervals/governance/champion change,
  Shiny local HTTP 200, V1/V2 untouched, V3.3/V4 not started.

## 12. Local app test

- App launched from V3 root on port 3838 (pid 42804). Clean boot (only the expected benign
  vroom parsing warning). `GET http://127.0.0.1:3838` → **HTTP 200**. All three Models pages
  render without error.

## 13. Governance confirmation

- Champion **ETS Explicit, MASE 6.901 — unchanged**. 0 challengers promoted.
- `forecasts.csv`, interval artifacts and governance artifacts **not modified**.
- V1 and V2 **untouched**. V3.3 and V4 **not started**.

## 14. Remaining caveats

- The 13-model pairwise bootstrap remains the only source of head-to-head evidence; the
  3 DL challengers have median MASE/RMSSE but no pairwise record (by design). A full
  15-model pairwise bootstrap would require re-running governed tournament statistics and
  is deliberately out of scope for a consistency fix.
