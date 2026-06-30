# AEGIS Forecasting Improvement / Tesseract V3 — Project Documentation

Version: V3
Status: Active baseline (Stage 1 — Methodology Documentation)
Date: 2026-06-25
Scope of this document: formal project write-up for the V3 dashboard and its
read-only data contract. This document describes the approach; it does not change
any data artifact, forecast, interval, champion decision, metric, or governance
outcome.

---

## 1. What is AEGIS Forecasting Improvement / Tesseract V3

AEGIS Forecasting Improvement (internally "Tesseract V3") is a governed forecasting
review platform for enterprise HDD-region capacity series. It takes forecasting
evidence produced by an upstream pipeline and presents it through a read-only
Shiny dashboard so that reviewers can inspect forecasts, model comparisons,
intervals, capacity views, and governance decisions in one place.

V3 is the final version line. It is built as a controlled clone of V2 (the
functional MVP baseline) and evolves it with documentation, an AI explanation
layer, a more robust forecasting model, and an automated daily refresh — each
introduced as a separate, governed stage.

## 2. What problem it solves

Forecasting outputs and their governance evidence are normally scattered across
SQL extracts, processing scripts, model-lab notebooks, tournament results, and
audit documents. Reviewers cannot easily answer: which model won, how accurate it
is, how wide the uncertainty is, what the capacity runway looks like, and whether
the decision was governed. V3 consolidates that evidence into a single, consistent,
read-only view backed by governed artifacts, so review and sign-off are auditable
and repeatable.

## 3. Central architectural rule: Shiny does not cook data

The single most important rule of the platform:

> The Shiny dashboard is a **read-only consumer**. It never downloads from
> Tesseract, never cleans data, never trains or recalculates models, never
> recomputes forecasts or intervals, and never writes or edits artifacts.

All data is produced and governed by the **upstream pipeline**. The dashboard
loads the governed CSVs once at startup through a read-only loader and renders
them as-is. If a number is wrong upstream, it is fixed upstream — not in the app.

## 4. General architecture

The system has two clearly separated halves (see
`docs/architecture/aegis_v3_architecture_diagram.mmd` / `.png`):

- **Upstream pipeline (producer):** Tesseract v2 (SQL) → ingestion (Python) →
  `data/raw/` → processing/validation → `data/processed/` (governed CSV contract)
  → Model Lab (training, backtest, tournament, champion selection) → forecast,
  interval, and governance/reference artifacts.
- **Shiny dashboard (consumer):** a read-only data loader feeds the Forecasting,
  Models, Governance, and Reference page groups. No write-back path exists.

Planned/optional V3 components (a daily refresh orchestrator and an AI/LLM
explanation layer) are marked as planned and are not yet implemented.

## 5. Data sources

- **Primary source:** `TesseractEarthDW.dbo.forecast_substrateBE_hdd_region`
  (Scenario = Enterprise, ValueType = Forecast-Mean), queried by the Python
  ingestion layer and exported to `data/raw/`.
- **Governed processed contract (`data/processed/`):** `forecasts.csv`,
  `actuals.csv`, `entities.csv`, `run_metadata.csv` — validated and reshaped
  with no shifted dates, no imputations, and no recompute.

## 6. Principal artifacts

- **Forecast/backtest:** `forecasts.csv`, `actuals.csv`, and
  `forecast_viewer_model_outputs.csv` (per-model backtest used by Viewer/Accuracy).
- **Intervals:** calibrated 80% prediction bands (see Section 8).
- **Model Lab closure pack:** key results, model universe, champion summary,
  risk register, next steps.
- **Tournament:** preliminary standings, model scorecard, pairwise evidence.
- **Governance:** audit findings, sanity review, champion conditions, and the
  approved dashboard language.

The Reference → Artifacts page lists the full governed registry and its
availability; the dashboard never edits these files.

## 7. Forecasting

The Forecasting page group presents series-level evidence:

- **Viewer:** actuals vs forecast per series, with model overlays from the
  backtest outputs.
- **Accuracy:** per-model backtest error diagnostics.
- **Forecast:** the governed forward forecast per series.
- **TTL / Capacity View:** time-to-limit / capacity runway (see Section 9).

All values are read directly from governed artifacts.

## 8. Intervals — 80% calibrated up to 60 days

The dashboard shows **80% prediction intervals that are empirically calibrated up
to a 60-day horizon**. Beyond the calibrated horizon, bands are not asserted as
calibrated. Intervals are produced upstream by the Model Lab calibration step; the
dashboard only displays them and does not recompute coverage or widen/narrow bands.

## 9. TTL / Capacity View

The TTL / Capacity View estimates a capacity runway (time-to-limit) from the
governed forecast. **Supply / capacity inputs remain prototype / simulated** unless
and until a validated supply artifact exists. Where supply is simulated, the view is
a planning prototype, not a production capacity commitment, and is labeled
accordingly. This view is read-only like every other page.

## 10. Models / Tournament / Champion

- **Universe:** the full set of candidate models considered.
- **Tournament:** preliminary standings, scorecard, and pairwise evidence used to
  rank models.
- **Champion:** the governed selected model and the conditions attached to its
  selection.

The champion is a **governed decision**. The dashboard displays the current
governed champion; it does not select, change, or auto-promote any model.

## 11. Governance / Risks / Audit

- **Risks:** the governed risk register and deferred-model / conditional context.
- **Audit:** the audit trail (audit findings, sanity review, verification verdict).

These reflect upstream governance decisions verbatim. The dashboard is evidence of
governance, not an actor in it.

## 12. Reference / Version / Freshness

- **Artifacts:** the governed artifact registry and downloads.
- **Methodology:** this approach, the data pipeline, and the architecture diagram.
- **Version:** build/runtime metadata, app version, policy, champion line, and the
  data snapshot freshness (forecast version, run date, coverage).

Freshness reflects the build date of the governed data contract, not a live query.

## 13. Current limitations

- The dashboard is strictly read-only and reflects the last governed build; it is
  not live against Tesseract.
- Intervals are only asserted as calibrated up to 60 days.
- TTL / Capacity supply inputs are prototype / simulated unless a validated supply
  artifact exists.
- The deep-learning challenger (FastNeuralAR_MLP) underperforms and is a candidate
  for replacement (planned, not yet done).
- No automated daily refresh is in place yet; updates are produced by running the
  upstream pipeline.
- No AI/LLM explanation layer is wired yet.

## 14. Roadmap (V3)

- **Stage 0 (done):** controlled clone of V2 → V3, parity validated, version bumped.
- **Stage 1 (this stage):** methodology documentation + architecture diagram.
- **Stage 2 (planned):** AI explanation layer with a provider abstraction
  (none / mock / azure_openai / local), starting with mock/static summaries;
  preference for Azure OpenAI or an approved corporate model; the LLM only explains
  artifacts and never computes.
- **Stage 3 (planned):** evaluate and replace the FastNeuralAR_MLP model against the
  engine and existing backtest (neural vs gradient-boosting), with no auto-promotion.
- **Stage 4 (planned):** daily refresh orchestrator (~10:00) — local benchmark first
  to measure end-to-end duration, then a robust Azure / approved internal scheduler.

## 15. How to interpret the dashboard

- Treat every number as **as-of the last governed build**, not live.
- Use Viewer/Accuracy to judge model behavior, Forecast for the forward path, and
  intervals for uncertainty (only up to 60 days).
- Use Tournament/Champion to understand model selection, and Governance for the
  decision trail.
- Use Reference → Version to confirm which data snapshot you are looking at.

## 16. What must NOT be assumed as final production

- TTL / Capacity supply figures where supply is simulated/prototype.
- Interval coverage beyond the 60-day calibrated horizon.
- The current deep-learning challenger as a final model choice.
- Any planned/optional component (daily refresh, AI/LLM layer) as already operating.
- Champion changes from any automated process — champion changes require human
  governance approval.
