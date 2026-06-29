# V4.5 — Rendering Contract (how the explanation must appear in Shiny)

> This contract tells V4.6 exactly how to render an explanation response that conforms to
> `v4_5_output_schema.json`. It defines layout, labels and copy rules only. **No Shiny code is
> written in V4.5, no button is added, no real LLM and no Azure are activated.**

## Where it renders

Each of the 4 MVP pages (`champion_overview`, `tournament`, `forecast_viewer`,
`governance_risks`) gets an **on-demand explanation panel**. The panel is built only when the
user asks for it (button), reads a temporary evidence pack, and shows one response object.

## Control row (above the panel)

| Element | Source | Copy / behavior |
|---------|--------|-----------------|
| **Button label** | static per page | `Explain this view` (champion: `Explain champion`, tournament: `Explain tournament`, forecast_viewer: `Explain forecast view`, governance_risks: `Explain governance & risks`) |
| **Progress message** | shown while building pack + composing | `Reading governed evidence pack…` then `Composing explanation (local mock — no real LLM)…` |
| **Provider badge** | `response_metadata.provider` + `provider_stage` | Render literally, e.g. `mock · mock_no_llm`. While stage is `mock_no_llm`, also show the disclaimer: `Local mock — not a real LLM. No Azure connected.` |

## Panel layout (top to bottom)

1. **Panel title** ← `display.title`
   - Rendered as the panel header.
2. **Executive summary** ← `display.executive_summary`
   - One short paragraph. If it equals an "Insufficient evidence" statement, render it as a
     muted info note and skip sections 3–4 (still render sources, limitations, confidence).
3. **What the evidence says** ← `display.what_the_evidence_says[]`
   - Bulleted list. Each bullet is a traceable fact. Never reformat the numbers.
4. **Why it matters** ← `display.why_it_matters`
   - One short paragraph, neutral/executive framing.
5. **Sources used** ← `display.sources_used[]`
   - Bulleted list of governed artifact filenames. **Always shown** (min 1).
6. **Limitations** ← `display.limitations[]`
   - Bulleted list. **Always shown** (min 1). Must include the explain-not-decide caveat and
     the 2026-06-28 snapshot caveat.
7. **Confidence** ← `display.confidence`
   - Badge: `high` / `medium` / `low` / `insufficient_evidence`.
8. **Download payload** ← `download_payload`
   - In MVP render a disabled control labelled `Download (available in V4.7)`. The structured
     payload (markdown / json / csv_rows) is shown read-only for traceability.

## Traceability affordance

- A collapsible **"Show traceability"** area renders `traceability.claims[]` as
  `claim → maps_to` rows, plus `source_artifacts[]` and `evidence_pack_refs[]`.
- This is how a reviewer confirms every visible claim is backed by evidence.

## Governance footer (always visible)

Render `governance` literally as a one-line footer:

`Champion: frozen / governed / no auto-change · LLM: explain_only · Data: read_only_evidence_pack`

## Copy rules (must hold at render time)

- Show the **provider badge and mock disclaimer** whenever `provider_stage = mock_no_llm`.
- Never render any forbidden term (see `v4_5_forbidden_language_policy.csv`).
- Never render language implying the champion changed, that a decision was made, that Azure is
  active, or that a real LLM is active during mock mode.
- `sources_used`, `limitations`, and `confidence` must always be visible.
- If `validation.is_valid = false`, render a blocking notice instead of the panel and show
  `validation.checks_failed[]`.

## States the UI must handle

| State | Trigger | Rendering |
|-------|---------|-----------|
| Ready | response valid | full panel as above |
| Insufficient evidence | `confidence = insufficient_evidence` | muted summary + sources + limitations + confidence; sections 3–4 hidden |
| Invalid | `validation.is_valid = false` | blocking notice + `checks_failed[]`; no narrative shown |
| Building | request in flight | progress messages only |
