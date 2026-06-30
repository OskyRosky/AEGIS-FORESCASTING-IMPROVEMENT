# V4.5 — Prompt Contract — Closure Summary

- **Status:** `V4_5_PROMPT_CONTRACT_COMPLETED`
- **Date:** 2026-06-29
- **Phase type:** Contract formalization. **No real LLM, no Azure, no Shiny, no buttons.**

## What was formalized

The stable prompt + output + rendering contract that V4.6 will use to render explanations in
Shiny, and that any provider (mock now, Azure later — gated V4.9) must satisfy behind the same
schema. The provider **explains, never decides**. MVP scope stays fixed at the 4 pages.

## Outputs (in `outputs/v4_5_prompt_contract/`)

- `v4_5_prompt_contract.md` — main contract: scope, provider stages, behavior, page rules.
- `v4_5_system_prompt.md` — provider-agnostic base system prompt (works for mock now / Azure later).
- `v4_5_page_prompt_templates.md` — one template per page (champion / tournament / forecast / governance).
- `v4_5_output_schema.json` — **final stable schema** (`response_metadata` / `display` /
  `traceability` / `governance` / `download_payload` / `validation`). Valid JSON.
- `v4_5_response_contract.csv` — every field: type, required, description, validation rule, how rendered.
- `v4_5_forbidden_language_policy.csv` — banned terms + neutral replacements.
- `v4_5_prompt_validation_rules.csv` — PR01–PR25 response validation rules.
- `v4_5_example_payloads.json` — 4 valid example payloads **derived from V4.4** (no invented facts),
  each carrying its own `validation` block (22 checks each, all valid).
- `v4_5_rendering_contract.md` — exact Shiny rendering: button label, progress message, panel title,
  executive summary, what the evidence says, why it matters, sources, limitations, confidence,
  download payload, traceability, governance footer, and UI states.
- `v4_5_validation.csv` — phase checklist: **29 checks, 29 PASS / 0 FAIL**.
- `v4_5_closure_summary.md` — this file.

Supporting (not an output artifact): `python/llm_explanation/build_prompt_contract.py` derives the
example payloads from V4.4 and emits the validation checklist (pure file I/O; no provider activated).

## Mandatory rules encoded (verified)

`executive_summary`, `what_the_evidence_says`, `why_it_matters`, `sources_used`, `limitations`,
`confidence`, and traceable `claims` are all required. Insufficient-evidence path defined.
Download payload keys always present (populated in V4.7). Governance block fixed:
`champion_policy = frozen / governed / no auto-change`, `llm_policy = explain_only`,
`data_policy = read_only_evidence_pack`.

## Page-specific rules encoded

- **champion_overview:** ETS Explicit remains champion under governed conditions; no absolute-win, no auto-change.
- **tournament:** documented challengers; SMLP-TCN at 2.72x allowed; no winner language.
- **forecast_viewer:** evidence filtered/summarized/capped; namespace limitation surfaced; full data not passed.
- **governance_risks:** risks only from artifacts; insufficient-evidence when missing.

## Guarantees verified

- Both JSON files valid. All 4 example payloads valid (`is_valid = true`).
- No forbidden language in user-visible example content (`forbidden = none`).
- 29/29 phase checks PASS.

## Guardrails honored

No Shiny changes, no real buttons, no Azure, no external API, no real LLM, no `data/processed` or
`data/raw` mutation, no SQL, no model runs, no forecast recompute, no champion/governance change,
no V1/V2/V3 changes, no expansion beyond the 4 MVP pages.

## Backlog (not done here, by request)

Executive **tone polish** from the V4.4 review (less repeated "evidence-only conditions", more
"based on the governed artifacts currently available…") is deferred until it can be seen in the
dashboard.

## Next (pending authorization)

V4.6 — Shiny local on-demand (button + progress bar + on-screen response, rendering per
`v4_5_rendering_contract.md`). **Not started; awaiting Oscar's review and authorization.**
