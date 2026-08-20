# V6.0F — Shiny Integration Requirements

Produced by V6.0E. This is the input specification for the next stage. No Shiny
file was touched in V6.0E.

---

## 1. Artifacts V6.0F must consume

All artifacts live in `V6/outputs/metrics_multi/`, which is already inside the
container read-only mount (`./outputs:/app/outputs:ro`).

| Purpose | Artifact |
| --- | --- |
| Filter contents and dependencies | `metric_filter_options.csv` |
| Metric tables | `official_metrics_normalized.csv` |
| Rankings | `official_metric_rankings.csv` |
| Availability badges | `metric_availability_status.csv` |
| Visual gating | `metric_computability_status.csv` |
| Traceability panel | `metric_source_lineage.csv` |
| Data quality flags | `metric_data_quality_checks.csv` |
| Registry transparency | `metric_registry_resolved.csv` |
| Assistant selection context | `assistant_metric_context.csv` |
| Assistant narrative grounding | `metric_assistant_evidence_pack.json` |

Register them through the existing governed loader in
`shiny_app/R/data_loader.R` using the same additive pattern as every other
artifact. Do not modify any existing registry entry.

## 2. Hard rules for the integration

| Rule | Statement |
| --- | --- |
| S1 | No live SQL. The dashboard reads artifacts only |
| S2 | No Shiny-side recomputation of any business measure |
| S3 | No raw aggregation across metrics or units |
| S4 | Never show single-version accuracy as drift |
| S5 | Filter contents come from `metric_filter_options.csv`, never from hardcoded vectors |
| S6 | View rendering is gated by `shiny_allowed_views` in `metric_computability_status.csv` |
| S7 | The existing pages, downloads and assistant panels stay exactly as they are |

## 3. Filter wiring

The dependency chain is already materialised in the artifact:

```
Metric -> DB Type -> Scenario -> Granularity -> Key -> Forecast Version
```

`filter_value` is a composite path such as
`ssd_phoenix::lv_with_efficiency::not_applicable::forest::NAMPRD07::2026-03-12`,
and `parent_value` points at the parent option, so the chain can be walked with a
simple filter and never needs bespoke logic.

Current option counts:

| Level | Options | Enabled |
| --- | --- | --- |
| Metric | 6 | 2 |
| DB Type | 10 | 3 |
| Scenario | 3 | 0 |
| Granularity | 4 | 4 |
| Key | 474 | 474 |
| Forecast Version | 873 | 873 |
| Availability Status | 6 | 6 |
| Computability Status | 5 | 5 |

Disabled options are intentional. Every one carries `reason_if_disabled` so the UI
explains the gap rather than hiding it.

Scenario is currently disabled on all three options because every local metrics
source lacks a Scenario column. Render it as `Not applicable` or hide it. Never
send a scenario value and never default to a scenario name.

## 4. View gating

| computability_status | Views to render |
| --- | --- |
| `accuracy_only` | accuracy table, accuracy heatmap, cross-version trend, plan-to-plan |
| `single_version_accuracy_only` | accuracy table, accuracy heatmap, plus a single-version badge |
| `blocked_by_data` / `blocked_by_mapping` / `not_computable` | none, with the reason shown |

`shiny_allowed_views` already encodes this per combination.

## 5. Assistant extension

The assistant keeps its current behaviour. Extend grounding only:

1. Keep reading `outputs/v4_4_mock_provider/v4_4_mock_responses.json` for the 11
   page-level responses. That file is frozen.
2. Additionally read `metric_assistant_evidence_pack.json`, which uses the same
   field shape (`summary`, `what_the_evidence_says`, `why_it_matters`,
   `sources_used`, `limitations`, `confidence`, `claims_traceability`,
   `download_payload`) and holds 11 multi-metric entries.
3. For the active selection, read the matching row of
   `assistant_metric_context.csv` and use `safe_summary`,
   `explanation_context`, `assistant_allowed_claims` and
   `assistant_disallowed_claims`.
4. If either new artifact is missing, the assistant must behave exactly as it does
   today.

## 6. Visual validations Oscar must be able to see

| # | Check |
| --- | --- |
| 1 | Metric filter visible with HDD-EDB and SSD-Phoenix enabled |
| 2 | DB Type filter visible with EDB, Low-Vol with Efficiency, Low-Vol without Efficiency |
| 3 | Scenario shown as Not applicable or hidden, never as Enterprise |
| 4 | Granularity filter visible with region and forest |
| 5 | Key filter visible and scoped to the selected granularity |
| 6 | Forecast Version filter visible and labelled single version where applicable |
| 7 | HDD region metrics visible |
| 8 | HDD forest metrics visible |
| 9 | SSD-Phoenix LVWE visible |
| 10 | SSD-Phoenix LVNE visible |
| 11 | NAMPRD07 visible as forest |
| 12 | LVWE and LVNE clearly separated, never one blended row |
| 13 | Single-version accuracy badge visible on SSD-Phoenix |
| 14 | Drift and curve views hidden where not computable, with the reason shown |
| 15 | Unavailable metrics such as CPU listed with a status and a reason |
| 16 | Assistant panel still present on every page that has it today |
| 17 | Assistant explains the active metric selection |
| 18 | Assistant explains why drift is unavailable for SSD-Phoenix |
| 19 | All five explanation export formats still work |
| 20 | Existing governed downloads still work |

## 7. Tests deferred into V6.0F

`T34` assistant export formats and the runtime half of `T26` to `T32` require a
running Shiny session and must be executed in V6.0F. `T35` container parity is
executed in V6.0H.
