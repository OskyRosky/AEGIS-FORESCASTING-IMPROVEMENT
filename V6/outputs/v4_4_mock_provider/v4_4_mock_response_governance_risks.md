# LLM Explanation — Governance & Risks

> Provider: `mock` · Stage: `mock_no_llm` · This is a deterministic local mock, **not a real LLM**. No Azure OpenAI is connected.

## Executive summary
Under governed, evidence-only conditions, governance and risk explanation is limited to the artifacts available in the evidence pack; no risks are inferred beyond recorded data. The governance snapshot covers 45 entities; months-to-live recorded min 5.23, median 18.60. Governed model scope is 15 with 0 model(s) carrying a recorded risk flag.

## What the evidence says
- Governance and risk explanation is limited to the artifacts available in the evidence pack; no risks are inferred beyond recorded data.
- The governance snapshot covers 45 entities; months-to-live recorded min 5.23, median 18.60.
- Governed model scope is 15 with 0 model(s) carrying a recorded risk flag.

## Why it matters
Governance matters because the explanation is bounded strictly by the recorded evidence pack. The time-to-live coverage and the count of models carrying a recorded risk flag are surfaced so reviewers can see the governed footprint without inferring risks beyond the data.

## Sources used
- run_metadata.csv
- ttl_months_to_live_snapshot.csv
- model_runtime_guardrails.csv
- model_universe_canonical.csv
- v4_2_evidence_pack_governance_risks.json
- v4_3_deterministic_insights.json
- v4_3_claims_traceability.csv
- v4_3_risk_flags.csv

## Limitations
- LLM explains; it does not decide, advance, or change the champion or governance.
- Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced).

## Download payload
Confidence: **high**. The structured payload below will become downloadable (MD / CSV / JSON) in a later phase (V4.7); it is shown here for traceability only.

```json
{
  "page_id": "governance_risks",
  "format_options": [
    "md",
    "json"
  ],
  "available_in_phase": "V4.7",
  "card_count": 7,
  "source_files": [
    "v4_3_deterministic_insights.json",
    "v4_3_claims_traceability.csv",
    "v4_3_risk_flags.csv"
  ],
  "note": "Download UI is deferred to V4.7; the payload structure is shown here for traceability only."
}
```
