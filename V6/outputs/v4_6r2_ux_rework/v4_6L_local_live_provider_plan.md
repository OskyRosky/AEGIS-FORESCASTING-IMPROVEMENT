# V4.6L — Local Live Provider (Ollama) — PLAN ONLY (not implemented)

This is the **planned** next phase after V4.6R2 (Nivel A). It is **not built yet** and must be
explicitly authorized before any work begins. It stays **local-first** and **governed**; Azure
remains a separate, optional, gated phase (V4.9).

## Goal
Replace the deterministic composition step with a **local LLM** (Ollama) that writes the
executive answer **from the same governed evidence pack**, while keeping every guardrail:
the model explains, it never decides, and it can only use the evidence it is handed.

## Flow (unchanged contract)
```
User asks in Shiny
  → Shiny sends page_id + current selection + question
  → Python/R builds a LIMITED evidence pack (the same V4.4 pack used today)
  → Local model (Ollama) drafts the answer from a GOVERNED prompt
  → Validator checks: language, bounded limits, champion name, internal sources only
  → Shiny shows the answer as executive paragraphs
```

## Design notes
- **Provider abstraction:** add a `provider` switch (`local_compose` | `ollama`) so the
  deterministic engine (`R/llm_compose.R`) remains the default and a safe fallback. If Ollama
  is unavailable, the app silently falls back to Nivel A — never stops.
- **Prompt construction:** build the prompt only from the evidence pack fields already shown
  in Technical traceability (claims, sources, limitations, confidence). No raw data, no SQL,
  no model internals.
- **Validator (reuse + extend `.comp_sanitize`):** reject/repair any output that (a) renames or
  re-ranks the champion, (b) makes a promotion/decision, (c) cites a source not in the pack,
  (d) introduces numbers not present in the evidence.
- **Determinism for review:** temperature 0 (or low), fixed seed where supported, so reviews
  are reproducible.
- **No network beyond localhost:** Ollama runs on `127.0.0.1`; no external API, no telemetry.

## Out of scope for V4.6L
- Azure OpenAI (that is V4.9, optional + gated).
- Any change to the champion, governance, scope, or the 2026-06-28 snapshot.
- Any expansion beyond the 4 MVP sections.

## Acceptance (when authorized)
- Same 19-point governance validation as V4.6R2, plus: provider=ollama, is_real_llm=true,
  uses_azure=false; validator catches injected violations in a red-team check; graceful
  fallback to `local_compose` verified.
