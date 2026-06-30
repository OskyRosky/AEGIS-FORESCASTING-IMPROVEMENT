# V4.3 — Deterministic Page Summaries (no LLM)

- Champion (frozen): **ETS Explicit** · Model scope: **15**
- Stage: deterministic_insights_no_llm

## champion_overview

- **Champion under governed conditions** — Champion remains ETS Explicit under governed conditions; not re-fit and not changed in V4.
- **Champion accuracy** — Champion accuracy on record: median MASE 6.90, median RMSSE 1.86.
- **Governed model scope** — Governed model scope contains 15 models.
- **No candidates advanced** — 0 candidates were advanced; the champion is retained for review.
- **Evidence-only stage** — V4 is evidence-only at this stage; no LLM provider is active. Insights are produced by deterministic rules.
- **Accepted snapshot caveat** — V4 uses snapshot 2026-06-28 as an accepted caveat for local LLM-layer development.
- **No mutations in V4.3** — No SQL, model refresh, Shiny mutation, champion mutation, or data/processed mutation occurred in V4.3.
- **Traceability guarantee** — Each visible insight is traceable to evidence fields or source artifacts.

_Limitations:_ Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced). LLM explains, does not decide.

## tournament

- **Models reviewed** — Evidence indicates 7 models ranked for review under stated conditions.
- **Closest challenger by MASE ratio** — The closest challenger by MASE ratio is SMLP-TCN at 2.72x the champion; it remains a documented challenger.
- **Challengers retained** — All challengers remain documented challengers; none advanced over the champion.
- **Evidence-only stage** — V4 is evidence-only at this stage; no LLM provider is active. Insights are produced by deterministic rules.
- **Accepted snapshot caveat** — V4 uses snapshot 2026-06-28 as an accepted caveat for local LLM-layer development.
- **No mutations in V4.3** — No SQL, model refresh, Shiny mutation, champion mutation, or data/processed mutation occurred in V4.3.
- **Traceability guarantee** — Each visible insight is traceable to evidence fields or source artifacts.

_Limitations:_ Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced). LLM explains, does not decide.

## forecast_viewer

- **Evidence is minimized** — Forecast Viewer evidence is filtered, summarized, and capped before explanation; full forecasts and actuals are never embedded.
- **Selection coverage** — The current selection covers 65095 forecast rows out of 65095 total; only 5 rows are embedded as a sample.
- **Forecast horizon span** — Forecast dates in the selection span 2026-04-28 to 2030-04-25.
- **Model namespace difference** — Forecast Viewer model labels (e.g., ExponentialSmoothing, ARIMA, FixedGrowth percentages) differ from tournament/governance model names (e.g., the champion name); this namespace difference must be shown so the two are never conflated.
- **Evidence-only stage** — V4 is evidence-only at this stage; no LLM provider is active. Insights are produced by deterministic rules.
- **Accepted snapshot caveat** — V4 uses snapshot 2026-06-28 as an accepted caveat for local LLM-layer development.
- **No mutations in V4.3** — No SQL, model refresh, Shiny mutation, champion mutation, or data/processed mutation occurred in V4.3.
- **Traceability guarantee** — Each visible insight is traceable to evidence fields or source artifacts.

_Limitations:_ Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced). LLM explains, does not decide.

## governance_risks

- **Governance scope is bounded by evidence** — Governance and risk explanation is limited to the artifacts available in the evidence pack; no risks are inferred beyond recorded data.
- **TTL snapshot coverage** — The governance snapshot covers 45 entities; months-to-live recorded min 5.23, median 18.60.
- **Governed scope and risk flags** — Governed model scope is 15 with 0 model(s) carrying a recorded risk flag.
- **Evidence-only stage** — V4 is evidence-only at this stage; no LLM provider is active. Insights are produced by deterministic rules.
- **Accepted snapshot caveat** — V4 uses snapshot 2026-06-28 as an accepted caveat for local LLM-layer development.
- **No mutations in V4.3** — No SQL, model refresh, Shiny mutation, champion mutation, or data/processed mutation occurred in V4.3.
- **Traceability guarantee** — Each visible insight is traceable to evidence fields or source artifacts.

_Limitations:_ Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced). LLM explains, does not decide.

