# V4.5 — Prompt Contract (AEGIS V4 explanation layer)

- **Status target:** `V4_5_PROMPT_CONTRACT_COMPLETED`
- **Scope:** local-first MVP. **No real LLM, no Azure** activated by this phase.
- **MVP pages (fixed):** `champion_overview`, `tournament`, `forecast_viewer`, `governance_risks`.
  Expansion to 8 modules is **backlog**, gated on Boon/team validating the MVP.

## 1. Purpose

Formalize the stable prompt + output + rendering contract that every AEGIS V4 explanation must
satisfy, so that V4.6 (Shiny) can render responses without re-negotiating the format, and so that
a future provider can be swapped in behind the same contract.

## 2. Provider stages

| Stage | provider | provider_stage | When | Active in MVP |
|-------|----------|----------------|------|---------------|
| Local mock | `mock` | `mock_no_llm` | now (V4.4–V4.8) | **yes** |
| Local live | `local` | `local_live` | reserved | no |
| Azure | `azure_openai` | `azure_live` | V4.9 opt-in, gated | **no** |

The contract is **provider-agnostic**: the same schema, system prompt and templates work for the
mock now and for Azure later. Activating Azure is a separate, explicitly authorized step (V4.9).

## 3. How the explanation layer must behave

1. The provider receives a **governed evidence pack** (V4.2) and/or **deterministic insights**
   (V4.3) — never raw productive data.
2. It produces a response conforming to `v4_5_output_schema.json`.
3. It **explains, never decides**. It never changes the champion or governance.
4. Every important claim maps to an evidence field, source artifact, or V4.3 card.
5. If evidence is missing, it returns `confidence = insufficient_evidence` and says
   "Insufficient evidence." — it never fills the gap with invented facts.
6. `sources_used`, `limitations`, and `confidence` are **always present**.
7. Output is **local-first** and **evidence-only** in the MVP.

## 4. Mandatory response fields (summary)

`response_metadata` (page_id, provider, provider_stage, generated_at, project_version, local_first) ·
`display` (title, executive_summary, what_the_evidence_says, why_it_matters, sources_used,
limitations, confidence) · `traceability` (claims, source_artifacts, evidence_pack_refs) ·
`governance` (champion_policy, llm_policy, data_policy) · `download_payload` (markdown, json,
csv_rows) · `validation` (is_valid, checks_passed, checks_failed).

Full field rules: see `v4_5_response_contract.csv`. JSON Schema: `v4_5_output_schema.json`.

## 5. Page-specific rules

- **champion_overview** — State that ETS Explicit **remains champion under governed conditions**.
  Do **not** say it won absolutely. Do **not** suggest any automatic change.
- **tournament** — May discuss **documented challengers**; may mention **SMLP-TCN at 2.72x** when
  present in V4.3/V4.4. No absolute-winner language.
- **forecast_viewer** — Must state the evidence was **filtered, summarized, and capped**; must
  surface the **model namespace** limitation; must make clear full data was not passed; depends on
  on-screen filters/selection in later phases.
- **governance_risks** — Explain risks, guardrails and limitations **from artifacts only**; never
  invent risks; say **insufficient evidence** when evidence is missing.

## 6. Forbidden language

See `v4_5_forbidden_language_policy.csv` for the full list and neutral replacements. Core banned
terms: `winner`, `best`, `unconditional champion`, `promote`, `promoted champion`,
`production approved`, `automatic decision`, plus any phrasing implying V4 changes the champion or
governance, that Azure OpenAI is active, or that a real LLM is active during mock mode.

## 7. Validation

Responses are validated against `v4_5_prompt_validation_rules.csv`. The phase-level checklist is
`v4_5_validation.csv`. Worked, valid examples (derived from V4.4, no invented facts) are in
`v4_5_example_payloads.json`.

## 8. What this phase does NOT do

No Shiny changes, no real buttons, no Azure, no external API, no real LLM, no `data/processed` or
`data/raw` mutation, no SQL, no model runs, no forecast recompute, no champion or governance change,
no V1/V2/V3 changes, no expansion beyond the 4 MVP pages.

## 9. Style note

The executive tone polish requested on V4.4 (less repeated "evidence-only conditions", more
"based on the governed artifacts currently available…") is **deferred to backlog** and will be
revisited once it can be seen in the dashboard. V4.5 only fixes the contract and ensures content
can be rendered.
