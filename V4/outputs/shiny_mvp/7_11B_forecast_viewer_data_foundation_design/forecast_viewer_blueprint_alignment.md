# Forecast Viewer — Blueprint Alignment & Stage Ownership

**Block:** 7.11B · Forecast Viewer Data Foundation Diagnosis (design only)
**Mode:** READ-ONLY. No code, data, model, governance, or Shiny file was modified.
**Blueprint reviewed:** `V1/docs/updated_blueprint/updated_tesseract_forecast_improvement_blueprint.md` (dated 2026-06-12).

---

## 1. Where does the multi-model Forecast Viewer artifact belong?

**Owner stage: Stage 5 (Model Lab) → handed off to Stage 7 (UI/UX).**

The Blueprint maps the 9-stage lifecycle as:

| # | Stage | Owns |
|---|---|---|
| 3 | Data Contract | Fixed schemas (forecasts, actuals, metrics, run_metadata) |
| 4 | Evaluation Platform | Evaluation dataset, backtest window inventory, official metric validation |
| **5** | **Model Lab** | **Baseline + challenger model execution, per-model forecasts, ranking, tournament, champion** |
| 6 | Validation Lab & Governance | Composite score, governance handoff, recommendations |
| 7 | UI/UX + LLM Insights | Executive UX (the Shiny Forecast Viewer) |

The **per-series, per-model forecast values** Oscar wants to compare are, by definition, **Stage 5
Model Lab outputs**. The Blueprint explicitly states the baseline execution
(`full_baseline_20260611_103953`, 95,340 rows, 39 entities × 7 models) and the challenger forecasts
live in `outputs/model_lab/`. Therefore:

- The **raw multi-model forecast data is a Stage 5 asset** (already produced).
- The **consolidated, visualization-ready artifact** (`forecast_viewer_model_outputs`) is a
  **Stage 5 → Stage 7 handoff artifact**: it is a *projection/curation* of Stage 5 outputs for
  presentation. It is NOT new modeling, NOT a metric recompute, NOT a governance decision.

**Conclusion:** This is a **Stage 5 handoff / Stage 7 support artifact**, not a Stage 3, Stage 4, or
Stage 6 concern, and not a Shiny-only bug.

---

## 2. Was the requirement missed earlier?

**It is a combination — primarily a missing handoff/consolidation artifact, plus Shiny binding to the
wrong source.**

1. **Shiny binding to the wrong artifact (immediate cause).** The current Forecast Viewer reads
   `data/processed/forecasts.csv`, which is the **final single-model production forecast** (45 series,
   exactly 1 `model_version` each). That is why the Viewer shows only one model per series.
2. **Missing consolidated data-foundation artifact (root cause).** The multi-model forecasts exist but
   are **split across two Stage 5 files** (`full_baseline_forecasts.csv` for 7 baseline models;
   `challenger_actual_forecast_join.csv` for 6 challenger models) and were **never consolidated** into a
   single visualization-ready table. The slot intended for this — `data/processed/forecast_comparison.csv`
   — exists but is **empty (0 rows)**.
3. **Partial blueprint scope nuance.** The Blueprint's original Stage 7 scope ("executive UX + LLM
   insights") did not explicitly define a *multi-model comparison viewer fed by a consolidated artifact*.
   The richer comparison view is an evolution of the requirement surfaced during Stage 7 build.
4. **Governance caveat (must be stated honestly).** As of the Blueprint date (2026-06-12) the challenger
   onboarding was **BLOCKED (AUDIT #2)** pending benchmark-semantics remediation. The challenger forecast
   artifacts present in `outputs/model_lab/` carry later timestamps (2026-06-13) and a
   `selected_champion = ETS Explicit`. The Forecast Viewer should therefore present challenger forecasts
   as **backtest evidence under a Stage 5 process still flagged for remediation**, not as final
   governed-champion production output.

**Net:** the pipeline produced the *data* but not the *consolidated handoff artifact*; Shiny then bound
to the only ready artifact (the final single-model forecast). It is a data-foundation gap, not a
conceptual error in Oscar's request.

---

## 3. Honest framing the Viewer must carry

- Multi-model values are **historical backtest forecasts** (window 2025-05-03 → 2026-04-27), **not**
  forward production forecasts (the forward forecast in `forecasts.csv` starts 2026-04-28).
- Multi-model coverage exists for **39 of 45 series**. Six series (AUT-, CHL-, DNK-, EUR-, IDN-, MYS-Go
  Local) have **only** the final single-model forecast.
- **Deep learning (NBEATS / NHITS) does not exist** — defined as registry placeholders and deferred;
  no forecast rows were produced.
- `FastNeuralAR_MLP` exists but must be labeled **lightweight neural / high-risk / not champion-eligible**
  (`risk_flag = TRUE`, `eligible_for_champion = FALSE`), never as a validated deep-learning champion.
- **No prediction intervals exist** in any forecast time-series artifact (all values are point
  forecasts).
