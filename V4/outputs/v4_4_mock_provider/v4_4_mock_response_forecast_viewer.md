# LLM Explanation — Forecast Viewer

> Provider: `mock` · Stage: `mock_no_llm` · This is a deterministic local mock, **not a real LLM**. No Azure OpenAI is connected.

## Executive summary
Under governed, evidence-only conditions, forecast Viewer evidence is filtered, summarized, and capped before explanation; full forecasts and actuals are never embedded. The current selection covers 65095 forecast rows out of 65095 total; only 5 rows are embedded as a sample. Forecast dates in the selection span 2026-04-28 to 2030-04-25. Forecast Viewer model labels (e.g., ExponentialSmoothing, ARIMA, FixedGrowth percentages) differ from tournament/governance model names (e.g., the champion name); this namespace difference must be shown so the two are never conflated.

## What the evidence says
- Forecast Viewer evidence is filtered, summarized, and capped before explanation; full forecasts and actuals are never embedded.
- The current selection covers 65095 forecast rows out of 65095 total; only 5 rows are embedded as a sample.
- Forecast dates in the selection span 2026-04-28 to 2030-04-25.
- Forecast Viewer model labels (e.g., ExponentialSmoothing, ARIMA, FixedGrowth percentages) differ from tournament/governance model names (e.g., the champion name); this namespace difference must be shown so the two are never conflated.

## Why it matters
This view matters because the forecast evidence is deliberately filtered, summarized, and capped before any explanation, and because the model labels here belong to a different namespace than the tournament names. Showing both protects reviewers from conflating productive labels with governed model names.

## Sources used
- forecasts_with_intervals.csv
- v4_2_evidence_pack_forecast_viewer.json
- v4_3_deterministic_insights.json
- v4_3_claims_traceability.csv
- v4_3_risk_flags.csv

## Limitations
- LLM explains; it does not decide, advance, or change the champion or governance.
- Data snapshot 2026-06-28 (V4 was cloned before the 2026-06-29 refresh and not resynced).
- Risk flag: Forecast Viewer model labels (e.g., ExponentialSmoothing, ARIMA, FixedGrowth percentages) differ from tournament/governance model names (e.g., the champion name); this namespace difference must be shown so the two are never conflated.

## Download payload
Confidence: **high**. The structured payload below will become downloadable (MD / CSV / JSON) in a later phase (V4.7); it is shown here for traceability only.

```json
{
  "page_id": "forecast_viewer",
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
