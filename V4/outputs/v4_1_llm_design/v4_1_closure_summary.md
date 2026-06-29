# V4.1 — LLM Design — Closure Summary

- **Status:** `V4_1_LLM_DESIGN_COMPLETED`
- **Date:** 2026-06-29
- **Phase type:** Design only (no functional code, no UI changes, no Azure).

## What was delivered

V4.1 defines the full local-first LLM explanation design for AEGIS V4: 4 buttons mapped to
real Shiny tabs, a per-button evidence contract, the visible panel mockup, the output schema,
and the anti-hallucination validation rules. Everything is grounded on **real governed
artifacts** in `V4/data/processed/` and the existing seam `shiny_app/modules/llm_summary/` +
`shiny_app/R/llm_client.R` (not modified in this phase).

## Buttons designed

| page_id | Button | Real tab |
|---------|--------|----------|
| `champion_overview` | Explain Champion | Overview |
| `tournament` | Explain Tournament | Models |
| `forecast_viewer` | Explain this Forecast (filter-aware + guided questions) | Forecast Viewer |
| `governance_risks` | Explain Governance & Risks | Governance |

## Guarantees baked into the design

- The LLM **explains, never decides**; prohibited language list enforced (no winner/best/promote/etc.).
- **Artifacts first**: every claim traces to an evidence field; `insufficient evidence` is a valid answer.
- **Sources used** and **Limitations** always shown; snapshot caveat (2026-06-28) always disclosed.
- Forecast Viewer free-text is **limited to the selected evidence pack**.
- Champion described as *currently selected under stated conditions* (frozen ETS Explicit).

## Guardrails honored in V4.1

No Python code, no `build_evidence_pack.py`, no `llm_client.py` logic, no Shiny UI edits, no
real buttons, no data/processed changes, no SQL, no model runs, no champion/governance
changes, no V1/V2/V3 changes, no Azure, no FastAPI/APIM/reticulate.

## Next (pending authorization)

V4.2 — Evidence pack builder (first code: read governed CSVs, slice by selection, emit a
visible JSON/table evidence pack). **Not started; awaiting Oscar's review and authorization.**
