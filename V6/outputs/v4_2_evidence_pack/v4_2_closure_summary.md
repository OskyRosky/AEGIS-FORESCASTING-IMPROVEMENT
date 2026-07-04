# V4.2 — Evidence Pack Builder — Closure Summary

- **Status:** `V4_2_EVIDENCE_PACK_COMPLETED`
- **Date:** 2026-06-29
- **Phase type:** First V4 code. Local, governed, **no LLM**, no Shiny changes.

## What was built

`python/llm_explanation/build_evidence_pack.py` — a local builder that reads only governed
artifacts under `data/processed` and emits small, **visible** evidence packs (JSON) that
represent exactly "what the LLM will be allowed to read" in later phases. It supports
`--all` and `--page-id` with `--entity`, `--model`, `--horizon`, `--output-dir`.

## Outputs (in `outputs/v4_2_evidence_pack/`)

- 4 JSON packs: `champion_overview`, `tournament`, `forecast_viewer`, `governance_risks`
- `v4_2_evidence_pack_summary.csv`, `v4_2_evidence_fields.csv`, `v4_2_evidence_validation.csv`
- `v4_2_evidence_summary.md` (auto), `v4_2_closure_summary.md` (this file)
- `examples/v4_2_evidence_pack_forecast_viewer.json` — a working **filtered** example

## Forecast Viewer — data minimization (the high-risk pack)

Verified: the pack never embeds full files.

| Run | rows_total_in_artifact | rows_after_filter | rows embedded (sample) |
|-----|-----------------------|-------------------|------------------------|
| `--all` (no filter) | 65,095 | 65,095 | **5 (capped)** |
| `--model ExponentialSmoothing` | 65,095 | 17,340 | **5 (capped)** |

The JSON documents `rows_total_in_artifact`, `rows_after_filter`, `columns_passed`,
`columns_withheld`, and `what_not_passed`. Full `forecasts.csv` / `actuals.csv` are never
embedded — only filtered aggregates (counts, min/max dates, value min/max/mean) plus a capped
5-row sample.

## Important naming-space note (honest finding)

The Forecast Viewer `model` filter matches **productive `model_version` labels** (e.g.,
`ExponentialSmoothing`, `ARIMA`, `FixedGrowth3%`, ensembles), which **differ** from tournament
model names (e.g., `ETS Explicit`, `SMLP-TCN`). Filtering by `ETS Explicit` therefore returns
`insufficient_evidence` and the pack lists `available_model_versions` to guide the user. This
mapping is documented so later phases (and the LLM) never conflate the two namespaces.

## Governance & language guarantees (verified)

- Champion frozen = **ETS Explicit**; governed scope = **15**; provider stage =
  `evidence_only_no_llm`.
- Forbidden language sanitized: artifact free-text (e.g., "Best DL... candidate",
  "0 candidates promoted") and forbidden column names (`best_dl_challenger` →
  `dl_challenger_reference`) were neutralized; a final recursive scan confirms
  `no_forbidden_language = True` for all 4 packs.
- Every pack carries `sources_used`, `limitations`, `candidate_claims` (traceable facts only,
  no narrative), `insufficient_evidence`, and an embedded `validation` block.

## Guardrails honored

No LLM, no mock provider, no Azure, no Shiny changes, no buttons, no data/processed or
data/raw mutation, no SQL, no model runs, no champion/governance changes, no V1/V2/V3 changes.

## Next (pending authorization)

V4.3 — Deterministic insights (rule-based cards/summaries from these packs, still no LLM).
**Not started; awaiting Oscar's review and authorization.**
