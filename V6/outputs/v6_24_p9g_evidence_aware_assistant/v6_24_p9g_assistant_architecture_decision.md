# V6.24-P9G — Assistant Architecture Decision

**Decision: Option A — selection-aware local deterministic evidence assistant.**

Option B (inject evidence into the existing engine) was evaluated and **rejected
as impossible**, not merely as less attractive. Option C (hybrid) was rejected
as a consequence.

---

## What the existing assistant actually is

I read all four assistant files before deciding.

| File | Entry point | What it accepts |
|---|---|---|
| `R/llm_explain.R` (860 lines) | `llm_explain_get(page_id)` | **a page id, and nothing else** |
| `R/llm_compose.R` (282 lines) | `.comp_answer(resp, question)` | the fixed response object above |
| `R/llm_client.R` (9 lines) | `get_llm_insight()` | **no arguments at all** |
| `modules/llm_summary/*` | — | 5-line stubs, no implementation |

`llm_explain_load()` reads `outputs/v4_4_mock_provider/v4_4_mock_responses.json`
once and indexes it **by `page_id`**. The panel for a page retrieves that page's
precomputed object. `.comp_answer()` then narrates *that object*.

There is no parameter, slot or hook through which a selected series could enter.
The file's own header states `is_real_llm = FALSE` and that it "does NOT call
any LLM, Azure, OpenAI or external API".

## Why that rules out Option B

Option B is permitted "only if the existing assistant already supports passing
custom evidence/context." It does not. To make it work I would have had to
either rewrite the mock-provider contract or pre-generate 140 series-specific
response objects — both of which produce *precomputed* text, not live evidence,
and the first mutates a V4.4 artifact I am not allowed to touch.

Mounting it unchanged under V6.24 would have produced the precise failure P9B
warned about: a panel titled "explain this series" that recites page-level text.
It would have looked finished and been wrong.

## What was built instead

`R/v6_24_assistant_helpers.R`:

- **`v6_24_evidence(series_id, cfg, fc_model)`** — builds the A–F context
  fresh on every request from `navigation_contract`, `series_signal_quality`,
  `model_backtests_15_models`, `model_rankings`, `accuracy_metrics`,
  `forecast_outputs` and `taxonomy_counts`. Missing values stay `NA` and print
  as "not available"; nothing defaults to zero.
- **`v6_24_assistant_intent(question)`** — routes free text to one of 14
  answerable categories, or to a refusal.
- **`v6_24_assistant_answer(e, question, intent)`** — composes prose from the
  context. Every number in the output came from an artifact column.

**What was reused:** the legacy assistant's UI pattern and CSS classes
(`llm-explain`, `llm-qp`, `llm-explain-btn`, `llm-explain-foot-badge`), so the
panel reads as the same product feature.

**What was not reused:** the engine, the mock provider, and
`.comp_intent()` — whose taxonomy is tournament-oriented (`mase`, `rmsse`) and
does not correspond to V6.24's fields.

## Honesty about what this is

The footer badge reads **"Local evidence · no LLM"** and every answer carries
`V6_24_LOCAL_DETERMINISTIC_EVIDENCE_V1`. There is no model, no network call and
no API key anywhere in the assistant path. The UI must not imply otherwise, so
it says so on screen.

## Consequence

Two assistants now exist: the legacy page-keyed one on the legacy sections, and
this evidence-aware one on V6.24. That duplication is deliberate for as long as
both sections coexist. Raised as Q2.
