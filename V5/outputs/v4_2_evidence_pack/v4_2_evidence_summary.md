# V4.2 — Evidence Pack Builder — Summary

- Generated: 2026-06-29T16:51:17Z
- Project root: `V4`
- Champion (frozen): **ETS Explicit** · Model scope: **15**
- Provider stage: `evidence_only_no_llm` (no LLM)

## Packs

| page_id | sources | evidence keys | claims | insufficient_evidence | no_forbidden_language |
|---------|---------|---------------|--------|-----------------------|-----------------------|
| champion_overview | 3 | 4 | 4 | False | True |
| tournament | 3 | 3 | 2 | False | True |
| forecast_viewer | 1 | 1 | 2 | False | True |
| governance_risks | 4 | 4 | 2 | False | True |

## Forecast Viewer data minimization

The `forecast_viewer` pack embeds **only** filtered aggregates plus a capped sample (max 5 rows). Full `forecasts.csv` and `actuals.csv` are never embedded; the JSON documents `rows_total_in_artifact`, `rows_after_filter`, and `what_not_passed`.

## Sources used per pack

- **champion_overview**: model_champion_comparison.csv, model_dashboard_summary.csv, model_universe_canonical.csv
- **tournament**: model_evaluation_ranking.csv, model_evaluation_summary.csv, model_runtime_guardrails.csv
- **forecast_viewer**: forecasts_with_intervals.csv
- **governance_risks**: model_runtime_guardrails.csv, model_universe_canonical.csv, run_metadata.csv, ttl_months_to_live_snapshot.csv
