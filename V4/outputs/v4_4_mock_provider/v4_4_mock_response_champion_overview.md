# LLM Explanation — Champion Overview

> Provider: `mock` · Stage: `mock_no_llm` · This is a deterministic local mock, **not a real LLM**. No Azure OpenAI is connected.

## Executive summary
Under governed, evidence-only conditions, champion remains ETS Explicit under governed conditions; not re-fit and not changed in V4. Champion accuracy on record: median MASE 6.90, median RMSSE 1.86. Governed model scope contains 15 models. 0 candidates were advanced; the champion is retained for review.

## What the evidence says
- Champion remains ETS Explicit under governed conditions; not re-fit and not changed in V4.
- Champion accuracy on record: median MASE 6.90, median RMSSE 1.86.
- Governed model scope contains 15 models.
- 0 candidates were advanced; the champion is retained for review.

## Why it matters
These figures describe the champion under governed conditions only. They are presented so reviewers can see the current accuracy of record and the size of the governed scope. Nothing here advances or changes the champion; the numbers support human review, not a documented decision.

## Sources used
- model_dashboard_summary.csv
- model_universe_canonical.csv
- v4_2_evidence_pack_champion_overview.json
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
  "page_id": "champion_overview",
  "format_options": [
    "md",
    "json"
  ],
  "available_in_phase": "V4.7",
  "card_count": 8,
  "source_files": [
    "v4_3_deterministic_insights.json",
    "v4_3_claims_traceability.csv",
    "v4_3_risk_flags.csv"
  ],
  "note": "Download UI is deferred to V4.7; the payload structure is shown here for traceability only."
}
```
