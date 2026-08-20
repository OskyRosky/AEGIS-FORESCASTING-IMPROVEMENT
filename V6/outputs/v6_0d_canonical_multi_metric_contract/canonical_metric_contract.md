# V6.0D — Canonical Multi-Metric Contract

**Stage:** V6.0D — Canonical Multi-Metric Contract
**Status:** design and governance only. No builder, no Shiny change, no legacy artifact touched.
**Depends on:** `V6/outputs/v6_0c_multi_metric_scope_diagnosis/`
**Contract version:** `v6.0d`

---

## 1. Purpose

V6.0C proved that the current pipeline destroys source identity, blends SSD-Phoenix
LVWE with LVNE in rankings, and never surfaces the official metrics in Shiny. This
document defines the contract that removes those failure modes structurally rather
than by patching a metric.

The contract is **additive**. Every legacy artifact listed in
`hdd_baseline_freeze.csv` stays byte-identical. New dimensions live only in new
artifacts.

## 2. Design principles

| # | Principle | Consequence |
| --- | --- | --- |
| P1 | Identity travels with every row | No consumer ever parses a filename to learn what a row is |
| P2 | Nothing branches on a metric name | Behaviour is driven by registry declarations and computability flags |
| P3 | Absence is a value, not a blank | `not_applicable` and `UNKNOWN` are first-class and never replaced by a guess |
| P4 | Isolation is enforced, not assumed | Aggregation is illegal unless the full identity tuple matches |
| P5 | Capability is declared, not inferred by the UI | Shiny reads booleans; it never decides what is computable |
| P6 | Legacy is superseded, never overwritten | New artifacts sit beside the frozen ones |
| P7 | The assistant layer is preserved and extended, never bypassed | Its grounding gains multi-metric context through an additive pack. See `llm_assistant_grounding_contract.md` |

## 3. Canonical row identity

The **identity tuple** is the contract's central object:

```
metric_id + db_type + scenario + granularity + entity_key + forecast_version
```

Two rows may only be aggregated when all six components are equal. This single
rule is what prevents the V6.0C defect: LVWE and LVNE share five of the six
components and differ only in `db_type`, so under this contract they can never
collapse into one ranking row.

Full column specification is in `canonical_metric_columns.csv` (44 columns).

## 4. Scenario is an optional dimension

Verified in V6.0C: `Scenario` exists only on the HDD fact table. All four metrics
tables lack it entirely.

Resolution rules, in order:

1. If the source exposes a `Scenario` column, copy the value verbatim and set
   `scenario_status = present`.
2. If the source has no `Scenario` column, set `scenario = not_applicable` and
   `scenario_status = not_applicable`.
3. If a stakeholder decision is required before the value can be known, set
   `scenario = pending_mapping` and `scenario_status = pending_mapping`.
4. Otherwise set both to `unknown`.

Hard prohibitions:

- Never write a blank or null scenario.
- Never inherit a scenario from another source.
- Never default to `Enterprise` for a source that has no scenario column.
- Never require Scenario as a mandatory filter step.

`not_applicable` participates in the identity tuple as a real value, so isolation
still holds for sources without scenarios.

## 5. Unit discipline

`unit` is mandatory on every row, and `UNKNOWN` is the honest default. No unit is
assumed, converted, or inferred. Detail in `metric_unit_contract_v6_0d.csv`.

Two hard rules:

- Raw business values are never aggregated across `metric_id`.
- A ranking group must resolve to exactly one `unit`; more than one is a build
  failure, not a warning.

## 6. Computability is declared upstream

Five booleans plus a derived status describe what each row supports. The dashboard
consumes them and never re-derives them. Precedence and allowed values are defined
in `computability_and_availability_contract.md`.

The critical distinction the contract must protect: **single-version accuracy is
not drift**. A source with one forecast version gets
`computability_status = single_version_accuracy_only` and
`drift_computable = false`, and Shiny must present it as accuracy evidence with an
explicit limitation rather than as an empty or zero drift chart.

## 7. Ranking contract

Defined in full in `official_artifact_contracts.md` section 3.

Grouping key: the six-part identity tuple. Grouping by `Key` plus
`Forecast_Version` alone is prohibited by contract.

Additional guard: a ranking row may aggregate rows from more than one
`source_object` **only** when the registry sets `merge_sources_allowed = true` for
that metric and db_type. The default is `false`. This protects the contract even
if stakeholder decision D2 later reclassifies LVWE and LVNE.

Ranking rows must also carry coverage context: `n_source_rows`, `n_windows`,
`window_start_min`, `window_end_max`, `unit`, and `computability_status`.

## 8. Relationship to the legacy artifacts

| Legacy artifact | Treatment under this contract |
| --- | --- |
| `data/processed/forecasts.csv` | Frozen. No new column is added. |
| `data/processed/actuals.csv` | Frozen. |
| `data/processed/forecast_comparison.csv` | Frozen. Its emptiness is documented as defect D-05. |
| `data/processed/forecast_viewer_model_outputs.csv` | Frozen. Remains the backtest source for the Viewer. |
| `outputs/metrics/baseline_metrics.csv` | Frozen and superseded by `official_metrics_normalized.csv`. |
| `outputs/metrics/baseline_rankings.csv` | Frozen and superseded by `official_metric_rankings.csv`. Not deleted. |

Superseded means a newer artifact becomes the governed source for new consumers.
It does not mean the old file is edited, moved, or removed.

## 9. What this contract deliberately does not decide

The contract is designed to stay valid whichever way the open stakeholder
decisions land:

- **D2** SSD-Phoenix Total, Organic and Low-Vol classification. Today LVWE and
  LVNE are modelled as `db_type` values. If they are reclassified as scenarios or
  variants, only the registry mapping changes; the isolation guarantee does not.
- **D3** CPU Consumed and Failover, plus the placement of Fleet and Workload.
- **D4** Exact table names for CPU, SSD-Total and MCDB.
- **D5** Real units for every metric, including HDD.
- **D10** Whether `SSD_TotalForecast` is shared and what discriminates its rows.

Until each is resolved, the affected rows carry `pending_mapping` and
`blocked_by_mapping` rather than a guess.
