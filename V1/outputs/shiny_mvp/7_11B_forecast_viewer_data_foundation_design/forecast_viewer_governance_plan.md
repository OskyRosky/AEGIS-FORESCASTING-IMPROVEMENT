# Forecast Viewer — Governance & Audit Plan

> How the consolidated `forecast_viewer_model_outputs` artifact must be governed.

## Provenance & manifest

- Ship a **manifest** (`forecast_viewer_model_outputs_manifest.csv`) listing every source artifact, its
  row count, checksum, and the build `run_id` / build timestamp.
- Every output row carries `source_artifact` so any value is traceable to its Stage 5 origin.

## Build-time validations (must all pass before publish)

| Validation | Rule |
|---|---|
| Schema validation | Columns + types match `forecast_viewer_recommended_schema.csv` |
| Row-count validation | Baseline rows == 95,340; challenger rows == 81,720; no inflation from joins |
| No recomputation | Build performs joins/relabels only; no model/inference/metric call |
| No synthetic forecasts | Every `forecast_value` maps 1:1 to a source row |
| Series coverage | 39 multi-model + 6 final-only = 45 series accounted for |
| Model coverage | 13 models on multi-model series; NBEATS/NHITS absent from forecast rows |
| Champion uniqueness | Exactly one `is_selected_champion = TRUE` (ETS Explicit) |
| Interval availability | `lower_bound`/`upper_bound` all NA → flagged "intervals not available" |
| Date-range validation | Backtest rows within 2025-05-03 → 2026-04-27 |

## Runtime governance (Shiny)

- **No recomputation inside Shiny** — Shiny reads + filters the governed artifact only.
- Viewer renders the honesty banners (backtest scope, 39/45 coverage, no deep learning, no intervals).
- Challenger forecasts labeled as **Stage 5 backtest evidence under a process flagged for remediation
  (AUDIT #2)**, not as final governed-champion output.

## Known limitations (must be documented with the artifact)

1. Backtest window only (no forward multi-model forecast).
2. 6 series lack multi-model coverage.
3. No deep-learning forecasts (NBEATS/NHITS deferred).
4. No prediction intervals (point forecasts only).
5. Challenger execution post-dates the blocking AUDIT #2; treat as evidence, not final governance.
