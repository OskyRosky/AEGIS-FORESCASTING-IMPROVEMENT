# V6.20 V5/V6 Presentation Reconciliation

## Final status

`V6_20_V5_V6_PRESENTATION_RECONCILIATION_BLOCKS_GENERATION`

This stage was read-only. No artifact was generated, no model was run, no SQL or
Tesseract extraction occurred, and no Shiny file was modified.

## Do V5/shiny_app and V6/shiny_app actually differ?

Barely. The two trees are near-identical:

| Measure | Value |
|---|---:|
| Files in `V5/shiny_app` | 48 |
| Files in `V6/shiny_app` | 53 |
| Identical | 43 |
| Different | 5 |
| Only in V5 | 0 |
| Only in V6 | 5 |

The five different files are `global.R`, `R/helpers.R`, `server/server.R`,
`ui/body.R` and `www/custom.css`. `R/helpers.R` differs by exactly two lines
(model family label capitalisation).

The five V6-only files are `R/viewer_pilot.R`, `R/forecast_pilot.R`,
`R/taxonomy_navigation.R`, `R/scenario_resolver.R` and `ui/tabs_v6_16_viewer.R`.

## What is the real baseline?

**Previous V6 presentation versus current V6 presentation**, not V5 versus V6.

`ui/tabs.R` is byte-identical between V5 and V6. That file still contains the
previous `section_explorer`, `section_forecast`, `section_accuracy` and
`section_ttl`. Because `ui/body.R` sources `ui/tabs_v6_16_viewer.R` *after*
`ui/tabs.R`, the later definitions of `section_explorer` and `section_forecast`
win. Everything else in `tabs.R` is still live.

So `ui/tabs.R` is simultaneously the V5 baseline and the live source for every
page except Viewer and Forecast.

## Git evidence

Git provides only partial evidence. `V6/shiny_app` has a single commit
(`0d573f4`, 2026-07-03, "add"). All V6.16, V6.17 and V6.18 work is still
uncommitted working-tree state: five modified files and five untracked files.
Per-change attribution was therefore reconstructed by file-level comparison
rather than by commit history.

## What V6 preserved

- Every page other than Viewer and Forecast, unchanged from V5.
- Accuracy metrics, heatmap and horizon logic.
- TTL prototype behaviour.
- Nine of ten LLM assistant panels.
- All eight governed artifact downloads.
- Artifact registry and fail-soft loader behaviour.
- Horizon, history window and chart semantics in the Viewer.

## What V6 improved

- Conditional, metadata-driven selection shared by Viewer and Forecast.
- Viewer coverage from 39 distinct entities to 596 route x key cases across 391
  distinct entities, over 6 routes.
- Forecast coverage to 896 entities across 8 routes.
- Explicit Forecast structure: Data Selection, Forecast Configuration, Forecast Results.
- Mandatory `Forecast start` boundary derived from the prepared artifact.
- Honest forecast-only handling for SSD-Phoenix, with no fabricated actuals.
- Complete Forecast data notes and conditional prediction-interval support.
- Lazy Parquet reads instead of full CSV loads.

## What was lost

One item, and it is real:

- **Forward Forecast lost its LLM assistant panel.** `server/server.R` line 552
  still registers `llm_forecasting_forecast`, the previous mount existed at
  `ui/tabs.R` line 673, and the live `section_forecast` in
  `ui/tabs_v6_16_viewer.R` has no `llm_explain_ui`. The module is orphaned.
  Classification: `LOST_FROM_PREVIOUS_V6`, user impact HIGH, no recalculation
  required.

## What must be recovered before generation

1. **Accuracy data source decision.** `acc_data()` resolves to
   `data/processed/forecast_viewer_model_outputs.csv`: 204,300 rows, 39 distinct
   entities, 15 models. The Viewer reads 2,416,050 rows covering 596 route x key
   cases across 391 distinct entities. The
   product currently shows two different universes. The owner must choose
   between migrating, labelling, disabling, or rebuilding Accuracy.
2. **Artifact registry versus Parquet-only.** The registry holds 43 entries,
   40 of them CSV and none Parquet. The productive Parquet files are read
   directly by the providers and are invisible to the registry. Under a
   Parquet-only migration, `forecast_viewer_full` would disappear and, because
   the loader fails soft, the Accuracy page would silently render empty rather
   than fail.

## What can be deferred

- Removal of the shadowed `tabs.R` sections and the `if (FALSE)` server blocks.
- `scenario_resolver.R`, which remains present and unwired.
- TTL legacy inputs.
- Prediction intervals, which are inert because the prepared forward artifact has
  no `lower_bound`, `upper_bound` or `interval_level` columns.
- Restoring the Forecast LLM panel is low-risk and may be done before or after
  generation, but it should not be forgotten.

## Owner decisions needed

| ID | Topic | Blocks generation |
|---|---|---|
| V620-D001 | Accuracy data source (A/B/C/D) | Yes |
| V620-D002 | Parquet-only migration and registry extension | Yes |
| V620-D003 | Restore the Forward Forecast LLM panel | No |
| V620-D004 | Normalize fail-soft versus fail-fast behaviour | No |
| V620-D005 | Emit prediction intervals in the next generation | No |
| V620-D006 | Remove dead legacy code after closure | No |

## Can artifact generation proceed?

No. Two open decisions define what the next generation must produce: the
Accuracy source and the Parquet-only registry contract. These are additional to
the V6.19 blockers, which remain open (missing E11 cohort files and the
unresolved SSD-Phoenix branch mapping).

## Exact next recommended step

Resolve V620-D001 and V620-D002 together with the V6.19 cohort decision, because
all three determine the schema, scope and format of the next productive build.
Restoring the Forward Forecast LLM panel can be scheduled independently as a
single-line UI change.

## Files created

- `v6_20_tree_diff_inventory.csv`
- `v6_20_git_change_evidence.csv`
- `v6_20_v5_v6_feature_diff.csv`
- `v6_20_recovery_candidates.csv`
- `v6_20_safe_to_defer.csv`
- `v6_20_owner_decisions_needed.csv`
- `v6_20_artifact_registry_risk.csv`
- `v6_20_llm_panel_reconciliation.csv`
- `v6_20_accuracy_data_source_reconciliation.csv`
- `v6_20_validation.csv`
- `v6_20_closure_summary.md`

## Files not touched

V1 through V5, all Shiny source files, productive CSV and Parquet artifacts,
model code, Tesseract and SQL, Docker, Azure, Grafana, and the Assistant/LLM
engine.
