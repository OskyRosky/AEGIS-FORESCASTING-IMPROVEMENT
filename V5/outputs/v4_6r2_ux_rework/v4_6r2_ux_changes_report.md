# V4.6R2 — LLM Assistant UX + Interaction Rework (Nivel A: local composition)

**Status:** `V4_6_SHINY_LOCAL_ON_DEMAND_COMPLETED_AFTER_UX_REWORK`
**Scope:** 4 MVP sections only (Champion, Tournament, Forecast Viewer, Governance & Risks)
**Mode:** Local-first, governed, read-only. No real LLM, no Azure, no network, no SQL, no model recompute.

## Why this rework

V4.6R passed technically but was rejected as a user experience: the panel felt like a
static, pre-written report behind a button. The request was an **assistant** where the
user asks a question and the system **generates a new answer from the governed evidence**,
adapting to the question — not loading a fixed `.md`.

## What changed

### 1. Conversational UI (`shiny_app/R/llm_explain.R`)
- Kicker "AEGIS Explanation Assistant" + heading "Ask AEGIS about this section".
- A real **question box** ("Ask a question about this section") with an example placeholder.
- **Quick prompts** row: Summarize the key takeaway · Explain what changed · Explain the
  main risk · What should I pay attention to?
- A single primary **Generate explanation** call-to-action.

### 2. Visible reasoning (non-blocking)
- A thinking sequence drives a status line and a thinking card:
  *Analyzing the governed evidence → Checking limitations → Composing the explanation → Ready.*
- Implemented with `reactiveValues(step, ticking)` + `invalidateLater(600)`; step is
  isolated so the UI advances on the timer rather than blocking the session.

### 3. Local deterministic composition engine — **Nivel A** (`shiny_app/R/llm_compose.R`, NEW)
- The answer is **generated at runtime** from the governed evidence pack, not echoed.
- `.comp_intent(question)` classifies the question into one of:
  `bounded · compare · numeric · changed · risk · attention · process · takeaway · default`.
- `.comp_factbase(resp)` splits the claims traceability into **content**, **process** and
  **numeric** facts; `.comp_answer(resp, question)` selects and frames facts per intent,
  returning executive paragraphs (lead / exec / evidence / why / limitations).
- `.comp_sanitize()` is a governed safety net (e.g. *promoted → retained*, *winner →
  leading candidate*) that **never** alters the champion name. Forbidden-token scan
  (best/promote/winner) returns FALSE across all generated text.
- **Bounded** questions ("should we promote…", "predict…", "invest…") return:
  *"I can only answer using the governed evidence available for this section."* and then
  restate only the recorded evidence — the LLM layer never decides.

### 4. Presentation
- Answers render as **executive paragraphs**, not bullet dumps.
- A **"Question asked"** block and an **"AEGIS response"** lead box (green; amber variant for
  bounded answers).
- **Technical traceability** (Sources used + claims table + provider/stage line) is in a
  **collapsed** `<details>` — visible on demand, not by default.
- **Download explanation (.md)** is **enabled** and produces a governed markdown transcript.
- Discrete "Local mock" badge and a single muted governance footer.

## Evidence / verification
- App: `HTTP 200`, port 3839, PID recorded in `runtime/`.
- Live browser checks (Tournament `compare`, Champion `bounded`) and an R-level composition
  test across six intents confirmed answers **vary by question** and stay within the evidence.
- Champion remains **ETS Explicit** (median MASE 6.90, RMSSE 1.86, scope 15); 0 advanced.
- Logs: only standard package masking, a pre-existing data-parse warning, and informational
  plotly messages. No critical errors.

## Governance invariants honoured
LLM explains / never decides · no SQL / no model recompute / no Azure / no real LLM / no
network · no mutation of `data/processed` or `data/raw` · champion & governance untouched ·
V1/V2/V3 untouched · snapshot 2026-06-28 retained.
