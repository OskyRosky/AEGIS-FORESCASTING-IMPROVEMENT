# Stage 07 / Block 7.3 - MODELS / Universe

_Generated: 2026-06-16 12:11:21_

## Summary

Populated the MODELS / Universe page of the read-only governed Shiny MVP.
All values are read from the governed `final_model_universe` artifact via the
Stage 07.0E loader. No metric was recomputed, no model was run, no forecast was
generated, and the champion decision is presented unchanged.

## Governed counts (read from artifact)

- Total models: **15**
- Baselines: **7**
- Challengers: **8**
- Included in tournament: **13**
- Deferred models: **2**
- Champion eligible: **12**
- Selected champion (with conditions): **1** (ETS Explicit)
- Models with risk flags: **3**

## Page content

- **Header**: title 'Model Universe' + governed subtitle.
- **Summary cards**: eight KPI cards across two rows for the counts above.
- **Table**: a read-only, searchable DT table (one row per model) with badges
  for origin, status, tournament inclusion, champion eligibility, the selected
  champion (with conditions), and risk flags. Deferred reasons are shown verbatim.
- **Notes**: governed interpretation rows explaining baseline, challenger,
  tournament inclusion, deferral, champion eligibility, and the conditional
  nature of the champion selection.

## Table rendering strategy

- Preferred `reactable` is **not installed**; `DT` (installed) is used instead as a
  static widget embedded at UI build time (no server handlers, no recompute).
- Badges reuse the existing `.pill` classes; a small scoped `.tess-table-wrap`
  CSS block styles the DataTable to match the shell (light + dark theme).

## Validation: 21 pass / 0 warning / 0 fail / 0 n/a

| Check | Status | Details |
| --- | --- | --- |
| models_universe_populated | pass | MODELS / Universe renders header, summary cards and governed table. |
| universe_artifact_loaded_via_loader | pass | final_model_universe read via governed loader (rows=15). |
| model_count_matches_artifact | pass | Displayed total (15) equals artifact row count (15). |
| baseline_count_computed | pass | Baselines derived from model_origin == 'baseline' (7). |
| challenger_count_computed | pass | Challengers derived from model_origin == 'challenger' (8). |
| tournament_inclusion_count_computed | pass | Included in tournament derived from included_in_tournament (13). |
| deferred_count_computed | pass | Deferred derived from included_in_tournament == FALSE (2). |
| champion_eligible_count_computed | pass | Champion eligible derived from eligible_for_champion (12). |
| selected_champion_with_conditions_shown | pass | Selected champion with conditions shown (1 = ETS Explicit). |
| risk_flag_count_computed | pass | Risk-flagged models derived from risk_flag (3). |
| no_metrics_recalculated | pass | Only existing artifact columns are read; no metric is recomputed. |
| no_forecasts_generated | pass | No forecasting code is invoked by the Universe page. |
| no_models_run | pass | No model training or scoring is invoked by the Universe page. |
| champion_decision_unchanged | pass | Champion selection is read from the artifact and presented unchanged. |
| no_forbidden_language_universe | pass | No forbidden terms in the Universe page. |
| no_forbidden_language_home | pass | No forbidden terms in the Home page. |
| overview_remains_deferred | pass | PROJECT / Overview is intentionally still a placeholder (deferred per plan). |
| home_intact | pass | PROJECT / Home hero remains intact. |
| ttl_remains_roadmap | pass | TTL section remains a roadmap/placeholder (not populated in 7.3). |
| app_launches | pass | Shiny app launched successfully (verified at runtime). |
| http_200 | pass | HTTP status: 200. |

## Runtime

- HTTP status: **200**
- Launch verified at runtime: **yes**

## Safety

- Read-only: existing artifacts only.
- No recompute, no model run, no forecast generation.
- Champion decision unchanged.
- Forbidden language (Universe): none
- Forbidden language (Home): none

