# V4.1 — LLM Design (AEGIS V4, local-first)

- **Status target:** `V4_1_LLM_DESIGN_COMPLETED`
- **Date:** 2026-06-29
- **Scope:** DESIGN ONLY. No functional code, no Shiny UI changes, no Python scripts, no Azure,
  no mock provider implementation. This document defines *how the LLM explanation experience
  will look and behave* before any code is written.

---

## 1. Purpose

V4 adds a **local-first LLM explanation layer** over already-governed artifacts. The LLM
**explains; it never decides**. It turns validated facts into executive prose with sources,
limitations, and (in later phases) a downloadable summary.

**Mother rule:** Shiny does not compute or modify productive artifacts; it may only build
**temporary read-only evidence packs** for on-demand LLM explanations.

---

## 2. Design principles (binding)

1. **Artifacts first, LLM second.** The LLM only sees a curated evidence pack built from
   governed CSVs. It never reads raw SQL, never recomputes metrics.
2. **The LLM explains, never decides.** It must not imply it selects, promotes, or changes
   the champion or governance.
3. **No invented metrics.** Every number in the output must trace to an evidence field.
4. **No causality without evidence.** Correlation/seasonality claims must be hedged unless
   the artifact states them.
5. **Insufficient evidence is a valid answer.** If the pack lacks the data, respond
   `insufficient evidence` — do not guess.
6. **Always show Sources used and Limitations.** Non-negotiable sections of every answer.
7. **Visible and executive.** The result is a panel the user can read and (later) download,
   not a backend log.

---

## 3. The 4 initial buttons (mapped to real tabs)

| page_id | Button | Real Shiny tab (file) | Primary governed artifacts |
|---------|--------|-----------------------|----------------------------|
| `champion_overview` | Explain Champion | Overview (`ui/tabs/overview_tab.R`) | `model_champion_comparison.csv`, `model_dashboard_summary.csv`, `model_universe_canonical.csv` |
| `tournament` | Explain Tournament | Models (`ui/tabs/models_tab.R`) | `model_evaluation_ranking.csv`, `model_evaluation_summary.csv`, `model_runtime_guardrails.csv` |
| `forecast_viewer` | Explain this Forecast | Forecast Viewer (`ui/tabs/forecast_overlay_tab.R`) | `forecasts.csv`, `actuals.csv`, `forecast_comparison.csv`, `forecasts_with_intervals*.csv`, `forecast_viewer_model_outputs.csv`, `entities.csv` |
| `governance_risks` | Explain Governance & Risks | Governance (`ui/tabs/governance_tab.R`) | `model_runtime_guardrails.csv`, `run_metadata.csv`, `ttl_months_to_live_snapshot.csv`, `ttl_supply_demand_timeseries.csv` |

The full per-button contract (allowed/prohibited artifacts, filters, answerable questions,
language, output, validations, fallback) lives in
[v4_1_button_evidence_contract.csv](v4_1_button_evidence_contract.csv).

---

## 4. Forecast Viewer — filter-aware behavior

The Forecast Viewer explanation **depends on what the user has selected on screen**. The
evidence pack must capture the current selection:

- entity / region (if applicable)
- model or models selected
- horizon
- time window
- available metric (from `model_evaluation_summary.csv`, read-only)
- the current visual comparison (actual vs forecast, intervals)

**Guided questions (buttons):**
- Explain selected model
- Compare selected models
- Summarize forecast risk
- Explain selected forecast movement

**Free-text box:** allowed but **strictly limited to the selected evidence pack**. The LLM
must refuse (with `insufficient evidence`) any question that cannot be answered from the
current pack. No outside knowledge, no speculation.

---

## 5. Provider seam (design, not built here)

- Local MVP uses **mock** only. `azure_openai` and `local` are deferred to V4.9 (gated).
- Integration is via shell-out: Shiny → `run_llm_explainer.py` (page_id + filters) → Python
  builds evidence pack → provider → validation → writes output artifact → Shiny reads it.
- **No reticulate, no FastAPI, no APIM** in the local MVP.
- The existing `shiny_app/R/llm_client.R` and `shiny_app/modules/llm_summary/` are the
  designated seams — **not modified in V4.1**.

---

## 6. Output contract (preview)

Every answer (future phases) follows the schema in
[v4_1_output_schema.json](v4_1_output_schema.json):
`summary`, `key_findings`, `evidence_used`, `sources_used`, `limitations`, `confidence`,
`claims_traceability`, `download_payload`.

Anti-hallucination rules are in
[v4_1_validation_rules.csv](v4_1_validation_rules.csv). The visible panel layout is in
[v4_1_panel_mockup.md](v4_1_panel_mockup.md).

---

## 7. Prohibited language (all buttons)

`winner`, `best`, `unconditional champion`, `promote`, `promoted champion`,
`production approved`, `automatic decision`, and any phrasing implying V4 changes the
champion or governance. The champion is **frozen ETS Explicit (with conditions)**; the LLM
describes it as *the currently selected champion under stated conditions*, never as a
"winner".

---

## 8. What V4.1 does NOT do

No Python code, no `build_evidence_pack.py`, no `llm_client.py` logic, no Shiny UI edits, no
real buttons, no data/processed changes, no SQL, no model runs, no champion/governance
changes, no V1/V2/V3 changes, no Azure, no FastAPI/APIM/reticulate, no advance to V4.2.
