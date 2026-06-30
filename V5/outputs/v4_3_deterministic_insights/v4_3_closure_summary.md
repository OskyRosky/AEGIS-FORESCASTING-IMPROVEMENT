# V4.3 — Deterministic Insights — Closure Summary

- **Status:** `V4_3_DETERMINISTIC_INSIGHTS_COMPLETED`
- **Date:** 2026-06-29
- **Phase type:** Rule-based insights. **No LLM**, no mock provider, no Azure, no Shiny changes.

## What was built

`python/llm_explanation/generate_deterministic_insights.py` — reads the 4 V4.2 evidence packs
and produces **visible, traceable, downloadable** insight cards and page summaries using
deterministic rules only. Verified: same evidence -> identical output (file hash stable).

## Outputs (in `outputs/v4_3_deterministic_insights/`)

- `v4_3_insight_cards.csv` — 30 cards across the 4 pages (all user-visible, all validation PASS)
- `v4_3_deterministic_insights.json` — full structured payload (metadata + pages + cards)
- `v4_3_page_summaries.md` — human-readable per-page bullet summaries
- `v4_3_risk_flags.csv` — risk/warning insights (e.g., model namespace difference)
- `v4_3_claims_traceability.csv` — every card mapped to pack, source artifacts, evidence fields
- `v4_3_sanitization_log.csv` — auditable record (V4.3 made 0 new changes; upstream V4.2 flags noted)
- `v4_3_validation.csv` — 22 checks, **22 PASS / 0 FAIL**
- `v4_3_closure_summary.md` — this file

## Insight coverage (examples, all rule-based)

- Champion remains **ETS Explicit** under governed conditions; not re-fit, not changed.
- Governed model scope = **15**; 0 candidates advanced; champion retained for review.
- Closest challenger by MASE ratio is **SMLP-TCN at 2.72x** (excludes the champion itself).
- Forecast Viewer evidence is filtered, summarized, and **capped** before explanation.
- **Model namespace difference** (productive labels vs tournament names) is surfaced as a risk flag.
- V4 is **evidence-only**; no LLM provider is active.
- Snapshot **2026-06-28** stated as accepted caveat.
- No SQL / model refresh / Shiny / champion / data-processed mutation occurred.

## Quality fix applied during the phase

The first run labelled the champion (ETS Explicit, ratio 1.00x) as the "closest challenger".
The rule was corrected to **exclude the champion** (ratio > 1.0 and name != champion), so the
card now correctly reports SMLP-TCN.

## Guarantees verified

- Determinism: identical `v4_3_insight_cards.csv` across reruns.
- No forbidden language in any user-visible output (re-scanned).
- Every visible insight has `source_artifacts`; every page has `limitations`; every card has `confidence`.
- Champion unchanged = ETS Explicit; scope unchanged = 15; no full raw forecast/actuals embedded.

## Guardrails honored

No LLM, no mock provider, no Azure, no Shiny changes, no buttons, no `run_llm_explainer.py`,
no data/processed or data/raw mutation, no SQL, no model runs, no champion/governance changes,
no V1/V2/V3 changes.

## Next (pending authorization)

V4.4 — Mock provider local (a button-triggered controlled narrative built from these
deterministic insights, still no real LLM). **Not started; awaiting Oscar's review and authorization.**
