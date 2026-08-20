# V6.0D — Official Artifact Contracts

Specification of the eight artifacts that **V6.0E** must build. Nothing here is
built in V6.0D.

Proposed location: `V6/outputs/metrics_multi/`.

Rationale for the location: `outputs/` is already mounted read-only into the
container (`./outputs:/app/outputs:ro`), so artifacts placed here are visible to
the dashboard locally and, later, through the Azure Files mount. A new
subdirectory keeps them physically separate from the frozen
`outputs/metrics/`. This answers open question Q17.

---

## 1. official_metrics_normalized.csv

**Grain:** one row per identity tuple per evaluation window.

**Purpose:** the single governed table of official accuracy metrics across every
available metric and db_type, carrying full identity and capability.

**Columns:** all 44 canonical columns from `canonical_metric_columns.csv`.

**Producer rules:**

- Built by iterating the registry. No hardcoded file list.
- Every input row keeps its verbatim measures; nothing is recomputed.
- Rows are only emitted for sources whose `availability_status` is
  `local_ingested` or `partially_available`.
- Unavailable metrics are represented in `metric_availability_status.csv`, not as
  empty rows here.

**Expected initial scope** given the current local snapshot: the four metrics
tables, that is 27,067 source rows carrying full identity instead of a filename.

## 2. official_metric_rankings.csv

**Grain:** one row per identity tuple.

**Grouping key, mandatory and complete:**

```
metric_id, db_type, scenario, granularity, entity_key, forecast_version
```

**Contamination guard:** if a group draws from more than one `source_object`, the
build fails unless the registry sets `merge_sources_allowed = true` for that
metric and db_type. Default `false`.

**Unit guard:** a group must resolve to exactly one `unit`. More than one is a
build failure.

**Aggregates:** `avg_mape`, `avg_smape`, `avg_rmse`, `avg_mae`, `avg_bias_pct`,
`avg_accuracy`, `worst_mape`, `worst_accuracy`.

**Coverage context, mandatory:** `n_source_rows`, `n_windows`,
`window_start_min`, `window_end_max`, `unit`, `computability_status`,
`source_object_count`.

**Ranks:** computed **within** a partition of `metric_id + db_type + granularity +
forecast_version`. A rank is meaningless across metrics, so a global rank is
prohibited.

**Why this matters:** under the legacy grouping, 137 of 736 groups blended LVWE
and LVNE, folding 15,689 rows. Under this contract that outcome is unreachable
because `db_type` is part of the key and `source_object_count` is asserted.

## 3. metric_filter_options.csv

**Grain:** one row per selectable option per filter level.

**Columns:** `filter_level`, `parent_level`, `parent_value`, `option_value`,
`option_label`, `enabled`, `reason`, `sort_order`.

**Purpose:** Shiny reads its dropdown contents from this file. No option is ever
hardcoded in the UI, which is what keeps the app metric-agnostic.

Disabled options are emitted with `enabled = false` and a `reason`, so the UI can
show why something is unavailable instead of silently hiding it.

## 4. metric_availability_status.csv

**Grain:** one row per `metric_id` plus `db_type` plus `granularity`.

Covers the **entire known universe**, including metrics with no local data, so the
dashboard can state honestly that CPU, SSD-MCDB and IOPS are not available and
why. Seeded from `v6_0c_source_inventory.csv`.

## 5. metric_computability_status.csv

**Grain:** one row per `metric_id` plus `db_type` plus `granularity`.

Carries the five booleans, the derived `computability_status`, and the
`not_computable_reason` codes. This is the file Shiny consults before rendering
any chart type.

## 6. metric_source_lineage.csv

**Grain:** one row per `source_object` and `source_file` pair.

Records `rows_in`, `rows_out`, the input `sha256`, and the production timestamp,
so any normalized row can be traced to a physical source and any drift in the
inputs is detectable.

## 7. metric_data_quality_checks.csv

**Grain:** one row per check per source.

Minimum checks: duplicate identity tuples, null measures, accuracy outside 0 to
100, `evaluation_end_date` earlier than `evaluation_start_date`, and unparseable
`forecast_version`.

Failing rows are **flagged and kept**, never dropped. Dropping data silently is
the failure mode this whole stage exists to remove.

## 8. metric_registry_resolved.csv

**Grain:** one row per registered `source_object`.

The materialised registry actually used by the build, so a reviewer can diff
intent against behaviour without reading code.

## 9. metric_assistant_evidence_pack.json

**Grain:** one entry per identity tuple.

**Purpose:** give the existing AI assistant layer grounded context for the active
multi-metric selection **without changing how it works today**.

The frozen `outputs/v4_4_mock_provider/v4_4_mock_responses.json` keeps answering
page-level questions unchanged. This new pack adds selection-level context and
reuses the same field shapes, so the renderer, the confidence badge, the
limitations block, the traceability panel and the five export formats need no
structural change.

Mandatory content per entry: the identity tuple, `unit` and `unit_status`,
`availability_status`, `computability_status`, `not_computable_reason`,
`sources_used`, `limitations` and `claims_traceability`.

When this pack is absent the assistant must behave exactly as it does today. Full
rules are in `llm_assistant_grounding_contract.md`.

---

## Cross-artifact rules

| Rule | Statement |
| --- | --- |
| R1 | Every artifact is additive. No legacy file is edited moved or deleted. |
| R2 | Every normalized row traces to `source_object` and `source_file`. |
| R3 | Every ranking row traces to the normalized rows that produced it. |
| R4 | Every Shiny option traces to `metric_filter_options.csv`. |
| R5 | No artifact contains raw business data outside the governed metrics. |
| R6 | No artifact contains credentials connection strings or server names. |
| R7 | A metric that cannot be computed appears with a status and a reason, never as zero and never as an empty chart. |
